import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, status_badge, responsive_width
from app.components.data_table import form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext


def build_reservations_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            reservations = ctx.reservations.list()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        if not reservations:
            list_container.controls = [ft.Text("Aucune réservation pour le moment.", color=C.COLOR_TEXT_MUTED)]
            page.update()
            return

        cards = []
        for r in reservations:
            actions = []
            if ctx.is_manager and r["status"] == "en_attente":
                actions.append(ft.TextButton("Valider", icon=ft.Icons.CHECK, style=ft.ButtonStyle(color=C.COLOR_SUCCESS),
                                              on_click=lambda e, rid=r["id"]: do_validate(rid, "validee")))
                actions.append(ft.TextButton("Refuser", icon=ft.Icons.CLOSE, style=ft.ButtonStyle(color=C.COLOR_DANGER),
                                              on_click=lambda e, rid=r["id"]: do_validate(rid, "refusee")))
            if ctx.is_manager and r["status"] in ("validee", "refusee"):
                actions.append(ft.TextButton("Archiver", icon=ft.Icons.ARCHIVE_OUTLINED, style=ft.ButtonStyle(color=C.COLOR_TEXT_MUTED),
                                              on_click=lambda e, rid=r["id"]: do_archive(rid)))
            if ctx.is_admin:
                actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=C.COLOR_DANGER, icon_size=18,
                                              on_click=lambda e, rid=r["id"]: do_delete(rid)))

            cards.append(ft.Container(
                bgcolor=C.COLOR_SURFACE, border=ft.Border.all(1, C.COLOR_BORDER), border_radius=10, padding=18,
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(f"{r['defunt_prenom']} {r['defunt_nom']}", size=15, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT),
                            ft.Text(f"Famille : {r['famille_nom']}" + (f" — {r['famille_contact']}" if r.get('famille_contact') else ""), size=12, color=C.COLOR_TEXT_MUTED),
                            ft.Text(f"Caveau : {r.get('grave_numero') or '—'}  •  Décès : {r['defunt_date_deces']}", size=12, color=C.COLOR_TEXT_MUTED),
                        ], spacing=3, expand=True),
                        status_badge(r["status"]),
                    ]),
                    ft.Row(actions, spacing=4) if actions else ft.Container(),
                ], spacing=8),
            ))

        list_container.controls = cards
        page.update()

    def do_validate(reservation_id, status):
        try:
            ctx.reservations.validate(reservation_id, status)
            show_snackbar(page, "Réservation validée." if status == "validee" else "Réservation refusée.")
            reload()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    def do_archive(reservation_id):
        try:
            ctx.reservations.archive(reservation_id)
            show_snackbar(page, "Réservation archivée.")
            reload()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    def do_delete(reservation_id):
        def confirmed():
            try:
                ctx.reservations.delete(reservation_id)
                show_snackbar(page, "Réservation supprimée.")
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)
        confirm_dialog(page, "Supprimer la réservation", "Cette action est irréversible. Confirmer ?", confirmed)

    def open_form(e=None):
        try:
            graves = ctx.cemetery.list_graves(status="libre")
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not graves:
            show_snackbar(page, "Aucun caveau libre disponible pour une réservation.", success=False)
            return

        grave_dd = dropdown_field("Caveau", [(g["id"], g["numero"]) for g in graves], value=graves[0]["id"], width=responsive_width(page, max=380, min=280))
        nom_field = text_field("Nom du défunt", width=responsive_width(page, max=380, min=280))
        prenom_field = text_field("Prénom du défunt", width=responsive_width(page, max=380, min=280))
        date_deces_field = text_field("Date de décès (AAAA-MM-JJ)", width=responsive_width(page, max=380, min=280))
        famille_field = text_field("Nom de la famille", width=responsive_width(page, max=380, min=280))
        contact_field = text_field("Contact famille (téléphone)", width=responsive_width(page, max=380, min=280))

        def save(close):
            if not all([nom_field.value, prenom_field.value, date_deces_field.value, famille_field.value]):
                show_snackbar(page, "Tous les champs obligatoires doivent être renseignés.", success=False)
                return
            payload = {
                "grave_id": grave_dd.value, "defunt_nom": nom_field.value.strip(), "defunt_prenom": prenom_field.value.strip(),
                "defunt_date_deces": date_deces_field.value.strip(), "famille_nom": famille_field.value.strip(),
                "famille_contact": contact_field.value.strip() if contact_field.value else None,
            }
            try:
                ctx.reservations.create(payload)
                show_snackbar(page, "Réservation créée.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Nouvelle réservation", [grave_dd, nom_field, prenom_field, date_deces_field, famille_field, contact_field], save)

    reload()

    content = ft.Column([
        page_header(page, "Gestion des réservations", "Nouvelle réservation" if ctx.is_staff else None, open_form),
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/reservations", "Réservations")
