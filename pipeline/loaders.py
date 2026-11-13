import pandas as pd

from database.connection import conectar


FORMATOS_DATA = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y")

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
    ON CONFLICT (id_cliente) DO NOTHING
"""


def converter_data(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    for formato in FORMATOS_DATA:
        try:
            return pd.to_datetime(texto, format=formato).date()
        except ValueError:
            continue

    return None


def para_banco(valor):
    if pd.isna(valor):
        return None

    if isinstance(valor, str):
        valor = valor.strip()

        if not valor:
            return None

    return valor


def carregar_csv(caminho):
    try:
        dados = pd.read_csv(caminho, sep=";", dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError:
        dados = pd.read_csv(caminho, sep=";", dtype=str, encoding="cp1252")

    dados["data_cadastro"] = dados["data_cadastro"].map(converter_data)

    return dados


def carregar_no_banco(dados):
    linhas = [
        (
            para_banco(linha["id_cliente"]),
            para_banco(linha["razao_social"]),
            para_banco(linha["cnpj"]),
            para_banco(linha["telefone"]),
            para_banco(linha["email"]),
            para_banco(linha["bairro_informado"]),
            para_banco(linha["cep"]),
            para_banco(linha["cidade"]),
            para_banco(linha["uf"]),
            para_banco(linha["data_cadastro"]),
            para_banco(linha["vendedor_responsavel"]),
        )
        for _, linha in dados.iterrows()
    ]

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