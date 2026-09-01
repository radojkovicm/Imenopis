# PROJECT.md — Serbian Name Statistics Explorer

**Version 2. Supersedes the previous `PROJECT.md`, `PROJECT_ADDENDUM.md` and
`PROJECT_ADDENDUM_V2.md`. Delete all three.** This is the only specification.

Working slug: `imena-rs`. **Public name decided: `imenopis.rs`** (set in
`config.SITE_NAME`, and hardcoded into the static pages' `<title>`, header and
footer copy since they have no server-side templating — see PROJECT.md §13's
folder layout and §6.2's "no build step" constraint).

**Stack (fixed):** Python 3.11+, FastAPI, SQLAlchemy, Pydantic, PostgreSQL,
vanilla JS. Dev on Windows in VS Code, production on a Linux VPS behind Docker.
No new libraries without a stated reason.

Two decisions in this document are **branches** resolved by Phase 0 (§9). They are
marked `BRANCH A` (counts) and `BRANCH B` (variant spellings). After Phase 0,
delete the dead branch from this file.

---

## 1. What this is

A public web app where someone types a first name — `Goran` — and sees where it
ranked across Serbian municipalities and birth cohorts, plus what the top names
were in any birth year.

**Positioning: a map of naming fashion across place and generation.** Not "how
many of us are there." Serbian official statistics publish ranks, not counts, for
first names (§2). Building the product around counts would promise something the
data cannot deliver; building it around geography and generations delivers
something no one has built for Serbia.

The site should be enjoyable to browse. That shapes tone and entry points (§8),
never the evidence rules (§4).

---

## 2. Data reality

**There is no Serbian dataset with absolute counts per first name.** Checked
against the RZS census publication, the RZS open data portal
(`opendata.stat.gov.rs/odata` — 731 datasets, no names dataset found), the
national open data portal, and GitHub. Absence of a search hit is not proof, but
nothing surfaced.

Consequences:

- ✅ Answerable: *where did `Goran` rank in Šabac among people born 1971–1980?*
- ❌ Not answerable: *how many people in Serbia are named `Goran`?*
- ⚠️ **Coverage cliff:** the census publishes only the **top 10** per municipality,
  per cohort, per gender — roughly 200–400 distinct names out of tens of
  thousands in use. `Vanja` will very likely return nothing. §8.1 handles this.

The exception is the annual newborn XLSX files, which may contain counts. That is
`BRANCH A`, resolved in Phase 0.

---

## 3. Sources

All links verified 2026-08-31.

### 3.1 Census publication — historical depth, 1940–2022

**"Najčešća imena i prezimena", RZS, Census 2022**

- Landing: <https://www.stat.gov.rs/sr-Latn/vesti/20240308-najcescaimenaiprezimena>
- **PDF:** <https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf>

| Table | Content | Granularity | Counts? |
|-------|---------|-------------|---------|
| T1 | Ten most frequent **female** names | Republic → region → district → municipality × 9 cohorts | No |
| T2 | Ten most frequent **male** names | Same | No |
| T3 | Most frequent female and male names | **Republic only**, by single birth year (~1940–2022), **top 5 only (ranks I–V), not top 10** | No |
| T4 | Ten most frequent surnames | Republic → region → district → municipality (same nesting as T1/T2) | No |
| T5 | Most frequent name + surname combinations | Republic, by gender, **top 20** | No |

**Phase 0 finding (2026-08-31), see `docs/DATA_NOTES.md`:** T1–T2 have **9**
cohorts, not 11 (`1940. и раније` + 7 decade buckets + `2011–2022`). T4's
granularity and T4/T5's "counts" column above are corrected from the original
draft of this document — T4 goes to municipality level like T1/T2, and neither
T4 nor T5 carries any count or approximation in the actual PDF (`G20244001.pdf`);
the approximate figures below came from the RZS press-release landing page, a
different document. Cohorts in T1–T2: `1940. и раније`, then decades
(`1941–1950` … `2001–2010`), then `2011–2022`. **Read the exact labels from the
PDF — do not hardcode from this document.**

Known facts, from the official landing page. **These are the parser test
fixtures** — if output contradicts them, the parser is wrong:

- Most frequent female name by birth year: `Radmila` to 1943 → `Slobodanka`
  (1944–45) → `Mirjana` (1946–48) → `Ljiljana` (1949–59) → `Snežana` (1960–63,
  1969–70) → `Vesna` (1964–68) → `Biljana` (1971–73) → `Danijela` (1974–75) →
  `Jelena` (1976–94) → `Milica` (1995–2011) → `Lena` (2012) → `Dunja` (2013–15) →
  `Sofija` (2016–22).
- Republic top 10 female: Jelena, Milica, Marija, Dragana, Mirjana, Ljiljana,
  Snežana, Ivana, Gordana, Ana.
- Republic top 10 male: Dragan, Aleksandar, Milan, Nikola, Zoran, Marko, Miloš,
  Goran, Dejan, Dušan.
- Cohort 2011–2022 female: Dunja, Sofija, Milica, Sara, Nikolina, Lena, Teodora,
  Anđela, Maša, Nađa.
- Cohort 2011–2022 male: Luka, Lazar, Stefan, Nikola, Aleksa, Vuk, Filip,
  Mihajlo, Pavle, Vasilije.
- Top surnames: Jovanović, Petrović, Nikolić, Marković, Đorđević, Stojanović,
  Ilić, Stanković, Pavlović, Milošević.
- Approximate surname counts: Jovanović ~130,000; Petrović ~100,000;
  Nikolić ~90,000. Combinations: Dragan Jovanović >2,200; Jelena Jovanović ~1,900.

### 3.2 Annual newborn names — currency, 2021–2025

Index: <https://www.stat.gov.rs/sr-latn/oblasti/stanovnistvo/eksel-tabele/>

- 2025: `https://www.stat.gov.rs/media/419659/najčešća-imena-dece-rođene-u-republici-srbiji-u-2025-godini-godini.xlsx`
- 2024: `https://www.stat.gov.rs/media/405440/najcesca-imena-dece-rodjene-u-2024-godini.xlsx`
- 2023: `https://www.stat.gov.rs/media/391794/najcescaimenadece2023.xlsx`
- 2022: `https://www.stat.gov.rs/media/358665/najcesca-imena-dece-rodjene-u-2022-godini.xlsx`
- 2021: `https://www.stat.gov.rs/media/358213/najcesca-imеna-dece-rodjene-u-2021-godini.xlsx`

> ⚠️ The 2021 filename contains a **Cyrillic `е` (U+0435)** in `imеna`, not the
> Latin `e`. Copy the URL literally; never retype it.

Machine-readable and updated annually. If `BRANCH A` resolves to counts, this
becomes the stronger long-term backbone.

### 3.3 Geography

- RZS spatial units register:
  <https://www.stat.gov.rs/sr-latn/oblasti/registar-prostornih-jedinica-i-gis/>
- Code lists (`Šifarnik`) at <http://opendata.stat.gov.rs/odata/> — municipalities
  and cities, settlements, NUTS territory. CSV/JSON.
- Municipality boundary polygons are **not** available from RZS in usable form.
  Use an OpenStreetMap-derived GeoJSON; record source and licence in
  `docs/DATA_NOTES.md`.

### 3.4 Request to RZS — send during Phase 0

Ask for **first-name frequencies by gender and single year of birth, at Republic
level**, with whatever suppression floor RZS requires. Cite four national
statistical offices that already publish such aggregates:

| Office | What they publish | Floor |
|--------|-------------------|-------|
| **SURS** (SI) | Counts per name, by statistical region and birth period, annual | <5 |
| **DZS** (HR) | Counts per name, surname, and combination | <10 |
| **Statbel** (BE) | First names of the **total population by municipality**, open data XLSX, CC BY 4.0 | <5 |
| **ONS** (UK) | **Rank and count** by local authority, region, mother's age, month; 1996–2025 | published floor |

What we are asking for is strictly less granular than what Statbel gives away.

Channels: `Pitajte nas`
(<https://www.stat.gov.rs/sr-latn/korisnicka-podrska/pitajte-nas/>) → microdata
request (<https://www.stat.gov.rs/sr-latn/korisnicka-podrska/micropodaci/>) → FOI
request (<http://www.stat.gov.rs/sr-cyrl/korisnicka-podrska/informacije-od-javnog-znacaja/>).
Contact: `stat@stat.gov.rs`. **Do not wait for a reply.**

### 3.5 Reference implementations

- **SURS**: <https://www.stat.si/imenarojstva> — data as of 1 Jan 2026. Search by
  name, surname, combination, birthday; region and birth-period breakdowns;
  autocomplete; two-name comparison; curated sections (most frequent, newborns,
  disappearing, modern). <5 suppressed; regional cells protected by the
  missing-values method.
- **DZS**: <https://web.dzs.hr/app/imena/default.aspx> — simpler; <10 suppressed.
- **Statbel**: <https://statbel.fgov.be/en/open-data/first-names-total-population-municipality>
- **ONS**: <https://www.ons.gov.uk/releases/babynamesinenglandandwales2025>
- **CSO Ireland**: <https://www.cso.ie/en/releasesandpublications/ep/p-ibn/irishbabiesnames2025/mainresults>
  — top risers, new top-100 entrants, county breakdown, interactive explorer.
- **CSO on variant spellings**: <https://www.cso.ie/en/releasesandpublications/ep/p-ibn/irishbabiesnames2024/mainresults/>
  — since 2018 `Sean` and `Seán` are two separate names, causing a documented
  break in series: `Seán` ranks 15th, `Sean` fell to 123rd. This is the precedent
  behind `BRANCH B`.

**Not verified — do not cite as precedent:** SSA publication depth beyond top
1000; the commercial site Namedaisy.

### 3.6 Licence

RZS open data terms permit copying, redistribution, modification and commercial
use, with attribution, retrieval date, and a clear note of any modification.
Footer on every page:

```
Izvor: Republički zavod za statistiku (Popis 2022; vitalna statistika 2021–2025).
Preuzeto: <YYYY-MM-DD>. Obrada: <SITE_NAME>.
```

If Slovenian data is ever cited: `Vir: SURS`.

---

## 4. Evidence model

Every value the API returns and the UI renders carries its evidence class. This is
a **data model requirement**, not documentation.

### 4.1 Three classes

| Class | Meaning | Example |
|-------|---------|---------|
| **observed** | Read directly from a source table | `Goran is #3 in Šabac, 1971–1980` |
| **derived** | Computed only from observed ranks, using set and comparison operations | `Goran appears in the top 10 in 83 municipalities` |
| **unknown** | The source cannot answer it | `How many people are named Goran` |

### 4.2 Evidence class vs data status

Keep these separate. `evidence` describes **what we can know**; `status` describes
**what happened in the source**.

```json
{
  "value": null,
  "evidence": "unknown",
  "status": "not_observed",
  "reason": "source_is_top10_only"
}
```

`status` vocabulary: `observed` · `not_observed` · `suppressed` · `not_applicable`.
`reason` vocabulary: `source_is_top10_only` · `source_is_top5_only` ·
`scope_not_published` · `source_has_no_counts` · `below_confidentiality_threshold` ·
`no_historical_source_for_period` (§16).

### 4.3 API envelope

Never return a bare scalar.

```json
{
  "rank": 3,
  "evidence": "observed",
  "status": "observed",
  "source": "census_2022_t2",
  "scope": { "municipality": "Šabac", "cohort": "1971-1980", "gender": "M" }
}
```

```json
{
  "municipality_count": 83,
  "evidence": "derived",
  "status": "observed",
  "derived_from": ["census_2022_t1", "census_2022_t2"],
  "note": "top10_presence_only"
}
```

### 4.4 `null` is not "rare"

`null` means the source cannot see it. The frontend must have **no code path**
that converts an unknown into a characterisation of a name.

Required test: assert that no rendered string containing `retk`, `čest`,
`popular`, `koncentr` or a `%` sign can be produced from any payload whose
`evidence` is `unknown`.

---

## 5. Hard rules

### 5.1 Truncation at rank 10 is censoring, not display

For any (municipality, cohort, gender) cell, everything outside the top 10 is one
undifferentiated state. A name at #11 in every municipality and a name held by
nobody produce **identical observations**. No metric may require distinguishing
them.

Does not ship until counts exist:

- ❌ Any concentration or regionality score
- ❌ Any percentage, share, or `−92%` trend
- ❌ `rare` / `common` / `high concentration` as characterisations
- ❌ Algorithmic "similar names" or "closest rival" — the candidate pool is ~200
  observable names; the result would be an artefact of the window

**User-chosen comparison is fine.** `Goran vs Zoran` because the user asked is a
valid rank comparison. The machine choosing the rival is not.

### 5.2 Rank depth limits what "rising" can mean

Ireland's CSO can say `Raya rose from 213rd to 99th` because they publish ranks
hundreds deep. **We have ranks 1–10.** A name entering our top 10 may have come
from #11 or from #4,000.

| Render as | Never render as |
|-----------|-----------------|
| `Ušlo u top 10` | `Ime u usponu` |
| `Ispalo iz top 10` | `Ime u nestajanju` |
| `Ponovo u top 10` | `Ime se vratilo` |
| `Viši rang nego prethodne generacije` | `Skočilo N mesta` |

Each carries a tooltip: *"Podaci pokazuju samo prvih 10 imena, pa ne možemo znati
koliko je ime bilo rasprostranjeno dok nije bilo u top 10."*

### 5.3 National rank often does not exist

Available only for names inside the national top 10. For every other name, the
national side of a local-vs-national comparison is `unknown`.

- ✅ `#1 u Šapcu — nije u nacionalnom top 10 za ovu generaciju`
- ❌ `#1 lokalno, #17 nacionalno`

### 5.4 Cohorts are not equal-length

Buckets are open-ended (`1940 and earlier`), 10-year, and 12-year (`2011–2022`).
Counting them as steps treats unequal intervals as equal units. Express
persistence as a year span, computed from `cohort.year_from` / `year_to`:

- ✅ `U top 10 kod rođenih 1941–1990.`
- ❌ `U top 10 sedam uzastopnih generacija.`

### 5.5 Set overlap is a count, never a bar

"6 of 10 names shared between two cohorts" is legitimate. A progress bar makes it
read as a similarity percentage, which it is not — two cohorts can share 6 of 10
top names while being entirely different below rank 10. Number and sentence only.
No bar, no gauge, no ring.

### 5.6 Rank charts use an inverted axis, never bar length

Bar length encodes magnitude. We have none. Comparison views plot rank positions
on a shared axis, 1 at top.

### 5.7 Terminology

The absence of a name from a cell is `not_in_top10`, never `absent`. This applies
to API fields, CSS classes, and map legend copy. `absent` invites the reading
"nobody has this name."

---

## 6. Data model

### 6.1 Name identity — the core decision

**The statistical unit is the form the source printed.** Not our normalisation,
not our display choice.

```sql
CREATE TABLE given_name (
    id           SERIAL PRIMARY KEY,
    source_form  TEXT NOT NULL,     -- verbatim as printed: 'LJiljana', 'Đorđe'
    source_key   TEXT NOT NULL REFERENCES data_source(key),
    search_key   TEXT NOT NULL,     -- ASCII-folded, digraph-normalised — NOT unique
    gender       CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    UNIQUE (source_form, source_key, gender)
);
CREATE INDEX ON given_name (search_key);
```

`source_key` identifies the **specific table or edition**, not the dataset family:
`census_2022_t1`, `census_2022_t2`, `census_2022_t3`, `census_2022_t4`,
`census_2022_t5`, `newborn_2021` … `newborn_2025`. This is what makes every row
auditable back to a page.

`search_key` is deliberately **not unique**. Two source forms may fold to the same
key. That is a finding to surface (§7.2), not a collision to resolve.

### 6.2 Clusters — display and search only

```sql
CREATE TABLE name_cluster (
    id         SERIAL PRIMARY KEY,
    canonical  TEXT NOT NULL,       -- the display form we choose
    gender     CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    UNIQUE (canonical, gender)
);

CREATE TABLE name_cluster_member (
    cluster_id     INT NOT NULL REFERENCES name_cluster(id),
    given_name_id  INT NOT NULL REFERENCES given_name(id),
    decided_by     TEXT NOT NULL CHECK (decided_by IN
                       ('exact_match','digraph_normalization','manual')),
    decision_note  TEXT,            -- required when decided_by = 'manual'
    decided_at     DATE NOT NULL,
    PRIMARY KEY (cluster_id, given_name_id)
);
```

**A cluster is a unit of search and display. It is never a unit of computation.**

Every statistic resolves its `given_name` members first and reports per member.
Two members are **never summed** merely because they share a cluster — summing
would assert that the source treats them as one name, which is exactly what we do
not know until `BRANCH B` is resolved.

`decision_note` is mandatory for manual decisions. The audit question the schema
must answer: *who or what decided these two forms are the same for display, and on
what basis?*

### 6.3 Geography

```sql
CREATE TABLE region (
    id    SERIAL PRIMARY KEY,
    code  TEXT UNIQUE NOT NULL,
    name  TEXT NOT NULL
);

CREATE TABLE district (
    id         SERIAL PRIMARY KEY,
    code       TEXT UNIQUE NOT NULL,
    name       TEXT NOT NULL,
    region_id  INT REFERENCES region(id)
);

CREATE TABLE municipality (
    id           SERIAL PRIMARY KEY,
    code_rzs     TEXT UNIQUE NOT NULL,   -- join on this, never on name
    name         TEXT NOT NULL,
    name_slug    TEXT NOT NULL,
    district_id  INT REFERENCES district(id),
    lat          DOUBLE PRECISION,
    lon          DOUBLE PRECISION
);
CREATE INDEX ON municipality (name_slug);
```

### 6.4 Cohorts

```sql
CREATE TABLE cohort (
    id          SERIAL PRIMARY KEY,
    label       TEXT UNIQUE NOT NULL,   -- exactly as printed in the PDF
    year_from   INT,                    -- NULL for the open-ended oldest bucket
    year_to     INT,
    sort_order  INT NOT NULL
);
```

### 6.5 Observations

`count` columns exist and are nullable throughout. Rank-only sources leave them
`NULL`. If `BRANCH A` or the RZS request delivers counts, no migration is needed.

Uniqueness is on **the name within its scope**, never on the rank number — this
stores tied ranks natively (§9.3).

```sql
CREATE TABLE census_rank (
    id               BIGSERIAL PRIMARY KEY,
    given_name_id    INT NOT NULL REFERENCES given_name(id),
    municipality_id  INT NOT NULL REFERENCES municipality(id),
    cohort_id        INT NOT NULL REFERENCES cohort(id),
    gender           CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank             SMALLINT NOT NULL CHECK (rank BETWEEN 1 AND 10),
    count            INT,
    UNIQUE (municipality_id, cohort_id, gender, given_name_id)
);
CREATE INDEX ON census_rank (given_name_id);
CREATE INDEX ON census_rank (municipality_id, cohort_id);

CREATE TABLE census_rank_by_year (
    id             BIGSERIAL PRIMARY KEY,
    given_name_id  INT NOT NULL REFERENCES given_name(id),
    birth_year     SMALLINT NOT NULL,
    gender         CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank           SMALLINT NOT NULL,
    count          INT,
    UNIQUE (birth_year, gender, given_name_id)
);
CREATE INDEX ON census_rank_by_year (given_name_id);

CREATE TABLE newborn_name (
    id             BIGSERIAL PRIMARY KEY,
    given_name_id  INT NOT NULL REFERENCES given_name(id),
    year           SMALLINT NOT NULL,
    gender         CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank           SMALLINT,
    count          INT,                 -- BRANCH A
    UNIQUE (year, gender, given_name_id)
);
CREATE INDEX ON newborn_name (given_name_id);

CREATE TABLE surname (
    id            SERIAL PRIMARY KEY,
    surname       TEXT NOT NULL,
    source_key    TEXT NOT NULL REFERENCES data_source(key),
    search_key    TEXT NOT NULL,
    approx_count  INT,
    UNIQUE (surname, source_key)
);

CREATE TABLE name_surname_combo (
    id             BIGSERIAL PRIMARY KEY,
    given_name_id  INT NOT NULL REFERENCES given_name(id),
    surname_id     INT NOT NULL REFERENCES surname(id),
    gender         CHAR(1) NOT NULL CHECK (gender IN ('M','F')),
    rank           SMALLINT,
    approx_count   INT,
    UNIQUE (given_name_id, surname_id)
);
```

### 6.6 Provenance

```sql
CREATE TABLE data_source (
    key           TEXT PRIMARY KEY,     -- 'census_2022_t1', 'newborn_2023'
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    table_ref     TEXT,                 -- 'Tabela 1', 'Sheet1'
    scope         TEXT NOT NULL,        -- 'municipality x cohort', 'republic x year'
    measure       TEXT NOT NULL,        -- 'rank' | 'count' | 'rank+count'
    retrieved_at  DATE NOT NULL,
    notes         TEXT
);
```

**No automatic merging across sources. There is no "latest wins".** If the census
and a newborn file disagree, they are answering different questions at different
scopes with different measures. The API routes each question to the source whose
`scope` and `measure` fit it, and names that source in the response. Merging
different statistical definitions is never done implicitly.

### 6.7 Volume

168 municipalities (confirmed exactly — §7 of `docs/DATA_NOTES.md`) × 9
cohorts × 2 genders × 10 ranks ≈ **30,240** rows in `census_rank`; 830 in
`census_rank_by_year` (§6a of `docs/DATA_NOTES.md`: 83 years × 2 genders × 5
ranks); a few hundred in the newborn layer. Trivial. No partitioning, no
cache layer, no search engine.

---

## 7. Features

All eight ship. Each is tagged with the source it needs — this drives the build
order in §10.

| # | Feature | Source | Evidence |
|---|---------|--------|----------|
| 1 | **Search a name** — everything the sources can prove about it | T1–T3, XLSX | observed + derived |
| 2 | **Generation Explorer** — birth year → top 10 M/F | **T3 only** | observed |
| 3 | **Name timeline** — rank across cohorts and years | T1–T3 | observed |
| 4 | **Map** — top-10 presence by municipality | T1–T2 | observed + derived |
| 5 | **Compare** — name A vs name B, user-chosen | T1–T3 | observed |
| 6 | **Municipality** — top 10 by cohort, and how it differs from national | T1–T2 | observed + derived |
| 7 | **Newborns** — 2021–2025 | XLSX | observed |
| 8 | **Šta ovaj sajt ne može da vam kaže** | — | — |

Feature 1 is worded *"everything the sources can prove"*, not "everything known" —
the census layer carries ranks, the newborn layer may carry counts, and the page
must not promise a uniform answer.

### 7.1 Name page — required content order

1. **Kada** — cohorts in which it reached the top 10, with rank; inverted-axis timeline
2. **Gde** — municipality count, highest rank achieved and where; map
3. **Najbolji rezultat** — highest rank, where and when
4. **Raspon** — first and last cohort in which it appears at all

All four are `observed` or `derived`. No scores, no percentages, no adjectives.

### 7.2 Split-name state (required)

Because `search_key` is not unique (§6.1), a search may resolve to more than one
`given_name`. The UI must handle this explicitly:

> Izvor vodi dva odvojena zapisa za ovo ime: **Đorđe** i **Djordje**.
> Prikazujemo ih odvojeno jer ih statistika ne spaja.

Timelines and maps render **per member**, never summed (§6.2). This is not an edge
case to defer — it is the visible consequence of the project's central
methodological commitment, and it ships in Phase 1.

### 7.3 Generation Explorer

An entry point equal in prominence to name search, not a sub-page. Birth year →
top 10 male and female names for that year, nationally. Two follow-ons, both pure
T3 lookups:

- **Compare two generations** (`1988 vs 2008`) — names that left the top 10, names
  that entered, names present in both.
- **"Kako bi te zvali da si rođen ranije"** — the #1 name of that year across
  several decades.

### 7.4 Municipality page

Top 10 by cohort, plus a second column with the same name's national rank for the
same cohort — showing `nije u nacionalnom top 10` wherever §5.3 applies. That
column is where local character shows.

### 7.5 Top-10 persistence

`Najduži period u top 10: rođeni 1941–1990` — a year span per §5.4.

### 7.6 Two time machines

They read different tables and cannot be merged:

- **National** — slider over single birth years, T3, **no map** (T3 has no geography)
- **Geographic** — 9-step control over cohorts (corrected by Phase 0 — see
  §9.1), T1–T2, **with map** (T1–T2 have no per-year resolution)

Never label the geographic control with years.

---

## 8. UX and tone

Three entry points on the home page, equal weight:
`Kako se zoveš?` (name) · `Rođen/a sam...` (year) · `Izaberi opštinu` (map).
One oversized search box hides two thirds of the product.

### 8.1 Empty state

Not an error, not an apology — a finding plus a way onward:

> **Vanja** nije bilo među 10 najčešćih imena ni u jednoj opštini ni u jednoj
> generaciji.
>
> Zvanična statistika objavljuje samo prvih deset imena po opštini — sve ispod
> desetog mesta je nevidljivo. Zato ne znamo koliko ljudi nosi ovo ime, samo da
> nije bilo među najčešćima.
>
> *Evo šta jeste bilo najčešće u istom periodu →*

Always offer the onward link. The page is never a dead end.

**We cannot distinguish "this name does not exist in Serbia" from "this name is
not in the top 10."** Our name index *is* the set of observed names; we have no
dictionary of Serbian names to check against. A real name and an invented string
produce the same result, and that is correct. Never claim to know whether a name
exists. Do not introduce an external name dictionary to fake the distinction — an
unsourced list inside a statistics product damages the thing that makes it
trustworthy.

### 8.2 The limitations page

Content, not boilerplate. Title it `Šta ovaj sajt ne može da vam kaže` and use it
to explain *why* Serbian data looks this way, with the Slovenian, Croatian,
Belgian and Irish comparisons from §3.4–3.5. Genuinely interesting reading, and it
doubles as the public argument for why RZS should publish more.

Part of the MVP. Not deferred.

### 8.3 Source badge

If `BRANCH A` yields counts, every page carries a visible badge:
`Podatak: RANG` or `Podatak: BROJ ROĐENIH`. A user must never have to open the
methodology page to know which they are looking at.

Rank years and count years are **never plotted on one chart**. Placing `#3` above
`843` invites the reading that they are the same measure.

---

## 9. Phase 0 — blocks everything — **COMPLETE, both branches resolved 2026-08-31**

All findings are recorded in `docs/DATA_NOTES.md`, which is now the source of
truth for what the raw files actually contain. Two things this spec assumed
turned out wrong and are corrected there — **read it before writing the T1/T2
parser or the cohort seed data**:

1. Table 1/2 have **9 cohort buckets, not 11** (`1940. и раније` + 7 decade
   buckets `1941–1950`…`2001–2010` + `2011–2022`).
2. Table 4 (surnames) is granular **to municipality level**, not Republic-only
   as this section previously stated — same nesting as T1/T2.

Also: the §11.2 "digraph corruption" hazard (`LJiljana`-style all-caps
artifacts) **does not apply** — the census PDF is printed entirely in
Cyrillic, not a Latin transliteration, so there is no such artifact to
recover from. A Cyrillic→Latin transliteration step is still needed for
`search_key`/display, but it's a clean script mapping, not error recovery.

### 9.1 XLSX checklist (per year, 2021–2025) — done, all 5 years

- [x] Sheet names and count — one sheet each; name drifts (`Коначно` /
      `Коначно 2024` / `Коначно 2025`)
- [x] Exact column headers, verbatim — no real headers; row 1 = title, row 2 =
      `Девојчице`/`Дечаци`
- [x] **Is there a count column, or rank only?** → **`BRANCH A` = rank only,
      confirmed all 5 years, 0 numeric cells found anywhere**
- [x] Maximum rank published — 10, every group, every year
- [x] Gender layout — two columns side by side (B=girls, C=boys)
- [x] Geography — district (`oblast`) level + Republic + macro-region + NUTS-2
      rollups, **32 groups**, identical every year; no municipality level
- [x] Tied ranks — none observed in any year
- [x] Script — Cyrillic, 100%, all 5 years
- [x] Diacritics/digraphs — N/A (Cyrillic has no Latin digraph problem)
- [x] **Variant spellings** → **`BRANCH B` = listed separately**, confirmed:
      `Михајло` (60+ occurrences) vs `Михаило` (2 occurrences) coexist as
      distinct strings in the same year's data
- [x] Layout consistency 2021→2025 — structurally identical (same 32 groups,
      same 10-per-group pattern); only cosmetic differences (trailing empty
      columns, sheet name)

Also found: a 2021-only data-entry error (name+surname typed into one cell,
`Пиротска област` rows 319–320) — see `docs/DATA_NOTES.md` §2.2 for how the
loader should handle it (store verbatim, flag, never silently strip).

### 9.2 Census PDF checklist — done, national tables + representative districts

- [x] Exact cohort labels as printed — see correction above; full label list in
      `docs/DATA_NOTES.md` §4
- [x] Confirm ranks I–V / VI–X split across facing pages — confirmed, but the
      cohort/year label **switches sides** between the two pages (leftmost
      column on the left page, rightmost column on the right page) — not a
      mirrored layout
- [x] Confirm the digraph corruption (`LJiljana`) actually appears — **it does
      not; the hazard doesn't apply to this source** (see above)
- [x] Belgrade: city municipalities separately, aggregated, or both — **both**;
      17 opštine appear individually and there's also one Republic-facing
      aggregate row for `Београдска област (Град Београд)`. **Resolved in
      Phase 3** (`docs/DATA_NOTES.md` §7.3): the 17 opštine feed
      `census_rank.municipality_id`; the aggregate row is not loaded. Four
      other cities (Ужице, Пожаревац, Ниш, Врање) have the same
      grad-with-subdistricts pattern at smaller scale (2, 2, 5, 2
      sub-districts respectively)
- [x] **Municipality count** — **168, confirmed exactly** in Phase 3 by
      extracting the full geography tree from the PDF's own table of
      contents (`docs/DATA_NOTES.md` §7): 140 plain opština/grad entries +
      28 sub-districts of the 5 multi-district cities. The RZS spatial
      register (§3.3) still isn't integrated for real `code_rzs` values —
      `code_rzs` is a stable name-slug placeholder for now
- [x] Tied ranks present? — none observed in T1, T2, T3, T4, or T5 samples

Extra findings beyond the original checklist, also in `docs/DATA_NOTES.md`:
Table 3 is confirmed Republic-only/single-birth-year as assumed; Table 5 is
top-20 (not top 10) per gender; **Tables 4 and 5 carry no counts or
approximations anywhere in the actual PDF** — the "Jovanović ~130,000"-style
figures in §3.1 above came from the RZS press-release landing page, a
different document, and do not appear in `G20244001.pdf` itself. Treat T4/T5
as rank-only like T1–T3 unless a citable source for those approximate counts
turns up.

### 9.3 Tied ranks are a validation finding, not a schema branch

The model in §6.5 already stores ties — uniqueness is on the name within scope,
not on the rank number. Phase 0 only needs to **record** whether ties occur, so
the validator knows whether to expect exactly 10 rows per cell or a variable
count. No schema change either way.

### 9.4 `BRANCH A` — counts in the newborn XLSX — **RESOLVED: rank only**

Confirmed across all 5 years and, incidentally, across census T4/T5 as well
(§9.2 above). No count-based layer exists anywhere in the currently available
sources. `newborn_name.count`, `surname.approx_count`, and
`name_surname_combo.approx_count` all stay `NULL` from these sources.
`data_source.measure` is `rank` for every `data_source` key seeded from these
files. The §3.4 RZS request remains the only path to real counts — send it in
parallel with Phase 1, per the original plan.

### 9.5 `BRANCH B` — variant spellings — **RESOLVED: source lists variants separately**

Confirmed in the newborn XLSX (`Михајло` vs `Михаило`, §9.1 above; see
`docs/DATA_NOTES.md` §5 for the full writeup). Each variant is its own
`given_name` row. Clusters group them for search and display only, never for
computation. The §7.2 split-name state is a **routine occurrence, not a rare
edge case**, and ships in Phase 1 as originally planned. Do not auto-cluster by
edit distance or phonetic similarity — `Јована` and `Јана` are both observed,
distinct names, not variants of each other; clustering decisions for anything
beyond exact transliteration mapping are `decided_by = 'manual'` with a
`decision_note`.

Either way, `decided_by` and `decision_note` record how the bridging was decided.
Nothing about merging is implicit.

---

## 10. Build order

Five of eight features need only T3 and the XLSX files. Three need T1–T2, where
all the parsing risk sits. Build by source, not by feature list.

| Step | Work | Unlocks | Est. |
|------|------|---------|------|
| **0** | Phase 0 checklist + send the RZS request | — | 1–2 h |
| **1** | Parse **T3** (~1,700 rows, one table shape) + load XLSX + schema | Features **2, 7, 8**, national parts of **3, 5**, and §7.2 | 8–10 h |
| **2** | **Ship it.** A working public site exists from here on. | — | — |
| **3** | Parse **T1–T2** with the validation harness | Features **1, 4, 6**, geographic parts of 3, 5 | 12–15 h |
| **4** | Persistence, entry/exit lists, generation comparison, municipality-vs-national | §7.3–7.5 | 6–8 h |
| **5** | Docker, VPS, TLS, attribution | — | 2–3 h |

**Total ~35 h.**

The point of this ordering: if T1–T2 parsing stalls, you have a live product
instead of an empty repository. T3 is one table with one row shape — by far the
cheaper parse, carrying the most shareable feature.

Starting with the map because it is the most striking was rejected: it puts the
whole project behind its own hardest component.

---

## 11. Ingestion

### 11.1 XLSX

`openpyxl` or `pandas.read_excel`. One loader per year →
`data/normalized/newborn_<year>.csv`.

Intermediate CSV convention throughout: **separator `;`, UTF-8 with BOM, dates
`DD.MM.YYYY`, decimal comma.**

### 11.2 Census PDF

`pdfplumber` with explicit per-column bounding boxes. Do not trust automatic table
detection.

Known hazards, all handled explicitly:

1. **Split tables across facing pages.** Ranks I–V left, VI–X right, cohort/year
   label repeated **but on opposite sides of the two pages** (leftmost column on
   the left page, rightmost column on the right page — not a mirrored layout).
   Stitch by (municipality, cohort) key, not page order or column position.
2. ~~Digraph corruption~~ **Does not apply.** Phase 0 confirmed the publication
   is printed entirely in **Cyrillic** (`Љиљана`, `Ђорђевић`), not a Latin
   transliteration — there is no `LJiljana`-style all-caps artifact to recover
   from. `given_name.source_form` stores the Cyrillic string verbatim; a
   Cyrillic→Latin transliteration (clean 1:1 script mapping, standard digraph
   rules `Љ`→`Lj`, `Њ`→`Nj`, `Џ`→`Dž`) feeds `search_key` and any Latin display
   form, same as for the newborn XLSX files.
3. **Diacritics.** Cyrillic equivalents of `š č ć ž đ` (`ш ч ћ ж ђ`) must
   survive — confirmed clean in the Phase 0 sample, no mojibake. If mojibake
   ever appears, it means non-standard font encoding — fall back to per-glyph
   mapping, never guess.
4. **Name collisions.** Municipalities share names with districts (Šabac, Niš).
   Join on `code_rzs`, never on the name string.
5. **Belgrade.** Both the 17 individual city municipalities and one Republic-
   facing aggregate row exist in the source (§9.2 finding) — decide which
   feeds `census_rank.municipality_id`, document it here once decided.
6. **`extract_text()` layout artifacts.** On some pages (title/cover, some
   table headers) `pdfplumber`'s plain text extraction interleaves characters
   from overlapping layout boxes into garbled strings. This is a z-order
   artifact, not a font-encoding problem — don't mistake it for hazard #3.
   Bounding-box extraction per column (already the plan) avoids it.

**The parser never fills gaps.** An unreadable cell is `NULL` — never inferred,
never interpolated from neighbouring rows, never taken from the national list.

### 11.3 Validation invariants

The loader refuses to commit if any fail:

- Every municipality has exactly 9 cohorts (corrected by Phase 0 — see §9.1).
- Every (municipality, cohort, gender) has ranks 1..10 with no gaps — allowing
  ties if Phase 0 found them.
- Every name in `census_rank` resolves to a `given_name` row.
- Municipality count matches the RZS register.
- Every known fact in §3.1 reproduces exactly.
- Every row's `source_key` exists in `data_source`.
- No API response carries `evidence: "observed"` for a computed value.

---

## 12. API

```
GET  /api/name/{search_key}?gender=M|F
     → one block per matching given_name (may be several, §7.2);
       each with timeline, map, stats, and its own source attribution

GET  /api/generation/{year}
     → national top 10 M/F for that birth year (T3)

GET  /api/generation/compare?a=1988&b=2008
     → entered / left / present in both

GET  /api/municipality/{slug}
     → top 10 by cohort and gender, with national rank or not_in_top10

GET  /api/cohort/{cohort_id}
     → national top 10 for that cohort, and municipalities that deviate

GET  /api/compare?a=Goran&b=Zoran&gender=M
     → rank positions on a shared inverted axis

GET  /api/newborn/{year}?gender=M|F
GET  /api/suggest?q=gor          → prefix match on search_key, limit 10
GET  /api/surname/{surname}      → approximate count, or evidence: unknown
```

`/api/name` returning a structured payload with `timeline`, `map` and `stats`
blocks is preferred to separate routes that re-query the same rows.

**No 404 for an unobserved name.** A name with no rows is a legitimate answer, not
an error. Return `200` with `evidence: "unknown"`, `status: "not_observed"`,
`reason: "source_is_top10_only"` — and per §8.1, do not attempt to distinguish
"not in our index" from "exists but not in the top 10", because we cannot.

---

## 13. Local development (Windows)

```
C:\projects\imena-rs\
├── data\
│   ├── raw\              # downloaded PDF and XLSX, never edited
│   ├── normalized\       # parser output, ';' + UTF-8 BOM
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
│   └── DATA_NOTES.md     # ← Phase 0 output
├── requirements.txt
└── docker-compose.yml
```

```powershell
cd C:\projects\imena-rs
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

PostgreSQL via Docker Desktop, not a native Windows install — keeps dev identical
to the VPS.

```
fastapi           # API framework
uvicorn[standard] # ASGI server
sqlalchemy        # ORM
psycopg[binary]   # PostgreSQL driver
pydantic          # request/response models
alembic           # migrations
pdfplumber        # PDF table extraction with bbox control
openpyxl          # XLSX reading
python-dotenv     # config
pytest            # tests
```

---

## 14. Claude Code subagents

Three agents under `.claude/agents/`. The separation prevents the failure mode
where the parser gets tuned to satisfy the validator instead of reading the
document.

**`pdf-extractor.md`** — worker. `tools: Read, Write, Edit, Bash`. Parses **one
district per invocation**, never the whole PDF. Writes
`data/normalized/{oblast}.csv`. Unreadable cells are `NULL`, never inferred.

**`data-reviewer.md`** — reviewer. `tools: Read, Bash` — **deliberately no
Write**. Checks the §11.3 invariants and returns a list of violations only. A
reviewer that can patch data will patch data. Also checks evidence-class
integrity: no response carries `evidence: "observed"` for a computed value.

**`test-runner.md`** — `tools: Bash, Read`. Runs `pytest` against
`tests/fixtures/` — three PDF pages transcribed by hand and verified by eye. The
only real ground truth in the project.

**Orchestration rule:** the extractor never receives the reviewer's output
directly. You read the violations, decide whether the fault is in the parser or in
the source, then issue a specific instruction. Wiring reviewer → extractor
produces a loop that converges on passing the validator rather than on correct
data.

---

## 15. Out of scope for v1

Login · user accounts · AI features of any kind · unsourced etymology or
name-meaning summaries · external name dictionaries not tied to a checkable
primary source (§8.1, §16.1) — a curated, citation-bearing historical
attestation corpus is in scope, see §16; a general meaning/origin dictionary is
not · algorithmic similar-name suggestions (§5.1) · React or any frontend
framework · Redis · Elasticsearch · microservices · Kubernetes.

The dataset is roughly 40,000 rows. PostgreSQL and vanilla JS are not a compromise
here — they are correctly sized.

---

## 16. Historical layer

A second, editorially curated corpus alongside the statistical one (§1–§15).
Where §1–§15 answer "how common is this name today, and where" from
government publications, this layer answers "is this name attested before
modern record-keeping, in what document, and how sure are we." The two
corpora are never merged into one number or one confidence score — a name's
historical page and its statistical page are always presented as separate,
independently sourced answers.

### 16.1 Why this is not what §15 forbade

§15 excluded "etymology or name-meaning layer" and "external name
dictionaries." That rule targeted a specific failure mode: an unsourced list
of "Name X means Y, origin: Slavic" copied from some other website, sitting
inside a statistics product and borrowing its trust without earning it
(§8.1's core argument, verbatim: "an unsourced list inside a statistics
product damages the thing that makes it trustworthy").

This layer is not that. Every row cites a named, checkable document — a
charter, a monastery pomenik, an Ottoman defter, or a published academic
paper with author and year — never a general-purpose etymology dictionary,
never a meaning/origin summary invented or scraped without a citation. §15's
ban on external name dictionaries and unsourced etymology **stays in force**.
What changes is narrower: a curated, citation-bearing historical corpus is
now in scope, with its own confidence taxonomy (§16.2) precisely so that
"attested in document X" is never confused with "this is what the name
means" or "this name is common."

### 16.2 Historical confidence — a field, not a replacement for `evidence`

`evidence` (§4) still governs every value: a historical attestation that
exists is `evidence: "observed"`, `status: "observed"` — we read it in a
named source. A period/name combination with no attestation is
`evidence: "unknown"`, `status: "not_observed"`, `reason:
"no_historical_source_for_period"` (§4.2).

`historical_confidence` is an **additional, independent field** on every
historical attestation, answering "how much should this specific source be
trusted for this specific claim" — not "do we know it" (that is what
`evidence` already answers) but "should this be presented as fact, as
attested, or as speculation."

| Level | Meaning | Example source | May render as |
|-------|---------|-----------------|----------------|
| **A** | Statistically proven — census, civil registry, a source with a real denominator | RZS, matične knjige | "najčešće ime [perioda/opštine]" |
| **B** | Quantitative historical source — a corpus large enough to support a frequency claim | Defter sa brojem pojavljivanja, veliki korpus povelja | "među najčešće zabeleženim imenima" |
| **C** | Attested — the name appears in one or more authentic period documents | Jedna povelja, jedan pomenik | "ime je potvrđeno u ovom periodu" |
| **D** | Reconstructed or inferred — etymological reconstruction, a later form projected backward without a dated attestation | Pretpostavljeni praslovenski oblik | never "potvrđeno"; must render as "pretpostavljeno" or "rekonstruisano" with the reasoning source cited |

Levels A and B are functionally different from C and D in one critical way:
**only A and B may ever support a frequency or ranking claim** ("most
common", "among the most attested"). C and D may only support an
*existence* claim ("this name is attested / this name is a proposed
reconstruction"), never a frequency claim — because a handful of surviving
charters is not a sample anyone can generalize from (§16.3 rule 1).

### 16.3 Hard rules

1. **No frequency or ranking claim below confidence B.** "Najčešće ime
   srednjeg veka" or any equivalent must never be generated from
   confidence-C or -D rows, regardless of how many C-level attestations
   exist for a name — attestation count is not sample size. This mirrors
   §5.1's rule that absence of counts caps what a rank can mean; here,
   absence of a real corpus caps what an attestation count can mean.
2. **Confidence D is never shown as an attested fact.** UI copy for a
   `historical_confidence: "D"` row must use `pretpostavljeno` /
   `rekonstruisano` language and must surface the reasoning source. No copy
   string may present a D-level name form the same way a C, B, or A form is
   presented.
3. **No population claim from a historical attestation.** "This name was
   common in the 14th century" is a claim about a population; an
   attestation is a claim about a document. A count of surviving
   attestations describes the surviving corpus, not the medieval
   population, and any copy generated from `attestation_count` must say so
   explicitly (mirrors §8.1's "we cannot distinguish absence in the source
   from absence in reality").
4. **No merging of the historical corpus with the statistical corpus**
   (§6.6's rule extended). A name's historical timeline and its RZS-era
   timeline (1940–2025) are shown as two separate blocks, never stitched
   into one continuous "popularity through history" line — the two corpora
   have incompatible evidentiary bases (one is a full-population
   census/registry, the other is a survivorship-biased documentary record).
5. **Every historical row cites a real, checkable source.** No row without
   a source may exist — enforced at the schema level (NOT NULL FK), not
   just by convention.
6. **Variant/cognate grouping across centuries is always `manual` or
   `historical_variant` in `name_cluster`, never automatic.** Unlike modern
   digraph folding (§9.5 / BRANCH B), a centuries-spanning claim like
   "Stepan is the same name as Štefan" is a linguistic argument, not a
   mechanical transformation, and always requires a `decision_note` citing
   the reasoning.
7. **`region`, when present, describes where the document was found or what
   territory it covers — never projected onto modern municipality
   boundaries.** A Smederevski sandžak defter is not equivalent to a modern
   opština; never join historical `region` text to `municipality` rows.

### 16.4 Data model

Extends §6's convention (`source_form` is authoritative, `search_key` is for
lookup only) rather than replacing it. Historical sources are rows in the
existing `data_source` table (§6.6) with `measure = 'attestation'` — a
`given_name` row for a historical form points at one of these via the same
`source_key` column every other `given_name` row already uses, so
`/api/suggest` and the search-key index work for historical names with no
schema change to `given_name` at all.

```sql
-- 1:1 extension of a data_source row whose measure = 'attestation'.
CREATE TABLE historical_source_meta (
    data_source_key   TEXT PRIMARY KEY REFERENCES data_source(key),
    author            TEXT,                -- modern editor/scholar, if applicable
    publication_year  INT,                 -- year of the modern edition/analysis, not the document
    source_type       TEXT NOT NULL CHECK (source_type IN
                          ('charter','monastery_register','ottoman_defter',
                           'academic_paper','other')),
    citation          TEXT NOT NULL
);

CREATE TABLE historical_name_attestation (
    id                     BIGSERIAL PRIMARY KEY,
    given_name_id          INT NOT NULL REFERENCES given_name(id),
    period_start           INT,             -- year, nullable (century-level precision only)
    period_end             INT,
    region                 TEXT,            -- free text, document's own territory — §16.3 rule 7
    name_type              TEXT CHECK (name_type IN
                                ('native_slavic','christian','noble','folk','other')),
    historical_confidence  TEXT NOT NULL CHECK (historical_confidence IN ('A','B','C','D')),
    frequency_level        TEXT CHECK (frequency_level IN
                                ('dominant','very_common','common','attested','rare','uncertain')),
    attestation_count      INT,             -- nullable; only meaningful with confidence B
    citation_note          TEXT NOT NULL    -- page/folio/entry reference within the source
);
CREATE INDEX ON historical_name_attestation (given_name_id);
CREATE INDEX ON historical_name_attestation (historical_confidence);
```

`frequency_level` is categorical by design (§16.2 / §16.3 rule 1) — there is
no numeric `frequency_rank` column, because ranking implies a comparable
population across candidates, which the historical corpus cannot supply
except at confidence B.

`name_cluster_member.decided_by` (§6.2) gains a fifth value,
`'historical_variant'`, alongside `exact_match` / `digraph_normalization` /
`manual` — for centuries-spanning form grouping (§16.3 rule 6).
`decision_note` stays mandatory whenever `decided_by` is `manual` or
`historical_variant`.

### 16.5 Feature: "Istorijska imena Srbije"

A dedicated page, filterable by period and `name_type`, plus a per-name "Ime
kroz istoriju" block linked from the name page. Never folded into §7.1's
four required statistical blocks — always a clearly separate, clearly
labeled section or link, so a reader is never in doubt about which corpus a
given claim came from.
