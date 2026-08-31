"""FastAPI entrypoint. Run: uvicorn src.api.main:app --reload --port 8000"""

from fastapi import FastAPI

from src.api.routers import generation, name, newborn, suggest
from src.config import settings
from src.db.session import init_db

app = FastAPI(title=settings.SITE_NAME)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/healthz")
def healthz():
    return {"status": "ok", "site": settings.SITE_NAME}


app.include_router(generation.router)
app.include_router(newborn.router)
app.include_router(suggest.router)
app.include_router(name.router)
