"""Extracts the geography tree (region -> district/oblast -> municipality,
plus the 5 multi-district "Grad X" cities) from the census PDF's own table of
contents (pages 7-11, printed page numbers 3-11 in the header but that's the
front matter - the geography TOC itself spans printed pages 12-220ish).

Why the TOC and not the body pages: the body pages (Table 1/2) have no
reliable geography-vs-cohort discriminator by position alone (see
docs/DATA_NOTES.md - a "Grad Ниш" sub-district row like "Медијана" lands at
the SAME x-position as a cohort label row, because it's one indent level
deeper than a normal oblast/opština row). The TOC, by contrast, is one
name + page-number per line in a stable two-column layout, and is complete
and authoritative: every municipality the publication covers appears here
exactly once per column (this module keeps only the earliest, from Table 1's
listing, since Table 2 repeats the identical list at different page numbers).

This is diagnostic/one-time tooling, not something the ingest pipeline calls
on every run - its output is meant to be reviewed and turned into a static
seed list (see build_municipality_seed() and docs/DATA_NOTES.md for the
manual corrections applied). Re-run only if a different PDF edition is used.
"""

import re
from pathlib import Path

import pdfplumber

TOC_PAGES = range(6, 11)  # 0-indexed pdfplumber pages 7-11

MACRO_REGIONS = {"РЕПУБЛИКА СРБИЈА", "СРБИЈА – СЕВЕР", "СРБИЈА – ЈУГ"}
# Note: "Регион Косовo и Метохијa" is spelled exactly like this in the source
# PDF - with Latin 'o' (U+006F) in "Косовo" and Latin 'a' (U+0061) in
# "Метохијa", mixed into otherwise-Cyrillic words. Confirmed by codepoint
# inspection, not a transcription typo here - a genuine font/encoding quirk
# in the publication. Kosovo and Metohija has no data (census wasn't
# conducted there, per docs/DATA_NOTES.md §4's Kosovo finding) so this entry
# is a rollup with no rows underneath it in practice.
NUTS2_REGIONS = {
    "Београдски регион",
    "Регион Војводине",
    "Регион Шумадије и Западне Србије",
    "Регион Јужне и Источне Србије",
    "Регион Косовo и Метохијa",
}
# The 5 cities whose TOC entry is itself a rollup with sub-district rows
# beneath it (confirmed by checking each one's body pages - see
# docs/DATA_NOTES.md). Belgrade's is spelled with the parenthetical.
GRAD_WITH_SUBDISTRICTS = {
    "Београдска област (Град Београд)",
    "Град Ужице",
    "Град Пожаревац",
    "Град Ниш",
    "Град Врање",
}

# Junk rows that survive word-extraction from page headers/dashes but aren't
# real TOC entries - filtered out by exact match.
JUNK_NAMES = {
    "рођења по општинама и градовима",
    "Републици Србији по години рођења",
    "градовима",
    "у Републици Србији",
    "Бања",  # fragment split from "Врњачка Бања" wrapping across lines on one page
    "област",  # fragment split from "Севернобанатска област" wrapping across lines
    "popis2022.stat.gov.rs",  # page footer, picked up when tolerance=3 row-clustering merges it with an adjacent line
}


def _strip_leader(text: str) -> str:
    """Strip a trailing dot-leader run (or other punctuation runs) that
    pdfplumber sometimes glues onto the preceding word with no space."""
    return re.sub(r"[^\w()–\s]+$", "", text).rstrip()


def extract_toc_entries(pdf_path: Path) -> list[tuple[str, float, int]]:
    """Returns (name, x0, printed_page_number) tuples in document order,
    deduplicated by name to the first (lowest-page, i.e. Table 1's) occurrence.

    Dedup is by name alone, not (name, x0): the same municipality's TOC entry
    can land in the left or right column of the two-column layout depending
    on where it falls on the page, and left/right columns have different x0
    baselines (~66-76 vs ~260-280) - keying on x0 as well as name produced
    spurious near-duplicates (e.g. "Јужнобанатска област" kept as two entries
    because one printing fell in the left column and the other in the right).
    x0 is still returned per entry for level classification, taken from
    whichever occurrence was kept.
    """
    entries: list[tuple[float, float, str, int]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pidx in TOC_PAGES:
            page = pdf.pages[pidx]
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            # Row grouping uses pdfplumber's own tolerance-based clustering,
            # not a naive round(top, 1): two words on the same visual line
            # can differ by up to ~1pt in 'top' (seen directly: "Западнобачка"
            # at top=402.41 vs "област" on the same line at top=402.46 - these
            # round to DIFFERENT buckets at 1 decimal place, silently
            # splitting one TOC row into two and losing the page number half,
            # which then drops that oblast from the extracted list entirely).
            # tolerance=3 merges same-line jitter without merging adjacent
            # rows, which are ~11-12pt apart in this document.
            row_clusters = pdfplumber.utils.cluster_objects(words, key_fn=lambda w: w["top"], tolerance=3)
            rows: dict[float, list[dict]] = {}
            for cluster in row_clusters:
                rows[min(w["top"] for w in cluster)] = cluster
            for top in sorted(rows.keys()):
                row_words = sorted(rows[top], key=lambda w: w["x0"])
                left = [w for w in row_words if w["x0"] < 250]
                right = [w for w in row_words if w["x0"] >= 250]
                for col in (left, right):
                    if not col:
                        continue
                    parts = []
                    page_num = None
                    for w in col:
                        t = w["text"]
                        if t.isdigit():
                            page_num = int(t)
                            continue
                        cleaned = _strip_leader(t)
                        if cleaned:
                            parts.append(cleaned)
                    if parts and page_num is not None:
                        name = " ".join(parts)
                        if name in JUNK_NAMES or len(name) < 2:
                            continue
                        entries.append((top, col[0]["x0"], name, page_num))

    best: dict[str, tuple[float, int]] = {}
    for _top, x0, name, pg in entries:
        if name not in best or pg < best[name][1]:
            best[name] = (x0, pg)

    order: list[tuple[str, float, int]] = []
    added = set()
    for _top, _x0, name, _pg in sorted(entries, key=lambda e: best[e[2]][1]):
        if name in added:
            continue
        added.add(name)
        x0, pg = best[name]
        order.append((name, x0, pg))
    return order


# The known sub-districts of each multi-district "Grad X" entry, keyed by
# their parent's TOC name. Extracted by inspecting each Grad's body pages
# directly (docs/DATA_NOTES.md) rather than by x0 indent alone - Belgrade's
# 17 opštine and Niš's 5 districts land at DIFFERENT x0 offsets from their
# parent than Užice/Požarevac/Vranje's 2 sub-entries each do, so there is no
# single "indent + N" rule that covers all five uniformly.
GRAD_SUBDISTRICTS = {
    "Београдска област (Град Београд)": {
        "Барајево", "Вождовац", "Врачар", "Гроцка", "Звездара", "Земун",
        "Лазаревац", "Младеновац", "Нови Београд", "Обреновац", "Палилула",
        "Раковица", "Савски венац", "Сопот", "Стари град", "Сурчин", "Чукарица",
    },
    "Град Ужице": {"Ужице", "Севојно"},
    "Град Пожаревац": {"Пожаревац", "Костолац"},
    "Град Ниш": {"Медијана", "Нишка Бања", "Палилула", "Пантелеј", "Црвени крст"},
    "Град Врање": {"Врање", "Врањска Бања"},
}


def classify_entries(entries: list[tuple[str, float, int]]) -> list[dict]:
    """Classifies each TOC entry into a geography level: rollup (Republic,
    macro-region, NUTS-2 region), grad_with_subdistricts (one of the 5 cities
    listed in GRAD_SUBDISTRICTS), subdistrict (a member of one of those 5),
    or oblast_or_municipality (everything else - the TOC alone can't
    distinguish an oblast heading from a plain opština under it, and doesn't
    need to: the body-page parser tells them apart via the cohort-label rule,
    see src/ingest/pdf_parser.py).
    """
    all_subdistrict_names: set[str] = set()
    for members in GRAD_SUBDISTRICTS.values():
        all_subdistrict_names |= members

    out = []
    for name, x0, pg in entries:
        if name in MACRO_REGIONS or name in NUTS2_REGIONS:
            level = "rollup"
        elif name in GRAD_WITH_SUBDISTRICTS:
            level = "grad_with_subdistricts"
        elif name in all_subdistrict_names:
            level = "subdistrict"
        else:
            level = "oblast_or_municipality"
        out.append({"name": name, "x0": x0, "page": pg, "level": level})
    return out
