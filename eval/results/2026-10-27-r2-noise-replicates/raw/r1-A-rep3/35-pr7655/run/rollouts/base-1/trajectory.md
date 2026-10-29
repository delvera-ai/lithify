# trajectory base-1

final message:
The Postgres dialect now handles the PostGIS 3D distance operator `<<->>`: it tokenizes, parses as a binary operator, and generates back as `<<->>`. The full test suite passes (1108 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/tokenizer_core.py`**: new `TokenType.LLR_ARROW`, added at the end of the `LR_ARROW` group.
- **`sqlglot/dialects/postgres.py`**: `"<<->>"` maps to `LLR_ARROW` in the Postgres tokenizer keywords.
- **`sqlglot/expressions/core.py`**: new `exp.Distance3D(Expression, Binary)`, alongside `exp.Distance`.
- **`sqlglot/parser.py`**: `LLR_ARROW` maps to `exp.Distance3D` in the `FACTOR` operator table, the same precedence as `<->`.
- **`sqlglot/generator.py`**: `distance3d_sql` emits `<<->>`, auto-discovered by name.
- **`tests/dialects/test_postgres.py`**: two identity round-trips, `SELECT a <<->> b FROM t` and a `WHERE (a <<->> b) < 10` case.

Choices to review:
- I added a new expression class rather than reusing `exp.Distance` with a flag, because the generator needs to emit a different operator.
- The token is only recognised in the Postgres tokenizer, so other dialects still see `<<` followed by `->>`. The generator method lives in the base class, so `Distance3D` can be rendered in any dialect.
- Existing `<<` (bit shift) and `<->` behaviour is unchanged; I checked `1 << 2` and `1 <<-2` still round-trip.

## events
[tool_use Bash] {"command": "grep -rn \"<->\\|<<\\|DISTANCE\\|LT_AT\\|DHASH\\|ARROW\" sqlglot/tokens.py sqlglot/dialects/postgres.py sqlglot/dialects/dialect.py | head -60; grep -rn \"<<->\\|<->\" tests/ | head"}
[tool_result] sqlglot/dialects/postgres.py:76:            "<@": TokenType.LT_AT,
sqlglot/tokens.py:233:        "->": TokenType.ARROW,
sqlglot/tokens.py:234:        "->>": TokenType.DARROW,
sqlglot/tokens.py:235:        "=>": TokenType.FARROW,
sqlglot/tokens.py:236:        "#>": TokenType.HASH_ARROW,
sqlglot/tokens.py:237:        "#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py:238:        "<->": TokenType.LR_ARROW,
tests/dialects/test_tsql.py:2385:            with self.subTest("Testing PARSENAME <-> SPLIT_PART"):
tests/dialects/test_postgres.py:370:            "SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) v1, LATERAL VERTICES(p2.poly) v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
tests/dialects/test_postgres.py:371:            "SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) AS v1, LATERAL VERTICES(p2.poly) AS v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
[tool_use Bash] {"command": "grep -rn \"LR_ARROW\\|LT_AT\\|DHASH_ARROW\" sqlglot/ | head -30; sed -n 60,90p sqlglot/dialects/postgres.py; sed -n 225,245p sqlglot/tokens.py"}
[tool_result] sqlglot/tokenizer_core.py:63:    DHASH_ARROW = auto()
sqlglot/tokenizer_core.py:64:    LR_ARROW = auto()
sqlglot/tokenizer_core.py:66:    LT_AT = auto()
sqlglot/parser.py:918:        TokenType.LR_ARROW: exp.Distance,
sqlglot/parser.py:1032:        TokenType.DHASH_ARROW: lambda self, this, path: self.expression(
sqlglot/parser.py:1194:        TokenType.LT_AT: binary_range_parser(exp.ArrayContainsAll, reverse_args=True),
sqlglot/tokens.py:237:        "#>>": TokenType.DHASH_ARROW,
sqlglot/tokens.py
…[1545 chars elided]…
,
        ":=": TokenType.COLON_EQ,
        "<=>": TokenType.NULLSAFE_EQ,
        "->": TokenType.ARROW,
        "->>": TokenType.DARROW,
        "=>": TokenType.FARROW,
        "#>": TokenType.HASH_ARROW,
        "#>>": TokenType.DHASH_ARROW,
        "<->": TokenType.LR_ARROW,
        "&&": TokenType.DAMP,
        "??": TokenType.DQMARK,
        "~~~": TokenType.GLOB,
        "~~": TokenType.LIKE,
        "~~*": TokenType.ILIKE,
        "~*": TokenType.IRLIKE,
        "-|-": TokenType.ADJACENT,
[tool_use Bash] {"command": "sed -n 905,925p sqlglot/parser.py; grep -rn \"class Distance\" -A3 sqlglot/expressions*.py sqlglot/expressions/ 2>/dev/null; grep -rn \"Distance\\b\" sqlglot/ | grep -v \"^sqlglot/expressions\" | head; grep -n \"def _scan_keywords\\|_KEYWORD_TRIE\\|_KEYWORD_TRIE\" sqlglot/tokens.py sqlglot/tokenizer_core.py | head; ls sqlglot/ | head -80"}
[tool_result ERROR] Exit code 1
        TokenType.CARET: exp.BitwiseXor,
        TokenType.PIPE: exp.BitwiseOr,
    }

    TERM: t.ClassVar = {
        TokenType.DASH: exp.Sub,
        TokenType.PLUS: exp.Add,
        TokenType.MOD: exp.Mod,
        TokenType.COLLATE: exp.Collate,
    }

    FACTOR: t.ClassVar = {
        TokenType.DIV: exp.IntDiv,
        TokenType.LR_ARROW: exp.Distance,
        TokenType.SLASH: exp.Div,
        TokenType.STAR: exp.Mul,
    }

    EXPONENT: t.ClassVar[dict[TokenType, type[exp.Expr]]] = {}

    TIMES: t.ClassVar = {
(eval):1: no matches found: sqlglot/expressions*.py
[tool_use Bash] {"command": "grep -rn \"class Distance\" -A3 sqlglot/; grep -rn \"exp.Distance\\|Distance:\" sqlglot/ | head; grep -n \"_KEYWORD_TRIE\\|_SINGLE_TOKENS\\|def _scan_keywords\" sqlglot/tokenizer_core.py | head -20"}
[tool_result] sqlglot/expressions/core.py:2117:class Distance(Expression, Binary):
sqlglot/expressions/core.py-2118-    pass
sqlglot/expressions/core.py-2119-
sqlglot/expressions/core.py-2120-
sqlglot/parser.py:918:        TokenType.LR_ARROW: exp.Distance,
sqlglot/generator.py:4222:    def distance_sql(self, expression: exp.Distance) -> str:
sqlglot/generators/clickhouse.py:297:        exp.CosineDistance: rename_func("cosineDistance"),
sqlglot/generators/clickhouse.py:333:        exp.EuclideanDistance: rename
…[132 chars elided]…
acle.py:73:        exp.EuclideanDistance: rename_func("L2_DISTANCE"),
sqlglot/generators/starrocks.py:113:        exp.StDistance: st_distance_sphere,
sqlglot/generators/snowflake.py:482:        exp.CosineDistance: rename_func("VECTOR_COSINE_SIMILARITY"),
sqlglot/generators/snowflake.py:483:        exp.EuclideanDistance: rename_func("VECTOR_L2_DISTANCE"),
sqlglot/generators/snowflake.py:518:        exp.ManhattanDistance: rename_func("VECTOR_L1_DISTANCE"),
800:    def _scan_keywords(self) -> None:
[tool_use Bash] {"command": "sed -n 4218,4226p sqlglot/generator.py; sed -n 800,830p sqlglot/tokenizer_core.py; grep -n \"class Tokenizer\\|_KEYWORD_TRIE\\|KEYWORD_TRIE\" sqlglot/tokens.py | head"}
[tool_result]     def overlaps_sql(self, expression: exp.Overlaps) -> str:
        return self.binary(expression, "OVERLAPS")

    def distance_sql(self, expression: exp.Distance) -> str:
        return self.binary(expression, "<->")

    def dot_sql(self, expression: exp.Dot) -> str:
        return f"{self.sql(expression, 'this')}.{self.sql(expression, 'expression')}"
    def _scan_keywords(self) -> None:
        sql = self.sql
        sql_size = self.size
        single_tokens = self.single_tokens
        c
…[464 chars elided]…
            word = chars

            end = self._current + size
            size += 1

            if end < sql_size:
                char = sql[end]
                single_token = single_token or char in single_tokens
                is_space = char.isspace()

90:    _KEYWORD_TRIE: t.ClassVar[dict[str, object]]
123:        cls._KEYWORD_TRIE = new_trie(
135:class Tokenizer(_TokenizerBase):
211:    _KEYWORD_TRIE: t.ClassVar[dict[str, object]] = {}
587:            keyword_trie=self._KEYWORD_TRIE,
[tool_use Bash] {"command": "sed -n 58,70p sqlglot/tokenizer_core.py; grep -n \"_sql\\\"\\|getattr(self, \\|_sql\\b\" sqlglot/generator.py | head -20; grep -n \"def camel_to_snake\\|def _snake\\|snake\" sqlglot/generator.py sqlglot/helper.py | head; sed -n 2110,2120p sqlglot/expressions/core.py; grep -rn \"distance\\|Distance\" tests/test_expressions.py tests/test_generator.py 2>/dev/null | head -3"}
[tool_result]     ARROW = auto()
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
83:        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
192:        exp.Get: lambda self, e: self.get_put_sql(e),
206:        exp.JSONObject: lambda self, e: self._jsonobject_sql(e),
207:        exp.JSONObjectAgg: 
…[786 chars elided]…
ts_sql = " IF EXISTS" if expression.args.get("exists") else ""
1110:        return f"UNCACHE TABLE{exists_sql} {table}"
sqlglot/helper.py:159:def camel_to_snake_case(name: str) -> str:
sqlglot/helper.py:160:    """Converts `name` from camelCase to snake_case and returns the result."""
    pass


class PropertyEQ(Expression, Binary):
    pass


class Distance(Expression, Binary):
    pass


tests/test_expressions.py:733:        self.assertIsInstance(parse_one("ST_DISTANCE(a, b)"), exp.StDistance)
[tool_use Bash] {"command": "sed -n 78,92p sqlglot/generator.py; sed -n 159,170p sqlglot/helper.py; grep -n \"LR_ARROW\\|Distance\" sqlglot/*.py sqlglot/expressions/*.py | head; grep -rn \"class Tokenizer\" -A3 sqlglot/dialects/postgres.py | head -3; grep -n \"_postgres\\|class Postgres\\|CHR\\|DHASH\\|LR_\" tests/dialects/test_postgres.py | head -5"}
[tool_result]     cls: type[Generator],
) -> dict[type[exp.Expr], t.Callable[..., str]]:
    dispatch: dict[type[exp.Expr], t.Callable[..., str]] = dict(cls.TRANSFORMS)

    for attr_name in dir(cls):
        if not attr_name.endswith("_sql") or attr_name.startswith("_"):
            continue

        expr_key = attr_name[:-4]
        expr_cls = exp.EXPR_CLASSES.get(expr_key)

        if expr_cls and expr_cls not in dispatch:
            dispatch[expr_cls] = getattr(cls, attr_name)

    return dispatch
def ca
…[1020 chars elided]…
ManhattanDistance(Expression, Func):
sqlglot/dialects/postgres.py:61:    class Tokenizer(tokens.Tokenizer):
sqlglot/dialects/postgres.py-62-        BIT_STRINGS = [("b'", "'"), ("B'", "'")]
sqlglot/dialects/postgres.py-63-        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
10:    def test_postgres(self):
1598:        expected_postgres = """WITH t(boxcrate) AS (
1610:        self.validate_all(expected_postgres, read={"trino": trino_input}, pretty=True)
1877:    def test_postgres_create_trigger(self):
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/tokenizer_core.py", "old_string": "    LR_ARROW = auto()\n    DAT = auto()", "new_string": "    LR_ARROW = auto()\n    LLR_ARROW = auto()\n    DAT = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"<@\": TokenType.LT_AT,\n            \"?&\": TokenType.QMARK_AMP,", "new_string": "            \"<@\": TokenType.LT_AT,\n            \"<<->>\": TokenType.LLR_ARROW,\n            \"?&\": TokenType.QMARK_AMP,"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/expressions/core.py", "old_string": "class Distance(Expression, Binary):\n    pass\n", "new_string": "class Distance(Expression, Binary):\n    pass\n\n\nclass Distance3D(Expression, Binary):\n    pass\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/expressions/core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/parser.py", "old_string": "        TokenType.LR_ARROW: exp.Distance,\n", "new_string": "        TokenType.LR_ARROW: exp.Distance,\n        TokenType.LLR_ARROW: exp.Distance3D,\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/generator.py", "old_string": "        return self.binary(expression, \"<->\")\n", "new_string": "        return self.binary(expression, \"<->\")\n\n    def distance3d_sql(self, expression: exp.Distance3D) -> str:\n        return self.binary(expression, \"<<->>\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now a test in the Postgres test file, next to the existing `<->` coverage.
[tool_use Bash] {"command": "sed -n 362,376p tests/dialects/test_postgres.py"}
[tool_result]             "SELECT SUBSTRING(2022::CHAR(4) || LPAD(3::CHAR(2), 2, '0') FROM 3 FOR 4)",
            "SELECT SUBSTRING(CAST(2022 AS CHAR(4)) || LPAD(CAST(3 AS CHAR(2)), 2, '0') FROM 3 FOR 4)",
        )
        self.validate_identity(
            "SELECT m.name FROM manufacturers AS m LEFT JOIN LATERAL GET_PRODUCT_NAMES(m.id) pname ON TRUE WHERE pname IS NULL",
            "SELECT m.name FROM manufacturers AS m LEFT JOIN LATERAL GET_PRODUCT_NAMES(m.id) AS pname ON TRUE WHERE pname IS NULL",
     
…[136 chars elided]…
oly) v1, LATERAL VERTICES(p2.poly) v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
            "SELECT p1.id, p2.id, v1, v2 FROM polygons AS p1, polygons AS p2, LATERAL VERTICES(p1.poly) AS v1, LATERAL VERTICES(p2.poly) AS v2 WHERE (v1 <-> v2) < 10 AND p1.id <> p2.id",
        )
        self.validate_identity(
            "SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL",
            "SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE NOT deleted IS NULL",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py", "old_string": "        self.validate_identity(\n            \"SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL\",", "new_string": "        self.validate_identity(\"SELECT a <<->> b FROM t\")\n        self.validate_identity(\"SELECT * FROM t WHERE (a <<->> b) < 10\")\n        self.validate_identity(\n            \"SELECT id, email, CAST(deleted AS TEXT) FROM users WHERE deleted NOTNULL\","}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-130523-postgres-dialect-support-the-pos/base-1/tests/dialects/test_postgres.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfrom sqlglot import exp\ne = sqlglot.parse_one('SELECT a <<->> b FROM t', read='postgres')\nprint(repr(e.selects[0].__class__), e.selects[0].sql('postgres'), e.selects[0].sql())\nprint(sqlglot.transpile('SELECT a <<->> b', read='postgres', write='postgres'))\nprint(sqlglot.transpile('SELECT a <-> b', read='postgres', write='postgres'))\nprint(sqlglot.transpile('SELECT a <<->> b', read='postgres', write='duckdb'))\n\" && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -3"}
[tool_result] <class 'sqlglot.expressions.core.Distance3D'> a <<->> b a <<->> b
['SELECT a <<->> b']
['SELECT a <-> b']
['SELECT a <<->> b']
.........................                        [100%]
25 passed, 384 subtests passed in 0.24s
[assistant] Targeted tests pass. Running the project's full check command now, since the tokenizer change touches shared code.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; <work>/env-sqlglot/bin/python -c \"import sqlglot; print(sqlglot.transpile('SELECT 1 << 2, 1 <<-2', read='postgres', write='postgres'))\""}
[tool_result] ........................................................................ [ 76%]
............................................. [ 80%]
.................................................................................................................................................... [ 93%]
....................................................................       [100%]
1108 passed, 18038 subtests passed in 52.89s
['SELECT 1 << 2, 1 << -2']
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_postgres.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_postgres.py) 2>&1 | tail -4; git status --short"}
[tool_result] All checks passed!
176 files already formatted
 M sqlglot/dialects/postgres.py
 M sqlglot/expressions/core.py
 M sqlglot/generator.py
 M sqlglot/parser.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_postgres.py
[assistant] The Postgres dialect now handles the PostGIS 3D distance operator `<<->>`: it tokenizes, parses as a binary operator, and generates back as `<<->>`. The full test suite passes (1108 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/tokenizer_core.py`**: new `TokenType.LLR_ARROW`, added at the end of the `LR_ARROW` group.
- **`sqlglot/dialects/postgres.py`**: `"<<->>"` maps to `LLR_ARROW` in the Postgres tokenizer keywords.
- **`sqlglot/expressions/core.py`**: new `exp.Distance3D(Expression, Binary)`, alongside `exp.Distance`.
- **`sqlglot/parser.py`**: `LLR_ARROW` maps to `ex
…[167 chars elided]…
`tests/dialects/test_postgres.py`**: two identity round-trips, `SELECT a <<->> b FROM t` and a `WHERE (a <<->> b) < 10` case.

Choices to review:
- I added a new expression class rather than reusing `exp.Distance` with a flag, because the generator needs to emit a different operator.
- The token is only recognised in the Postgres tokenizer, so other dialects still see `<<` followed by `->>`. The generator method lives in the base class, so `Distance3D` can be rendered in any dialect.
- Existing `<<` (bit shift) and `<->` behaviour is unchanged; I checked `1 << 2` and `1 <<-2` still round-trip.
