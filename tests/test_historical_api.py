"""API-level tests for §16's historical layer endpoints.

Runs against the real, already-ingested database - skipped if it hasn't
been loaded (src.ingest.load_all + src.ingest.load_historical), same
convention as test_municipality_api.py.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.historical_models import HistoricalNameAttestation
from src.db.session import get_session

DB_PATH = Path(__file__).resolve().parents[1] / "imena.db"

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="database not loaded - run src.ingest.load_all first")

client = TestClient(app)


def _historical_row_count() -> int:
    if not DB_PATH.exists():
        return 0
    session = get_session()
    try:
        return session.query(HistoricalNameAttestation).count()
    finally:
        session.close()


historical_seed_loaded = pytest.mark.skipif(
    _historical_row_count() == 0,
    reason="historical layer not loaded - run src.ingest.load_historical first",
)


@historical_seed_loaded
def test_historical_name_returns_observed_attestation():
    resp = client.get("/api/historical/vuk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["search_key"] == "vuk"
    assert len(data["matches"]) == 1
    block = data["matches"][0]
    assert block["source_form"] == "Вук"
    assert block["gender"] == "M"
    attestation = block["attestations"][0]
    assert attestation["evidence"] == "observed"
    assert attestation["historical_confidence"] == "C"
    assert attestation["citation_note"]  # §16.3 rule 5: never empty


@historical_seed_loaded
def test_historical_unknown_name_returns_200_not_404():
    # §12's no-404 rule extended to §16 (module docstring).
    resp = client.get("/api/historical/ovo-ime-sigurno-ne-postoji-nigde")
    assert resp.status_code == 200
    data = resp.json()
    assert data["matches"] == []
    assert data["result"]["evidence"] == "unknown"
    assert data["result"]["reason"] == "no_historical_source_for_period"


@historical_seed_loaded
def test_historical_filter_by_name_type():
    resp = client.get("/api/historical", params={"name_type": "native_slavic"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) >= 1
    for r in data["results"]:
        assert r["attestation"]["value"]["name_type"] == "native_slavic"


@historical_seed_loaded
def test_historical_confidence_b_row_has_no_frequency_rank_field():
    # §16.2/§16.3 rule 1: frequency_level is categorical, never a numeric
    # rank - confirm the API never introduces one.
    resp = client.get("/api/historical/vukosava")
    assert resp.status_code == 200
    data = resp.json()
    block = data["matches"][0]
    attestation = block["attestations"][0]
    assert attestation["historical_confidence"] == "B"
    assert "frequency_rank" not in attestation["value"]
    assert attestation["value"]["frequency_level"] in (
        "dominant", "very_common", "common", "attested", "rare", "uncertain", None,
    )


@historical_seed_loaded
def test_name_endpoint_reports_historical_available():
    # §16: /api/name's historical_available cross-link field.
    resp = client.get("/api/name/milica")
    assert resp.status_code == 200
    data = resp.json()
    block = next(b for b in data["matches"] if b["gender"] == "F")
    assert block["historical_available"] is True

    resp2 = client.get("/api/name/goran")
    data2 = resp2.json()
    block2 = next(b for b in data2["matches"] if b["gender"] == "M")
    assert block2["historical_available"] is False
