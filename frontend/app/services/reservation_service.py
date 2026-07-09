from app.services.api_client import ApiClient


class ReservationService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self):
        return self.client.get("/reservations/")

    def stats(self):
        return self.client.get("/reservations/stats")

    def create(self, data: dict):
        return self.client.post("/reservations/", data)

    def validate(self, reservation_id: str, status: str, notes: str = None):
        payload = {"status": status}
        if notes:
            payload["notes"] = notes
        return self.client.post(f"/reservations/{reservation_id}/validate", payload)

    def archive(self, reservation_id: str):
        return self.client.post(f"/reservations/{reservation_id}/archive")

    def delete(self, reservation_id: str):
        return self.client.delete(f"/reservations/{reservation_id}")
