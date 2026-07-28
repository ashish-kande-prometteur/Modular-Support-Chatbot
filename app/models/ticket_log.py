import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.chatbot_db import Base


class TicketLog(Base):
    __tablename__ = "tickets_log"

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

    # Ticket id returned by provider (Zoho, Freshdesk, etc.)
    external_ticket_id = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    # zoho, freshdesk, zendesk...
    provider = Column(
        String(100),
        nullable=False,
    )

    # ai_escalation / manual / api
    trigger_type = Column(
        String(100),
        nullable=False,
        default="ai_escalation",
    )

    # User's last question
    user_query = Column(
        Text,
        nullable=False,
    )

    # AI response before escalation
    bot_answer = Column(
        Text,
        nullable=True,
    )

    # Request sent to provider
    provider_payload = Column(
        JSON,
        nullable=True,
    )

    # Response received from provider
    provider_response = Column(
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
        backref="ticket_logs",
    )

    def __repr__(self):
        return (
            f"<TicketLog("
            f"id={self.id}, "
            f"provider={self.provider}, "
            f"external_ticket_id={self.external_ticket_id}"
            f")>"
        )
    