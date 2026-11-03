# duration_quantity_normalizer

Converts mixed time duration expressions such as `1h30m`, `90 mins`, `1.5 hours`, and `3600 seconds` into a canonical integer number of seconds.

```python
from duration_quantity_normalizer import normalize_duration

normalize_duration("1h30m")        # 5400
normalize_duration("90 mins")      # 5400
normalize_duration("1.5 hours")    # 5400
normalize_duration("3600 seconds") # 3600
```

The parser also accepts compound expressions with spaces (`1 h 30 m`) and is case-insensitive for unit names. It raises `DurationParseError` for unknown units, missing units, empty strings, and stray separator characters.

## Why this exists

Duration strings arrive from configuration files, user input, and logs in many shapes. Most parsers either accept a fixed set of formats or silently ignore unrecognized text. This library makes one clear choice: a duration must be a sequence of number/unit pairs, and anything else is an error. That strictness means malformed input fails loudly instead of producing a plausible but wrong number of seconds.

The trade-off is that bare numbers are not accepted. `"90"` is not a duration because it has no unit, and guessing seconds would hide mistakes. Callers who have a bare number should add the unit explicitly.

## Rounding

Seconds are returned as an integer. By default, fractional seconds are rounded half away from zero, so `0.5s` becomes `1`. Passing `round_half_up=False` truncates toward zero instead, which is useful when over-reporting time is worse than under-reporting it.

```python
from duration_quantity_normalizer import normalize_duration

normalize_duration("0.5s")                    # 1
normalize_duration("0.5s", round_half_up=False)  # 0
```

## Awkward edge

The grammar does not allow a bare number, a sign, or a comma between quantities. `"1h 30"`, `"-1h"`, and `"1h,30m"` all raise `DurationParseError`. If you need to accept those forms, normalize them before calling this library.
