from audit.logger import auditar_transformacao
from neighborhood.normalizer import (
    formatar_para_exibicao,
    limpar_bairro,
    normalizar_limpo,
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

CAMPO = "bairro"
FONTE_REGRAS = "regras-de-tratamento.md"


def preparar(bairro, id_registro=None):
    limpo = limpar_bairro(bairro, id_registro)

    if limpo is None:
        return None, None

    chave = normalizar_limpo(limpo, id_registro)

    if chave is None:
        return None, None

    if chave in APELIDOS:
        chave_original = chave
        chave = APELIDOS[chave]

        auditar_transformacao(
            campo=CAMPO,
            valor_original=chave_original,
            valor_tratado=chave,
            criterio=f"Substituição do apelido '{chave_original}' pelo nome oficial (dicionário APELIDOS)",
            fonte=f"APELIDOS | {FONTE_REGRAS}",
            id_registro=id_registro,
            etapa="apelido",
        )

        return chave, formatar_para_exibicao(chave, id_registro)

    return chave, formatar_para_exibicao(limpo, id_registro)


def esta_contido(menor, maior):
    palavras_menor = set(menor.split())
    palavras_maior = set(maior.split())

    return (
        bool(palavras_menor)
        and palavras_menor <= palavras_maior
        and not palavras_menor <= DIRECOES
    )


def _decidir(bairro_informado, bairro_api, resultado, criterio, motivo, fonte, id_registro):
    auditar_transformacao(
        campo=CAMPO,
        valor_original=f"informado={bairro_informado!r} | api={bairro_api!r}",
        valor_tratado=resultado,
        criterio=f"{criterio}: {motivo}",
        fonte=fonte,
        id_registro=id_registro,
        etapa="decisao",
    )

    return resultado, criterio


def resolver_bairro(bairro_informado, bairro_api, id_registro=None):
    informado, nome_informado = preparar(bairro_informado, id_registro)
    obtido_api, nome_api = preparar(bairro_api, id_registro)

    if informado is None and obtido_api is None:
        return _decidir(
            bairro_informado, bairro_api, None,
            CRITERIO_SEM_INFORMACAO,
            "nenhum dos dois valores é utilizável após o tratamento",
            "nenhuma",
            id_registro,
        )

    if informado is None:
        return _decidir(
            bairro_informado, bairro_api, nome_api,
            CRITERIO_API,
            "bairro informado ausente ou inválido; utilizado o valor da API",
            "api",
            id_registro,
        )

    if obtido_api is None:
        return _decidir(
            bairro_informado, bairro_api, nome_informado,
            CRITERIO_INFORMADO,
            "API sem bairro utilizável; mantido o valor informado",
            "informado",
            id_registro,
        )

    if informado == obtido_api:
        return _decidir(
            bairro_informado, bairro_api, nome_api,
            CRITERIO_CONVERGENTE,
            "chaves normalizadas idênticas entre informado e API",
            "informado+api",
            id_registro,
        )

    if esta_contido(informado, obtido_api):
        return _decidir(
            bairro_informado, bairro_api, nome_api,
            CRITERIO_CONVERGENTE,
            "bairro informado está contido no nome da API; mantido o nome mais completo (API)",
            "api",
            id_registro,
        )

    if esta_contido(obtido_api, informado):
        return _decidir(
            bairro_informado, bairro_api, nome_informado,
            CRITERIO_CONVERGENTE,
            "bairro da API está contido no nome informado; mantido o nome mais completo (informado)",
            "informado",
            id_registro,
        )

    return _decidir(
        bairro_informado, bairro_api, nome_informado,
        CRITERIO_DIVERGENTE,
        "informado e API diferem e nenhum está contido no outro; mantido o informado",
        "informado",
        id_registro,
    )