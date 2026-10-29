# trajectory base-1

final message:
A `WINDOW` clause now parses without a `FROM`. `SELECT 1 WINDOW a AS (PARTITION BY fake_column)` parses in SQLite and round-trips unchanged, as do the same query in DuckDB and BigQuery.

**Cause:** `WINDOW` is in the parser's general identifier token set, so in `SELECT 1 WINDOW ...` the parser read `WINDOW` as an implicit column alias for `1`, and then failed at `a`. With a `FROM` the projection list ends before `WINDOW`, which is why that form worked.

**Fix** (`sqlglot/parser.py`): `WINDOW` is now an ambiguous alias token, like `LIMIT`/`OFFSET` already were. It is treated as a clause only when it is followed by `<name> AS`. Otherwise it is still an alias, so `SELECT x window FROM t` and `SELECT * FROM foo window` still work. I renamed the helper `_can_parse_limit_or_offset` to `_can_parse_clause_instead_of_alias` because it now covers `WINDOW` too.

My first version checked for any parseable `WINDOW` clause, which broke `SELECT 1 window FROM t` (it produced `SELECT 1 WINDOW FROM AS t`). The existing tests didn't catch that; the tighter lookahead does.

**Tests:** I added two identity checks to `tests/dialects/test_sqlite.py`: the no-`FROM` window query, and `SELECT 1 AS window FROM t` to cover the alias case. The full suite passes (1106 tests, 17999 subtests), and `ruff check` and `ruff format --check` are clean.

The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -n \"WINDOW\" sqlglot/parser.py | head -50 && grep -n \"_parse_query_modifiers\\|def _parse_select\" sqlglot/parser.py | head", "description": "Find WINDOW handling in parser"}
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
…[195 chars elided]…
E...
sqlglot/parser.py:8252:self._parse_var_from_options(self.WINDOW_EXCLUDE_OPTIONS)
14 matches in 5 files:

4102:0:E) -> E: ...
4105:0:None) -> None: ...
4107:0:
8488:0:bool = False) -> exp.Expr | None:
sqlglot/parser.py:2290:return self._parse_query_modifiers(expression)
sqlglot/parser.py:3751:this = self._parse_query_modifiers(self._parse_set_operations(this))
sqlglot/parser.py:3765:this = self._parse_query_modifiers(self._parse_set_operations(this))
sqlglot/parser.py:3769:def _parse_select(
[tool_use Bash] {"command": "sed -n 3769,3800p sqlglot/parser.py && grep -n \"def _parse_query_modifiers\" -A40 sqlglot/parser.py | head -70", "description": "Read select and query modifier parsing"}
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

      
…[2224 chars elided]…
sion.expressions
4137-                                expression.set("expressions", None)
4138-                                offset.set("expressions", limit_by_expressions)
4139-                        continue
4140-                break
4141-
4142-        if self.SUPPORTS_IMPLICIT_UNNEST and this and this.args.get("from_"):
4143-            this = self._implicit_unnests_to_explicit(this)
4144-
4145-        return this
4146-
4147-    def _parse_hint_fallback_to_string(self) -> exp.Hint | None:
[tool_use Bash] {"command": "sed -n 3800,3900p sqlglot/parser.py | grep -n \"FROM\\|from_\\|WINDOW\\|window\\|_parse_from\\|_parse_where\" ; sed -n 1515,1535p sqlglot/parser.py; grep -n \"_parse_from(\" sqlglot/parser.py | head; grep -n \"def _parse_from\" -A12 sqlglot/parser.py", "description": "Locate FROM and window parsing in select"}
[tool_result] 23:        # duckdb supports leading with FROM x
24:        from_ = (
25:            self._parse_from(joins=True, consume_pipe=True)
26:            if self._match(TokenType.FROM, advance=False)
99:            if not from_:
100:                from_ = self._parse_from()
        "TRY_CAST": lambda self: self._parse_cast(False, safe=True),
        "TRY_CONVERT": lambda self: self._parse_convert(False, safe=True),
        "XMLELEMENT": lambda self: self._parse_xml_element(),
        "XMLTABLE": lamb
…[1261 chars elided]…
ef _parse_from(
4199-        self,
4200-        joins: bool = False,
4201-        skip_from_token: bool = False,
4202-        consume_pipe: bool = False,
4203-    ) -> exp.From | None:
4204-        if not skip_from_token and not self._match(TokenType.FROM):
4205-            return None
4206-
4207-        comments = self._prev_comments
4208-        return self.expression(
4209-            exp.From(this=self._parse_table(joins=joins, consume_pipe=consume_pipe)),
4210-            comments=comments,
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['SELECT 1 WINDOW a AS (PARTITION BY fake_column)', 'SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite')))\n    except Exception as e: print('ERR', e)\n\" ; sed -n 3880,3960p sqlglot/parser.py", "description": "Reproduce the error and view select body"}
[tool_result] ERR Invalid expression / Unexpected token. Line 1, Col: 17.
  SELECT 1 WINDOW [4ma[0m AS (PARTITION BY fake_column)
Select(
  expressions=[
    Literal(this=1, is_string=False)],
  from_=From(
    this=Table(
      this=Identifier(this=t, quoted=False))),
  windows=[
    Window(
      this=Identifier(this=a, quoted=False),
      partition_by=[
        Column(
          this=Identifier(this=fake_column, quoted=False))])])

            this = self.expression(
                exp.Select(
        
…[2358 chars elided]…
ession=self._match_text_seq("SET") and self._parse_id_var(),
                using=self._match_text_seq("USING") and self._parse_id_var(),
            )
        )

    def _parse_with(self, skip_with_token: bool = False) -> exp.With | None:
        if not skip_with_token and not self._match(TokenType.WITH):
            return None

        comments = self._prev_comments
        recursive = self._match(TokenType.RECURSIVE)

        last_comments = None
        expressions = []
        while True:
[assistant] The error is at `a`, not at `WINDOW`, which suggests `WINDOW` is being consumed as a column alias for `1`. Checking the token sets that include `WINDOW`.
[tool_use Bash] {"command": "sed -n 750,790p sqlglot/parser.py; sed -n 865,878p sqlglot/parser.py; grep -n \"TokenType.WINDOW\" sqlglot/dialects/*.py | head; grep -n \"WINDOW\" sqlglot/dialects/sqlite.py", "description": "View token sets containing WINDOW"}
[tool_result ERROR] Exit code 1
        TokenType.TOP,
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
        *SUBQUERY_PREDICAT
…[498 chars elided]…
 t.ClassVar = {
        "ARRAY": exp.Array,
        "LIST": exp.List,
        TokenType.TABLE,
        TokenType.TIMESTAMP,
        TokenType.TIMESTAMPTZ,
        TokenType.TRUNCATE,
        TokenType.UTC_DATE,
        TokenType.UTC_TIME,
        TokenType.UTC_TIMESTAMP,
        TokenType.WINDOW,
        TokenType.XOR,
        *TYPE_TOKENS,
        *SUBQUERY_PREDICATES,
    }

    CONJUNCTION: t.ClassVar[dict[TokenType, type[exp.Expr]]] = {
0 matches for 'TokenType.WINDOW'
0 matches for 'WINDOW'
[assistant] `WINDOW` is in `ID_VAR_TOKENS`, so in a projection list `1 WINDOW` is parsed as an implicit alias. Let me look at the alias logic and check whether any existing test relies on `WINDOW` as an alias.
[tool_use Bash] {"command": "grep -n \"def _parse_alias\" -A40 sqlglot/parser.py | head -60; grep -rn -i \"window\" tests/*.py tests/dialects/*.py | grep -i \"select [^;]* window\\b\" | grep -v \"OVER\\|over (\" | head", "description": "View _parse_alias and window alias tests"}
[tool_result] 5098:        def _parse_aliased_expression() -> exp.Expr | None:
5099-            this = self._parse_select_or_expression()
5100-
5101-            self._match(TokenType.ALIAS)
5102-            alias = self._parse_bitwise()
5103-            if alias:
5104-                if isinstance(alias, exp.Column) and not alias.db:
5105-                    alias = alias.this
5106-                return self.expression(exp.PivotAlias(this=this, alias=alias))
5107-
5108-            return this
5109-
5110-    
…[1832 chars elided]…
L_PAREN):
8322-            aliases = self.expression(
8323-                exp.Aliases(
8324-                    this=this, expressions=self._parse_csv(lambda: self._parse_id_var(any_token))
8325-                ),
tests/dialects/test_bigquery.py:252:            "SELECT * FROM test QUALIFY a IS DISTINCT FROM b WINDOW c AS (PARTITION BY d)"
tests/dialects/test_snowflake.py:1016:            "SELECT * FROM foo window",
tests/dialects/test_snowflake.py:1017:            "SELECT * FROM foo AS window",
[tool_use Bash] {"command": "sed -n 8326,8345p sqlglot/parser.py; grep -n \"_can_parse_limit_or_offset\" -A15 sqlglot/parser.py | sed -n 1,25p; grep -n \"def _parse_projections\\|def _parse_expression\\b\" -A8 sqlglot/parser.py | head -30", "description": "View alias fallback and limit/offset guard"}
[tool_result]                 comments=comments,
            )
            self._match_r_paren(aliases)
            return aliases

        alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
            self.STRING_ALIASES and self._parse_string_as_identifier()
        )

        if alias:
            comments.extend(alias.pop_comments())
            this = self.expression(exp.Alias(this=this, alias=alias), comments=comments)
            column = this.this

            # Moves the comment ne
…[1673 chars elided]…
   def _parse_expression(self) -> exp.Expr | None:
5685-        return self._parse_alias(self._parse_assignment())
5686-
5687-    def _parse_assignment(self) -> exp.Expr | None:
5688-        this = self._parse_disjunction()
5689-        if not this and self._next.token_type in self.ASSIGNMENT:
5690-            # This allows us to parse <non-identifier token> := <expr>
5691-            this = exp.column(
5692-                t.cast(str, self._advance_any(ignore_reserved=True) and self._prev.text)
[assistant] There's an existing precedent: `AMBIGUOUS_ALIAS_TOKENS` with `_can_parse_limit_or_offset`, which lets `LIMIT`/`OFFSET` be a clause instead of an alias when the clause parses. Reading that helper in full.
[tool_use Bash] {"command": "sed -n 5545,5562p sqlglot/parser.py; grep -n \"AMBIGUOUS_ALIAS_TOKENS\" -A3 sqlglot/parser.py sqlglot/dialects/*.py | head -20; grep -n \"def _parse_window_clause\" -A12 sqlglot/parser.py", "description": "View ambiguous alias helper and window clause parser"}
[tool_result]     def _can_parse_limit_or_offset(self) -> bool:
        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
            return False

        index = self._index
        result = bool(
            self._try_parse(self._parse_limit, retreat=True)
            or self._try_parse(self._parse_offset, retreat=True)
        )
        self._retreat(index)

        # MATCH_CONDITION (...) is a special construct that should not be consumed by limit/offset
        if self._next.token_type
…[844 chars elided]…
self._parse_window(self._parse_id_var(), alias=True)
8159-
8160-    def _parse_respect_or_ignore_nulls(self, this: exp.Expr | None) -> exp.Expr | None:
8161-        if self._curr.token_type == TokenType.VAR:
8162-            if self._match_text_seq("IGNORE", "NULLS"):
8163-                return self.expression(exp.IgnoreNulls(this=this))
8164-            if self._match_text_seq("RESPECT", "NULLS"):
8165-                return self.expression(exp.RespectNulls(this=this))
8166-        return this
[assistant] The fix is to let `WINDOW` act as a clause rather than an alias when a window clause actually parses there, mirroring `LIMIT`/`OFFSET`. Checking the helper's call sites before changing it.
[tool_use Bash] {"command": "grep -rn \"_can_parse_limit_or_offset\\|AMBIGUOUS_ALIAS_TOKENS\" sqlglot/ tests/ | cat; grep -n \"def _try_parse\" -A12 sqlglot/parser.py | head -20", "description": "Find all uses of the alias helper"}
[tool_result] Binary file sqlglot/__pycache__/parser.cpython-312.pyc matches
sqlglot/parser.py:1743:    AMBIGUOUS_ALIAS_TOKENS: t.ClassVar = (TokenType.LIMIT, TokenType.OFFSET)
sqlglot/parser.py:4032:        if self._can_parse_limit_or_offset():
sqlglot/parser.py:5545:    def _can_parse_limit_or_offset(self) -> bool:
sqlglot/parser.py:5546:        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):
sqlglot/parser.py:8312:        if self._can_parse_limit_or_offset():
2006:    def _try_parse(self, parse_method: t.Callable[[], T], retreat: bool = False) -> T | None:
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
[assistant] I'll add `WINDOW` to the ambiguous alias tokens and have the helper also check whether a window clause parses at that position. I'm renaming the helper since it no longer only covers LIMIT/OFFSET.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    AMBIGUOUS_ALIAS_TOKENS: t.ClassVar = (TokenType.LIMIT, TokenType.OFFSET)", "new_string": "    AMBIGUOUS_ALIAS_TOKENS: t.ClassVar = (TokenType.LIMIT, TokenType.OFFSET, TokenType.WINDOW)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        if self._can_parse_limit_or_offset():\n            return None", "new_string": "        if self._can_parse_clause_instead_of_alias():\n            return None"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "        if self._can_parse_limit_or_offset():\n            return this\n\n        any_token", "new_string": "        if self._can_parse_clause_instead_of_alias():\n            return this\n\n        any_token"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "    def _can_parse_limit_or_offset(self) -> bool:\n        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):\n            return False\n\n        index = self._index\n        result = bool(\n          
…[174 chars elided]…
tead_of_alias(self) -> bool:\n        if not self._match_set(self.AMBIGUOUS_ALIAS_TOKENS, advance=False):\n            return False\n\n        index = self._index\n        result = bool(\n            self._try_parse(self._parse_limit, retreat=True)\n            or self._try_parse(self._parse_offset, retreat=True)\n            or self._try_parse(self._parse_window_clause, retreat=True)\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[assistant] Now I'll check the repro, several edge cases (the alias forms that must still work), and the full test suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q,d in [('SELECT 1 WINDOW a AS (PARTITION BY fake_column)','sqlite'),('SELECT 1 WINDOW a AS (PARTITION BY x), b AS (ORDER BY y)','sqlite'),('SELECT 1 window','sqlite'),('SELECT x window FROM t','snowflake'),('SELECT * FROM foo window','snowflake'),('SELECT 1 window FROM t','sqlite')]:\n    try: print(q, '->', sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(q, 'ERR', e)\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check repro, alias edge cases, and run test suite"}
[tool_result] SELECT 1 WINDOW a AS (PARTITION BY fake_column) -> SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT 1 WINDOW a AS (PARTITION BY x), b AS (ORDER BY y) -> SELECT 1 WINDOW a AS (PARTITION BY x), b AS (ORDER BY y)
SELECT 1 window -> SELECT 1 AS window
SELECT x window FROM t -> SELECT x
SELECT * FROM foo window -> SELECT * FROM foo AS window
SELECT 1 window FROM t -> SELECT 1 WINDOW FROM AS t
........................... [  8%]
............. [  9%]
...............................................
…[642 chars elided]…
........................................................................... [ 73%]
................................................................................................................................... [ 85%]
............................. [ 87%]
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 47.36s
[assistant] Tests pass, but the edge cases show a regression: `SELECT x window FROM t` silently drops the alias, and `SELECT 1 window FROM t` now produces broken SQL. `_parse_window_clause` accepts a bare `WINDOW` with no name, so the lookahead is too loose. Checking what `_parse_window(alias=True)` requires.
[tool_use Bash] {"command": "grep -n \"    def _parse_window(\" -A30 sqlglot/parser.py | head -45; git stash list | head -0; git show HEAD:sqlglot/parser.py > /tmp/orig_parser_check.txt; ", "description": "Read _parse_window to see alias handling"}
[tool_result] 8179:    def _parse_window(self, this: exp.Expr | None, alias: bool = False) -> exp.Expr | None:
8180-        func = this
8181-        comments = func.comments if isinstance(func, exp.Expr) else None
8182-
8183-        # T-SQL allows the OVER (...) syntax after WITHIN GROUP.
8184-        # https://learn.microsoft.com/en-us/sql/t-sql/functions/percentile-disc-transact-sql?view=sql-server-ver16
8185-        if self._match_text_seq("WITHIN", "GROUP"):
8186-            order = self._parse_wrapped(se
…[1055 chars elided]…
acle-database/19/sqlrf/img_text/first_value.html)
8208-        #   and Snowflake chose to do the same for familiarity
8209-        #   https://docs.snowflake.com/en/sql-reference/functions/first_value.html#usage-notes
head: illegal line count -- 0

thread 'main' (44364065) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
[assistant] `_parse_window` doesn't require `AS`, so the bare `WINDOW` path is too permissive. I'll require the exact shape `WINDOW <name> AS` as the lookahead instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py", "old_string": "            or self._try_parse(self._parse_window_clause, retreat=True)\n        )", "new_string": "            or (\n                self._match(TokenType.WINDOW)\n                and self._parse_id_var()\n                and self._match(TokenType.ALIAS, advance=False)\n            )\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0,'.')\nimport sqlglot\nfor q,d in [('SELECT 1 WINDOW a AS (PARTITION BY fake_column)','sqlite'),('SELECT 1 WINDOW a AS (PARTITION BY x), b AS (ORDER BY y)','sqlite'),('SELECT 1 window','sqlite'),('SELECT x window FROM t','snowflake'),('SELECT * FROM foo window','snowflake')
…[150 chars elided]…
umn)','duckdb'),('SELECT 1 WINDOW a AS (PARTITION BY fake_column)','bigquery')]:\n    try: print(q, '->', sqlglot.transpile(q, read=d, write=d)[0])\n    except Exception as e: print(q, 'ERR', e)\n\" 2>&1; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Recheck edge cases and run full test suite"}
[tool_result] SELECT 1 WINDOW a AS (PARTITION BY fake_column) -> SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT 1 WINDOW a AS (PARTITION BY x), b AS (ORDER BY y) -> SELECT 1 WINDOW a AS (PARTITION BY x), b AS (ORDER BY y)
SELECT 1 window -> SELECT 1 AS window
SELECT x window FROM t -> SELECT x AS window FROM t
SELECT * FROM foo window -> SELECT * FROM foo AS window
SELECT 1 window FROM t -> SELECT 1 AS window FROM t
SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column) -> SELECT 1 FROM t WINDOW a AS (PARTITION BY fake_column)
SELECT 1 WINDOW a AS (PARTITION BY fake_column) -> SELECT 1 WINDOW a AS (PARTITION BY fake_column)
SELECT 1 WINDOW a AS (PARTITION BY fake_column) -> SELECT 1 WINDOW a AS (PARTITION BY fake_column)
.............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 46.45s
[assistant] Behavior is right across the edge cases and the full suite passes. Now I'll add a regression test next to the existing SQLite tests.
[tool_use Bash] {"command": "grep -n \"def test_\\|WINDOW\" tests/dialects/test_sqlite.py | head -30; grep -n \"class TestSQLite\" -A6 tests/dialects/test_sqlite.py", "description": "Look at SQLite test file structure"}
[tool_result] 11 matches in 11 files:

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
7:class TestSQLite(Validator):
8-    dialect = "sqlite"
9-
10-    def test_sqlite(self):
11-        self.validate_identity("WITH xyz(x) AS (SELECT 1) SELECT x FROM xyz")
12-        self.validate_identity("SELECT * FROM t AS t INDEXED BY s.i")
13-        self.validate_identity("SELECT * FROM t INDEXED BY s.i")
[tool_use Bash] {"command": "sed -n 14,16p tests/dialects/test_sqlite.py", "description": "View lines after first identity tests"}
[tool_result]         self.validate_identity("SELECT * FROM t INDEXED BY i")
        self.validate_identity("SELECT * FROM t NOT INDEXED")
        self.validate_identity("SELECT match FROM t")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"SELECT match FROM t\")", "new_string": "        self.validate_identity(\"SELECT match FROM t\")\n        self.validate_identity(\"SELECT 1 WINDOW a AS (PARTITION BY fake_column)\")\n        self.validate_identity(\"SELECT 1 window FROM t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[assistant] `SELECT 1 window FROM t` round-trips as `SELECT 1 AS window FROM t`, so the identity check needs the explicit form.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"SELECT 1 window FROM t\")", "new_string": "        self.validate_identity(\"SELECT 1 AS window FROM t\")"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-190836-sqlite-and-other-dialects-a-wind/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_sqlite.py 2>&1 | tail -2; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_sqlite.py 2>&1 | tail -2; git diff --stat", "description": "Run tests, lint, format check, and diff stat"}
[tool_result] .............................................................................. [ 94%]
........................................................                                                [100%]
1106 passed, 17999 subtests passed in 46.65s
All checks passed!
2 files already formatted
sqlglot/parser.py             | 13 +++++++++----
 tests/dialects/test_sqlite.py |  2 ++
 2 files changed, 11 insertions(+), 4 deletions(-)
[assistant] A `WINDOW` clause now parses without a `FROM`. `SELECT 1 WINDOW a AS (PARTITION BY fake_column)` parses in SQLite and round-trips unchanged, as do the same query in DuckDB and BigQuery.

**Cause:** `WINDOW` is in the parser's general identifier token set, so in `SELECT 1 WINDOW ...` the parser read `WINDOW` as an implicit column alias for `1`, and then failed at `a`. With a `FROM` the projection list ends before `WINDOW`, which is why that form worked.

**Fix** (`sqlglot/parser.py`): `WINDOW` is now an ambiguous alias token, like `LIMIT`/`OFFSET` already were. It is treated as a clause only wh
…[182 chars elided]…
set` to `_can_parse_clause_instead_of_alias` because it now covers `WINDOW` too.

My first version checked for any parseable `WINDOW` clause, which broke `SELECT 1 window FROM t` (it produced `SELECT 1 WINDOW FROM AS t`). The existing tests didn't catch that; the tighter lookahead does.

**Tests:** I added two identity checks to `tests/dialects/test_sqlite.py`: the no-`FROM` window query, and `SELECT 1 AS window FROM t` to cover the alias case. The full suite passes (1106 tests, 17999 subtests), and `ruff check` and `ruff format --check` are clean.

The changes are uncommitted in the worktree.
