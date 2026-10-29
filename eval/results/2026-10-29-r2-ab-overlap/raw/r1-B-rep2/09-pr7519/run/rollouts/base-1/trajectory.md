# trajectory base-1

final message:
MySQL now accepts backtick-quoted index names that look like keywords in `UNIQUE KEY`/`UNIQUE INDEX` table constraints. The full test suite passes (1087 tests) and ruff is clean.

**Cause:** `_parse_unique_key` in `sqlglot/parser.py` skipped any token whose text matched a constraint keyword. That also caught a quoted identifier such as `` `Unique` `` or `` `Key` ``, so the name was never consumed and parsing failed at the `(`.

**Fix:** the check now ignores `IDENTIFIER` tokens, the same rule `_parse_unnamed_constraint` already uses. Unquoted keywords are still rejected as names, so `UNIQUE PRIMARY KEY` on a column behaves as before. The change is in the base parser, so it applies to every dialect, not only MySQL. Quoted names were already rejected there too, so this only makes them accepted.

**Output:** the `KEY`/`INDEX` keyword is dropped on output, as it already was for unquoted names and as the existing MySQL tests expect:

- `UNIQUE KEY `Unique` (a)` → ``UNIQUE `Unique` (a)``
- `KEY `Index` (b)` → ``INDEX `Index` (b)``
- `UNIQUE INDEX `Key` (c)` → ``UNIQUE `Key` (c)``

The output is valid MySQL and re-parses to the same AST, but it is not byte-identical to the input. If you want the keyword kept, that's a generator change and a rewrite of the existing expectations, so I left it alone.

**Tests:** I added three `validate_identity` cases to `tests/dialects/test_mysql.py`, next to the existing `UNIQUE INDEX` cases. I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"CONSTRAINT_PARSERS\\|def _parse_index_constraint\\|def _parse_unnamed_constraint\\|CONSTRAINT_KEYWORDS\\|_parse_create\\b\" sqlglot/parser.py | head -50; grep -n \"CONSTRAINT\\|UNIQUE\\|INDEX\\|KEY\" sqlglot/dialects/mysql.py | head -60", "description": "Find constraint parsing code"}
[tool_result] 12 matches in 8 files:

1074:0:lambda self: self._parse_create(),
1326:0:t.ClassVar = {
2330:0:
7216:0:
7234:0:
7255:0:
7265:0:
sqlglot/parser.py:7217:constraint = self.CONSTRAINT_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7244:def _parse_unnamed_constraint(
sqlglot/parser.py:7250:constraints or self.CONSTRAINT_PARSERS
sqlglot/parser.py:7258:result = self.CONSTRAINT_PARSERS[constraint_key](self)
sqlglot/parser.py:7389:and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
4 matches in 3 files:

130:0:TokenType.INTRODUCER,
86:0:TokenType.KEY,
sqlglot/dialects/mysql.py:78:KEYWORDS = {
sqlglot/dialects/mysql.py:79:**tokens.Tokenizer.KEYWORDS,
[tool_use Bash] {"command": "sed -n 7200,7300p sqlglot/parser.py; grep -n \"CONSTRAINT_PARSERS\\|UNIQUE\\|\\\"INDEX\\\"\\|\\\"KEY\\\"\\|FULLTEXT\\|SPATIAL\" sqlglot/parser.py | head -80", "description": "Read constraint parsing code in parser"}
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
          
…[4157 chars elided]…
kenType.UNIQUE)
sqlglot/parser.py:7217:constraint = self.CONSTRAINT_PARSERS[self._prev.text.upper()](self)
sqlglot/parser.py:7250:constraints or self.CONSTRAINT_PARSERS
sqlglot/parser.py:7258:result = self.CONSTRAINT_PARSERS[constraint_key](self)
sqlglot/parser.py:7270:self._match_texts(("KEY", "INDEX"))
sqlglot/parser.py:7389:and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
sqlglot/parser.py:7797:self._match_text_seq("KEY")
sqlglot/parser.py:8582:self._match_text_seq("KEY", "DISTKEY")
[tool_use Bash] {"command": "for s in 'CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))' 'CREATE TABLE t (b INT, KEY `Index` (b))' 'CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c))' 'CREATE TABLE t (a INT, CONSTRAINT `Unique` UNIQUE (a))' 'CREATE TABLE t (a INT, INDEX `Primary` (a))'; do <work>/env-sqlglot/bin/python -c \"\nimport sys, sqlglot\ns=sys.argv[1]\ntry:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:300])\n\" \"$s\"; done; git log --oneline -1", "description": "Reproduce MySQL quoted index name failures"}
[tool_result] ERR ParseError Expecting ). Line 1, Col: 42.
  CREATE TABLE t (a INT, UNIQUE KEY [4m`Unique`[0m (a))
CREATE TABLE t (b INT, INDEX `Index` (b))
ERR ParseError Expecting ). Line 1, Col: 41.
  CREATE TABLE t (c INT, UNIQUE INDEX [4m`Key`[0m (c))
CREATE TABLE t (a INT, CONSTRAINT `Unique` UNIQUE (a))
CREATE TABLE t (a INT, INDEX `Primary` (a))
c17ddcce8 lithify: probe base
[assistant] The failure is in `_parse_unique_key`: it checks the token's text against `CONSTRAINT_PARSERS`, so a backtick-quoted `` `Unique` `` or `` `Key` `` is treated as a following constraint keyword and skipped. `_parse_unnamed_constraint` already avoids this by excluding `IDENTIFIER` tokens, so I'll apply the same rule here.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135316-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)", "new_string": "        if (\n            self._curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-135316-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in 'CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))' 'CREATE TABLE t (b INT, KEY `Index` (b))' 'CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c))' 'CREATE TABLE t (a INT UNIQUE PRIMARY KEY)' 'CREATE TABLE t (a INT, UNIQUE KEY CHECK (a > 0))'; do $PY -c \"\nimport sys, sqlglot\ns=sys.argv[1]\ntry:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\nexcept Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\" \"$s\"; done; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify fix and run full test suite"}
[tool_result] CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (b INT, INDEX `Index` (b))
CREATE TABLE t (c INT, UNIQUE `Key` (c))
CREATE TABLE t (a INT UNIQUE PRIMARY KEY)
ERR ParseError Expecting ). Line 1, Col: 39.
  CREATE TABLE t (a INT, UNIQUE KEY [4mCHECK[0m (a > 0))
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 54.97s
[assistant] Quoted names now parse and the full suite passes (1087 tests). The output drops the `KEY`/`INDEX` keyword, though, and the issue asks for round-tripping. I'll check whether that's existing behaviour for unquoted names too.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (a INT, UNIQUE KEY foo (a))','CREATE TABLE t (a INT, UNIQUE INDEX foo (a))','CREATE TABLE t (a INT, UNIQUE KEY \\`Unique\\` (a))']:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n\"; grep -n \"def uniquecolumnconstraint_sql\" -A12 sqlglot/generator.py | head -30; grep -n \"class UniqueColumnConstraint\" -A3 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null | head", "description": "Check unquoted KEY/INDEX round-trip and generator"}
[tool_result] CREATE TABLE t (a INT, UNIQUE foo (a))
CREATE TABLE t (a INT, UNIQUE foo (a))
CREATE TABLE t (a INT, UNIQUE `Unique` (a))
1240:    def uniquecolumnconstraint_sql(self, expression: exp.UniqueColumnConstraint) -> str:
1241-        this = self.sql(expression, "this")
1242-        this = f" {this}" if this else ""
1243-        index_type = expression.args.get("index_type")
1244-        index_type = f" USING {index_type}" if index_type else ""
1245-        on_conflict = self.sql(expression, "on_confl
…[272 chars elided]…
" {options}" if options else ""
1250-        return f"UNIQUE{nulls_sql}{this}{index_type}{on_conflict}{options}"
1251-
1252-    def inoutcolumnconstraint_sql(self, expression: exp.InOutColumnConstraint) -> str:
sqlglot/expressions/constraints.py:167:class UniqueColumnConstraint(Expression, ColumnConstraintKind):
sqlglot/expressions/constraints.py-168-    arg_types = {
sqlglot/expressions/constraints.py-169-        "this": False,
sqlglot/expressions/constraints.py-170-        "index_type": False,
[tool_use Bash] {"command": "grep -rn \"UNIQUE KEY\\|UNIQUE INDEX\" tests/dialects/test_mysql.py | head; grep -n \"UNIQUE\" tests/dialects/test_mysql.py | head -20", "description": "Check existing MySQL tests for UNIQUE KEY"}
[tool_result] tests/dialects/test_mysql.py:140:            "CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`id`), UNIQUE KEY `id` (`id`))",
tests/dialects/test_mysql.py:144:            "CREATE TABLE IF NOT EXISTS industry_info (a BIGINT(20) NOT NULL AUTO_INCREMENT, b BIGINT(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE KEY d (b), KEY e (b))",
tests/dialects/test_mysql.py:164:            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
10 matches in 1 files:

te
…[584 chars elided]…
..d` CHAR(36) NOT NULL DEFAULT (UUID()), PRIMARY KEY (`id`), UNIQUE `id` (`id`))",
tests/dialects/test_mysql.py:144:...T(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE KEY d (b), KEY e (b))",
tests/dialects/test_mysql.py:145:...INT(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE d (b), INDEX e (b))",
tests/dialects/test_mysql.py:164:"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
tests/dialects/test_mysql.py:165:"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
[assistant] The existing tests (`test_mysql.py:140-165`) already expect `UNIQUE KEY`/`UNIQUE INDEX` to render without the keyword, so the output is consistent with the project. I'll add regression tests next to those.
[tool_use Bash] {"command": "sed -n 158,172p tests/dialects/test_mysql.py", "description": "View MySQL test context around UNIQUE INDEX"}
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-135316-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n\n        self.validate_all(", "new_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )
…[134 chars elided]…
NT, UNIQUE `Unique` (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (b INT, KEY `Index` (b))\",\n            \"CREATE TABLE t (b INT, INDEX `Index` (b))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (c INT, UNIQUE INDEX `Key` (c))\",\n            \"CREATE TABLE t (c INT, UNIQUE `Key` (c))\",\n        )\n\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-135316-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -1; git status --short; git diff --stat; (ruff --version >/dev/null 2>&1 && ruff check sqlglot/parser.py tests/dialects/test_mysql.py && ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -3", "description": "Run full test suite and lint the changes"}
[tool_result] ............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 55.56s
50 passed, 481 subtests passed in 0.17s
 M sqlglot/parser.py
 M tests/dialects/test_mysql.pysqlglot/parser.py            |  6 +++++-
 tests/dialects/test_mysql.py | 12 ++++++++++++
 2 files changed, 17 insertions(+), 1 deletion(-)
Ruff: No issues found
2 files already formatted
[assistant] MySQL now accepts backtick-quoted index names that look like keywords in `UNIQUE KEY`/`UNIQUE INDEX` table constraints. The full test suite passes (1087 tests) and ruff is clean.

**Cause:** `_parse_unique_key` in `sqlglot/parser.py` skipped any token whose text matched a constraint keyword. That also caught a quoted identifier such as `` `Unique` `` or `` `Key` ``, so the name was never consumed and parsing failed at the `(`.

**Fix:** the check now ignores `IDENTIFIER` tokens, the same rule `_parse_unnamed_constraint` already uses. Unquoted keywords are still rejected as names, so `UNIQUE PR
…[268 chars elided]…
it already was for unquoted names and as the existing MySQL tests expect:

- `UNIQUE KEY `Unique` (a)` → ``UNIQUE `Unique` (a)``
- `KEY `Index` (b)` → ``INDEX `Index` (b)``
- `UNIQUE INDEX `Key` (c)` → ``UNIQUE `Key` (c)``

The output is valid MySQL and re-parses to the same AST, but it is not byte-identical to the input. If you want the keyword kept, that's a generator change and a rewrite of the existing expectations, so I left it alone.

**Tests:** I added three `validate_identity` cases to `tests/dialects/test_mysql.py`, next to the existing `UNIQUE INDEX` cases. I did not commit anything.
