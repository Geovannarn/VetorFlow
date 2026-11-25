import re
import unicodedata

from audit.logger import auditar_transformacao


UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

SUFIXO_UF = re.compile(r"\s*[-/]\s*([A-Za-z]{2})$")

PREPOSICOES = {"de", "da", "do", "das", "dos", "e"}
ALGARISMOS_ROMANOS = re.compile(r"^(i{1,3}|iv|v|vi{1,3}|ix|x)$")

CAMPO = "bairro"
FONTE = "regras-de-tratamento.md"


def _auditar(valor_original, valor_tratado, criterio, id_registro=None, etapa="transformacao"):
    if valor_original != valor_tratado:
        auditar_transformacao(
            campo=CAMPO,
            valor_original=valor_original,
            valor_tratado=valor_tratado,
            criterio=criterio,
            fonte=FONTE,
            id_registro=id_registro,
            etapa=etapa,
        )

    return valor_tratado


def remover_uf(bairro, id_registro=None):
    achado = SUFIXO_UF.search(bairro)

    if achado and achado.group(1).upper() in UFS:
        return _auditar(
            bairro,
            bairro[:achado.start()],
            f"Remoção do sufixo de UF '{achado.group(1).upper()}' (sigla válida presente em UFS)",
            id_registro=id_registro,
        )

    return bairro


def remover_acentos(texto, id_registro=None):
    decomposto = unicodedata.normalize("NFKD", texto)

    tratado = "".join(
        caractere
        for caractere in decomposto
        if not unicodedata.combining(caractere)
    )

    return _auditar(
        texto,
        tratado,
        "Remoção de acentos (normalização Unicode NFKD)",
        id_registro=id_registro,
    )


def limpar_bairro(bairro, id_registro=None):
    if not isinstance(bairro, str):
        auditar_transformacao(
            campo=CAMPO,
            valor_original=bairro,
            valor_tratado=None,
            criterio="Valor descartado: tipo não textual (esperado str)",
            fonte=FONTE,
            id_registro=id_registro,
            etapa="validacao",
        )
        return None

    original = bairro

    bairro = _auditar(
        bairro,
        unicodedata.normalize("NFC", bairro).strip(),
        "Normalização Unicode (NFC) e remoção de espaços nas pontas",
        id_registro=id_registro,
    )

    if not bairro:
        auditar_transformacao(
            campo=CAMPO,
            valor_original=original,
            valor_tratado=None,
            criterio="Valor descartado: texto vazio após remoção de espaços",
            fonte=FONTE,
            id_registro=id_registro,
            etapa="validacao",
        )
        return None

    dentro_parenteses = re.search(r"\(([^)]+)\)", bairro)

    if dentro_parenteses:
        bairro = _auditar(
            bairro,
            dentro_parenteses.group(1),
            "Uso do conteúdo entre parênteses como nome do bairro",
            id_registro=id_registro,
        )

    bairro = remover_uf(bairro, id_registro)

    bairro = _auditar(
        bairro,
        re.sub(r"[^\w\s]", " ", bairro),
        "Substituição de pontuação por espaço",
        id_registro=id_registro,
    )

    bairro = _auditar(
        bairro,
        re.sub(r"\s+", " ", bairro).strip(),
        "Colapso de espaços repetidos",
        id_registro=id_registro,
    )

    if not bairro:
        auditar_transformacao(
            campo=CAMPO,
            valor_original=original,
            valor_tratado=None,
            criterio="Valor descartado: texto vazio após limpeza",
            fonte=FONTE,
            id_registro=id_registro,
            etapa="validacao",
        )
        return None

    return bairro


def normalizar_limpo(limpo, id_registro=None):
    """Gera a chave de comparação a partir de um bairro já limpo."""
    sem_acentos = remover_acentos(limpo, id_registro)

    normalizado = _auditar(
        sem_acentos,
        sem_acentos.casefold(),
        "Conversão para minúsculas (casefold) para formar a chave de comparação",
        id_registro=id_registro,
    )

    return normalizado or None


def normalizar_bairro(bairro, id_registro=None):
    limpo = limpar_bairro(bairro, id_registro)

    if limpo is None:
        return None

    return normalizar_limpo(limpo, id_registro)


def formatar_para_exibicao(nome, id_registro=None):
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

    formatado = " ".join(resultado)

    return _auditar(
        nome,
        formatado,
        "Formatação para exibição (iniciais maiúsculas, numerais romanos em caixa alta)",
        id_registro=id_registro,
        etapa="exibicao",
    )