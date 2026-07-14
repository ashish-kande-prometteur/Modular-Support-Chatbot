from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import (
    get_ai_response
)

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
async def chat(
    request: ChatRequest
):
    answer = get_ai_response(
        request.question
    )

    return {
        "question": request.question,
        "answer": answer
    }