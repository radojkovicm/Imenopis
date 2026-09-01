from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.db.models import Base

# Imported for its side effect of registering the §16 historical-layer
# tables on Base.metadata before create_all() runs below - nothing in this
# module references it directly.
from src.db import historical_models  # noqa: F401

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()
