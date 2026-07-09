"""
Client HTTP centralisé pour l'API Django Ninja.
Gère : jetons JWT (access/refresh), rafraîchissement automatique sur 401,
sérialisation JSON, et exceptions métier lisibles pour l'UI.
"""
import httpx
from typing import Optional, Any
from app.config import API_BASE_URL


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ApiClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self._client = httpx.Client(base_url=self.base_url, timeout=20.0)

    # ─── Gestion des jetons ───────────────────────────────────────────────
    def set_tokens(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def clear_tokens(self):
        self.access_token = None
        self.refresh_token = None

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _try_refresh(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            resp = self._client.post("/auth/refresh", json={"refresh_token": self.refresh_token})
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                return True
        except httpx.RequestError:
            pass
        return False

    # ─── Requête générique ────────────────────────────────────────────────
    def request(self, method: str, path: str, json_body: Optional[dict] = None,
                params: Optional[dict] = None, retry_on_401: bool = True) -> Any:
        try:
            resp = self._client.request(method, path, json=json_body, params=params, headers=self._headers())
        except httpx.ConnectError:
            raise ApiError("Impossible de joindre le serveur. Vérifiez votre connexion ou que le serveur est démarré.")
        except httpx.TimeoutException:
            raise ApiError("Le serveur met trop de temps à répondre. Réessayez.")
        except httpx.RequestError as e:
            raise ApiError(f"Erreur réseau : {e}")

        if resp.status_code == 401 and retry_on_401 and self._try_refresh():
            return self.request(method, path, json_body, params, retry_on_401=False)

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text or f"Erreur HTTP {resp.status_code}"
            raise ApiError(detail, resp.status_code)

        content_type = resp.headers.get("content-type", "")
        if content_type.startswith("application/pdf") or content_type.startswith("text/csv"):
            return resp.content

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def get(self, path: str, params: Optional[dict] = None):
        return self.request("GET", path, params=params)

    def post(self, path: str, json_body: Optional[dict] = None):
        return self.request("POST", path, json_body=json_body)

    def put(self, path: str, json_body: Optional[dict] = None):
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str):
        return self.request("DELETE", path)

    def close(self):
        self._client.close()
