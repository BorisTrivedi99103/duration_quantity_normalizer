"""Core duration parsing and normalization logic.

The parser accepts a single quantity with a unit, or a sequence of
quantity/unit pairs such as ``1h30m``. It deliberately does not accept
completely bare numbers because the unit is the only thing that makes the
value meaningful. The canonical output is always an integer number of
seconds.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


class DurationParseError(ValueError):
    """Raised when a duration string cannot be parsed."""


# Unit aliases are case-insensitive. The canonical unit is the key.
_UNIT_ALIASES: Dict[str, str] = {
    "s": "s",
    "sec": "s",
    "secs": "s",
    "second": "s",
    "seconds": "s",
    "m": "m",
    "min": "m",
    "mins": "m",
    "minute": "m",
    "minutes": "m",
    "h": "h",
    "hr": "h",
    "hrs": "h",
    "hour": "h",
    "hours": "h",
}

# Only the units we actually support can appear in a duration expression.
_SUPPORTED_UNITS = frozenset(_UNIT_ALIASES)

# Matches a number (integer or decimal) followed by a unit token.
# The unit token is intentionally greedy on letters so that unknown units
# are captured and rejected explicitly rather than silently ignored.
_QUANTITY_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]+)")

# Used to reject stray characters between quantities.
_SEPARATOR_RE = re.compile(r"\s*")


def _canonical_unit(raw_unit: str) -> str:
    """Return the canonical unit name for *raw_unit* or raise.

    The lookup is lowercased so that ``H`` and ``h`` are equivalent. This is
    a deliberate simplification: real-world duration strings are almost
    always lowercase, and accepting mixed case costs nothing.
    """
    key = raw_unit.lower()
    try:
        return _UNIT_ALIASES[key]
    except KeyError:
        raise DurationParseError(f"unknown unit: {raw_unit!r}") from None


def _seconds_for(value: float, unit: str) -> float:
    """Convert a numeric value in *unit* to seconds as a float."""
    if unit == "s":
        return value
    if unit == "m":
        return value * 60.0
    if unit == "h":
        return value * 3600.0
    raise AssertionError(f"unhandled canonical unit: {unit!r}")


def _split_quantities(text: str) -> List[Tuple[float, str]]:
    """Split *text* into (value, canonical_unit) pairs.

    The parser walks the string from left to right. Anything that is not
    whitespace between quantities is an error. This is stricter than a
    permissive regex search and gives clearer failures for malformed input
    such as ``1h 30`` (missing unit) or ``1h,30m`` (comma separator).
    """
    quantities: List[Tuple[float, str]] = []
    pos = 0
    length = len(text)

    while pos < length:
        # Skip whitespace between quantities.
        while pos < length and text[pos].isspace():
            pos += 1
        if pos >= length:
            break

        match = _QUANTITY_RE.match(text, pos)
        if match is None:
            raise DurationParseError(
                f"unexpected character at position {pos}: {text[pos]!r}"
            )

        raw_value = match.group("value")
        raw_unit = match.group("unit")
        unit = _canonical_unit(raw_unit)

        try:
            value = float(raw_value)
        except ValueError:
            # The regex only admits digit strings, so this is unreachable in
            # practice, but converting explicitly keeps the error surface
            # consistent if the pattern ever changes.
            raise DurationParseError(f"invalid number: {raw_value!r}") from None

        quantities.append((value, unit))
        pos = match.end()

    if not quantities:
        raise DurationParseError("no duration quantities found")
    return quantities


class DurationNormalizer:
    """Normalizes mixed duration expressions to whole seconds.

    The class is intentionally stateless. It exists so that callers can
    inject a custom rounding policy at construction time instead of relying
    on a module-level global.
    """

    def __init__(self, *, round_half_up: bool = True) -> None:
        """Create a normalizer.

        Parameters
        ----------
        round_half_up:
            When True (the default), fractional seconds are rounded to the
            nearest integer with halves going away from zero. When False,
            fractional seconds are truncated toward zero. Truncation is
            useful when the caller cares about not over-reporting time.
        """
        self._round_half_up = round_half_up

    def _round(self, seconds: float) -> int:
        if self._round_half_up:
            # Python's round() uses banker's rounding, which surprises users
            # who expect 0.5 to round up. Add 0.5 for positive values and
            # subtract for negative values to get half-away-from-zero.
            if seconds >= 0:
                return int(seconds + 0.5)
            return int(seconds - 0.5)
        return int(seconds)

    def parse(self, text: str) -> int:
        """Parse *text* and return the total number of seconds.

        Raises DurationParseError for malformed input or unknown units.
        """
        if not isinstance(text, str):
            raise DurationParseError("duration must be a string")
        stripped = text.strip()
        if not stripped:
            raise DurationParseError("duration is empty")

        quantities = _split_quantities(stripped)
        total = 0.0
        for value, unit in quantities:
            total += _seconds_for(value, unit)
        return self._round(total)


def normalize_duration(text: str, *, round_half_up: bool = True) -> int:
    """Convenience wrapper around :class:`DurationNormalizer`.

    This is the function most callers should use. It creates a normalizer
    with the requested rounding policy and parses *text* immediately.
    """
    return DurationNormalizer(round_half_up=round_half_up).parse(text)
