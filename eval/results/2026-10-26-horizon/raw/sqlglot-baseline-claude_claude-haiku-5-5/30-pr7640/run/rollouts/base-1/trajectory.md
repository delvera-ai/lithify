# trajectory base-1

final message:
`SELECT 1 WINDOW a AS (...)` now parses in SQLite, and the full test suite passes (1106 tests, before I added the new test). I did not commit.

**Cause:** `WINDOW` is in `ID_VAR_TOKENS`, so without a `FROM` the parser read it as an implicit column alias for `1`. Then `a` was an unexpected token, which produced the error at column 17. With a `FROM`, the `WINDOW` keyword was reached in a different position and parsed correctly.

**Fix:** In `sqlglot/parser.py`, `ALIAS_TOKENS` now excludes `TokenType.WINDOW`. `TABLE_ALIAS_TOKENS` already excluded it, so this brings projection aliases in line with table aliases. `SELECT 1 window` with no `AS` no longer takes `window` as an alias; `AS window` still works.

**Test:** Added `test_window_without_from` to `tests/dialects/test_sqlite.py`, which round-trips the query. The SQLite test file passes (12 tests).

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\" sqlglot/parser.py | head -40 && grep -n \"def _parse_query_modifiers\" -A 30 sqlglot/parser.py | head -60", "description": "Locate WINDOW handling in parser"}
[tool_result] 759:        TokenType.WINDOW,
781:        TokenType.WINDOW,
872:        TokenType.WINDOW,
1528:        TokenType.WINDOW: lambda self: ("windows", self._parse_window_clause()),
1655:    WINDOW_EXCLUDE_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
1675:    WINDOW_ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1676:    WINDOW_BEFORE_PAREN_TOKENS: t.ClassVar = {TokenType.OVER}
1677:    WINDOW_SIDES: t.ClassVar = {"FOLLOWING", "PRECEDING"}
8155:        return self._parse_csv(sel
…[1719 chars elided]…
 == "limit":
4129-                            offset = expression.args.get("offset")
4130-                            expression.set("offset", None)
4131-
4132-                            if offset:
4133-                                offset = exp.Offset(expression=offset)
4134-                                this.set("offset", offset)
4135-
4136-                                limit_by_expressions = expression.expressions
4137-                                expression.set("expressions", None)
[tool_use Bash] {"command": "sed -n 4138,4200p sqlglot/parser.py && grep -n \"def _parse_select\" -A 5 sqlglot/parser.py | head -20 && grep -n \"QUERY_MODIFIER_PARSERS\" sqlglot/parser.py | head && grep -n \"_parse_from\\b\\|_parse_from(\" sqlglot/parser.py | head -30", "description": "Inspect query modifier parsing and FROM handling"}
[tool_result]                                 offset.set("expressions", limit_by_expressions)
                        continue
                break

        if self.SUPPORTS_IMPLICIT_UNNEST and this and this.args.get("from_"):
            this = self._implicit_unnests_to_explicit(this)

        return this

    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
        start = self._curr
        while self._curr:
            self._advance()

        end = self._tokens[self._index - 1]
        retur
…[2437 chars elided]…
atch_set(self.QUERY_MODIFIER_PARSERS, advance=False):
4117:                    parser = self.QUERY_MODIFIER_PARSERS[modifier_token.token_type]
1052:        exp.From: lambda self: self._parse_from(joins=True),
3649:                from_ = self._parse_from(joins=True)
3742:            from_ = self._parse_from(joins=True, skip_from_token=True, consume_pipe=True)
3824:            self._parse_from(joins=True, consume_pipe=True)
3899:                from_ = self._parse_from()
4198:    def _parse_from(
[tool_use Bash] {"command": "sed -n 3810,3920p sqlglot/parser.py", "description": "Read select query parsing around FROM"}
[tool_result]             while isinstance(this, exp.Subquery) and this.is_wrapper:
                this = this.this

            assert this is not None
            if "with_" in this.arg_types:
                this.set("with_", cte)
            else:
                self.raise_error(f"{this.key} does not support CTE")
                this = cte

            return this

        # duckdb supports leading with FROM x
        from_ = (
            self._parse_from(joins=True, consume_pipe=True)
            if 
…[3035 chars elided]…
 UNION isn't attached to the subquery by the
            # following call to _parse_set_operations, but instead becomes the parent node
            self._match_r_paren()
            return self._parse_subquery(this, parse_alias=parse_subquery_alias)
        elif self._match(TokenType.VALUES, advance=False):
            this = self._parse_derived_table_values()
        elif from_:
            this = exp.select("*").from_(from_.this, copy=False)
            this = self._parse_query_modifiers(this)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)', 'SELECT x FROM t WINDOW a AS (PARTITION BY fake_column)']:\n    try: print(sqlglot.parse_one(q, read='sqlite').sql('sqlite'))\n    except Exception as e: print('ERR', e)\n\"; grep -n \"MODIFIABLES\" sqlglot/parser.py | head", "description": "Reproduce the WINDOW parse error"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
1751:    MODIFIABLES: t.ClassVar = (exp.Query, exp.Table, exp.TableFromRows, exp.Values)
4108:        if isinstance(this, self.MODIFIABLES):
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)', 'SELECT x FROM t WINDOW a AS (PARTITION BY fake_column)']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite')))\n    except Exception as e: print('ERR', e)\n\"", "description": "Reproduce WINDOW parse with worktree on path"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 17.
  SELECT 1 WINDOW [4ma[0m AS (PARTITION BY fake_column)
Select(
  expressions=[
    Column(
      this=Identifier(this=x, quoted=False))],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))),
  windows=[
    Window(
      this=Identifier(this=a, quoted=False),
      partition_by=[
        Column(
          this=Identifier(this=fake_column, quoted=False))])])
[tool_use Bash] {"command": "sed -n 750,790p sqlglot/parser.py && sed -n 860,880p sqlglot/parser.py && grep -n \"TABLE_ALIAS_TOKENS\\|ALIAS_TOKENS\" sqlglot/parser.py | head -20", "description": "Inspect token sets containing WINDOW"}
[tool_result]         TokenType.TOP,
        TokenType.TRUE,
        TokenType.TRUNCATE,
        TokenType.UNIQUE,
        TokenType.UNNEST,
        TokenType.UNPIVOT,
        TokenType.UPDATE,
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
        
…[1941 chars elided]…
            alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
4828:        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
4956:                any_token=False, tokens=self.UNNEST_OFFSET_ALIAS_TOKENS
5546:        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
8235:        window_alias = self._parse_id_var(any_token=False, tokens=self.WINDOW_ALIAS_TOKENS)
8331:        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
[assistant] WINDOW is in `ID_VAR_TOKENS`, so without a `FROM` the parser takes it as an implicit column alias for `1`. `TABLE_ALIAS_TOKENS` already excludes it; I'll do the same for `ALIAS_TOKENS` and run the suite.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151315-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS\n\n", "new_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.WINDOW}\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151315-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)', 'SELECT SUM(x) OVER a FROM t WINDOW a AS (PARTITION BY y)']:\n    print(sqlglot.parse_one(q, read='sqlite').sql('sqlite'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix and run full test suite"}
[tool_result] SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT SUM(x) OVER a FROM t WINDOW a AS (PARTITION BY y)
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [ 32%]
.......................................... [ 36%]
...........
…[350 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 55.77s
[assistant] The full suite passes (1106 tests). Now I'll add a regression test to the SQLite dialect tests.
[tool_use Bash] {"command": "grep -n \"WINDOW\\|def test_\" tests/dialects/test_sqlite.py | head -30 && grep -n \"validate_identity\" tests/dialects/test_sqlite.py | head -3", "description": "Find SQLite test file structure"}
[tool_result] 10:    def test_sqlite(self):
202:    def test_strftime(self):
225:    def test_datediff(self):
239:    def test_hexadecimal_literal(self):
248:    def test_window_null_treatment(self):
256:    def test_longvarchar_dtype(self):
262:    def test_warnings(self):
271:    def test_trunc(self):
280:    def test_ddl(self):
361:    def test_analyze(self):
365:    def test_create_trigger(self):
11:        self.validate_identity("WITH xyz(x) AS (SELECT 1) SELECT x FROM xyz")
12:        self.validate_identity("SELECT * FROM t AS t INDEXED BY s.i")
13:        self.validate_identity("SELECT * FROM t INDEXED BY s.i")
[tool_use Bash] {"command": "sed -n 246,256p tests/dialects/test_sqlite.py", "description": "View window test in SQLite tests"}
[tool_result]         )

    def test_window_null_treatment(self):
        self.validate_all(
            "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks",
            write={
                "sqlite": "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks"
            },
        )

    def test_longvarchar_dtype(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151315-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_longvarchar_dtype(self):", "new_string": "    def test_window_without_from(self):\n        self.validate_identity(\"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\")\n\n    def test_longvarchar_dtype(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151315-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py 2>&1 | tail -3; git stash list >/dev/null; git diff --stat", "description": "Run SQLite tests and show diff stat"}
[tool_result] .......... [ 83%]
..                                                                      [100%]
12 passed, 63 subtests passed in 0.08s
 sqlglot/parser.py             | 2 +-
 tests/dialects/test_sqlite.py | 3 +++
 2 files changed, 4 insertions(+), 1 deletion(-)
[assistant] `SELECT 1 WINDOW a AS (...)` now parses in SQLite, and the full test suite passes (1106 tests, before I added the new test). I did not commit.

**Cause:** `WINDOW` is in `ID_VAR_TOKENS`, so without a `FROM` the parser read it as an implicit column alias for `1`. Then `a` was an unexpected token, which produced the error at column 17. With a `FROM`, the `WINDOW` keyword was reached in a different position and parsed correctly.

**Fix:** In `sqlglot/parser.py`, `ALIAS_TOKENS` now excludes `TokenType.WINDOW`. `TABLE_ALIAS_TOKENS` already excluded it, so this brings projection aliases in line with table aliases. `SELECT 1 window` with no `AS` no longer takes `window` as an alias; `AS window` still works.

**Test:** Added `test_window_without_from` to `tests/dialects/test_sqlite.py`, which round-trips the query. The SQLite test file passes (12 tests).
