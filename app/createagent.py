import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session

from app.database.chatbot_db import SessionLocal
from app.models.agent import Agent, AgentStatus
from app.security.password import hash_password


def create_agents():
    db: Session = SessionLocal()

    try:
        agents = [
            {
                "name": "Rohit Kendre",
                "email": "rohit.kendre@example.com",
            },
            {
                "name": "Akshay Patil",
                "email": "akshay.patil@example.com",
            },
            {
                "name": "Priya Sharma",
                "email": "priya.sharma@example.com",
            },
        ]

        for data in agents:

            existing = (
                db.query(Agent)
                .filter(Agent.email == data["email"])
                .first()
            )

            if existing:
                print(f"Agent already exists: {data['email']}")
                continue

            agent = Agent(
                name=data["name"],
                email=data["email"],
                password_hash=hash_password("Pass@123"),
                status=AgentStatus.AVAILABLE,
                is_active=True,
                open_session_count=0,
            )

            db.add(agent)

        db.commit()

        print("\n✅ Agents created successfully.\n")
        print("Login Credentials:")
        print("-------------------------------------")
        print("Email: rohit.kendre@example.com")
        print("Password: Pass@123")
        print("-------------------------------------")
        print("Email: akshay.patil@example.com")
        print("Password: Pass@123")
        print("-------------------------------------")
        print("Email: priya.sharma@example.com")
        print("Password: Pass@123")
        print("-------------------------------------")

    except Exception as e:
        db.rollback()
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    create_agents()