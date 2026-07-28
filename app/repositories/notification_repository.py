from sqlalchemy.orm import Session
from app.models.notification_model import Notification

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