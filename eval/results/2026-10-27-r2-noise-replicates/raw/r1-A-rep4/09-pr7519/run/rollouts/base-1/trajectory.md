# trajectory base-1

final message:
MySQL now accepts backtick-quoted index and constraint names that match keywords, such as `` UNIQUE KEY `Unique` (a) ``, `` KEY `Index` (b) `` and `` UNIQUE INDEX `Key` (c) ``. The full pytest suite passes (1087 tests), and ruff check and format are clean.

**Root cause:** In `sqlglot/parser.py`, `_parse_unique_key` returned `None` whenever the current token's text matched a `CONSTRAINT_PARSERS` key. That check ignored the token type, so a backtick-quoted `` `Unique` `` was treated as the keyword. I added the same `TokenType.IDENTIFIER` guard that `_parse_unnamed_constraint` already uses.

**Tests:** I added two round-trip cases to `test_ddl` in `tests/dialects/test_mysql.py`. One covers `Unique`, `Index` and `Key` as quoted names. The other covers `Check` and `Primary`.

**Output change:** `KEY` is normalized to `INDEX` on output, so `KEY \`Index\` (b)` round-trips as `INDEX \`Index\` (b)`. The quoted name itself is preserved. This is existing behavior for unquoted `KEY` as well, and I left it alone. If you want `KEY` kept verbatim, that's a separate change.

Unquoted `UNIQUE KEY Unique (a)` still fails to parse. That is correct, since `Unique` is a reserved word in MySQL and needs backticks.

I did not commit anything.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"UNIQUE\\|CONSTRAINT_KEYWORDS\\|INDEX_KEYWORDS\\|KEY\\b\" sqlglot/dialects/mysql.py | head -60 && grep -n \"CONSTRAINT_PARSERS\\|_parse_index_constraint\\|def _parse_unique\\|CONSTRAINT_KEYWORDS\\|def _parse_create\\b\" sqlglot/parser.py | head -40", "description": "Check repo state and find constraint parsing code"}
[tool_result] 86:            "KEY": TokenType.KEY,
1326:    CONSTRAINT_PARSERS: t.ClassVar = {
2330:    def _parse_create(self) -> exp.Create | exp.Command:
7216:        if not procedure_option_follows and self._match_texts(self.CONSTRAINT_PARSERS):
7217:            constraint = self.CONSTRAINT_PARSERS[self._prev.text.upper()](self)
7250:            constraints or self.CONSTRAINT_PARSERS
7255:        if constraint_key not in self.CONSTRAINT_PARSERS:
7258:        result = self.CONSTRAINT_PARSERS[constraint_key](self)
7264:    def _parse_unique_key(self) -> exp.Expr | None:
7265:        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:
7269:    def _parse_unique(self) -> exp.UniqueColumnConstraint:
7389:            and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
[tool_use Bash] {"command": "sed -n 1320,1345p sqlglot/parser.py && sed -n 7200,7300p sqlglot/parser.py && sed -n 7380,7400p sqlglot/parser.py && grep -n \"_parse_index_constraint\\|def _parse_unique_key\\|\\\"KEY\\\"\\|\\\"INDEX\\\"\" sqlglot/parser.py sqlglot/dialects/mysql.py", "description": "Read constraint parsing code in parser"}
[tool_result]         "USING": lambda self: self._parse_property_assignment(exp.FileFormatProperty),
        "UNLOGGED": lambda self: self.expression(exp.UnloggedProperty()),
        "VOLATILE": lambda self: self._parse_volatile_property(),
        "WITH": lambda self: self._parse_with_property(),
    }

    CONSTRAINT_PARSERS: t.ClassVar = {
        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
        "CASESPECIFIC": lambda s
…[5898 chars elided]…
self._match_text_seq("USING", "INDEX", "TABLESPACE")
sqlglot/parser.py:5520:            elif self._match_text_seq("FOR", "KEY", "SHARE"):
sqlglot/parser.py:5522:            elif self._match_text_seq("FOR", "NO", "KEY", "UPDATE"):
sqlglot/parser.py:7264:    def _parse_unique_key(self) -> exp.Expr | None:
sqlglot/parser.py:7270:        self._match_texts(("KEY", "INDEX"))
sqlglot/parser.py:7797:        self._match_text_seq("KEY")
sqlglot/parser.py:8582:        self._match_text_seq("KEY", "DISTKEY")
[assistant] Let me reproduce the failure before changing anything.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a), KEY \\`Index\\` (b), UNIQUE INDEX \\`Key\\` (c))',\n          'CREATE TABLE t (a INT, UNIQUE KEY \\`Check\\` (a))',\n          'CREATE TABLE t (a INT, CONSTRAINT \\`Unique\\` UNIQUE (a))',\n          'CREATE TABLE t (a INT, CONSTRAINT \\`Index\\` UNIQUE (a))']:\n    try: print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\"; grep -n \"def _match_texts\" -A8 sqlglot/parser.py", "description": "Reproduce quoted keyword index name failures"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 56.
  CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY [4m`Unique`[0m (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))
ERR ParseError Expecting ). Line 1, Col: 41.
  CREATE TABLE t (a INT, UNIQUE KEY [4m`Check`[0m (a))
CREATE TABLE t (a INT, CONSTRAINT `Unique` UNIQUE (a))
CREATE TABLE t (a INT, CONSTRAINT `Index` UNIQUE (a))
1927:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1928-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1929-            if advance:
1930-                self._advance()
1931-            return True
1932-        return False
1933-
1934-    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1935-        index = self._index
[assistant] The root cause is `_parse_unique_key`: it checks the current token's text against `CONSTRAINT_PARSERS` without looking at whether the token is a quoted identifier. `_parse_unnamed_constraint` already guards against this with `TokenType.IDENTIFIER`, so I'll apply the same guard here.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165058-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)", "new_string": "        if (\n            self._curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165058-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a), KEY \\`Index\\` (b), UNIQUE INDEX \\`Key\\` (c))',\n          'CREATE TABLE t (a INT, UNIQUE KEY \\`Check\\` (a))',\n          'CREATE TABLE t (a INT, UNIQUE \\`Primary\\` (a))',\n          'CREATE TABLE t (a INT,
…[2 chars elided]…
NIQUE KEY \\`Foreign\\` (a), INDEX \\`Unique\\` (a))',\n          'CREATE TABLE t (a INT, UNIQUE KEY Unique (a))',\n          'CREATE TABLE t (a INT, UNIQUE KEY \\`Unique\\` (a) USING BTREE)']:\n    try: print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\"", "description": "Re-run reproduction cases after the fix"}
[tool_result] CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))
CREATE TABLE t (a INT, UNIQUE `Check` (a))
CREATE TABLE t (a INT, UNIQUE `Primary` (a))
CREATE TABLE t (a INT, UNIQUE `Foreign` (a), INDEX `Unique` (a))
ERR ParseError Expecting ). Line 1, Col: 40.
  CREATE TABLE t (a INT, UNIQUE KEY [4mUnique[0m (a))
CREATE TABLE t (a INT, UNIQUE `Unique` (a) USING BTREE)
[assistant] Quoted names now parse. The one remaining error is for unquoted `Unique`, which is a reserved word in MySQL, so rejecting it is correct. Next I'll add regression tests to the MySQL dialect test file.
[tool_use Bash] {"command": "grep -n \"UNIQUE\\|def test_ddl\\|def test_\" tests/dialects/test_mysql.py | head -80", "description": "Locate test functions in MySQL dialect tests"}
[tool_result] 12:    def test_ddl(self):
19:        self.validate_identity("CREATE TABLE foo (a BIGINT, UNIQUE (b) USING BTREE)")
20:        self.validate_identity("CREATE TABLE foo (a VARCHAR(32) NOT NULL UNIQUE COMMENT 'test')")
37:        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
62:            "CREATE TABLE `oauth_consumer` (`key` VARCHAR(32) NOT NULL, UNIQUE `OAUTH_CONSUMER_KEY` (`key`))"
140:            "CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`id`), 
…[2013 chars elided]…
lf):
1493:    def test_grant(self):
1508:    def test_revoke(self):
1523:    def test_explain(self):
1535:    def test_number_format(self):
1565:    def test_analyze(self):
1575:    def test_utc_time(self):
1581:    def test_mod(self):
1586:    def test_numeric_trunc(self):
1606:    def test_valid_interval_units(self):
1623:    def test_create_trigger(self):
1640:    def test_ignore_respect_nulls(self):
1694:    def test_invisible_column(self):
1701:    def test_alter_table_auto_increment(self):
[tool_use Bash] {"command": "sed -n 18,22p tests/dialects/test_mysql.py && sed -n 160,168p tests/dialects/test_mysql.py", "description": "View context around test_ddl additions"}
[tool_result]         self.validate_identity("CREATE TABLE t (id DECIMAL(20, 4) UNSIGNED)")
        self.validate_identity("CREATE TABLE foo (a BIGINT, UNIQUE (b) USING BTREE)")
        self.validate_identity("CREATE TABLE foo (a VARCHAR(32) NOT NULL UNIQUE COMMENT 'test')")
        self.validate_identity("CREATE TABLE foo (id BIGINT)")
        self.validate_identity("CREATE TABLE 00f (1d BIGINT)")
            "CREATE TABLE `foo` (a VARCHAR(10), KEY idx_a (a DESC))",
            "CREATE TABLE `foo` (a VARCHAR(10), INDEX idx_a (a DESC))",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
        )

        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-165058-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\n            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))\",\n            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n", "new_string":
…[288 chars elided]…
 `Unique` (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))\",\n            \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, UNIQUE KEY `Check` (a), UNIQUE `Primary` (a))\",\n            \"CREATE TABLE t (a INT, UNIQUE `Check` (a), UNIQUE `Primary` (a))\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-165058-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now I'll run the MySQL tests, then the full suite with the project's command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run MySQL tests and full pytest suite"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.27s
................................................... [ 52%]
.......................................................................................................................................................................... [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 49.80s
[assistant] All 1087 tests pass. I'll run the linter on the two changed files, since the new test lines are long.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py            | 6 +++++-
 tests/dialects/test_mysql.py | 8 ++++++++
 2 files changed, 13 insertions(+), 1 deletion(-)
[assistant] MySQL now accepts backtick-quoted index and constraint names that match keywords, such as `` UNIQUE KEY `Unique` (a) ``, `` KEY `Index` (b) `` and `` UNIQUE INDEX `Key` (c) ``. The full pytest suite passes (1087 tests), and ruff check and format are clean.

**Root cause:** In `sqlglot/parser.py`, `_parse_unique_key` returned `None` whenever the current token's text matched a `CONSTRAINT_PARSERS` key. That check ignored the token type, so a backtick-quoted `` `Unique` `` was treated as the keyword. I added the same `TokenType.IDENTIFIER` guard that `_parse_unnamed_constraint` already uses.

**T
…[40 chars elided]…
`test_ddl` in `tests/dialects/test_mysql.py`. One covers `Unique`, `Index` and `Key` as quoted names. The other covers `Check` and `Primary`.

**Output change:** `KEY` is normalized to `INDEX` on output, so `KEY \`Index\` (b)` round-trips as `INDEX \`Index\` (b)`. The quoted name itself is preserved. This is existing behavior for unquoted `KEY` as well, and I left it alone. If you want `KEY` kept verbatim, that's a separate change.

Unquoted `UNIQUE KEY Unique (a)` still fails to parse. That is correct, since `Unique` is a reserved word in MySQL and needs backticks.

I did not commit anything.
