
import re

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def normalizar_email(email):
    if not isinstance(email, str):
        return None

    email = email.strip().lower()

    if not email or "@" not in email:
        return None

    usuario, dominio = email.rsplit("@", 1)

    try:
        dominio = dominio.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    return f"{usuario}@{dominio}"


def validar_email(email):
    email = normalizar_email(email)

    if email is None:
        return False

    return bool(EMAIL_REGEX.fullmatch(email))
