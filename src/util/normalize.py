"""ASCII-folding for search_key generation (PROJECT.md §6.1).

search_key is deliberately not unique — two source forms may fold to the same
key (e.g. Mihajlo/Mihailo do NOT fold to the same key, since they differ by a
real letter, not a diacritic; but Đorđe/Djordje would). Collisions are a
finding surfaced via name_cluster (§7.2), never resolved by this function.
"""

from src.util.transliteration import cyrillic_to_latin

_DIACRITIC_FOLD = str.maketrans({
    "š": "s", "Š": "S",
    "č": "c", "Č": "C",
    "ć": "c", "Ć": "C",
    "ž": "z", "Ž": "Z",
    "đ": "dj", "Đ": "Dj",
})


def make_search_key(source_form: str) -> str:
    """Latin (transliterating if Cyrillic), diacritic-folded, lowercased."""
    latin = cyrillic_to_latin(source_form)
    folded = latin.translate(_DIACRITIC_FOLD)
    return folded.lower().strip()
