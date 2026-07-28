import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# ==========================================================
# Chatbot Database (Read / Write)
# ==========================================================

CHATBOT_DB_HOST = os.getenv("CHATBOT_DB_HOST", "localhost")
CHATBOT_DB_PORT = os.getenv("CHATBOT_DB_PORT", "5432")
CHATBOT_DB_NAME = os.getenv("CHATBOT_DB_NAME")
CHATBOT_DB_USER = os.getenv("CHATBOT_DB_USER")
CHATBOT_DB_PASSWORD = os.getenv("CHATBOT_DB_PASSWORD")

CHATBOT_DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{CHATBOT_DB_USER}:{CHATBOT_DB_PASSWORD}"
    f"@{CHATBOT_DB_HOST}:{CHATBOT_DB_PORT}/{CHATBOT_DB_NAME}"
)

chatbot_engine = create_engine(
    CHATBOT_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)

SessionLocal = sessionmaker(
    bind=chatbot_engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================================
# Business Database (Read Only)
# ==========================================================

RAG_ADMIN_DB_HOST = os.getenv("RAG_ADMIN_DB_HOST", "localhost")
RAG_ADMIN_DB_PORT = os.getenv("RAG_ADMIN_DB_PORT", "5432")
RAG_ADMIN_DB_NAME = os.getenv("RAG_ADMIN_DB_NAME")
RAG_ADMIN_DB_USER = os.getenv("RAG_ADMIN_DB_USER")
RAG_ADMIN_DB_PASSWORD = os.getenv("RAG_ADMIN_DB_PASSWORD")

RAG_DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{RAG_ADMIN_DB_USER}:{RAG_ADMIN_DB_PASSWORD}"
    f"@{RAG_ADMIN_DB_HOST}:{RAG_ADMIN_DB_PORT}/{RAG_ADMIN_DB_NAME}"
)

rag_engine = create_engine(
    RAG_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)

RAGSessionLocal = sessionmaker(
    bind=rag_engine,
    autocommit=False,
    autoflush=False,
)


def get_rag_db():
    db = RAGSessionLocal()
    try:
        yield db
    finally:
        db.close()
        