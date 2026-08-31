"""§4.4 required test: no rendered string containing 'retk', 'čest', 'popular',
'koncentr' or a '%' sign can be produced from any payload whose evidence is
'unknown'. Checked here at the envelope level (the API layer that actually
emits these payloads), since there's no frontend yet to test end-to-end.
"""

import json

from src.api.envelope import UnknownValue

FORBIDDEN_SUBSTRINGS = ["retk", "čest", "popular", "koncentr", "%"]


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
