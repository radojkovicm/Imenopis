"""Census PDF Table 3 parser (PROJECT.md §11.2, Step 1 of §10 build order).

Table 3 only, for Phase 1 (Republic-level, single birth year 1940-2022, both
genders). Tables 1/2/4/5 (municipality-level, the hard parse) are Step 3 of
the build order - not attempted here.

**Correction found while building Phase 1, not caught during Phase 0's
sampling**: Table 3 publishes ranks I-V only (top 5), not I-X (top 10) like
Tables 1/2/4. There are exactly 4 pages total - 222 (female I-V, 1940-1981),
223 (male I-V, 1940-1981), 224 (female I-V continued, 1982-2022), 225 (male
I-V continued, 1982-2022) - confirmed by checking every page in that range for
a "VI VII VIII IX X" header, which never appears. PROJECT.md §6.5's
`census_rank_by_year.rank` has no CHECK constraint restricting it to 1-10 (only
census_rank does), so this doesn't need a schema change - just don't expect
ranks 6-10 to exist for this table. Update docs/DATA_NOTES.md if this
parser output is later cross-checked against the PDF again.

Line format confirmed by Phase 0: the year label sits on whichever side is
adjacent to the row's start in reading order - first token on female pages
("<year> <name1..5>"), last token on male pages ("<name1..5> <year>"). Both
orientations are handled by `_extract_year_and_names`.

The whole document is Cyrillic; no digraph-corruption hazard applies (see
PROJECT.md §11.2 note 2). pdfplumber's extract_text() can interleave
overlapping layout boxes on some pages (title/header rows, not these table
body pages) - not an issue for Table 3's plain row-per-line layout.

The parser never fills a gap: a year with fewer than 5 ranks found becomes a
short list, not a guess, and the validator (src/ingest/validate.py, Phase 3)
is responsible for deciding whether that's acceptable.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

YEAR_RE = re.compile(r"^\d{4}$|^1940\.$")


@dataclass
class YearRankRow:
    birth_year: int | None  # None for the open-ended "1940 and earlier" bucket
    year_label: str  # verbatim as printed, e.g. '1940. и раније' or '1987'
    gender: str  # 'M' or 'F'
    rank: int
    source_form: str


MIN_YEAR = 1900
MAX_YEAR = 2100


def _is_year_token(tok: str) -> bool:
    stripped = tok.rstrip(".")
    return stripped.isdigit() and MIN_YEAR <= int(stripped) <= MAX_YEAR


def _extract_year_and_names(line_text: str) -> tuple[str, list[str]] | None:
    """Parse one text line of the form '<year> <name1> <name2> ... <name5>'
    or '<name1> ... <name5> <year>' (the label can be on either side,
    confirmed by Phase 0) into (year_label, [names]).

    Returns None for lines that aren't a data row at all - e.g. page-footer
    lines like '220 popis2022.stat.gov.rs', which have a leading token that
    looks like a year but isn't followed by 5 Cyrillic names. Exactly 5 names
    are required (Table 3 publishes ranks I-V only, confirmed in this
    module's docstring) - a different count means this wasn't a data row.
    """
    tokens = line_text.split()
    if not tokens:
        return None

    # "1940. и раније" spans 3 tokens; a plain year is 1 token.
    if len(tokens) >= 4 and tokens[0] == "1940." and tokens[1] == "и" and tokens[2] == "раније":
        names = tokens[3:]
        if len(names) == 5:
            return "1940. и раније", names
        return None

    if tokens[-3:] == ["1940.", "и", "раније"]:
        names = tokens[:-3]
        if len(names) == 5:
            return "1940. и раније", names
        return None

    if _is_year_token(tokens[0]):
        names = tokens[1:]
        if len(names) == 5:
            return tokens[0], names
        return None

    if _is_year_token(tokens[-1]):
        names = tokens[:-1]
        if len(names) == 5:
            return tokens[-1], names
        return None

    return None


def _year_label_to_int(label: str) -> int | None:
    if label.startswith("1940"):
        return None
    return int(label)


def parse_table3_block(pages_text: list[str], gender: str) -> list[YearRankRow]:
    """Parse a sequence of extracted page-text blocks belonging to Table 3's
    female or male section into rank rows. Each page contributes ranks I-V or
    VI-X for the same set of years; the caller is responsible for passing
    left/right page pairs in order so rows can be merged by year label.
    """
    by_year: dict[str, list[str]] = {}
    order: list[str] = []

    for page_text in pages_text:
        for line in page_text.splitlines():
            parsed = _extract_year_and_names(line.strip())
            if not parsed:
                continue
            year_label, names = parsed
            if not names:
                continue
            if year_label not in by_year:
                by_year[year_label] = []
                order.append(year_label)
            by_year[year_label].extend(names)

    rows: list[YearRankRow] = []
    for year_label in order:
        names = by_year[year_label]
        birth_year = _year_label_to_int(year_label)
        for rank, name in enumerate(names, start=1):
            rows.append(
                YearRankRow(
                    birth_year=birth_year,
                    year_label=year_label,
                    gender=gender,
                    rank=rank,
                    source_form=name,
                )
            )
    return rows


# Confirmed by Phase 0/1 inspection of G20244001.pdf (2022 census edition).
# Re-verify if the PDF is ever regenerated with a different page count.
TABLE3_FEMALE_PAGES = [222, 224]
TABLE3_MALE_PAGES = [223, 225]


def parse_table3(
    pdf_path: Path,
    female_pages: list[int] = TABLE3_FEMALE_PAGES,
    male_pages: list[int] = TABLE3_MALE_PAGES,
) -> list[YearRankRow]:
    """female_pages / male_pages: 1-indexed PDF page numbers containing Table 3
    for that gender, in reading order. Defaults are the confirmed pages for
    G20244001.pdf; pass explicit lists for a different edition.
    """
    with pdfplumber.open(pdf_path) as pdf:
        female_text = [pdf.pages[p - 1].extract_text() or "" for p in female_pages]
        male_text = [pdf.pages[p - 1].extract_text() or "" for p in male_pages]

    rows = parse_table3_block(female_text, "F")
    rows += parse_table3_block(male_text, "M")
    return rows
