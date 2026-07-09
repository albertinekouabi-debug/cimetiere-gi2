import threading

_thread_locals = threading.local()


class CurrentRequestMiddleware:
    """Rend la requête HTTP courante accessible globalement (pour capter l'IP
    et l'utilisateur au moment où un signal/service écrit un AuditLog)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.request = None
        return response


def get_current_request():
    return getattr(_thread_locals, "request", None)


def get_client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
