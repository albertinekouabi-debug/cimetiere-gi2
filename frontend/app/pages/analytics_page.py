import flet as ft
from app import config as C
from app.components.theme import card_container, loading_indicator, responsive_width, stat_card
from app.components.layout import build_app_shell
from app.components.pie_chart import build_pie_chart, build_pie_legend
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

        pie_data = [
            ("Libre", occupancy.get("libre", 0), C.COLOR_SUCCESS),
            ("Occupé", occupancy.get("occupe", 0), C.COLOR_DANGER),
            ("Réservé", occupancy.get("reserve", 0), C.COLOR_WARNING),
            ("Maintenance", occupancy.get("maintenance", 0), C.COLOR_TEXT_MUTED),
        ]
        max_chart_size = responsive_width(page, max=200, min=140)
        pie_card = card_container(ft.Column([
            ft.Text("Répartition des caveaux par statut", size=15, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
            ft.Container(height=14),
            ft.Row([
                ft.Container(build_pie_chart(pie_data, size=max_chart_size), alignment=ft.Alignment.CENTER),
                ft.Container(build_pie_legend(pie_data), expand=True, padding=ft.Padding.only(left=20)),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
        ]))

        top_row_items = [
            ft.Container(stat_card("Taux d'occupation global", f"{occupancy['taux_occupation']}%", ft.Icons.PIE_CHART_OUTLINE, C.COLOR_WARNING), col={"sm": 6, "md": 3}),
            ft.Container(stat_card("Caveaux au total", str(occupancy["total"]), ft.Icons.SQUARE_OUTLINED, C.COLOR_INFO), col={"sm": 6, "md": 3}),
        ]
        if reservation_stats:
            top_row_items += [
                ft.Container(stat_card("Réservations validées", str(reservation_stats["validee"]), ft.Icons.CHECK_CIRCLE_OUTLINE, C.COLOR_SUCCESS), col={"sm": 6, "md": 3}),
                ft.Container(stat_card("Réservations ce mois", str(reservation_stats["ce_mois"]), ft.Icons.CALENDAR_MONTH, C.COLOR_ACCENT), col={"sm": 6, "md": 3}),
            ]

        blocks = [ft.ResponsiveRow(top_row_items, spacing=16, run_spacing=16), ft.Container(height=20), pie_card]

        if reservation_stats:
            res_pie_data = [
                ("En attente", reservation_stats.get("en_attente", 0), C.COLOR_WARNING),
                ("Validées", reservation_stats.get("validee", 0), C.COLOR_SUCCESS),
                ("Refusées", reservation_stats.get("refusee", 0), C.COLOR_DANGER),
            ]
            res_pie_card = card_container(ft.Column([
                ft.Text("Répartition des réservations par statut", size=15, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
                ft.Container(height=14),
                ft.Row([
                    ft.Container(build_pie_chart(res_pie_data, size=max_chart_size), alignment=ft.Alignment.CENTER),
                    ft.Container(build_pie_legend(res_pie_data), expand=True, padding=ft.Padding.only(left=20)),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True),
            ]))
            blocks += [ft.Container(height=20), res_pie_card]

        if financial_stats:
            blocks += [ft.Container(height=20), ft.ResponsiveRow([
                ft.Container(stat_card("Revenus du mois", f"{financial_stats['revenus_mois']:,.0f} FCFA".replace(",", " "), ft.Icons.CALENDAR_MONTH, C.COLOR_SUCCESS), col={"sm": 6, "md": 4}),
                ft.Container(stat_card("Revenus de l'année", f"{financial_stats['revenus_annee']:,.0f} FCFA".replace(",", " "), ft.Icons.INSIGHTS_OUTLINED, C.COLOR_INFO), col={"sm": 6, "md": 4}),
                ft.Container(stat_card("Revenus totaux", f"{financial_stats['total_revenus']:,.0f} FCFA".replace(",", " "), ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, C.COLOR_ACCENT), col={"sm": 6, "md": 4}),
            ], spacing=16, run_spacing=16)]

        content_holder.controls = blocks
        page.update()

    load()

    return build_app_shell(page, ctx, ft.Column([content_holder], scroll=ft.ScrollMode.AUTO), "/analytique", "Analytique")
