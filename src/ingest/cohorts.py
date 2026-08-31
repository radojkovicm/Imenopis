"""Table 1/2 cohort definitions (PROJECT.md §6.4, corrected by Phase 0 to 9
cohorts, not 11 - see docs/DATA_NOTES.md §4)."""

from dataclasses import dataclass


@dataclass
class CohortDef:
    label: str  # exactly as printed in the PDF
    year_from: int | None
    year_to: int | None
    sort_order: int


COHORTS: list[CohortDef] = [
    CohortDef("1940. и раније", None, 1940, 1),
    CohortDef("1941–1950", 1941, 1950, 2),
    CohortDef("1951–1960", 1951, 1960, 3),
    CohortDef("1961–1970", 1961, 1970, 4),
    CohortDef("1971–1980", 1971, 1980, 5),
    CohortDef("1981–1990", 1981, 1990, 6),
    CohortDef("1991–2000", 1991, 2000, 7),
    CohortDef("2001–2010", 2001, 2010, 8),
    CohortDef("2011–2022", 2011, 2022, 9),
]

COHORT_LABELS: set[str] = {c.label for c in COHORTS}
COHORT_SORT_ORDER: dict[str, int] = {c.label: c.sort_order for c in COHORTS}
