def calcular_percentual(valor, total):
    if not total:
        return 0.0

    return round((valor / total) * 100, 2)


def calcular_metricas(df, checks):
    total_registros = len(df)

    nulos_por_coluna = checks.get("nulos", {})

    total_nulos = sum(nulos_por_coluna.values())
    total_duplicados = checks.get("duplicados", 0)
    total_vazios = checks.get("registros_vazios", 0)

    total_celulas = total_registros * len(nulos_por_coluna)

    return {
        "total_registros": total_registros,
        "total_nulos": total_nulos,
        "total_duplicados": total_duplicados,
        "total_registros_vazios": total_vazios,
        "percentual_nulos": calcular_percentual(total_nulos, total_celulas),
        "percentual_duplicados": calcular_percentual(
            total_duplicados, total_registros
        ),
        "nulos_por_coluna": {
            coluna: calcular_percentual(qtd, total_registros)
            for coluna, qtd in nulos_por_coluna.items()
        },
        "colunas_avaliadas": list(nulos_por_coluna.keys()),
        "nulos_por_coluna_quantidade": dict(nulos_por_coluna),
    }