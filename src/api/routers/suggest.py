"""GET /api/suggest (PROJECT.md §12). Prefix match on search_key, limit 10."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.db.models import GivenName
from src.db.session import get_session
from src.util.normalize import make_search_key

router = APIRouter(prefix="/api/suggest", tags=["suggest"])


def _session() -> Session:
    return get_session()


@router.get("")
def suggest(q: str = Query(min_length=1), session: Session = Depends(_session)):
    prefix = make_search_key(q)
    rows = (
        session.query(GivenName.search_key, GivenName.source_form, GivenName.gender)
        .filter(GivenName.search_key.like(f"{prefix}%"))
        .distinct()
        .limit(10)
        .all()
    )
    return [
        {"search_key": search_key, "display": source_form, "gender": gender}
        for search_key, source_form, gender in rows
    ]
