import json

import numpy as np
import pandas as pd

from benchmark import config


REGIOES = [
    "Plano Piloto", "Gama", "Taguatinga", "Brazlândia", "Sobradinho", "Planaltina",
    "Paranoá", "Núcleo Bandeirante", "Ceilândia", "Guará", "Cruzeiro", "Samambaia",
    "Santa Maria", "São Sebastião", "Recanto das Emas", "Lago Sul", "Riacho Fundo",
    "Lago Norte", "Candangolândia", "Águas Claras", "Riacho Fundo II", "Sudoeste",
    "Varjão", "Park Way", "Sobradinho II", "Jardim Botânico", "Itapoã", "Vicente Pires",
    "Fercal", "Sol Nascente", "Arniqueira",
]
TIPOS_NOME = [
    "Mercadinho", "Distribuidora", "Comercial", "Casa", "Armarinho", "Supermercado",
    "Padaria", "Farmácia", "Bazar", "Empório", "Mercearia", "Atacadão",
]
COMPLEMENTOS = [
    "Boa Vista", "São Judas", "Dois Irmãos", "Vale Verde", "Estrela Dourada",
    "Nova Aliança", "Central", "Popular", "do Cerrado", "Planalto", "Horizonte",
    "Santa Luzia", "União", "Sol Nascente", "Bom Preço",
]
SUFIXOS = ["", "", "LTDA", "ME", "EIRELI", "& Cia", "S/A"]
TIPOS_VIA = ["SQN", "SQS", "CLN", "CLS", "QNM", "QNN", "QNG", "QI", "QS", "EQNP"]
CEPS_RUINS = ["123", "ABCDE-123", "7100-000", "000000000", "71.000-000", ""]

DEFEITOS = {
    "documento_invalido": 0.03,
    "documento_vazio": 0.01,
    "cep_invalido": 0.03,
    "nome_vazio": 0.01,
    "id_duplicado": 0.02,
}

PESOS_CNPJ_1 = np.array([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
PESOS_CNPJ_2 = np.array([6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
PESOS_CPF_1 = np.arange(10, 1, -1)
PESOS_CPF_2 = np.arange(11, 1, -1)


def digito_verificador(digitos, pesos):
    resto = (digitos @ pesos) % 11

    return np.where(resto < 2, 0, 11 - resto)


def como_numero(digitos):
    """Junta uma matriz de dígitos (n, k) em um número inteiro por linha."""
    potencias = 10 ** np.arange(digitos.shape[1] - 1, -1, -1, dtype=np.int64)

    return digitos @ potencias


def gerar_cnpjs(n, rng):
    base = rng.integers(0, 10, (n, 12))
    base[:, 0] = rng.integers(1, 10, n)
    base[:, 8:] = [0, 0, 0, 1]  # filial 0001

    d1 = digito_verificador(base, PESOS_CNPJ_1)
    com_d1 = np.column_stack([base, d1])
    d2 = digito_verificador(com_d1, PESOS_CNPJ_2)

    return como_numero(np.column_stack([com_d1, d2]))


def gerar_cpfs(n, rng):
    base = rng.integers(0, 10, (n, 9))
    base[:, 0] = rng.integers(1, 10, n)

    d1 = digito_verificador(base, PESOS_CPF_1)
    com_d1 = np.column_stack([base, d1])
    d2 = digito_verificador(com_d1, PESOS_CPF_2)

    return como_numero(np.column_stack([com_d1, d2]))


def formatar_cnpj(s):
    return s.str[:2] + "." + s.str[2:5] + "." + s.str[5:8] + "/" + s.str[8:12] + "-" + s.str[12:]


def formatar_cpf(s):
    return s.str[:3] + "." + s.str[3:6] + "." + s.str[6:9] + "-" + s.str[9:]


def gerar_documentos(n, rng, invalidos):
    """Mistura de 80% CNPJ e 20% CPF, metade formatados (com pontos) e metade só dígitos."""
    eh_cnpj = rng.random(n) < 0.8
    numeros = np.zeros(n, dtype=np.int64)
    numeros[eh_cnpj] = gerar_cnpjs(int(eh_cnpj.sum()), rng)
    numeros[~eh_cnpj] = gerar_cpfs(int((~eh_cnpj).sum()), rng)

    ultimo = numeros % 10
    numeros = np.where(invalidos, numeros - ultimo + (ultimo + 1) % 10, numeros)

    texto = pd.Series(numeros).astype(str)
    texto = texto.where(~eh_cnpj, texto.str.zfill(14))
    texto = texto.where(eh_cnpj, texto.str.zfill(11))

    formatar = rng.random(n) < 0.5
    formatado = texto.where(~eh_cnpj, formatar_cnpj(texto))
    formatado = formatado.where(eh_cnpj, formatar_cpf(texto))

    return texto.where(~formatar, formatado)


def gerar_regioes(n, rng):
    regiao = pd.Series(rng.choice(REGIOES, n))
    sorteio = rng.random(n)

    regiao = regiao.where(sorteio >= 0.25, regiao.str.upper())
    regiao = regiao.where((sorteio < 0.25) | (sorteio >= 0.40), regiao + " - DF")
    regiao = regiao.where((sorteio < 0.40) | (sorteio >= 0.50), regiao + "/DF")

    return regiao


def gerar_chunk(inicio, quantidade, rng):
    n = quantidade
    numeros_id = np.arange(inicio, inicio + n)
    defeito = {nome: rng.random(n) < p for nome, p in DEFEITOS.items()}

    duplicar = defeito["id_duplicado"] & (numeros_id > 0)
    numeros_id = numeros_id.copy()
    numeros_id[duplicar] = (rng.random(int(duplicar.sum())) * numeros_id[duplicar]).astype(np.int64)
    ids = config.PREFIXO_ID + pd.Series(numeros_id).astype(str).str.zfill(9)

    nome = (
        pd.Series(rng.choice(TIPOS_NOME, n)) + " "
        + pd.Series(rng.choice(COMPLEMENTOS, n)) + " "
        + pd.Series(rng.choice(SUFIXOS, n))
    ).str.strip()
    nome = nome.where(~defeito["nome_vazio"], "")

    documento = gerar_documentos(n, rng, defeito["documento_invalido"])
    documento = documento.where(~defeito["documento_vazio"], "")

    cep = pd.Series(rng.integers(70_000_000, 73_700_000, n)).astype(str).str.zfill(8)
    cep = cep.where(rng.random(n) >= 0.5, cep.str[:5] + "-" + cep.str[5:])
    cep = cep.where(~defeito["cep_invalido"], pd.Series(rng.choice(CEPS_RUINS, n)))

    endereco = (
        pd.Series(rng.choice(TIPOS_VIA, n)) + " "
        + pd.Series(rng.integers(1, 917, n)).astype(str) + " Bloco "
        + pd.Series(rng.choice(list("ABCDEFGH"), n)) + " Casa "
        + pd.Series(rng.integers(1, 80, n)).astype(str)
    )

    tabela = pd.DataFrame({
        "id_cliente": ids,
        "nome": nome,
        "documento": documento,
        "cep": cep,
        "endereco": endereco,
        "regiao_administrativa": gerar_regioes(n, rng),
    })

    return tabela, {nome: int(mascara.sum()) for nome, mascara in defeito.items()}


def caminho_meta(caminho):
    return caminho.with_suffix(".meta.json")


def arquivo_reaproveitavel(caminho, volume, semente):
    meta = caminho_meta(caminho)

    if not caminho.exists() or not meta.exists():
        return False

    try:
        dados = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False

    return dados.get("volume") == volume and dados.get("semente") == semente


def gerar_csv(volume, caminho, semente=config.SEMENTE, tamanho_chunk=200_000):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(semente)
    injetados = {nome: 0 for nome in DEFEITOS}
    escritas = 0

    while escritas < volume:
        quantidade = min(tamanho_chunk, volume - escritas)
        tabela, contagem = gerar_chunk(escritas, quantidade, rng)

        tabela.to_csv(
            caminho,
            sep=";",
            index=False,
            mode="w" if escritas == 0 else "a",
            header=escritas == 0,
            encoding="utf-8",
        )

        for nome, qtd in contagem.items():
            injetados[nome] += qtd

        escritas += quantidade

    meta = {
        "volume": volume,
        "semente": semente,
        "defeitos_injetados": injetados,
        "tamanho_mb": caminho.stat().st_size / (1024 * 1024),
    }
    caminho_meta(caminho).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return meta


def ler_meta(caminho):
    try:
        return json.loads(caminho_meta(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}