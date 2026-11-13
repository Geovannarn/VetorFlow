import re
import unicodedata


def normalizar_bairro(bairro):
    if not isinstance(bairro, str):
        return None

    bairro = bairro.strip()

    if not bairro:
        return None

    dentro_parenteses = re.search(r"\(([^)]+)\)", bairro)

    if dentro_parenteses:
        bairro = dentro_parenteses.group(1)

    bairro = re.sub(r"\s*[-/]\s*[A-Za-z]{2}$", "", bairro)

    bairro = unicodedata.normalize("NFKD", bairro)

    bairro = "".join(
        caractere
        for caractere in bairro
        if not unicodedata.combining(caractere)
    )

    bairro = re.sub(r"[^\w\s]", " ", bairro)
    bairro = re.sub(r"\s+", " ", bairro).strip()

    return bairro.casefold() or None