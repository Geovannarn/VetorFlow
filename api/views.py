import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from audit.logger import registrar_operacao
from database.connection import conectar
from normalizers.cnpj import normalizar_cnpj
from normalizers.data import normalizar_data
from normalizers.email import normalizar_email, validar_email
from normalizers.postal_code import normalizar_cep
from normalizers.telefone import padronizar_telefone


logger = logging.getLogger(__name__)


CAMPOS = [
    "razao_social",
    "cnpj",
    "telefone",
    "email",
    "bairro",
    "cep",
    "cidade",
    "uf",
    "cadastro",
    "responsavel",
]


def valor(dados, campo):
    x = dados.get(campo)

    if isinstance(x, str):
        x = x.strip()

    return None if x in ("", None) else x


def padronizar_campo(campo, bruto):
    if bruto is None:
        return None, None

    if campo == "cnpj":
        cnpj = normalizar_cnpj(bruto)

        if cnpj is None:
            return None, "CNPJ precisa ter 14 dígitos."

        return cnpj, None

    elif campo == "telefone":
        telefone = padronizar_telefone(bruto)

        if telefone is None:
            return None, "Telefone precisa ter 10 ou 11 dígitos."

        return telefone, None

    elif campo == "email":
        email = normalizar_email(bruto)

        if not validar_email(email):
            return None, "E-mail inválido."

        return email, None

    elif campo == "cep":
        cep = normalizar_cep(bruto)

        if cep is None:
            return None, "CEP precisa ter 8 dígitos."

        return cep, None

    elif campo == "uf":
        uf = str(bruto).strip().upper()

        if len(uf) != 2 or not uf.isalpha():
            return None, "UF precisa ter 2 letras."

        return uf, None

    elif campo == "cadastro":
        data = normalizar_data(bruto)

        if data is None:
            return None, "Data de cadastro inválida. Use AAAA-MM-DD ou DD/MM/AAAA."

        return data, None

    else:
        return bruto, None


def padronizar_dados(dados, campos):
    valores = {}
    erros = []

    for campo in campos:
        padronizado, erro = padronizar_campo(campo, valor(dados, campo))

        if erro is not None:
            erros.append(erro)

        valores[campo] = padronizado

    return valores, erros


def codigo_erro(erro):
    return getattr(erro, "sqlstate", None) or getattr(erro, "pgcode", None)


def descrever_erro_banco(erro):
    diag = getattr(erro, "diag", None)
    codigo = codigo_erro(erro)

    principal = getattr(diag, "message_primary", None) or str(erro).strip()
    coluna = getattr(diag, "column_name", None)
    restricao = getattr(diag, "constraint_name", None)

    if codigo == "23502":
        return f'A coluna "{coluna}" não pode ficar vazia e não tem valor padrão. ({principal})'

    if codigo == "23505":
        return f'Valor duplicado na restrição "{restricao}". ({principal})'

    if codigo == "22001":
        return f"Um dos textos é maior que o tamanho da coluna. ({principal})"

    if codigo == "22P02":
        return f"Valor em formato inválido para o tipo da coluna. ({principal})"

    if codigo and codigo.startswith("22"):
        return f"Dado inválido. ({principal})"

    return principal


def responder(request, corpo, status_http, id_cliente=None, detalhes=None):
    if status_http < 400:
        resultado = "sucesso"
    else:
        resultado = corpo.get("erro", "erro")

    registrar_operacao(
        request.method,
        request.path,
        id_cliente,
        resultado,
        ip=request.META.get("REMOTE_ADDR", "-"),
        detalhes=detalhes,
    )

    return Response(corpo, status=status_http)


def cliente_existe(cursor, id_cliente):
    cursor.execute(
        """
        SELECT 1
        FROM usuarios
        WHERE id_cliente = %s
        """,
        (id_cliente,)
    )

    return cursor.fetchone() is not None


@api_view(["GET", "POST", "PUT", "DELETE"])
def clientes(request, id_cliente=None):

    conexao = conectar()

    try:
        with conexao.cursor() as cursor:

            if request.method == "GET":

                if id_cliente is not None:
                    cursor.execute(
                        """
                        SELECT *
                        FROM usuarios
                        WHERE id_cliente = %s
                        """,
                        (id_cliente,)
                    )

                    registro = cursor.fetchone()

                    if registro is None:
                        return responder(
                            request,
                            {"erro": "Cliente não encontrado."},
                            status.HTTP_404_NOT_FOUND,
                            id_cliente
                        )

                    colunas = [coluna.name for coluna in cursor.description]

                    return responder(
                        request,
                        dict(zip(colunas, registro)),
                        status.HTTP_200_OK,
                        id_cliente
                    )

                cursor.execute(
                    """
                    SELECT *
                    FROM usuarios
                    ORDER BY id_cliente
                    """
                )

                colunas = [coluna.name for coluna in cursor.description]

                resultado = [
                    dict(zip(colunas, registro))
                    for registro in cursor.fetchall()
                ]

                return responder(request, resultado, status.HTTP_200_OK)

            elif request.method == "POST":

                dados = request.data
                novo_id = valor(dados, "id_cliente")
                razao_social = valor(dados, "razao_social")

                if novo_id is None:
                    return responder(
                        request,
                        {"erro": "Informe o código do cliente."},
                        status.HTTP_400_BAD_REQUEST
                    )

                if razao_social is None:
                    return responder(
                        request,
                        {"erro": "Informe a razão social do cliente."},
                        status.HTTP_400_BAD_REQUEST,
                        novo_id
                    )

                valores, erros = padronizar_dados(dados, CAMPOS)

                if erros:
                    return responder(
                        request,
                        {"erro": " ".join(erros)},
                        status.HTTP_400_BAD_REQUEST,
                        novo_id
                    )

                if cliente_existe(cursor, novo_id):
                    return responder(
                        request,
                        {"erro": "Já existe um cliente cadastrado com esse código."},
                        status.HTTP_409_CONFLICT,
                        novo_id
                    )

                cursor.execute(
                    """
                    INSERT INTO usuarios (
                        id_cliente,
                        razao_social,
                        cnpj,
                        telefone,
                        email,
                        bairro,
                        cep,
                        cidade,
                        uf,
                        cadastro,
                        responsavel
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    RETURNING id_cliente
                    """,
                    (
                        novo_id,
                        valores["razao_social"],
                        valores["cnpj"],
                        valores["telefone"],
                        valores["email"],
                        valores["bairro"],
                        valores["cep"],
                        valores["cidade"],
                        valores["uf"],
                        valores["cadastro"],
                        valores["responsavel"],
                    )
                )

                novo_id = cursor.fetchone()[0]
                conexao.commit()

                return responder(
                    request,
                    {
                        "mensagem": "Cliente criado com sucesso.",
                        "id_cliente": novo_id
                    },
                    status.HTTP_201_CREATED,
                    novo_id,
                    valores
                )

            elif request.method == "PUT":

                if id_cliente is None or str(id_cliente).strip() == "":
                    return responder(
                        request,
                        {"erro": "Informe o código do cliente."},
                        status.HTTP_400_BAD_REQUEST
                    )

                dados = request.data

                campos_enviados = [campo for campo in CAMPOS if campo in dados]

                if not campos_enviados:
                    return responder(
                        request,
                        {"erro": "Nenhum campo válido foi enviado."},
                        status.HTTP_400_BAD_REQUEST,
                        id_cliente
                    )

                campos_atualizar, erros = padronizar_dados(dados, campos_enviados)

                if erros:
                    return responder(
                        request,
                        {"erro": " ".join(erros)},
                        status.HTTP_400_BAD_REQUEST,
                        id_cliente
                    )

                if (
                    "razao_social" in campos_atualizar
                    and campos_atualizar["razao_social"] is None
                ):
                    return responder(
                        request,
                        {"erro": "Informe a razão social do cliente."},
                        status.HTTP_400_BAD_REQUEST,
                        id_cliente
                    )

                if not cliente_existe(cursor, id_cliente):
                    return responder(
                        request,
                        {"erro": "Cliente não encontrado."},
                        status.HTTP_404_NOT_FOUND,
                        id_cliente
                    )

                campos_sql = ", ".join(
                    f"{campo} = %s"
                    for campo in campos_atualizar
                )

                valores = list(campos_atualizar.values())
                valores.append(id_cliente)

                cursor.execute(
                    f"""
                    UPDATE usuarios
                    SET {campos_sql}
                    WHERE id_cliente = %s
                    """,
                    valores
                )

                conexao.commit()

                return responder(
                    request,
                    {"mensagem": "Cliente atualizado com sucesso."},
                    status.HTTP_200_OK,
                    id_cliente,
                    campos_atualizar
                )

            elif request.method == "DELETE":

                if id_cliente is None or str(id_cliente).strip() == "":
                    return responder(
                        request,
                        {"erro": "Informe o código do cliente."},
                        status.HTTP_400_BAD_REQUEST
                    )

                cursor.execute(
                    """
                    DELETE FROM usuarios
                    WHERE id_cliente = %s
                    """,
                    (id_cliente,)
                )

                if cursor.rowcount == 0:
                    return responder(
                        request,
                        {"erro": "Cliente não encontrado."},
                        status.HTTP_404_NOT_FOUND,
                        id_cliente
                    )

                conexao.commit()

                return responder(
                    request,
                    {"mensagem": "Cliente excluído com sucesso."},
                    status.HTTP_200_OK,
                    id_cliente
                )

    except Exception as erro:
        conexao.rollback()

        codigo = codigo_erro(erro)

        if codigo == "23505":
            restricao = getattr(getattr(erro, "diag", None), "constraint_name", "") or ""

            if "id_cliente" in restricao:
                return responder(
                    request,
                    {"erro": "Já existe um cliente cadastrado com esse código."},
                    status.HTTP_409_CONFLICT,
                    id_cliente
                )

        if codigo:
            logger.error("Erro do banco: %s %s", codigo, erro)

            return responder(
                request,
                {"erro": descrever_erro_banco(erro), "codigo": codigo},
                (
                    status.HTTP_400_BAD_REQUEST
                    if codigo[:2] in ("22", "23")
                    else status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                id_cliente
            )

        raise

    finally:
        conexao.close()