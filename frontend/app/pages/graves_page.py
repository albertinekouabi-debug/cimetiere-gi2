import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, status_badge, responsive_width
from app.components.data_table import build_data_table, form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext
from app.utils import parse_float, FieldValidationError

STATUS_OPTIONS = [("libre", "Libre"), ("occupe", "Occupé"), ("reserve", "Réservé"), ("maintenance", "Maintenance")]


def build_graves_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])
    status_filter = dropdown_field("Filtrer par statut", [("", "Tous les statuts")] + STATUS_OPTIONS, value="", width=responsive_width(page, max=220, min=180))

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            graves = ctx.cemetery.list_graves(status=status_filter.value or None)
            blocs = ctx.cemetery.list_blocs()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        if not blocs:
            list_container.controls = [ft.Text("Créez d'abord un bloc avant d'ajouter des caveaux.", color=C.COLOR_WARNING)]
            page.update()
            return

        rows = []
        for g in graves:
            rows.append(([
                g["numero"], g.get("section_nom") or "—", g.get("bloc_nom") or "—",
                status_badge(g["status"]), str(g.get("nb_defunts", 0)),
            ], g["id"]))

        def do_edit(grave_id):
            open_form(next(g for g in graves if g["id"] == grave_id), blocs)

        def do_delete(grave_id):
            def confirmed():
                try:
                    ctx.cemetery.delete_grave(grave_id)
                    show_snackbar(page, "Caveau supprimé.")
                    reload()
                except ApiError as err:
                    show_snackbar(page, err.message, success=False)
            confirm_dialog(page, "Supprimer le caveau", "Cette action est irréversible. Confirmer ?", confirmed)

        list_container.controls = [build_data_table(
            ["Numéro", "Section", "Bloc", "Statut", "Défunts"], rows,
            on_edit=do_edit if ctx.is_staff else None,
            on_delete=do_delete if ctx.is_admin else None,
        )]
        page.update()

    def open_form(grave, blocs):
        numero_field = text_field("Numéro du caveau", value=grave["numero"] if grave else "", width=responsive_width(page, max=380, min=280))
        bloc_dd = dropdown_field("Bloc", [(b["id"], f"{b['nom']} ({b.get('section_nom', '')})") for b in blocs],
                                  value=grave["bloc_id"] if grave else blocs[0]["id"], width=responsive_width(page, max=380, min=280))
        status_dd = dropdown_field("Statut", STATUS_OPTIONS, value=grave["status"] if grave else "libre", width=responsive_width(page, max=380, min=280))
        lat_field = text_field("Latitude (optionnel)", value=str(grave["latitude"]) if grave and grave.get("latitude") else "", width=responsive_width(page, max=380, min=280), hint_text="entre -90 et 90")
        lng_field = text_field("Longitude (optionnel)", value=str(grave["longitude"]) if grave and grave.get("longitude") else "", width=responsive_width(page, max=380, min=280), hint_text="entre -180 et 180")
        notes_field = text_field("Notes", value=(grave.get("notes") or "") if grave else "", width=responsive_width(page, max=380, min=280), multiline=True, min_lines=2)

        def save(close):
            numero = (numero_field.value or "").strip()
            if not numero or not bloc_dd.value:
                show_snackbar(page, "Le numéro et le bloc sont obligatoires.", success=False)
                return

            # Chaque champ numérique est validé séparément AVANT tout appel
            # réseau : une saisie invalide affiche un message précis (quel
            # champ, pourquoi) et laisse le formulaire ouvert, plutôt que de
            # faire planter l'application (ex: "3 800" avec un espace).
            try:
                latitude = parse_float(lat_field.value, "La latitude", required=False, min_value=-90, max_value=90)
                longitude = parse_float(lng_field.value, "La longitude", required=False, min_value=-180, max_value=180)
            except FieldValidationError as err:
                show_snackbar(page, str(err), success=False)
                return

            payload = {
                "bloc_id": bloc_dd.value, "numero": numero, "status": status_dd.value,
                "latitude": latitude,
                "longitude": longitude,
                "notes": notes_field.value.strip() if notes_field.value else None,
            }
            try:
                if grave:
                    ctx.cemetery.update_grave(grave["id"], payload)
                    show_snackbar(page, "Caveau mis à jour.")
                else:
                    ctx.cemetery.create_grave(payload)
                    show_snackbar(page, "Caveau créé.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Modifier le caveau" if grave else "Nouveau caveau",
                    [numero_field, bloc_dd, status_dd, lat_field, lng_field, notes_field], save)

    reload()
    status_filter.on_change = lambda e: reload()

    def new_grave(e):
        try:
            blocs = ctx.cemetery.list_blocs()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not blocs:
            show_snackbar(page, "Créez d'abord un bloc.", success=False)
            return
        open_form(None, blocs)

    content = ft.Column([
        page_header(page, "Gestion des caveaux", "Nouveau caveau" if ctx.is_staff else None, new_grave),
        ft.Container(height=10),
        status_filter,
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/caveaux", "Caveaux")
