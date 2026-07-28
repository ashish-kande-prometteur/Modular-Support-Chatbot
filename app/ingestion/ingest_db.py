"""
app/ingestion/ingest_db.py

Standalone runner for JUST the database ingestion step. Use this to
verify the DB -> chunks flow works end-to-end (connection, view access,
templating, hashing) before merging its output into the full
processed_chunks.json pipeline in ingest_tickets.py.

Usage:
    python -m app.ingestion.ingest_db

Output:
    app/output/db_chunks.json
"""

import json
from pathlib import Path

from app.ingestion.db_loader import load_database_chunks

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_FILE = BASE_DIR / "app" / "output" / "db_chunks.json"


def main():
    chunks = load_database_chunks()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(chunks)} DB chunks -> {OUTPUT_FILE}")

    if chunks:
        print("\nSample chunk:")
        print(json.dumps(chunks[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
