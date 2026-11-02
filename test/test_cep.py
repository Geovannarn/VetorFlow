from normalizers.postal_code import (
    normalizar_cep,
    formatar_cep,
)


def test_normalizar_cep():
    assert normalizar_cep("71000-000") == "71000000"
    assert normalizar_cep("71000000") == "71000000"


def test_normalizar_cep_invalido():
    assert normalizar_cep("") is None
    assert normalizar_cep(None) is None
    assert normalizar_cep("123") is None


def test_formatar_cep():
    assert formatar_cep("71000000") == "71000-000"