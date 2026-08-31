"""Unit tests for §7.5's persistence algorithm (longest consecutive run),
isolated from the database - pure function tests."""

from src.api.routers.name import _longest_consecutive_order_run, _longest_consecutive_year_run


def test_longest_consecutive_year_run_simple():
    assert _longest_consecutive_year_run([1961, 1962, 1963]) == (1961, 1963)


def test_longest_consecutive_year_run_with_gap():
    # two runs: 1961-1963 (3 years) and 1970-1971 (2 years) - pick the longer
    assert _longest_consecutive_year_run([1961, 1962, 1963, 1970, 1971]) == (1961, 1963)


def test_longest_consecutive_year_run_picks_first_of_equal_length():
    # two equal-length runs - the scan keeps the first one found (no tie-break rule stated in spec)
    assert _longest_consecutive_year_run([1961, 1962, 1970, 1971]) == (1961, 1962)


def test_longest_consecutive_year_run_single_year():
    assert _longest_consecutive_year_run([1988]) == (1988, 1988)


def test_longest_consecutive_year_run_empty():
    assert _longest_consecutive_year_run([]) is None


def test_longest_consecutive_order_run_matches_year_run_algorithm():
    # same algorithm, different semantic space (cohort.sort_order, not calendar years)
    assert _longest_consecutive_order_run([1, 2, 3, 5, 6]) == (1, 3)
    assert _longest_consecutive_order_run([1]) == (1, 1)
