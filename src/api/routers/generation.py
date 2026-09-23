"""GET /api/generation/{year}, GET /api/generation/compare (PROJECT.md §12, §7.3).

Pure Table 3 lookups - Republic-level, single birth year, ranks I-V only (not
I-X - see docs/DATA_NOTES.md §6a). No map (T3 has no geography, §7.6).

Route order matters: /compare must be declared before /{year}, or FastAPI's
first-match routing sends "compare" into the {year}:int path converter and
fails with a parse error.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.envelope import DerivedValue, ObservedValue, Scope, UnknownValue
from src.db.models import CensusRankByYear, GivenName
from src.db.session import get_session
from src.ingest.seed_sources import CENSUS_T3_KEY

router = APIRouter(prefix="/api/generation", tags=["generation"])

MIN_YEAR = 1941  # Table 3's earliest single birth year (1940 and earlier is a
# separate open-ended bucket not stored in this table - see load_all.py)
MAX_YEAR = 2022


def _session() -> Session:
    return get_session()


def _top_names(session: Session, year: int, gender: str) -> list[dict]:
    rows = (
        session.query(CensusRankByYear, GivenName)
        .join(GivenName, CensusRankByYear.given_name_id == GivenName.id)
        .filter(CensusRankByYear.birth_year == year, CensusRankByYear.gender == gender)
        .order_by(CensusRankByYear.rank)
        .all()
    )
    return [{"rank": r.rank, "name": g.source_form} for r, g in rows]


@router.get("/compare")
def compare_generations(a: int, b: int, session: Session = Depends(_session)):
    """Entered / left / present in both, per gender (§7.3)."""
    response = {"a": a, "b": b}
    for gender, key in (("F", "female"), ("M", "male")):
        names_a = {row["name"] for row in _top_names(session, a, gender)}
        names_b = {row["name"] for row in _top_names(session, b, gender)}
        response[key] = DerivedValue(
            value={
                "entered": sorted(names_b - names_a),
                "left": sorted(names_a - names_b),
                "present_in_both": sorted(names_a & names_b),
            },
            derived_from=[CENSUS_T3_KEY],
            note=f"set_comparison_top5_only_{a}_vs_{b}",
        ).model_dump()
    return response


@router.get("/across-decades")
def across_decades(year: int, session: Session = Depends(_session)):
    """§7.3's second follow-on: 'Kako bi te zvali da si rođen ranije' - the
    #1 name of `year` across several earlier decades. Pure T3 lookup, one
    row per decade back to MIN_YEAR, each independently `observed` or
    `unknown` (a decade with no #1 - shouldn't happen inside MIN_YEAR..
    MAX_YEAR, but T3 rows can theoretically be sparse - is never silently
    skipped or padded).
    """
    if year < MIN_YEAR or year > MAX_YEAR:
        return {
            "year": year,
            "female": UnknownValue(reason="scope_not_published").model_dump(),
            "male": UnknownValue(reason="scope_not_published").model_dump(),
        }

    years = []
    y = year
    while y >= MIN_YEAR:
        years.append(y)
        y -= 10

    response = {"year": year, "years": years}
    for gender, key in (("F", "female"), ("M", "male")):
        entries = []
        for y in years:
            top = _top_names(session, y, gender)
            first = next((row for row in top if row["rank"] == 1), None)
            entries.append(
                {
                    "year": y,
                    "name": ObservedValue(
                        value=first["name"], source=CENSUS_T3_KEY, scope=Scope(birth_year=y, gender=gender)
                    ).model_dump()
                    if first
                    else UnknownValue(reason="scope_not_published").model_dump(),
                }
            )
        response[key] = entries
    return response


@router.get("/{year}")
def get_generation(year: int, session: Session = Depends(_session)):
    if year < MIN_YEAR or year > MAX_YEAR:
        return {
            "year": year,
            "female": UnknownValue(reason="scope_not_published").model_dump(),
            "male": UnknownValue(reason="scope_not_published").model_dump(),
        }

    female = _top_names(session, year, "F")
    male = _top_names(session, year, "M")

    return {
        "year": year,
        "female": ObservedValue(
            value=female, source=CENSUS_T3_KEY, scope=Scope(birth_year=year, gender="F")
        ).model_dump(),
        "male": ObservedValue(
            value=male, source=CENSUS_T3_KEY, scope=Scope(birth_year=year, gender="M")
        ).model_dump(),
    }
