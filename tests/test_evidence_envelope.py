"""§4.4 required test: no rendered string containing 'retk', 'čest', 'popular',
'koncentr' or a '%' sign can be produced from any payload whose evidence is
'unknown'. Checked here at the envelope level (the API layer that actually
emits these payloads), since there's no frontend yet to test end-to-end.

Also covers §16.3 rules 1-2's analogous requirement for the historical
layer: a confidence-D (or C, for frequency claims) attestation must never
carry API-level copy that already reads as "potvrđeno"/"najčešće" - the API
itself never generates such copy (that's static/evidence.js's job, per its
own docstring naming itself the one choke point for this), so this test
locks in that the envelope stays copy-free, forcing any future "helpful"
copy-generation added to the API to go through the same review this file
already gets.
"""

import json

from src.api.envelope import HistoricalAttestationValue, UnknownValue

FORBIDDEN_SUBSTRINGS = ["retk", "čest", "popular", "koncentr", "%"]
HISTORICAL_FORBIDDEN_SUBSTRINGS = ["potvrđeno", "najčešće", "confirmed", "most common"]


def test_unknown_value_envelope_is_clean():
    payload = UnknownValue(reason="source_is_top10_only").model_dump()
    text = json.dumps(payload, ensure_ascii=False)
    for bad in FORBIDDEN_SUBSTRINGS:
        assert bad not in text, f"UnknownValue envelope leaked forbidden text: {bad!r}"


def test_unknown_value_has_null_value():
    payload = UnknownValue(reason="scope_not_published").model_dump()
    assert payload["value"] is None
    assert payload["evidence"] == "unknown"


def test_evidence_and_status_are_separate_fields():
    # §4.2: evidence describes what we can know, status describes what
    # happened in the source - never collapsed into one field.
    payload = UnknownValue(reason="source_is_top10_only").model_dump()
    assert "evidence" in payload
    assert "status" in payload
    assert payload["evidence"] != payload["status"]


def test_historical_attestation_envelope_never_generates_confirmation_copy():
    # §16.3 rules 1-2: the API must never itself emit "potvrđeno"/"najčešće"
    # style copy for a historical attestation - that wording decision
    # belongs to the frontend (static/evidence.js's confidenceText()),
    # which gates it on historical_confidence. The API's job is only to
    # report historical_confidence faithfully.
    for level in ("A", "B", "C", "D"):
        payload = HistoricalAttestationValue(
            value={"period_start": 1348, "period_end": 1348},
            source="povelja_dusan_1348",
            historical_confidence=level,
            citation_note="test citation",
        ).model_dump()
        text = json.dumps(payload, ensure_ascii=False)
        for bad in HISTORICAL_FORBIDDEN_SUBSTRINGS:
            assert bad not in text, f"HistoricalAttestationValue (confidence={level}) leaked forbidden text: {bad!r}"


def test_historical_attestation_is_always_observed():
    # §16.2: a historical attestation that exists is always evidence/status
    # "observed" - historical_confidence is the separate, independent
    # qualifier, never folded into evidence/status.
    payload = HistoricalAttestationValue(
        value={"period_start": 1516, "period_end": 1516},
        source="defter_smederevo_1516",
        historical_confidence="D",
        citation_note="test citation",
    ).model_dump()
    assert payload["evidence"] == "observed"
    assert payload["status"] == "observed"
    assert payload["historical_confidence"] == "D"
