from datetime import datetime
import re


FORMATOS_DATA = (
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
)

MESES_INGLES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def normalizar_data(data):
    if data is None or not isinstance(data, str):
        return None

    data = data.strip()

    if not data:
        return None

    for formato in FORMATOS_DATA:
        try:
            resultado = datetime.strptime(data, formato)
            return resultado.strftime("%Y-%m-%d")
        except ValueError:
            continue

    correspondencia = re.fullmatch(
        r"([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})",
        data
    )

    if correspondencia:
        mes_texto, dia, ano = correspondencia.groups()

        mes = MESES_INGLES.get(mes_texto.casefold())

        if mes is None:
            return None

        try:
            resultado = datetime(
                int(ano),
                mes,
                int(dia)
            )

            return resultado.strftime("%Y-%m-%d")

        except ValueError:
            return None

    return None
