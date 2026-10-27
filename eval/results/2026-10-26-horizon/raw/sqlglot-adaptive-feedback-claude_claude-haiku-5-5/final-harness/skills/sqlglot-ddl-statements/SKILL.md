---
name: sqlglot-ddl-statements
description: Load when a task adds or changes parsing/generation of a DDL statement in sqlglot (CREATE / ALTER / DROP of a TABLE, VIEW, TYPE, SEQUENCE, FUNCTION, MACRO, INDEX, TRIGGER, …, including statements with several repeated clauses such as overloaded DuckDB macros), or when a clause/property must become legal in another position of a CREATE (e.g. `KEY=VALUE` properties before the column list), or when a statement "contains unsupported syntax. Falling back to parsing as a Command" and must become a real AST node (exp.Create, exp.Alter, …) in any dialect.
---

# DDL statements (exp.Create and friends) in sqlglot

## Who owns what (verified in the source)
- `Parser._parse_create` in `sqlglot/parser.py` handles every `CREATE`. It dispatches on the
  token sets `CREATABLES` / `DB_CREATABLES`. A kind word that is not in them (e.g. `TYPE`, which
  is a plain VAR token) ends in `self._parse_as_command(start)`, which is what prints the
  "Falling back to parsing as a 'Command'" warning and returns `exp.Command`. Trailing tokens
  it did not consume also fall back to Command.
- A dialect can override `_parse_create` in `sqlglot/parsers/<d>.py`, claim its own form, and
  `return super()._parse_create()` for everything else. Check whether the dialect already
  overrides it before adding a second override.
- `exp.Create` is in `sqlglot/expressions/ddl.py`. `kind` is an uppercase string, normalised
  through the dialect's `CREATABLE_KIND_MAPPING` (parse) and `INVERSE_CREATABLE_KIND_MAPPING`
  (generate).
- `Generator.create_sql` in `sqlglot/generator.py` emits the whole statement for every dialect:
  `CREATE <kind> <this> ... AS <expression>`. The ` AS ` is printed whenever `expression` is
  set (`expression_sql = f" AS{...}{expression_sql}"`).

## INVARIANT: `this` is the object's name, `expression` is what follows AS
Base `_parse_create` builds `exp.Create` with this layout:
- `this` holds the name: an `exp.Table` from `_parse_table_parts`, or
  `_parse_schema(this=table_parts)`, i.e. `exp.Schema(this=<Table>, expressions=[ColumnDef…])`,
  only when the column list follows the name directly (`CREATE TABLE t (a INT)`).
- `expression` holds the body that follows `AS`: the DDL SELECT (`_parse_ddl_select`), a table
  (`CREATE TABLE t AS other`), the sequence's type (`_parse_types`), a function body.

A new CREATE form follows the same split. A body introduced by `AS` goes in `expression`, even
when it is a parenthesised attribute list. Build it as `exp.Schema(expressions=[ColumnDef…])`
with no `this`; `schema_sql` then prints just `(...)`. `this` stays the bare name (`exp.Table`).
Do not wrap the name in a Schema for a list that comes after `AS`. That is the CREATE TABLE
shape for a different grammar position, and it loses the `AS` on output.

Consequence you can check: with the layout right, the base `create_sql` already prints
`CREATE <KIND> <name> AS <body>` in every dialect. A dialect `create_sql` override that
re-assembles the statement by hand is a sign the args are in the wrong slots. It also means
every other dialect prints the node without that override. In the rollout that motivated this
skill, the composite type stored in `this` came out of DuckDB/MySQL as `CREATE TYPE c (a INT, b TEXT)`,
with the `AS` dropped. If the dialect really spells something differently, put the generator
change where that difference lives. Don't fork the whole statement.

## CONTRACT: turning a Command-fallback CREATE into an exp.Create
1. Parser: claim the form (base `_parse_create` or a dialect override that defers to `super()`),
   parse the name with `_parse_table_parts()`, parse the body after `AS` into `expression`,
   and keep `_parse_as_command(start)` for forms you do not support and for leftover tokens.
2. Body nodes: reuse existing classes. A type body is `exp.DataType` (e.g.
   `exp.DataType(this=exp.DType.ENUM, expressions=[...])`). An attribute list is
   `exp.Schema(expressions=[exp.ColumnDef…])` via `_parse_column_def`.
   Every variant of one statement (enum list, attribute list, …) uses the same slot mapping. If
   one variant reassigns `this` to a different node class, or mypy reports an incompatible
   assignment to `this`, you have picked a second shape: fix the shape, do not widen the
   annotation to silence mypy.
3. Generator: start from the base `create_sql` output and only add what it gets wrong.
4. Tests: CREATE-statement tests go in `test_ddl` of `tests/dialects/test_<d>.py` (Postgres,
   MySQL, Snowflake, ClickHouse, T-SQL, … have one). DuckDB's `CREATE FUNCTION` / `CREATE MACRO`
   cases live in `TestDuckDB.test_udf`; extend that method. Assert the node layout (`this` and
   `expression` classes for each variant), not just the string. Take that layout from the
   sibling statements above, not from whatever your parser printed.

## CREATE properties: which position is parsed where (verified in the source)
- In base `_parse_create` (`sqlglot/parser.py`), properties between the name and the column
  list are read by `_parse_properties(before=True)`, which calls `_parse_property_before`. The
  base version is Teradata-only: it accepts only `PROPERTY_PARSERS` keywords (with
  NO/DUAL/DEFAULT/… modifiers), never generic `KEY=VALUE`.
- After `_parse_schema(this=table_parts)`, `_parse_properties()` calls `_parse_property`:
  `PROPERTY_PARSERS` first, then generic `key = value` into `exp.Property(this=Var, value=…)`,
  with the value read by `_parse_bitwise()`.
- Snowflake `CREATE DYNAMIC TABLE` goes through the same TABLE path (`DYNAMIC` is a
  `DynamicProperty` entry in `sqlglot/parsers/snowflake.py`), and its column list may be bare
  names with no types, followed by `AS SELECT`.
- Where a property is printed comes from the generator's `PROPERTIES_LOCATION`, not from where
  it was parsed. Generic `exp.Property` is `POST_WITH`, so a before-schema input prints after
  the column list. That move makes `ast_check.py` print `[DIFFERS]`. For this case, compare
  ASTs with `form_equiv.py` (below) instead.

## INVARIANT: a value in a new position must not swallow the next delimiter
Before the schema, the column list `(` comes right after the last property. `_parse_bitwise()`
reads `ident (` as a function call. So reusing `_parse_property` unchanged in that slot turns
`K=ident (cols)` into `K=IDENT(cols)`, an `Anonymous` call, and the column list is gone.
Literal and keyword values (`TRUE`, `1`, `'x'`) do not trigger it. In the rollout that motivated
this section, the agent probed only those values and passed the full suite. The bug then failed
a later DYNAMIC TABLE test. Guarding with "stop if the next token is `(`" protects only the
start of the property, not its value. Fix how the value is parsed in that position. Do not drop
that value kind from the probes.

Procedure for any "X works in position A, support it in position B" task:
1. Before editing, list the already-supported forms in the dialect's test file, e.g.
   `grep -n "CREATE" tests/dialects/test_<d>.py | grep "="`. Note every CREATE kind that has
   both a column list and properties (TABLE, DYNAMIC TABLE, VIEW, …). All of them reach the
   same hook.
2. After your last source edit, run this from the repo root:
   `<python> .lithify/harness/skills/sqlglot-ddl-statements/scripts/form_equiv.py --read <d> "<new form with {V}> => <supported form with {V}>" ...`
   - Use one pair per CREATE kind from step 1.
   - Cover a single property and several (`K={V} W={V}`), and a pair with a trailing `AS SELECT`.
   - `{V}` expands to a boolean, a number, a string, a bare identifier, a dotted name and a
     function call.
   - Done = `SUMMARY` shows 0 AST DIFFERS and 0 PARSE ERROR. A PARSE ERROR on the reference
     side means the pair is wrong, not the fix.
3. Also check that in `repr()`, `this` is `Schema(this=Table, expressions=[…])` holding every
   column.
4. Tests: one `validate_identity(new, canonical)` per CREATE kind you changed. Include a
   bare-identifier value directly before the column list.

## Functions and macros (verified in the source)
- DuckDB tokenizes `MACRO` as `TokenType.FUNCTION` (`sqlglot/dialects/duckdb.py`), so
  `CREATE MACRO` and `CREATE FUNCTION` share base `_parse_create`'s function branch: `this` =
  `exp.UserDefinedFunction(this=<Table>, expressions=<params>, wrapped=True)` (printed
  `name(params)` by `userdefinedfunction_sql`), `expression` = the body. DuckDB's `AS TABLE` is
  not in the body: `DuckDBParser._parse_function_properties` turns it into
  `ReturnsProperty(is_table=True)` in `properties`.
- Base `_parse_user_defined_function_expression` is `_parse_statement()`. Followed by a comma it
  over-reads: `(SELECT 1), (a, b) AS a` becomes one aliased Subquery and the CREATE falls back
  to Command. A body that can be followed by a sibling clause must be parsed so it stops at
  the comma.

## INVARIANT: a list of repeated clauses prints every entry the same way
When one statement carries N parallel clauses (e.g. overloads, each `(params) AS body`), the
list node holds ALL of them as entries of one class, and one generator method prints every
entry. The list follows the name the way the task's input separates them; do not glue the
first entry onto the name to imitate the one-signature `name(params)` shape. That shape
belongs to `UserDefinedFunction`, not to the new list node, so it is no evidence for how the
list prints. Never change the spacing of new output toward a form you believe "canonical"
unless an existing test in `tests/` shows that form.

## Done means, read from output after your last edit
- For every form the task names, `repr()` of the parsed `exp.Create` shows `this` = the name
  (`Table`, no Schema unless the columns precede `AS`) and `expression` = the body node
  (for a repeated-clause list, each entry holds its own body; check each entry's slots).
- The task's example, pasted verbatim, run through
  `<python> .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read <d> --repr "<sql>"`
  shows no `[DIFFERS]` (it ignores case, whitespace runs and a trailing `;`, but a space the
  input has and the output dropped, e.g. `name (a)` → `name(a)`, is flagged). A hand-rolled
  probe that only checks `parse(out).sql() == out` cannot see this. On `[DIFFERS]`, fix the
  generator, and write the test's expected string from the task example, not the output.
- A checker flag (`[FUNCTION CHANGED]`, `[WORDS DROPPED]`) you believe is an artifact is a
  claim to test, not to dismiss. E.g. `FUNCTION CHANGED: TRUE missing` on `K=TRUE (cols)` means
  the checker saw `word (` exactly where your parser decides between a value and a call. Rerun
  with an identifier in that slot (`form_equiv.py` does this) and quote the result.
- Each form round-trips in the dialect, and transpiling to one other dialect still prints
  `AS <body>`, not the body glued onto the name.
- Unsupported variants still parse as `exp.Command`, and existing CREATE TABLE/VIEW tests pass.
