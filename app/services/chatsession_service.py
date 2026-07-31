from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.repositories.chat_session_repository import ChatSessionRepository

class ChatSessionService:

    @staticmethod
    async def save_feedback(
        db: Session,
        session_id: UUID,
        helpful: bool,
    ):

        session = ChatSessionRepository.get_by_id(
            db,
            session_id,
        )

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found",
            )

        if session.helpful is not None:
            raise HTTPException(
                status_code=400,
                detail="Feedback already submitted",
            )

        return await ChatSessionRepository.save_feedback(
            db,
            session,
            helpful,
        )
