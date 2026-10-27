---
name: sqlglot-parser-options
description: Load when a task adds or changes a keyword option of the sqlglot Parser or Generator (anything passed through parse / parse_one / transpile / Dialect.parse as **opts, such as a limit, safeguard or flag), or adds a new user-facing error message such as a ParseError raised by the parser core in sqlglot/parser.py.
---

# Parser/Generator options and core ParseErrors in sqlglot

## How an option reaches the parser (verified plumbing)
`sqlglot.parse(sql, read, **opts)` and `parse_one(sql, read, into=..., **opts)` forward to
`Dialect.parse` / `Dialect.parse_into`, which call `self.parser(**opts)` →
`parser_class(dialect=self, **opts)`. A new `Parser.__init__` keyword therefore reaches every
entry point with no extra plumbing. Exception: `sqlglot.transpile` passes only `error_level` to
parsing; its `**opts` go to the Generator.

## CONTRACT: a new Parser option touches all of these, and they must agree
1. `Parser.__init__` in `sqlglot/parser.py`: the keyword, with a default that keeps today's
   behaviour (e.g. `None` = no limit).
2. `Parser.__slots__` (same file, under the class docstring): every new instance attribute,
   including private counters.
3. The `Args:` section of the `Parser` class docstring, in the style of `max_errors`.
4. `Parser.reset()`: reset per-parse state (counters) next to `_chunks` / `_chunk_index`, since
   one parser instance can parse several times.
5. `ParserNoDialectArgs` in `sqlglot/_typing.py`, so `parse_one(..., new_opt=...)` type-checks.
   Generator options go in `GeneratorNoDialectArgs` / `sqlglot/generator.py` instead.
6. Tests in `tests/test_parser.py`, calling the public entry points (`parse_one`, `parse`,
   `parse_one(into=...)`).

## INVARIANT: ParseError swallowing sites
These catch `ParseError` and fall back silently, so an error raised deep inside parsing can vanish:
`Parser._try_parse` (backtracking), `Parser.parse_into` (tries each `into` type), a third site in
`parser.py` (around line 4110), `sqlglot/expressions/builders.py`,
`sqlglot/expressions/datatypes.py`, and `sqlglot/dialects/dialect.py`. Find the current list with
`grep -rn "except ParseError\|except (ParseError" sqlglot`. An error that must ALWAYS surface
(a safety limit) needs state that survives the catch plus a re-check after the swallowing site
returns. `parse_into` reads `e.errors[0]`; a bare `ParseError(msg)` has no `errors` entries, so it
must be re-raised before that line.

## INVARIANT: how the parser raises
- `self.raise_error(msg)` builds `ParseError.new(...)` with line/col context, appends it to the
  message, and raises immediately only under `ErrorLevel.IMMEDIATE`; under RAISE/WARN/IGNORE it is
  collected or dropped. Use it for syntax errors.
- A guard that must stop parsing regardless of `error_level` raises `ParseError(msg)` directly.
- Nearly all nodes are built through `Parser.expression(instance, ...)` (~660 call sites in
  `parser.py` and `parsers/*.py`); some builders construct `exp.X(...)` directly and bypass it.
  A hook in `expression()` covers the main path, not every node — say so in the report.

## The error message is part of the interface
The task usually states only a fragment of the message, but the whole text is user-facing and may
be checked. Before writing it:
1. Keep the stated fragment verbatim.
2. Grep for analogous messages (`grep -rnE "Maximum|exceed|too many|limit" sqlglot`) and copy
   their shape. Existing sqlglot messages put values into the sentence plainly, e.g.
   `f"Normalization distance {distance} exceeds max {max_distance}"` (`optimizer/normalize.py`);
   don't invent a new rendering such as `option_name=value`.
3. Quote the exact final message in your final reply.

## Done means all of these, read from actual output
- A direct `parse_one` probe shows: (a) the normal inputs the task names parse unchanged with no
  option AND under a realistic, generous limit; (b) a pathological input raises under that same
  generous limit, not only under a tiny one; (c) a small limit raises. Print the full
  `str(exception)` and compare it with the message rules above.
- The new test covers (a)–(c) and asserts the message; then the full check command in
  `memory.md` passes, and `<python> -m mypy sqlglot/parser.py sqlglot/_typing.py` and
  `<python> -m ruff check` are clean.
