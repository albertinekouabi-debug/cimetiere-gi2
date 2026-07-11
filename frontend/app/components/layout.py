"""Coquille applicative : barre latérale de navigation + zone de contenu.
Le menu affiché dépend du rôle de l'utilisateur connecté (RBAC côté UI —
la sécurité réelle reste appliquée côté backend).

Responsive : en dessous de MOBILE_BREAKPOINT (768px), la barre latérale
permanente est remplacée par un tiroir de navigation natif Flet
(NavigationDrawer, ouvert/fermé via page.show_drawer()/close_drawer()),
avec recouvrement (scrim) et fermeture automatique après navigation —
comportement géré nativement par Flet, pas de réimplémentation manuelle.
"""
import flet as ft
from app import config as C
from app.components.theme import responsive_width
from app.state.session_context import SessionContext

MOBILE_BREAKPOINT = 768

NAV_ITEMS = [
    # (route, label, icon, roles autorisés)
    ("/dashboard", "Tableau de bord", ft.Icons.DASHBOARD_OUTLINED, {"admin", "gestionnaire", "agent"}),
    ("/carte", "Carte interactive", ft.Icons.MAP_OUTLINED, {"admin", "gestionnaire", "agent"}),
    ("/sections", "Sections", ft.Icons.GRID_VIEW_OUTLINED, {"admin", "gestionnaire", "agent"}),
    ("/blocs", "Blocs", ft.Icons.VIEW_MODULE_OUTLINED, {"admin", "gestionnaire", "agent"}),
    ("/caveaux", "Caveaux", ft.Icons.SQUARE_OUTLINED, {"admin", "gestionnaire", "agent"}),
    ("/reservations", "Réservations", ft.Icons.BOOKMARK_OUTLINE, {"admin", "gestionnaire", "agent"}),
    ("/concessions", "Concessions", ft.Icons.DESCRIPTION_OUTLINED, {"admin", "gestionnaire"}),
    ("/paiements", "Paiements", ft.Icons.PAYMENTS_OUTLINED, {"admin", "gestionnaire"}),
    ("/exhumations", "Exhumations", ft.Icons.SWAP_VERT, {"admin", "gestionnaire", "agent"}),
    ("/analytique", "Analytique", ft.Icons.INSIGHTS_OUTLINED, {"admin", "gestionnaire", "agent"}),
    ("/utilisateurs", "Utilisateurs", ft.Icons.PEOPLE_OUTLINE, {"admin"}),
    ("/audit", "Journal d'audit", ft.Icons.HISTORY, {"admin"}),
]


def is_mobile(page: ft.Page) -> bool:
    """Détecte le mode mobile/tablette. Si la largeur n'est pas encore
    connue (tout premier rendu avant que le client ne la communique), on
    suppose le mode desktop par défaut ; on_resize corrigera dès que
    possible."""
    width = getattr(page, "width", None)
    return width is not None and width < MOBILE_BREAKPOINT


def _nav_items_column(page: ft.Page, ctx: SessionContext, active_route: str, on_navigate) -> ft.Column:
    """Construit la liste des liens de navigation. `on_navigate(route)` est
    appelé au clic — permet de mutualiser le contenu entre la sidebar fixe
    (desktop) et le tiroir de navigation (mobile)."""
    items = []
    for route, label, icon, roles in NAV_ITEMS:
        if ctx.role not in roles:
            continue
        is_active = route == active_route
        items.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=20, color=C.COLOR_ACCENT if is_active else C.COLOR_TEXT_MUTED),
                    ft.Text(label, size=14, color=C.COLOR_TEXT if is_active else C.COLOR_TEXT_MUTED,
                             weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                             overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=12),
                padding=ft.Padding(16, 12, 16, 12),
                bgcolor=C.COLOR_SURFACE_LIGHT if is_active else None,
                border_radius=8,
                on_click=(lambda e, r=route: on_navigate(r)),
                ink=True,
                margin=ft.Margin(8, 2, 8, 2),
            )
        )
    return ft.Column(items, spacing=0)


def _user_footer(ctx: SessionContext, on_logout) -> ft.Container:
    return ft.Container(
        padding=16,
        content=ft.Column([
            ft.Row([
                ft.CircleAvatar(content=ft.Text(ctx.full_name[:1].upper() if ctx.full_name else "?"),
                                 bgcolor=C.COLOR_PRIMARY, color="#ffffff", radius=16),
                ft.Column([
                    ft.Text(ctx.full_name or "Utilisateur", size=13, color=C.COLOR_TEXT, weight=ft.FontWeight.BOLD,
                             overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(C.ROLE_LABELS.get(ctx.role, ctx.role or ""), size=11, color=C.COLOR_TEXT_MUTED),
                ], spacing=0, expand=True),
            ], spacing=10),
            ft.TextButton(content=ft.Text("Déconnexion"), icon=ft.Icons.LOGOUT, on_click=on_logout,
                          style=ft.ButtonStyle(color=C.COLOR_DANGER)),
        ], spacing=10),
    )


def _brand_header() -> ft.Container:
    return ft.Container(
        padding=20,
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.CHURCH_OUTLINED, color=C.COLOR_ACCENT, size=26),
                    ft.Text("Cimetière", size=18, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT)]),
            ft.Text("Municipal de Vindoulou", size=11, color=C.COLOR_TEXT_MUTED),
        ], spacing=4),
    )


def build_sidebar(page: ft.Page, ctx: SessionContext, active_route: str) -> ft.Container:
    """Barre latérale permanente (mode desktop, largeur >= MOBILE_BREAKPOINT)."""
    def navigate(route):
        page.go(route)

    def logout(e):
        ctx.logout()
        page.go("/login")

    return ft.Container(
        width=responsive_width(page, max=250, min=220),
        bgcolor=C.COLOR_SURFACE,
        border=ft.Border.only(right=ft.BorderSide(1, C.COLOR_BORDER)),
        content=ft.Column([
            _brand_header(),
            ft.Divider(color=C.COLOR_BORDER, height=1),
            ft.Container(content=_nav_items_column(page, ctx, active_route, navigate), expand=True,
                         padding=ft.Padding.only(top=8)),
            ft.Divider(color=C.COLOR_BORDER, height=1),
            _user_footer(ctx, logout),
        ], spacing=0, expand=True),
    )


def build_nav_drawer(page: ft.Page, ctx: SessionContext, active_route: str) -> ft.NavigationDrawer:
    """Tiroir de navigation natif Flet pour le mode mobile/tablette.
    Ouvert via page.show_drawer(), fermé via page.close_drawer() — Flet gère
    nativement le recouvrement (scrim), l'animation et la fermeture au clic
    en dehors du tiroir."""
    async def navigate(route):
        await page.close_drawer()
        page.go(route)

    async def logout(e):
        await page.close_drawer()
        ctx.logout()
        page.go("/login")

    def sync_navigate(route):
        page.run_task(navigate, route)

    return ft.NavigationDrawer(
        bgcolor=C.COLOR_SURFACE,
        controls=[
            _brand_header(),
            ft.Divider(color=C.COLOR_BORDER, height=1),
            ft.Container(content=_nav_items_column(page, ctx, active_route, sync_navigate),
                         padding=ft.Padding.only(top=8)),
            ft.Divider(color=C.COLOR_BORDER, height=1),
            _user_footer(ctx, logout),
        ],
    )


def build_notification_bell(page: ft.Page, ctx: SessionContext) -> ft.Control:
    """Icône cloche avec badge de notifications non lues. Le clic ouvre un
    dialogue listant les notifications, avec marquage individuel/global."""
    try:
        unread = ctx.notifications.unread_count().get("count", 0)
    except Exception:
        unread = 0

    def open_panel(e):
        try:
            notifications = ctx.notifications.list()
        except Exception:
            notifications = []

        def mark_read(notif_id):
            try:
                ctx.notifications.mark_read(notif_id)
            except Exception:
                pass
            page.pop_dialog()
            page.go(page.route)  # rafraîchit la vue (et donc le badge)

        def mark_all_read(e2):
            try:
                ctx.notifications.mark_all_read()
            except Exception:
                pass
            page.pop_dialog()
            page.go(page.route)

        def close_dialog(e2=None):
            page.pop_dialog()

        if not notifications:
            items = [ft.Text("Aucune notification pour le moment.", color=C.COLOR_TEXT_MUTED, size=13)]
        else:
            items = []
            for n in notifications[:30]:
                items.append(
                    ft.Container(
                        padding=10, border_radius=8,
                        bgcolor=C.COLOR_SURFACE_LIGHT if not n["is_read"] else None,
                        content=ft.Column([
                            ft.Text(n["titre"], size=13, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
                            ft.Text(n["message"], size=12, color=C.COLOR_TEXT_MUTED),
                            ft.Text(n["created_at"][:16].replace("T", " "), size=10, color=C.COLOR_TEXT_MUTED),
                        ], spacing=2),
                        on_click=(lambda e2, nid=n["id"]: mark_read(nid)) if not n["is_read"] else None,
                        ink=not n["is_read"],
                    )
                )

        dialog = ft.AlertDialog(
            modal=True, bgcolor=C.COLOR_SURFACE,
            title=ft.Row([
                ft.Text("Notifications", color=C.COLOR_TEXT),
                ft.Container(expand=True),
                ft.TextButton("Tout marquer comme lu", on_click=mark_all_read, style=ft.ButtonStyle(color=C.COLOR_PRIMARY)),
            ]),
            content=ft.Container(
                content=ft.Column(items, spacing=6, scroll=ft.ScrollMode.AUTO),
                width=responsive_width(page, max=380, min=260),
                height=420,
            ),
            actions=[ft.TextButton("Fermer", on_click=close_dialog, style=ft.ButtonStyle(color=C.COLOR_TEXT_MUTED))],
        )
        page.show_dialog(dialog)

    icon = ft.IconButton(ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=C.COLOR_TEXT_MUTED, on_click=open_panel,
                          badge=ft.Badge(label=str(unread), bgcolor=C.COLOR_DANGER) if unread > 0 else None)
    return icon


def build_app_shell(page: ft.Page, ctx: SessionContext, content: ft.Control, active_route: str, title: str, scrollable: bool = True) -> ft.View:
    mobile = is_mobile(page)

    topbar_children = []
    drawer = None
    if mobile:
        drawer = build_nav_drawer(page, ctx, active_route)

        async def open_drawer(e):
            await page.show_drawer()

        topbar_children.append(ft.IconButton(ft.Icons.MENU, icon_color=C.COLOR_TEXT, on_click=open_drawer))

    topbar_children.extend([
        ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT,
                 overflow=ft.TextOverflow.ELLIPSIS, expand=True),
        build_notification_bell(page, ctx),
    ])

    topbar = ft.Container(
        padding=ft.Padding(16 if mobile else 28, 14 if mobile else 18, 16 if mobile else 28, 14 if mobile else 18),
        border=ft.Border.only(bottom=ft.BorderSide(1, C.COLOR_BORDER)),
        content=ft.Row(topbar_children, spacing=8),
    )

    body_padding = 14 if mobile else 28
    if scrollable:
        body = ft.Container(content=content, padding=body_padding, expand=True)
        main_area = ft.Container(content=ft.Column([body], scroll=ft.ScrollMode.AUTO), expand=True)
    else:
        # Mode plein-écran (ex: carte) : pas de wrapper scrollable, qui
        # donnerait une hauteur non bornée et casserait les contrôles
        # nécessitant une taille explicite (WebView).
        main_area = ft.Container(content=content, padding=body_padding // 2, expand=True)

    if mobile:
        # Pas de sidebar permanente : navigation via le tiroir (icône menu).
        return ft.View(
            route=active_route,
            padding=0,
            bgcolor=C.COLOR_BG,
            drawer=drawer,
            controls=[
                ft.Column([topbar, main_area], spacing=0, expand=True),
            ],
        )

    return ft.View(
        route=active_route,
        padding=0,
        bgcolor=C.COLOR_BG,
        controls=[
            ft.Row([
                build_sidebar(page, ctx, active_route),
                ft.Column([topbar, main_area], spacing=0, expand=True),
            ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
        ],
    )