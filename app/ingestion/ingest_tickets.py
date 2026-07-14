import json
from pathlib import Path
from excel_loader import load_excel_tickets

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "zoho_all_tickets_full.json"
OUTPUT_FILE = BASE_DIR / "app" / "output" / "processed_chunks.json"


def load_tickets():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("tickets", [])


def extract_issue(ticket):
    """
    First version:
    Use subject as issue.
    Later this can be replaced with LLM extraction.
    """
    return ticket.get("subject", "Unknown Issue")


def extract_resolution(ticket):
    """
    Get the last meaningful agent response.
    """
    conversations = ticket.get("conversation", [])

    agent_messages = []

    for message in conversations:
        author = message.get("author", {})

        if author.get("type") == "AGENT":
            content = message.get("content", "")

            if content and len(content.strip()) > 20:
                agent_messages.append(content.strip())

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
        "closed_time": ticket.get("closedTime")
    }


def save_chunks(chunks):
    Path("output").mkdir(
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

    tickets = (
        json_tickets
        + excel_tickets
    )

    print(
        f"Loaded {len(tickets)} tickets"
    )

    processed_chunks = []

    for ticket in tickets:

        if ticket.get("source") == "excel":
            processed_chunks.append(
                ticket
            )

        else:
            chunk = create_chunk(
                ticket
            )

            chunk["source"] = "json"

            processed_chunks.append(
                chunk
            )

    save_chunks(
        processed_chunks
    )

    print(
        f"Saved {len(processed_chunks)} processed tickets"
    )
    print(
        f"Output file: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()