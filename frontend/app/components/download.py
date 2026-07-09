import base64
import flet as ft

MIME_TYPES = {
    "pdf": "application/pdf",
    "csv": "text/csv",
}


def download_file(page: ft.Page, file_bytes: bytes, extension: str):
    """Déclenche le téléchargement d'un fichier dans le navigateur via une
    data-URI (aucun stockage serveur nécessaire, fonctionne en mode Flet web).

    `page.launch_url()` est une coroutine dans cette version de Flet : un
    appel synchrone direct crée l'objet coroutine sans jamais l'exécuter (le
    navigateur ne reçoit alors jamais l'ordre de téléchargement, sans la
    moindre erreur visible). On la planifie donc via `page.run_task()`,
    utilisable depuis un gestionnaire d'événement synchrone."""
    mime = MIME_TYPES.get(extension, "application/octet-stream")
    b64 = base64.b64encode(file_bytes).decode()
    page.run_task(page.launch_url, f"data:{mime};base64,{b64}")
