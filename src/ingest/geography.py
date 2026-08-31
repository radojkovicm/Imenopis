"""Static geography reference data for the newborn XLSX loader.

The 32 group labels are confirmed identical across all 5 years of newborn
XLSX files (docs/DATA_NOTES.md §2.1). This module classifies each label as
either the Republic row, a macro-region rollup (not stored — no schema slot
for it), a NUTS-2 region rollup (not stored either), or an actual district
(oblast) — which does get a district_id.

Only real districts are persisted to `district`/`newborn_name.district_id`.
Republic and region/macro-region rollup rows in the source become the
Republic-level newborn_name row (district_id = NULL) or are dropped as
redundant with sums that can be derived from the district rows — the spec
(§6.5) never asked for rollup storage, and storing them would create a second,
un-auditable path to the same numbers.
"""

REPUBLIC_LABEL = "РЕПУБЛИКА СРБИЈА"

# Labels that are rollups above district level - skipped, not real districts.
ROLLUP_LABELS = {
    "РЕПУБЛИКА СРБИЈА",
    "СРБИЈА - СЕВЕР",
    "СРБИЈА - ЈУГ",
    "Београдски регион",
    "Регион Војводине",
    "Регион Шумадије и Западне Србије",
    "Регион Јужне и Источне Србије",
}

# The 25 actual districts (oblast) found in the newborn XLSX files, mapped to
# a stable code. Codes are our own (RZS spatial-register codes are not yet
# integrated - §3.3 of PROJECT.md - this is a placeholder key good enough to
# join newborn rows to a `district` row until the real register is loaded).
DISTRICT_CODES = {
    "Београдска област (Град Београд)": "beogradska",
    "Западнобачка област": "zapadnobacka",
    "Јужнобанатска област": "juznobanatska",
    "Јужнобачка област": "juznobacka",
    "Севернобанатска област": "severnobanatska",
    "Севернобачка област": "severnobacka",
    "Средњобанатска област": "srednjobanatska",
    "Сремска област": "sremska",
    "Златиборска област": "zlatiborska",
    "Колубарска област": "kolubarska",
    "Мачванска област": "macvanska",
    "Моравичка област": "moravicka",
    "Поморавска област": "pomoravska",
    "Расинска област": "rasinska",
    "Рашка област": "raska",
    "Шумадијска област": "sumadijska",
    "Борска област": "borska",
    "Браничевска област": "branicevska",
    "Зајечарска област": "zajecarska",
    "Јабланичка област": "jablanicka",
    "Нишавска област": "nisavska",
    "Пиротска област": "pirotska",
    "Подунавска област": "podunavska",
    "Пчињска област": "pcinjska",
    "Топличка област": "toplicka",
}


def classify_label(raw_label: str) -> tuple[str, str | None]:
    """Return (kind, district_code). kind is 'republic', 'rollup', or 'district'.

    raw_label may have incidental whitespace (e.g. the trailing space on
    'Западнобачка област ' found in Phase 0) - stripped before lookup.
    """
    label = raw_label.strip()
    if label == REPUBLIC_LABEL:
        return "republic", None
    if label in ROLLUP_LABELS:
        return "rollup", None
    if label in DISTRICT_CODES:
        return "district", DISTRICT_CODES[label]
    raise ValueError(f"Unrecognized geography label: {raw_label!r}")
