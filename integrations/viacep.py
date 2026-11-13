import logging
import re

import requests


logger = logging.getLogger(__name__)

URL_VIACEP = "https://viacep.com.br/ws/{}/json/"
TIMEOUT = 5


def consultar_viacep(cep):
    cep = re.sub(r"\D", "", str(cep or ""))

    if len(cep) != 8:
        return None

    url = URL_VIACEP.format(cep)

    try:
        resposta = requests.get(url, timeout=TIMEOUT)

        if resposta.status_code != 200:
            return None

        resultado = resposta.json()

    except (requests.RequestException, ValueError) as erro:
        logger.warning("Falha ao consultar ViaCEP para o CEP %s: %s", cep, erro)
        return None

    if not isinstance(resultado, dict) or resultado.get("erro"):
        return None

    return resultado