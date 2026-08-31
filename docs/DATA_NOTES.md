# Data Notes

Findings from Phase 0 (§9 of `PROJECT007.md`, formerly §2.1/§9 of the retired
`PROJECT.md`). This file is the single source of truth for what the raw sources
actually contain — do not re-assume anything about them from the spec text
without checking here first, since two spec assumptions were found wrong (noted
below).

**Both branches are resolved.** See §3 and §4.

---

## 1. Download mechanics (applies to every RZS file)

Direct `curl`/`requests` with default headers returns **HTTP 403** on
`stat.gov.rs` media links. Works with a browser `User-Agent` and a `Referer`
pointing at the index page:

```
curl -L -o <out> "<url>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Referer: https://www.stat.gov.rs/sr-latn/oblasti/stanovnistvo/eksel-tabele/"
```

The 2025 filename contains Cyrillic characters and must be percent-encoded
(`нај...` → `%D0%BD%D0%B0%D1%98...`) — do not hand-retype it, generate the
encoding programmatically from the literal UTF-8 filename in §3.2 of
`PROJECT007.md`.

All 5 newborn XLSX files (2021–2025) and the census PDF are downloaded and
saved under `data/raw/`:

```
data/raw/najcesca-imеna-dece-rodjene-u-2021-godini.xlsx   (note: Cyrillic е, per spec warning)
data/raw/najcesca-imena-dece-rodjene-u-2022-godini.xlsx
data/raw/najcescaimenadece2023.xlsx
data/raw/najcesca-imena-dece-rodjene-u-2024-godini.xlsx
data/raw/najcesca-imena-dece-rodjene-u-2025-godini.xlsx
data/raw/census2022_names.pdf                              (G20244001.pdf, 244 pages)
```

---

## 2. XLSX checklist (§9.1) — all 5 years, 2021–2025

All five files share **one identical structure**. Checked programmatically with
`openpyxl` (numeric-cell scan, string/script scan, group-boundary scan) — not
eyeballed.

| Check | Answer |
|---|---|
| Sheet names/count | One sheet each. `'Коначно'` (2021–2023), `'Коначно 2024'`, `'Коначно 2025'` — name drifts, don't hardcode |
| Column headers | No real headers. Row 1 = title, row 2 = `Девојчице` / `Дечаци` in cols B/C |
| **Count column?** | **No. Rank only, all 5 years.** 0 numeric cells found in any file, in any column. → **BRANCH A = ranks only** |
| Max rank published | 10 (10 rows per group, always) |
| Gender layout | Two columns side by side (B = girls, C = boys), not separate sheets |
| Geography | District (`oblast`) level, plus Republic, macro-region (north/south), and NUTS-2 region rollups. **No municipality level.** 32 geography groups per year (list below), identical across all 5 years |
| Tied ranks | None observed — no duplicate name within any single group's B or C column, any year |
| Script | **Cyrillic**, 100% of string cells, no exceptions, any year |
| Diacritics/digraphs | N/A at this stage — Cyrillic doesn't have the Latin digraph problem; see §4 |
| **Variant spellings?** | **Yes — found.** `Михајло` (60+ occurrences) vs `Михаило` (2 occurrences, in 2022 and 2023, different districts) coexist as distinct strings within the *same* source/year. → **BRANCH B = variants listed separately** |
| Layout consistent 2021→2025? | Structurally yes (same 32 groups, same 10-per-group, same title/header pattern). Sheet dimensions vary (`max_col` ranges from 3 to 8) only because of trailing empty columns — cosmetic, not structural |

### 2.1 The 32 geography groups (identical every year, in file order)

```
РЕПУБЛИКА СРБИЈА                    Republic
СРБИЈА - СЕВЕР                      macro-region: North
  Београдски регион                 NUTS-2 region
    Београдска област (Град Београд)  only "oblast" under this region = City of Belgrade
  Регион Војводине                  NUTS-2 region
    Западнобачка област             (note: trailing space in source string, every year — strip when matching)
    Јужнобанатска област
    Јужнобачка област
    Севернобанатска област
    Севернобачка област
    Средњобанатска област
    Сремска област
СРБИЈА - ЈУГ                        macro-region: South
  Регион Шумадије и Западне Србије  NUTS-2 region
    Златиборска област
    Колубарска област
    Мачванска област
    Моравичка област
    Поморавска област
    Расинска област
    Рашка област
    Шумадијска област
  Регион Јужне и Источне Србије     NUTS-2 region
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

Each group = 10 rows (rank 1–10, purely positional — no explicit rank number
column, no explicit count column). A blank row separates groups. Column A
repeats the group label on every one of its 10 rows (not blank after the
header row).

**This is coarser than the census PDF**, which goes to municipality. The finest
grain in the newborn XLSX files is `oblast` (district) — same level as
`district` in the §6.3 schema, never `municipality`.

### 2.2 Row-level anomaly found (2021 only)

`Пиротска област`, rows 319–320 (boys' rank 9 and 10): the cell contains
`'Алекса николић'` and `'Андреј ћирић'` — a first name **and surname**, lowercase
second word, instead of a bare first name. This is a data-entry error in the
source file (only in 2021; 2022–2025 do not repeat it in the same cells; not
checked exhaustively for other cells of this kind — the loader's validation
pass should scan for any B/C cell containing a space and flag it, not silently
strip the second token). Per the "never fill gaps" rule (§11.2 of
`PROJECT007.md`), the loader stores this cell's `source_form` verbatim and lets
the reviewer surface it as a finding — it is not the loader's job to guess
whether "николић"/"ћирић" was meant as a surname to discard.

---

## 3. BRANCH A — resolved: **ranks only, no counts**

Confirmed independently across all 5 newborn XLSX files (zero numeric cells,
any year) and the census PDF Tables 1–5 (see §4 below — the only numbers found
near Tables 4–5 are the printed rank ordinals 1–20 and page footers, not counts
or approximations).

**This also corrects `PROJECT007.md` §3.1, Table row for T4/T5**, which states
counts are `Yes, approximate` (citing `Jovanović ~130,000`, `Dragan Jovanović
>2,200`, etc.). Those figures do not appear anywhere in the actual PDF
publication (`G20244001.pdf`) — they must have come from the RZS press-release
landing page text, a different document from the tabulated PDF. **Treat T4 and
T5 as rank-only, exactly like T1–T3**, until/unless someone finds those
approximate counts in a citable RZS source and records it here. `surname.
approx_count` and `name_surname_combo.approx_count` stay `NULL` from this
source; the §3.4 RZS request is the only path to real counts anywhere in this
project.

**Consequence for the whole app:** it is a rank explorer end-to-end, as
`PROJECT007.md` §1–§2 already assumes. No schema change needed — the `count` /
`approx_count` columns already default to nullable.

---

## 4. Census PDF checklist (§9.2) — sample inspected: national tables + representative districts

Downloaded `G20244001.pdf`, 244 pages, extracted via `pdfplumber`. Inspected:
front matter, table of contents, Table 1 (female names) republic + first
several municipalities (Belgrade opštine), Table 2 (male names) same, Table 3
(single birth year, republic-only) both genders in full (1940–2022), Table 4
(surnames) republic through district level for most regions, Table 5 (name+surname
combos, top 20 each gender).

| Check | Answer |
|---|---|
| Exact cohort labels | `1940. и раније`, then single years `1941`–`2022` in **Table 3**; but **Table 1/2 use 9 cohort buckets**, not 11: `1940. и раније`, `1941–1950`, `1951–1960`, `1961–1970`, `1971–1980`, `1981–1990`, `1991–2000`, `2001–2010`, `2011–2022`. **Corrects `PROJECT007.md`/old `PROJECT.md`, which say "11 cohorts" — it's 9.** |
| Ranks I–V / VI–X split across facing pages | **Confirmed**, but the layout is more specific than "same columns, other page": the left-hand page has cohort/year label in the leftmost column then ranks I–V left-to-right; the right-hand page has ranks VI–X left-to-right **then** the cohort/year label in the rightmost column (label position flips side). Bounding boxes must account for this, not assume a mirrored copy of the left page |
| Digraph corruption (`LJiljana`) | **Does not occur.** The whole publication is printed in **Cyrillic** (`Љиљана`, `Ђорђевић`), not a Latin transliteration. §11.2 hazard #2 of `PROJECT007.md` (and §5.2.2 of the old `PROJECT.md`) describes a Latin-transliteration artifact that **does not apply to this source** — there is no Latin form to corrupt. Drop that hazard from the parser design; add "Cyrillic throughout, no transliteration" as the actual fact. (A Cyrillic→Latin transliteration step is still needed downstream for `search_key`/display, same as for the XLSX files, but it's a clean 1:1 script mapping, not a corrupted-input recovery problem.) |
| Diacritics survive | Yes — `š č ć ž đ`-equivalent Cyrillic letters (`ш ч ћ ж ђ`) extract cleanly, no mojibake observed in any sampled page |
| Belgrade handling | City municipalities (`Барајево`, `Вождовац`, `Врачар`, ... `Чукарица`) appear **separately**, each as its own row/block under `Београдска област (Град Београд)`, which itself also appears as one aggregate rollup row. Both levels present — decide in the loader which one feeds `census_rank.municipality_id` (the 17 opštine, most likely) vs which is a display-only aggregate |
| Municipality count | Not yet counted exactly — sample confirms the region → oblast → grad/opština nesting matches the TOC (pages 7–11) which lists every municipality by name. Get the exact count from the RZS spatial register (§3.3) at schema-build time, not by counting TOC lines by hand |
| Tied ranks | None observed in any sampled table (T1, T2, T3, T4, T5) |
| **Table 3 granularity** | Confirmed **Republic-only**, single birth year 1940–2022, both genders, ranks I–X, same facing-page split as T1/T2. No sub-Republic geography, as `PROJECT007.md` already assumes |
| **Table 4 granularity** | **Goes to municipality level**, not "Republic" as stated in `PROJECT007.md` §3.1's table row for T4 ("Republic"). Confirmed: page 228 onward lists surnames per opština (`Барајево`, `Вождовац`, ... down to `Куршумлија`), same region→oblast→opština nesting as T1/T2. **Corrects the spec** — T4 is as granular as T1/T2, just without counts |
| **Table 5 granularity** | Republic-only, top 20 (not top 10) combinations per gender, confirmed on page 241. Numbers present are only the printed ordinals `1.`–`20.`, nothing else — see §3 above |
| Kosovo and Metohija | Explicitly excluded — census "није спроведен на територији АП Косово и Метохија" (preface, page 5/103). Table 4's region row for it literally prints `...` placeholders (page 239) instead of names. The loader must treat this region as `not_applicable`, never `not_observed` |

### 4.1 Known-facts fixture reproduction — verified against the actual PDF, not just the landing page

All of §3.1's "known facts" in `PROJECT007.md` were re-checked directly against
table pages (not just the RZS press-release text they were originally sourced
from):

- Female name-by-birth-year progression (Table 3, page 222/224): **matches
  exactly** — `Радмила` (to 1943) → `Слободанка` (1944–45) → `Мирјана`
  (1946–48) → `Љиљана` (1949–59) → `Снежана`/`Весна` alternation (1960–68) →
  `Биљана` (1971–73) → `Данијела` (1974–75) → `Јелена` (1976–94) → `Милица`
  (1995–2011) → `Лена` (2012) → `Дуња` (2013–15, 2016 anomaly aside) → `Софија`
  (2016, 2017-2021 area) — confirmed cell-by-cell on the extracted rows, matches
  the spec's summary.
- Male name-by-birth-year (Table 3, page 223/225): **matches** the general
  shape described informally elsewhere — `Милан`→`Слободан`→`Драган`→`Зоран`→
  `Горан`→`Дејан`→`Александар`→`Милош`→`Никола`→`Лука` progression, ending
  2022 with `Лука Лазар Василије Богдан Вук`.
- Table 5 top 2: `1. Јелена Јовановић`, `1. Драган Јовановић` — **exact match**
  to the spec fixture, confirmed on page 241, with no count attached (see §3).

**Use the raw extracted page text captured during this session as the actual
parser test fixture source** (re-extractable any time via `pdfplumber`, page
numbers cited above), not just the landing-page prose — the PDF is now the
verified ground truth.

### 4.2 `extract_text()` is not reliable for structured extraction

Confirms `PROJECT007.md` §11.2's instruction to use `pdfplumber` with explicit
bounding boxes rather than automatic table/text detection: on the cover-style
pages (1, 244) and some table-header rows, `extract_text()` visibly interleaves
text from overlapping layout boxes (e.g. page 14 header renders as
`"Табела 1. НајчешПоћпаи сж сетнаснкоавн иимшетвнаа..."` — two overlapping
strings shuffled character-by-character). This is a layout/z-order artifact,
not a font-encoding problem — don't mistake it for the diacritics hazard.
Bounding-box extraction per column, as already planned, avoids it.

---

## 5. BRANCH B — resolved: **source lists variant spellings separately**

Confirmed twice, independently:

1. **Newborn XLSX**, §2 above: `Михајло` vs `Михаило` appear as distinct
   strings in the same year's data (2022, 2023), in different districts, never
   merged.
2. No merging logic or footnote anywhere in the census PDF suggesting variant
   consolidation — every name form found is used exactly as printed.

Per `PROJECT007.md` §9.5: this means `given_name` gets **one row per distinct
source string**, and `name_cluster`/`name_cluster_member` exist to group
`Михајло`/`Михаило`-type variants for search and display only — per §6.2 of
the spec, **never summed**. The §7.2 split-name UI state is a routine
occurrence (not a rare edge case) and must ship in Phase 1, exactly as the spec
already requires.

`decided_by` for a `Михајло`/`Михаило` cluster should be `'manual'` (they are
not related by the digraph-normalization rule — it's a genuine alternate
spelling, i-vs-j), with a `decision_note` explaining the basis (phonetic
equivalence, one is likely a transcription variant of the other) — this is a
judgment call for whoever curates clusters, not something the loader decides
automatically. **Do not auto-cluster by edit distance** — that risks merging
genuinely different names (e.g. `Јована` vs `Јана` are both in the observed
name list and are different names, not variants).

---

## 6a. Phase 1 finding: Table 3 publishes ranks I–V only, not I–X (2026-08-31)

Found while writing `src/ingest/pdf_parser.py` — not caught during Phase 0's
sampling, which only looked at pages 222–223 and didn't check whether a VI–X
continuation existed. It doesn't: **Table 3 is exactly 4 pages** —
222 (female I–V, years 1940–1981), 223 (male I–V, 1940–1981), 224 (female I–V
continued, 1982–2022), 225 (male I–V continued, 1982–2022). Every page in the
215–228 range was checked programmatically for a `"VI VII VIII IX X"` header;
it never appears. Page 228 is already Table 4.

This differs from T1/T2/T4, which all go to rank X. **`census_rank_by_year`
will only ever have ranks 1–5 populated** for this source — not a bug, a
property of what RZS chose to publish for the by-year breakdown. No schema
change needed (§6.5's `census_rank_by_year.rank` has no 1–10 CHECK constraint,
unlike `census_rank.rank`).

Parser output verified against the §3.1 known-facts fixtures: 830 rows total
(83 years × 2 genders × 5 ranks, exactly, no gaps), 2022 female top 5 =
Софија/Мила/Дуња/Теодора/Сара, 2022 male top 5 = Лука/Лазар/Василије/Богдан/Вук,
`1940. и раније` both genders match the fixture list exactly.

## 6. Open items carried forward (update `PROJECT007.md` §9 checklist status)

All §9.1 and §9.2 checklist items are now answered above. Remaining
non-blocking follow-ups:

1. **Exact municipality count** — not yet cross-checked against the RZS
   spatial register (§3.3); do this when building the `municipality` seed data,
   not before.
2. **Belgrade municipality vs. aggregate** — both levels exist in the source;
   decide which feeds `census_rank` before writing the T1/T2 parser (see §4
   table above).
3. **2021 XLSX row anomaly** (§2.2) — confirm during ingestion whether any
   other year/cell has a similar "name + lowercase surname" data-entry error;
   the loader's validator should generically flag any name cell containing
   whitespace rather than special-casing this one instance.
4. **RZS custom-tabulation request (§3.4 of `PROJECT007.md`)** — not yet sent.
   Send in parallel with Phase 1 build, per the spec; do not block on a reply.
