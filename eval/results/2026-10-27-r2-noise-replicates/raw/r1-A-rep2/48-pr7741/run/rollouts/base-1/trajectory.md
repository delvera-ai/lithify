# trajectory base-1

final message:
Hive, Spark, Spark2 and Databricks now read `''` inside a string as an escaped single quote. `COMMENT 'Hello ''World!'` parses to `Hello 'World!`.

**Cause:** Hive's tokenizer set `STRING_ESCAPES = ["\\"]`, so `''` was no longer an escape. The tokenizer then read `'Hello '` and `'World!'` as two adjacent literals, which the parser turned into a `CONCAT`. Spark, Spark2 and Databricks inherit that tokenizer, so one change covers all of them.

**Change:**
- `sqlglot/dialects/hive.py`: `STRING_ESCAPES = ["\\", "'"]`.
- `tests/dialects/test_hive.py`: a new `test_quotes` case that reads `''` from Hive, Spark and Databricks and checks the output.

**Round-trip form:** the output uses backslash, so `COMMENT 'Hello ''World!'` comes back as `COMMENT 'Hello \'World!'`. That is the form these dialects already emit, and existing tests pin it (`'\''`), so I didn't change it. The two strings are equivalent in these engines, but the text is not byte-identical to the input. If you need the output to keep `''`, that's a generator change that would also alter those existing expectations, so I'd want your go-ahead first.

**Verification:** the full suite passes with the project's test command (1120 tests, 18170 subtests). I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -n \"STRING_ESCAPES\\|QUOTES\\|class Tokenizer\\|class Hive\\|class Spark\\|class Databricks\" sqlglot/dialects/hive.py sqlglot/dialects/spark.py sqlglot/dialects/spark2.py sqlglot/dialects/databricks.py sqlglot/dialects/dialect.py | head -50; python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks','spark2']:\n    try:\n        e = sqlglot.parse_one(\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", read=d)\n        print(d, repr(e.sql(d)))\n        print(repr(e.find(sqlglot.exp.ColumnConstraint)))\n    except Exception as ex: print(d, 'ERR', ex)\n\"", "description": "Locate escape config and reproduce bug"}
[tool_result] sqlglot/dialects/databricks.py:14:class Databricks(Spark):
sqlglot/dialects/databricks.py:31:    class Tokenizer(Spark.Tokenizer):
sqlglot/dialects/hive.py:18:class Hive(Dialect):
sqlglot/dialects/hive.py:89:    class Tokenizer(tokens.Tokenizer):
sqlglot/dialects/hive.py:90:        QUOTES = ["'", '"']
sqlglot/dialects/hive.py:92:        STRING_ESCAPES = ["\\"]
sqlglot/dialects/spark.py:12:class Spark(Spark2):
sqlglot/dialects/spark.py:19:    class Tokenizer(Spark2.Tokenizer):
sqlglot/dialects/sp
…[846 chars elided]…
iterals support escape sequences. Set by the metaclass based on the tokenizer's BYTE_STRING_ESCAPES."""
hive ERR Expecting ). Line 1, Col: 46.
  CREATE TABLE t (a INT COMMENT 'Hello '[4m'World!'[0m)
spark ERR Expecting ). Line 1, Col: 46.
  CREATE TABLE t (a INT COMMENT 'Hello '[4m'World!'[0m)
databricks ERR Expecting ). Line 1, Col: 46.
  CREATE TABLE t (a INT COMMENT 'Hello '[4m'World!'[0m)
spark2 ERR Expecting ). Line 1, Col: 46.
  CREATE TABLE t (a INT COMMENT 'Hello '[4m'World!'[0m)
[tool_use Bash] {"command": "sed -n 85,100p sqlglot/dialects/hive.py; echo ---; sed -n 15,35p sqlglot/dialects/spark.py; echo ---; sed -n 18,40p sqlglot/dialects/spark2.py; echo ---; sed -n 28,40p sqlglot/dialects/databricks.py; echo ---; grep -n \"STRING_ESCAPES\\b\" sqlglot/tokens.py | head; grep -n \"ESCAPE_FOLLOW_CHARS\\|def _scan_string\" -n sqlglot/tokens.py sqlglot/tokenizer_core.py 2>/dev/null | head -20; python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','databricks']:\n    for s in [\\\"SELECT 'Hello ''World!'\\\", \\\"SELECT 'a\\\\\\\\'b'\\\"]:\n        try: print(d, s, '->', sqlglot.transpile(s, read=d, write=d))\n        except Exception as ex: print(d, s, 'ERR', str(ex)[:80])\n\"", "description": "Inspect Hive/Spark tokenizer and escape behavior"}
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
---
    SUPPORTS_NULL_TYPE = True
    ARRAY_FUNCS_PROPAGATES_NULLS = True
    EXPRESSION_METADATA 
…[2052 chars elided]…
lot/tokens.py:212:    _ESCAPE_FOLLOW_CHARS: t.ClassVar[set[str]] = set()
sqlglot/tokens.py:575:            escape_follow_chars=self._ESCAPE_FOLLOW_CHARS,
hive SELECT 'Hello ''World!' -> ["SELECT CONCAT('Hello ', 'World!')"]
hive SELECT 'a\'b' -> ["SELECT 'a\\'b'"]
spark SELECT 'Hello ''World!' -> ["SELECT CONCAT('Hello ', 'World!')"]
spark SELECT 'a\'b' -> ["SELECT 'a\\'b'"]
databricks SELECT 'Hello ''World!' -> ["SELECT CONCAT('Hello ', 'World!')"]
databricks SELECT 'a\'b' -> ["SELECT 'a\\'b'"]
[tool_use Bash] {"command": "sed -n 1033,1090p sqlglot/tokenizer_core.py; echo ---; git log --oneline -5 -- sqlglot/dialects/hive.py; grep -rn \"STRING_ESCAPES = \\[\" sqlglot/dialects/ | head -30; grep -n \"ESCAPE\" tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py | head -30", "description": "Read string scanning logic and related tests"}
[tool_result]     def _scan_string(self, start: str) -> bool:
        base = None
        token_type = TokenType.STRING

        if start in self.quotes:
            end = self.quotes[start]
        elif start in self.format_strings:
            end, token_type = self.format_strings[start]

            if token_type == TokenType.HEX_STRING:
                base = 16
            elif token_type == TokenType.BIT_STRING:
                base = 2
            elif token_type == TokenType.HEREDOC_STRING:
          
…[2141 chars elided]…
b.py:71:        BYTE_STRING_ESCAPES = ["'", "\\"]
sqlglot/dialects/mysql.py:70:        STRING_ESCAPES = ["'", '"', "\\"]
tests/dialects/test_spark.py:1027:                "spark": "foo LIKE 'pattern' ESCAPE '!'",
tests/dialects/test_spark.py:1028:                "databricks": "foo LIKE 'pattern' ESCAPE '!'",
tests/dialects/test_spark.py:1041:                "spark": "foo ILIKE 'pattern' ESCAPE '!'",
tests/dialects/test_spark.py:1042:                "databricks": "foo ILIKE 'pattern' ESCAPE '!'",
[tool_use Bash] {"command": "grep -n \"''\" tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py | head -20; python3 -c \"\nimport sqlglot\nfrom sqlglot import exp\nfor d in ['hive','spark','databricks','spark2','presto']:\n    print(d, exp.Literal.string(\\\"a'b\\\").sql(d), exp.Literal.string('a\\\\\\\\b').sql(d))\n\"; grep -n \"def literal_sql\\|escape_str\\|STRING_ESCAPE\\|QUOTE_ESCAPE\" sqlglot/generator.py | head; grep -n \"escape\" sqlglot/dialects/hive.py sqlglot/dialects/spark2.py | head", "description": "Check existing tests and literal escaping in generator"}
[tool_result] tests/dialects/test_databricks.py:232:            "SELECT test, LISTAGG(email, '') AS Email FROM organizations GROUP BY test",
tests/dialects/test_databricks.py:312:                "postgres": "SELECT JSON_EXTRACT_PATH(col, 'fr''uit')",
tests/dialects/test_hive.py:217:            """CREATE EXTERNAL TABLE x (y INT) ROW FORMAT SERDE 'serde' ROW FORMAT DELIMITED FIELDS TERMINATED BY '1' WITH SERDEPROPERTIES ('input.regex'='')""",
tests/dialects/test_hive.py:321:            "'\\''",
tests/dialects/t
…[1650 chars elided]…
lass.STRING_ESCAPES[0] + self.dialect.BYTE_END
1590:            escaped_byte_string = self.escape_str(
1612:        if "\\" in self.dialect.tokenizer_class.STRING_ESCAPES:
1643:        if "\\" in self.dialect.tokenizer_class.STRING_ESCAPES:
1646:        string = self.escape_str(string, escape_backslash=False)
2949:    def literal_sql(self, expression: exp.Literal) -> str:
2952:            text = f"{self.dialect.QUOTE_START}{self.escape_str(text)}{self.dialect.QUOTE_END}"
2955:    def escape_str(
[assistant] The root cause: Hive's tokenizer sets `STRING_ESCAPES = ["\\"]`, so `''` is no longer an escape and the two adjacent strings are read as a concatenation. Spark, Spark2 and Databricks inherit this tokenizer. I'll add `'` as an escape in Hive's tokenizer; the generator still emits `\'` as the dialect's canonical form, which the existing tests pin.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py", "old_string": "        STRING_ESCAPES = [\"\\\\\"]\n\n        SINGLE_TOKENS = {\n            **tokens.Tokenizer.SINGLE_TOKENS,\n            \"$\": TokenType.PARAMETER,", "new_string": "        STRING_ESCAPES = [\"\\\\\", \"'\"]\n\n        SINGLE_TOKENS = {\n            **tokens.Tokenizer.SINGLE_TOKENS,\n            \"$\": TokenType.PARAMETER,"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/sqlglot/dialects/hive.py has been updated successfully.
[tool_use Bash] {"command": "python3 -c \"\nimport sqlglot\nfor d in ['hive','spark','spark2','databricks']:\n    for s in [\\\"CREATE TABLE t (a INT COMMENT 'Hello ''World!')\\\", \\\"SELECT 'Hello ''World!'\\\", \\\"SELECT 'a\\\\\\\\'b'\\\", \\\"SELECT ''''\\\", \\\"SELECT 'x'' y' AS c\\\"]:\n        print(d, s, '->', sqlglot.transpile(s, read=d, write=d))\nprint(sqlglot.transpile(\\\"SELECT 'it''s'\\\", read='presto', write='spark'))\nprint(sqlglot.transpile(\\\"SELECT 'it''s'\\\", read='spark', write='presto'))\n\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Verify fix on Hive/Spark/Databricks and run test suite"}
[tool_result] hive CREATE TABLE t (a INT COMMENT 'Hello ''World!') -> ["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
hive SELECT 'Hello ''World!' -> ["SELECT 'Hello \\'World!'"]
hive SELECT 'a\'b' -> ["SELECT 'a\\'b'"]
hive SELECT '''' -> ["SELECT '\\''"]
hive SELECT 'x'' y' AS c -> ["SELECT 'x\\' y' AS c"]
spark CREATE TABLE t (a INT COMMENT 'Hello ''World!') -> ["CREATE TABLE t (a INT COMMENT 'Hello \\'World!')"]
spark SELECT 'Hello ''World!' -> ["SELECT 'Hello \\'World!'"]
spark SELECT 'a\'b' -> ["SE
…[1542 chars elided]…
......................... [ 64%]
.............................................................................................................................................................................................................................................................................................................................................................. [ 95%]
...............................................           [100%]
1120 passed, 18166 subtests passed in 50.51s
[assistant] The full suite passes (1120 tests). Now I'll add a regression test next to the existing quote-escape tests in the Hive test file.
[tool_use Bash] {"command": "sed -n 314,350p tests/dialects/test_hive.py", "description": "Read existing quote-escape tests in Hive test file"}
[tool_result]                 "hive": "SELECT a FROM x LATERAL VIEW EXPLODE(ARRAY(y)) t AS a",
                "spark": "SELECT a FROM x LATERAL VIEW EXPLODE(ARRAY(y)) t AS a",
            },
        )

    def test_quotes(self):
        self.validate_all(
            "'\\''",
            write={
                "duckdb": "''''",
                "presto": "''''",
                "hive": "'\\''",
                "spark": "'\\''",
            },
        )
        self.validate_all(
            "'\"x\"'",
      
…[40 chars elided]…
"'\"x\"'",
                "presto": "'\"x\"'",
                "hive": "'\"x\"'",
                "spark": "'\"x\"'",
            },
        )
        self.validate_all(
            "\"'x'\"",
            write={
                "duckdb": "'''x'''",
                "presto": "'''x'''",
                "hive": "'\\'x\\''",
                "spark": "'\\'x\\''",
            },
        )
        self.validate_all(
            "'\\\\\\\\a'",
            read={
                "drill": "'\\\\\\\\a'",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "    def test_quotes(self):\n        self.validate_all(\n            \"'\\\\''\",\n            write={\n                \"duckdb\": \"''''\",\n                \"presto\": \"''''\",\n                \"hive\": \"
…[564 chars elided]…
MMENT 'Hello ''World!'\",\n                \"databricks\": \"COMMENT 'Hello ''World!'\",\n            },\n            write={\n                \"hive\": \"COMMENT 'Hello \\\\'World!'\",\n                \"spark\": \"COMMENT 'Hello \\\\'World!'\",\n                \"databricks\": \"COMMENT 'Hello \\\\'World!'\",\n                \"duckdb\": \"COMMENT 'Hello ''World!'\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[assistant] That test is wrong: `validate_all` parses its first argument in the default dialect, where `COMMENT ...` isn't a valid statement. I'll switch it to a `SELECT` form.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "        self.validate_all(\n            \"COMMENT 'Hello ''World!'\",\n            read={\n                \"hive\": \"COMMENT 'Hello ''World!'\",\n                \"spark\": \"COMMENT 'Hello ''World!'\",\n   
…[739 chars elided]…
d!'\",\n                \"spark\": \"SELECT 'Hello \\\\'World!'\",\n                \"databricks\": \"SELECT 'Hello \\\\'World!'\",\n                \"duckdb\": \"SELECT 'Hello ''World!'\",\n            },\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT COMMENT 'Hello \\\\'World!')\",\n            \"CREATE TABLE t (a INT COMMENT 'Hello \\\\'World!')\",\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py tests/dialects/test_spark.py tests/dialects/test_databricks.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git status --short", "description": "Run dialect tests and full suite, check git status"}
[tool_result] =========================== short test summary info ============================
SUBFAILED[hive -> SELECT 'Hello ''World!'] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED[spark -> SELECT 'Hello ''World!'] tests/dialects/test_hive.py::TestHive::test_quotes
SUBFAILED[databricks -> SELECT 'Hello ''World!'] tests/dialects/test_hive.py::TestHive::test_quotes
3 failed, 55 passed, 996 subtests passed in 0.32s
SUBFAILED[databricks -> SELECT 'Hello ''World!'] tests/dialects/test_hive.py::TestHive::test_quotes
3 failed, 1120 passed, 18170 subtests passed in 50.99s
 M sqlglot/dialects/hive.py
 M tests/dialects/test_hive.py
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_hive.py -k test_quotes 2>&1 | grep -B3 \"Error\\|assert\" | head -30", "description": "Show failure details for the new quotes test"}
[tool_result] =================================== FAILURES ===================================
____________ TestHive.test_quotes [hive -> SELECT 'Hello ''World!'] ____________
tests/dialects/test_dialect.py:85: in validate_all
    self.assertEqual(
E   AssertionError: "SELECT 'Hello \\'World!'" != "SELECT 'Hello ''World!'"
--
E   ?               ^
___________ TestHive.test_quotes [spark -> SELECT 'Hello ''World!'] ____________
tests/dialects/test_dialect.py:85: in validate_all
    self.assertEqual(
E   AssertionError: "SELECT 'Hello \\'World!'" != "SELECT 'Hello ''World!'"
--
E   ?               ^
_________ TestHive.test_quotes [databricks -> SELECT 'Hello ''World!'] _________
tests/dialects/test_dialect.py:85: in validate_all
    self.assertEqual(
E   AssertionError: "SELECT 'Hello \\'World!'" != "SELECT 'Hello ''World!'"
[assistant] `validate_all` generates the read results in the test class's own dialect (Hive), so the expected string must be Hive-escaped. Fixing the test's expected values:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py", "old_string": "        self.validate_all(\n            \"SELECT 'Hello ''World!'\",\n            read={\n                \"hive\": \"SELECT 'Hello ''World!'\",\n                \"spark\": \"SELECT 'Hello ''World!'\",\n      
…[550 chars elided]…
string": "        self.validate_all(\n            \"SELECT 'Hello \\\\'World!'\",\n            read={\n                \"hive\": \"SELECT 'Hello ''World!'\",\n                \"spark\": \"SELECT 'Hello ''World!'\",\n                \"databricks\": \"SELECT 'Hello ''World!'\",\n            },\n            write={\n                \"duckdb\": \"SELECT 'Hello ''World!'\",\n            },\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-101846-hive-spark-and-databricks-dialec/base-1/tests/dialects/test_hive.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -2; git diff --stat", "description": "Run full test suite and show diff stats"}
[tool_result] ....................................................................       [100%]
1120 passed, 18170 subtests passed in 50.53s
 sqlglot/dialects/hive.py    |  2 +-
 tests/dialects/test_hive.py | 11 +++++++++++
 2 files changed, 12 insertions(+), 1 deletion(-)
[assistant] Hive, Spark, Spark2 and Databricks now read `''` inside a string as an escaped single quote. `COMMENT 'Hello ''World!'` parses to `Hello 'World!`.

**Cause:** Hive's tokenizer set `STRING_ESCAPES = ["\\"]`, so `''` was no longer an escape. The tokenizer then read `'Hello '` and `'World!'` as two adjacent literals, which the parser turned into a `CONCAT`. Spark, Spark2 and Databricks inherit that tokenizer, so one change covers all of them.

**Change:**
- `sqlglot/dialects/hive.py`: `STRING_ESCAPES = ["\\", "'"]`.
- `tests/dialects/test_hive.py`: a new `test_quotes` case that reads `''` from Hi
…[51 chars elided]…
Round-trip form:** the output uses backslash, so `COMMENT 'Hello ''World!'` comes back as `COMMENT 'Hello \'World!'`. That is the form these dialects already emit, and existing tests pin it (`'\''`), so I didn't change it. The two strings are equivalent in these engines, but the text is not byte-identical to the input. If you need the output to keep `''`, that's a generator change that would also alter those existing expectations, so I'd want your go-ahead first.

**Verification:** the full suite passes with the project's test command (1120 tests, 18170 subtests). I haven't committed anything.
