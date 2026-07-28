"""
app/ingestion/db_loader.py

Reads exported database JSON files created by db_reader.py
and converts them into chunks that match the existing
embedding pipeline.

Flow

db_reader.py
        ↓
app/data/db_export/*.json
        ↓
db_loader.py
        ↓
processed_chunks.json
"""

import hashlib
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "db_export"
)

def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _english(value):
    """
    Extract English value from multilingual JSON.
    """

    if isinstance(value, dict):

        return (
            value.get("EN")
            or value.get("en")
            or next(iter(value.values()), "")
        )

    return value


def _bonus_chunk(record):

    bonus_percent = ""

    if isinstance(record.get("bonus_percent"), dict):

        values = list(record["bonus_percent"].values())

        if values:
            bonus_percent = values[0]

    lines = [
        f"Promotion Title: {record.get('promotion_title')}",
        f"Description: {record.get('description')}",
        f"Terms & Conditions: {record.get('terms_and_conditions')}",
        f"Bonus Percentage: {bonus_percent}",
        f"Bonus Type: {record.get('bonus_type')}",
        f"Currency Code: {record.get('currency_code')}",
        f"Minimum Deposit: {record.get('min_deposit')}",
    ]

    return "\n".join(
        line
        for line in lines
        if line.split(": ", 1)[1] not in ["", "None", "null"]
    )


def _casino_category_chunk(record):

    return (
        f"Casino Category: "
        f"{_english(record.get('name'))}"
    )


def _casino_provider_chunk(record):

    return (
        f"Casino Provider: "
        f"{_english(record.get('name'))}"
    )


def _country_chunk(record):

    return (
        f"Country Code: {record.get('code')}\n"
        f"Country Name: {record.get('name')}"
    )


def _record_to_text(table_name, record):

    if table_name == "bonus":
        return _bonus_chunk(record)

    if table_name == "casino_categories":
        return _casino_category_chunk(record)

    if table_name == "casino_providers":
        return _casino_provider_chunk(record)

    if table_name == "countries":
        return _country_chunk(record)

    # Skip CMS for now
    if table_name == "cms":
        return None

    return None


def load_database_chunks():

    chunks = []

    if not EXPORT_DIR.exists():

        print("Database export folder not found.")

        return chunks

    for json_file in EXPORT_DIR.glob("*.json"):

        table_name = json_file.stem

        if table_name == "cms":

            print("Skipping cms")

            continue

        print(f"Loading {table_name}")

        with open(
            json_file,
            "r",
            encoding="utf-8"
        ) as f:

            records = json.load(f)

        for index, record in enumerate(records):

            content = _record_to_text(
                table_name,
                record
            )

            if not content:

                continue

            ref_id = (
                f"{table_name}_"
                f"{record.get('id', index)}"
            )

            chunks.append(
                {
                    "source": "database",
                    "document": table_name,
                    "ref_id": ref_id,
                    "content": content,
                    "content_hash": _content_hash(
                        content
                    )
                }
            )

    print(
        f"Database Chunks: "
        f"{len(chunks)}"
    )

    return chunks


if __name__ == "__main__":

    chunks = load_database_chunks()

    print(
        json.dumps(
            chunks[:5],
            indent=4,
            ensure_ascii=False
        )
    )