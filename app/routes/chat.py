from fastapi import APIRouter , Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..database.chatbot_db import get_db
from app.services.chat_service import (
    get_ai_response
)
from app.services.context_resolver import resolve_query
from app.services.session_service import (
    SessionService
)
from app.services.message_service import MessageService
from app.services.conversation_service import ConversationService
from app.models.chat_session import SessionStatus
from app.websocket.connection_manager import manager
from app.services.greeting_service import get_greeting_response


import time
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
    user_message = message_service.save_user_message(
        session_id=session.id,
        message=request.question,
    )
    print(user_message.id)
    print(user_message.created_at)

    # ----------------------------------------
    # Greeting Handling
    # ----------------------------------------

    greeting = get_greeting_response(request.question)

    if greeting:

        message_service.save_ai_message(
            session_id=session.id,
            message=greeting,
        )

        return {
            "success": True,
            "session_id": str(session.id),
            "answer": greeting,
            "confidence": 1.0,
            "show_feedback": False,
        }

    # -----------------------------------------
    # Resolve follow-up context before AI search
    # The raw question is already saved to DB above.
    # resolved_query is what gets sent to the vector
    # search / RAG pipeline.
    # -----------------------------------------
    resolved_query = resolve_query(
        db=db,
        session_id=session.id,
        user_query=request.question,
    )

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
    start_time = time.perf_counter()
    answer = get_ai_response(
        db=db,
        session_id=session.id,
        user_query=resolved_query
    )
    response_time_ms = int(
    (time.perf_counter() - start_time) * 1000
    )
 
    print("response_time_ms", response_time_ms) 
    message_service.save_ai_message(
        session_id=session.id,
        message=answer["answer"],
        response_time_ms=response_time_ms,
        reply_to_message_id=user_message.id,
    )

    return {
        "success": True,
        "session_id": str(session.id),
        **answer,
    }
