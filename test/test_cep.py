import pytest

from normalizers.postal_code import (
    exigir_cep,
    formatar_cep,
    normalizar_cep,
    validar_cep,
)


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("71000-000", "71000000"),
        ("71000000", "71000000"),
        ("  71000-000  ", "71000000"),
        (71000000, "71000000"),
        (1001000, "01001000"),
    ],
)
def test_normalizar_cep(entrada, esperado):
    assert normalizar_cep(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [
        "",
        "   ",
        None,
        "123",
        "710000000",
        "71000-00",
        "7100A-000",
        "71.000-000",
        -1,
        True,
        3.14,
        ["71000000"],
    ],
)
def test_normalizar_cep_invalido(entrada):
    assert normalizar_cep(entrada) is None


def test_formatar_cep():
    assert formatar_cep("71000000") == "71000-000"
    assert formatar_cep("71000-000") == "71000-000"
    assert formatar_cep(1001000) == "01001-000"


def test_formatar_cep_invalido():
    assert formatar_cep("123") is None
    assert formatar_cep(None) is None


def test_validar_cep():
    assert validar_cep("71000-000") is True
    assert validar_cep("123") is False
    assert validar_cep(None) is False


def test_exigir_cep():
    assert exigir_cep("71000-000") == "71000000"

    with pytest.raises(ValueError):
        exigir_cep("123")