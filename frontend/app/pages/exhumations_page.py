import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, status_badge, responsive_width
from app.components.data_table import form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext

STATUS_FLOW = {"planifie": "en_cours", "en_cours": "termine"}
STATUS_LABELS = {"planifie": "Démarrer", "en_cours": "Terminer"}


def build_exhumations_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            exhumations = ctx.exhumations.list()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        if not exhumations:
            list_container.controls = [ft.Text("Aucune exhumation planifiée.", color=C.COLOR_TEXT_MUTED)]
            page.update()
            return

        cards = []
        for ex in exhumations:
            actions = []
            next_status = STATUS_FLOW.get(ex["status"])
            if ctx.is_manager and next_status:
                actions.append(ft.TextButton(STATUS_LABELS[ex["status"]], icon=ft.Icons.ARROW_FORWARD,
                                              style=ft.ButtonStyle(color=C.COLOR_PRIMARY),
                                              on_click=lambda e, eid=ex["id"], ns=next_status: do_change_status(eid, ns)))
            if ctx.is_admin:
                actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=C.COLOR_DANGER, icon_size=18,
                                              on_click=lambda e, eid=ex["id"]: do_delete(eid)))

            cards.append(ft.Container(
                bgcolor=C.COLOR_SURFACE, border=ft.Border.all(1, C.COLOR_BORDER), border_radius=10, padding=18,
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(f"Caveau {ex.get('grave_numero') or '—'}", size=15, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
                            ft.Text(f"Motif : {ex.get('motif') or '—'}", size=12, color=C.COLOR_TEXT_MUTED),
                            ft.Text(f"Planifiée le {ex.get('date_planifiee') or '—'}" + (f"  •  Réalisée le {ex['date_realisation']}" if ex.get("date_realisation") else ""), size=12, color=C.COLOR_TEXT_MUTED),
                        ], spacing=3, expand=True),
                        status_badge(ex["status"]),
                    ]),
                    ft.Row(actions, spacing=4) if actions else ft.Container(),
                ], spacing=8),
            ))

        list_container.controls = cards
        page.update()

    def do_change_status(exhumation_id, new_status):
        try:
            ctx.exhumations.change_status(exhumation_id, new_status)
            show_snackbar(page, "Statut mis à jour.")
            reload()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    def do_delete(exhumation_id):
        def confirmed():
            try:
                ctx.exhumations.delete(exhumation_id)
                show_snackbar(page, "Exhumation supprimée.")
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)
        confirm_dialog(page, "Supprimer l'exhumation", "Cette action est irréversible. Confirmer ?", confirmed)

    def open_form(e=None):
        try:
            graves = ctx.cemetery.list_graves(status="occupe")
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not graves:
            show_snackbar(page, "Aucun caveau occupé disponible pour une exhumation.", success=False)
            return

        grave_dd = dropdown_field("Caveau", [(g["id"], g["numero"]) for g in graves], value=graves[0]["id"], width=responsive_width(page, max=380, min=280))
        date_field = text_field("Date planifiée (AAAA-MM-JJ)", width=responsive_width(page, max=380, min=280))
        motif_field = text_field("Motif", width=responsive_width(page, max=380, min=280), multiline=True, min_lines=2)

        def save(close):
            payload = {
                "grave_id": grave_dd.value,
                "date_planifiee": date_field.value.strip() if date_field.value else None,
                "motif": motif_field.value.strip() if motif_field.value else None,
            }
            try:
                ctx.exhumations.create(payload)
                show_snackbar(page, "Exhumation planifiée.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Planifier une exhumation", [grave_dd, date_field, motif_field], save)

    reload()

    content = ft.Column([
        page_header(page, "Gestion des exhumations", "Planifier une exhumation" if ctx.is_staff else None, open_form),
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/exhumations", "Exhumations")
