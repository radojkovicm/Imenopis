"""Builds the municipality/district seed data from the census PDF's own
table of contents (via toc_extractor.py), for §6.3's municipality/district
tables.

Ground truth summary (verified by running this against G20244001.pdf,
see docs/DATA_NOTES.md): 140 plain opština entries, 5 multi-district
"Grad X" rollups (Beograd 17, Užice 2, Požarevac 2, Niš 5, Vranje 2 = 28
sub-districts total) whose sub-districts are the real
census_rank.municipality_id targets for those cities, and 25 oblasts
(matching src/ingest/geography.py's DISTRICT_CODES built earlier from the
newborn XLSX files - same 25 districts, independently confirmed from a
second source). 140 + 28 = 168 real municipality-level units (the 5 "Grad X"
rows themselves are NOT separate municipality rows - they're display-only
aggregates, per the Belgrade decision below). Note "Палилула" is a genuine
naming collision, not a bug: it's both a Belgrade opština and a Niš city
district, kept as two distinct rows disambiguated by code_rzs.

**Belgrade decision (PROJECT.md §11.2 hazard #5, §9.2 finding):** both the
17 individual opštine and one Beograd-wide aggregate row exist in the source.
This loader feeds census_rank from the 17 opštine (and Niš/Užice/Požarevac/
Vranje's sub-districts) - the finer-grained, auditable rows - and does NOT
also load the 5 "Grad X" aggregate rows into census_rank, because that would
let the same person be double-counted at two municipality granularities
under the same municipality_id space. The aggregate text is still visible in
the PDF for a user reading the source directly, but this app's map/search
only ever shows the district-level constituent rows.

code_rzs is NOT the real RZS registry code (§3.3's spatial register isn't
integrated - out of scope for Phase 1). It's a stable slug of the Cyrillic
name, sufficient to join census_rank.municipality_id today; swapping in real
RZS codes later is a data migration, not a schema change (code_rzs is just a
TEXT UNIQUE column per §6.3).
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from src.ingest.geography import DISTRICT_CODES
from src.ingest.toc_extractor import GRAD_SUBDISTRICTS, GRAD_WITH_SUBDISTRICTS, classify_entries, extract_toc_entries
from src.util.normalize import make_search_key


@dataclass
class DistrictSeed:
    code: str
    name: str


@dataclass
class MunicipalitySeed:
    code_rzs: str
    name: str
    name_slug: str
    district_code: str | None  # None for a Grad-subdistrict whose parent isn't a plain oblast
    # Matches t1t2_parser.MunicipalityRankRow.parent_grad exactly, so the two
    # can be joined on (name, parent_grad) to disambiguate a real naming
    # collision like "Палилула" (Belgrade opština vs Niš city district).
    # None only for the 140 plain municipalities. Every "Grad X" subdistrict
    # - including Belgrade's 17 opštine - carries its parent's exact TOC
    # label string (e.g. "Београдска област (Град Београд)", "Град Ниш"),
    # matching what the parser tags cohort rows with.
    parent_grad: str | None = None


def _slugify(name: str) -> str:
    ascii_name = make_search_key(name)
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
    return slug


def build_district_seeds() -> list[DistrictSeed]:
    return [DistrictSeed(code=code, name=name) for name, code in DISTRICT_CODES.items()]


# Which oblast each of the 5 "Grad X" entries administratively belongs to -
# read directly off the TOC's page-order context (each Grad row is nested
# under its oblast in the source, e.g. Grad Niš falls under Нишавска област).
# Not derivable purely from GRAD_SUBDISTRICTS, so recorded explicitly here.
GRAD_PARENT_DISTRICT = {
    "Београдска област (Град Београд)": None,  # Belgrade is its own top-level oblast, not nested under another
    "Град Ужице": "Златиборска област",
    "Град Пожаревац": "Браничевска област",
    "Град Ниш": "Нишавска област",
    "Град Врање": "Пчињска област",
}


def build_municipality_seeds(pdf_path: Path) -> list[MunicipalitySeed]:
    entries = extract_toc_entries(pdf_path)
    classified = classify_entries(entries)
    oblast_names = set(DISTRICT_CODES.keys())

    # name -> district_code, for every plain municipality: the district it
    # follows in TOC page order (municipalities are listed immediately after
    # their oblast heading, in ascending page order).
    seeds: list[MunicipalitySeed] = []
    current_district_code: str | None = None

    for e in classified:
        name, level = e["name"], e["level"]
        if level == "rollup":
            continue
        # Check grad_with_subdistricts BEFORE oblast_names: Belgrade's TOC
        # entry, "Београдска област (Град Београд)", is *also* the exact
        # string used for Belgrade's district in DISTRICT_CODES (they share
        # a name in the source - Belgrade's district and its "Grad X"
        # rollup are the same administrative unit). Checking oblast_names
        # first would treat it as a plain oblast and silently skip emitting
        # its 17 opštine - confirmed as the actual bug when this produced 0
        # Belgrade municipalities instead of 17 in testing.
        if level == "grad_with_subdistricts":
            # its sub-districts are the real municipality rows; the parent
            # itself is a display-only aggregate (see module docstring)
            parent_oblast = GRAD_PARENT_DISTRICT[name]
            district_code = DISTRICT_CODES[parent_oblast] if parent_oblast else None
            for sub_name in sorted(GRAD_SUBDISTRICTS[name]):
                seeds.append(
                    MunicipalitySeed(
                        code_rzs=_slugify(f"{name}-{sub_name}"),
                        name=sub_name,
                        name_slug=_slugify(sub_name),
                        district_code=district_code,
                        parent_grad=name,
                    )
                )
            continue
        if level == "subdistrict":
            # already emitted as part of its grad_with_subdistricts parent
            continue
        if name in oblast_names:
            current_district_code = DISTRICT_CODES[name]
            continue
        # plain municipality
        seeds.append(
            MunicipalitySeed(
                code_rzs=_slugify(name),
                name=name,
                name_slug=_slugify(name),
                district_code=current_district_code,
            )
        )

    return seeds
