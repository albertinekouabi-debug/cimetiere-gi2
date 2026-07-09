from app.services.api_client import ApiClient


class ConcessionService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self):
        return self.client.get("/concessions/")

    def create(self, data: dict):
        return self.client.post("/concessions/", data)

    def update(self, concession_id: str, data: dict):
        return self.client.put(f"/concessions/{concession_id}", data)

    def renew(self, concession_id: str, nouvelle_duree: str, montant_supplementaire: float = 0):
        return self.client.post(f"/concessions/{concession_id}/renew", {
            "nouvelle_duree": nouvelle_duree, "montant_supplementaire": montant_supplementaire
        })

    def delete(self, concession_id: str):
        return self.client.delete(f"/concessions/{concession_id}")
