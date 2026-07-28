import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv

load_dotenv()


class PostgresConnector:
    """
    Read-only PostgreSQL connector used by the chatbot ingestion pipeline.

    Responsibilities:
        - Open PostgreSQL connection
        - Start READ ONLY transactions
        - Return reusable cursors
        - Ensure proper cleanup

    This connector MUST NEVER perform INSERT/UPDATE/DELETE operations.
    """

    def __init__(self):
        self.config = {
            "host": os.getenv("RAG_SOURCE_DB_HOST"),
            "port": os.getenv("RAG_SOURCE_DB_PORT"),
            "dbname": os.getenv("RAG_SOURCE_DB_NAME"),
            "user": os.getenv("RAG_SOURCE_DB_USER"),
            "password": os.getenv("RAG_SOURCE_DB_PASSWORD"),
        }

    def get_connection(self):
        """
        Create a new PostgreSQL connection.

        Returns:
            psycopg.Connection
        """
        return psycopg.connect(**self.config)

    @contextmanager
    def get_cursor(self):
        """
        Opens a read-only transaction and yields a cursor.

        Usage:
            connector = PostgresConnector()

            with connector.get_cursor() as cursor:
                cursor.execute(...)
        """

        conn = self.get_connection()

        try:
            # Begin transaction
            conn.execute("BEGIN")

            # Enforce read-only mode
            conn.execute("SET TRANSACTION READ ONLY")

            with conn.cursor() as cursor:
                yield cursor

            # Nothing to commit in READ ONLY mode
            conn.rollback()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()