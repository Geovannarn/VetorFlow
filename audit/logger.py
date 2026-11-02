from datetime import datetime
from pathlib import Path


AUDIT_FILE = Path(__file__).resolve().parent / "audit.log"


def registrar_operacao(metodo, rota, id_cliente=None, resultado=None):
    registro = {
        "data_hora": datetime.now().isoformat(),
        "metodo": metodo,
        "rota": rota,
        "id_cliente": id_cliente,
        "resultado": resultado,
    }

    with open(AUDIT_FILE, "a", encoding="utf-8") as arquivo:
        arquivo.write(
            f"{registro['data_hora']} | "
            f"{registro['metodo']} | "
            f"{registro['rota']} | "
            f"{registro['id_cliente']} | "
            f"{registro['resultado']}\n"
        )

    print(registro)

    return registro