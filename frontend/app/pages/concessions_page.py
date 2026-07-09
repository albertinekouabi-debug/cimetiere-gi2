import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, status_badge, responsive_width
from app.components.data_table import build_data_table, form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext
from app.utils import parse_float, parse_positive_float, FieldValidationError

DUREE_OPTIONS = [("10_ans", "10 ans"), ("30_ans", "30 ans"), ("perpetuelle", "Perpétuelle")]


def build_concessions_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            concessions = ctx.concessions.list()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        rows = []
        for c in concessions:
            reste = c["montant_total"] - c["montant_paye"]
            rows.append(([
                c.get("grave_numero") or "—", c["famille_nom"],
                dict(DUREE_OPTIONS).get(c["duree"], c["duree"]),
                c.get("date_fin") or "Perpétuelle",
                f"{c['montant_total']:,.0f} FCFA".replace(",", " "),
                f"{reste:,.0f} FCFA".replace(",", " ") if reste > 0 else "Soldé",
                status_badge(c["status"]),
            ], c["id"]))

        def do_renew(concession_id):
            open_renew_form(concession_id)

        def do_delete(concession_id):
            def confirmed():
                try:
                    ctx.concessions.delete(concession_id)
                    show_snackbar(page, "Concession supprimée.")
                    reload()
                except ApiError as err:
                    show_snackbar(page, err.message, success=False)
            confirm_dialog(page, "Supprimer la concession", "Cette action est irréversible. Confirmer ?", confirmed)

        list_container.controls = [build_data_table(
            ["Caveau", "Famille", "Durée", "Fin", "Montant total", "Reste à payer", "Statut"], rows,
            on_edit=do_renew if ctx.is_manager else None,
            on_delete=do_delete if ctx.is_admin else None,
        )]
        page.update()

    def open_renew_form(concession_id):
        duree_dd = dropdown_field("Nouvelle durée", DUREE_OPTIONS, value="10_ans", width=responsive_width(page, max=380, min=280))
        montant_field = text_field("Montant supplémentaire (FCFA)", value="0", width=responsive_width(page, max=380, min=280), hint_text="ex: 50000")

        def save(close):
            try:
                # Le montant supplémentaire peut légitimement être 0 (simple
                # prolongation sans frais), mais pas négatif.
                montant = parse_float(montant_field.value, "Le montant supplémentaire", required=False, min_value=0) or 0
            except FieldValidationError as err:
                show_snackbar(page, str(err), success=False)
                return
            try:
                ctx.concessions.renew(concession_id, duree_dd.value, montant)
                show_snackbar(page, "Concession renouvelée.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Renouveler la concession", [duree_dd, montant_field], save, save_label="Renouveler")

    def open_form(e=None):
        try:
            graves = ctx.cemetery.list_graves()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not graves:
            show_snackbar(page, "Aucun caveau disponible.", success=False)
            return

        grave_dd = dropdown_field("Caveau", [(g["id"], g["numero"]) for g in graves], value=graves[0]["id"], width=responsive_width(page, max=380, min=280))
        famille_field = text_field("Nom de la famille", width=responsive_width(page, max=380, min=280))
        contact_field = text_field("Contact famille", width=responsive_width(page, max=380, min=280))
        duree_dd = dropdown_field("Durée", DUREE_OPTIONS, value="10_ans", width=responsive_width(page, max=380, min=280))
        date_debut_field = text_field("Date de début (AAAA-MM-JJ)", width=responsive_width(page, max=380, min=280))
        montant_field = text_field("Montant total (FCFA)", width=responsive_width(page, max=380, min=280), hint_text="ex: 350000")

        def save(close):
            famille = (famille_field.value or "").strip()
            date_debut = (date_debut_field.value or "").strip()
            if not famille or not date_debut or not montant_field.value:
                show_snackbar(page, "Tous les champs obligatoires doivent être renseignés.", success=False)
                return
            try:
                montant = parse_positive_float(montant_field.value, "Le montant total")
            except FieldValidationError as err:
                show_snackbar(page, str(err), success=False)
                return
            payload = {
                "grave_id": grave_dd.value, "famille_nom": famille,
                "famille_contact": contact_field.value.strip() if contact_field.value else None,
                "duree": duree_dd.value, "date_debut": date_debut, "montant_total": montant,
            }
            try:
                ctx.concessions.create(payload)
                show_snackbar(page, "Concession créée.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Nouvelle concession", [grave_dd, famille_field, contact_field, duree_dd, date_debut_field, montant_field], save)

    reload()

    content = ft.Column([
        page_header(page, "Gestion des concessions", "Nouvelle concession" if ctx.is_manager else None, open_form),
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/concessions", "Concessions")
