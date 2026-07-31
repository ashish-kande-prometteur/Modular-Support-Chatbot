from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.chatbot_db import get_db
from app.schemas.support_auth import SessionFeedbackRequest , SuccessResponse
from app.services.chatsession_service import ChatSessionService

router = APIRouter(
    prefix="/api/chat",
    tags=["Feedback"],
)

@router.post(
    "/session/{session_id}/feedback",
    response_model=SuccessResponse,
)
async def submit_feedback(
    session_id: UUID,
    request: SessionFeedbackRequest,
    db: Session = Depends(get_db),
):

    await ChatSessionService.save_feedback(
        db=db,
        session_id=session_id,
        helpful=request.helpful,
    )

    return {
        "success": True,
    }
