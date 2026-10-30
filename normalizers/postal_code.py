import re
from typing import Optional

CEP_REGEX = re.compile(r"([0-9]{5})-?([0-9]{3})")


def normalizar_cep(cep: object) -> Optional[str]:
    if cep is None or isinstance(cep, bool):
        return None

    if isinstance(cep, int):
        if cep < 0:
            return None
        cep = f"{cep:08d}"
    else:
        cep = str(cep).strip()

    resultado = CEP_REGEX.fullmatch(cep)

    if resultado is None:
        return None

    return "".join(resultado.groups())


def verifica_cep(cep: object) -> bool:
    return normalizar_cep(cep) is not None


def formatar_cep(cep: object) -> Optional[str]:
    normalizado = normalizar_cep(cep)

    if normalizado is None:
        return None

    return f"{normalizado[:5]}-{normalizado[5:]}"
