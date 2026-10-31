import re
import unicodedata


def normalizar_texto(texto):
    if not isinstance(texto, str):
        return None

    texto = texto.strip()

    if not texto:
        return None

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def normalizar_texto_minusculo(texto):
    texto = normalizar_texto(texto)

    if texto is None:
        return None

    return texto.lower()