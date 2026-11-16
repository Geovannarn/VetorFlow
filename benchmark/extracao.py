
import pandas as pd

from benchmark import config


def ler_em_chunks(caminho, tamanho_chunk=config.TAMANHO_CHUNK):
    total = 0

    for parte in pd.read_csv(
        caminho, sep=";", dtype=str, keep_default_na=False, chunksize=tamanho_chunk
    ):
        total += len(parte)

    return total


def ler_inteiro(caminho):
    return len(pd.read_csv(caminho, sep=";", dtype=str, keep_default_na=False))


def testar_extracao(coletor, volume, caminho):
    tamanho_mb = caminho.stat().st_size / (1024 * 1024)

    with coletor.medir(volume, "extracao", "chunks") as m:
        m.registros = ler_em_chunks(caminho)
        m.extras["tamanho_arquivo_mb"] = tamanho_mb

    if volume <= config.LIMITE_LEITURA_INTEIRA:
        with coletor.medir(volume, "extracao", "inteiro") as m:
            m.registros = ler_inteiro(caminho)
            m.extras["tamanho_arquivo_mb"] = tamanho_mb
    else:
        coletor.registrar(
            volume,
            "extracao",
            "inteiro",
            ignorado=True,
            observacao=(
                f"não executado: acima de {config.LIMITE_LEITURA_INTEIRA:,} linhas "
                "ler tudo de uma vez pode estourar a memória"
            ).replace(",", "."),
        )