"""Vacancy-count range rounding (BE 3.4 follow-up) - never show an exact
ad count, per the industry mentor's guidance. Bucket width scales with
magnitude so small and large counts both get a proportionally meaningful
band, not one fixed width for every role."""

import pytest

from app.core.vacancy_rounding import round_to_range


@pytest.mark.parametrize(
    ("value", "expected_low", "expected_high"),
    [
        (64, 60, 70),  # < 100 -> nearest 10
        (99, 90, 100),
        (100, 100, 150),  # 100-999 -> nearest 50
        (420, 400, 450),
        (999, 950, 1000),
        (1000, 1000, 1100),  # 1,000-9,999 -> nearest 100
        (1752, 1700, 1800),  # the real Database Administrator figure
        (1749, 1700, 1800),  # both land in the same bucket
        (9999, 9900, 10000),
        (10000, 10000, 10500),  # >= 10,000 -> nearest 500
        (12340, 12000, 12500),
        (0, 0, 10),
    ],
)
def test_round_to_range(value, expected_low, expected_high):
    result = round_to_range(value)
    assert result.low == expected_low
    assert result.high == expected_high


def test_the_real_value_always_falls_inside_its_own_range():
    for value in [1, 50, 99, 100, 500, 999, 1000, 5000, 9999, 10000, 50000]:
        result = round_to_range(value)
        assert result.low <= value <= result.high


def test_str_formats_with_thousands_separators_and_an_en_dash():
    assert str(round_to_range(1752)) == "1,700–1,800"
