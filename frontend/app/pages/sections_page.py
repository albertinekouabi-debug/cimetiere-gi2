import flet as ft
from app import config as C
from app.components.theme import text_field, show_snackbar, confirm_dialog, loading_indicator, responsive_width
from app.components.data_table import build_data_table, form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext
from app.utils import parse_float, FieldValidationError


def build_sections_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            sections = ctx.cemetery.list_sections()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        rows = []
        for s in sections:
            rows.append(([
                s["nom"],
                s.get("description") or "—",
                f"{s['superficie']} m²" if s.get("superficie") else "—",
            ], s["id"]))

        def do_edit(section_id):
            open_form(next(s for s in sections if s["id"] == section_id))

        def do_delete(section_id):
            def confirmed():
                try:
                    ctx.cemetery.delete_section(section_id)
                    show_snackbar(page, "Section supprimée.")
                    reload()
                except ApiError as err:
                    show_snackbar(page, err.message, success=False)
            confirm_dialog(page, "Supprimer la section", "Cette action est irréversible. Confirmer la suppression ?", confirmed)

        list_container.controls = [build_data_table(
            ["Nom", "Description", "Superficie"], rows,
            on_edit=do_edit if ctx.is_staff else None,
            on_delete=do_delete if ctx.is_admin else None,
        )]
        page.update()

    def open_form(section=None):
        nom_field = text_field(
            "Nom de la section",
            value=section["nom"] if section else "",
            width=responsive_width(page, max=380, min=280),
        )
        desc_field = text_field(
            "Description",
            value=(section.get("description") or "") if section else "",
            width=responsive_width(page, max=380, min=280),
            multiline=True, min_lines=2,
        )
        superficie_field = text_field(
            "Superficie (m²)",
            value=str(section["superficie"]) if section and section.get("superficie") else "",
            width=responsive_width(page, max=380, min=280),
            hint_text="ex: 3800 ou 3800,50",
        )

        def save(close):
            nom = (nom_field.value or "").strip()
            if not nom:
                show_snackbar(page, "Le nom de la section est obligatoire.", success=False)
                return

            # Validation des champs numériques AVANT tout appel réseau : un
            # format invalide (espaces, virgule, texte) ne doit jamais faire
            # planter l'application — juste afficher un message clair et
            # laisser le formulaire ouvert pour correction.
            try:
                superficie = parse_float(superficie_field.value, "La superficie", required=False)
            except FieldValidationError as err:
                show_snackbar(page, str(err), success=False)
                return

            payload = {
                "nom": nom,
                "description": desc_field.value.strip() if desc_field.value else None,
                "superficie": superficie,
            }
            try:
                if section:
                    ctx.cemetery.update_section(section["id"], payload)
                    show_snackbar(page, "Section mise à jour.")
                else:
                    ctx.cemetery.create_section(payload)
                    show_snackbar(page, "Section créée.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Modifier la section" if section else "Nouvelle section",
                    [nom_field, desc_field, superficie_field], save)

    reload()

    content = ft.Column([
        page_header(page, "Gestion des sections du cimetière", "Nouvelle section" if ctx.is_staff else None, lambda e: open_form()),
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/sections", "Sections")
