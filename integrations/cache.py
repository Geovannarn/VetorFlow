import json
import logging
import os
import tempfile
from pathlib import Path


logger = logging.getLogger(__name__)

CACHE_FILE = (
    Path(__file__).resolve().parents[1] / "data" / "cache" / "cep_cache.json"
)


def carregar_cache():
    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (json.JSONDecodeError, OSError) as erro:
        logger.warning("Cache de CEP ilegível, será recriado: %s", erro)
        return {}

    return dados if isinstance(dados, dict) else {}


def salvar_cache(cache):
    temporario = None

    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        descritor, temporario = tempfile.mkstemp(
            dir=CACHE_FILE.parent, suffix=".tmp"
        )

        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(cache, arquivo, ensure_ascii=False, indent=4)

        os.replace(temporario, CACHE_FILE)

    except OSError as erro:
        logger.error("Erro ao salvar cache de CEP: %s", erro)

        if temporario and os.path.exists(temporario):
            os.remove(temporario)


def buscar_cache(cep):
    return carregar_cache().get(cep)


def armazenar_cache(cep, resultado):
    if not isinstance(resultado, dict) or not any(resultado.values()):
        return

    cache = carregar_cache()
    cache[cep] = resultado
    salvar_cache(cache)