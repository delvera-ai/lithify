# trajectory base-2

final message:
The Oracle `MERGE` branches now accept `WHERE`, and the full suite passes (1081 passed) along with ruff and mypy. I haven't committed anything.

What changed:

- **Parser** (`sqlglot/parser.py`): after each WHEN branch, if it's an `INSERT` or `UPDATE`, the optional `WHERE` is attached to that node as its `where` arg. This lives in the shared parser, so any dialect that reads the statement will now accept the clause rather than failing on it.
- **Generator** (`sqlglot/generator.py`): new flag `MERGE_BRANCH_WHERE_SUPPORTED`, default `False`. When a branch has a `WHERE` and the target doesn't support it, the generator calls `self.unsupported(...)` and drops the clause. The warning fires once per branch.
- **Oracle** (`sqlglot/generators/oracle.py`): sets the flag to `True`, so the clause round-trips.
- **Tests** (`tests/dialects/test_oracle.py`): new `test_merge_where` covers the UPDATE-only, INSERT-only, and both-branches round-trips. It also checks that transpiling to Postgres drops the clause and logs two warnings, and that `ErrorLevel.RAISE` raises `UnsupportedError`.

Choices to review:

- I reused the existing `where` key on `exp.Insert`. That key already means `REPLACE WHERE` for Databricks, but that rendering happens only in `insert_sql`, and MERGE branches are built by `when_sql`, so there's no collision. A separate key would avoid the overlap if you'd rather keep the two meanings apart.
- The flag is on by default only for Oracle. Other dialects that parse the clause will warn and drop it.

## events
[assistant] I'll start by finding how MERGE is parsed and generated today, in the parser, the generator, and the Oracle dialect.
[tool_use Bash] {"command": "grep -n \"Merge\\|_parse_when_matched\\|WHEN MATCHED\\|NOT MATCHED\" sqlglot/parser.py | head -60; echo ---; grep -n \"merge\\|Merge\\|when\" sqlglot/generator.py | head -60; echo ---; grep -n \"Merge\\|MERGE\" sqlglot/dialects/oracle.py; echo ---; grep -n \"class Merge\\|class When\" -A12 sqlglot/expressions.py"}
[tool_result ERROR] Exit code 2
14 matches in 6 files:

1056:0:lambda self: self._parse_when_matched(),
1377:0:lambda self: self.expression(exp.MergeTreeTTL(expressions=[self._parse_bitwis...
3039:0:
8884:0:
8905:0:
sqlglot/parser.py:2194:return self.expression(exp.MergeTreeTTLAction(this=this, delete=True))
sqlglot/parser.py:2197:exp.MergeTreeTTLAction(this=this, recompress=self._parse_bitwise())
sqlglot/parser.py:2201:exp.MergeTreeTTLAction(this=this, to_disk=self._parse_string())
sqlglot/parser.py:2205:exp.Merge
…[2416 chars elided]…
hen(arg.is_(exp.null()), exp.null())
sqlglot/generator.py:4475:# T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_...
sqlglot/generator.py:4480:whens = self.sql(expression, "whens")
sqlglot/generator.py:4491:whens = f"{whens}{returning}"
sqlglot/generator.py:4497:f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
sqlglot/generator.py:4638:case = exp.Case().when(
---
0 matches for 'Merge\|MERGE'
---
grep: sqlglot/expressions.py: No such file or directory
[assistant] The shell grep output was garbled, so I'll switch to the search tool and locate the MERGE and `When` definitions directly.
[tool_use Grep] {"pattern": "class (Merge|When|Whens)\\b", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot", "-n": "true", "-A": "12", "output_mode": "content"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Grep] {"pattern": "def _parse_when_matched", "path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot", "-n": "true", "-A": "75", "output_mode": "content"}
[tool_result ERROR] <tool_use_error>Error: No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.</tool_use_error>
[tool_use Bash] {"command": "ls sqlglot | head -50; git status --short | head; git log --oneline -1", "description": "List sqlglot package and repo status"}
[tool_result] dialects/
executor/
expressions/
generators/
optimizer/
parsers/
typing/
__init__.py  6.4K
__main__.py  2.1K
_typing.py  1.5K
_version.py  91B
diff.py  16.3K
errors.py  4.7K
generator.py  244.0K
helper.py  11.7K
jsonpath.py  7.8K
lineage.py  16.7K
parser.py  365.2K
planner.py  14.2K
py.typed  0B
schema.py  27.4K
serde.py  3.0K
time.py  18.0K
tokenizer_core.py  34.4K
tokens.py  22.4K
transforms.py  41.0K
trie.py  2.2K
okbd4773525 lithify: probe base
[assistant] The package has been split into `expressions/`, `parsers/`, and `generators/` subpackages, so I'll search those.
[tool_use Bash] {"command": "grep -rn \"class Merge\\|class When\\b\\|class Whens\\|_parse_when_matched\\|def _parse_merge\\|class Insert(\" sqlglot/ ; echo ---; grep -rn \"Merge\\|MERGE\\|When\" sqlglot/dialects/oracle.py | head; echo ---; grep -rln \"exp.Whens\\|exp.When\\b\" sqlglot tests | head -30", "description": "Locate MERGE and When expression definitions and usages"}
[tool_result] sqlglot/parser.py:1056:        exp.Whens: lambda self: self._parse_when_matched(),
sqlglot/parser.py:3037:    def _parse_mergeblockratio(
sqlglot/parser.py:8884:    def _parse_merge(self) -> exp.Merge:
sqlglot/parser.py:8900:                whens=self._parse_when_matched(),
sqlglot/parser.py:8905:    def _parse_when_matched(self) -> exp.Whens:
sqlglot/expressions/ddl.py:310:class MergeTreeTTLAction(Expression):
sqlglot/expressions/ddl.py:320:class MergeTreeTTL(Expression):
sqlglot/expressions/properties.py:284:class MergeBlockRatioProperty(Property):
sqlglot/expressions/dml.py:194:class Insert(Expression, DDL, DML):
sqlglot/expressions/dml.py:505:class Merge(Expression, DML):
sqlglot/expressions/dml.py:517:class When(Expression):
sqlglot/expressions/dml.py:521:class Whens(Expression):
---
---
sqlglot/parser.py
sqlglot/generator.py
tests/test_parser.py
tests/test_build.py
[tool_use Bash] {"command": "sed -n 8884,8960p sqlglot/parser.py; echo ----GEN; sed -n 4440,4500p sqlglot/generator.py; echo ----DML; sed -n 505,530p sqlglot/expressions/dml.py", "description": "Show MERGE parser, generator, and expression code"}
[tool_result]     def _parse_merge(self) -> exp.Merge:
        self._match(TokenType.INTO)
        target = self._parse_table()

        if target and self._match(TokenType.ALIAS, advance=False):
            target.set("alias", self._parse_table_alias())

        self._match(TokenType.USING)
        using = self._parse_table()

        return self.expression(
            exp.Merge(
                this=target,
                using=using,
                on=self._match(TokenType.ON) and self._parse_disjunctio
…[5000 chars elided]…
pported_args("format")
----DML
class Merge(Expression, DML):
    arg_types = {
        "this": True,
        "using": True,
        "on": False,
        "using_cond": False,
        "whens": True,
        "with_": False,
        "returning": False,
    }


class When(Expression):
    arg_types = {"matched": True, "source": False, "condition": False, "then": True}


class Whens(Expression):
    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""

    arg_types = {"expressions": True}
[assistant] The MERGE branches are built from `exp.Update` and `exp.Insert`, so the branch-level WHERE belongs on those. I'll check their arg types, how the generator handles them, and the existing MERGE tests.
[tool_use Bash] {"command": "sed -n 194,215p sqlglot/expressions/dml.py; grep -n \"class Update\" -A14 sqlglot/expressions/dml.py; echo ---GEN; grep -n \"def update_sql\\|def insert_sql\" -A25 sqlglot/generator.py | head -90; echo ---TESTS; grep -rn \"WHEN NOT MATCHED THEN INSERT\\|WHEN MATCHED THEN UPDATE\" tests | head -40; echo ---UNSUP; grep -n \"self.unsupported(\" sqlglot/generator.py | head -3", "description": "Inspect Insert/Update expressions, generators, and merge tests"}
[tool_result] class Insert(Expression, DDL, DML):
    arg_types = {
        "hint": False,
        "with_": False,
        "is_function": False,
        "this": False,
        "expression": False,
        "conflict": False,
        "returning": False,
        "overwrite": False,
        "exists": False,
        "alternative": False,
        "where": False,
        "ignore": False,
        "by_name": False,
        "stored": False,
        "partition": False,
        "settings": False,
        "source": False,
…[10108 chars elided]…
a, b) VALUES (src.a, src.b)""",
tests/dialects/test_tsql.py:227:            "WITH t(c) AS (SELECT 1) MERGE INTO x AS z USING (SELECT c AS c FROM t) AS y ON a = b WHEN MATCHED THEN UPDATE SET a = y.b",
tests/dialects/test_tsql.py:229:                "postgres": "MERGE INTO x AS z USING (WITH t(c) AS (SELECT 1) SELECT c FROM t) AS y ON a = b WHEN MATCHED THEN UPDATE SET a = y.b",
---UNSUP
rg: regex parse error:
    (?:self.unsupported()
    ^
error: unclosed group
0 matches for 'self.unsupported('
[assistant] Two findings shape the design. `exp.Insert` already has a `where` arg, but `insert_sql` renders it as `REPLACE WHERE`. The MERGE branch builds its INSERT by hand in `when_sql`, so reusing the key is safe. Next I'll check the generator flag pattern, how Oracle sets flags, and how existing tests assert unsupported warnings.
[tool_use Bash] {"command": "grep -rn \"MATCHED_BY_SOURCE\" sqlglot | head; echo ---; grep -n \"def unsupported\" -A6 sqlglot/generator.py; echo ---; ls sqlglot/generators sqlglot/parsers | head -80; echo ---; grep -rn \"class Generator\" -A8 sqlglot/dialects/oracle.py; echo ---; grep -n \"unsupported_level\\|assertLogs\\|UnsupportedError\" tests/dialects/test_oracle.py | head -5; echo ---; grep -rn \"def when_sql\\|def merge_sql\" sqlglot | head; echo ---; sed -n 870,905p tests/dialects/test_oracle.py", "description": "Check generator flags, unsupported helper, Oracle generator, and tests"}
[tool_result] sqlglot/generator.py:321:    MATCHED_BY_SOURCE = True
sqlglot/generator.py:4445:        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
sqlglot/generators/snowflake.py:378:    MATCHED_BY_SOURCE = False
---
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
34-    Decorator that can be used to mark certain args of an `Expr` subclass as unsupported.
35-    It expects a sequence o
…[3057 chars elided]…
 THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )

    def test_pseudocolumns(self):
        ast = self.validate_identity(
            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
        )
        self.assertIsNone(ast.find(exp.Pseudocolumn))

        qualified = qualify(ast, dialect="oracle")
        self.assertIsNotNone(qualified.find(exp.Pseudocolumn))
[assistant] Generators live in `sqlglot/generators/`. I'll read the Oracle generator and find an existing unsupported-warning test to copy.
[tool_use Bash] {"command": "sed -n 1,60p sqlglot/generators/oracle.py; echo ---; sed -n 315,325p sqlglot/generator.py; echo ---; grep -rn \"assertLogs\" tests/dialects/*.py | head -4; grep -rn \"UnsupportedError\" tests/dialects/test_dialect.py | head -3", "description": "Read Oracle generator and unsupported-warning test patterns"}
[tool_result] from __future__ import annotations


from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    no_ilike_sql,
    rename_func,
    strposition_sql,
    to_number_with_nls_param,
    trim_sql,
)


def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
    position = expression.args.get("position")

    if position and position.upper() in ("LEADING", "TRAILING"):
        return self.trim_sql(expression)

    return trim_sql(self, expression)


class Oracl
…[1722 chars elided]…

tests/dialects/test_bigquery.py:2139:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2147:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_bigquery.py:2167:        with self.assertLogs(helper_logger) as cm:
tests/dialects/test_dialect.py:11:    UnsupportedError,
tests/dialects/test_dialect.py:97:                if write_sql is UnsupportedError:
tests/dialects/test_dialect.py:98:                    with self.assertRaises(UnsupportedError):
[assistant] I have enough to design this. The plan:

- **Parser (shared):** attach an optional `WHERE` to the `Update` or `Insert` produced for a WHEN branch.
- **Generator:** emit it only when a new `MERGE_BRANCH_WHERE_SUPPORTED` flag is set. The base generator leaves it off and Oracle turns it on. Otherwise it calls `self.unsupported(...)` and drops the clause.

Before editing, I'll confirm the helper names, the warning logger, and the test imports.
[tool_use Bash] {"command": "grep -n \"def _parse_where\" -A4 sqlglot/parser.py; echo ---; grep -n \"unsupported_messages\" -B2 -A4 sqlglot/generator.py | sed -n 1,30p; echo ---; sed -n 1,20p tests/dialects/test_oracle.py; echo ---; grep -n \"^logger\\|getLogger\" sqlglot/generator.py sqlglot/__init__.py | head", "description": "Confirm where-parser helper, warning logger, and test imports"}
[tool_result] 5183:    def _parse_where(self, skip_where_token: bool = False) -> exp.Where | None:
5184-        if not skip_where_token and not self._match(TokenType.WHERE):
5185-            return None
5186-
5187-        comments = self._prev_comments
---
824-        "comments",
825-        "dialect",
826:        "unsupported_messages",
827-        "_escaped_quote_end",
828-        "_escaped_byte_quote_end",
829-        "_escaped_identifier_end",
830-        "_next_name",
--
870-        )
871-
872:        se
…[1193 chars elided]…
   "SELECT CONNECT_BY_ROOT x y",
            write={
                "": "SELECT CONNECT_BY_ROOT x AS y",
                "oracle": "SELECT CONNECT_BY_ROOT x AS y",
            },
        )
        self.parse_one("ALTER TABLE tbl_name DROP FOREIGN KEY fk_symbol").assert_is(exp.Alter)

        self.validate_identity("XMLELEMENT(EVALNAME foo + bar)")
---
2 matches in 2 files:

sqlglot/__init__.py:78:logger = logging.getLogger("sqlglot")
sqlglot/generator.py:24:logger = logging.getLogger("sqlglot")
[assistant] Now the edits. First, the parser attaches the optional `WHERE` to the INSERT or UPDATE branch.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py", "old_string": "            elif self._match(TokenType.DELETE):\n                then = self.expression(exp.Var(this=self._prev.text))\n            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n  
…[5 chars elided]…
     whens.append(", "new_string": "            elif self._match(TokenType.DELETE):\n                then = self.expression(exp.Var(this=self._prev.text))\n            else:\n                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)\n\n            if isinstance(then, (exp.Insert, exp.Update)):\n                then.set(\"where\", self._parse_where())\n\n            whens.append("}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/parser.py has been updated successfully.
[assistant] Next, the generator: a base-class flag (off by default) and the emit-or-warn logic in `when_sql`.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE ... WHEN [NOT] MATCHED THEN UPDATE/INSERT ... WHERE is allowed\n    MERGE_BRANCH_WHERE_SUPPORTED = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        i
…[7 chars elided]…
tance(then_expression, (exp.Insert, exp.Update)) and then_expression.args.get(\"where\"):\n            if self.MERGE_BRANCH_WHERE_SUPPORTED:\n                then = f\"{then} {self.sql(then_expression, 'where')}\"\n            else:\n                self.unsupported(\"WHERE clause in MERGE WHEN UPDATE/INSERT is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    MERGE_BRANCH_WHERE_SUPPORTED = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generators/oracle.py has been updated successfully.
[assistant] Now the tests in `test_oracle.py`: round-trips for both branches, plus the warn and raise behavior for a non-Oracle target. I'll add `ErrorLevel` to the existing import.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one", "new_string": "from sqlglot import exp, ErrorLevel, UnsupportedError, ParseError, parse, parse_one"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "    def test_pseudocolumns(self):", "new_string": "    def test_merge_where(self):\n        self.validate_identity(\n            \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN
…[1345 chars elided]…
") as cm:\n            self.assertEqual(parse_one(sql, read=\"oracle\").sql(\"postgres\"), expected)\n        self.assertEqual(len(cm.output), 1)\n        self.assertIn(\"WHERE clause in MERGE\", cm.output[0])\n\n        with self.assertRaises(UnsupportedError):\n            parse_one(sql, read=\"oracle\").sql(\"postgres\", unsupported_level=ErrorLevel.RAISE)\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[assistant] Running the Oracle test file with the project's checks interpreter first.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Run Oracle dialect tests"}
[tool_result] .............F..........                                                      [100%]
=================================== FAILURES ===================================
_________________________ TestOracle.test_merge_where __________________________

self = <tests.dialects.test_oracle.TestOracle testMethod=test_merge_where>

    def test_merge_where(self):
>       self.validate_identity(
            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SE
…[644 chars elided]…
e USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1  WHERE source_table.col1 > 0
E   ?                                                                                                                                        +
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 23 passed, 211 subtests passed in 0.36s
[assistant] The `WHERE` already carries a leading space from `where_sql`, so my extra space doubled it. I'll drop the extra separator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py", "old_string": "                then = f\"{then} {self.sql(then_expression, 'where')}\"", "new_string": "                then = f\"{then}{self.sql(then_expression, 'where')}\""}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/sqlglot/generator.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; echo ---; $PY -m ruff format --check sqlglot tests 2>&1 | tail -3; $PY -m ruff check sqlglot tests 2>&1 | tail -3", "description": "Run Oracle tests, full suite, and ruff checks", "timeout": 600000}
[tool_result] =========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 23 passed, 211 subtests passed in 0.15s
        self.validate_identity(
            "MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 > 0 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.i
…[925 chars elided]…
urce_table.col1 WHEN NO[90 chars]ol1)'
E           Diff is 750 characters long. Set self.maxDiff to None to see it.

tests/dialects/test_oracle.py:912: AssertionError
=========================== short test summary info ============================
FAILED tests/dialects/test_oracle.py::TestOracle::test_merge_where - Assertio...
1 failed, 1080 passed, 17834 subtests passed in 44.74s
---
Would reformat: sqlglot/generator.py
1 file would be reformatted, 232 files already formatted
All checks passed!
[assistant] Two things to fix. The postgres output strips the `my_table.` qualifier on SET and INSERT columns, so my expected string was wrong. Ruff also wants to reformat `generator.py`. I'll correct the expectation and apply the formatter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/generator.py && git diff --stat && $PY -c \"\nfrom sqlglot import parse_one\nsql='MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHERE source_table.col1 > 0 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1) WHERE source_table.id > 0'\nprint(parse_one(sql, read='oracle').sql('postgres'))\"", "description": "Format generator and print Postgres output for the sample"}
[tool_result] 1 file reformatted
sqlglot/generator.py          | 12 ++++++++++++
 sqlglot/generators/oracle.py  |  1 +
 sqlglot/parser.py             |  3 +++
 tests/dialects/test_oracle.py | 23 ++++++++++++++++++++++-
 4 files changed, 38 insertions(+), 1 deletion(-)
WHERE clause in MERGE WHEN UPDATE/INSERT is not supported
WHERE clause in MERGE WHEN UPDATE/INSERT is not supported
MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (id, col1) VALUES (source_table.id, source_table.col1)
[This command modified 1 file you've previously read: sqlglot/generator.py. Call Read before editing.]
[assistant] The output confirms two warnings, one per dropped branch, and the qualifier stripping. I'll fix the test expectation to match and assert both warnings.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py", "old_string": "        expected = \"MERGE INTO my_table USING source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table
…[463 chars elided]…
l1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (id, col1) VALUES (source_table.id, source_table.col1)\"\n        with self.assertLogs(\"sqlglot\", level=\"WARNING\") as cm:\n            self.assertEqual(parse_one(sql, read=\"oracle\").sql(\"postgres\"), expected)\n        self.assertEqual(len(cm.output), 2)\n        self.assertTrue(all(\"WHERE clause in MERGE\" in msg for msg in cm.output))"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-171911-oracle-dialect-support-the-optio/base-2/tests/dialects/test_oracle.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; $PY -m ruff format --check sqlglot tests | tail -1; $PY -m ruff check sqlglot tests | tail -1; $PY -m mypy sqlglot/generator.py sqlglot/parser.py 2>&1 | tail -2", "description": "Rerun Oracle tests, full suite, format, lint, and mypy", "timeout": 600000}
[tool_result] ........................                                                      [100%]
24 passed, 211 subtests passed in 0.13s
....................... [ 96%]
....................................                      [100%]
1081 passed, 17834 subtests passed in 43.63s
233 files already formatted
All checks passed!
Success: no issues found in 2 source files
[assistant] The Oracle `MERGE` branches now accept `WHERE`, and the full suite passes (1081 passed) along with ruff and mypy. I haven't committed anything.

What changed:

- **Parser** (`sqlglot/parser.py`): after each WHEN branch, if it's an `INSERT` or `UPDATE`, the optional `WHERE` is attached to that node as its `where` arg. This lives in the shared parser, so any dialect that reads the statement will now accept the clause rather than failing on it.
- **Generator** (`sqlglot/generator.py`): new flag `MERGE_BRANCH_WHERE_SUPPORTED`, default `False`. When a branch has a `WHERE` and the target doesn't sup
…[321 chars elided]…
oth-branches round-trips. It also checks that transpiling to Postgres drops the clause and logs two warnings, and that `ErrorLevel.RAISE` raises `UnsupportedError`.

Choices to review:

- I reused the existing `where` key on `exp.Insert`. That key already means `REPLACE WHERE` for Databricks, but that rendering happens only in `insert_sql`, and MERGE branches are built by `when_sql`, so there's no collision. A separate key would avoid the overlap if you'd rather keep the two meanings apart.
- The flag is on by default only for Oracle. Other dialects that parse the clause will warn and drop it.
