from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UnansweredQueryCreate(BaseModel):
    """
    Payload sent by the chatbot service whenever it could not
    confidently answer a user's question, either from the vector
    store or the structured database.
    """

    user_query: str = Field(
        ...,
        min_length=1,
        description="The original question asked by the user"
    )

    bot_answer: Optional[str] = Field(
        default=None,
        description="Whatever partial/fallback answer (if any) was shown to the user"
    )

    trigger_type: str = Field(
        ...,
        description="Why this record was created, e.g. NO_VECTOR_RESULTS, "
                    "LOW_CONTEXT_RELEVANCE, NO_DATABASE_MATCH"
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score at the time of fallback, if any"
    )


class UnansweredQueryResponse(BaseModel):
    id: str
    user_query: str
    bot_answer: Optional[str] = None
    trigger_type: str
    confidence: float
    status: str
    created_at: datetime