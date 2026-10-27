# trajectory base-1

final message:
Quoted index and constraint names that look like keywords now parse and round-trip. `` UNIQUE KEY `Unique` (a) ``, `` KEY `Index` (b) `` and `` UNIQUE INDEX `Key` (c) `` all work. The full test suite passes (1087 tests), and ruff lint and format are clean on the changed files.

**Cause:** Two spots in `sqlglot/parser.py` treated any token whose text matched a keyword as that keyword, even when it was a quoted identifier:
- `_parse_unique_key` refused to read the index name when its text was `UNIQUE`, `KEY`, `INDEX` and so on, so `` `Unique` `` was dropped and the parse failed.
- `_parse_unique` consumed a quoted `` `Key` `` as the optional `KEY`/`INDEX` keyword, so `` UNIQUE `Key` (c) `` would lose the name.

**Fix:** Both checks now skip tokens of type `IDENTIFIER`. Unquoted keywords behave exactly as before. The change is in `sqlglot/parser.py` (`_parse_unique_key` and `_parse_unique`).

**Tests:** I added four cases to `tests/dialects/test_mysql.py`, next to the existing `UNIQUE INDEX idx_a` test: `UNIQUE KEY `Unique``, `KEY `Index``, `UNIQUE INDEX `Key``, and `UNIQUE `Key``.

Two existing MySQL normalizations are unchanged and visible in the output. `KEY` is rewritten to `INDEX`, and the `KEY` or `INDEX` keyword is dropped from `UNIQUE KEY ...`. The quoted names themselves are preserved. I left these alone because existing tests depend on them.

I haven't committed anything. Say if you want a commit with the Haiku co-author line.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"UNIQUE\\|INDEX\\|KEY\\b\" sqlglot/dialects/mysql.py | head -80", "description": "Check status and grep MySQL index handling"}
[tool_result] 86:            "KEY": TokenType.KEY,
[tool_use Bash] {"command": "grep -n \"_parse_index_constraint\\|CONSTRAINT_PARSERS\\|def _parse_unique\\|INDEX_CONSTRAINT\\|\\\"UNIQUE\\\"\\|\\\"KEY\\\"\\|TokenType.KEY\\|TokenType.UNIQUE\\|TokenType.INDEX\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -60", "description": "Locate index and constraint parsing code"}
[tool_result] sqlglot/dialects/mysql.py:86:            "KEY": TokenType.KEY,
sqlglot/parser.py:630:        TokenType.INDEX,
sqlglot/parser.py:644:        TokenType.INDEX,
sqlglot/parser.py:738:        TokenType.UNIQUE,
sqlglot/parser.py:827:        TokenType.INDEX,
sqlglot/parser.py:1326:    CONSTRAINT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1382:        "UNIQUE": lambda self: self._parse_unique(),
sqlglot/parser.py:1448:        "UNIQUE",
sqlglot/parser.py:1553:    PRE_VOLATILE_TOKENS: t.ClassVar = {TokenTy
…[1905 chars elided]…
atch_texts(("KEY", "INDEX"))
sqlglot/parser.py:7389:            and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
sqlglot/parser.py:7797:        self._match_text_seq("KEY")
sqlglot/parser.py:7861:        if self._match_text_seq("WITH", "UNIQUE"):
sqlglot/parser.py:7863:        elif self._match_text_seq("WITHOUT", "UNIQUE"):
sqlglot/parser.py:8582:        self._match_text_seq("KEY", "DISTKEY")
sqlglot/parser.py:8742:        if self._match(TokenType.TABLE) or self._match(TokenType.INDEX):
[tool_use Bash] {"command": "sed -n 7200,7300p sqlglot/parser.py && sed -n 7370,7400p sqlglot/parser.py && sed -n 1320,1330p sqlglot/parser.py", "description": "Read constraint parsing helpers in parser"}
[tool_result]         if self._match_text_seq("FOR", "REPLICATION"):
            return self.expression(exp.NotForReplicationColumnConstraint())

        # Unconsume the `NOT` token
        self._retreat(self._index - 1)
        return None

    def _parse_column_constraint(self) -> exp.Expr | None:
        this = self._parse_id_var() if self._match(TokenType.CONSTRAINT) else None

        procedure_option_follows = (
            self._match(TokenType.WITH, advance=False)
            and self._next
          
…[4471 chars elided]…
lf.expression(exp.UnloggedProperty()),
        "VOLATILE": lambda self: self._parse_volatile_property(),
        "WITH": lambda self: self._parse_with_property(),
    }

    CONSTRAINT_PARSERS: t.ClassVar = {
        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
        "CASESPECIFIC": lambda self: self.expression(exp.CaseSpecificColumnConstraint(not_=False)),
        "CHARACTER SET": lambda self: self.expression(
[assistant] Let me reproduce the failure before changing anything.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nfor sql in ['CREATE TABLE t (a INT, UNIQUE KEY \\`Unique\\` (a))','CREATE TABLE t (b INT, KEY \\`Index\\` (b))','CREATE TABLE t (c INT, UNIQUE INDEX \\`Key\\` (c))','CREATE TABLE t (a INT, CONSTRAINT \\`Unique\\` UNIQUE (a))','CREATE TABLE t (a INT, CONSTRAINT \\`Index\\` UNIQUE (a))']:\n    try: print(sqlglot.transpile(sql, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', sql, '->', type(e).__name__, str(e).splitlines()[0])\n\" 2>&1 | tail -20", "description": "Reproduce quoted keyword index name failures"}
[tool_result] ERR CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a)) -> ParseError Expecting ). Line 1, Col: 42.
CREATE TABLE t (b INT, INDEX `Index` (b))
ERR CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c)) -> ParseError Expecting ). Line 1, Col: 41.
CREATE TABLE t (a INT, CONSTRAINT `Unique` UNIQUE (a))
CREATE TABLE t (a INT, CONSTRAINT `Index` UNIQUE (a))
[assistant] Reproduced: `UNIQUE KEY `Unique``, and `UNIQUE INDEX `Key`` fail. Let me check how `_match_texts` and `_parse_id_var` treat quoted tokens before choosing the fix.
[tool_use Bash] {"command": "grep -n \"def _match_texts\" -A8 sqlglot/parser.py && grep -n \"_parse_unique_key\\|_parse_unique()\" sqlglot/parser.py sqlglot/dialects/*.py", "description": "Inspect _match_texts and _parse_unique_key usages"}
[tool_result] 1927:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1928-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1929-            if advance:
1930-                self._advance()
1931-            return True
1932-        return False
1933-
1934-    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1935-        index = self._index
sqlglot/parser.py:1382:        "UNIQUE": lambda self: self._parse_unique(),
sqlglot/parser.py:7264:    def _parse_unique_key(self) -> exp.Expr | None:
sqlglot/parser.py:7274:                this=self._parse_schema(self._parse_unique_key()),
[assistant] The root cause is clear: `_parse_unique_key` checks the token's text against `CONSTRAINT_PARSERS` without excluding quoted identifiers, so `` `Unique` `` is treated as the `UNIQUE` keyword and the index name is dropped. `_match_texts` has the same gap, so `UNIQUE `Key` (c)` would silently swallow the name as the `KEY` keyword. Let me read the exact lines and fix both.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160759-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "offset": 7263, "limit": 12}
[tool_result] 7263	
7264	    def _parse_unique_key(self) -> exp.Expr | None:
7265	        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:
7266	            return None
7267	        return self._parse_id_var(any_token=False)
7268	
7269	    def _parse_unique(self) -> exp.UniqueColumnConstraint:
7270	        self._match_texts(("KEY", "INDEX"))
7271	        return self.expression(
7272	            exp.UniqueColumnConstraint(
7273	                nulls=self._match_text_seq("NULLS", "NOT", "DISTINCT"),
7274	                this=self._parse_schema(self._parse_unique_key()),
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160759-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "    def _parse_unique_key(self) -> exp.Expr | None:\n        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)\n\n    def 
…[202 chars elided]…
curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)\n\n    def _parse_unique(self) -> exp.UniqueColumnConstraint:\n        if self._curr.token_type != TokenType.IDENTIFIER:\n            self._match_texts((\"KEY\", \"INDEX\"))"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160759-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nfor sql in ['CREATE TABLE t (a INT, UNIQUE KEY \\`Unique\\` (a))','CREATE TABLE t (b INT, KEY \\`Index\\` (b))','CREATE TABLE t (c INT, UNIQUE INDEX \\`Key\\` (c))','CREATE TABLE t (c INT, UNIQUE \\`Key\\` (c))','CREATE TABLE t (c INT, UNIQUE KEY \\`Key\\` (c))','CREATE TABLE t (a INT, UNIQUE KEY unique_idx (a))','CREATE TABLE t (a INT, UNIQUE KEY \\`primary\\` (a))','CREATE TABLE t (a INT, UNIQUE (a))','CREATE TABLE t (a INT UNIQUE PRIMARY KEY)']:\n    try: print(sqlglot.transpile(sql, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', sql, '->', type(e).__name__, str(e).splitlines()[0])\n\" 2>&1 | tail -20", "description": "Verify fix on quoted and unquoted index names"}
[tool_result] CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (b INT, INDEX `Index` (b))
CREATE TABLE t (c INT, UNIQUE `Key` (c))
CREATE TABLE t (c INT, UNIQUE `Key` (c))
CREATE TABLE t (c INT, UNIQUE `Key` (c))
CREATE TABLE t (a INT, UNIQUE unique_idx (a))
CREATE TABLE t (a INT, UNIQUE `primary` (a))
CREATE TABLE t (a INT, UNIQUE (a))
CREATE TABLE t (a INT UNIQUE PRIMARY KEY)
[assistant] All the quoted cases now parse and keep their names, and unquoted names are unaffected. Next I'll add a regression test to the MySQL dialect tests.
[tool_use Bash] {"command": "grep -n \"UNIQUE KEY\\|UNIQUE INDEX\\|KEY \\`\\|def test_ddl\" tests/dialects/test_mysql.py | head -30", "description": "Find existing DDL/unique key tests in MySQL tests"}
[tool_result] 12:    def test_ddl(self):
107:        self.validate_identity("CREATE TABLE test (id INT, PRIMARY KEY `pk_name` (id))")
110:            "CREATE TABLE test (id INT, PRIMARY KEY `pk_name` (id))",
136:            "ALTER TABLE t ADD KEY `i` (`c`)",
140:            "CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`id`), UNIQUE KEY `id` (`id`))",
144:            "CREATE TABLE IF NOT EXISTS industry_info (a BIGINT(20) NOT NULL AUTO_INCREMENT, b BIGINT(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE KEY d (b), KEY e (b))",
164:            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
[tool_use Bash] {"command": "sed -n 104,170p tests/dialects/test_mysql.py", "description": "Read nearby MySQL DDL test cases"}
[tool_result]             "CREATE TABLE test_table (id INT AUTO_INCREMENT, PRIMARY KEY (id) USING HASH)"
        )
        self.validate_identity("CREATE TABLE test (id INT, PRIMARY KEY pk_name (id))")
        self.validate_identity("CREATE TABLE test (id INT, PRIMARY KEY `pk_name` (id))")
        self.validate_identity(
            'CREATE TABLE test (id INT, PRIMARY KEY "pk_name" (id))',
            "CREATE TABLE test (id INT, PRIMARY KEY `pk_name` (id))",
        )
        self.validate_identity("CREATE TA
…[2530 chars elided]…
utf8 ROW_FORMAT=DYNAMIC",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), KEY idx_a (a DESC))",
            "CREATE TABLE `foo` (a VARCHAR(10), INDEX idx_a (a DESC))",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
        )

        self.validate_all(
            "insert into t(i) values (default)",
            write={
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261026-160759-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n\n        self.validate_all(", "new_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )
…[237 chars elided]…
a INT, KEY `Index` (a))\",\n            \"CREATE TABLE t (a INT, INDEX `Index` (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, UNIQUE INDEX `Key` (a))\",\n            \"CREATE TABLE t (a INT, UNIQUE `Key` (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, UNIQUE `Key` (a))\",\n        )\n\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261026-160759-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now I'll run the project's test command, plus the MySQL and full suite.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>&1; PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run MySQL tests and full project test suite", "timeout": 900000}
[tool_result] <work>/env-sqlglot/bin/python
.............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.69s
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
.........................
…[470 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 58.78s
[assistant] The full suite passes (1087 tests). I'll run the linter and formatter on the changed files and review the diff.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ($PY -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py && $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Run ruff lint/format checks and show diff stat"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py            |  9 +++++++--
 tests/dialects/test_mysql.py | 15 +++++++++++++++
 2 files changed, 22 insertions(+), 2 deletions(-)
[assistant] Quoted index and constraint names that look like keywords now parse and round-trip. `` UNIQUE KEY `Unique` (a) ``, `` KEY `Index` (b) `` and `` UNIQUE INDEX `Key` (c) `` all work. The full test suite passes (1087 tests), and ruff lint and format are clean on the changed files.

**Cause:** Two spots in `sqlglot/parser.py` treated any token whose text matched a keyword as that keyword, even when it was a quoted identifier:
- `_parse_unique_key` refused to read the index name when its text was `UNIQUE`, `KEY`, `INDEX` and so on, so `` `Unique` `` was dropped and the parse failed.
- `_parse_unique
…[257 chars elided]…
` (`_parse_unique_key` and `_parse_unique`).

**Tests:** I added four cases to `tests/dialects/test_mysql.py`, next to the existing `UNIQUE INDEX idx_a` test: `UNIQUE KEY `Unique``, `KEY `Index``, `UNIQUE INDEX `Key``, and `UNIQUE `Key``.

Two existing MySQL normalizations are unchanged and visible in the output. `KEY` is rewritten to `INDEX`, and the `KEY` or `INDEX` keyword is dropped from `UNIQUE KEY ...`. The quoted names themselves are preserved. I left these alone because existing tests depend on them.

I haven't committed anything. Say if you want a commit with the Haiku co-author line.
