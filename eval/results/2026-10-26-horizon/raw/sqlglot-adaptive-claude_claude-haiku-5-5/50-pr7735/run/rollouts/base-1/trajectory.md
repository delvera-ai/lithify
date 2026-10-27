# trajectory base-1

final message:
Snowflake `UNDROP` now parses and regenerates for all twelve object types, including the `IDENTIFIER(...)` form. The full suite passes (1120 tests) and ruff is clean. I didn't run mypy or `make style`.

Before the change, every form raised a `ParseError` because `UNDROP` was an unknown keyword. Now:

- **Token:** `UNDROP` is a keyword in the Snowflake dialect (`tokenizer_core.py`, `dialects/snowflake.py`), and it is added to `ID_VAR_TOKENS` so it still works as an identifier. `SELECT undrop FROM undrop` still parses.
- **Node:** a new `exp.Undrop(this, kind)` in `expressions/ddl.py`. I did not reuse `exp.Drop`, because it would generate `DROP`.
- **Parser:** `_parse_undrop` in `parsers/snowflake.py` matches the kind from a `UNDROP_KINDS` tuple, multi-word kinds included. It then parses the name with `_parse_table_parts`, so qualified names and `IDENTIFIER(...)` work. An unrecognized kind such as `UNDROP VIEW` falls back to `exp.Command`, as other unsupported statements do.
- **Generator:** `undrop_sql` in `generators/snowflake.py`.
- **Tests:** `test_ddl` in `tests/dialects/test_snowflake.py` round-trips each kind with a plain name and with `IDENTIFIER('"my_object"')`, plus a qualified `db.schema.t` name and `UNDROP SCHEMA db.my_schema`.

Decision for you: the new `UNDROP` keyword is Snowflake-only, so Snowflake code can no longer use `undrop` as an unquoted identifier outside a `SELECT` column list. `GET` and `PUT` already have the same restriction. If you'd rather avoid that, I can match on text in the statement parser instead, at the cost of a less conventional pattern.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "grep -rn \"UNDROP\" sqlglot tests | head -50; echo ---; ls sqlglot/parsers sqlglot/generators | grep -i snow", "description": "Search for UNDROP references and Snowflake files"}
[tool_result] ---
snowflake.py
snowflake.py
[assistant] The skill's contract is clear: node, parser, and generator have to agree, and a `validate_identity` test pins it down. My earlier grep found no `UNDROP` anywhere, so next I'll look at how `DROP` and `ALTER`-style Snowflake statements are parsed.
[tool_use Bash] {"command": "grep -n \"UNDROP\\|_parse_drop\\|def _parse_create\\|STATEMENT_PARSERS\\|TokenType.DROP\" sqlglot/parser.py sqlglot/parsers/snowflake.py sqlglot/tokens.py sqlglot/parsers/*.py | head -40; echo ---; grep -n \"class Drop\\|class Undrop\\|class Create(\" -A 25 sqlglot/expressions/*.py | head -80; echo ---; git log --oneline -1; python3 -c \"import sqlglot\" 2>&1; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Locate DROP parsing and Drop node definitions"}
[tool_result] sqlglot/parsers/snowflake.py:758:    STATEMENT_PARSERS = {
sqlglot/parsers/snowflake.py:759:        **parser.Parser.STATEMENT_PARSERS,
sqlglot/parsers/snowflake.py:1008:    def _parse_create(self) -> exp.Create | exp.Command:
sqlglot/tokens.py:286:        "DROP": TokenType.DROP,
sqlglot/parsers/bigquery.py:355:    STATEMENT_PARSERS: t.ClassVar = {
sqlglot/parsers/bigquery.py:356:        **parser.Parser.STATEMENT_PARSERS,
sqlglot/parsers/fabric.py:8:    def _parse_create(self) -> exp.Create | exp
…[6491 chars elided]…
ind": True,
sqlglot/expressions/ddl.py-393-        "actions": True,
sqlglot/expressions/ddl.py-394-        "exists": False,
sqlglot/expressions/query.py:1949:class DropPartition(Expression):
sqlglot/expressions/query.py-1950-    arg_types = {"expressions": True, "exists": False}
sqlglot/expressions/query.py-1951-
---
f8e9edaf2 lithify: probe base
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "sed -n 2290,2350p sqlglot/parser.py; echo ---; sed -n 755,790p sqlglot/parsers/snowflake.py; echo ---; grep -n \"UNDROP\\|undrop\" -i sqlglot/*.py sqlglot/*/*.py tests/dialects/test_snowflake.py | head; echo ---; grep -n \"def drop_sql\" -A 40 sqlglot/generator.py | head -60", "description": "Read DROP parser, Snowflake statements, and drop generator"}
[tool_result]         expression = self._parse_expression()
        expression = self._parse_set_operations(expression) if expression else self._parse_select()

        if isinstance(expression, exp.Subquery) and self._match(TokenType.PIPE_GT, advance=False):
            expression = self._parse_pipe_syntax_query(expression)

        return self._parse_query_modifiers(expression)

    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
        start = self._prev
        temporary = self._ma
…[5208 chars elided]…
ssion.args.get("distinct")
1813-        if (
1814-            distinct is False
1815-            and op_type in (exp.Except, exp.Intersect)
1816-            and not self.EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE
1817-        ):
1818-            self.unsupported(f"{op_name} ALL is not supported")
1819-
1820-        default_distinct = self.dialect.SET_OP_DISTINCT_BY_DEFAULT[op_type]
1821-
1822-        if distinct is None:
1823-            distinct = default_distinct
1824-            if distinct is None:
[assistant] Nothing in the repo knows about `UNDROP` yet, and `DROP` is parsed by the base `_parse_drop`. Next I'll check how Snowflake's tokenizer and statement dispatch handle keyword-led statements like `GET`/`PUT`, and how `IDENTIFIER(...)` is parsed in table names.
[tool_use Bash] {"command": "sed -n 2265,2290p sqlglot/parser.py; echo ---; grep -n \"GET\\b\\|\\\"PUT\\\"\\|TokenType.PUT\\|TokenType.GET\" sqlglot/tokens.py sqlglot/tokenizer_core.py sqlglot/dialects/snowflake.py sqlglot/parsers/snowflake.py | head; echo ---; grep -n \"CREATABLES = \\|CREATABLES: \" -A 30 sqlglot/parser.py | head -45; echo ---; grep -n \"IDENTIFIER\" sqlglot/parser.py | head -20; echo ---; grep -n \"def _parse_as_command\" -A 12 sqlglot/parser.py", "description": "Inspect statement dispatch, creatables, and IDENTIFIER handling"}
[tool_result]                 )
            )
        )

    def _parse_whileblock(self) -> exp.WhileBlock:
        return self.expression(
            exp.WhileBlock(this=self._parse_condition(), body=self._parse_block())
        )

    def _parse_statement(self) -> exp.Expr | None:
        if not self._curr:
            return None

        if self._match_set(self.STATEMENT_PARSERS):
            comments = self._prev_comments
            stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
           
…[3409 chars elided]…
_as_command(self, start: Token) -> exp.Command:
9279-        while self._curr:
9280-            self._advance()
9281-        text = self._find_sql(start, self._prev)
9282-        size = len(start.text)
9283-        self._warn_unsupported()
9284-        return exp.Command(this=text[:size], expression=text[size:])
9285-
9286-    def _parse_dict_property(self, this: str) -> exp.DictProperty:
9287-        settings = []
9288-
9289-        self._match_l_paren()
9290-        kind = self._parse_id_var()
[assistant] Before designing anything, I'll confirm what the current parser does with each form in the task.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['UNDROP TABLE t','UNDROP SCHEMA s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT s','UNDROP TAG t','UNDROP TYPE t','UNDROP DYNAMIC TABLE t','UN
…[47 chars elided]…
','UNDROP TABLE IDENTIFIER(\\'\\\"abc\\\"\\')','UNDROP TABLE db.s.t']:\n    try:\n        e=sqlglot.parse_one(s,read='snowflake'); print(repr(s),'->',type(e).__name__, e.sql('snowflake'))\n    except Exception as ex: print(repr(s),'ERR',type(ex).__name__, str(ex)[:100])\n\"; grep -n \"IDENTIFIER(\" sqlglot/parsers/snowflake.py | head", "description": "Probe current parse behavior of UNDROP forms"}
[tool_result] 'UNDROP TABLE t' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 14.
  UNDROP TABLE [4mt[0m
'UNDROP SCHEMA s' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP SCHEMA [4ms[0m
'UNDROP DATABASE d' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 17.
  UNDROP DATABASE [4md[0m
'UNDROP ACCOUNT a' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 16.
  UNDROP ACCOUNT [4ma[0m
'UNDROP NOTEBOOK n' ERR ParseError I
…[707 chars elided]…
eError Invalid expression / Unexpected token. Line 1, Col: 22.
  UNDROP EXTERNAL [4mVOLUME[0m v
'UNDROP ICEBERG TABLE t' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 20.
  UNDROP ICEBERG [4mTABLE[0m t
'UNDROP TABLE IDENTIFIER(\'"abc"\')' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 23.
  UNDROP TABLE [4mIDENTIFIER[0m('"abc"')
'UNDROP TABLE db.s.t' ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 15.
  UNDROP TABLE [4mdb[0m.s.t
[assistant] Every form fails at the keyword, so the fix is a dedicated statement. Snowflake already uses this pattern for `GET`/`PUT`: a tokenizer keyword plus a `STATEMENT_PARSERS` entry. I'll check how those are wired so `UNDROP` follows the same route.
[tool_use Bash] {"command": "grep -n \"GET\\|PUT\" sqlglot/tokenizer_core.py | head; grep -n \"\\bGET\\b\\|\\bPUT\\b\" sqlglot/tokens.py | head; sed -n 140,160p sqlglot/dialects/snowflake.py; echo ---; grep -n \"def _parse_get\\|def _parse_put\" -A 12 sqlglot/parsers/snowflake.py | head -40; echo ---; grep -n \"class Get\\|class Put\" -A 6 sqlglot/expressions/*.py; echo ---; grep -n \"class Drop\\|class Undrop\\|class Alter(\" sqlglot/expressions/ddl.py; echo; grep -n \"def drop_sql\\|def get_sql\\|def put_sql\\|def _get_sql\\|def _put_sql\" sqlglot/generators/snowflake.py sqlglot/generator.py", "description": "Study GET/PUT wiring to mirror for UNDROP"}
[tool_result] 306:    GET = auto()
386:    PUT = auto()
        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            "BYTEINT": TokenType.INT,
            "FILE://": TokenType.URI_START,
            "FILE FORMAT": TokenType.FILE_FORMAT,
            "GET": TokenType.GET,
            "INTEGRATION": TokenType.INTEGRATION,
            "MATCH_CONDITION": TokenType.MATCH_CONDITION,
            "MATCH_RECOGNIZE": TokenType.MATCH_RECOGNIZE,
            "MINUS": TokenType.EXCEPT,
            "NCHAR VARYIN
…[2928 chars elided]…
y.py-940-    arg_types = {"this": True, "target": True, "properties": False}
sqlglot/expressions/query.py-941-
sqlglot/expressions/query.py-942-
sqlglot/expressions/query.py-943-class Table(Expression, Selectable):
sqlglot/expressions/query.py-944-    arg_types = {
sqlglot/expressions/query.py-945-        "this": False,
---
345:class Drop(Expression):
369:class DropPrimaryKey(Expression):
389:class Alter(Expression):

sqlglot/generator.py:1784:    def drop_sql(self, expression: exp.Drop) -> str:
[tool_use Bash] {"command": "grep -rn \"def put_sql\\|def get_sql\" -A 10 sqlglot/generators/ sqlglot/generator.py | head -30; echo ---; grep -n \"TokenType.PUT\\|TokenType.GET\" sqlglot/*.py sqlglot/*/*.py | head; echo ---; sed -n 300,310p sqlglot/tokenizer_core.py; sed -n 382,390p sqlglot/tokenizer_core.py; echo ---; grep -n \"def test_\\|^class\" tests/dialects/test_snowflake.py | head -30; grep -n \"IDENTIFIER(\" tests/dialects/test_snowflake.py | head -5", "description": "Check put/get generators, token enum, and test layout"}
[tool_result] ---
sqlglot/parser.py:706:        TokenType.GET,
sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:839:        TokenType.GET,
sqlglot/dialects/snowflake.py:145:            "GET": TokenType.GET,
sqlglot/dialects/snowflake.py:154:            "PUT": TokenType.PUT,
sqlglot/parsers/snowflake.py:760:        TokenType.GET: lambda self: self._parse_get(),
sqlglot/parsers/snowflake.py:761:        TokenType.PUT: lambda self: self._parse_put(),
---
    FORCE = auto()
    FOREIGN_KEY = auto()
 
…[1409 chars elided]…
_file_formats(self):
5228:    def test_show_functions(self):
5236:    def test_show_procedures(self):
770:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT foo FROM IDENTIFIER('x')")
771:        self.validate_identity("WITH x AS (SELECT 1 AS foo) SELECT IDENTIFIER('foo') FROM x")
4268:        self.validate_identity("CREATE TABLE IDENTIFIER('foo') (COLUMN1 VARCHAR, COLUMN2 VARCHAR)")
4269:        self.validate_identity("CREATE TABLE IDENTIFIER($foo) (col1 VARCHAR, col2 VARCHAR)")
[assistant] The `GET`/`PUT` wiring is clear: a `TokenType` in `tokenizer_core.py`, a Snowflake keyword mapping, and a `STATEMENT_PARSERS` entry. I'll check the neighboring token-set registrations and the existing `U` keywords so the new entry lands in the right spots.
[tool_use Bash] {"command": "sed -n 700,708p sqlglot/parser.py; echo ...; sed -n 728,734p sqlglot/parser.py; echo ...; sed -n 835,841p sqlglot/parser.py; echo ---; grep -n \"    UN[A-Z_]* = auto\\|    UPDATE = auto\\|    UNIQUE\\|    UNION\" sqlglot/tokenizer_core.py; echo ---; grep -n '\"U[A-Z_ ]*\":' sqlglot/dialects/snowflake.py; grep -n \"UNDROP\\|TokenType.UNION\\|TokenType.UNNEST\" sqlglot/parser.py | head -3; echo ---; grep -n \"def _parse_table_parts\" -A 3 sqlglot/parser.py; grep -n \"is_db_reference\" sqlglot/parser.py | head", "description": "Check token set membership and keyword ordering"}
[tool_result]         TokenType.FIRST,
        TokenType.FILE,
        TokenType.FILTER,
        TokenType.FINAL,
        TokenType.FORMAT,
        TokenType.FULL,
        TokenType.GET,
        TokenType.IDENTIFIER,
        TokenType.INOUT,
...
        TokenType.PARTITION,
        TokenType.PERCENT,
        TokenType.PIVOT,
        TokenType.PRAGMA,
        TokenType.PUT,
        TokenType.RANGE,
        TokenType.RECURSIVE,
...
        TokenType.CURRENT_CATALOG,
        TokenType.FILTER,
        TokenType.F
…[908 chars elided]…
ype == TokenType.SCHEMA
4712:        is_db_reference: bool = False,
4746:        if is_db_reference:
4751:        if not table and not is_db_reference:
4753:        if not db and is_db_reference:
4786:        is_db_reference: bool = False,
4790:        if not schema and not is_db_reference and not consume_pipe and not joins:
4857:                self._parse_table_parts(schema=schema, is_db_reference=is_db_reference)
8970:                this = self._parse_table(schema=True, is_db_reference=True)
[tool_use Bash] {"command": "awk 'NR>=600 && NR<=860 && /: t.ClassVar|= \\{|frozenset/ {print NR\": \"$0}' sqlglot/parser.py | head -30; echo ---; sed -n 160,176p sqlglot/dialects/snowflake.py; echo ---; sed -n 1,12p sqlglot/parsers/snowflake.py | head -3; grep -n \"^class\\|^from\\|^import\" sqlglot/parsers/snowflake.py | head; grep -n \"class Generator\" -A 3 sqlglot/generators/snowflake.py | head -5", "description": "Identify token-set names and dict placement"}
[tool_result] 601:     SUBQUERY_PREDICATES: t.ClassVar = {
608:     SUBQUERY_TOKENS: t.ClassVar = {
614:     RESERVED_TOKENS: t.ClassVar = {
619:     DB_CREATABLES: t.ClassVar = {
639:     CREATABLES: t.ClassVar = {
651:     TRIGGER_EVENTS: t.ClassVar = {
658:     ALTERABLES: t.ClassVar = {
666:     ID_VAR_TOKENS: t.ClassVar[set] = {
772:     TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
784:     ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
786:     COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_TOKENS
7
…[1231 chars elided]…
        # FLOAT is a synonym for DOUBLE in Snowflake
            "FLOAT": TokenType.DOUBLE,
        }
        KEYWORDS.pop("/*+")

---
from __future__ import annotations

import typing as t
1:from __future__ import annotations
3:import typing as t
5:from sqlglot import exp, parser
6:from sqlglot.trie import new_trie
7:from sqlglot.dialects.dialect import (
19:from sqlglot.helper import is_date_unit, is_int, seq_get
20:from sqlglot.tokens import TokenType
329:class SnowflakeParser(parser.Parser):
[assistant] I have the wiring. Before editing I'll read the exact regions I'm changing, starting with the base parser's token sets, the `Drop` node, and the Snowflake statement parsers.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "offset": 1184, "limit": 30}
[tool_result] 1184	    def _parse_put(self) -> exp.Put | exp.Command:
1185	        if self._curr.token_type != TokenType.STRING:
1186	            return self._parse_as_command(self._prev)
1187	
1188	        return self.expression(
1189	            exp.Put(
1190	                this=self._parse_string(),
1191	                target=self._parse_location_path(),
1192	                properties=self._parse_properties(),
1193	            )
1194	        )
1195	
1196	    def _parse_get(self) -> exp.Expr | None:
1197
…[161 chars elided]…
N):
1201	            self._retreat(self._index - 2)
1202	            return self._parse_expression()
1203	
1204	        target = self._parse_location_path()
1205	
1206	        # Parse as command if unquoted file path
1207	        if self._curr.token_type == TokenType.URI_START:
1208	            return self._parse_as_command(start)
1209	
1210	        return self.expression(
1211	            exp.Get(this=self._parse_string(), target=target, properties=self._parse_properties())
1212	        )
1213	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "offset": 362, "limit": 10}
[tool_result] 362	
363	    @property
364	    def kind(self) -> str | None:
365	        kind = self.args.get("kind")
366	        return kind and kind.upper()
367	
368	
369	class DropPrimaryKey(Expression):
370	    arg_types = {}
371	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "offset": 432, "limit": 4}
[tool_result] 432	    TYPE = auto()
433	    UNCACHE = auto()
434	    UNION = auto()
435	    UNNEST = auto()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "offset": 752, "limit": 4}
[tool_result] 752	        TokenType.TRUNCATE,
753	        TokenType.UNIQUE,
754	        TokenType.UNNEST,
755	        TokenType.UNPIVOT,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "offset": 756, "limit": 8}
[tool_result] 756	    }
757	
758	    STATEMENT_PARSERS = {
759	        **parser.Parser.STATEMENT_PARSERS,
760	        TokenType.GET: lambda self: self._parse_get(),
761	        TokenType.PUT: lambda self: self._parse_put(),
762	        TokenType.SHOW: lambda self: self._parse_show(),
763	    }
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "offset": 164, "limit": 3}
[tool_result] 164	            "STORAGE INTEGRATION": TokenType.STORAGE_INTEGRATION,
165	            "STREAMLIT": TokenType.STREAMLIT,
166	            "TAG": TokenType.TAG,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "offset": 4238, "limit": 12}
[tool_result] 4238	    def test_ddl(self):
4239	        for constraint_prefix in ("WITH ", ""):
4240	            with self.subTest(f"Constraint prefix: {constraint_prefix}"):
4241	                self.validate_identity(
4242	                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p.q.r)",
4243	                    "CREATE TABLE t (id INT MASKING POLICY p.q.r)",
4244	                )
4245	                self.validate_identity(
4246	                    f"CREATE TABLE t (id INT {constraint_prefix}MASKING POLICY p USING (c1, c2, c3))",
4247	                    "CREATE TABLE t (id INT MASKING POLICY p USING (c1, c2, c3))",
4248	                )
4249	                self.validate_identity(
[assistant] Now the edits. Token first, then the node, parser, and dialect keyword.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNCACHE = auto()\n    UNION = auto()", "new_string": "    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TAG\": TokenType.TAG,\n            \"TIMESTAMP_TZ\": TokenType.TIMESTAMPTZ,\n            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TAG\": TokenType.TAG,\n            \"TIMESTAMP_TZ\": TokenType.TIMESTAMPTZ,\n            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.UNIQUE,\n        TokenType.UNNEST,\n        TokenType.UNPIVOT,", "new_string": "        TokenType.UNIQUE,\n        TokenType.UNDROP,\n        TokenType.UNNEST,\n        TokenType.UNPIVOT,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass DropPrimaryKey(Expression):", "new_string": "        kind = self.args.get(\"kind\")\n        return kind and kind.upper()\n\n\nclass Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Now the Snowflake parser: the statement dispatch entry and the `_parse_undrop` method, placed after `_parse_get`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.PUT: lambda self: self._parse_put(),\n        TokenType.SHOW: lambda self: self._parse_show(),\n    }", "new_string": "        TokenType.PUT: lambda self: self._parse_put(),\n        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return self.expression(\n            exp.Get(this=self._parse_string(), target=target, properties=self._parse_properties())\n        )\n", "new_string": "        return self.expression(\n            e
…[165 chars elided]…
 start = self._prev\n        kind = next((k for k in self.UNDROP_KINDS if self._match_text_seq(*k.split())), None)\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(\n            exp.Undrop(\n                this=self._parse_table_parts(schema=True, is_db_reference=kind == \"SCHEMA\"),\n                kind=kind,\n            )\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,\n        TokenType.GET: lambda self: self._parse_get(),", "new_string": "    UNDROP_KINDS: t.ClassVar = (\n        \"ACCOUNT\",\n        \"DATABASE\",\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n        \"NOTEBOOK\",\n        \"SCHEMA\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TABLE\",\n        \"TAG\",\n        \"TYPE\",\n    )\n\n    STATEMENT_PARSERS = {\n        **parser.Parser.STATEMENT_PARSERS,\n        TokenType.GET: lambda self: self._parse_get(),"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Next, the generator. I'll find a fitting spot in the Snowflake generator first.
[tool_use Bash] {"command": "grep -n \"    def \" sqlglot/generators/snowflake.py | head -80", "description": "List Snowflake generator method definitions"}
[tool_result] 53:    def _builder(args: list) -> E:
102:    def _flatten_structured_type(expression: exp.Expr) -> exp.Expr:
619:    def sortarray_sql(self, expression: exp.SortArray) -> str:
626:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
677:    def with_properties(self, properties: exp.Properties) -> str:
680:    def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
686:    def datatype_sql(self, expression: exp.DataType) -> str:
717:    def tonumber_sql(self, e
…[1749 chars elided]…
l(self, expression: exp.Array) -> str:
1082:    def currentdate_sql(self, expression: exp.CurrentDate) -> str:
1093:    def dot_sql(self, expression: exp.Dot) -> str:
1107:    def modelattribute_sql(self, expression: exp.ModelAttribute) -> str:
1110:    def format_sql(self, expression: exp.Format) -> str:
1116:    def splitpart_sql(self, expression: exp.SplitPart) -> str:
1126:    def uniform_sql(self, expression: exp.Uniform) -> str:
1140:    def window_sql(self, expression: exp.Window) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "offset": 868, "limit": 8}
[tool_result] 868	
869	    def rowaccessproperty_sql(self, expression: exp.RowAccessProperty) -> str:
870	        if not expression.this:
871	            return "ROW ACCESS"
872	        on = f" ON ({self.expressions(expression, flat=True)})" if expression.expressions else ""
873	        return f"WITH ROW ACCESS POLICY {self.sql(expression, 'this')}{on}"
874	
875	    def describe_sql(self, expression: exp.Describe) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "        return f\"WITH ROW ACCESS POLICY {self.sql(expression, 'this')}{on}\"\n\n    def describe_sql(self, expression: exp.Describe) -> str:", "new_string": "        return f\"WITH ROW ACCESS POLICY {self.sql(expression, 'this')}{on}\"\n\n    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n\n    def describe_sql(self, expression: exp.Describe) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll probe the new parser with every form in the task, plus a couple of edge cases (a qualified name, a column named `undrop`, and an unknown kind).
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases=['UNDROP TABLE t','UNDROP TABLE db.s.t','UNDROP SCHEMA s','UNDROP SCHEMA d.s','UNDROP DATABASE d','UNDROP ACCOUNT a','UNDROP NOTEBOOK n','UNDROP SNAPSHOT s','UNDROP STREAMLIT s','UNDROP TAG t','UNDR
…[119 chars elided]…
"abc\\\"\\')','UNDROP SCHEMA IDENTIFIER(\\'foo\\')','UNDROP VIEW v','SELECT undrop FROM undrop']\nfor s in cases:\n    try:\n        e=sqlglot.parse_one(s,read='snowflake'); print(repr(s),'->',type(e).__name__, '|', e.sql('snowflake'))\n    except Exception as ex: print(repr(s),'ERR',type(ex).__name__, str(ex).splitlines()[0][:100])\n\"", "description": "Probe new UNDROP parsing across all forms"}
[tool_result] 'UNDROP VIEW v' contains unsupported syntax. Falling back to parsing as a 'Command'.
'UNDROP TABLE t' -> Undrop | UNDROP TABLE t
'UNDROP TABLE db.s.t' -> Undrop | UNDROP TABLE db.s.t
'UNDROP SCHEMA s' -> Undrop | UNDROP SCHEMA s
'UNDROP SCHEMA d.s' -> Undrop | UNDROP SCHEMA d.s
'UNDROP DATABASE d' -> Undrop | UNDROP DATABASE d
'UNDROP ACCOUNT a' -> Undrop | UNDROP ACCOUNT a
'UNDROP NOTEBOOK n' -> Undrop | UNDROP NOTEBOOK n
'UNDROP SNAPSHOT s' -> Undrop | UNDROP SNAPSHOT s
'UNDROP STREAMLIT s' ->
…[63 chars elided]…
TAG t
'UNDROP TYPE t' -> Undrop | UNDROP TYPE t
'UNDROP DYNAMIC TABLE t' -> Undrop | UNDROP DYNAMIC TABLE t
'UNDROP EXTERNAL VOLUME v' -> Undrop | UNDROP EXTERNAL VOLUME v
'UNDROP ICEBERG TABLE t' -> Undrop | UNDROP ICEBERG TABLE t
'UNDROP TABLE IDENTIFIER(\'"abc"\')' -> Undrop | UNDROP TABLE IDENTIFIER('"abc"')
"UNDROP SCHEMA IDENTIFIER('foo')" -> Undrop | UNDROP SCHEMA IDENTIFIER('foo')
'UNDROP VIEW v' -> Command | UNDROP VIEW v
'SELECT undrop FROM undrop' -> Select | SELECT undrop FROM undrop
[assistant] Every form in the task round-trips, and the `Command` fallback still covers unknown kinds. Next I'll add identity tests at the end of `test_ddl`.
[tool_use Bash] {"command": "sed -n 4385,4408p tests/dialects/test_snowflake.py", "description": "Show end of test_ddl for insertion point"}
[tool_result]         self.validate_identity("CREATE TABLE a TAG (key1='value_1', key2='value_2')")
        self.validate_all(
            "CREATE TABLE a TAG (key1='value_1')",
            read={
                "snowflake": "CREATE TABLE a WITH TAG (key1='value_1')",
            },
        )

        for action in ("SET", "DROP"):
            with self.subTest(f"ALTER COLUMN {action} NOT NULL"):
                self.validate_all(
                    f"ALTER TABLE a ALTER COLUMN my_column {action} NOT NULL",
…[44 chars elided]…
        "snowflake": f"ALTER TABLE a MODIFY COLUMN my_column {action} NOT NULL",
                    },
                    write={
                        "snowflake": f"ALTER TABLE a ALTER COLUMN my_column {action} NOT NULL",
                        "duckdb": f"ALTER TABLE a ALTER COLUMN my_column {action} NOT NULL",
                        "postgres": f"ALTER TABLE a ALTER COLUMN my_column {action} NOT NULL",
                    },
                )

    def test_user_defined_functions(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "                        \"postgres\": f\"ALTER TABLE a ALTER COLUMN my_column {action} NOT NULL\",\n                    },\n                )\n\n    def test_user_defined_functions(self):", "new_string": 
…[496 chars elided]…
        ):\n            with self.subTest(f\"UNDROP {kind}\"):\n                self.validate_identity(f\"UNDROP {kind} my_object\")\n                self.validate_identity(f\"UNDROP {kind} IDENTIFIER('\\\"my_object\\\"')\")\n\n        self.validate_identity(\"UNDROP TABLE db.schema.t\")\n        self.validate_identity(\"UNDROP SCHEMA db.my_schema\")\n\n    def test_user_defined_functions(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100833-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] Now the tests: the Snowflake dialect file first, then the full suite using the project's pytest command.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py 2>&1 | tail -15", "description": "Run Snowflake dialect tests"}
[tool_result] ......................................................... [ 60%]
......................................                                                      [100%]
95 passed, 1580 subtests passed in 0.57s
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"--- ruff\"; ($PY -m ruff check sqlglot tests/dialects/test_snowflake.py && $PY -m ruff format --check sqlglot tests/dialects/test_snowflake.py) 2>&1 | tail -8", "description": "Run full test suite and lint checks"}
[tool_result] ..................... [ 21%]
............................................................................... [ 28%]
................................................ [ 32%]
................................................................................................. [ 41%]
...............................................................................................................................................................................................................................
…[185 chars elided]…
........... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
.......................... [ 97%]
.................. [ 99%]
.......                                                             [100%]
1120 passed, 18188 subtests passed in 85.09s (0:01:25)
--- ruff
All checks passed!
177 files already formatted
[assistant] All 1120 tests pass and ruff is clean. I'll take a final look at the diff.
[tool_use Bash] {"command": "git status --short && git diff --stat", "description": "Show changed files and diff stats"}
[tool_result]  M sqlglot/dialects/snowflake.py
 M sqlglot/expressions/ddl.py
 M sqlglot/generators/snowflake.py
 M sqlglot/parser.py
 M sqlglot/parsers/snowflake.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_snowflake.py
 sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generators/snowflake.py  |  3 +++
 sqlglot/parser.py                |  1 +
 sqlglot/parsers/snowflake.py     | 29 +++++++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 21 +++++++++++++++++++++
 7 files changed, 60 insertions(+)
[assistant] Snowflake `UNDROP` now parses and regenerates for all twelve object types, including the `IDENTIFIER(...)` form. The full suite passes (1120 tests) and ruff is clean. I didn't run mypy or `make style`.

Before the change, every form raised a `ParseError` because `UNDROP` was an unknown keyword. Now:

- **Token:** `UNDROP` is a keyword in the Snowflake dialect (`tokenizer_core.py`, `dialects/snowflake.py`), and it is added to `ID_VAR_TOKENS` so it still works as an identifier. `SELECT undrop FROM undrop` still parses.
- **Node:** a new `exp.Undrop(this, kind)` in `expressions/ddl.py`. I did not
…[399 chars elided]…
or:** `undrop_sql` in `generators/snowflake.py`.
- **Tests:** `test_ddl` in `tests/dialects/test_snowflake.py` round-trips each kind with a plain name and with `IDENTIFIER('"my_object"')`, plus a qualified `db.schema.t` name and `UNDROP SCHEMA db.my_schema`.

Decision for you: the new `UNDROP` keyword is Snowflake-only, so Snowflake code can no longer use `undrop` as an unquoted identifier outside a `SELECT` column list. `GET` and `PUT` already have the same restriction. If you'd rather avoid that, I can match on text in the statement parser instead, at the cost of a less conventional pattern.
