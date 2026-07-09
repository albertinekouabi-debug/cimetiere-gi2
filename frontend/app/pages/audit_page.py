import flet as ft
from app import config as C
from app.components.theme import loading_indicator, dropdown_field, show_snackbar, responsive_width
from app.components.data_table import build_data_table
from app.components.layout import build_app_shell
from app.components.download import download_file
from app.services.api_client import ApiError
from app.state.session_context import SessionContext

ACTION_LABELS = {"create": "Création", "update": "Modification", "delete": "Suppression", "login": "Connexion"}
ACTION_COLORS = {"create": C.COLOR_SUCCESS, "update": C.COLOR_INFO, "delete": C.COLOR_DANGER, "login": C.COLOR_ACCENT}
TABLE_LABELS = {
    "sections": "Sections", "blocs": "Blocs", "graves": "Caveaux", "defunts": "Défunts",
    "reservations": "Réservations", "concessions": "Concessions", "paiements": "Paiements",
    "momo_transactions": "Transactions MoMo", "exhumations": "Exhumations",
    "profiles": "Utilisateurs", "auth": "Connexions",
}


def build_audit_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])
    action_filter = dropdown_field("Filtrer par action", [("", "Toutes les actions")] + list(ACTION_LABELS.items()), value="", width=responsive_width(page, max=240, min=200))
    table_filter = dropdown_field("Filtrer par module", [("", "Tous les modules")] + list(TABLE_LABELS.items()), value="", width=responsive_width(page, max=240, min=200))

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            logs = ctx.audit.list(action=action_filter.value or None, table_name=table_filter.value or None)
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        if not logs:
            list_container.controls = [ft.Text("Aucune entrée dans le journal.", color=C.COLOR_TEXT_MUTED)]
            page.update()
            return

        rows = []
        for log in logs:
            action_chip = ft.Container(
                content=ft.Text(ACTION_LABELS.get(log["action"], log["action"]), size=12, color=ACTION_COLORS.get(log["action"], C.COLOR_TEXT_MUTED)),
                bgcolor=ft.Colors.with_opacity(0.15, ACTION_COLORS.get(log["action"], C.COLOR_TEXT_MUTED)),
                border_radius=15, padding=ft.Padding(10, 4, 10, 4),
            )
            rows.append(([
                log.get("user_email") or "Système", action_chip, TABLE_LABELS.get(log["table_name"], log["table_name"]),
                (log.get("record_id") or "—")[:8], log["created_at"][:19].replace("T", " "),
            ], log["id"]))

        list_container.controls = [build_data_table(["Utilisateur", "Action", "Module", "Réf.", "Date/heure"], rows, on_edit=None, on_delete=None)]
        page.update()

    def do_export_csv(e):
        try:
            csv_bytes = ctx.audit.export_csv(table_name=table_filter.value or None, action=action_filter.value or None)
            download_file(page, csv_bytes, "csv")
        except ApiError as err:
            show_snackbar(page, err.message, success=False)

    action_filter.on_select = lambda e: reload()
    table_filter.on_select = lambda e: reload()
    reload()

    content = ft.Column([
        ft.Row([
            ft.Container(content=ft.Text("Journal d'audit — traçabilité des actions", size=16, color=C.COLOR_TEXT_MUTED), expand=True),
            ft.OutlinedButton("Exporter en CSV", icon=ft.Icons.TABLE_CHART_OUTLINED, on_click=do_export_csv,
                               style=ft.ButtonStyle(color=C.COLOR_TEXT, side=ft.BorderSide(1, C.COLOR_BORDER))),
        ]),
        ft.Container(height=10),
        ft.Row([action_filter, table_filter]),
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/audit", "Journal d'audit")
