"""§16 historical layer - proof-of-concept seed data (3-5 hand-entered
examples), NOT a real corpus. PROJECT.md §16 requires every row cite a
checkable source (§16.3 rule 5) - these entries deliberately use only what
was actually verified/provided, never invented dates or citation details.

This is manually curated data, not parsed from a PDF/XLSX like the rest of
the ingest pipeline - see src/ingest/load_historical.py for why it has its
own standalone entry point instead of a step in load_all.py.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.db.historical_models import HistoricalNameAttestation
from src.db.models import GivenName
from src.ingest.seed_sources import HIST_ANALIZA_1516, HIST_DEFTER_SMEDEREVO_1516, HIST_POVELJA_DUSAN_1348
from src.util.normalize import make_search_key


@dataclass
class HistoricalAttestationExample:
    source_form: str
    gender: str
    source_key: str  # data_source.key this attestation belongs to
    period_start: int | None
    period_end: int | None
    region: str | None
    name_type: str
    historical_confidence: str  # 'A' | 'B' | 'C' | 'D'
    frequency_level: str | None
    attestation_count: int | None
    citation_note: str


def historical_attestation_examples() -> list[HistoricalAttestationExample]:
    """3-5 proof-of-concept examples, per the approved plan - not a bulk
    dataset. Confidence C for the charter-attested names (a name appearing
    in one specific document), confidence B for the two names drawn from
    the 1516 census's real quantitative corpus (942 names - a large enough
    sample to support a frequency_level claim, per §16.2/§16.3 rule 1).
    """
    return [
        HistoricalAttestationExample(
            source_form="Вук",
            gender="M",
            source_key=HIST_POVELJA_DUSAN_1348,
            period_start=1348,
            period_end=1348,
            region="Srbija (Dušanovo carstvo)",
            name_type="native_slavic",
            historical_confidence="C",
            frequency_level=None,  # confidence C: existence claim only, no frequency claim (§16.3 rule 1)
            attestation_count=None,
            citation_note="Ime potvrđeno u tekstu povelje cara Dušana, 1348.",
        ),
        HistoricalAttestationExample(
            source_form="Стефан",
            gender="M",
            source_key=HIST_POVELJA_DUSAN_1348,
            period_start=1348,
            period_end=1348,
            region="Srbija (Dušanovo carstvo)",
            name_type="christian",
            historical_confidence="C",
            frequency_level=None,
            attestation_count=None,
            citation_note="Ime potvrđeno u tekstu povelje cara Dušana, 1348 (dinastičko ime Nemanjića).",
        ),
        HistoricalAttestationExample(
            source_form="Милица",
            gender="F",
            source_key=HIST_POVELJA_DUSAN_1348,
            period_start=1348,
            period_end=1348,
            region="Srbija (Dušanovo carstvo)",
            name_type="native_slavic",
            historical_confidence="C",
            frequency_level=None,
            attestation_count=None,
            citation_note="Ime potvrđeno u tekstu povelje cara Dušana, 1348.",
        ),
        HistoricalAttestationExample(
            source_form="Вукосава",
            gender="F",
            source_key=HIST_DEFTER_SMEDEREVO_1516,
            period_start=1516,
            period_end=1516,
            region="Smederevski sandžak",
            name_type="native_slavic",
            historical_confidence="B",
            frequency_level="common",
            attestation_count=None,  # exact per-name count not extracted from the source at this stage
            citation_note="Zabeleženo u popisu 942 žena/udovica poreskih obveznika, Smederevski sandžak, 1516.",
        ),
        HistoricalAttestationExample(
            source_form="Радосава",
            gender="F",
            source_key=HIST_DEFTER_SMEDEREVO_1516,
            period_start=1516,
            period_end=1516,
            region="Smederevski sandžak",
            name_type="native_slavic",
            historical_confidence="B",
            frequency_level="common",
            attestation_count=None,
            citation_note="Zabeleženo u popisu 942 žena/udovica poreskih obveznika, Smederevski sandžak, 1516.",
        ),
    ]


def _get_or_create_historical_given_name(
    session: Session,
    cache: dict[tuple[str, str, str], int],
    source_form: str,
    source_key: str,
    gender: str,
) -> int:
    """Same pattern as load_all.py's get_or_create_given_name - reused by
    hand rather than imported, since load_all.py's version isn't exposed as
    a shared utility (it's a module-local helper there too). If this
    duplication grows, both should move to a shared src/ingest/common.py.
    """
    cache_key = (source_form, source_key, gender)
    if cache_key in cache:
        return cache[cache_key]

    existing = (
        session.query(GivenName)
        .filter_by(source_form=source_form, source_key=source_key, gender=gender)
        .one_or_none()
    )
    if existing:
        cache[cache_key] = existing.id
        return existing.id

    gn = GivenName(
        source_form=source_form,
        source_key=source_key,
        search_key=make_search_key(source_form),
        gender=gender,
    )
    session.add(gn)
    session.flush()
    cache[cache_key] = gn.id
    return gn.id


def load_historical_seed(session: Session) -> int:
    cache: dict[tuple[str, str, str], int] = {}
    count = 0
    for ex in historical_attestation_examples():
        gn_id = _get_or_create_historical_given_name(session, cache, ex.source_form, ex.source_key, ex.gender)
        existing = (
            session.query(HistoricalNameAttestation)
            .filter_by(given_name_id=gn_id, period_start=ex.period_start, period_end=ex.period_end)
            .one_or_none()
        )
        if existing:
            continue
        session.add(
            HistoricalNameAttestation(
                given_name_id=gn_id,
                period_start=ex.period_start,
                period_end=ex.period_end,
                region=ex.region,
                name_type=ex.name_type,
                historical_confidence=ex.historical_confidence,
                frequency_level=ex.frequency_level,
                attestation_count=ex.attestation_count,
                citation_note=ex.citation_note,
            )
        )
        count += 1
    session.commit()
    return count
