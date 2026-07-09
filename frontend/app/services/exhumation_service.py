from app.services.api_client import ApiClient


class ExhumationService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self):
        return self.client.get("/exhumations/")

    def create(self, data: dict):
        return self.client.post("/exhumations/", data)

    def change_status(self, exhumation_id: str, status: str, date_realisation: str = None):
        payload = {"status": status}
        if date_realisation:
            payload["date_realisation"] = date_realisation
        return self.client.post(f"/exhumations/{exhumation_id}/status", payload)

    def delete(self, exhumation_id: str):
        return self.client.delete(f"/exhumations/{exhumation_id}")
