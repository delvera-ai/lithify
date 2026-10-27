---
name: sqlglot-time-parsing
description: Load when a task transpiles or fixes a format-string date/time PARSING function between dialects — BigQuery PARSE_DATE / PARSE_TIME / PARSE_DATETIME / PARSE_TIMESTAMP, DuckDB STRPTIME / TRY_STRPTIME, STR_TO_DATE, TO_TIMESTAMP(x, fmt), parseDateTime, or the exp.StrToTime / StrToDate / ParseDatetime / ParseTime nodes — including when the task already shows the "expected" target string.
---

# Format-string time parsing across dialects

## Where each piece lives (verified in source)
- BigQuery parser (`sqlglot/parsers/bigquery.py`, `FUNCTIONS`): BigQuery takes the FORMAT first;
  the builders swap it so `this` = the value and `format` = the format.
  - `PARSE_DATE` -> `exp.StrToDate`, `PARSE_TIME` -> `exp.ParseTime`,
    `PARSE_DATETIME` -> `exp.ParseDatetime` (args `this`, `format`, `zone`),
    `PARSE_TIMESTAMP` -> `exp.StrToTime` via `_build_parse_timestamp` (sets `zone`).
  - Classes are in `sqlglot/expressions/temporal.py`; `exp.SafeFunc` (the `SAFE.` prefix) is in
    `sqlglot/expressions/core.py`.
- `build_formatted_time` (`sqlglot/dialects/dialect.py`) converts the source format into the
  canonical (Python strftime) form at parse time using the dialect's `TIME_MAPPING`
  (`sqlglot/dialects/<d>.py`). The generator's `self.format_time(expression)`
  (`sqlglot/generator.py`) converts it back with the TARGET's `INVERSE_TIME_MAPPING`. Never
  hand-translate format directives; this is also why BigQuery round-trips `%Y-%m-%d %H:%M:%S`
  as `%F %T`.
- DuckDB generator (`sqlglot/generators/duckdb.py`): `strtotime_sql` (STRPTIME / TRY_STRPTIME
  when `safe`, TIMESTAMPTZ cast for tz targets), `strtodate_sql` (`CAST(STRPTIME(..) AS DATE)`),
  `parsetime_sql` (`CAST(STRPTIME(..) AS TIME)`). The shared `str_to_time_sql` helper in
  `sqlglot/dialects/dialect.py` only emits `STRPTIME(this, format)` — it is a rename, nothing more.

## INVARIANT: unspecified fields must default to the same value on both sides
A parse function fills the fields its format does not mention with defaults, and engines
disagree:
- BigQuery `PARSE_DATETIME` / `PARSE_TIMESTAMP`: unspecified fields default to
  `1970-01-01 00:00:00` (BigQuery docs).
- DuckDB `STRPTIME` (C `strptime` convention): an unspecified year defaults to 1900.
So mapping a datetime-returning parse onto `STRPTIME` with only a rename (`str_to_time_sql`) is a
semantic bug for any format without a year (`'%H:%M:%S'`, `'%a %b %e ...'`), even though the
task's full-date example comes out looking right. The task's example output shows the minimum
it needs. If the defaults differ, reconcile them even if the example doesn't show it.
- The format argument may be a column or expression, so you cannot always tell whether it has a
  year. The reconciliation must be correct for ANY format, not only literals you can inspect.
- One way that works for any format, literal or not: build the target call from nodes. Prepend the
  source's default year to the value and a matching `%Y` directive to the format, joining each
  with `exp.DPipe` (DuckDB `||`, `sqlglot/expressions/core.py`). A later `%Y` in the user's
  format then supplies the real year. Build nodes (`exp.DPipe`, `exp.Literal.string`) instead of
  f-strings, as in `strtotime_sql`.
- Decide per node whether its result type exposes the differing default (a DATETIME/TIMESTAMP
  result does; check TIME/DATE results case by case), and do not change the output of a
  sibling node the task did not name.

## Contract for a new/changed parse transpile
1. Give the node its own entry in the target generator's `TRANSFORMS` (or a `<node>_sql`
   method). Map it to the right target function and the same RESULT TYPE (BigQuery DATETIME has
   no zone; DuckDB `STRPTIME` returns TIMESTAMP). Also reconcile the defaults (invariant above).
2. Carry every arg: `zone` on `ParseDatetime`/`StrToTime`, and `safe` / `SAFE.` -> DuckDB
   `TRY_STRPTIME`. Don't silently drop an arg the target can't express.
3. Tests go in the source dialect's file next to the function's existing tests
   (`tests/dialects/test_bigquery.py`). Read-side transpile tests for DuckDB output go in
   `tests/dialects/test_duckdb.py` (`test_time` already has `read={"bigquery": "PARSE_TIME(..)"}`
   cases). Include a format WITHOUT a year and a non-literal format, and write each expected
   string from the two engines' default rules, not from what your generator prints.
