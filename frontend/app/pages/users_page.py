import flet as ft
from app import config as C
from app.components.theme import text_field, dropdown_field, show_snackbar, confirm_dialog, loading_indicator, status_badge, responsive_width
from app.components.data_table import build_data_table, form_dialog, page_header
from app.components.layout import build_app_shell
from app.services.api_client import ApiError
from app.state.session_context import SessionContext

ROLE_OPTIONS = [("admin", "Administrateur"), ("gestionnaire", "Gestionnaire"), ("agent", "Agent")]


def build_users_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    list_container = ft.Column([loading_indicator()])
    role_filter = dropdown_field("Filtrer par rôle", [("", "Tous les rôles")] + ROLE_OPTIONS, value="", width=responsive_width(page, max=240, min=180))

    def reload():
        list_container.controls = [loading_indicator()]
        page.update()
        try:
            users = ctx.users.list()
        except ApiError as err:
            list_container.controls = [ft.Text(err.message, color=C.COLOR_DANGER)]
            page.update()
            return

        if role_filter.value:
            users = [u for u in users if u["role"] == role_filter.value]

        rows = []
        for u in users:
            active_badge = status_badge("active" if u["is_active"] else "resiliee", "Actif" if u["is_active"] else "Désactivé")
            rows.append(([
                u["full_name"] or "—", u["email"], C.ROLE_LABELS.get(u["role"], u["role"]), active_badge,
            ], u["id"]))

        def do_edit(user_id):
            open_form(next(u for u in users if u["id"] == user_id))

        def do_delete(user_id):
            if user_id == ctx.profile["id"]:
                show_snackbar(page, "Vous ne pouvez pas supprimer votre propre compte.", success=False)
                return
            def confirmed():
                try:
                    ctx.users.delete(user_id)
                    show_snackbar(page, "Utilisateur supprimé.")
                    reload()
                except ApiError as err:
                    show_snackbar(page, err.message, success=False)
            confirm_dialog(page, "Supprimer l'utilisateur", "Cette action est irréversible. Confirmer ?", confirmed)

        def do_reset_password(user_id):
            target = next(u for u in users if u["id"] == user_id)
            open_reset_password_form(target)

        list_container.controls = [build_data_table(
            ["Nom complet", "Email", "Rôle", "Statut"], rows,
            on_edit=do_edit, on_delete=do_delete,
            extra_action=(ft.Icons.KEY_OUTLINED, C.COLOR_WARNING, "Réinitialiser le mot de passe", do_reset_password),
        )]
        page.update()

    def open_form(user=None):
        nom_field = text_field("Nom complet", value=user["full_name"] if user else "", width=responsive_width(page, max=380, min=280))
        email_field = text_field("Email", value=user["email"] if user else "", width=responsive_width(page, max=380, min=280), disabled=bool(user))
        password_field = text_field("Mot de passe", password=True, can_reveal_password=True, width=responsive_width(page, max=380, min=280))
        role_dd = dropdown_field("Rôle", ROLE_OPTIONS, value=user["role"] if user else "agent", width=responsive_width(page, max=380, min=280))
        active_switch = ft.Switch(label="Compte actif", value=user["is_active"] if user else True, active_color=C.COLOR_PRIMARY)

        fields = [nom_field, email_field, role_dd]
        if not user:
            fields.append(password_field)
        else:
            fields.append(active_switch)

        def save(close):
            if not nom_field.value or (not user and (not email_field.value or not password_field.value)):
                show_snackbar(page, "Tous les champs obligatoires doivent être renseignés.", success=False)
                return
            try:
                if user:
                    ctx.users.update(user["id"], {"full_name": nom_field.value.strip(), "role": role_dd.value, "is_active": active_switch.value})
                    show_snackbar(page, "Utilisateur mis à jour.")
                else:
                    ctx.users.create({"email": email_field.value.strip(), "password": password_field.value, "full_name": nom_field.value.strip(), "role": role_dd.value})
                    show_snackbar(page, "Utilisateur créé.")
                close()
                reload()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Modifier l'utilisateur" if user else "Nouvel utilisateur", fields, save)

    def open_reset_password_form(user):
        info_text = ft.Text(f"Nouveau mot de passe pour {user['email']}", size=13, color=C.COLOR_TEXT_MUTED)
        new_password_field = text_field("Nouveau mot de passe (8 caractères min.)", password=True, can_reveal_password=True, width=responsive_width(page, max=380, min=280))

        def save(close):
            if not new_password_field.value or len(new_password_field.value) < 8:
                show_snackbar(page, "Le mot de passe doit contenir au moins 8 caractères.", success=False)
                return
            try:
                ctx.users.reset_password(user["id"], new_password_field.value)
                show_snackbar(page, f"Mot de passe de {user['email']} réinitialisé.")
                close()
            except ApiError as err:
                show_snackbar(page, err.message, success=False)

        form_dialog(page, "Réinitialiser le mot de passe", [info_text, new_password_field], save, save_label="Réinitialiser")

    role_filter.on_select = lambda e: reload()
    reload()

    content = ft.Column([
        page_header(page, "Gestion des utilisateurs", "Nouvel utilisateur", lambda e: open_form()),
        ft.Container(height=10),
        role_filter,
        ft.Container(height=16),
        list_container,
    ])

    return build_app_shell(page, ctx, content, "/utilisateurs", "Utilisateurs")
