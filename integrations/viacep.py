import requests


URL_VIACEP = "https://viacep.com.br/ws/{}/json/"
TIMEOUT = 5


def consultar_viacep(cep):
    url = URL_VIACEP.format(cep)

    try:
        resposta = requests.get(url, timeout=TIMEOUT)
        resposta.raise_for_status()

        resultado = resposta.json()

        if resultado.get("erro"):
            return None

        return resultado

    except requests.RequestException:
        return None