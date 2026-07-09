from app.services.api_client import ApiClient


class AuthService:
    def __init__(self, client: ApiClient):
        self.client = client

    def login(self, email: str, password: str) -> dict:
        data = self.client.post("/auth/login", {"email": email, "password": password})
        self.client.set_tokens(data["tokens"]["access_token"], data["tokens"]["refresh_token"])
        return data["profile"]

    def logout(self):
        self.client.clear_tokens()

    def me(self) -> dict:
        return self.client.get("/auth/me")

    def change_password(self, old_password: str, new_password: str):
        return self.client.post("/auth/change-password", {"old_password": old_password, "new_password": new_password})
