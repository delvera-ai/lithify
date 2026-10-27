# trajectory base-2

final message:
MySQL `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `Alter` whose action is the same `AutoIncrementProperty` that `CREATE TABLE` uses, and it round-trips. Before this change it fell back to a `Command`.

**Change:** one line in `sqlglot/parsers/mysql.py`. I added an `AUTO_INCREMENT` entry to the MySQL `ALTER_PARSERS`, reusing `_parse_property_assignment(exp.AutoIncrementProperty)`, the same parser `CREATE TABLE` uses.

**Tests** in `tests/dialects/test_mysql.py`:
- A round-trip identity case in the ALTER block.
- `test_alter_auto_increment`, which checks the AST: the node is `exp.Alter`, the first action is `exp.AutoIncrementProperty`, and its value is `3000000000`.

**Results:**
- `tests/dialects/test_mysql.py`: 50 passed.
- Full suite via `run_suite.py`: `SUMMARY: 1087 passed, 17844 subtests passed in 73.15s` and `EXIT: 0`, taken after the last edit.
- `ruff check` and `ruff format --check` are clean on both files.

**Not covered:** the form with a trailing option, such as `ALTER TABLE t AUTO_INCREMENT=5, ALGORITHM=INPLACE`, still falls back to a `Command`. `RENAME INDEX ... , ALGORITHM=...` has the same limitation, so this is a pre-existing gap in how single-action ALTERs take trailing options. I left it out of this change to keep it minimal; it would be a separate fix in the generic ALTER parsing.

## events
[tool_use Bash] {"command": "git status --short | head && grep -rn -i \"autoincrement\\|auto_increment\" sqlglot/ --include=*.py | head -50 && grep -n \"ALTER_PARSERS\\|def _parse_alter\\b\\|def _parse_alter_table\" sqlglot/parser.py sqlglot/parsers/mysql.py sqlglot/dialects/mysql.py", "description": "Search auto-increment handling and ALTER parsers"}
[tool_result] (eval):1: no matches found: --include=*.py
sqlglot/parser.py:1420:    ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:1434:    ALTER_ALTER_PARSERS: t.ClassVar = {
sqlglot/parser.py:8498:    def _parse_alter_table_add(self) -> list[exp.Expr]:
sqlglot/parser.py:8537:    def _parse_alter_table_alter(self) -> exp.Expr | None:
sqlglot/parser.py:8538:        if self._match_texts(self.ALTER_ALTER_PARSERS):
sqlglot/parser.py:8539:            return self.ALTER_ALTER_PARSERS[self._prev.text.upper()](self)
…[369 chars elided]…
       parser = self.ALTER_PARSERS.get(self._prev.text.upper()) if self._prev else None
sqlglot/parsers/mysql.py:253:    ALTER_PARSERS = {
sqlglot/parsers/mysql.py:254:        **parser.Parser.ALTER_PARSERS,
sqlglot/parsers/mysql.py:258:    ALTER_ALTER_PARSERS = {
sqlglot/parsers/mysql.py:259:        **parser.Parser.ALTER_ALTER_PARSERS,
sqlglot/parsers/mysql.py:304:    def _parse_alter_table_rename(self):
sqlglot/parsers/mysql.py:512:    def _parse_alter_table_alter_index(self) -> exp.AlterIndex:
[tool_use Bash] {"command": "grep -rn -i \"autoincrement\" sqlglot/ | head -40; echo ---; sed -n 245,320p sqlglot/parsers/mysql.py; echo ---; sed -n 1415,1440p sqlglot/parser.py; echo ---; sed -n 8660,8720p sqlglot/parser.py", "description": "Inspect auto-increment and ALTER parsing code"}
[tool_result] sqlglot/tokens.py:238:        "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
sqlglot/parser.py:1217:        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
sqlglot/parser.py:1327:        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py:7083:    ) -> exp.GeneratedAsIdentityColumnConstraint | exp.AutoIncrementColumnConstraint:
sqlglot/parser.py:7106:        return exp.AutoIncrementColumnConstraint()
sqlglot/generator.py:653:      
…[7003 chars elided]…
ists,
                        actions=actions,
                        only=only,
                        options=options,
                        cluster=cluster,
                        not_valid=not_valid,
                        check=check,
                        cascade=cascade,
                        iceberg=iceberg,
                    )
                )

        return self._parse_as_command(start)

    def _parse_analyze(self) -> exp.Analyze | exp.Command:
        start = self._prev
[tool_use Bash] {"command": "grep -n \"def _parse_property_assignment\" -A12 sqlglot/parser.py; grep -n \"def alter_sql\" -A40 sqlglot/generator.py | head -60; grep -n \"def _parse_property(\" -A30 sqlglot/parser.py | head -50; sed -n 35,50p sqlglot/expressions/properties.py; ls .lithify/harness/ 2>/dev/null; cat .lithify/memory.md 2>/dev/null | head -20", "description": "Read property and alter generation code"}
[tool_result] 2790:    def _parse_property_assignment(self, exp_class: type[E], **kwargs: t.Any) -> E:
2791-        self._match(TokenType.EQ)
2792-        self._match(TokenType.ALIAS)
2793-
2794-        return self.expression(exp_class(this=self._parse_unquoted_field(), **kwargs))
2795-
2796-    def _parse_properties(self, before: bool | None = None) -> exp.Properties | None:
2797-        properties = []
2798-        while True:
2799-            if before:
2800-                prop = self._parse_property_befo
…[3250 chars elided]…
mn):
2750-            key = key.to_dot() if len(key.parts) > 1 else exp.var(key.name)
2751-
2752-        value = self._parse_bitwise() or self._parse_var(any_token=True)

class ApplicationProperty(Property):
    arg_types = {}


class AutoIncrementProperty(Property):
    arg_types = {"this": True}


class AutoRefreshProperty(Property):
    arg_types = {"this": True}


class BackupProperty(Property):
    arg_types = {"this": True}

guardrails.md
memory.md
scripts
skills
system.md
tool_guidance.md
[tool_use Bash] {"command": "cat .lithify/memory.md | head -30; PY=<work>/env-sqlglot/bin/python; ls -la $PY && $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','CREATE TABLE t (a INT) AUTO_INCREMENT=3']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, repr(e)[:300]); print(e.sql('mysql'))\n\"", "description": "Check python env and current MySQL AUTO_INCREMENT behavior"}
[tool_result] cat: .lithify/memory.md: No such file or directory
lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
'ALTER TABLE t AUTO_INCREMENT=3000000000' contains unsupported syntax. Falling back to parsing as a 'Command'.
Command Command(this=ALTER, expression=TABLE t AUTO_INCREMENT=3000000000)
ALTER TABLE t AUTO_INCREMENT=3000000000
Create Create(
  this=Schema(
    this=Table(
      this=Identifier(this=t, quoted=False)),
    expressions=[
      ColumnDef(
        this=Identifier(this=a, quoted=False),
        kind=DataType(this=DType.INT, nested=False))]),
  kind=TABLE,
  replace=False,
  refresh=False,
  unique=False,
  exists=Fals
CREATE TABLE t (a INT) AUTO_INCREMENT=3
[assistant] Confirmed: today `ALTER TABLE ... AUTO_INCREMENT=...` falls back to a `Command`. I'll add a MySQL `ALTER_PARSERS` entry that reuses the same property parser as `CREATE TABLE`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/sqlglot/parsers/mysql.py", "old_string": "        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }", "new_string": "        \"AUTO_INCREMENT\": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),\n        \"MODIFY\": lambda self: self._parse_alter_table_alter(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/sqlglot/parsers/mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor s in ['ALTER TABLE t AUTO_INCREMENT=3000000000','ALTER TABLE t AUTO_INCREMENT = 5, ALGORITHM=INPLACE','ALTER TABLE db.t AUTO_INCREMENT=1']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__); print(repr(e.args['actions'])); print(e.sql('mysql'))\nprint(sqlglot.transpile('ALTER TABLE t AUTO_INCREMENT=3000000000', read='mysql', write='mysql'))\n\"; ls tests/dialects | grep -i mysql; grep -n \"ALTER TABLE\" tests/dialects/test_mysql.py | head", "description": "Verify AST and round-trip for MySQL ALTER AUTO_INCREMENT"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT = 5, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Traceback (most recent call last):
  File "<string>", line 5, in <module>
KeyError: 'actions'
Alter
[AutoIncrementProperty(
  this=Literal(this=3000000000, is_string=False))]
ALTER TABLE t AUTO_INCREMENT=3000000000
Command
test_mysql.py
32:        self.validate_identity("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
33:        self.validate_identity("ALTER TABLE t1 ADD COLUMN x
…[126 chars elided]…
lf.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
36:        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
133:            "ALTER TABLE t ADD KEY `i` (`c`)",
134:            "ALTER TABLE t ADD INDEX `i` (`c`)",
149:            "ALTER TABLE test_table ALTER COLUMN test_column SET DATA TYPE LONGTEXT",
150:            "ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT",
195:        self.validate_identity("ALTER TABLE t ALTER INDEX i INVISIBLE")
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t AUTO_INCREMENT = 5','ALTER TABLE t AUTO_INCREMENT=5, ALGORITHM=INPLACE','ALTER TABLE t ADD COLUMN x INT, ALGORITHM=INPLACE','ALTER TABLE db.t AUTO_INCREMENT=1','ALTER TABLE t AUTO_INCREMENT=3000000000, ALGORITHM=INPLACE']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, e.sql('mysql'))\n\"", "description": "Debug option-list and qualified-table variants"}
[tool_result] 'ALTER TABLE t AUTO_INCREMENT=5, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
'ALTER TABLE t AUTO_INCREMENT=3000000000, ALGORITHM=INPLACE' contains unsupported syntax. Falling back to parsing as a 'Command'.
Alter ALTER TABLE t AUTO_INCREMENT=5
Command ALTER TABLE t AUTO_INCREMENT=5, ALGORITHM=INPLACE
Alter ALTER TABLE t ADD COLUMN x INT, ALGORITHM=INPLACE
Alter ALTER TABLE db.t AUTO_INCREMENT=1
Command ALTER TABLE t AUTO_INCREMENT=3000000000, ALGORITHM=INPLACE
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['ALTER TABLE t DROP COLUMN a, ALGORITHM=INPLACE','ALTER TABLE t RENAME INDEX a TO b, ALGORITHM=INPLACE']:\n    e=sqlglot.parse_one(s,read='mysql'); print(type(e).__name__, e.sql('mysql'))\n\" 2>&1 | grep -v Falling; git stash list | head -0; git diff --stat", "description": "Check whether comma-separated options fail for other actions too"}
[tool_result] Alter ALTER TABLE t DROP COLUMN a, ALGORITHM=INPLACE
Command ALTER TABLE t RENAME INDEX a TO b, ALGORITHM=INPLACE
head: illegal line count -- 0
 sqlglot/parsers/mysql.py | 1 +
 1 file changed, 1 insertion(+)
[assistant] The bare form is what the task asks for and it now parses to an `Alter` with an `AutoIncrementProperty` action. The `, ALGORITHM=...` combo also falls back for `RENAME INDEX`, which is a pre-existing limitation of single-action parsers, so I'll leave it out of scope. Next I'll add tests next to the existing MySQL ALTER identities.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/tests/dialects/test_mysql.py", "offset": 28, "limit": 12}
[tool_result] 28	        self.validate_identity("CREATE TABLE foo (a BIGINT, FULLTEXT INDEX (b))")
29	        self.validate_identity("CREATE TABLE foo (a BIGINT, SPATIAL INDEX (b))")
30	        self.validate_identity("CREATE TABLE foo (a INT UNSIGNED ZEROFILL)")
31	        self.validate_identity("CREATE TABLE foo (a INT INVISIBLE)")
32	        self.validate_identity("ALTER TABLE t ADD COLUMN c INT INVISIBLE")
33	        self.validate_identity("ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INPLACE, LOCK=EXCLUSIVE")
34	        self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
35	        self.validate_identity("ALTER TABLE t ADD UNIQUE `i` (`c`)")
36	        self.validate_identity("ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT")
37	        self.validate_identity("ALTER VIEW v AS SELECT a, b, c, d FROM foo")
38	        self.validate_identity("ALTER VIEW v AS SELECT * FROM foo WHERE c > 100")
39	        self.validate_identity(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/tests/dialects/test_mysql.py", "old_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER VIEW v AS", "new_string": "        self.validate_identity(\"ALTER TABLE test_table MODIFY COLUMN test_column LONGTEXT\")\n        self.validate_identity(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.validate_identity(\"ALTER VIEW v AS"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Round-trip is covered. The harness also wants the AST checked, so I'll add a direct assertion on the node.
[tool_use Bash] {"command": "grep -n \"def test_\\|^from\\|^import\" tests/dialects/test_mysql.py | head -40; grep -n \"parse_one\" tests/dialects/test_mysql.py | head -5", "description": "Find test structure in MySQL test file"}
[tool_result] 1:import unittest
2:import sys
4:from sqlglot import UnsupportedError, expressions as exp
5:from sqlglot.dialects.mysql import MySQL
6:from tests.dialects.test_dialect import Validator
12:    def test_ddl(self):
238:    def test_identity(self):
380:    def test_types(self):
423:    def test_canonical_functions(self):
462:    def test_escape(self):
494:    def test_introducers(self):
523:    def test_hexadecimal_literal(self):
575:    def test_bits_literal(self):
599:    def test_string_literals(
…[809 chars elided]…
):
1403:    def test_json_object(self):
1406:    def test_is_null(self):
1411:    def test_monthname(self):
1420:    def test_safe_div(self):
1445:    def test_timestamp_trunc(self):
1375:        cmd = self.parse_one("SET SESSION x = 1")
1382:        cmd = self.parse_one("SET @@GLOBAL.x = @@GLOBAL.y")
1389:        cmd = self.parse_one("SET NAMES 'charset_name' COLLATE 'collation_name'")
1395:        cmd = self.parse_one("SET CHARSET DEFAULT")
1400:        cmd = self.parse_one("SET x = 1, y = 2")
[tool_use Bash] {"command": "sed -n 1403,1412p tests/dialects/test_mysql.py", "description": "Read a short existing test method for style"}
[tool_result]     def test_json_object(self):
        self.validate_identity("SELECT JSON_OBJECT('id', 87, 'name', 'carrot')")

    def test_is_null(self):
        self.validate_all(
            "SELECT ISNULL(x)", write={"": "SELECT (x IS NULL)", "mysql": "SELECT (x IS NULL)"}
        )

    def test_monthname(self):
        self.validate_all(
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/tests/dialects/test_mysql.py", "old_string": "    def test_json_object(self):\n        self.validate_identity(\"SELECT JSON_OBJECT('id', 87, 'name', 'carrot')\")\n", "new_string": "    def test_json_object(self):\n        self.validate_identity(\"SELECT JSON_OBJECT('id', 87, 'name', 'carrot')\")\n\n    def test_alter_auto_increment(self):\n        alter = self.parse_one(\"ALTER TABLE t AUTO_INCREMENT=3000000000\")\n        self.assertIsInstance(alter, exp.Alter)\n        self.assertIsInstance(alter.args[\"actions\"][0], exp.AutoIncrementProperty)\n        self.assertEqual(alter.args[\"actions\"][0].this.name, \"3000000000\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-183415-mysql-dialect-mysql-allows-setti/base-2/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -15; ls .lithify/harness/scripts/", "description": "Run the MySQL dialect test file"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.30s
run_suite.py
[assistant] MySQL tests pass. Now the full suite via the harness script, plus lint on the two changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -30; echo \"exit=$?\"; $PY -m ruff check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py; $PY -m ruff format --check sqlglot/parsers/mysql.py tests/dialects/test_mysql.py", "description": "Run full test suite and lint changed files", "timeout": 600000}
[tool_result] WARNING: 3 other pytest process(es) running; expect slower runs:
  34207 02-23:03:52 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  84125       00:20 <work>/env-sqlglot/b
  85065       00:02 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-f51886012e.log
ELAPSED: 74s
SUMMARY: 1087 passed, 17844 subtests passed in 73.15s (0:01:13)
EXIT: 0
exit=0
All checks passed!
2 files already formatted
[tool_use Bash] {"command": "git diff", "description": "Show final diff"}
[tool_result] diff --git a/sqlglot/parsers/mysql.py b/sqlglot/parsers/mysql.py
index c059ca66f..610b2e7ad 100644
--- a/sqlglot/parsers/mysql.py
+++ b/sqlglot/parsers/mysql.py
@@ -252,6 +252,7 @@ class MySQLParser(parser.Parser):
 
     ALTER_PARSERS = {
         **parser.Parser.ALTER_PARSERS,
+        "AUTO_INCREMENT": lambda self: self._parse_property_assignment(exp.AutoIncrementProperty),
         "MODIFY": lambda self: self._parse_alter_table_alter(),
     }
 
diff --git a/tests/dialects/test_mysql.py b/te
…[818 chars elided]…
me', 'carrot')")
 
+    def test_alter_auto_increment(self):
+        alter = self.parse_one("ALTER TABLE t AUTO_INCREMENT=3000000000")
+        self.assertIsInstance(alter, exp.Alter)
+        self.assertIsInstance(alter.args["actions"][0], exp.AutoIncrementProperty)
+        self.assertEqual(alter.args["actions"][0].this.name, "3000000000")
+
     def test_is_null(self):
         self.validate_all(
             "SELECT ISNULL(x)", write={"": "SELECT (x IS NULL)", "mysql": "SELECT (x IS NULL)"}
[assistant] MySQL `ALTER TABLE t AUTO_INCREMENT=3000000000` now parses as an `Alter` whose action is the same `AutoIncrementProperty` that `CREATE TABLE` uses, and it round-trips. Before this change it fell back to a `Command`.

**Change:** one line in `sqlglot/parsers/mysql.py`. I added an `AUTO_INCREMENT` entry to the MySQL `ALTER_PARSERS`, reusing `_parse_property_assignment(exp.AutoIncrementProperty)`, the same parser `CREATE TABLE` uses.

**Tests** in `tests/dialects/test_mysql.py`:
- A round-trip identity case in the ALTER block.
- `test_alter_auto_increment`, which checks the AST: the node is `exp.
…[135 chars elided]…
 50 passed.
- Full suite via `run_suite.py`: `SUMMARY: 1087 passed, 17844 subtests passed in 73.15s` and `EXIT: 0`, taken after the last edit.
- `ruff check` and `ruff format --check` are clean on both files.

**Not covered:** the form with a trailing option, such as `ALTER TABLE t AUTO_INCREMENT=5, ALGORITHM=INPLACE`, still falls back to a `Command`. `RENAME INDEX ... , ALGORITHM=...` has the same limitation, so this is a pre-existing gap in how single-action ALTERs take trailing options. I left it out of this change to keep it minimal; it would be a separate fix in the generic ALTER parsing.
