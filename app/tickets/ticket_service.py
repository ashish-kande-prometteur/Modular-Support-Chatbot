import os

from app.tickets.zoho_adapter import (
    ZohoAdapter
)


PROVIDERS = {
    "zoho":
        ZohoAdapter
}


def get_ticket_provider():

    provider_name = os.getenv(
        "TICKET_PROVIDER",
        "zoho"
    )

    provider_class = PROVIDERS[
        provider_name
    ]

    return provider_class()
