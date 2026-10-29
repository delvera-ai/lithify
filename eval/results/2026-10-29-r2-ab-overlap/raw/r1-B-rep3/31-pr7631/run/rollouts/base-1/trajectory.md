# trajectory base-1

final message:
Unquoted alias references now match case-insensitively, so `SELECT 1 AS idField FROM t GROUP BY idfield` transpiles to Exasol as `GROUP BY LOCAL.idField`. The same applies to `WHERE` and `HAVING`. The full suite passes (1107 tests), and ruff, format and mypy are clean. I haven't committed.

The fix is in `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py`. Alias names are now compared using Exasol's identifier rule: unquoted names are folded to upper case, quoted names are compared exactly.

Two behaviours to be aware of:

- **Output spelling:** the rewritten reference uses the alias's spelling and quoting, not the reference's. So `idfield` becomes `LOCAL.idField`. This is semantically identical in Exasol, but it differs from the input text. Say if you'd rather keep the reference's spelling.
- **Quoted aliases stay case-sensitive:** `"idField"` does not match `idfield`, which is correct under Exasol's rules. `"IDFIELD"` does match an unquoted `idfield`, and it is emitted as `LOCAL."IDFIELD"`.

I added regression tests to `tests/dialects/test_exasol.py` next to the existing alias-rewrite tests. They cover unquoted GROUP BY and WHERE cases, and the quoted-alias cases in both directions. Existing tests are unchanged.

## events
[tool_use Bash] {"command": "grep -rn \"LOCAL\" sqlglot/dialects/exasol.py sqlglot/transforms.py sqlglot/optimizer/*.py | head -40", "description": "Find LOCAL alias handling references"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "pwd && ls sqlglot/dialects | head -50 && grep -rln \"LOCAL\" sqlglot | head", "description": "Check repo layout and find LOCAL references"}
[tool_result] ~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1
__init__.py  3.6K
athena.py  4.3K
bigquery.py  7.1K
clickhouse.py  4.6K
databricks.py  1.1K
dialect.py  91.0K
doris.py  364B
dremio.py  1.6K
drill.py  1.4K
druid.py  224B
duckdb.py  4.2K
dune.py  329B
exasol.py  2.0K
fabric.py  1.8K
hive.py  3.6K
materialize.py  305B
mysql.py  5.7K
oracle.py  3.3K
postgres.py  4.5K
presto.py  2.1K
prql.py  782B
redshift.py  1.9K
risingwave.py  618B
singlestore.py  2.1K
snowflake.py  6.5K
solr.py  535B
spark.py  897B
spark2.py  977B
sqlite.py  1.1K
starrocks.py  529B
tableau.py  432B
teradata.py  2.5K
trino.py  545B
tsql.py  5.3K
sqlglot/parsers/singlestore.py
sqlglot/parsers/snowflake.py
sqlglot/parsers/postgres.py
sqlglot/parsers/presto.py
sqlglot/parsers/oracle.py
sqlglot/parsers/exasol.py
sqlglot/parsers/duckdb.py
sqlglot/parsers/teradata.py
sqlglot/parsers/base.py
sqlglot/parsers/mysql.py
[tool_use Bash] {"command": "cat sqlglot/dialects/exasol.py && grep -rn \"LOCAL\" sqlglot --include=*.py | grep -v \"LOCAL_\\|_LOCAL\" | head -30", "description": "Show Exasol dialect and LOCAL references"}
[tool_result] from __future__ import annotations


from sqlglot import tokens
from sqlglot.dialects.dialect import (
    Dialect,
    NormalizationStrategy,
)
from sqlglot.generators.exasol import ExasolGenerator
from sqlglot.parsers.exasol import DATE_UNITS as DATE_UNITS, ExasolParser
from sqlglot.tokens import TokenType


class Exasol(Dialect):
    # https://docs.exasol.com/db/latest/sql_references/basiclanguageelements.htm#SQLidentifier
    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
    # htt
…[1094 chars elided]…
     # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/if.htm
            "ENDIF": TokenType.END,
            "LONG VARCHAR": TokenType.TEXT,
            "REGEXP_LIKE": TokenType.RLIKE,
            "SEPARATOR": TokenType.SEPARATOR,
            "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
            "MINUS": TokenType.EXCEPT,
        }
        KEYWORDS.pop("DIV")

    Parser = ExasolParser

    Generator = ExasolGenerator
(eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn \"LOCAL\" sqlglot/parsers sqlglot/generators sqlglot/optimizer | grep -v \"LOCAL_\\|_LOCAL\" ; grep -rn \"LOCAL\\.\" sqlglot | head", "description": "Search LOCAL alias rewrite code"}
[tool_result] sqlglot/parsers/singlestore.py:202:        "FULLTEXT SERVICE METRICS LOCAL": _show_parser("FULLTEXT SERVICE METRICS LOCAL"),
sqlglot/parsers/snowflake.py:380:        TokenType.LOCALTIME: exp.Localtime,
sqlglot/parsers/snowflake.py:381:        TokenType.LOCALTIMESTAMP: exp.Localtimestamp,
sqlglot/parsers/snowflake.py:556:        "LOCALTIMESTAMP": exp.CurrentTimestamp.from_arg_list,
sqlglot/parsers/postgres.py:146:        TokenType.LOCALTIME: exp.Localtime,
sqlglot/parsers/postgres.py:147:        
…[893 chars elided]…
lot/generators/exasol.py:51:            and table_ident.name.upper() == "LOCAL"
sqlglot/generators/exasol.py:61:                        table=exp.to_identifier("LOCAL", quoted=False),
sqlglot/generators/exasol.py:307:        # Exasol supports a fixed default precision of 3 for TIMESTAMP WITH LOCAL TIME ZONE
sqlglot/generators/exasol.py:310:            return "TIMESTAMP WITH LOCAL TIME ZONE"
sqlglot/generators/duckdb.py:1554:        exp.Localtime: unsupported_args("this")(lambda *_: "LOCALTIME"),
[tool_use Bash] {"command": "cat sqlglot/generators/exasol.py | head -120 && sed -n 120,170p sqlglot/parsers/exasol.py", "description": "Read Exasol generator and parser alias code"}
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
…[5248 chars elided]…
(table_ident.args.get("quoted"))
        ):
            column.set("table", None)
        return column

    def _parse_json_extract(self) -> exp.JSONExtract:
        args = self._parse_expressions()
        self._match_r_paren()

        expression = exp.JSONExtract(expressions=args)

        if self._match_texts("EMITS"):
            expression.set("emits", self._parse_schema())

        return expression

    ODBC_DATETIME_LITERALS = {
        "d": exp.Date,
        "ts": exp.Timestamp,
    }
[tool_use Bash] {"command": "grep -rn \"_add_local_prefix_for_aliases\" sqlglot tests | head && <work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in ['SELECT 1 AS idField FROM t GROUP BY idfield', 'SELECT 1 AS idField FROM t WHERE idfield > 1', 'SELECT 1 AS idField FROM t HAVING IDFIELD > 1', 'SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield', 'SELECT 1 AS \\\"IDFIELD\\\" FROM t GROUP BY idfield']:\n    print(sqlglot.transpile(q, read='mysql', write='exasol'))\n\"", "description": "Locate rewrite caller and reproduce the bug"}
[tool_result] sqlglot/generators/exasol.py:38:def _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:
sqlglot/generators/exasol.py:396:                _add_local_prefix_for_aliases,
['SELECT 1 AS idField FROM t GROUP BY idfield']
['SELECT 1 AS idField FROM t WHERE idfield > 1']
['SELECT 1 AS idField FROM t HAVING IDFIELD > 1']
['SELECT 1 AS "idField" FROM t GROUP BY idfield']
['SELECT 1 AS "IDFIELD" FROM t GROUP BY idfield']
[tool_use Bash] {"command": "sed -n 385,405p sqlglot/generators/exasol.py && grep -rn \"LOCAL\" tests/dialects/test_exasol.py | head -30", "description": "Read call site and existing LOCAL tests"}
[tool_result]         # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/hash_sha256.htm
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/hash_sha512.htm
        exp.SHA2: _sha2_sql,
        exp.MD5: rename_func("HASH_MD5"),
        # https://docs.exasol.com/db/latest/sql_references/functions/alphabeticallistfunctions/hashtype_md5.htm
        exp.MD5Digest: rename_func("HASHTYPE_MD5"),
        # https://docs.exasol.com/db/latest
…[2690 chars elided]…
"SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year",
tests/dialects/test_exasol.py:1006:            write={"exasol": "SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year"},
tests/dialects/test_exasol.py:1014:        # HAVING alias -> LOCAL prefix
tests/dialects/test_exasol.py:1016:            "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1",
tests/dialects/test_exasol.py:1018:            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
[assistant] Reproduced: the mismatched-case alias `idfield` against `idField` is left unprefixed. The rewrite in `_add_local_prefix_for_aliases` compares raw names, so I'll key both sides by Exasol's identifier rule (unquoted folds to upper case, quoted is exact) and emit the alias's own name and quoting.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n     
…[522 chars elided]…
ql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, exp.Identifier] = {\n            _exasol_identifier_key(alias): alias\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "        def prefix_local(node: exp.Expr, visible_aliases: dict[str, bool]) -> exp.Expr:\n            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n    
…[1735 chars elided]…
      for sel in expression.selects:\n            if isinstance(sel, exp.Alias):\n                inner = sel.this.transform(lambda node: prefix_local(node, seen_aliases))\n                sel.set(\"this\", inner)\n\n                if alias_node := sel.args.get(\"alias\"):\n                    seen_aliases[_exasol_identifier_key(alias_node)] = alias_node\n                new_selects.append(sel)"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now the reproduction cases, the Exasol test file, and then the full suite.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -I -c \"\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nfor q in ['SELECT 1 AS idField FROM t GROUP BY idfield', 'SELECT 1 AS idField FROM t WHERE idfield > 1', 'SELECT 1 AS idField FROM t HAVING IDFIELD > 1', 'SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield', 'SELECT 1 AS \\\"IDFIELD\\\" FROM t GROUP
…[22 chars elided]…
1 AS idField, idfield + 1 AS b FROM t', 'SELECT 1 AS \\\"idField\\\" FROM t GROUP BY \\\"idfield\\\"']:\n    print(sqlglot.transpile(q, read='mysql', write='exasol'))\n\" && <work>/env-sqlglot/bin/python -I -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -5", "description": "Run repro cases and Exasol dialect tests"}
[tool_result] ['SELECT 1 AS idField FROM t GROUP BY LOCAL.idField']
['SELECT 1 AS idField FROM t WHERE LOCAL.idField > 1']
['SELECT 1 AS idField FROM t HAVING LOCAL.idField > 1']
['SELECT 1 AS "idField" FROM t GROUP BY idfield']
['SELECT 1 AS "IDFIELD" FROM t GROUP BY LOCAL."IDFIELD"']
['SELECT 1 AS idField, LOCAL.idField + 1 AS b FROM t']
['SELECT 1 AS "idField" FROM t GROUP BY \'idfield\'']
...................                                                       [100%]
19 passed, 575 subtests passed in 0.21s
[assistant] The four reported shapes now rewrite correctly, and the quoted-identifier cases still behave per Exasol's rules. Running the full suite with the project's command:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8", "description": "Run full test suite"}
[tool_result] ................................................................................................. [ 73%]
......................................................................................................... [ 82%]
........................................ [ 86%]
................................................................ [ 92%]
.................................................... [ 96%]
....... [ 97%]
...........................                                   [100%]
1107 passed, 18011 subtests passed in 46.27s
[assistant] All 1107 pass. Next I'll add regression tests next to the existing alias-rewrite tests.
[tool_use Bash] {"command": "sed -n 990,1030p tests/dialects/test_exasol.py", "description": "Read existing alias rewrite tests"}
[tool_result]             write={
                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
            },
        )

    def test_group_by_alias_local(self):
        # GROUP BY bare alias -> LOCAL prefix
        self.validate_all(
            "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt",
            read={"mysql": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY cnt"},
            write={"exasol": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt
…[466 chars elided]…
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
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "        # HAVING alias -> LOCAL prefix\n        self.validate_all(\n            \"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1\",\n            read={\"mysql\": \"SELECT COUNT(*) AS cnt FROM t HAVING cn
…[1141 chars elided]…
case reference\n        self.validate_all(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY idfield',\n            write={\"exasol\": 'SELECT 1 AS \"idField\" FROM t GROUP BY idfield'},\n        )\n        self.validate_all(\n            'SELECT 1 AS \"IDFIELD\" FROM t GROUP BY idfield',\n            write={\"exasol\": 'SELECT 1 AS \"IDFIELD\" FROM t GROUP BY LOCAL.\"IDFIELD\"'},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-191320-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -3; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -1; ($PY -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py && $PY -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py) 2>&1 | tail -4; git status --short", "description": "Run tests, lint and format checks, and git status"}
[tool_result] ...................                                                 [100%]
19 passed, 581 subtests passed in 0.14s
1107 passed, 18017 subtests passed in 47.31s
All checks passed!
2 files already formatted
 M sqlglot/generators/exasol.py
 M tests/dialects/test_exasol.py
[assistant] Tests, ruff lint, and format all pass. Checking types as well, since the pre-commit config runs mypy:
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m mypy sqlglot/generators/exasol.py 2>&1 | tail -3; git diff", "description": "Run mypy on changed file and show diff"}
[tool_result] Success: no issues found in 1 source file
sqlglot/generators/exasol.py  | 22 +++++++++++++---------
 tests/dialects/test_exasol.py | 20 ++++++++++++++++++++
 2 files changed, 33 insertions(+), 9 deletions(-)

--- Changes ---

sqlglot/generators/exasol.py
  @@ -34,11 +34,16 @@ def _date_diff_sql(self: ExasolGenerator, expression: exp.DateDiff | exp.TsOrDsD
  +# Unquoted identifiers are folded to upper case, quoted identifiers are case-sensitive
  +def _exasol_identifier_key(identifier: exp.Expr) 
…[3095 chars elided]…
        )
  +        # Quoted aliases are case-sensitive -> no LOCAL prefix on a different-case reference
  +        self.validate_all(
  +            'SELECT 1 AS "idField" FROM t GROUP BY idfield',
  +            write={"exasol": 'SELECT 1 AS "idField" FROM t GROUP BY idfield'},
  +        )
  +        self.validate_all(
  +            'SELECT 1 AS "IDFIELD" FROM t GROUP BY idfield',
  +            write={"exasol": 'SELECT 1 AS "IDFIELD" FROM t GROUP BY LOCAL."IDFIELD"'},
  +        )
  +20 -0
[assistant] Unquoted alias references now match case-insensitively, so `SELECT 1 AS idField FROM t GROUP BY idfield` transpiles to Exasol as `GROUP BY LOCAL.idField`. The same applies to `WHERE` and `HAVING`. The full suite passes (1107 tests), and ruff, format and mypy are clean. I haven't committed.

The fix is in `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py`. Alias names are now compared using Exasol's identifier rule: unquoted names are folded to upper case, quoted names are compared exactly.

Two behaviours to be aware of:

- **Output spelling:** the rewritten reference uses the a
…[47 chars elided]…
s. So `idfield` becomes `LOCAL.idField`. This is semantically identical in Exasol, but it differs from the input text. Say if you'd rather keep the reference's spelling.
- **Quoted aliases stay case-sensitive:** `"idField"` does not match `idfield`, which is correct under Exasol's rules. `"IDFIELD"` does match an unquoted `idfield`, and it is emitted as `LOCAL."IDFIELD"`.

I added regression tests to `tests/dialects/test_exasol.py` next to the existing alias-rewrite tests. They cover unquoted GROUP BY and WHERE cases, and the quoted-alias cases in both directions. Existing tests are unchanged.
