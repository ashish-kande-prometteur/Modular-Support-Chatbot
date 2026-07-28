from datetime import datetime

from sqlalchemy.orm import Session

from app.models.chat_session import (
    ChatSession,
    SessionStatus,
)


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
    ):

        session.status = SessionStatus.ESCALATED_PENDING
        session.handoff_requested_at = datetime.utcnow()
        session.handoff_reason = reason

        db.commit()
        db.refresh(session)

        return session
    