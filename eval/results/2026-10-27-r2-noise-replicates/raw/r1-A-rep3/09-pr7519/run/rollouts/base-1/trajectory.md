# trajectory base-1

final message:
Quoted index and constraint names in MySQL `CREATE TABLE` now parse and round-trip. The full suite passes (1087 tests), and ruff format and lint are clean.

**Root cause:** `_parse_unique` and `_parse_unique_key` in `sqlglot/parser.py` compared token text (`.text.upper()`) against the keyword tables without checking the token type. A backtick-quoted `` `Unique` `` or `` `Key` `` therefore looked like the keyword `UNIQUE`/`KEY`. That caused two failures:
- `UNIQUE KEY `Unique` (a)` and `UNIQUE INDEX `Key` (a)` were rejected.
- `UNIQUE `Key` (a)` was accepted, but the name was silently dropped, producing `UNIQUE (a)`.

**Fix:** Both spots now skip the keyword check when the current token is an `IDENTIFIER`, which is the same guard `_parse_unnamed_constraint` already uses. The change is in the shared parser, not MySQL-only, so other dialects that quote keyword-like names in these positions get the same behaviour.

**Results:**
- `UNIQUE KEY `Unique` (a)` → `UNIQUE `Unique` (a)`
- `UNIQUE INDEX `Key` (c)` → `UNIQUE `Key` (c)`
- `UNIQUE `Key` (a)` → `UNIQUE `Key` (a)` (name no longer dropped)
- `KEY `Index` (b)` → `INDEX `Index` (b)`, unchanged from before

Unquoted forms like `UNIQUE KEY (a)` still produce `UNIQUE (a)`, as before.

**Tests:** I added regression cases to `test_ddl` in `tests/dialects/test_mysql.py`. The existing tests already show that `KEY`/`INDEX` is dropped after `UNIQUE` on output, so the new expectations follow that convention. I did not weaken or edit any existing assertions.

I have not committed. Say if you want a commit, and I'll add the model name to the title as the project's CLAUDE.md asks.

## events
[tool_use Bash] {"command": "grep -n \"CONSTRAINT_PARSERS\\|SCHEMA_UNNAMED_CONSTRAINTS\\|UNNAMED_CONSTRAINT\\|def _parse_unnamed_constraint\\|def _parse_index_constraint\\|def _parse_constraint\\b\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -50", "description": "Locate constraint parsing code"}
[tool_result] sqlglot/parser.py:1326:    CONSTRAINT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1441:    SCHEMA_UNNAMED_CONSTRAINTS: t.ClassVar = {
sqlglot/parser.py:7216:        if not procedure_option_follows and self._match_texts(self.CONSTRAINT_PARSERS):
sqlglot/parser.py:7217:            constraint = self.CONSTRAINT_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7226:    def _parse_constraint(self) -> exp.Expr | None:
sqlglot/parser.py:7228:            return self._parse_unnamed_constraint(constr
…[115 chars elided]…
Expr]:
sqlglot/parser.py:7244:    def _parse_unnamed_constraint(
sqlglot/parser.py:7250:            constraints or self.CONSTRAINT_PARSERS
sqlglot/parser.py:7255:        if constraint_key not in self.CONSTRAINT_PARSERS:
sqlglot/parser.py:7258:        result = self.CONSTRAINT_PARSERS[constraint_key](self)
sqlglot/parser.py:7265:        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:
sqlglot/parser.py:7389:            and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['UNIQUE KEY \\`Unique\\` (a)', 'KEY \\`Index\\` (b)', 'UNIQUE INDEX \\`Key\\` (c)']:\n    s = f'CREATE TABLE t (a INT, b INT, c INT, {q})'\n    try:\n        print(sqlglot.transpile(s, read='mysql', write='mysql'))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\"", "description": "Reproduce the failing MySQL parses"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 56.
  CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY [4m`Unique`[0m (a))
['CREATE TABLE t (a INT, b INT, c INT, INDEX `Index` (b))']
ERR ParseError Expecting ). Line 1, Col: 55.
  CREATE TABLE t (a INT, b INT, c INT, UNIQUE INDEX [4m`Key`[0m (c))
[tool_use Bash] {"command": "sed -n 1436,1460p sqlglot/parser.py && echo ---- && sed -n 7210,7275p sqlglot/parser.py && echo ---- && grep -n \"KEY\\|INDEX\\|UNIQUE\" sqlglot/dialects/mysql.py | head -80", "description": "Read constraint parsing code and MySQL key references"}
[tool_result]         "DISTSTYLE": lambda self: self._parse_alter_diststyle(),
        "SORTKEY": lambda self: self._parse_alter_sortkey(),
        "COMPOUND": lambda self: self._parse_alter_sortkey(compound=True),
    }

    SCHEMA_UNNAMED_CONSTRAINTS: t.ClassVar = {
        "CHECK",
        "EXCLUDE",
        "FOREIGN KEY",
        "LIKE",
        "PERIOD",
        "PRIMARY KEY",
        "UNIQUE",
        "BUCKET",
        "TRUNCATE",
    }

    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
        "ANY": lambd
…[2468 chars elided]…
atch_texts(("KEY", "INDEX"))
        return self.expression(
            exp.UniqueColumnConstraint(
                nulls=self._match_text_seq("NULLS", "NOT", "DISTINCT"),
                this=self._parse_schema(self._parse_unique_key()),
                index_type=self._match(TokenType.USING) and self._advance_any() and self._prev.text,
----
78:        KEYWORDS = {
79:            **tokens.Tokenizer.KEYWORDS,
86:            "KEY": TokenType.KEY,
130:            "_KEYBCS2": TokenType.INTRODUCER,
[tool_use Bash] {"command": "sed -n 7380,7395p sqlglot/parser.py && echo ---- && grep -n \"_parse_unique_key\\|def _match_texts\" -A6 sqlglot/parser.py | head -60 && echo ---- && grep -n \"UNIQUE\" sqlglot/dialects/mysql.py tests/dialects/test_mysql.py | head -30", "description": "Inspect helper matchers and existing MySQL unique tests"}
[tool_result]         desc = (
            self._prev.token_type == TokenType.DESC
            if self._match_set((TokenType.ASC, TokenType.DESC))
            else None
        )

        this = None
        if (
            named_primary_key
            and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
            and self._next
            and self._next.token_type == TokenType.L_PAREN
        ):
            this = self._parse_id_var()

        if not in_props and not self._match(TokenType.L_PAREN,
…[1960 chars elided]…
T(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE KEY d (b), KEY e (b))",
tests/dialects/test_mysql.py:145:            "CREATE TABLE IF NOT EXISTS industry_info (a BIGINT(20) NOT NULL AUTO_INCREMENT, b BIGINT(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE d (b), INDEX e (b))",
tests/dialects/test_mysql.py:164:            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
tests/dialects/test_mysql.py:165:            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['UNIQUE \\`Key\\` (a)', 'UNIQUE KEY \\`Key\\` (a)', 'UNIQUE INDEX \\`Index\\` (a)', 'UNIQUE \\`Unique\\` (a)']:\n    s = f'CREATE TABLE t (a INT, {q})'\n    try:\n        print(sqlglot.transpile(s, read='mysql', write='mysql'))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:120].replace(chr(10),' '))\n\"", "description": "Check more quoted unique-name variants before editing"}
[tool_result] ['CREATE TABLE t (a INT, UNIQUE (a))']
ERR ParseError Expecting ). Line 1, Col: 39.   CREATE TABLE t (a INT, UNIQUE KEY [4m`Key`[0m (a))
ERR ParseError Expecting ). Line 1, Col: 43.   CREATE TABLE t (a INT, UNIQUE INDEX [4m`Index`[0m (a))
ERR ParseError Expecting ). Line 1, Col: 38.   CREATE TABLE t (a INT, UNIQUE [4m`Unique`[0m (a))
[assistant] Three problems show up: a quoted name after `UNIQUE KEY`/`UNIQUE INDEX` gets rejected, a bare quoted `` `Key` `` is swallowed as the `KEY` keyword (the name is dropped), and `` `Unique` `` fails too. The cause is that `_match_texts` and the keyword check compare token text without looking at token type, so a backtick-quoted identifier matches a keyword. I'll fix both spots in `_parse_unique`/`_parse_unique_key`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112633-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "    def _parse_unique_key(self) -> exp.Expr | None:\n        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)\n\n    def 
…[268 chars elided]…
token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)\n\n    def _parse_unique(self) -> exp.UniqueColumnConstraint:\n        if self._curr.token_type != TokenType.IDENTIFIER:\n            self._match_texts((\"KEY\", \"INDEX\"))\n        return self.expression("}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112633-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor q in ['UNIQUE KEY \\`Unique\\` (a)', 'KEY \\`Index\\` (b)', 'UNIQUE INDEX \\`Key\\` (c)', 'UNIQUE \\`Key\\` (a)', 'UNIQUE \\`Unique\\` (a)', 'UNIQUE INDEX \\`Index\\` (a)', 'UNIQUE KEY (a)', 'UNIQUE INDEX (a)']:\n    s = f'CREATE TABLE t (a INT, {q})'\n    try:\n        print(sqlglot.transpile(s, read='mysql', write='mysql'))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:120].replace(chr(10),' '))\n\"", "description": "Verify quoted unique/key names now parse and round-trip"}
[tool_result] ['CREATE TABLE t (a INT, UNIQUE `Unique` (a))']
['CREATE TABLE t (a INT, INDEX `Index` (b))']
['CREATE TABLE t (a INT, UNIQUE `Key` (c))']
['CREATE TABLE t (a INT, UNIQUE `Key` (a))']
['CREATE TABLE t (a INT, UNIQUE `Unique` (a))']
['CREATE TABLE t (a INT, UNIQUE `Index` (a))']
['CREATE TABLE t (a INT, UNIQUE (a))']
['CREATE TABLE t (a INT, UNIQUE (a))']
[assistant] All variants now parse and keep their names. Next I'll add a regression test to the MySQL test file, near the existing unique-index tests.
[tool_use Bash] {"command": "sed -n 158,172p tests/dialects/test_mysql.py", "description": "Read test context around unique index tests"}
[tool_result]         )
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
                "duckdb": "INSERT INTO t (i) VALUES (DEFAULT)",
                "mysql": "INSERT INTO t (i) VALUES (DEFAULT)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112633-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n\n        self.validate_all(\n            \"insert into t(i) values (default)\",", "new_string": "            \"CREATE TABLE `
…[107 chars elided]…
T, UNIQUE KEY `Unique` (a))\")\n        self.validate_identity(\"CREATE TABLE t (a INT, KEY `Index` (a))\", \"CREATE TABLE t (a INT, INDEX `Index` (a))\")\n        self.validate_identity(\"CREATE TABLE t (a INT, UNIQUE INDEX `Key` (a))\")\n        self.validate_identity(\"CREATE TABLE t (a INT, UNIQUE `Key` (a))\")\n\n        self.validate_all(\n            \"insert into t(i) values (default)\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112633-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the project's test command from the harness config, plus a format check on the touched files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py 2>&1 | tail -3", "description": "Run test suite and ruff format/lint checks"}
[tool_result]             "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
        )
>       self.validate_identity("CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))")

tests/dialects/test_mysql.py:167: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/dialects/test_dialect.py:63: in validate_identity
    self.assertEqual(
E   AssertionError: 'CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))' != 'CREATE TABLE t (a INT, UNIQUE `Unique` (a))'
E   - CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))
E   ?                              ----
E   + CREATE TABLE t (a INT, UNIQUE `Unique` (a))
=========================== short test summary info ============================
FAILED tests/dialects/test_mysql.py::TestMySQL::test_ddl - AssertionError: 'C...
1 failed, 1086 passed, 17834 subtests passed in 53.62s
Would reformat: tests/dialects/test_mysql.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[assistant] The one failure is in my new test, not the parser: the generator drops `KEY`/`INDEX` after `UNIQUE`, as the existing tests show (`UNIQUE KEY d (b)` → `UNIQUE d (b)`). I'll set the expected outputs to match, then format.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-112633-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))\")\n        self.validate_identity(\"CREATE TABLE t (a INT, KEY `Index` (a))\", \"CREATE TABLE t (a INT, INDEX `Index` (a))\")\
…[359 chars elided]…
self.validate_identity(\n            \"CREATE TABLE t (a INT, KEY `Index` (a))\",\n            \"CREATE TABLE t (a INT, INDEX `Index` (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, UNIQUE INDEX `Key` (a))\",\n            \"CREATE TABLE t (a INT, UNIQUE `Key` (a))\",\n        )\n        self.validate_identity(\"CREATE TABLE t (a INT, UNIQUE `Key` (a))\")"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-112633-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/parser.py tests/dialects/test_mysql.py && git diff --stat && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests 2>&1 | tail -1; <work>/env-sqlglot/bin/python -m ruff check sqlglot tests 2>&1 | tail -1", "description": "Format, rerun full test suite, and lint"}
[tool_result] 2 files left unchanged
 sqlglot/parser.py            |  9 +++++++--
 tests/dialects/test_mysql.py | 13 +++++++++++++
 2 files changed, 20 insertions(+), 2 deletions(-)
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 52.69s
232 files already formatted
All checks passed!
[assistant] Quoted index and constraint names in MySQL `CREATE TABLE` now parse and round-trip. The full suite passes (1087 tests), and ruff format and lint are clean.

**Root cause:** `_parse_unique` and `_parse_unique_key` in `sqlglot/parser.py` compared token text (`.text.upper()`) against the keyword tables without checking the token type. A backtick-quoted `` `Unique` `` or `` `Key` `` therefore looked like the keyword `UNIQUE`/`KEY`. That caused two failures:
- `UNIQUE KEY `Unique` (a)` and `UNIQUE INDEX `Key` (a)` were rejected.
- `UNIQUE `Key` (a)` was accepted, but the name was silently dropped, 
…[441 chars elided]…
UNIQUE `Key` (a)` → `UNIQUE `Key` (a)` (name no longer dropped)
- `KEY `Index` (b)` → `INDEX `Index` (b)`, unchanged from before

Unquoted forms like `UNIQUE KEY (a)` still produce `UNIQUE (a)`, as before.

**Tests:** I added regression cases to `test_ddl` in `tests/dialects/test_mysql.py`. The existing tests already show that `KEY`/`INDEX` is dropped after `UNIQUE` on output, so the new expectations follow that convention. I did not weaken or edit any existing assertions.

I have not committed. Say if you want a commit, and I'll add the model name to the title as the project's CLAUDE.md asks.
