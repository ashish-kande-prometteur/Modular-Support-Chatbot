from fastapi import WebSocket, WebSocketDisconnect , HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import asyncio
from app.models.notification_model import NotificationType
from app.notifications.notification_manager import notification_manager
from app.repositories.agent_repository import AgentRepository
from app.repositories.notification_repository import NotificationRepository


class NotificationService:

    @staticmethod
    async def connect_agent(
        websocket: WebSocket,
        db: Session,
        agent_id: str,
    ):
        agent = AgentRepository.get_by_id(
            db=db,
            agent_id=agent_id,
        )

        if agent is None:
            await websocket.close(
                code=4004,
                reason="Agent not found.",
            )
            return

        if not agent.is_active:
            await websocket.close(
                code=4003,
                reason="Inactive agent.",
            )
            return

        await notification_manager.connect(
            agent_id=str(agent.id),
            websocket=websocket,
        )

        try:
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            notification_manager.disconnect(
                agent_id=str(agent.id),
            )

    # ---------------------------------------------------------
    # Notification Creation
    # ---------------------------------------------------------

    @staticmethod
    def create_support_notification(
        db: Session,
        session,
    ):
        notification = NotificationRepository.create(
            db=db,
            notification_type=NotificationType.NEW_SUPPORT_REQUEST,
            title="New Support Request",
            message="A customer requested human assistance.",
            session_id=session.id,
            external_user_id=session.external_user_id,
            metadata_json={
                "handoff_reason": session.handoff_reason,
            },
        )

        db.commit()
        db.refresh(notification)

        payload = {
            "event": "new_support_request",
            "notification_id": str(notification.id),
            "type": notification.type.value,
            "title": notification.title,
            "message": notification.message,
            "session_id": str(notification.session_id),
            "external_user_id": notification.external_user_id,
            "is_read": notification.is_read,
            "assigned_agent_id": (
                str(notification.assigned_agent_id)
                if notification.assigned_agent_id
                else None
            ),
            "created_at": notification.created_at.isoformat(),
            "metadata": notification.metadata_json,
        }

        NotificationService.broadcast_notification(payload)

        return notification

    # ---------------------------------------------------------
    # Push to Single Agent
    # ---------------------------------------------------------

    @staticmethod
    def push_notification(
        agent_id: str,
        payload: dict,
    ) -> bool:

        return notification_manager.send(
            agent_id=agent_id,
            payload=payload,
        )

    # ---------------------------------------------------------
    # Broadcast
    # ---------------------------------------------------------

    @staticmethod
    def broadcast_new_support_request(notification):

        payload = {
            "event": "new_support_request",
            "notification_id": str(notification.id),
            "session_id": str(notification.session_id),
            "title": notification.title,
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
            "external_user_id": notification.external_user_id,
        }

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                notification_manager.broadcast(payload)
            )
        except RuntimeError:
            pass

    def get_unread_notifications(db):

        notifications = NotificationRepository.get_unread_notifications(db)

        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "session_id": n.session_id,
                "external_user_id": n.external_user_id,
                "created_at": n.created_at,
                "metadata": n.metadata_json
            }
            for n in notifications
        ]


    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: UUID
    ):

        notification = NotificationRepository.get_by_id(
            db=db,
            notification_id=notification_id
        )

        if not notification:
            raise HTTPException(
                status_code=404,
                detail="Notification not found."
            )

        if notification.is_read:
            return {
                "success": True,
                "message": "Notification already marked as read."
            }

        NotificationRepository.mark_as_read(
            db=db,
            notification=notification
        )

        return {
            "success": True,
            "message": "Notification marked as read.",
            "notification": {
                "id": str(notification.id),
                "is_read": notification.is_read,
                "read_at": notification.read_at
            }
        }
