from pathlib import Path

import pandas as pd
import pytest

from pipeline.loaders import carregar_csv, converter_data, para_banco


CSV = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "clientes_distribuidora_vetor.csv"
)

COLUNAS = [
    "id_cliente",
    "razao_social",
    "cnpj",
    "telefone",
    "email",
    "bairro_informado",
    "cep",
    "cidade",
    "uf",
    "data_cadastro",
    "vendedor_responsavel",
]


@pytest.fixture(scope="module")
def dados():
    return carregar_csv(CSV)


def test_carregar_csv(dados):
    assert isinstance(dados, pd.DataFrame)
    assert not dados.empty


def test_colunas_do_csv(dados):
    ausentes = [coluna for coluna in COLUNAS if coluna not in dados.columns]

    assert ausentes == []


def test_id_cliente_unico_e_preenchido(dados):
    assert dados["id_cliente"].notna().all()
    assert dados["id_cliente"].is_unique


def test_razao_social_preenchida(dados):
    assert dados["razao_social"].notna().all()


def test_todas_as_datas_foram_convertidas(dados):
    invalidas = dados.loc[dados["data_cadastro"].isna(), "id_cliente"].tolist()

    assert invalidas == []


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("2023-10-07", "2023-10-07"),
        ("28/02/2022", "2022-02-28"),
        ("24-12-2023", "2023-12-24"),
        ("Dec 24, 2023", "2023-12-24"),
        ("  2023-10-07  ", "2023-10-07"),
    ],
)
def test_converter_data(entrada, esperado):
    assert converter_data(entrada).isoformat() == esperado


@pytest.mark.parametrize("entrada", [None, "", "   ", "31/02/2022", "texto"])
def test_converter_data_invalida(entrada):
    assert converter_data(entrada) is None


def test_para_banco():
    assert para_banco(None) is None
    assert para_banco(float("nan")) is None
    assert para_banco("   ") is None
    assert para_banco("  Loja X  ") == "Loja X"