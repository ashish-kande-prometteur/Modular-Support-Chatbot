from sqlalchemy.orm import Session
from app.models.notification_model import Notification
from datetime import datetime , timezone
from uuid import UUID
class NotificationRepository:

    @staticmethod
    def create(
        db: Session,
        notification_type,
        title,
        message,
        session_id,
        external_user_id,
        metadata_json=None,
    ):

        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            session_id=session_id,
            external_user_id=external_user_id,
            metadata_json=metadata_json or {},
        )

        db.add(notification)

        return notification

    @staticmethod
    def get_unread_notifications(db: Session):

        return (
            db.query(Notification)
            .filter(Notification.is_read == False)
            .order_by(Notification.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(
        db: Session,
        notification_id: UUID
    ):

        return (
            db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    @staticmethod
    def mark_as_read(
        db: Session,
        notification: Notification
    ):

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notification)

        return notification
