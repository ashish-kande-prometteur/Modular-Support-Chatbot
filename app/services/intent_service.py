import re
from typing import Dict, Optional


class IntentService:
    """
    Detects whether the user query should use:
    - Database
    - RAG
    """

    TABLE_KEYWORDS = {
        "casino_providers": [
            "provider",
            "providers",
            "casino provider",
            "casino providers"
        ],

        "countries": [
            "country",
            "countries",
            "country code",
            "supported countries"
        ],

        "casino_categories": [
            "category",
            "categories",
            "casino category",
            "casino categories"
        ],

        "bonus": [
            "bonus",
            "bonuses",
            "promotion",
            "welcome bonus"
        ]
    }

    COUNT_KEYWORDS = [
        "how many",
        "count",
        "total",
        "number of"
    ]

    LIST_KEYWORDS = [
        "list",
        "show",
        "show all",
        "display",
        "all",
        "available",
        "available providers",
        "available countries",
        "names of"
    ]

    SEARCH_KEYWORDS = [
        "find",
        "search",
        "tell me about",
        "details",
        "information about"
    ]

    def detect_table(self, question: str) -> Optional[str]:

        question = question.lower()

        for table, keywords in self.TABLE_KEYWORDS.items():

            for keyword in keywords:

                if keyword in question:
                    return table

        return None

    def detect_intent(self, question: str) -> Dict:

        q = question.lower().strip()

        table = self.detect_table(q)

        if table is None:
            return {
                "type": "rag"
            }

        # ----------------------------
        # COUNT
        # ----------------------------

        if any(
            keyword in q
            for keyword in self.COUNT_KEYWORDS
        ):
            return {
                "type": "count",
                "table": table
            }

        # ----------------------------
        # LIST
        # ----------------------------

        if any(
            keyword in q
            for keyword in self.LIST_KEYWORDS
        ):
            return {
                "type": "list",
                "table": table
            }

        # ----------------------------
        # SEARCH
        # ----------------------------

        if any(
            keyword in q
            for keyword in self.SEARCH_KEYWORDS
        ):

            search_value = q

            for keyword in self.SEARCH_KEYWORDS:
                search_value = search_value.replace(
                    keyword,
                    ""
                )

            for keyword in self.TABLE_KEYWORDS[table]:
                search_value = search_value.replace(
                    keyword,
                    ""
                )

            search_value = re.sub(
                r"\s+",
                " ",
                search_value
            ).strip()

            return {
                "type": "search",
                "table": table,
                "value": search_value
            }

        # ----------------------------
        # DEFAULT
        # ----------------------------

        return {
            "type": "rag"
        }


intent_service = IntentService()
