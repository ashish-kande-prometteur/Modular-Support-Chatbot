import uuid
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
    func,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.chatbot_db import Base


class ResolutionType(str, Enum):
    AI_RESOLVED = "ai_resolved"
    HUMAN_RESOLVED = "human_resolved"
    ABANDONED = "abandoned"


class SessionStatus(str, Enum):
    AI_HANDLING = "ai_handling"
    ESCALATED_PENDING = "escalated_pending"
    HUMAN_ACTIVE = "human_active"
    CLOSED = "closed"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # External user id from website/widget
    external_user_id = Column(
        String(255),
        nullable=False,
        index=True,
    )

    # Current session status
    status = Column(
        SqlEnum(
            SessionStatus,
            name="session_status",
        ),
        nullable=False,
        default=SessionStatus.AI_HANDLING,
        index=True,
    )

    # Support agent handling this session
    assigned_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True,
        index=True,
    )

    # When AI requested human support
    handoff_requested_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # When support agent joined
    agent_joined_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_confirmed_resolved = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    user_confirmed_resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_abandoned_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolution_type = Column(
        SqlEnum(
            ResolutionType,
            name="resolution_type",
        ),
        nullable=True,
        index=True,
    )

    # When conversation was completed
    closed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Why AI escalated
    handoff_reason = Column(
        String(255),
        nullable=True,
    )

    # Widget / Website identifier
    widget_source = Column(
        String(255),
        nullable=True,
    )

    # Additional metadata
    metadata_json = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    # ------------------------------------
    # Customer feedback after session ends
    # ------------------------------------

    helpful = Column(
        Boolean,
        nullable=True,
    )

    feedback_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
    notifications = relationship(
    "Notification",
    back_populates="session",
    cascade="all, delete-orphan",
    )
    agent = relationship(
        "Agent",
        back_populates="sessions",
    )

    def __repr__(self):
        return (
            f"<ChatSession("
            f"id={self.id}, "
            f"status={self.status}, "
            f"user={self.external_user_id}, "
            f"assigned_agent={self.assigned_agent_id}"
            f")>"
        )
