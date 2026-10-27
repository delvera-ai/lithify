# trajectory base-1

final message:
Parameterised `BIGNUMERIC` / `BIGDECIMAL` types now transpile to DuckDB with the user's parameters, and the default `DECIMAL(38, 5)` is used only when none are given. The full suite passes: `SUMMARY: 1105 passed, 17952 subtests passed in 59.89s`, `EXIT: 0`, run after my last edit.

**The fix** is a `datatype_sql` override in `sqlglot/generators/duckdb.py`. For a `BIGDECIMAL` with parameters it emits `DECIMAL(<params>)`. Otherwise it defers to the base generator. The bug was that the base generator appended the parameters to the fixed `DECIMAL(38, 5)` mapping.

**Probes after the fix**, all in DuckDB output:
- `DECLARE x BIGNUMERIC(76, 38)` → `DECLARE x DECIMAL(76, 38)`
- `BIGDECIMAL(76, 38)` (alias) → `DECIMAL(76, 38)`
- `CREATE TABLE t (c BIGNUMERIC(76, 38))` → `DECIMAL(76, 38)`
- `CAST(x AS BIGNUMERIC(76, 38))` → `DECIMAL(76, 38)`
- `ARRAY<BIGNUMERIC(76, 38)>` → `DECIMAL(76, 38)[]`
- `STRUCT<a BIGNUMERIC(76, 38)>` → `STRUCT(a DECIMAL(76, 38))`
- one parameter, `BIGNUMERIC(38)` → `DECIMAL(38)`
- no parameters, `BIGNUMERIC` → `DECIMAL(38, 5)` (unchanged)

None of the probed forms still fail.

**Tests:** I added three cases to `test_bignumeric` in `tests/dialects/test_bigquery.py`: a parameterised cast, a parameterised `DECLARE`, and the existing no-parameter default. No existing assertions changed. `ruff check` and `ruff format --check` are clean on both files.

**Things to check:**
- **DuckDB caps DECIMAL precision at 38.** So `BIGNUMERIC(76, 38)` now produces `DECIMAL(76, 38)`, which DuckDB will reject when executed. I followed your instruction to emit the user's parameters rather than clamping them silently. If you'd rather clamp to 38 or fall back to the default for precision above 38, that's a small follow-up.
- **BigQuery round-trip drops parameters.** `BIGNUMERIC(76, 38)` written back to BigQuery becomes `BIGNUMERIC`. That's existing behaviour and outside this change, so I left it alone.

Nothing is committed.

## events
[tool_use Bash] {"command": "grep -rn -i \"bignumeric\\|bigdecimal\" sqlglot/ | head -50", "description": "Find BIGNUMERIC/BIGDECIMAL references in sqlglot"}
[tool_result] sqlglot/tokens.py:447:        "BIGDECIMAL": TokenType.BIGDECIMAL,
sqlglot/tokens.py:448:        "BIGNUMERIC": TokenType.BIGDECIMAL,
sqlglot/tokenizer_core.py:141:    BIGDECIMAL = auto()
sqlglot/parser.py:545:        TokenType.BIGDECIMAL,
sqlglot/optimizer/annotate_types.py:132:        exp.DType.BIGDECIMAL,
sqlglot/typing/bigquery.py:16:    |  INPUT  | INT64   | NUMERIC | BIGNUMERIC | FLOAT64 |
sqlglot/typing/bigquery.py:18:    |  OUTPUT | FLOAT64 | NUMERIC | BIGNUMERIC | FLOAT64 |
sqlglot/typing
…[1213 chars elided]…
ons/datatypes.py:264:        DType.BIGDECIMAL,
sqlglot/expressions/datatypes.py:295:        DType.BIGDECIMAL,
sqlglot/expressions/string.py:577:class ParseBignumeric(Expression, Func):
sqlglot/generators/singlestore.py:343:        exp.DType.BIGDECIMAL: "DECIMAL",
sqlglot/generators/bigquery.py:413:        exp.DType.BIGDECIMAL: "BIGNUMERIC",
sqlglot/generators/snowflake.py:647:        exp.DType.BIGDECIMAL: "DOUBLE",
sqlglot/generators/duckdb.py:1745:        exp.DType.BIGDECIMAL: "DECIMAL(38, 5)",
[tool_use Bash] {"command": "grep -rn -i \"bignumeric\\|bigdecimal\" tests/ | head -30; ls .lithify/harness/scripts/ 2>/dev/null; cat memory.md 2>/dev/null | head -20", "description": "Search tests and harness files for BIGNUMERIC"}
[tool_result] tests/test_optimizer.py:1484:                "bignum_col": "BIGNUMERIC",
tests/test_optimizer.py:2132:            ("SELECT 1::INT AS c", "SELECT 2::BIGDECIMAL AS c", "BIGDECIMAL"),
tests/test_optimizer.py:2643:        null_sql = "SELECT t.foo FROM (SELECT CAST(1 AS BIGDECIMAL) AS foo UNION ALL SELECT NULL AS foo) AS t"
tests/test_optimizer.py:2647:        self.assertEqual(annotated.selects[0].type.this, exp.DataType.Type.BIGDECIMAL)
tests/test_optimizer.py:2649:        null_sql = "SELECT t.foo F
…[1920 chars elided]…
nnotate_functions.sql:930:BIGDECIMAL;
tests/fixtures/optimizer/annotate_functions.sql:942:BIGDECIMAL;
tests/fixtures/optimizer/annotate_functions.sql:954:BIGDECIMAL;
tests/fixtures/optimizer/annotate_functions.sql:966:BIGDECIMAL;
tests/fixtures/optimizer/annotate_functions.sql:978:BIGDECIMAL;
tests/fixtures/optimizer/annotate_functions.sql:990:BIGDECIMAL;
tests/fixtures/optimizer/annotate_functions.sql:1002:BIGNUMERIC;
tests/fixtures/optimizer/annotate_functions.sql:1010:BIGNUMERIC;
run_suite.py
[tool_use Bash] {"command": "sed -n 1725,1775p sqlglot/generators/duckdb.py; echo ----; grep -n \"def datatype_sql\" -A60 sqlglot/generator.py", "description": "Read DuckDB type mapping and base datatype_sql"}
[tool_result]     TYPE_MAPPING = {
        **generator.Generator.TYPE_MAPPING,
        exp.DType.BINARY: "BLOB",
        exp.DType.BPCHAR: "TEXT",
        exp.DType.CHAR: "TEXT",
        exp.DType.DATETIME: "TIMESTAMP",
        exp.DType.DECFLOAT: "DECIMAL(38, 5)",
        exp.DType.FLOAT: "REAL",
        exp.DType.JSONB: "JSON",
        exp.DType.NCHAR: "TEXT",
        exp.DType.NVARCHAR: "TEXT",
        exp.DType.UINT: "UINTEGER",
        exp.DType.VARBINARY: "BLOB",
        exp.DType.ROWVERSION: "BLOB",
  
…[3266 chars elided]…
 directory_sql(self, expression: exp.Directory) -> str:
1692-        local = "LOCAL " if expression.args.get("local") else ""
1693-        row_format = self.sql(expression, "row_format")
1694-        row_format = f" {row_format}" if row_format else ""
1695-        return f"{local}DIRECTORY {self.sql(expression, 'this')}{row_format}"
1696-
1697-    def delete_sql(self, expression: exp.Delete) -> str:
1698-        hint = self.sql(expression, "hint")
1699-        this = self.sql(expression, "this")
[tool_use Bash] {"command": "cat > /tmp/probe_bn.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nqs = [\n \"DECLARE x BIGNUMERIC(76, 38)\",\n \"DECLARE x BIGDECIMAL(76, 38)\",\n \"DECLARE x BIGNUMERIC\",\n \"DECLARE x BIGNUMERIC(38)\",\n \"CREATE TABLE t (c BIGNUMERIC(76, 38))\",\n \"CREATE TABLE t (c BIGNUMERIC)\",\n \"SELECT CAST(x AS BIGNUMERIC(76, 38))\",\n \"SELECT CAST(x AS BIGNUMERIC)\",\n \"SELECT CA
…[258 chars elided]…
nt(q, \"!!\", type(ex).__name__, ex)\ne = sqlglot.parse_one(\"DECLARE x BIGNUMERIC(76, 38)\", read=\"bigquery\")\nprint(repr(e.find(exp.DataType)))\nEOF\n<work>/env-sqlglot/bin/python -I /tmp/probe_bn.py", "description": "Reproduce BIGNUMERIC parameterised transpile to DuckDB"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "/tmp/probe_bn.py", line 1, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[tool_use Bash] {"command": "PYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_bn.py", "description": "Reproduce BIGNUMERIC parameterised transpile to DuckDB"}
[tool_result] DECLARE x BIGNUMERIC(76, 38) => DECLARE x DECIMAL(38, 5)(76, 38)
DECLARE x BIGDECIMAL(76, 38) => DECLARE x DECIMAL(38, 5)(76, 38)
DECLARE x BIGNUMERIC => DECLARE x DECIMAL(38, 5)
DECLARE x BIGNUMERIC(38) => DECLARE x DECIMAL(38, 5)(38)
CREATE TABLE t (c BIGNUMERIC(76, 38)) => CREATE TABLE t (c DECIMAL(38, 5)(76, 38))
CREATE TABLE t (c BIGNUMERIC) => CREATE TABLE t (c DECIMAL(38, 5))
SELECT CAST(x AS BIGNUMERIC(76, 38)) => SELECT CAST(x AS DECIMAL(38, 5)(76, 38))
SELECT CAST(x AS BIGNUMERIC) => SELECT CAST(x AS DECIMAL(38, 5))
SELECT CAST(x AS ARRAY<BIGNUMERIC(76, 38)>) => SELECT CAST(x AS DECIMAL(38, 5)(76, 38)[])
SELECT CAST(x AS STRUCT<a BIGNUMERIC(76, 38)>) => SELECT CAST(x AS STRUCT(a DECIMAL(38, 5)(76, 38)))
DataType(
  this=DType.BIGDECIMAL,
  expressions=[
    DataTypeParam(
      this=Literal(this=76, is_string=False)),
    DataTypeParam(
      this=Literal(this=38, is_string=False))],
  nested=False)
[tool_use Bash] {"command": "grep -rn \"def datatype_sql\" -A12 sqlglot/generators/duckdb.py sqlglot/generators/bigquery.py | head -60; grep -n \"DataTypeParam\" sqlglot/generators/duckdb.py | head", "description": "Check existing datatype_sql overrides in DuckDB and BigQuery"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn \"def datatype_sql\" sqlglot/ | head; grep -rn \"def datatype_sql\" -A15 sqlglot/generators/snowflake.py sqlglot/generators/postgres.py 2>/dev/null | head -40; grep -n \"^    def .*_sql\" sqlglot/generators/duckdb.py | head -80 | tail -60", "description": "Look for datatype_sql overrides in other generators"}
[tool_result] sqlglot/generator.py:1639:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/optimizer/simplify.py:1605:    def datatype_sql(self, e: exp.DataType) -> None:
sqlglot/generators/clickhouse.py:517:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/fabric.py:78:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/singlestore.py:1468:    def datatype_sql(self, expression: exp.DataType) -> str:
sqlglot/generators/risingwave.py:2
…[6972 chars elided]…
sect) -> str:
3367:    def arrayexcept_sql(self, expression: exp.ArrayExcept) -> str:
3375:    def arrayslice_sql(self, expression: exp.ArraySlice) -> str:
3407:    def arrayszip_sql(self, expression: exp.ArraysZip) -> str:
3460:    def lower_sql(self, expression: exp.Lower) -> str:
3464:    def upper_sql(self, expression: exp.Upper) -> str:
3468:    def reverse_sql(self, expression: exp.Reverse) -> str:
3472:    def _left_right_sql(self, expression: exp.Left | exp.Right, func_name: str) -> str:
[tool_use Bash] {"command": "grep -n \"^class \\|^    def \\|^    [A-Z_]* = \" sqlglot/generators/duckdb.py | sed -n 1,60p", "description": "List DuckDB generator class members near the top"}
[tool_result] 334:    def _duckdb_date_delta_sql(self: DuckDBGenerator, expression: DATETIME_DELTA) -> str:
704:    def replace_seq(node: exp.Expr) -> exp.Expr:
1455:class DuckDBGenerator(generator.Generator):
1456:    PARAMETER_TOKEN = "$"
1457:    NAMED_PLACEHOLDER_TOKEN = "$"
1458:    JOIN_HINTS = False
1459:    TABLE_HINTS = False
1460:    QUERY_HINTS = False
1461:    LIMIT_FETCH = "LIMIT"
1462:    STRUCT_DELIMITER = ("(", ")")
1463:    RENAME_TABLE_WITH_DB = False
1465:    SEMI_ANTI_JOIN_WITH_SIDE = Fals
…[2185 chars elided]…
.DecompressBinary) -> str:
2320:    def jarowinklersimilarity_sql(self, expression: exp.JarowinklerSimilarity) -> str:
2335:    def nthvalue_sql(self, expression: exp.NthValue) -> str:
2342:    def randstr_sql(self, expression: exp.Randstr) -> str:
2370:    def reduce_sql(self, expression: exp.Reduce) -> str:
2380:    def zipf_sql(self, expression: exp.Zipf) -> str:
2407:    def tobinary_sql(self, expression: exp.ToBinary) -> str:
2444:    def tonumber_sql(self, expression: exp.ToNumber) -> str:
[tool_use Bash] {"command": "sed -n 2170,2184p sqlglot/generators/duckdb.py", "description": "Read lines around the insertion point"}
[tool_result]             WHEN :delimiter = '' THEN NULL
            WHEN :part_index < 0 THEN NULL
            WHEN :string IS NULL OR :delimiter IS NULL OR :part_index IS NULL THEN NULL
            ELSE :base_func
        END
        """
    )

    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:
        cond = exp.Paren(this=exp.replace_placeholders(condition, arr1=arr1, arr2=arr2))
        return self.sql(
            exp.replace_placeholders(self.ARRAY_BAG_TEMPLATE, arr1=arr1, arr2=arr2, cond=cond)
        )

    def timeslice_sql(self, expression: exp.TimeSlice) -> str:
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-232946-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py", "old_string": "    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:\n        cond = exp.Paren(", "new_string": "    def datatype_sql(self, expression: exp.DataType) -> str:\n        if expression.is_type(exp.DType.BIGDECIMAL) and expression.expressions:\n            return f\"DECIMAL({self.expressions(expression, flat=True)})\"\n\n        return super().datatype_sql(expression)\n\n    def _array_bag_sql(self, condition: exp.Expr, arr1: exp.Expr, arr2: exp.Expr) -> str:\n        cond = exp.Paren("}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-232946-bigquery-duckdb-a-parameterised/base-1/sqlglot/generators/duckdb.py has been updated successfully.
[tool_use Bash] {"command": "cat >> /tmp/probe_bn.py <<'EOF'\nfor q in [\"DECLARE x BIGNUMERIC(76, 38)\", \"SELECT CAST(x AS BIGNUMERIC(38))\", \"SELECT CAST(x AS BIGNUMERIC(10, 2))\", \"SELECT CAST(x AS ARRAY<BIGNUMERIC(76, 38)>)\", \"SELECT CAST(x AS BIGNUMERIC)\"]:\n    e = sqlglot.parse_one(q, read=\"bigquery\")\n    print(\"DUCK\", q, \"=>\", e.sql(\"duckdb\"), \"| BQ\", e.sql(\"bigquery\"))\nEOF\nPYTHONPATH=. <work>/env-sqlglot/bin/python /tmp/probe_bn.py 2>&1 | head -30; ls tests/dialects | grep -i duck", "description": "Re-run BIGNUMERIC probes after the fix"}
[tool_result] DECLARE x BIGNUMERIC(76, 38) => DECLARE x DECIMAL(76, 38)
DECLARE x BIGDECIMAL(76, 38) => DECLARE x DECIMAL(76, 38)
DECLARE x BIGNUMERIC => DECLARE x DECIMAL(38, 5)
DECLARE x BIGNUMERIC(38) => DECLARE x DECIMAL(38)
CREATE TABLE t (c BIGNUMERIC(76, 38)) => CREATE TABLE t (c DECIMAL(76, 38))
CREATE TABLE t (c BIGNUMERIC) => CREATE TABLE t (c DECIMAL(38, 5))
SELECT CAST(x AS BIGNUMERIC(76, 38)) => SELECT CAST(x AS DECIMAL(76, 38))
SELECT CAST(x AS BIGNUMERIC) => SELECT CAST(x AS DECIMAL(38, 5))
SEL
…[434 chars elided]…
8) | BQ DECLARE x BIGNUMERIC(76, 38)
DUCK SELECT CAST(x AS BIGNUMERIC(38)) => SELECT CAST(x AS DECIMAL(38)) | BQ SELECT CAST(x AS BIGNUMERIC)
DUCK SELECT CAST(x AS BIGNUMERIC(10, 2)) => SELECT CAST(x AS DECIMAL(10, 2)) | BQ SELECT CAST(x AS BIGNUMERIC)
DUCK SELECT CAST(x AS ARRAY<BIGNUMERIC(76, 38)>) => SELECT CAST(x AS DECIMAL(76, 38)[]) | BQ SELECT CAST(x AS ARRAY<BIGNUMERIC>)
DUCK SELECT CAST(x AS BIGNUMERIC) => SELECT CAST(x AS DECIMAL(38, 5)) | BQ SELECT CAST(x AS BIGNUMERIC)
test_duckdb.py
[tool_use Bash] {"command": "sed -n 3815,3840p tests/dialects/test_bigquery.py", "description": "Read existing BIGNUMERIC test in BigQuery tests"}
[tool_result]     def test_bignumeric(self):
        # BIGDECIMAL is an alias of BIGNUMERIC
        for type_ in ("BIGNUMERIC", "BIGDECIMAL"):
            with self.subTest(f"Testing BigQuery's {type_}"):
                self.validate_all(
                    f"SELECT {type_} '1'",
                    write={
                        "bigquery": "SELECT CAST('1' AS BIGNUMERIC)",
                        "duckdb": "SELECT CAST('1' AS DECIMAL(38, 5))",
                    },
                )

                self.validate_all(
                    f"SELECT CAST(1 AS {type_})",
                    write={
                        "bigquery": "SELECT CAST(1 AS BIGNUMERIC)",
                        "duckdb": "SELECT CAST(1 AS DECIMAL(38, 5))",
                    },
                )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-232946-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py", "old_string": "                self.validate_all(\n                    f\"SELECT CAST(1 AS {type_})\",\n                    write={\n                        \"bigquery\": \"SELECT CAST(1 AS BIGNUMERIC)\",\n               
…[504 chars elided]…
S {type_}(10, 2))\",\n                    write={\n                        \"duckdb\": \"SELECT CAST(1 AS DECIMAL(10, 2))\",\n                    },\n                )\n\n                self.validate_all(\n                    f\"DECLARE x {type_}(76, 38)\",\n                    write={\n                        \"duckdb\": \"DECLARE x DECIMAL(76, 38)\",\n                    },\n                )"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-232946-bigquery-duckdb-a-parameterised/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_duckdb.py -k \"bignumeric or duckdb or bigquery\" 2>&1 | tail -15", "description": "Run BigQuery and DuckDB dialect tests"}
[tool_result] ................................................................... [ 65%]
.......................... [ 91%]
.........                                              [100%]
102 passed, 1653 subtests passed in 0.59s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 2 other pytest process(es) running; expect slower runs:
  34207 03-03:59:21 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
  48362       00:07 <work>/env-sqlglot/b
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-4dd6bb25d8.log
ELAPSED: 60s
SUMMARY: 1105 passed, 17952 subtests passed in 59.89s
EXIT: 0
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/duckdb.py tests/dialects/test_bigquery.py; git status --short", "description": "Lint and format-check the changed files"}
[tool_result] All checks passed!
2 files already formatted
 M sqlglot/generators/duckdb.py
 M tests/dialects/test_bigquery.py
[assistant] Parameterised `BIGNUMERIC` / `BIGDECIMAL` types now transpile to DuckDB with the user's parameters, and the default `DECIMAL(38, 5)` is used only when none are given. The full suite passes: `SUMMARY: 1105 passed, 17952 subtests passed in 59.89s`, `EXIT: 0`, run after my last edit.

**The fix** is a `datatype_sql` override in `sqlglot/generators/duckdb.py`. For a `BIGDECIMAL` with parameters it emits `DECIMAL(<params>)`. Otherwise it defers to the base generator. The bug was that the base generator appended the parameters to the fixed `DECIMAL(38, 5)` mapping.

**Probes after the fix**, all in 
…[750 chars elided]…
--check` are clean on both files.

**Things to check:**
- **DuckDB caps DECIMAL precision at 38.** So `BIGNUMERIC(76, 38)` now produces `DECIMAL(76, 38)`, which DuckDB will reject when executed. I followed your instruction to emit the user's parameters rather than clamping them silently. If you'd rather clamp to 38 or fall back to the default for precision above 38, that's a small follow-up.
- **BigQuery round-trip drops parameters.** `BIGNUMERIC(76, 38)` written back to BigQuery becomes `BIGNUMERIC`. That's existing behaviour and outside this change, so I left it alone.

Nothing is committed.
