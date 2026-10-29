# trajectory base-1

final message:
Alias references in `WHERE`, `GROUP BY` and `HAVING` now match case-insensitively when the alias and the reference are both unquoted, so your example produces `GROUP BY LOCAL.idField`. The full test suite passes (1107 tests), and ruff is clean.

The change is in `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py`. Aliases and references are keyed by Exasol's effective identifier: upper-cased when unquoted, exact when quoted. So:

- `idField` and `idfield` (unquoted) match.
- A quoted alias `"idField"` does not match an unquoted `idfield`, because Exasol would fold the reference to `IDFIELD`.
- The rewritten reference uses the alias's own spelling and quoting, as before.

I added three cases to `test_local_prefix_for_alias` in `tests/dialects/test_exasol.py`: the mixed-case GROUP BY, a WHERE using a different case, and a quoted-alias case that must stay unrewritten. I didn't run the new tests against the original code to confirm they fail there. The changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "rtk grep -rn \"LOCAL\" sqlglot/ | head -40", "description": "Find LOCAL alias rewrite references"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -rn \"LOCAL\" sqlglot/ | head -40", "description": "Find LOCAL alias rewrite references"}
[tool_result] sqlglot/tokens.py:329:        "LOCALTIME": TokenType.LOCALTIME,
sqlglot/tokens.py:330:        "LOCALTIMESTAMP": TokenType.LOCALTIMESTAMP,
sqlglot/parser.py:761:        TokenType.LOCALTIME,
sqlglot/parser.py:762:        TokenType.LOCALTIMESTAMP,
sqlglot/parser.py:847:        TokenType.LOCALTIME,
sqlglot/parser.py:848:        TokenType.LOCALTIMESTAMP,
sqlglot/parser.py:1553:        "LOCAL": lambda self: self._parse_set_item_assignment("LOCAL"),
sqlglot/parser.py:1722:        "LOCAL",
sqlglot/parse
…[2133 chars elided]…
db.py:80:        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
sqlglot/parsers/duckdb.py:117:        "CURRENT_LOCALTIMESTAMP": exp.Localtimestamp.from_arg_list,
sqlglot/parsers/base.py:10:        TokenType.LOCALTIME: exp.Localtime,
sqlglot/parsers/base.py:11:        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
sqlglot/generators/exasol.py:51:            and table_ident.name.upper() == "LOCAL"
sqlglot/generators/exasol.py:61:                        table=exp.to_identifier("LOCAL", quoted=False),
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
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "offset": 40, "limit": 50}
[tool_result] 40	        aliases: dict[str, bool] = {
41	            alias.name: bool(alias.args.get("quoted"))
42	            for sel in expression.selects
43	            if isinstance(sel, exp.Alias) and (alias := sel.args.get("alias"))
44	        }
45	
46	        table = expression.find(exp.Table)
47	        table_ident = table.this if table else None
48	
49	        if (
50	            table_ident
51	            and table_ident.name.upper() == "LOCAL"
52	            and not bool(table_ident.args.get("quote
…[1151 chars elided]…
.args.get("alias")
77	
78	                seen_aliases[sel.alias] = bool(alias_node and getattr(alias_node, "quoted", False))
79	                new_selects.append(sel)
80	            else:
81	                new_selects.append(sel.transform(lambda node: prefix_local(node, seen_aliases)))
82	        expression.set("expressions", new_selects)
83	
84	    return expression
85	
86	
87	def _trunc_sql(
88	    self: ExasolGenerator, kind: str, expression: exp.DateTrunc | exp.TimestampTrunc
89	) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "def _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, bool] = {\n            alias.name: bool(alias.args.get(\"quoted\"))
…[312 chars elided]…
d else name.upper()\n\n\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, exp.Identifier] = {\n            _alias_key(alias.name, bool(alias.args.get(\"quoted\"))): alias\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        def prefix_local(node: exp.Expr, visible_aliases: dict[str, bool]) -> exp.Expr:\n            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n    
…[1880 chars elided]…
s:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.transform(lambda node: prefix_local(node, seen_aliases))\n                sel.set(\"this\", inner)\n\n                if alias_node := sel.args.get(\"alias\"):\n                    seen_aliases[_alias_key(alias_node.name, bool(alias_node.args.get(\"quoted\")))] = alias_node\n\n                new_selects.append(sel)"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['SELECT 1 AS idField FROM t GROUP BY idfield','SELECT 1 AS idField FROM t WHERE IDFIELD > 1','SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield','SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idField\\\"','SELECT 1 AS idfield FROM t HAVING idField > 1']:\n    print(sqlglot.transpile(s, read='mysql', write='exasol')[0])\n\"; $PY -m ruff format sqlglot/generators/exasol.py && $PY -m ruff check sqlglot/generators/exasol.py; git diff --stat", "description": "Check transpile outputs and lint the change"}
[tool_result] SELECT 1 AS idField FROM t GROUP BY LOCAL.idField
SELECT 1 AS idField FROM t WHERE LOCAL.idField > 1
SELECT 1 AS "idField" FROM t GROUP BY idfield
SELECT 1 AS "idField" FROM t GROUP BY 'idField'
SELECT 1 AS idfield FROM t HAVING LOCAL.idfield > 1
1 file reformatted
All checks passed!
 sqlglot/generators/exasol.py | 24 ++++++++++++++++--------
 1 file changed, 16 insertions(+), 8 deletions(-)
[This command modified 1 file you've previously read: sqlglot/generators/exasol.py. Call Read before editing.]
[assistant] The rewrite now matches case-insensitively for unquoted identifiers. The quoted-alias cases behave per Exasol's rules (quoted names stay case-sensitive; in MySQL `"..."` is a string, so case 4 is expected). Next, I'll find the existing LOCAL alias tests and add coverage.
[tool_use Bash] {"command": "grep -rn \"LOCAL\\.\" tests/dialects/test_exasol.py | head -20; git diff --stat", "description": "Find existing Exasol LOCAL alias tests"}
[tool_result] tests/dialects/test_exasol.py:818:            'SELECT YEAR(a_date) AS "a_year" FROM MY_SUMMARY_TABLE GROUP BY LOCAL."a_year"',
tests/dialects/test_exasol.py:827:                "SELECT YEAR(a_date) AS a_year FROM my_table GROUP BY LOCAL.a_year",
tests/dialects/test_exasol.py:832:                "SELECT SUM(amount) AS total FROM my_table HAVING LOCAL.total > 10000",
tests/dialects/test_exasol.py:837:                "SELECT YEAR(a_date) AS a_year FROM my_table WHERE LOCAL.a_year > 2020",
tests/dia
…[736 chars elided]…
ear FROM t GROUP BY LOCAL.a_year",
tests/dialects/test_exasol.py:1006:            write={"exasol": "SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year"},
tests/dialects/test_exasol.py:1016:            "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1",
tests/dialects/test_exasol.py:1018:            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
 sqlglot/generators/exasol.py | 24 ++++++++++++++++--------
 1 file changed, 16 insertions(+), 8 deletions(-)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "offset": 812, "limit": 50}
[tool_result] 812	    def test_local_prefix_for_alias(self):
813	        self.validate_identity(
814	            'SELECT ID FROM local WHERE "LOCAL".ID IS NULL',
815	            'SELECT ID FROM "LOCAL" WHERE "LOCAL".ID IS NULL',
816	        )
817	        self.validate_identity(
818	            'SELECT YEAR(a_date) AS "a_year" FROM MY_SUMMARY_TABLE GROUP BY LOCAL."a_year"',
819	        )
820	        self.validate_identity(
821	            'SELECT a_year AS a_year FROM "LOCAL" GROUP BY "LOCAL".a_year',
822	    
…[1507 chars elided]…
         "SELECT YEAR(CURRENT_DATE) AS current_year, LOCAL.current_year + 1 AS next_year",
853	                "SELECT YEAR(CURRENT_DATE) AS current_year, current_year + 1 AS next_year",
854	            ),
855	        ]
856	        for title, exasol_sql, dbx_sql in test_cases:
857	            with self.subTest(clause=title):
858	                self.validate_all(
859	                    exasol_sql,
860	                    write={"exasol": exasol_sql, "databricks": dbx_sql},
861	                )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "        for title, exasol_sql, dbx_sql in test_cases:\n            with self.subTest(clause=title):\n                self.validate_all(\n                    exasol_sql,\n                    write={\"exasol\"
…[685 chars elided]…
M t WHERE LOCAL.IDFIELD > 1\",\n            read={\"mysql\": \"SELECT 1 AS idField FROM t WHERE IDFIELD > 1\"},\n            write={\"exasol\": \"SELECT 1 AS idField FROM t WHERE LOCAL.IDFIELD > 1\"},\n        )\n        self.validate_all(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY idfield',\n            write={\"exasol\": 'SELECT 1 AS \"idField\" FROM t GROUP BY idfield'},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "            \"SELECT 1 AS idField FROM t WHERE LOCAL.IDFIELD > 1\",\n            read={\"mysql\": \"SELECT 1 AS idField FROM t WHERE IDFIELD > 1\"},\n            write={\"exasol\": \"SELECT 1 AS idField FROM t WHERE LOCAL.IDFIELD > 1\"},", "new_string": "            \"SELECT 1 AS idField FROM t WHERE LOCAL.idField > 1\",\n            read={\"mysql\": \"SELECT 1 AS idField FROM t WHERE IDFIELD > 1\"},\n            write={\"exasol\": \"SELECT 1 AS idField FROM t WHERE LOCAL.idField > 1\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-105328-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/generators/exasol.py tests/dialects/test_exasol.py && $PY -m ruff check sqlglot tests/dialects/test_exasol.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Format, lint, and run Exasol and full test suites"}
[tool_result] 2 files left unchanged
All checks passed!
...................                                                  [100%]
19 passed, 580 subtests passed in 0.24s
...................................................................................................................................... [ 85%]
........................................................................... [ 91%]
................................. [ 94%]
..........................................................                              [100%]
1107 passed, 18016 subtests passed in 52.79s
[assistant] Alias references in `WHERE`, `GROUP BY` and `HAVING` now match case-insensitively when the alias and the reference are both unquoted, so your example produces `GROUP BY LOCAL.idField`. The full test suite passes (1107 tests), and ruff is clean.

The change is in `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py`. Aliases and references are keyed by Exasol's effective identifier: upper-cased when unquoted, exact when quoted. So:

- `idField` and `idfield` (unquoted) match.
- A quoted alias `"idField"` does not match an unquoted `idfield`, because Exasol would fold the reference to `IDFIELD`.
- The rewritten reference uses the alias's own spelling and quoting, as before.

I added three cases to `test_local_prefix_for_alias` in `tests/dialects/test_exasol.py`: the mixed-case GROUP BY, a WHERE using a different case, and a quoted-alias case that must stay unrewritten. I didn't run the new tests against the original code to confirm they fail there. The changes are uncommitted in the worktree.
