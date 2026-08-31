"""API-level tests for §7.4's municipality page: top 10 by cohort/gender,
with a national-comparison column that is `unknown` (not a number), per §5.3,
whenever the name isn't in the Republic top 10 for that cohort.

Runs against the real, already-ingested database (data/raw + load_all.py) -
skipped if it hasn't been loaded, same convention as the other ground-truth
tests in this suite.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.session import get_session
from src.db.models import Municipality

DB_PATH = Path(__file__).resolve().parents[1] / "imena.db"

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="database not loaded - run src.ingest.load_all first")

client = TestClient(app)


def _municipality_count() -> int:
    session = get_session()
    try:
        return session.query(Municipality).count()
    finally:
        session.close()


def test_municipality_list_returns_168():
    resp = client.get("/api/municipality")
    assert resp.status_code == 200
    assert len(resp.json()) == _municipality_count() == 168


def test_municipality_404_for_unknown_slug():
    resp = client.get("/api/municipality/not-a-real-place")
    assert resp.status_code == 404


def test_sabac_female_2011_2022_matches_known_data():
    resp = client.get("/api/municipality/sabac?gender=F")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Шабац"
    cohort = data["cohorts"]["female"][-1]
    assert cohort["cohort"] == "2011–2022"
    top10 = cohort["top10"]["value"]
    assert [e["name"] for e in top10] == [
        "Дуња", "Софија", "Милица", "Николина", "Нађа",
        "Теодора", "Сара", "Јана", "Лена", "Анђела",
    ]


def test_national_rank_is_unknown_not_a_guessed_number():
    # §5.3: a name outside the Republic top 10 for that cohort must be
    # evidence:"unknown", never a fabricated or omitted rank number.
    resp = client.get("/api/municipality/sabac?gender=F")
    data = resp.json()
    cohort = data["cohorts"]["female"][-1]
    entries = {e["name"]: e["national"] for e in cohort["top10"]["value"]}
    # "Јана" is locally #8 in Šabac 2011-2022 but not in the Republic top 10.
    assert entries["Јана"]["evidence"] == "unknown"
    assert entries["Јана"]["value"] is None
    # "Дуња" is both locally #1 and nationally #1.
    assert entries["Дуња"]["evidence"] == "observed"
    assert entries["Дуња"]["value"] == 1


def test_cohort_endpoint_national_top10_and_deviation():
    resp = client.get("/api/cohort/9?gender=F")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cohort"] == "2011–2022"
    national = data["female"]["national_top10"]["value"]
    assert [e["name"] for e in national][:3] == ["Дуња", "Софија", "Милица"]
    deviation = data["female"]["deviating_municipalities"]
    assert deviation["evidence"] == "derived"
    assert isinstance(deviation["value"], list)
    assert len(deviation["value"]) > 0


def test_cohort_404_for_unknown_id():
    resp = client.get("/api/cohort/9999")
    assert resp.status_code == 404


def test_name_endpoint_includes_municipality_data():
    resp = client.get("/api/name/goran")
    assert resp.status_code == 200
    data = resp.json()
    block = next(b for b in data["matches"] if b["gender"] == "M")
    assert block["municipality_count"]["evidence"] == "derived"
    assert block["municipality_count"]["value"] > 0
    assert block["best_rank"]["evidence"] == "observed"
    assert block["best_rank"]["value"]["rank"] >= 1
