"""Thème visuel de l'application — gothique dark-green."""

import builtins
import flet as ft
from app import config as C


def build_theme() -> ft.Theme:
    """Construit le thème compatible avec Flet 0.85.x."""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=C.COLOR_PRIMARY,
            on_primary="#FFFFFF",

            secondary=C.COLOR_ACCENT,

            surface=C.COLOR_SURFACE,
            on_surface=C.COLOR_TEXT,

            error=C.COLOR_DANGER,
            on_error="#FFFFFF",
        ),
        font_family="Georgia",
    )


def apply_page_theme(page: ft.Page):
    """Applique le thème global à la page."""
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = build_theme()
    page.bgcolor = C.COLOR_BG

    page.fonts = {
        "Cinzel": "https://cdnjs.cloudflare.com/ajax/libs/cardinal/2.0.0/fonts/Cinzel-Regular.ttf",
    }


def responsive_width(page: ft.Page, max: int = 420, min: int = 280, margin: int = 40) -> int:
    """Retourne une largeur adaptative pour les formulaires et dialogues.

    Sur grand écran, retourne la largeur max.
    Sur petit écran, réduit la largeur selon la taille de la fenêtre.
    """
    _max, _min = builtins.max, builtins.min
    window_width = getattr(page, "width", None)
    if window_width is None:
        return max

    available = window_width - margin
    if available <= min:
        return _max(200, available)
    return _min(max, available)
    return min(max, available)


def card_container(content: ft.Control, padding: int = 20) -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=C.COLOR_SURFACE,
        border=ft.Border.all(1, C.COLOR_BORDER),
        border_radius=10,
    )


def primary_button(
    text: str,
    on_click=None,
    icon=None,
    width=None,
    disabled=False,
) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        width=width,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: C.COLOR_PRIMARY,
                ft.ControlState.DISABLED: C.COLOR_SURFACE_LIGHT,
            },
            color={
                ft.ControlState.DEFAULT: "#FFFFFF",
                ft.ControlState.DISABLED: C.COLOR_TEXT_MUTED,
            },
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding(20, 14, 20, 14),
        ),
    )


def secondary_button(
    text: str,
    on_click=None,
    icon=None,
) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=C.COLOR_TEXT,
            side=ft.BorderSide(1, C.COLOR_BORDER),
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding(20, 14, 20, 14),
        ),
    )


def danger_button(
    text: str,
    on_click=None,
    icon=None,
) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        content=ft.Text(text),
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor=C.COLOR_DANGER,
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding(20, 14, 20, 14),
        ),
    )


def status_badge(status: str, label: str | None = None) -> ft.Container:
    color = C.STATUS_COLORS.get(status, C.COLOR_TEXT_MUTED)

    return ft.Container(
        content=ft.Text(
            label or status.replace("_", " ").capitalize(),
            size=12,
            weight=ft.FontWeight.BOLD,
            color=color,
        ),
        bgcolor=ft.Colors.with_opacity(0.15, color),
        border=ft.Border.all(1, color),
        border_radius=20,
        padding=ft.Padding(12, 5, 12, 5),
    )


def text_field(label: str, **kwargs) -> ft.TextField:
    return ft.TextField(
        label=label,
        border_color=C.COLOR_BORDER,
        focused_border_color=C.COLOR_PRIMARY,
        label_style=ft.TextStyle(color=C.COLOR_TEXT_MUTED),
        text_style=ft.TextStyle(color=C.COLOR_TEXT),
        cursor_color=C.COLOR_PRIMARY,
        border_radius=8,
        **kwargs,
    )


def dropdown_field(label: str, options: list, **kwargs) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=[
            ft.dropdown.Option(key=o[0], text=o[1])
            if isinstance(o, tuple)
            else ft.dropdown.Option(o)
            for o in options
        ],
        border_color=C.COLOR_BORDER,
        focused_border_color=C.COLOR_PRIMARY,
        label_style=ft.TextStyle(color=C.COLOR_TEXT_MUTED),
        border_radius=8,
        **kwargs,
    )


def show_snackbar(page: ft.Page, message: str, success: bool = True):
    snack = ft.SnackBar(
        content=ft.Text(message, color="#FFFFFF"),
        bgcolor=C.COLOR_SUCCESS if success else C.COLOR_DANGER,
    )
    page.show_dialog(snack)


def confirm_dialog(page: ft.Page, title: str, message: str, on_confirm):
    def close_dialog(e=None):
        dialog.open = False
        dialog.update()

    def confirm(e):
        close_dialog()
        try:
            on_confirm()
        except Exception as exc:
            # Filet de sécurité, cf. data_table.form_dialog : une exception
            # imprévue lors d'une confirmation (suppression, etc.) ne doit
            # jamais faire planter l'application silencieusement.
            import traceback
            traceback.print_exc()
            show_snackbar(page, f"Une erreur inattendue est survenue : {exc}", success=False)

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=C.COLOR_SURFACE,
        title=ft.Text(title, color=C.COLOR_TEXT),
        content=ft.Text(message, color=C.COLOR_TEXT_MUTED),
        actions=[
            ft.TextButton(
                content=ft.Text("Annuler"),
                on_click=close_dialog,
                style=ft.ButtonStyle(color=C.COLOR_TEXT_MUTED),
            ),
            ft.TextButton(
                content=ft.Text("Confirmer"),
                on_click=confirm,
                style=ft.ButtonStyle(color=C.COLOR_DANGER),
            ),
        ],
    )

    page.show_dialog(dialog)


def stat_card(
    title: str,
    value: str,
    icon: str,
    color: str | None = None,
) -> ft.Container:
    color = color or C.COLOR_PRIMARY

    return card_container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, color=color, size=28),
                        ft.Container(expand=True),
                    ]
                ),
                ft.Text(
                    value,
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=C.COLOR_TEXT,
                ),
                ft.Text(
                    title,
                    size=13,
                    color=C.COLOR_TEXT_MUTED,
                ),
            ],
            spacing=6,
        )
    )


def loading_indicator() -> ft.Row:
    return ft.Row(
        [
            ft.ProgressRing(
                color=C.COLOR_PRIMARY,
                width=32,
                height=32,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )


def empty_state(
    message: str,
    icon: str = ft.Icons.INBOX_OUTLINED,
) -> ft.Column:
    return ft.Column(
        [
            ft.Icon(
                icon,
                size=48,
                color=C.COLOR_TEXT_MUTED,
            ),
            ft.Text(
                message,
                color=C.COLOR_TEXT_MUTED,
                size=14,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )