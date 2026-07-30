"""
app/ingestion/embed_chunks.py

Reads processed_chunks.json (tickets + excel + docs + database chunks)
and embeds everything into the existing ticket_embeddings table.

Only change from the original version: content_hash (added by
db_loader.py) now rides along in `metadata`, so future incremental-sync
work can diff on it without a schema migration.
"""

import json
import os
from pathlib import Path

import psycopg
from tqdm import tqdm
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILES = [
    BASE_DIR / "app" / "output" / "processed_chunks.json",
]

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))


def load_chunks():
    all_chunks = []
    for file in INPUT_FILES:
        if not file.exists():
            continue
        with open(file, "r", encoding="utf-8") as f:
            all_chunks.extend(json.load(f))
    return all_chunks


def create_embedding_text(chunk):
    if chunk.get("content"):
        return chunk["content"]

    parts = []
    issue = chunk.get("issue") or chunk.get("question") or chunk.get("document")
    resolution = chunk.get("resolution") or chunk.get("content")

    if issue:
        parts.append(f"Issue:\n{issue}")
    if resolution:
        parts.append(f"Resolution:\n{resolution}")
    if chunk.get("status"):
        parts.append(f"Status:\n{chunk['status']}")
    if chunk.get("channel"):
        parts.append(f"Channel:\n{chunk['channel']}")
    if chunk.get("source"):
        parts.append(f"Source:\n{chunk['source']}")

    return "\n\n".join(parts)


def main():
    print("Loading processed chunks...")
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    conn = psycopg.connect(**DB_CONFIG)
    register_vector(conn)
    cur = conn.cursor()

    inserted = 0

    for chunk in tqdm(chunks):
        text = create_embedding_text(chunk)

        if not text.strip():
            continue

        embedding = model.encode(text).tolist()

        ticket_id = chunk.get("ticket_id")
        ticket_number = chunk.get("ticket_number")

        if not ticket_id:
            ticket_id = f"{chunk.get('source', 'doc')}_{chunk.get('ref_id', inserted)}"

        if not ticket_number:
            ticket_number = f"{chunk.get('source', 'DOC').upper()}-{inserted}"

        issue = (
            chunk.get("issue")
            or chunk.get("question")
            or chunk.get("section")
            or chunk.get("document")
            or "Knowledge Base Document"
        )

        resolution = chunk.get("resolution") or chunk.get("content") or ""

        cur.execute(
            """
            INSERT INTO ticket_embeddings(
                ticket_id, ticket_number, issue, resolution, embedding, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                ticket_id,
                ticket_number,
                issue,
                resolution,
                embedding,
                json.dumps(
                    {
                        "status": chunk.get("status"),
                        "channel": chunk.get("channel"),
                        "source": chunk.get("source"),
                        "created_time": chunk.get("created_time"),
                        "closed_time": chunk.get("closed_time"),
                        "section": chunk.get("section"),
                        "document": chunk.get("document"),
                        "ref_id": chunk.get("ref_id"),
                        "content_hash": chunk.get("content_hash"),
                    }
                ),
            ),
        )

        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Inserted {inserted} embeddings")


if __name__ == "__main__":
    main()
