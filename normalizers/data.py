from datetime import datetime


FORMATOS_DATA = (
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
)


def normalizar_data(data):
    if data is None:
        return None

    if not isinstance(data, str):
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

    return None