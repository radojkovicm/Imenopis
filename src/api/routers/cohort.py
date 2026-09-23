"""GET /api/cohort/{cohort_id} (PROJECT.md §12).

National top 10 for that cohort, and municipalities that deviate from it.
"Deviate" is defined narrowly and observably (§5.1 bars every derived score):
a municipality whose #1 name for this cohort/gender differs from the
national #1. This is a direct observed-vs-observed comparison, not a
computed distance or similarity score - the forbidden kind under §5.1.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.envelope import DerivedValue, ObservedValue, Scope, UnknownValue
from src.db.models import CensusRank, Cohort, GivenName, Municipality
from src.db.session import get_session
from src.ingest.seed_sources import CENSUS_T1_KEY, CENSUS_T2_KEY

router = APIRouter(prefix="/api/cohort", tags=["cohort"])

SOURCE_BY_GENDER = {"F": CENSUS_T1_KEY, "M": CENSUS_T2_KEY}


def _session() -> Session:
    return get_session()


def _top10(session: Session, municipality_id: int | None, cohort_id: int, gender: str) -> list[dict]:
    rows = (
        session.query(CensusRank, GivenName)
        .join(GivenName, CensusRank.given_name_id == GivenName.id)
        .filter(
            CensusRank.municipality_id == municipality_id if municipality_id is not None else CensusRank.municipality_id.is_(None),
            CensusRank.cohort_id == cohort_id,
            CensusRank.gender == gender,
        )
        .order_by(CensusRank.rank)
        .all()
    )
    return [{"rank": r.rank, "name": g.source_form} for r, g in rows]


@router.get("/{cohort_id}")
def get_cohort(cohort_id: int, gender: str | None = None, session: Session = Depends(_session)):
    cohort = session.get(Cohort, cohort_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail="cohort not found")

    genders = [gender] if gender else ["F", "M"]
    result = {
        "cohort_id": cohort_id,
        "cohort": cohort.label,
        "year_from": cohort.year_from,
        "year_to": cohort.year_to,
    }

    for g in genders:
        source = SOURCE_BY_GENDER[g]
        national_top10 = _top10(session, None, cohort_id, g)
        key = "female" if g == "F" else "male"
        result[key] = {
            "national_top10": ObservedValue(
                value=national_top10, source=source, scope=Scope(cohort=cohort.label, gender=g)
            ).model_dump()
            if national_top10
            else UnknownValue(reason="scope_not_published").model_dump(),
        }

        if not national_top10:
            result[key]["deviating_municipalities"] = UnknownValue(reason="scope_not_published").model_dump()
            continue

        national_first = national_top10[0]["name"]
        munis = session.query(Municipality).order_by(Municipality.name).all()
        deviating = []
        for muni in munis:
            local_top10 = _top10(session, muni.id, cohort_id, g)
            if not local_top10:
                continue
            if local_top10[0]["name"] != national_first:
                deviating.append({"municipality": muni.name, "slug": muni.name_slug, "local_first": local_top10[0]["name"]})

        result[key]["deviating_municipalities"] = DerivedValue(
            value=deviating,
            derived_from=[source],
            note="municipalities_whose_rank1_differs_from_national_rank1",
        ).model_dump()

    return result
