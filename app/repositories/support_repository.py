from datetime import datetime, timezone

from app.models.chat_session import ChatSession, SessionStatus


class SupportRepository:

    @staticmethod
    def claim_session(
        db,
        session_id,
        agent_id,
    ):

        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

        if session is None:
            raise Exception("Session not found.")

        if session.status == SessionStatus.CLOSED:
            raise Exception("Session is already closed.")

        if (
            session.assigned_agent_id
            and session.assigned_agent_id != agent_id
        ):
            raise Exception(
                "This session has already been claimed by another support agent."
            )

        if session.status == SessionStatus.HUMAN_ACTIVE:
            return session

        session.assigned_agent_id = agent_id
        session.status = SessionStatus.HUMAN_ACTIVE
        session.agent_joined_at = datetime.now(timezone.utc)

        return session


    @staticmethod
    def get_session(
        db,
        session_id,
    ):
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

        if session is None:
            raise Exception("Session not found.")

        return session

    @staticmethod
    def close_session(
        session,
    ):
        session.status = SessionStatus.CLOSED
        session.closed_at = datetime.now(timezone.utc)
