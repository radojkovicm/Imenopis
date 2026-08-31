"""GET /api/name/{search_key} (PROJECT.md §12, §7.1, §7.2).

search_key is not unique (§6.1) for two different reasons, and this endpoint
must not conflate them:

1. **Genuinely different spellings** sharing a search_key (the actual §7.2
   split-name case, e.g. Đorđe/Djordje, or Mihajlo/Mihailo folding together
   - though in practice those two don't share a search_key, see
   docs/DATA_NOTES.md §5). These get separate display blocks and the
   split_notice.
2. **The same spelling appearing in several source tables** - one given_name
   row per year (source_key = newborn_2021..newborn_2025) plus one for
   census_2022_t3, all with an identical source_form. This is NOT a spelling
   split; it's the natural consequence of source_key identifying "the
   specific table or edition" (§6.1). Presenting these as separate cards
   would misrepresent a data-modeling artifact as a linguistic finding.

So: group given_name rows by (source_form, gender) for display. Each group
becomes one block whose per-row observations (timeline entries, newborn
appearances, municipality data) are merged and still individually
source-attributed; the block itself is never treated as a merged
statistical unit for anything beyond that (§6.2 still applies - across
DIFFERENT source_forms, nothing is summed).

§7.1 "Gde" (municipality count, highest rank, map) reads census_rank
(Table 1/2, Step 3 of §10) by (source_form, gender) - census_rank's
given_name rows use their own source_key (census_2022_t1/t2), a disjoint
given_name_id space from T3/newborn's, so they can't be picked up via the
T3/newborn given_name_id list already collected above; they're looked up
separately by the same (source_form, gender) key the whole block is
grouped by.

No 404 for an unobserved name (§12): a name with no rows is a legitimate
`evidence: unknown` answer, not an error.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.envelope import DerivedValue, ObservedValue, Scope, UnknownValue
from src.db.models import CensusRank, CensusRankByYear, Cohort, District, GivenName, Municipality, NewbornName
from src.db.session import get_session
from src.ingest.seed_sources import CENSUS_T1_KEY, CENSUS_T2_KEY

router = APIRouter(prefix="/api/name", tags=["name"])

SOURCE_BY_GENDER = {"F": CENSUS_T1_KEY, "M": CENSUS_T2_KEY}


def _session() -> Session:
    return get_session()


def _timeline_by_year(session: Session, given_name_id: int) -> list[dict]:
    rows = (
        session.query(CensusRankByYear)
        .filter(CensusRankByYear.given_name_id == given_name_id)
        .order_by(CensusRankByYear.birth_year)
        .all()
    )
    return [{"birth_year": r.birth_year, "rank": r.rank} for r in rows]


def _newborn_appearances(session: Session, given_name_id: int) -> list[dict]:
    """Every year/district row this given_name appears in - Republic-level
    (district=None) and district-level both, since a given_name_id from a
    single year's XLSX (§6.1: source_key is year-specific) may only ever
    appear in district rows and never make the Republic top 10 for that year
    (see docs/DATA_NOTES.md §2 - 'Михајло' in 2021 is exactly this case).
    Dropping district-only rows would silently under-report what's observed.
    """
    rows = (
        session.query(NewbornName, District)
        .outerjoin(District, NewbornName.district_id == District.id)
        .filter(NewbornName.given_name_id == given_name_id)
        .order_by(NewbornName.year, District.name)
        .all()
    )
    # Each row's source is year-specific ('newborn_2021' .. 'newborn_2025'),
    # so the source is attached per-item, not hoisted to the ObservedValue
    # envelope wrapping the whole list (§4.3 - the envelope names ONE source;
    # a multi-year list spans several, so each item names its own).
    return [
        {
            "year": r.year,
            "rank": r.rank,
            "district": d.name if d else None,
            "source": f"newborn_{r.year}",
        }
        for r, d in rows
    ]


def _municipality_data(session: Session, source_form: str, gender: str) -> dict:
    """§7.1 'Gde': municipality count, highest rank achieved and where.
    Looked up by (source_form, gender) directly against census_rank's own
    given_name rows (source_key = census_2022_t1/t2) - see module docstring.
    Excludes the Republic-level row (municipality_id IS NULL) from the
    per-municipality list and count, since that's the national side, not a
    place (§7.4's national comparison is served by /api/municipality, not
    duplicated here).
    """
    source = SOURCE_BY_GENDER[gender]
    rows = (
        session.query(CensusRank, Municipality, Cohort)
        .join(GivenName, CensusRank.given_name_id == GivenName.id)
        .join(Municipality, CensusRank.municipality_id == Municipality.id)
        .join(Cohort, CensusRank.cohort_id == Cohort.id)
        .filter(
            GivenName.source_form == source_form,
            GivenName.gender == gender,
            GivenName.source_key == source,
            CensusRank.municipality_id.is_not(None),
        )
        .all()
    )
    if not rows:
        return {
            "municipality_count": UnknownValue(reason="source_is_top10_only").model_dump(),
            "best_rank": UnknownValue(reason="source_is_top10_only").model_dump(),
            "appearances": UnknownValue(reason="source_is_top10_only").model_dump(),
        }

    distinct_municipalities = {m.id for _, m, _ in rows}
    best = min(rows, key=lambda t: t[0].rank)
    best_rank_row, best_muni, best_cohort = best

    appearances = [
        {
            "municipality": m.name,
            "slug": m.name_slug,
            "cohort": c.label,
            "rank": r.rank,
        }
        for r, m, c in sorted(rows, key=lambda t: (t[1].name, t[2].sort_order))
    ]

    return {
        "municipality_count": DerivedValue(
            value=len(distinct_municipalities),
            derived_from=[source],
            note="count_of_distinct_municipalities_where_in_top10",
        ).model_dump(),
        "best_rank": ObservedValue(
            value={"rank": best_rank_row.rank, "municipality": best_muni.name, "cohort": best_cohort.label},
            source=source,
            scope=Scope(gender=gender),
        ).model_dump(),
        "appearances": ObservedValue(
            value=appearances,
            source=source,
            scope=Scope(gender=gender),
        ).model_dump(),
    }


@router.get("/{search_key}")
def get_name(search_key: str, gender: str | None = None, session: Session = Depends(_session)):
    key = search_key.strip().lower()
    query = session.query(GivenName).filter(GivenName.search_key == key)
    if gender:
        query = query.filter(GivenName.gender == gender)
    matches = query.all()

    if not matches:
        return {
            "search_key": key,
            "matches": [],
            "result": UnknownValue(reason="source_is_top10_only").model_dump(),
        }

    # Group by (source_form, gender): see module docstring for why this is
    # not the same thing as grouping by given_name_id.
    groups: dict[tuple[str, str], list[GivenName]] = {}
    for gn in matches:
        groups.setdefault((gn.source_form, gn.gender), []).append(gn)

    blocks = []
    for (source_form, gender_val), gn_rows in groups.items():
        national_by_year: list[dict] = []
        newborn: list[dict] = []
        source_keys = []
        for gn in gn_rows:
            source_keys.append(gn.source_key)
            national_by_year.extend(_timeline_by_year(session, gn.id))
            newborn.extend(_newborn_appearances(session, gn.id))
        national_by_year.sort(key=lambda r: r["birth_year"])
        newborn.sort(key=lambda r: (r["year"], r["district"] or ""))

        block = {
            "source_form": source_form,
            "source_keys": sorted(source_keys),
            "gender": gender_val,
            "national_timeline_by_year": ObservedValue(
                value=national_by_year,
                source="census_2022_t3",
                scope=Scope(gender=gender_val),
            ).model_dump()
            if national_by_year
            else UnknownValue(reason="source_is_top5_only").model_dump(),
            "newborn_timeline": ObservedValue(
                value=newborn,
                source="newborn_2021..2025",  # each item also carries its own year-specific source
                scope=Scope(gender=gender_val),
            ).model_dump()
            if newborn
            else UnknownValue(reason="scope_not_published").model_dump(),
        }
        block.update(_municipality_data(session, source_form, gender_val))
        blocks.append(block)

    # §7.2: surface the split explicitly only when genuinely different
    # spellings/forms are present - not when the same spelling simply spans
    # several source_keys (see module docstring).
    split_notice = None
    distinct_forms = sorted({b["source_form"] for b in blocks})
    if len(distinct_forms) > 1:
        split_notice = (
            f"Izvor vodi {len(distinct_forms)} odvojena zapisa za ovo ime: "
            f"{', '.join(distinct_forms)}. Prikazujemo ih odvojeno jer ih "
            "statistika ne spaja."
        )

    return {
        "search_key": key,
        "matches": blocks,
        "split_notice": split_notice,
    }
