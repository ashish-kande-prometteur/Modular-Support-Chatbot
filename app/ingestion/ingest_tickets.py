import json
import os
from pathlib import Path

from excel_loader import load_excel_tickets
from document_loader import load_document_chunks
from db_loader import load_database_chunks


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "zoho_all_tickets_full.json"

OUTPUT_FILE = (
    BASE_DIR
    / "app"
    / "output"
    / "processed_chunks.json"
)


website_urls = os.getenv(
    "WEBSITE_URLS",
    ""
)


def load_tickets():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data.get(
        "tickets",
        []
    )


def extract_issue(ticket):
    """
    First version:
    Use subject as issue.
    """

    return ticket.get(
        "subject",
        "Unknown Issue"
    )


def extract_resolution(ticket):
    """
    Get the last meaningful agent response.
    """

    conversations = ticket.get(
        "conversation",
        []
    )

    agent_messages = []

    for message in conversations:

        author = message.get(
            "author",
            {}
        )

        if author.get("type") == "AGENT":

            content = message.get(
                "content",
                ""
            )

            if (
                content
                and len(content.strip()) > 20
            ):

                agent_messages.append(
                    content.strip()
                )

    if agent_messages:

        return agent_messages[-1]

    return None


def create_chunk(ticket):

    issue = extract_issue(ticket)

    resolution = extract_resolution(ticket)

    return {
        "ticket_id": ticket.get("id"),
        "ticket_number": ticket.get("ticketNumber"),
        "issue": issue,
        "resolution": resolution,
        "status": ticket.get("status"),
        "channel": ticket.get("channel"),
        "created_time": ticket.get("createdTime"),
        "closed_time": ticket.get("closedTime"),
        "source": "json"
    }


def save_chunks(chunks):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            chunks,
            f,
            indent=4,
            ensure_ascii=False
        )


def main():

    print("Loading tickets...")

    json_tickets = load_tickets()

    excel_tickets = load_excel_tickets()

    document_chunks = load_document_chunks()

    database_chunks = load_database_chunks()


    tickets = (
        json_tickets
        + excel_tickets
        + document_chunks
        + database_chunks
    )

    print(f"Loaded {len(tickets)} total records")

    processed_chunks = []

    for ticket in tickets:

        source = ticket.get("source")

        # Already processed chunks
        if source in [
            "excel",
            "website",
            "faq",
            "betting_rules",
            "privacy_policy",
            "responsible_gaming",
            "terms_conditions",
            "database",
        ]:

            processed_chunks.append(
                ticket
            )

            continue

        # Raw Zoho ticket
        processed_chunks.append(
            create_chunk(ticket)
        )

    save_chunks(
        processed_chunks
    )

    print(
        f"\nSaved {len(processed_chunks)} processed chunks"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":

    main()
