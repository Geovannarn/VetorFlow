from neighborhood.normalizer import (
    formatar_para_exibicao,
    limpar_bairro,
    normalizar_bairro,
)


CRITERIO_CONVERGENTE = "convergente"
CRITERIO_INFORMADO = "informado"
CRITERIO_API = "api"
CRITERIO_DIVERGENTE = "divergente"
CRITERIO_SEM_INFORMACAO = "sem informação"

APELIDOS = {
    "v pires": "vicente pires",
    "vte pires": "vicente pires",
}

DIRECOES = {"norte", "sul", "leste", "oeste", "centro"}


def preparar(bairro):
    """Devolve (chave, nome): a chave serve para comparar, o nome para gravar."""
    chave = normalizar_bairro(bairro)

    if chave is None:
        return None, None

    if chave in APELIDOS:
        chave = APELIDOS[chave]
        return chave, formatar_para_exibicao(chave)

    return chave, formatar_para_exibicao(limpar_bairro(bairro))


def esta_contido(menor, maior):
    palavras_menor = set(menor.split())
    palavras_maior = set(maior.split())

    return (
        bool(palavras_menor)
        and palavras_menor <= palavras_maior
        and not palavras_menor <= DIRECOES
    )


def resolver_bairro(bairro_informado, bairro_api):
    informado, nome_informado = preparar(bairro_informado)
    obtido_api, nome_api = preparar(bairro_api)

    if informado is None and obtido_api is None:
        return None, CRITERIO_SEM_INFORMACAO

    if informado is None:
        return nome_api, CRITERIO_API

    if obtido_api is None:
        return nome_informado, CRITERIO_INFORMADO

    if informado == obtido_api:
        return nome_api, CRITERIO_CONVERGENTE

    if esta_contido(informado, obtido_api):
        return nome_api, CRITERIO_CONVERGENTE

    if esta_contido(obtido_api, informado):
        return nome_informado, CRITERIO_CONVERGENTE

    return nome_informado, CRITERIO_DIVERGENTE