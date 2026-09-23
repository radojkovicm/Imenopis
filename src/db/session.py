import os
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import BASE_DIR, settings
from src.db.models import Base

# Imported for its side effect of registering the §16 historical-layer
# tables on Base.metadata before create_all() runs below - nothing in this
# module references it directly.
from src.db import historical_models  # noqa: F401

_DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR / 'imena.db'}"


def _resolve_database_url(url: str) -> str:
    """On Vercel the deployment bundle is a read-only filesystem, so the
    shipped sqlite file can't be opened read-write there (init_db()'s
    CREATE TABLE IF NOT EXISTS still needs a writable handle even though the
    schema already exists). Vercel sets VERCEL=1 at runtime; copy the bundled
    db into /tmp (the one writable path) once per cold start and use that
    copy instead. No-op for local dev and for a non-sqlite DATABASE_URL.

    This site has no external database to provision - it only ever needs
    the bundled sqlite file - so a DATABASE_URL env var that's unset,
    empty, or not a well-formed URL (e.g. a stray/blank value some
    deployment platform injected) falls back to that bundled file rather
    than crashing create_engine() with a parse error.
    """
    if not url or "://" not in url:
        url = _DEFAULT_SQLITE_URL
    if not url.startswith("sqlite:///") or not os.environ.get("VERCEL"):
        return url
    src_path = url.removeprefix("sqlite:///")
    tmp_path = "/tmp/imena.db"
    if not os.path.exists(tmp_path):
        shutil.copyfile(src_path, tmp_path)
    return f"sqlite:///{tmp_path}"


database_url = _resolve_database_url(settings.DATABASE_URL)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()
