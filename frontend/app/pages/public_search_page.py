import flet as ft
from app import config as C
from app.components.theme import text_field, primary_button, card_container, empty_state, loading_indicator, responsive_width
from app.services.api_client import ApiError
from app.state.session_context import SessionContext


def build_public_search_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    query_field = text_field("Nom ou prénom du défunt", width=responsive_width(page, max=400, min=280), autofocus=True)
    results_column = ft.Column(spacing=12)
    status_text = ft.Text("", color=C.COLOR_TEXT_MUTED, size=13)

    def render_results(defunts):
        results_column.controls.clear()
        if not defunts:
            results_column.controls.append(empty_state("Aucun résultat pour cette recherche."))
        for d in defunts:
            results_column.controls.append(
                card_container(
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON_OUTLINE, color=C.COLOR_ACCENT, size=28),
                        ft.Column([
                            ft.Text(f"{d['prenom']} {d['nom']}", size=16, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
                            ft.Text(f"Décès : {d['date_deces']}", size=12, color=C.COLOR_TEXT_MUTED),
                            ft.Text(f"Caveau : {d.get('grave_numero') or 'Non localisé'}", size=12, color=C.COLOR_TEXT_MUTED),
                        ], spacing=2, expand=True),
                    ], spacing=14),
                )
            )
        page.update()

    def do_search(e):
        if not query_field.value or len(query_field.value.strip()) < 2:
            status_text.value = "Saisissez au moins 2 caractères."
            page.update()
            return
        status_text.value = ""
        results_column.controls = [loading_indicator()]
        page.update()
        try:
            defunts = ctx.cemetery.search_defunts(query_field.value.strip())
            render_results(defunts)
        except ApiError as err:
            results_column.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()

    query_field.on_submit = do_search

    header = ft.Column([
        ft.Icon(ft.Icons.CHURCH_OUTLINED, color=C.COLOR_ACCENT, size=38),
        ft.Text("Recherche publique", size=22, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
        ft.Text("Retrouvez un défunt inhumé au Cimetière Municipal de Vindoulou", size=13, color=C.COLOR_TEXT_MUTED),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

    search_row = ft.Row([query_field, primary_button("Rechercher", icon=ft.Icons.SEARCH, on_click=do_search)],
                         alignment=ft.MainAxisAlignment.CENTER)

    content = ft.Container(
        content=ft.Column([
            header, ft.Container(height=20), search_row, status_text, ft.Container(height=20),
            ft.Container(content=results_column, width=responsive_width(page, max=560, min=320)),
            ft.Container(height=20),
            ft.TextButton("Espace personnel", on_click=lambda e: page.go("/login"), style=ft.ButtonStyle(color=C.COLOR_TEXT_MUTED)),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6, scroll=ft.ScrollMode.AUTO),
        alignment=ft.Alignment.TOP_CENTER,
        padding=40,
        expand=True,
    )

    return ft.View(route="/recherche", bgcolor=C.COLOR_BG, controls=[content])
