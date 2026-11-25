def verificar_colunas_obrigatorias(df, colunas):
    return [coluna for coluna in colunas if coluna not in df.columns]


def _mascara_vazios(serie):
    vazios = serie.isna()

    if serie.dtype == object or str(serie.dtype) in ("string", "str"):
        em_branco = serie.astype("string").str.strip().eq("").fillna(False)
        vazios = vazios | em_branco.astype(bool)

    return vazios


def verificar_nulos(df, colunas):
    resultado = {}

    for coluna in colunas:
        if coluna not in df.columns:
            continue

        resultado[coluna] = int(_mascara_vazios(df[coluna]).sum())

    return resultado


def verificar_duplicados(df, colunas_chave=None):
    if colunas_chave:
        colunas_chave = [c for c in colunas_chave if c in df.columns]

    return int(df.duplicated(subset=colunas_chave or None).sum())


def verificar_registros_vazios(df):
    if df.empty:
        return 0

    vazios = df.apply(_mascara_vazios)

    return int(vazios.all(axis=1).sum())


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