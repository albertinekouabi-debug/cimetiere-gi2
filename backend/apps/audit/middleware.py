import contextvars
from django.conf import settings

# Remplacement de threading.local() par ContextVar pour une compatibilité 
# parfaite avec les environnements synchrones (WSGI) et asynchrones (ASGI).
_current_request_ctx = contextvars.ContextVar("current_request", default=None)


class CurrentRequestMiddleware:
    """
    Rend la requête HTTP courante accessible globalement au sein du cycle de vie
    du thread/contexte actuel (idéal pour capter automatiquement l'IP et l'utilisateur
    au moment où un signal ou un service tiers génère un AuditLog).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # On définit la requête dans le contexte actuel
        token = _current_request_ctx.set(request)
        try:
            response = self.get_response(request)
        finally:
            # Réinitialisation propre du contexte après traitement pour éviter les fuites de mémoire
            _current_request_ctx.reset(token)
        return response


class SecurityCSPMiddleware:
    """
    Middleware de sécurité pour injecter l'en-tête Content-Security-Policy (CSP).
    Utilise la directive moderne 'frame-ancestors' pour autoriser dynamiquement 
    l'intégration de la carte interactive dans l'iframe du frontend Flet.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Récupération sécurisée de la configuration définie dans settings.py
        allowed_origins = getattr(settings, "MAP_EMBED_ALLOWED_ORIGINS", [])
        
        # Si la configuration renvoie une liste/tuple, on fusionne avec des espaces.
        # Sinon, on s'assure que c'est une chaîne ou on utilise une valeur vide par défaut.
        if isinstance(allowed_origins, (list, tuple)):
            origins_str = " ".join(allowed_origins)
        else:
            origins_str = str(allowed_origins)

        # Injection propre de l'en-tête de sécurité
        csp_value = f"frame-ancestors 'self' {origins_str}".strip()
        response["Content-Security-Policy"] = csp_value
        
        return response


def get_current_request():
    """Permet de récupérer la requête en cours n'importe où dans l'application."""
    return _current_request_ctx.get()


def get_client_ip(request=None):
    """
    Extrait l'adresse IP réelle du client.
    Prend en compte le proxy inverse (Render) via l'en-tête HTTP_X_FORWARDED_FOR.
    """
    if request is None:
        request = get_current_request()
        
    if request is None:
        return None

    # En production (Render), l'IP d'origine est le premier élément de X-Forwarded-For
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
        
    return request.META.get("REMOTE_ADDR")