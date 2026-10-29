# trajectory base-1

final message:
Postgres now supports the PostGIS 3D distance operator `<<->>`. `SELECT a <<->> b FROM t` tokenizes, parses as a binary operator, and generates back as `<<->>`. The full test suite passes (1108 tests), and ruff lint and format are clean.

Changes:
- **`sqlglot/tokenizer_core.py`**: new token type `LR_ARROW_3D`, next to `LR_ARROW`.
- **`sqlglot/dialects/postgres.py`**: `"<<->>"` maps to `LR_ARROW_3D` in the Postgres tokenizer. The operator is Postgres-only, so I didn't add it to the base tokenizer.
- **`sqlglot/expressions/core.py`**: new binary expression `Distance3D`, alongside `Distance`.
- **`sqlglot/parser.py`**: `LR_ARROW_3D` maps to `exp.Distance3D` in the factor-level operators, next to `<->`.
- **`sqlglot/generator.py`**: `distance3d_sql` emits `<<->>`.
- **`tests/dialects/test_postgres.py`**: two identity round-trips, one in a select list and one in an `ORDER BY ... LIMIT`.

I checked that `<->` still parses to `Distance` and generates `<->`, and that `<<` still parses as a bitwise shift.

I did not commit anything.

## events
[tool_use Bash] {"command": "rg -n \"<->|<<|DHASH|LR_ARROW|PIPE_SLASH|ARROW\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/parser.py sqlglot/generator.py sqlglot/dialects/dialect.py | head -60; rg -n \"<->\" tests/dialects/test_postgres.py | head", "description": "Search for existing distance/shift operator handling"}
[tool_result] 24 matches in 4 files:

sqlglot/dialects/postgres.py:80:"|/": TokenType.PIPE_SLASH,
sqlglot/dialects/postgres.py:81:"||/": TokenType.DPIPE_SLASH,
sqlglot/generator.py:3895:return self.binary(expression, "<<")
sqlglot/generator.py:4223:return self.binary(expression, "<->")
sqlglot/parser.py:918:TokenType.LR_ARROW: exp.Distance,
sqlglot/parser.py:989:TokenType.ARROW: lambda self, expressions: self.expression(
sqlglot/parser.py:998:TokenType.FARROW: lambda self, expressions: self.expression(
sqlglo
…[969 chars elided]…
t/tokens.py:234:"->>": TokenType.DARROW,
sqlglot/tokens.py:235:"=>": TokenType.FARROW,
sqlglot/tokens.py:236:"#>": TokenType.HASH_ARROW,
sqlglot/tokens.py:237:"#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:238:"<->": TokenType.LR_ARROW,
2 matches in 1 files:

tests/dialects/test_postgres.py:370:...ly) v1, LATERAL VERTICES(p2.poly) v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
tests/dialects/test_postgres.py:371:... v1, LATERAL VERTICES(p2.poly) AS v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
[tool_use Bash] {"command": "rg -n \"LR_ARROW|\\\"<<\\\"|BITWISE_LEFT|DHASH_ARROW\" sqlglot/ tests/ | head -30; sed -n 225,245p sqlglot/tokens.py; sed -n 4215,4230p sqlglot/generator.py; rg -n \"class Distance\" -A3 sqlglot/expressions.py; sed -n 910,922p sqlglot/parser.py; sed -n 365,375p tests/dialects/test_postgres.py; git log --oneline -3 -- sqlglot/dialects/postgres.py", "description": "Inspect distance token/expression wiring"}
[tool_result] 9 matches in 6 files:

sqlglot/generator.py:3895:return self.binary(expression, "<<")
sqlglot/generators/duckdb.py:1189:operator = "<<" if isinstance(expression, exp.BitwiseLeftShift) else ">>"
sqlglot/parser.py:918:TokenType.LR_ARROW: exp.Distance,
sqlglot/parser.py:1032:TokenType.DHASH_ARROW: lambda self, this, path: self.expression(
sqlglot/parsers/singlestore.py:188:TokenType.DHASH_ARROW,
sqlglot/tokenizer_core.py:63:DHASH_ARROW = auto()
sqlglot/tokenizer_core.py:64:LR_ARROW = auto()
sqlglot
…[2362 chars elided]…
AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) AS v1, LATERAL VERTICES(p2.poly) AS v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
        )
        self.validate_identity(
            "SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL",
            "SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE NOT deleted IS NULL",
ae58fd10c feat(postgres)!: parse CREATE TYPE statements (#7616)
f3871121d fix(parser): robust CONCAT_WS (#7544)
8ae227476 Revert `TO_CHAR` changes
[tool_use Bash] {"command": "rg -n \"class Distance|class BitwiseLeftShift\" -A3 sqlglot/expressions/; rg -n \"BitwiseLeftShift|\\\"<<\\\"|LT_LT|DLT\" sqlglot/tokens.py sqlglot/tokenizer_core.py sqlglot/parser.py | head; rg -n \"LR_ARROW|DHASH_ARROW\" -r . --include=*.py --include=*.pyi --include=*.md -l . | head; ls sqlglot/tokenizer_core* ; git status --short | head", "description": "Locate Distance expression and shift tokens"}
[tool_result] grep: sqlglot/expressions/: Is a directory
1 matches in 1 files:

sqlglot/parser.py:6004:exp.BitwiseLeftShift(this=this, expression=self._parse_term())
(eval):1: no matches found: --include=*.py
sqlglot/tokenizer_core.py  34.4K
ok
[tool_use Bash] {"command": "rg -n \"class Distance\\b|class Distance\\(|class BitwiseLeftShift\" -A4 sqlglot/expressions/ ; rg -n \"LR_ARROW|DHASH_ARROW\" sqlglot/ docs 2>/dev/null; rg -n \"\\\"<<\\\"|'<<'|<<\" sqlglot/tokens.py sqlglot/tokenizer_core.py | head; sed -n 40,75p sqlglot/tokenizer_core.py", "description": "Find Distance class and tokenizer enum"}
[tool_result] grep: parentheses not balanced
7 matches in 4 files:

sqlglot/parser.py:918:TokenType.LR_ARROW: exp.Distance,
sqlglot/parser.py:1032:TokenType.DHASH_ARROW: lambda self, this, path: self.expression(
sqlglot/parsers/singlestore.py:188:TokenType.DHASH_ARROW,
sqlglot/tokenizer_core.py:63:DHASH_ARROW = auto()
sqlglot/tokenizer_core.py:64:LR_ARROW = auto()
sqlglot/tokens.py:237:"#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:238:"<->": TokenType.LR_ARROW,
0 matches for '"<<"|'<<'|<<'
    NOT = auto()

…[223 chars elided]…
 = auto()
    PIPE_SLASH = auto()
    DPIPE_SLASH = auto()
    CARET = auto()
    CARET_AT = auto()
    TILDE = auto()
    ARROW = auto()
    DARROW = auto()
    FARROW = auto()
    HASH = auto()
    HASH_ARROW = auto()
    DHASH_ARROW = auto()
    LR_ARROW = auto()
    DAT = auto()
    LT_AT = auto()
    AT_GT = auto()
    DOLLAR = auto()
    PARAMETER = auto()
    SESSION = auto()
    SESSION_PARAMETER = auto()
    SESSION_USER = auto()
    DAMP = auto()
    AMP_LT = auto()
    AMP_GT = auto()
[tool_use Bash] {"command": "rg -n \"class Distance\" sqlglot/ ; rg -n \"DHASH_ARROW|LR_ARROW\" sqlglot/tokenizer_core.py; rg -n \"LR_ARROW|<->\" sqlglot/dialects/*.py sqlglot/parsers/*.py sqlglot/generators/*.py | head; grep -n \"<<\" sqlglot/tokens.py | head", "description": "Locate Distance class and << token handling"}
[tool_result] 1 matches in 1 files:

sqlglot/expressions/core.py:2117:class Distance(Expression, Binary):
2 matches in 1 files:

sqlglot/tokenizer_core.py:63:DHASH_ARROW = auto()
sqlglot/tokenizer_core.py:64:LR_ARROW = auto()
0 matches for 'LR_ARROW|<->'
0 matches for '<<'
[tool_use Bash] {"command": "sed -n 2110,2125p sqlglot/expressions/core.py; sed -n 5998,6006p sqlglot/parser.py; rg -n \"LT_LT|GT_GT\" sqlglot/tokenizer_core.py sqlglot/tokens.py | head -5; rg -n \"def _scan_keywords|KEYWORD_TRIE\" sqlglot/tokens.py | head -3; sed -n 1,30p sqlglot/dialects/postgres.py | head -0; sed -n 70,90p sqlglot/dialects/postgres.py", "description": "Inspect Distance class and shift token wiring"}
[tool_result]     pass


class PropertyEQ(Expression, Binary):
    pass


class Distance(Expression, Binary):
    pass


class Escape(Expression, Binary):
    pass


class Glob(Expression, Binary, Predicate):
            elif self._match(TokenType.DQMARK):
                this = self.expression(
                    exp.Coalesce(this=this, expressions=ensure_list(self._parse_term()))
                )
            elif self._match_pair(TokenType.LT, TokenType.LT):
                this = self.expression(
       
…[542 chars elided]…
ype.QMARK_PIPE,
            "#-": TokenType.HASH_DASH,
            "|/": TokenType.PIPE_SLASH,
            "||/": TokenType.DPIPE_SLASH,
            "BEGIN": TokenType.BEGIN,
            "BIGSERIAL": TokenType.BIGSERIAL,
            "CSTRING": TokenType.PSEUDO_TYPE,
            "DECLARE": TokenType.COMMAND,
            "DO": TokenType.COMMAND,
            "EXEC": TokenType.COMMAND,
            "HSTORE": TokenType.HSTORE,
            "INT8": TokenType.BIGINT,
            "MONEY": TokenType.MONEY,
[tool_use Bash] {"command": "ls sqlglot/parsers/ sqlglot/generators/ | head -80; rg -n \"FACTOR\" sqlglot/parser.py sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py; rg -n \"class Tokenizer|class Parser|class Generator\" sqlglot/dialects/postgres.py; rg -n \"distance_sql|binary\\(expression, \\\"<\" sqlglot/generator.py sqlglot/generators/postgres.py", "description": "Survey postgres parser/generator layout"}
[tool_result] __init__.py  0B
athena.py  5.8K
bigquery.py  24.4K
clickhouse.py  26.8K
databricks.py  3.8K
doris.py  14.3K
dremio.py  3.3K
drill.py  4.2K
druid.py  892B
duckdb.py  175.8K
dune.py  323B
exasol.py  29.2K
fabric.py  6.5K
hive.py  21.0K
materialize.py  2.0K
mysql.py  26.5K
oracle.py  6.4K
postgres.py  21.7K
presto.py  25.2K
prql.py  192B
python.py  3.9K
redshift.py  11.7K
risingwave.py  1.1K
singlestore.py  42.3K
snowflake.py  46.6K
solr.py  192B
spark.py  7.8K
spark2.py  9.6K
sqlite.py  11.9K
star
…[794 chars elided]…
py:6042:klass = self.FACTOR[self._prev.token_type]
1 matches in 1 files:

61:0:
6 matches in 1 files:

sqlglot/generator.py:3895:return self.binary(expression, "<<")
sqlglot/generator.py:4222:def distance_sql(self, expression: exp.Distance) -> str:
sqlglot/generator.py:4223:return self.binary(expression, "<->")
sqlglot/generator.py:4323:return self.binary(expression, "<")
sqlglot/generator.py:4326:return self.binary(expression, "<=")
sqlglot/generator.py:4335:return self.binary(expression, "<>")
[tool_use Bash] {"command": "rg -n \"Distance\\b\" sqlglot/ | grep -v \"^sqlglot/expressions/core.py:2117\"; rg -n \"LR_ARROW\" -B2 -A2 sqlglot/tokenizer_core.py; rg -n \"^class Tokenizer|^class Parser|^class Generator\" sqlglot/dialects/postgres.py; rg -n \"tokenizer_core|_hidden|SKIP\" Makefile setup.py 2>/dev/null | head -5", "description": "Find all Distance references and token enum context"}
[tool_result] 33 matches in 18 files:

sqlglot/expressions/array.py:363:class StDistance(Expression, Func):
sqlglot/expressions/math.py:98:class CosineDistance(Expression, Func):
sqlglot/expressions/math.py:106:class EuclideanDistance(Expression, Func):
sqlglot/expressions/math.py:119:class ManhattanDistance(Expression, Func):
sqlglot/generator.py:4222:def distance_sql(self, expression: exp.Distance) -> str:
sqlglot/generators/clickhouse.py:297:exp.CosineDistance: rename_func("cosineDistance"),
sqlglot/genera
…[1879 chars elided]…
e,
sqlglot/typing/snowflake.py:364:exp.CosineDistance,
sqlglot/typing/snowflake.py:368:exp.EuclideanDistance,
sqlglot/typing/snowflake.py:369:exp.ManhattanDistance,
62-    HASH_ARROW = auto()
63-    DHASH_ARROW = auto()
64:    LR_ARROW = auto()
65-    DAT = auto()
66-    LT_AT = auto()
0 matches for '^class Tokenizer|^class Parser|^class Generator'
2 matches in 1 files:

Makefile:85:trap '$(MAKE) showc' EXIT; SKIP_INTEGRATION=1 python -m unittest
Makefile:91:SKIP_INTEGRATION=1 python -m unittest
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/tokenizer_core.py", "old_string": "    LR_ARROW = auto()\n", "new_string": "    LR_ARROW = auto()\n    LR_ARROW_3D = auto()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/expressions/core.py", "old_string": "class Distance(Expression, Binary):\n    pass\n", "new_string": "class Distance(Expression, Binary):\n    pass\n\n\nclass Distance3D(Expression, Binary):\n    pass\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/expressions/core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/parser.py", "old_string": "        TokenType.LR_ARROW: exp.Distance,\n", "new_string": "        TokenType.LR_ARROW: exp.Distance,\n        TokenType.LR_ARROW_3D: exp.Distance3D,\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/generator.py", "old_string": "        return self.binary(expression, \"<->\")\n", "new_string": "        return self.binary(expression, \"<->\")\n\n    def distance3d_sql(self, expression: exp.Distance3D) -> str:\n        return self.binary(expression, \"<<->>\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/generator.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"|/\": TokenType.PIPE_SLASH,\n", "new_string": "            \"|/\": TokenType.PIPE_SLASH,\n            \"<<->>\": TokenType.LR_ARROW_3D,\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[assistant] Now a test next to the existing `<->` case, then a check of the behaviour.
[tool_use Bash] {"command": "rg -n \"def test_postgres\" tests/dialects/test_postgres.py | head -3 && sed -n 367,368p tests/dialects/test_postgres.py", "description": "Locate test insertion point in postgres tests"}
[tool_result] 2 matches in 2 files:

10:0:
            "SELECT m.name FROM manufacturers AS m LEFT JOIN LATERAL GET_PRODUCT_NAMES(m.id) AS pname ON TRUE WHERE pname IS NULL",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py", "old_string": "            \"SELECT m.name FROM manufacturers AS m LEFT JOIN LATERAL GET_PRODUCT_NAMES(m.id) pname ON TRUE WHERE pname IS NULL\",\n            \"SELECT m.name FROM manufacturers AS m LEFT JOIN LATERAL GET
…[112 chars elided]…
m.name FROM manufacturers AS m LEFT JOIN LATERAL GET_PRODUCT_NAMES(m.id) pname ON TRUE WHERE pname IS NULL\",\n            \"SELECT m.name FROM manufacturers AS m LEFT JOIN LATERAL GET_PRODUCT_NAMES(m.id) AS pname ON TRUE WHERE pname IS NULL\",\n        )\n        self.validate_identity(\"SELECT a <<->> b FROM t\")\n        self.validate_identity(\"SELECT * FROM t ORDER BY a <<->> b LIMIT 1\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-6e430de19896/20261029-192554-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne=sqlglot.parse_one('SELECT a <<->> b FROM t', read='postgres')\nprint(repr(e.selects[0]), e.sql('postgres'))\nprint(sqlglot.transpile('SELECT a <<->> b FROM t', read='postgres', write='duckdb'))\nprint(sqlglot.transpile('SELECT a <-> b FROM t', read='postgres', write='postgres'))\nprint(sqlglot.transpile('SELECT a << b, a <-> b FROM t', read='postgres', write='postgres'))\n\"; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5", "description": "Verify parse/generate and run full test suite"}
[tool_result] Distance3D(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Column(
    this=Identifier(this=b, quoted=False))) SELECT a <<->> b FROM t
['SELECT a <<->> b FROM t']
['SELECT a <-> b FROM t']
['SELECT a << b, a <-> b FROM t']
........................................................................ [ 76%]
............................................. [ 80%]
.................................................................................................................................................... [ 93%]
....................................................................       [100%]
1108 passed, 18038 subtests passed in 46.28s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/ruff check sqlglot tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -5; git status --short", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
176 files already formatted
 M sqlglot/dialects/postgres.py
 M sqlglot/expressions/core.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_postgres.py
[assistant] Postgres now supports the PostGIS 3D distance operator `<<->>`. `SELECT a <<->> b FROM t` tokenizes, parses as a binary operator, and generates back as `<<->>`. The full test suite passes (1108 tests), and ruff lint and format are clean.

Changes:
- **`sqlglot/tokenizer_core.py`**: new token type `LR_ARROW_3D`, next to `LR_ARROW`.
- **`sqlglot/dialects/postgres.py`**: `"<<->>"` maps to `LR_ARROW_3D` in the Postgres tokenizer. The operator is Postgres-only, so I didn't add it to the base tokenizer.
- **`sqlglot/expressions/core.py`**: new binary expression `Distance3D`, alongside `Distance`.
- **`sqlglot/parser.py`**: `LR_ARROW_3D` maps to `exp.Distance3D` in the factor-level operators, next to `<->`.
- **`sqlglot/generator.py`**: `distance3d_sql` emits `<<->>`.
- **`tests/dialects/test_postgres.py`**: two identity round-trips, one in a select list and one in an `ORDER BY ... LIMIT`.

I checked that `<->` still parses to `Distance` and generates `<->`, and that `<<` still parses as a bitwise shift.

I did not commit anything.
