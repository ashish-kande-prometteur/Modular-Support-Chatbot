from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.agent_repository import AgentRepository
from app.security.jwt import create_access_token
from app.security.password import verify_password


class SupportAuthService:

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ):

        agent = AgentRepository.get_by_email(
            db=db,
            email=email,
        )

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent account is inactive.",
            )

        if not verify_password(
            password,
            agent.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        access_token = create_access_token(agent)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "agent": {
                "id": str(agent.id),
                "name": agent.name,
                "is_active": agent.is_active,
            },
        }
