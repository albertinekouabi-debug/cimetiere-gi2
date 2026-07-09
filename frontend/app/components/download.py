import base64
import flet as ft

MIME_TYPES = {
    "pdf": "application/pdf",
    "csv": "text/csv",
}


def download_file(page: ft.Page, file_bytes: bytes, extension: str):
    """Déclenche le téléchargement d'un fichier dans le navigateur via une
    data-URI (aucun stockage serveur nécessaire, fonctionne en mode Flet web)."""
    mime = MIME_TYPES.get(extension, "application/octet-stream")
    b64 = base64.b64encode(file_bytes).decode()
    page.launch_url(f"data:{mime};base64,{b64}")
