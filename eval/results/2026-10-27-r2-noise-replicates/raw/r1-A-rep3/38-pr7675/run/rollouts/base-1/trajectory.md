# trajectory base-1

final message:
`LOAD DATA INTO TEMP TABLE` and `INTO TEMPORARY TABLE` now parse, and all three forms from your request round-trip in BigQuery. The full test suite passes (1112 tests, 18136 subtests) and ruff is clean.

The change touches three places:

- **Parser** (`sqlglot/parser.py`, `_parse_load`): `INTO` is matched on its own, then an optional `TEMP`/`TEMPORARY` (both tokenize to the same token), then an optional `TABLE`. Previously it required `INTO TABLE` as a pair, which is why `INTO TEMP TABLE` failed.
- **Expression** (`sqlglot/expressions/dml.py`): `LoadData` gets a `temporary` arg.
- **Generator** (`sqlglot/generator.py`, `loaddata_sql`): emits `TEMP` when the flag is set.

I added `LOAD DATA INTO TEMP TABLE ... FROM FILES(...)` to the existing round-trip list in `tests/dialects/test_bigquery.py`. I did not edit or weaken any existing test.

Choices to review:
- `TEMPORARY` parses but is written back as `TEMP`, so it is a normalizing round-trip rather than an exact identity.
- `OVERWRITE` combined with temp emits `LOAD DATA OVERWRITE TEMP table ...` (no `TABLE` keyword, matching the existing overwrite form). I'm not certain BigQuery accepts that combination, so tell me if you'd rather it be rejected.
- The Hive-style `INPATH ... INTO TABLE` branch also honours the temp flag, so the flag is never silently dropped.
- `INTO` is now optional in the parser, so `LOAD DATA TABLE x` is accepted too. This is looser than before for the Hive path.

I haven't committed anything.

## events
[tool_use Bash] {"command": "grep -rn \"LOAD\" sqlglot/dialects/bigquery.py sqlglot/parser.py sqlglot/generator.py sqlglot/expressions.py | grep -i \"load\" | head -50; grep -rn \"LOAD DATA\" tests/ | head", "description": "Find LOAD handling in sqlglot and tests"}
[tool_result] ugrep: warning: sqlglot/expressions.py: No such file or directory
sqlglot/generator.py:2169:        return f"WITH{no}{concurrent} ISOLATED LOADING{target}"
sqlglot/generator.py:2905:            return f"LOAD DATA{overwrite}{this} FROM {files_sql}"
sqlglot/generator.py:2916:        return f"LOAD DATA{local}{inpath}{overwrite}{this}{partition}{input_format}{serde}"
sqlglot/parser.py:716:        TokenType.LOAD,
sqlglot/parser.py:1099:        TokenType.LOAD: lambda self: self._parse_load(),
sqlglot/
…[717 chars elided]…
es/identity.sql:710:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy')
tests/fixtures/identity.sql:711:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y'
tests/fixtures/identity.sql:712:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:713:LOAD DATA INPATH 'x' INTO TABLE y INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:714:LOAD DATA INPATH 'x' INTO TABLE y.b INPUTFORMAT 'y' SERDE 'z'
[tool_use Bash] {"command": "grep -n \"_parse_load\" -A40 sqlglot/parser.py | sed -n '1,60p'; sed -n 2895,2920p sqlglot/generator.py; sed -n 205,230p tests/dialects/test_bigquery.py; grep -n \"class LoadData\" -A12 sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null", "description": "Inspect LOAD parser and generator code"}
[tool_result ERROR] Exit code 2
1099:        TokenType.LOAD: lambda self: self._parse_load(),
1100-        TokenType.MERGE: lambda self: self._parse_merge(),
1101-        TokenType.PIVOT: lambda self: self._parse_simplified_pivot(),
1102-        TokenType.PRAGMA: lambda self: self.expression(exp.Pragma(this=self._parse_expression())),
1103-        TokenType.REFRESH: lambda self: self._parse_refresh(),
1104-        TokenType.ROLLBACK: lambda self: self._parse_commit_or_rollback(),
1105-        TokenType.SET: lambda 
…[5777 chars elided]…
qlglot/expressions/dml.py-284-        "local": False,
sqlglot/expressions/dml.py-285-        "overwrite": False,
sqlglot/expressions/dml.py-286-        "inpath": False,
sqlglot/expressions/dml.py-287-        "files": False,
sqlglot/expressions/dml.py-288-        "partition": False,
sqlglot/expressions/dml.py-289-        "input_format": False,
sqlglot/expressions/dml.py-290-        "serde": False,
sqlglot/expressions/dml.py-291-    }
sqlglot/expressions/dml.py-292-
sqlglot/expressions/dml.py-293-
[tool_use Bash] {"command": "sed -n 3606,3615p sqlglot/parser.py; <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nfor s in ['LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\')']:\n    try: print(repr(sqlglot.transpile(s, read='bigquery', write='bigquery')))\n    except Exception as e: print('ERR', type(e).__name__, str(e)[:200])\n\"; grep -n \"TEMPORARY\\|\\\"TEMP\\\"\" sqlglot/tokens.py | head", "description": "Inspect remaining parser lines and reproduce failure"}
[tool_result]                     input_format=self._match_text_seq("INPUTFORMAT") and self._parse_string(),
                    serde=self._match_text_seq("SERDE") and self._parse_string(),
                )
            )
        return self._parse_as_command(self._prev)

    def _parse_delete(self) -> exp.Delete:
        hint = self._parse_hint()

        # This handles MySQL's "Multiple-Table Syntax"
ERR ParseError Expected table name but got <Token token_type: TokenType.INTO, text: INTO, line: 1, col: 14, start: 10, end: 13, comments: []>. Line 1, Col: 14.
  LOAD DATA [4mINTO[0m TEMP TABLE mydataset.table1 FR
ERR ParseError Expected table name but got <Token token_type: TokenType.INTO, text: INTO, line: 1, col: 14, start: 10, end: 13, comments: []>. Line 1, Col: 14.
  LOAD DATA [4mINTO[0m TEMPORARY TABLE mydataset.tabl
392:        "TEMP": TokenType.TEMPORARY,
393:        "TEMPORARY": TokenType.TEMPORARY,
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\np='sqlglot/parser.py'\ns=open(p).read()\nold='''            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwr
…[2139 chars elided]…
turn f\"LOAD DATA{overwrite}{this} FROM {files_sql}\"\n\n        local = \" LOCAL\" if expression.args.get(\"local\") else \"\"\n        inpath = f\" INPATH {self.sql(expression, 'inpath')}\"\n        this = f\" INTO {temp}TABLE {this}\"\n'''\nassert s.count(old)==1\ns=s.replace(old,new)\nopen(p,'w').write(s)\nEOF\ngit diff --stat", "description": "Apply parser, expression, and generator changes"}
[tool_result]  sqlglot/expressions/dml.py | 1 +
 sqlglot/generator.py       | 5 +++--
 sqlglot/parser.py          | 6 +++++-
 3 files changed, 9 insertions(+), 3 deletions(-)
[assistant] Now I'll add the new round-trip cases to the existing BigQuery test loop and run the suite.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='tests/dialects/test_bigquery.py'\ns=open(p).read()\nold='''            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):'''\nnew='''            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydata
…[356 chars elided]…
TA OVERWRITE TEMP mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\')','LOAD DATA INPATH \\'x\\' INTO TABLE y']:\n    print(sqlglot.transpile(s, read='bigquery', write='bigquery')[0])\n\" ; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -15", "description": "Add TEMP test case, check outputs, run full test suite"}
[tool_result] LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
LOAD DATA OVERWRITE TEMP mydataset.table1 FROM FILES(FORMAT='AVRO')
LOAD DATA INPATH 'x' INTO TABLE y
............................................................................................................................................................................................................................................... [ 21%]
.................................... [ 24%]
......................................
…[447 chars elided]…
............................................................................................. [ 73%]
............................................. [ 77%]
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 50.74s
[tool_use Bash] {"command": "(<work>/env-sqlglot/bin/python -m ruff check sqlglot tests/dialects/test_bigquery.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot tests/dialects/test_bigquery.py) 2>&1 | tail -5; git diff", "description": "Run ruff lint and format checks on changed files"}
[tool_result] All checks passed!
177 files already formatted
diff --git a/sqlglot/expressions/dml.py b/sqlglot/expressions/dml.py
index 1305f77d5..856e28f23 100644
--- a/sqlglot/expressions/dml.py
+++ b/sqlglot/expressions/dml.py
@@ -283,6 +283,7 @@ class LoadData(Expression):
         "this": True,
         "local": False,
         "overwrite": False,
+        "temporary": False,
         "inpath": False,
         "files": False,
         "partition": False,
diff --git a/sqlglot/generator.py b/sqlglot/genera
…[2489 chars elided]…
       "LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
             "LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
+            "LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
         ):
             with self.subTest(load_data_sql=load_data_sql):
                 self.validate_identity(load_data_sql).assert_is(exp.LoadData)
[assistant] The diff has a regression risk: `OVERWRITE INTO TABLE x` previously parsed (via `_match_pair`), but my `if not overwrite` skips INTO in that case. I'll match INTO unconditionally and verify.
[tool_use Bash] {"command": "python3 - <<'EOF'\np='sqlglot/parser.py'\ns=open(p).read()\nold='''            if not overwrite:\n                self._match(TokenType.INTO)\n            temporary = self._match(TokenType.TEMPORARY)\n'''\nnew='''            self._match(TokenType.INTO)\n            temporary = self._match(TokenType.TEMPORARY)\n'''\nassert s.count(old)==1\nopen(p,'w').write(s.replace(old,new))\nEOF\nP=
…[326 chars elided]…
\')','LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\')','LOAD DATA INPATH \\'x\\' INTO TABLE y']:\n    print(sqlglot.transpile(s, read='bigquery', write='bigquery')[0])\n\"; $P -m pytest -q -p no:cacheprovider --color=no tests/ 2>&1 | tail -2; $P -m ruff check sqlglot tests/dialects/test_bigquery.py | tail -1", "description": "Recheck parsing edge cases and rerun tests and lint"}
[tool_result] LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO')
LOAD DATA OVERWRITE t FROM FILES(FORMAT='AVRO')
LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO')
LOAD DATA INPATH 'x' INTO TABLE y
......................................................................................................................................................................................................................................................                                                 [100%]
1112 passed, 18136 subtests passed in 58.48s
All checks passed!
[assistant] `LOAD DATA INTO TEMP TABLE` and `INTO TEMPORARY TABLE` now parse, and all three forms from your request round-trip in BigQuery. The full test suite passes (1112 tests, 18136 subtests) and ruff is clean.

The change touches three places:

- **Parser** (`sqlglot/parser.py`, `_parse_load`): `INTO` is matched on its own, then an optional `TEMP`/`TEMPORARY` (both tokenize to the same token), then an optional `TABLE`. Previously it required `INTO TABLE` as a pair, which is why `INTO TEMP TABLE` failed.
- **Expression** (`sqlglot/expressions/dml.py`): `LoadData` gets a `temporary` arg.
- **Generator*
…[288 chars elided]…
es but is written back as `TEMP`, so it is a normalizing round-trip rather than an exact identity.
- `OVERWRITE` combined with temp emits `LOAD DATA OVERWRITE TEMP table ...` (no `TABLE` keyword, matching the existing overwrite form). I'm not certain BigQuery accepts that combination, so tell me if you'd rather it be rejected.
- The Hive-style `INPATH ... INTO TABLE` branch also honours the temp flag, so the flag is never silently dropped.
- `INTO` is now optional in the parser, so `LOAD DATA TABLE x` is accepted too. This is looser than before for the Hive path.

I haven't committed anything.
