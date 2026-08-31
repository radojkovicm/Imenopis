"""Ground-truth tests for the Table 3 parser (PROJECT.md §11.3: 'Every known
fact in §3.1 reproduces exactly'). Uses the real census PDF - this is the one
real ground truth in the project per §14 (test-runner subagent notes).
"""

from pathlib import Path

import pytest

from src.ingest.pdf_parser import parse_table3

PDF_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "census2022_names.pdf"

pytestmark = pytest.mark.skipif(not PDF_PATH.exists(), reason="census PDF not present in data/raw")


@pytest.fixture(scope="module")
def rows():
    return parse_table3(PDF_PATH)


def _top(rows, gender, year_label):
    return [r.source_form for r in sorted(
        (r for r in rows if r.gender == gender and r.year_label == year_label),
        key=lambda r: r.rank,
    )]


def test_row_count_is_exact(rows):
    # 83 distinct birth years (1940-and-earlier + 1941..2022) x 2 genders x 5 ranks
    assert len(rows) == 830


def test_every_year_has_exactly_5_ranks(rows):
    from collections import Counter

    counts = Counter((r.gender, r.year_label) for r in rows)
    assert all(v == 5 for v in counts.values())
    assert len(counts) == 83 * 2


def test_female_by_year_progression(rows):
    # PROJECT.md §3.1 known-facts fixture
    assert _top(rows, "F", "1940. и раније")[0] == "Радмила"
    assert _top(rows, "F", "1944")[0] == "Слободанка"
    assert _top(rows, "F", "1946")[0] == "Мирјана"
    assert _top(rows, "F", "1949")[0] == "Љиљана"
    assert _top(rows, "F", "1971")[0] == "Биљана"
    assert _top(rows, "F", "1974")[0] == "Данијела"
    assert _top(rows, "F", "1976")[0] == "Јелена"
    assert _top(rows, "F", "1995")[0] == "Милица"
    assert _top(rows, "F", "2013")[0] == "Дуња"
    assert _top(rows, "F", "2016")[0] == "Софија"


def test_2022_top5(rows):
    assert _top(rows, "F", "2022") == ["Софија", "Мила", "Дуња", "Теодора", "Сара"]
    assert _top(rows, "M", "2022") == ["Лука", "Лазар", "Василије", "Богдан", "Вук"]


def test_1940_and_earlier_top5(rows):
    assert _top(rows, "F", "1940. и раније") == ["Радмила", "Милица", "Марија", "Љубица", "Вера"]
    assert _top(rows, "M", "1940. и раније") == ["Милан", "Томислав", "Душан", "Миодраг", "Петар"]
