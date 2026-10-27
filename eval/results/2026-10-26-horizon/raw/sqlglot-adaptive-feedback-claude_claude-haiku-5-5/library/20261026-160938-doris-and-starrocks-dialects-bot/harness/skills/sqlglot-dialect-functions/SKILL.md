---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when adding/mapping a dialect function — any change to a dialect's FUNCTIONS / FUNCTION_PARSERS / AGG_FUNCTIONS or generator TRANSFORMS, including choosing which target-dialect function is "the equivalent" of a source function (e.g. JSON constructors into Snowflake ARRAY_CONSTRUCT / OBJECT_CONSTRUCT / VARIANT).
---

# Dialect functions and parse fixes in sqlglot

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the function must
parse into THAT class so it can transpile. The generic nodes `exp.Anonymous`, `exp.AnonymousAggFunc`,
`exp.ParameterizedAgg`, `exp.CombinedAggFunc` and `exp.CombinedParameterizedAgg` (all in
`sqlglot/expressions/core.py`) are only for functions that have NO canonical class. The tests
check node types too. A fix that routes the function into a generic node can round-trip as a
string in its own dialect and still be wrong.

## Procedure
1. **Reproduce and inspect the node** before editing. Run from the repo root with the project's
   python (see `memory.md`):
   `<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read <dialect> --write duckdb,mysql,postgres --repr "<sql>"`
   Also try the bare form and any other variants of the function.
2. **Find the canonical class and a typed precedent.** Grep `sqlglot/expressions/*.py` for a class
   with the function's semantics. For example, string aggregation is `GroupConcat` in
   `expressions/aggregate.py`, quantile is `Quantile`, and uniq is `ApproxDistinct`. Grep other
   `sqlglot/parsers/*.py` for the same SQL concept: `LISTAGG`, `GROUP_CONCAT` and `STRING_AGG`
   all build `exp.GroupConcat`. In the dialect's parser and generator, look at
   `FUNCTION_PARSERS` and `TRANSFORMS` for a sibling handled the same way.
3. **Implement the contract below** following that precedent. Map each part of the input
   (parameter vs argument) to the matching arg of the typed node.
4. **You are done only when all of these hold, read from actual output:**
   - `ast_check.py` shows the typed node, with no `GENERIC node` flag, for every input form.
   - The round-trip in the source dialect matches the input (no `[DIFFERS]`).
   - Transpiling to at least two other dialects gives each dialect's native form, not the source
     dialect's syntax copied verbatim.
   - Each target's output returns the same type as the source function (see the return-type
     invariant below). Valid SQL with a similar-sounding name is not enough.
   - The new test asserts the node class (`validate_identity` returns the parsed expression;
     unwrap an alias if there is one) and adds a `validate_all` with `read=`/`write=` for another
     dialect where that applies.
   - The dialect's test file passes, then one full-suite run via
     `.lithify/harness/scripts/run_suite.py` (see `tool_guidance.md`) ends with `EXIT: 0`.
5. If `ast_check.py` exits 2, sqlglot was not importable. Rerun it from the repo root with the
   project's python. If it still fails, inspect `repr()` once by hand; don't retry the script.

In the final message, name the expression class the new syntax parses into and the result type
on each side of the translation. "Round-trips" alone is not enough.

## Contract for mapping a dialect spelling onto a canonical expression
Change all of these and make them agree:
1. Parser, `sqlglot/parsers/<dialect>.py`:
   - `FUNCTIONS` (`"NAME": exp.X.from_arg_list` or a builder) for a plain `name(args)` call.
     Keys are UPPERCASE.
   - `FUNCTION_PARSERS` (`"NAME": lambda self: self._parse_x()`) when the syntax is not a plain
     arg list (keywords, a second paren group, …). It is called after `NAME(` is consumed, and
     the base parser consumes the final `)`.
2. Generator, `sqlglot/generators/<dialect>.py`: a `TRANSFORMS` entry or `<exprname>_sql` method
   that emits the dialect's own spelling. Without it the base generator's spelling is emitted
   and the identity round-trip breaks. Reuse the shared helpers in `sqlglot/dialects/dialect.py`
   (`rename_func`, `groupconcat_sql`, …) when they fit.
3. Tests, `tests/dialects/test_<dialect>.py`: put them next to the existing tests for that
   function family.
4. Every form the dialect accepts for the name must keep working: with and without parameters,
   and with and without the optional argument. Don't emit a missing optional arg.
5. If the dialect form carries a parameter the canonical class has no arg for, don't drop it
   silently. Fall back to the generic node for that case, or report it.

## Invariant: the target spelling must return the SAME TYPE as the source function
sqlglot preserves semantics, not names. Before a target function counts as "the equivalent",
write down what the source function returns (dialect docs) and what the target returns. If they
differ, wrap or cast the target call so the types match; don't just rename.
- A dialect's name for a type is in its generator's `TYPE_MAPPING`. In
  `sqlglot/generators/snowflake.py`, `exp.DType.JSON` maps to `"VARIANT"`: a JSON-typed source
  value must arrive in Snowflake as a VARIANT.
- Snowflake constructors return ARRAY/OBJECT, not VARIANT (`ARRAY_CONSTRUCT` parses as
  `exp.Array` in `sqlglot/parsers/snowflake.py`). A JSON-returning source constructor mapped onto
  one of them needs a VARIANT wrapper.
- The wrapper node is `exp.ToVariant` (`sqlglot/expressions/functions.py`); Snowflake emits it as
  `TO_VARIANT(...)`. Build the node (`self.sql(exp.ToVariant(this=<node>))`) rather than
  hand-writing the string. Change only the transform you are adding.
- A neighbouring transform is not proof of type-correctness. In the Snowflake generator,
  `exp.JSONObject` maps to a bare `OBJECT_CONSTRUCT_KEEP_NULL`, which would mislead you if you
  copied it. When a precedent and the type check disagree, the type check wins.
- Derive the expected target string in your test from this type check, not from what the
  generator prints after your edit. A test that records your own output can't catch a wrong
  translation.

## ClickHouse specifics (`sqlglot/parsers/clickhouse.py`, `sqlglot/generators/clickhouse.py`)
- Parametric aggregate syntax is `name(params)(args)`.
- The module-level `AGG_FUNCTIONS` set (camelCase names) and `AGG_FUNCTIONS_SUFFIXES` feed
  `_resolve_clickhouse_agg`. `ClickHouseParser._parse_function` then turns a resolved
  `Anonymous` into `AnonymousAggFunc`, `ParameterizedAgg` or `Combined*`. Adding a name only to
  `AGG_FUNCTIONS` therefore yields a generic `ParameterizedAgg`, never a canonical node.
- `ParameterizedAgg` field names are inverted relative to SQL. `expressions` holds the FIRST
  paren group (the parameters) and `params` holds the SECOND group (the arguments).
- `quantile` is the canonical template already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.
