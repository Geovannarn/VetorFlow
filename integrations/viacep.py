import requests


URL_VIACEP = "https://viacep.com.br/ws/{}/json/"
TIMEOUT = 5


def consultar_viacep(cep):
    url = URL_VIACEP.format(cep)

    try:
        resposta = requests.get(url, timeout=TIMEOUT)

        if resposta.status_code == 200:
            resultado = resposta.json()

            if resultado.get("erro"):
                return None

            return resultado

    except requests.RequestException:
        return None

    return None
