from pydantic import BaseModel, EmailStr


class AgentLoginRequest(BaseModel):
    email: EmailStr
    password: str