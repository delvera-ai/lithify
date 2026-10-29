# trajectory base-1

final message:
Unquoted alias references in Exasol `WHERE`, `GROUP BY` and `HAVING` are now matched case-insensitively, so your example produces valid SQL:

```
SELECT 1 AS idField FROM t GROUP BY LOCAL.idField
```

The cause was a case-sensitive dict lookup (`node.name in visible_aliases`). The fix is in `sqlglot/generators/exasol.py`:

- **Matching:** aliases and references are keyed by Exasol's identity rule. Unquoted names fold to upper case, quoted names match exactly. A new helper `_exasol_identifier_key` does this.
- **Emitted name:** the `LOCAL.` prefix now uses the alias's own spelling, not the reference's. For unquoted names this is equivalent in Exasol, and it's the spelling the alias was defined with.

I checked the edge cases under Exasol's rules:
- `"idField"` (quoted alias) with `GROUP BY idfield` is left unprefixed, since `IDFIELD` ≠ `idField`.
- `"IDFIELD"` (quoted alias) with `GROUP BY idfield` becomes `LOCAL."IDFIELD"`.
- `GROUP BY "idfield"` against an unquoted `idField` is left unprefixed.

I added cases to `test_group_by_alias_local` in `tests/dialects/test_exasol.py` covering these. The full suite passes with the project's test command (1107 tests), and ruff check and format both pass on the two changed files. My first draft of one new test expected the wrong casing for the emitted alias; I corrected that expectation, and no existing tests were touched.

Nothing is committed.

## events
[tool_use Bash] {"command": "rg -n \"LOCAL\" sqlglot/dialects/exasol.py sqlglot/transforms.py sqlglot/optimizer/*.py | head -50; rg -n \"LOCAL\\b\" sqlglot --type py | head -30", "description": "Find LOCAL alias handling references"}
[tool_result] sqlglot/generators/exasol.py:51:            and table_ident.name.upper() == "LOCAL"
sqlglot/generators/exasol.py:61:                        table=exp.to_identifier("LOCAL", quoted=False),
sqlglot/generators/exasol.py:307:        # Exasol supports a fixed default precision of 3 for TIMESTAMP WITH LOCAL TIME ZONE
sqlglot/generators/exasol.py:310:            return "TIMESTAMP WITH LOCAL TIME ZONE"
sqlglot/parser.py:1553:        "LOCAL": lambda self: self._parse_set_item_assignment("LOCAL"),
sqlglot
…[340 chars elided]…
ext_seq("LOCAL")
sqlglot/parser.py:6302:            elif self._match_text_seq("WITH", "LOCAL", "TIME", "ZONE"):
sqlglot/parsers/exasol.py:143:            and table_ident.name.upper() == "LOCAL"
sqlglot/parsers/singlestore.py:202:        "FULLTEXT SERVICE METRICS LOCAL": _show_parser("FULLTEXT SERVICE METRICS LOCAL"),
sqlglot/generator.py:1751:        local = "LOCAL " if expression.args.get("local") else ""
sqlglot/generator.py:2902:        local = " LOCAL" if expression.args.get("local") else ""
[tool_use Bash] {"command": "cat sqlglot/generators/exasol.py | head -120; echo ----; sed -n 120,200p sqlglot/parsers/exasol.py; echo ----; rg -n \"alias|Alias\" sqlglot/generators/exasol.py sqlglot/dialects/exasol.py sqlglot/parsers/exasol.py | head -40", "description": "Read Exasol generator and parser sources"}
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
…[7414 chars elided]…
.%20You%20can%20use%20an%20expression%20like%20t.*%20to%20list%20all%20columns%20of%20the%20table%20t%2C%20the%20view%20t%2C%20or%20the%20object%20with%20the%20table%20alias%20t.
sqlglot/generators/exasol.py:285:        # https://docs.exasol.com/db/latest/sql_references/data_types/datatypealiases.htm
sqlglot/generators/exasol.py:290:    # https://docs.exasol.com/db/latest/sql_references/data_types/datatypealiases.htm
sqlglot/generators/exasol.py:396:                _add_local_prefix_for_aliases,
[tool_use Bash] {"command": "rg -n \"def quoted|def name\\b\" -A4 sqlglot/expressions*.py sqlglot/expressions/*.py 2>/dev/null | head -40; rg -n \"_add_local_prefix|LOCAL\" tests/dialects/test_exasol.py | head -30; <work>/env-sqlglot/bin/python -c \"import sqlglot;print(sqlglot.transpile('SELECT 1 AS idField FROM t GROUP BY idfield', read='mysql', write='exasol'))\"", "description": "Check Identifier.quoted and reproduce the bug"}
[tool_result] (eval):1: no matches found: sqlglot/expressions*.py
133:            "CAST(x AS TIMESTAMPLTZ)", "CAST(x AS TIMESTAMP WITH LOCAL TIME ZONE)"
136:            "CAST(x AS TIMESTAMP(3) WITH LOCAL TIME ZONE)",
137:            "CAST(x AS TIMESTAMP WITH LOCAL TIME ZONE)",
814:            'SELECT ID FROM local WHERE "LOCAL".ID IS NULL',
815:            'SELECT ID FROM "LOCAL" WHERE "LOCAL".ID IS NULL',
818:            'SELECT YEAR(a_date) AS "a_year" FROM MY_SUMMARY_TABLE GROUP BY LOCAL."a_year"',
821:   
…[911 chars elided]…
02:        # GROUP BY expression alias -> LOCAL prefix
1004:            "SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year",
1006:            write={"exasol": "SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year"},
1014:        # HAVING alias -> LOCAL prefix
1016:            "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1",
1018:            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
['SELECT 1 AS idField FROM t GROUP BY idfield']
[tool_use Bash] {"command": "rg -n \"def quoted|def name\" -A3 sqlglot/expressions/*.py sqlglot/*.py | head -30; sed -n 810,860p tests/dialects/test_exasol.py; sed -n 990,1030p tests/dialects/test_exasol.py", "description": "Locate quoted property and existing alias tests"}
[tool_result] sqlglot/expressions/query.py:86:    def named_selects(self) -> list[str]:
sqlglot/expressions/query.py-87-        return _named_selects(self)
sqlglot/expressions/query.py-88-
sqlglot/expressions/query.py-89-
--
sqlglot/expressions/query.py:546:    def name(self) -> str:
sqlglot/expressions/query.py-547-        return self.this.name
sqlglot/expressions/query.py-548-
sqlglot/expressions/query.py-549-    @property
--
sqlglot/expressions/query.py:963:    def name(self) -> str:
sqlglot/expressions/qu
…[4195 chars elided]…
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
[assistant] Reproduced: the GROUP BY reference is left unprefixed. The cause is `node.name in visible_aliases`, a case-sensitive dict lookup. I'll key aliases by Exasol's folded identity (unquoted → upper, quoted → exact) and emit the alias's own spelling.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n     
…[522 chars elided]…
ql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, exp.Identifier] = {\n            _exasol_identifier_key(alias): alias\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        def prefix_local(node: exp.Expr, visible_aliases: dict[str, bool]) -> exp.Expr:\n            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n    
…[326 chars elided]…
: dict[str, exp.Identifier]) -> exp.Expr:\n            if isinstance(node, exp.Column) and not node.table:\n                if alias := visible_aliases.get(_exasol_identifier_key(node.this)):\n                    return exp.Column(\n                        this=alias.copy(),\n                        table=exp.to_identifier(\"LOCAL\", quoted=False),\n                    )\n            return node"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        seen_aliases: dict[str, bool] = {}\n        new_selects: list[exp.Expr] = []\n        for sel in expression.selects:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.trans
…[411 chars elided]…
      for sel in expression.selects:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.transform(lambda node: prefix_local(node, seen_aliases))\n                sel.set(\"this\", inner)\n\n                if alias_node := sel.args.get(\"alias\"):\n                    seen_aliases[_exasol_identifier_key(alias_node)] = alias_node\n                new_selects.append(sel)"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now I'll check the reported case and the edge cases (quoted vs unquoted on each side), then add tests.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\ncases = [\n 'SELECT 1 AS idField FROM t GROUP BY idfield',\n 'SELECT 1 AS idField FROM t WHERE IDFIELD > 1',\n 'SELECT COUNT(*) AS cnt FROM t HAVING CNT > 1',\n 'SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield',\n 'SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idField\\\"',\n 'SELECT 1 AS \\\"IDFIELD\\\" FROM t GROUP BY idfield',\n 'SELECT 1 AS idField FROM t GROUP BY \\\"idfield\\\"',\n 'SELECT YR AS THE_YEAR, ID AS YR, the_year + 1 AS NEXT_YEAR FROM my_table',\n]\nfor c in cases: print(sqlglot.transpile(c, read='mysql', write='exasol')[0])\n\"", "description": "Check case-insensitive alias rewrite on edge cases"}
[tool_result] SELECT 1 AS idField FROM t GROUP BY LOCAL.idField
SELECT 1 AS idField FROM t WHERE LOCAL.idField > 1
SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1
SELECT 1 AS "idField" FROM t GROUP BY idfield
SELECT 1 AS "idField" FROM t GROUP BY 'idField'
SELECT 1 AS "IDFIELD" FROM t GROUP BY LOCAL."IDFIELD"
SELECT 1 AS idField FROM t GROUP BY 'idfield'
SELECT YR AS THE_YEAR, ID AS YR, LOCAL.THE_YEAR + 1 AS NEXT_YEAR FROM my_table
[assistant] The MySQL-read quoted-reference cases are MySQL string literals, so they aren't meaningful. I'll re-check those with `read='exasol'`, then add tests.
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor c in ['SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idField\\\"', 'SELECT 1 AS idField FROM t GROUP BY \\\"idfield\\\"', 'SELECT 1 AS \\\"IDFIELD\\\" FROM t GROUP BY \\\"IDFIELD\\\"']:\n    print(sqlglot.transpile(c, read='exasol', write='exasol')[0])\n\"", "description": "Check quoted-reference cases under Exasol read"}
[tool_result] SELECT 1 AS "idField" FROM t GROUP BY LOCAL."idField"
SELECT 1 AS idField FROM t GROUP BY "idfield"
SELECT 1 AS "IDFIELD" FROM t GROUP BY LOCAL."IDFIELD"
[assistant] All correct under Exasol's rules. Now the regression tests, appended to the existing alias test method.
[tool_use Bash] {"command": "sed -n 1030,1040p tests/dialects/test_exasol.py", "description": "View end of alias local test method"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "wc -l tests/dialects/test_exasol.py && tail -n +1018 tests/dialects/test_exasol.py", "description": "View tail of Exasol test file"}
[tool_result]     1019 tests/dialects/test_exasol.py
            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "            write={\"exasol\": \"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1\"},\n        )", "new_string": "            write={\"exasol\": \"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1\"},\n  
…[659 chars elided]…
liases are case-sensitive, so they only match the exact spelling\n        self.validate_identity(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY LOCAL.\"idField\"',\n        )\n        self.validate_identity(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY idfield',\n        )\n        self.validate_identity(\n            'SELECT 1 AS idField FROM t GROUP BY \"idfield\"',\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Running the Exasol dialect tests, then the full suite with the project's command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -30", "description": "Run Exasol dialect tests"}
[tool_result] ...................                                                   [100%]
=================================== FAILURES ===================================
_ TestExasol.test_group_by_alias_local [mysql -> SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.CNT > 1] _
tests/dialects/test_dialect.py:85: in validate_all
    self.assertEqual(
E   AssertionError: 'SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.cnt > 1' != 'SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.CNT > 1'
E   - SELECT COUNT(*) AS cnt FROM t WHER
…[605 chars elided]…
T(*) AS cnt FROM t WHERE LOCAL.CNT > 1
E   ?                                           ^^^
=========================== short test summary info ============================
SUBFAILED[mysql -> SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.CNT > 1] tests/dialects/test_exasol.py::TestExasol::test_group_by_alias_local
SUBFAILED[SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.CNT > 1 -> exasol] tests/dialects/test_exasol.py::TestExasol::test_group_by_alias_local
2 failed, 19 passed, 577 subtests passed in 0.27s
[assistant] Both failures are in the new test I just wrote, not the code: the emitted prefix uses the alias's own spelling (`cnt`), which is the intended behavior. Correcting my expectation:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "            \"SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.CNT > 1\",\n            read={\"mysql\": \"SELECT COUNT(*) AS cnt FROM t WHERE CNT > 1\"},\n            write={\"exasol\": \"SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.CNT > 1\"},", "new_string": "            \"SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.cnt > 1\",\n            read={\"mysql\": \"SELECT COUNT(*) AS cnt FROM t WHERE CNT > 1\"},\n            write={\"exasol\": \"SELECT COUNT(*) AS cnt FROM t WHERE LOCAL.cnt > 1\"},"}
[tool_result] The file ~/.cache/lithify/work/repo-d5521a213087/20261028-182201-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Run Exasol tests then full project test suite"}
[tool_result] ...................                                                   [100%]
19 passed, 579 subtests passed in 0.15s
........................................................................................................ [ 91%]
................................. [ 94%]
............................. [ 97%]
............................                               [100%]
1107 passed, 18015 subtests passed in 49.38s
[assistant] Full suite passes (1107 tests). Last, a lint/format check on the two changed files.
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generators/exasol.py
 M tests/dialects/test_exasol.py
[assistant] Unquoted alias references in Exasol `WHERE`, `GROUP BY` and `HAVING` are now matched case-insensitively, so your example produces valid SQL:

```
SELECT 1 AS idField FROM t GROUP BY LOCAL.idField
```

The cause was a case-sensitive dict lookup (`node.name in visible_aliases`). The fix is in `sqlglot/generators/exasol.py`:

- **Matching:** aliases and references are keyed by Exasol's identity rule. Unquoted names fold to upper case, quoted names match exactly. A new helper `_exasol_identifier_key` does this.
- **Emitted name:** the `LOCAL.` prefix now uses the alias's own spelling, not the refe
…[206 chars elided]…
d` is left unprefixed, since `IDFIELD` ≠ `idField`.
- `"IDFIELD"` (quoted alias) with `GROUP BY idfield` becomes `LOCAL."IDFIELD"`.
- `GROUP BY "idfield"` against an unquoted `idField` is left unprefixed.

I added cases to `test_group_by_alias_local` in `tests/dialects/test_exasol.py` covering these. The full suite passes with the project's test command (1107 tests), and ruff check and format both pass on the two changed files. My first draft of one new test expected the wrong casing for the emitted alias; I corrected that expectation, and no existing tests were touched.

Nothing is committed.
