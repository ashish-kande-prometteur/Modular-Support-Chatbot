from sentence_transformers import SentenceTransformer
import psycopg
from pgvector.psycopg import register_vector
import os 

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Create database connection
conn = psycopg.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)


register_vector(conn)


def search(query, top_k=5):
    embedding = model.encode(
        query
    ).tolist()

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            ticket_number,
            issue,
            resolution,
            embedding <=> %s::vector AS distance
        FROM ticket_embeddings
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (
            embedding,
            embedding,
            top_k
        )
    )

    results = cur.fetchall()

    for row in results:
        print("\n====================")
        print("Ticket Number:", row[0])
        print("Issue:", row[1][:100] if row[1] else None)
        print("Resolution:", row[2][:200] if row[2] else None)
        print("Distance:", row[3])

    return results


if __name__ == "__main__":

    results = search(
        "I cannot withdraw my money because of bank mismatch"
    )

    for result in results:
        print()
        print("=" * 50)
        print("Ticket:", result[0])
        print("Issue:", result[1])
        print("Distance:", result[3])
        print()
        print((result[2] or "No resolution found")[:300])