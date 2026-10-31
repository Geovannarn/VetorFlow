import pandas as pd

from src.vetorflow.database.connection import conectar

def carregar_csv(caminho):
    dados = pd.read_csv(caminho, sep=";")

    dados["data_cadastro"] = pd.to_datetime(
        dados["data_cadastro"],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    )

    return dados


def carregar_no_banco(dados):
    conexao = conectar()

    with conexao.cursor() as cursor:
        for _, linha in dados.iterrows():
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
                ON CONFLICT (id_cliente) DO NOTHING
                """,
                (
                    linha["id_cliente"],
                    linha["razao_social"],
                    linha["cnpj"],
                    linha["telefone"],
                    linha["email"],
                    linha["bairro_informado"],
                    linha["cep"],
                    linha["cidade"],
                    linha["uf"],
                    linha["data_cadastro"],
                    linha["vendedor_responsavel"]
                )
            )

    conexao.commit()
    conexao.close()


if __name__ == "__main__":
    dados = carregar_csv(
        "../data/raw/clientes_distribuidora_vetor.csv"
    )

    carregar_no_banco(dados)

    print("Dados carregados no PostgreSQL com sucesso!")