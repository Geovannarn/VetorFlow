import os
import random
import time

import numpy as np
import requests

from benchmark import config


PREFIXO_API = config.PREFIXO_ID + "API"


class ApiIndisponivel(Exception):
    pass


class UsuariosProtegida(Exception):
    pass


def percentil(valores, p):
    return float(np.percentile(valores, p)) if valores else 0.0


def estatisticas(latencias_ms, bytes_recebidos):
    n = max(len(latencias_ms), 1)

    return {
        "lat_media_ms": sum(latencias_ms) / n,
        "lat_p50_ms": percentil(latencias_ms, 50),
        "lat_p95_ms": percentil(latencias_ms, 95),
        "lat_p99_ms": percentil(latencias_ms, 99),
        "lat_max_ms": max(latencias_ms, default=0.0),
        "kb_resposta_media": bytes_recebidos / n / 1024,
    }


def executar_chamadas(coletor, sessao, volume, variante, chamadas):
    latencias = []
    erros = 0
    recebidos = 0

    with coletor.medir(volume, "api", variante) as m:
        for metodo, url, corpo in chamadas:
            inicio = time.perf_counter()

            try:
                resposta = sessao.request(metodo, url, json=corpo, timeout=60)
                recebidos += len(resposta.content)

                if resposta.status_code >= 400:
                    erros += 1
            except requests.RequestException:
                erros += 1

            latencias.append((time.perf_counter() - inicio) * 1000)

        m.registros = len(chamadas)
        m.erros = erros
        m.extras.update(estatisticas(latencias, recebidos))


def listar_tudo(coletor, sessao, volume, url_lista, repeticoes):
    latencias = []
    erros = 0
    recebidos = 0
    linhas_total = 0
    ultimos = []

    with coletor.medir(volume, "api", "listar_todos") as m:
        for _ in range(repeticoes):
            inicio = time.perf_counter()

            try:
                resposta = sessao.get(url_lista, timeout=600)
                recebidos += len(resposta.content)

                if resposta.status_code >= 400:
                    erros += 1
                else:
                    ultimos = resposta.json()
                    linhas_total += len(ultimos)
            except (requests.RequestException, ValueError):
                erros += 1

            latencias.append((time.perf_counter() - inicio) * 1000)

        m.registros = linhas_total
        m.erros = erros
        m.observacao = "registros = linhas devolvidas pela API (JSON já decodificado)"
        m.extras.update(estatisticas(latencias, recebidos))
        m.extras["linhas_por_resposta"] = len(ultimos)

    return ultimos


def testar_api(coletor, volume, url_base, repeticoes_listagem=3, amostra_ids=200, operacoes_crud=100):
    url_lista = url_base.rstrip("/") + "/api/clientes/"
    sessao = requests.Session()

    try:
        sessao.get(url_lista, timeout=10)
    except requests.RequestException as erro:
        raise ApiIndisponivel(f"não consegui falar com {url_lista}: {erro}") from erro

    clientes = listar_tudo(coletor, sessao, volume, url_lista, repeticoes_listagem)

    ids = [c["id_cliente"] for c in clientes if isinstance(c, dict) and c.get("id_cliente")]
    sorteados = random.Random(config.SEMENTE).sample(ids, min(amostra_ids, len(ids)))

    if sorteados:
        executar_chamadas(
            coletor, sessao, volume, "buscar_por_id",
            [("GET", f"{url_lista}{i}/", None) for i in sorteados],
        )

    coletor.registrar(
        volume, "api", "filtrar", ignorado=True,
        observacao="a API ainda não tem filtro (a busca da tabela é feita no navegador); "
                   "o filtro foi medido no banco, em consultas_banco",
    )

    novos = [f"{PREFIXO_API}{i:05d}" for i in range(operacoes_crud)]

    try:
        executar_chamadas(coletor, sessao, volume, "crud_criar", [
            ("POST", url_lista, {
                "id_cliente": i, "razao_social": f"Benchmark {i}", "cnpj": "11222333000181",
                "cep": "71000-000", "bairro": "Taguatinga",
            }) for i in novos
        ])
        executar_chamadas(coletor, sessao, volume, "crud_consultar",
                          [("GET", f"{url_lista}{i}/", None) for i in novos])
        executar_chamadas(coletor, sessao, volume, "crud_atualizar",
                          [("PUT", f"{url_lista}{i}/", {"cidade": "Brasília"}) for i in novos])
    finally:
        executar_chamadas(coletor, sessao, volume, "crud_excluir",
                          [("DELETE", f"{url_lista}{i}/", None) for i in novos])

    return len(ids)


def conferir_banco_de_teste(conexao):
    """Só deixa mexer em "usuarios" se for um banco de teste e se não houver dados reais."""
    nome = (os.getenv("DB_NAME") or "").lower()

    if "bench" not in nome and "test" not in nome:
        raise UsuariosProtegida(
            f'DB_NAME="{nome}" não parece um banco de teste (precisa conter "bench" ou "test").'
        )

    with conexao.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM usuarios WHERE id_cliente NOT LIKE %s",
            (config.PREFIXO_ID + "%",),
        )
        reais = cursor.fetchone()[0]

    if reais:
        raise UsuariosProtegida(f'a tabela "usuarios" tem {reais} linhas que não são do benchmark.')


def popular_usuarios(conexao, lotes):
    sql = "COPY usuarios (id_cliente, razao_social, cnpj, cep, bairro) FROM STDIN"
    total = 0

    with conexao.cursor() as cursor:
        with cursor.copy(sql) as copia:
            for lote in lotes:
                for id_cliente, nome, documento, cep, _endereco, regiao in lote:
                    copia.write_row((id_cliente, nome, documento, cep, regiao))

                total += len(lote)

    conexao.commit()

    return total


def limpar_usuarios(conexao):
    with conexao.cursor() as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id_cliente LIKE %s", (config.PREFIXO_ID + "%",))

    conexao.commit()