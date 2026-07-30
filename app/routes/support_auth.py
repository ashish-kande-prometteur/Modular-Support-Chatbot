from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.chatbot_db import get_db
from app.schemas.support_auth import AgentLoginRequest
from app.services.support_auth_service import SupportAuthService

router = APIRouter(
    prefix="/api/support/auth",
    tags=["Support Authentication"],
)


@router.post("/login")
def login(
    request: AgentLoginRequest,
    db: Session = Depends(get_db),
):

    return SupportAuthService.login(
        db=db,
        email=request.email,
        password=request.password,
    )
