from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        """
        Structure:

        {
            session_id: {
                "user": WebSocket,
                "agent": WebSocket,
            }
        }
        """
        self.active_connections = defaultdict(dict)

    async def connect(
        self,
        session_id: str,
        participant_type: str,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.active_connections[session_id][
            participant_type
        ] = websocket

        print(
            f"{participant_type} connected "
            f"to session {session_id}"
        )

    def disconnect(
        self,
        session_id: str,
        participant_type: str,
    ):

        if session_id not in self.active_connections:
            return

        self.active_connections[
            session_id
        ].pop(participant_type, None)

        if not self.active_connections[session_id]:
            del self.active_connections[session_id]

        print(
            f"{participant_type} disconnected "
            f"from session {session_id}"
        )

    async def send_to_user(
        self,
        session_id: str,
        message: dict,
    ):

        websocket = self.active_connections.get(
            session_id,
            {},
        ).get("user")

        print("User websocket:", websocket)
        
        if websocket:
            await websocket.send_json(message)

    async def send_to_agent(
        self,
        session_id: str,
        message: dict,
    ):

        websocket = self.active_connections.get(
            session_id,
            {},
        ).get("agent")

        print("Agent websocket:", websocket)

        if websocket:
            await websocket.send_json(message)

    async def broadcast(
        self,
        session_id: str,
        message: dict,
    ):

        participants = self.active_connections.get(
            session_id,
            {}
        )

        for websocket in participants.values():
            await websocket.send_json(message)


manager = ConnectionManager()
