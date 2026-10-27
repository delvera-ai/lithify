# trajectory base-1

final message:
Hive, Spark and Databricks now parse `''` inside string literals as an escaped quote. `COMMENT 'Hello ''World!'` yields the value `Hello 'World!`. The full suite passes (1120 tests), and ruff is clean.

The change is one line in `sqlglot/dialects/hive.py`: the Hive tokenizer's `STRING_ESCAPES` becomes `["\\", "'"]`. Spark, Spark2 and Databricks inherit it.

**Round-trip caveat:** the text is not written back as `''`. It comes out as `\'`, which Hive also accepts, so the literal is the same, but the SQL text changes. For example, `SELECT 'it''s'` regenerates as `SELECT 'it\'s'`. Writing `''` would mean changing the generator, and existing tests (`test_quotes`, `test_time`, `test_hive`) require `\'` output. Those tests can't be edited under the project rules. If you want textual `''` output, those tests need to be changed by you, and I can make that change.

I added a regression test to `tests/dialects/test_hive.py::test_quotes`. It checks the parsed value of a column comment and a `SELECT` literal in the Spark dialect. It does not check the textual output.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "git status --short && ls sqlglot/dialects | grep -iE 'hive|spark|databricks' && grep -n \"ESCAPED\\|STRING_ESCAPES\\|escape\" sqlglot/dialects/hive.py sqlglot/dialects/spark.py sqlglot/dialects/spark2.py sqlglot/dialects/databricks.py sqlglot/tokens.py | head -50", "description": "Check repo state and find escape handling in dialects"}
[tool_result] databricks.py
hive.py
spark.py
spark2.py
sqlglot/dialects/hive.py:92:        STRING_ESCAPES = ["\\"]
sqlglot/dialects/spark.py:20:        STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = False
sqlglot/tokens.py:65:    STRING_ESCAPES: t.ClassVar[list[str]]
sqlglot/tokens.py:66:    BYTE_STRING_ESCAPES: t.ClassVar[list[str]]
sqlglot/tokens.py:77:    STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS: t.ClassVar[bool]
sqlglot/tokens.py:85:    _STRING_ESCAPES: t.ClassVar[set[str]]
sqlglot/tokens.py:86:    _BYTE_STRING_ESC
…[1069 chars elided]…
py:572:            string_escapes=self._STRING_ESCAPES,
sqlglot/tokens.py:573:            byte_string_escapes=self._BYTE_STRING_ESCAPES,
sqlglot/tokens.py:574:            identifier_escapes=self._IDENTIFIER_ESCAPES,
sqlglot/tokens.py:575:            escape_follow_chars=self._ESCAPE_FOLLOW_CHARS,
sqlglot/tokens.py:585:            string_escapes_allowed_in_raw_strings=self.STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS,
sqlglot/tokens.py:592:            unescaped_sequences=self.dialect.UNESCAPED_SEQUENCES,
[assistant] The skill's guidance is that I should reproduce the failure before changing anything, so I'll run the example first.
[tool_use Bash] {"command": "ls <work>/env-sqlglot/bin/python 2>/dev/null; for d in hive spark databricks spark2; do echo \"== $d\"; PYTHONPATH=. python3 -c \"\nimport sqlglot\ns=\\\"CREATE TABLE t (a STRING COMMENT 'Hello ''World!') \\\"\nfor q in [\\\"SELECT 'Hello ''World!'\\\", s]:\n    tr
…[5 chars elided]…
       e=sqlglot.parse_one(q, read='$d'); print(repr(e.sql('$d')))\n    except Exception as ex: print('ERR', type(ex).__name__, str(ex)[:200])\n\"; done; grep -n \"STRING_ESCAPES\\|class Tokenizer\\|class Parser\\|class Generator\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py sqlglot/dialects/databricks.py", "description": "Reproduce doubled-quote escape failure across Hive/Spark dialects"}
[tool_result] <work>/env-sqlglot/bin/python
== hive
"SELECT CONCAT('Hello ', 'World!')"
ERR ParseError Expecting ). Line 1, Col: 49.
  CREATE TABLE t (a STRING COMMENT 'Hello '[4m'World!'[0m) 
== spark
"SELECT CONCAT('Hello ', 'World!')"
ERR ParseError Expecting ). Line 1, Col: 49.
  CREATE TABLE t (a STRING COMMENT 'Hello '[4m'World!'[0m) 
== databricks
"SELECT CONCAT('Hello ', 'World
…[181 chars elided]…
g ). Line 1, Col: 49.
  CREATE TABLE t (a STRING COMMENT 'Hello '[4m'World!'[0m) 
sqlglot/dialects/databricks.py:31:    class Tokenizer(Spark.Tokenizer):
sqlglot/dialects/hive.py:89:    class Tokenizer(tokens.Tokenizer):
sqlglot/dialects/hive.py:92:        STRING_ESCAPES = ["\\"]
sqlglot/dialects/spark2.py:20:    class Tokenizer(Hive.Tokenizer):
sqlglot/dialects/spark.py:19:    class Tokenizer(Spark2.Tokenizer):
sqlglot/dialects/spark.py:20:        STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = False
[assistant] Reproduced: all four dialects split `'Hello ''World!'` into two strings. Hive's tokenizer only treats `\` as an escape. Next I'll check the surrounding config and how the generator escapes quotes.
[tool_use Bash] {"command": "sed -n 86,100p sqlglot/dialects/hive.py && grep -n \"def string_sql\\|escaped_quote\\|QUOTE_END\\|_escape\" sqlglot/generator.py | head -20 && grep -n \"escape\" sqlglot/dialects/hive.py sqlglot/dialects/spark*.py | head", "description": "Inspect Hive tokenizer config and generator escaping"}
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
846:        "_escaped_quote_end",
847:        "_escaped_byte_quote_end",
848:        "_escaped_identifier_end",
892:        self._escaped_quote_end: s
…[665 chars elided]…
 supports_escape_sequences = self.dialect.BYTE_STRINGS_SUPPORT_ESCAPED_SEQUENCES
2966:            supports_escape_sequences = self.dialect.STRINGS_SUPPORT_ESCAPED_SEQUENCES
2968:        if supports_escape_sequences:
2974:        delimiter = delimiter or self.dialect.QUOTE_END
2975:        escaped_delimiter = escaped_delimiter or self._escaped_quote_end
3728:            path = f"{self.dialect.QUOTE_START}{path}{self.dialect.QUOTE_END}"
5711:    def string_sql(self, expression: exp.String) -> str:
[assistant] The generator escapes quotes using `STRING_ESCAPES[0]`, so adding `'` as a second entry would leave output as `\'`. To round-trip `''`, `'` has to be the first entry. I'll make that change and run the dialect test suites to see what the `\'` behaviour change affects.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"\\\\\"]", "new_string": "        STRING_ESCAPES = [\"\\\\\", \"'\"]"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks']:\n    for q in [\\\"SELECT 'Hello ''World!'\\\", \\\"CREATE TABLE t (a STRING COMMENT 'Hello ''World!')\\\", \\\"SELECT 'it\\\\\\\\'s'\\\"]:\n        e=sqlglot.parse_one(q, read=d); print(d, repr(e.sql(d)))\n\"", "description": "Try Hive escape order and check round-trips"}
[tool_result] hive "SELECT 'Hello \\'World!'"
hive "CREATE TABLE t (a STRING COMMENT 'Hello \\'World!')"
hive "SELECT 'it\\'s'"
spark "SELECT 'Hello \\'World!'"
spark "CREATE TABLE t (a STRING COMMENT 'Hello \\'World!')"
spark "SELECT 'it\\'s'"
databricks "SELECT 'Hello \\'World!'"
databricks "CREATE TABLE t (a STRING COMMENT 'Hello \\'World!')"
databricks "SELECT 'it\\'s'"
[assistant] My edit put `\\` first, so the generator still emits `\'`. I'll reorder so `'` is first.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"\\\\\", \"'\"]", "new_string": "        STRING_ESCAPES = [\"'\", \"\\\\\"]"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks']:\n    for q in [\\\"SELECT 'Hello ''World!'\\\", \\\"CREATE TABLE t (a STRING COMMENT 'Hello ''World!')\\\", \\\"SELECT 'it\\\\\\\\'s'\\\", \\\"SELECT 'a\\\\\\\\nb'\\\"]:\n        e=sqlglot.parse_one(q, read=d); print(d, repr(e.sql(d)))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py 2>&1 | tail -40", "description": "Recheck round-trips and run Hive/Spark/Databricks tests"}
[tool_result] hive "SELECT 'Hello ''World!'"
hive "CREATE TABLE t (a STRING COMMENT 'Hello ''World!')"
hive "SELECT 'it''s'"
hive "SELECT 'a\\nb'"
spark "SELECT 'Hello ''World!'"
spark "CREATE TABLE t (a STRING COMMENT 'Hello ''World!')"
spark "SELECT 'it''s'"
spark "SELECT 'a\\nb'"
databricks "SELECT 'Hello ''World!'"
databricks "CREATE TABLE t (a STRING COMMENT 'Hello ''World!')"
databricks "SELECT 'it''s'"
databricks "SELECT 'a\\nb'"
    self.assertEqual(
E   AssertionError: "'''x'''" != "'\\'x\\''"
E   - 
…[1460 chars elided]…
quotes - ...
SUBFAILED['\'' -> spark] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED["'x'" -> hive] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED["'x'" -> spark] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED[from_unixtime(x, "yyyy-MM-dd'T'HH") -> hive] tests/dialects/test_hive.py::TestHive::test_time
SUBFAILED[from_unixtime(x, "yyyy-MM-dd'T'HH") -> spark] tests/dialects/test_hive.py::TestHive::test_time
8 failed, 55 passed, 984 subtests passed in 0.90s
[assistant] The existing Hive and Spark tests assert that quotes are generated as `\'` (`test_quotes`, `test_time`, `test_hive`). The rules say I can't edit or weaken those tests, so changing the generator output to `''` is out. I'll keep `\` as the generator's escape and only let the tokenizer accept `''` as well. I'll check that this keeps the existing suites green.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"'\", \"\\\\\"]", "new_string": "        STRING_ESCAPES = [\"\\\\\", \"'\"]"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=. python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks']:\n    for q in [\\\"SELECT 'Hello ''World!'\\\", \\\"CREATE TABLE t (a STRING COMMENT 'Hello ''World!')\\\", \\\"SELECT 'it\\\\\\\\'s'\\\"]:\n        e=sqlglot.parse_one(q, read=d); print(d, repr(e.sql(d)), e.find(sqlglot.exp.Literal).this)\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py 2>&1 | tail -5", "description": "Verify parse-only fix and rerun dialect tests"}
[tool_result] hive "SELECT 'Hello \\'World!'" Hello 'World!
hive "CREATE TABLE t (a STRING COMMENT 'Hello \\'World!')" Hello 'World!
hive "SELECT 'it\\'s'" it's
spark "SELECT 'Hello \\'World!'" Hello 'World!
spark "CREATE TABLE t (a STRING COMMENT 'Hello \\'World!')" Hello 'World!
spark "SELECT 'it\\'s'" it's
databricks "SELECT 'Hello \\'World!'" Hello 'World!
databricks "CREATE TABLE t (a STRING COMMENT 'Hello \\'World!')" Hello 'World!
databricks "SELECT 'it\\'s'" it's
.............. [ 25%]
.........................................                                  [100%]
55 passed, 992 subtests passed in 0.37s
[assistant] Parsing is fixed in all three dialects, and the existing suites pass. Now I'll add a regression test and run the full suite to catch side effects in other dialects that inherit the Hive tokenizer.
[tool_use Bash] {"command": "grep -n \"def test_quotes\" -A12 tests/dialects/test_hive.py && grep -n \"^from\\|^import\" tests/dialects/test_hive.py", "description": "Locate test_quotes in Hive tests"}
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
1:from tests.dialects.test_dialect import Validator
2:from sqlglot import exp
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "    def test_quotes(self):\n        self.validate_all(\n            \"'\\\\''\",", "new_string": "    def test_quotes(self):\n        self.assertEqual(\n            parse_one(\"CREATE TABLE t (a STRING COMMENT 'Hello ''World!')\", read=\"hive\")\n            .find(exp.ColumnDef)\n            .find(exp.Literal)\n            .this,\n            \"Hello 'World!\",\n        )\n        self.assertEqual(\n            parse_one(\"SELECT 'it''s'\", read=\"spark\").selects[0].this,\n            \"it's\",\n        )\n        self.validate_all(\n            \"'\\\\''\","}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "sed -i 's/^from sqlglot import exp$/from sqlglot import exp, parse_one/' tests/dialects/test_hive.py && head -3 tests/dialects/test_hive.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Add import, then run the full test suite"}
[tool_result ERROR] Exit code 1
sed: 2: "tests/dialects/test_hiv ...": undefined label 'ests/dialects/test_hive.py'
[assistant] The `sed -i` failed because macOS needs an explicit backup suffix. I'll make the import edit directly instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "from sqlglot import exp\n", "new_string": "from sqlglot import exp, parse_one\n"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-100324-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests 2>&1 | tail -15", "description": "Run the full test suite"}
[tool_result] ........................................................................................... [  8%]
........................................................................................................................................................................................ [ 24%]
........................... [ 26%]
........................................ [ 30%]
........................................................................................ [ 38%]
..............................
…[264 chars elided]…
............... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 60.27s (0:01:00)
[assistant] The full suite passes (1120 tests). Last, I'll run the linter and formatter on the two touched files and review the diff.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin; ($P/ruff check sqlglot/dialects/hive.py tests/dialects/test_hive.py 2>&1 || python3 -m ruff check sqlglot/dialects/hive.py tests/dialects/test_hive.py 2>&1) | tail -3; ($P/ruff format --check sqlglot/dialects/hive.py tests/dialects/test_hive.py 2>&1 || true) | tail -2; git diff --stat", "description": "Lint, format-check and show diff stats"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/dialects/hive.py    |  2 +-
 tests/dialects/test_hive.py | 13 ++++++++++++-
 2 files changed, 13 insertions(+), 2 deletions(-)
[assistant] Hive, Spark and Databricks now parse `''` inside string literals as an escaped quote. `COMMENT 'Hello ''World!'` yields the value `Hello 'World!`. The full suite passes (1120 tests), and ruff is clean.

The change is one line in `sqlglot/dialects/hive.py`: the Hive tokenizer's `STRING_ESCAPES` becomes `["\\", "'"]`. Spark, Spark2 and Databricks inherit it.

**Round-trip caveat:** the text is not written back as `''`. It comes out as `\'`, which Hive also accepts, so the literal is the same, but the SQL text changes. For example, `SELECT 'it''s'` regenerates as `SELECT 'it\'s'`. Writing `''` would mean changing the generator, and existing tests (`test_quotes`, `test_time`, `test_hive`) require `\'` output. Those tests can't be edited under the project rules. If you want textual `''` output, those tests need to be changed by you, and I can make that change.

I added a regression test to `tests/dialects/test_hive.py::test_quotes`. It checks the parsed value of a column comment and a `SELECT` literal in the Spark dialect. It does not check the textual output.
