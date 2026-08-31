"""FastAPI entrypoint. Run: uvicorn src.api.main:app --reload --port 8000"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routers import generation, name, newborn, suggest
from src.config import settings
from src.db.session import init_db

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

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

# Static site (§6.2: vanilla JS, no build step). Mounted after the /api
# routes so API paths always take priority.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
