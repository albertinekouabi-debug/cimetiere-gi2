from app.services.api_client import ApiClient


class CemeteryService:
    def __init__(self, client: ApiClient):
        self.client = client

    # Sections
    def list_sections(self):
        return self.client.get("/cimetiere/sections")

    def create_section(self, data: dict):
        return self.client.post("/cimetiere/sections", data)

    def update_section(self, section_id: str, data: dict):
        return self.client.put(f"/cimetiere/sections/{section_id}", data)

    def delete_section(self, section_id: str):
        return self.client.delete(f"/cimetiere/sections/{section_id}")

    # Blocs
    def list_blocs(self):
        return self.client.get("/cimetiere/blocs")

    def create_bloc(self, data: dict):
        return self.client.post("/cimetiere/blocs", data)

    def update_bloc(self, bloc_id: str, data: dict):
        return self.client.put(f"/cimetiere/blocs/{bloc_id}", data)

    def delete_bloc(self, bloc_id: str):
        return self.client.delete(f"/cimetiere/blocs/{bloc_id}")

    # Graves (caveaux)
    def list_graves(self, status: str = None, section_id: str = None):
        params = {}
        if status:
            params["status"] = status
        if section_id:
            params["section_id"] = section_id
        return self.client.get("/cimetiere/graves", params=params)

    def get_grave(self, grave_id: str):
        return self.client.get(f"/cimetiere/graves/{grave_id}")

    def create_grave(self, data: dict):
        return self.client.post("/cimetiere/graves", data)

    def update_grave(self, grave_id: str, data: dict):
        return self.client.put(f"/cimetiere/graves/{grave_id}", data)

    def delete_grave(self, grave_id: str):
        return self.client.delete(f"/cimetiere/graves/{grave_id}")

    def occupancy_stats(self):
        return self.client.get("/cimetiere/stats/occupancy")

    # Défunts
    def list_defunts(self):
        return self.client.get("/cimetiere/defunts")

    def search_defunts(self, query: str):
        return self.client.get("/cimetiere/defunts/recherche", params={"q": query})

    def create_defunt(self, data: dict):
        return self.client.post("/cimetiere/defunts", data)

    def update_defunt(self, defunt_id: str, data: dict):
        return self.client.put(f"/cimetiere/defunts/{defunt_id}", data)

    def delete_defunt(self, defunt_id: str):
        return self.client.delete(f"/cimetiere/defunts/{defunt_id}")
