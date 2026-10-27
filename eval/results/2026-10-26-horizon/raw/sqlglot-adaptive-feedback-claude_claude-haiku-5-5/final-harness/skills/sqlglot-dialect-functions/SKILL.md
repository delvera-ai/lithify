---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTERVAL), or when adding/mapping a dialect function — replacing an inherited operator such as Postgres `@>` / `<@` with a function, or string aggregation (LISTAGG / STRING_AGG / GROUP_CONCAT separator, WITHIN GROUP, ON OVERFLOW), or any change to a dialect's FUNCTIONS / FUNCTION_PARSERS / AGG_FUNCTIONS or generator TRANSFORMS, including choosing which target-dialect function is "the equivalent" of a source function (e.g. JSON constructors into Snowflake ARRAY_CONSTRUCT / OBJECT_CONSTRUCT / VARIANT), or when adding a new expression class for syntax only one dialect has (a call on a dynamically resolved name, `model!attribute`, a dialect-only statement) and deciding what other dialects generate for it.
---

# Dialect functions and parse fixes in sqlglot

If the failing syntax is SQL/JSON (JSON_TABLE, FORMAT JSON, JSON_OBJECT RETURNING), also load
the `sqlglot-json-table` skill: that syntax is parsed in the base `sqlglot/parser.py`, not in
the dialect's parser. If it is a list inside a clause (ON CONFLICT target, index/key column
list) rather than a function, load `sqlglot-clause-element-lists` instead
(plus `sqlglot-upsert-on-conflict` for an ON CONFLICT target).

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
   Also try the bare form and any other variants of the function. Use these scripts rather
   than a hand-written `/tmp` probe: their flags are the checks a hand probe leaves out.
2. **Find the canonical class and a typed precedent.** If the dialect already parses another
   form of the SAME function name (e.g. an INTERVAL form), that form's node is the precedent:
   see the shorthand invariant below. Otherwise grep `sqlglot/expressions/*.py` for a class
   with the function's semantics. For example, string aggregation is `GroupConcat` in
   `expressions/aggregate.py`, quantile is `Quantile`, and uniq is `ApproxDistinct`. Grep other
   `sqlglot/parsers/*.py` for the same SQL concept: `LISTAGG`, `GROUP_CONCAT` and `STRING_AGG`
   all build `exp.GroupConcat`. In the dialect's parser and generator, look at
   `FUNCTION_PARSERS` and `TRANSFORMS` for a sibling handled the same way.
3. **Implement the contract below** following that precedent. Map each part of the input
   (parameter vs argument) to the matching arg of the typed node.
4. **You are done only when all of these hold, read from actual output:**
   - `ast_check.py`, rerun AFTER your last source edit (not a hand-written `-c` probe), shows
     the typed node, with no `GENERIC node` flag, for every input form the task names. Pass
     them all in one call (e.g. both the ADD and SUB spelling).
   - No `[FUNCTION CHANGED]` (exit 4): every function the user wrote is still in the round-trip.
     `DATE_SUB(x, 1)` coming back as `DATE_ADD(x, -1)` is a failure even though the arithmetic
     is equal. Go back to step 2; don't report it as a caveat or record it in a test.
   - No `[WORDS DROPPED]` (exit 4) for any form you probed, including each documented optional
     clause of the construct (e.g. `ON OVERFLOW ...`, `DISTINCT`, `WITHIN GROUP`), passed in the
     same `ast_check.py` call as the task's example. A clause the parser accepts and the
     generator drops is a failed round-trip of the construct you changed: fix it. Not knowing
     the clause's default is no reason to leave it: a round-trip emits exactly the args the
     parser stored (`expression.args`), so emit what was parsed and invent no default.
     The only exception is a dropped word you can name as a normalisation the generator already
     applies to every input (e.g. a default `NULLS` ordering it never prints).
   - The round-trip matches the input (no `[DIFFERS]`; case and whitespace are ignored), except
     for a normalisation you can name. A shorthand spelling of an existing node normalizes to the
     spelling the dialect's generator already emits for that node (see the shorthand invariant
     below); its test is `validate_identity(shorthand, canonical)` in its own dialect. A
     same-dialect `validate_all(read=...)` does not prove a form round-trips.
   - Transpiling to at least two other dialects gives each dialect's native form, not the source
     dialect's syntax copied verbatim, OR is tagged `[UNSUPPORTED: ...]` by `ast_check.py` when
     the target has no documented equivalent (runtime/dynamic name resolution, session
     variables, a dialect-only call form). An untagged line that quietly rewrites such a
     construct into ordinary SQL (drops the wrapper, emits a plain call) is a wrong transpile,
     even if a sibling node lowers that way. See the contract at the end of this file.
   - When the task is "dialect X must GENERATE its own spelling" (transpiling INTO X), run
     `<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/into_dialect.py --write <X> "<X-native sql>" ...`
     after your last source edit, with X's spelling of EVERY construct the task names. It reads
     that text under every other dialect. A hand-picked list of source spellings (e.g. only
     `@>` and `ARRAY_HAS_ALL`) is not enough: another dialect can parse X's own function name
     into a different class (an argument-swapped/inverse operator node) that X still emits in
     foreign syntax. Each `[DIFFERS]` line (exit 4) needs a TRANSFORMS entry for that class, or
     a reason from that source dialect's docs that the text means something else there.
   - Each target's output returns the same type as the source function (see the return-type
     invariant below). Valid SQL with a similar-sounding name is not enough.
   - Each target's output returns the same VALUE as the source for the edge inputs listed in
     the value invariant below, not only for the task's example.
   - The new test asserts the node class (`validate_identity` returns the parsed expression;
     unwrap an alias if there is one) and adds a `validate_all` with `read=`/`write=` for another
     dialect where that applies. A `write=` value is a claim about the target engine: take it
     from that engine's docs, not from your probe output. For a target that cannot express the
     construct the value is `UnsupportedError`. Never pin a guessed lowering.
   - The dialect's test file passes, then one full-suite run via
     `.lithify/harness/scripts/run_suite.py` (see `tool_guidance.md`) ends with `EXIT: 0`.
5. If `ast_check.py` exits 2, sqlglot was not importable. Rerun it from the repo root with the
   project's python. If it still fails, inspect `repr()` once by hand; don't retry the script.

If your final message would say a form the task names "does not round-trip" or is rewritten,
you are not done: that is the failure, not a footnote.

In the final message, name the expression class the new syntax parses into and the result type
on each side of the translation. "Round-trips" alone is not enough.

## INVARIANT: shorthand forms reuse the node the full form already builds
When a dialect accepts a second spelling of a function it already parses (an omitted keyword or
a defaulted argument), the new spelling must build the SAME expression class as the existing
form, with the omitted part filled in. Do not switch it to another node class.
- Take the precedent from the dialect's own parent class, not from an unrelated dialect that
  shares the spelling. Doris and StarRocks extend MySQL (`DorisParser(MySQLParser)`,
  `StarRocksParser(MySQLParser)`, same for the generators). MySQL builds `DATE_ADD` / `DATE_SUB`
  as `exp.DateAdd` / `exp.DateSub` (`build_date_delta_with_interval` in
  `sqlglot/dialects/dialect.py`, wired in `sqlglot/parsers/mysql.py`), so the bare-number form
  there is `exp.DateAdd` / `exp.DateSub` with `unit` DAY. It is not Hive/Spark's `exp.TsOrDsAdd`
  (`_build_date_add` in `sqlglot/parsers/hive.py`), which belongs to the Hive family.
- Keep the operation. A `*_SUB` call stays `exp.DateSub`. Do not rewrite it as an Add with a
  negated operand: that loses the function name on round-trip.
- Default units follow existing builders: `build_date_delta(..., default_unit=...)` in
  `sqlglot/dialects/dialect.py` fills the unit when it is absent. Extend or wrap the existing
  shared builder there (next to `build_date_delta_with_interval`) rather than creating a
  parallel one per dialect.
- Generation needs no new transform when the inherited generator already handles the node.
  MySQL's `date_add_sql("ADD"/"SUB")` (`sqlglot/generators/mysql.py`) emits
  `DATE_ADD/DATE_SUB(x, INTERVAL n <unit>)`, and Doris/StarRocks inherit it, so the shorthand
  normalizes to the INTERVAL form. "Parse and generate" means the parsed node generates valid
  dialect SQL. It does not mean the shorthand is echoed back verbatim.
- Do not add or change a generator `TRANSFORMS` entry for a node that other dialects also
  produce (e.g. `exp.TsOrDsAdd`) just to make your shorthand echo. That changes the output for
  every source dialect that transpiles into this one. (Doris's generator already maps
  `exp.TsOrDsAdd` to a two-arg `DATE_ADD` that ignores the unit; StarRocks inherits MySQL's
  INTERVAL form.)
- Check: `ast_check.py` shows the full form and the shorthand as the same class, the `SUB`
  shorthand as the `Sub` class, and the shorthand round-trips to the full form's spelling.

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
   silently. Fall back to the generic node for that case, or report it. If the class DOES have
   the arg and another dialect's generator already emits it, "report it" is not allowed: emit it.
6. Every node that means the same thing must be covered, including converse nodes (next section).
7. Parser and generator are a pair. When you route a name to a shared `_parse_*` helper in
   `sqlglot/parser.py`, read which args that helper `set`s, find a dialect already routed to the
   same helper (grep `sqlglot/parsers/*.py` for it), and copy that dialect's generator entry,
   flags included. Every arg the parser fills must appear in the generator's output, or the
   identity round-trip drops it. Check: `ast_check.py` on an input that fills each arg.

## INVARIANT: string aggregation (LISTAGG / STRING_AGG / GROUP_CONCAT) → `exp.GroupConcat`
`exp.GroupConcat` (`sqlglot/expressions/aggregate.py`) has args `this`, `separator`, `on_overflow`.
- Two parse helpers in `sqlglot/parser.py`, chosen by the SQL shape, not the name:
  `_parse_string_agg` for `NAME(x [, sep] [ON OVERFLOW ...]) [WITHIN GROUP (ORDER BY ...)]`
  (Oracle, Snowflake, Trino, DuckDB route LISTAGG here); `_parse_group_concat` for MySQL-style
  `GROUP_CONCAT(x [, y ...] [ORDER BY ...] [SEPARATOR s])`, which folds extra positional args
  into `exp.Concat`. A comma-separated second argument that is a separator needs `_parse_string_agg`.
- `_parse_string_agg` fills `on_overflow` (`exp.var("ERROR")` or `exp.OverflowTruncateBehavior`,
  `sqlglot/expressions/query.py`). It is only kept on the `WITHIN GROUP` path; the other return
  paths drop it.
- Generation goes through `groupconcat_sql` in `sqlglot/dialects/dialect.py`. Its keyword flags
  decide what is emitted: `on_overflow=False` by default (the ON OVERFLOW clause is silently
  dropped), `sep=","` (the separator written when the node has none; Snowflake passes `sep=""`,
  BigQuery `sep=None`), `within_group`, `func_name`. Oracle and Trino pass `on_overflow=True`.
  So a dialect switched to `_parse_string_agg` whose docs list ON OVERFLOW must also pass
  `on_overflow=True` in its generator's `exp.GroupConcat` TRANSFORMS entry.
- `OverflowTruncateBehavior` is always generated with an explicit `WITH COUNT` / `WITHOUT COUNT`
  (`overflowtruncatebehavior_sql` in `sqlglot/generator.py`); an omitted count parses as
  with_count=True. That is the existing normalisation shared by Oracle/Trino; an undocumented
  count default in the target is not a reason to drop the clause.
- Check, under the dialect: `ON OVERFLOW ERROR` and `ON OVERFLOW TRUNCATE '...' WITH COUNT`
  inside a `WITHIN GROUP` call each round-trip unchanged (`ast_check.py`, no `[DIFFERS]`).

## INVARIANT: converse and sibling nodes are mapped together
One SQL meaning can arrive as more than one expression class. When you give a node a dialect
spelling, give it to its siblings too. If you don't, a source dialect that builds the sibling
still emits the old (rejected) form.
- Array containment is a pair of classes in `sqlglot/expressions/array.py`. `ArrayContainsAll(this=a,
  expression=b)` means "a contains every element of b". `ArrayContainedBy(this=a, expression=b)`
  means "a is contained by b", which is the same as `ArrayContainsAll(b, a)`. The base parser
  (`RANGE_PARSERS` in `sqlglot/parser.py`) builds them from `@>` and `<@`, and the base
  generator emits them back as those operators. So Postgres/DuckDB `a <@ b` arrives as
  `ArrayContainedBy`. DuckDB and Postgres also read the function call `ARRAY_CONTAINS_ALL(a, b)`
  into `ArrayContainedBy` with the operands swapped, so after a `rename_func` on
  `ArrayContainsAll` alone, StarRocks still emitted `b <@ a` for that input. A target that has
  only a function form must map BOTH:
  `ArrayContainedBy` becomes `FUNC(b, a)`, with the operands swapped (e.g.
  `self.func("ARRAY_CONTAINS_ALL", e.expression, e.this)`). A `rename_func` on that class would
  keep the operand order and be wrong. `ArrayOverlaps` (`&&`) is the third member of the same
  operator family.
- The parent generator shows you which nodes go together. `MySQLGenerator`
  (`sqlglot/generators/mysql.py`) overrides `arraycontainsall_sql` and `arraycontainedby_sql`
  next to each other, and Doris/StarRocks inherit both. Before overriding one inherited
  `TRANSFORMS` entry or `<node>_sql` method, read the methods and entries next to it in the
  parent and handle each one that has the same meaning. Other pairs already handled together:
  `ArgMax`/`ArgMin`, and `Map`/`VarMap` (`var_map_sql` in `sqlglot/dialects/dialect.py` takes either).
- Check: for every operator and function spelling that builds one of these nodes (grep
  `RANGE_PARSERS`, `FUNCTIONS` and `_sql_names` for the class), run `ast_check.py --read <src>
  --write <target>` and add a `read=` entry to the test. For containment that is at least
  `a @> b` AND `a <@ b` from postgres or duckdb.

## Invariant: the target call must return the SAME VALUE for every input, not just the example
A task's example output shows the function to emit for ONE input. A mapping that reproduces it
can still return a different value for other inputs. Before writing tests:
1. From the SOURCE engine's docs, write down what the function does with: an input/format that
   omits components (no year, no date, no time part), NULL, unparseable input (error or NULL),
   and time zones. Do the same for the target function. Defaults for omitted parts often differ
   between engines; a format-string date/time parser (PARSE_DATETIME, STRPTIME, …) is the usual
   case: load `sqlglot-time-parsing` for the known defaults and where the pieces live.
2. Probe those inputs, and execute them in DuckDB when DuckDB is the target:
   `<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/value_check.py --read <src> "<sql>" ...`
   Exit 3 means the `duckdb` module is not installed: compare against the docs instead (do not
   install it, do not retry) and say so in the final message.
3. Grep the target generator for how sibling functions of the same family (the other
   `PARSE_*` / `STR_TO_*` / format-parsing transforms) already compensate for such differences,
   and follow that precedent, applied to every input rather than special-cased by literal.
4. If a difference remains, the transpile is not done; fix it in the generator. When the
   semantically correct output differs from the task's example string, the semantics win: put
   the correct output in the test and explain the difference in the final message.

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

## CONTRACT: a new expression class for syntax only one dialect has
Applies when you add a class to `sqlglot/expressions/*.py` for syntax no other engine has an
equivalent for (e.g. a call on a runtime/session-resolved name, Snowflake `model!attr` →
`exp.ModelAttribute`, `SHOW` → `exp.Show`).
1. Base generator (`sqlglot/generator.py`): the auto-discovered `<lowercaseclass>_sql` is what
   EVERY OTHER dialect runs. It calls `self.unsupported("<construct> is not supported")` and
   returns a best-effort string (or `""`). Precedents: `modelattribute_sql`, `show_sql`,
   `install_sql`.
2. The owning dialect's spelling goes in an override in `sqlglot/generators/<dialect>.py`
   (`SnowflakeGenerator.modelattribute_sql`, `SnowflakeGenerator.show_sql`) or in a
   `TRANSFORMS` entry (Snowflake has `exp.DynamicIdentifier: rename_func("IDENTIFIER")`).
   Don't make the dialect's spelling the base generator's silent default.
3. Don't invent a lowering for other dialects. A convenience on a neighbouring node is not a
   precedent for a new node that wraps it: dropping a dynamic/runtime wrapper because an
   argument happens to be a literal is a semantic choice. The default is `self.unsupported(...)`
   for every argument form, literal included, unless you can cite the target's docs.
4. Tests: `validate_all(..., write={"<dialect>": "<native sql>", "<other>": UnsupportedError})`.
   `Validator.validate_all` (`tests/dialects/test_dialect.py`) checks a STRING `write=` value
   with `unsupported_level=ErrorLevel.IGNORE`, so a string entry passes even when the generator
   logged "not supported". Passing it does not show the target supports the construct. An
   `UnsupportedError` value is checked with `ErrorLevel.RAISE`, the same check `ast_check.py`
   uses for its `[UNSUPPORTED: ...]` tag.
5. Parser: to add a suffix after a function result (e.g. `NAME(...)(args)`), override
   `_parse_function_call` in the dialect parser and check the returned node. `_parse_table_part`
   (`sqlglot/parser.py`) is the only caller passing `optional_parens=False`, and there a
   following `(a, b)` is a table column alias, not an argument list. Gate the suffix on
   `optional_parens`.
