"""Local demo icin in-memory WebSocket baglanti yonetimi."""

from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from app.schemas.events import AnalysisUpdatedEvent


class ConnectionManager:
    def __init__(self) -> None:
        self._active_connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, session_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections.setdefault(session_id, []).append(websocket)

    def disconnect(self, session_id: UUID, websocket: WebSocket) -> None:
        connections = self._active_connections.get(session_id)
        if connections is None:
            return

        try:
            connections.remove(websocket)
        except ValueError:
            pass

        if not connections:
            self._active_connections.pop(session_id, None)

    async def broadcast_analysis(
        self,
        session_id: UUID,
        event: AnalysisUpdatedEvent,
    ) -> None:
        connections = list(self._active_connections.get(session_id, ()))
        event_payload = event.model_dump(mode="json")

        for websocket in connections:
            try:
                await websocket.send_json(event_payload)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(session_id, websocket)


connection_manager = ConnectionManager()
