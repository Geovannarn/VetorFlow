from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from database.connection import conectar


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


def descrever_erro_banco(erro):
    """Traduz o erro do PostgreSQL para uma mensagem legível."""
    diag = getattr(erro, "diag", None)
    codigo = getattr(erro, "pgcode", None) or getattr(erro, "sqlstate", None)

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
                        return Response(
                            {"erro": "Cliente não encontrado."},
                            status=status.HTTP_404_NOT_FOUND
                        )

                    colunas = [
                        coluna.name
                        for coluna in cursor.description
                    ]

                    return Response(dict(zip(colunas, registro)))

                cursor.execute(
                    """
                    SELECT *
                    FROM usuarios
                    ORDER BY id_cliente
                    """
                )

                colunas = [
                    coluna.name
                    for coluna in cursor.description
                ]

                registros = cursor.fetchall()

                resultado = [
                    dict(zip(colunas, registro))
                    for registro in registros
                ]

                return Response(resultado)

            elif request.method == "POST":

                dados = request.data
                novo_id = dados.get("id_cliente")

                if novo_id is None or str(novo_id).strip() == "":
                    return Response(
                        {"erro": "Informe o código do cliente."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not dados.get("razao_social"):
                    return Response(
                        {"erro": "Informe a razão social do cliente."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                cursor.execute(
                    """
                    SELECT 1
                    FROM usuarios
                    WHERE id_cliente = %s
                    """,
                    (novo_id,)
                )

                if cursor.fetchone():
                    return Response(
                        {
                            "erro": "Já existe um cliente cadastrado com esse código."
                        },
                        status=status.HTTP_409_CONFLICT
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
                        dados.get("razao_social"),
                        valor(dados, "cnpj"),
                        valor(dados, "telefone"),
                        valor(dados, "email"),
                        valor(dados, "bairro"),
                        valor(dados, "cep"),
                        valor(dados, "cidade"),
                        valor(dados, "uf"),
                        valor(dados, "cadastro"),
                        valor(dados, "responsavel"),
                    )
                )

                novo_id = cursor.fetchone()[0]
                conexao.commit()

                return Response(
                    {
                        "mensagem": "Cliente criado com sucesso.",
                        "id_cliente": novo_id
                    },
                    status=status.HTTP_201_CREATED
                )

            elif request.method == "PUT":

                if id_cliente is None or str(id_cliente).strip() == "":
                    return Response(
                        {"erro": "Informe o código do cliente."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                dados = request.data

                campos_atualizar = {
                    campo: dados[campo]
                    for campo in CAMPOS
                    if campo in dados
                }

                if not campos_atualizar:
                    return Response(
                        {"erro": "Nenhum campo válido foi enviado."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if (
                    "razao_social" in campos_atualizar
                    and not campos_atualizar["razao_social"]
                ):
                    return Response(
                        {"erro": "Informe a razão social do cliente."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                cursor.execute(
                    """
                    SELECT 1
                    FROM usuarios
                    WHERE id_cliente = %s
                    """,
                    (id_cliente,)
                )

                if cursor.fetchone() is None:
                    return Response(
                        {"erro": "Cliente não encontrado."},
                        status=status.HTTP_404_NOT_FOUND
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

                return Response(
                    {"mensagem": "Cliente atualizado com sucesso."},
                    status=status.HTTP_200_OK
                )

            elif request.method == "DELETE":

                if id_cliente is None or str(id_cliente).strip() == "":
                    return Response(
                        {"erro": "Informe o código do cliente."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                coluna = "id" if request.query_params.get("por") == "id" else "id_cliente"

                cursor.execute(
                    f"""
                    DELETE FROM usuarios
                    WHERE {coluna} = %s
                    """,
                    (id_cliente,)
                )

                if cursor.rowcount == 0:
                    return Response(
                        {"erro": "Cliente não encontrado."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                conexao.commit()

                return Response(
                    {"mensagem": "Cliente excluído com sucesso."},
                    status=status.HTTP_200_OK
                )

    except Exception as erro:
        conexao.rollback()

        codigo = getattr(erro, "pgcode", None) or getattr(erro, "sqlstate", None)

        if codigo == "23505":
            restricao = getattr(getattr(erro, "diag", None), "constraint_name", "") or ""

            if "id_cliente" in restricao:
                return Response(
                    {"erro": "Já existe um cliente cadastrado com esse código."},
                    status=status.HTTP_409_CONFLICT
                )

        if codigo:
            print("ERRO DO BANCO:", codigo, erro)

            return Response(
                {"erro": descrever_erro_banco(erro), "codigo": codigo},
                status=(
                    status.HTTP_400_BAD_REQUEST
                    if codigo[:2] in ("22", "23")
                    else status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            )

        raise

    finally:
        conexao.close()