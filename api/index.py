"""Vercel entrypoint: re-exports the FastAPI app for @vercel/python's ASGI detection."""

from src.api.main import app  # noqa: F401
