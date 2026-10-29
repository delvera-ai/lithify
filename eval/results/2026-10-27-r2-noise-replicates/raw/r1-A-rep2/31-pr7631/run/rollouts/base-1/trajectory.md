# trajectory base-1

final message:
The MySQL → Exasol alias rewrite now matches case-insensitively, following Exasol's identifier rules. The reported query produces `SELECT 1 AS idField FROM t GROUP BY LOCAL.idField`.

The full suite passes (1108 tests), and ruff lint and format are clean. I didn't commit; the changes are in the working tree.

**The fix** (`sqlglot/generators/exasol.py`): alias names and column references are now keyed by Exasol's folding rule. Unquoted names are upper-cased and quoted names are kept exact. Key matching goes through the new `_alias_key` helper, used in the WHERE/GROUP BY/HAVING pass and the select-list pass.

I also made one choice beyond the literal ask: the rewritten reference copies the alias's own spelling and quoting, not the reference's. Otherwise a quoted alias `"IDFIELD"` referenced as `idfield` would emit `LOCAL."idfield"`, which is wrong.

**Behaviour checked:**
- Unquoted alias and reference in different case now match (GROUP BY, WHERE, HAVING, and select-list alias reuse).
- A quoted alias `"idField"` is not matched by `idfield`, since quoted identifiers are case-sensitive in Exasol.

**Test** (`tests/dialects/test_exasol.py`): added `test_local_prefix_for_alias_case_insensitive`, covering the reported MySQL case, a WHERE case, and the quoted non-match. I did not run it against the unfixed code, so I haven't seen it fail before the change.

## events
[tool_use Bash] {"command": "grep -n -i \"LOCAL\" sqlglot/dialects/exasol.py sqlglot/transforms.py sqlglot/dialects/mysql.py | head -50", "description": "Find LOCAL alias handling code"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn -i \"local\\.\" sqlglot/ | grep -v \"\\.pyc\" | head -30; git status --short | head", "description": "Search for LOCAL alias rewrite code"}
[tool_result] sqlglot/generators/exasol.py:37:# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10
[tool_use Bash] {"command": "sed -n 1,120p sqlglot/generators/exasol.py; grep -n -i \"exasol\" -r tests/dialects/*.py | head -5", "description": "Read Exasol generator and test references"}
[tool_result] from __future__ import annotations

import typing as t

from sqlglot import exp, generator, transforms
from sqlglot.dialects.dialect import (
    DATE_ADD_OR_SUB,
    groupconcat_sql,
    no_last_day_sql,
    rename_func,
    strposition_sql,
    timestrtotime_sql,
    timestamptrunc_sql,
)
from sqlglot.errors import UnsupportedError
from sqlglot.generator import unsupported_args
from sqlglot.optimizer.scope import build_scope
from sqlglot.parsers.exasol import DATE_UNITS


def _sha2_sql(self: E
…[3827 chars elided]…
pression.args["count"]
    count_sql = self.sql(expression, "count")
tests/dialects/test_dialect.py:1002:                "exasol": "FROM_POSIX_TIME(x)",
tests/dialects/test_dialect.py:4235:                "exasol": "WEEK(CAST('2025-01-01' AS DATE))",
tests/dialects/test_dialect.py:4362:                "exasol": "REGR_COUNT(x, y)",
tests/dialects/test_dialect.py:4376:                "exasol": "REGR_COUNT(x, y)",
tests/dialects/test_dialect.py:4395:                "exasol": "REGR_INTERCEPT(x, y)",
[tool_use Bash] {"command": "grep -rn \"LOCAL\" tests/ | head -30; grep -n \"def quoted\" -A3 sqlglot/expressions*.py sqlglot/expressions/*.py 2>/dev/null | head", "description": "Find LOCAL tests and Identifier.quoted helper"}
[tool_result] tests/test_parser.py:505:            parse_one("TIMESTAMP WITH LOCAL TIME ZONE '2022-01-01'").sql(),
tests/test_parser.py:517:            parse_one("TIMESTAMP(1) WITH LOCAL TIME ZONE '2022-01-01'").sql(),
tests/test_parser.py:525:        self.assertEqual(parse_one("TIMESTAMP(1) WITH LOCAL TIME ZONE").sql(), "TIMESTAMPLTZ(1)")
tests/dialects/test_singlestore.py:898:        self.validate_identity("SHOW FULLTEXT SERVICE METRICS LOCAL")
tests/dialects/test_exasol.py:133:            "CAST(x AS TIMEST
…[2378 chars elided]…
FROM t HAVING LOCAL.cnt > 1"},
tests/dialects/test_snowflake.py:3217:        self.validate_identity("LOCALTIMESTAMP", "CURRENT_TIMESTAMP")
tests/dialects/test_snowflake.py:3218:        self.validate_identity("LOCALTIMESTAMP()", "CURRENT_TIMESTAMP()")
tests/dialects/test_snowflake.py:3219:        self.validate_identity("LOCALTIMESTAMP(3)", "CURRENT_TIMESTAMP(3)")
tests/dialects/test_snowflake.py:3225:                "duckdb": "SELECT LOCALTIME",
(eval):1: no matches found: sqlglot/expressions*.py
[tool_use Bash] {"command": "sed -n 805,860p tests/dialects/test_exasol.py; grep -rn \"def quoted\" -A3 sqlglot/ | head; ls <work>/env-sqlglot/bin/python", "description": "Read existing Exasol alias tests and helpers"}
[tool_result]     def test_odbc_date_literals(self):
        self.validate_identity("SELECT {d'2024-01-01'}", "SELECT TO_DATE('2024-01-01')")
        self.validate_identity(
            "SELECT {ts'2024-01-01 12:00:00'}",
            "SELECT TO_TIMESTAMP('2024-01-01 12:00:00')",
        )

    def test_local_prefix_for_alias(self):
        self.validate_identity(
            'SELECT ID FROM local WHERE "LOCAL".ID IS NULL',
            'SELECT ID FROM "LOCAL" WHERE "LOCAL".ID IS NULL',
        )
        self.v
…[1862 chars elided]…
_sql in test_cases:
            with self.subTest(clause=title):
                self.validate_all(
                    exasol_sql,
                    write={"exasol": exasol_sql, "databricks": dbx_sql},
sqlglot/expressions/core.py:1772:    def quoted(self) -> bool:
sqlglot/expressions/core.py-1773-        return bool(self.args.get("quoted"))
sqlglot/expressions/core.py-1774-
sqlglot/expressions/core.py-1775-    @property
<work>/env-sqlglot/bin/python
[assistant] The bug is in `prefix_local`: it looks up `node.name` in a dict keyed by the alias's raw spelling. I'll key both sides by Exasol's folding rule (unquoted → upper case, quoted → exact) and emit the alias's own identifier.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n     
…[492 chars elided]…
/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, exp.Identifier] = {\n            _alias_key(alias): alias\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        def prefix_local(node: exp.Expr, visible_aliases: dict[str, bool]) -> exp.Expr:\n            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n    
…[410 chars elided]…
nce(node, exp.Column)\n                and not node.table\n                and isinstance(node.this, exp.Identifier)\n                and (alias := visible_aliases.get(_alias_key(node.this)))\n            ):\n                return exp.Column(\n                    this=alias.copy(),\n                    table=exp.to_identifier(\"LOCAL\", quoted=False),\n                )\n            return node"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        seen_aliases: dict[str, bool] = {}\n        new_selects: list[exp.Expr] = []\n        for sel in expression.selects:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.trans
…[399 chars elided]…
pr] = []\n        for sel in expression.selects:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.transform(lambda node: prefix_local(node, seen_aliases))\n                sel.set(\"this\", inner)\n\n                if alias_node := sel.args.get(\"alias\"):\n                    seen_aliases[_alias_key(alias_node)] = alias_node\n                new_selects.append(sel)"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now I'll check the reported case and the quoting edge cases before adding a test.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -I -c '\nimport sqlglot\nfor s in [\n \"SELECT 1 AS idField FROM t GROUP BY idfield\",\n \"SELECT 1 AS idField FROM t WHERE IDFIELD > 1\",\n \"SELECT 1 AS idfield FROM t HAVING idField > 1\",\n \"SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield\",\n \"SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idField\\\"\",\n \"SELECT 1 AS idField FROM t GROUP BY \\\"idfield\\\"\",\n \"SELECT 1 AS idfield, idField + 1 AS x FROM t\",\n]:\n  print(sqlglot.transpile(s, read=\"mysql\", write=\"exasol\")[0])\n' 2>&1; git diff --stat", "description": "Verify fix against reported and edge-case queries"}
[tool_result] Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sqlglot'
 sqlglot/generators/exasol.py | 34 +++++++++++++++++++++-------------
 1 file changed, 21 insertions(+), 13 deletions(-)
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c '\nimport sqlglot\nfor s in [\n \"SELECT 1 AS idField FROM t GROUP BY idfield\",\n \"SELECT 1 AS idField FROM t WHERE IDFIELD > 1\",\n \"SELECT 1 AS idfield FROM t HAVING idField > 1\",\n \"SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield\",\n \"SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idField\\\"\",\n \"SELECT 1 AS idField FROM t GROUP BY \\\"idfield\\\"\",\n \"SELECT 1 AS idfield, idField + 1 AS x FROM t\",\n]:\n  print(sqlglot.transpile(s, read=\"mysql\", write=\"exasol\")[0])\n' 2>&1", "description": "Run reported and edge-case queries through transpiler"}
[tool_result] SELECT 1 AS idField FROM t GROUP BY LOCAL.idField
SELECT 1 AS idField FROM t WHERE LOCAL.idField > 1
SELECT 1 AS idfield FROM t HAVING LOCAL.idfield > 1
SELECT 1 AS "idField" FROM t GROUP BY idfield
SELECT 1 AS "idField" FROM t GROUP BY 'idField'
SELECT 1 AS idField FROM t GROUP BY 'idfield'
SELECT 1 AS idfield, LOCAL.idfield + 1 AS x FROM t
[assistant] Reported case and the mixed-case variants now resolve correctly. (The `'idField'` output for `"idField"` is MySQL's own double-quote-as-string reading, unrelated to this change.) Next I'll add a regression test next to the existing LOCAL-prefix tests.
[tool_use Bash] {"command": "sed -n 858,872p tests/dialects/test_exasol.py", "description": "View end of LOCAL prefix test method"}
[tool_result]                 self.validate_all(
                    exasol_sql,
                    write={"exasol": exasol_sql, "databricks": dbx_sql},
                )

    def test_regexp_like(self):
        # Exasol uses binary predicate syntax: col REGEXP_LIKE pattern
        self.validate_identity("SELECT x REGEXP_LIKE '.*pattern.*'")

        # Cross-dialect: partial match semantics from other dialects get .* wrapping
        self.validate_all(
            "SELECT a REGEXP_LIKE '.*x.*'",
            read={
                "hive": "SELECT a RLIKE 'x'",
                "presto": "SELECT REGEXP_LIKE(a, 'x')",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "                self.validate_all(\n                    exasol_sql,\n                    write={\"exasol\": exasol_sql, \"databricks\": dbx_sql},\n                )\n\n    def test_regexp_like(self):", "new_
…[716 chars elided]…
      read={\"mysql\": \"SELECT 1 AS idfield FROM t WHERE IDFIELD > 1\"},\n            write={\"exasol\": \"SELECT 1 AS idfield FROM t WHERE LOCAL.idfield > 1\"},\n        )\n\n        # Quoted identifiers are case-sensitive, so a differently-cased reference is not an alias match\n        self.validate_identity('SELECT 1 AS \"idField\" FROM t GROUP BY idfield')\n\n    def test_regexp_like(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-091908-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Exasol dialect tests"}
[tool_result] ....................                                                  [100%]
20 passed, 579 subtests passed in 0.23s
[assistant] Exasol tests pass. Now the full suite, which is the project's check command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3", "description": "Run full test suite and ruff lint/format checks"}
[tool_result] ......................................................................... [ 57%]
.............................................................................................................................. [ 68%]
............................................... [ 72%]
...................................................................................................................................... [ 85%]
........................................................................... [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1108 passed, 18015 subtests passed in 52.86s
All checks passed!
2 files already formatted
[assistant] The MySQL → Exasol alias rewrite now matches case-insensitively, following Exasol's identifier rules. The reported query produces `SELECT 1 AS idField FROM t GROUP BY LOCAL.idField`.

The full suite passes (1108 tests), and ruff lint and format are clean. I didn't commit; the changes are in the working tree.

**The fix** (`sqlglot/generators/exasol.py`): alias names and column references are now keyed by Exasol's folding rule. Unquoted names are upper-cased and quoted names are kept exact. Key matching goes through the new `_alias_key` helper, used in the WHERE/GROUP BY/HAVING pass and the sel
…[172 chars elided]…
alias `"IDFIELD"` referenced as `idfield` would emit `LOCAL."idfield"`, which is wrong.

**Behaviour checked:**
- Unquoted alias and reference in different case now match (GROUP BY, WHERE, HAVING, and select-list alias reuse).
- A quoted alias `"idField"` is not matched by `idfield`, since quoted identifiers are case-sensitive in Exasol.

**Test** (`tests/dialects/test_exasol.py`): added `test_local_prefix_for_alias_case_insensitive`, covering the reported MySQL case, a WHERE case, and the quoted non-match. I did not run it against the unfixed code, so I haven't seen it fail before the change.
