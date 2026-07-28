from fastapi import WebSocket


class NotificationManager:
    """
    Manages active support agent websocket connections.

    Structure:
    {
        "agent_id": WebSocket
    }
    """

    def __init__(self):
        self.active_agents: dict[str, WebSocket] = {}

    async def connect(
        self,
        agent_id: str,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.active_agents[agent_id] = websocket

        print(
            f"[Notification] Agent connected : {agent_id}"
        )

    def disconnect(
        self,
        agent_id: str,
    ):
        self.active_agents.pop(agent_id, None)

        print(
            f"[Notification] Agent disconnected : {agent_id}"
        )

    async def send(
        self,
        agent_id: str,
        payload: dict,
    ):
        websocket = self.active_agents.get(agent_id)

        if websocket is None:
            return False

        try:

            await websocket.send_json(payload)

            return True

        except Exception:

            self.disconnect(agent_id)

            return False

    async def broadcast(
        self,
        payload: dict,
    ):
        disconnected = []

        for agent_id, websocket in self.active_agents.items():

            try:

                await websocket.send_json(payload)

            except Exception:

                disconnected.append(agent_id)

        for agent_id in disconnected:
            self.disconnect(agent_id)


notification_manager = NotificationManager()
