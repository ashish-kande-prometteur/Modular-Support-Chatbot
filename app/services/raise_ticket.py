from datetime import datetime, timezone
from typing import Dict


from app.mongo_client import get_unanswered_queries_collection



def create_unanswered_query(payload: Dict) -> Dict:
    """
    Insert a record for a question the bot couldn't answer, so it can
    be reviewed/actioned later - this replaces raising a Zoho ticket.
    """

    collection = get_unanswered_queries_collection()

    document = {
        "user_query": payload["user_query"],
        "bot_answer": payload.get("bot_answer"),
        "trigger_type": payload.get("trigger_type", "UNKNOWN"),
        "confidence": payload.get("confidence", 0.0),
        "status": "OPEN",
        "created_at": datetime.now(timezone.utc)
    }

    result = collection.insert_one(document)

    document["id"] = str(result.inserted_id)
    document.pop("_id", None)

    return document