# trajectory base-1

final message:
Unquoted alias references now match case-insensitively in Exasol output, so the report's example produces `GROUP BY LOCAL.idfield` instead of invalid SQL.

**The fix** is in `sqlglot/generators/exasol.py`, in `_add_local_prefix_for_aliases`. The alias map and the reference lookup both used the raw name. They now go through a small `_alias_key` helper that follows Exasol's rule:
- Unquoted names are keyed by their upper-cased form, so `idField` and `idfield` match.
- Quoted names keep their exact spelling, so `"idField"` does not match `idfield`. Those references are left unchanged, as before.

The rewrite still emits the reference's own spelling, and the `LOCAL` prefix only applies when the key matches.

**Tests** are in `tests/dialects/test_exasol.py`, in `test_group_by_alias_local`. They cover:
- the report's case (`GROUP BY idfield` after `AS idField`)
- a `HAVING` case with different casing
- a quoted alias that should not be rewritten for a differently-cased reference

**Verification:**
- `tests/dialects/test_exasol.py`: 19 passed.
- Full suite: 1107 passed.
- `ruff check` and `ruff format --check` pass on both changed files.

I did not commit. The working tree has the two file changes for you to review.

## events
[tool_use Bash] {"command": "grep -rn \"LOCAL\" sqlglot/dialects/exasol.py sqlglot/transforms.py sqlglot/generator.py | head -40", "description": "Find LOCAL alias handling references"}
[tool_result] sqlglot/generator.py:1751:        local = "LOCAL " if expression.args.get("local") else ""
sqlglot/generator.py:2902:        local = " LOCAL" if expression.args.get("local") else ""
sqlglot/generator.py:5972:        return self.func("LOCALTIME", this) if this else "LOCALTIME"
sqlglot/generator.py:5976:        return self.func("LOCALTIMESTAMP", this) if this else "LOCALTIMESTAMP"
[tool_use Bash] {"command": "grep -rn \"LOCAL\\|local\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -30; grep -rln \"Exasol\" sqlglot | head; ls sqlglot/dialects | grep -i exa", "description": "Search Exasol and MySQL dialects for LOCAL handling"}
[tool_result] sqlglot/parsers/exasol.py
sqlglot/dialects/__init__.py
sqlglot/dialects/exasol.py
sqlglot/generators/exasol.py
exasol.py  2.0K
[tool_use Bash] {"command": "cat sqlglot/generators/exasol.py; grep -rn \"local\" sqlglot/optimizer/*.py sqlglot/transforms.py | grep -i \"alias\\|local=\" | head -20", "description": "Read Exasol generator and search for local alias rewrites"}
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
…[28739 chars elided]…
       else:
                expression.set(
                    "expression",
                    exp.Paren(
                        this=exp.Concat(
                            expressions=[
                                exp.Literal.string(".*"),
                                pattern,
                                exp.Literal.string(".*"),
                            ]
                        )
                    ),
                )
        return self.binary(expression, "REGEXP_LIKE")
[assistant] The alias lookup in `_add_local_prefix_for_aliases` keys on the raw `name`, so `idfield` never matches `idField`. Let me check the existing tests before changing it.
[tool_use Bash] {"command": "grep -n \"LOCAL\" tests/dialects/test_exasol.py | head -60", "description": "Find existing LOCAL alias tests in Exasol tests"}
[tool_result] 22 matches in 4 files:

1000:0:"SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt"},
1006:0:"SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year"},
1018:0:"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
tests/dialects/test_exasol.py:133:"CAST(x AS TIMESTAMPLTZ)", "CAST(x AS TIMESTAMP WITH LOCAL TIME ZONE)"
tests/dialects/test_exasol.py:136:"CAST(x AS TIMESTAMP(3) WITH LOCAL TIME ZONE)",
tests/dialects/test_exasol.py:137:"CAST(x AS TIMESTAMP WITH LOCAL TIME ZONE)",
tes
…[1051 chars elided]…
ts/dialects/test_exasol.py:996:# GROUP BY bare alias -> LOCAL prefix
tests/dialects/test_exasol.py:998:"SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt",
tests/dialects/test_exasol.py:1002:# GROUP BY expression alias -> LOCAL prefix
tests/dialects/test_exasol.py:1004:"SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year",
tests/dialects/test_exasol.py:1014:# HAVING alias -> LOCAL prefix
tests/dialects/test_exasol.py:1016:"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1",
[tool_use Bash] {"command": "sed -n 806,856p tests/dialects/test_exasol.py; sed -n 990,1025p tests/dialects/test_exasol.py", "description": "Read existing alias rewrite tests"}
[tool_result]         self.validate_identity("SELECT {d'2024-01-01'}", "SELECT TO_DATE('2024-01-01')")
        self.validate_identity(
            "SELECT {ts'2024-01-01 12:00:00'}",
            "SELECT TO_TIMESTAMP('2024-01-01 12:00:00')",
        )

    def test_local_prefix_for_alias(self):
        self.validate_identity(
            'SELECT ID FROM local WHERE "LOCAL".ID IS NULL',
            'SELECT ID FROM "LOCAL" WHERE "LOCAL".ID IS NULL',
        )
        self.validate_identity(
            'SELECT Y
…[2809 chars elided]…
 city, COUNT(*) FROM t GROUP BY city",
            read={"mysql": "SELECT city, COUNT(*) FROM t GROUP BY city"},
            write={"exasol": "SELECT city, COUNT(*) FROM t GROUP BY city"},
        )
        # HAVING alias -> LOCAL prefix
        self.validate_all(
            "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1",
            read={"mysql": "SELECT COUNT(*) AS cnt FROM t HAVING cnt > 1"},
            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
        )
[assistant] I'll key the alias map on Exasol's identifier rule: unquoted names fold to upper case, quoted names stay exact. Both the alias registry and the reference lookup go through the same key.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n     
…[517 chars elided]…
x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, bool] = {\n            _alias_key(alias.name, bool(alias.args.get(\"quoted\"))): bool(alias.args.get(\"quoted\"))\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n                    return exp.Column(\n                        this=exp.to_identifier(node.n
…[225 chars elided]…
and not node.table:\n                key = _alias_key(node.name, bool(node.this.args.get(\"quoted\")))\n                if key in visible_aliases:\n                    return exp.Column(\n                        this=exp.to_identifier(node.name, quoted=visible_aliases[key]),\n                        table=exp.to_identifier(\"LOCAL\", quoted=False),\n                    )\n            return node"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "                seen_aliases[sel.alias] = bool(alias_node and getattr(alias_node, \"quoted\", False))", "new_string": "                quoted = bool(alias_node and getattr(alias_node, \"quoted\", False))\n                seen_aliases[_alias_key(sel.alias, quoted)] = quoted"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now I'll check the new behavior against the cases from the report and some edge cases (quoted aliases must stay case-sensitive).
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c '\nimport sqlglot\nfor s in [\n \"SELECT 1 AS idField FROM t GROUP BY idfield\",\n \"SELECT COUNT(*) AS cnt FROM t HAVING CNT > 1\",\n \"SELECT YEAR(a_date) AS a_year FROM t WHERE A_YEAR > 2020\",\n \"SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield\",\n \"SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"IDFIELD\\\"\",\n \"SELECT 1 AS idField FROM t GROUP BY \\\"IDFIELD\\\"\",\n \"SELECT 1 AS idField FROM t GROUP BY \\\"idfield\\\"\",\n \"SELECT x AS a, a AS b FROM t WHERE B > 1\",\n]:\n    print(sqlglot.transpile(s, read=\"mysql\", write=\"exasol\")[0])\n' 2>&1", "description": "Check transpile output for alias case variants"}
[tool_result] SELECT 1 AS idField FROM t GROUP BY LOCAL.idfield
SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.CNT > 1
SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t WHERE LOCAL.A_YEAR > 2020
SELECT 1 AS "idField" FROM t GROUP BY idfield
SELECT 1 AS "idField" FROM t GROUP BY 'IDFIELD'
SELECT 1 AS idField FROM t GROUP BY 'IDFIELD'
SELECT 1 AS idField FROM t GROUP BY 'idfield'
SELECT x AS a, LOCAL.a AS b FROM t WHERE LOCAL.B > 1
[assistant] Double quotes are string literals in MySQL, so those last three cases didn't test identifiers. Re-running them with backtick-quoted identifiers:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c '\nimport sqlglot\nfor s in [\n \"SELECT 1 AS `idField` FROM t GROUP BY idfield\",\n \"SELECT 1 AS `idField` FROM t GROUP BY `idfield`\",\n \"SELECT 1 AS idField FROM t GROUP BY `IDFIELD`\",\n \"SELECT 1 AS idField FROM t GROUP BY `idField`\",\n \"SELECT 1 AS `idField` FROM t GROUP BY `IDFIELD`\",\n \"SELECT 1 AS `idField` FROM t GROUP BY `idField`\",\n \"SELECT 1 AS `idField` FROM t GROUP BY idField\",\n]:\n    print(sqlglot.transpile(s, read=\"mysql\", write=\"exasol\")[0])\n' 2>&1", "description": "Check quoted-identifier alias cases with backticks"}
[tool_result] SELECT 1 AS "idField" FROM t GROUP BY idfield
SELECT 1 AS "idField" FROM t GROUP BY "idfield"
SELECT 1 AS idField FROM t GROUP BY LOCAL.IDFIELD
SELECT 1 AS idField FROM t GROUP BY "idField"
SELECT 1 AS "idField" FROM t GROUP BY "IDFIELD"
SELECT 1 AS "idField" FROM t GROUP BY LOCAL."idField"
SELECT 1 AS "idField" FROM t GROUP BY idField
[assistant] The results follow Exasol's rules: unquoted aliases match any case of the reference, quoted aliases only match their exact spelling. Now I'll add regression tests next to the existing alias tests.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "        # HAVING alias -> LOCAL prefix\n        self.validate_all(\n            \"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1\",\n            read={\"mysql\": \"SELECT COUNT(*) AS cnt FROM t HAVING cn
…[1049 chars elided]…
HAVING LOCAL.CNT > 1\"},\n        )\n        # Quoted aliases are case-sensitive, so a differently-cased reference is not rewritten\n        self.validate_all(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY idfield',\n            read={\"mysql\": 'SELECT 1 AS `idField` FROM t GROUP BY idfield'},\n            write={\"exasol\": 'SELECT 1 AS \"idField\" FROM t GROUP BY idfield'},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15", "description": "Run Exasol dialect tests"}
[tool_result] ...................                                                 [100%]
19 passed, 581 subtests passed in 0.22s
[assistant] Exasol tests pass. Running the full suite as the final gate, plus a lint pass on the two changed files.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3", "description": "Run full test suite and lint changed files"}
[tool_result] ...................................................................................................................................... [ 84%]
........................................................................... [ 91%]
............................................................... [ 97%]
.............................                             [100%]
1107 passed, 18017 subtests passed in 54.68s
All checks passed!
Would reformat: tests/dialects/test_exasol.py
1 file would be reformatted, 1 file already formatted
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --diff tests/dialects/test_exasol.py 2>&1 | head -30; git stash list | head -0; git diff --stat", "description": "Show formatter diff for the test file"}
[tool_result] --- tests/dialects/test_exasol.py
+++ tests/dialects/test_exasol.py
@@ -1031,6 +1031,6 @@
         # Quoted aliases are case-sensitive, so a differently-cased reference is not rewritten
         self.validate_all(
             'SELECT 1 AS "idField" FROM t GROUP BY idfield',
-            read={"mysql": 'SELECT 1 AS `idField` FROM t GROUP BY idfield'},
+            read={"mysql": "SELECT 1 AS `idField` FROM t GROUP BY idfield"},
             write={"exasol": 'SELECT 1 AS "idField" FROM t GROUP BY idfield'},
         )

1 file would be reformatted
head: illegal line count -- 0

thread 'main' (42800495) panicked at /rustc/59807616e1fa2540724bfbac14d7976d7e4a3860/library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
sqlglot/generators/exasol.py  | 15 +++++++++++----
 tests/dialects/test_exasol.py | 17 +++++++++++++++++
 2 files changed, 28 insertions(+), 4 deletions(-)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "            read={\"mysql\": 'SELECT 1 AS `idField` FROM t GROUP BY idfield'},", "new_string": "            read={\"mysql\": \"SELECT 1 AS `idField` FROM t GROUP BY idfield\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-153504-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format --check tests/dialects/test_exasol.py sqlglot/generators/exasol.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -1", "description": "Verify formatting and rerun Exasol tests"}
[tool_result] 2 files already formatted
19 passed, 581 subtests passed in 0.15s
[assistant] Unquoted alias references now match case-insensitively in Exasol output, so the report's example produces `GROUP BY LOCAL.idfield` instead of invalid SQL.

**The fix** is in `sqlglot/generators/exasol.py`, in `_add_local_prefix_for_aliases`. The alias map and the reference lookup both used the raw name. They now go through a small `_alias_key` helper that follows Exasol's rule:
- Unquoted names are keyed by their upper-cased form, so `idField` and `idfield` match.
- Quoted names keep their exact spelling, so `"idField"` does not match `idfield`. Those references are left unchanged, as before.

…[28 chars elided]…
 reference's own spelling, and the `LOCAL` prefix only applies when the key matches.

**Tests** are in `tests/dialects/test_exasol.py`, in `test_group_by_alias_local`. They cover:
- the report's case (`GROUP BY idfield` after `AS idField`)
- a `HAVING` case with different casing
- a quoted alias that should not be rewritten for a differently-cased reference

**Verification:**
- `tests/dialects/test_exasol.py`: 19 passed.
- Full suite: 1107 passed.
- `ruff check` and `ruff format --check` pass on both changed files.

I did not commit. The working tree has the two file changes for you to review.
