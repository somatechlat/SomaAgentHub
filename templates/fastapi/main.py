from fastapi import FastAPI

app = FastAPI(title="Template FastAPI Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Replace this template with service logic."}
