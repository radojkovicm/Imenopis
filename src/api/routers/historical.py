"""GET /api/historical/{search_key}, GET /api/historical (PROJECT.md §16).

A separate corpus from /api/name's statistical data (§16.3 rule 4: the two
are never merged into one number or one timeline). Every response uses
HistoricalAttestationValue envelopes, which always carry evidence:"observed"
+ historical_confidence - a level D row is still faithfully reported as
"observed" (we did read it somewhere), but the frontend must gate its own
copy on historical_confidence to satisfy §16.3 rule 2 (D is never rendered
as an attested fact). This API layer's job is to report the confidence
level faithfully, not to enforce the wording rule itself.

No 404 for an unattested name (§12's rule extended to §16): a name with no
historical rows is evidence:"unknown", reason:"no_historical_source_for_period".
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.envelope import HistoricalAttestationValue, Scope, UnknownValue
from src.db.historical_models import HistoricalNameAttestation
from src.db.models import DataSource, GivenName
from src.db.session import get_session
from src.util.normalize import make_search_key

router = APIRouter(prefix="/api/historical", tags=["historical"])


def _session() -> Session:
    return get_session()


def _attestation_dict(a: HistoricalNameAttestation, source: DataSource) -> dict:
    return HistoricalAttestationValue(
        value={
            "period_start": a.period_start,
            "period_end": a.period_end,
            "region": a.region,
            "name_type": a.name_type,
            "frequency_level": a.frequency_level,
            "attestation_count": a.attestation_count,
        },
        source=source.key,
        historical_confidence=a.historical_confidence,
        citation_note=a.citation_note,
        scope=Scope(),
    ).model_dump()


@router.get("")
def list_historical(
    period_start: int | None = None,
    period_end: int | None = None,
    name_type: str | None = None,
    gender: str | None = None,
    session: Session = Depends(_session),
):
    """§16.5's filtered listing for the 'Istorijska imena Srbije' page."""
    query = (
        session.query(HistoricalNameAttestation, GivenName, DataSource)
        .join(GivenName, HistoricalNameAttestation.given_name_id == GivenName.id)
        .join(DataSource, GivenName.source_key == DataSource.key)
        .filter(DataSource.measure == "attestation")
    )
    if gender:
        query = query.filter(GivenName.gender == gender)
    if name_type:
        query = query.filter(HistoricalNameAttestation.name_type == name_type)
    if period_start is not None:
        query = query.filter(
            (HistoricalNameAttestation.period_end.is_(None)) | (HistoricalNameAttestation.period_end >= period_start)
        )
    if period_end is not None:
        query = query.filter(
            (HistoricalNameAttestation.period_start.is_(None))
            | (HistoricalNameAttestation.period_start <= period_end)
        )

    results = []
    for a, g, source in query.order_by(GivenName.source_form).all():
        results.append(
            {
                "source_form": g.source_form,
                "gender": g.gender,
                "search_key": g.search_key,
                "attestation": _attestation_dict(a, source),
            }
        )
    return {"results": results}


@router.get("/{search_key}")
def get_historical(search_key: str, gender: str | None = None, session: Session = Depends(_session)):
    key = make_search_key(search_key)
    query = (
        session.query(GivenName)
        .join(DataSource, GivenName.source_key == DataSource.key)
        .filter(GivenName.search_key == key, DataSource.measure == "attestation")
    )
    if gender:
        query = query.filter(GivenName.gender == gender)
    matches = query.all()

    if not matches:
        return {
            "search_key": key,
            "matches": [],
            "result": UnknownValue(reason="no_historical_source_for_period").model_dump(),
        }

    # Group by (source_form, gender), same convention as /api/name (§7.2) -
    # different historical_source rows for the same spelling are multiple
    # attestations of one block, not separate spelling variants.
    groups: dict[tuple[str, str], list[GivenName]] = {}
    for gn in matches:
        groups.setdefault((gn.source_form, gn.gender), []).append(gn)

    blocks = []
    for (source_form, gender_val), gn_rows in groups.items():
        attestations = []
        for gn in gn_rows:
            source = session.get(DataSource, gn.source_key)
            rows = session.query(HistoricalNameAttestation).filter_by(given_name_id=gn.id).all()
            for a in rows:
                attestations.append(_attestation_dict(a, source))
        attestations.sort(key=lambda x: (x["value"]["period_start"] or 0))
        blocks.append(
            {
                "source_form": source_form,
                "gender": gender_val,
                "attestations": attestations,
            }
        )

    distinct_forms = sorted({b["source_form"] for b in blocks})
    split_notice = None
    if len(distinct_forms) > 1:
        split_notice = (
            f"Izvor vodi {len(distinct_forms)} odvojena zapisa za ovo ime: "
            f"{', '.join(distinct_forms)}. Prikazujemo ih odvojeno jer ih "
            "istorijski izvori ne spajaju."
        )

    return {"search_key": key, "matches": blocks, "split_notice": split_notice}
