from fastapi import APIRouter , Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..database.chatbot_db import get_db
from app.services.chat_service import (
    get_ai_response
)
from app.services.session_service import (
    SessionService
)
from app.services.message_service import MessageService
from app.services.conversation_service import ConversationService
from app.models.chat_session import SessionStatus
from app.websocket.connection_manager import manager

router = APIRouter()


class ChatRequest(BaseModel):
    chatbot_id: str
    question: str

    session_id: Optional[UUID] = None
    external_user_id: str
    widget_source: Optional[str] = "website"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    # Session Service
    session_service = SessionService(db)

    session = session_service.get_or_create_session(
        session_id=request.session_id,
        external_user_id=request.external_user_id,
        widget_source=request.widget_source,
    )

    # Message Service
    message_service = MessageService(db)

    # Store user message
    message_service.save_user_message(
        session_id=session.id,
        message=request.question,
    )

    # -----------------------------
    # TEST Conversation Memory
    # -----------------------------
    # conversation_service = ConversationService(db)

    # history = conversation_service.format_for_llm(
    #     session_id=session.id,
    #     limit=10
    # )

    # print("\n========== Conversation History ==========")
    # for msg in history:
    #     print(msg)
    # print("==========================================\n")

    # Existing AI pipeline
    if session.status == SessionStatus.HUMAN_ACTIVE:

        await manager.send_to_agent(
            session_id=str(session.id),
            message={
                "type": "message",
                "sender": "user",
                "text": request.question,
            },
        )

        return {
            "success": True,
            "session_id": str(session.id),
            "live_chat": True,
        }


    # --------------------------------------------------------
    # Continue AI pipeline
    # --------------------------------------------------------

    answer = get_ai_response(
        db=db,
        session_id=session.id,
        user_query=request.question,
    )

    message_service.save_ai_message(
        session_id=session.id,
        message=answer["answer"],
    )

    return {
        "success": True,
        "session_id": str(session.id),
        **answer,
    }
