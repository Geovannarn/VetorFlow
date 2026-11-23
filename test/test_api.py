import pytest
from rest_framework.test import APIClient

from api import views


class Coluna:
    def __init__(self, name):
        self.name = name


class CursorFalso:

    def __init__(self, linhas=None, colunas=None, rowcount=1):
        self.linhas = list(linhas or [])
        self.description = [Coluna(nome) for nome in (colunas or [])]
        self.rowcount = rowcount
        self.consultas = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, parametros=None):
        self.consultas.append((sql, parametros))

    def fetchone(self):
        return self.linhas.pop(0) if self.linhas else None

    def fetchall(self):
        linhas, self.linhas = self.linhas, []
        return linhas


class ConexaoFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.fechada = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.fechada = True


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def banco(monkeypatch):

    def preparar(linhas=None, colunas=None, rowcount=1):
        conexao = ConexaoFalsa(CursorFalso(linhas, colunas, rowcount))
        monkeypatch.setattr(views, "conectar", lambda: conexao)
        return conexao

    monkeypatch.setattr(views, "registrar_operacao", lambda *args, **kwargs: None)

    return preparar


def test_listar_clientes(client, banco):
    conexao = banco(
        linhas=[("CLI0001", "Mercadinho Boa Vista")],
        colunas=["id_cliente", "razao_social"],
    )

    resposta = client.get("/api/clientes/")

    assert resposta.status_code == 200
    assert resposta.json() == [
        {"id_cliente": "CLI0001", "razao_social": "Mercadinho Boa Vista"}
    ]
    assert conexao.fechada


def test_buscar_cliente_existente(client, banco):
    banco(
        linhas=[("CLI0001", "Mercadinho Boa Vista")],
        colunas=["id_cliente", "razao_social"],
    )

    resposta = client.get("/api/clientes/CLI0001/")

    assert resposta.status_code == 200
    assert resposta.json()["id_cliente"] == "CLI0001"


def test_buscar_cliente_inexistente(client, banco):
    banco(linhas=[])

    resposta = client.get("/api/clientes/NAO_EXISTE/")

    assert resposta.status_code == 404


def test_criar_cliente_sem_codigo(client, banco):
    banco()

    resposta = client.post(
        "/api/clientes/", {"razao_social": "Loja X"}, format="json"
    )

    assert resposta.status_code == 400


def test_criar_cliente_sem_razao_social(client, banco):
    banco()

    resposta = client.post(
        "/api/clientes/", {"id_cliente": "CLI9999"}, format="json"
    )

    assert resposta.status_code == 400


def test_criar_cliente_duplicado(client, banco):
    banco(linhas=[(1,)])

    resposta = client.post(
        "/api/clientes/",
        {"id_cliente": "CLI0001", "razao_social": "Loja X"},
        format="json",
    )

    assert resposta.status_code == 409


def test_criar_cliente(client, banco):
    conexao = banco(linhas=[None, ("CLI9999",)])

    resposta = client.post(
        "/api/clientes/",
        {"id_cliente": "CLI9999", "razao_social": "Loja X"},
        format="json",
    )

    assert resposta.status_code == 201
    assert resposta.json()["id_cliente"] == "CLI9999"
    assert conexao.commits == 1


def test_atualizar_cliente_inexistente(client, banco):
    banco(linhas=[None])

    resposta = client.put(
        "/api/clientes/NAO_EXISTE/", {"cidade": "Brasília"}, format="json"
    )

    assert resposta.status_code == 404


def test_atualizar_cliente_sem_campos_validos(client, banco):
    banco()

    resposta = client.put(
        "/api/clientes/CLI0001/", {"campo_invalido": "x"}, format="json"
    )

    assert resposta.status_code == 400


def test_excluir_cliente(client, banco):
    conexao = banco(rowcount=1)

    resposta = client.delete("/api/clientes/CLI0001/")

    assert resposta.status_code == 200
    assert conexao.commits == 1


def test_excluir_cliente_inexistente(client, banco):
    banco(rowcount=0)

    resposta = client.delete("/api/clientes/NAO_EXISTE/")

    assert resposta.status_code == 404


def test_criar_cliente_padroniza_campos(client, banco):
    conexao = banco(linhas=[None, ("CLI9999",)])

    resposta = client.post(
        "/api/clientes/",
        {
            "id_cliente": "CLI9999",
            "razao_social": "Loja X",
            "cnpj": "11.222.333/0001-81",
            "telefone": "(61) 99999-9999",
            "email": "  CONTATO@Loja.com ",
            "cep": "71929-000",
            "uf": "df",
            "cadastro": "31/12/2025",
        },
        format="json",
    )

    assert resposta.status_code == 201

    _, parametros = conexao._cursor.consultas[-1]

    assert parametros[2] == "11222333000181"
    assert parametros[3] == "+5561999999999"
    assert parametros[4] == "contato@loja.com"
    assert parametros[6] == "71929000"
    assert parametros[8] == "DF"
    assert parametros[9] == "2025-12-31"


@pytest.mark.parametrize(
    "campo, valor_invalido",
    [
        ("cnpj", "123"),
        ("telefone", "999"),
        ("email", "sem-arroba"),
        ("cep", "1234"),
        ("uf", "D"),
        ("cadastro", "ontem"),
    ],
)
def test_criar_cliente_com_campo_invalido(client, banco, campo, valor_invalido):
    conexao = banco()

    resposta = client.post(
        "/api/clientes/",
        {"id_cliente": "CLI9999", "razao_social": "Loja X", campo: valor_invalido},
        format="json",
    )

    assert resposta.status_code == 400
    assert conexao.commits == 0


def test_atualizar_cliente_padroniza_campos(client, banco):
    conexao = banco(linhas=[(1,)])

    resposta = client.put(
        "/api/clientes/CLI0001/", {"telefone": "61 99999-9999"}, format="json"
    )

    assert resposta.status_code == 200

    _, parametros = conexao._cursor.consultas[-1]

    assert parametros[0] == "+5561999999999"


def test_atualizar_cliente_com_campo_invalido(client, banco):
    banco()

    resposta = client.put(
        "/api/clientes/CLI0001/", {"cnpj": "123"}, format="json"
    )

    assert resposta.status_code == 400