"""Phase 1 ingestion orchestrator (Step 1 of PROJECT.md §10 build order).

Loads: data_source seed rows, Table 3 (census PDF, Republic x birth year,
ranks I-V), and all 5 newborn XLSX years (district-level + Republic rollup).

Run with: py -3.11 -m src.ingest.load_all

Idempotent: safe to re-run against a fresh database. Not safe to re-run
against a partially-loaded one without clearing tables first - this script
does not attempt incremental/upsert loading, matching the spec's "no
automatic merging across sources" stance (§6.6): a load is a clean pass over
one source into the tables that source owns.
"""

import sys
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from src.db.models import CensusRankByYear, District, GivenName, NewbornName
from src.db.session import get_session, init_db
from src.ingest.geography import DISTRICT_CODES
from src.ingest.pdf_parser import parse_table3
from src.ingest.seed_sources import CENSUS_T3_KEY, NEWBORN_KEYS, seed_rows
from src.ingest.xlsx_loader import XlsxStructureError, load_year
from src.util.normalize import make_search_key

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
NORMALIZED_DIR = BASE_DIR / "data" / "normalized"

NEWBORN_FILES = {
    2021: "najcesca-imеna-dece-rodjene-u-2021-godini.xlsx",
    2022: "najcesca-imena-dece-rodjene-u-2022-godini.xlsx",
    2023: "najcescaimenadece2023.xlsx",
    2024: "najcesca-imena-dece-rodjene-u-2024-godini.xlsx",
    2025: "najcesca-imena-dece-rodjene-u-2025-godini.xlsx",
}

CENSUS_PDF = RAW_DIR / "census2022_names.pdf"


def load_data_sources(session: Session) -> None:
    for row in seed_rows():
        session.merge(row)
    session.commit()


def load_districts(session: Session) -> dict[str, int]:
    """Seed districts from the geography module's known codes. Returns
    code -> district.id map. region_id left NULL - the RZS spatial register
    (§3.3) isn't integrated yet; not needed for Step 1's endpoints.
    """
    code_to_id: dict[str, int] = {}
    for name, code in DISTRICT_CODES.items():
        existing = session.query(District).filter_by(code=code).one_or_none()
        if existing:
            code_to_id[code] = existing.id
            continue
        d = District(code=code, name=name, region_id=None)
        session.add(d)
        session.flush()
        code_to_id[code] = d.id
    session.commit()
    return code_to_id


def get_or_create_given_name(
    session: Session,
    cache: dict[tuple[str, str, str], int],
    source_form: str,
    source_key: str,
    gender: str,
) -> int:
    cache_key = (source_form, source_key, gender)
    if cache_key in cache:
        return cache[cache_key]

    existing = (
        session.query(GivenName)
        .filter_by(source_form=source_form, source_key=source_key, gender=gender)
        .one_or_none()
    )
    if existing:
        cache[cache_key] = existing.id
        return existing.id

    gn = GivenName(
        source_form=source_form,
        source_key=source_key,
        search_key=make_search_key(source_form),
        gender=gender,
    )
    session.add(gn)
    session.flush()
    cache[cache_key] = gn.id
    return gn.id


def load_table3(session: Session) -> None:
    if not CENSUS_PDF.exists():
        print(f"SKIP Table 3: {CENSUS_PDF} not found", file=sys.stderr)
        return

    rows = parse_table3(CENSUS_PDF)
    cache: dict[tuple[str, str, str], int] = {}
    count = 0
    for r in rows:
        if r.birth_year is None:
            # Open-ended "1940. и раније" bucket has no single birth_year to
            # store in this table's schema (birth_year is required/not-null
            # per §6.5). Skip it here - it belongs in a cohort-based table,
            # not census_rank_by_year. Recorded as a known gap, not silently
            # dropped: see docs/DATA_NOTES.md if this needs revisiting.
            continue
        gn_id = get_or_create_given_name(session, cache, r.source_form, CENSUS_T3_KEY, r.gender)
        existing = (
            session.query(CensusRankByYear)
            .filter_by(birth_year=r.birth_year, gender=r.gender, given_name_id=gn_id)
            .one_or_none()
        )
        if existing:
            continue
        session.add(
            CensusRankByYear(
                given_name_id=gn_id,
                birth_year=r.birth_year,
                gender=r.gender,
                rank=r.rank,
                count=None,
            )
        )
        count += 1
    session.commit()
    print(f"Table 3: loaded {count} rows ({len(cache)} distinct given_name rows)")


def load_newborn(session: Session, district_ids: dict[str, int]) -> None:
    cache: dict[tuple[str, str, str], int] = {}
    total = 0
    for year, filename in NEWBORN_FILES.items():
        raw_path = RAW_DIR / filename
        if not raw_path.exists():
            print(f"SKIP newborn {year}: {raw_path} not found", file=sys.stderr)
            continue
        source_key = NEWBORN_KEYS[year]
        try:
            rows = load_year(raw_path, year, NORMALIZED_DIR)
        except XlsxStructureError as e:
            print(f"SKIP newborn {year}: {e}", file=sys.stderr)
            continue

        year_count = 0
        for r in rows:
            gn_id = get_or_create_given_name(session, cache, r.source_form, source_key, r.gender)
            district_id = district_ids[r.district_code] if r.district_code else None
            existing = (
                session.query(NewbornName)
                .filter_by(year=r.year, gender=r.gender, given_name_id=gn_id, district_id=district_id)
                .one_or_none()
            )
            if existing:
                continue
            session.add(
                NewbornName(
                    given_name_id=gn_id,
                    year=r.year,
                    gender=r.gender,
                    rank=r.rank,
                    count=None,
                    district_id=district_id,
                )
            )
            year_count += 1
        session.commit()
        total += year_count
        print(f"Newborn {year}: loaded {year_count} rows")
    print(f"Newborn total: {total} rows")


def main() -> None:
    init_db()
    session = get_session()
    try:
        load_data_sources(session)
        district_ids = load_districts(session)
        load_table3(session)
        load_newborn(session, district_ids)
    finally:
        session.close()


if __name__ == "__main__":
    main()
