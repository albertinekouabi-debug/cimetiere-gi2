from ninja import NinjaAPI
from ninja.errors import HttpError
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import logging

logger = logging.getLogger("cimetiere")


def register_exception_handlers(api: NinjaAPI):
    @api.exception_handler(HttpError)
    def http_error_handler(request, exc: HttpError):
        return api.create_response(request, {"detail": str(exc)}, status=exc.status_code)

    @api.exception_handler(ObjectDoesNotExist)
    def not_found_handler(request, exc):
        return api.create_response(request, {"detail": "Ressource introuvable."}, status=404)

    @api.exception_handler(IntegrityError)
    def integrity_error_handler(request, exc):
        logger.warning("IntegrityError: %s", exc)
        return api.create_response(
            request,
            {"detail": "Opération refusée : contrainte d'intégrité (référence encore utilisée ou doublon)."},
            status=409,
        )

    @api.exception_handler(Exception)
    def generic_error_handler(request, exc):
        logger.exception("Erreur non gérée")
        return api.create_response(request, {"detail": "Erreur interne du serveur."}, status=500)
