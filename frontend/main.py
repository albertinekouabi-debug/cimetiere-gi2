"""
Point d'entrée de l'application Flet (mode web).

Une instance de SessionContext est créée PAR CONNEXION (paramètre `page` de
main()), garantissant l'isolation totale des jetons/données entre
utilisateurs simultanés.
"""

import flet as ft
import os

from app.config import APP_TITLE, APP_PORT
from app.components.theme import apply_page_theme
from app.state.session_context import SessionContext
from app.services.api_client import ApiError

from app.pages.login_page import build_login_view
from app.pages.public_search_page import build_public_search_view
from app.pages.dashboard_page import build_dashboard_view
from app.pages.map_page import build_map_view
from app.pages.sections_page import build_sections_view
from app.pages.blocs_page import build_blocs_view
from app.pages.graves_page import build_graves_view
from app.pages.reservations_page import build_reservations_view
from app.pages.concessions_page import build_concessions_view
from app.pages.paiements_page import build_paiements_view
from app.pages.exhumations_page import build_exhumations_view
from app.pages.analytics_page import build_analytics_view
from app.pages.users_page import build_users_view
from app.pages.audit_page import build_audit_view


PUBLIC_ROUTES = {"/login", "/recherche"}

PROTECTED_ROUTES = {
    "/dashboard": (build_dashboard_view, None),
    "/carte": (build_map_view, None),
    "/sections": (build_sections_view, None),
    "/blocs": (build_blocs_view, None),
    "/caveaux": (build_graves_view, None),
    "/reservations": (build_reservations_view, None),
    "/concessions": (build_concessions_view, {"admin", "gestionnaire"}),
    "/paiements": (build_paiements_view, {"admin", "gestionnaire"}),
    "/exhumations": (build_exhumations_view, None),
    "/analytique": (build_analytics_view, None),
    "/utilisateurs": (build_users_view, {"admin"}),
    "/audit": (build_audit_view, {"admin"}),
}


def main(page: ft.Page):

    page.title = APP_TITLE
    apply_page_theme(page)

    ctx = SessionContext()

    # ------------------------------------------------------------------
    # Compatibilité Flet 0.85.x
    # ------------------------------------------------------------------

    HAS_CLIENT_STORAGE = hasattr(page, "client_storage")

    def storage_get(key):
        if HAS_CLIENT_STORAGE:
            return page.client_storage.get(key)
        return None

    def storage_set(key, value):
        if HAS_CLIENT_STORAGE:
            page.client_storage.set(key, value)

    def storage_remove(key):
        if HAS_CLIENT_STORAGE:
            page.client_storage.remove(key)

    # ------------------------------------------------------------------
    # Session persistante
    # ------------------------------------------------------------------

    def try_restore_session():

        stored_refresh = storage_get("refresh_token")

        if not stored_refresh:
            return False

        ctx.client.refresh_token = stored_refresh

        if not ctx.client._try_refresh():
            storage_remove("refresh_token")
            return False

        try:
            profile = ctx.auth.me()

            ctx.set_profile(profile)

            storage_set(
                "refresh_token",
                ctx.client.refresh_token,
            )

            return True

        except ApiError:
            storage_remove("refresh_token")
            return False

    def persist_session():

        if ctx.client.refresh_token:
            storage_set(
                "refresh_token",
                ctx.client.refresh_token,
            )

    def clear_persisted_session():

        storage_remove("refresh_token")

    # ------------------------------------------------------------------
    # Hooks login / logout
    # ------------------------------------------------------------------

    original_set_profile = ctx.set_profile

    def set_profile_and_persist(profile):

        original_set_profile(profile)
        persist_session()

    ctx.set_profile = set_profile_and_persist

    original_logout = ctx.logout

    def logout_and_clear():

        original_logout()
        clear_persisted_session()

    ctx.logout = logout_and_clear

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def route_change(e: ft.RouteChangeEvent):

        route = page.route

        if route in PUBLIC_ROUTES:

            page.views.clear()

            if route == "/login":
                page.views.append(
                    build_login_view(page, ctx)
                )
            else:
                page.views.append(
                    build_public_search_view(page, ctx)
                )

            page.update()
            return

        if not ctx.is_authenticated:
            page.go("/login")
            return

        entry = PROTECTED_ROUTES.get(route)

        if entry is None:
            page.go("/dashboard")
            return

        builder, allowed_roles = entry

        if (
            allowed_roles is not None
            and ctx.role not in allowed_roles
        ):
            page.go("/dashboard")
            return

        page.views.clear()
        page.views.append(builder(page, ctx))
        page.update()

    def view_pop(e: ft.ViewPopEvent):

        if len(page.views) > 1:
            page.views.pop()

        top_view = page.views[-1]
        page.go(top_view.route)

    # ------------------------------------------------------------------
    # Réactivité au redimensionnement (bascule desktop <-> mobile en direct)
    # ------------------------------------------------------------------
    from app.components.layout import is_mobile

    _last_mobile_state = {"value": is_mobile(page)}

    def on_resize(e: ft.PageResizeEvent):
        current_mobile = is_mobile(page)
        if current_mobile != _last_mobile_state["value"]:
            _last_mobile_state["value"] = current_mobile
            # Ne reconstruit que si le mode (mobile/desktop) a réellement
            # changé, pour éviter des reconstructions inutiles pendant un
            # redimensionnement continu (glisser-déposer du bord de fenêtre).
            if page.route and page.route not in ("", "/"):
                route_change(None)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.on_resize = on_resize

    # ------------------------------------------------------------------
    # Démarrage
    # ------------------------------------------------------------------

    if try_restore_session():
        page.go(
            page.route
            if page.route not in ("", "/")
            else "/dashboard"
        )
    else:
        page.go(
            page.route
            if page.route in PUBLIC_ROUTES
            else "/login"
        )


if __name__ == "__main__":
    # Render fournit la variable 'PORT'. Si elle est absente, on utilise APP_PORT (local)
    render_port = int(os.environ.get("PORT", APP_PORT))
    
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=render_port,
        host="0.0.0.0"  # Indispensable pour que le proxy de Render puisse rediriger le trafic
    )