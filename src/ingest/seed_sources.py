"""data_source seed rows for everything Phase 1 (Step 1 of §10) loads.

Every given_name/census_rank_by_year/newborn_name row must resolve its
source_key to one of these (PROJECT.md §11.3 validation invariant).
"""

from datetime import date

from src.db.models import DataSource

RETRIEVED_AT = date(2026, 8, 31)

CENSUS_T3_KEY = "census_2022_t3"

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
            key=CENSUS_T3_KEY,
            title="Najčešća imena i prezimena — Tabela 3 (najčešća imena po godini rođenja)",
            url="https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf",
            table_ref="Tabela 3",
            scope="republic x birth_year",
            measure="rank",
            retrieved_at=RETRIEVED_AT,
            notes="Ranks I-V only (top 5), not I-X. See docs/DATA_NOTES.md §6a.",
        )
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
    return rows
