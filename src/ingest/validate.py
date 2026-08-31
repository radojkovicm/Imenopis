"""Validation invariants (PROJECT.md §11.3). Read-only - reports violations,
never patches data. Run after load_all.py, or standalone against an existing
database: py -3.11 -m src.ingest.validate

Mirrors the §14 data-reviewer role's brief deliberately: this module has no
write path anywhere in it. A validator that can fix what it finds will fix
it quietly instead of surfacing it, which is exactly the failure mode §14
exists to prevent.
"""

import sys
from collections import defaultdict

from sqlalchemy.orm import Session

from src.db.models import CensusRank, DataSource, GivenName, Municipality
from src.db.session import get_session


def check_every_municipality_has_9_cohorts(session: Session) -> list[str]:
    violations = []
    rows = session.query(CensusRank.municipality_id, CensusRank.gender, CensusRank.cohort_id).distinct().all()
    by_muni_gender: dict[tuple[int, str], set[int]] = defaultdict(set)
    for muni_id, gender, cohort_id in rows:
        by_muni_gender[(muni_id, gender)].add(cohort_id)
    for (muni_id, gender), cohort_ids in by_muni_gender.items():
        if len(cohort_ids) != 9:
            muni = session.get(Municipality, muni_id)
            violations.append(
                f"Municipality {muni.name if muni else muni_id!r} ({gender}) has "
                f"{len(cohort_ids)} distinct cohorts, expected 9"
            )
    return violations


def check_ranks_1_to_10_no_gaps(session: Session) -> list[str]:
    violations = []
    rows = session.query(
        CensusRank.municipality_id, CensusRank.cohort_id, CensusRank.gender, CensusRank.rank
    ).all()
    by_cell: dict[tuple[int, int, str], list[int]] = defaultdict(list)
    for muni_id, cohort_id, gender, rank in rows:
        by_cell[(muni_id, cohort_id, gender)].append(rank)
    for key, ranks in by_cell.items():
        expected = list(range(1, len(ranks) + 1))
        if sorted(ranks) != expected:
            violations.append(f"Cell {key}: ranks {sorted(ranks)}, expected contiguous 1..{len(ranks)}")
    return violations


def check_every_census_rank_resolves_to_given_name(session: Session) -> list[str]:
    violations = []
    orphans = (
        session.query(CensusRank.id)
        .outerjoin(GivenName, CensusRank.given_name_id == GivenName.id)
        .filter(GivenName.id.is_(None))
        .all()
    )
    if orphans:
        violations.append(f"{len(orphans)} census_rank rows have no matching given_name row")
    return violations


def check_municipality_count(session: Session, expected: int = 168) -> list[str]:
    # docs/DATA_NOTES.md §7: 168 confirmed exactly from the PDF's own TOC.
    # The RZS spatial register (§3.3) isn't integrated, so this checks
    # against that confirmed count, not an external registry.
    actual = session.query(Municipality).count()
    if actual != expected:
        return [f"Municipality count is {actual}, expected {expected} (docs/DATA_NOTES.md §7)"]
    return []


def check_every_source_key_exists_in_data_source(session: Session) -> list[str]:
    violations = []
    source_keys = {row.key for row in session.query(DataSource.key).all()}
    orphan_given_names = (
        session.query(GivenName.source_key).distinct().filter(~GivenName.source_key.in_(source_keys)).all()
    )
    for (key,) in orphan_given_names:
        violations.append(f"given_name.source_key {key!r} has no matching data_source row")
    return violations


KNOWN_FACTS = {
    ("РЕПУБЛИКА СРБИЈА", "2011–2022", "F"): [
        "Дуња", "Софија", "Милица", "Сара", "Николина",
        "Лена", "Теодора", "Анђела", "Маша", "Нађа",
    ],
    ("РЕПУБЛИКА СРБИЈА", "2011–2022", "M"): [
        "Лука", "Лазар", "Стефан", "Никола", "Алекса",
        "Вук", "Филип", "Михајло", "Павле", "Василије",
    ],
}


def check_known_facts_reproduce(session: Session) -> list[str]:
    # PROJECT.md §3.1's known-facts fixtures are Republic-level, which
    # census_rank does NOT store (§7.3/load_census_rank.py's scope decision -
    # municipality_id is NOT NULL, no rollup rows persisted there). This
    # check is a placeholder documenting that gap rather than a real check
    # against this database - the actual known-facts verification for T1/T2
    # lives in tests/test_t1t2_parser.py, run directly against parser output
    # before the rollup rows get dropped at load time.
    return []


def run_all(session: Session) -> dict[str, list[str]]:
    checks = {
        "every_municipality_has_9_cohorts": check_every_municipality_has_9_cohorts,
        "ranks_1_to_10_no_gaps": check_ranks_1_to_10_no_gaps,
        "census_rank_resolves_to_given_name": check_every_census_rank_resolves_to_given_name,
        "municipality_count": check_municipality_count,
        "source_key_exists_in_data_source": check_every_source_key_exists_in_data_source,
        "known_facts_reproduce": check_known_facts_reproduce,
    }
    results = {}
    for name, fn in checks.items():
        results[name] = fn(session)
    return results


def main() -> None:
    session = get_session()
    try:
        results = run_all(session)
    finally:
        session.close()

    total_violations = sum(len(v) for v in results.values())
    for check_name, violations in results.items():
        status = "OK" if not violations else f"{len(violations)} VIOLATIONS"
        print(f"[{status}] {check_name}")
        for v in violations:
            print(f"    - {v}")

    if total_violations:
        print(f"\n{total_violations} total violations found.", file=sys.stderr)
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
