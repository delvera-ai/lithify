# trajectory base-1

final message:
MySQL → Exasol alias references now match unquoted aliases case-insensitively, so `SELECT 1 AS idField FROM t GROUP BY idfield` transpiles to `... GROUP BY LOCAL.idField`. The full suite passes (1107 tests), and ruff check and format are clean on the changed files.

The fix is in `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py`. Aliases are now keyed by the name Exasol would resolve them to: unquoted names fold to upper case, quoted names stay exact. The rewrite emits the alias's own identifier, so the output keeps the alias's spelling and quoting. That matters for a quoted alias like `"IDFIELD"` referenced as `idfield`: it must not be emitted as `"idfield"`.

Behaviour across the quoting combinations:
- Unquoted alias `idField`, unquoted reference `idfield`: rewritten to `LOCAL.idField`.
- Quoted alias `"idField"`, unquoted reference `idfield`: not rewritten, since they name different identifiers.
- Quoted alias `"idField"`, quoted reference `"idField"`: rewritten, as before.

I added tests to `tests/dialects/test_exasol.py` next to the existing alias tests. They cover the reported case, a case-insensitive WHERE reference, and quoted aliases staying case-sensitive. The reported case failed before the change, and the Exasol test file passes after it.

I have not committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"LOCAL\" sqlglot/dialects/exasol.py sqlglot/transforms.py sqlglot/optimizer/*.py sqlglot/dialects/dialect.py | head -40", "description": "Search for LOCAL alias handling"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "git status --short | head; ls; grep -rln \"LOCAL\" sqlglot | head -20; grep -rn \"class Exasol\" sqlglot/dialects/", "description": "Check repo layout and find LOCAL references"}
[tool_result] AGENTS.md
CHANGELOG.md
CLAUDE.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
Makefile
README.md
benchmarks
pdoc
posts
pyproject.toml
setup.cfg
setup.py
sqlglot
sqlglot-integration-tests
sqlglot.png
sqlglotc
tests
sqlglot/tokenizer_core.py
sqlglot/parser.py
sqlglot/generator.py
sqlglot/tokens.py
sqlglot/parsers/snowflake.py
sqlglot/parsers/postgres.py
sqlglot/parsers/duckdb.py
sqlglot/parsers/oracle.py
sqlglot/parsers/singlestore.py
sqlglot/parsers/mysql.py
sqlglot/parsers/base.py
sqlglot/parsers/presto.py
sqlglot/parsers/exasol.py
sqlglot/parsers/teradata.py
sqlglot/generators/exasol.py
sqlglot/generators/duckdb.py
sqlglot/dialects/exasol.py:14:class Exasol(Dialect):
[tool_use Bash] {"command": "grep -rn \"LOCAL\" sqlglot/generators/exasol.py sqlglot/optimizer/ sqlglot/generator.py | head -30; grep -rn \"LocalAlias\\|local_alias\\|\\bLOCAL\\b\" sqlglot/ --include=*.py | head -30", "description": "Locate LOCAL alias rewrite code"}
[tool_result] sqlglot/generators/exasol.py:51:            and table_ident.name.upper() == "LOCAL"
sqlglot/generators/exasol.py:61:                        table=exp.to_identifier("LOCAL", quoted=False),
sqlglot/generators/exasol.py:307:        # Exasol supports a fixed default precision of 3 for TIMESTAMP WITH LOCAL TIME ZONE
sqlglot/generators/exasol.py:310:            return "TIMESTAMP WITH LOCAL TIME ZONE"
sqlglot/generator.py:1751:        local = "LOCAL " if expression.args.get("local") else ""
sqlglot/generator.py:2902:        local = " LOCAL" if expression.args.get("local") else ""
sqlglot/generator.py:5972:        return self.func("LOCALTIME", this) if this else "LOCALTIME"
sqlglot/generator.py:5976:        return self.func("LOCALTIMESTAMP", this) if this else "LOCALTIMESTAMP"
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "cat sqlglot/generators/exasol.py | head -120", "description": "Read Exasol generator"}
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
…[3395 chars elided]…
ression: exp.DateTrunc | exp.TimestampTrunc
) -> str:
    return _trunc_sql(self, "TIMESTAMP", expression)


def is_case_insensitive(node: exp.Expr) -> bool:
    return isinstance(node, exp.Collate) and node.text("expression").upper() == "UTF8_LCASE"


def _substring_index_sql(self: ExasolGenerator, expression: exp.SubstringIndex) -> str:
    this = expression.this
    delimiter = expression.args["delimiter"]
    count_node = expression.args["count"]
    count_sql = self.sql(expression, "count")
[tool_use Bash] {"command": "grep -rn \"LOCAL\\.\" tests/dialects/test_exasol.py | head -30; grep -n \"NORMALIZATION\\|class Exasol\" -A3 sqlglot/dialects/exasol.py | head -20", "description": "Check existing LOCAL tests and Exasol normalization"}
[tool_result] tests/dialects/test_exasol.py:818:            'SELECT YEAR(a_date) AS "a_year" FROM MY_SUMMARY_TABLE GROUP BY LOCAL."a_year"',
tests/dialects/test_exasol.py:827:                "SELECT YEAR(a_date) AS a_year FROM my_table GROUP BY LOCAL.a_year",
tests/dialects/test_exasol.py:832:                "SELECT SUM(amount) AS total FROM my_table HAVING LOCAL.total > 10000",
tests/dialects/test_exasol.py:837:                "SELECT YEAR(a_date) AS a_year FROM my_table WHERE LOCAL.a_year > 2020",
tests/dia
…[1006 chars elided]…
,
tests/dialects/test_exasol.py:1018:            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
14:class Exasol(Dialect):
15-    # https://docs.exasol.com/db/latest/sql_references/basiclanguageelements.htm#SQLidentifier
16:    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
17-    # https://docs.exasol.com/db/latest/sql_references/data_types/datatypesoverview.htm
18-    SUPPORTS_USER_DEFINED_TYPES = False
19-    # https://docs.exasol.com/db/latest/sql/select.htm
[tool_use Bash] {"command": "sed -n 810,860p tests/dialects/test_exasol.py; sed -n 990,1025p tests/dialects/test_exasol.py", "description": "Read existing alias rewrite tests"}
[tool_result]         )

    def test_local_prefix_for_alias(self):
        self.validate_identity(
            'SELECT ID FROM local WHERE "LOCAL".ID IS NULL',
            'SELECT ID FROM "LOCAL" WHERE "LOCAL".ID IS NULL',
        )
        self.validate_identity(
            'SELECT YEAR(a_date) AS "a_year" FROM MY_SUMMARY_TABLE GROUP BY LOCAL."a_year"',
        )
        self.validate_identity(
            'SELECT a_year AS a_year FROM "LOCAL" GROUP BY "LOCAL".a_year',
        )

        test_cases = [
   
…[2767 chars elided]…
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
[assistant] Reproducing the bug first, then I'll fix it.
[tool_use Bash] {"command": "PYTHONPATH=. python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT 1 AS idField FROM t GROUP BY idfield', read='mysql', write='exasol'))\nprint(sqlglot.transpile('SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idField\\\"', read='mysql', write='exasol'))\n\"", "description": "Reproduce the case-sensitive alias miss"}
[tool_result] ['SELECT 1 AS idField FROM t GROUP BY idfield']
['SELECT 1 AS "idField" FROM t GROUP BY \'idField\'']
[assistant] Reproduced: the unquoted `idfield` reference is left untouched. Now the fix: key aliases by their Exasol-folded name (unquoted → upper case, quoted → exact), and emit the alias's own identifier so the output stays valid.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151559-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n     
…[526 chars elided]…
est/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, exp.Identifier] = {\n            _exasol_alias_key(alias): alias\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151559-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151559-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        def prefix_local(node: exp.Expr, visible_aliases: dict[str, bool]) -> exp.Expr:\n            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n    
…[1725 chars elided]…
]\n        for sel in expression.selects:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.transform(lambda node: prefix_local(node, seen_aliases))\n                sel.set(\"this\", inner)\n\n                if alias_node := sel.args.get(\"alias\"):\n                    seen_aliases[_exasol_alias_key(alias_node)] = alias_node\n                new_selects.append(sel)"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151559-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now I'll add regression tests next to the existing alias tests, covering the reported case and the quoting rules that must not change.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-b63a38b63828/20261026-151559-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "        # HAVING alias -> LOCAL prefix\n        self.validate_all(\n            \"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1\",\n            read={\"mysql\": \"SELECT COUNT(*) AS cnt FROM t HAVING cn
…[960 chars elided]…
 WHERE IDFIELD > 0\"},\n            write={\"exasol\": \"SELECT 1 AS idField FROM t WHERE LOCAL.idField > 0\"},\n        )\n        # Quoted identifiers stay case-sensitive\n        self.validate_identity(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY LOCAL.\"idField\"',\n        )\n        self.validate_identity(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY idfield',\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-b63a38b63828/20261026-151559-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls $PY 2>/dev/null || PY=python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -30", "description": "Run Exasol dialect tests"}
[tool_result] <work>/env-sqlglot/bin/python
...................                                                   [100%]
19 passed, 579 subtests passed in 0.29s
[assistant] Exasol tests pass. Now the full suite, plus the reported case and the mixed-quoting edge cases.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in [\n 'SELECT 1 AS idField FROM t GROUP BY idfield',\n 'SELECT 1 AS \\\"IDFIELD\\\" FROM t GROUP BY idfield',\n 'SELECT 1 AS idfield FROM t GROUP BY \\\"IDFIELD\\\"',\n 'SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield',\n]:\n    print(sqlglot.transpile(s, read='mysql', write='exasol'))\n\"", "description": "Run full test suite and edge-case checks"}
[tool_result] ........................................................................................................ [ 91%]
................................. [ 94%]
............................. [ 97%]
............................                               [100%]
1107 passed, 18015 subtests passed in 54.97s
['SELECT 1 AS idField FROM t GROUP BY LOCAL.idField']
['SELECT 1 AS "IDFIELD" FROM t GROUP BY LOCAL."IDFIELD"']
["SELECT 1 AS idfield FROM t GROUP BY 'IDFIELD'"]
['SELECT 1 AS "idField" FROM t GROUP BY idfield']
[assistant] All 1107 tests pass. The third case is a MySQL quirk (double quotes are string literals there), so I'll confirm the quoted-reference rule through the Exasol reader and run the linter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT 1 AS idfield FROM t GROUP BY \\\"IDFIELD\\\"', read='exasol', write='exasol'))\n\"; ($PY -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && $PY -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git diff --stat", "description": "Check quoted reference, lint and format changed files"}
[tool_result] ['SELECT 1 AS idfield FROM t GROUP BY LOCAL.idfield']
All checks passed!
2 files already formatted
 sqlglot/generators/exasol.py  | 22 +++++++++++++---------
 tests/dialects/test_exasol.py | 18 ++++++++++++++++++
 2 files changed, 31 insertions(+), 9 deletions(-)
[assistant] MySQL → Exasol alias references now match unquoted aliases case-insensitively, so `SELECT 1 AS idField FROM t GROUP BY idfield` transpiles to `... GROUP BY LOCAL.idField`. The full suite passes (1107 tests), and ruff check and format are clean on the changed files.

The fix is in `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py`. Aliases are now keyed by the name Exasol would resolve them to: unquoted names fold to upper case, quoted names stay exact. The rewrite emits the alias's own identifier, so the output keeps the alias's spelling and quoting. That matters for a quoted al
…[119 chars elided]…
inations:
- Unquoted alias `idField`, unquoted reference `idfield`: rewritten to `LOCAL.idField`.
- Quoted alias `"idField"`, unquoted reference `idfield`: not rewritten, since they name different identifiers.
- Quoted alias `"idField"`, quoted reference `"idField"`: rewritten, as before.

I added tests to `tests/dialects/test_exasol.py` next to the existing alias tests. They cover the reported case, a case-insensitive WHERE reference, and quoted aliases staying case-sensitive. The reported case failed before the change, and the Exasol test file passes after it.

I have not committed anything.
