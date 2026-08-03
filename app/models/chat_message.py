from enum import Enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    JSON,
    Text,
    func,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.chatbot_db import Base


class SenderType(str, Enum):
    USER = "user"
    AI = "ai"
    AGENT = "agent"
    SYSTEM = "system"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_type = Column(
        SqlEnum(SenderType, name="sender_type"),
        nullable=False,
        index=True,
    )

    # User ID / Agent ID
    # AI and SYSTEM messages will keep this NULL.
    sender_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    content_type = Column(
        SqlEnum(ContentType, name="content_type"),
        nullable=False,
        default=ContentType.TEXT,
    )

    message = Column(
        Text,
        nullable=False,
    )

    # Image / File attachments
    attachments = Column(
        JSON,
        nullable=True,
    )

    # Sources used by the AI response
    # Example:
    # [
    #   {"type":"faq","id":"faq_10"},
    #   {"type":"ticket","id":"ticket_201"}
    # ]
    sources = Column(
        JSON,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )

    response_time_ms = Column(
        Integer,
        nullable=True,
    ) 

    reply_to_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id"),
        nullable=True,
    )

    def __repr__(self):
        return (
            f"<ChatMessage("
            f"id={self.id}, "
            f"sender={self.sender_type}, "
            f"session={self.session_id}"
            f")>"
        )
    