def verificar_colunas_obrigatorias(df, colunas):
    return [coluna for coluna in colunas if coluna not in df.columns]


def verificar_nulos(df, colunas):
    resultado = {}

    for coluna in colunas:
        if coluna not in df.columns:
            continue

        serie = df[coluna]
        vazios = serie.isna()

        if serie.dtype == object or str(serie.dtype) in ("string", "str"):
            vazios = vazios | serie.astype("string").str.strip().eq("").fillna(False)

        resultado[coluna] = int(vazios.sum())

    return resultado


def verificar_duplicados(df, colunas_chave=None):
    if colunas_chave:
        colunas_chave = [c for c in colunas_chave if c in df.columns]

    return int(df.duplicated(subset=colunas_chave or None).sum())


def verificar_registros_vazios(df):
    return int(df.isna().all(axis=1).sum())


def executar_checks(df, colunas_obrigatorias, colunas_chave=None):
    return {
        "colunas_ausentes": verificar_colunas_obrigatorias(
            df, colunas_obrigatorias
        ),
        "nulos": verificar_nulos(df, colunas_obrigatorias),
        "duplicados": verificar_duplicados(df, colunas_chave),
        "registros_vazios": verificar_registros_vazios(df),
        "possui_dados": not df.empty,
    }