from pathlib import Path

import pandas as pd
import pytest

from pipeline.checks import (
    executar_checks,
    verificar_colunas_obrigatorias,
    verificar_duplicados,
    verificar_nulos,
    verificar_registros_vazios,
)
from pipeline.loaders import carregar_csv
from pipeline.metrics import calcular_metricas, calcular_percentual


CSV = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "clientes_distribuidora_vetor.csv"
)


@pytest.fixture(scope="module")
def dados():
    return carregar_csv(CSV)



def test_verificar_colunas_obrigatorias():
    df = pd.DataFrame({"a": [1]})

    assert verificar_colunas_obrigatorias(df, ["a", "z"]) == ["z"]


def test_verificar_nulos_conta_vazios_e_espacos():
    df = pd.DataFrame({"a": ["x", " ", None, "y"], "b": [1, None, 3, 4]})

    assert verificar_nulos(df, ["a", "b", "inexistente"]) == {"a": 2, "b": 1}


def test_verificar_duplicados_por_chave():
    df = pd.DataFrame({"id": [1, 1, 2], "valor": ["a", "b", "c"]})

    assert verificar_duplicados(df) == 0
    assert verificar_duplicados(df, ["id"]) == 1


def test_verificar_registros_vazios():
    df = pd.DataFrame({"a": [None, "x"], "b": [None, "y"]})

    assert verificar_registros_vazios(df) == 1


def test_executar_checks_dataframe_vazio():
    df = pd.DataFrame({"a": []})

    assert executar_checks(df, ["a"])["possui_dados"] is False



@pytest.mark.parametrize(
    "valor, total, esperado",
    [(1, 4, 25.0), (1, 3, 33.33), (0, 10, 0.0), (5, 0, 0.0), (5, None, 0.0)],
)
def test_calcular_percentual(valor, total, esperado):
    assert calcular_percentual(valor, total) == esperado


def test_calcular_metricas():
    df = pd.DataFrame({"a": ["x", " ", None, "y"], "b": [1, None, 3, 4]})

    metricas = calcular_metricas(df, executar_checks(df, ["a", "b"]))

    assert metricas["total_registros"] == 4
    assert metricas["total_nulos"] == 3
    assert metricas["percentual_nulos"] == 37.5
    assert metricas["nulos_por_coluna"] == {"a": 50.0, "b": 25.0}


def test_percentual_de_nulos_nunca_passa_de_100():
    df = pd.DataFrame({"a": [None, None], "b": [None, None], "c": [None, None]})

    metricas = calcular_metricas(df, executar_checks(df, ["a", "b", "c"]))

    assert metricas["percentual_nulos"] == 100.0



def test_qualidade_do_csv(dados):
    checks = executar_checks(
        dados,
        ["id_cliente", "razao_social", "data_cadastro"],
        ["id_cliente"],
    )

    assert checks["possui_dados"]
    assert checks["colunas_ausentes"] == []
    assert checks["nulos"] == {
        "id_cliente": 0,
        "razao_social": 0,
        "data_cadastro": 0,
    }
    assert checks["duplicados"] == 0
    assert checks["registros_vazios"] == 0