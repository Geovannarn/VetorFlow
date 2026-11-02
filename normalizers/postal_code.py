import re


_CEP_REGEX = re.compile(r"([0-9]{5})-?([0-9]{3})")


def normalizar_cep(cep):
    if cep is None:
        return None

    if isinstance(cep, bool):
        return None

    if isinstance(cep, int):
        if cep < 0:
            return None

        cep = f"{cep:08d}"

    elif isinstance(cep, str):
        cep = cep.strip()

    else:
        return None

    resultado = _CEP_REGEX.fullmatch(cep)

    if not resultado:
        return None

    return resultado.group(1) + resultado.group(2)


def validar_cep(cep):
    return normalizar_cep(cep) is not None


def formatar_cep(cep):
    cep_normalizado = normalizar_cep(cep)

    if cep_normalizado is None:
        return None

    return f"{cep_normalizado[:5]}-{cep_normalizado[5:]}"


def exigir_cep(cep):
    cep_normalizado = normalizar_cep(cep)

    if cep_normalizado is None:
        raise ValueError("CEP inválido.")

    return cep_normalizado