# Data Notes

## Phase 0 finding: `najcescaimenadece2023.xlsx` (2026-08-31)

**Source:** `https://www.stat.gov.rs/media/391794/najcescaimenadece2023.xlsx`
Downloaded successfully via `curl` with a browser `User-Agent` and `Referer` header
(direct `curl` with default headers returns **HTTP 403** — the RZS media server
appears to block requests without those headers; keep both when re-downloading
any file in §3.2 of `PROJECT.md`). Saved to `data/raw/najcescaimenadece2023.xlsx`.

### Answer to the blocking question (§2.1 of PROJECT.md)

**Ranks only — no absolute counts.** Verified programmatically with `openpyxl`:
zero numeric cells anywhere in the sheet, zero non-empty cells in columns D–H.

**Consequence:** the whole app is a rank explorer end-to-end. There is no
count-based layer to build. `newborn_name.count` and every other `count` /
`approx_count` column in the schema stays `NULL` unless the RZS custom-tabulation
request (§3.5) succeeds. Proceed with the rank-only design exactly as described
in the rest of `PROJECT.md`.

### File structure

- One sheet: `Коначно` (Cyrillic, means "Final").
- Dimensions: `A1:H425`. Only columns A (group label), B (girls' name), C
  (boys' name) are ever populated. D–H are entirely empty — not a hidden
  count column, just unused.
- Row 1: title `Најчешћа имена деце рођене  у 2023. години.` (note: double space
  before "у", present in the source, not a typo to fix).
- Row 2: sub-header `Девојчице` / `Дечаци` in columns B/C.
- From row 3 on: **32 groups**, each **exactly 10 rows** (rank 1–10, implied by
  row position — there is no explicit rank number column). A blank row
  separates each group from the next.
- Text is **Cyrillic**, not the Latin transliteration used in the census PDF.
  Needs Cyrillic→Latin transliteration in the loader (standard Serbian digraph
  rules: `Љ`→`Lj`, `Њ`→`Nj`, `Џ`→`Dž`, plus the usual 1:1 letter map). This is a
  *simpler* problem than the census PDF's digraph-corruption issue (§5.2.2 of
  PROJECT.md) because there's no all-caps rendering artifact — just a clean
  script transliteration.

### The 32 groups (geographic granularity) — in file order

```
РЕПУБЛИКА СРБИЈА                    (Republic)
СРБИЈА - СЕВЕР                      (macro-region: North)
  Београдски регион                 (NUTS-2 region)
    Београдска област (Град Београд)  (= City of Belgrade; only "oblast" under this region)
  Регион Војводине                  (NUTS-2 region)
    Западнобачка област
    Јужнобанатска област
    Јужнобачка област
    Севернобанатска област
    Севернобачка област
    Средњобанатска област
    Сремска област
СРБИЈА - ЈУГ                        (macro-region: South)
  Регион Шумадије и Западне Србије  (NUTS-2 region)
    Златиборска област
    Колубарска област
    Мачванска област
    Моравичка област
    Поморавска област
    Расинска област
    Рашка област
    Шумадијска област
  Регион Јужне и Источне Србије     (NUTS-2 region)
    Борска област
    Браничевска област
    Зајечарска област
    Јабланичка област
    Нишавска област
    Пиротска област
    Подунавска област
    Пчињска област
    Топличка област
```

**Important — this is coarser than the census PDF.** No municipality
(`opština`) level here at all; the finest grain is `oblast` (NUTS-3, district),
same level as `district` in the schema (§4 of PROJECT.md), not `municipality`.

**Schema implication:** `newborn_name` as currently designed (§4) has no
geography column — it's implicitly Republic-only. If we want the newborn layer
to also show district-level breakdowns (which this file supports), the table
needs a nullable `district_id` (Republic-level row = `NULL`) or a separate
`newborn_name_district` table. **Open decision — see open question #6 below.**

Also note: `Западнобачка област ` (West Bačka district) has a **trailing space**
in the source label — normalize/strip when matching against the district
reference table, don't rely on exact string equality.

### Row/column layout summary for the loader

| Row range (per group) | Meaning |
|---|---|
| group header row | column A = geography label, B/C empty |
| next 10 rows | column A repeats the same geography label (not blank!); B = girl name rank N (row offset+1..10), C = boy name rank N |

Correction to the naive assumption: column A is **not** blank after the header —
it repeats the full label on every one of the 10 rows (see raw dump: rows 3–12
all show `'РЕПУБЛИКА СРБИЈА'` in column A). Rank number is purely positional
(1st row in group = rank 1, ..., 10th row = rank 10) — there is no explicit
numeral in the sheet. **The loader must derive rank from row position within
the group, and must verify each group has exactly 10 rows before doing so**,
per the §5.3 validation invariants.

### Other year files — not yet checked

2021, 2022, 2024, 2025 XLSX files (§3.2 of PROJECT.md) have not been inspected.
**Assume same 403-without-headers behavior and same rank-only, no-count
structure until each is individually verified** — do not assume identical
sheet name, group list, or column layout without checking; RZS has a track record
of inconsistent filename conventions across years per PROJECT.md §3.2, so the
internal layout may also drift year to year.

### New open question (add to PROJECT.md §10)

6. **Newborn layer geography** — the XLSX gives district-level (`oblast`)
   breakdowns, not just Republic-level. Decide whether `newborn_name` should
   carry a nullable district reference (matching this file's actual
   granularity) instead of being implicitly Republic-only. Affects the Phase 1
   schema and the `/api/newborn/{year}` endpoint shape.
