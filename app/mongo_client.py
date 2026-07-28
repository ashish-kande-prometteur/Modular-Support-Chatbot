import os

from pymongo import MongoClient
from pymongo.collection import Collection

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "chatbot_db"
)

UNANSWERED_QUERIES_COLLECTION = os.getenv(
    "UNANSWERED_QUERIES_COLLECTION",
    "unanswered_queries"
)

_mongo_client = MongoClient(MONGO_URI)
mongo_db = _mongo_client[MONGO_DB_NAME]


def get_unanswered_queries_collection() -> Collection:
    return mongo_db[UNANSWERED_QUERIES_COLLECTION]
