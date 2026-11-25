import json
import threading
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
AUDIT_FILE = BASE_DIR / "audit.log"
TRANSFORMACOES_FILE = BASE_DIR / "audit_transformacoes.jsonl"

_lock = threading.Lock()


def limpar(texto):
    return str(texto).replace("\r", " ").replace("\n", " ")


def _escrever(arquivo_destino, linha):
    try:
        with _lock:
            with arquivo_destino.open("a", encoding="utf-8") as arquivo:
                arquivo.write(linha)
    except OSError as erro:
        print(f"Erro ao registrar auditoria: {erro}")


def registrar(tipo, ip, texto):
    linha = f"{datetime.now():%d/%m/%Y %H:%M:%S} | {tipo} | {ip} | {limpar(texto)}\n"
    _escrever(AUDIT_FILE, linha)


def registrar_operacao(metodo, rota, id_cliente=None, resultado=None, ip="-", detalhes=None):
    if metodo.upper() == "GET":
        return

    texto = f"{metodo.upper()} {rota} | cliente: {id_cliente or '-'} | {resultado or 'Não informado'}"

    if detalhes:
        texto += f" | dados: {detalhes}"

    registrar("OPERACAO", ip, texto)


def registrar_transformacao(
    campo,
    valor_original,
    valor_tratado,
    criterio,
    fonte=None,
    id_registro=None,
    etapa=None,
):
    
    evento = {
        "data_hora": datetime.now().isoformat(timespec="seconds"),
        "id_registro": None if id_registro is None else limpar(id_registro),
        "etapa": etapa,
        "campo": campo,
        "valor_original": None if valor_original is None else limpar(valor_original),
        "valor_tratado": None if valor_tratado is None else limpar(valor_tratado),
        "alterado": valor_original != valor_tratado,
        "criterio": criterio,
        "fonte": fonte,
    }

    linha = json.dumps(evento, ensure_ascii=False) + "\n"
    _escrever(TRANSFORMACOES_FILE, linha)


def auditar_transformacao(
    campo,
    valor_original,
    valor_tratado,
    criterio,
    fonte=None,
    id_registro=None,
    etapa=None,
):
    registrar_transformacao(
        campo=campo,
        valor_original=valor_original,
        valor_tratado=valor_tratado,
        criterio=criterio,
        fonte=fonte,
        id_registro=id_registro,
        etapa=etapa,
    )
    return valor_tratado