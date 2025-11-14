from fastapi import FastAPI
from services.common.config.base_settings import resolve_env

app = FastAPI(title="{{APP_NAME}}")


@app.get("/health/live")
def health_live() -> dict:
return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> dict:
return {"status": "ready"}
