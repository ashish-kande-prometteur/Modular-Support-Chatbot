from pydantic import BaseModel
from uuid import UUID


class JoinSessionRequest(BaseModel):
    agent_id: UUID

class CloseSessionRequest(BaseModel):
    agent_id: UUID
    resolution_note: str | None = None