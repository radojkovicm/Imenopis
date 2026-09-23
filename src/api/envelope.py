"""Evidence-envelope response models (PROJECT.md §4).

Every value the API returns carries evidence + status, never a bare scalar
(§4.3). `evidence` describes what we can know; `status` describes what
happened in the source (§4.2) - the two are kept as separate fields, never
collapsed into one.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

Evidence = Literal["observed", "derived", "unknown"]
Status = Literal["observed", "not_observed", "suppressed", "not_applicable"]
Reason = Literal[
    "source_is_top10_only",
    "source_is_top5_only",
    "scope_not_published",
    "source_has_no_counts",
    "below_confidentiality_threshold",
    "no_historical_source_for_period",
]

# §16.2: independent of Evidence/Status - answers "how much should this
# specific historical source be trusted for this claim", not "do we know it".
HistoricalConfidence = Literal["A", "B", "C", "D"]


class Scope(BaseModel):
    municipality: str | None = None
    district: str | None = None
    cohort: str | None = None
    birth_year: int | None = None
    gender: str | None = None


class ObservedValue(BaseModel):
    """An envelope for a value read directly from one source table."""

    value: Any
    evidence: Evidence = "observed"
    status: Status = "observed"
    source: str
    scope: Scope | None = None


class DerivedValue(BaseModel):
    """An envelope for a value computed only from observed ranks."""

    value: Any
    evidence: Evidence = "derived"
    status: Status = "observed"
    derived_from: list[str]
    note: str | None = None


class UnknownValue(BaseModel):
    """An envelope for a question the source cannot answer (§4.4: null is not
    'rare' - this is the normal, correct shape for an out-of-coverage query)."""

    value: None = None
    evidence: Evidence = "unknown"
    status: Status = "not_observed"
    reason: Reason


class HistoricalAttestationValue(BaseModel):
    """An envelope for a §16 historical name attestation - a sibling of
    ObservedValue, not a replacement. evidence/status are always
    'observed'/'observed' (the row exists in a named source); the
    historical_confidence field is the additional, independent qualifier
    §16.2 requires and must never be collapsed into evidence/status.
    """

    value: Any
    evidence: Evidence = "observed"
    status: Status = "observed"
    source: str  # data_source.key, measure='attestation'
    historical_confidence: HistoricalConfidence
    citation_note: str
    scope: Scope | None = None
