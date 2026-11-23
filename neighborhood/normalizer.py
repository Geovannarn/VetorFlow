import re
import unicodedata


UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

SUFIXO_UF = re.compile(r"\s*[-/]\s*([A-Za-z]{2})$")

PREPOSICOES = {"de", "da", "do", "das", "dos", "e"}
ALGARISMOS_ROMANOS = re.compile(r"^(i{1,3}|iv|v|vi{1,3}|ix|x)$")


def remover_uf(bairro):
    achado = SUFIXO_UF.search(bairro)

    if achado and achado.group(1).upper() in UFS:
        return bairro[:achado.start()]

    return bairro


def remover_acentos(texto):
    texto = unicodedata.normalize("NFKD", texto)

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )


def limpar_bairro(bairro):
    if not isinstance(bairro, str):
        return None

    bairro = unicodedata.normalize("NFC", bairro).strip()

    if not bairro:
        return None

    dentro_parenteses = re.search(r"\(([^)]+)\)", bairro)

    if dentro_parenteses:
        bairro = dentro_parenteses.group(1)

    bairro = remover_uf(bairro)
    bairro = re.sub(r"[^\w\s]", " ", bairro)
    bairro = re.sub(r"\s+", " ", bairro).strip()

    return bairro or None


def normalizar_bairro(bairro):
    limpo = limpar_bairro(bairro)

    if limpo is None:
        return None

    return remover_acentos(limpo).casefold() or None


def formatar_para_exibicao(nome):
    """'AGUAS CLARAS' / 'águas claras' -> 'Aguas Claras' / 'Águas Claras'."""
    palavras = nome.lower().split()
    resultado = []

    for posicao, palavra in enumerate(palavras):
        if posicao > 0 and palavra in PREPOSICOES:
            resultado.append(palavra)
        elif ALGARISMOS_ROMANOS.match(palavra):
            resultado.append(palavra.upper())
        else:
            resultado.append(palavra.capitalize())

    return " ".join(resultado)