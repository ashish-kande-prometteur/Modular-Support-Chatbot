from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.chatbot_db import get_db
from app.services.support_service import (
    SupportService,
)
from app.schemas.support import JoinSessionRequest , CloseSessionRequest, SessionUserRequest
from uuid import UUID
from app.services.session_service import SessionService



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


@router.post("/session/{session_id}/confirm-resolution")
def confirm_resolution(
    session_id: UUID,
    payload: SessionUserRequest,
    db: Session = Depends(get_db),
):
    try:
        session = SessionService(db).confirm_resolution(
            session_id=session_id,
            external_user_id=payload.external_user_id,
        )

        return {
            "success": True,
            "session_id": str(session.id),
            "status": session.status.value,
            "resolution_type": (
                session.resolution_type.value
                if session.resolution_type
                else None
            ),
            "user_confirmed_resolved": (
                session.user_confirmed_resolved
            ),
            "user_confirmed_resolved_at": (
                session.user_confirmed_resolved_at
            ),
            "closed_at": session.closed_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/session/{session_id}/abandon")
def abandon_session(
    session_id: UUID,
    payload: SessionUserRequest,
    db: Session = Depends(get_db),
):
    try:
        session = SessionService(db).mark_abandoned(
            session_id=session_id,
            external_user_id=payload.external_user_id,
        )

        return {
            "success": True,
            "session_id": str(session.id),
            "status": session.status.value,
            "resolution_type": (
                session.resolution_type.value
                if session.resolution_type
                else None
            ),
            "user_abandoned_at": session.user_abandoned_at,
            "closed_at": session.closed_at,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )