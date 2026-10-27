# trajectory base-1

final message:
The full suite passes: 1112 tests and 18136 subtests, exit code 0. That covers the change in the last turn.

Your three `LOAD DATA` statements (OVERWRITE, INTO TABLE, INTO TEMP TABLE) all round-trip on BigQuery.

Still open from before:
- `TEMPORARY` is accepted but written back as `TEMP`. Say if you want the original keyword kept.
- `TEMP` is only parsed after `INTO`, not after `OVERWRITE`, since I wasn't sure BigQuery allows that form.

I haven't committed anything.

## events
[tool_use Skill] {"skill": "sqlglot-syntax-support"}
[tool_result] Launching skill: sqlglot-syntax-support
[user] Base directory for this skill: ~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/.claude/skills/sqlglot-syntax-support

# Adding or fixing syntax support in sqlglot

## Contract: a syntax change touches three places that must agree
1. **Node** — the `exp.<Node>` class in `sqlglot/expressions/*.py`. New information goes in
   `arg_types` (optional args `False`). Prefer reusing an existing wrapper node over adding a flag.
2. **Parser** — a `_parse_*` method in `sqlglot/parser.py` (base) or `sqlglot/parsers/<dialect>.py`.
   Build nodes w
…[2311 chars elided]…
r is dialect-controlled: `Dialect.ON_CONDITION_EMPTY_BEFORE_ERROR`
  (Oracle sets `False`); use `_parse_on_handling` / `_parse_on_condition`, not ad-hoc matching.

## When the quoted example already works
If the literal example in the task already parses and round-trips, the requested feature is not
"done": find the form of the same construct and clause that still fails (the "incomplete" notes
above are the known gaps) and implement it, with a `validate_identity` test next to the existing ones. A no-change
deliverable must be justified by evidence that every form of the named construct works.

[tool_use Bash] {"command": "grep -rn -i \"LOAD DATA\\|LOAD_DATA\\|\\\"LOAD\\\"\\|LoadData\" sqlglot/ tests/ | head -50", "description": "Search codebase for LOAD DATA handling"}
[tool_result] sqlglot/generator.py:2895:    def loaddata_sql(self, expression: exp.LoadData) -> str:
sqlglot/generator.py:2905:            return f"LOAD DATA{overwrite}{this} FROM {files_sql}"
sqlglot/generator.py:2916:        return f"LOAD DATA{local}{inpath}{overwrite}{this}{partition}{input_format}{serde}"
sqlglot/tokens.py:329:        "LOAD": TokenType.LOAD,
sqlglot/parser.py:3589:    def _parse_load(self) -> exp.LoadData | exp.Command:
sqlglot/parser.py:3598:                exp.LoadData(
sqlglot/expressi
…[990 chars elided]…
es/identity.sql:710:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy')
tests/fixtures/identity.sql:711:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y'
tests/fixtures/identity.sql:712:LOAD DATA LOCAL INPATH 'x' INTO TABLE y PARTITION(ds = 'yyyy') INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:713:LOAD DATA INPATH 'x' INTO TABLE y INPUTFORMAT 'y' SERDE 'z'
tests/fixtures/identity.sql:714:LOAD DATA INPATH 'x' INTO TABLE y.b INPUTFORMAT 'y' SERDE 'z'
[assistant] Continuing with the code. The `LOAD DATA` parser and generator are the starting point.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "offset": 3585, "limit": 40}
[tool_result] 3585	            kwargs["null"] = self._parse_string()
3586	
3587	        return self.expression(exp.RowFormatDelimitedProperty(**kwargs))  # type: ignore
3588	
3589	    def _parse_load(self) -> exp.LoadData | exp.Command:
3590	        if self._match_text_seq("DATA"):
3591	            local = self._match_text_seq("LOCAL")
3592	            self._match_text_seq("INPATH")
3593	            inpath = self._parse_string()
3594	            overwrite = self._match(TokenType.OVERWRITE)
3595	            se
…[832 chars elided]…
   def _parse_delete(self) -> exp.Delete:
3613	        hint = self._parse_hint()
3614	
3615	        # This handles MySQL's "Multiple-Table Syntax"
3616	        # https://dev.mysql.com/doc/refman/8.0/en/delete.html
3617	        tables = None
3618	        if not self._match(TokenType.FROM, advance=False):
3619	            tables = self._parse_csv(self._parse_table) or None
3620	
3621	        returning = self._parse_returning()
3622	
3623	        return self.expression(
3624	            exp.Delete(
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "offset": 2893, "limit": 26}
[tool_result] 2893	        return self._replace_line_breaks(text).replace(delimiter, escaped_delimiter)
2894	
2895	    def loaddata_sql(self, expression: exp.LoadData) -> str:
2896	        is_overwrite = expression.args.get("overwrite")
2897	        overwrite = " OVERWRITE" if is_overwrite else ""
2898	        this = self.sql(expression, "this")
2899	
2900	        files = expression.args.get("files")
2901	        if files:
2902	            files_sql = self.expressions(files, flat=True)
2903	            files_
…[388 chars elided]…
tion = self.sql(expression, "partition")
2911	        partition = f" {partition}" if partition else ""
2912	        input_format = self.sql(expression, "input_format")
2913	        input_format = f" INPUTFORMAT {input_format}" if input_format else ""
2914	        serde = self.sql(expression, "serde")
2915	        serde = f" SERDE {serde}" if serde else ""
2916	        return f"LOAD DATA{local}{inpath}{overwrite}{this}{partition}{input_format}{serde}"
2917	
2918	    def null_sql(self, *_) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "offset": 278, "limit": 12}
[tool_result] 278	    arg_types = {"expressions": True, "into": False}
279	
280	
281	class LoadData(Expression):
282	    arg_types = {
283	        "this": True,
284	        "local": False,
285	        "overwrite": False,
286	        "inpath": False,
287	        "files": False,
288	        "partition": False,
289	        "input_format": False,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "offset": 214, "limit": 12}
[tool_result] 214	        self.validate_identity("BEGIN TRANSACTION")
215	        self.validate_identity("COMMIT TRANSACTION")
216	        self.validate_identity("ROLLBACK TRANSACTION")
217	        for load_data_sql in (
218	            "LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
219	            "LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])",
220	        ):
221	            with self.subTest(load_data_sql=load_data_sql):
222	                self.validate_identity(load_data_sql).assert_is(exp.LoadData)
223	        self.validate_identity("CAST(x AS BIGNUMERIC)")
224	        self.validate_identity("SELECT y + 1 FROM x GROUP BY y + 1 ORDER BY 1")
225	        self.validate_identity("SELECT TIMESTAMP_SECONDS(2) AS t")
[assistant] The gap is clear: `LoadData` has no `temporary` flag, and the parser only consumes `INTO TABLE`, so `INTO TEMP TABLE` fails. I'll confirm the helper semantics before editing.
[tool_use Bash] {"command": "grep -n \"def _match_texts\" -A 8 sqlglot/parser.py && sed -n 281,295p sqlglot/expressions/dml.py && grep -n \"TEMP\\b\\|\\\"TEMP\\\"\\|TEMPORARY\" sqlglot/tokens.py | head", "description": "Check _match_texts helper and TEMP token handling"}
[tool_result] 1943:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1944-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1945-            if advance:
1946-                self._advance()
1947-            return True
1948-        return False
1949-
1950-    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1951-        index = self._index
class LoadData(Expression):
    arg_types = {
        "this": True,
        "local": False,
        "overwrite": False,
        "inpath": False,
        "files": False,
        "partition": False,
        "input_format": False,
        "serde": False,
    }


class Update(Expression, DML):
    arg_types = {
392:        "TEMP": TokenType.TEMPORARY,
393:        "TEMPORARY": TokenType.TEMPORARY,
[assistant] `_match_texts` matches on text, so both `TEMP` and `TEMPORARY` will be caught. Making the three edits: the node flag, the parser, and the generator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py", "old_string": "        \"overwrite\": False,\n        \"inpath\": False,\n        \"files\": False,", "new_string": "        \"overwrite\": False,\n        \"temporary\": False,\n        \"inpath\": False,\n        \"files\": False,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/expressions/dml.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py", "old_string": "            overwrite = self._match(TokenType.OVERWRITE)\n            self._match_pair(TokenType.INTO, TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=sel
…[218 chars elided]…
     if self._match(TokenType.INTO):\n                temporary = self._match_texts((\"TEMP\", \"TEMPORARY\"))\n            self._match(TokenType.TABLE)\n\n            return self.expression(\n                exp.LoadData(\n                    this=self._parse_table(schema=True),\n                    local=local,\n                    overwrite=overwrite,\n                    temporary=temporary,"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py", "old_string": "        overwrite = \" OVERWRITE\" if is_overwrite else \"\"\n        this = self.sql(expression, \"this\")\n\n        files = expression.args.get(\"files\")\n        if files:\n            files_sql = self.expressio
…[743 chars elided]…
       files_sql = f\"FILES{self.wrap(files_sql)}\"\n            this = f\" {this}\" if is_overwrite else f\" INTO {temporary}TABLE {this}\"\n            return f\"LOAD DATA{overwrite}{this} FROM {files_sql}\"\n\n        local = \" LOCAL\" if expression.args.get(\"local\") else \"\"\n        inpath = f\" INPATH {self.sql(expression, 'inpath')}\"\n        this = f\" INTO {temporary}TABLE {this}\""}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/sqlglot/generator.py has been updated successfully.
[assistant] Now the tests. I'll add the `TEMP` form as an identity round-trip, and `TEMPORARY` with `TEMP` as its canonical output.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py", "old_string": "            \"LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ):\n            with self.subTest(load_data_sql=load_data_sql):\n             
…[398 chars elided]…
                self.validate_identity(load_data_sql).assert_is(exp.LoadData)\n        self.validate_identity(\n            \"LOAD DATA INTO TEMPORARY TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n            \"LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://bucket/path/file.avro'])\",\n        ).assert_is(exp.LoadData)"}
[tool_result] The file ~/.cache/lithify/work/repo-161bf5b46800/20261027-061429-bigquery-dialect-support-load-da/base-1/tests/dialects/test_bigquery.py has been updated successfully.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_bigquery.py tests/dialects/test_hive.py tests/dialects/test_mysql.py tests/test_transpile.py tests/test_parser.py 2>&1 | tail -15", "description": "Run BigQuery and related dialect tests"}
[tool_result] .................................................................... [ 31%]
.......................................................................................... [ 72%]
...........................................................                                       [100%]
217 passed, 3129 subtests passed in 10.29s
[assistant] Targeted tests pass. Running the full suite with the project's check command, plus a direct round-trip of the three examples from the request.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -c \"\nimport sqlglot\nfor s in ['LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])']:\n    out = sqlglot.transpile(s, read='bigquery', write='bigquery')[0]\n    print(out == s, out)\n\"", "description": "Run full test suite and check the three examples"}
[tool_result] Command did not complete within its 120s timeout and was moved to the background (ID: bo7qvl4zi). Output is being written to: /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output. You will be notified when it completes. If it is still running after 10m in the background, it will be stopped and you will be notified. It is running now: do not start a second copy while it runs. If it is no longer needed, stop it with TaskStop. No output had been read from it when it was moved. A program that buffers its output, or a pipe into one such as tail, can keep the output file empty until the command finishes. To check interim output, use Read on that file path.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])','LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT=\\'AVRO\\', uris=[\\'gs://b/f.avro\\'])']:\n    out = sqlglot.transpile(s, read='bigquery', write='bigquery')[0]\n    print(out == s, out)\n\"", "description": "Round-trip the three example statements"}
[tool_result] True LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
True LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
True LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
[tool_use Bash] {"command": "sleep 100; cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output | tail -8", "description": "Check background full test run output"}
[tool_result ERROR] <tool_use_error>Blocked: sleep 100 followed by: cat /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output tail -8. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output"}
[tool_result] <system-reminder>Warning: the file exists but the contents are empty.</system-reminder>
[tool_use Monitor] {"description": "Wait for full test suite to finish", "command": "until grep -q -E \"passed|failed|error\" /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output 2>/dev/null; do sleep 5; done; tail -5 /private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output", "timeout": "600000"}
[tool_result] Monitor started (task b0l5qcg2a, expires in 5m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[tool_use Monitor] {"description": "Wait for full test suite result", "command": "sleep 1; echo waiting", "timeout": "5000"}
[tool_result] Monitor started (task bgs07dl4f, expires in 5m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
[assistant] The `LOAD DATA` fix is in place and the targeted tests pass. The full suite is still running in the background, so I'm not yet calling the change fully verified.

**Change**

- `sqlglot/expressions/dml.py`: `LoadData` gets an optional `temporary` arg.
- `sqlglot/parser.py` (`_parse_load`): after `INTO`, it accepts `TEMP` or `TEMPORARY` before `TABLE`. This replaces the old `_match_pair(INTO, TABLE)`, which is why `INTO TEMP TABLE` failed.
- `sqlglot/generator.py` (`loaddata_sql`): emits `TEMP ` before `TABLE` in both the `FROM FILES(...)` and the Hive-style branches.
- `tests/dialects/test_big
…[299 chars elided]…
.py`, `test_transpile.py` and `test_parser.py`: 217 tests and 3129 subtests pass.
- The full suite (`python -m pytest -q -p no:cacheprovider --color=no`) exceeded the 120s limit and was moved to background task `bo7qvl4zi`. Its output file is still empty, so I don't have a result yet.

**Choices I made**

- `TEMPORARY` is accepted but written back as `TEMP`. Only one keyword is stored, so the original spelling isn't preserved. Tell me if you want the exact keyword kept.
- `TEMP` is only supported after `INTO`. I didn't add `LOAD DATA OVERWRITE TEMP ...`, since I wasn't sure BigQuery allows it.
[assistant] That notification is from my placeholder monitor, not the test run. The full suite is still `bo7qvl4zi`, so I'll check its output.
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output"}
[tool_result] <system-reminder>Warning: the file exists but the contents are empty.</system-reminder>
[tool_use Bash] {"command": "pgrep -fl \"pytest -q -p no:cacheprovider\" | head -5", "description": "Check whether the full pytest run is still alive"}
[tool_result] 34204 /bin/zsh -c source ~/.claude/shell-snapshots/snapshot-zsh-1792775860252-0z2ieb.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin unalias -- 'unsetenv'; \builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'PY=/private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacity/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no > 
…[716 chars elided]…
a/scratchpad/hwork/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; $PY -c "
import sqlglot
for s in ['"'"'LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT=\'"'"'AVRO\'"'"', uris=[\'"'"'gs://b/f.avro\'"'"'])'"'"','"'"'LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT=\'"'"'AVRO\'"'"', uris=[\'"'"'gs://b/f.avro\'"'"'])'"'"','"'"'LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT=\'"'"'AVRO\'"'"', uris=[\'"'"'gs://b/f.avro\'"'"'])'"'"']:
[tool_use Bash] {"command": "pgrep -fl \"f0ecd001.*python -m pytest\" ; echo \"---\"; ps -o pid,etime,command -p $(pgrep -f \"f0ecd001.*env-sqlglot/bin/python -m pytest\" | head -1) 2>/dev/null | cut -c1-160", "description": "Check whether my sqlglot pytest process is still running"}
[tool_result] ---
[tool_use Read] {"file_path": "/private/tmp/claude-501/-Users-user--cache-lithify-work-repo-161bf5b46800-20261027-061429-bigquery-dialect-support-load-da-base-1/abe30bdb-1da4-4c61-8fda-7e92eaa9d4f2/tasks/bo7qvl4zi.output"}
[tool_result] 1	................ [ 53%]
2	............................................................................................................................................................................................................................. [ 73%]
3	............................................. [ 77%]
4	......................................................................................................................................................................................................................................................                                                 [100%]
5	1112 passed, 18136 subtests passed in 48.65s
6	True LOAD DATA OVERWRITE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
7	True LOAD DATA INTO TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
8	True LOAD DATA INTO TEMP TABLE mydataset.table1 FROM FILES(FORMAT='AVRO', uris=['gs://b/f.avro'])
9	
10	[exited with code 0]
11	
[assistant] The full suite passes: 1112 tests and 18136 subtests, exit code 0. That covers the change in the last turn.

Your three `LOAD DATA` statements (OVERWRITE, INTO TABLE, INTO TEMP TABLE) all round-trip on BigQuery.

Still open from before:
- `TEMPORARY` is accepted but written back as `TEMP`. Say if you want the original keyword kept.
- `TEMP` is only parsed after `INTO`, not after `OVERWRITE`, since I wasn't sure BigQuery allows that form.

I haven't committed anything.
