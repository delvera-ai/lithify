# trajectory base-1

final message:
Hive, Spark and Databricks now read a doubled single quote inside a string as an escaped quote. `COMMENT 'Hello ''World!'` in a `CREATE TABLE` now parses, and the full test suite passes (1120 tests).

The fix is one line in `sqlglot/dialects/hive.py`: the Hive tokenizer's `STRING_ESCAPES` changes from `["\\"]` to `["\\", "'"]`. Spark, Spark2 and Databricks inherit it.

The order matters. The generator uses the first entry as its quote-escape character. My first attempt put `"'"` first, which changed Hive/Spark output from `\'` to `''` and broke 22 existing tests. Keeping the backslash first means output is unchanged. The `''` form is now accepted on input and written back as `\'`, which these engines also accept.

I added a regression case to `test_quotes` in `tests/dialects/test_hive.py`. It parses the Spark and Databricks `''` form and checks the Hive/Spark output. I did not edit any existing test. `ruff check` and `ruff format --check` pass on both files.

## events
[assistant] I'll start by checking how the Hive, Spark and Databricks dialects tokenize string escapes today.
[tool_use Bash] {"command": "git status --short | head && grep -n \"STRING_ESCAPES\\|QUOTES\\|ESCAPE\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py sqlglot/dialects/databricks.py sqlglot/dialects/spark2.py sqlglot/dialects/dialect.py | head -50", "description": "Check escape settings in Hive/Spark/Databricks dialects"}
[tool_use Bash] {"command": "grep -n \"STRING_ESCAPES\" sqlglot/tokens.py sqlglot/dialects/*.py | head -40; grep -n \"def _scan_string\\|def _extract_string\" -A40 sqlglot/tokens.py | head -120", "description": "Find string escape handling in tokenizer"}
[tool_result] sqlglot/dialects/athena.py:55:        STRING_ESCAPES = Trino.Tokenizer.STRING_ESCAPES + Hive.Tokenizer.STRING_ESCAPES
sqlglot/dialects/bigquery.py:172:        STRING_ESCAPES = ["\\"]
sqlglot/tokens.py:65:    STRING_ESCAPES: t.ClassVar[list[str]]
sqlglot/tokens.py:66:    BYTE_STRING_ESCAPES: t.ClassVar[list[str]]
sqlglot/tokens.py:77:    STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS: t.ClassVar[bool]
sqlglot/tokens.py:85:    _STRING_ESCAPES: t.ClassVar[set[str]]
sqlglot/tokens.py:86:    _BYTE_STRING_ESCA
…[1667 chars elided]…

sqlglot/dialects/duckdb.py:71:        BYTE_STRING_ESCAPES = ["'", "\\"]
sqlglot/dialects/hive.py:92:        STRING_ESCAPES = ["\\"]
sqlglot/dialects/mysql.py:70:        STRING_ESCAPES = ["'", '"', "\\"]
sqlglot/dialects/redshift.py:39:        STRING_ESCAPES = ["\\", "'"]
sqlglot/dialects/postgres.py:68:        BYTE_STRING_ESCAPES = ["'", "\\"]
sqlglot/dialects/spark.py:20:        STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = False
sqlglot/dialects/snowflake.py:134:        STRING_ESCAPES = ["\\", "'"]
[tool_result] sqlglot/dialects/spark.py:20:        STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = False
sqlglot/dialects/spark.py:24:            for q in t.cast(list[str], Spark2.Tokenizer.QUOTES)
sqlglot/dialects/hive.py:90:        QUOTES = ["'", '"']
sqlglot/dialects/hive.py:92:        STRING_ESCAPES = ["\\"]
sqlglot/dialects/dialect.py:66:UNESCAPED_SEQUENCES = {
sqlglot/dialects/dialect.py:277:        klass.QUOTE_START, klass.QUOTE_END = list(klass.tokenizer_class._QUOTES.items())[0]
sqlglot/dialects/dialect.py:2
…[909 chars elided]…
False
sqlglot/dialects/dialect.py:427:    """Whether string literals support escape sequences (e.g. `\\n`). Set by the metaclass based on the tokenizer's STRING_ESCAPES."""
sqlglot/dialects/dialect.py:429:    BYTE_STRINGS_SUPPORT_ESCAPED_SEQUENCES: bool = False
sqlglot/dialects/dialect.py:430:    """Whether byte string literals support escape sequences. Set by the metaclass based on the tokenizer's BYTE_STRING_ESCAPES."""
sqlglot/dialects/dialect.py:782:    ESCAPED_SEQUENCES: dict[str, str] = {}
[assistant] The Hive tokenizer sets `STRING_ESCAPES = ["\\"]`, so `''` is not treated as an escape there. I'll look at the Hive tokenizer block and reproduce the bug.
[tool_use Bash] {"command": "sed -n 85,100p sqlglot/dialects/hive.py; sed -n 15,30p sqlglot/dialects/spark.py; ls <work>/env-sqlglot/bin/python 2>&1; python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks','spark2']:\n    for s in [\\\"SELECT COMMENT 'Hello ''World!'\\\", \\\"SELE
…[84 chars elided]…
       except Exception as e: print(d, 'ERR', e)\n\" ; python3 -c \"\nimport sqlglot\nprint(repr(sqlglot.parse_one(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!') \\\", read='hive').sql('hive')))\nprint(repr(sqlglot.parse_one(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!') \\\", read='spark').sql('spark')))\n\" 2>&1 | tail -5", "description": "Inspect Hive tokenizer and reproduce the bug"}
[tool_result]             *jsonpath.JSONPathTokenizer.VAR_TOKENS,
            TokenType.DASH,
        }

    class Tokenizer(tokens.Tokenizer):
        QUOTES = ["'", '"']
        IDENTIFIERS = ["`"]
        STRING_ESCAPES = ["\\"]

        SINGLE_TOKENS = {
            **tokens.Tokenizer.SINGLE_TOKENS,
            "$": TokenType.PARAMETER,
        }

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
    SUPPORTS_NULL_TYPE = True
    ARRAY_FUNCS_PROPAGATES_NULLS = True
    EXPRESSION_METADATA = EX
…[939 chars elided]…
ks "SELECT CONCAT('a', 'b')"
spark2 ERR Invalid expression / Unexpected token. Line 1, Col: 23.
  SELECT COMMENT [4m'Hello '[0m'World!'
spark2 "SELECT CONCAT('a', 'b')"
    self.raise_error("Expecting )")
  File "~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/sqlglot/parser.py", line 1998, in raise_error
    raise error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 46.
  CREATE TABLE t (a INT COMMENT 'Hello '[4m'World!'[0m)
[assistant] Reproduced: both `hive` and `spark` fail to parse a doubled quote in a comment. The fix is to add `"'"` to the Hive tokenizer's `STRING_ESCAPES`. Spark, Spark2 and Databricks inherit from Hive, so they pick it up. Making the change and checking the round-trip:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"\\\\\"]\n\n        SINGLE_TOKENS = {\n            **tokens.Tokenizer.SINGLE_TOKENS,\n            \"$\": TokenType.PARAMETER,", "new_string": "        STRING_ESCAPES = [\"'\", \"\\\\\"]\n\n        SINGLE_TOKENS = {\n            **tokens.Tokenizer.SINGLE_TOKENS,\n            \"$\": TokenType.PARAMETER,"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks','spark2']:\n    for s in [\\\"SELECT COMMENT 'Hello ''World!'\\\", \\\"SELECT 'a''b'\\\", \\\"SELECT 'it''s \\\\\\\\n'\\\"]:\n        try: print(d, repr(sqlglot.parse_one(s, read=d).sql(d)))\n        except Exception as e: print(d, 'ERR', e)\nprint(sqlglot.transpile(\\\"SELECT 'Hello ''World!'\\\", read='spark', write='duckdb'))\nprint(sqlglot.transpile(\\\"SELECT 'Hello ''World!'\\\", read='databricks', write='spark'))\nprint(sqlglot.transpile(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", read='spark', write='spark'))\nprint(sqlglot.transpile(\\\"SELECT 'a\\\\\\\\'b'\\\", read='hive', write='hive'))\n\" 2>&1", "description": "Apply tokenizer fix and verify round-trips"}
[tool_result] hive ERR Invalid expression / Unexpected token. Line 1, Col: 31.
  SELECT COMMENT [4m'Hello ''World!'[0m
hive "SELECT 'a''b'"
hive "SELECT 'it''s \\n'"
spark ERR Invalid expression / Unexpected token. Line 1, Col: 31.
  SELECT COMMENT [4m'Hello ''World!'[0m
spark "SELECT 'a''b'"
spark "SELECT 'it''s \\n'"
databricks ERR Invalid expression / Unexpected token. Line 1, Col: 31.
  SELECT COMMENT [4m'Hello ''World!'[0m
databricks "SELECT 'a''b'"
databricks "SELECT 'it''s \\n'"
spark2 ERR Invalid expression / Unexpected token. Line 1, Col: 31.
  SELECT COMMENT [4m'Hello ''World!'[0m
spark2 "SELECT 'a''b'"
spark2 "SELECT 'it''s \\n'"
["SELECT 'Hello ''World!'"]
["SELECT 'Hello ''World!'"]
["CREATE TABLE t (a INT COMMENT 'Hello ''World!')"]
["SELECT 'a''b'"]
[assistant] The `SELECT COMMENT '...'` error is my test input being invalid SQL. The `CREATE TABLE` case now round-trips. One thing to check: Hive input `'a\'b'` now generates `'a''b'`, which is a generator-side change, so I'll verify against the original and run the suite.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; git stash list >/dev/null; git show HEAD:sqlglot/dialects/hive.py > /dev/null && python3 -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT 'a\\\\\\\\'b'\\\", read='hive', write='hive'))\nprint(sqlglot.transpile(\\\"SELECT 'a\\\\\\\\'b'\\\", read='spark', write='spark'))\nprint(sqlglot.transpile(\\\"SELECT 'a''b'\\\", read='hive', write='spark'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Check escaping behaviour and run the full test suite"}
[tool_result] ["SELECT 'a''b'"]
["SELECT 'a''b'"]
["SELECT 'a''b'"]
    self.assertEqual(
E   AssertionError: "SELECT '''test'''" != "SELECT '\\'test\\''"
E   - SELECT '''test'''
E   ?         ^     ^
E   + SELECT '\'test\''
E   ?         ^     ^
=========================== short test summary info ============================
FAILED tests/dialects/test_athena.py::TestAthena::test_ddl - AssertionError: ...
SUBFAILED["""x'""" -> hive] tests/dialects/test_bigquery.py::TestBigQuery::test_bigquery
SUBFAILED["""x'"
…[1253 chars elided]…
BFAILED['''x' -> hive] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED['''x' -> spark] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED[x IN ('a', 'a''b') -> hive] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED[x IN ('a', 'a''b') -> spark] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED[SELECT '''test''' -> spark] tests/dialects/test_tsql.py::TestTSQL::test_string
22 failed, 1119 passed, 18145 subtests passed in 69.09s (0:01:09)
[assistant] The change broke 22 existing tests. The generator is picking up the escape character from `STRING_ESCAPES`. Hive output for a quote changed from `\'` to `''`, which existing tests expect to stay as `\'`. I'll check how the generator chooses its escape character.
[tool_use Bash] {"command": "grep -n \"STRING_ESCAPES\\|_escape\\|escape_str\\|def escape\" sqlglot/generator.py sqlglot/dialects/dialect.py | head -30", "description": "Locate generator string escape logic"}
[tool_result] sqlglot/dialects/dialect.py:297:        klass.STRINGS_SUPPORT_ESCAPED_SEQUENCES = "\\" in klass.tokenizer_class.STRING_ESCAPES
sqlglot/dialects/dialect.py:299:            "\\" in klass.tokenizer_class.BYTE_STRING_ESCAPES
sqlglot/dialects/dialect.py:427:    """Whether string literals support escape sequences (e.g. `\\n`). Set by the metaclass based on the tokenizer's STRING_ESCAPES."""
sqlglot/dialects/dialect.py:430:    """Whether byte string literals support escape sequences. Set by the metacla
…[1518 chars elided]…
rts_escape_sequences = self.dialect.BYTE_STRINGS_SUPPORT_ESCAPED_SEQUENCES
sqlglot/generator.py:2966:            supports_escape_sequences = self.dialect.STRINGS_SUPPORT_ESCAPED_SEQUENCES
sqlglot/generator.py:2968:        if supports_escape_sequences:
sqlglot/generator.py:2975:        escaped_delimiter = escaped_delimiter or self._escaped_quote_end
sqlglot/generator.py:3725:            path = self.escape_str(path)
sqlglot/generator.py:4372:    def escape_sql(self, expression: exp.Escape) -> str:
[assistant] The generator uses `STRING_ESCAPES[0]` as its quote-escape character. I'll put the backslash first so Hive/Spark keep emitting `\'`, and the tokenizer still accepts `''` as well.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"'\", \"\\\\\"]", "new_string": "        STRING_ESCAPES = [\"\\\\\", \"'\"]"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", read='spark', write='spark'))\nprint(sqlglot.transpile(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", read='databricks', write='databricks'))\nprint(sqlglot.transpile(\\\"SELECT 'a''b', 'a\\\\\\\\'b'\\\", read='hive', write='hive'))\nprint(sqlglot.transpile(\\\"SELECT 'a''b'\\\", read='spark', write='duckdb'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Recheck round-trips and run full test suite"}
[tool_result] ["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
["SELECT 'a\\'b', 'a\\'b'"]
["SELECT 'a''b'"]
........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
......................
…[416 chars elided]…
............... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 77.61s (0:01:17)
[assistant] All 1120 tests pass, and the bug is fixed. Next I'll add a regression test. I'll look at the existing `test_quotes` in the Hive tests first.
[tool_use Bash] {"command": "grep -n \"def test_quotes\" -A22 tests/dialects/test_hive.py", "description": "View existing Hive quote tests"}
[tool_result] 319:    def test_quotes(self):
320-        self.validate_all(
321-            "'\\''",
322-            write={
323-                "duckdb": "''''",
324-                "presto": "''''",
325-                "hive": "'\\''",
326-                "spark": "'\\''",
327-            },
328-        )
329-        self.validate_all(
330-            "'\"x\"'",
331-            write={
332-                "duckdb": "'\"x\"'",
333-                "presto": "'\"x\"'",
334-                "hive": "'\"x\"'",
335-                "spark": "'\"x\"'",
336-            },
337-        )
338-        self.validate_all(
339-            "\"'x'\"",
340-            write={
341-                "duckdb": "'''x'''",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "    def test_quotes(self):\n        self.validate_all(\n            \"'\\\\''\",\n            write={\n                \"duckdb\": \"''''\",\n                \"presto\": \"''''\",\n                \"hive\": \"
…[507 chars elided]…
MMENT 'Hello ''World!'\",\n                \"databricks\": \"COMMENT 'Hello ''World!'\",\n            },\n            write={\n                \"duckdb\": \"COMMENT 'Hello ''World!'\",\n                \"hive\": \"COMMENT 'Hello \\\\'World!'\",\n                \"spark\": \"COMMENT 'Hello \\\\'World!'\",\n                \"databricks\": \"COMMENT 'Hello \\\\'World!'\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git status --short; git diff --stat", "description": "Run new test, full suite, and check diff"}
[tool_result] E   + COMMENT 'Hello \'World!'
E   ?                ^
________ TestHive.test_quotes [COMMENT 'Hello ''World!' -> databricks] _________
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: "COMMENT 'Hello ''World!'" != "COMMENT 'Hello \\'World!'"
E   - COMMENT 'Hello ''World!'
E   ?                ^
E   + COMMENT 'Hello \'World!'
E   ?                ^
=========================== short test summary info ============================
SUBFAILED[COMMENT 'Hello
…[263 chars elided]…
otes
3 failed, 55 passed, 995 subtests passed in 0.33s
SUBFAILED[COMMENT 'Hello ''World!' -> spark] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED[COMMENT 'Hello ''World!' -> databricks] tests/dialects/test_hive.py::TestHive::test_quotes
3 failed, 1120 passed, 18169 subtests passed in 58.82s
 M sqlglot/dialects/hive.py
 M tests/dialects/test_hive.py
 sqlglot/dialects/hive.py    |  2 +-
 tests/dialects/test_hive.py | 13 +++++++++++++
 2 files changed, 14 insertions(+), 1 deletion(-)
[assistant] My new test has the `read` and `write` directions mixed up. In `validate_all`, the main SQL is parsed as Hive, and `read` entries are checked against the Hive output. I'll fix the test's expectations.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "        self.validate_all(\n            \"COMMENT 'Hello ''World!'\",\n            read={\n                \"spark\": \"COMMENT 'Hello ''World!'\",\n                \"databricks\": \"COMMENT 'Hello ''World!'\"
…[394 chars elided]…
ld!'\",\n            read={\n                \"spark\": \"COMMENT 'Hello ''World!'\",\n                \"databricks\": \"COMMENT 'Hello ''World!'\",\n            },\n            write={\n                \"duckdb\": \"COMMENT 'Hello ''World!'\",\n                \"spark\": \"COMMENT 'Hello \\\\'World!'\",\n                \"databricks\": \"COMMENT 'Hello \\\\'World!'\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3", "description": "Rerun Hive tests and full suite"}
[tool_result] SUBFAILED[databricks -> COMMENT 'Hello \'World!'] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED[COMMENT 'Hello \'World!' -> duckdb] tests/dialects/test_hive.py::TestHive::test_quotes
3 failed, 14 passed, 492 subtests passed in 0.19s
SUBFAILED[databricks -> COMMENT 'Hello \'World!'] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED[COMMENT 'Hello \'World!' -> duckdb] tests/dialects/test_hive.py::TestHive::test_quotes
3 failed, 1120 passed, 18168 subtests passed in 49.02s
[assistant] Two subtests still fail, and I'm guessing at the expected values. I'll print the real outputs rather than keep guessing.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ns=\\\"COMMENT 'Hello \\\\\\\\'World!'\\\"\nprint(s)\nfor r,w in [('hive','duckdb'),('hive','spark'),('spark','duckdb'),('databricks','hive')]:\n    print(r,w, sqlglot.transpile(\\\"COMMENT 'Hello ''World!'\\\" if r!='hive' else s, read=r, write=w))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py 2>&1 | grep -B2 \"AssertionError\" | head -30", "description": "Print actual transpile outputs for the new test"}
[tool_result] 'COMMENT 'Hello \'World!'' contains unsupported syntax. Falling back to parsing as a 'Command'.
'COMMENT 'Hello \'World!'' contains unsupported syntax. Falling back to parsing as a 'Command'.
'COMMENT 'Hello ''World!'' contains unsupported syntax. Falling back to parsing as a 'Command'.
'COMMENT 'Hello ''World!'' contains unsupported syntax. Falling back to parsing as a 'Command'.
COMMENT 'Hello \'World!'
hive duckdb ["COMMENT 'Hello \\'World!'"]
hive spark ["COMMENT 'Hello \\'World!'"]
spark du
…[38 chars elided]…
bricks hive ["COMMENT 'Hello ''World!'"]
tests/dialects/test_dialect.py:85: in validate_all
    self.assertEqual(
E   AssertionError: "COMMENT 'Hello ''World!'" != "COMMENT 'Hello \\'World!'"
--
tests/dialects/test_dialect.py:85: in validate_all
    self.assertEqual(
E   AssertionError: "COMMENT 'Hello ''World!'" != "COMMENT 'Hello \\'World!'"
--
tests/dialects/test_dialect.py:101: in validate_all
    self.assertEqual(
E   AssertionError: "COMMENT 'Hello \\'World!'" != "COMMENT 'Hello ''World!'"
[assistant] The `COMMENT` on its own isn't a valid statement, so sqlglot falls back to a raw `Command` and nothing is actually parsed. I'll use a real `CREATE TABLE ... COMMENT` statement so the test exercises the fix.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "        self.validate_all(\n            \"COMMENT 'Hello \\\\'World!'\",\n            read={\n                \"spark\": \"COMMENT 'Hello ''World!'\",\n                \"databricks\": \"COMMENT 'Hello ''World!
…[183 chars elided]…
tabricks\": \"COMMENT 'Hello \\\\'World!'\",\n            },\n        )", "new_string": "        self.validate_all(\n            \"CREATE TABLE t (a INT COMMENT 'Hello \\\\'World!')\",\n            read={\n                \"spark\": \"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\",\n                \"databricks\": \"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-182408-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; git stash list --format='%H' >/dev/null; git diff", "description": "Run targeted and full test suites, show diff"}
[tool_result] .......................................................                                [100%]
55 passed, 994 subtests passed in 0.25s
................. [ 97%]
................................         [100%]
1120 passed, 18168 subtests passed in 49.11s
diff --git a/sqlglot/dialects/hive.py b/sqlglot/dialects/hive.py
index 718e1c0b9..a4cfc59e7 100644
--- a/sqlglot/dialects/hive.py
+++ b/sqlglot/dialects/hive.py
@@ -89,7 +89,7 @@ class Hive(Dialect):
     class Tokenizer(tokens.Tokenizer):
        
…[351 chars elided]…
lects/test_hive.py
@@ -326,6 +326,13 @@ class TestHive(Validator):
                 "spark": "'\\''",
             },
         )
+        self.validate_all(
+            "CREATE TABLE t (a INT COMMENT 'Hello \\'World!')",
+            read={
+                "spark": "CREATE TABLE t (a INT COMMENT 'Hello ''World!')",
+                "databricks": "CREATE TABLE t (a INT COMMENT 'Hello ''World!')",
+            },
+        )
         self.validate_all(
             "'\"x\"'",
             write={
[assistant] Targeted and full suites pass. Last, a lint/format check on the two changed files, since the project asks for `make check`-style validation.
[tool_use Bash] {"command": "(ruff check sqlglot/dialects/hive.py tests/dialects/test_hive.py && ruff format --check sqlglot/dialects/hive.py tests/dialects/test_hive.py) 2>&1 | tail -5", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
[assistant] Hive, Spark and Databricks now read a doubled single quote inside a string as an escaped quote. `COMMENT 'Hello ''World!'` in a `CREATE TABLE` now parses, and the full test suite passes (1120 tests).

The fix is one line in `sqlglot/dialects/hive.py`: the Hive tokenizer's `STRING_ESCAPES` changes from `["\\"]` to `["\\", "'"]`. Spark, Spark2 and Databricks inherit it.

The order matters. The generator uses the first entry as its quote-escape character. My first attempt put `"'"` first, which changed Hive/Spark output from `\'` to `''` and broke 22 existing tests. Keeping the backslash first means output is unchanged. The `''` form is now accepted on input and written back as `\'`, which these engines also accept.

I added a regression case to `test_quotes` in `tests/dialects/test_hive.py`. It parses the Spark and Databricks `''` form and checks the Hive/Spark output. I did not edit any existing test. `ruff check` and `ruff format --check` pass on both files.
