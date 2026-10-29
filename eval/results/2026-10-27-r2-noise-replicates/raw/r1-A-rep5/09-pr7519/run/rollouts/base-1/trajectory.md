# trajectory base-1

final message:
MySQL now accepts backtick-quoted index names that look like keywords, such as ``UNIQUE KEY `Unique` (a)``, ``KEY `Index` (b)`` and ``UNIQUE INDEX `Key` (c)``, and keeps the names in the output. The full suite passes (1087 tests) and ruff is clean.

**Cause:** `_parse_unique_key` in `sqlglot/parser.py` rejected any token whose text matched a constraint keyword. It never checked whether the token was a quoted identifier, so `` `Unique` `` was treated as the `UNIQUE` keyword. The fix skips that check for `IDENTIFIER` tokens. Unquoted keywords are still rejected, so `UNIQUE KEY CHECK (a)` still fails, as it should.

**Tests:** I added three `validate_identity` cases to `tests/dialects/test_mysql.py`, next to the existing `UNIQUE INDEX` test.

**Output changes:** The generator drops the `KEY` in `UNIQUE KEY `Unique`` and writes ``UNIQUE `Unique` (a)``. `KEY` becomes `INDEX` for plain keys. This matches what sqlglot already does for other MySQL index forms, but the output is not byte-identical to the input. The tests assert the normalized form.

I haven't committed anything.

## events
[tool_use Bash] {"command": "git status --short | head && grep -n \"UNIQUE_KEY\\|\\\"KEY\\\"\\|\\\"INDEX\\\"\\|CONSTRAINT_PARSERS\\|\\\"UNIQUE\\\"\" sqlglot/dialects/mysql.py sqlglot/parser.py | head -60", "description": "Check status and find index/constraint handling"}
[tool_result] sqlglot/dialects/mysql.py:86:            "KEY": TokenType.KEY,
sqlglot/parser.py:1326:    CONSTRAINT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1382:        "UNIQUE": lambda self: self._parse_unique(),
sqlglot/parser.py:1448:        "UNIQUE",
sqlglot/parser.py:2908:        self._match_text_seq("KEY")
sqlglot/parser.py:3245:        if self._match_text_seq("PRIMARY", "INDEX"):
sqlglot/parser.py:3463:        duplicate = self._match_text_seq("ON", "DUPLICATE", "KEY")
sqlglot/parser.py:3947:          
…[848 chars elided]…
r and self._curr.text.upper() in self.CONSTRAINT_PARSERS:
sqlglot/parser.py:7270:        self._match_texts(("KEY", "INDEX"))
sqlglot/parser.py:7389:            and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
sqlglot/parser.py:7797:        self._match_text_seq("KEY")
sqlglot/parser.py:7861:        if self._match_text_seq("WITH", "UNIQUE"):
sqlglot/parser.py:7863:        elif self._match_text_seq("WITHOUT", "UNIQUE"):
sqlglot/parser.py:8582:        self._match_text_seq("KEY", "DISTKEY")
[tool_use Bash] {"command": "sed -n 7230,7290p sqlglot/parser.py && echo ---- && sed -n 1320,1330p sqlglot/parser.py && echo ---- && sed -n 1440,1460p sqlglot/parser.py && echo ---- && sed -n 7380,7400p sqlglot/parser.py && echo ---- && grep -n \"def _parse_index_constraint\\|def _parse_unique\\b\\|def _parse_unique(\" sqlglot/parser.py", "description": "Read constraint parsing code in parser"}
[tool_result]         return self.expression(
            exp.Constraint(this=self._parse_id_var(), expressions=self._parse_unnamed_constraints())
        )

    def _parse_unnamed_constraints(self) -> list[exp.Expr]:
        constraints = []
        while True:
            constraint = self._parse_unnamed_constraint() or self._parse_function()
            if not constraint:
                break
            constraints.append(constraint)

        return constraints

    def _parse_unnamed_constraint(
       
…[3165 chars elided]…
elf.CONSTRAINT_PARSERS
            and self._next
            and self._next.token_type == TokenType.L_PAREN
        ):
            this = self._parse_id_var()

        if not in_props and not self._match(TokenType.L_PAREN, advance=False):
            return self.expression(
                exp.PrimaryKeyColumnConstraint(
                    desc=desc, options=self._parse_key_constraint_options()
                )
            )
----
7269:    def _parse_unique(self) -> exp.UniqueColumnConstraint:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for q in 'CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))' 'CREATE TABLE t (b INT, KEY `Index` (b))' 'CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c))' 'CREATE TABLE t (a INT, UNIQUE KEY `x` (a))' 'CREATE TABLE t (a INT, UNIQUE KEY \"Unique\" (a))'; do $PY -c \"\nimport sqlglot,sys\nq=sys.argv[1]\ntry:\n  print(sqlglot.transpile(q, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\" \"$q\"; done", "description": "Reproduce the MySQL quoted index name failures"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 42.
  CREATE TABLE t (a INT, UNIQUE KEY [4m`Unique`[0m (a))
CREATE TABLE t (b INT, INDEX `Index` (b))
ERR ParseError Expecting ). Line 1, Col: 41.
  CREATE TABLE t (c INT, UNIQUE INDEX [4m`Key`[0m (c))
CREATE TABLE t (a INT, UNIQUE `x` (a))
ERR ParseError Expecting ). Line 1, Col: 42.
  CREATE TABLE t (a INT, UNIQUE KEY [4m"Unique"[0m (a))
[assistant] The failure is in `_parse_unique_key`, which checks the token's text against `CONSTRAINT_PARSERS` without checking the token type, so a backtick-quoted identifier is rejected. Checking existing tests and the keyword table before changing it.
[tool_use Bash] {"command": "grep -n \"UNIQUE KEY\\|UNIQUE INDEX\" tests/dialects/test_mysql.py | head -20; grep -n '\"INDEX\"\\|\"KEY\"\\|\"UNIQUE\"' sqlglot/parser.py | head; grep -rn \"_parse_unique_key\" sqlglot | head", "description": "Find related tests and usages"}
[tool_result] 140:            "CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`id`), UNIQUE KEY `id` (`id`))",
144:            "CREATE TABLE IF NOT EXISTS industry_info (a BIGINT(20) NOT NULL AUTO_INCREMENT, b BIGINT(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE KEY d (b), KEY e (b))",
164:            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
1382:        "UNIQUE": lambda self: self._parse_unique(),
1448:        "UNIQUE",
2908:        self._match_text_se
…[247 chars elided]…
      if self._match_text_seq("USING", "INDEX", "TABLESPACE")
5520:            elif self._match_text_seq("FOR", "KEY", "SHARE"):
5522:            elif self._match_text_seq("FOR", "NO", "KEY", "UPDATE"):
7270:        self._match_texts(("KEY", "INDEX"))
sqlglot/parser.py:7264:    def _parse_unique_key(self) -> exp.Expr | None:
sqlglot/parser.py:7274:                this=self._parse_schema(self._parse_unique_key()),
sqlglot/parsers/postgres.py:309:    def _parse_unique_key(self) -> exp.Expr | None:
[assistant] Existing tests cover `UNIQUE KEY \`id\``, which works because `id` isn't a constraint keyword. The fix belongs in the base `_parse_unique_key`: only unquoted tokens should be matched against constraint keywords.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092500-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)", "new_string": "        if (\n            self._curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092500-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for q in 'CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))' 'CREATE TABLE t (b INT, KEY `Index` (b))' 'CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c))' 'CREATE TABLE t (a INT, UNIQUE KEY `Primary` (a))' 'CREATE TABLE t (a INT, UNIQUE KEY `x` (a))' 'CREATE TABLE t (a INT, UNIQUE KEY (a))' 'CREATE TABLE t (a INT, UNIQUE KEY CHECK (a))'; do $PY -c \"\nimport sqlglot,sys\nq=sys.argv[1]\ntry:\n  print(sqlglot.transpile(q, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:120])\n\" \"$q\"; done", "description": "Re-run reproduction cases after the fix"}
[tool_result] CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (b INT, INDEX `Index` (b))
CREATE TABLE t (c INT, UNIQUE `Key` (c))
CREATE TABLE t (a INT, UNIQUE `Primary` (a))
CREATE TABLE t (a INT, UNIQUE `x` (a))
CREATE TABLE t (a INT, UNIQUE (a))
ERR ParseError Expecting ). Line 1, Col: 39.
  CREATE TABLE t (a INT, UNIQUE KEY [4mCHECK[0m (a))
[assistant] All the quoted cases now parse and keep their names. The last case (unquoted `CHECK` as an index name) was already invalid MySQL and still errors, which is correct. Next I'll add regression tests next to the existing `UNIQUE INDEX` test.
[tool_use Bash] {"command": "sed -n 160,168p tests/dialects/test_mysql.py", "description": "View test context for insertion point"}
[tool_result]             "CREATE TABLE `foo` (a VARCHAR(10), KEY idx_a (a DESC))",
            "CREATE TABLE `foo` (a VARCHAR(10), INDEX idx_a (a DESC))",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
        )

        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092500-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n\n        self.validate_all(", "new_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )
…[134 chars elided]…
NT, UNIQUE `Unique` (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (b INT, KEY `Index` (b))\",\n            \"CREATE TABLE t (b INT, INDEX `Index` (b))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c))\",\n            \"CREATE TABLE t (c INT, UNIQUE `Key` (c))\",\n        )\n\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-092500-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the project's check command, the full test suite, as the harness requires.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run full pytest suite", "timeout": 900000}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[167 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 49.34s
[assistant] All 1087 tests pass. I'll also run the linter on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot/parser.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py            |  6 +++++-
 tests/dialects/test_mysql.py | 12 ++++++++++++
 2 files changed, 17 insertions(+), 1 deletion(-)
[assistant] MySQL now accepts backtick-quoted index names that look like keywords, such as ``UNIQUE KEY `Unique` (a)``, ``KEY `Index` (b)`` and ``UNIQUE INDEX `Key` (c)``, and keeps the names in the output. The full suite passes (1087 tests) and ruff is clean.

**Cause:** `_parse_unique_key` in `sqlglot/parser.py` rejected any token whose text matched a constraint keyword. It never checked whether the token was a quoted identifier, so `` `Unique` `` was treated as the `UNIQUE` keyword. The fix skips that check for `IDENTIFIER` tokens. Unquoted keywords are still rejected, so `UNIQUE KEY CHECK (a)` still fails, as it should.

**Tests:** I added three `validate_identity` cases to `tests/dialects/test_mysql.py`, next to the existing `UNIQUE INDEX` test.

**Output changes:** The generator drops the `KEY` in `UNIQUE KEY `Unique`` and writes ``UNIQUE `Unique` (a)``. `KEY` becomes `INDEX` for plain keys. This matches what sqlglot already does for other MySQL index forms, but the output is not byte-identical to the input. The tests assert the normalized form.

I haven't committed anything.
