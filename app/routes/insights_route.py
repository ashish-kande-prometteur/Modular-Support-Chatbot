from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.chatbot_db import get_db
from app.services.insights_service import InsightsController


router = APIRouter(
    prefix="/insights",
    tags=["Insights"],
)


@router.get("/conversation-analytics")
def get_conversation_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    try:
        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be after end_date.",
            )

        return InsightsController.get_conversation_analytics(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )