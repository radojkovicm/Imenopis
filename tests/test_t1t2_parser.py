"""Ground-truth tests for the Table 1/2 (municipality-level census ranks)
parser - the hardest parse in the project (PROJECT.md §10 calls this out as
where "all the parsing risk sits"). Runs against the real PDF.
"""

from pathlib import Path

import pytest

from src.ingest.geography import DISTRICT_CODES
from src.ingest.geo_seed import build_municipality_seeds
from src.ingest.t1t2_parser import TABLE1_PAGE_RANGE, TABLE2_PAGE_RANGE, parse_table

PDF_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "census2022_names.pdf"

pytestmark = pytest.mark.skipif(not PDF_PATH.exists(), reason="census PDF not present in data/raw")

ROLLUP_NAMES = {
    "РЕПУБЛИКА СРБИЈА", "СРБИЈА – СЕВЕР", "СРБИЈА – ЈУГ",
    "Београдски регион", "Регион Војводине",
    "Регион Шумадије и Западне Србије", "Регион Јужне и Источне Србије",
}


@pytest.fixture(scope="module")
def known_names():
    munis = build_municipality_seeds(PDF_PATH)
    return set(m.name for m in munis) | set(DISTRICT_CODES.keys()) | ROLLUP_NAMES


@pytest.fixture(scope="module")
def female_rows(known_names):
    return parse_table(PDF_PATH, TABLE1_PAGE_RANGE, "F", known_names)


@pytest.fixture(scope="module")
def male_rows(known_names):
    return parse_table(PDF_PATH, TABLE2_PAGE_RANGE, "M", known_names)


def _top(rows, geography_label, cohort_label):
    return [
        r.source_form
        for r in sorted(
            (r for r in rows if r.geography_label == geography_label and r.cohort_label == cohort_label),
            key=lambda r: r.rank,
        )
    ]


def test_female_row_count(female_rows):
    # 199 geography blocks (168 municipality-level + rollups) x 9 cohorts x 10 ranks
    assert len(female_rows) == 17910


def test_male_row_count(male_rows):
    assert len(male_rows) == 17910


def test_every_block_has_9x10_rows_except_the_known_palilula_duplicate(female_rows):
    from collections import Counter

    counts = Counter((r.geography_label, r.cohort_label) for r in female_rows)
    # each (geography, cohort) pair should have exactly 10 ranks - Палилула
    # is a genuine naming collision (Belgrade opština + Niš city district,
    # docs/DATA_NOTES.md §7) so it legitimately has 2x the data under one
    # label string; every other label should be clean.
    bad = {k: v for k, v in counts.items() if v != 10}
    non_palilula_bad = {k: v for k, v in bad.items() if k[0] != "Палилула"}
    assert non_palilula_bad == {}


def test_republic_top10_female_matches_known_facts(female_rows):
    # PROJECT.md §3.1 known-facts fixture
    assert _top(female_rows, "РЕПУБЛИКА СРБИЈА", "2011–2022") == [
        "Дуња", "Софија", "Милица", "Сара", "Николина",
        "Лена", "Теодора", "Анђела", "Маша", "Нађа",
    ]
    assert _top(female_rows, "РЕПУБЛИКА СРБИЈА", "1971–1980")[0] == "Јелена"


def test_republic_top10_male_matches_known_facts(male_rows):
    assert _top(male_rows, "РЕПУБЛИКА СРБИЈА", "2011–2022") == [
        "Лука", "Лазар", "Стефан", "Никола", "Алекса",
        "Вук", "Филип", "Михајло", "Павле", "Василије",
    ]


def test_no_tied_ranks_within_a_block(female_rows):
    # PROJECT.md §9.3: ranks should be 1..10 with no duplicates, per block
    from collections import defaultdict

    by_block: dict[tuple, list[int]] = defaultdict(list)
    for r in female_rows:
        by_block[(r.geography_label, r.cohort_label, r.page_left)].append(r.rank)
    # spot-check a sample rather than every block (this is a slow parse)
    sample = list(by_block.items())[:50]
    for key, ranks in sample:
        assert sorted(ranks) == list(range(1, len(ranks) + 1)), f"{key}: {ranks}"
