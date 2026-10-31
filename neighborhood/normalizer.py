import re
import unicodedata


def normalizar_bairro(bairro):
    if not isinstance(bairro, str):
        return None

    bairro = bairro.strip()

    if not bairro:
        return None

    bairro = unicodedata.normalize("NFKD", bairro)

    bairro = "".join(
        caractere
        for caractere in bairro
        if not unicodedata.combining(caractere)
    )

    bairro = re.sub(r"\s+", " ", bairro)

    return bairro.lower()