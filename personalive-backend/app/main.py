from fastapi import FastAPI

from app.api.routes.analysis import router as analysis_router
from app.api.routes.websocket import router as websocket_router


app = FastAPI(title="PersonaLive API", version="0.1.0")
app.include_router(analysis_router)
app.include_router(websocket_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "personalive-api",
        "version": "0.1.0",
    }
