from ninja import NinjaAPI

from apps.core.exceptions import register_exception_handlers
from apps.accounts.api import router as accounts_router
from apps.cemetery.api import router as cemetery_router
from apps.reservations.api import router as reservations_router
from apps.concessions.api import router as concessions_router
from apps.exhumations.api import router as exhumations_router
from apps.payments.api import router as payments_router
from apps.notifications.api import router as notifications_router
from apps.audit.api import router as audit_router

# On désactive la doc par défaut à cet endroit en mettant docs_url=None
api = NinjaAPI(
    title="API — Gestion de Cimetière GI2",
    version="2.0.0",
    description="API REST (Django Ninja) pour la gestion numérique du cimetière municipal.",
    docs_url=None,  # Désactive la vue automatique boguée
)

register_exception_handlers(api)

api.add_router("", accounts_router)
api.add_router("/cimetiere", cemetery_router)
api.add_router("/reservations", reservations_router)
api.add_router("/concessions", concessions_router)
api.add_router("/exhumations", exhumations_router)
api.add_router("/paiements", payments_router)
api.add_router("/notifications", notifications_router)
api.add_router("/audit", audit_router)