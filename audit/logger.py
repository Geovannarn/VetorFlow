from datetime import datetime
from pathlib import Path


AUDIT_FILE = Path(__file__).resolve().parent / "audit.log"


def limpar(texto):
    return str(texto).replace("\r", " ").replace("\n", " ")


def registrar(tipo, ip, texto):
    linha = f"{datetime.now():%d/%m/%Y %H:%M:%S} | {tipo} | {ip} | {limpar(texto)}\n"

    try:
        with AUDIT_FILE.open("a", encoding="utf-8") as arquivo:
            arquivo.write(linha)
    except OSError as erro:
        print(f"Erro ao registrar auditoria: {erro}")


def registrar_operacao(metodo, rota, id_cliente=None, resultado=None, ip="-", detalhes=None):
    if metodo.upper() == "GET":
        return

    texto = f"{metodo.upper()} {rota} | cliente: {id_cliente or '-'} | {resultado or 'Não informado'}"

    if detalhes:
        texto += f" | dados: {detalhes}"

    registrar("OPERACAO", ip, texto)