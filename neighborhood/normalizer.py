import re
import unicodedata


UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

SUFIXO_UF = re.compile(r"\s*[-/]\s*([A-Za-z]{2})$")


def remover_uf(bairro):
    achado = SUFIXO_UF.search(bairro)

    if achado and achado.group(1).upper() in UFS:
        return bairro[:achado.start()]

    return bairro


def normalizar_bairro(bairro):
    if not isinstance(bairro, str):
        return None

    bairro = bairro.strip()

    if not bairro:
        return None

    dentro_parenteses = re.search(r"\(([^)]+)\)", bairro)

    if dentro_parenteses:
        bairro = dentro_parenteses.group(1)

    bairro = remover_uf(bairro)

    bairro = unicodedata.normalize("NFKD", bairro)

    bairro = "".join(
        caractere
        for caractere in bairro
        if not unicodedata.combining(caractere)
    )

    bairro = re.sub(r"[^\w\s]", " ", bairro)
    bairro = re.sub(r"\s+", " ", bairro).strip()

    return bairro.casefold() or None