"""Table 1 (female names) / Table 2 (male names) parser — the municipality-
level census ranks (PROJECT.md §11.2, Step 3 of §10's build order).

Confirmed by Phase 0/3 (docs/DATA_NOTES.md §4, §7):
- Facing-page split: left page has cohort/geography label in the leftmost
  column then ranks I-V; right page has ranks VI-X then the label in the
  RIGHTMOST column (label side flips, not a mirrored copy).
- 9 cohorts per municipality (not 11), always in the same order.
- Whole document is Cyrillic; no digraph-corruption hazard.
- No position-only rule reliably separates a geography-label row from a
  cohort-label row at every nesting depth (a "Grad Ниш" sub-district row
  lands at the same x as a cohort row) - only matching row text against the
  known 9 cohort labels is reliable.
- Row grouping MUST use tolerance-based clustering
  (pdfplumber.utils.cluster_objects), not round(top, N) - sub-point jitter
  between words on the same line has caused real data loss (§7.2 of
  docs/DATA_NOTES.md).
- Geography labels can wrap across multiple `top` values (e.g. "Београдска
  област (Град Београд)" prints on 3 lines, with the row's 5 names landing
  on the middle line's `top`, not the first or last).

Parsing strategy: walk each page's rows top-to-bottom. A row is a *cohort
row* if its text starts with one of the 9 known cohort labels (from
src/ingest/cohorts.py) - unambiguous, since cohort labels never collide with
a geography name. Any other row either continues the current geography
label (if no cohort row has been seen since the last confirmed geography
row) or starts a new one. A geography row transitions when we see a
non-cohort row whose leftmost word matches a name from the geo_seed-built
municipality list (src/ingest/geo_seed.py) - matching against real known
names, not position, avoids the Table-3-B-style ambiguity entirely.

Left/right page pairing: rows are matched by nearest `top` (within a
tolerance), not equality - the two pages' cohort rows are typeset
independently and can drift by a point or two.

The parser never fills a gap: a municipality with fewer than 9 cohorts, or a
cohort with fewer than 10 ranks, is recorded as-is and surfaced by the
validator (src/ingest/validate.py) - never padded or guessed.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from src.ingest.cohorts import COHORT_LABELS
from src.ingest.toc_extractor import GRAD_SUBDISTRICTS, GRAD_WITH_SUBDISTRICTS

# Table 1 = female names, Table 2 = male names, in G20244001.pdf.
# 0-indexed pdfplumber page numbers, confirmed by Phase 3 inspection.
TABLE1_PAGE_RANGE = (13, 115)  # pdf pages 14-115 inclusive (0-indexed 13-114)
TABLE2_PAGE_RANGE = (117, 219)  # pdf pages 118-220 inclusive (0-indexed 117-219)

ROW_CLUSTER_TOLERANCE = 3
LEFT_RIGHT_MATCH_TOLERANCE = 4  # max 'top' drift allowed when pairing a left-page row with its right-page counterpart


@dataclass
class MunicipalityRankRow:
    geography_label: str  # verbatim as printed - may be a region/oblast rollup OR a real municipality
    parent_grad: str | None  # disambiguates naming collisions, e.g. "Палилула" under "Град Ниш" vs Belgrade
    cohort_label: str
    gender: str
    rank: int
    source_form: str
    page_left: int  # 0-indexed pdf page the rank came from (I-V side)
    page_right: int | None  # 0-indexed pdf page for VI-X, if matched


@dataclass
class PageRow:
    top: float
    words: list[dict]

    @property
    def text(self) -> str:
        return " ".join(w["text"] for w in self.words)


def _cluster_rows(words: list[dict]) -> list[PageRow]:
    clusters = pdfplumber.utils.cluster_objects(words, key_fn=lambda w: w["top"], tolerance=ROW_CLUSTER_TOLERANCE)
    rows = []
    for cluster in clusters:
        cluster_sorted = sorted(cluster, key=lambda w: w["x0"])
        rows.append(PageRow(top=min(w["top"] for w in cluster), words=cluster_sorted))
    return sorted(rows, key=lambda r: r.top)


def _match_cohort_label(text: str) -> str | None:
    """Matches a cohort label at the START of the row (left/I-V page shape:
    '<cohort> <name1..5>'). Use _match_cohort_label_suffix for the right/
    VI-X page shape, where the cohort label is the LAST token(s) instead
    ('<name6..10> <cohort>') - confirmed by Phase 3 direct inspection, this
    is not a formatting fluke, every right-hand page in T1/T2 is this shape.
    """
    for label in COHORT_LABELS:
        if text.startswith(label):
            return label
    return None


def _match_cohort_label_suffix(text: str) -> str | None:
    for label in COHORT_LABELS:
        if text.endswith(label):
            return label
    return None


def _is_page_furniture(text: str) -> bool:
    # EXACT matches only, or startswith for markers that can never be a
    # true prefix of a real geography label. "Регион" and "Област" as
    # standalone column-header words must be EXACT - a startswith check
    # here would also swallow real geography rows like "Регион Војводине
    # <5 names>" or "Западнобачка област <5 names>", which was a real bug:
    # confirmed it silently dropped an entire "Регион Војводине" data block
    # (9 cohort rows) that then got misattributed to the preceding
    # municipality, doubling its apparent cohort count to 18.
    exact_furniture = {
        "Регион", "Област", "Град – oпштина", "година рођења",
        "НАЈЧЕШЋА", "по општинама и градовима",
    }
    prefix_furniture = [
        "Табела", "Попис становништва", "popis2022", "Републички завод",
        "по општинама и градовима",
    ]
    stripped = text.strip()
    if not stripped:
        return True
    if stripped in exact_furniture:
        return True
    if re.fullmatch(r"[IVX]+(\s+[IVX]+)*", stripped):
        return True  # bare rank-numeral header row, e.g. "I II III IV V"
    if re.fullmatch(r"\d+", stripped):
        return True  # bare page number
    return any(stripped.startswith(m) for m in prefix_furniture)


def parse_page_rows(page: "pdfplumber.page.Page") -> list[PageRow]:
    """One body page (either the I-V/left-hand page or the VI-X/right-hand
    page of a facing pair) is full-width - there is no left/right COLUMN
    split within a single page (that was a property of the TOC's two-column
    layout, a different page type; confirmed by direct inspection that a
    Republic-row's 5 names span x0=66 to x0=419 on one page). The
    left-vs-right distinction in this module refers to which of the two
    FACING PAGES a row came from, not a column boundary within one page.
    """
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    return _cluster_rows(words)


def _split_geography_and_names(row: PageRow, known_names: set[str]) -> tuple[str | None, list[str]]:
    """For a single non-cohort row, figure out which words are the geography
    label and which are the 5 names, when both are on the SAME row (the
    common case: 'РЕПУБЛИКА СРБИЈА Јелена Милица Марија Драгана Мирјана').
    The label can be a prefix or a suffix of the row text - tested both ways,
    matched against known_names (built from geo_seed.py plus the known
    rollup/oblast lists) so there's no ambiguity between a label and a name
    (both are capitalized Cyrillic, so text shape alone can't tell them apart).

    Returns (None, []) when the label isn't on this row at all - see
    _group_geography_rows for the 3-line-wrap case (label above AND below a
    names-only row), which this function alone cannot resolve.
    """
    tokens = [w["text"] for w in row.words]
    for split in range(1, len(tokens)):
        prefix = " ".join(tokens[:split])
        suffix = " ".join(tokens[split:])
        if prefix in known_names:
            names = tokens[split:]
            if len(names) == 5:
                return prefix, names
        if suffix in known_names:
            names = tokens[:split]
            if len(names) == 5:
                return suffix, names
    return None, []


def group_geography_and_data_rows(
    rows: list[PageRow],
    known_names: set[str],
    side: str = "left",
    initial_grad_context: str | None = None,
) -> tuple[list[tuple[str, str | None, list[PageRow]]], str | None]:
    """Walks a page's non-furniture rows and groups them into
    (geography_label, parent_grad, [cohort_rows_that_follow]) blocks.
    Returns (blocks, ending_grad_context) - the caller must thread
    ending_grad_context into the next page's initial_grad_context, since a
    "Grad X" aggregate's subdistrict run can span a page boundary (e.g.
    Belgrade's 17 opštine span many pages - only the first one or two share
    a page with the "Београдска област (Град Београд)" aggregate row
    itself). Without cross-page threading, current_grad_context resets to
    None at the top of every call and only the subdistricts sharing a page
    with their Grad row get tagged correctly - confirmed as a real bug: the
    naming-collision fix below appeared to work in isolated testing only by
    coincidence (Niš's subdistricts all shared one page with "Град Ниш", so
    per-page-reset context still looked right for that one case).

    parent_grad disambiguates real naming collisions: "Палилула" is both a
    Belgrade opština and a Niš city district (docs/DATA_NOTES.md §7) - two
    different real places sharing a name. Without tracking which "Grad X"
    aggregate block most recently preceded a subdistrict row, both collapse
    to the same (geography_label) key downstream and their census_rank data
    gets merged under one municipality_id - confirmed as an actual bug found
    via the validator (src/ingest/validate.py) reporting 15-17 "ranks" in a
    single cell that should have exactly 10, because two different
    municipalities' 10 ranks each were landing in the same bucket.
    parent_grad is the "Grad X" label (from GRAD_WITH_SUBDISTRICTS) if the
    current geography row is one of that Grad's subdistrict rows, else None.

    side: 'left' = the I-V page (cohort label is the row's first token(s):
    '<cohort> <name1..5>'), 'right' = the VI-X page (cohort label is the
    row's LAST token(s) instead: '<name6..10> <cohort>' - confirmed by
    Phase 3 direct inspection). Geography-label rows can have the label as
    either a prefix or suffix regardless of side (both are tried by
    _split_geography_and_names), but cohort-row detection must match the
    correct end or every right-hand-page cohort row is misread as an
    unrecognized geography row (confirmed: this was the actual bug the
    first time this function was tested against a real right-hand page -
    every block came back with 0 cohort rows because _match_cohort_label
    only ever checks the row's start).

    Handles the confirmed 3-line wrap case (docs/DATA_NOTES.md §4, §7.1):
    a geography label can print as <label part 1> / <5 names> / <label part
    2> across three consecutive `top` values, when the label is long enough
    to not fit on the names' own line (only ever seen for "Београдска
    област (Град Београд)" so far, but written generically). Detected here
    as: current row doesn't single-row-split via _split_geography_and_names,
    is exactly 5 tokens with none matching a cohort label, and is
    immediately preceded and followed by short non-cohort rows whose
    combined text (label_before + " " + label_after) matches a known name.
    """
    match_cohort = _match_cohort_label if side == "left" else _match_cohort_label_suffix
    # known_names may or may not include the 5 "Grad X" aggregate labels
    # (build_municipality_seeds deliberately excludes them from the real
    # municipality list, per the §7.3 Belgrade decision - their sub-districts
    # are the real municipality rows, not the aggregate itself). But the PDF
    # still prints a full 9-cohort data block FOR the aggregate row, right
    # before its sub-districts' own blocks. If that row isn't recognized at
    # all, group_geography_and_data_rows falls through to "unrecognized",
    # and its 9 cohort rows then get silently appended to whichever real
    # block came before it - confirmed as the actual bug (an oblast's block
    # size doubled to 18 because "Град Ужице"'s block wasn't recognized and
    # its cohort rows leaked into "Златиборска област"'s block instead).
    # Fix: always recognize these 5 labels as a block boundary - but instead
    # of dropping them (label=None), track them as the "current Grad
    # context" so the subdistrict rows that follow can be tagged with
    # their real parent.
    recognized_names = known_names | GRAD_WITH_SUBDISTRICTS
    all_subdistrict_names: set[str] = set()
    for members in GRAD_SUBDISTRICTS.values():
        all_subdistrict_names |= members

    blocks: list[tuple[str | None, str | None, list[PageRow]]] = []
    current_grad_context: str | None = initial_grad_context
    i = 0
    n = len(rows)
    while i < n:
        row = rows[i]
        cohort = match_cohort(row.text)
        if cohort:
            # data row belonging to the current (last-seen) geography block
            if blocks:
                blocks[-1][2].append(row)
            i += 1
            continue

        label, names = _split_geography_and_names(row, recognized_names)
        if label is not None:
            if label in GRAD_WITH_SUBDISTRICTS:
                current_grad_context = label
                blocks.append((None, None, []))  # the aggregate row's own data is dropped, per §7.3
            else:
                parent = current_grad_context if label in all_subdistrict_names else None
                if label not in all_subdistrict_names:
                    current_grad_context = None  # left the Grad's subdistrict run
                blocks.append((label, parent, []))
            i += 1
            continue

        # Try the 3-line-wrap pattern: this row IS the 5 names, with the
        # label split across the row before and the row after.
        tokens = [w["text"] for w in row.words]
        if len(tokens) == 5 and i > 0 and i + 1 < n:
            before_text = rows[i - 1].text.strip()
            after_text = rows[i + 1].text.strip()
            combined = f"{before_text} {after_text}".strip()
            if combined in recognized_names and match_cohort(before_text) is None:
                if combined in GRAD_WITH_SUBDISTRICTS:
                    current_grad_context = combined
                    blocks.append((None, None, []))
                else:
                    parent = current_grad_context if combined in all_subdistrict_names else None
                    if combined not in all_subdistrict_names:
                        current_grad_context = None
                    blocks.append((combined, parent, []))
                i += 2  # skip the row after too, it was the label's second half
                continue

        # Unrecognized row (page furniture that slipped through, or a
        # genuine parse failure) - skip it rather than guess.
        i += 1

    return [b for b in blocks if b[0] is not None], current_grad_context


def _extract_names_from_cohort_row(row: PageRow, cohort_label: str, side: str) -> list[str]:
    """Strips the cohort-label tokens off a cohort row, leaving exactly the
    5 name tokens (left/I-V rows: cohort tokens come first; right/VI-X rows:
    cohort tokens come last).
    """
    tokens = [w["text"] for w in row.words]
    label_tokens = cohort_label.split()
    if side == "left":
        return tokens[len(label_tokens):]
    return tokens[: len(tokens) - len(label_tokens)]


def extract_rank_rows(
    left_blocks: list[tuple[str, str | None, list[PageRow]]],
    right_blocks: list[tuple[str, str | None, list[PageRow]]],
    gender: str,
    page_left: int,
    page_right: int,
) -> list[MunicipalityRankRow]:
    """Pairs left (ranks I-V) and right (ranks VI-X) geography blocks by
    INDEX, not position: both lists are built by walking the same ordered
    sequence of geography rows on facing pages, so a matching left/right
    page pair produces blocks in identical order (confirmed: both sides
    always yield the same block count for every facing pair in T1 and T2,
    199 vs 199). Index-pairing is simpler and more robust than `top`-based
    matching, which would need to account for independent typesetting drift
    between the two pages.

    A block whose cohort-row count isn't exactly 9 (on either side) is
    still emitted with whatever rows it has - the parser never pads or
    guesses; docs/DATA_NOTES.md and the validator are where a mismatch
    should be investigated, not silently patched here.
    """
    out: list[MunicipalityRankRow] = []
    if len(left_blocks) != len(right_blocks):
        # Can't safely index-pair a mismatched block count for this page
        # pair - surface nothing rather than guess a wrong alignment.
        return out

    for (label, parent, left_rows), (label_r, parent_r, right_rows) in zip(left_blocks, right_blocks):
        if label != label_r or parent != parent_r:
            continue  # label/parent mismatch between sides - don't guess an alignment
        cohort_map: dict[str, tuple[list[str], list[str]]] = {}
        for row in left_rows:
            cohort = _match_cohort_label(row.text)
            if cohort is None:
                continue
            names = _extract_names_from_cohort_row(row, cohort, "left")
            cohort_map.setdefault(cohort, ([], []))
            cohort_map[cohort] = (names, cohort_map[cohort][1])
        for row in right_rows:
            cohort = _match_cohort_label_suffix(row.text)
            if cohort is None:
                continue
            names = _extract_names_from_cohort_row(row, cohort, "right")
            cohort_map.setdefault(cohort, ([], []))
            cohort_map[cohort] = (cohort_map[cohort][0], names)

        for cohort_label, (left_names, right_names) in cohort_map.items():
            all_names = left_names + right_names  # rank 1..len(left_names) then continuing
            for idx, name in enumerate(all_names, start=1):
                out.append(
                    MunicipalityRankRow(
                        geography_label=label,
                        parent_grad=parent,
                        cohort_label=cohort_label,
                        gender=gender,
                        rank=idx,
                        source_form=name,
                        page_left=page_left,
                        page_right=page_right,
                    )
                )
    return out


def parse_table(
    pdf_path: Path,
    page_range: tuple[int, int],
    gender: str,
    known_names: set[str],
) -> list[MunicipalityRankRow]:
    """Parses a full table (Table 1 or Table 2) across all its facing page
    pairs. page_range is (first_left_page_idx, last_page_idx_exclusive) -
    e.g. TABLE1_PAGE_RANGE.

    Left pages and right pages form two independent sequences (odd vs even
    indices), each of which can have a "Grad X" aggregate's subdistrict run
    span a page boundary - so the ending grad-context from one left page is
    threaded into the next left page's starting context, and likewise for
    right pages, separately. Without this, a Grad's subdistricts that don't
    happen to share a page with their aggregate row lose their parent_grad
    tag - confirmed as a real bug (see group_geography_and_data_rows).
    """
    start, end = page_range
    out: list[MunicipalityRankRow] = []
    left_grad_context: str | None = None
    right_grad_context: str | None = None
    with pdfplumber.open(pdf_path) as pdf:
        for left_idx in range(start, end, 2):
            right_idx = left_idx + 1
            if right_idx >= end:
                break
            left_page = pdf.pages[left_idx]
            right_page = pdf.pages[right_idx]

            left_rows = [r for r in parse_page_rows(left_page) if not _is_page_furniture(r.text)]
            right_rows = [r for r in parse_page_rows(right_page) if not _is_page_furniture(r.text)]

            left_blocks, left_grad_context = group_geography_and_data_rows(
                left_rows, known_names, side="left", initial_grad_context=left_grad_context
            )
            right_blocks, right_grad_context = group_geography_and_data_rows(
                right_rows, known_names, side="right", initial_grad_context=right_grad_context
            )

            out.extend(extract_rank_rows(left_blocks, right_blocks, gender, left_idx, right_idx))
    return out
