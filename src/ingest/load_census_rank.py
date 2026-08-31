"""Loads Table 1/Table 2 (municipality-level census ranks) into `municipality`,
`cohort`, and `census_rank` (Step 3 of PROJECT.md §10's build order).

**Scope decision**: `census_rank.municipality_id` is `NOT NULL` in the schema
(§6.5) - it has no slot for Republic/macro-region/NUTS-2-region/oblast rollup
rows, only real municipalities. This loader therefore persists only the 168
real municipality-level rows (140 plain opština + 28 Grad-subdistrict rows,
per docs/DATA_NOTES.md §7) into `census_rank`. The Republic-level and
region/oblast-level rows that `t1t2_parser.py` also extracts (for the 9
rollup labels) are parsed but NOT loaded here - there's currently no table
they belong in. This is a real, deliberate gap versus what the source
actually contains, not an oversight - flagged here and in docs/DATA_NOTES.md
so a future schema change (if §7.4's municipality-vs-national comparison
needs it) has a clear starting point rather than rediscovering the gap.
"""

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.models import Cohort, CensusRank, District, GivenName, Municipality
from src.ingest.cohorts import COHORTS
from src.ingest.geo_seed import MunicipalitySeed, build_municipality_seeds
from src.ingest.geography import DISTRICT_CODES
from src.ingest.seed_sources import CENSUS_T1_KEY, CENSUS_T2_KEY
from src.ingest.t1t2_parser import TABLE1_PAGE_RANGE, TABLE2_PAGE_RANGE, parse_table
from src.util.normalize import make_search_key

ROLLUP_NAMES = {
    "РЕПУБЛИКА СРБИЈА", "СРБИЈА – СЕВЕР", "СРБИЈА – ЈУГ",
    "Београдски регион", "Регион Војводине",
    "Регион Шумадије и Западне Србије", "Регион Јужне и Источне Србије",
}


def load_cohorts(session: Session) -> dict[str, int]:
    label_to_id: dict[str, int] = {}
    for c in COHORTS:
        existing = session.query(Cohort).filter_by(label=c.label).one_or_none()
        if existing:
            label_to_id[c.label] = existing.id
            continue
        row = Cohort(label=c.label, year_from=c.year_from, year_to=c.year_to, sort_order=c.sort_order)
        session.add(row)
        session.flush()
        label_to_id[c.label] = row.id
    session.commit()
    return label_to_id


def load_municipalities(
    session: Session, pdf_path: Path, district_ids: dict[str, int]
) -> dict[tuple[str, str | None], int]:
    """Returns (name, parent_grad) -> municipality.id. Keyed by this pair,
    not name alone, because of a real naming collision: "Палилула" is both
    a Belgrade opština and a Niš city district (docs/DATA_NOTES.md §7).
    parent_grad matches t1t2_parser.MunicipalityRankRow.parent_grad exactly
    (both ultimately come from GRAD_SUBDISTRICTS in toc_extractor.py), so
    the caller can look up a parsed row's municipality directly by
    (row.geography_label, row.parent_grad).
    """
    seeds = build_municipality_seeds(pdf_path)
    key_to_id: dict[tuple[str, str | None], int] = {}
    for seed in seeds:
        existing = session.query(Municipality).filter_by(code_rzs=seed.code_rzs).one_or_none()
        if existing:
            key_to_id[(seed.name, seed.parent_grad)] = existing.id
            continue
        district_id = district_ids.get(seed.district_code) if seed.district_code else None
        row = Municipality(
            code_rzs=seed.code_rzs,
            name=seed.name,
            name_slug=seed.name_slug,
            district_id=district_id,
        )
        session.add(row)
        session.flush()
        key_to_id[(seed.name, seed.parent_grad)] = row.id
    session.commit()
    return key_to_id


def load_census_rank(
    session: Session,
    pdf_path: Path,
    municipality_ids: dict[tuple[str, str | None], int],
    cohort_ids: dict[str, int],
) -> None:
    given_name_cache: dict[tuple[str, str, str], int] = {}

    def get_or_create_given_name(source_form: str, source_key: str, gender: str) -> int:
        key = (source_form, source_key, gender)
        if key in given_name_cache:
            return given_name_cache[key]
        existing = (
            session.query(GivenName)
            .filter_by(source_form=source_form, source_key=source_key, gender=gender)
            .one_or_none()
        )
        if existing:
            given_name_cache[key] = existing.id
            return existing.id
        gn = GivenName(
            source_form=source_form,
            source_key=source_key,
            search_key=make_search_key(source_form),
            gender=gender,
        )
        session.add(gn)
        session.flush()
        given_name_cache[key] = gn.id
        return gn.id

    total = 0
    skipped_rollup = 0
    for gender, page_range, source_key in (
        ("F", TABLE1_PAGE_RANGE, CENSUS_T1_KEY),
        ("M", TABLE2_PAGE_RANGE, CENSUS_T2_KEY),
    ):
        known_names = {name for name, _parent in municipality_ids.keys()} | set(DISTRICT_CODES.keys()) | ROLLUP_NAMES
        rows = parse_table(pdf_path, page_range, gender, known_names)
        count = 0
        for r in rows:
            muni_key = (r.geography_label, r.parent_grad)
            if muni_key not in municipality_ids:
                # Republic / macro-region / NUTS-2 region / oblast rollup -
                # not loaded into census_rank (see module docstring).
                skipped_rollup += 1
                continue
            municipality_id = municipality_ids[muni_key]
            cohort_id = cohort_ids[r.cohort_label]
            gn_id = get_or_create_given_name(r.source_form, source_key, gender)
            existing = (
                session.query(CensusRank)
                .filter_by(
                    municipality_id=municipality_id,
                    cohort_id=cohort_id,
                    gender=gender,
                    given_name_id=gn_id,
                )
                .one_or_none()
            )
            if existing:
                continue
            session.add(
                CensusRank(
                    given_name_id=gn_id,
                    municipality_id=municipality_id,
                    cohort_id=cohort_id,
                    gender=gender,
                    rank=r.rank,
                    count=None,
                )
            )
            count += 1
        session.commit()
        total += count
        print(f"census_rank ({gender}): loaded {count} rows")
    print(f"census_rank total: {total} rows (skipped {skipped_rollup} rollup-level rows - see module docstring)")
