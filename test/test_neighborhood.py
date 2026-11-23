import pytest

from neighborhood.normalizer import normalizar_bairro
from neighborhood.resolver import (
    CRITERIO_API,
    CRITERIO_CONVERGENTE,
    CRITERIO_DIVERGENTE,
    CRITERIO_INFORMADO,
    CRITERIO_SEM_INFORMACAO,
    resolver_bairro,
)


def test_chave_de_comparacao_continua_sem_acento():
    assert normalizar_bairro("Sul (Águas Claras)") == "aguas claras"


@pytest.mark.parametrize(
    "informado, api, esperado, criterio",
    [
        ("Sul (Águas Claras)", "Águas Claras", "Águas Claras", CRITERIO_CONVERGENTE),
        ("AGUAS CLARAS", "Águas Claras", "Águas Claras", CRITERIO_CONVERGENTE),
        ("aguas claras", None, "Aguas Claras", CRITERIO_INFORMADO),
        ("Taguatinga - DF", "Taguatinga", "Taguatinga", CRITERIO_CONVERGENTE),
        ("Taguatinga/DF", None, "Taguatinga", CRITERIO_INFORMADO),
        (None, "Plano Piloto", "Plano Piloto", CRITERIO_API),
        ("V Pires", "Vicente Pires", "Vicente Pires", CRITERIO_CONVERGENTE),
        ("RIACHO FUNDO II", None, "Riacho Fundo II", CRITERIO_INFORMADO),
        ("SETOR DE INDUSTRIA E ABASTECIMENTO", None, "Setor de Industria e Abastecimento", CRITERIO_INFORMADO),
        ("Ceilândia", "Taguatinga", "Ceilândia", CRITERIO_DIVERGENTE),
        (None, None, None, CRITERIO_SEM_INFORMACAO),
    ],
)
def test_resolver_bairro_grava_nome_legivel(informado, api, esperado, criterio):
    assert resolver_bairro(informado, api) == (esperado, criterio)