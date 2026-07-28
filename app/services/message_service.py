from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_message import (
    ChatMessage,
    ContentType,
    SenderType,
)


class MessageService:
    def __init__(self, db: Session):
        self.db = db

    def save_message(
        self,
        session_id: UUID,
        sender_type: SenderType,
        message: str,
        content_type: ContentType = ContentType.TEXT,
        sender_id: Optional[UUID] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatMessage:
        """
        Generic message creation.
        Used by User, AI, Agent and System messages.
        """

        chat_message = ChatMessage(
            session_id=session_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content_type=content_type,
            message=message,
            attachments=attachments,
            sources=sources,
        )

        self.db.add(chat_message)
        self.db.commit()
        self.db.refresh(chat_message)

        return chat_message

    def save_user_message(
        self,
        session_id: UUID,
        message: str,
    ) -> ChatMessage:
        """
        Save a user message.
        """

        return self.save_message(
            session_id=session_id,
            sender_type=SenderType.USER,
            message=message,
        )

    def save_ai_message(
        self,
        session_id: UUID,
        message: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatMessage:
        """
        Save an AI response.
        """

        return self.save_message(
            session_id=session_id,
            sender_type=SenderType.AI,
            message=message,
            sources=sources,
        )

    def save_agent_message(
        self,
        session_id: UUID,
        sender_id: UUID,
        message: str,
    ) -> ChatMessage:
        """
        Save an agent message.
        """

        return self.save_message(
            session_id=session_id,
            sender_type=SenderType.AGENT,
            sender_id=sender_id,
            message=message,
        )

    def save_system_message(
        self,
        session_id: UUID,
        message: str,
    ) -> ChatMessage:
        """
        Save a system event.
        """

        return self.save_message(
            session_id=session_id,
            sender_type=SenderType.SYSTEM,
            content_type=ContentType.SYSTEM,
            message=message,
        )
    