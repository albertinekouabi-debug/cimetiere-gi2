import base64
import flet as ft

MIME_TYPES = {
    "pdf": "application/pdf",
    "csv": "text/csv",
}


async def _launch(page: ft.Page, url: str):
    """Wrapper async minimal. `page.launch_url` est bien une coroutine à
    l'exécution, mais le décorateur @deprecated qui l'enrobe dans cette
    version de Flet fait que `inspect.iscoroutinefunction(page.launch_url)`
    renvoie False. Or `page.run_task()` valide justement ce test avant
    d'accepter un handler ("handler must be a coroutine function"), donc
    passer `page.launch_url` directement à `run_task` plante. Cette
    fonction, elle, est une véritable coroutine reconnue comme telle."""
    await page.launch_url(url)


def download_file(page: ft.Page, file_bytes: bytes, extension: str):
    """Déclenche le téléchargement d'un fichier dans le navigateur via une
    data-URI (aucun stockage serveur nécessaire, fonctionne en mode Flet web)."""
    mime = MIME_TYPES.get(extension, "application/octet-stream")
    b64 = base64.b64encode(file_bytes).decode()
    page.run_task(_launch, page, f"data:{mime};base64,{b64}")
