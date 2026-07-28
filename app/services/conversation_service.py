from typing import List

from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_message import SenderType


class ConversationService:

    def __init__(self, db: Session):
        self.db = db

    def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[ChatMessage]:
        """
        Fetch last N messages for a session.
        Returns them in chronological order.
        """

        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )

        # Reverse because we fetched DESC
        messages.reverse()

        return messages

    def format_for_llm(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        Convert DB messages into OpenAI-compatible chat format.
        """

        history = self.get_recent_messages(
            session_id=session_id,
            limit=limit,
        )

        conversation = []

        for message in history:
            print(
                f"sender_type={message.sender_type}, "
                f"message={message.message}"
            )

            role = (
                "assistant"
                if message.sender_type == SenderType.AI
                else "user"
            )

            conversation.append(
                {
                    "role": role,
                    "content": message.message,
                }
            )

        return conversation


conversation_service = ConversationService
