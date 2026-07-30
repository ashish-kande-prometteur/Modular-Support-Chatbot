from app.models.agent import Agent, AgentStatus
from sqlalchemy.orm import Session

class AgentRepository:

    @staticmethod
    def get_by_id(
        db,
        agent_id,
    ):
        return (
            db.query(Agent)
            .filter(
                Agent.id == agent_id,
                Agent.is_active == True,
            )
            .first()
        )

    @staticmethod
    def mark_busy(
        agent,
        session_id,
    ):
        agent.status = AgentStatus.BUSY
        agent.current_session_id = session_id
        agent.open_session_count += 1

    @staticmethod
    def mark_available(
        agent,
    ):
        agent.status = AgentStatus.AVAILABLE
        agent.current_session_id = None

        if agent.open_session_count > 0:
            agent.open_session_count -= 1

    @staticmethod
    def get_available_agents(db):
        """
        Returns all available support agents.
        """
        return (
            db.query(Agent)
            .filter(
                Agent.is_active == True,
                Agent.status == AgentStatus.AVAILABLE,
            )
            .order_by(Agent.open_session_count.asc())
            .all()
        )

    @staticmethod
    def get_by_email(
        db: Session,
        email: str,
    ):
        return (
            db.query(Agent)
            .filter(Agent.email == email)
            .first()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        agent_id: str,
    ):
        return (
            db.query(Agent)
            .filter(Agent.id == agent_id)
            .first()
        )
