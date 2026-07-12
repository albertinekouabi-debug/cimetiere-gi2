"""Composant de liste/tableau générique avec actions (édition/suppression),
utilisé par les pages Sections/Blocs/Caveaux/etc. pour éviter la duplication."""
import traceback
import flet as ft
from app import config as C
from app.components.theme import card_container, primary_button, empty_state, responsive_width, show_snackbar


def build_data_table(columns: list[str], rows: list[list], on_edit=None, on_delete=None, can_write: bool = True, extra_action=None) -> ft.Control:
    """extra_action, si fourni, est un tuple (icone, couleur, tooltip, callback(row_id))
    ajoutant un bouton d'action supplémentaire avant Éditer/Supprimer (ex: réinitialiser un mot de passe)."""
    if not rows:
        return card_container(empty_state("Aucune donnée pour le moment."))

    table_columns = [ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD, color=C.COLOR_TEXT_MUTED, size=12)) for c in columns]
    if can_write and (on_edit or on_delete or extra_action):
        table_columns.append(ft.DataColumn(ft.Text("")))

    table_rows = []
    for row_data, row_id in rows:
        cells = [ft.DataCell(cell if isinstance(cell, ft.Control) else ft.Text(str(cell), color=C.COLOR_TEXT, size=13)) for cell in row_data]
        if can_write and (on_edit or on_delete or extra_action):
            actions = []
            if extra_action:
                icon, color, tooltip, callback = extra_action
                actions.append(ft.IconButton(icon, icon_size=18, icon_color=color, tooltip=tooltip, on_click=lambda e, rid=row_id: callback(rid)))
            if on_edit:
                actions.append(ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18, icon_color=C.COLOR_INFO, tooltip="Modifier", on_click=lambda e, rid=row_id: on_edit(rid)))
            if on_delete:
                actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=C.COLOR_DANGER, tooltip="Supprimer", on_click=lambda e, rid=row_id: on_delete(rid)))
            cells.append(ft.DataCell(ft.Row(actions, spacing=0)))
        table_rows.append(ft.DataRow(cells=cells))

    table = ft.DataTable(
        columns=table_columns,
        rows=table_rows,
        heading_row_color=C.COLOR_SURFACE_LIGHT,
        data_row_color={ft.ControlState.HOVERED: C.COLOR_SURFACE_LIGHT},
        border=ft.Border.all(1, C.COLOR_BORDER),
        border_radius=10,
        column_spacing=24,
        horizontal_lines=ft.BorderSide(1, C.COLOR_BORDER),
    )
    # Un DataTable ne réduit ni ne fait passer ses colonnes à la ligne : si
    # leur largeur cumulée dépasse la largeur de l'écran (quasi systématique
    # sur mobile dès qu'il y a 4-5 colonnes + actions), les colonnes de
    # droite étaient tout simplement invisibles, sans aucun moyen d'y
    # accéder. On enveloppe donc le tableau dans un défilement horizontal :
    # rien n'est perdu, il suffit de glisser pour voir la suite.
    return ft.Container(
        content=ft.Row([table], scroll=ft.ScrollMode.AUTO),
        border_radius=10,
    )


def form_dialog(page: ft.Page, title: str, fields: list[ft.Control], on_save, save_label: str = "Enregistrer"):
    def close_dialog(e=None):
        # Ferme CE dialogue précisément (et non "le plus récent encore
        # ouvert" via page.pop_dialog()) : si le code appelant affiche une
        # snackbar avant de fermer le formulaire, page.pop_dialog() fermerait
        # la snackbar à la place de ce dialogue, laissant le formulaire ouvert.
        dialog.open = False
        dialog.update()

    def save(e):
        try:
            on_save(close_dialog)
        except Exception as exc:
            # Filet de sécurité : une exception imprévue dans la logique de
            # sauvegarde d'une page (bug non anticipé, format de donnée
            # inattendu, etc.) ne doit jamais faire planter l'application ni
            # laisser l'interface silencieusement figée. On journalise la
            # trace complète en console pour le diagnostic, et on affiche un
            # message clair à l'utilisateur ; le dialogue reste ouvert pour
            # permettre de corriger la saisie et réessayer.
            traceback.print_exc()
            show_snackbar(page, f"Une erreur inattendue est survenue : {exc}", success=False)

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=C.COLOR_SURFACE,
        title=ft.Text(title, color=C.COLOR_TEXT),
        content=ft.Container(
            content=ft.Column(fields, spacing=14, tight=True, scroll=ft.ScrollMode.AUTO),
            width=responsive_width(page, max=420, min=300),
            height=min(70 * len(fields) + 40, 480),
        ),
        actions=[
            ft.TextButton(content=ft.Text("Annuler"), on_click=close_dialog, style=ft.ButtonStyle(color=C.COLOR_TEXT_MUTED)),
            ft.ElevatedButton(content=ft.Text(save_label), on_click=save, style=ft.ButtonStyle(bgcolor=C.COLOR_PRIMARY, color="#ffffff")),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)
    return dialog


def page_header(page: ft.Page, title: str, action_label: str = None, on_action=None, icon=None) -> ft.Control:
    """En-tête de page avec titre + bouton d'action optionnel. Sur petit
    écran (< 640px), le bouton passe sous le titre plutôt que de le
    chevaucher (cause du chevauchement visible sur mobile/fenêtre étroite)."""
    title_control = ft.Text(title, size=16, color=C.COLOR_TEXT_MUTED, overflow=ft.TextOverflow.ELLIPSIS)
    narrow = getattr(page, "width", None) is not None and page.width < 640

    if not (action_label and on_action):
        return ft.Row([ft.Container(content=title_control, expand=True)])

    button = primary_button(action_label, on_click=on_action, icon=icon or ft.Icons.ADD)

    if narrow:
        return ft.Column([title_control, button], spacing=12)
    return ft.Row([ft.Container(content=title_control, expand=True), button])
