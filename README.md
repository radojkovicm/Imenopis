# Imenopis

**Imenopis** is an evidence-first explorer of given names in Serbia. It lets
people look up a name, follow its ranking across birth years and generations,
compare local and national top-ten lists, and browse a small, separately
curated historical layer.

Live at **[imenopis.vercel.app](https://imenopis.vercel.app)**. The
`imenopis.rs` domain is the intended long-term public name.

> Serbian interface · Cyrillic and Latin display modes · rank data, not name counts

## What is available today

- Search Serbian given names in either script; the display can be switched
  between Cyrillic and Latin.
- Explore national rankings by single year of birth from the 2022 Census
  publication (1941–2022, top 5 per gender).
- Browse annual newborn-name rankings for 2021–2025 (Republic and district
  level, top 10 per gender).
- Browse top-ten names across nine generational cohorts for **168 Serbian
  municipalities and city municipalities**, with national comparison.
- See top-ten persistence, entry/exit lists, and cross-decade generation
  comparisons.
- Browse an initial proof-of-concept historical corpus with sources,
  period, name type, and confidence level.

## Data and evidence model

Imenopis deliberately reports only what its sources can support.

| Data layer | Source | Coverage | What it represents |
| --- | --- | --- | --- |
| Census names | Statistical Office of the Republic of Serbia (RZS), *Most Common Names and Surnames*, Census 2022 | 1941–2022; Republic by individual birth year; municipality/cohort rankings | Published rankings only; no counts are inferred |
| Newborn names | RZS annual vital-statistics spreadsheets | 2021–2025; Republic and district rankings | Published top-ten rankings only |
| Historical names | Curated, citation-bearing historical sources | Initial five-record proof of concept | Historical attestations, not population-wide popularity claims |

The database and API distinguish `observed`, `derived`, and `unknown` values.
Absence from a top-ten source does **not** mean that a name was absent from the
population. It only means the source does not establish a top-ten placement.

Historical attestations use a second, independent confidence scale:

- **A** — statistically proven source
- **B** — quantitative historical source
- **C** — historically attested source
- **D** — reconstructed or uncertain interpretation

The historical corpus is kept separate from modern RZS statistics. A
historical mention is never presented as a modern ranking, and modern ranking
data is never projected backwards into history.

## Sources

- [RZS — Most Common Names and Surnames, Census 2022](https://publikacije.stat.gov.rs/G2024/Pdf/G20244001.pdf)
- [RZS — population statistics and annual newborn-name releases](https://www.stat.gov.rs/sr-latn/oblasti/stanovnistvo/)

Detailed source findings, parsing constraints, and known data anomalies are
documented in [docs/DATA_NOTES.md](docs/DATA_NOTES.md). The authoritative
project specification is [PROJECT.md](PROJECT.md).

## Technology

- Python 3.11+
- FastAPI and Pydantic
- SQLAlchemy
- SQLite, bundled prebuilt (`imena.db`) — this site has no data that changes
  at request time, so the whole database ships with the deployment instead of
  needing a provisioned one; PostgreSQL 16 remains available for a
  containerized deployment (`docker-compose.yml`)
- Vanilla HTML, CSS, and JavaScript (no frontend build step)
- `pdfplumber` and `openpyxl` for source ingestion (dev-only, not part of the
  deployed app)

## Deployment

The production site runs on Vercel as a Python serverless function
(`api/index.py` re-exports the FastAPI app; see `vercel.json`). It deploys
automatically from `main`. `imena.db` is committed to the repo and copied to
`/tmp` on cold start, since the deployment bundle's filesystem is read-only.

## Run locally (Windows)

Prerequisites: Python 3.11 or later and Git.

```powershell
git clone https://github.com/radojkovicm/Imenopis.git
cd Imenopis
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.11 -m pip install -r requirements.txt
```

The repository includes the RZS source files and normalized newborn extracts.
Create the local database and load the statistical and historical records:

```powershell
py -3.11 -m src.ingest.load_all
py -3.11 -m src.ingest.load_historical
```

Start the application:

```powershell
py -3.11 -m uvicorn src.api.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API
documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

To stop the development server, press `Ctrl+C` in the terminal that started it.

### Test

After loading both data layers, run:

```powershell
py -3.11 -m pytest tests/ -q
```

## API overview

| Endpoint | Purpose |
| --- | --- |
| `GET /api/name/{search_key}` | Name timeline, municipal presence, persistence, and historical availability |
| `GET /api/generation/{year}` | National top-five names for one birth year |
| `GET /api/generation/compare?a=1988&b=2008` | Compare two birth years |
| `GET /api/generation/across-decades` | Cross-decade generation view |
| `GET /api/newborn/{year}` | Newborn top-ten rankings for 2021–2025 |
| `GET /api/municipality/{slug}` | Municipal top tens by cohort and national comparison |
| `GET /api/cohort/{cohort_id}` | Cohort-level municipality comparison |
| `GET /api/suggest?q=gor` | Name autocomplete |
| `GET /api/historical` | Filtered historical-attestation list |
| `GET /api/historical/{search_key}` | Historical attestations for a name |

## Development notes

The project currently focuses on trustworthy ingestion and representation of
published rankings. It does not claim to know the number of people with a
name, nor rank names outside the source's published top-ten/top-five window.

Planned work includes a modern visual redesign, map presentation, and
expansion of the sourced historical corpus.

## License and attribution

Code-license terms have not yet been selected. Source material remains
attributed to RZS and to each cited historical source. Reuse of the underlying
official data should follow the relevant publisher terms.
