# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. Your example produces `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`. The full suite passes (1104 tests), and ruff check and format are clean on the changed files.

**Cause:** In `sqlglot/parser.py`, `_parse_table` returns early when the source is a parenthesized subquery, before it reaches the `if joins:` block that attaches JOIN clauses. The FROM-first path then consumed the joins later, after the trailing `SELECT` had already been skipped, so the parser failed on `select`. Plain tables were unaffected because their joins were attached before that return.

**Fix:** On the subquery return path, `_parse_table` now attaches joins to the subquery when `joins=True`, using the same pattern as the table path.

**Test:** I added two cases to `tests/dialects/test_duckdb.py` next to the other FROM-first tests. One is your positional join example. The other is a subquery followed by a regular `JOIN`.

Joins are now attached to the subquery node when the source is a subquery in a FROM-first query. I didn't check the generated SQL against a live DuckDB instance.

## events
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n          'from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2',\n          'from (select 1 as x) t1 positional join (select 2 as x) t2 select t1.x as x1, t2.x as x2',\n          'from (FROM tbl_1) t1 select t1.x',\n          'from (FROM tbl_1) select x']:\n    try:\n        print(repr(sqlglot.parse_one(q, read='duckdb').sql('duckdb')))\n    except Exception as e:\n        print('ERR', q, '->', str(e)[:300])\n\"; grep -n \"FROM\\|from_\" sqlglot/dialects/duckdb.py | head -60", "description": "Reproduce the FROM-first parse failure"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
0 matches for 'FROM\|from_'
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.__file__)\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n          'from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2',\n          'from (select 1 as x) t1 positional join (select 2 as x) t2 select t1.x as 
…[65 chars elided]…
          'from (FROM tbl_1) select x']:\n    try:\n        print(repr(sqlglot.parse_one(q, read='duckdb').sql('duckdb')))\n    except Exception as e:\n        print('ERR', q, '->', str(e)[:300])\n\"; grep -n \"FROM\" sqlglot/dialects/duckdb.py | head; grep -n \"def _parse_select\\|FROM\\b\" sqlglot/parser.py | head -40", "description": "Reproduce FROM-first parse failures and locate parser code"}
[tool_result] ~/.cache/lithify/work/repo-6e430de19896/20261029-184329-duckdb-dialect-from-first-querie/base-1/sqlglot/__init__.py
ERR from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2 -> Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
'SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2'
ERR from (select 1 as x) t1 positional join (select 2 a
…[1210 chars elided]…
..b case
sqlglot/parser.py:4758:if self._match_text_seq("ROWS", "FROM")
sqlglot/parser.py:5409:from_=self._match(TokenType.FROM) and self._parse_bitwise(),
sqlglot/parser.py:7613:self.raise_error("Expected FROM or comma after EXTRACT", self._prev)
sqlglot/parser.py:8086:invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_F...
sqlglot/parser.py:9408:kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
sqlglot/parser.py:9576:from_=_parse_overlay_arg("FROM"),
[tool_use Bash] {"command": "sed -n 3700,3830p sqlglot/parser.py", "description": "Read FROM-first and subquery parsing code"}
[tool_result]         def _parse_value_expression() -> exp.Expr | None:
            if self.dialect.SUPPORTS_VALUES_DEFAULT and self._match(TokenType.DEFAULT):
                return exp.var(self._prev.text.upper())
            return self._parse_expression()

        if self._match(TokenType.L_PAREN):
            expressions = self._parse_csv(_parse_value_expression)
            self._match_r_paren()
            return self.expression(exp.Tuple(expressions=expressions))

        # In some dialects we can hav
…[3813 chars elided]…

            hint = self._parse_hint()

            if self._next and not self._next.token_type == TokenType.DOT:
                all_ = self._match(TokenType.ALL)
                matched_distinct = self._match_set(self.DISTINCT_TOKENS)
            else:
                all_, matched_distinct = None, False

            kind = (
                self._prev.text.upper()
                if self._match(TokenType.ALIAS) and self._match_texts(("STRUCT", "VALUE"))
                else None
            )
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = ['from tbl_1 t1 join (select 2 as x) t2 on true select t1.x',\n'from tbl_1 t1 positional join (select 2 as x) t2 select t1.x',\n'from (select 1 as x) t1 select t1.x',\n'from (select 1 as x) t1 join tbl_2 t2 on true select t1.x',\n'from (select 1 as x) t1 join (select 2 as x) t2 on tru
…[176 chars elided]…
 tbl_2) t2 on true select t1.x',\n'from tbl_1 t1 join (FROM tbl_2) t2 on true',\n'from tbl_1 t1 positional join tbl_2 t2 select t1.x',\n]\nfor q in qs:\n    try:\n        print('OK ', repr(sqlglot.parse_one(q, read='duckdb').sql('duckdb')))\n    except Exception as e:\n        print('ERR', q, '->', str(e)[:120].replace(chr(10),' | '))\n\"", "description": "Bisect which FROM-first join forms fail"}
[tool_result] OK  'SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT 2 AS x) AS t2 ON TRUE'
OK  'SELECT t1.x FROM tbl_1 AS t1 POSITIONAL JOIN (SELECT 2 AS x) AS t2'
OK  'SELECT t1.x FROM (SELECT 1 AS x) AS t1'
ERR from (select 1 as x) t1 join tbl_2 t2 on true select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 52. |   from (select 1 as x) t1 join tbl_2 t2 on true [4mselect[0m t
ERR from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x -> Invalid expression / Unexpected token. Line 1, Co
…[53 chars elided]…
x) t2 on true [4mse
OK  'SELECT t1.x FROM (SELECT 1 AS x) AS t1 POSITIONAL JOIN (SELECT 2 AS x) AS t2'
ERR from (FROM tbl_1) t1 join tbl_2 t2 on true select t1.x -> Invalid expression / Unexpected token. Line 1, Col: 49. |   from (FROM tbl_1) t1 join tbl_2 t2 on true [4mselect[0m t1.x
OK  'SELECT t1.x FROM tbl_1 AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON TRUE'
OK  'SELECT * FROM tbl_1 AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON TRUE'
OK  'SELECT t1.x FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2'
[tool_use Bash] {"command": "grep -n \"def _parse_from\\|def _parse_table(\\|def _parse_query_modifiers\\|def _parse_subquery\\|def _parse_table_parts\" sqlglot/parser.py", "description": "Locate FROM, table, and modifier parsing functions"}
[tool_result ERROR] Exit code 2
rg: regex parse error:
    (?:def _parse_from|def _parse_table(|def _parse_query_modifiers|def _parse_subquery|def _parse_table_parts)
    ^
error: unclosed group
0 matches for 'def _parse_from\|def _parse_table(\|def _parse_query_modifiers\|def _parse_subquery\|def _parse_table_parts'
[tool_use Bash] {"command": "grep -nE \"def (_parse_from|_parse_table|_parse_query_modifiers|_parse_subquery|_parse_table_parts)\\b\" sqlglot/parser.py", "description": "Locate FROM, table, and modifier parsing functions"}
[tool_result] 4029:    def _parse_subquery(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4168:    def _parse_from(
4627:    def _parse_table_parts(
4698:    def _parse_table(
[tool_use Bash] {"command": "sed -n 4029,4200p sqlglot/parser.py && echo ---- && sed -n 4698,4790p sqlglot/parser.py", "description": "Read subquery, modifiers, from, and table parsing"}
[tool_result]     def _parse_subquery(
        self, this: exp.Expr | None, parse_alias: bool = True
    ) -> exp.Subquery | None:
        if not this:
            return None

        return self.expression(
            exp.Subquery(
                this=this,
                pivots=self._parse_pivots(),
                alias=self._parse_table_alias() if parse_alias else None,
                sample=self._parse_table_sample(),
            )
        )

    def _implicit_unnests_to_explicit(self, this: E) -> E
…[8677 chars elided]…
upports a wildcard (table) suffix operator, which is a no-op in this context
        self._match(TokenType.STAR)

        parse_partition = parse_partition or self.SUPPORTS_PARTITION_SELECTION
        if parse_partition and self._match(TokenType.PARTITION, advance=False):
            this.set("partition", self._parse_partition())

        if schema:
            return self._parse_schema(this=this)

        if self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())
[tool_use Bash] {"command": "sed -n 4790,4830p sqlglot/parser.py && echo ---- && sed -n 3830,3990p sqlglot/parser.py | grep -n \"\" | sed -n 1,200p | grep -n \"L_PAREN\\|_parse_wrapped_select\\|_parse_subquery\\|_parse_query_modifiers\\|from_\\|joins\\|table\" ", "description": "Read rest of table parsing and select-query L_PAREN handling"}
[tool_result]             this.set("version", self._parse_version())

        if self.dialect.ALIAS_POST_TABLESAMPLE:
            this.set("sample", self._parse_table_sample())

        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
        if alias:
            this.set("alias", alias)

        if self._match(TokenType.INDEXED_BY):
            this.set("indexed", self._parse_table_parts())
        elif self._match_text_seq("NOT", "INDEXED"):
            this.set("indexe
…[1464 chars elided]…
m_:
60:60:            this = exp.select("*").from_(from_.this, copy=False)
61:61:            this = self._parse_query_modifiers(this)
63:63:            table = self._match(TokenType.TABLE)
64:64:            this = self._parse_select() or self._parse_string() or self._parse_table()
65:65:            return self.expression(exp.Summarize(this=this, table=table))
127:127:        alias = self._parse_table_alias(self.ID_VAR_TOKENS)
161:161:                cte.set("this", exp.select("*").from_(values))
[tool_use Bash] {"command": "sed -n 3870,3905p sqlglot/parser.py; echo ----; sed -n 3960,3975p sqlglot/parser.py", "description": "Read select-query branches after FROM handling"}
[tool_result]             if from_:
                this.set("from_", from_)

            this = self._parse_query_modifiers(this)
        elif (table or nested) and self._match(TokenType.L_PAREN):
            comments = self._prev_comments
            this = self._parse_wrapped_select(table=table)

            if this:
                this.add_comments(comments, prepend=True)

            # We return early here so that the UNION isn't attached to the subquery by the
            # following call to _parse_set
…[1125 chars elided]…
           self._parse_wrapped_id_vars() if self._match_text_seq("USING", "KEY") else None
        )

        if not self._match(TokenType.ALIAS) and not self.OPTIONAL_ALIAS_TOKEN_CTE:
            self._retreat(index)
            return None

        comments = self._prev_comments

        if self._match_text_seq("NOT", "MATERIALIZED"):
            materialized = False
        elif self._match_text_seq("MATERIALIZED"):
            materialized = True
        else:
            materialized = None
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = ['from (select * from tbl_1) t1 select t1.x',\n'from (FROM tbl_1) t1 select t1.x',\n'from (FROM tbl_1) as t1 select t1.x',\n'from (FROM tbl_1 where a = 1) t1 select t1.x',\n'from tbl_1 t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n]\nfor q in qs:\n    try:\n     
…[34 chars elided]…
duckdb'); print('OK ', repr(e.sql('duckdb')), '|', repr(e.sql('duckdb')) and type(e.args['from_'].this).__name__)\n    except Exception as e:\n        print('ERR', q, '->', str(e)[:120].replace(chr(10),' | '))\n\"; grep -rn \"joins=True\" sqlglot/ | head; grep -n \"class Subquery\" -A12 sqlglot/expressions/query.py | head -30", "description": "Check alias handling and find joins-in-table callers"}
[tool_result] OK  'SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1' | Subquery
OK  'SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1' | Subquery
OK  'SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1' | Subquery
OK  'SELECT t1.x FROM (SELECT * FROM tbl_1 WHERE a = 1) AS t1' | Subquery
OK  'SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2' | Table
sqlglot/parsers/teradata.py:122:                from_=self._parse_from(joins=True),
sqlglot/parser.py:1051:        exp.From: lambda sel
…[443 chars elided]…
py:3809:            self._parse_from(joins=True, consume_pipe=True)
1662:class Subquery(Expression, DerivedTable, Query):
1663-    is_subquery: t.ClassVar[bool] = True
1664-    arg_types = {
1665-        "this": True,
1666-        "alias": False,
1667-        "with_": False,
1668-        **QUERY_MODIFIERS,
1669-    }
1670-
1671-    def unnest(self) -> Expr:
1672-        """Returns the first non subquery."""
1673-        expression: Expr = self
1674-        while isinstance(expression, Subquery):
[assistant] The root cause is in `_parse_table`: when the source is a parenthesized subquery, it returns early (line ~4745) before the `if joins:` block that attaches JOIN clauses. The FROM-first path then falls into the `elif from_` branch, which consumes the joins but leaves the trailing `select` unparsed. I'll apply the same join handling on the subquery early-return path.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184329-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return subquery", "new_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins:\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184329-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n'from (select 1 as x) t1 join tbl_2 t2 on true select t1.x',\n'from (select 1 as x) t1 join (select 2 as x) t2 on true select t1.x',\n'from (select 1 as x) t1 join tbl_2 t2 on true',\n'from (FROM t
…[136 chars elided]…
        e = sqlglot.parse_one(q, read='duckdb'); print('OK ', repr(e.sql('duckdb')))\n    except Exception as e:\n        print('ERR', q, '->', str(e)[:120].replace(chr(10),' | '))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix on joined-subquery cases and run the test suite"}
[tool_result] OK  'SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2'
OK  'SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE'
OK  'SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN (SELECT 2 AS x) AS t2 ON TRUE'
OK  'SELECT * FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE'
OK  'SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN tbl_2 AS t2 ON TRUE WHERE t1.x > 1'
OK  'SELECT * FROM (SELECT 1) AS t1 JOIN t2 ON TRUE'
..........................
…[410 chars elided]…
................................... [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
.................................................................................................................................................. [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 47.29s
[assistant] All 1104 tests pass. Now I'll add a regression test next to the existing FROM-first tests.
[tool_use Bash] {"command": "grep -n -i \"from-first\\|FROM tbl\\|\\\"FROM \" tests/dialects/test_duckdb.py | head -20; grep -n \"positional join\\|POSITIONAL\" tests/dialects/test_duckdb.py | head", "description": "Find existing FROM-first and positional join tests"}
[tool_result] 426:            "SELECT tbl.x*1e4+tbl.y FROM tbl",
427:            "SELECT tbl.x * 1e4 + tbl.y FROM tbl",
485:        self.validate_identity("FROM  x SELECT x UNION SELECT 1", "SELECT x FROM x UNION SELECT 1")
486:        self.validate_identity("FROM (FROM tbl)", "SELECT * FROM (SELECT * FROM tbl)")
487:        self.validate_identity("FROM tbl", "SELECT * FROM tbl")
496:        self.validate_identity("SUMMARIZE SELECT * FROM tbl").assert_is(exp.Summarize)
1453:            "FROM (FROM t1 UNION FR
…[626 chars elided]…
SING SAMPLE BERNOULLI (10 PERCENT)",
1962:            "SELECT * FROM tbl USING SAMPLE reservoir(50 ROWS) REPEATABLE (100)",
1963:            "SELECT * FROM tbl USING SAMPLE RESERVOIR (50 ROWS) REPEATABLE (100)",
1966:            "SELECT * FROM tbl USING SAMPLE 10% (system, 377)",
1967:            "SELECT * FROM tbl USING SAMPLE SYSTEM (10 PERCENT) REPEATABLE (377)",
1 matches in 1 files:

tests/dialects/test_duckdb.py:469:self.validate_identity("SELECT df1.*, df2.* FROM df1 POSITIONAL JOIN df2")
[tool_use Bash] {"command": "sed -n 1515,1525p tests/dialects/test_duckdb.py", "description": "View context around FROM-first tests"}
[tool_result]         self.validate_identity(
            "SELECT CAST(TRIM(CAST(CAST('***apple***' AS BLOB) AS TEXT), CAST(CAST('*' AS BLOB) AS TEXT)) AS BLOB) AS result"
        )
        self.validate_identity("SELECT GREATEST(1.0, 2.5, NULL, 3.7)")
        self.validate_identity("FROM t1, t2 SELECT *", "SELECT * FROM t1, t2")
        self.validate_identity("ROUND(2.256, 1)")

        # TODO: This is incorrect AST, DATE_PART creates a STRUCT of values but it's stored in 'year' arg
        self.validate_identity(
            "SELECT MAKE_DATE(DATE_PART(['year', 'month', 'day'], CURRENT_DATE))"
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-184329-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "        self.validate_identity(\"FROM t1, t2 SELECT *\", \"SELECT * FROM t1, t2\")\n        self.validate_identity(\"ROUND(2.256, 1)\")", "new_string": "        self.validate_identity(\"FROM t1, t2 SELECT *\
…[155 chars elided]…
S x2\",\n            \"SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2\",\n        )\n        self.validate_identity(\n            \"FROM (SELECT 1 AS x) t1 JOIN tbl_2 t2 ON TRUE SELECT t1.x\",\n            \"SELECT t1.x FROM (SELECT 1 AS x) AS t1 JOIN tbl_2 AS t2 ON TRUE\",\n        )\n        self.validate_identity(\"ROUND(2.256, 1)\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-184329-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short; git diff --stat", "description": "Run full test suite and show changed files"}
[tool_result] ................................. [ 94%]
..........................................................                              [100%]
1104 passed, 17947 subtests passed in 47.61s
 M sqlglot/parser.py
 M tests/dialects/test_duckdb.pysqlglot/parser.py             | 3 +++
 tests/dialects/test_duckdb.py | 8 ++++++++
 2 files changed, 11 insertions(+)
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_duckdb.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py) 2>&1 | tail -5", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] FROM-first queries with joined subqueries now parse. Your example produces `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`. The full suite passes (1104 tests), and ruff check and format are clean on the changed files.

**Cause:** In `sqlglot/parser.py`, `_parse_table` returns early when the source is a parenthesized subquery, before it reaches the `if joins:` block that attaches JOIN clauses. The FROM-first path then consumed the joins later, after the trailing `SELECT` had already been skipped, so the parser failed on `select`. Plain tables were unaffected because their joins were attached before that return.

**Fix:** On the subquery return path, `_parse_table` now attaches joins to the subquery when `joins=True`, using the same pattern as the table path.

**Test:** I added two cases to `tests/dialects/test_duckdb.py` next to the other FROM-first tests. One is your positional join example. The other is a subquery followed by a regular `JOIN`.

Joins are now attached to the subquery node when the source is a subquery in a FROM-first query. I didn't check the generated SQL against a live DuckDB instance.
