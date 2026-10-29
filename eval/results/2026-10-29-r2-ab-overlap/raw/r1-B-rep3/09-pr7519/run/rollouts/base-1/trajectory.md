# trajectory base-1

final message:
Quoted index and constraint names that look like keywords now parse and round-trip in the MySQL dialect. The full test suite passes (1087 tests) and ruff check and format are clean. I haven't committed.

**Cause:** `_parse_unique_key` in `sqlglot/parser.py` decided whether the token after `UNIQUE` (or `UNIQUE KEY` / `UNIQUE INDEX`) was a name by comparing its text against the constraint keywords. A backtick-quoted `` `Unique` `` has the same text as the keyword, so it was rejected. Quoted names are tokenized as `TokenType.IDENTIFIER`, so the check now skips identifier tokens. Unquoted keywords behave as before.

**Fix:**
- `sqlglot/parser.py`: `_parse_unique_key` ignores the keyword check when the token is an identifier.
- `tests/dialects/test_mysql.py`: added round-trip cases for `` UNIQUE KEY `Unique` ``, `` KEY `Index` `` and `` UNIQUE INDEX `Key` `` in a `CREATE TABLE`, plus a plain `` UNIQUE `Unique` `` case.

**Output shape:** The names round-trip exactly, but the keyword is normalized as the dialect already does for unquoted names. `KEY` becomes `INDEX` and `UNIQUE KEY` becomes `UNIQUE`. For example, `UNIQUE KEY \`Unique\` (a)` is written back as ``UNIQUE `Unique` (a)``.

**Not fixed:** `UNIQUE KEY name USING BTREE (a)` still fails to parse. It also fails with an unquoted name, so it is an existing gap in how the index type is placed after the name, not part of this quoting bug. I left it alone to keep the change scoped. It could be a follow-up.

## events
[tool_use Bash] {"command": "grep -n \"UNIQUE\\|INDEX\\|\\bKEY\\b\\|_parse_index_constraint\\|CONSTRAINT_PARSERS\\|_parse_create\\b\" sqlglot/dialects/mysql.py | head -80; echo ---; grep -n \"CONSTRAINT_PARSERS\\|def _parse_index_constraint\\|def _parse_unnamed_constraint\\|def _parse_constraint\\|def _parse_unique\\b\\|def _parse_unique_key\\|def _parse_key_constraint_option\" sqlglot/parser.py", "description": "Find MySQL index/constraint parsing code"}
[tool_result] 1 matches in 1 files:

86:0:TokenType.KEY,
---
14 matches in 10 files:

1326:0:t.ClassVar = {
7216:0:
7226:0:
7234:0:
7255:0:
7264:0:
7265:0:
7269:0:
7281:0:
sqlglot/parser.py:7217:constraint = self.CONSTRAINT_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7244:def _parse_unnamed_constraint(
sqlglot/parser.py:7250:constraints or self.CONSTRAINT_PARSERS
sqlglot/parser.py:7258:result = self.CONSTRAINT_PARSERS[constraint_key](self)
sqlglot/parser.py:7389:and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
[tool_use Bash] {"command": "sed -n 7205,7300p sqlglot/parser.py; echo ---; sed -n 7375,7400p sqlglot/parser.py; echo ---; grep -n \"CONSTRAINT_PARSERS\\|\\\"UNIQUE\\\"\\|\\\"INDEX\\\"\\|\\\"KEY\\\"\\|FULLTEXT\\|SPATIAL\" sqlglot/dialects/mysql.py sqlglot/parser.py | head -60", "description": "Read constraint parsing code in parser and mysql"}
[tool_result]         return None

    def _parse_column_constraint(self) -> exp.Expr | None:
        this = self._parse_id_var() if self._match(TokenType.CONSTRAINT) else None

        procedure_option_follows = (
            self._match(TokenType.WITH, advance=False)
            and self._next
            and self._next.text.upper() in self.PROCEDURE_OPTIONS
        )

        if not procedure_option_follows and self._match_texts(self.CONSTRAINT_PARSERS):
            constraint = self.CONSTRAINT_PARSERS[sel
…[5184 chars elided]…
raint_key](self)
sqlglot/parser.py:7265:if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:
sqlglot/parser.py:7270:self._match_texts(("KEY", "INDEX"))
sqlglot/parser.py:7389:and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
sqlglot/parser.py:7797:self._match_text_seq("KEY")
sqlglot/parser.py:7861:if self._match_text_seq("WITH", "UNIQUE"):
sqlglot/parser.py:7863:elif self._match_text_seq("WITHOUT", "UNIQUE"):
sqlglot/parser.py:8582:self._match_text_seq("KEY", "DISTKEY")
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a), KEY \\`Index\\` (b), UNIQUE INDEX \\`Key\\` (c))\" \"CREATE TABLE t (a INT, UNIQUE \\`Unique\\` (a))\" \"CREATE TABLE t (a INT, KEY \\`Key\\` (a))\" \"CREATE TABLE t (a INT, INDEX \\`Index\\` (a))\" \"CREATE TABLE t (a INT, CONSTRAINT \\`Unique\\` UNIQUE (a))\"; do $PY -I -c \"\nimport sys, sqlglot\ns=sys.argv[1]\ntry:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\" \"$s\"; done", "description": "Reproduce MySQL quoted index name failures"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a), KEY \\`Index\\` (b), UNIQUE INDEX \\`Key\\` (c))\" \"CREATE TABLE t (a INT, UNIQUE \\`Unique\\` (a))\" \"CREATE TABLE t (a INT, KEY \\`Key\\` (a))\" \"CREATE TABLE t (a INT, INDEX \\`Index\\` (a))\" \"CREATE TABLE t (a INT, CONSTRAINT \\`Unique\\` UNIQUE (a))\"; do $PY -c \"\nimport sys, sqlglot\ns=sys.argv[1]\ntry:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\" \"$s\"; done", "description": "Reproduce MySQL quoted index name failures"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 56.
  CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY [4m`Unique`[0m (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))
ERR ParseError Expecting ). Line 1, Col: 38.
  CREATE TABLE t (a INT, UNIQUE [4m`Unique`[0m (a))
CREATE TABLE t (a INT, INDEX `Key` (a))
CREATE TABLE t (a INT, INDEX `Index` (a))
CREATE TABLE t (a INT, CONSTRAINT `Unique` UNIQUE (a))
[assistant] The failure is in `_parse_unique_key`: it checks the current token's *text* against `CONSTRAINT_PARSERS`, so a backtick-quoted `` `Unique` `` is rejected even though it's an identifier. Let me confirm the quoted token type before changing it.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.dialects.mysql import MySQL\nfor t in MySQL().tokenize('\\`Unique\\` UNIQUE KEY'): print(t.token_type, repr(t.text))\n\"; grep -n \"_parse_unique_key\" sqlglot/*.py sqlglot/dialects/*.py", "description": "Check token types for backtick identifiers"}
[tool_result] TokenType.IDENTIFIER 'Unique'
TokenType.UNIQUE 'UNIQUE'
TokenType.KEY 'KEY'
2 matches in 1 files:

sqlglot/parser.py:7264:def _parse_unique_key(self) -> exp.Expr | None:
sqlglot/parser.py:7274:this=self._parse_schema(self._parse_unique_key()),
[assistant] Quoted names arrive as `TokenType.IDENTIFIER`, so the fix is to let identifiers bypass the keyword check. This is in the shared parser, but it only changes behaviour for quoted names.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174702-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)", "new_string": "        if (\n            self._curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174702-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a), KEY \\`Index\\` (b), UNIQUE INDEX \\`Key\\` (c))\" \"CREATE TABLE t (a INT, UNIQUE \\`Unique\\` (a))\" \"CREATE TABLE t (a INT, UNIQUE KEY \\`Key\\` (a))\" \"CREATE TABLE t (a INT, UNIQUE INDEX \\`Index\\` (a))\" \"CREATE TABLE t (a
…[12 chars elided]…
 INDEX \\`Unique\\` (a))\" \"CREATE TABLE t (a INT, UNIQUE KEY (a))\" \"CREATE TABLE t (a INT, UNIQUE KEY \\`Unique\\` USING BTREE (a))\"; do $PY -c \"\nimport sys, sqlglot\ns=sys.argv[1]\ntry:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\" \"$s\"; done", "description": "Re-run reproduction cases after fix"}
[tool_result] CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))
CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (a INT, UNIQUE `Key` (a))
CREATE TABLE t (a INT, UNIQUE `Index` (a))
CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (a INT, UNIQUE (a))
ERR ParseError Expecting ). Line 1, Col: 56.
  CREATE TABLE t (a INT, UNIQUE KEY `Unique` USING BTREE [4m([0ma))
[assistant] The quoted-name cases now parse and round-trip. The last case (`USING BTREE` after the name) is a separate question, so I'll check whether the unquoted form fails the same way, then run the test suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (a INT, UNIQUE KEY foo USING BTREE (a))', 'CREATE TABLE t (a INT, UNIQUE KEY foo (a))']:\n    try: print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', str(e)[:120])\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Check unquoted USING case and run full test suite"}
[tool_result] ERR Expecting ). Line 1, Col: 51.
  CREATE TABLE t (a INT, UNIQUE KEY foo USING BTREE [4m([0ma))
CREATE TABLE t (a INT, UNIQUE foo (a))
............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
..............................................................................................................................................................................................
…[305 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 47.06s
[assistant] The `USING BTREE` failure also happens with unquoted names, so it's a separate pre-existing gap and I'll leave it out of this change. The full suite passes (1087 tests). Now I'll add regression tests to the MySQL dialect tests.
[tool_use Bash] {"command": "grep -n \"UNIQUE KEY\\|UNIQUE INDEX\\|KEY \\`\\|INDEX \\`\\|def test_ddl\\|def test_\" tests/dialects/test_mysql.py | head -60", "description": "Locate existing MySQL DDL tests"}
[tool_result] 58 matches in 51 files:

1161:0:
1179:0:
1195:0:
12:0:
1229:0:
1244:0:
1261:0:
1267:0:
1279:0:
1289:0:
1302:0:
1326:0:
1336:0:
1353:0:
1365:0:
1376:0:
1405:0:
1408:0:
1413:0:
1422:0:
1447:0:
1472:0:
1481:0:
1493:0:
1508:0:
1523:0:
1535:0:
1565:0:
1575:0:
1581:0:
1586:0:
1606:0:
1623:0:
1640:0:
1694:0:
1701:0:
240:0:
382:0:
425:0:
464:0:
496:0:
525:0:
577:0:
601:0:
609:0:
626:0:
662:0:
737:0:
848:0:
866:0:
tests/dialects/test_mysql.py:36:self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
…[166 chars elided]…
 (id INT, PRIMARY KEY `pk_name` (id))",
tests/dialects/test_mysql.py:136:"ALTER TABLE t ADD KEY `i` (`c`)",
tests/dialects/test_mysql.py:137:"ALTER TABLE t ADD INDEX `i` (`c`)",
tests/dialects/test_mysql.py:140:"CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`i...
tests/dialects/test_mysql.py:144:"CREATE TABLE IF NOT EXISTS industry_info (a BIGINT(20) NOT NULL AUTO_INCREME...
tests/dialects/test_mysql.py:164:"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
[tool_use Bash] {"command": "sed -n 104,112p tests/dialects/test_mysql.py; echo ...; sed -n 160,170p tests/dialects/test_mysql.py", "description": "View nearby MySQL DDL test lines"}
[tool_result]             "CREATE TABLE test_table (id INT AUTO_INCREMENT, PRIMARY KEY (id) USING HASH)"
        )
        self.validate_identity("CREATE TABLE test (id INT, PRIMARY KEY pk_name (id))")
        self.validate_identity("CREATE TABLE test (id INT, PRIMARY KEY `pk_name` (id))")
        self.validate_identity(
            'CREATE TABLE test (id INT, PRIMARY KEY "pk_name" (id))',
            "CREATE TABLE test (id INT, PRIMARY KEY `pk_name` (id))",
        )
        self.validate_identity("CREATE TABLE test (id INT, CONSTRAINT pk_name PRIMARY KEY (id))")
...
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-174702-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n", "new_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n        self.validate_iden
…[22 chars elided]…
REATE TABLE t (a INT, b INT, c INT, UNIQUE KEY `Unique` (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))\",\n            \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, UNIQUE `Unique` (a))\",\n            \"CREATE TABLE t (a INT, UNIQUE `Unique` (a))\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-174702-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list >/dev/null; git status --short; ruff --version 2>/dev/null; $PY -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py 2>&1 | tail -2; $PY -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Run MySQL tests, full suite, and lint checks"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.16s
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 48.28s
 M sqlglot/parser.py
 M tests/dialects/test_mysql.pyruff 0.15.6
All checks passed!
2 files already formatted
[assistant] Quoted index and constraint names that look like keywords now parse and round-trip in the MySQL dialect. The full test suite passes (1087 tests) and ruff check and format are clean. I haven't committed.

**Cause:** `_parse_unique_key` in `sqlglot/parser.py` decided whether the token after `UNIQUE` (or `UNIQUE KEY` / `UNIQUE INDEX`) was a name by comparing its text against the constraint keywords. A backtick-quoted `` `Unique` `` has the same text as the keyword, so it was rejected. Quoted names are tokenized as `TokenType.IDENTIFIER`, so the check now skips identifier tokens. Unquoted keywords
…[276 chars elided]…
TE TABLE`, plus a plain `` UNIQUE `Unique` `` case.

**Output shape:** The names round-trip exactly, but the keyword is normalized as the dialect already does for unquoted names. `KEY` becomes `INDEX` and `UNIQUE KEY` becomes `UNIQUE`. For example, `UNIQUE KEY \`Unique\` (a)` is written back as ``UNIQUE `Unique` (a)``.

**Not fixed:** `UNIQUE KEY name USING BTREE (a)` still fails to parse. It also fails with an unquoted name, so it is an existing gap in how the index type is placed after the name, not part of this quoting bug. I left it alone to keep the change scoped. It could be a follow-up.
