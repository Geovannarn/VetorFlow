import json
from pathlib import Path


CACHE_FILE = Path("data/cache/cep_cache.json")


def carregar_cache():
    if not CACHE_FILE.exists():
        return {}

    with CACHE_FILE.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with CACHE_FILE.open("w", encoding="utf-8") as arquivo:
        json.dump(cache, arquivo, ensure_ascii=False, indent=4)


def buscar_cache(cep):
    cache = carregar_cache()
    return cache.get(cep)


def armazenar_cache(cep, resultado):
    cache = carregar_cache()
    cache[cep] = resultado
    salvar_cache(cache)