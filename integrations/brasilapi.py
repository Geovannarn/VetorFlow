import requests


URL_BRASILAPI = "https://brasilapi.com.br/api/cep/v2/{}"
TIMEOUT = 5


def consultar_brasilapi(cep):
    url = URL_BRASILAPI.format(cep)

    try:
        resposta = requests.get(url, timeout=TIMEOUT)
        resposta.raise_for_status()

        return resposta.json()

    except requests.RequestException:
        return None