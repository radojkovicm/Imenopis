"""§16 historical layer ingestion. Standalone entry point, deliberately NOT
a step in load_all.py: the statistical pipeline (load_all.py) re-parses
real source files (PDF/XLSX) and is idempotent against their presence, but
the historical layer is hand-curated Python data with no source file to
re-run against - its lifecycle is "edited by hand, reviewed, re-run only
when new entries are added", not "re-run whenever a new year's data drops".

Run with: py -3.11 -m src.ingest.load_historical
"""

from src.db.session import get_session, init_db
from src.ingest.historical_seed import load_historical_seed
from src.ingest.seed_sources import historical_data_source_rows, historical_source_meta_rows


def main() -> None:
    init_db()
    session = get_session()
    try:
        for row in historical_data_source_rows():
            session.merge(row)
        session.commit()

        for row in historical_source_meta_rows():
            session.merge(row)
        session.commit()

        count = load_historical_seed(session)
        print(f"Historical layer: loaded {count} attestation rows")
    finally:
        session.close()


if __name__ == "__main__":
    main()
