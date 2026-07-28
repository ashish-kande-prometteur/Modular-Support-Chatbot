import uuid
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.chatbot_db import Base


class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class Agent(Base):
    __tablename__ = "agents"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Display name
    name = Column(
        String(255),
        nullable=False,
    )

    # Login / notification email
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Current availability
    status = Column(
        SqlEnum(
            AgentStatus,
            name="agent_status",
        ),
        nullable=False,
        default=AgentStatus.OFFLINE,
        index=True,
    )

    # Whether the account is enabled
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Session currently being handled
    current_session_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Number of open support sessions
    open_session_count = Column(
        Integer,
        nullable=False,
        default=0,
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

    # Relationships
    sessions = relationship(
        "ChatSession",
        back_populates="agent",
    )

    def __repr__(self):
        return (
            f"<Agent("
            f"id={self.id}, "
            f"name={self.name}, "
            f"status={self.status}"
            f")>"
        )
    