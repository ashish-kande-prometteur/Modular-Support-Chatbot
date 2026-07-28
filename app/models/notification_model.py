import uuid
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.chatbot_db import Base


class NotificationType(str, Enum):
    NEW_SUPPORT_REQUEST = "NEW_SUPPORT_REQUEST"
    SUPPORT_REQUEST_CLAIMED = "SUPPORT_REQUEST_CLAIMED"
    SUPPORT_REQUEST_CANCELLED = "SUPPORT_REQUEST_CANCELLED"
    SUPPORT_SESSION_CLOSED = "SUPPORT_SESSION_CLOSED"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    type = Column(
        SQLEnum(NotificationType, name="notification_type"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    external_user_id = Column(
        String(255),
        nullable=True,
        index=True,
    )

    # Agent who finally accepted the support request
    assigned_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Whether the notification has been handled
    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    metadata_json = Column(
        JSON,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ----------------------------------------
    # Relationships
    # ----------------------------------------

    session = relationship(
        "ChatSession",
        back_populates="notifications",
    )

    assigned_agent = relationship(
        "Agent",
        back_populates="notifications",
    )

    def __repr__(self):
        return (
            f"<Notification("
            f"id={self.id}, "
            f"type={self.type}, "
            f"session_id={self.session_id}, "
            f"assigned_agent_id={self.assigned_agent_id}, "
            f"is_read={self.is_read})>"
        )
