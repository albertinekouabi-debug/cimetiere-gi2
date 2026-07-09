from app.services.api_client import ApiClient


class PaymentService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self):
        return self.client.get("/paiements/")

    def stats(self):
        return self.client.get("/paiements/stats")

    def create(self, data: dict):
        return self.client.post("/paiements/", data)

    def delete(self, paiement_id: str):
        return self.client.delete(f"/paiements/{paiement_id}")

    def download_recu(self, paiement_id: str) -> bytes:
        return self.client.get(f"/paiements/{paiement_id}/recu")

    def export_pdf(self, date_debut: str = None, date_fin: str = None) -> bytes:
        params = {}
        if date_debut:
            params["date_debut"] = date_debut
        if date_fin:
            params["date_fin"] = date_fin
        return self.client.get("/paiements/export/pdf", params=params)

    def export_csv(self, date_debut: str = None, date_fin: str = None) -> bytes:
        params = {}
        if date_debut:
            params["date_debut"] = date_debut
        if date_fin:
            params["date_fin"] = date_fin
        return self.client.get("/paiements/export/csv", params=params)

    # MTN MoMo
    def momo_initiate(self, concession_id: str, montant: float, phone_number: str, notes: str = None):
        payload = {"concession_id": concession_id, "montant": montant, "phone_number": phone_number}
        if notes:
            payload["notes"] = notes
        return self.client.post("/paiements/momo/initiate", payload)

    def momo_status(self, reference_id: str):
        return self.client.get(f"/paiements/momo/{reference_id}/status")

    def momo_transactions(self):
        return self.client.get("/paiements/momo/transactions")
