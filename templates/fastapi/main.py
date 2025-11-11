from fastapi import FastAPI
from services.common.config.base_settings import resolve_env

app = FastAPI(title="Template FastAPI Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Replace this template with service logic."}
