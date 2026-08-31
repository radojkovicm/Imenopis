from src.util.transliteration import cyrillic_to_latin

# PROJECT.md §11.2 test list: Ljiljana, Njegoš, Đorđe, Anđela, Snežana
CASES = [
    ("Љиљана", "Ljiljana"),
    ("Његош", "Njegoš"),
    ("Ђорђе", "Đorđe"),
    ("Анђела", "Anđela"),
    ("Снежана", "Snežana"),
]


def test_known_names():
    for cyr, expected in CASES:
        assert cyrillic_to_latin(cyr) == expected


def test_digraphs_lowercase():
    assert cyrillic_to_latin("љ") == "lj"
    assert cyrillic_to_latin("њ") == "nj"
    assert cyrillic_to_latin("џ") == "dž"
