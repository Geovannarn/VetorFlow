import pandas as pd


def verificar_colunas_obrigatorias(df, colunas):
    return [coluna for coluna in colunas if coluna not in df.columns]


def verificar_nulos(df, colunas):
    resultado = {}

    for coluna in colunas:
        if coluna in df.columns:
            resultado[coluna] = int(df[coluna].isna().sum())

    return resultado


def verificar_duplicados(df):
    return int(df.duplicated().sum())


def verificar_registros_vazios(df):
    return int(df.dropna(how="all").shape[0] == 0)


def executar_checks(df, colunas_obrigatorias):
    return {
        "colunas_ausentes": verificar_colunas_obrigatorias(
            df, colunas_obrigatorias
        ),
        "nulos": verificar_nulos(df, colunas_obrigatorias),
        "duplicados": verificar_duplicados(df),
        "possui_dados": not df.empty,
    }