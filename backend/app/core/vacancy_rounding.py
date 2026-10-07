"""Rounds a raw ad count into a display range, never showing an exact
figure (per the industry mentor's guidance) - the bucket width scales with
magnitude so small and large counts both get a proportionally meaningful
band, not one fixed width for every role.
"""

from dataclasses import dataclass


def _bucket_width(value: int) -> int:
    if value < 100:
        return 10
    if value < 1000:
        return 50
    if value < 10000:
        return 100
    return 500


@dataclass(frozen=True)
class VacancyRange:
    low: int
    high: int

    def __str__(self) -> str:
        return f"{self.low:,}–{self.high:,}"


def round_to_range(value: int) -> VacancyRange:
    """Round a raw ad count down to its bucket and return [bucket, bucket +
    width] - the real value always falls inside the returned range."""
    width = _bucket_width(value)
    low = (value // width) * width
    return VacancyRange(low=low, high=low + width)
