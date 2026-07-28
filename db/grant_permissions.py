"""
grant_permissions.py

Automatically grants SELECT permission on all allowed tables
to the chatbot_reader role.

Run this whenever a new table is added to ALLOWED_TABLES.

Usage:
    python grant_permissions.py
"""

import os

import psycopg
from dotenv import load_dotenv

from allowed_tables import ALLOWED_TABLES

load_dotenv()


ADMIN_CONFIG = {
    "host": os.getenv("RAG_ADMIN_DB_HOST"),
    "port": os.getenv("RAG_ADMIN_DB_PORT"),
    "dbname": os.getenv("RAG_ADMIN_DB_NAME"),
    "user": os.getenv("RAG_ADMIN_DB_USER"),
    "password": os.getenv("RAG_ADMIN_DB_PASSWORD"),
}

CHATBOT_ROLE = os.getenv("RAG_SOURCE_DB_USER", "chatbot_reader")


def grant_permissions():
    conn = psycopg.connect(**ADMIN_CONFIG)

    try:
        with conn.cursor() as cursor:

            print(f"Granting permissions to '{CHATBOT_ROLE}'...\n")

            for table in ALLOWED_TABLES:

                query = (
                    f'GRANT SELECT ON TABLE "{table}" TO "{CHATBOT_ROLE}";'
                )

                cursor.execute(query)

                print(f"✓ Granted SELECT on {table}")

            conn.commit()

        print("\nAll permissions granted successfully.")

    except Exception as e:

        conn.rollback()

        print("\nFailed to grant permissions.")

        print(e)

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    grant_permissions()