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
from src.db.models import CensusRank, CensusRankByYear, Cohort, DataSource, District, GivenName, Municipality, NewbornName
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


def _longest_consecutive_year_run(years: list[int]) -> tuple[int, int] | None:
    """Longest run of consecutive integers in a sorted, deduped list.
    Returns (start, end) or None if the list is empty."""
    if not years:
        return None
    best_start = best_end = years[0]
    cur_start = cur_end = years[0]
    for y in years[1:]:
        if y == cur_end + 1:
            cur_end = y
        else:
            if cur_end - cur_start > best_end - best_start:
                best_start, best_end = cur_start, cur_end
            cur_start = cur_end = y
    if cur_end - cur_start > best_end - best_start:
        best_start, best_end = cur_start, cur_end
    return best_start, best_end


def _national_persistence(national_by_year: list[dict]) -> dict | None:
    """§7.5 / §5.4: longest CONSECUTIVE run of single birth years (T3, top
    5) the name appears in, expressed as a year span - never a count of
    cohorts, since §5.4 bars treating unequal-length buckets as equal steps.
    T3's rows are individual years already, so this is a plain consecutive-
    integer scan, not a cohort-boundary computation (that's the T1/T2 case,
    _municipality_persistence below).
    """
    years = sorted({r["birth_year"] for r in national_by_year})
    run = _longest_consecutive_year_run(years)
    if run is None:
        return None
    start, end = run
    return {"year_from": start, "year_to": end}


def _longest_consecutive_order_run(orders: list[int]) -> tuple[int, int]:
    """Longest run of consecutive integers in a sorted, deduped list.
    Same algorithm as _longest_consecutive_year_run but named separately
    since it operates on cohort.sort_order values, not calendar years -
    keeping the two call sites self-documenting about which space they're
    scanning in."""
    best_start = best_end = orders[0]
    cur_start = cur_end = orders[0]
    for o in orders[1:]:
        if o == cur_end + 1:
            cur_end = o
        else:
            if cur_end - cur_start > best_end - best_start:
                best_start, best_end = cur_start, cur_end
            cur_start = cur_end = o
    if cur_end - cur_start > best_end - best_start:
        best_start, best_end = cur_start, cur_end
    return best_start, best_end


def _census_rank_rows(session: Session, source_form: str, gender: str, source_key: str):
    """Shared query behind _municipality_data and _municipality_persistence -
    every municipality-level census_rank row for this (source_form, gender)
    in the given table (census_2022_t1 or t2). Excludes the Republic-level
    row (municipality_id IS NULL); that's the national side, served by
    /api/municipality, not duplicated here.
    """
    return (
        session.query(CensusRank, Municipality, Cohort)
        .join(GivenName, CensusRank.given_name_id == GivenName.id)
        .join(Municipality, CensusRank.municipality_id == Municipality.id)
        .join(Cohort, CensusRank.cohort_id == Cohort.id)
        .filter(
            GivenName.source_form == source_form,
            GivenName.gender == gender,
            GivenName.source_key == source_key,
            CensusRank.municipality_id.is_not(None),
        )
        .all()
    )


def _municipality_persistence(rows: list) -> list[dict]:
    """§7.5 / §5.4: for each municipality the name appears in (T1/T2), the
    longest run of CONSECUTIVE cohorts (by cohort.sort_order, not by label
    string) it holds a top-10 spot in, expressed as the year span covered
    by that run (cohort.year_from of the first cohort to cohort.year_to of
    the last) - never a count of cohorts, per §5.4's ban on treating
    unequal-length buckets as equal steps.
    """
    by_muni: dict[str, tuple[str, list[Cohort]]] = {}
    for _rank, m, c in rows:
        by_muni.setdefault(m.name, (m.name_slug, []))[1].append(c)

    out = []
    for muni_name, (slug, cohorts) in by_muni.items():
        cohorts_by_order = sorted({c.sort_order: c for c in cohorts}.items())
        orders = [o for o, _ in cohorts_by_order]
        start_order, end_order = _longest_consecutive_order_run(orders)
        order_to_cohort = dict(cohorts_by_order)
        first_cohort = order_to_cohort[start_order]
        last_cohort = order_to_cohort[end_order]
        out.append(
            {
                "municipality": muni_name,
                "slug": slug,
                "year_from": first_cohort.year_from,  # None if the run starts at the open-ended "1940 and earlier" bucket
                "year_to": last_cohort.year_to,
                "cohort_from": first_cohort.label,
                "cohort_to": last_cohort.label,
            }
        )
    return out


def _municipality_data(session: Session, source_form: str, gender: str, rows: list) -> dict:
    """§7.1 'Gde': municipality count, highest rank achieved and where.
    Takes the already-fetched census_rank rows (see _census_rank_rows) so
    the query isn't run twice for the same block.
    """
    source = SOURCE_BY_GENDER[gender]
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

        # §7.5: longest consecutive top-5/top-10 run, national (T3) and per
        # municipality (T1/T2). Two different measures from two different
        # sources - never merged into one number (§6.6's "no automatic
        # merging across sources").
        national_persistence = _national_persistence(national_by_year)
        block["national_persistence"] = (
            ObservedValue(
                value=national_persistence,
                source="census_2022_t3",
                scope=Scope(gender=gender_val),
            ).model_dump()
            if national_persistence
            else UnknownValue(reason="source_is_top5_only").model_dump()
        )

        census_source = SOURCE_BY_GENDER[gender_val]
        census_rows = _census_rank_rows(session, source_form, gender_val, census_source)
        block.update(_municipality_data(session, source_form, gender_val, census_rows))
        muni_persistence = _municipality_persistence(census_rows) if census_rows else []
        block["municipality_persistence"] = (
            DerivedValue(
                value=muni_persistence,
                derived_from=[census_source],
                note="longest_consecutive_cohort_run_per_municipality",
            ).model_dump()
            if muni_persistence
            else UnknownValue(reason="source_is_top10_only").model_dump()
        )

        # §16: a plain boolean pointer to the historical layer, computed by
        # checking whether any given_name row with this search_key resolves
        # to a data_source whose measure='attestation'. Deliberately just a
        # boolean - the historical data itself lives only behind
        # /api/historical, never duplicated inline here (§16.3 rule 4: the
        # two corpora are never merged into one response).
        block["historical_available"] = (
            session.query(GivenName)
            .join(DataSource, GivenName.source_key == DataSource.key)
            .filter(GivenName.search_key == key, DataSource.measure == "attestation")
            .first()
            is not None
        )

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
