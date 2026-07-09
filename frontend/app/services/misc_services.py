from app.services.api_client import ApiClient


class UserService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self):
        return self.client.get("/users")

    def create(self, data: dict):
        return self.client.post("/users", data)

    def update(self, user_id: str, data: dict):
        return self.client.put(f"/users/{user_id}", data)

    def delete(self, user_id: str):
        return self.client.delete(f"/users/{user_id}")

    def reset_password(self, user_id: str, new_password: str):
        return self.client.post(f"/users/{user_id}/reset-password", {"new_password": new_password})


class NotificationService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self):
        return self.client.get("/notifications/")

    def unread_count(self):
        return self.client.get("/notifications/unread-count")

    def mark_read(self, notification_id: str):
        return self.client.post(f"/notifications/{notification_id}/read")

    def mark_all_read(self):
        return self.client.post("/notifications/read-all")


class AuditService:
    def __init__(self, client: ApiClient):
        self.client = client

    def list(self, table_name: str = None, action: str = None):
        params = {}
        if table_name:
            params["table_name"] = table_name
        if action:
            params["action"] = action
        return self.client.get("/audit/", params=params)

    def export_csv(self, table_name: str = None, action: str = None) -> bytes:
        params = {}
        if table_name:
            params["table_name"] = table_name
        if action:
            params["action"] = action
        return self.client.get("/audit/export/csv", params=params)
