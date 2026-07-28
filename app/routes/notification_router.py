from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.orm import Session

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
