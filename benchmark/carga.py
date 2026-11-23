import pandas as pd

from benchmark import config


SQL_INSERIR = """
INSERT INTO benchmark_clientes
    (id_cliente, nome, documento, cep, endereco, regiao_administrativa)
VALUES (%s, %s, %s, %s, %s, %s)
"""

SQL_COPY = """
COPY benchmark_clientes
    (id_cliente, nome, documento, cep, endereco, regiao_administrativa)
FROM STDIN
"""


def conectar_banco():
    try:
        from database.connection import conectar
    except ImportError:
        raise RuntimeError("psycopg não está instalado. Rode: pip install 'psycopg[binary]'")

    return conectar()


def criar_tabela(conexao):
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_clientes (
            id_cliente            TEXT,
            nome                  TEXT,
            documento             TEXT,
            cep                   TEXT,
            endereco              TEXT,
            regiao_administrativa TEXT
        )
    """)
    cursor.execute("DROP INDEX IF EXISTS idx_benchmark_regiao")
    cursor.execute("TRUNCATE TABLE benchmark_clientes")
    conexao.commit()
    cursor.close()


def apagar_tabela(conexao):
    cursor = conexao.cursor()
    cursor.execute("DROP INDEX IF EXISTS idx_benchmark_regiao")
    cursor.execute("TRUNCATE TABLE benchmark_clientes")
    conexao.commit()
    cursor.close()


def ler_primeiras_linhas(caminho, quantidade):
    tabela = pd.read_csv(
        caminho, sep=";", dtype=str, keep_default_na=False, nrows=quantidade
    )

    return tabela.values.tolist()


def gravar_uma_por_vez_commit_em_cada(conexao, linhas):
    cursor = conexao.cursor()
    erros = 0

    for linha in linhas:
        try:
            cursor.execute(SQL_INSERIR, linha)
            conexao.commit()
        except Exception:
            conexao.rollback()
            erros = erros + 1

    cursor.close()

    return erros


def gravar_uma_por_vez_commit_no_fim(conexao, linhas):
    cursor = conexao.cursor()
    erros = 0

    try:
        for linha in linhas:
            cursor.execute(SQL_INSERIR, linha)

        conexao.commit()
    except Exception:
        conexao.rollback()
        erros = len(linhas)

    cursor.close()

    return erros


def gravar_em_lotes(conexao, caminho):
    cursor = conexao.cursor()
    erros = 0

    pedacos = pd.read_csv(
        caminho, sep=";", dtype=str, keep_default_na=False, chunksize=config.TAMANHO_LOTE
    )

    for pedaco in pedacos:
        linhas = pedaco.values.tolist()

        try:
            cursor.executemany(SQL_INSERIR, linhas)
            conexao.commit()
        except Exception:
            conexao.rollback()
            erros = erros + len(linhas)

    cursor.close()

    return erros


def gravar_com_copy(conexao, caminho, total_de_linhas):
    cursor = conexao.cursor()
    erros = 0

    pedacos = pd.read_csv(
        caminho, sep=";", dtype=str, keep_default_na=False, chunksize=config.TAMANHO_LOTE
    )

    try:
        with cursor.copy(SQL_COPY) as copia:
            for pedaco in pedacos:
                for linha in pedaco.values.tolist():
                    copia.write_row(linha)

        conexao.commit()
    except Exception:
        conexao.rollback()
        erros = total_de_linhas

    cursor.close()

    return erros


def testar_carga(coletor, volume, caminho_limpo, validos, limite_individual, avisar=print):
    conexao = conectar_banco()

    try:
        amostra = ler_primeiras_linhas(caminho_limpo, limite_individual)
        tamanho_amostra = len(amostra)

        criar_tabela(conexao)

        with coletor.medir(volume, "carga", "individual_commit_por_linha") as m:
            erros = gravar_uma_por_vez_commit_em_cada(conexao, amostra)
            m.registros = tamanho_amostra
            m.erros = erros
            m.extras["amostra"] = tamanho_amostra
            m.extras["volume_total"] = validos
            m.observacao = f"medido em {tamanho_amostra} linhas; o tempo total é estimado no relatório"

        avisar(f"      carga/individual_commit_por_linha: {tamanho_amostra - erros} gravados, {erros} erros")

        criar_tabela(conexao)

        with coletor.medir(volume, "carga", "individual_commit_unico") as m:
            erros = gravar_uma_por_vez_commit_no_fim(conexao, amostra)
            m.registros = tamanho_amostra
            m.erros = erros
            m.extras["amostra"] = tamanho_amostra
            m.extras["volume_total"] = validos
            m.observacao = f"medido em {tamanho_amostra} linhas; o tempo total é estimado no relatório"

        avisar(f"      carga/individual_commit_unico: {tamanho_amostra - erros} gravados, {erros} erros")

        criar_tabela(conexao)

        with coletor.medir(volume, "carga", "lote") as m:
            erros = gravar_em_lotes(conexao, caminho_limpo)
            m.registros = validos
            m.erros = erros

        avisar(f"      carga/lote: {validos - erros} gravados, {erros} erros")

        criar_tabela(conexao)

        with coletor.medir(volume, "carga", "copy") as m:
            erros = gravar_com_copy(conexao, caminho_limpo, validos)
            m.registros = validos
            m.erros = erros

        avisar(f"      carga/copy: {validos - erros} gravados, {erros} erros")

        testar_consultas(coletor, volume, conexao, validos)

    finally:
        apagar_tabela(conexao)
        conexao.close()


def testar_consultas(coletor, volume, conexao, validos):
    if validos == 0:
        return

    cursor = conexao.cursor()

    cursor.execute("SELECT id_cliente FROM benchmark_clientes ORDER BY id_cliente LIMIT 200")
    linhas_ids = cursor.fetchall()

    ids = []
    for linha in linhas_ids:
        ids.append(linha[0])

    cursor.execute("SELECT regiao_administrativa FROM benchmark_clientes LIMIT 1")
    regiao = cursor.fetchone()[0]

    with coletor.medir(volume, "consultas_banco", "contar_registros") as m:
        cursor.execute("SELECT COUNT(*) FROM benchmark_clientes")
        m.registros = cursor.fetchone()[0]

    with coletor.medir(volume, "consultas_banco", "busca_por_id") as m:
        for id_cliente in ids:
            cursor.execute("SELECT * FROM benchmark_clientes WHERE id_cliente = %s", (id_cliente,))
            cursor.fetchone()

        m.registros = len(ids)

    with coletor.medir(volume, "consultas_banco", "ler_100_mil_linhas") as m:
        cursor.execute("SELECT * FROM benchmark_clientes LIMIT 100000")
        m.registros = len(cursor.fetchall())

    with coletor.medir(volume, "consultas_banco", "filtro_regiao_sem_indice") as m:
        cursor.execute("SELECT * FROM benchmark_clientes WHERE regiao_administrativa = %s", (regiao,))
        m.registros = len(cursor.fetchall())

    with coletor.medir(volume, "consultas_banco", "criar_indice_regiao") as m:
        cursor.execute("CREATE INDEX idx_benchmark_regiao ON benchmark_clientes (regiao_administrativa)")
        conexao.commit()
        m.registros = validos

    with coletor.medir(volume, "consultas_banco", "filtro_regiao_com_indice") as m:
        cursor.execute("SELECT * FROM benchmark_clientes WHERE regiao_administrativa = %s", (regiao,))
        m.registros = len(cursor.fetchall())

    cursor.close()


def ler_lotes(caminho, tamanho):
    for pedaco in pd.read_csv(
        caminho, sep=";", dtype=str, keep_default_na=False, chunksize=tamanho
    ):
        yield list(pedaco.itertuples(index=False, name=None))