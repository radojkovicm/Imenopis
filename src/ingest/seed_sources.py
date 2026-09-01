"""data_source seed rows for everything Phase 1 (Step 1 of §10) loads, plus
the §16 historical-layer sources (measure='attestation').

Every given_name/census_rank_by_year/newborn_name row must resolve its
source_key to one of these (PROJECT.md §11.3 validation invariant). Same
requirement applies to historical given_name rows - see
src/ingest/historical_seed.py.
"""

from datetime import date

from src.db.historical_models import HistoricalSourceMeta
from src.db.models import DataSource

RETRIEVED_AT = date(2026, 8, 31)

CENSUS_T1_KEY = "census_2022_t1"
CENSUS_T2_KEY = "census_2022_t2"
CENSUS_T3_KEY = "census_2022_t3"

# §16 historical sources. Two rows for the 1516 census deliberately: the
# defter itself (the primary document) and the modern scholarly analysis of
# it (a secondary source with its own citation and confidence basis) are
# not interchangeable - PROJECT.md §16 requires every attestation cite a
# specific, checkable source, and "the defter" vs "a paper analyzing the
# defter" are different sources even when describing the same underlying
# document.
HIST_POVELJA_DUSAN_1348 = "povelja_dusan_1348"
HIST_DEFTER_SMEDEREVO_1516 = "defter_smederevo_1516"
HIST_ANALIZA_1516 = "analiza_jovanovic_katic_jakovljevic_1516"

NEWBORN_KEYS = {
    2021: "newborn_2021",
    2022: "newborn_2022",
    2023: "newborn_2023",
    2024: "newborn_2024",
    2025: "newborn_2025",
}

NEWBORN_URLS = {
    2021: "https://www.stat.gov.rs/media/358213/najcesca-imеna-dece-rodjene-u-2021-godini.xlsx",
    2022: "https://www.stat.gov.rs/media/358665/najcesca-imena-dece-rodjene-u-2022-godini.xlsx",
    2023: "https://www.stat.gov.rs/media/391794/najcescaimenadece2023.xlsx",
    2024: "https://www.stat.gov.rs/media/405440/najcesca-imena-dece-rodjene-u-2024-godini.xlsx",
    2025: "https://www.stat.gov.rs/media/419659/najčešća-imena-dece-rođene-u-republici-srbiji-u-2025-godini-godini.xlsx",
}


def seed_rows() -> list[DataSource]:
    rows = [
        DataSource(
            key=CENSUS_T1_KEY,
            title="Najčešća imena i prezimena — Tabela 1 (najčešća ženska imena po opštinama)",
            url="https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf",
            table_ref="Tabela 1",
            scope="municipality x cohort x gender(F)",
            measure="rank",
            retrieved_at=RETRIEVED_AT,
            notes="9 cohorts (not 11). See docs/DATA_NOTES.md §4, §7.",
        ),
        DataSource(
            key=CENSUS_T2_KEY,
            title="Najčešća imena i prezimena — Tabela 2 (najčešća muška imena po opštinama)",
            url="https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf",
            table_ref="Tabela 2",
            scope="municipality x cohort x gender(M)",
            measure="rank",
            retrieved_at=RETRIEVED_AT,
            notes="9 cohorts (not 11). See docs/DATA_NOTES.md §4, §7.",
        ),
        DataSource(
            key=CENSUS_T3_KEY,
            title="Najčešća imena i prezimena — Tabela 3 (najčešća imena po godini rođenja)",
            url="https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf",
            table_ref="Tabela 3",
            scope="republic x birth_year",
            measure="rank",
            retrieved_at=RETRIEVED_AT,
            notes="Ranks I-V only (top 5), not I-X. See docs/DATA_NOTES.md §6a.",
        ),
    ]
    for year, key in NEWBORN_KEYS.items():
        rows.append(
            DataSource(
                key=key,
                title=f"Najčešća imena dece rođene u {year}. godini",
                url=NEWBORN_URLS[year],
                table_ref="Коначно" if year != 2024 and year != 2025 else f"Коначно {year}",
                scope="district x gender (+ republic rollup)",
                measure="rank",
                retrieved_at=RETRIEVED_AT,
                notes=None,
            )
        )
    rows.extend(historical_data_source_rows())
    return rows


def historical_data_source_rows() -> list[DataSource]:
    """§16 historical sources, as data_source rows with measure='attestation'
    (§16.4 - historical sources deliberately reuse this table rather than a
    parallel one, so given_name.source_key needs no schema change).
    """
    return [
        DataSource(
            key=HIST_POVELJA_DUSAN_1348,
            title="Povelja cara Dušana (1348)",
            url="izvor nije digitalno dostupan - fizički arhivski/publikacioni izvor",
            table_ref=None,
            scope="charter, single document",
            measure="attestation",
            retrieved_at=RETRIEVED_AT,
            notes="Proof-of-concept seed row for the §16 historical layer schema - not a full corpus.",
        ),
        DataSource(
            key=HIST_DEFTER_SMEDEREVO_1516,
            title="Osmanski popisni defter Smederevskog sandžaka (1516)",
            url="izvor nije digitalno dostupan - fizički arhivski/publikacioni izvor",
            table_ref=None,
            scope="Ottoman tax census, Smederevo sanjak, 942 recorded women/widows",
            measure="attestation",
            retrieved_at=RETRIEVED_AT,
            notes="Primary document. See HIST_ANALIZA_1516 for the modern scholarly analysis of it - cited separately, per module docstring.",
        ),
        DataSource(
            key=HIST_ANALIZA_1516,
            title="Analiza ženskih imena iz popisa Smederevskog sandžaka 1516. godine",
            url="izvor nije digitalno dostupan - fizički arhivski/publikacioni izvor",
            table_ref=None,
            scope="scholarly analysis of the 1516 defter's 942 female names",
            measure="attestation",
            retrieved_at=RETRIEVED_AT,
            notes="Author/publication_year/citation in historical_source_meta - see historical_source_meta_rows().",
        ),
    ]


def historical_source_meta_rows() -> list[HistoricalSourceMeta]:
    """1:1 extension of the historical_data_source_rows() entries - author,
    publication_year, source_type, citation (fields data_source has no slot
    for). Citation details here are exactly what the site owner provided;
    do not add page numbers, ISBNs, or journal names that weren't given.
    """
    return [
        HistoricalSourceMeta(
            data_source_key=HIST_POVELJA_DUSAN_1348,
            author=None,
            publication_year=None,
            source_type="charter",
            citation="Povelja cara Dušana, 1348.",
        ),
        HistoricalSourceMeta(
            data_source_key=HIST_DEFTER_SMEDEREVO_1516,
            author=None,
            publication_year=1516,
            source_type="ottoman_defter",
            citation="Osmanski popisni defter Smederevskog sandžaka, 1516.",
        ),
        HistoricalSourceMeta(
            data_source_key=HIST_ANALIZA_1516,
            author="Gordana M. Jovanović, Srđan Katić, Aleksandar Jakovljević",
            publication_year=None,
            source_type="academic_paper",
            citation=(
                "Gordana M. Jovanović, Srđan Katić, Aleksandar Jakovljević — "
                "analiza ženskih imena (942 žene/udovice poreskih obveznika) "
                "iz osmanskog popisa Smederevskog sandžaka, 1516."
            ),
        ),
    ]
