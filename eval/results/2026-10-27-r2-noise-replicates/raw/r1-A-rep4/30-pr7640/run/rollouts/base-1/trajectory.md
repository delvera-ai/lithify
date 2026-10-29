# trajectory base-1

final message:
`SELECT 1 WINDOW a AS (...)` now parses in SQLite, with or without a `FROM`. The full suite passes: 1107 tests, up from 1106 because of the new test.

**Cause:** `WINDOW` is in `ID_VAR_TOKENS`, so `ALIAS_TOKENS` accepted it. The parser read `1 WINDOW` as a column alias, then choked on `a`. With a `FROM`, the table-alias path already excludes `WINDOW`, which is why that form worked.

**Fix:** `sqlglot/parser.py`: `ALIAS_TOKENS` is now `ID_VAR_TOKENS - {TokenType.WINDOW}`, matching `TABLE_ALIAS_TOKENS`.

**Test:** `tests/dialects/test_sqlite.py` gets `test_window_clause_without_from`, covering the no-`FROM` case and the existing `FROM` case.

The change means `WINDOW` can no longer be a bare projection alias, e.g. `SELECT x window FROM t`. Only `AS window` still works as an alias. I searched the existing tests and found no case relying on the bare form. I didn't check other dialects where `WINDOW` may be a legal bare alias; the full suite passing suggests none are covered.

I didn't commit anything.

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\\|_parse_query_modifiers\\|def _parse_select\" sqlglot/parser.py | head -60", "description": "Locate WINDOW and query modifier parsing"}
[tool_result] 759:        TokenType.WINDOW,
781:        TokenType.WINDOW,
872:        TokenType.WINDOW,
1528:        TokenType.WINDOW: lambda self: ("windows", self._parse_window_clause()),
1655:    WINDOW_EXCLUDE_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
1675:    WINDOW_ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
1676:    WINDOW_BEFORE_PAREN_TOKENS: t.ClassVar = {TokenType.OVER}
1677:    WINDOW_SIDES: t.ClassVar = {"FOLLOWING", "PRECEDING"}
2290:        return self._parse_query_m
…[909 chars elided]…
PAREN_TOKENS):
8235:        window_alias = self._parse_id_var(any_token=False, tokens=self.WINDOW_ALIAS_TOKENS)
8252:                self._parse_var_from_options(self.WINDOW_EXCLUDE_OPTIONS)
8286:        if self._match_set(self.WINDOW_BEFORE_PAREN_TOKENS, advance=False):
8305:            "side": self._prev.text if self._match_texts(self.WINDOW_SIDES) else None,
8488:    def _parse_select_or_expression(self, alias: bool = False) -> exp.Expr | None:
8499:        return self._parse_query_modifiers(
[tool_use Bash] {"command": "sed -n 4107,4135p sqlglot/parser.py && echo ---- && sed -n 1515,1535p sqlglot/parser.py && echo ---- && grep -n \"QUERY_MODIFIER_PARSERS\\|_parse_from(\" sqlglot/parser.py | head; echo ----; sed -n 3794,3830p sqlglot/parser.py", "description": "Inspect query modifier parsing code"}
[tool_result]     def _parse_query_modifiers(self, this):
        if isinstance(this, self.MODIFIABLES):
            for join in self._parse_joins():
                this.append("joins", join)
            for lateral in iter(self._parse_lateral, None):
                this.append("laterals", lateral)

            while True:
                if self._match_set(self.QUERY_MODIFIER_PARSERS, advance=False):
                    modifier_token = self._curr
                    parser = self.QUERY_MODIFIER_PARSERS[mo
…[3419 chars elided]…
_" in this.arg_types:
                this.set("with_", cte)
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
[assistant] Let me see how the SELECT path handles the no-FROM case, and reproduce the error first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)', 'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)', 'SELECT 1 WHERE TRUE', 'SELECT 1 GROUP BY 1']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite').sql('sqlite')))\n    except Exception as e: print('ERR', q, e)\n\"; sed -n 3830,3850p sqlglot/parser.py; sed -n 3880,3930p sqlglot/parser.py", "description": "Reproduce the error and read the SELECT parsing path"}
[tool_result] ERR SELECT 1 WINDOW a AS (PARTITION BY fake_column) Invalid expression / Unexpected token. Line 1, Col: 17.
  SELECT 1 WINDOW [4ma[0m AS (PARTITION BY fake_column)
'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)'
'SELECT 1 WHERE TRUE'
'SELECT 1 GROUP BY 1'
            comments = self._prev_comments

            hint = self._parse_hint()

            if self._next and not self._next.token_type == TokenType.DOT:
                all_ = self._match(TokenType.ALL)
                matched_di
…[2008 chars elided]…
= self._parse_query_modifiers(this)
        elif self._match(TokenType.SUMMARIZE):
            table = self._match(TokenType.TABLE)
            this = self._parse_select() or self._parse_string() or self._parse_table()
            return self.expression(exp.Summarize(this=this, table=table))
        elif self._match(TokenType.DESCRIBE):
            this = self._parse_describe()
        else:
            this = None

        return self._parse_set_operations(this) if parse_set_operation else this
[assistant] Reproduced. `SELECT 1 WHERE TRUE` already works, so the modifier loop isn't the problem. My guess is that `WINDOW` is being consumed as a column alias for `1`. Checking the token sets that include `WINDOW`:
[tool_use Bash] {"command": "sed -n 750,160p sqlglot/parser.py; for l in 759 781 872; do echo \"== $l\"; awk -v s=$l 'NR<=s && /^    [A-Z_]+[:=]/ {h=$0} NR==s {print h}' sqlglot/parser.py; done; grep -n \"ALIAS_TOKENS\\b\" sqlglot/parser.py | head -5; grep -n \"TokenType.WINDOW\\|\\\"WINDOW\\\"\" sqlglot/dialects/sqlite.py sqlglot/dialects/dialect.py sqlglot/tokens.py | head", "description": "Find which token sets contain WINDOW"}
[tool_result]         TokenType.TOP,
== 759
    ID_VAR_TOKENS: t.ClassVar[set] = {
== 781
    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
== 872
    FUNC_TOKENS: t.ClassVar = {
772:    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
784:    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS
793:    COMMENT_TABLE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.IS}
795:    UPDATE_ALIAS_TOKENS: t.ClassVar = TABLE_ALIAS_TOKENS - {TokenType.SET}
1675:    WINDOW_ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.RANGE, TokenType.ROWS}
sqlglot/tokens.py:410:        "WINDOW": TokenType.WINDOW,
[assistant] `WINDOW` sits in `ID_VAR_TOKENS`, which makes `ALIAS_TOKENS` include it, so `1 WINDOW` is parsed as an alias. Let me check how `TABLE_ALIAS_TOKENS` avoids this and where the projection alias is parsed.
[tool_use Bash] {"command": "sed -n 770,800p sqlglot/parser.py; grep -n \"def _parse_alias\\|def _parse_expression\\b\\|def _parse_projections\\|def _parse_expressions\" sqlglot/parser.py", "description": "Read alias token sets and alias parsing"}
[tool_result]     } - {TokenType.UNION}

    TABLE_ALIAS_TOKENS: t.ClassVar[set] = ID_VAR_TOKENS - {
        TokenType.ANTI,
        TokenType.ASOF,
        TokenType.FULL,
        TokenType.LEFT,
        TokenType.LOCK,
        TokenType.NATURAL,
        TokenType.RIGHT,
        TokenType.SEMI,
        TokenType.WINDOW,
    }

    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS

    COLON_PLACEHOLDER_TOKENS: t.ClassVar = ID_VAR_TOKENS

    ARRAY_CONSTRUCTORS: t.ClassVar = {
        "ARRAY": exp.Array,
        "LIST
…[199 chars elided]…
ssVar = {"LEADING", "TRAILING", "BOTH"}

    # Tokens that indicate a simple column reference
    IDENTIFIER_TOKENS: t.ClassVar[frozenset] = frozenset({TokenType.VAR, TokenType.IDENTIFIER})
3731:    def _parse_projections(
5098:        def _parse_aliased_expression() -> exp.Expr | None:
5684:    def _parse_expression(self) -> exp.Expr | None:
8308:    def _parse_alias(self, this: exp.Expr | None, explicit: bool = False) -> exp.Expr | None:
8485:    def _parse_expressions(self) -> list[exp.Expr]:
[assistant] `TABLE_ALIAS_TOKENS` already excludes `WINDOW` for exactly this reason, but `ALIAS_TOKENS` does not. The minimal fix is to make `ALIAS_TOKENS` match. Before changing it, I'll check whether any existing test relies on `WINDOW` as a projection alias.
[tool_use Bash] {"command": "grep -rni \"window\" tests/ | grep -i \"select.*[a-z0-9)] window\\b\" | grep -vi \"over\\|partition\" | head; echo ---; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Search tests for WINDOW alias usage and run baseline suite"}
[tool_result] tests/dialects/test_snowflake.py:1016:            "SELECT * FROM foo window",
tests/dialects/test_snowflake.py:1017:            "SELECT * FROM foo AS window",
---
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 50.36s
[assistant] Baseline is green (1106 passed). Applying the change: `ALIAS_TOKENS` gets the same `WINDOW` exclusion that `TABLE_ALIAS_TOKENS` already has.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-181745-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS\n\n", "new_string": "    ALIAS_TOKENS: t.ClassVar = ID_VAR_TOKENS - {TokenType.WINDOW}\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-181745-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)', 'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)', 'SELECT x AS window FROM t']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite').sql('sqlite')))\n    except Exception as e: print('ERR', q, e)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Verify the fix and rerun the full test suite"}
[tool_result] 'SELECT 1 WINDOW a AS (PARTITION BY fake_column)'
'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)'
'SELECT x AS window FROM t'
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 50.27s
[assistant] The fix works and the suite still passes. Per the repo's guidelines, I'll add a regression test to the SQLite dialect tests.
[tool_use Bash] {"command": "grep -n \"def test_\\|WINDOW\\|window\" tests/dialects/test_sqlite.py | head -40; sed -n 1,20p tests/dialects/test_sqlite.py", "description": "Look at SQLite test file structure"}
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
from tests.dialects.test_dialect import Validator

from sqlglot import exp
from sqlglot.helper import logger a
…[243 chars elided]…
")
        self.validate_identity("SELECT * FROM t INDEXED BY s.i")
        self.validate_identity("SELECT * FROM t INDEXED BY i")
        self.validate_identity("SELECT * FROM t NOT INDEXED")
        self.validate_identity("SELECT match FROM t")
        self.validate_identity("SELECT rowid FROM t1 WHERE t1 MATCH 'lorem'")
        self.validate_identity("SELECT RANK() OVER (RANGE CURRENT ROW) FROM tbl")
        self.validate_identity("UNHEX(a, b)")
        self.validate_identity("SELECT DATE()")
[tool_use Bash] {"command": "sed -n 248,256p tests/dialects/test_sqlite.py", "description": "Read the nearby window test"}
[tool_result]     def test_window_null_treatment(self):
        self.validate_all(
            "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks",
            write={
                "sqlite": "SELECT FIRST_VALUE(Name) OVER (PARTITION BY AlbumId ORDER BY Bytes DESC) AS LargestTrack FROM tracks"
            },
        )

    def test_longvarchar_dtype(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-181745-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "    def test_longvarchar_dtype(self):", "new_string": "    def test_window_clause_without_from(self):\n        self.validate_identity(\"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\")\n        self.validate_identity(\"SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)\")\n\n    def test_longvarchar_dtype(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-181745-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git diff --stat", "description": "Run full test suite and show diff stat"}
[tool_result] ............................. [ 87%]
.......................................................................................................................................                                               [100%]
1107 passed, 17999 subtests passed in 50.03s
 sqlglot/parser.py             | 2 +-
 tests/dialects/test_sqlite.py | 4 ++++
 2 files changed, 5 insertions(+), 1 deletion(-)
[assistant] `SELECT 1 WINDOW a AS (...)` now parses in SQLite, with or without a `FROM`. The full suite passes: 1107 tests, up from 1106 because of the new test.

**Cause:** `WINDOW` is in `ID_VAR_TOKENS`, so `ALIAS_TOKENS` accepted it. The parser read `1 WINDOW` as a column alias, then choked on `a`. With a `FROM`, the table-alias path already excludes `WINDOW`, which is why that form worked.

**Fix:** `sqlglot/parser.py`: `ALIAS_TOKENS` is now `ID_VAR_TOKENS - {TokenType.WINDOW}`, matching `TABLE_ALIAS_TOKENS`.

**Test:** `tests/dialects/test_sqlite.py` gets `test_window_clause_without_from`, covering the no-`FROM` case and the existing `FROM` case.

The change means `WINDOW` can no longer be a bare projection alias, e.g. `SELECT x window FROM t`. Only `AS window` still works as an alias. I searched the existing tests and found no case relying on the bare form. I didn't check other dialects where `WINDOW` may be a legal bare alias; the full suite passing suggests none are covered.

I didn't commit anything.
