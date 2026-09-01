"""Schema-level tests for the §16 historical layer models. Uses a fresh
in-memory SQLite database (not the project's dev database) so CHECK
constraint violations can be tested without touching real data.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db import historical_models  # noqa: F401 - registers tables on Base.metadata
from src.db.historical_models import HistoricalNameAttestation, HistoricalSourceMeta
from src.db.models import Base, DataSource, GivenName


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = Session(engine)
    yield s
    s.close()


def _seed_source_and_name(session: Session) -> int:
    source = DataSource(
        key="test_historical_source",
        title="Test source",
        url="n/a",
        scope="test",
        measure="attestation",
        retrieved_at=date(2026, 1, 1),
    )
    session.add(source)
    session.flush()
    gn = GivenName(source_form="Тест", source_key=source.key, search_key="test", gender="M")
    session.add(gn)
    session.flush()
    return gn.id


def test_valid_confidence_level_accepted(session):
    gn_id = _seed_source_and_name(session)
    session.add(
        HistoricalNameAttestation(
            given_name_id=gn_id,
            historical_confidence="C",
            citation_note="test citation",
        )
    )
    session.commit()  # should not raise


def test_invalid_confidence_level_rejected(session):
    gn_id = _seed_source_and_name(session)
    session.add(
        HistoricalNameAttestation(
            given_name_id=gn_id,
            historical_confidence="Z",  # not in ('A','B','C','D')
            citation_note="test citation",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_name_type_rejected(session):
    gn_id = _seed_source_and_name(session)
    session.add(
        HistoricalNameAttestation(
            given_name_id=gn_id,
            historical_confidence="C",
            name_type="not_a_real_type",
            citation_note="test citation",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_frequency_level_rejected(session):
    gn_id = _seed_source_and_name(session)
    session.add(
        HistoricalNameAttestation(
            given_name_id=gn_id,
            historical_confidence="B",
            frequency_level="extremely_common",  # not in the allowed set
            citation_note="test citation",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_citation_note_is_required():
    # citation_note has no server default and is NOT NULL - §16.3 rule 5:
    # every historical row must cite a source. Constructing the ORM object
    # without it and flushing should fail.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        gn_id = _seed_source_and_name(session)
        session.add(HistoricalNameAttestation(given_name_id=gn_id, historical_confidence="C", citation_note=None))
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()


def test_invalid_source_type_rejected():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        source = DataSource(
            key="bad_source",
            title="Bad source",
            url="n/a",
            scope="test",
            measure="attestation",
            retrieved_at=date(2026, 1, 1),
        )
        session.add(source)
        session.flush()
        session.add(
            HistoricalSourceMeta(
                data_source_key=source.key,
                source_type="not_a_real_source_type",
                citation="test",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()


def test_name_cluster_member_accepts_historical_variant():
    from src.db.models import NameCluster, NameClusterMember

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        gn_id = _seed_source_and_name(session)
        cluster = NameCluster(canonical="Тест", gender="M")
        session.add(cluster)
        session.flush()
        session.add(
            NameClusterMember(
                cluster_id=cluster.id,
                given_name_id=gn_id,
                decided_by="historical_variant",  # §16.3 rule 6
                decision_note="test grouping rationale",
                decided_at=date(2026, 1, 1),
            )
        )
        session.commit()  # should not raise
    finally:
        session.close()
