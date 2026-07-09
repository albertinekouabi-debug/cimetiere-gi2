import flet as ft
from app import config as C
from app.components.theme import text_field, primary_button, responsive_width
from app.services.api_client import ApiError
from app.state.session_context import SessionContext


def build_login_view(page: ft.Page, ctx: SessionContext) -> ft.View:
    email_field = text_field("Adresse email", autofocus=True, width=responsive_width(page, max=340, min=260))
    password_field = text_field("Mot de passe", password=True, can_reveal_password=True, width=responsive_width(page, max=340, min=260))
    error_text = ft.Text("", color=C.COLOR_DANGER, size=13)
    loading = ft.ProgressRing(color=C.COLOR_PRIMARY, width=20, height=20, visible=False)

    def do_login(e):
        error_text.value = ""
        if not email_field.value or not password_field.value:
            error_text.value = "Veuillez renseigner l'email et le mot de passe."
            page.update()
            return
        loading.visible = True
        login_btn.disabled = True
        page.update()
        try:
            profile = ctx.auth.login(email_field.value.strip(), password_field.value)
            ctx.set_profile(profile)
            page.go("/dashboard")
        except ApiError as err:
            error_text.value = err.message
        finally:
            loading.visible = False
            login_btn.disabled = False
            page.update()

    def on_submit(e):
        do_login(e)

    password_field.on_submit = on_submit
    login_btn = primary_button("Se connecter", on_click=do_login, width=responsive_width(page, max=340, min=260))

    form = ft.Container(
        width=responsive_width(page, max=420, min=320),
        padding=40,
        bgcolor=C.COLOR_SURFACE,
        border=ft.Border.all(1, C.COLOR_BORDER),
        border_radius=14,
        content=ft.Column([
            ft.Icon(ft.Icons.CHURCH_OUTLINED, color=C.COLOR_ACCENT, size=42),
            ft.Text("Cimetière Municipal de Vindoulou", size=20, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT, text_align=ft.TextAlign.CENTER),
            ft.Text("Espace réservé au personnel", size=13, color=C.COLOR_TEXT_MUTED),
            ft.Container(height=20),
            email_field,
            password_field,
            error_text,
            ft.Container(height=10),
            ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
            login_btn,
            ft.Container(height=10),
            ft.TextButton(content=ft.Text("Recherche publique d'un défunt"), on_click=lambda e: page.go("/recherche"),
                          style=ft.ButtonStyle(color=C.COLOR_TEXT_MUTED)),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
    )

    return ft.View(
        route="/login",
        bgcolor=C.COLOR_BG,
        controls=[ft.Container(content=form, alignment=ft.Alignment.CENTER, expand=True)],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
