# trajectory base-1

final message:
Druid now parses `JSON_VALUE(... RETURNING <type>)`, and the reported query round-trips unchanged. The full suite passes: `SUMMARY: 1122 passed, 18178 subtests passed in 51.82s`, `EXIT: 0`. The changes are uncommitted in the worktree.

**What was wrong:** Druid had no `JSON_VALUE` entry in its parser, so the call fell through to the generic function parser, which doesn't accept `RETURNING`. MySQL, Trino and Exasol each map `JSON_VALUE` to the shared `_parse_json_value`.

**What I changed:**
- `sqlglot/parsers/druid.py`: added `"JSON_VALUE": lambda self: self._parse_json_value()` to `DruidParser.FUNCTION_PARSERS`, matching Trino and Exasol.
- `sqlglot/parser.py`: in `_parse_json_value`, the `RETURNING` type is now parsed with `_parse_types()` instead of `_parse_type()`. Before this, `BIGINT` came back as a `Column` and `DECIMAL(4, 2)` as an `Anonymous` call, so the node didn't hold a type. `DataType` is now what `CAST` produces too.
- `tests/dialects/test_druid.py`: added `test_json_value`. It round-trips `RETURNING` with `VARCHAR`, `BIGINT`, `DOUBLE` and `DECIMAL(4, 2)`, and asserts the `returning` arg is an `exp.DataType`.

**Side effect on other dialects:** the shared change affects MySQL and Exasol output for these types. `RETURNING BIGINT` used to come out as `` `BIGINT` `` (MySQL) or `"BIGINT"` (Exasol) and now comes out bare. MySQL `RETURNING VARCHAR` now renders as `TEXT`, because MySQL's type mapping applies once the node is a real type. Trino output is unchanged for these types.

**Not done:**
- **`RETURNING VARCHAR ARRAY`** is the array form in Druid's documentation. It parses but comes back as `ARRAY<VARCHAR>`, so it does not round-trip. Druid's generator has no postfix array-type rendering, and adding it changes `CAST` and column types too. That is a separate change, so I left it out. I can do it if you want.
- **Transpiling to MySQL and DuckDB is not valid.** `RETURNING BIGINT` is passed through as-is, and MySQL's `JSON_VALUE` does not accept `BIGINT` in `RETURNING`. DuckDB has no `RETURNING` clause on `json_value`. Both problems predate this change.
- **`ON EMPTY` / `ON ERROR`** are accepted by the shared helper, but I did not check them against Druid's docs and did not add tests for them.

**Process note:** I edited `sqlglot/parsers/druid.py` before reading the `sqlglot-data-types` skill, which the harness asks for before the first source edit. I read it before changing `parser.py`, and its guidance (only the `RETURNING` call site changed, not `_parse_types`) held.

## events
[assistant] I'll start by reading the relevant harness skills and how Druid and the other dialects handle `JSON_VALUE`.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md && echo ---- && cat .lithify/harness/skills/sqlglot-json-table/SKILL.md && echo ---- && grep -rn \"JSON_VALUE\\|JSONValue\\|RETURNING\" sqlglot/dialects/druid.py sqlglot/parsers/druid.py sqlglot/generators/druid.py sqlglot/parsers/mysql.py sqlglot/parsers/trino.py sqlglot/parsers/exasol.py sqlglot/parser.py sqlglot/generators/mysql.py sqlglot/generators/trino.py sqlglot/generators/exasol.py sqlglot/generator.py 2>&1 | head -80", "description": "Read matching skills and grep JSON_VALUE handling"}
[tool_result] ---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTERVAL), or when adding/mapping a dialect function — any change to a
…[19524 chars elided]…
17:        return_type = f" RETURNING {return_type}" if return_type else ""
sqlglot/generator.py:5531:    def jsonvalue_sql(self, expression: exp.JSONValue) -> str:
sqlglot/generator.py:5534:        returning = f" RETURNING {returning}" if returning else ""
sqlglot/generator.py:5539:        return self.func("JSON_VALUE", expression.this, f"{path}{returning}{on_condition}")
sqlglot/generator.py:5953:        by_ref = f"{self.sep()}RETURNING SEQUENCE BY REF" if expression.args.get("by_ref") else ""
[assistant] Both skills are read. Next I'll look at the shared `_parse_json_value` and how Druid is wired.
[tool_use Bash] {"command": "sed -n 10025,10060p sqlglot/parser.py && echo ---- && sed -n 5528,5542p sqlglot/generator.py && echo ---- && cat sqlglot/parsers/druid.py && echo ---- && cat sqlglot/dialects/druid.py | head -60 && echo ---- && grep -n \"JSON_VALUE\\|JSONValue\" -r sqlglot/dialects/druid.py sqlglot/generators/druid.py tests/dialects/test_druid.py; grep -n \"RETURNING\" tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py | head", "description": "Read JSON_VALUE parser, generator and Druid files"}
[tool_result]         if exp_class == exp.TryCast:
            kwargs["requires_string"] = self.dialect.TRY_CAST_REQUIRES_STRING

        return self.expression(exp_class(**kwargs))

    def _parse_json_value(self) -> exp.JSONValue:
        this = self._parse_bitwise()
        self._match(TokenType.COMMA)
        path = self._parse_bitwise()

        returning = self._match(TokenType.RETURNING) and self._parse_type()

        return self.expression(
            exp.JSONValue(
                this=this,
      
…[2002 chars elided]…
rice' RETURNING DECIMAL(4, 2))"""
tests/dialects/test_trino.py:162:                f"""SELECT JSON_VALUE({json_doc}, 'lax $.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
tests/dialects/test_mysql.py:1561:            f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
tests/dialects/test_mysql.py:1566:                f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
[assistant] Druid has no `JSON_VALUE` entry, so it falls through to the generic function parser. Before editing, I'll confirm the project Python and probe what Druid and MySQL build today.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; cat .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py | head -30; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['druid','mysql']:\n    try:\n        t = sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", dialect=d)\n        print(d, repr(t.selects[0]))\n        print(d, t.sql(dialect=d))\n    except Exception as e: print(d, 'ERR', e)\nt = sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a') FROM t\\\", dialect='druid')\nprint(repr(t.selects[0]))\n\"", "description": "Probe Druid and MySQL JSON_VALUE parsing"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
#!/usr/bin/env python3
"""Show what a SQL string parses into, how it round-trips, and how it transpiles.

Usage (run from the repository root with the project's python):
    <python> .lithify/harness/skills/sqlglot
…[1286 chars elided]…
.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m BIGINT) FROM t
mysql JSONValue(
  this=Column(
    this=Identifier(this=x, quoted=False)),
  path=JSONPath(
    expressions=[
      JSONPathRoot(),
      JSONPathKey(this=a)]),
  returning=Column(
    this=Identifier(this=BIGINT, quoted=False)))
mysql SELECT JSON_VALUE(x, '$.a' RETURNING `BIGINT`) FROM t
Anonymous(
  this=JSON_VALUE,
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False)),
    Literal(this='$.a', is_string=True)])
[assistant] Druid fails at the `RETURNING` token as reported, and MySQL parses it to a `JSONValue` node. The MySQL output backticks `BIGINT`, which means `BIGINT` is parsed as a column there, not as a type. I'll check how the base parser and the Trino parser treat `BIGINT` before choosing the fix.
[tool_use Bash] {"command": "sed -n 1,30p sqlglot/parsers/exasol.py | head -40; grep -n \"FUNCTION_PARSERS\" sqlglot/parsers/exasol.py sqlglot/parsers/trino.py; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor d in ['trino','exasol','mysql','druid','']:\n    for s in [\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT)\\\", \\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING VARCHAR)\\\"]:\n        try: print(d, sqlglot.transpile(s, read=d or None, write=d or None)[0])\n        except Exception as e: print(d, 'ERR', e)\n\"; grep -n \"BIGINT\\|VARCHAR\" tests/dialects/test_druid.py | head", "description": "Compare BIGINT/VARCHAR round-trips across dialects"}
[tool_result] from __future__ import annotations


from sqlglot import exp, parser
from sqlglot.dialects.dialect import (
    binary_from_function,
    build_date_delta,
    build_formatted_time,
    build_timetostr_or_tochar,
    build_trunc,
)
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType

DATE_UNITS = {"DAY", "WEEK", "MONTH", "YEAR", "HOUR", "MINUTE", "SECOND"}


# https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/zeroifnull.htm
def _build_zeroif
…[943 chars elided]…
 RETURNING "VARCHAR")
mysql SELECT JSON_VALUE(x, '$.a' RETURNING `BIGINT`)
mysql SELECT JSON_VALUE(x, '$.a' RETURNING `VARCHAR`)
druid ERR Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m BIGINT)
druid ERR Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m VARCHAR)
 ERR Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m BIGINT)
 ERR Expecting ). Line 1, Col: 36.
  SELECT JSON_VALUE(x, '$.a' [4mRETURNING[0m VARCHAR)
[assistant] Trino round-trips `BIGINT` and `VARCHAR` unchanged, while MySQL and Exasol quote them, so the type-parsing path matters. I'll add the Druid `JSON_VALUE` entry the same way Trino and Exasol do, then probe the result.
[tool_use Bash] {"command": "sed -n 15,30p sqlglot/parsers/trino.py; sed -n 115,130p sqlglot/parsers/exasol.py", "description": "Read Trino and Exasol FUNCTION_PARSERS blocks"}
[tool_result]     FUNCTIONS = {
        **PrestoParser.FUNCTIONS,
        "VERSION": exp.CurrentVersion.from_arg_list,
    }

    FUNCTION_PARSERS = {
        **PrestoParser.FUNCTION_PARSERS,
        "TRIM": lambda self: self._parse_trim(),
        "JSON_QUERY": lambda self: self._parse_json_query(),
        "JSON_VALUE": lambda self: self._parse_json_value(),
        "LISTAGG": lambda self: self._parse_string_agg(),
    }

    JSON_QUERY_OPTIONS: parser.OPTIONS_TYPE = {
        **dict.fromkeys(
            (
…[416 chars elided]…
        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
        "JSON_VALUE": lambda self: self._parse_json_value(),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_extract.htm
        "JSON_EXTRACT": lambda self: self._parse_json_extract(),
    }

    def _parse_statement(self) -> exp.Expr | None:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py", "old_string": "class DruidParser(Parser):\n    pass", "new_string": "class DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in [\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", \\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING VARCHAR) FROM t\\\", \\\"SELECT JSON_VALUE(x, '\\$
…[11 chars elided]…
\\\", \\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING DOUBLE) FROM t\\\"]:\n    t = sqlglot.parse_one(s, dialect='druid')\n    jv = t.find(exp.JSONValue)\n    print(type(jv.args.get('returning')).__name__, '|', t.sql(dialect='druid'))\n    print('  to mysql:', t.sql(dialect='mysql'))\n    print('  to trino:', t.sql(dialect='trino'))\n\"", "description": "Probe Druid JSON_VALUE RETURNING after the fix"}
[tool_result] Column | SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
  to mysql: SELECT JSON_VALUE(x, '$.a' RETURNING `BIGINT`) FROM t
  to trino: SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
Column | SELECT JSON_VALUE(x, '$.a' RETURNING VARCHAR) FROM t
  to mysql: SELECT JSON_VALUE(x, '$.a' RETURNING `VARCHAR`) FROM t
  to trino: SELECT JSON_VALUE(x, '$.a' RETURNING VARCHAR) FROM t
bool | SELECT JSON_VALUE(x, '$.a') FROM t
  to mysql: SELECT JSON_VALUE(x, '$.a') FROM t
  to trino: SELECT JSON_VALUE(x, '$.a') FROM t
Column | SELECT JSON_VALUE(x, '$.a' RETURNING DOUBLE) FROM t
  to mysql: SELECT JSON_VALUE(x, '$.a' RETURNING `DOUBLE`) FROM t
  to trino: SELECT JSON_VALUE(x, '$.a' RETURNING DOUBLE) FROM t
[assistant] The Druid round-trip now matches, but `returning` comes back as a `Column` rather than a `DataType` for `BIGINT`/`VARCHAR`/`DOUBLE`. Trino gets the same string, so the node shape is what differs. I'll find out why `_parse_type` returns a column here.
[tool_use Bash] {"command": "grep -n \"def _parse_type\\b\\|def _parse_type(\" sqlglot/parser.py; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['druid','trino','mysql']:\n  for s in ['BIGINT','VARCHAR','DOUBLE','DECIMAL(4, 2)']:\n    e = sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING %s)\\\" % s, dialect=d)\n    print(d, s, type(e.find(exp.JSONValue).args.get('returning')).__name__)\n  print(d, 'CAST', type(sqlglot.parse_one('CAST(x AS BIGINT)', dialect=d).args['to']).__name__)\n\"", "description": "Check when RETURNING types become DataType vs Column"}
[tool_result] 6134:    def _parse_type(
druid BIGINT Column
druid VARCHAR Column
druid DOUBLE Column
druid DECIMAL(4, 2) Anonymous
druid CAST DataType
trino BIGINT Column
trino VARCHAR Column
trino DOUBLE Column
trino DECIMAL(4, 2) Anonymous
trino CAST DataType
mysql BIGINT Column
mysql VARCHAR Column
mysql DOUBLE Column
mysql DECIMAL(4, 2) Anonymous
mysql CAST DataType
[assistant] Even MySQL and Trino store `RETURNING BIGINT` as a `Column`, and `DECIMAL(4, 2)` as `Anonymous`. That is a shared bug in `_parse_json_value`, not a Druid quirk. I'll check `_parse_type`'s signature to see whether a narrow fix exists.
[tool_use Bash] {"command": "sed -n 6134,6150p sqlglot/parser.py; grep -n \"def _parse_types\\b\\|def _parse_types(\" sqlglot/parser.py; grep -n \"_parse_json_value\\|_parse_type()\" sqlglot/parser.py | head -5; PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['druid','trino']:\n  for s in ['BIGINT','VARCHAR','DECIMAL(4, 2)']:\n    e = sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING %s)\\\" % s, dialect=d)\n    r = e.find(exp.JSONValue).args.get('returning')\n    print(d, s, repr(r)[:200].replace(chr(10),' '))\n\"", "description": "Read _parse_type header and returning node reprs"}
[tool_result]     def _parse_type(
        self, parse_interval: bool = True, fallback_to_identifier: bool = False
    ) -> exp.Expr | None:
        if not fallback_to_identifier and (atom := self._parse_atom()) is not None:
            return atom

        if interval := parse_interval and self._parse_interval():
            return self._parse_column_ops(interval)

        index = self._index
        data_type = self._parse_types(check_func=True, allow_identifiers=False)

        # parse_types() returns a Ca
…[701 chars elided]…
 quoted=False))
druid VARCHAR Column(   this=Identifier(this=VARCHAR, quoted=False))
druid DECIMAL(4, 2) Anonymous(   this=DECIMAL,   expressions=[     Literal(this=4, is_string=False),     Literal(this=2, is_string=False)])
trino BIGINT Column(   this=Identifier(this=BIGINT, quoted=False))
trino VARCHAR Column(   this=Identifier(this=VARCHAR, quoted=False))
trino DECIMAL(4, 2) Anonymous(   this=DECIMAL,   expressions=[     Literal(this=4, is_string=False),     Literal(this=2, is_string=False)])
[assistant] The cause is that `_parse_type` tries `_parse_atom` first, so bare type names become identifiers and `DECIMAL(4, 2)` becomes an `Anonymous` call. I'll test whether `_parse_types()` gives proper `DataType` nodes and keeps the round-trip, before deciding whether to change the shared helper.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp, parser\nfrom sqlglot.parser import Parser\norig = Parser._parse_json_value\ndef patched(self):\n    this = self._parse_bitwise()\n    self._match(sqlglot.tokens.Token
…[396 chars elided]…
OUBLE','DECIMAL(4, 2)','ARRAY<INT>']:\n    try:\n      e = sqlglot.parse_one(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING %s) FROM t\\\" % s, dialect=d)\n      r = e.find(exp.JSONValue).args.get('returning')\n      print(d, s, type(r).__name__, '|', e.sql(dialect=d))\n    except Exception as ex: print(d, s, 'ERR', str(ex)[:80])\n\"", "description": "Probe patched _parse_types variant for RETURNING"}
[tool_result] druid BIGINT DataType | SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
druid VARCHAR DataType | SELECT JSON_VALUE(x, '$.a' RETURNING VARCHAR) FROM t
druid DOUBLE DataType | SELECT JSON_VALUE(x, '$.a' RETURNING DOUBLE) FROM t
druid DECIMAL(4, 2) DataType | SELECT JSON_VALUE(x, '$.a' RETURNING DECIMAL(4, 2)) FROM t
druid ARRAY<INT> DataType | SELECT JSON_VALUE(x, '$.a' RETURNING ARRAY<INT>) FROM t
trino BIGINT DataType | SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
trino VARCHAR DataTy
…[212 chars elided]…
 2)) FROM t
trino ARRAY<INT> DataType | SELECT JSON_VALUE(x, '$.a' RETURNING ARRAY(INTEGER)) FROM t
mysql BIGINT DataType | SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
mysql VARCHAR DataType | SELECT JSON_VALUE(x, '$.a' RETURNING TEXT) FROM t
mysql DOUBLE DataType | SELECT JSON_VALUE(x, '$.a' RETURNING DOUBLE) FROM t
mysql DECIMAL(4, 2) DataType | SELECT JSON_VALUE(x, '$.a' RETURNING DECIMAL(4, 2)) FROM t
mysql ARRAY<INT> DataType | SELECT JSON_VALUE(x, '$.a' RETURNING ARRAY<INT>) FROM t
[assistant] `_parse_types()` gives real `DataType` nodes for every case, which is what `CAST` already produces. The harness says to read the `sqlglot-data-types` skill before changing how a data type is parsed, and I missed that before my Druid edit, so I'll read it now.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-data-types/SKILL.md", "description": "Read sqlglot-data-types skill"}
[tool_result] ---
name: sqlglot-data-types
description: Load when a task changes how sqlglot parses or generates a data type (exp.DataType) — CAST / TRY_CAST / `::` target types, nested types (ARRAY<…>, STRUCT<…>, MAP, Nullable(…)), type modifiers or trailing clauses such as COLLATE, CHARACTER SET, WITH TIME ZONE — or when a fix adds a new arg to any existing expression class (DataType, Cast, Column, …) that must survive generation in every dialect.
---

# Data types and new node args in sqlglot

## Who owns 
…[3136 chars elided]…
hive/spark and any dialect with an override.
3. Tests: `validate_identity` in the source dialect file next to existing tests of the same
   clause, plus a `validate_all(..., read={<source>: ...})` in the test file of a dialect whose
   generator overrides the method (e.g. `tests/dialects/test_spark.py`), with the expected
   string written from that engine's syntax, not copied from the script output.
4. Then the normal done-check: dialect test files, then `run_suite.py` (see `tool_guidance.md`).
[assistant] The skill's guidance fits this change: it touches the `RETURNING` type parse only, not the shared `_parse_types`. I'll make the one-line change in `_parse_json_value` so the type is a real `DataType`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/sqlglot/parser.py", "old_string": "        returning = self._match(TokenType.RETURNING) and self._parse_type()\n\n        return self.expression(\n            exp.JSONValue(", "new_string": "        returning = self._match(TokenType.RETURNING) and self._parse_types()\n\n        return self.expression(\n            exp.JSONValue("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Next, the tests. I'll look at the Druid test file's structure and the existing MySQL `JSON_VALUE` test to match them.
[tool_use Bash] {"command": "sed -n 1,30p tests/dialects/test_druid.py; echo ...; tail -15 tests/dialects/test_druid.py; echo ----; sed -n 1555,1572p tests/dialects/test_mysql.py", "description": "Read Druid test file structure and MySQL JSON_VALUE test"}
[tool_result] from sqlglot.dialects.dialect import Dialects
from tests.dialects.test_dialect import Validator


class TestDruid(Validator):
    dialect = "druid"

    def test_druid(self):
        self.validate_identity("SELECT MOD(1000, 60)")
        self.validate_identity("SELECT CEIL(__time TO WEEK) FROM t")
        self.validate_identity("SELECT CEIL(col) FROM t")
        self.validate_identity("SELECT CEIL(price, 2) AS rounded_price FROM t")
        self.validate_identity("SELECT FLOOR(__time TO WEEK) FR
…[1539 chars elided]…
 JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
        )

        for on_option in ("NULL", "ERROR", "DEFAULT 1"):
            self.validate_identity(
                f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2) {on_option} ON EMPTY {on_option} ON ERROR) AS price"""
            )

    def test_grant(self):
        grant_cmds = [
            "GRANT 'role1', 'role2' TO 'user1'@'localhost', 'user2'@'localhost'",
            "GRANT SELECT ON world.* TO 'role3'",
[assistant] The Druid test file uses `validate_identity`, so I'll mirror the MySQL test. Before writing expectations, I want Druid's documented `JSON_VALUE` grammar, since the harness asks for the target's documented forms and the shared helper also accepts `ON EMPTY`/`ON ERROR`.
[tool_use WebSearch] {"query": "Apache Druid JSON_VALUE function RETURNING sqlType syntax documentation", "mode": "standard"}
[tool_result] Web search results for query: "Apache Druid JSON_VALUE function RETURNING sqlType syntax documentation"

Links: [{"title":"SQL JSON functions","url":"https://druid.apache.org/docs/latest/querying/sql-json-functions"},{"title":"sql json functions","url":"https://apache.googlesource.com/druid/+show/HEAD/docs/querying/sql-json-functions.md"},{"title":"SQL JSON functions","url":"https://druid.staged.apache.org/docs/latest/querying/sql-json-functions"},{"title":"JSON VALUE","url":"https://docs.oracle
…[1124 chars elided]…
nly when RETURNING specifies an ARRAY type, such as RETURNING VARCHAR ARRAY.

The results include a staged copy of the docs that describes the same function in slightly different terms, calling the output a "literal" value rather than a "primitive" one. The latest docs are the authoritative version. The Oracle and Firebolt JSON_VALUE results are for different databases and don't apply to Druid.


REMINDER: You MUST include the sources above in your response to the user using markdown hyperlinks.
[assistant] Druid documents `JSON_VALUE(expr, path [RETURNING sqlType])`, with primitive arrays as `RETURNING VARCHAR ARRAY`. I'll probe that array form, plus the documented types, before writing tests.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['BIGINT','VARCHAR','DOUBLE','VARCHAR ARRAY','BIGINT ARRAY','DECIMAL(4, 2)']:\n    q = \\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING %s) FROM t\\\" % s\n    try
…[139 chars elided]…
__, '|', e.sql(dialect='druid'), '| same:', e.sql(dialect='druid')==q)\n    except Exception as ex: print('ERR', s, str(ex)[:120])\n\"; PYTHONPATH=. $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py tests/dialects/test_druid.py 2>&1 | tail -15", "description": "Probe Druid array/type forms and run dialect tests"}
[tool_result] DataType | SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t | same: True
DataType | SELECT JSON_VALUE(x, '$.a' RETURNING VARCHAR) FROM t | same: True
DataType | SELECT JSON_VALUE(x, '$.a' RETURNING DOUBLE) FROM t | same: True
DataType | SELECT JSON_VALUE(x, '$.a' RETURNING ARRAY<VARCHAR>) FROM t | same: False
DataType | SELECT JSON_VALUE(x, '$.a' RETURNING ARRAY<BIGINT>) FROM t | same: False
DataType | SELECT JSON_VALUE(x, '$.a' RETURNING DECIMAL(4, 2)) FROM t | same: True
............................................................................... [100%]
79 passed, 1102 subtests passed in 0.37s
[assistant] The documented `VARCHAR ARRAY` form parses but comes back as `ARRAY<VARCHAR>`, so it does not round-trip. I'll check what the Druid generator already does with types before deciding how to handle it.
[tool_use Bash] {"command": "cat sqlglot/generators/druid.py; grep -rn \"ARRAY\" tests/dialects/test_druid.py | head -5; git log --oneline -3 -- sqlglot/generators/druid.py sqlglot/parsers/druid.py", "description": "Read Druid generator and related history"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator
from sqlglot.dialects.dialect import rename_func


class DruidGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    # https://druid.apache.org/docs/latest/querying/sql-data-types/
    TYPE_MAPPING = {
        **generator.Generator.TYPE
…[197 chars elided]…
Generator.TRANSFORMS,
        exp.CurrentTimestamp: lambda *_: "CURRENT_TIMESTAMP",
        exp.Mod: rename_func("MOD"),
        exp.Array: lambda self, e: f"ARRAY[{self.expressions(e)}]",
    }
tests/dialects/test_druid.py:17:        self.validate_identity("SELECT ARRAY[1, 2, 3]")
08b51e81e Refactor: use ruff UP rule to modernize coding style (#7459)
3582aa542 refactor(generators): Cleanup and fully compile all generators (#7389)
cb78bc3d5 refactor(druid)!: Extract and compile generator (#7365)
[assistant] The Druid generator has no array-type rendering at all, and `VARCHAR ARRAY` is a type-spelling change that would also affect `CAST` and column types. That goes beyond the `RETURNING` construct in the report, so I'll leave it out of this change and flag it at the end. Now I'll add the Druid test, asserting the node class as the harness requires.
[tool_use Bash] {"command": "grep -n \"def validate_identity\" -A12 tests/dialects/test_dialect.py | head -30; grep -n \"def validate_all\" -A3 tests/dialects/test_dialect.py | head -5", "description": "Check validate_identity return value in test helper"}
[tool_result] 53:    def validate_identity(
54-        self, sql, write_sql=None, pretty=False, check_command_warning=False, identify=False
55-    ):
56-        if check_command_warning:
57-            with self.assertLogs(parser_logger) as cm:
58-                expression = self.parse_one(sql)
59-                assert f"'{sql[:100]}' contains unsupported syntax" in cm.output[0]
60-        else:
61-            expression = self.parse_one(sql)
62-
63-        self.assertEqual(
64-            write_sql or sql, expression.sql(dialect=self.dialect, pretty=pretty, identify=identify)
65-        )
68:    def validate_all(self, sql, read=None, write=None, pretty=False, identify=False):
69-        """
70-        Validate that:
71-        1. Everything in `read` transpiles to `sql`
[assistant] `validate_identity` returns nothing, so the test will call `self.parse_one` directly to check the node class. I'll add the test next to the existing Druid tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "from sqlglot.dialects.dialect import Dialects\nfrom tests.dialects.test_dialect import Validator\n\n\nclass TestDruid(Validator):\n    dialect = \"druid\"\n", "new_string": "from sqlglot import exp\nfrom sqlg
…[375 chars elided]…
ALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING DOUBLE)\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING DECIMAL(4, 2))\")\n\n        returning = self.parse_one(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT)\").find(exp.JSONValue)\n        self.assertIsInstance(returning.args[\"returning\"], exp.DataType)\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] The variable there holds the `JSONValue` node, not the type, so I'll rename it before running anything.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        returning = self.parse_one(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT)\").find(exp.JSONValue)\n        self.assertIsInstance(returning.args[\"returning\"], exp.DataType)", "new_string": "        json_value = self.parse_one(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT)\").find(exp.JSONValue)\n        self.assertIsInstance(json_value.args[\"returning\"], exp.DataType)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112959-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Next I'll run the affected dialect test files, then the lint/format checks.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py tests/dialects/test_oracle.py 2>&1 | tail -15; $PY -m ruff format --check sqlglot/parser.py sqlglot/parsers/druid.py tests/dialects/test_druid.py 2>&1 | tail -3; $PY -m ruff check sqlglot/parser.py sqlglot/parsers/druid.py tests/dialects/test_druid.py 2>&1 | tail -3", "description": "Run dialect tests and ruff checks"}
[tool_result] ...... [  5%]
.................................................... [ 55%]
...................................... [ 91%]
.........                   [100%]
105 passed, 1317 subtests passed in 0.33s
Would reformat: tests/dialects/test_druid.py
1 file would be reformatted, 2 files already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format tests/dialects/test_druid.py && git diff --stat && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py 2>&1 | tail -2", "description": "Apply ruff formatting and rerun Druid tests"}
[tool_result] 1 file reformatted
 sqlglot/parser.py            |  2 +-
 sqlglot/parsers/druid.py     |  5 ++++-
 tests/dialects/test_druid.py | 13 +++++++++++++
 3 files changed, 18 insertions(+), 2 deletions(-)
..                                       [100%]
2 passed, 32 subtests passed in 0.08s
[This command modified 1 file you've previously read: tests/dialects/test_druid.py. Call Read before editing.]
[assistant] The reported change is just my own `ruff format` pass on the test file, so the content is as intended. Now the full suite, run in the foreground via the harness script as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -25", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-16:00:45 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-c711ee67e4.log
ELAPSED: 52s
SUMMARY: 1122 passed, 18178 subtests passed in 51.82s
EXIT: 0
[assistant] The full suite passes (`SUMMARY: 1122 passed`, `EXIT: 0`). One last check: run the reported query through the AST script and see what Druid's `RETURNING BIGINT` transpiles to in the dialects that already support it, so I can report those outputs accurately.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/skills/sqlglot-dialect-functions/scripts/ast_check.py --read druid --write mysql,trino,exasol,duckdb \"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\"; echo \"exit=$?\"; PYTHONPATH=. $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read='druid', write='mysql')[0])\nprint(sqlglot.transpile(\\\"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\\\", read='druid', write='trino')[0])\n\"; git status --short", "description": "Run AST check and inspect cross-dialect output"}
[tool_result] == SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
  node: JSONValue
  druid (round-trip): SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
  mysql: SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
  trino: SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
  exasol: SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
  duckdb: SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
exit=0
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
 M sqlglot/parser.py
 M sqlglot/parsers/druid.py
 M tests/dialects/test_druid.py
[assistant] Druid now parses `JSON_VALUE(... RETURNING <type>)`, and the reported query round-trips unchanged. The full suite passes: `SUMMARY: 1122 passed, 18178 subtests passed in 51.82s`, `EXIT: 0`. The changes are uncommitted in the worktree.

**What was wrong:** Druid had no `JSON_VALUE` entry in its parser, so the call fell through to the generic function parser, which doesn't accept `RETURNING`. MySQL, Trino and Exasol each map `JSON_VALUE` to the shared `_parse_json_value`.

**What I changed:**
- `sqlglot/parsers/druid.py`: added `"JSON_VALUE": lambda self: self._parse_json_value()` to `DruidParse
…[1324 chars elided]…
is passed through as-is, and MySQL's `JSON_VALUE` does not accept `BIGINT` in `RETURNING`. DuckDB has no `RETURNING` clause on `json_value`. Both problems predate this change.
- **`ON EMPTY` / `ON ERROR`** are accepted by the shared helper, but I did not check them against Druid's docs and did not add tests for them.

**Process note:** I edited `sqlglot/parsers/druid.py` before reading the `sqlglot-data-types` skill, which the harness asks for before the first source edit. I read it before changing `parser.py`, and its guidance (only the `RETURNING` call site changed, not `_parse_types`) held.
