from fastapi import FastAPI


app = FastAPI(title="PersonaLive API", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "personalive-api",
        "version": "0.1.0",
    }
