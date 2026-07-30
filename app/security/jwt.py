from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 480


def create_access_token(
    agent,
):

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(agent.id),
        "email": agent.email,
        "role": "SUPPORT_AGENT",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
