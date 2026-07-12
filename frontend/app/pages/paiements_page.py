import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, stat_card, responsive_width
from app.components.data_table import build_data_table, form_dialog
from app.components.layout import build_app_shell
from app.components.download import download_file
from app.services.api_client import ApiError
from app.state.session_context import SessionContext
from app.utils import parse_positive_float, FieldValidationError

MODE_OPTIONS = [("especes", "Espèces"), ("virement", "Virement"), ("cheque", "Chèque"), ("carte", "Carte bancaire")]


def build_paiements_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])
    stats_row = ft.Row()

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            paiements = ctx.payments.list()
            stats = ctx.payments.stats()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        stats_row.controls = [
            ft.Container(stat_card("Revenus du mois", f"{stats['revenus_mois']:,.0f} FCFA".replace(",", " "), ft.Icons.CALENDAR_MONTH, C.COLOR_SUCCESS), expand=True),
            ft.Container(stat_card("Revenus totaux", f"{stats['total_revenus']:,.0f} FCFA".replace(",", " "), ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED, C.COLOR_INFO), expand=True),
            ft.Container(stat_card("Nombre de paiements", str(stats["nombre_paiements"]), ft.Icons.RECEIPT_LONG_OUTLINED, C.COLOR_ACCENT), expand=True),
        ]

        rows = []
        for p in paiements:
            recu_btn = ft.IconButton(ft.Icons.PICTURE_AS_PDF_OUTLINED, icon_color=C.COLOR_ACCENT, icon_size=18, tooltip="Télécharger le reçu",
                                      on_click=lambda e, pid=p["id"], num=p["numero_recu"]: download_recu(pid, num))
            rows.append(([
                p["numero_recu"], p.get("famille_nom") or "—", p.get("grave_numero") or "—",
                f"{p['montant']:,.0f} FCFA".replace(",", " "), dict(MODE_OPTIONS + [("momo", "MTN MoMo")]).get(p["mode_paiement"], p["mode_paiement"]),
                p["date_paiement"], recu_btn,
            ], p["id"]))

        def do_delete(paiement_id):
            def confirmed():
                try:
                    ctx.payments.delete(paiement_id)
                    show_snackbar(page, "Paiement supprimé.")
                    reload()
                except ApiError as err:
                    show_snackbar(page, err.message, success=False)
            confirm_dialog(page, "Supprimer le paiement", "Cette action est irréversible. Confirmer ?", confirmed)

        list_container.controls = [build_data_table(
            ["N° reçu", "Famille", "Caveau", "Montant", "Mode", "Date", ""], rows,
            on_edit=None, on_delete=do_delete if ctx.is_admin else None,
        )]
        page.update()

    def download_recu(paiement_id, numero):
        try:
            pdf_bytes = ctx.payments.download_recu(paiement_id)
            download_file(page, pdf_bytes, "pdf")
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    def do_export_pdf(e):
        try:
            pdf_bytes = ctx.payments.export_pdf()
            download_file(page, pdf_bytes, "pdf")
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    def do_export_csv(e):
        try:
            csv_bytes = ctx.payments.export_csv()
            download_file(page, csv_bytes, "csv")
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    # ─── Paiement manuel ──────────────────────────────────────────────────
    def open_manual_form(e=None):
        try:
            concessions = ctx.concessions.list()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not concessions:
            show_snackbar(page, "Aucune concession disponible.", success=False)
            return

        concession_dd = dropdown_field("Concession", [(c["id"], f"{c['famille_nom']} — {c.get('grave_numero', '')}") for c in concessions], value=concessions[0]["id"], width=responsive_width(page, max=380, min=280))
        montant_field = text_field("Montant (FCFA)", width=responsive_width(page, max=380, min=280), hint_text="ex: 150000")
        date_field = text_field("Date de paiement (AAAA-MM-JJ)", width=responsive_width(page, max=380, min=280))
        mode_dd = dropdown_field("Mode de paiement", MODE_OPTIONS, value="especes", width=responsive_width(page, max=380, min=280))

        def save(close):
            date_paiement = (date_field.value or "").strip()
            if not montant_field.value or not date_paiement:
                show_snackbar(page, "Le montant et la date sont obligatoires.", success=False)
                return
            try:
                montant = parse_positive_float(montant_field.value, "Le montant")
            except FieldValidationError as err:
                show_snackbar(page, str(err), success=False)
                return
            try:
                ctx.payments.create({
                    "concession_id": concession_dd.value, "montant": montant,
                    "date_paiement": date_paiement, "mode_paiement": mode_dd.value,
                })
                show_snackbar(page, "Paiement enregistré.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Enregistrer un paiement manuel", [concession_dd, montant_field, date_field, mode_dd], save)

    # ─── Paiement MTN MoMo ────────────────────────────────────────────────
    def open_momo_form(e=None):
        try:
            concessions = ctx.concessions.list()
        except ApiError as err:
            show_snackbar(page, err.message, success=False)
            return
        if not concessions:
            show_snackbar(page, "Aucune concession disponible.", success=False)
            return

        concession_dd = dropdown_field("Concession", [(c["id"], f"{c['famille_nom']} — {c.get('grave_numero', '')}") for c in concessions], value=concessions[0]["id"], width=responsive_width(page, max=380, min=280))
        montant_field = text_field("Montant (FCFA)", width=responsive_width(page, max=380, min=280), hint_text="ex: 150000")
        phone_field = text_field("Numéro MTN MoMo (ex: 242061234567)", width=responsive_width(page, max=380, min=280))
        status_text = ft.Text("", size=12, color=C.COLOR_TEXT_MUTED)

        def initiate(close):
            phone = (phone_field.value or "").strip()
            if not montant_field.value or not phone:
                show_snackbar(page, "Le montant et le numéro sont obligatoires.", success=False)
                return
            try:
                montant = parse_positive_float(montant_field.value, "Le montant")
            except FieldValidationError as err:
                show_snackbar(page, str(err), success=False)
                return
            try:
                ctx.payments.momo_initiate(concession_dd.value, montant, phone)
                show_snackbar(page, "Demande envoyée. Le client doit valider sur son téléphone avec son code PIN MoMo.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Paiement MTN Mobile Money", [concession_dd, montant_field, phone_field, status_text], initiate, save_label="Envoyer la demande")

    reload()

    action_buttons = []
    if ctx.is_manager:
        action_buttons.append(ft.OutlinedButton("CSV", icon=ft.Icons.TABLE_CHART_OUTLINED, on_click=do_export_csv,
                                                   style=ft.ButtonStyle(color=C.COLOR_TEXT, side=ft.BorderSide(1, C.COLOR_BORDER))))
        action_buttons.append(ft.OutlinedButton("PDF", icon=ft.Icons.PICTURE_AS_PDF_OUTLINED, on_click=do_export_pdf,
                                                   style=ft.ButtonStyle(color=C.COLOR_TEXT, side=ft.BorderSide(1, C.COLOR_BORDER))))
    if ctx.is_staff:
        action_buttons.append(ft.OutlinedButton("MTN MoMo", icon=ft.Icons.PHONE_ANDROID, on_click=open_momo_form,
                                                   style=ft.ButtonStyle(color=C.COLOR_ACCENT, side=ft.BorderSide(1, C.COLOR_ACCENT))))
    if ctx.is_manager:
        action_buttons.append(ft.ElevatedButton("Nouveau paiement", icon=ft.Icons.ADD, on_click=open_manual_form,
                                                   style=ft.ButtonStyle(bgcolor=C.COLOR_PRIMARY, color="#ffffff")))

    title_text = ft.Text("Historique des paiements", size=16, color=C.COLOR_TEXT_MUTED)
    buttons_row = ft.Row(action_buttons, spacing=8, run_spacing=8, wrap=True)

    # Sur petit écran, empile le titre au-dessus des boutons (eux-mêmes
    # enveloppants sur plusieurs lignes si besoin) plutôt que de les forcer
    # sur une seule ligne : avec jusqu'à 4 boutons, un Row("expand"+boutons)
    # écrasait le conteneur du titre à une largeur quasi nulle, provoquant un
    # rendu catastrophique où chaque lettre passait à la ligne.
    narrow = getattr(page, "width", None) is not None and page.width < 640
    if narrow:
        header_row = ft.Column([title_text, buttons_row], spacing=12)
    else:
        header_row = ft.Row([ft.Container(content=title_text, expand=True), buttons_row])

    content = ft.Column([
        stats_row, ft.Container(height=20),
        header_row,
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/paiements", "Paiements")
