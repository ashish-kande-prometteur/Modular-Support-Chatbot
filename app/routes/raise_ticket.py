from fastapi import APIRouter, HTTPException

from app.schema.raise_ticket import (
    UnansweredQueryCreate,
    UnansweredQueryResponse
)
from app.services.raise_ticket import create_unanswered_query
router = APIRouter(
    prefix="/api/unanswered-queries",
    tags=["Unanswered Queries"]
)


@router.post(
    "",
    response_model=UnansweredQueryResponse,
    status_code=201
)
def create_unanswered_query_record(
    payload: UnansweredQueryCreate
):
    """
    Called by the chatbot service whenever a user query couldn't be
    answered from the vector store or the database. Stores the query
    in MongoDB for later follow-up (replaces the old Zoho ticket flow).
    """

    try:
        document = create_unanswered_query(
            payload.model_dump()
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store unanswered query: {exc}"
        ) from exc

    return document
