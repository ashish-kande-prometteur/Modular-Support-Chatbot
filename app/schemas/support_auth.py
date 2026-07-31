from pydantic import BaseModel, EmailStr


class AgentLoginRequest(BaseModel):
    email: EmailStr
    password: str

class SessionFeedbackRequest(BaseModel):
    helpful: bool

class SuccessResponse(BaseModel):
    success: bool

