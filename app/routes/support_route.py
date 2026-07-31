from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.chatbot_db import get_db
from app.services.support_service import (
    SupportService,
)
from app.schemas.support import JoinSessionRequest , CloseSessionRequest

router = APIRouter(
    prefix="/support",
    tags=["Support"],
)


@router.get("/session/{session_id}")
def get_support_session(
    session_id: str,
    db: Session = Depends(get_db),
):

    try:

        return SupportService.get_session_details(
            db=db,
            session_id=session_id,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@router.post("/session/{session_id}/join")
def join_session(
    session_id: str,
    payload: JoinSessionRequest,
    db: Session = Depends(get_db),
):

    try:

        return SupportService.join_session(
            db=db,
            session_id=session_id,
            agent_id=payload.agent_id,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post("/session/{session_id}/close")
async def close_session(
    session_id: str,
    payload: CloseSessionRequest,
    db: Session = Depends(get_db),
):
    """
    Close an active support session.

    Flow:
        1. Validate session
        2. Validate assigned agent
        3. Close session
        4. Mark agent available
        5. Save system message
    """

    try:
        return await SupportService.close_session(
            db=db,
            session_id=session_id,
            agent_id=payload.agent_id,
            resolution_note=payload.resolution_note,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
