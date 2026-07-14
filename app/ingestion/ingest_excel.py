import json
from pathlib import Path

from excel_loader import (
    load_excel_tickets
)

BASE_DIR = Path(__file__).resolve().parents[2]

EXCEL_FILE = (
    BASE_DIR
    / "data"
    / "Zoho_Desk_All_Tickets.xlsx"
)

OUTPUT_FILE = (
    BASE_DIR
    / "app"
    / "output"
    / "excel_chunks.json"
)


def main():

    chunks = load_excel_tickets(
        EXCEL_FILE
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

    print(
        f"Saved {len(chunks)} excel tickets"
    )


if __name__ == "__main__":
    main()