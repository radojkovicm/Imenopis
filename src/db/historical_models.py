"""Historical layer models — mirrors PROJECT.md §16.4 exactly.

Kept in a separate module from models.py deliberately: models.py's own
docstring says it "mirrors PROJECT.md §6 exactly", and keeping the
historical layer (§16) in its own file lets that claim stay literally true
for both modules rather than interleaving two different specs' tables.

Historical sources are NOT a new top-level table - they are rows in the
existing `data_source` table (§6.6) with measure='attestation'.
HistoricalSourceMeta below is a 1:1 extension of one of those rows, carrying
fields (author, publication_year, source_type, citation) that data_source
has no slot for. given_name rows for historical name forms use the
existing source_key column unchanged (§16.4) - no schema change to
given_name at all, so /api/suggest and search_key indexing work on
historical names for free.

This module must be imported somewhere reachable from src/db/session.py's
init_db() (even if nothing here is referenced directly) so these tables
register on Base.metadata before create_all() runs.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models import Base


class HistoricalSourceMeta(Base):
    __tablename__ = "historical_source_meta"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('charter','monastery_register','ottoman_defter','academic_paper','other')",
            name="ck_historical_source_meta_type",
        ),
    )

    # 1:1 extension of a data_source row - PK is also the FK, not a
    # separate surrogate id, since this table only ever has exactly one
    # row per historical data_source entry.
    data_source_key: Mapped[str] = mapped_column(ForeignKey("data_source.key"), primary_key=True)
    author: Mapped[str | None] = mapped_column(Text)
    publication_year: Mapped[int | None] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    citation: Mapped[str] = mapped_column(Text, nullable=False)


class HistoricalNameAttestation(Base):
    __tablename__ = "historical_name_attestation"
    __table_args__ = (
        CheckConstraint(
            "name_type IN ('native_slavic','christian','noble','folk','other')",
            name="ck_historical_attestation_name_type",
        ),
        CheckConstraint("historical_confidence IN ('A','B','C','D')", name="ck_historical_attestation_confidence"),
        CheckConstraint(
            "frequency_level IN ('dominant','very_common','common','attested','rare','uncertain')",
            name="ck_historical_attestation_frequency",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    given_name_id: Mapped[int] = mapped_column(ForeignKey("given_name.id"), nullable=False, index=True)
    period_start: Mapped[int | None] = mapped_column(Integer)  # year, nullable - century-level precision only
    period_end: Mapped[int | None] = mapped_column(Integer)
    # Free text, the document's own territory - never joined against
    # municipality rows (PROJECT.md §16.3 rule 7: a medieval sandžak is not
    # a modern opština).
    region: Mapped[str | None] = mapped_column(Text)
    name_type: Mapped[str | None] = mapped_column(Text)
    historical_confidence: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    # Categorical, not a numeric rank (§16.2/§16.3 rule 1) - ranking implies
    # a comparable population across candidates, which this corpus can't
    # supply below confidence B.
    frequency_level: Mapped[str | None] = mapped_column(Text)
    attestation_count: Mapped[int | None] = mapped_column(Integer)  # only meaningful with confidence B
    citation_note: Mapped[str] = mapped_column(Text, nullable=False)  # page/folio/entry reference within the source
