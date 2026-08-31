"""Ground-truth tests for the newborn XLSX loader, using the real 2023 file
(docs/DATA_NOTES.md §2's confirmed structure)."""

from pathlib import Path

import pytest

from src.ingest.xlsx_loader import XlsxStructureError, parse_xlsx

XLSX_2023 = Path(__file__).resolve().parents[1] / "data" / "raw" / "najcescaimenadece2023.xlsx"

pytestmark = pytest.mark.skipif(not XLSX_2023.exists(), reason="2023 XLSX not present in data/raw")


def test_republic_top10_matches_known_facts():
    rows = parse_xlsx(XLSX_2023, 2023)
    republic_female = sorted(
        (r for r in rows if r.gender == "F" and r.district_code is None),
        key=lambda r: r.rank,
    )
    assert [r.source_form for r in republic_female] == [
        "Софија", "Дуња", "Мила", "Теодора", "Маша",
        "Сара", "Нађа", "Милица", "Тара", "Ленка",
    ]


def test_no_counts_present():
    rows = parse_xlsx(XLSX_2023, 2023)
    # BRANCH A resolved: rank only. Nothing in this parser's output should
    # carry a count - there's no count field on NewbornRow at all, so this
    # test is really asserting the dataclass shape stays that way.
    assert not any(hasattr(r, "count") for r in rows)


def test_flags_the_2021_data_entry_error():
    """docs/DATA_NOTES.md §2.2: 'Алекса николић' / 'Андреј ћирић' in the 2021
    file, Пиротска област, contain a name+surname typo - must be flagged, not
    silently corrected."""
    path_2021 = Path(__file__).resolve().parents[1] / "data" / "raw" / "najcesca-imеna-dece-rodjene-u-2021-godini.xlsx"
    if not path_2021.exists():
        pytest.skip("2021 XLSX not present")
    rows = parse_xlsx(path_2021, 2021)
    flagged = [r for r in rows if r.flagged]
    assert any("николић" in r.source_form.lower() for r in flagged)
    assert any("ћирић" in r.source_form.lower() for r in flagged)


def test_every_group_has_ten_rows_or_raises():
    # parse_xlsx already raises XlsxStructureError internally if a group
    # doesn't have exactly 10 rows - this just confirms the real file passes.
    rows = parse_xlsx(XLSX_2023, 2023)
    assert len(rows) > 0
