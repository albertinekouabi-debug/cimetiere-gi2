import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, responsive_width
from app.components.data_table import build_data_table, form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext


def build_blocs_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            blocs = ctx.cemetery.list_blocs()
            sections = ctx.cemetery.list_sections()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        if not sections:
            list_container.controls = [ft.Text("Créez d'abord une section avant d'ajouter des blocs.", color=C.COLOR_WARNING)]
            page.update()
            return

        rows = [(([b["nom"], b.get("section_nom") or "—", b.get("description") or "—"]), b["id"]) for b in blocs]

        def do_edit(bloc_id):
            open_form(next(b for b in blocs if b["id"] == bloc_id), sections)

        def do_delete(bloc_id):
            def confirmed():
                try:
                    ctx.cemetery.delete_bloc(bloc_id)
                    show_snackbar(page, "Bloc supprimé.")
                    reload()
                except ApiError as err:
                    show_snackbar(page, err.message, success=False)
            confirm_dialog(page, "Supprimer le bloc", "Cette action est irréversible. Confirmer ?", confirmed)

        list_container.controls = [build_data_table(
            ["Nom", "Section", "Description"], rows,
            on_edit=do_edit if ctx.is_staff else None,
            on_delete=do_delete if ctx.is_admin else None,
        )]
        page.update()

    def open_form(bloc, sections):
        nom_field = text_field("Nom du bloc", value=bloc["nom"] if bloc else "", width=responsive_width(page, max=380, min=280))
        desc_field = text_field("Description", value=(bloc.get("description") or "") if bloc else "", width=responsive_width(page, max=380, min=280), multiline=True, min_lines=2)
        section_dd = dropdown_field("Section", [(s["id"], s["nom"]) for s in sections],
                                     value=bloc["section_id"] if bloc else (sections[0]["id"] if sections else None), width=responsive_width(page, max=380, min=280))

        def save(close):
            if not nom_field.value or not section_dd.value:
                show_snackbar(page, "Le nom et la section sont obligatoires.", success=False)
                return
            payload = {"section_id": section_dd.value, "nom": nom_field.value.strip(),
                       "description": desc_field.value.strip() if desc_field.value else None}
            try:
                if bloc:
                    ctx.cemetery.update_bloc(bloc["id"], payload)
                    show_snackbar(page, "Bloc mis à jour.")
                else:
                    ctx.cemetery.create_bloc(payload)
                    show_snackbar(page, "Bloc créé.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Modifier le bloc" if bloc else "Nouveau bloc", [nom_field, section_dd, desc_field], save)

    reload()

    def new_bloc(e):
        try:
            sections = ctx.cemetery.list_sections()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not sections:
            show_snackbar(page, "Créez d'abord une section.", success=False)
            return
        open_form(None, sections)

    content = ft.Column([
        page_header(page, "Gestion des blocs", "Nouveau bloc" if ctx.is_staff else None, new_bloc),
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/blocs", "Blocs")
