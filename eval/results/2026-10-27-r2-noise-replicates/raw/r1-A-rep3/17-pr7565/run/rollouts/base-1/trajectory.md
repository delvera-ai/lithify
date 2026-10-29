# trajectory base-1

final message:
Oracle now parses and round-trips `LISTAGG(... ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT])` and `ON OVERFLOW ERROR`. The full suite passes (1094 tests), and ruff check and format are clean. I haven't committed anything.

The change has three parts:

- **Parser** (`sqlglot/parsers/oracle.py`): `LISTAGG` now goes through the existing `_parse_string_agg`, the same path Snowflake uses. Before this, Oracle raised a `ParseError` on the `ON OVERFLOW` clause.
- **Generator** (`sqlglot/generators/oracle.py`): `GroupConcat` is written as `LISTAGG(...) WITHIN GROUP (ORDER BY ...)`, using the shared `groupconcat_sql` helper as Exasol does. Before this, Oracle emitted `GROUP_CONCAT(...)`, which is not valid Oracle.
- **Tests** (`tests/dialects/test_oracle.py`): a new `test_listagg` covers `ERROR`, `TRUNCATE '...'` with and without `WITH|WITHOUT COUNT`, and the no-separator and `DESC` forms.

Decisions to check:

- I passed `sep=None` to the helper. Its default is `","`, which would have turned Oracle's `LISTAGG(x)` (no separator) into `LISTAGG(x, ',')`.
- A bare `ON OVERFLOW TRUNCATE '...'` is written back with an explicit `WITH COUNT`, because that is Oracle's default. The test pins this.

Side effects: other dialects transpiled to Oracle now produce `LISTAGG` instead of `GROUP_CONCAT`. No existing test depended on the old output.

Not changed: writing an `ON OVERFLOW` clause to Snowflake still drops it. That is Snowflake's existing generator behavior, and I left it alone since it was outside this request.

## events
[tool_use Bash] {"command": "grep -rn -i \"overflow\" sqlglot/ | head -50; echo ---; grep -rn -i \"listagg\" sqlglot/ tests/ | head -60", "description": "Search for overflow and listagg references"}
[tool_result] sqlglot/generator.py:5489:    def overflowtruncatebehavior_sql(self, expression: exp.OverflowTruncateBehavior) -> str:
sqlglot/parser.py:7705:        if self._match_text_seq("ON", "OVERFLOW"):
sqlglot/parser.py:7706:            # trino: LISTAGG(expression [, separator] [ON OVERFLOW overflow_behavior])
sqlglot/parser.py:7708:                on_overflow: exp.Expr | None = exp.var("ERROR")
sqlglot/parser.py:7711:                on_overflow = self.expression(
sqlglot/parser.py:7712:                 
…[9890 chars elided]…
"SELECT LISTAGG(DISTINCT col, ',') WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:59:            "SELECT LISTAGG(col, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:62:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITH COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
tests/dialects/test_trino.py:65:            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/parser.py", "offset": 7690, "limit": 70}
[tool_result] 7690	            safe=safe,
7691	            action=self._parse_var_from_options(self.CAST_ACTIONS, raise_unmatched=False),
7692	            default=default,
7693	        )
7694	
7695	    def _parse_string_agg(self) -> exp.GroupConcat:
7696	        if self._match(TokenType.DISTINCT):
7697	            args: list[exp.Expr | None] = [
7698	                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
7699	            ]
7700	            if self._match(TokenType.COMMA):
7701	
…[2613 chars elided]…
arse_convert(self, strict: bool, safe: bool | None = None) -> exp.Expr | None:
7750	        this = self._parse_bitwise()
7751	
7752	        if self._match(TokenType.USING):
7753	            to: exp.Expr | None = exp.DType.CHARACTER_SET.into_expr(kind=self._parse_charset_name())
7754	        elif self._match(TokenType.COMMA):
7755	            to = self._parse_types()
7756	        else:
7757	            to = None
7758	
7759	        return self.build_cast(strict=strict, this=this, to=to, safe=safe)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generator.py", "offset": 5485, "limit": 20}
[tool_result] 5485	            )
5486	
5487	        return self.function_fallback_sql(expression)
5488	
5489	    def overflowtruncatebehavior_sql(self, expression: exp.OverflowTruncateBehavior) -> str:
5490	        filler = self.sql(expression, "this")
5491	        filler = f" {filler}" if filler else ""
5492	        with_count = "WITH COUNT" if expression.args.get("with_count") else "WITHOUT COUNT"
5493	        return f"TRUNCATE{filler} {with_count}"
5494	
5495	    def unixseconds_sql(self, expression: exp.UnixSeconds) -> str:
5496	        if self.SUPPORTS_UNIX_SECONDS:
5497	            return self.function_fallback_sql(expression)
5498	
5499	        start_ts = exp.cast(exp.Literal.string("1970-01-01 00:00:00+00"), to=exp.DType.TIMESTAMPTZ)
5500	
5501	        return self.sql(
5502	            exp.TimestampDiff(this=expression.this, expression=start_ts, unit=exp.var("SECONDS"))
5503	        )
5504	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_trino.py", "offset": 50, "limit": 25}
[tool_result] 50	        )
51	
52	        self.validate_identity("SELECT VERSION()")
53	
54	    def test_listagg(self):
55	        self.validate_identity(
56	            "SELECT LISTAGG(DISTINCT col, ',') WITHIN GROUP (ORDER BY col ASC) FROM tbl"
57	        )
58	        self.validate_identity(
59	            "SELECT LISTAGG(col, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
60	        )
61	        self.validate_identity(
62	            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE WITH CO
…[184 chars elided]…
 (ORDER BY col ASC) FROM tbl"
66	        )
67	        self.validate_identity(
68	            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
69	        )
70	        self.validate_identity(
71	            "SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY col ASC) FROM tbl"
72	        )
73	        self.validate_identity(
74	            "SELECT LISTAGG(col) WITHIN GROUP (ORDER BY col DESC) FROM tbl",
[tool_use Bash] {"command": "grep -n \"class Oracle\\|LISTAGG\\|_parse_string_agg\\|Parser(\" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py | head; grep -n \"OverflowTruncate\" -A12 sqlglot/expressions/query.py | head -30; grep -n \"def _parse_string_agg\" -A5 sqlglot/parser.py | head", "description": "Inspect Oracle parser/generator and expression classes"}
[tool_result] sqlglot/generators/oracle.py:23:class OracleGenerator(generator.Generator):
sqlglot/parsers/oracle.py:22:class OracleParser(parser.Parser):
1883:class OverflowTruncateBehavior(Expression):
1884-    arg_types = {"this": False, "with_count": True}
1885-
1886-
1887-class JSON(Expression):
1888-    arg_types = {"this": False, "with_": False, "unique": False}
1889-
1890-
1891-class JSONPath(Expression):
1892-    arg_types = {"expressions": True, "escape": False}
1893-
1894-    @property
1895-    def output_name(self) -> str:
7695:    def _parse_string_agg(self) -> exp.GroupConcat:
7696-        if self._match(TokenType.DISTINCT):
7697-            args: list[exp.Expr | None] = [
7698-                self.expression(exp.Distinct(expressions=[self._parse_disjunction()]))
7699-            ]
7700-            if self._match(TokenType.COMMA):
[assistant] Now let me see how Oracle currently handles LISTAGG and what it does with the clause today.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n          \\\"SELECT LISTAGG(col, '; ' ON OVERFLOW ERROR) WITHIN GROUP (ORDER BY col) FROM t\\\",\n          \\\"SELECT LISTAGG(col, '; ' ON OVERFLOW TRUNCATE '..
…[133 chars elided]…
'->', sqlglot.transpile(s, read='oracle', write=d)[0])\n        except Exception as e: print(d, 'ERR', type(e).__name__, str(e)[:200])\n\"; grep -n \"LISTAGG\\|GROUP_CONCAT\\|_parse_string_agg\\|FUNCTIONS = \" sqlglot/parsers/oracle.py sqlglot/generators/oracle.py; sed -n 1,80p sqlglot/parsers/oracle.py | grep -n \"FUNCTIONS\\|import\" ", "description": "Reproduce current Oracle LISTAGG behavior"}
[tool_result] oracle ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
snowflake ERR ParseError Expecting ). Line 1, Col: 33.
  SELECT LISTAGG(last_name, '; ' [4mON[0m OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t
oracle ERR ParseError Expecting ). Line 1, Col: 27.
  SELECT LISTAGG(col, '; ' [4mON[0m OVERFLOW ERROR) WITHIN GROUP (ORDER BY col) FROM t
snowflake ERR ParseError Expecti
…[592 chars elided]…
typing as t
5:from sqlglot import exp, parser
6:from sqlglot.dialects.dialect import build_formatted_time, build_timetostr_or_tochar, build_trunc
7:from sqlglot.helper import seq_get
8:from sqlglot.parser import OPTIONS_TYPE, build_coalesce
9:from sqlglot.tokens import TokenType
12:    from sqlglot._typing import E
26:    FUNCTIONS = {
27:        **{k: v for k, v in parser.Parser.FUNCTIONS.items() if k != "TO_BOOLEAN"},
48:    NO_PAREN_FUNCTIONS = {
49:        **parser.Parser.NO_PAREN_FUNCTIONS,
[assistant] Oracle reads LISTAGG through the generic function parser, not `_parse_string_agg`, which is why the clause fails. Let me check how Snowflake parses it and how Oracle generates `GroupConcat` today.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns=\\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\\\"\nprint(repr(sqlglot.parse_one(s, read='snowflake').selects[0]))\nprint(sqlglot.transpile(s, read='snowflake', write='oracle')[0])\nprint(sqlglot.transpile(s, 
…[194 chars elided]…
glot.parse_one(\\\"SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t\\\", read='oracle').selects[0]))\n\"; grep -n \"GroupConcat\\|WithinGroup\\|groupconcat\" sqlglot/generators/oracle.py sqlglot/generators/generator.py | head; grep -n \"def groupconcat_sql\" -A25 sqlglot/generators/generator.py | head -40", "description": "Check Snowflake parse and Oracle generation paths"}
[tool_result] GroupConcat(
  this=Order(
    this=Column(
      this=Identifier(this=last_name, quoted=False)),
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=last_name, quoted=False)),
        nulls_first=False)]),
  separator=Literal(this='; ', is_string=True),
  on_overflow=OverflowTruncateBehavior(
    this=Literal(this='...', is_string=True),
    with_count=False))
SELECT GROUP_CONCAT(last_name ORDER BY last_name, '; ', TRUNCATE '...' WITHOUT COUNT) FROM t
SELECT LIS
…[240 chars elided]…
s=[
      Column(
        this=Identifier(this=last_name, quoted=False),
        join_mark=False),
      Literal(this='; ', is_string=True)]),
  expression=Order(
    expressions=[
      Ordered(
        this=Column(
          this=Identifier(this=last_name, quoted=False),
          join_mark=False),
        nulls_first=False)]),
  join_mark=False)
ugrep: warning: sqlglot/generators/generator.py: No such file or directory
ugrep: warning: sqlglot/generators/generator.py: No such file or directory
[assistant] Snowflake parses the clause into `GroupConcat(on_overflow=...)`, but Oracle writes it out as `GROUP_CONCAT(... ORDER BY ...)`, which is wrong. Next I'll read the shared `groupconcat_sql` helper and the Oracle parser and generator setup.
[tool_use Bash] {"command": "sed -n 2405,2455p sqlglot/dialects/dialect.py; echo ----; sed -n 20,60p sqlglot/parsers/oracle.py; echo ----; grep -n \"GroupConcat\\|TRANSFORMS\\|def .*_sql\\|groupconcat\" sqlglot/generators/oracle.py | head -60; echo ----; grep -n \"GroupConcat\" -B2 -A8 sqlglot/generators/exasol.py | head -40; grep -n \"def groupconcat_sql\\|def groupconcat\" -A3 sqlglot/generator.py", "description": "Read groupconcat helper and Oracle/Exasol generator code"}
[tool_result] def groupconcat_sql(
    self: Generator,
    expression: exp.GroupConcat,
    func_name: str = "LISTAGG",
    sep: str | None = ",",
    within_group: bool = True,
    on_overflow: bool = False,
) -> str:
    this = expression.this
    separator = self.sql(
        expression.args.get("separator") or (exp.Literal.string(sep) if sep else None)
    )

    on_overflow_sql = self.sql(expression, "on_overflow")
    on_overflow_sql = f" ON OVERFLOW {on_overflow_sql}" if (on_overflow and on_overflow_s
…[3692 chars elided]…
    self, e, func_name="LISTAGG", within_group=True
343-        ),
344-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/edit_distance.htm#EDIT_DISTANCE
345-        exp.Levenshtein: unsupported_args("ins_cost", "del_cost", "sub_cost", "max_dist")(
346-            rename_func("EDIT_DISTANCE")
347-        ),
348-        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/mod.htm
349-        exp.Mod: rename_func("MOD"),
[assistant] The plan is to add `LISTAGG` to Oracle's parser so it routes through the existing `_parse_string_agg`, and to make Oracle's generator emit `GroupConcat` as `LISTAGG ... WITHIN GROUP` using the shared `groupconcat_sql` helper, as Exasol does. Before editing, I'll check existing Oracle tests that depend on the current `GROUP_CONCAT` output.
[tool_use Bash] {"command": "grep -rn -i \"listagg\\|group_concat\\|GroupConcat\" tests/dialects/test_oracle.py | head -20; echo ----; grep -rn \"\\\"oracle\\\"\" tests/dialects/*.py | grep -i \"group_concat\\|listagg\\|string_agg\" | head; echo ----; grep -n \"GroupConcat\" sqlglot/generators/*.py | head -30", "description": "Find Oracle tests and GroupConcat generator usages"}
[tool_result] ----
----
sqlglot/generators/databricks.py:47:            exp.GroupConcat: groupconcat_sql,
sqlglot/generators/bigquery.py:313:        exp.GroupConcat: lambda self, e: groupconcat_sql(
sqlglot/generators/clickhouse.py:419:    def groupconcat_sql(self, expression: exp.GroupConcat) -> str:
sqlglot/generators/doris.py:60:        exp.GroupConcat: lambda self, e: self.func(
sqlglot/generators/duckdb.py:1596:        exp.GroupConcat: lambda self, e: groupconcat_sql(self, e, within_group=False),
sqlglot
…[748 chars elided]…
tor, expression: exp.GroupConcat) -> str:
sqlglot/generators/spark.py:115:            exp.GroupConcat: _groupconcat_sql,
sqlglot/generators/redshift.py:87:        exp.GroupConcat: rename_func("LISTAGG"),
sqlglot/generators/tsql.py:49:def _string_agg_sql(self: TSQLGenerator, expression: exp.GroupConcat) -> str:
sqlglot/generators/tsql.py:53:        # exp.Distinct can appear below an exp.Order or an exp.GroupConcat expression
sqlglot/generators/tsql.py:204:        exp.GroupConcat: _string_agg_sql,
[assistant] No existing Oracle tests depend on this. I'll check the Oracle generator's imports and TRANSFORMS block, then make the edits.
[tool_use Bash] {"command": "sed -n 1,22p sqlglot/generators/oracle.py; sed -n 65,110p sqlglot/generators/oracle.py", "description": "Read Oracle generator imports and TRANSFORMS"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)


def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
    position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)


    TRANSFO
…[1631 chars elided]…
f, e: f"ASCII(UNISTR({self.sql(e.this)}))",
        exp.UnixToTime: lambda self, e: (
            f"TO_DATE('1970-01-01', 'YYYY-MM-DD') + ({self.sql(e, 'this')} / 86400)"
        ),
        exp.UtcTimestamp: rename_func("UTC_TIMESTAMP"),
        exp.UtcTime: rename_func("UTC_TIME"),
        exp.Systimestamp: lambda self, e: "SYSTIMESTAMP",
    }

    PROPERTIES_LOCATION = {
        **generator.Generator.PROPERTIES_LOCATION,
        exp.VolatileProperty: exp.Properties.Location.UNSUPPORTED,
    }
[assistant] Making the edits now: the parser entry, then the generator transform, then the import.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py", "old_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n    }", "new_string": "        \"JSON_EXISTS\": lambda self: self._parse_json_exists(),\n        \"LISTAGG\": lambda self: self._parse_string_agg(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/parsers/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "from sqlglot.dialects.dialect import (\n    no_ilike_sql,", "new_string": "from sqlglot.dialects.dialect import (\n    groupconcat_sql,\n    no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.ILike: no_ilike_sql,", "new_string": "        exp.EuclideanDistance: rename_func(\"L2_DISTANCE\"),\n        exp.GroupConcat: lambda self, e: groupconcat_sql(\n            self, e, func_name=\"LISTAGG\", within_group=True, on_overflow=True\n        ),\n        exp.ILike: no_ilike_sql,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now I'll check the behavior against the examples in the request, plus a few round-trip and cross-dialect cases.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases = [\n \\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n \\\"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\\\",\n \\\"SELECT LISTAGG(last_name, '; '
…[569 chars elided]…
, sqlglot.transpile(s, read='oracle', write='snowflake')[0])\nprint(sqlglot.transpile(cases[0], read='oracle', write='trino')[0])\nprint(sqlglot.transpile(\\\"SELECT GROUP_CONCAT(x SEPARATOR ',') FROM t\\\", read='mysql', write='oracle')[0])\nprint(sqlglot.transpile(cases[0], read='oracle', write='oracle', pretty=True)[0])\n\"", "description": "Verify Oracle LISTAGG overflow parse and round-trip"}
[tool_result] RT  SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t | DIFF
  snowflake->oracle: SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
RT  SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t | same
  snowflake->oracle: SELECT LISTAGG(last_name, '; ') WITHIN GROUP (ORDER BY last_name) FROM t
RT  SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE WITH COUN
…[567 chars elided]…
(ORDER BY last_name DESC) FROM t | DIFF
  snowflake->oracle: SELECT LISTAGG(last_name) WITHIN GROUP (ORDER BY last_name DESC) FROM t
RT  SELECT LISTAGG(last_name, ', ') FROM t | same
  snowflake->oracle: SELECT LISTAGG(last_name, ', ') FROM t
SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t
SELECT LISTAGG(x, ',') FROM t
SELECT
  LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY
    last_name)
FROM t
[assistant] Most cases work, but there's a semantic bug: the shared helper defaults `sep` to `","`, so Oracle `LISTAGG(x)` (no separator, which means empty) would be emitted as `LISTAGG(x, ',')`. Oracle's default is no separator, so I'll pass `sep=None`. The `WITH COUNT` diff is expected: the default is written out explicitly, which matches Oracle's default.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py", "old_string": "            self, e, func_name=\"LISTAGG\", within_group=True, on_overflow=True\n        ),", "new_string": "            self, e, func_name=\"LISTAGG\", sep=None, within_group=True, on_overflow=True\n        ),"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Next I'll add a test to the Oracle test file. I'll look at its structure first.
[tool_use Bash] {"command": "grep -n \"    def test_\" tests/dialects/test_oracle.py | head -40; sed -n 1,12p tests/dialects/test_oracle.py", "description": "List Oracle test methods"}
[tool_result] 9:    def test_oracle(self):
378:    def test_join_marker(self):
393:    def test_hints(self):
468:    def test_xml_table(self):
532:    def test_match_recognize(self):
557:    def test_json_table(self):
586:    def test_connect_by(self):
608:    def test_query_restrictions(self):
617:    def test_multitable_inserts(self):
693:    def test_json_functions(self):
707:    def test_grant(self):
725:    def test_revoke(self):
743:    def test_datetrunc(self):
760:    def test_trunc_type_inference(sel
…[225 chars elided]…
ocolumns(self):
927:    def test_chr(self):
931:    def test_full_procedure(self):
973:    def test_create_trigger(self):
from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
from tests.dialects.test_dialect import Validator
from sqlglot.optimizer.qualify import qualify


class TestOracle(Validator):
    dialect = "oracle"

    def test_oracle(self):
        self.validate_identity("1 /* /* */", "1 /* / * */")
        self.validate_all(
            "SELECT CONNECT_BY_ROOT x y",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py", "old_string": "    def test_chr(self):", "new_string": "    def test_listagg(self):\n        self.validate_identity(\"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y DESC) FROM t\")\n        self.validate_identity(\"SELECT LIST
…[970 chars elided]…
e) FROM t\",\n            },\n            write={\n                \"oracle\": \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\",\n                \"trino\": \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITHOUT COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\",\n            },\n        )\n\n    def test_chr(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] The test I just wrote is sloppy: one line is redundant, and the `validate_all` block reads more than it proves. I'll simplify it to a clear set of identity checks.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py", "old_string": "        self.validate_identity(\"SELECT LISTAGG(x) WITHIN GROUP (ORDER BY y DESC) FROM t\")\n        self.validate_identity(\"SELECT LISTAGG(x, ', ') FROM t\")\n        self.validate_identity(\n            \
…[1840 chars elided]…
ast_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\"\n        )\n        self.validate_identity(\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...') WITHIN GROUP (ORDER BY last_name) FROM t\",\n            \"SELECT LISTAGG(last_name, '; ' ON OVERFLOW TRUNCATE '...' WITH COUNT) WITHIN GROUP (ORDER BY last_name) FROM t\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-120637-oracle-dialect-support-listagg-e/base-1/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Now I'll run the Oracle, Trino, Snowflake and Exasol test files, then the full suite using the project's test command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py tests/dialects/test_trino.py tests/dialects/test_snowflake.py tests/dialects/test_exasol.py 2>&1 | tail -30", "description": "Run dialect tests for Oracle and related dialects"}
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full project test suite"}
[tool_result] ......................................... [ 28%]
.............................................. [ 60%]
..........................................................                      [100%]
145 passed, 2354 subtests passed in 0.70s
[tool_result] ................................................................................. [  7%]
............................................................................................................................................ [ 20%]
............................................................ [ 25%]
...................................... [ 29%]
.............................................................................................. [ 37%]
...............................................
…[284 chars elided]…
................................................................. [ 71%]
............................................. [ 75%]
............................................. [ 79%]
............................... [ 82%]
............................................................................................................................................................................................                                           [100%]
1094 passed, 17872 subtests passed in 52.22s
[assistant] The full suite passes (1094 tests). The repo's pre-commit uses ruff, so I'll lint and format-check the changed files, then review the diff.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff --version && $PY -m ruff check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py && $PY -m ruff format --check sqlglot/parsers/oracle.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py) 2>&1 | tail -8; git status --short; git diff -- sqlglot", "description": "Lint, format-check and show the source diff"}
[tool_result] ruff 0.15.6
All checks passed!
3 files already formatted
 M sqlglot/generators/oracle.py
 M sqlglot/parsers/oracle.py
 M tests/dialects/test_oracle.py
diff --git a/sqlglot/generators/oracle.py b/sqlglot/generators/oracle.py
index d3f2e99e2..514f70ebf 100644
--- a/sqlglot/generators/oracle.py
+++ b/sqlglot/generators/oracle.py
@@ -3,6 +3,7 @@ from __future__ import annotations
 
 from sqlglot import exp, generator, transforms
 from sqlglot.dialects.dialect import (
+    groupconcat_sql,
     no_i
…[562 chars elided]…
t/parsers/oracle.py b/sqlglot/parsers/oracle.py
index 169b1bcd7..0aede77c3 100644
--- a/sqlglot/parsers/oracle.py
+++ b/sqlglot/parsers/oracle.py
@@ -56,6 +56,7 @@ class OracleParser(parser.Parser):
         "JSON_ARRAY": lambda self: self._parse_oracle_json_array(),
         "JSON_ARRAYAGG": lambda self: self._parse_oracle_json_arrayagg(),
         "JSON_EXISTS": lambda self: self._parse_json_exists(),
+        "LISTAGG": lambda self: self._parse_string_agg(),
     }
 
     PROPERTY_PARSERS = {
[assistant] Oracle now parses and round-trips `LISTAGG(... ON OVERFLOW TRUNCATE '...' [WITH|WITHOUT COUNT])` and `ON OVERFLOW ERROR`. The full suite passes (1094 tests), and ruff check and format are clean. I haven't committed anything.

The change has three parts:

- **Parser** (`sqlglot/parsers/oracle.py`): `LISTAGG` now goes through the existing `_parse_string_agg`, the same path Snowflake uses. Before this, Oracle raised a `ParseError` on the `ON OVERFLOW` clause.
- **Generator** (`sqlglot/generators/oracle.py`): `GroupConcat` is written as `LISTAGG(...) WITHIN GROUP (ORDER BY ...)`, using the shared 
…[324 chars elided]…
ssed `sep=None` to the helper. Its default is `","`, which would have turned Oracle's `LISTAGG(x)` (no separator) into `LISTAGG(x, ',')`.
- A bare `ON OVERFLOW TRUNCATE '...'` is written back with an explicit `WITH COUNT`, because that is Oracle's default. The test pins this.

Side effects: other dialects transpiled to Oracle now produce `LISTAGG` instead of `GROUP_CONCAT`. No existing test depended on the old output.

Not changed: writing an `ON OVERFLOW` clause to Snowflake still drops it. That is Snowflake's existing generator behavior, and I left it alone since it was outside this request.
