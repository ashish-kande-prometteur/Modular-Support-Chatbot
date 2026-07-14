import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EXCEL_FILE = (
    BASE_DIR
    / "data"
    / "Zoho_Desk_All_Tickets.xlsx"
)


def load_excel_tickets():
    df = pd.read_excel(EXCEL_FILE)

    tickets = []

    for _, row in df.iterrows():

        ticket = {
            "ticket_id": str(
                row.get("Ticket ID", "")
            ),

            "ticket_number": str(
                row.get("Ticket ID", "")
            ),

            "issue": str(
                row.get(
                    "Subject",
                    ""
                )
            ),

            "resolution": str(
                row.get(
                    "Question",
                    ""
                )
            ),

            "status": str(
                row.get(
                    "Status",
                    ""
                )
            ),

            "channel": str(
                row.get(
                    "Channel",
                    ""
                )
            ),

            "created_time": str(
                row.get(
                    "Created Time",
                    ""
                )
            ),

            "closed_time": str(
                row.get(
                    "Closed Time",
                    ""
                )
            ),

            "source": "excel"
        }

        tickets.append(ticket)

    return tickets