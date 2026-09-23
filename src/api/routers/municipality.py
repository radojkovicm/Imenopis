"""GET /api/municipality/{slug} (PROJECT.md §12, §7.4).

Top 10 by cohort and gender, with a second column showing the same name's
national (Republic-level) rank for the same cohort - `not_in_top10` (§5.7,
never "absent") wherever §5.3 applies: a name outside the Republic top 10 is
`unknown` on the national side, not a number we don't have.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.envelope import ObservedValue, Scope, UnknownValue
from src.db.models import CensusRank, Cohort, GivenName, Municipality
from src.db.session import get_session
from src.ingest.seed_sources import CENSUS_T1_KEY, CENSUS_T2_KEY

router = APIRouter(prefix="/api/municipality", tags=["municipality"])

SOURCE_BY_GENDER = {"F": CENSUS_T1_KEY, "M": CENSUS_T2_KEY}


def _session() -> Session:
    return get_session()


@router.get("")
def list_municipalities(session: Session = Depends(_session)):
    """List all municipalities for the picker page (§8's 'Izaberi opštinu'
    entry point). Route declared before /{slug} so FastAPI's first-match
    routing doesn't send an empty path segment into the slug converter
    (same lesson as generation.py's /compare-before-/{year} ordering).
    """
    munis = session.query(Municipality).order_by(Municipality.name).all()
    return [{"name": m.name, "slug": m.name_slug} for m in munis]


def _municipality_top10(session: Session, municipality_id: int, cohort_id: int, gender: str) -> list[dict]:
    rows = (
        session.query(CensusRank, GivenName)
        .join(GivenName, CensusRank.given_name_id == GivenName.id)
        .filter(
            CensusRank.municipality_id == municipality_id,
            CensusRank.cohort_id == cohort_id,
            CensusRank.gender == gender,
        )
        .order_by(CensusRank.rank)
        .all()
    )
    return [{"rank": r.rank, "name": g.source_form, "given_name_id": g.id} for r, g in rows]


def _national_rank_for(session: Session, given_name_id: int, cohort_id: int, gender: str) -> int | None:
    """§5.3: national rank exists only for names inside the Republic top 10
    for that cohort. Looked up by given_name_id, not by name string, so a
    name that resolves to a different given_name row nationally (different
    source_key) is correctly treated as not found - PROJECT.md §6.2 never
    treats two given_name rows as interchangeable, so this shouldn't
    silently match across them either. In practice the Republic-level and
    municipality-level rows for one table share the same source_key
    (census_2022_t1 or t2), so this lookup only works within one table,
    which is the correct scope.
    """
    row = (
        session.query(CensusRank)
        .filter(
            CensusRank.municipality_id.is_(None),
            CensusRank.cohort_id == cohort_id,
            CensusRank.gender == gender,
            CensusRank.given_name_id == given_name_id,
        )
        .one_or_none()
    )
    return row.rank if row else None


@router.get("/{slug}")
def get_municipality(slug: str, gender: str | None = None, session: Session = Depends(_session)):
    muni = session.query(Municipality).filter_by(name_slug=slug).one_or_none()
    if muni is None:
        raise HTTPException(status_code=404, detail="municipality not found")

    cohorts = session.query(Cohort).order_by(Cohort.sort_order).all()
    genders = [gender] if gender else ["F", "M"]

    result = {
        "slug": slug,
        "name": muni.name,
        "cohorts": {},
    }
    for g in genders:
        source = SOURCE_BY_GENDER[g]
        by_cohort = []
        for cohort in cohorts:
            top10 = _municipality_top10(session, muni.id, cohort.id, g)
            entries = []
            for item in top10:
                national_rank = _national_rank_for(session, item["given_name_id"], cohort.id, g)
                entries.append(
                    {
                        "rank": item["rank"],
                        "name": item["name"],
                        "national": ObservedValue(
                            value=national_rank,
                            source=source,
                            scope=Scope(cohort=cohort.label, gender=g),
                        ).model_dump()
                        if national_rank is not None
                        else UnknownValue(reason="source_is_top10_only").model_dump(),
                    }
                )
            by_cohort.append(
                {
                    "cohort": cohort.label,
                    "year_from": cohort.year_from,
                    "year_to": cohort.year_to,
                    "top10": ObservedValue(
                        value=entries,
                        source=source,
                        scope=Scope(municipality=muni.name, cohort=cohort.label, gender=g),
                    ).model_dump(),
                }
            )
        key = "female" if g == "F" else "male"
        result["cohorts"][key] = by_cohort

    return result
