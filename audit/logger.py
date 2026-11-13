import logging
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)

AUDIT_FILE = Path(__file__).resolve().parent / "audit.log"


def limpar(texto):
    """Remove quebras de linha e separadores para não corromper o log."""
    return (
        str(texto)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("|", "/")
        .strip()
    )


def registrar_operacao(metodo, rota, id_cliente=None, resultado=None):
    registro = {
        "data_hora": datetime.now().astimezone().isoformat(timespec="seconds"),
        "metodo": limpar(metodo).upper(),
        "rota": limpar(rota),
        "id_cliente": limpar(id_cliente) if id_cliente is not None else "-",
        "resultado": limpar(resultado) if resultado else "Não informado",
    }

    linha = (
        f"{registro['data_hora']} | "
        f"{registro['metodo']} | "
        f"{registro['rota']} | "
        f"{registro['id_cliente']} | "
        f"{registro['resultado']}\n"
    )

    try:
        AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with AUDIT_FILE.open("a", encoding="utf-8") as arquivo:
            arquivo.write(linha)

    except OSError as erro:
        logger.error("Erro ao registrar auditoria: %s", erro)
        return None

    return registro