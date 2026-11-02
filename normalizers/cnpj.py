import re


def normalizar_cnpj(cnpj):
    if cnpj is None:
        return None

    if not isinstance(cnpj, (str, int)):
        return None

    cnpj = str(cnpj).strip()
    cnpj = re.sub(r"\D", "", cnpj)

    if len(cnpj) != 14:
        return None

    return cnpj


def validar_cnpj(cnpj):
    cnpj = normalizar_cnpj(cnpj)

    if cnpj is None:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    primeiro_digito = calcular_digito(cnpj[:12])
    segundo_digito = calcular_digito(cnpj[:12] + primeiro_digito)

    return cnpj[-2:] == primeiro_digito + segundo_digito


def calcular_digito(numero):
    peso = len(numero) + 1
    soma = 0

    for digito in numero:
        soma += int(digito) * peso
        peso -= 1

        if peso < 2:
            peso = 9

    resto = soma % 11

    if resto < 2:
        return "0"

    return str(11 - resto)