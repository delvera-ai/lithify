# trajectory base-1

final message:
Parameterised `BIGNUMERIC` / `BIGDECIMAL` now transpiles to DuckDB using the supplied parameters, and falls back to `DECIMAL(38, 5)` only when none are given. The full suite passes (1105 passed).

```
BIGNUMERIC(76, 38)  →  DECIMAL(76, 38)     (was DECIMAL(38, 5)(76, 38))
BIGNUMERIC(10)      →  DECIMAL(10)         (was DECIMAL(38, 5)(10))
BIGNUMERIC          →  DECIMAL(38, 5)      (unchanged)
```

The cause was a static `TYPE_MAPPING` entry in `sqlglot/generators/duckdb.py` that always emitted `DECIMAL(38, 5)`. The base `datatype_sql` then appended the user's parameters after it.

Changes:
- **`sqlglot/generators/duckdb.py`**: removed the `BIGDECIMAL` entry from `TYPE_MAPPING` and added a `datatype_sql` override. It copies the type, switches it to `DECIMAL`, and uses the default `(38, 5)` only when no parameters are present.
- **`tests/dialects/test_bigquery.py`**: added a case to `test_bignumeric` for the `(76, 38)` form, for both `BIGNUMERIC` and `BIGDECIMAL`. Existing assertions are unchanged.

I did not commit. The changes are in the working tree.

## events
[tool_use Bash] {"command": "rtk grep -n -i \"bignumeric\\|BIGDECIMAL\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/typing/*.py 2>/dev/null; rtk grep -rn -i \"bignumeric\\|bigdecimal\" tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -40", "description": "Search for BIGNUMERIC handling in dialects and tests"}
[tool_result] (eval):1: command not found: rtk
[tool_use Bash] {"command": "grep -n -i \"bignumeric\\|bigdecimal\" sqlglot/dialects/bigquery.py sqlglot/dialects/duckdb.py sqlglot/generator.py sqlglot/parser.py sqlglot/expressions.py; grep -rn -i \"bignumeric\\|bigdecimal\" tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py | head -40", "description": "Search for BIGNUMERIC handling in dialects and tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
tests/dialects/test_bigquery.py:223:        self.validate_identity("CAST(x AS BIGNUMERIC)")
tests/dialects/test_bi
…[24 chars elided]…
elf.validate_identity("PARSE_BIGNUMERIC('1.2')")
tests/dialects/test_bigquery.py:3815:    def test_bignumeric(self):
tests/dialects/test_bigquery.py:3816:        # BIGDECIMAL is an alias of BIGNUMERIC
tests/dialects/test_bigquery.py:3817:        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
tests/dialects/test_bigquery.py:3822:                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
tests/dialects/test_bigquery.py:3830:                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
[tool_use Bash] {"command": "sed -n 3810,3845p tests/dialects/test_bigquery.py; grep -n \"BIGNUMERIC\\|BIGDECIMAL\\|DECIMAL\" sqlglot/dialects/duckdb.py sqlglot/dialects/dialect.py sqlglot/typing/*.py sqlglot/generator.py | head -40; grep -rn \"BIGDECIMAL\\|BIGNUMERIC\" sqlglot/*.py sqlglot/dialects/*.py | grep -v \"^sqlglot/dialects/bigquery.py:10[89]\\|111\" | head -30", "description": "Inspect BIGNUMERIC test and type mappings"}
[tool_result]             with self.assertRaises(UnsupportedError):
                self.parse_one("APPROX_QUANTILES(x, 2 RESPECT NULLS)").sql(
                    "duckdb", unsupported_level=ErrorLevel.RAISE
                )

    def test_bignumeric(self):
        # BIGDECIMAL is an alias of BIGNUMERIC
        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
            with self.subTest(f"Testing BigQuery's {type_}"):
                self.validate_all(
                    f"SELECT {type_} '1'",
                 
…[1660 chars elided]…
ery.py:361:    exp.ParseNumeric: {"returns": exp.DType.DECIMAL},
sqlglot/typing/snowflake.py:218:    - For other numeric types (NUMBER, DECIMAL, DOUBLE) -> return DOUBLE
sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
[tool_use Bash] {"command": "grep -n \"38\\|BIGDECIMAL\\|BIGNUMERIC\\|DType.DECIMAL\" sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py | head -40; sed -n 2225,2250p sqlglot/dialects/dialect.py; grep -n \"def datatype_sql\" -A60 sqlglot/generator.py | head -90", "description": "Locate DuckDB decimal mapping and datatype generation"}
[tool_result] sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py:110:    COERCES_TO[exp.DType.DECIMAL] |= {exp.DType.BIGDECIMAL}
sqlglot/dialects/bigquery.py:111:    COERCES_TO[exp.DType.BIGINT] |= {exp.DType.BIGDECIMAL}

def to_number_with_nls_param(self: Generator, expression: exp.ToNumber) -> str:
    return self.func(
        "TO_NUMBER",
        expression.this,
        expression.args.get("format"),
        expression.args.get("nlsparam"),
   
…[2888 chars elided]…
 directory_sql(self, expression: exp.Directory) -> str:
1692-        local = "LOCAL " if expression.args.get("local") else ""
1693-        row_format = self.sql(expression, "row_format")
1694-        row_format = f" {row_format}" if row_format else ""
1695-        return f"{local}DIRECTORY {self.sql(expression, 'this')}{row_format}"
1696-
1697-    def delete_sql(self, expression: exp.Delete) -> str:
1698-        hint = self.sql(expression, "hint")
1699-        this = self.sql(expression, "this")
[tool_use Bash] {"command": "grep -rn \"build_default_decimal_type\\|DEFAULT_DECIMAL\\|default_decimal\" sqlglot | head; grep -n \"BIGDECIMAL\\|BIGNUMERIC\" -B3 -A3 sqlglot/dialects/duckdb.py sqlglot/dialects/bigquery.py | head -5", "description": "Find where default decimal builder is wired up"}
[tool_result] sqlglot/parsers/snowflake.py:9:    build_default_decimal_type,
sqlglot/parsers/snowflake.py:807:        exp.DType.DECIMAL: build_default_decimal_type(precision=38, scale=0),
sqlglot/parsers/duckdb.py:9:    build_default_decimal_type,
sqlglot/parsers/duckdb.py:210:        exp.DType.DECIMAL: build_default_decimal_type(precision=18, scale=3),
sqlglot/dialects/dialect.py:2235:def build_default_decimal_type(
sqlglot/dialects/bigquery.py-105-    # https://cloud.google.com/bigquery/docs/reference/standard-sql/navigation_functions#percentile_cont
sqlglot/dialects/bigquery.py-106-    COERCES_TO = {
sqlglot/dialects/bigquery.py-107-        **TypeAnnotator.COERCES_TO,
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/bigquery.py-109-    }
[tool_use Bash] {"command": "grep -rn \"38, 5\\|BIGDECIMAL\" sqlglot/ | grep -v \"\\.pyc\" ; ls sqlglot/generators | head -50", "description": "Find where BIGDECIMAL maps to DECIMAL(38, 5)"}
[tool_result] sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
sqlglot/typing/bigquery.py:360:    exp.ParseBignumeric: {"returns": exp.DType.BIGDECIMAL},
sqlglot/dialects/bigquery.py:108:        exp.DType.BIGDECIMAL: {exp.DType.DOUBLE},
sqlglot/dialects/b
…[611 chars elided]…
b.py:1731:        exp.DType.DECFLOAT: "DECIMAL(38, 5)",
sqlglot/generators/duckdb.py:1745:        exp.DType.BIGDECIMAL: "DECIMAL(38, 5)",
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
doris.py
dremio.py
drill.py
druid.py
duckdb.py
dune.py
exasol.py
fabric.py
hive.py
materialize.py
mysql.py
oracle.py
postgres.py
presto.py
prql.py
python.py
redshift.py
risingwave.py
singlestore.py
snowflake.py
solr.py
spark.py
spark2.py
sqlite.py
starrocks.py
tableau.py
teradata.py
trino.py
tsql.py
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'SELECT CAST(1 AS BIGNUMERIC(76, 38))', 'SELECT CAST(1 AS BIGDECIMAL)', 'SELECT CAST(1 AS BIGNUMERIC(10))']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\"; sed -n 1725,1750p sqlglot/generators/duckdb.py; grep -n \"def datatype_sql\\|class Generator\" sqlglot/generators/duckdb.py", "description": "Reproduce the BIGNUMERIC parameter bug"}
[tool_result] ['DECLARE x DECIMAL(38, 5)(76, 38)']
['SELECT CAST(1 AS DECIMAL(38, 5)(76, 38))']
['SELECT CAST(1 AS DECIMAL(38, 5))']
['SELECT CAST(1 AS DECIMAL(38, 5)(10))']
    TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DType.BINARY: "BLOB",
        exp.DType.BPCHAR: "TEXT",
        exp.DType.CHAR: "TEXT",
        exp.DType.DATETIME: "TIMESTAMP",
        exp.DType.DECFLOAT: "DECIMAL(38, 5)",
        exp.DType.FLOAT: "REAL",
        exp.DType.JSONB: "JSON",
        exp.DType.NCHA
…[180 chars elided]…
HAR: "TEXT",
        exp.DType.TIMESTAMPLTZ: "TIMESTAMPTZ",
        exp.DType.TIMESTAMPNTZ: "TIMESTAMP",
        exp.DType.TIMESTAMP_S: "TIMESTAMP_S",
        exp.DType.TIMESTAMP_MS: "TIMESTAMP_MS",
        exp.DType.TIMESTAMP_NS: "TIMESTAMP_NS",
        exp.DType.BIGDECIMAL: "DECIMAL(38, 5)",
    }

    # https://github.com/duckdb/duckdb/blob/ff7f24fd8e3128d94371827523dae85ebaf58713/third_party/libpg_query/grammar/keywords/reserved_keywords.list#L1-L77
    RESERVED_KEYWORDS = {
        "array",
[tool_use Bash] {"command": "grep -rn \"def datatype_sql\" -A12 sqlglot/generators/ | head -60; grep -n \"def datatype_sql\\|def .*_sql(self, expression: exp.DataType\" sqlglot/generators/duckdb.py", "description": "Check existing datatype_sql overrides for pattern"}
[tool_result] sqlglot/generators/redshift.py:325:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/redshift.py-326-        """
sqlglot/generators/redshift.py-327-        Redshift converts the `TEXT` data type to `VARCHAR(255)` by default when people more generally mean
sqlglot/generators/redshift.py-328-        VARCHAR of max length which is `VARCHAR(max)` in Redshift. Therefore if we get a `TEXT` data type
sqlglot/generators/redshift.py-329-        without precision we convert i
…[4206 chars elided]…
ot/generators/risingwave.py-29-            key_type, value_type = expression.expressions
sqlglot/generators/risingwave.py-30-            return f"MAP({self.sql(key_type)}, {self.sql(value_type)})"
sqlglot/generators/risingwave.py-31-
sqlglot/generators/risingwave.py-32-        return super().datatype_sql(expression)
sqlglot/generators/singlestore.py:1468:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/singlestore.py-1469-        for arg_name in ("kind", "values"):
[tool_use Bash] {"command": "grep -n \"    def \\|^class\" sqlglot/generators/duckdb.py | head -30", "description": "List method layout in DuckDB generator"}
[tool_result] 334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
704:    def replace_seq(node: exp.Expr) -> exp.Expr:
1455:class DuckDBGenerator(generator.Generator):
2178:    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2184:    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2220:    def bitmapbucketnumber_sql(self, expression: exp.BitmapBucketNumber) -> str:
2245:    def bitmapbitposition_sql(self, expression: ex
…[1157 chars elided]…
   def tonumber_sql(self, expression: exp.ToNumber) -> str:
2458:    def _greatest_least_sql(self, expression: exp.Greatest | exp.Least) -> str:
2482:    def generator_sql(self, expression: exp.Generator) -> str:
2496:    def greatest_sql(self, expression: exp.Greatest) -> str:
2499:    def least_sql(self, expression: exp.Least) -> str:
2502:    def lambda_sql(self, expression: exp.Lambda, arrow_sep: str = "->", wrap: bool = True) -> str:
2513:    def show_sql(self, expression: exp.Show) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "offset": 2172, "limit": 14}
[tool_result] 2172	            WHEN :string IS NULL OR :delimiter IS NULL OR :part_index IS NULL THEN NULL
2173	            ELSE :base_func
2174	        END
2175	        """
2176	    )
2177	
2178	    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
2179	        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
2180	        return self.sql(
2181	            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
2182	        )
2183	
2184	    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
2185	        """
[assistant] Reproduced: the `TYPE_MAPPING` string `DECIMAL(38, 5)` is emitted and then `datatype_sql` appends the user's parameters. I'll drop the static mapping entry and handle `BIGDECIMAL` in a `datatype_sql` override that uses the supplied parameters, falling back to `DECIMAL(38, 5)` only when none are given.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "        exp.DType.TIMESTAMP_NS: \"TIMESTAMP_NS\",\n        exp.DType.BIGDECIMAL: \"DECIMAL(38, 5)\",\n    }", "new_string": "        exp.DType.TIMESTAMP_NS: \"TIMESTAMP_NS\",\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:", "new_string": "    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.
…[7 chars elided]…
MAL):\n            expression = expression.copy()\n            expression.set(\"this\", exp.DType.DECIMAL)\n            if not expression.expressions:\n                expression.set(\"expressions\", exp.DataType.from_str(\"DECIMAL(38, 5)\").expressions)\n\n        return super().datatype_sql(expression)\n\n    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -c \"\nimport sqlglot\nfor s in ['DECLARE x BIGNUMERIC(76, 38)', 'SELECT CAST(1 AS BIGNUMERIC(76, 38))', 'SELECT CAST(1 AS BIGDECIMAL)', 'SELECT CAST(1 AS BIGNUMERIC(10))', 'SELECT CAST(1 AS BIGNUMERIC)']:\n    print(sqlglot.transpile(s, read='bigquery', write='duckdb'))\n\"; $P -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py 2>&1 | tail -5", "description": "Verify fix output and run BigQuery/DuckDB tests"}
[tool_result] ['DECLARE x DECIMAL(76, 38)']
['SELECT CAST(1 AS DECIMAL(76, 38))']
['SELECT CAST(1 AS DECIMAL(38, 5))']
['SELECT CAST(1 AS DECIMAL(10))']
['SELECT CAST(1 AS DECIMAL(38, 5))']
................................................... [ 50%]
...................................................                                                  [100%]
102 passed, 1649 subtests passed in 0.63s
[assistant] The fix works and the existing tests pass. I'll add a regression test for the parameterised case next to the existing `test_bignumeric`, without touching its current assertions.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[275 chars elided]…
\"SELECT CAST(1 AS BIGNUMERIC)\",\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(38, 5))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_}(76, 38))\",\n                    write={\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(76, 38))\",\n                    },\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-e2b5bc4f1eee/20261029-102851-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "P=<work>/env-sqlglot/bin/python; $P -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show changed files"}
[tool_result] ........................... [ 86%]
.......................... [ 88%]
................................. [ 91%]
...............................................................................................                          [100%]
1105 passed, 17950 subtests passed in 58.91s
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[assistant] Parameterised `BIGNUMERIC` / `BIGDECIMAL` now transpiles to DuckDB using the supplied parameters, and falls back to `DECIMAL(38, 5)` only when none are given. The full suite passes (1105 passed).

```
BIGNUMERIC(76, 38)  →  DECIMAL(76, 38)     (was DECIMAL(38, 5)(76, 38))
BIGNUMERIC(10)      →  DECIMAL(10)         (was DECIMAL(38, 5)(10))
BIGNUMERIC          →  DECIMAL(38, 5)      (unchanged)
```

The cause was a static `TYPE_MAPPING` entry in `sqlglot/generators/duckdb.py` that always emitted `DECIMAL(38, 5)`. The base `datatype_sql` then appended the user's parameters after it.

Changes:
- **`sqlglot/generators/duckdb.py`**: removed the `BIGDECIMAL` entry from `TYPE_MAPPING` and added a `datatype_sql` override. It copies the type, switches it to `DECIMAL`, and uses the default `(38, 5)` only when no parameters are present.
- **`tests/dialects/test_bigquery.py`**: added a case to `test_bignumeric` for the `(76, 38)` form, for both `BIGNUMERIC` and `BIGDECIMAL`. Existing assertions are unchanged.

I did not commit. The changes are in the working tree.
