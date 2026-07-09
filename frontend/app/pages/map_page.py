import flet as ft
from flet_webview import WebView
from app import config as C
from app.components.layout import build_app_shell
from app.state.session_context import SessionContext


def build_map_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    """
    Carte interactive Google Maps du Cimetière Municipal de Vindoulou.
    La carte elle-même (marqueurs colorés par statut, filtres, contour du
    site) est une page HTML servie par le backend Django
    (/cimetiere/carte-embed/), embarquée ici via un contrôle WebView.
    Ce découpage évite toute duplication de logique cartographique entre
    frontend et backend, et permet à la carte de fonctionner même si l'on
    y accède directement depuis un navigateur (hors app Flet).
    """
    webview = WebView(url=C.MAP_EMBED_URL, expand=True)

    content = ft.Container(content=webview, expand=True, border_radius=10, clip_behavior=ft.ClipBehavior.ANTI_ALIAS)

    return build_app_shell(page, ctx, content, "/carte", "Carte interactive du cimetière", scrollable=False)
