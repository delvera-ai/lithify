# trajectory base-1

final message:
Postgres now tokenizes `<<->>` as a single operator, parses it as a binary expression, and generates it back as `<<->>`. The full test suite passes (1108 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/tokenizer_core.py`**: new `TokenType.LR_ARROW_3D`.
- **`sqlglot/expressions/core.py`**: new `Distance3D(Expression, Binary)`, next to `Distance`.
- **`sqlglot/dialects/postgres.py`**: `"<<->>"` added to the Postgres tokenizer keywords only.
- **`sqlglot/parsers/postgres.py`**: `FACTOR` maps `LR_ARROW_3D` to `exp.Distance3D`, at the same precedence as `<->`.
- **`sqlglot/generators/postgres.py`**: `distance3d_sql` emits `<<->>`.
- **`tests/dialects/test_postgres.py`**: round-trip tests for `SELECT a <<->> b FROM t` and an `ORDER BY geom <<->> other_geom` case.

Choices I made:
- I scoped the token to Postgres rather than the base tokenizer, as the request asked. Other dialects still tokenize `<<->>` as before.
- I used a new expression class rather than reusing `exp.Distance`, so that the 2D `<->` and 3D `<<->>` operators stay distinct and each generates its own symbol.
- I did not commit anything.

## events
[tool_use Bash] {"command": "grep -n \"<->\\|<<\\|>>\\|L2_DISTANCE\\|DISTANCE\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/generator.py sqlglot/parser.py | head -80; grep -rn \"<<->\" sqlglot tests | head", "description": "Search for operator token handling and existing distance ops"}
[tool_result] sqlglot/tokens.py:234:        "->>": TokenType.DARROW,
sqlglot/tokens.py:237:        "#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:238:        "<->": TokenType.LR_ARROW,
sqlglot/generator.py:3895:        return self.binary(expression, "<<")
sqlglot/generator.py:3904:        return self.binary(expression, ">>")
sqlglot/generator.py:4223:        return self.binary(expression, "<->")
sqlglot/parser.py:1782:    # Whether the -> and ->> operators expect documents of type JSON (e.g. Postgres)
sqlglot/parser.py:6450:            # Takes care of special cases like `STRUCT<list ARRAY<...>>` where the identifier is also a
[tool_use Bash] {"command": "grep -rn \"LR_ARROW\\|EuclideanDistance\\|class .*Distance\" sqlglot/ | head -30; sed -n 4215,4230p sqlglot/generator.py; grep -n \"LR_ARROW\\|<->\" tests/dialects/*.py | head", "description": "Find LR_ARROW usage and distance expression classes"}
[tool_result] sqlglot/tokens.py:238:        "<->": TokenType.LR_ARROW,
sqlglot/tokenizer_core.py:64:    LR_ARROW = auto()
sqlglot/parsers/clickhouse.py:286:        "L2Distance": exp.EuclideanDistance.from_arg_list,
sqlglot/parser.py:918:        TokenType.LR_ARROW: exp.Distance,
sqlglot/parsers/doris.py:35:        "L2_DISTANCE": exp.EuclideanDistance.from_arg_list,
sqlglot/parsers/oracle.py:30:        "L2_DISTANCE": exp.EuclideanDistance.from_arg_list,
sqlglot/parsers/snowflake.py:700:        "VECTOR_L2_DISTAN
…[1777 chars elided]…
         "SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) v1, LATERAL VERTICES(p2.poly) v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
tests/dialects/test_postgres.py:371:            "SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) AS v1, LATERAL VERTICES(p2.poly) AS v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
tests/dialects/test_tsql.py:2385:            with self.subTest("Testing PARSENAME <-> SPLIT_PART"):
[tool_use Bash] {"command": "sed -n 2110,2125p sqlglot/expressions/core.py; sed -n 900,935p sqlglot/parser.py; grep -n \"class Tokenizer\\|KEYWORDS\\|SINGLE_TOKENS\\|TokenType\\.\\(DHASH\\|DARROW\\)\" sqlglot/dialects/postgres.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py | head -30; sed -n 225,245p sqlglot/tokens.py; sed -n 55,70p sqlglot/tokenizer_core.py; grep -n \"Distance\" sqlglot/generators/postgres.py sqlglot/generator.py | head", "description": "Inspect Distance class, parser ops, and postgres tokenizer"}
[tool_result]     pass


class PropertyEQ(Expression, Binary):
    pass


class Distance(Expression, Binary):
    pass


class Escape(Expression, Binary):
    pass


class Glob(Expression, Binary, Predicate):
        TokenType.LTE: exp.LTE,
    }

    BITWISE: t.ClassVar = {
        TokenType.AMP: exp.BitwiseAnd,
        TokenType.CARET: exp.BitwiseXor,
        TokenType.PIPE: exp.BitwiseOr,
    }

    TERM: t.ClassVar = {
        TokenType.DASH: exp.Sub,
        TokenType.PLUS: exp.Add,
        TokenType.MOD
…[1779 chars elided]…
": TokenType.ILIKE,
        "~*": TokenType.IRLIKE,
        "-|-": TokenType.ADJACENT,
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
sqlglot/generator.py:4222:    def distance_sql(self, expression: exp.Distance) -> str:
[tool_use Bash] {"command": "sed -n 59,130p sqlglot/dialects/postgres.py; grep -n \"FACTOR\\|class Parser\\|RANGE_PARSERS\\|^from\\|^import\" sqlglot/parsers/postgres.py | head -20; grep -rn \"FACTOR = \" sqlglot/parsers sqlglot/dialects | head -5; grep -n \"class Generator\\|TRANSFORMS = {\" sqlglot/generators/postgres.py | head -3; grep -n \"TokenType\" sqlglot/tokens.py | head -3; ls tests/dialects | grep postg", "description": "Read postgres dialect tokenizer and parser override patterns"}
[tool_result]     }

    class Tokenizer(tokens.Tokenizer):
        BIT_STRINGS = [("b'", "'"), ("B'", "'")]
        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
        BYTE_STRINGS = [("e'", "'"), ("E'", "'")]
        BYTE_STRING_ESCAPES = ["'", "\\"]
        HEREDOC_STRINGS = ["$"]

        HEREDOC_TAG_IS_IDENTIFIER = True
        HEREDOC_STRING_ALTERNATIVE = TokenType.PARAMETER

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS,
            "~": TokenType.RLIKE,
            "@@": TokenType.DAT,
   
…[2225 chars elided]…
sqlglot.dialects.dialect import (
13:from sqlglot.helper import is_int, seq_get
14:from sqlglot.parser import binary_range_parser
15:from sqlglot.tokens import TokenType
171:    RANGE_PARSERS = {
172:        **parser.Parser.RANGE_PARSERS,
sqlglot/parsers/databricks.py:33:    FACTOR = {
285:    TRANSFORMS = {
8:from sqlglot.tokenizer_core import Token, TokenizerCore, TokenType
51:    token_type: TokenType, arr: list[str | tuple[str, str]]
52:) -> dict[str, tuple[str, TokenType]]:
test_postgres.py
[tool_use Bash] {"command": "grep -n \"^class PostgresParser\\|^    [A-Z_]* = {\\|^    [A-Z_]*: t.ClassVar\" sqlglot/parsers/postgres.py | head -20; grep -n \"class PostgresGenerator\" -A3 sqlglot/generators/postgres.py; grep -n \"def distance_sql\\|def binary\" sqlglot/generators/postgres.py; grep -n \"\\\"<<\\\"\\|LT_LT\\|LSHIFT\" sqlglot/tokens.py | head -3; grep -n \"__all__\" sqlglot/expressions/*.py | head -3; grep -n \"^from\\|^import\" sqlglot/expressions/core.py | head; ls tests/dialects/test_postgres.py && grep -n \"<->\" -B3 -A3 tests/dialects/test_postgres.py | head -20", "description": "Check postgres parser/generator structure and related tokens"}
[tool_result] 86:class PostgresParser(parser.Parser):
89:    PROPERTY_PARSERS = {
94:    PLACEHOLDER_PARSERS = {
100:    FUNCTIONS = {
139:    NO_PAREN_FUNCTION_PARSERS = {
144:    NO_PAREN_FUNCTIONS = {
153:    FUNCTION_PARSERS = {
162:    BITWISE = {
167:    EXPONENT = {
171:    RANGE_PARSERS = {
179:    STATEMENT_PARSERS = {
184:    UNARY_PARSERS = {
192:    COLUMN_OPERATORS = {
206:    ARG_MODE_TOKENS: t.ClassVar = {TokenType.IN, TokenType.OUT, TokenType.INOUT, TokenType.VARIADIC}
225:class PostgresGenera
…[570 chars elided]…
SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) v1, LATERAL VERTICES(p2.poly) v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
371:            "SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) AS v1, LATERAL VERTICES(p2.poly) AS v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
372-        )
373-        self.validate_identity(
374-            "SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL",
[assistant] I have what I need. Plan: a new token type, a `Distance3D` binary expression, the Postgres-only tokenizer keyword, a Postgres `FACTOR` mapping, and an auto-discovered `distance3d_sql` generator method.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/tokenizer_core.py", "old_string": "    LR_ARROW = auto()\n", "new_string": "    LR_ARROW = auto()\n    LR_ARROW_3D = auto()\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/expressions/core.py", "old_string": "class Distance(Expression, Binary):\n    pass\n", "new_string": "class Distance(Expression, Binary):\n    pass\n\n\nclass Distance3D(Expression, Binary):\n    pass\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/expressions/core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"~\": TokenType.RLIKE,\n", "new_string": "            \"~\": TokenType.RLIKE,\n            \"<<->>\": TokenType.LR_ARROW_3D,\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[assistant] Now the parser and generator. Let me check the surrounding Postgres parser and generator code before editing.
[tool_use Bash] {"command": "sed -n 160,180p sqlglot/parsers/postgres.py; sed -n 225,240p sqlglot/generators/postgres.py; grep -n \"    def .*_sql\" sqlglot/generators/postgres.py | head -5", "description": "Read postgres parser and generator sections"}
[tool_result]     }

    BITWISE = {
        **parser.Parser.BITWISE,
        TokenType.HASH: exp.BitwiseXor,
    }

    EXPONENT = {
        TokenType.CARET: exp.Pow,
    }

    RANGE_PARSERS = {
        **parser.Parser.RANGE_PARSERS,
        TokenType.DAMP: binary_range_parser(exp.ArrayOverlaps),
        TokenType.DAT: lambda self, this: self.expression(
            exp.MatchAgainst(this=self._parse_bitwise(), expressions=[this])
        ),
    }

    STATEMENT_PARSERS = {
        **parser.Parser.STATEMENT_
…[384 chars elided]…
 False
    TABLE_HINTS = False
    QUERY_HINTS = False
    NVL2_SUPPORTED = False
    PARAMETER_TOKEN = "$"
264:    def lateral_sql(self, expression: exp.Lateral) -> str:
401:    def schemacommentproperty_sql(self, expression: exp.SchemaCommentProperty) -> str:
405:    def commentcolumnconstraint_sql(self, expression: exp.CommentColumnConstraint) -> str:
409:    def columndef_sql(self, expression: exp.ColumnDef, sep: str = " ") -> str:
421:    def unnest_sql(self, expression: exp.Unnest) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/parsers/postgres.py", "old_string": "    EXPONENT = {\n        TokenType.CARET: exp.Pow,\n    }\n", "new_string": "    EXPONENT = {\n        TokenType.CARET: exp.Pow,\n    }\n\n    FACTOR = {\n        **parser.Parser.FACTOR,\n        TokenType.LR_ARROW_3D: exp.Distance3D,\n    }\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/parsers/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/generators/postgres.py", "old_string": "    def lateral_sql(self, expression: exp.Lateral) -> str:", "new_string": "    def distance3d_sql(self, expression: exp.Distance3D) -> str:\n        return self.binary(expression, \"<<->>\")\n\n    def lateral_sql(self, expression: exp.Lateral) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/sqlglot/generators/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL\",", "new_string": "        self.validate_identity(\"SELECT a <<->> b FROM t\")\n        self.validate_identity(\n            \"SELECT id FROM t ORDER BY geom <<->> ST_MakePoint(1, 2, 3) LIMIT 1\",\n        )\n        self.validate_identity(\n            \"SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL\","}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Now I'll confirm the parse tree and run the test suite with the project's interpreter.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT a <<->> b FROM t', read='postgres')\nprint(repr(e.selects[0]))\nprint(e.sql('postgres'))\nprint(sqlglot.transpile('SELECT a <<->> b', read='postgres', write='postgres'))\nprint(sqlglot.transpile('SELECT a * b <<->> c', read='postgres', write='postgres'))\n\" && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -5", "description": "Verify parse/generate round trip and run postgres tests"}
[tool_result] Distance3D(
  this=Column(
    this=Identifier(this=a, quoted=False)),
  expression=Column(
    this=Identifier(this=b, quoted=False)))
SELECT a <<->> b FROM t
['SELECT a <<->> b']
['SELECT a * b <<->> c']
E   + SELECT id FROM t ORDER BY geom <<->> ST_POINT(1, 2, 3) LIMIT 1
E   ?                                          ^^^^
=========================== short test summary info ============================
FAILED tests/dialects/test_postgres.py::TestPostgres::test_postgres - Asserti...
1 failed, 24 passed, 187 subtests passed in 0.26s
[assistant] The only failure is my own test: `ST_MakePoint` is normalized to `ST_POINT` by existing Postgres handling. I'll use a plain column in that test instead.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT id FROM t ORDER BY geom <<->> ST_MakePoint(1, 2, 3) LIMIT 1\",\n        )", "new_string": "        self.validate_identity(\"SELECT id FROM t ORDER BY geom <<->> other_geom LIMIT 1\")"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261028-093224-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -2; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -3; (ruff check sqlglot tests/dialects/test_postgres.py && ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -3", "description": "Run postgres tests, full suite, and lint checks"}
[tool_result] .........................                        [100%]
25 passed, 384 subtests passed in 0.16s
.................................................................................................................................................... [ 93%]
....................................................................       [100%]
1108 passed, 18038 subtests passed in 49.23s
All checks passed!
176 files already formatted
[assistant] Postgres now tokenizes `<<->>` as a single operator, parses it as a binary expression, and generates it back as `<<->>`. The full test suite passes (1108 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/tokenizer_core.py`**: new `TokenType.LR_ARROW_3D`.
- **`sqlglot/expressions/core.py`**: new `Distance3D(Expression, Binary)`, next to `Distance`.
- **`sqlglot/dialects/postgres.py`**: `"<<->>"` added to the Postgres tokenizer keywords only.
- **`sqlglot/parsers/postgres.py`**: `FACTOR` maps `LR_ARROW_3D` to `exp.Distance3D`, at the same precedence as `<->`.
- **`sqlglot/generators/postgres.py`**: `distance3d_sql` emits `<<->>`.
- **`tests/dialects/test_postgres.py`**: round-trip tests for `SELECT a <<->> b FROM t` and an `ORDER BY geom <<->> other_geom` case.

Choices I made:
- I scoped the token to Postgres rather than the base tokenizer, as the request asked. Other dialects still tokenize `<<->>` as before.
- I used a new expression class rather than reusing `exp.Distance`, so that the 2D `<->` and 3D `<<->>` operators stay distinct and each generates its own symbol.
- I did not commit anything.
