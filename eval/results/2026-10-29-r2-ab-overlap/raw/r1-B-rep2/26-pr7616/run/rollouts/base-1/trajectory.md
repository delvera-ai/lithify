# trajectory base-1

final message:
`CREATE TYPE ... AS ENUM (...)` and `CREATE TYPE ... AS (attr type, ...)` now parse into `exp.Create` nodes and round-trip in Postgres. The full suite passes (1105 tests) and ruff is clean.

**The bug:** the reported statement was never a parse error. The parser fell back to `exp.Command`, which echoes the text back, so it only looked like it round-tripped.

**Changes:**
- `sqlglot/parsers/postgres.py`: a `PostgresParser._parse_create` override handles `CREATE TYPE`. Enum bodies become an `exp.DataType` with `DType.ENUM`, and composite bodies become an `exp.Schema` of column defs. Everything else still goes to `super()._parse_create()`, so other dialects are unaffected.
- `sqlglot/generators/postgres.py`: `datatype_sql` emits `ENUM (...)` with the space Postgres uses, but only when the enum type sits directly under a `Create`. Column types are unchanged.
- `tests/dialects/test_postgres.py`: in `test_ddl`, I added round-trip checks for the enum, qualified and empty enum, and composite forms, plus `assertIsInstance(..., exp.Create)` checks to catch a silent fallback to `Command`. No existing assertions were touched.

**Choices I made:**
- Empty composite `AS ()` falls back to `Command`. Generating it as a `Create` would drop the `AS` and emit invalid SQL. Postgres accepts it, so this is a known gap.
- Shell types (`CREATE TYPE foo`) and range types (`AS RANGE (...)`) still fall back to `Command`. They were out of scope.

**Probe results** (`probe_parse.py --read postgres`, final run):
- OK: the reported enum, qualified `public.book_type AS ENUM ('a')`, empty `ENUM ()`, qualified composite `s.complex AS (...)`, composite with `VARCHAR(100)` and `NOT NULL`.
- OK but still `Command`: `AS ()`, shell `CREATE TYPE shell_t`, `AS RANGE (...)`, and enum with trailing junk. These round-trip as text, which is expected.
- OK and unchanged: `CREATE TABLE t (x ENUM)`.

**Harness deviations:**
- The harness interpreter (`env-sqlglot`) doesn't have `sqlglot` installed, and `-I` ignores `PYTHONPATH`. I ran the probe and tests with `PYTHONPATH=$PWD` and without `-I`. The repo is trusted, so the isolation concern didn't apply.
- Your `CLAUDE.md` asks for the model name at the end of commit messages and PR titles. I haven't committed, so nothing needs it yet.

## events
[tool_use Skill] {"skill": "parse-failure-triage"}
[tool_result] Launching skill: parse-failure-triage
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/.claude/skills/parse-failure-triage

# Parse failure triage

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the
   repository, one statement per line, then run:
   `<python> -I .lithify/harness/scripts/probe_parse.py --read <dialect> < stmts.sql`
   Use the interpreter named in `memory.md`.

2. If the reported statement is OK, do not stop there. Put every variant of the clause the
   report names into the same file: inpu
…[512 chars elided]…
s
   fix: list it in your final message.

4. Add a case for each fixed statement to the existing test function for that dialect, using the
   same assertion style. Do not edit or delete existing assertions.

5. Re-run the probe on the reported statement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.

[tool_use Bash] {"command": "grep -rn \"TYPE\" sqlglot/dialects/postgres.py | head -40; grep -rn \"class Create\\b\\|class Create(\" sqlglot/expressions*.py sqlglot/expressions/ 2>/dev/null | head; grep -rn \"\\\"ENUM\\\"\\|ENUM = \\|\\bENUM\\b\" sqlglot/parser.py sqlglot/tokens.py sqlglot/dialects/postgres.py | head -20; ls .lithify/harness/scripts/"}
[tool_result] sqlglot/dialects/postgres.py:12:    TYPED_DIVISION = True
sqlglot/dialects/postgres.py:84:            "CSTRING": TokenType.PSEUDO_TYPE,
sqlglot/dialects/postgres.py:111:            "REGTYPE": TokenType.OBJECT_IDENTIFIER,
(eval):1: no matches found: sqlglot/expressions*.py
sqlglot/parser.py:460:        TokenType.ENUM,
sqlglot/tokens.py:288:        "ENUM": TokenType.ENUM,
probe_parse.py  2.2K
[tool_use Bash] {"command": "cat .lithify/harness/scripts/probe_parse.py; ls ~/.claude/projects/ 2>/dev/null | head -3; mkdir -p /tmp/ct-probe && printf '%s\\n' \"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\" \"CREATE TYPE public.book_type AS ENUM ()\" \"CREATE TYPE complex AS (r double precision, i double precision)\" \"CREATE TYPE addr AS (street VARCHAR(100), zip INT NOT NULL)\" \"CREATE TYPE e AS ENUM ('a')\" > /tmp/ct-probe/stmts.sql && <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/ct-probe/stmts.sql", "description": "Inspect probe script and reproduce CREATE TYPE failures"}
[tool_result ERROR] Exit code 1
"""Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the 
…[1634 chars elided]…
s.stderr)
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
-/
-Users-user/
-Users-user--cache-lithify-dev-r2-noise-scratch-replay-r2-calibration-calibration-A1-repo/
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; $PY -c \"import sys;print(sys.path)\"; $PY -m pip show sqlglot 2>&1 | head -3; ls <work>/ 2>&1 | head", "description": "Check the project interpreter and sqlglot install"}
[tool_result] <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12', '~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload', '<work>/env-sqlglot/lib/python3.12/site-packages']
<work>/env-sqlglot/bin/python: No module named pip
ab-load-preflight/
archive-b2-before-task4-20261029T104902Z/
claude-2.1.309/
claude-2.1.310/
env-calibration/
env-r2-replicates/
env-round1/
env-sqlglot/
holdouts/
oracle-logs/
[assistant] The project interpreter has no `sqlglot` installed, and `-I` drops `PYTHONPATH`, so I'll point the probe at this checkout directly without `-I`. The repo is trusted, so the isolation concern doesn't apply here.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/ct-probe/stmts.sql; echo EXIT $?; <work>/env-sqlglot/bin/python -c \"import sys; print(sys.version)\" ; grep -n \"Falling back\\|def _parse_create\" sqlglot/parser.py | head", "description": "Probe CREATE TYPE statements against postgres dialect"}
[tool_result] 'CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE public.book_type AS ENUM ()' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE public.book_type AS ENUM ()' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE complex AS 
…[1004 chars elided]…
cision)
          CREATE TYPE complex AS (r double precision, i double precision)
OK        CREATE TYPE addr AS (street VARCHAR(100), zip INT NOT NULL)
          CREATE TYPE addr AS (street VARCHAR(100), zip INT NOT NULL)
OK        CREATE TYPE e AS ENUM ('a')
          CREATE TYPE e AS ENUM ('a')
EXIT 0
3.12.13 (main, Apr 14 2026, 14:33:40) [Clang 22.1.3 ]
3 matches in 3 files:

2344:0:
3280:0:
sqlglot/parser.py:2165:f"'{sql}' contains unsupported syntax. Falling back to parsing as a 'Command'."
[assistant] Reproduced: the statements fall back to `Command` and only look OK because the text is echoed back. Next I'll read how `_parse_create` handles creatable kinds.
[tool_use Bash] {"command": "grep -n \"CREATABLES\\|def _parse_create\\|def _parse_user_defined_function\\|def _parse_types\\|def _parse_column_def\\|def _parse_struct_types\" sqlglot/parser.py | head -20; grep -rn \"TokenType.TYPE\\b\\|\\\"TYPE\\\"\" sqlglot/tokens.py sqlglot/parser.py | head; grep -rn \"class Create(\" -A 30 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head -45", "description": "Locate create parsing and Create expression"}
[tool_result] 19 matches in 10 files:

2344:0:
2488:0:
3280:0:
619:0:t.ClassVar = {
639:0:t.ClassVar = {
6395:0:bool = False) -> exp.Expr | None:
6958:0:
6964:0:TokenType | None = None) -> exp.Expr | None:
8526:0:
sqlglot/parser.py:647:*DB_CREATABLES,
sqlglot/parser.py:765:*CREATABLES,
sqlglot/parser.py:2183:kind = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2297:kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
sqlglot/parser.py:2370:create_token = self._match_set(self
…[1576 chars elided]…
 kind = self.args.get("kind")
sqlglot/expressions/ddl.py-61-        return kind and kind.upper()
sqlglot/expressions/ddl.py-62-
sqlglot/expressions/ddl.py-63-
sqlglot/expressions/ddl.py-64-class SequenceProperties(Expression):
sqlglot/expressions/ddl.py-65-    arg_types = {
sqlglot/expressions/ddl.py-66-        "increment": False,
sqlglot/expressions/ddl.py-67-        "minvalue": False,
sqlglot/expressions/ddl.py-68-        "maxvalue": False,
sqlglot/expressions/ddl.py-69-        "cache": False,
[tool_use Bash] {"command": "sed -n 755,770p sqlglot/parser.py; sed -n 2285,2420p sqlglot/parser.py", "description": "Read the CREATE statement parser"}
[tool_result]         TokenType.UPDATE,
        TokenType.USE,
        TokenType.VOLATILE,
        TokenType.WINDOW,
        TokenType.CURRENT_CATALOG,
        TokenType.LOCALTIME,
        TokenType.LOCALTIMESTAMP,
        TokenType.SESSION_USER,
        TokenType.STRAIGHT_JOIN,
        *ALTERABLES,
        *CREATABLES,
        *SUBQUERY_PREDICATES,
        *TYPE_TOKENS,
        *NO_PAREN_FUNCTIONS,
    } - {TokenType.UNION}


        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, 
…[4867 chars elided]…
               if self._match(TokenType.STRING, advance=False):
                        # Takes care of BigQuery's JavaScript UDF definitions that end in an OPTIONS property
                        # # https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_function_statement
                        expression = self._parse_string()
                        extend_props(self._parse_properties())
                    else:
                        expression = (
[tool_use Bash] {"command": "sed -n 2420,2560p sqlglot/parser.py; grep -n \"^CREATABLES\\|^    CREATABLES\\|CREATABLES = \" sqlglot/parser.py; grep -n \"CREATABLES\" -A 25 sqlglot/parser.py | sed -n 1,30p | grep -v \"^--$\" | head -30", "description": "Read rest of CREATE parsing and CREATABLES set"}
[tool_result]                         expression = (
                            self._parse_user_defined_function_expression()
                            if create_token_type == TokenType.FUNCTION
                            else self._parse_block()
                        )

                    if return_:
                        expression = self.expression(exp.Return(this=expression))
        elif create_token_type == TokenType.INDEX:
            # Postgres allows anonymous indexes, eg. CREATE INDEX IF N
…[5952 chars elided]…
        TokenType.STORAGE_INTEGRATION,
632-        TokenType.STREAMLIT,
633-        TokenType.TABLE,
634-        TokenType.TAG,
635-        TokenType.VIEW,
636-        TokenType.WAREHOUSE,
637-    }
638-
639:    CREATABLES: t.ClassVar = {
640-        TokenType.COLUMN,
641-        TokenType.CONSTRAINT,
642-        TokenType.FOREIGN_KEY,
643-        TokenType.FUNCTION,
644-        TokenType.INDEX,
645-        TokenType.PROCEDURE,
646-        TokenType.TRIGGER,
647:        *DB_CREATABLES,
648-    }
[assistant] `TYPE` isn't in `CREATABLES`, so I need to see how the tail of `_parse_create` builds the node, and whether any dialect already handles `CREATE TYPE`.
[tool_use Bash] {"command": "sed -n 2560,2640p sqlglot/parser.py; grep -rn \"TYPE\\b\" sqlglot/tokens.py | grep -i \"\\\"TYPE\\\"\\|TokenType.TYPE\" ; grep -rln \"CREATE TYPE\\|create type\" tests/ sqlglot/ | head; grep -n \"def _parse_schema\\|def _parse_column_def\\|def _parse_wrapped_csv\\|def _parse_csv\" sqlglot/parser.py", "description": "Read end of CREATE parsing and search for existing CREATE TYPE handling"}
[tool_result]                 clone = self.expression(
                    exp.Clone(this=self._parse_table(schema=True), shallow=shallow, copy=copy)
                )

        if self._curr and not self._match_set((TokenType.R_PAREN, TokenType.COMMA), advance=False):
            return self._parse_as_command(start)

        create_kind_text = create_token.text.upper()
        return self.expression(
            exp.Create(
                this=this,
                kind=self.dialect.CREATABLE_KIND_MAPPING.ge
…[2427 chars elided]…
_column)
                if event_type == "UPDATE" and self._match_text_seq("OF")
                else None
            )

            events.append(self.expression(exp.TriggerEvent(this=event_type, columns=columns)))

            if not self._match(TokenType.OR):
                break
5 matches in 3 files:

7043:0:exp.Expr | None = None) -> exp.Expr | None:
8526:0:
sqlglot/parser.py:7060:def _parse_column_def(
sqlglot/parser.py:8417:def _parse_csv(
sqlglot/parser.py:8435:def _parse_wrapped_csv(
[assistant] No dialect handles `CREATE TYPE` today, so this is new parser and generator work. Next I'll check how `_match_text_seq` and the Postgres parser override points work, and how `create_sql` emits `expression`.
[tool_use Bash] {"command": "grep -n \"def _match_text_seq\" -A3 sqlglot/parser.py; grep -n \"class Parser\" -A3 sqlglot/dialects/postgres.py; grep -n \"def _parse_\\|STATEMENT_PARSERS\\|CREATABLE\" sqlglot/dialects/postgres.py | head -40; grep -n \"def create_sql\" -A60 sqlglot/generator.py | head -110", "description": "Inspect helper signatures, postgres parser hooks, and create_sql generator"}
[tool_result] 1948:    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1949-        index = self._index
1950-        string_type = TokenType.STRING
1951-        for text in texts:
0 matches for 'def _parse_\|STATEMENT_PARSERS\|CREATABLE'
1284:    def create_sql(self, expression: exp.Create) -> str:
1285-        kind = self.sql(expression, "kind")
1286-        kind = self.dialect.INVERSE_CREATABLE_KIND_MAPPING.get(kind) or kind
1287-
1288-        properties = expression.args.get("properti
…[2256 chars elided]…
      )
1337-                postalias_props_sql = f" {postalias_props_sql}" if postalias_props_sql else ""
1338-                expression_sql = f" AS{postalias_props_sql}{expression_sql}"
1339-
1340-        postindex_props_sql = ""
1341-        if properties_locs.get(exp.Properties.Location.POST_INDEX):
1342-            postindex_props_sql = self.properties(
1343-                exp.Properties(expressions=properties_locs[exp.Properties.Location.POST_INDEX]),
1344-                wrapped=False,
[assistant] The generator already prints `AS <expression>` for `Create`, so the body of a type can live in `expression`. Next I'll check the schema, column-def and DataType helpers, and the Postgres class layout.
[tool_use Bash] {"command": "grep -n \"^class \\|    class \" sqlglot/dialects/postgres.py; grep -n \"def _parse_schema\\|def _parse_field_def\\|def _parse_column_def\\|def _parse_as_command\" -A12 sqlglot/parser.py | head -120; grep -n \"def schema_sql\" -A12 sqlglot/generator.py; grep -n \"Type.ENUM\\|ENUM\" sqlglot/generator.py sqlglot/dialects/postgres.py sqlglot/expressions/datatypes.py | head", "description": "Inspect schema/column helpers and ENUM datatype generation"}
[tool_result] 2 matches in 2 files:

10:0:
61:0:
7043:    def _parse_schema(self, this: exp.Expr | None = None) -> exp.Expr | None:
7044-        index = self._index
7045-        if not self._match(TokenType.L_PAREN):
7046-            return this
7047-
7048-        # Disambiguate between schema and subquery/CTE, e.g. in INSERT INTO table (<expr>),
7049-        # expr can be of both types
7050-        if self._match_set(self.SELECT_START_TOKENS):
7051-            self._retreat(index)
7052-            return thi
…[2185 chars elided]…
n f"({self.sep('')}{self.expressions(expression)}{self.seg(')', sep='')}"
3216-        return ""
3217-
3218-    def star_sql(self, expression: exp.Star) -> str:
3219-        except_ = self.expressions(expression, key="except_", flat=True)
3220-        except_ = f"{self.seg(self.STAR_EXCEPT)} ({except_})" if except_ else ""
3 matches in 1 files:

sqlglot/expressions/datatypes.py:62:ENUM = auto()
sqlglot/expressions/datatypes.py:63:ENUM8 = auto()
sqlglot/expressions/datatypes.py:64:ENUM16 = auto()
[tool_use Bash] {"command": "grep -n \"^class \\|^    class \\|^    [A-Z_]* = \\|def \\|^from\\|^import\" sqlglot/dialects/postgres.py | head -80; grep -rn \"ENUM\" sqlglot/generator.py sqlglot/dialects/*.py | grep -v \"^sqlglot/dialects/duckdb\" | head -20", "description": "Survey postgres dialect structure and ENUM handling"}
[tool_result] 18 matches in 4 files:

10:0:
16:0:MI:SS'"
61:0:
sqlglot/dialects/postgres.py:1:from __future__ import annotations
sqlglot/dialects/postgres.py:3:from sqlglot import exp, tokens
sqlglot/dialects/postgres.py:4:from sqlglot.dialects.dialect import Dialect
sqlglot/dialects/postgres.py:5:from sqlglot.generators.postgres import PostgresGenerator
sqlglot/dialects/postgres.py:6:from sqlglot.parsers.postgres import PostgresParser
sqlglot/dialects/postgres.py:7:from sqlglot.tokens import TokenType
sqlglo
…[175 chars elided]…
es.py:14:CONCAT_WS_COALESCE = True
sqlglot/dialects/postgres.py:15:NULL_ORDERING = "nulls_are_large"
sqlglot/dialects/postgres.py:17:TABLESAMPLE_SIZE_IS_PERCENT = True
sqlglot/dialects/postgres.py:18:TABLES_REFERENCEABLE_AS_COLUMNS = True
sqlglot/dialects/postgres.py:20:DEFAULT_FUNCTIONS_COLUMN_NAMES = {
sqlglot/dialects/postgres.py:24:TIME_MAPPING = {
sqlglot/dialects/clickhouse.py:90:            "ENUM8": TokenType.ENUM8,
sqlglot/dialects/clickhouse.py:91:            "ENUM16": TokenType.ENUM16,
[assistant] Parsers and generators live in `sqlglot/parsers/` and `sqlglot/generators/`. I'll check those for existing `_parse_create` overrides and how a `DataType` ENUM is emitted.
[tool_use Bash] {"command": "ls sqlglot/parsers/ | head -50; grep -rn \"_parse_create\\b\\|def _parse_create(\" sqlglot/parsers/ | head; grep -n \"def \\|^class \" sqlglot/parsers/postgres.py | head -80; grep -rn \"ENUM\\|def datatype_sql\" sqlglot/generators/generator.py sqlglot/generators/postgres.py sqlglot/generator.py 2>/dev/null | head", "description": "Survey parser package layout and overrides"}
[tool_result] __init__.py  1B
athena.py  2.3K
base.py  582B
bigquery.py  28.3K
clickhouse.py  32.6K
databricks.py  1.7K
doris.py  5.0K
dremio.py  3.8K
drill.py  671B
druid.py  108B
duckdb.py  15.3K
dune.py  124B
exasol.py  6.5K
fabric.py  1.3K
hive.py  10.8K
materialize.py  1.3K
mysql.py  23.6K
oracle.py  8.5K
postgres.py  12.8K
presto.py  5.2K
prql.py  6.9K
redshift.py  5.6K
risingwave.py  2.2K
singlestore.py  10.4K
snowflake.py  52.4K
solr.py  353B
spark.py  5.2K
spark2.py  4.2K
sqlite.py  3.5K
starrocks.py
…[1005 chars elided]…
0:
335:0:exp.Identifier) -> exp.Expr | None:
41:0:list, dialect: DialectType = None) -> exp.RegexpReplace:
66:0:list) -> exp.Levenshtein:
83:0:
sqlglot/parsers/postgres.py:279:column_def = self._parse_column_def(this=param_name, computed_column=False)
sqlglot/parsers/postgres.py:321:def _parse_generated_as_identity(
sqlglot/generators/postgres.py:477:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generator.py:1683:    def datatype_sql(self, expression: exp.DataType) -> str:
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/parsers/postgres.py; echo ----; sed -n 55,80p sqlglot/parsers/starrocks.py; echo ----; grep -n \"    def \\|^class \\|^def \" sqlglot/parsers/postgres.py | sed -n 1,60p; echo ----; sed -n 470,500p sqlglot/generators/postgres.py; echo ----; grep -n \"STATEMENT_PARSERS\\|ENUM\" sqlglot/parsers/postgres.py sqlglot/generators/postgres.py | head", "description": "Read postgres parser module, a precedent override, and datatype_sql"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    DialectType,
    binary_from_function,
    build_formatted_time,
    build_json_extract_path,
    build_timestamp_trunc,
)
from sqlglot.helper import is_int, seq_get
from sqlglot.parser import binary_range_parser
from sqlglot.tokens import TokenType


def _build_generate_series(args: list) -> exp.ExplodingGenerateSeries:
    # The goal is to convert step values like 
…[2976 chars elided]…
al for transpilation but when roundtripping it's superfluous
        if isinstance(this, exp.IntDiv) and expression.to == exp.DType.DECIMAL.into_expr():
            return self.sql(this)

        return super().cast_sql(expression, safe_prefix=safe_prefix)

    def array_sql(self, expression: exp.Array) -> str:
        exprs = expression.expressions
----
2 matches in 1 files:

sqlglot/parsers/postgres.py:176:STATEMENT_PARSERS = {
sqlglot/parsers/postgres.py:177:**parser.Parser.STATEMENT_PARSERS,
[assistant] The codebase has moved to `DType` and split parsers into per-dialect modules. I'll read the `PostgresParser` class and its `_parse_create`-adjacent methods, plus the generator's `exp.DType` ENUM output.
[tool_use Bash] {"command": "grep -n \"class PostgresParser\" -A3 sqlglot/parsers/postgres.py; grep -n \"    def _parse\\|    def \\w*(self\" sqlglot/parsers/postgres.py | head -40; grep -n \"ENUM\\|def _parse_create\\|TYPE\" sqlglot/parsers/postgres.py | head; sed -n 1,10p sqlglot/parsers/starrocks.py | head -3; grep -n \"class DataType\" -A5 sqlglot/expressions/datatypes.py | head; grep -n \"def datatype_sql\" -A25 sqlglot/generator.py | head -40", "description": "Locate PostgresParser class and base datatype_sql"}
[tool_result] 83:class PostgresParser(parser.Parser):
84-    SUPPORTS_OMITTED_INTERVAL_SPAN_UNIT = True
85-
86-    PROPERTY_PARSERS = {
rg: regex parse error:
    (?:    def _parse|    def \w*(self)
    ^
error: unclosed group
0 matches for '    def _parse\|    def \w*(self'
8 matches in 4 files:

221:0:MODE TYPE
234:0:MODE NAME TYPE
57:0:
sqlglot/parsers/postgres.py:187:JSON_ARROWS_REQUIRE_JSON_TYPE = True
sqlglot/parsers/postgres.py:193:exp.JSONExtract, arrow_req_json_type=self.JSON_ARROWS_REQUIRE_JSON_TYPE
…[1147 chars elided]…
            self.expressions(
1699-                expression, dynamic=True, new_line=True, skip_first=True, skip_last=True
1700-            )
1701-            if expr_nested and self.pretty
1702-            else self.expressions(expression, flat=True)
1703-        )
1704-
1705-        if type_value in self.UNSUPPORTED_TYPES:
1706-            self.unsupported(
1707-                f"Data type {type_value.value} is not supported when targeting {self.dialect.__class__.__name__}"
1708-            )
[tool_use Bash] {"command": "grep -n \"    def \" sqlglot/parsers/postgres.py; sed -n 176,186p sqlglot/parsers/postgres.py; sed -n 1708,1725p sqlglot/generator.py; grep -n \"TYPE_PARAM_SETTINGS\\|ENUM\" sqlglot/generator.py | head -5; cat tests/dialects/test_postgres.py | grep -n \"def test_\\|validate_identity(\\\"CREATE\" | head -30", "description": "List PostgresParser methods, statement parsers, and test layout"}
[tool_result] 9 matches in 9 files:

205:0:
253:0:TokenType) -> exp.InOutColumnConstraint:
271:0:
290:0:
299:0:
309:0:
312:0:
335:0:exp.Identifier) -> exp.Expr | None:
sqlglot/parsers/postgres.py:321:def _parse_generated_as_identity(
    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.END: lambda self: self._parse_commit_or_rollback(),
    }

    UNARY_PARSERS = {
        **parser.Parser.UNARY_PARSERS,
        # The `~` token is remapped from TILDE to RLIKE in Postgres due t
…[2854 chars elided]…
CTION foo(inout VARCHAR)")  # "inout" as identifier
1271:        self.validate_identity("CREATE FUNCTION foo(variadic INT[])")  # "variadic" as identifier
1275:        self.validate_identity("CREATE OR REPLACE FUNCTION foo(INOUT id UUID)")
1279:        self.validate_identity("CREATE FUNCTION foo(OUT x INT DEFAULT 5)")
1280:        self.validate_identity("CREATE FUNCTION foo(INOUT y VARCHAR DEFAULT 'test')")
1281:        self.validate_identity("CREATE FUNCTION foo(IN a INT DEFAULT 0, OUT b INT)")
[assistant] I have enough to design the fix. Before editing, I'll read the end of `PostgresParser` to find where its methods live.
[tool_use Bash] {"command": "awk 'NR>=186 && NR<=320 && /^    [a-zA-Z_]/ {print NR\": \"$0}' sqlglot/parsers/postgres.py; sed -n 225,250p sqlglot/parsers/postgres.py", "description": "List methods and class body layout in PostgresParser"}
[tool_result] 187:     JSON_ARROWS_REQUIRE_JSON_TYPE = True
189:     COLUMN_OPERATORS = {
203:     ARG_MODE_TOKENS: t.ClassVar = {TokenType.IN, TokenType.OUT, TokenType.INOUT, TokenType.VARIADIC}
205:     def _parse_parameter_mode(self) -> TokenType | None:
253:     def _create_mode_constraint(self, param_mode: TokenType) -> exp.InOutColumnConstraint:
271:     def _parse_function_parameter(self) -> exp.Expr | None:
290:     def _parse_query_parameter(self) -> exp.Expr | None:
299:     def _parse_date_part(sel
…[591 chars elided]…
lt-in or user-defined (allow_identifiers=True)
        if self._next.token_type not in self.ID_VAR_TOKENS:
            return None

        is_followed_by_any_type = self._try_parse(
            lambda: (
                self._advance(2)  # type: ignore
                or self._parse_types(check_func=False, allow_identifiers=True)
            ),
            retreat=True,
        )

        if is_followed_by_any_type:
            return mode_token.token_type  # Pattern: "OUT x INT" -> OUT is mode
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "offset": 308, "limit": 16}
[tool_result] 308	
309	    def _parse_unique_key(self) -> exp.Expr | None:
310	        return None
311	
312	    def _parse_jsonb_exists(self) -> exp.JSONBExists:
313	        return self.expression(
314	            exp.JSONBExists(
315	                this=self._parse_bitwise(),
316	                path=self._match(TokenType.COMMA)
317	                and self.dialect.to_json_path(self._parse_bitwise()),
318	            )
319	        )
320	
321	    def _parse_generated_as_identity(
322	        self,
323	    ) -> (
[assistant] I'll add the override at the end of `PostgresParser`. It only handles `CREATE TYPE`, and everything else goes to `super()`, so other dialects are untouched.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "                path=self._match(TokenType.COMMA)\n                and self.dialect.to_json_path(self._parse_bitwise()),\n            )\n        )\n\n    def _parse_generated_as_identity(", "new_string": "    
…[704 chars elided]…
L_PAREN, advance=False):\n            expression = exp.Schema(expressions=self._parse_wrapped_csv(self._parse_field_def))\n        else:\n            return self._parse_as_command(start)\n\n        if self._curr:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Create(this=this, kind=\"TYPE\", expression=expression))\n\n    def _parse_generated_as_identity("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/ct-probe/stmts.sql; echo EXIT $?; PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TYPE book_type AS ENUM (\\'FICTION\\', \\'NONFICTION\\')','CREATE TYPE complex AS (r double precision, i double precision)']:\n    e=sqlglot.parse_one(s,read='postgres'); print(type(e).__name__, repr(e)[:200]); print(e.sql('postgres'))\n\"", "description": "Re-run probe and inspect AST for CREATE TYPE"}
[tool_result] OK        CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
          CREATE TYPE book_type AS ENUM('FICTION', 'NONFICTION')
ERR       CREATE TYPE public.book_type AS ENUM ()
          output does not re-parse: ParseError: Expecting (. Line 1, Col: 36.
OK        CREATE TYPE complex AS (r double precision, i double precision)
          CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
OK        CREATE TYPE addr AS (street VARCHAR(100), zip INT NOT NULL)
          CREATE TYPE a
…[163 chars elided]…
his=Identifier(this=book_type, quoted=False)),
  kind=TYPE,
  expression=DataType(
    this=DType.ENUM,
    expressions=[
      Literal(this='FICTION', is_string=True),
    
CREATE TYPE book_type AS ENUM('FICTION', 'NONFICTION')
Create Create(
  this=Table(
    this=Identifier(this=complex, quoted=False)),
  kind=TYPE,
  expression=Schema(
    expressions=[
      ColumnDef(
        this=Identifier(this=r, quoted=False),
        kind
CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
[assistant] Two problems show up. The enum body prints as `ENUM('a')` with no space, which doesn't match Postgres' `AS ENUM ('a')`. The empty `ENUM ()` also drops its parentheses, so it doesn't re-parse. I'll fix both in the Postgres generator, scoped to a `DataType` that sits directly under a `Create`, so column types are unaffected.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py", "old_string": "            return f\"FLOAT({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)", "new_string": "            return f\"FLOAT({self.expressions(expression, flat=True)})\"\n\n        if expression.is_type(exp.DType.ENUM) and isinstance(expression.parent, exp.Create):\n            return f\"ENUM ({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/generators/postgres.py has been updated successfully.
[assistant] Next I'll re-run the probe with the reported statement plus the variants: qualified names, empty enum and composite, a shell type, a range type (which should still fall back), and a trailing-junk case.
[tool_use Bash] {"command": "printf '%s\\n' \"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\" \"CREATE TYPE public.book_type AS ENUM ('a')\" \"CREATE TYPE book_type AS ENUM ()\" \"CREATE TYPE s.complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\" \"CREATE TYPE addr AS (street VARCHAR(100), zip INT NOT NULL)\" \"CREATE TYPE empty_comp AS ()\" \"CREATE TYPE shell_t\" \"CREATE TYPE r AS RANGE (SUBTYPE = float8)\" \"CREATE TYPE e AS ENUM ('a') extra\" \"CREATE TABLE t (x ENUM)\" > /tmp/ct-probe/stmts2.sql && PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/ct-probe/stmts2.sql 2>/dev/null; echo EXIT $?", "description": "Probe CREATE TYPE variants after generator fix"}
[tool_result] OK        CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
          CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')
OK        CREATE TYPE public.book_type AS ENUM ('a')
          CREATE TYPE public.book_type AS ENUM ('a')
OK        CREATE TYPE book_type AS ENUM ()
          CREATE TYPE book_type AS ENUM ()
OK        CREATE TYPE s.complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
          CREATE TYPE s.complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)
OK        CREATE TYPE ad
…[14 chars elided]…
VARCHAR(100), zip INT NOT NULL)
          CREATE TYPE addr AS (street VARCHAR(100), zip INT NOT NULL)
OK        CREATE TYPE empty_comp AS ()
          CREATE TYPE empty_comp
OK        CREATE TYPE shell_t
          CREATE TYPE shell_t
OK        CREATE TYPE r AS RANGE (SUBTYPE = float8)
          CREATE TYPE r AS RANGE (SUBTYPE = float8)
OK        CREATE TYPE e AS ENUM ('a') extra
          CREATE TYPE e AS ENUM ('a') extra
OK        CREATE TABLE t (x ENUM)
          CREATE TABLE t (x ENUM)
EXIT 0
[assistant] Almost everything round-trips now. One real bug is left: the empty composite `AS ()` loses its `AS` and produces invalid SQL. I'll send empty composite bodies to the existing `Command` fallback, so their text is preserved exactly.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py", "old_string": "        elif self._match(TokenType.L_PAREN, advance=False):\n            expression = exp.Schema(expressions=self._parse_wrapped_csv(self._parse_field_def))\n        else:\n            return self._parse_as_command(start)", "new_string": "        elif self._match(TokenType.L_PAREN, advance=False):\n            attributes = self._parse_wrapped_csv(self._parse_field_def)\n            if not attributes:\n                return self._parse_as_command(start)\n            expression = exp.Schema(expressions=attributes)\n        else:\n            return self._parse_as_command(start)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[assistant] Now the tests. I'll check the imports and helpers in `test_postgres.py` so the new cases use the file's existing assertion style.
[tool_use Bash] {"command": "sed -n 1,9p tests/dialects/test_postgres.py; grep -n \"assertIsInstance\\|self.parse_one\" tests/dialects/test_postgres.py | head -3; grep -n \"CREATE TABLE test (foo HSTORE)\" tests/dialects/test_postgres.py", "description": "Check test file imports and helper usage"}
[tool_result ERROR] Exit code 1
from sqlglot import ParseError, UnsupportedError, exp, transpile
from sqlglot.helper import logger as helper_logger
from tests.dialects.test_dialect import Validator


class TestPostgres(Validator):
    maxDiff = None
    dialect = "postgres"

16 matches in 2 files:

869:0::UUID"), exp.Cast)
0 matches for 'CREATE TABLE test (foo HSTORE)'
[tool_use Bash] {"command": "grep -n \"def parse_one\\|def validate_identity\" -A3 tests/dialects/test_dialect.py | head -12", "description": "Confirm Validator helper methods"}
[tool_result] 29:    def parse_one(self, sql, **kwargs):
30-        return parse_one(sql, read=self.dialect, **kwargs)
31-
32-    def assert_duckdb_sql(
--
53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
[assistant] `validate_identity` takes `check_command_warning=True`, which asserts the statement doesn't fall back to `Command`. That's the right check for this bug, so I'll use it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\"CREATE TABLE test (foo JSONB)\")\n", "new_string": "        self.validate_identity(\"CREATE TABLE test (foo JSONB)\")\n        self.validate_identity(\n            \"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\", check_command_warning=True\n        )\n        self.validate_identity(\"CREATE TYPE public.book_type AS ENUM ()\", check_command_warning=True)\n        self.validate_identity(\n            \"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\",\n            check_command_warning=True,\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read postgres < /tmp/ct-probe/stmts2.sql; echo PROBE_EXIT $?; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -15", "description": "Re-run probe and postgres dialect tests"}
[tool_result] 'CREATE TYPE empty_comp AS ()' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE empty_comp AS ()' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE shell_t' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE shell_t' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREATE TYPE r AS RANGE (SUBTYPE = float8)' contains unsupported syntax. Falling back to parsing as a 'Command'.
'CREA
…[1589 chars elided]…
= self.parse_one(sql)
>               assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
                                                                       ^^^^^^^^^^^^
E               IndexError: list index out of range

tests/dialects/test_dialect.py:59: IndexError
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_ddl - IndexError: ...
1 failed, 24 passed, 363 subtests passed in 0.32s
[assistant] I misread the helper: `check_command_warning=True` asserts the statement *does* fall back, so the test failed as it should have for the wrong flag. I'll drop the flag and assert `exp.Create` directly, keeping `validate_identity` for the round-trip.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\", check_command_warning=True\n        )\n        self.validate_identity(\"CREATE TYPE public.book_typ
…[413 chars elided]…
validate_identity(\"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\")\n        self.assertIsInstance(\n            self.parse_one(\"CREATE TYPE book_type AS ENUM ('FICTION', 'NONFICTION')\"), exp.Create\n        )\n        self.assertIsInstance(\n            self.parse_one(\"CREATE TYPE complex AS (r DOUBLE PRECISION, i DOUBLE PRECISION)\"),\n            exp.Create,\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-151619-postgres-dialect-create-type-fal/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -3; echo ===FULL; time $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo FULL_EXIT ${PIPESTATUS[0]}", "description": "Run postgres dialect tests then full suite"}
[tool_result ERROR] Exit code 1
.........................                              [100%]
25 passed, 378 subtests passed in 0.16s
(eval):1: ==FULL not found
[assistant] The Postgres test file passes (25 tests). My echo label broke zsh, so I'll run the full suite on its own.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full test suite", "timeout": 300000}
[tool_result] ........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
....................................................................................................................
…[262 chars elided]…
...... [ 70%]
..................................... [ 73%]
......................................................................................................................................................... [ 87%]
........................... [ 89%]
............................... [ 92%]
............................................................. [ 98%]
....................                                                                  [100%]
1105 passed, 17982 subtests passed in 54.53s
[assistant] The full suite passes: 1105 tests, no failures. I'll run a quick lint and format check on the three changed files, then review the diff.
[tool_use Bash] {"command": "(command -v ruff && ruff check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py && ruff format --check sqlglot/parsers/postgres.py sqlglot/generators/postgres.py tests/dialects/test_postgres.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stats"}
[tool_result] <work>/env-sqlglot/bin/ruff
Ruff: No issues found
3 files already formatted
sqlglot/generators/postgres.py  |  3 +++
 sqlglot/parsers/postgres.py     | 26 ++++++++++++++++++++++++++
 tests/dialects/test_postgres.py | 10 ++++++++++
 3 files changed, 39 insertions(+)
[assistant] `CREATE TYPE ... AS ENUM (...)` and `CREATE TYPE ... AS (attr type, ...)` now parse into `exp.Create` nodes and round-trip in Postgres. The full suite passes (1105 tests) and ruff is clean.

**The bug:** the reported statement was never a parse error. The parser fell back to `exp.Command`, which echoes the text back, so it only looked like it round-tripped.

**Changes:**
- `sqlglot/parsers/postgres.py`: a `PostgresParser._parse_create` override handles `CREATE TYPE`. Enum bodies become an `exp.DataType` with `DType.ENUM`, and composite bodies become an `exp.Schema` of column defs. Everything e
…[1077 chars elided]…
LL`.
- OK but still `Command`: `AS ()`, shell `CREATE TYPE shell_t`, `AS RANGE (...)`, and enum with trailing junk. These round-trip as text, which is expected.
- OK and unchanged: `CREATE TABLE t (x ENUM)`.

**Harness deviations:**
- The harness interpreter (`env-sqlglot`) doesn't have `sqlglot` installed, and `-I` ignores `PYTHONPATH`. I ran the probe and tests with `PYTHONPATH=$PWD` and without `-I`. The repo is trusted, so the isolation concern didn't apply.
- Your `CLAUDE.md` asks for the model name at the end of commit messages and PR titles. I haven't committed, so nothing needs it yet.
