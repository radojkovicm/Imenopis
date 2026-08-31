"""Serbian Cyrillic -> Latin transliteration.

Standard digraph rules confirmed applicable by Phase 0 (docs/DATA_NOTES.md §4):
the census PDF and every newborn XLSX are printed entirely in Cyrillic, so this
is a clean 1:1 script mapping, not recovery from a corrupted Latin form (the
"digraph corruption" hazard in PROJECT.md §11.2 does not apply to these
sources).

Digraphs (Љ/Њ/Џ) must be matched before single-character replacement, longest
match first, so this walks the string rather than using a naive translate().
"""

_DIGRAPHS = {
    "Љ": "Lj",
    "љ": "lj",
    "Њ": "Nj",
    "њ": "nj",
    "Џ": "Dž",
    "џ": "dž",
}

_SINGLE = {
    "А": "A", "а": "a",
    "Б": "B", "б": "b",
    "В": "V", "в": "v",
    "Г": "G", "г": "g",
    "Д": "D", "д": "d",
    "Ђ": "Đ", "ђ": "đ",
    "Е": "E", "е": "e",
    "Ж": "Ž", "ж": "ž",
    "З": "Z", "з": "z",
    "И": "I", "и": "i",
    "Ј": "J", "ј": "j",
    "К": "K", "к": "k",
    "Л": "L", "л": "l",
    "М": "M", "м": "m",
    "Н": "N", "н": "n",
    "О": "O", "о": "o",
    "П": "P", "п": "p",
    "Р": "R", "р": "r",
    "С": "S", "с": "s",
    "Т": "T", "т": "t",
    "Ћ": "Ć", "ћ": "ć",
    "У": "U", "у": "u",
    "Ф": "F", "ф": "f",
    "Х": "H", "х": "h",
    "Ц": "C", "ц": "c",
    "Ч": "Č", "ч": "č",
    "Ш": "Š", "ш": "š",
}


def cyrillic_to_latin(text: str) -> str:
    """Transliterate a Serbian Cyrillic string to Latin, digraphs first."""
    result = []
    for ch in text:
        if ch in _DIGRAPHS:
            result.append(_DIGRAPHS[ch])
        elif ch in _SINGLE:
            result.append(_SINGLE[ch])
        else:
            result.append(ch)
    return "".join(result)
