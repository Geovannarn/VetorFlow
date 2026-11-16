from neighborhood.normalizer import normalizar_bairro


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
    nome = normalizar_bairro(bairro)

    return APELIDOS.get(nome, nome)


def esta_contido(menor, maior):
    palavras_menor = set(menor.split())
    palavras_maior = set(maior.split())

    return (
        bool(palavras_menor)
        and palavras_menor <= palavras_maior
        and not palavras_menor <= DIRECOES
    )


def resolver_bairro(bairro_informado, bairro_api):
    informado = preparar(bairro_informado)
    obtido_api = preparar(bairro_api)

    if informado is None and obtido_api is None:
        return None, CRITERIO_SEM_INFORMACAO

    if informado is None:
        return obtido_api, CRITERIO_API

    if obtido_api is None:
        return informado, CRITERIO_INFORMADO

    if informado == obtido_api:
        return informado, CRITERIO_CONVERGENTE

    if esta_contido(informado, obtido_api):
        return obtido_api, CRITERIO_CONVERGENTE

    if esta_contido(obtido_api, informado):
        return informado, CRITERIO_CONVERGENTE

    return informado, CRITERIO_DIVERGENTE