def calcular_percentual(valor, total):
    if total == 0:
        return 0.0

    return round((valor / total) * 100, 2)


def calcular_metricas(df, checks):
    total_registros = len(df)

    total_nulos = sum(checks["nulos"].values())
    total_duplicados = checks["duplicados"]

    return {
        "total_registros": total_registros,
        "total_nulos": total_nulos,
        "total_duplicados": total_duplicados,
        "percentual_nulos": calcular_percentual(
            total_nulos, total_registros
        ),
        "percentual_duplicados": calcular_percentual(
            total_duplicados, total_registros
        ),
    }