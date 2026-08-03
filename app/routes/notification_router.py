from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.chatbot_db import get_db
from app.notifications.notification_service import NotificationService

router = APIRouter(
    prefix="/ws",
    tags=["Support Notification"],
)


@router.websocket("/support")
async def support_notifications(
    websocket: WebSocket,
    agent_id: str,
    db: Session = Depends(get_db),
):
    await NotificationService.connect_agent(
        websocket=websocket,
        db=db,
        agent_id=agent_id,
    )

@router.get("/support/notifications/unread")
async def unread_notifications(
    db: Session = Depends(get_db)
):
    return NotificationService.get_unread_notifications(db)

@router.patch("/support/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db)
):
    return NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id
    )
