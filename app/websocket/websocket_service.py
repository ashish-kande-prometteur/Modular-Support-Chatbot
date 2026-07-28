from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.repositories.support_repository import SupportRepository
from app.models.chat_session import SessionStatus
from app.websocket.connection_manager import manager


class WebSocketService:

    @staticmethod
    async def handle_connection(
        websocket: WebSocket,
        db: Session,
        session_id: str,
        participant: str,
        external_user_id: str | None,
        agent_id: str | None,
    ):

        # ----------------------------------------
        # Get Session
        # ----------------------------------------

        session = SupportRepository.get_session(
            db=db,
            session_id=session_id,
        )

        if session is None:
            await websocket.close(
                code=4004,
                reason="Session not found.",
            )
            return

        # ----------------------------------------
        # Session must be HUMAN_ACTIVE
        # ----------------------------------------

        if session.status != SessionStatus.HUMAN_ACTIVE:
            await websocket.close(
                code=4001,
                reason="Support session is not active.",
            )
            return

        # ----------------------------------------
        # Validate User
        # ----------------------------------------

        if participant == "user":

            if external_user_id is None:
                await websocket.close(
                    code=4002,
                    reason="external_user_id is required.",
                )
                return

            if str(session.external_user_id) != external_user_id:
                await websocket.close(
                    code=4003,
                    reason="Unauthorized user.",
                )
                return

        # ----------------------------------------
        # Validate Agent
        # ----------------------------------------

        elif participant == "agent":

            if agent_id is None:
                await websocket.close(
                    code=4002,
                    reason="agent_id is required.",
                )
                return

            if str(session.assigned_agent_id) != agent_id:
                await websocket.close(
                    code=4003,
                    reason="Unauthorized agent.",
                )
                return

        else:

            await websocket.close(
                code=4005,
                reason="Invalid participant.",
            )
            return

        # ----------------------------------------
        # Register Connection
        # ----------------------------------------

        await manager.connect(
            session_id=str(session.id),
            participant_type=participant,
            websocket=websocket,
        )

        # ----------------------------------------
        # Keep Connection Alive
        # ----------------------------------------

        try:

            while True:

                data = await websocket.receive_json()

                print(data)

                if participant == "user":

                    await manager.send_to_agent(
                        session_id=str(session.id),
                        message=data,
                    )

                else:

                    await manager.send_to_user(
                        session_id=str(session.id),
                        message=data,
                    )

        except WebSocketDisconnect:

            manager.disconnect(
                session_id=str(session.id),
                participant_type=participant,
            )

            print(
                f"{participant} disconnected from session {session.id}"
            )
