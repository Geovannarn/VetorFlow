import re


def normalizar_telefone(telefone):
    if telefone is None:
        return None

    if not isinstance(telefone, (str, int)):
        return None

    telefone = str(telefone).strip()

    telefone = re.sub(r"\D", "", telefone)

    if not telefone:
        return None

    return telefone


def validar_telefone(telefone):
    telefone = normalizar_telefone(telefone)

    if telefone is None:
        return False

    return len(telefone) in (10, 11)