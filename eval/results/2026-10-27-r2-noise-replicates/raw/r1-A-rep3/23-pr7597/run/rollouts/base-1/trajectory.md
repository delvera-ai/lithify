# trajectory base-1

final message:
FROM-first queries with joined subqueries now parse. Your example produces `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`. The full suite passes (1105 tests), and ruff check and format are clean.

**Cause:** In `_parse_table`, a parenthesized source returns early before the bottom-of-function `if joins:` block. So with `joins=True`, the join after `(FROM tbl_1) t1` was never consumed. The FROM-first path then saw `JOIN` where it expected `SELECT`, fell into the `elif from_:` branch, and left `select ...` unparsed. That's why the error points at `select`. The bug also affected `from (select ...) t1 join ...`, not just `(FROM ...)`.

**Fix (`sqlglot/parser.py`):**
- `_parse_table` now attaches joins to a parenthesized source when `joins=True`.
- `_parse_update` had a workaround for the same gap, attaching joins to a subquery by hand. It's now redundant, so I removed it. UPDATE with a subquery and a join still generates the same SQL.

**Test (`tests/dialects/test_duckdb.py`):** added `test_from_first_with_joined_subqueries` covering your query and a `JOIN ... ON TRUE` variant.

I didn't commit, since you didn't ask for one.

## events
[assistant] I'll start by reproducing the failure and finding the FROM-first parsing code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2',\n          'from tbl_1 t1 positional join tbl_2 t2 select t1.x as x1, t2.x as x2',\n          'from (select * from tbl_1) t1 positional join (select * from tbl_2) t2 select t1.x as x1, t2.x as x
…[57 chars elided]…
 on true select t1.x']:\n    try:\n        print(repr(sqlglot.parse_one(q, read='duckdb').sql('duckdb')))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\" ; grep -n \"FROM\" sqlglot/dialects/duckdb.py | head -40; grep -n \"def _parse_from\\|def _parse_select\\|FROM\\b\" sqlglot/parser.py | head -40", "description": "Reproduce failure and locate FROM-first parsing code"}
[tool_result] ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 59.
  from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
'SELECT t1.x AS x1, t2.x AS x2 FROM tbl_1 AS t1 POSITIONAL JOIN tbl_2 AS t2'
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 77.
  from (select * from tbl_1) t1 positional join (select * from tbl_2) t2 [4mselect[0m t1.x as x1, t2.x as x2
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 56.
  from
…[1551 chars elided]…
_set((TokenType.FROM, TokenType.COMMA)):
8086:            invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_FIRST
8433:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
8780:            if self._match_set((TokenType.FROM, TokenType.IN)):
9408:        kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
9541:        if not securable or not self._match_text_seq("FROM"):
9576:                from_=_parse_overlay_arg("FROM"),
[assistant] The failure reproduces, and it's not specific to `FROM (FROM ...)`: `from (select ...) ... join (select ...)` fails the same way. Let me read the relevant parser code.
[tool_use Bash] {"command": "sed -n 3700,3760p sqlglot/parser.py; echo ----; sed -n 3779,3840p sqlglot/parser.py", "description": "Read FROM-first and table-parsing code in parser"}
[tool_result]         def _parse_value_expression() -> exp.Expr | None:
            if self.dialect.SUPPORTS_VALUES_DEFAULT and self._match(TokenType.DEFAULT):
                return exp.var(self._prev.text.upper())
            return self._parse_expression()

        if self._match(TokenType.L_PAREN):
            expressions = self._parse_csv(_parse_value_expression)
            self._match_r_paren()
            return self.expression(exp.Tuple(expressions=expressions))

        # In some dialects we can hav
…[3490 chars elided]…
d = (
                self._prev.text.upper()
                if self._match(TokenType.ALIAS) and self._match_texts(("STRUCT", "VALUE"))
                else None
            )

            distinct: exp.Expr | None = (
                self.expression(
                    exp.Distinct(
                        on=self._parse_value(values=False) if self._match(TokenType.ON) else None
                    )
                )
                if matched_distinct
                else None
            )
[assistant] The top-level FROM-first path calls `_parse_from(joins=True)`. To find where the subquery case diverges, I'll test minimal variants.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = ['from (select * from t1) t1 select t1.x',\n'from (select * from t1) t1 join t2 on true select t1.x',\n'from t1 join (select * from t2) t2 on true select t1.x',\n'from t1 join (select * from t2) t2 on true',\n'from (select * from t1) t1 join (select * from t2) t2 on true',\n'select t1
…[115 chars elided]…
select t1.x',\n'from (select * from t1) t1 positional join t2 select t1.x',\n'from t1 positional join t2 select t1.x',\n]\nfor q in qs:\n    try: print('OK ', q, '=>', sqlglot.parse_one(q, read='duckdb').sql('duckdb'))\n    except Exception as e: print('ERR', q)\n\"; grep -n \"def _parse_from\\b\" -A 30 sqlglot/parser.py | head -45", "description": "Test minimal FROM-first subquery join variants"}
[tool_result] OK  from (select * from t1) t1 select t1.x => SELECT t1.x FROM (SELECT * FROM t1) AS t1
ERR from (select * from t1) t1 join t2 on true select t1.x
OK  from t1 join (select * from t2) t2 on true select t1.x => SELECT t1.x FROM t1 JOIN (SELECT * FROM t2) AS t2 ON TRUE
OK  from t1 join (select * from t2) t2 on true => SELECT * FROM t1 JOIN (SELECT * FROM t2) AS t2 ON TRUE
OK  from (select * from t1) t1 join (select * from t2) t2 on true => SELECT * FROM (SELECT * FROM t1) AS t1 JOIN (SELECT * FROM 
…[1140 chars elided]…
ure(
4186-                window_frame=self._match_texts(("FINAL", "RUNNING")) and self._prev.text.upper(),
4187-                this=self._parse_expression(),
4188-            )
4189-        )
4190-
4191-    def _parse_match_recognize(self) -> exp.MatchRecognize | None:
4192-        if not self._match(TokenType.MATCH_RECOGNIZE):
4193-            return None
4194-
4195-        self._match_l_paren()
4196-
4197-        partition = self._parse_partition_by()
4198-        order = self._parse_order()
[assistant] The failing pattern is a subquery as the first FROM source combined with a join under `joins=True`. Let me look at how `_parse_table` handles a parenthesized source.
[tool_use Bash] {"command": "grep -n \"def _parse_table(\\|def _parse_derived_table\\|def _parse_table_parts\\|def _parse_subquery\\|def _parse_query_modifiers\" sqlglot/parser.py", "description": "Find table-parsing function definitions"}
[tool_result] 4029:    def _parse_subquery(
4072:    def _parse_query_modifiers(self, this: E) -> E: ...
4075:    def _parse_query_modifiers(self, this: None) -> None: ...
4077:    def _parse_query_modifiers(self, this):
4564:    def _parse_table_parts_fast(self) -> exp.Table | None:
4627:    def _parse_table_parts(
4698:    def _parse_table(
4928:    def _parse_derived_table_values(self) -> exp.Values | None:
[tool_use Bash] {"command": "sed -n 4029,4070p sqlglot/parser.py; echo -----; sed -n 4698,4790p sqlglot/parser.py", "description": "Read subquery and _parse_table implementation"}
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
…[4082 chars elided]…
upports a wildcard (table) suffix operator, which is a no-op in this context
        self._match(TokenType.STAR)

        parse_partition = parse_partition or self.SUPPORTS_PARTITION_SELECTION
        if parse_partition and self._match(TokenType.PARTITION, advance=False):
            this.set("partition", self._parse_partition())

        if schema:
            return self._parse_schema(this=this)

        if self.dialect.ALIAS_POST_VERSION:
            this.set("version", self._parse_version())
[tool_use Bash] {"command": "sed -n 3754,3778p sqlglot/parser.py; echo ----; grep -n \"L_PAREN\" sqlglot/parser.py | sed -n 1,80p | awk -F: '$1>3754 && $1<3800'; echo; sed -n 4077,4100p sqlglot/parser.py", "description": "Read _parse_select wrapper and query modifiers entry"}
[tool_result]     def _parse_select(
        self,
        nested: bool = False,
        table: bool = False,
        parse_subquery_alias: bool = True,
        parse_set_operation: bool = True,
        consume_pipe: bool = True,
        from_: exp.From | None = None,
    ) -> exp.Expr | None:
        query = self._parse_select_query(
            nested=nested,
            table=table,
            parse_subquery_alias=parse_subquery_alias,
            parse_set_operation=parse_set_operation,
        )

      
…[973 chars elided]…
 expression:
                        if this.args.get(key):
                            self.raise_error(
                                f"Found multiple '{modifier_token.text.upper()}' clauses",
                                token=modifier_token,
                            )

                        this.set(key, expression)
                        if key == "limit":
                            offset = expression.args.get("offset")
                            expression.set("offset", None)
[tool_use Bash] {"command": "awk 'NR>=3840 && NR<=3990 && /L_PAREN|nested|table|parse_subquery|from_|modifiers|return this|return query|this = /{print NR\": \"$0}' sqlglot/parser.py", "description": "Scan select-query tail for subquery handling"}
[tool_result] 3844:             operation_modifiers = []
3846:                 operation_modifiers.append(exp.var(self._prev.text.upper()))
3851:             this = self.expression(
3859:                     operation_modifiers=operation_modifiers or None,
3868:             if not from_:
3869:                 from_ = self._parse_from()
3871:             if from_:
3872:                 this.set("from_", from_)
3874:             this = self._parse_query_modifiers(this)
3875:         elif (table or nested) and s
…[338 chars elided]…

3890:             this = self._parse_query_modifiers(this)
3892:             table = self._match(TokenType.TABLE)
3893:             this = self._parse_select() or self._parse_string() or self._parse_table()
3894:             return self.expression(exp.Summarize(this=this, table=table))
3896:             this = self._parse_describe()
3898:             this = None
3956:         alias = self._parse_table_alias(self.ID_VAR_TOKENS)
3990:                 cte.set("this", exp.select("*").from_(values))
[tool_use Bash] {"command": "sed -n 3862,3905p sqlglot/parser.py", "description": "Read select-query branches for FROM and parenthesized subquery"}
[tool_result]             this.comments = comments

            into = self._parse_into()
            if into:
                this.set("into", into)

            if not from_:
                from_ = self._parse_from()

            if from_:
                this.set("from_", from_)

            this = self._parse_query_modifiers(this)
        elif (table or nested) and self._match(TokenType.L_PAREN):
            comments = self._prev_comments
            this = self._parse_wrapped_select(table=table)

      
…[797 chars elided]…
able()
            return self.expression(exp.Summarize(this=this, table=table))
        elif self._match(TokenType.DESCRIBE):
            this = self._parse_describe()
        else:
            this = None

        return self._parse_set_operations(this) if parse_set_operation else this

    def _parse_recursive_with_search(self) -> exp.RecursiveWithSearch | None:
        self._match_text_seq("SEARCH")

        kind = self._match_texts(self.RECURSIVE_CTE_SEARCH_KIND) and self._prev.text.upper()
[assistant] The parenthesized branch returns early from `_parse_select`, so joins after a subquery depend on what `_parse_table` does with `joins=True`. Let me check that tail.
[tool_use Bash] {"command": "sed -n 4790,4830p sqlglot/parser.py; echo ----; sed -n 3600,3640p sqlglot/parser.py", "description": "Read rest of _parse_table and nearby join handling"}
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
…[2279 chars elided]…
           kwargs["returning"] = self._parse_returning()
            elif self._match(TokenType.FROM, advance=False):
                from_ = self._parse_from(joins=True)
                table = from_.this if from_ else None
                if isinstance(table, exp.Subquery) and self._match(TokenType.JOIN, advance=False):
                    table.set("joins", list(self._parse_joins()) or None)

                kwargs["from_"] = from_
            elif self._match(TokenType.WHERE, advance=False):
[assistant] Found the cause. In `_parse_table`, the subquery branch returns early (line ~4745) before the `if joins:` block at the bottom, so `join` after a parenthesized source is never consumed under `joins=True`. Then the FROM-first path sees a `JOIN` instead of `SELECT`, falls into the `elif from_:` branch, and that path consumes the join but leaves `select ...` unparsed. The error column points at `select`, which matches.

`_parse_update` already works around the same gap by attaching joins to a `Subquery` manually. Let me confirm `Subquery` supports a `joins` arg and see how the generator emits it before deciding where to fix.
[tool_use Bash] {"command": "grep -n \"class Subquery(\" -A 12 sqlglot/expressions.py | head -20; grep -n \"def subquery_sql\" -A 25 sqlglot/generator.py | head -40; git log --oneline -3 -- sqlglot/parser.py | cat; grep -rn \"from (FROM\\|FROM-first\\|from_first\" tests/ | head", "description": "Check Subquery args, generator and existing FROM-first tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
3182:    def subquery_sql(self, expression: exp.Subquery, sep: str = " AS ") -> str:
3183-        alias = self.sql(expression, "alias")
3184-        alias = f"{sep}{alias}" if alias else ""
3185-        sample = self.sql(expression, "sample")
3186-        if self.dialect.ALIAS_POST_TABLESAMPLE and sample:
3187-            alias = f"{sample}{alias}"
3188-
3189-            # Set to None so it's not generated again by self.query_modi
…[606 chars elided]…
t=True)
3202-
3203-        alias = expression.args.get("alias")
3204-        offset = expression.args.get("offset")
3205-
3206-        if self.UNNEST_WITH_ORDINALITY:
3207-            if alias and isinstance(offset, exp.Expr):
717a50d81 Support FORMAT JSON for JSON_TABLE in Oracle (#7578)
fc32a7bd5 refactor (datatypes): add `from_str` constructor (#7465)
206e2f892 fix(mysql)!: full `MODIFY COLUMN` support. (#7562)
tests/dialects/test_duckdb.py:2351:    def test_from_first_with_parentheses(self):
[assistant] The generator's `query_modifiers` emits joins for a `Subquery`, so attaching them there round-trips. Let me look at the existing FROM-first test and the `Subquery` class.
[tool_use Bash] {"command": "sed -n 2351,2375p tests/dialects/test_duckdb.py; grep -rn \"class Subquery(\" -A 8 sqlglot/expressions/ | head -14; grep -n \"POSITIONAL\" sqlglot/parser.py | head -5", "description": "Read existing FROM-first test and Subquery definition"}
[tool_result]     def test_from_first_with_parentheses(self):
        self.validate_identity(
            "CREATE TABLE t1 AS (FROM t2 SELECT foo1, foo2)",
            "CREATE TABLE t1 AS (SELECT foo1, foo2 FROM t2)",
        )
        self.validate_identity(
            "FROM (FROM t1 SELECT foo1, foo2)",
            "SELECT * FROM (SELECT foo1, foo2 FROM t1)",
        )
        self.validate_identity(
            "WITH t1 AS (FROM (FROM t2 SELECT foo1, foo2)) FROM t1",
            "WITH t1 AS (SELECT * FROM
…[449 chars elided]…
pression, DerivedTable, Query):
sqlglot/expressions/query.py-1663-    is_subquery: t.ClassVar[bool] = True
sqlglot/expressions/query.py-1664-    arg_types = {
sqlglot/expressions/query.py-1665-        "this": True,
sqlglot/expressions/query.py-1666-        "alias": False,
sqlglot/expressions/query.py-1667-        "with_": False,
sqlglot/expressions/query.py-1668-        **QUERY_MODIFIERS,
sqlglot/expressions/query.py-1669-    }
sqlglot/expressions/query.py-1670-
946:        TokenType.POSITIONAL,
[assistant] `Subquery` carries `QUERY_MODIFIERS`, so joins are a valid arg. My fix is to make `_parse_table` honor `joins` for a parenthesized source, the same way it already does for tables at the bottom of the function. Then the `_parse_update` workaround becomes redundant and I'll remove it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122322-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            return su
…[17 chars elided]…
ing": "        if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):\n            if not subquery.args.get(\"pivots\"):\n                subquery.set(\"pivots\", self._parse_pivots())\n            if joins and isinstance(subquery, exp.Subquery):\n                for join in self._parse_joins():\n                    subquery.append(\"joins\", join)\n            return subquery"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122322-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now the UPDATE workaround is redundant, since `_parse_from(joins=True)` consumes the joins itself. I'll remove it.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122322-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py", "old_string": "                from_ = self._parse_from(joins=True)\n                table = from_.this if from_ else None\n                if isinstance(table, exp.Subquery) and self._match(TokenType.JOIN, advance=False):\n                    table.set(\"joins\", list(self._parse_joins()) or None)\n\n                kwargs[\"from_\"] = from_", "new_string": "                kwargs[\"from_\"] = self._parse_from(joins=True)"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122322-duckdb-dialect-from-first-querie/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Next I'll re-run the repro cases, then add a regression test next to the existing FROM-first test in `tests/dialects/test_duckdb.py`.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nqs = ['''from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2''',\n'from (select * from t1) t1 join t2 on true select t1.x',\n'from (select * from t1) t1 positional join t2 select t1.x',\n'from (FROM tbl_1) t1 join (FROM tbl_2) t2 on true select t1.x',\n'from 
…[298 chars elided]…
e-scratch/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.parse_one('from (FROM tbl_1) t1 positional join (FROM tbl_2) t2 select t1.x as x1, t2.x as x2', read='duckdb').sql('duckdb', pretty=True))\nprint(repr(sqlglot.parse_one('update t set a = 1 from (select 1 as b) s join u on true where true', read='duckdb').sql('duckdb')))\n\"", "description": "Re-run repro cases after parser fix"}
[tool_result] OK  SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2
OK  SELECT t1.x FROM (SELECT * FROM t1) AS t1 JOIN t2 ON TRUE
OK  SELECT t1.x FROM (SELECT * FROM t1) AS t1 POSITIONAL JOIN t2
OK  SELECT t1.x FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON TRUE
OK  SELECT * FROM (SELECT * FROM tbl_1) AS t1 JOIN (SELECT * FROM tbl_2) AS t2 ON TRUE
OK  SELECT t1.x FROM t1 JOIN (SELECT * FROM t2) AS t2 ON TRUE
SELECT
  t1.x AS x1,
  t2.x AS x2
FROM (
  SELECT
    *
  FROM tbl_1
) AS t1
POSITIONAL JOIN (
  SELECT
    *
  FROM tbl_2
) AS t2
'UPDATE t SET a = 1 FROM (SELECT 1 AS b) AS s JOIN u ON TRUE WHERE TRUE'
[assistant] All the variants now parse and generate valid SQL, and the UPDATE path still works. I'll add a regression test next to the existing FROM-first test.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-122322-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py", "old_string": "            \"WITH t1 AS (SELECT * FROM (SELECT foo1, foo2 FROM t2)) SELECT * FROM t1\",\n        )\n\n    def test_analyze(self):", "new_string": "            \"WITH t1 AS (SELECT * FROM (SELECT foo1, foo2 
…[193 chars elided]…
2) t2 SELECT t1.x AS x1, t2.x AS x2\",\n            \"SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2\",\n        )\n        self.validate_identity(\n            \"FROM (SELECT * FROM t1) t1 JOIN t2 ON TRUE SELECT t1.x\",\n            \"SELECT t1.x FROM (SELECT * FROM t1) AS t1 JOIN t2 ON TRUE\",\n        )\n\n    def test_analyze(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-122322-duckdb-dialect-from-first-querie/base-1/tests/dialects/test_duckdb.py has been updated successfully.
[assistant] The project's check command is pytest with the given interpreter. I'll run it along with the linter on the changed files, since the new test line is long.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_duckdb.py 2>&1 | tail -3", "description": "Run full test suite and lint changed files"}
[tool_result] .......................... [ 36%]
.................................... [ 40%]
............................ [ 42%]
.......................................... [ 46%]
............................... [ 49%]
................................................................................... [ 56%]
.............................. [ 59%]
................................................................................................................ [ 69%]
.... [ 69%]
.................................................. [ 74%]
............................................. [ 78%]
.................................................................................................................................................. [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1105 passed, 17947 subtests passed in 49.36s
All checks passed!
2 files already formatted
[assistant] All 1105 tests pass and lint/format is clean. I'll check the final diff.
[tool_use Bash] {"command": "git diff --stat && git diff -- sqlglot/parser.py", "description": "Show diff stat and parser diff"}
[tool_result]  sqlglot/parser.py             | 10 ++++------
 tests/dialects/test_duckdb.py | 10 ++++++++++
 2 files changed, 14 insertions(+), 6 deletions(-)
diff --git a/sqlglot/parser.py b/sqlglot/parser.py
index 5a4ed118b..7fb24388e 100644
--- a/sqlglot/parser.py
+++ b/sqlglot/parser.py
@@ -3631,12 +3631,7 @@ class Parser:
             elif self._match(TokenType.RETURNING, advance=False):
                 kwargs["returning"] = self._parse_returning()
             elif self._match(TokenType.FROM, advance=F
…[569 chars elided]…
ance=False):
@@ -4748,6 +4743,9 @@ class Parser:
         if subquery := self._parse_select(table=True, consume_pipe=consume_pipe):
             if not subquery.args.get("pivots"):
                 subquery.set("pivots", self._parse_pivots())
+            if joins and isinstance(subquery, exp.Subquery):
+                for join in self._parse_joins():
+                    subquery.append("joins", join)
             return subquery
 
         bracket = parse_bracket and self._parse_bracket(None)
[assistant] FROM-first queries with joined subqueries now parse. Your example produces `SELECT t1.x AS x1, t2.x AS x2 FROM (SELECT * FROM tbl_1) AS t1 POSITIONAL JOIN (SELECT * FROM tbl_2) AS t2`. The full suite passes (1105 tests), and ruff check and format are clean.

**Cause:** In `_parse_table`, a parenthesized source returns early before the bottom-of-function `if joins:` block. So with `joins=True`, the join after `(FROM tbl_1) t1` was never consumed. The FROM-first path then saw `JOIN` where it expected `SELECT`, fell into the `elif from_:` branch, and left `select ...` unparsed. That's why the error points at `select`. The bug also affected `from (select ...) t1 join ...`, not just `(FROM ...)`.

**Fix (`sqlglot/parser.py`):**
- `_parse_table` now attaches joins to a parenthesized source when `joins=True`.
- `_parse_update` had a workaround for the same gap, attaching joins to a subquery by hand. It's now redundant, so I removed it. UPDATE with a subquery and a join still generates the same SQL.

**Test (`tests/dialects/test_duckdb.py`):** added `test_from_first_with_joined_subqueries` covering your query and a `JOIN ... ON TRUE` variant.

I didn't commit, since you didn't ask for one.
