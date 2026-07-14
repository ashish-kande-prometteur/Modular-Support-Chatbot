import json
import psycopg
from tqdm import tqdm
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector


from pathlib import Path


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILES = [
    BASE_DIR / "app" / "output" / "processed_chunks.json",
    BASE_DIR / "app" / "output" / "excel_chunks.json"
]

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


model = SentenceTransformer(
    os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"
    )
)

def load_chunks():

    all_chunks = []

    for file in INPUT_FILES:

        if not file.exists():
            continue

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:
            all_chunks.extend(
                json.load(f)
            )

    return all_chunks

def create_embedding_text(chunk):
    parts = []

    if chunk.get("issue"):
        parts.append(
            f"Issue:\n{chunk['issue']}"
        )

    if chunk.get("resolution"):
        parts.append(
            f"Resolution:\n{chunk['resolution']}"
        )

    if chunk.get("status"):
        parts.append(
            f"Status:\n{chunk['status']}"
        )

    if chunk.get("channel"):
        parts.append(
            f"Channel:\n{chunk['channel']}"
        )

    if chunk.get("source"):
        parts.append(
            f"Source:\n{chunk['source']}"
        )

    return "\n\n".join(parts)


def main():

    print(
        "Loading processed chunks..."
    )

    chunks = load_chunks()

    print(
        f"Loaded {len(chunks)} chunks"
    )

    conn = psycopg.connect(
        **DB_CONFIG
    )

    register_vector(conn)

    cur = conn.cursor()

    inserted = 0

    for chunk in tqdm(chunks):

        text = create_embedding_text(
            chunk
        )

        embedding = model.encode(
            text
        ).tolist()

        cur.execute(
            """
            INSERT INTO ticket_embeddings(
                ticket_id,
                ticket_number,
                issue,
                resolution,
                embedding,
                metadata
            )
            VALUES(
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                chunk["ticket_id"],
                chunk["ticket_number"],
                chunk["issue"],
                chunk["resolution"],
                embedding,
                json.dumps(
                    {
                        "status":
                            chunk.get(
                                "status"
                            ),

                        "channel":
                            chunk.get(
                                "channel"
                            ),

                        "source":
                            chunk.get(
                                "source"
                            ),

                        "created_time":
                            chunk.get(
                                "created_time"
                            ),

                        "closed_time":
                            chunk.get(
                                "closed_time"
                            )
                    }
                )
            )
        )

        inserted += 1

    conn.commit()

    cur.close()
    conn.close()

    print(
        f"Inserted {inserted} embeddings"
    )


if __name__ == "__main__":
    main()