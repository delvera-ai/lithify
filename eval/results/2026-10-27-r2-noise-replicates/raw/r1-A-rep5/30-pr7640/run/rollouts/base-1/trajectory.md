# trajectory base-1

final message:
`SELECT 1 WINDOW a AS (...)` now parses, with or without a `FROM` clause.

**Cause:** `WINDOW` is in the identifier token set, so the parser read it as an implicit column alias for `1` (`SELECT 1 WINDOW`) and then failed on `a`. With a `FROM`, the alias step never sees `WINDOW`, which is why that form worked.

**Fix:** In `_parse_alias` (`sqlglot/parser.py`), I added a guard alongside the existing LIMIT/OFFSET one. If the next token is `WINDOW` and it parses as a window clause, the alias parser leaves it alone. This is a lookahead with retreat, so `SELECT 1 AS window`, `SELECT 1 window` and `SELECT window FROM t` still produce the same output as before.

**Test:** I added `test_window_clause_without_from` to `tests/dialects/test_sqlite.py`. It is an identity round-trip for the reported query.

**Results:**
- The full suite passes: 1106 tests, 17999 subtests, run with the project's pytest command.
- `ruff check` and `ruff format --check` pass on both changed files.

I didn't commit anything. The changes are in the working tree.

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\\|_parse_query_modifiers\\|def _parse_select\" sqlglot/parser.py | head -60", "description": "Find WINDOW and query modifier parsing code"}
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
[tool_use Bash] {"command": "sed -n 4107,4135p sqlglot/parser.py && echo ---- && sed -n 3880,3925p sqlglot/parser.py && echo ---- && sed -n 1520,1530p sqlglot/parser.py", "description": "Show query modifier and select parsing code"}
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
…[2815 chars elided]…
pe.WHERE: lambda self: ("where", self._parse_where()),
        TokenType.GROUP_BY: lambda self: ("group", self._parse_group()),
        TokenType.HAVING: lambda self: ("having", self._parse_having()),
        TokenType.QUALIFY: lambda self: ("qualify", self._parse_qualify()),
        TokenType.WINDOW: lambda self: ("windows", self._parse_window_clause()),
        TokenType.ORDER_BY: lambda self: ("order", self._parse_order()),
        TokenType.LIMIT: lambda self: ("limit", self._parse_limit()),
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)','SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)','SELECT 1 WHERE TRUE','SELECT 1 LIMIT 1']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite').sql('sqlite')))\n    except Exception as e: print('ERR', q, e)\n\"; sed -n 3836,3850p sqlglot/parser.py; sed -n 8150,8160p sqlglot/parser.py", "description": "Reproduce the WINDOW parse error and inspect code"}
[tool_result] ERR SELECT 1 WINDOW a AS (PARTITION BY fake_column) Invalid expression / Unexpected token. Line 1, Col: 17.
  SELECT 1 WINDOW [4ma[0m AS (PARTITION BY fake_column)
'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)'
'SELECT 1 WHERE TRUE'
'SELECT 1 LIMIT 1'
                matched_distinct = self._match_set(self.DISTINCT_TOKENS)
            else:
                all_, matched_distinct = None, False

            kind = (
                self._prev.text.upper()
                if self._match
…[341 chars elided]…
turn self.expression(
            exp.Trim(this=this, position=position, expression=expression, collation=collation)
        )

    def _parse_window_clause(self) -> list[exp.Expr] | None:
        return self._parse_csv(self._parse_named_window) if self._match(TokenType.WINDOW) else None

    def _parse_named_window(self) -> exp.Expr | None:
        return self._parse_window(self._parse_id_var(), alias=True)

    def _parse_respect_or_ignore_nulls(self, this: exp.Expr | None) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 750,760p sqlglot/parser.py; echo ----; sed -n 776,783p sqlglot/parser.py; echo ----; sed -n 866,874p sqlglot/parser.py; echo ----; grep -n \"TABLE_ALIAS_TOKENS\\|ALIAS_TOKENS = \\|COMMENT_TABLE_ALIAS\\|def _parse_expression\\b\\|def _parse_alias\" sqlglot/parser.py | head; grep -rn \"WINDOW\" sqlglot/dialects/sqlite.py sqlglot/dialects/dialect.py | head", "description": "Inspect token sets containing WINDOW"}
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
----
        TokenType.LEFT,
        TokenType.LOCK,
        TokenType.NATURAL,
        TokenType.RIGHT,
        TokenType.SEMI,
        TokenType.WINDOW,
    }

----
        TokenType.TIMESTAMP,
        Toke
…[521 chars elided]…
IONS
2191:            this = self._parse_table(alias_tokens=self.COMMENT_TABLE_ALIAS_TOKENS)
4037:            self._parse_id_var(any_token=any_token, tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
4757:                        alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS
4828:        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
5098:        def _parse_aliased_expression() -> exp.Expr | None:
5684:    def _parse_expression(self) -> exp.Expr | None:
[tool_use Bash] {"command": "sed -n 770,796p sqlglot/parser.py; echo ----; grep -n \"ALIAS_TOKENS\\b\" sqlglot/parser.py | head -20; grep -n \"def _parse_alias\" -A12 sqlglot/parser.py | head -30", "description": "Inspect alias token sets and _parse_alias"}
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
…[2173 chars elided]…
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
[tool_use Bash] {"command": "grep -n \"def _can_parse_limit_or_offset\" -A25 sqlglot/parser.py; sed -n 8320,8345p sqlglot/parser.py", "description": "Show limit/offset lookahead and alias parsing"}
[tool_result] 5545:    def _can_parse_limit_or_offset(self) -> bool:
5546-        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
5547-            return False
5548-
5549-        index = self._index
5550-        result = bool(
5551-            self._try_parse(self._parse_limit, retreat=True)
5552-            or self._try_parse(self._parse_offset, retreat=True)
5553-        )
5554-        self._retreat(index)
5555-
5556-        # MATCH_CONDITION (...) is a special construct that should not 
…[984 chars elided]…
) or (
            self.STRING_ALIASES and self._parse_string_as_identifier()
        )

        if alias:
            comments.extend(alias.pop_comments())
            this = self.expression(exp.Alias(this=this, alias=alias), comments=comments)
            column = this.this

            # Moves the comment next to the alias in `expr /* comment */ AS alias`
            if not this.comments and column and column.comments:
                this.comments = column.pop_comments()

        return this
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105046-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        if self._can_parse_limit_or_offset():\n            return this\n\n        any_token = self._match(TokenType.ALIAS)", "new_string": "        if self._can_parse_limit_or_offset():\n            return this\n\n        # A WINDOW clause can directly follow a select list when there's no FROM clause\n        if self._match(TokenType.WINDOW, advance=False) and self._try_parse(\n            self._parse_window_clause, retreat=True\n        ):\n            return this\n\n        any_token = self._match(TokenType.ALIAS)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105046-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)','SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)','SELECT 1 AS window','SELECT window FROM t','SELECT 1 window']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite').sql('sqlite')))\n    except Exception as e: print('ERR', q, e)\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix on repro cases and run full test suite"}
[tool_result] 'SELECT 1 WINDOW a AS (PARTITION BY fake_column)'
'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)'
'SELECT 1 AS window'
'SELECT window FROM t'
'SELECT 1 AS window'
........................... [  8%]
............. [  9%]
........................................................................................................................................ [ 21%]
............................................................................................ [ 30%]
.......................... [
…[417 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 54.00s
[tool_use Bash] {"command": "grep -n \"WINDOW\" tests/dialects/test_sqlite.py tests/test_parser.py | head; grep -n \"def test_\" tests/dialects/test_sqlite.py | tail -3; tail -5 tests/dialects/test_sqlite.py", "description": "Find existing WINDOW tests and test file end"}
[tool_result] 280:    def test_ddl(self):
361:    def test_analyze(self):
365:    def test_create_trigger(self):

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view BEGIN INSERT INTO employees (id, name, department) VALUES (NEW.id, NEW.name, NEW.department) END",
            check_command_warning=True,
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_sqlite.py <<'EOF'\n\n    def test_window_clause_without_from(self):\n        self.validate_identity(\n            \"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\",\n            \"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\",\n        )\nEOF\n<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --c
…[56 chars elided]…
sers/user/.cache/lithify-dev/r2-noise-scratch/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_sqlite.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py 2>&1 | tail -2; git status --short", "description": "Add regression test and run sqlite tests plus lint"}
[tool_result] .......... [ 83%]
..                                                                      [100%]
12 passed, 63 subtests passed in 0.08s
All checks passed!
2 files already formatted
 M sqlglot/parser.py
 M tests/dialects/test_sqlite.py
[assistant] `SELECT 1 WINDOW a AS (...)` now parses, with or without a `FROM` clause.

**Cause:** `WINDOW` is in the identifier token set, so the parser read it as an implicit column alias for `1` (`SELECT 1 WINDOW`) and then failed on `a`. With a `FROM`, the alias step never sees `WINDOW`, which is why that form worked.

**Fix:** In `_parse_alias` (`sqlglot/parser.py`), I added a guard alongside the existing LIMIT/OFFSET one. If the next token is `WINDOW` and it parses as a window clause, the alias parser leaves it alone. This is a lookahead with retreat, so `SELECT 1 AS window`, `SELECT 1 window` and `SELECT window FROM t` still produce the same output as before.

**Test:** I added `test_window_clause_without_from` to `tests/dialects/test_sqlite.py`. It is an identity round-trip for the reported query.

**Results:**
- The full suite passes: 1106 tests, 17999 subtests, run with the project's pytest command.
- `ruff check` and `ruff format --check` pass on both changed files.

I didn't commit anything. The changes are in the working tree.
