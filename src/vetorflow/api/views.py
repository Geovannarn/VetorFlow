from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from src.vetorflow.database.connection import conectar
@api_view(["GET", "POST"])
def clientes(request, id_cliente=None):

    if request.method == "GET":
        conexao = conectar()

        try:
            with conexao.cursor() as cursor:

                if id_cliente:
                    cursor.execute(
                        """
                        SELECT
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

                    colunas = [coluna.name for coluna in cursor.description]

                    cliente = dict(zip(colunas, registro))

                    return Response(cliente)

                cursor.execute(
                    """
                    SELECT
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
                    FROM usuarios
                    ORDER BY id_cliente
                    """
                )

                colunas = [coluna.name for coluna in cursor.description]
                registros = cursor.fetchall()

                clientes = [
                    dict(zip(colunas, registro))
                    for registro in registros
                ]

                return Response(clientes)

        finally:
            conexao.close()

    if request.method == "POST":
        dados = request.data

        conexao = conectar()

        try:
            with conexao.cursor() as cursor:
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
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id_cliente
                    """,
                    (
                        dados.get("id_cliente"),
                        dados.get("razao_social"),
                        dados.get("cnpj"),
                        dados.get("telefone"),
                        dados.get("email"),
                        dados.get("bairro"),
                        dados.get("cep"),
                        dados.get("cidade"),
                        dados.get("uf"),
                        dados.get("cadastro"),
                        dados.get("responsavel"),
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

        except Exception:
            conexao.rollback()

            return Response(
                {"erro": "Não foi possível criar o cliente."},
                status=status.HTTP_400_BAD_REQUEST
            )

        finally:
            conexao.close()