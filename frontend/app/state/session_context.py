"""
Contexte de session — instancié UNE FOIS PAR CONNEXION FLET (dans main(page)).

Point critique en mode Flet web : le serveur Flet gère plusieurs utilisateurs
simultanément dans le même process Python. Toute variable module-level
("singleton") serait partagée entre TOUS les utilisateurs connectés, ce qui
provoquerait une fuite de jetons JWT et de données entre sessions.
SessionContext élimine ce risque : chaque page/session possède sa propre
instance de ApiClient (donc ses propres jetons) et son propre état.
"""

from typing import Optional

from app.services.api_client import ApiClient
from app.services.auth_service import AuthService
from app.services.cemetery_service import CemeteryService
from app.services.reservation_service import ReservationService
from app.services.concession_service import ConcessionService
from app.services.exhumation_service import ExhumationService
from app.services.payment_service import PaymentService
from app.services.misc_services import UserService, NotificationService, AuditService


class SessionContext:
    """Un objet de ce type est créé par connexion utilisateur et transmis
    à toutes les pages via closure/attribut de page."""

    def __init__(self):
        self.client = ApiClient()
        self.profile: Optional[dict] = None

        # Services métier, tous branchés sur le même client HTTP (donc les
        # mêmes jetons JWT et le même utilisateur pour toute la session).
        self.auth = AuthService(self.client)
        self.cemetery = CemeteryService(self.client)
        self.reservations = ReservationService(self.client)
        self.concessions = ConcessionService(self.client)
        self.exhumations = ExhumationService(self.client)
        self.payments = PaymentService(self.client)
        self.users = UserService(self.client)
        self.notifications = NotificationService(self.client)
        self.audit = AuditService(self.client)

    # ─── État d'authentification ──────────────────────────────────────────
    @property
    def is_authenticated(self) -> bool:
        return self.profile is not None

    @property
    def role(self) -> Optional[str]:
        return self.profile["role"] if self.profile else None

    @property
    def full_name(self) -> str:
        return self.profile.get("full_name", "") if self.profile else ""

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role in ("admin", "gestionnaire")

    @property
    def is_staff(self) -> bool:
        return self.role in ("admin", "gestionnaire", "agent")

    def set_profile(self, profile: dict):
        self.profile = profile

    def logout(self):
        self.auth.logout()
        self.profile = None

    def close(self):
        self.client.close()
