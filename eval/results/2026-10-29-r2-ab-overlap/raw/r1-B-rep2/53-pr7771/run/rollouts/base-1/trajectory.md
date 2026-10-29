# trajectory base-1

final message:
Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged.

**Cause:** `DruidParser` was an empty subclass, so `JSON_VALUE` fell through to generic argument parsing, which expects `)` after the path and rejects `RETURNING`. MySQL, Trino and Exasol register `_parse_json_value` for `JSON_VALUE`. The generator already emits `RETURNING`, so only the parser needed changing.

**Changes:**
- `sqlglot/parsers/druid.py`: `DruidParser` now sets `FUNCTION_PARSERS` to the base parsers plus `"JSON_VALUE": lambda self: self._parse_json_value()`, copying the MySQL and Exasol pattern.
- `tests/dialects/test_druid.py`: added two `validate_identity` cases to the existing `test_druid` function, one with a bare column and one with a qualified column. I did not modify any existing assertions.

**Verification (read in output):**
- Probe on the reported statement and six variants (qualified column, bind variable, nested function call, `RETURNING VARCHAR`, `ERROR ON ERROR`, JOIN/subquery placement). Every line is `OK` and stable on re-transpile. Before the fix, all seven were `ParseError: Expecting )`.
- `tests/dialects/test_druid.py`: 1 passed, 32 subtests passed.
- Full suite: `1121 passed, 18178 subtests passed in 45.58s`, with no failures. My pipe didn't capture pytest's exit code, but a clean pass with no failure lines is exit 0.

**Things to know:**
- The probe failed under the `-I` flag the skill specifies. The project env doesn't install `sqlglot`, and `-I` also ignores `PYTHONPATH`. I ran `PYTHONPATH=$PWD <env python> .lithify/harness/scripts/probe_parse.py --read druid` without `-I`. This is worth fixing in the harness docs or the env.
- No ERR outside the reported construct came up in the probe, so there's nothing to list there.
- I haven't committed. The changes are in the working tree.

## events
[assistant] I'll load the parse-failure-triage skill, since this is a parse failure in a dialect.
[tool_use Skill] {"skill": "parse-failure-triage"}
[tool_result] Launching skill: parse-failure-triage
[user] Base directory for this skill: ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/.claude/skills/parse-failure-triage

# Parse failure triage

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the
   repository, one statement per line, then run:
   `<python> -I .lithify/harness/scripts/probe_parse.py --read <dialect> < stmts.sql`
   Use the interpreter named in `memory.md`.

2. If the reported statement is OK, do not stop there. Put every variant of the clause the
   report names into the same file: inpu
…[512 chars elided]…
s
   fix: list it in your final message.

4. Add a case for each fixed statement to the existing test function for that dialect, using the
   same assertion style. Do not edit or delete existing assertions.

5. Re-run the probe on the reported statement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.

[assistant] Step 1: reproduce the reported statement with the probe script, using the interpreter from the project's checks.
[tool_use Bash] {"command": "ls .lithify/harness/ && find . -name memory.md -not -path './.git/*' | head; mkdir -p /tmp/druid-probe && printf '%s\\n' \"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) FROM t\" \"SELECT JSON_VALUE(t.x, '\\$.a' RETURNING BIGINT) FROM t\" \"SELECT JSON_VALUE(:b, '\\$.a' RETURNING BIGINT) FROM t\" \"SELECT JSON_VALUE(JSON_EXTRACT(x, '\\$.b'), '\\$.a' RETURNING BIGINT) FROM t\" \"SELECT
…[70 chars elided]…
(x, '\\$.a' RETURNING BIGINT ERROR ON ERROR) FROM t\" \"SELECT JSON_VALUE(x, '\\$.a' RETURNING BIGINT) AS y FROM a JOIN (SELECT JSON_VALUE(z, '\\$.a' RETURNING BIGINT) AS w FROM u) s ON 1=1\" > /tmp/druid-probe/stmts.sql && cat /tmp/druid-probe/stmts.sql && ls <work>/env-sqlglot/bin/python", "description": "Locate memory file and write probe statements"}
[tool_result] scripts/
skills/
guardrails.md  147B
memory.md  153B
system.md  260B
tool_guidance.md  535B
./.lithify/harness/memory.md
./.lithify/library/20261029-144515-oracle-dialect-json-table-fails/harness/memory.md
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
SELECT JSON_VALUE(t.x, '$.a' RETURNING BIGINT) FROM t
SELECT JSON_VALUE(:b, '$.a' RETURNING BIGINT) FROM t
SELECT JSON_VALUE(JSON_EXTRACT(x, '$.b'), '$.a' RETURNING BIGINT) FROM t
SELECT JSON_VALUE(x, '$.a' RETURNING VARCHAR) FROM t
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT ERROR ON ERROR) FROM t
SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) AS y FROM a JOIN (SELECT JSON_VALUE(z, '$.a' RETURNING BIGINT) AS w FROM u) s ON 1=1
<work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12  84B
[tool_use Bash] {"command": "cat .lithify/harness/memory.md; echo ---; <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read druid < /tmp/druid-probe/stmts.sql", "description": "Read harness memory and run probe on Druid statements"}
[tool_result ERROR] Exit code 1
- The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
---
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The probe couldn't import `sqlglot` under `-I`, which ignores the working directory. I'll point `PYTHONPATH` at this worktree and rerun.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python -I .lithify/harness/scripts/probe_parse.py --read druid < /tmp/druid-probe/stmts.sql", "description": "Run probe on Druid statements with worktree on path"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "cat .lithify/harness/scripts/probe_parse.py | head -40; <work>/env-sqlglot/bin/python -c \"import sys; print(sys.path)\"", "description": "Inspect probe script header and interpreter path"}
[tool_result] """Probe SQL statements for parse and round-trip failures with sqlglot.

Reads one SQL statement per line from stdin. Blank lines and lines starting with
`--` are skipped. Each statement is transpiled from --read to --write (--write
defaults to --read), then the output is transpiled again to check it is stable.

Prints, per statement:
  OK       output is stable; the next line is the output
  ERR      the error class and first line of the message; the statement failed
  UNSTABLE the output chang
…[730 chars elided]…
ines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out

['', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python312.zip', '~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12', '~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/lib/python3.12/lib-dynload', '<work>/env-sqlglot/lib/python3.12/site-packages']
[tool_use Bash] {"command": "ls <work>/env-sqlglot/lib/python3.12/site-packages | grep -i sqlglot; <work>/env-sqlglot/bin/python -c \"import sqlglot,sys; print(sqlglot.__file__)\"", "description": "Check whether sqlglot is importable in the project env"}
[tool_result] sqlglot_mypy-2.3.0.post2.dist-info/
~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/sqlglot/__init__.py
[assistant] The env doesn't install `sqlglot`; it only resolves from the worktree when the current directory is on the path. `-I` also drops `PYTHONPATH`, so I'll run the probe without `-I`. This is our own repo, so the shadowing risk the skill guards against doesn't apply.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read druid < /tmp/druid-probe/stmts.sql; echo \"exit=$?\"", "description": "Run probe on Druid statements from worktree"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
exit=1
[assistant] Running a script puts its own directory on the path, not the current directory. I'll set `PYTHONPATH` without `-I`.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read druid < /tmp/druid-probe/stmts.sql; echo \"exit=$?\"", "description": "Run probe on Druid statements with PYTHONPATH set"}
[tool_result] ERR       SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
          ParseError: Expecting ). Line 1, Col: 36.
ERR       SELECT JSON_VALUE(t.x, '$.a' RETURNING BIGINT) FROM t
          ParseError: Expecting ). Line 1, Col: 38.
ERR       SELECT JSON_VALUE(:b, '$.a' RETURNING BIGINT) FROM t
          ParseError: Expecting ). Line 1, Col: 37.
ERR       SELECT JSON_VALUE(JSON_EXTRACT(x, '$.b'), '$.a' RETURNING BIGINT) FROM t
          ParseError: Expecting ). Line 1, Col: 57.
ERR       SELECT JSON_VALUE(x, '$.a' RETURNING VARCHAR) FROM t
          ParseError: Expecting ). Line 1, Col: 36.
ERR       SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT ERROR ON ERROR) FROM t
          ParseError: Expecting ). Line 1, Col: 36.
ERR       SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) AS y FROM a JOIN (SELECT JSON_VALUE(z, '$.a' RETURNING BIGINT) AS w FROM u) s ON 1=1
          ParseError: Expecting ). Line 1, Col: 36.
exit=1
[assistant] The failure reproduces on every variant. Next I'll check how MySQL, Trino and Exasol handle `RETURNING` in `JSON_VALUE`, and how Druid's parser is built.
[tool_use Bash] {"command": "grep -rn \"JSONValue\\|JSON_VALUE\\|JsonValue\" sqlglot/ --include=*.py | head -40; echo ---; grep -n \"RETURNING\" sqlglot/dialects/mysql.py sqlglot/dialects/trino.py sqlglot/dialects/exasol.py sqlglot/dialects/druid.py sqlglot/parser.py sqlglot/generator.py | head -40", "description": "Find JSON_VALUE and RETURNING handling across dialects"}
[tool_result] (eval):1: no matches found: --include=*.py
---
17 matches in 2 files:

sqlglot/generator.py:377:# Whether to generate INSERT INTO ... RETURNING or INSERT INTO RETURNING ...
sqlglot/generator.py:378:RETURNING_END = True
sqlglot/generator.py:1786:if self.RETURNING_END:
sqlglot/generator.py:2279:if self.RETURNING_END:
sqlglot/generator.py:2335:return f"{self.seg('RETURNING')} {self.expressions(expression, flat=True)}"
sqlglot/generator.py:2654:if self.RETURNING_END:
sqlglot/generator.py:3788:return
…[457 chars elided]…
7:returning = self._parse_returning()  # TSQL allows RETURNING before source
sqlglot/parser.py:3573:if not self._match(TokenType.RETURNING):
sqlglot/parser.py:3694:elif self._match(TokenType.RETURNING, advance=False):
sqlglot/parser.py:7983:by_ref = self._match_text_seq("RETURNING", "SEQUENCE", "BY", "REF")
sqlglot/parser.py:8088:return_type = self._match_text_seq("RETURNING") and self._parse_format_json(
sqlglot/parser.py:10036:returning = self._match(TokenType.RETURNING) and self._parse_type()
[tool_use Bash] {"command": "sed -n 10020,10060p sqlglot/parser.py; echo ---; sed -n 5520,5545p sqlglot/generator.py; echo ---; grep -rn \"JSON_VALUE\\|JSONValue\\|json_value\" sqlglot/ | head -30", "description": "Read JSON_VALUE parser and generator code"}
[tool_result]         return self.expression(exp.Declare(expressions=expressions, replace=replace))

    def build_cast(self, strict: bool, **kwargs) -> exp.Expr:
        exp_class = exp.Cast if strict else exp.TryCast

        if exp_class == exp.TryCast:
            kwargs["requires_string"] = self.dialect.TRY_CAST_REQUIRES_STRING

        return self.expression(exp_class(**kwargs))

    def _parse_json_value(self) -> exp.JSONValue:
        this = self._parse_bitwise()
        self._match(TokenType.COMMA)
 
…[4418 chars elided]…

sqlglot/generators/tsql.py:104:    json_value = self.func("JSON_VALUE", expression.this, expression.expression)
sqlglot/generators/tsql.py:105:    return self.func("ISNULL", json_query, json_value)
sqlglot/generators/snowflake.py:230:    self: SnowflakeGenerator, expression: exp.JSONValueArray | exp.JSONExtractArray
sqlglot/generators/snowflake.py:235:    if isinstance(expression, exp.JSONValueArray):
sqlglot/generators/snowflake.py:511:        exp.JSONValueArray: _json_extract_value_array_sql,
[assistant] The parsers now live under `sqlglot/parsers/`. Next I'll look at the Druid parser and dialect, and at the existing RETURNING tests for MySQL, Trino and Exasol.
[tool_use Bash] {"command": "ls sqlglot/parsers/ | grep -i druid; ls sqlglot/dialects | grep -i druid; cat sqlglot/parsers/druid.py 2>/dev/null; echo ---; cat sqlglot/dialects/druid.py; echo ---; grep -n \"RETURNING\" tests/dialects/test_mysql.py tests/dialects/test_trino.py tests/dialects/test_exasol.py tests/dialects/test_druid.py | head -20; echo ---; grep -n \"JSON_VALUE\" sqlglot/parsers/mysql.py sqlglot/parsers/exasol.py sqlglot/parsers/trino.py; sed -n 150,170p sqlglot/parsers/mysql.py", "description": "Inspect Druid parser/dialect and related tests"}
[tool_result] druid.py  108B
druid.py  224B
from __future__ import annotations

from sqlglot.parser import Parser


class DruidParser(Parser):
    pass
---
from sqlglot.dialects.dialect import Dialect
from sqlglot.generators.druid import DruidGenerator
from sqlglot.parsers.druid import DruidParser


class Druid(Dialect):
    Parser = DruidParser

    Generator = DruidGenerator
---
5 matches in 2 files:

tests/dialects/test_mysql.py:1561:f"""SELECT JSON_VALUE({json_doc}, '$.price' RETURNING DECIMAL(4, 2))"""
t
…[1059 chars elided]…
# https://dev.mysql.com/doc/refman/5.7/en/miscellaneous-functions.html#function_values
        "VALUES": lambda self: self.expression(
            exp.Anonymous(this="VALUES", expressions=[self._parse_id_var()])
        ),
        "JSON_VALUE": lambda self: self._parse_json_value(),
        "SUBSTR": lambda self: self._parse_substring(),
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_PARSERS,
        TokenType.SHOW: lambda self: self._parse_show(),
    }

    SHOW_PARSERS = {
[assistant] The Druid parser is an empty subclass, so `JSON_VALUE` falls through to generic argument parsing, which can't read `RETURNING`. MySQL and Exasol register `_parse_json_value` in `FUNCTION_PARSERS`. Before editing I'll check the Druid generator and test file.
[tool_use Bash] {"command": "cat sqlglot/generators/druid.py; echo ---; cat tests/dialects/test_druid.py; echo ---; sed -n 1,30p sqlglot/parsers/exasol.py | head -5; sed -n 118,130p sqlglot/parsers/exasol.py", "description": "Read Druid generator, tests, and Exasol parser snippet"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator
from sqlglot.dialects.dialect import rename_func


class DruidGenerator(generator.Generator):
    SELECT_KINDS: tuple[str, ...] = ()
    TRY_SUPPORTED = False
    SUPPORTS_UESCAPE = False
    SUPPORTS_DECODE_CASE = False

    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS

    # https://druid.apache.org/docs/latest/querying/sql-data-types/
    TYPE_MAPPING = {
        **generator.Generator.TYPE
…[1777 chars elided]…
        **dict.fromkeys(("GROUP_CONCAT", "LISTAGG"), lambda self: self._parse_group_concat()),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_value.htm
        "JSON_VALUE": lambda self: self._parse_json_value(),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/json_extract.htm
        "JSON_EXTRACT": lambda self: self._parse_json_extract(),
    }

    def _parse_statement(self) -> exp.Expr | None:
[assistant] I have what I need. The fix is to register `_parse_json_value` for `JSON_VALUE` in `DruidParser`, the same way MySQL and Exasol do. The generator already emits `RETURNING` for `exp.JSONValue`, so no generator change is needed.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py", "old_string": "class DruidParser(Parser):\n    pass", "new_string": "class DruidParser(Parser):\n    FUNCTION_PARSERS = {\n        **Parser.FUNCTION_PARSERS,\n        \"JSON_VALUE\": lambda self: self._parse_json_value(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/sqlglot/parsers/druid.py has been updated successfully.
[assistant] Now I'll add the round-trip cases to the existing Druid test function, in the same `validate_identity` style, then re-run the probe on the reported statement and its variants.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py", "old_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n", "new_string": "        self.validate_identity(\"SELECT ARRAY[1, 2, 3]\")\n        self.validate_identity(\"SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t\")\n        self.validate_identity(\"SELECT JSON_VALUE(t.x, '$.a' RETURNING VARCHAR) FROM t\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-165232-druid-dialect-the-returning-type/base-1/tests/dialects/test_druid.py has been updated successfully.
[tool_use Bash] {"command": "PYTHONPATH=$PWD <work>/env-sqlglot/bin/python .lithify/harness/scripts/probe_parse.py --read druid < /tmp/druid-probe/stmts.sql; echo \"exit=$?\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_druid.py 2>&1 | tail -5", "description": "Re-run probe and Druid dialect tests after fix"}
[tool_result] OK        SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
          SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) FROM t
OK        SELECT JSON_VALUE(t.x, '$.a' RETURNING BIGINT) FROM t
          SELECT JSON_VALUE(t.x, '$.a' RETURNING BIGINT) FROM t
OK        SELECT JSON_VALUE(:b, '$.a' RETURNING BIGINT) FROM t
          SELECT JSON_VALUE(:b, '$.a' RETURNING BIGINT) FROM t
OK        SELECT JSON_VALUE(JSON_EXTRACT(x, '$.b'), '$.a' RETURNING BIGINT) FROM t
          SELECT JSON_VALUE(JSON_EXTRAC
…[201 chars elided]…
'$.a' RETURNING BIGINT ERROR ON ERROR) FROM t
          SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT ERROR ON ERROR) FROM t
OK        SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) AS y FROM a JOIN (SELECT JSON_VALUE(z, '$.a' RETURNING BIGINT) AS w FROM u) s ON 1=1
          SELECT JSON_VALUE(x, '$.a' RETURNING BIGINT) AS y FROM a JOIN (SELECT JSON_VALUE(z, '$.a' RETURNING BIGINT) AS w FROM u) AS s ON 1 = 1
exit=0
.                                        [100%]
1 passed, 32 subtests passed in 0.16s
[assistant] Every probe line now reads OK, and the Druid test file passes. Next is the full suite, the final gate.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo \"exit=${PIPESTATUS[0]}\"", "description": "Run full test suite as final gate", "timeout": 300000}
[tool_result] ................................................ [ 32%]
................................................................................................. [ 41%]
........................................................................................................................................................ [ 54%]
.................. [ 56%]
.................... [ 58%]
....................... [ 60%]
.............. [ 61%]
............ [ 62%]
....................................................
…[35 chars elided]…
...................................... [ 72%]
................................................................................................................................................................................................... [ 90%]
............................... [ 93%]
.......................................................................... [ 99%]
...                                                                      [100%]
1121 passed, 18178 subtests passed in 45.58s
exit=
[assistant] Druid now parses `JSON_VALUE(... RETURNING <type>)` and round-trips it unchanged.

**Cause:** `DruidParser` was an empty subclass, so `JSON_VALUE` fell through to generic argument parsing, which expects `)` after the path and rejects `RETURNING`. MySQL, Trino and Exasol register `_parse_json_value` for `JSON_VALUE`. The generator already emits `RETURNING`, so only the parser needed changing.

**Changes:**
- `sqlglot/parsers/druid.py`: `DruidParser` now sets `FUNCTION_PARSERS` to the base parsers plus `"JSON_VALUE": lambda self: self._parse_json_value()`, copying the MySQL and Exasol pattern.
-
…[628 chars elided]…
ssed in 45.58s`, with no failures. My pipe didn't capture pytest's exit code, but a clean pass with no failure lines is exit 0.

**Things to know:**
- The probe failed under the `-I` flag the skill specifies. The project env doesn't install `sqlglot`, and `-I` also ignores `PYTHONPATH`. I ran `PYTHONPATH=$PWD <env python> .lithify/harness/scripts/probe_parse.py --read druid` without `-I`. This is worth fixing in the harness docs or the env.
- No ERR outside the reported construct came up in the probe, so there's nothing to list there.
- I haven't committed. The changes are in the working tree.
