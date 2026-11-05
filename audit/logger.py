
from datetime import datetime
from pathlib import Path


AUDIT_FILE = Path(__file__).resolve().parent / "audit.log"


def registrar_operacao(metodo, rota, id_cliente=None, resultado=None):

    registro = {
        "data_hora": datetime.now().astimezone().isoformat(timespec="seconds"),
        "metodo": metodo.upper(),
        "rota": rota,
        "id_cliente": id_cliente,
        "resultado": resultado or "Não informado",
    }

    try:
        with AUDIT_FILE.open("a", encoding="utf-8") as arquivo:
            arquivo.write(
                f"{registro['data_hora']} | "
                f"{registro['metodo']} | "
                f"{registro['rota']} | "
                f"{registro['id_cliente']} | "
                f"{registro['resultado']}\n"
            )

    except OSError as erro:
        print(f"Erro ao registrar auditoria: {erro}")
        return None

    return registro
