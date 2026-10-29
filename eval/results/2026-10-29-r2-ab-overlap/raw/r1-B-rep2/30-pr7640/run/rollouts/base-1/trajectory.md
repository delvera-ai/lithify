# trajectory base-1

final message:
A `WINDOW` clause now parses without a `FROM`. `SELECT 1 WINDOW a AS (PARTITION BY fake_column)` round-trips in SQLite and the base dialect, and the full suite passes (1107 passed).

**Cause:** `WINDOW` is in the parser's `ALIAS_TOKENS`, so in `SELECT 1 WINDOW ...` the parser took `WINDOW` as a column alias for `1` and then failed on `a`. With a `FROM`, the table-alias token set excludes `WINDOW`, which is why that case already worked.

**Fix** (`sqlglot/parser.py`):
- `_parse_alias` now also returns early when the next tokens form a valid window clause. This mirrors the existing LIMIT/OFFSET check.
- The check is a new helper, `_can_parse_window_clause`. It uses `_try_parse` with a retreat, so a plain alias named `window` (e.g. `SELECT 1 AS window`, or `SELECT window FROM t`) still parses as before.

**Test** (`tests/dialects/test_sqlite.py`): added `test_window_clause_without_from`, which checks the window-clause form and the `AS window` alias form.

I did not change the upstream CLAUDE.md-style commit or PR steps; nothing is committed. Ruff check and format pass on both files.

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\" sqlglot/parser.py | head -50; grep -n \"def _parse_query_modifiers\" -A30 sqlglot/parser.py | head -60", "description": "Find WINDOW handling in parser"}
[tool_result] 14 matches in 9 files:

1528:0:lambda self: ("windows", self._parse_window_clause()),
1655:0:t.ClassVar[OPTIONS_TYPE] = {
1675:0:t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1676:0:t.ClassVar = {TokenType.OVER}
1677:0:t.ClassVar = {"FOLLOWING", "PRECEDING"}
8222:0:
8286:0:
8305:0:self._prev.text if self._match_texts(self.WINDOW_SIDES) else None,
sqlglot/parser.py:759:TokenType.WINDOW,
sqlglot/parser.py:781:TokenType.WINDOW,
sqlglot/parser.py:872:TokenType.WINDOW,
sqlglot/parser
…[1513 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"_parse_select\\b\\|def _parse_select\" sqlglot/parser.py | head; sed -n 1440,1460p sqlglot/parser.py | head -5; grep -n \"def _parse_select\" -A5 sqlglot/parser.py | head -20; grep -n \"from_ = \\|self._parse_from\\|FROM\" sqlglot/parser.py | sed -n 1,60p | grep -n \"\" | head -60", "description": "Locate select parsing and FROM handling"}
[tool_result] 21 matches in 5 files:

1070:0:lambda self: self._parse_select(),
1437:0:lambda self: self._parse_select(),
4778:0:= self._parse_select(table=True, consume_pipe=consume_pipe):
8488:0:bool = False) -> exp.Expr | None:
sqlglot/parser.py:2285:expression = self._parse_set_operations(expression) if expression else self._...
sqlglot/parser.py:3699:this=table, lazy=lazy, options=options, expression=self._parse_select(nested=...
sqlglot/parser.py:3744:select = self._parse_select(from_=from_)
sqlglot/par
…[2440 chars elided]…
1:sqlglot/parser.py:5442:from_=self._match(TokenType.FROM) and self._parse_bitwise(),
32:sqlglot/parser.py:7668:self.raise_error("Expected FROM or comma after EXTRACT", self._prev)
33:sqlglot/parser.py:8141:invert_order = self._prev.token_type == TokenType.FROM or self.TRIM_PATTERN_F...
34:sqlglot/parser.py:9465:kind = self._match(TokenType.FROM) or not self._match_text_seq("TO")
35:sqlglot/parser.py:9633:from_=_parse_overlay_arg("FROM"),
36:sqlglot/parser.py:9808:from_ = query.args.get("from_")
[tool_use Bash] {"command": "sed -n 3815,3850p sqlglot/parser.py; sed -n 3895,3910p sqlglot/parser.py; sed -n 8150,8160p sqlglot/parser.py; ls .lithify/harness/scripts/; printf 'SELECT 1 WINDOW a AS (PARTITION BY fake_column)\\nSELECT x FROM t WINDOW a AS (PARTITION BY fake_column)\\n' | <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py 2>&1 | head -30", "description": "Inspect select parsing and run probe script"}
[tool_result]                 this.set("with_", cte)
            else:
                self.raise_error(f"{this.key} does not support CTE")
                this = cte

            return this

        # duckdb supports leading with FROM x
        from_ = (
            self._parse_from(joins=True, consume_pipe=True)
            if self._match(TokenType.FROM, advance=False)
            else None
        )

        if self._match(TokenType.SELECT):
            comments = self._prev_comments

            hint = s
…[1519 chars elided]…
se_named_window(self) -> exp.Expr | None:
        return self._parse_window(self._parse_id_var(), alias=True)

    def _parse_respect_or_ignore_nulls(self, this: exp.Expr | None) -> exp.Expr | None:
probe_parse.py  2.2K
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf 'SELECT 1 WINDOW a AS (PARTITION BY fake_column)\\nSELECT x FROM t WINDOW a AS (PARTITION BY fake_column)\\n' | PYTHONPATH=. $PY .lithify/harness/scripts/probe_parse.py 2>&1 | head -30; sed -n 3850,3895p sqlglot/parser.py", "description": "Run probe script with repo on path"}
[tool_result] ERR       SELECT 1 WINDOW a AS (PARTITION BY fake_column)
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 17.
OK        SELECT x FROM t WINDOW a AS (PARTITION BY fake_column)
          SELECT x FROM t WINDOW a AS (PARTITION BY fake_column)
                    )
                )
                if matched_distinct
                else None
            )

            operation_modifiers = []
            while self._curr and self._match_texts(self.OPERATION_MODIFIERS):
  
…[907 chars elided]…
._parse_projections()

            this = self.expression(
                exp.Select(
                    kind=kind,
                    hint=hint,
                    distinct=distinct,
                    expressions=projections,
                    limit=limit,
                    exclude=exclude,
                    operation_modifiers=operation_modifiers or None,
                )
            )
            this.comments = comments

            into = self._parse_into()
            if into:
[tool_use Bash] {"command": "for l in 759 781 872; do awk -v l=$l 'NR<=l && /^[A-Z_]+ *(=|:)/ {name=$0} NR==l {print l\": \"name}' sqlglot/parser.py; done; grep -n \"ALIAS_TOKENS\\b\" sqlglot/parser.py | head -5; grep -n \"def _parse_projections\" -A12 sqlglot/parser.py | head -20; grep -n \"def _parse_alias\" -A25 sqlglot/parser.py | head -40", "description": "Identify token sets containing WINDOW and alias logic"}
[tool_result] 759: SENTINEL_NONE: Token = Token(TokenType.SENTINEL, "SENTINEL")
781: SENTINEL_NONE: Token = Token(TokenType.SENTINEL, "SENTINEL")
872: SENTINEL_NONE: Token = Token(TokenType.SENTINEL, "SENTINEL")
16 matches in 10 files:

1675:0:t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1694:0:t.ClassVar = TABLE_ALIAS_TOKENS - SET_OPERATIONS
1743:0:t.ClassVar = (TokenType.LIMIT, TokenType.OFFSET)
3731:    def _parse_projections(
3732-        self,
3733-    ) -> tuple[list[exp.Expr], list[ex
…[1854 chars elided]…
  # In some dialects, LIMIT and OFFSET can act as both identifiers and keywords (clauses)
8310-        # so this section tries to parse the clause version and if it fails, it treats the token
8311-        # as an identifier (alias)
8312-        if self._can_parse_limit_or_offset():
8313-            return this
8314-
8315-        any_token = self._match(TokenType.ALIAS)
8316-        comments = self._prev_comments
8317-
8318-        if explicit and not any_token:
8319-            return this
8320-
[tool_use Bash] {"command": "sed -n 8320,8345p sqlglot/parser.py; grep -n \"_can_parse_limit_or_offset\" -A25 sqlglot/parser.py | sed -n 1,40p | grep -v \"^--$\" | head -40; sed -n 1520,1530p sqlglot/parser.py", "description": "Read alias and limit/offset helper logic"}
[tool_result]         if self._match(TokenType.L_PAREN):
            aliases = self.expression(
                exp.Aliases(
                    this=this, expressions=self._parse_csv(lambda: self._parse_id_var(any_token))
                ),
                comments=comments,
            )
            self._match_r_paren(aliases)
            return aliases

        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
            self.STRING_ALIASES and self._parse_string_as_identifier()
      
…[2275 chars elided]…
pe.WHERE: lambda self: ("where", self._parse_where()),
        TokenType.GROUP_BY: lambda self: ("group", self._parse_group()),
        TokenType.HAVING: lambda self: ("having", self._parse_having()),
        TokenType.QUALIFY: lambda self: ("qualify", self._parse_qualify()),
        TokenType.WINDOW: lambda self: ("windows", self._parse_window_clause()),
        TokenType.ORDER_BY: lambda self: ("order", self._parse_order()),
        TokenType.LIMIT: lambda self: ("limit", self._parse_limit()),
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nfrom sqlglot.parser import Parser\nfrom sqlglot.tokens import TokenType as T\nfor n in ['ID_VAR_TOKENS','ALIAS_TOKENS','TABLE_ALIAS_TOKENS','AMBIGUOUS_ALIAS_TOKENS','COLUMN_OPERATORS']:\n    print(n, T.WINDOW in getattr(Parser,n))\n\"; grep -n \"AMBIGUOUS_ALIAS_TOKENS\" sqlglot/parser.py sqlglot/dialects/*.py | head; grep -n \"ALIAS_TOKENS = \" -A3 sqlglot/parser.py | head", "description": "Check which parser token sets contain WINDOW"}
[tool_result] ID_VAR_TOKENS True
ALIAS_TOKENS True
TABLE_ALIAS_TOKENS False
AMBIGUOUS_ALIAS_TOKENS False
COLUMN_OPERATORS False
2 matches in 1 files:

sqlglot/parser.py:1743:AMBIGUOUS_ALIAS_TOKENS: t.ClassVar = (TokenType.LIMIT, TokenType.OFFSET)
sqlglot/parser.py:5546:if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
[tool_use Bash] {"command": "grep -n \"def _try_parse\" -A22 sqlglot/parser.py; sed -n 5557,5566p sqlglot/parser.py; grep -n \"window\" tests/dialects/test_sqlite.py | head", "description": "Read _try_parse helper and existing window tests"}
[tool_result] 2006:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
2007-        index = self._index
2008-        error_level = self.error_level
2009-        this: T | None = None
2010-
2011-        self.error_level = ErrorLevel.IMMEDIATE
2012-        try:
2013-            this = parse_method()
2014-        except ParseError:
2015-            this = None
2016-        finally:
2017-            if not this or retreat:
2018-                self._retreat(index)
2019-  
…[184 chars elided]…
5-        Parses a list of tokens and returns a list of syntax trees, one tree
2026-        per parsed SQL statement.
2027-
2028-        Args:
        if self._next.token_type == TokenType.MATCH_CONDITION:
            result = False

        return result

    def _parse_limit_by(self) -> list[exp.Expr] | None:
        return self._parse_csv(self._parse_bitwise) if self._match_text_seq("BY") else None

    def _parse_locks(self) -> list[exp.Lock]:
        locks = []
1 matches in 1 files:

248:0:
[assistant] I've traced the cause: `WINDOW` is in `ALIAS_TOKENS`, so in `SELECT 1 WINDOW ...` the parser takes `WINDOW` as a column alias for `1` and then fails on `a`. With a `FROM`, the table-alias token set excludes it, which is why that case works. I'll make `_parse_alias` leave a `WINDOW` clause alone when it parses as one.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        if self._can_parse_limit_or_offset():\n            return this\n\n        any_token = self._match(TokenType.ALIAS)\n        comments = self._prev_comments", "new_string": "        if self._can_parse_limit_or_offset() or self._can_parse_window_clause():\n            return this\n\n        any_token = self._match(TokenType.ALIAS)\n        comments = self._prev_comments"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    def _parse_limit_by(self) -> list[exp.Expr] | None:", "new_string": "    def _can_parse_window_clause(self) -> bool:\n        return self._curr.token_type == TokenType.WINDOW and bool(\n            self._try_parse(self._parse_window_clause, retreat=True)\n        )\n\n    def _parse_limit_by(self) -> list[exp.Expr] | None:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; printf 'SELECT 1 WINDOW a AS (PARTITION BY fake_column)\\nSELECT 1 AS window\\nSELECT window FROM t\\nSELECT x FROM t WINDOW a AS (PARTITION BY fake_column)\\n' | PYTHONPATH=. $PY .lithify/harness/scripts/probe_parse.py 2>&1 | head -30; grep -n \"def test\" tests/dialects/test_sqlite.py | head -30; grep -n \"WINDOW\" tests/test_parser.py tests/test_transpile.py tests/test_expressions.py | head", "description": "Re-run probe and find existing test locations"}
[tool_result] OK        SELECT 1 WINDOW a AS (PARTITION BY fake_column)
          SELECT 1 WINDOW a AS (PARTITION BY fake_column)
OK        SELECT 1 AS window
          SELECT 1 AS window
OK        SELECT window FROM t
          SELECT window FROM t
OK        SELECT x FROM t WINDOW a AS (PARTITION BY fake_column)
          SELECT x FROM t WINDOW a AS (PARTITION BY fake_column)
11 matches in 11 files:

10:0:
202:0:
225:0:
239:0:
248:0:
256:0:
262:0:
271:0:
280:0:
361:0:
365:0:
0 matches for 'WINDOW'
[assistant] The fix works for all four cases. Now I'll add a regression test next to the existing SQLite tests.
[tool_use Bash] {"command": "sed -n 236,262p tests/dialects/test_sqlite.py", "description": "View nearby SQLite test methods"}
[tool_result]             write={"sqlite": "CAST((JULIANDAY(a) - JULIANDAY(b)) / 365.0 AS INTEGER)"},
        )

    def test_hexadecimal_literal(self):
        self.validate_all(
            "SELECT 0XCC",
            write={
                "sqlite": "SELECT x'CC'",
                "mysql": "SELECT x'CC'",
            },
        )

    def test_window_null_treatment(self):
        self.validate_all(
            "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks",
            write={
                "sqlite": "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks"
            },
        )

    def test_longvarchar_dtype(self):
        self.validate_all(
            "CREATE TABLE foo (bar LONGVARCHAR)",
            write={"sqlite": "CREATE TABLE foo (bar TEXT)"},
        )

    def test_warnings(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_longvarchar_dtype(self):", "new_string": "    def test_window_clause_without_from(self):\n        self.validate_identity(\"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\")\n        self.validate_identity(\"SELECT 1 AS window\")\n\n    def test_longvarchar_dtype(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153235-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run SQLite tests then full test suite", "timeout": 300000}
[tool_result] .......... [ 83%]
..                                                                      [100%]
12 passed, 63 subtests passed in 0.14s
............................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.......................................................................................................................................                                               [100%]
1107 passed, 17999 subtests passed in 47.76s
[tool_use Bash] {"command": "(ruff check sqlglot/parser.py tests/dialects/test_sqlite.py && ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py) 2>&1 | tail -4; git diff --stat", "description": "Lint changed files and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
sqlglot/parser.py             | 7 ++++++-
 tests/dialects/test_sqlite.py | 4 ++++
 2 files changed, 10 insertions(+), 1 deletion(-)
[assistant] A `WINDOW` clause now parses without a `FROM`. `SELECT 1 WINDOW a AS (PARTITION BY fake_column)` round-trips in SQLite and the base dialect, and the full suite passes (1107 passed).

**Cause:** `WINDOW` is in the parser's `ALIAS_TOKENS`, so in `SELECT 1 WINDOW ...` the parser took `WINDOW` as a column alias for `1` and then failed on `a`. With a `FROM`, the table-alias token set excludes `WINDOW`, which is why that case already worked.

**Fix** (`sqlglot/parser.py`):
- `_parse_alias` now also returns early when the next tokens form a valid window clause. This mirrors the existing LIMIT/OFFSET check.
- The check is a new helper, `_can_parse_window_clause`. It uses `_try_parse` with a retreat, so a plain alias named `window` (e.g. `SELECT 1 AS window`, or `SELECT window FROM t`) still parses as before.

**Test** (`tests/dialects/test_sqlite.py`): added `test_window_clause_without_from`, which checks the window-clause form and the `AS window` alias form.

I did not change the upstream CLAUDE.md-style commit or PR steps; nothing is committed. Ruff check and format pass on both files.
