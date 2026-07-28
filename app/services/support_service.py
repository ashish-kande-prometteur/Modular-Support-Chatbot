from app.repositories.support_repository import (
    SupportRepository,
)
from app.models.chat_session import SessionStatus
from app.repositories.agent_repository import AgentRepository
from app.services.message_service import MessageService

class SupportService:

    @staticmethod
    def join_session(
        db,
        session_id,
        agent_id,
    ):

        # --------------------------
        # Validate Agent
        # --------------------------
        agent = AgentRepository.get_by_id(
            db=db,
            agent_id=agent_id,
        )

        if agent is None:
            raise Exception("Support agent not found.")

        # --------------------------
        # Claim Chat Session
        # --------------------------
        session = SupportRepository.claim_session(
            db=db,
            session_id=session_id,
            agent_id=agent.id,
        )

        # --------------------------
        # Update Agent Status
        # --------------------------
        AgentRepository.mark_busy(
            agent=agent,
            session_id=session.id,
        )

        # --------------------------
        # Commit Everything
        # --------------------------
        db.commit()

        db.refresh(session)
        db.refresh(agent)

        return {
            "message": "Session joined successfully.",
            "session_id": str(session.id),
            "status": session.status.value,
            "assigned_agent_id": str(session.assigned_agent_id),
            "agent_status": agent.status.value,
            "current_session_id": str(agent.current_session_id),
            "open_session_count": agent.open_session_count,
        }

    @staticmethod
    def get_session_details(
        db,
        session_id,
    ):

        session = SupportRepository.get_session(
            db=db,
            session_id=session_id,
        )

        return {
            "session": {
                "id": str(session.id),
                "status": session.status.value,
                "external_user_id": session.external_user_id,
                "handoff_reason": session.handoff_reason,
                "created_at": session.created_at,
                "handoff_requested_at": session.handoff_requested_at,
                "assigned_agent_id": (
                    str(session.assigned_agent_id)
                    if session.assigned_agent_id
                    else None
                ),
            },
            "conversation": [
                {
                    "id": str(message.id),
                    "sender_type": message.sender_type.value,
                    "sender_id": (
                        str(message.sender_id)
                        if message.sender_id
                        else None
                    ),
                    "content_type": message.content_type.value,
                    "message": message.message,
                    "attachments": message.attachments,
                    "sources": message.sources,
                    "created_at": message.created_at,
                }
                for message in session.messages
            ],
        }

    @staticmethod
    def close_session(
        db,
        session_id,
        agent_id,
        resolution_note=None,
    ):
        # -----------------------------------
        # Get Session
        # -----------------------------------
        session = SupportRepository.get_session(
            db=db,
            session_id=session_id,
        )

        if session is None:
            raise Exception("Session not found.")

        # -----------------------------------
        # Session must be active
        # -----------------------------------
        if session.status != SessionStatus.HUMAN_ACTIVE:
            raise Exception(
                "Only active support sessions can be closed."
            )

        # -----------------------------------
        # Validate assigned agent
        # -----------------------------------
        if session.assigned_agent_id != agent_id:
            raise Exception(
                "Only the assigned support agent can close this session."
            )

        # -----------------------------------
        # Load Agent
        # -----------------------------------
        agent = AgentRepository.get_by_id(
            db=db,
            agent_id=agent_id,
        )

        if agent is None:
            raise Exception(
                "Support agent not found."
            )

        # -----------------------------------
        # Close Session
        # -----------------------------------
        SupportRepository.close_session(
            session=session,
        )

        # -----------------------------------
        # Mark Agent Available
        # -----------------------------------
        AgentRepository.mark_available(
            agent=agent,
        )

        # -----------------------------------
        # Save System Message
        # -----------------------------------
        message = "Support session closed."

        if resolution_note:
            message += f"\nResolution: {resolution_note}"

        MessageService(db).save_system_message(
            session_id=session.id,
            message=message,
        )

        # -----------------------------------
        # Commit
        # -----------------------------------
        db.commit()

        db.refresh(session)
        db.refresh(agent)

        return {
            "message": "Support session closed successfully.",
            "session_id": str(session.id),
            "status": session.status.value,
            "closed_at": session.closed_at,
            "agent_status": agent.status.value,
        }
