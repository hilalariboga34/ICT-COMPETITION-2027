from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.manager import connection_manager


router = APIRouter()


@router.websocket("/api/v1/ws/sessions/{session_id}")
async def analysis_websocket(websocket: WebSocket, session_id: UUID) -> None:
    await connection_manager.connect(session_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(session_id, websocket)
