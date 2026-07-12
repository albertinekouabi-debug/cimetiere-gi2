import flet as ft
from app import config as C
from app.components.theme import loading_indicator, stat_card
from app.components.layout import build_app_shell
from app.components.pie_chart import build_pie_section
from app.services.api_client import ApiError
from app.state.session_context import SessionContext


def build_analytics_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    content_holder = ft.Column([loading_indicator()])

    def load():
        try:
            occupancy = ctx.cemetery.occupancy_stats()
        except ApiError:
            occupancy = {"total": 0, "libre": 0, "occupe": 0, "reserve": 0, "maintenance": 0, "taux_occupation": 0}

        reservation_stats = None
        if ctx.is_staff:
            try:
                reservation_stats = ctx.reservations.stats()
            except ApiError:
                pass

        financial_stats = None
        if ctx.is_manager:
            try:
                financial_stats = ctx.payments.stats()
            except ApiError:
                pass

        top_row_items = [
            ft.Container(stat_card("Taux d'occupation global", f"{occupancy['taux_occupation']}%", ft.Icons.PIE_CHART_OUTLINE, C.COLOR_WARNING), col={"xs": 12, "sm": 6, "md": 3}),
            ft.Container(stat_card("Caveaux au total", str(occupancy["total"]), ft.Icons.SQUARE_OUTLINED, C.COLOR_INFO), col={"xs": 12, "sm": 6, "md": 3}),
        ]
        if reservation_stats:
            top_row_items += [
                ft.Container(stat_card("Réservations validées", str(reservation_stats["validee"]), ft.Icons.CHECK_CIRCLE_OUTLINE, C.COLOR_SUCCESS), col={"xs": 12, "sm": 6, "md": 3}),
                ft.Container(stat_card("Réservations ce mois", str(reservation_stats["ce_mois"]), ft.Icons.CALENDAR_MONTH, C.COLOR_ACCENT), col={"xs": 12, "sm": 6, "md": 3}),
            ]

        # Chaque camembert est assemblé dans sa propre carte, toujours en
        # disposition empilée (voir pie_chart.build_pie_section) : c'est
        # délibérément simple pour rester fiable sur toutes les tailles
        # d'écran, après qu'une disposition côte-à-côte plus "élégante" a
        # produit un espace vide énorme et imprévisible sur mobile.
        occupancy_pie_data = [
            ("Libre", occupancy.get("libre", 0), C.COLOR_SUCCESS),
            ("Occupé", occupancy.get("occupe", 0), C.COLOR_DANGER),
            ("Réservé", occupancy.get("reserve", 0), C.COLOR_WARNING),
            ("Maintenance", occupancy.get("maintenance", 0), C.COLOR_TEXT_MUTED),
        ]

        blocks = [
            ft.ResponsiveRow(top_row_items, spacing=16, run_spacing=16),
            ft.Container(height=20),
            build_pie_section("Répartition des caveaux par statut", occupancy_pie_data, page),
        ]

        if reservation_stats:
            res_pie_data = [
                ("En attente", reservation_stats.get("en_attente", 0), C.COLOR_WARNING),
                ("Validées", reservation_stats.get("validee", 0), C.COLOR_SUCCESS),
                ("Refusées", reservation_stats.get("refusee", 0), C.COLOR_DANGER),
            ]
            blocks += [
                ft.Container(height=20),
                build_pie_section("Répartition des réservations par statut", res_pie_data, page),
            ]

        if financial_stats:
            blocks += [ft.Container(height=20), ft.ResponsiveRow([
                ft.Container(stat_card("Revenus du mois", f"{financial_stats['revenus_mois']:,.0f} FCFA".replace(",", " "), ft.Icons.CALENDAR_MONTH, C.COLOR_SUCCESS), col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(stat_card("Revenus de l'année", f"{financial_stats['revenus_annee']:,.0f} FCFA".replace(",", " "), ft.Icons.INSIGHTS_OUTLINED, C.COLOR_INFO), col={"xs": 12, "sm": 6, "md": 4}),
                ft.Container(stat_card("Revenus totaux", f"{financial_stats['total_revenus']:,.0f} FCFA".replace(",", " "), ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, C.COLOR_ACCENT), col={"xs": 12, "sm": 6, "md": 4}),
            ], spacing=16, run_spacing=16)]

        content_holder.controls = blocks
        page.update()

    load()

    return build_app_shell(page, ctx, ft.Column([content_holder], scroll=ft.ScrollMode.AUTO), "/analytique", "Analytique")
