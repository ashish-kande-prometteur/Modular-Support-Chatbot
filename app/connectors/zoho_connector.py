import json


class ZohoConnector:

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_tickets(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("tickets", [])

connector = ZohoConnector(
    "data/zoho_all_tickets_full.json"
)

tickets = connector.load_tickets()

print(len(tickets))
