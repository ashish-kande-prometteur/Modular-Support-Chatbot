from app.core.config import settings
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.agent_repository import AgentRepository

class HandoffService:

    @staticmethod
    def request_handoff(
        db,
        session_id,
        reason,
    ):

        session = ChatSessionRepository.get_by_id(
            db,
            session_id,
        )

        if not session:
            raise Exception("Session not found.")

        session = ChatSessionRepository.mark_for_handoff(
            db=db,
            session=session,
            reason=reason,
        )

        available_agents = (
            AgentRepository.get_available_agents(db)
        )

        support_url = (
            f"{settings.SUPPORT_PORTAL_URL}"
            f"/support/session/{session.id}"
        )

        return {
            "session_id": str(session.id),
            "support_url": support_url,
            "status": session.status.value,
            "available_agents": len(available_agents),
        }
    