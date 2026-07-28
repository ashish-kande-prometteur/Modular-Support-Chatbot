"""
app/db/db_reader.py

Reads approved PostgreSQL tables using the read-only chatbot_reader role
and exports each table into a separate JSON file.

Flow

PostgreSQL
    ↓
Allowed Tables
    ↓
SELECT *
    ↓
Rows -> dict
    ↓
table_name.json

No chunk generation happens here.
"""

import json
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

from postgres_connector import PostgresConnector
from grant_permissions import grant_permissions
from allowed_tables import ALLOWED_TABLES


EXPORT_DIR = Path("app/data/db_export")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


class JSONEncoder(json.JSONEncoder):
    """
    Handles PostgreSQL datatypes while exporting JSON.
    """

    def default(self, obj):

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, Decimal):
            return float(obj)

        return super().default(obj)


class DBReader:

    def __init__(self):
        self.connector = PostgresConnector()

    def export_table(self, table_name: str):

        print(f"\nReading table: {table_name}")

        with self.connector.get_cursor() as cursor:

            # Safe because table names come only from ALLOWED_TABLES
            cursor.execute(f"SELECT * FROM {table_name}")

            rows = cursor.fetchall()

            columns = [col.name for col in cursor.description]

            records = [
                dict(zip(columns, row))
                for row in rows
            ]

        output_file = EXPORT_DIR / f"{table_name}.json"

        with open(output_file, "w", encoding="utf-8") as fp:

            json.dump(
                records,
                fp,
                indent=4,
                ensure_ascii=False,
                cls=JSONEncoder,
            )

        print(f"Exported {len(records)} records")
        print(f"Saved -> {output_file}")

    def export_all_tables(self):

        for table in ALLOWED_TABLES:

            try:

                self.export_table(table)

            except Exception as e:

                print(f"Failed to export {table}")

                print(e)


def export_database():
    """
    Pipeline:

    1. Grant SELECT permissions on all allowed tables.
    2. Read tables using chatbot_reader.
    3. Export each table to JSON.
    """

    print("=" * 60)
    print("STEP 1: Granting database permissions...")
    print("=" * 60)

    grant_permissions()

    print("\n" + "=" * 60)
    print("STEP 2: Exporting database tables...")
    print("=" * 60)

    reader = DBReader()

    reader.export_all_tables()

    print("\n" + "=" * 60)
    print("Database export completed successfully.")
    print("=" * 60)


if __name__ == "__main__":

    export_database()