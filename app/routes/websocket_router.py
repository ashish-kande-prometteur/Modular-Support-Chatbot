from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session

from ..database.chatbot_db import get_db
from app.websocket.websocket_service import WebSocketService

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)


@router.websocket("/chat/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    participant: str,
    external_user_id: str | None = None,
    agent_id: str | None = None,
    db: Session = Depends(get_db),
):

    await WebSocketService.handle_connection(
        websocket=websocket,
        db=db,
        session_id=session_id,
        participant=participant,
        external_user_id=external_user_id,
        agent_id=agent_id,
    )
