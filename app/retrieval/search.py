from sentence_transformers import SentenceTransformer
import psycopg
from pgvector.psycopg import register_vector

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="chatbot_db",
    user="postgres",
    password="postgres"
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

    cur.close()

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