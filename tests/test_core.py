import unittest

from duration_quantity_normalizer import (
    DurationNormalizer,
    DurationParseError,
    normalize_duration,
)


class TestNormalizeDuration(unittest.TestCase):
    def test_single_hour(self):
        self.assertEqual(normalize_duration("1h"), 3600)

    def test_single_minute(self):
        self.assertEqual(normalize_duration("90 mins"), 5400)

    def test_single_second(self):
        self.assertEqual(normalize_duration("3600 seconds"), 3600)

    def test_compound_expression(self):
        self.assertEqual(normalize_duration("1h30m"), 5400)

    def test_compound_with_spaces(self):
        self.assertEqual(normalize_duration("1 h 30 m"), 5400)

    def test_decimal_hours(self):
        self.assertEqual(normalize_duration("1.5 hours"), 5400)

    def test_decimal_minutes_rounds_half_up(self):
        # 1.5 minutes is 90 seconds exactly, so no rounding is involved.
        self.assertEqual(normalize_duration("1.5m"), 90)

    def test_decimal_seconds_round_half_up(self):
        # 0.5 seconds rounds up to 1 second by default.
        self.assertEqual(normalize_duration("0.5s"), 1)

    def test_decimal_seconds_truncated(self):
        self.assertEqual(normalize_duration("0.5s", round_half_up=False), 0)

    def test_mixed_units(self):
        self.assertEqual(normalize_duration("2h 15m 10s"), 8110)

    def test_case_insensitive_units(self):
        self.assertEqual(normalize_duration("1H 30M"), 5400)

    def test_leading_and_trailing_whitespace(self):
        self.assertEqual(normalize_duration("  1h30m  "), 5400)

    def test_unknown_unit_raises(self):
        with self.assertRaises(DurationParseError):
            normalize_duration("5 fortnights")

    def test_missing_unit_raises(self):
        with self.assertRaises(DurationParseError):
            normalize_duration("1h 30")

    def test_empty_string_raises(self):
        with self.assertRaises(DurationParseError):
            normalize_duration("")

    def test_non_string_raises(self):
        with self.assertRaises(DurationParseError):
            normalize_duration(3600)  # type: ignore[arg-type]

    def test_separator_characters_rejected(self):
        with self.assertRaises(DurationParseError):
            normalize_duration("1h,30m")


class TestDurationNormalizer(unittest.TestCase):
    def test_default_rounding(self):
        normalizer = DurationNormalizer()
        self.assertEqual(normalizer.parse("0.5s"), 1)

    def test_truncation_policy(self):
        normalizer = DurationNormalizer(round_half_up=False)
        self.assertEqual(normalizer.parse("0.9s"), 0)

    def test_negative_not_supported(self):
        # Negative durations are not part of the grammar; the minus sign is
        # rejected as an unexpected character.
        with self.assertRaises(DurationParseError):
            DurationNormalizer().parse("-1h")


if __name__ == "__main__":
    unittest.main()
