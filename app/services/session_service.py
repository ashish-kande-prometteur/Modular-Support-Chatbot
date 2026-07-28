from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession


class SessionService:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------
    # Create Session
    # ---------------------------------------------------------

    def create_session(
        self,
        external_user_id: str,
        widget_source: str = "website",
        metadata_json=None,
    ):

        session = ChatSession(
            external_user_id=external_user_id,
            widget_source=widget_source,
            metadata_json=metadata_json,
            status="AI_HANDLING",
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    # ---------------------------------------------------------
    # Get Session By ID
    # ---------------------------------------------------------

    def get_session(self, session_id: UUID):

        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

    # ---------------------------------------------------------
    # Get Active Session
    # ---------------------------------------------------------

    def get_active_session(
        self,
        external_user_id: str,
    ):

        return (
            self.db.query(ChatSession)
            .filter(
                ChatSession.external_user_id == external_user_id,
                ChatSession.status == "AI_HANDLING",
            )
            .order_by(ChatSession.created_at.desc())
            .first()
        )

    # ---------------------------------------------------------
    # Close Session
    # ---------------------------------------------------------

    def close_session(self, session_id: UUID):

        session = self.get_session(session_id)

        if session:

            session.status = "CLOSED"

            self.db.commit()

            self.db.refresh(session)

        return session

    # ---------------------------------------------------------
    # Get Or Create Session
    # ---------------------------------------------------------

    def get_or_create_session(
        self,
        session_id,
        external_user_id,
        widget_source="website",
        metadata_json=None,
    ):

        # -----------------------------------------------------
        # Case 1
        # Frontend already has session_id
        # -----------------------------------------------------

        if session_id:

            session = self.get_session(session_id)

            if session:
                return session

        # -----------------------------------------------------
        # Case 2
        # Find active session of same user
        # -----------------------------------------------------

        session = self.get_active_session(external_user_id)

        if session:
            return session

        # -----------------------------------------------------
        # Case 3
        # Create new session
        # -----------------------------------------------------

        return self.create_session(
            external_user_id=external_user_id,
            widget_source=widget_source,
            metadata_json=metadata_json,
        )
    