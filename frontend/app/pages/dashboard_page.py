import flet as ft
from app import config as C
from app.components.theme import stat_card, card_container, loading_indicator
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext


def build_dashboard_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    content_holder = ft.Column([loading_indicator()], expand=True)

    def load_data():
        try:
            occupancy = ctx.cemetery.occupancy_stats()
        except ApiError:
            occupancy = {"total": 0, "libre": 0, "occupe": 0, "reserve": 0, "maintenance": 0, "taux_occupation": 0}

        reservation_stats = {"en_attente": 0, "total": 0}
        if ctx.is_staff:
            try:
                reservation_stats = ctx.reservations.stats()
            except ApiError:
                pass

        financial_stats = {"revenus_mois": 0, "total_revenus": 0}
        if ctx.is_manager:
            try:
                financial_stats = ctx.payments.stats()
            except ApiError:
                pass

        stats_row = ft.ResponsiveRow([
            ft.Container(stat_card("Caveaux au total", str(occupancy["total"]), ft.Icons.SQUARE_OUTLINED, C.COLOR_INFO), col={"sm": 6, "md": 3}),
            ft.Container(stat_card("Caveaux libres", str(occupancy["libre"]), ft.Icons.CHECK_CIRCLE_OUTLINE, C.COLOR_SUCCESS), col={"sm": 6, "md": 3}),
            ft.Container(stat_card("Taux d'occupation", f"{occupancy['taux_occupation']}%", ft.Icons.PIE_CHART_OUTLINE, C.COLOR_WARNING), col={"sm": 6, "md": 3}),
            ft.Container(stat_card("Réservations en attente", str(reservation_stats.get("en_attente", 0)), ft.Icons.BOOKMARK_OUTLINE, C.COLOR_ACCENT), col={"sm": 6, "md": 3}),
        ], spacing=16, run_spacing=16)

        occupancy_breakdown = card_container(
            ft.Column([
                ft.Text("Répartition des caveaux", size=15, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
                ft.Container(height=10),
                _bar_row("Libre", occupancy["libre"], occupancy["total"], C.COLOR_SUCCESS),
                _bar_row("Occupé", occupancy["occupe"], occupancy["total"], C.COLOR_DANGER),
                _bar_row("Réservé", occupancy["reserve"], occupancy["total"], C.COLOR_WARNING),
                _bar_row("Maintenance", occupancy["maintenance"], occupancy["total"], C.COLOR_TEXT_MUTED),
            ], spacing=10),
        )

        blocks = [stats_row, ft.Container(height=20), occupancy_breakdown]

        if ctx.is_manager:
            blocks += [ft.Container(height=20), ft.ResponsiveRow([
                ft.Container(stat_card("Revenus du mois", f"{financial_stats.get('revenus_mois', 0):,.0f} FCFA".replace(",", " "), ft.Icons.PAYMENTS_OUTLINED, C.COLOR_SUCCESS), col={"sm": 6, "md": 4}),
                ft.Container(stat_card("Revenus totaux", f"{financial_stats.get('total_revenus', 0):,.0f} FCFA".replace(",", " "), ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, C.COLOR_INFO), col={"sm": 6, "md": 4}),
            ], spacing=16, run_spacing=16)]

        content_holder.controls = blocks
        page.update()

    def _bar_row(label, value, total, color):
        pct = (value / total * 100) if total else 0
        return ft.Column([
            ft.Row([ft.Text(label, size=13, color=C.COLOR_TEXT), ft.Container(expand=True), ft.Text(str(value), size=13, color=C.COLOR_TEXT_MUTED)]),
            ft.ProgressBar(value=pct / 100, color=color, bgcolor=C.COLOR_SURFACE_LIGHT, height=8, border_radius=4),
        ], spacing=4)

    load_data()

    return build_app_shell(page, ctx, ft.Column([content_holder], scroll=ft.ScrollMode.AUTO), "/dashboard", "Tableau de bord")
