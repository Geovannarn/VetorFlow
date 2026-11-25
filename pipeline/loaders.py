from pathlib import Path
from datetime import datetime

import pandas as pd

from audit.logger import auditar_transformacao
from database.connection import conectar
from integrations.brasilapi import consultar_brasilapi
from integrations.viacep import consultar_viacep
from neighborhood.resolver import resolver_bairro
from normalizers.cnpj import normalizar_cnpj, validar_cnpj
from normalizers.data import normalizar_data
from normalizers.email import normalizar_email, validar_email
from normalizers.postal_code import normalizar_cep
from normalizers.telefone import normalizar_telefone
from pipeline.checks import executar_checks
from pipeline.metrics import calcular_metricas

try:
    from integrations.cache import armazenar_cache, buscar_cache
except ImportError:
    from integrations.cahe import armazenar_cache, buscar_cache


COLUNAS_CSV = [
    "id_cliente",
    "razao_social",
    "cnpj",
    "telefone",
    "email",
    "bairro_informado",
    "cep",
    "cidade",
    "uf",
    "data_cadastro",
    "vendedor_responsavel",
]

COLUNAS_OBRIGATORIAS = [
    "id_cliente",
    "razao_social",
    "cnpj",
    "cep",
]

COLUNAS_BANCO = [
    "id_cliente",
    "razao_social",
    "cnpj",
    "telefone",
    "email",
    "bairro",
    "cep",
    "cidade",
    "uf",
    "cadastro",
    "responsavel",
]

SQL_INSERIR = """
    INSERT INTO usuarios (
        id_cliente,
        razao_social,
        cnpj,
        telefone,
        email,
        bairro,
        cep,
        cidade,
        uf,
        cadastro,
        responsavel
    )
    VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s
    )
    ON CONFLICT (id_cliente) DO UPDATE SET
        razao_social = COALESCE(EXCLUDED.razao_social, usuarios.razao_social),
        cnpj = COALESCE(EXCLUDED.cnpj, usuarios.cnpj),
        telefone = COALESCE(EXCLUDED.telefone, usuarios.telefone),
        email = COALESCE(EXCLUDED.email, usuarios.email),
        bairro = COALESCE(EXCLUDED.bairro, usuarios.bairro),
        cep = COALESCE(EXCLUDED.cep, usuarios.cep),
        cidade = COALESCE(EXCLUDED.cidade, usuarios.cidade),
        uf = COALESCE(EXCLUDED.uf, usuarios.uf),
        cadastro = COALESCE(EXCLUDED.cadastro, usuarios.cadastro),
        responsavel = COALESCE(EXCLUDED.responsavel, usuarios.responsavel)
"""

CEP_ZERADO = "00000000"

FONTE_REGRAS = "regras-de-tratamento.md"
FONTE_CEP = "ViaCEP/BrasilAPI (cache local)"

CSV_PADRAO = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "clientes_distribuidora_vetor.csv"
)


def converter_data(valor):
    if pd.isna(valor):
        return None

    resultado = normalizar_data(str(valor))

    if resultado is None:
        return None

    return datetime.strptime(resultado, "%Y-%m-%d").date()


def para_banco(valor):
    if pd.isna(valor):
        return None

    if isinstance(valor, str):
        valor = valor.strip()

        if not valor:
            return None

    return valor


def limpar_texto(valor):
    if pd.isna(valor):
        return None

    texto = " ".join(str(valor).split())

    if texto == "":
        return None

    return texto


def _valor_ou_none(valor):
    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None

    return valor


def auditar_campo(
    campo,
    original,
    tratado,
    criterio,
    id_registro,
    fonte=FONTE_REGRAS,
    etapa="transformacao",
):
    original = _valor_ou_none(original)

    if original is None and tratado is None:
        return

    if (
        original is not None
        and tratado is not None
        and str(original) == str(tratado)
    ):
        return

    auditar_transformacao(
        campo=campo,
        valor_original=original,
        valor_tratado=tratado,
        criterio=criterio,
        fonte=fonte,
        id_registro=id_registro,
        etapa=etapa,
    )


def carregar_csv(caminho):
    try:
        dados = pd.read_csv(
            caminho,
            sep=";",
            dtype=str,
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        dados = pd.read_csv(
            caminho,
            sep=";",
            dtype=str,
            encoding="cp1252"
        )

    if "data_cadastro" in dados.columns:
        dados["data_cadastro_original"] = dados["data_cadastro"]

        dados["data_cadastro"] = dados["data_cadastro"].map(
            converter_data
        )

    return dados


def padronizar_endereco(resultado):
    return {
        "bairro": resultado.get("bairro") or resultado.get("neighborhood"),
        "cidade": (
            resultado.get("localidade")
            or resultado.get("city")
            or resultado.get("cidade")
        ),
        "uf": resultado.get("uf") or resultado.get("state"),
    }


def consultar_endereco(cep):
    guardado = buscar_cache(cep)

    if isinstance(guardado, dict):
        return padronizar_endereco(guardado)

    resultado = consultar_viacep(cep)

    if resultado is None:
        resultado = consultar_brasilapi(cep)

    if resultado is None:
        return None

    endereco = padronizar_endereco(resultado)
    armazenar_cache(cep, endereco)

    return endereco


def buscar_enderecos(ceps, contagem):
    enderecos = {}
    consultados = set()

    for valor in ceps.unique():
        cep = normalizar_cep(valor)

        if cep is None or cep == CEP_ZERADO or cep in consultados:
            continue

        consultados.add(cep)
        contagem["cep_consultados"] += 1

        endereco = consultar_endereco(cep)

        if endereco is None:
            contagem["cep_nao_encontrados"] += 1
        else:
            enderecos[cep] = endereco

    return enderecos


def tratar_telefone(valor):
    digitos = normalizar_telefone(valor)

    if digitos is None:
        return None

    if len(digitos) > 11 and digitos.startswith("55"):
        digitos = digitos[2:]

    if len(digitos) not in (10, 11):
        return None

    return "+55" + digitos


def nova_contagem():
    return {
        "lidos": 0,
        "aceitos": 0,
        "rejeitados": 0,
        "cnpj_formato_invalido": 0,
        "cnpj_digito_invalido": 0,
        "telefone_invalido": 0,
        "email_invalido": 0,
        "cep_invalido": 0,
        "cep_consultados": 0,
        "cep_nao_encontrados": 0,
        "cidade_preenchida": 0,
        "uf_preenchida": 0,
        "criterios_bairro": {},
        "inseridos": 0,
    }


def tratar_linha(linha, id_cliente, razao_social, enderecos, contagem):
    auditar_campo(
        "razao_social",
        linha["razao_social"],
        razao_social,
        "Colapso de espaços repetidos",
        id_cliente,
    )

    cnpj = normalizar_cnpj(linha["cnpj"])

    if cnpj is None:
        if limpar_texto(linha["cnpj"]) is not None:
            contagem["cnpj_formato_invalido"] += 1

        auditar_campo(
            "cnpj",
            linha["cnpj"],
            None,
            "Descartado: não possui 14 dígitos após remoção de máscara",
            id_cliente,
        )
    else:
        if not validar_cnpj(cnpj):
            contagem["cnpj_digito_invalido"] += 1
            criterio_cnpj = (
                "Remoção de máscara (14 dígitos); dígito verificador inválido, "
                "valor mantido e sinalizado sem descartar o registro"
            )
        else:
            criterio_cnpj = (
                "Remoção de máscara (14 dígitos); dígitos verificadores válidos"
            )

        auditar_campo("cnpj", linha["cnpj"], cnpj, criterio_cnpj, id_cliente)

    telefone = tratar_telefone(linha["telefone"])

    if telefone is None and limpar_texto(linha["telefone"]) is not None:
        contagem["telefone_invalido"] += 1

    if telefone is None:
        auditar_campo(
            "telefone",
            linha["telefone"],
            None,
            "Descartado: quantidade de dígitos inválida (esperado 10 ou 11, após DDI 55)",
            id_cliente,
        )
    else:
        auditar_campo(
            "telefone",
            linha["telefone"],
            telefone,
            "Remoção de máscara e DDI 55; padronizado como +55 seguido dos dígitos",
            id_cliente,
        )

    email = normalizar_email(linha["email"])

    if email is not None and not validar_email(email):
        email = None

    if email is None and limpar_texto(linha["email"]) is not None:
        contagem["email_invalido"] += 1

    if email is None:
        auditar_campo(
            "email",
            linha["email"],
            None,
            "Descartado: e-mail em formato inválido",
            id_cliente,
        )
    else:
        auditar_campo(
            "email",
            linha["email"],
            email,
            "Padronização: remoção de espaços e conversão para minúsculas",
            id_cliente,
        )

    cep = normalizar_cep(linha["cep"])
    cep_zerado = cep == CEP_ZERADO

    if cep_zerado:
        cep = None

    if cep is None and limpar_texto(linha["cep"]) is not None:
        contagem["cep_invalido"] += 1

    if cep_zerado:
        auditar_campo(
            "cep",
            linha["cep"],
            None,
            "Descartado: CEP zerado (00000000) tratado como ausente",
            id_cliente,
        )
    elif cep is None:
        auditar_campo(
            "cep",
            linha["cep"],
            None,
            "Descartado: formato inválido (esperado 8 dígitos)",
            id_cliente,
        )
    else:
        auditar_campo(
            "cep",
            linha["cep"],
            cep,
            "Remoção do hífen; padronizado em 8 dígitos",
            id_cliente,
        )

    endereco = enderecos.get(cep, {})

    bairro, criterio = resolver_bairro(
        linha["bairro_informado"],
        endereco.get("bairro"),
        id_registro=id_cliente,
    )

    contagem["criterios_bairro"][criterio] = (
        contagem["criterios_bairro"].get(criterio, 0) + 1
    )

    cidade = limpar_texto(linha["cidade"])

    if cidade is None and endereco.get("cidade"):
        cidade = endereco["cidade"]
        contagem["cidade_preenchida"] += 1

        auditar_campo(
            "cidade",
            None,
            cidade,
            "Preenchida pela consulta de CEP (cidade ausente no cadastro)",
            id_cliente,
            fonte=FONTE_CEP,
            etapa="enriquecimento",
        )
    else:
        auditar_campo(
            "cidade",
            linha["cidade"],
            cidade,
            "Colapso de espaços repetidos",
            id_cliente,
        )

    uf = limpar_texto(linha["uf"])

    if uf is not None:
        uf = uf.upper()

    if uf is None and endereco.get("uf"):
        uf = endereco["uf"].upper()
        contagem["uf_preenchida"] += 1

        auditar_campo(
            "uf",
            None,
            uf,
            "Preenchida pela consulta de CEP (UF ausente no cadastro)",
            id_cliente,
            fonte=FONTE_CEP,
            etapa="enriquecimento",
        )
    else:
        auditar_campo(
            "uf",
            linha["uf"],
            uf,
            "Conversão para maiúsculas e colapso de espaços",
            id_cliente,
        )

    cadastro = para_banco(linha["data_cadastro"])
    data_original = linha.get("data_cadastro_original", linha["data_cadastro"])

    if cadastro is None:
        auditar_campo(
            "data_cadastro",
            data_original,
            None,
            "Descartado: formato de data não reconhecido",
            id_cliente,
        )
    else:
        auditar_campo(
            "data_cadastro",
            data_original,
            cadastro,
            "Conversão para AAAA-MM-DD (formatos aceitos: dd/mm/aaaa, "
            "aaaa-mm-dd, dd-mm-aaaa com dia primeiro, e 'Mês dd, aaaa')",
            id_cliente,
        )

    responsavel = limpar_texto(linha["vendedor_responsavel"])

    auditar_campo(
        "responsavel",
        linha["vendedor_responsavel"],
        responsavel,
        "Colapso de espaços repetidos",
        id_cliente,
    )

    return {
        "id_cliente": id_cliente,
        "razao_social": razao_social,
        "cnpj": cnpj,
        "telefone": telefone,
        "email": email,
        "bairro": bairro,
        "cep": cep,
        "cidade": cidade,
        "uf": uf,
        "cadastro": cadastro,
        "responsavel": responsavel,
    }


def tratar_dados(dados, consultar_api=True):
    contagem = nova_contagem()
    contagem["lidos"] = len(dados)

    enderecos = {}

    if consultar_api:
        enderecos = buscar_enderecos(dados["cep"], contagem)

    ids_vistos = set()
    aceitos = []
    rejeitados = []

    for _, linha in dados.iterrows():
        id_cliente = limpar_texto(linha["id_cliente"])
        razao_social = limpar_texto(linha["razao_social"])
        motivo = None

        if id_cliente is None:
            motivo = "id_cliente vazio"
        elif razao_social is None:
            motivo = "razao_social vazia"
        elif id_cliente in ids_vistos:
            motivo = "id_cliente duplicado"

        if motivo is not None:
            registro = linha.to_dict()
            registro["motivo"] = motivo
            rejeitados.append(registro)
            contagem["rejeitados"] += 1

            auditar_transformacao(
                campo="registro",
                valor_original=id_cliente or "(sem id_cliente)",
                valor_tratado=None,
                criterio=f"Registro rejeitado: {motivo}",
                fonte=FONTE_REGRAS,
                id_registro=id_cliente,
                etapa="rejeicao",
            )
            continue

        ids_vistos.add(id_cliente)

        aceitos.append(
            tratar_linha(
                linha,
                id_cliente,
                razao_social,
                enderecos,
                contagem
            )
        )

        contagem["aceitos"] += 1

    return (
        pd.DataFrame(aceitos, columns=COLUNAS_BANCO),
        pd.DataFrame(rejeitados),
        contagem
    )


def carregar_no_banco(tratados):
    linhas = []

    for _, linha in tratados.iterrows():
        valores = []

        for coluna in COLUNAS_BANCO:
            valores.append(para_banco(linha[coluna]))

        linhas.append(tuple(valores))

    conexao = conectar()

    try:
        with conexao.cursor() as cursor:
            cursor.executemany(SQL_INSERIR, linhas)
            inseridos = cursor.rowcount

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()

    return inseridos


def processar_csv(caminho, consultar_api=True, gravar=True):
    dados = carregar_csv(caminho)

    ausentes = [
        coluna
        for coluna in COLUNAS_CSV
        if coluna not in dados.columns
    ]

    if ausentes:
        raise ValueError(
            "Colunas ausentes no CSV: " + ", ".join(ausentes)
        )

    checks = executar_checks(
        dados,
        COLUNAS_OBRIGATORIAS,
        ["id_cliente"]
    )

    metricas = calcular_metricas(dados, checks)

    tratados, rejeitados, contagem = tratar_dados(
        dados,
        consultar_api
    )

    if gravar and len(tratados) > 0:
        contagem["inseridos"] = carregar_no_banco(tratados)

    return {
        "checks": checks,
        "metricas": metricas,
        "tratamento": contagem,
        "tratados": tratados,
        "rejeitados": rejeitados,
    }


def mostrar_resumo(resultado):
    metricas = resultado["metricas"]
    tratamento = resultado["tratamento"]

    print("QUALIDADE DA BASE DE ENTRADA")
    print("  registros:", metricas["total_registros"])
    print(
        "  nulos:",
        metricas["total_nulos"],
        f"({metricas['percentual_nulos']}%)"
    )
    print(
        "  duplicados:",
        metricas["total_duplicados"],
        f"({metricas['percentual_duplicados']}%)"
    )

    print("\nTRATAMENTO")
    print("  aceitos:", tratamento["aceitos"])
    print("  rejeitados:", tratamento["rejeitados"])
    print(
        "  CNPJ com formato inválido:",
        tratamento["cnpj_formato_invalido"]
    )
    print(
        "  CNPJ com dígito verificador inválido:",
        tratamento["cnpj_digito_invalido"]
    )
    print("  telefones inválidos:", tratamento["telefone_invalido"])
    print("  e-mails inválidos:", tratamento["email_invalido"])
    print("  CEPs inválidos:", tratamento["cep_invalido"])

    print("\nENRIQUECIMENTO POR CEP")
    print("  CEPs consultados:", tratamento["cep_consultados"])
    print(
        "  CEPs não encontrados:",
        tratamento["cep_nao_encontrados"]
    )
    print(
        "  cidades preenchidas:",
        tratamento["cidade_preenchida"]
    )
    print("  UFs preenchidas:", tratamento["uf_preenchida"])

    print("\nRESOLUÇÃO DE BAIRROS")

    for criterio, quantidade in tratamento["criterios_bairro"].items():
        print(f"  {criterio}: {quantidade}")

    print("\nBANCO")
    print("  inseridos:", tratamento["inseridos"])


if __name__ == "__main__":
    mostrar_resumo(processar_csv(CSV_PADRAO))