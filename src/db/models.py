"""SQLAlchemy models — mirrors PROJECT.md §6 exactly.

One deliberate addition beyond the spec: `newborn_name.district_id` (nullable).
The spec's §6.5 newborn_name has no geography column (implicitly Republic-only),
but Phase 0 (docs/DATA_NOTES.md §2) found the source XLSX files carry 32
geography groups (Republic, macro-region, NUTS-2 region, and district/oblast).
NULL district_id = the Republic-level row; populated = a district-level row.
This follows the same "nullable column, no migration needed later" pattern the
spec already uses for every `count` column.
"""

from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------- provenance ----------


class DataSource(Base):
    __tablename__ = "data_source"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    table_ref: Mapped[str | None] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    measure: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_at: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


# ---------- name identity ----------


class GivenName(Base):
    __tablename__ = "given_name"
    __table_args__ = (
        UniqueConstraint("source_form", "source_key", "gender"),
        CheckConstraint("gender IN ('M','F')", name="ck_given_name_gender"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_form: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(ForeignKey("data_source.key"), nullable=False)
    search_key: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)


class NameCluster(Base):
    __tablename__ = "name_cluster"
    __table_args__ = (
        UniqueConstraint("canonical", "gender"),
        CheckConstraint("gender IN ('M','F')", name="ck_name_cluster_gender"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical: Mapped[str] = mapped_column(Text, nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)


class NameClusterMember(Base):
    __tablename__ = "name_cluster_member"
    __table_args__ = (
        CheckConstraint(
            "decided_by IN ('exact_match','digraph_normalization','manual')",
            name="ck_cluster_member_decided_by",
        ),
    )

    cluster_id: Mapped[int] = mapped_column(ForeignKey("name_cluster.id"), primary_key=True)
    given_name_id: Mapped[int] = mapped_column(ForeignKey("given_name.id"), primary_key=True)
    decided_by: Mapped[str] = mapped_column(Text, nullable=False)
    decision_note: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[date] = mapped_column(Date, nullable=False)


# ---------- geography ----------


class Region(Base):
    __tablename__ = "region"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class District(Base):
    __tablename__ = "district"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("region.id"))


class Municipality(Base):
    __tablename__ = "municipality"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code_rzs: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_slug: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    district_id: Mapped[int | None] = mapped_column(ForeignKey("district.id"))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)


# ---------- cohorts ----------


class Cohort(Base):
    __tablename__ = "cohort"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    year_from: Mapped[int | None] = mapped_column(Integer)
    year_to: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


# ---------- observations ----------


class CensusRank(Base):
    __tablename__ = "census_rank"
    __table_args__ = (
        UniqueConstraint("municipality_id", "cohort_id", "gender", "given_name_id"),
        CheckConstraint("gender IN ('M','F')", name="ck_census_rank_gender"),
        CheckConstraint("rank BETWEEN 1 AND 10", name="ck_census_rank_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    given_name_id: Mapped[int] = mapped_column(ForeignKey("given_name.id"), nullable=False, index=True)
    # Nullable, deliberately - beyond PROJECT.md §6.5's original NOT NULL.
    # NULL = the Republic-level row for that cohort/gender (T1/T2 print a
    # national top-10 per cohort alongside every municipality's; §7.4 needs
    # it for the municipality-vs-national comparison column). Populated =
    # a real municipality. Same "nullable column absorbs a source dimension
    # the original schema had no slot for" pattern already used for
    # newborn_name.district_id.
    municipality_id: Mapped[int | None] = mapped_column(ForeignKey("municipality.id"), index=True)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohort.id"), nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    count: Mapped[int | None] = mapped_column(Integer)


class CensusRankByYear(Base):
    __tablename__ = "census_rank_by_year"
    __table_args__ = (
        UniqueConstraint("birth_year", "gender", "given_name_id"),
        CheckConstraint("gender IN ('M','F')", name="ck_census_rank_by_year_gender"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    given_name_id: Mapped[int] = mapped_column(ForeignKey("given_name.id"), nullable=False, index=True)
    birth_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    count: Mapped[int | None] = mapped_column(Integer)


class NewbornName(Base):
    __tablename__ = "newborn_name"
    __table_args__ = (
        UniqueConstraint("year", "gender", "given_name_id", "district_id"),
        CheckConstraint("gender IN ('M','F')", name="ck_newborn_name_gender"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    given_name_id: Mapped[int] = mapped_column(ForeignKey("given_name.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    rank: Mapped[int | None] = mapped_column(SmallInteger)
    count: Mapped[int | None] = mapped_column(Integer)  # BRANCH A resolved: stays NULL
    # Nullable: NULL = Republic-level row, populated = district-level row.
    # See module docstring — addition beyond spec §6.5 to fit the Phase 0 finding.
    district_id: Mapped[int | None] = mapped_column(ForeignKey("district.id"), index=True)


class Surname(Base):
    __tablename__ = "surname"
    __table_args__ = (UniqueConstraint("surname", "source_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surname: Mapped[str] = mapped_column(Text, nullable=False)
    source_key: Mapped[str] = mapped_column(ForeignKey("data_source.key"), nullable=False)
    search_key: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    approx_count: Mapped[int | None] = mapped_column(Integer)


class NameSurnameCombo(Base):
    __tablename__ = "name_surname_combo"
    __table_args__ = (
        UniqueConstraint("given_name_id", "surname_id"),
        CheckConstraint("gender IN ('M','F')", name="ck_combo_gender"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    given_name_id: Mapped[int] = mapped_column(ForeignKey("given_name.id"), nullable=False)
    surname_id: Mapped[int] = mapped_column(ForeignKey("surname.id"), nullable=False)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)
    rank: Mapped[int | None] = mapped_column(SmallInteger)
    approx_count: Mapped[int | None] = mapped_column(Integer)
