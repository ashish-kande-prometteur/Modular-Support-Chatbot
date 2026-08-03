from typing import Dict, List, Optional

from sqlalchemy import text

from app.database.chatbot_db import RAGSessionLocal


class DatabaseService:

    """
    Read-only database service used by the chatbot.
    Only supports SELECT queries on whitelisted tables.
    """

    TABLES: Dict[str, Dict] = {
        "casino_providers": {
            "columns": ["name"],
            "display": "Casino Providers"
        },
        "casino_categories": {
            "columns": ["name"],
            "display": "Casino Categories"
        },
        "countries": {
            "columns": ["name", "code"],
            "display": "Countries"
        },
        "states": {
            "columns": ["name", "code"],
            "display": "States"
        },
        "languages": {
            "columns": ["name", "code"],
            "display": "Languages"
        },
        "currencies": {
            "columns": ["name", "code"],
            "display": "Currencies"
        },
        "bonus": {
            "columns": [
                "promotion_title",
                "bonus_percent",
                "bonus_type",
                "currency_code",
                "min_deposit",
                "description",
                "terms_and_conditions"
            ],
            "display": "Bonuses"
        }
    }

    def table_exists(self, table: str) -> bool:
        return table in self.TABLES

    def get_display_name(self, table: str) -> str:
        return self.TABLES[table]["display"]

    def count(self, table: str) -> Optional[Dict]:

        if not self.table_exists(table):
            return None

        db = RAGSessionLocal()

        try:

            result = db.execute(
                text(
                    f"""
                    SELECT COUNT(*)
                    FROM {table}
                    """
                )
            ).scalar()

            return {
                "type": "count",
                "table": table,
                "display": self.get_display_name(table),
                "count": result
            }

        finally:
            db.close()

    def list(
        self,
        table: str,
        limit: int = 1000,
        active_only: bool = False
    ) -> Optional[Dict]:

        if not self.table_exists(table):
            return None

        column = self.TABLES[table]["columns"][0]

        query = f"""
            SELECT {column}
            FROM {table}
        """

        if active_only:
            query += " WHERE is_active = TRUE"

        query += f"""
            ORDER BY {column}
            LIMIT :limit
        """

        db = RAGSessionLocal()

        try:

            rows = db.execute(
                text(query),
                {"limit": limit}
            ).fetchall()

            return {
                "type": "list",
                "table": table,
                "display": self.get_display_name(table),
                "rows": [
                    row[0]
                    for row in rows
                    if row[0]
                ]
            }

        finally:
            db.close()

    def search(
        self,
        table: str,
        keyword: str
    ) -> Optional[Dict]:

        if not self.table_exists(table):
            return None

        columns = self.TABLES[table]["columns"]

        conditions = [
            f"LOWER(CAST({col} AS TEXT)) LIKE LOWER(:keyword)"
            for col in columns
        ]

        where_clause = " OR ".join(conditions)

        db = RAGSessionLocal()

        try:

            rows = db.execute(
                text(
                    f"""
                    SELECT *
                    FROM {table}
                    WHERE {where_clause}
                    LIMIT 20
                    """
                ),
                {
                    "keyword": f"%{keyword}%"
                }
            ).mappings().all()

            return {
                "type": "search",
                "table": table,
                "display": self.get_display_name(table),
                "rows": [dict(row) for row in rows]
            }

        finally:
            db.close()

    def get_by_name(
        self,
        table: str,
        value: str
    ) -> Optional[Dict]:

        if not self.table_exists(table):
            return None

        column = self.TABLES[table]["columns"][0]

        db = RAGSessionLocal()

        try:

            row = db.execute(
                text(
                    f"""
                    SELECT *
                    FROM {table}
                    WHERE LOWER({column})
                    = LOWER(:value)
                    LIMIT 1
                    """
                ),
                {
                    "value": value
                }
            ).mappings().first()

            if not row:
                return None

            return {
                "type": "record",
                "table": table,
                "display": self.get_display_name(table),
                "record": dict(row)
            }

        finally:
            db.close()
