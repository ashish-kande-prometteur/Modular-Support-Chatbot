import os
import httpx

from dotenv import load_dotenv

from app.tickets.base import (
    TicketProvider
)

load_dotenv()


class ZohoAdapter(
    TicketProvider
):

    def create_ticket(
        self,
        payload: dict
    ) -> dict:

        zoho_payload = {
            "subject": payload["user_query"][:100],
            "description": payload.get("bot_answer") or "No answer found",
            "departmentId": os.getenv("ZOHO_DEPARTMENT_ID"),
            "contactId": os.getenv("ZOHO_CONTACT_ID")
        }

        response = httpx.post(
            f"{os.getenv('ZOHO_API_BASE_URL')}/tickets",
            json=zoho_payload,
            headers={
                "Authorization":
                    f"Zoho-oauthtoken "
                    f"{os.getenv('ZOHO_ACCESS_TOKEN')}",

                "orgId":
                    os.getenv(
                        "ZOHO_ORG_ID"
                    ),

                "Content-Type":
                    "application/json"
            },
            timeout=int(
                os.getenv(
                    "TICKET_API_TIMEOUT_SECONDS",
                    30
                )
            )
        )

        if response.status_code != 200 and response.status_code != 201:
            print("Zoho Response Status:", response.status_code)
            print("Zoho Response Body:", response.text)

        response.raise_for_status()

        return response.json()
