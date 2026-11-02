import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from pipeline.loaders import carregar_csv

def test_carregar_csv():
    dados = carregar_csv(
        "data/raw/clientes_distribuidora_vetor.csv"
    )

    assert isinstance(dados, pd.DataFrame)
    assert not dados.empty


def test_colunas_do_csv():
    dados = carregar_csv(
        "data/raw/clientes_distribuidora_vetor.csv"
    )

    colunas = [
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

    for coluna in colunas:
        assert coluna in dados.columns