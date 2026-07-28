from datetime import datetime

from sqlalchemy.orm import Session

from app.models.chat_session import (
    ChatSession,
    SessionStatus,
)
from app.notifications.notification_service import NotificationService

class ChatSessionRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        session_id,
    ):
        return (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

    @staticmethod
    def mark_for_handoff(
        db: Session,
        session: ChatSession,
        reason: str,
    ) -> ChatSession:

        session.status = SessionStatus.ESCALATED_PENDING
        session.handoff_reason = reason
        session.handoff_requested_at = datetime.utcnow()

        return session
    