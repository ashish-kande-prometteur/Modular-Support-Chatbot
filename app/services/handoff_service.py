from sqlalchemy.orm import Session
from app.repositories.notification_repository import NotificationRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.models.notification_model import NotificationType
from app.notifications.notification_service import NotificationService


class HandoffService:

    @staticmethod
    def request_handoff(
        db: Session,
        session_id,
        reason: str,
    ):

        session = ChatSessionRepository.get_by_id(
            db=db,
            session_id=session_id,
        )

        if session is None:
            raise Exception("Session not found")

        ChatSessionRepository.mark_for_handoff(
            db=db,
            session=session,
            reason=reason,
        )

        db.commit()
        db.refresh(session)

        notification = NotificationRepository.create(
            db=db,
            notification_type=NotificationType.NEW_SUPPORT_REQUEST,
            title="New Support Request",
            message="Customer requested human assistance.",
            session_id=session.id,
            external_user_id=session.external_user_id,
            metadata_json={
                "handoff_reason": reason,
            },
        )

        db.commit()
        db.refresh(notification)

        NotificationService.broadcast_new_support_request(
            notification=notification,
            db=db,
        )

        return {
            "session_id": str(session.id),
            "support_url": f"/support/{session.id}",
        }
