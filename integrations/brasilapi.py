import logging
import re

import requests


logger = logging.getLogger(__name__)

URL_BRASILAPI = "https://brasilapi.com.br/api/cep/v2/{}"
TIMEOUT = 5


def consultar_brasilapi(cep):
    cep = re.sub(r"\D", "", str(cep or ""))

    if len(cep) != 8:
        return None

    url = URL_BRASILAPI.format(cep)

    try:
        resposta = requests.get(url, timeout=TIMEOUT)

        if resposta.status_code == 404:
            return None

        if resposta.status_code != 200:
            logger.warning(
                "BrasilAPI respondeu com status %s para o CEP %s",
                resposta.status_code,
                cep,
            )
            return None

        resultado = resposta.json()

    except (requests.RequestException, ValueError) as erro:
        logger.warning("Falha ao consultar BrasilAPI para o CEP %s: %s", cep, erro)
        return None

    return resultado if isinstance(resultado, dict) else None