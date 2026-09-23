"""GET /api/newborn/{year} (PROJECT.md §12, Feature 7).

Republic-level by default; district breakdown available via ?district=<slug>
since Phase 0 found the source carries that granularity (docs/DATA_NOTES.md
§2, newborn_name.district_id addition - see src/db/models.py docstring).
BRANCH A resolved rank-only (docs/DATA_NOTES.md §3): count is always null.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.envelope import ObservedValue, Scope, UnknownValue
from src.db.models import District, GivenName, NewbornName
from src.db.session import get_session
from src.ingest.seed_sources import NEWBORN_KEYS

router = APIRouter(prefix="/api/newborn", tags=["newborn"])


def _session() -> Session:
    return get_session()


@router.get("/{year}")
def get_newborn(
    year: int,
    gender: str | None = Query(default=None, pattern="^[MF]$"),
    district: str | None = Query(default=None, description="district code, e.g. 'juznobacka'"),
    session: Session = Depends(_session),
):
    if year not in NEWBORN_KEYS:
        return UnknownValue(reason="scope_not_published").model_dump()

    source_key = NEWBORN_KEYS[year]
    district_id = None
    district_name = None
    if district:
        d = session.query(District).filter_by(code=district).one_or_none()
        if d is None:
            return UnknownValue(reason="scope_not_published").model_dump()
        district_id = d.id
        district_name = d.name

    genders = [gender] if gender else ["F", "M"]
    result = {"year": year, "district": district}
    for g in genders:
        rows = (
            session.query(NewbornName, GivenName)
            .join(GivenName, NewbornName.given_name_id == GivenName.id)
            .filter(
                NewbornName.year == year,
                NewbornName.gender == g,
                NewbornName.district_id == district_id,
            )
            .order_by(NewbornName.rank)
            .all()
        )
        key = "female" if g == "F" else "male"
        result[key] = ObservedValue(
            value=[{"rank": r.rank, "name": gn.source_form} for r, gn in rows],
            source=source_key,
            scope=Scope(birth_year=year, gender=g, district=district_name),
        ).model_dump()
    return result
