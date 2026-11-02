import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


def test_listar_clientes(client):
    resposta = client.get("/api/clientes/")

    assert resposta.status_code == 200