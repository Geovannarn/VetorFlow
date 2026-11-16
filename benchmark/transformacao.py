import time
from collections import defaultdict
from contextlib import contextmanager

import numpy as np
import pandas as pd

from benchmark import config
from neighborhood.normalizer import normalizar_bairro
from normalizers.cnpj import validar_cnpj
from normalizers.postal_code import normalizar_cep


MOTIVOS = [
    "id_vazio",
    "nome_vazio",
    "documento_vazio",
    "documento_invalido",
    "cep_invalido",
    "duplicado",
]


class Cronometros:

    def __init__(self):
        self.tempos = defaultdict(float)

    @contextmanager
    def trecho(self, nome):
        inicio = time.perf_counter()

        try:
            yield
        finally:
            self.tempos[nome] += time.perf_counter() - inicio


def validar_cpf(cpf):
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False

    def digito(numeros, pesos):
        resto = sum(int(n) * p for n, p in zip(numeros, pesos)) % 11
        return 0 if resto < 2 else 11 - resto

    d1 = digito(cpf[:9], range(10, 1, -1))
    d2 = digito(cpf[:9] + str(d1), range(11, 1, -1))

    return cpf[9:] == f"{d1}{d2}"


def validar_documento(documento):
    if len(documento) == 14:
        return validar_cnpj(documento)

    if len(documento) == 11:
        return validar_cpf(documento)

    return False


def mapear_unicos(serie, funcao):
    """Aplica a função uma vez por valor diferente (ótimo para colunas com poucos valores)."""
    tabela = {valor: funcao(valor) for valor in serie.unique()}

    return serie.map(tabela)


def transformar(caminho_entrada, caminho_limpo, caminho_rejeitados, tamanho_chunk=config.TAMANHO_CHUNK):
    cron = Cronometros()
    vistos = set() 
    contagem_motivos = {motivo: 0 for motivo in MOTIVOS}
    vazios = {coluna: 0 for coluna in config.COLUNAS}
    total = validos = 0
    primeiro = True

    leitor = pd.read_csv(
        caminho_entrada, sep=";", dtype=str, keep_default_na=False, chunksize=tamanho_chunk
    )

    while True:
        with cron.trecho("leitura_csv"):
            try:
                parte = next(leitor)
            except StopIteration:
                break

        with cron.trecho("identificar_vazios"):
            em_branco = {c: parte[c].str.strip() == "" for c in config.COLUNAS}
            for coluna, mascara in em_branco.items():
                vazios[coluna] += int(mascara.sum())

        with cron.trecho("normalizar_documento"):
            documento = parte["documento"].str.replace(r"\D", "", regex=True)

        with cron.trecho("validar_documento"):
            documento_ok = documento.map(validar_documento).astype(bool)
            documento_vazio = documento == ""

        with cron.trecho("validar_cep"):
            cep_normalizado = parte["cep"].map(normalizar_cep)
            cep_ok = cep_normalizado.notna()

        with cron.trecho("normalizar_regiao"):
            regiao = mapear_unicos(parte["regiao_administrativa"], normalizar_bairro)

        with cron.trecho("identificar_duplicados"):
            ids = parte["id_cliente"]
            hashes = pd.util.hash_pandas_object(ids, index=False).to_numpy().tolist()
            repetido_antes = np.array([h in vistos for h in hashes], dtype=bool)
            repetido_no_chunk = ids.duplicated().to_numpy()
            duplicado = pd.Series(
                (repetido_antes | repetido_no_chunk) & ~em_branco["id_cliente"].to_numpy(),
                index=parte.index,
            )
            vistos.update(h for h, vazio in zip(hashes, em_branco["id_cliente"]) if not vazio)

        with cron.trecho("corrigir_inconsistencias"):
            nome = parte["nome"].str.strip().str.replace(r"\s+", " ", regex=True)
            endereco = parte["endereco"].str.strip().str.replace(r"\s+", " ", regex=True)
            cep_formatado = cep_normalizado.str[:5] + "-" + cep_normalizado.str[5:]

        with cron.trecho("preparar_armazenamento"):
            mascaras = {
                "id_vazio": em_branco["id_cliente"],
                "nome_vazio": em_branco["nome"],
                "documento_vazio": documento_vazio,
                "documento_invalido": ~documento_ok & ~documento_vazio,
                "cep_invalido": ~cep_ok,
                "duplicado": duplicado,
            }
            rejeitada = pd.Series(False, index=parte.index)
            motivos = pd.Series("", index=parte.index)

            for motivo, mascara in mascaras.items():
                contagem_motivos[motivo] += int(mascara.sum())
                rejeitada |= mascara
                motivos = motivos.mask(mascara, motivos + motivo + ";")

            limpo = pd.DataFrame({
                "id_cliente": ids,
                "nome": nome,
                "documento": documento,
                "cep": cep_formatado,
                "endereco": endereco,
                "regiao_administrativa": regiao.fillna(""),
            })[~rejeitada]

            limpo.to_csv(
                caminho_limpo, sep=";", index=False,
                mode="w" if primeiro else "a", header=primeiro, encoding="utf-8",
            )
            parte[rejeitada].assign(motivos=motivos[rejeitada]).to_csv(
                caminho_rejeitados, sep=";", index=False,
                mode="w" if primeiro else "a", header=primeiro, encoding="utf-8",
            )

        primeiro = False
        total += len(parte)
        validos += len(limpo)

    return {
        "total": total,
        "validos": validos,
        "rejeitados": total - validos,
        "motivos": contagem_motivos,
        "vazios": vazios,
        "duplicados": contagem_motivos["duplicado"],
        "tempos": dict(cron.tempos),
    }


def testar_transformacao(coletor, volume, caminho_entrada, caminho_limpo, caminho_rejeitados):
    with coletor.medir(volume, "transformacao", "completa") as m:
        resumo = transformar(caminho_entrada, caminho_limpo, caminho_rejeitados)
        m.registros = resumo["total"]
        m.rejeitados = resumo["rejeitados"]
        m.extras.update({f"motivo_{k}": v for k, v in resumo["motivos"].items()})
        m.extras.update({f"vazio_{k}": v for k, v in resumo["vazios"].items()})
        m.extras["validos"] = resumo["validos"]

    for operacao, segundos in resumo["tempos"].items():
        coletor.registrar(
            volume,
            "transformacao",
            operacao,
            tempo_s=segundos,
            registros=resumo["total"],
        )

    return resumo