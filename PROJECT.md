# Project: `kakosezoves` — Serbian Name Statistics Explorer

> Working name. Alternative: `imena-rs`. Domain idea: `kakosezoves.rs` (mirrors the
> Slovenian app's framing "Kako se imenujete?").

**Goal:** a public web app where a user types a first name (e.g. `Goran`) and sees
where that name ranks across Serbian municipalities and birth cohorts — the closest
achievable equivalent to Slovenia's `stat.si/imenarojstva`, given that Serbian
official statistics publish **ranks, not absolute counts**, for first names.

**Stack (fixed):** Python 3.11+ / FastAPI / SQLAlchemy / Pydantic, PostgreSQL,
vanilla JS frontend (no framework). Dev on Windows in VS Code, production on a
Linux VPS behind Docker.

---

## 1. Reference implementation: what the Slovenian app does

Source: <https://www.stat.si/imenarojstva> (SURS — Statistical Office of Slovenia).
The site blocks automated fetching, so the feature list below is assembled from
SURS press releases and the app's own visible text. **Verify by hand before
copying any UX decision.**

### 1.1 Data foundation

- Backed by the **Central Population Register**, refreshed **annually** (current
  release: 1 January 2026, population 2,135,107).
- Publishes **absolute frequencies per name**, not ranks.
- Coverage is total: Slovenia has ~64,000 distinct first names and ~143,000
  distinct surnames; ~71% of names are unique to a single person.
- **Statistical confidentiality:** names/surnames held by fewer than 5 residents
  are not displayed at all. Breakdowns by statistical region and birth period are
  additionally protected using the *missing values* method (individual cells
  suppressed).

### 1.2 Features

| # | Feature | Notes |
|---|---------|-------|
| 1 | Search by **first name** | With gender selection. Returns count, rank, share. |
| 2 | Search by **surname** | Returns count. |
| 3 | Search by **name + surname combination** | Both fields; at least one required. |
| 4 | Search by **birth date** | "How many residents share your birthday." Not available for dates before a cutoff. |
| 5 | Breakdown by **statistical region** | NUTS-3, 12 regions. |
| 6 | Breakdown by **birth period** | Decade-style buckets. |
| 7 | **Autocomplete** while typing | Suggests names and surnames mid-entry. |
| 8 | **Compare two names** side by side | Added in the 2019 redesign. |
| 9 | Curated editorial sections | "Most frequent names", "Newborn names", "Disappearing names", "Modern names", "Most frequent surnames". |
| 10 | Interactive visualisations | Charts and infographics per name. |

### 1.3 Croatian equivalent (second reference)

<https://web.dzs.hr/app/imena/default.aspx> (DZS — Croatian Bureau of Statistics).
Same idea, census-based rather than register-based. Search by name, surname, or
combination. Suppression threshold is **fewer than 10** persons. Worth opening for
UI ideas — it is a simpler, older implementation than the Slovenian one.

---

## 2. Data reality for Serbia — read this before designing anything

**There is no Serbian dataset with absolute counts per first name.** This has been
checked across: the RZS census publication, the RZS open data portal
(`opendata.stat.gov.rs/odata`, 731 datasets, 23 categories — no names dataset
found), the national open data portal, and GitHub. Absence of a search hit is not
proof of non-existence, but nothing surfaced.

What this means concretely:

- ✅ We CAN answer: *"Where did the name Goran rank in Šabac among people born
  1971–1980?"*
- ❌ We CANNOT answer: *"How many people in Serbia are named Goran?"*
- ⚠️ Coverage cliff: the census publication lists only the **top 10** names per
  municipality per cohort per gender. That is roughly **200–400 distinct names
  total**, out of the tens of thousands actually in use. A name like `Vanja` will
  very likely return **nothing**.

**This drives the product positioning.** Do not present the app as "how many of us
are there". Present it as a **map of naming fashions across place and generation**.
Then an empty result is a correct, informative answer rather than a bug — see
§6.3 for the required empty state.

### 2.1 Open question that blocks Phase 1

The annual newborn XLSX files (§3.2) may or may not contain absolute counts. They
could not be inspected during research (binary download). **First task: open
`najcescaimenadece2023.xlsx` and record the exact column layout in
`docs/DATA_NOTES.md`.**

- If they contain **counts** → build the newborn layer as a true count-based tool
  (a real Slovenian equivalent for the 2021–2025 birth years), and treat the census
  layer as historical depth.
- If they contain **ranks only** → the whole app is a rank explorer; proceed as
  described below and file the RZS request in §3.5.

---

## 3. Data sources — verified links

All links below were resolved successfully during research on 2026-08-31.

### 3.1 Primary: census publication (historical depth, 1940–2022)

**"Najčešća imena i prezimena", RZS, Census 2022, published 2024-03-08**

- Landing page: <https://www.stat.gov.rs/sr-Latn/vesti/20240308-najcescaimenaiprezimena>
- **PDF (the actual data):** <https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf>

Contents:

| Table | Content | Granularity | Counts? |
|-------|---------|-------------|---------|
| 1 | Ten most frequent **female** first names | Republic → region → district → municipality × 11 birth cohorts | No — rank only |
| 2 | Ten most frequent **male** first names | Same as Table 1 | No — rank only |
| 3 | Most frequent female and male names | Republic, by **single birth year** (approx. 1940–2022) | No — rank only |
| 4 | Ten most frequent **surnames** | Republic | **Yes**, approximate (Jovanović ~130,000; Petrović ~100,000; Nikolić ~90,000) |
| 5 | Most frequent **name + surname combinations** | Republic, by gender | **Yes**, approximate (Dragan Jovanović >2,200; Jelena Jovanović ~1,900) |

Birth cohorts in Tables 1–2: `1940 and earlier`, then by decade
(`1941–1950` … `2001–2010`), then `2011–2022`. **Confirm the exact cohort labels
from the PDF — do not hardcode from this document.**

Known facts usable as parser test fixtures (from the official landing page):

- Most frequent female name by birth year: `Radmila` until 1943 → `Slobodanka`
  (1944–1945) → `Mirjana` (1946–1948) → `Ljiljana` (1949–1959) → `Snežana`
  (1960–1963, 1969–1970) → `Vesna` (1964–1968) → `Biljana` (1971–1973) →
  `Danijela` (1974–1975) → `Jelena` (1976–1994) → `Milica` (1995–2011) → `Lena`
  (2012) → `Dunja` (2013–2015) → `Sofija` (2016–2022).
- Republic-level top 10 female: Jelena, Milica, Marija, Dragana, Mirjana,
  Ljiljana, Snežana, Ivana, Gordana, Ana.
- Republic-level top 10 male: Dragan, Aleksandar, Milan, Nikola, Zoran, Marko,
  Miloš, Goran, Dejan, Dušan.
- Cohort 2011–2022 female: Dunja, Sofija, Milica, Sara, Nikolina, Lena, Teodora,
  Anđela, Maša, Nađa.
- Cohort 2011–2022 male: Luka, Lazar, Stefan, Nikola, Aleksa, Vuk, Filip,
  Mihajlo, Pavle, Vasilije.
- Top surnames: Jovanović, Petrović, Nikolić, Marković, Đorđević, Stojanović,
  Ilić, Stanković, Pavlović, Milošević.

**Use these as assertions in the parser test suite.** If the parser output
contradicts any of them, the parser is wrong.

### 3.2 Secondary: annual newborn names (currency, 2021–2025)

Index page: <https://www.stat.gov.rs/sr-latn/oblasti/stanovnistvo/eksel-tabele/>

Direct XLSX links (note the mixed and inconsistent filename conventions — some
contain Cyrillic-derived characters; URL-encode carefully):

- 2025: `https://www.stat.gov.rs/media/419659/najčešća-imena-dece-rođene-u-republici-srbiji-u-2025-godini-godini.xlsx`
- 2024: `https://www.stat.gov.rs/media/405440/najcesca-imena-dece-rodjene-u-2024-godini.xlsx`
- 2023: `https://www.stat.gov.rs/media/391794/najcescaimenadece2023.xlsx`
- 2022: `https://www.stat.gov.rs/media/358665/najcesca-imena-dece-rodjene-u-2022-godini.xlsx`
- 2021: `https://www.stat.gov.rs/media/358213/najcesca-imеna-dece-rodjene-u-2021-godini.xlsx`

> ⚠️ The 2021 filename contains a **Cyrillic `е` (U+0435)** in `imеna` — it is not
> the Latin `e`. Copy the URL literally; do not retype it.

These are machine-readable and updated annually, unlike the decennial census.
**This is the better long-term backbone if the files contain counts.**

### 3.3 Reference/geography data

Needed to join municipalities and draw the map.

- RZS spatial units register and GIS:
  <https://www.stat.gov.rs/sr-latn/oblasti/registar-prostornih-jedinica-i-gis/>
- Open data code lists (`Šifarnik` category) at
  <http://opendata.stat.gov.rs/odata/> — includes `Општине и градови`
  (municipalities and cities), `Насеља` (settlements), `Територија - НСТЈ`
  (NUTS territory). Download as CSV or JSON.
- Municipality boundary polygons for the SVG map are **not** on the RZS portal in
  a usable form. Use OpenStreetMap-derived boundaries or a public GeoJSON of
  Serbian municipalities; record whatever source is chosen in `docs/DATA_NOTES.md`
  with its licence.

### 3.4 Census 2011 (optional comparison layer)

RZS published an equivalent names publication after the 2011 census. Only rank
lists — same limitation. Useful only if we want a 2011-vs-2022 comparison feature.
Deprioritise.

- Census 2011 Excel tables:
  <https://www.stat.gov.rs/sr-latn/oblasti/popis/popis-2011/popisni-podaci-eksel-tabele/>

### 3.5 The real unlock: request a custom tabulation from RZS

Frequencies of first names by gender and birth year at Republic level are an
aggregate that does not breach statistical confidentiality — SURS and DZS both
publish exactly this. Ask RZS for it. Three channels, in order of formality:

1. `Pitajte nas` (user support):
   <https://www.stat.gov.rs/sr-latn/korisnicka-podrska/pitajte-nas/>
2. Microdata request (formal, may involve a fee/contract):
   <https://www.stat.gov.rs/sr-latn/korisnicka-podrska/micropodaci/>
3. Freedom-of-information request under the *Zakon o slobodnom pristupu
   informacijama od javnog značaja*:
   <http://www.stat.gov.rs/sr-cyrl/korisnicka-podrska/informacije-od-javnog-znacaja/>

Contact e-mail on the open data portal: `stat@stat.gov.rs`.

**Send this in parallel with Phase 1.** If it lands, the schema below already has
a `count` column ready to populate.

### 3.6 Licensing

RZS open data terms allow copying, redistribution, modification and **commercial
use**, with mandatory attribution: source institution, retrieval date, and a clear
note of any modification. Put this in the site footer:

```
Izvor: Republički zavod za statistiku (Popis 2022; vitalna statistika 2021–2025).
Preuzeto: <YYYY-MM-DD>. Obrada: <projekat>.
```

For the Slovenian and Croatian references, if anything from them is ever cited:
SURS requires the credit `Vir: SURS`.

---

## 4. Database schema (PostgreSQL)

Design principle: `count` columns exist and are **nullable**. Rank-only sources
leave them `NULL`. If RZS ever supplies counts, no migration is needed.

```sql
-- ---------- geography ----------
CREATE TABLE region (            -- NUTS 2
    id          SERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL
);

CREATE TABLE district (          -- oblast, NUTS 3
    id          SERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    region_id   INT REFERENCES region(id)
);

CREATE TABLE municipality (
    id          SERIAL PRIMARY KEY,
    code_rzs    TEXT UNIQUE NOT NULL,   -- official RZS municipality code
    name        TEXT NOT NULL,
    name_slug   TEXT NOT NULL,          -- ASCII, lowercase, for URLs
    district_id INT REFERENCES district(id),
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION
);
CREATE INDEX ON municipality (name_slug);

-- ---------- names ----------
CREATE TABLE given_name (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,          -- canonical Latin script, e.g. 'Ljiljana'
    name_cyr    TEXT,                   -- Cyrillic form if known
    name_norm   TEXT NOT NULL,          -- ASCII-folded lowercase, e.g. 'ljiljana'
    gender      CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    UNIQUE (name_norm, gender)
);
CREATE INDEX ON given_name (name_norm);

CREATE TABLE surname (
    id            SERIAL PRIMARY KEY,
    surname       TEXT UNIQUE NOT NULL,
    surname_norm  TEXT NOT NULL,
    approx_count  INT                   -- from census Table 4, nullable
);

-- ---------- birth cohorts ----------
CREATE TABLE cohort (
    id          SERIAL PRIMARY KEY,
    label       TEXT UNIQUE NOT NULL,   -- exactly as printed in the PDF
    year_from   INT,                    -- NULL for the open-ended oldest bucket
    year_to     INT,
    sort_order  INT NOT NULL
);

-- ---------- census rank layer (Tables 1-2) ----------
CREATE TABLE census_rank (
    id              BIGSERIAL PRIMARY KEY,
    given_name_id   INT NOT NULL REFERENCES given_name(id),
    municipality_id INT NOT NULL REFERENCES municipality(id),
    cohort_id       INT NOT NULL REFERENCES cohort(id),
    gender          CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank            SMALLINT NOT NULL CHECK (rank BETWEEN 1 AND 10),
    count           INT,                -- always NULL from this source
    UNIQUE (municipality_id, cohort_id, gender, rank)
);
CREATE INDEX ON census_rank (given_name_id);
CREATE INDEX ON census_rank (municipality_id, cohort_id);

-- ---------- census rank by single birth year, Republic level (Table 3) ----------
CREATE TABLE census_rank_by_year (
    id              BIGSERIAL PRIMARY KEY,
    given_name_id   INT NOT NULL REFERENCES given_name(id),
    birth_year      SMALLINT NOT NULL,
    gender          CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank            SMALLINT NOT NULL,
    count           INT,
    UNIQUE (birth_year, gender, rank)
);
CREATE INDEX ON census_rank_by_year (given_name_id);

-- ---------- name + surname combinations (Table 5) ----------
CREATE TABLE name_surname_combo (
    id              BIGSERIAL PRIMARY KEY,
    given_name_id   INT NOT NULL REFERENCES given_name(id),
    surname_id      INT NOT NULL REFERENCES surname(id),
    gender          CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank            SMALLINT,
    approx_count    INT,
    UNIQUE (given_name_id, surname_id)
);

-- ---------- newborn layer (annual XLSX) ----------
CREATE TABLE newborn_name (
    id              BIGSERIAL PRIMARY KEY,
    given_name_id   INT NOT NULL REFERENCES given_name(id),
    year            SMALLINT NOT NULL,
    gender          CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank            SMALLINT,
    count           INT,                -- populate if the XLSX has counts
    UNIQUE (year, gender, given_name_id)
);
CREATE INDEX ON newborn_name (given_name_id);

-- ---------- provenance ----------
CREATE TABLE data_source (
    id              SERIAL PRIMARY KEY,
    key             TEXT UNIQUE NOT NULL,   -- 'census2022_pdf', 'newborn_2023_xlsx'
    title           TEXT NOT NULL,
    url             TEXT NOT NULL,
    retrieved_at    DATE NOT NULL,
    notes           TEXT
);
```

**Volume estimate:** ~170 municipalities × 11 cohorts × 2 genders × 10 ranks ≈
**37,400 rows** in `census_rank`; ~1,700 in `census_rank_by_year`; a few hundred
in the newborn layer. Trivial for PostgreSQL — no partitioning, no caching layer
needed.

---

## 5. Ingestion

### 5.1 Newborn XLSX (Phase 1 — do this first)

Straightforward: `openpyxl` or `pandas.read_excel`. One loader per year, output to
`data/normalized/newborn_<year>.csv`.

CSV convention for all intermediate files in this project:
**separator `;`, UTF-8 with BOM, dates `DD.MM.YYYY`, decimal comma.**

### 5.2 Census PDF (Phase 2 — the hard part, ~60% of total effort)

Use `pdfplumber` with explicit per-column bounding boxes. Do **not** trust
automatic table detection.

Known hazards, all of which must be handled explicitly:

1. **Split tables across facing pages.** Ranks I–V appear on the left page and
   VI–X on the right, with the municipality label repeated on both. Rows must be
   stitched by (municipality, cohort) key, not by page order.
2. **Cyrillic → Latin digraph corruption.** The published Latin transliteration
   renders `Љиљана` as `LJiljana` (both letters of the digraph capitalised). The
   same will affect `NJ` and `DŽ`. Normalise: `LJ`→`Lj`, `NJ`→`Nj`, `DŽ`→`Dž`
   when not at a word boundary requiring full caps. Build a mapping table and
   test it against `Ljiljana`, `Njegoš`, `Đorđe`, `Anđela`, `Snežana`.
3. **Diacritics.** `š č ć ž đ` must survive extraction. If they arrive as mojibake,
   the font encoding is non-standard — fall back to per-glyph mapping rather than
   guessing.
4. **Municipality name ambiguity.** Several municipalities share names with
   districts (e.g. Šabac, Niš). Join on the RZS code, never on the name string.
5. **Belgrade.** Belgrade's city municipalities may appear separately, as a
   combined row, or both. Decide once and document it.

**Never let the parser fill gaps.** A missing cell is `NULL`, never a guess.

### 5.3 Validation invariants

The loader must refuse to commit if any of these fail:

- Every municipality has exactly 11 cohorts.
- Every (municipality, cohort, gender) has exactly 10 ranks, 1..10, no duplicates.
- Every name in `census_rank` resolves to a `given_name` row.
- Municipality count matches the official RZS municipality register count.
- The known-facts list in §3.1 reproduces exactly.

---

## 6. Application

### 6.1 API (FastAPI)

```
GET  /api/name/{name}?gender=M|F
     → per-municipality best rank, per-cohort rank timeline, national rank by year

GET  /api/municipality/{slug}
     → top 10 by cohort and gender for that municipality

GET  /api/cohort/{cohort_id}
     → national top 10 for that cohort, plus which municipalities deviate

GET  /api/compare?a=Goran&b=Zoran&gender=M
     → side-by-side (mirrors the Slovenian app's compare feature)

GET  /api/newborn/{year}?gender=M|F
     → annual newborn ranking

GET  /api/suggest?q=gor
     → autocomplete over given_name.name_norm, prefix match, limit 10

GET  /api/surname/{surname}
     → approximate count if in top 10, else 404 with an explanatory payload
```

Every response includes a `source` block populated from `data_source`, so the
frontend can render attribution per view.

### 6.2 Frontend (vanilla JS)

- Search box with autocomplete hitting `/api/suggest`.
- Choropleth SVG map of Serbian municipalities, shaded by the name's best rank
  (rank 1 darkest, rank 10 lightest, absent = neutral grey).
- Cohort timeline: rank on the Y axis **inverted** (1 at top).
- Comparison view for two names.
- No build step. Plain ES modules, one CSS file.

### 6.3 The empty state — required, not optional

When a name has no rows, do **not** render an empty page or an error. Render:

> **Vanja** nije bilo među 10 najčešćih imena ni u jednoj opštini ni u jednoj
> generaciji. Zvanična statistika objavljuje samo prvih 10 imena po opštini, pa
> ovaj alat ne može da potvrdi koliko ljudi nosi ovo ime — samo da nije bilo među
> najčešćima.

…followed by the most frequent names in whatever municipality/cohort context the
user was last looking at, so the page is never a dead end.

A permanent **"Šta ovaj sajt ne može da vam kaže"** page explaining the rank-only
limitation is part of the MVP, not a nice-to-have. It is what keeps the project
honest.

---

## 7. Phases

| Phase | Deliverable | Est. |
|-------|-------------|------|
| **0** | Open the 2023 XLSX, document its layout in `docs/DATA_NOTES.md`. Decide count-vs-rank. Send the RZS request from §3.5. | 1 h |
| **1** | Newborn layer MVP: ingest 5 XLSX files, schema, 3 endpoints, minimal search UI. Runs locally on Windows. | 6–8 h |
| **2** | Census PDF parser + validation harness + full historical load. | 12–15 h |
| **3** | Map, cohort timeline, comparison view, empty state, limitations page. | 6–8 h |
| **4** | Dockerise, deploy to VPS, nginx + TLS, attribution footer. | 2–3 h |

**Total: ~30 hours.** Phase 2 is the risk; everything else is routine.

---

## 8. Local development (Windows)

```
C:\projects\kakosezoves\
├── data\
│   ├── raw\              # downloaded PDF and XLSX, never edited
│   ├── normalized\       # parser output, CSV, ';' + UTF-8 BOM
│   └── geo\              # municipality GeoJSON
├── src\
│   ├── ingest\           # pdf_parser.py, xlsx_loader.py, geo_loader.py
│   ├── db\               # models.py, session.py, migrations\
│   ├── api\              # main.py, routers\
│   └── util\             # transliteration.py, normalize.py
├── static\               # index.html, app.js, style.css, serbia.svg
├── tests\
│   └── fixtures\         # 3 hand-transcribed PDF pages = ground truth
├── docs\
│   └── DATA_NOTES.md     # ← Phase 0 output lives here
├── requirements.txt
└── docker-compose.yml
```

```powershell
cd C:\projects\kakosezoves
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

PostgreSQL locally via Docker Desktop rather than a native Windows install —
keeps the dev environment identical to the VPS.

Dependencies, and the reason each is present:

```
fastapi          # API framework
uvicorn[standard]# ASGI server
sqlalchemy       # ORM, already in the stack
psycopg[binary]  # PostgreSQL driver
pydantic         # request/response models
alembic          # schema migrations
pdfplumber       # PDF table extraction with bbox control
openpyxl         # XLSX reading
python-dotenv    # config
pytest           # tests
```

No other libraries without a stated reason.

---

## 9. Claude Code subagent setup

Three agents under `.claude/agents/`. The separation exists to prevent the failure
mode where the parser gets tuned to satisfy the validator instead of reading the
document correctly.

### `pdf-extractor.md` — worker

```
tools: Read, Write, Edit, Bash
```

Parses **one district (`oblast`) per invocation**, never the whole PDF. Writes to
`data/normalized/{oblast}.csv` (`;` separator, UTF-8 BOM). Explicit instruction:
a cell that cannot be read is written as `NULL` — never inferred, never
interpolated from neighbouring rows, never guessed from the national list.

### `data-reviewer.md` — reviewer

```
tools: Read, Bash          # deliberately NO Write
```

Checks the §5.3 invariants and returns a **list of violations only**. It must not
edit any file. Withholding write access is the point: a reviewer that can patch
data will patch data.

### `test-runner.md` — test-runner

```
tools: Bash, Read
```

Runs `pytest` against `tests/fixtures/` — three PDF pages transcribed **by hand**
and verified by eye. This is the only real ground truth in the project. Without
it, there is no way to know whether the parser is reading or hallucinating.

### Orchestration rule

The extractor never receives the reviewer's output directly. You read the
violation list, decide whether the fault is in the parser or in the source
document, and only then issue a specific instruction to the extractor. Wiring
reviewer → extractor directly produces a loop that converges on passing the
validator rather than on correct data.

---

## 10. Open questions

1. ~~Does the newborn XLSX contain counts?~~ **RESOLVED 2026-08-31: ranks only,
   no counts.** See `docs/DATA_NOTES.md`. The app is a rank explorer end-to-end.
2. **Exact cohort labels** as printed in the census PDF — read them, do not assume.
3. **Belgrade handling** — separate city municipalities, aggregate, or both?
4. **Municipality GeoJSON source and licence** — needs picking and recording.
5. **RZS response** to the custom tabulation request — unknown timeline.
6. **Newborn layer geography** — the 2023 XLSX gives district-level (`oblast`)
   breakdowns, not just Republic-level, and has no municipality granularity at
   all. Decide whether `newborn_name` needs a nullable `district_id` column (or
   a sibling table) to preserve that, instead of being implicitly
   Republic-only as currently drafted in §4. See `docs/DATA_NOTES.md` for the
   full group list found in the file.
