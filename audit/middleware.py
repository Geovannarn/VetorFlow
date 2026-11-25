from audit.logger import registrar


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resposta = self.get_response(request)

        if not request.path.startswith("/static/"):
            ip = request.META.get("REMOTE_ADDR", "-")
            registrar(
                "ACESSO",
                ip,
                f"{request.method} {request.get_full_path()} -> {resposta.status_code}",
            )

        return resposta