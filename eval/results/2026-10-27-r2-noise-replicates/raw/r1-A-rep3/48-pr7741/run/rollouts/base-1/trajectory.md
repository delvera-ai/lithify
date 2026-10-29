# trajectory base-1

final message:
Hive, Spark and Databricks now read `''` inside a string literal as an escaped single quote. The full suite passes (1121 tests), including the new regression tests.

The fix is one line in `sqlglot/dialects/hive.py`. Hive's `STRING_ESCAPES` was `["\\"]`, so the tokenizer ended the string at the first `'`. It is now `["\\", "'"]`. Spark, Spark2 and Databricks inherit this, and Athena's escape set is unchanged.

The round-trip is semantic, not textual. `COMMENT 'Hello ''World!'` now parses correctly, but the Hive-family generators emit `COMMENT 'Hello \'World!'`. I kept the `\'` output because the generator takes its quote escape from `STRING_ESCAPES[0]`. Putting `'` first made it emit `''`, but that broke 22 existing tests that pin `\'` output. I did not edit those tests, so I left the generator alone. If you want `''` as the output form, that is a separate change that means updating those expectations.

I added regression tests to `tests/dialects/test_hive.py` (`test_doubled_quote_escape`) and `tests/dialects/test_databricks.py`. Nothing is committed.

## events
[tool_use Bash] {"command": "grep -n \"STRING_ESCAPES\\|QUOTES\\|class Tokenizer\" sqlglot/dialects/hive.py sqlglot/dialects/spark.py sqlglot/dialects/spark2.py sqlglot/dialects/databricks.py sqlglot/dialects/dialect.py sqlglot/tokens.py | head -50; git log --oneline -1", "description": "Find string escape settings in dialect files"}
[tool_result] sqlglot/dialects/spark2.py:20:    class Tokenizer(Hive.Tokenizer):
sqlglot/dialects/spark.py:19:    class Tokenizer(Spark2.Tokenizer):
sqlglot/dialects/spark.py:20:        STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = False
sqlglot/dialects/spark.py:24:            for q in t.cast(list[str], Spark2.Tokenizer.QUOTES)
sqlglot/dialects/databricks.py:31:    class Tokenizer(Spark.Tokenizer):
sqlglot/dialects/hive.py:89:    class Tokenizer(tokens.Tokenizer):
sqlglot/dialects/hive.py:90:        QUOTES = ["'",
…[2158 chars elided]…
 "\\" in klass.tokenizer_class.STRING_ESCAPES
sqlglot/dialects/dialect.py:299:            "\\" in klass.tokenizer_class.BYTE_STRING_ESCAPES
sqlglot/dialects/dialect.py:427:    """Whether string literals support escape sequences (e.g. `\\n`). Set by the metaclass based on the tokenizer's STRING_ESCAPES."""
sqlglot/dialects/dialect.py:430:    """Whether byte string literals support escape sequences. Set by the metaclass based on the tokenizer's BYTE_STRING_ESCAPES."""
4497ec8fb lithify: probe base
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['hive','spark','spark2','databricks']:\n    e = sqlglot.parse_one(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!') \\\", read=d)\n    print(d, repr(e.sql(d)))\n    print(repr(sqlglot.parse_one(\\\"SELECT 'Hello ''World!'\\\", read=d).sql(d)))\n\"", "description": "Reproduce doubled-quote parsing in Hive/Spark/Databricks"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/__init__.py", line 160, in parse_one
    result = dialect.parse(sql, **opts)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/dialect.py", line 1124, in parse
    r
…[1944 chars elided]…
en()
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/parser.py", line 9406, in _match_r_paren
    self.raise_error("Expecting )")
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/parser.py", line 1998, in raise_error
    raise error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 46.
  CREATE TABLE t (a INT COMMENT 'Hello '[4m'World!'[0m)
[assistant] Reproduced: in Hive the tokenizer ends the string at the first `'` because `''` isn't an escape there. Let me look at the Hive, Spark and Databricks tokenizers.
[tool_use Bash] {"command": "sed -n 86,100p sqlglot/dialects/hive.py; echo ---; sed -n 15,40p sqlglot/dialects/spark.py; echo ---; sed -n 28,45p sqlglot/dialects/databricks.py; echo ---; sed -n 18,30p sqlglot/dialects/spark2.py; echo ---; grep -rn \"STRING_ESCAPES\" sqlglot/dialects/*.py | head -30", "description": "Read Hive, Spark, Databricks tokenizer settings"}
[tool_result]             TokenType.DASH,
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
---
    SUPPORTS_NULL_TYPE = True
    ARRAY_FUNCS_PROPAGATES_NULLS = True
    EXPRESSION_METADATA = EXPRESSION_METADATA.copy()

    class Tokenizer(Sp
…[1935 chars elided]…
:    """Whether byte string literals support escape sequences. Set by the metaclass based on the tokenizer's BYTE_STRING_ESCAPES."""
sqlglot/dialects/mysql.py:70:        STRING_ESCAPES = ["'", '"', "\\"]
sqlglot/dialects/postgres.py:68:        BYTE_STRING_ESCAPES = ["'", "\\"]
sqlglot/dialects/snowflake.py:134:        STRING_ESCAPES = ["\\", "'"]
sqlglot/dialects/spark.py:20:        STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = False
sqlglot/dialects/redshift.py:39:        STRING_ESCAPES = ["\\", "'"]
[assistant] Athena inherits Hive's `STRING_ESCAPES` but already includes `'` via Trino, so adding it on Hive is safe there. Before changing it, I need to check how the generator picks its escape character, since `\` is currently the first entry.
[tool_use Bash] {"command": "grep -n \"STRING_ESCAPES\\|escape\" sqlglot/generator.py | head -30; grep -n \"STRING_ESCAPES\" sqlglot/dialects/trino.py sqlglot/dialects/presto.py", "description": "Check generator escape handling"}
[tool_result] 489:    # Whether to escape keys using single quotes in JSON paths
524:    # Function used to replace escaped unicode codes in unicode strings
846:        "_escaped_quote_end",
847:        "_escaped_byte_quote_end",
848:        "_escaped_identifier_end",
892:        self._escaped_quote_end: str = (
893:            self.dialect.tokenizer_class.STRING_ESCAPES[0] + self.dialect.QUOTE_END
895:        self._escaped_byte_quote_end: str = (
896:            self.dialect.tokenizer_class.STRING_ESCAPES[0]
…[879 chars elided]…
ct.UNICODE_START or (escape and not self.SUPPORTS_UESCAPE):
1637:            this = escape_pattern.sub(self.UNICODE_SUBSTITUTE or escape_substitute, this)
1639:        return f"{left_quote}{this}{right_quote}{escape_sql}"
1643:        if "\\" in self.dialect.tokenizer_class.STRING_ESCAPES:
1646:        string = self.escape_str(string, escape_backslash=False)
1953:        text = text.replace(self._identifier_end, self._escaped_identifier_end)
2325:        escaped = self.sql(expression, "escaped")
[assistant] The generator uses `STRING_ESCAPES[0]` as the escape for embedded quotes. If I append `'` after `\`, Hive would generate `\'` instead of `''`. So I'll put `'` first, matching MySQL and ClickHouse, which keeps `\` working as an escape on input.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"\\\\\"]\n\n        SINGLE_TOKENS = {", "new_string": "        STRING_ESCAPES = [\"'\", \"\\\\\"]\n\n        SINGLE_TOKENS = {"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['hive','spark','spark2','databricks','athena']:\n    print(d, repr(sqlglot.parse_one(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", read=d).sql(d)))\n    print(d, repr(sqlglot.parse_one(\\\"SELECT 'Hello ''World!', 'a\\\\\\\\'b'\\\", read=d).sql(d)))\n\"", "description": "Edit Hive escapes and verify round-trip across dialects"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/tokenizer_core.py", line 669, in tokenize
    self._scan()
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/tokenizer_core.py", line 705, in _scan
    self._scan_keywords()
  File "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hi
…[2363 chars elided]…
Error tokenizing 'SELECT 'Hello ''World!', 'a\'b'
hive "CREATE TABLE t (a INT COMMENT 'Hello ''World!')"
hive "SELECT 'Hello ''World!', 'a''b'"
spark "CREATE TABLE t (a INT COMMENT 'Hello ''World!')"
spark "SELECT 'Hello ''World!', 'a''b'"
spark2 "CREATE TABLE t (a INT COMMENT 'Hello ''World!')"
spark2 "SELECT 'Hello ''World!', 'a''b'"
databricks "CREATE TABLE t (a INT COMMENT 'Hello ''World!')"
databricks "SELECT 'Hello ''World!', 'a''b'"
athena "CREATE TABLE t (a INT COMMENT 'Hello ''World!')"
[assistant] The Athena error comes from my test input, not the change. `'a\'b'` is invalid in Trino, and Athena's escape set is unchanged (`'` plus `\` before and after). Hive, Spark, Spark2 and Databricks all parse and round-trip `''` correctly. Next I'll run the existing suite to check for regressions.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite"}
[tool_result]     self.assertEqual(
E   AssertionError: "SELECT '''test'''" != "SELECT '\\'test\\''"
E   - SELECT '''test'''
E   ?         ^     ^
E   + SELECT '\'test\''
E   ?         ^     ^
=========================== short test summary info ============================
FAILED tests/dialects/test_athena.py::TestAthena::test_ddl - AssertionError: ...
SUBFAILED["""x'""" -> hive] tests/dialects/test_bigquery.py::TestBigQuery::test_bigquery
SUBFAILED["""x'""" -> spark] tests/dialects/test_bigquery.py::TestBigQ
…[1189 chars elided]…
_quotes
SUBFAILED['''x' -> hive] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED['''x' -> spark] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED[x IN ('a', 'a''b') -> hive] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED[x IN ('a', 'a''b') -> spark] tests/dialects/test_presto.py::TestPresto::test_quotes
SUBFAILED[SELECT '''test''' -> spark] tests/dialects/test_tsql.py::TestTSQL::test_string
22 failed, 1119 passed, 18145 subtests passed in 50.49s
[assistant] Twenty-two existing tests fail. Many of them pin Hive/Spark output to `\'` for embedded quotes. The generator takes its escape character from `STRING_ESCAPES[0]`, so my reordering changed generated SQL across the Hive family. That breaks existing expectations, and I'm not allowed to edit those tests. I'll keep `\` as the first entry so generated output is unchanged, and add `'` only as an accepted input escape.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"'\", \"\\\\\"]", "new_string": "        STRING_ESCAPES = [\"\\\\\", \"'\"]"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Revert escape order and rerun full test suite"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[254 chars elided]…
......................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 49.30s
[assistant] The full suite passes (1120 tests). Now I'll add regression tests for the Hive, Spark and Databricks cases, following the existing test style.
[tool_use Bash] {"command": "grep -n \"def test_quotes\" -A 12 tests/dialects/test_hive.py; grep -n \"def test_\\|validate_identity\\|validate_all\" tests/dialects/test_spark.py | head -20; grep -n \"def test_\" tests/dialects/test_databricks.py | head -5; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks']:\n    print(d, sqlglot.transpile(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", read=d, write=d))\n    print(d, sqlglot.transpile(\\\"SELECT 'Hello ''World!'\\\", read=d, write='duckdb'))\n\"", "description": "Inspect existing test layout and sample outputs"}
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
12:    def test_ddl(self):
13:        self.validate_identity("DAYOFWEEK(TO_DATE(x))")
14:        self.validate_identity("DA
…[1221 chars elided]…
  self.validate_all(
42:        self.validate_all(
9:    def test_databricks(self):
278:    def test_json(self):
316:    def test_datediff(self):
395:    def test_add_date(self):
420:    def test_without_as(self):
hive ["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
hive ["SELECT 'Hello ''World!'"]
spark ["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
spark ["SELECT 'Hello ''World!'"]
databricks ["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
databricks ["SELECT 'Hello ''World!'"]
[assistant] Hive, Spark and Databricks now all parse `''` as an escaped quote and generate the same `\'` output the existing tests expect. I'll add regression tests next to the existing quote and DDL tests.
[tool_use Bash] {"command": "grep -n \"    def test_time(self)\" tests/dialects/test_hive.py; sed -n 1,12p tests/dialects/test_databricks.py; sed -n 9,12p tests/dialects/test_databricks.py", "description": "Locate insertion points in dialect tests"}
[tool_result] 386:    def test_time(self):
from sqlglot import exp, transpile, parse_one
from sqlglot.errors import ParseError
from tests.dialects.test_dialect import Validator


class TestDatabricks(Validator):
    dialect = "databricks"

    def test_databricks(self):
        self.validate_identity("CREATE TABLE foo (my_arr ARRAY<STRING COLLATE UTF8_BINARY>)")
        self.validate_identity("CREATE TABLE foo (m MAP<STRING, STRING COLLATE UTF8_BINARY>)")
        self.validate_identity("SELECT CAST('a' AS STRING COLLATE UTF8_BINARY)")
    def test_databricks(self):
        self.validate_identity("CREATE TABLE foo (my_arr ARRAY<STRING COLLATE UTF8_BINARY>)")
        self.validate_identity("CREATE TABLE foo (m MAP<STRING, STRING COLLATE UTF8_BINARY>)")
        self.validate_identity("SELECT CAST('a' AS STRING COLLATE UTF8_BINARY)")
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "    def test_time(self):", "new_string": "    def test_doubled_quote_escape(self):\n        self.validate_all(\n            \"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\",\n            write={\n          
…[141 chars elided]…
\\'World!')\",\n                \"databricks\": \"CREATE TABLE t (a INT COMMENT 'Hello \\\\'World!')\",\n            },\n        )\n        self.validate_all(\n            \"SELECT 'a''b', 'a\\\\'b'\",\n            write={\n                \"hive\": \"SELECT 'a\\\\'b', 'a\\\\'b'\",\n                \"spark\": \"SELECT 'a\\\\'b', 'a\\\\'b'\",\n            },\n        )\n\n    def test_time(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_databricks.py", "old_string": "    def test_databricks(self):\n        self.validate_identity(\"CREATE TABLE foo (my_arr ARRAY<STRING COLLATE UTF8_BINARY>)\")", "new_string": "    def test_databricks(self):\n        self.validate_identity(\"CREATE TABLE foo (my_arr ARRAY<STRING COLLATE UTF8_BINARY>)\")\n        self.validate_all(\n            \"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\",\n            write={\"databricks\": \"CREATE TABLE t (a INT COMMENT 'Hello \\\\'World!')\"},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-135728-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_databricks.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py tests/dialects/test_databricks.py tests/dialects/test_spark.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git stash list | head -0; git status --short", "description": "Run dialect tests and full suite, check status"}
[tool_result] ........................................................                           [100%]
56 passed, 998 subtests passed in 0.27s
.......................................................................    [100%]
1121 passed, 18172 subtests passed in 50.77s
head: illegal line count -- 0
 M sqlglot/dialects/hive.py
 M tests/dialects/test_databricks.py
 M tests/dialects/test_hive.py
[assistant] Hive, Spark and Databricks now read `''` inside a string literal as an escaped single quote. The full suite passes (1121 tests), including the new regression tests.

The fix is one line in `sqlglot/dialects/hive.py`. Hive's `STRING_ESCAPES` was `["\\"]`, so the tokenizer ended the string at the first `'`. It is now `["\\", "'"]`. Spark, Spark2 and Databricks inherit this, and Athena's escape set is unchanged.

The round-trip is semantic, not textual. `COMMENT 'Hello ''World!'` now parses correctly, but the Hive-family generators emit `COMMENT 'Hello \'World!'`. I kept the `\'` output because the generator takes its quote escape from `STRING_ESCAPES[0]`. Putting `'` first made it emit `''`, but that broke 22 existing tests that pin `\'` output. I did not edit those tests, so I left the generator alone. If you want `''` as the output form, that is a separate change that means updating those expectations.

I added regression tests to `tests/dialects/test_hive.py` (`test_doubled_quote_escape`) and `tests/dialects/test_databricks.py`. Nothing is committed.
