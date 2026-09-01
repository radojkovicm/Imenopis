"""FastAPI entrypoint. Run: uvicorn src.api.main:app --reload --port 8000"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routers import cohort, generation, historical, municipality, name, newborn, suggest
from src.config import settings
from src.db.session import init_db

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.SITE_NAME, lifespan=lifespan)


@app.get("/api/healthz")
def healthz():
    return {"status": "ok", "site": settings.SITE_NAME}


app.include_router(generation.router)
app.include_router(newborn.router)
app.include_router(suggest.router)
app.include_router(municipality.router)
app.include_router(cohort.router)
app.include_router(historical.router)
app.include_router(name.router)

# Static site (§6.2: vanilla JS, no build step). Mounted after the /api
# routes so API paths always take priority.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
