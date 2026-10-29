# trajectory base-1

final message:
`UNDROP` now parses and generates for all twelve Snowflake object types, including the `IDENTIFIER(...)` form. The full suite passes: 1121 tests, 18188 subtests.

**Before:** every `UNDROP <type> <name>` raised `ParseError`. `UNDROP ACCOUNT` was worse: it silently parsed as `SELECT UNDROP AS ACCOUNT`.

**After:** each form round-trips in the Snowflake dialect, e.g. `undrop table db.s.t` → `UNDROP TABLE db.s.t`, and `UNDROP TABLE IDENTIFIER('"1234567"')` is preserved as written.

Changes:
- `sqlglot/tokenizer_core.py`: new `TokenType.UNDROP`.
- `sqlglot/parser.py`: `UNDROP` added to `ID_VAR_TOKENS`, so it still works as an identifier (`SELECT undrop FROM t` is unchanged).
- `sqlglot/dialects/snowflake.py`: `UNDROP` keyword mapped to the new token.
- `sqlglot/parsers/snowflake.py`: `_parse_undrop` and `UNDROP_KINDS`. Multi-word kinds (`DYNAMIC TABLE`, `EXTERNAL VOLUME`, `ICEBERG TABLE`) are matched as sequences. Unknown kinds fall back to `Command`.
- `sqlglot/expressions/ddl.py`: new `exp.Undrop` expression with `this` and `kind`.
- `sqlglot/generators/snowflake.py`: `undrop_sql`.
- `tests/dialects/test_snowflake.py`: `test_undrop` covers all kinds, the `IDENTIFIER` form, and lowercase input.

Design choice: the object name is parsed with the existing `_parse_table_parts`, so dotted names and `IDENTIFIER(...)` work without special-casing.

Not verified: I had no live Snowflake account, so the test SQL is checked only by parse and round-trip, not executed against Snowflake. The exact `IDENTIFIER` literal shape for restore-by-ID should be confirmed against a real account. I haven't committed anything.

## events
[assistant] I'll start by checking how the Snowflake dialect currently handles `DROP` and `UNDROP`, and whether the probe script exists.
[tool_use Bash] {"command": "grep -rn -i \"undrop\" sqlglot/ tests/ | head -50; ls .lithify/harness/scripts/ 2>/dev/null; ls .claude/skills 2>/dev/null", "description": "Search for UNDROP references and harness files"}
[tool_result] probe_parse.py  2.2K
parse-failure-triage/
[tool_use Bash] {"command": "grep -n \"UNDROP\\|\\\"DROP\\\"\\|TokenType.DROP\\|_parse_drop\\|def _parse_drop\\|STATEMENT_PARSERS\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head -40; grep -n \"class Drop\\|class Undrop\" sqlglot/expressions/*.py sqlglot/*.py 2>/dev/null", "description": "Locate DROP parsing and Drop expression class"}
[tool_result] 15 matches in 1 files:

sqlglot/parser.py:1082:STATEMENT_PARSERS: t.ClassVar = {
sqlglot/parser.py:1094:TokenType.DROP: lambda self: self._parse_drop(),
sqlglot/parser.py:1442:"DROP": lambda self: self._parse_alter_table_drop(),
sqlglot/parser.py:1734:"DROP": lambda self: self._parse_analyze_histogram(),
sqlglot/parser.py:2278:if self._match_set(self.STATEMENT_PARSERS):
sqlglot/parser.py:2280:stmt = self.STATEMENT_PARSERS[self._prev.token_type](self)
sqlglot/parser.py:2298:def _parse_drop(self, 
…[430 chars elided]…
 | None = None) -> exp.DropPartit...
sqlglot/parser.py:8772:if self._match_pair(TokenType.DROP, TokenType.DEFAULT):
sqlglot/parser.py:8778:if self._match_text_seq("DROP", "NOT", "NULL"):
sqlglot/parser.py:8825:return self._parse_csv(lambda: self._parse_drop_partition(exists=partition_ex...
3 matches in 2 files:

sqlglot/expressions/ddl.py:345:class Drop(Expression):
sqlglot/expressions/ddl.py:369:class DropPrimaryKey(Expression):
sqlglot/expressions/query.py:1949:class DropPartition(Expression):
[tool_use Bash] {"command": "sed -n 340,370p sqlglot/expressions/ddl.py; sed -n 2295,2400p sqlglot/parser.py; cat .lithify/harness/scripts/probe_parse.py | head -40; ls .claude/skills/parse-failure-triage/", "description": "Read Drop expression and _parse_drop implementation"}
[tool_result]         "group": False,
        "aggregates": False,
    }


class Drop(Expression):
    arg_types = {
        "this": False,
        "kind": False,
        "expressions": False,
        "exists": False,
        "temporary": False,
        "materialized": False,
        "cascade": False,
        "restrict": False,
        "constraints": False,
        "purge": False,
        "cluster": False,
        "concurrently": False,
        "sync": False,
        "iceberg": False,
    }

    @property
   
…[4941 chars elided]…
       out = sqlglot.transpile(sql, read=read, write=write)[0]
    except Exception as e:
        return "ERR", f"{type(e).__name__}: {str(e).splitlines()[0]}"

    try:
        again = sqlglot.transpile(out, read=write, write=write)[0]
    except Exception as e:
        return "ERR", f"output does not re-parse: {type(e).__name__}: {str(e).splitlines()[0]}"

    if again != out:
        return "UNSTABLE", f"{out}\n           -> {again}"

    return "OK", out

.lithify-managed  24B
SKILL.md  1.8K
[assistant] Next I'll probe the current behaviour for each object type, using the project's interpreter and probe script.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat <<'EOF' | $PY -I .lithify/harness/scripts/probe_parse.py --read snowflake\nUNDROP TABLE t\nUNDROP TABLE db.s.t\nUNDROP SCHEMA s\nUNDROP DATABASE d\nUNDROP ACCOUNT\nUNDROP NOTEBOOK nb\nUNDROP SNAPSHOT snap\nUNDROP STREAMLIT st\nUNDROP TAG tg\nUNDROP TYPE ty\nUNDROP DYNAMIC TABLE dt\nUNDROP EXTERNAL VOLUME ev\nUNDROP ICEBERG TABLE it\nUNDROP TABLE IDENTIFIER('\"1234567\"')\nUNDROP TABLE IDENTIFIER($id)\nDROP TABLE t\nDROP DYNAMIC TABLE dt\nEOF\ngrep -n \"CREATABLES\\|CREATABLE_KIND_MAPPING\" -A4 sqlglot/dialects/snowflake.py sqlglot/dialects/dialect.py | head -40", "description": "Probe current UNDROP and DROP behavior in Snowflake"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
sqlglot/dialects/dialect.py:247:        klass.INVERSE_CREATABLE_KIND_MAPPING = {
sqlglot/dialects/dialect.py:248:            v: k for k, v in klass.CREATABLE_KIND_MAPPING.items()
sqlglot/dialects/dialect.py-249-        
…[406 chars elided]…
me for the same creatable kind. For example, the Clickhouse
sqlglot/dialects/dialect.py-693-    equivalent of CREATE SCHEMA is CREATE DATABASE.
sqlglot/dialects/dialect.py-694-    """
--
sqlglot/dialects/dialect.py:780:    INVERSE_CREATABLE_KIND_MAPPING: dict[str, str] = {}
sqlglot/dialects/dialect.py-781-
sqlglot/dialects/dialect.py-782-    ESCAPED_SEQUENCES: dict[str, str] = {}
sqlglot/dialects/dialect.py-783-
sqlglot/dialects/dialect.py-784-    # Delimiters for string literals and identifiers
[assistant] The `-I` flag drops the working directory from `sys.path`, so I'll pass the repo via `PYTHONPATH`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; export PYTHONPATH=$PWD; cat <<'EOF' | $PY -I .lithify/harness/scripts/probe_parse.py --read snowflake\nUNDROP TABLE t\nUNDROP TABLE db.s.t\nUNDROP SCHEMA s\nUNDROP DATABASE d\nUNDROP ACCOUNT\nUNDROP NOTEBOOK nb\nUNDROP SNAPSHOT snap\nUNDROP STREAMLIT st\nUNDROP TAG tg\nUNDROP TYPE ty\nUNDROP DYNAMIC TABLE dt
…[24 chars elided]…
 ev\nUNDROP ICEBERG TABLE it\nUNDROP TABLE IDENTIFIER('\"1234567\"')\nUNDROP TABLE IDENTIFIER($id)\nDROP TABLE t\nDROP DYNAMIC TABLE dt\nEOF\n$PY -I -c \"import sys; sys.path.insert(0,'.'); import sqlglot; print(sqlglot.__file__)\"; grep -n \"CREATABLE_KIND_MAPPING\\|CREATABLES\" sqlglot/dialects/snowflake.py sqlglot/parser.py | head", "description": "Probe UNDROP with PYTHONPATH set to the repo"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/__init__.py
sqlglot/parser.py:619:    DB_CREATABLES: t.ClassVar = {
sqlglot/parser.py:639:    CREATABL
…[160 chars elided]…
t(self.CREATABLES) and self._prev
sqlglot/parser.py:2304:        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
sqlglot/parser.py:2330:                kind=self.dialect.CREATABLE_KIND_MAPPING.get(kind) or kind,
sqlglot/parser.py:2377:        create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2382:            create_token = self._match_set(self.CREATABLES) and self._prev
sqlglot/parser.py:2538:        elif create_token_type in self.DB_CREATABLES:
[assistant] `-I` ignores `PYTHONPATH` as well, so I'll run the probe without `-I`. It's the repo's own script, not an untrusted file.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat <<'EOF' | $PY .lithify/harness/scripts/probe_parse.py --read snowflake\nUNDROP TABLE t\nUNDROP TABLE db.s.t\nUNDROP SCHEMA s\nUNDROP DATABASE d\nUNDROP ACCOUNT\nUNDROP NOTEBOOK nb\nUNDROP SNAPSHOT snap\nUNDROP STREAMLIT st\nUNDROP TAG tg\nUNDROP TYPE ty\nUNDROP DYNAMIC TABLE dt\nUNDROP EXTERNAL VOLUME ev\nUNDROP ICEBERG TABLE it\nUNDROP TABLE IDENTIFIER('\"1234567\"')\nUNDROP TABLE IDENTIFIER($id)\nDROP TABLE t\nDROP DYNAMIC TABLE dt\nEOF", "description": "Probe UNDROP statements against the Snowflake dialect"}
[tool_result ERROR] Exit code 1
Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
[assistant] The script's own directory goes on `sys.path`, not the working directory, so I'll set `PYTHONPATH` explicitly without `-I`.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat <<'EOF' | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read snowflake\nUNDROP TABLE t\nUNDROP TABLE db.s.t\nUNDROP SCHEMA s\nUNDROP DATABASE d\nUNDROP ACCOUNT\nUNDROP NOTEBOOK nb\nUNDROP SNAPSHOT snap\nUNDROP STREAMLIT st\nUNDROP TAG tg\nUNDROP TYPE ty\nUNDROP DYNAMIC TABLE dt\nUNDROP EXTERNAL VOLUME ev\nUNDROP ICEBERG TABLE it\nUNDROP TABLE IDENTIFIER('\"1234567\"')\nUNDROP TABLE IDENTIFIER($id)\nDROP TABLE t\nDROP DYNAMIC TABLE dt\nEOF", "description": "Probe UNDROP statements with repo on PYTHONPATH"}
[tool_result ERROR] Exit code 1
'DROP DYNAMIC TABLE dt' contains unsupported syntax. Falling back to parsing as a 'Command'.
'DROP DYNAMIC TABLE dt' contains unsupported syntax. Falling back to parsing as a 'Command'.
ERR       UNDROP TABLE t
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 14.
ERR       UNDROP TABLE db.s.t
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 15.
ERR       UNDROP SCHEMA s
          ParseError: Invalid expression / Unexpected token. Line
…[890 chars elided]…
/ Unexpected token. Line 1, Col: 22.
ERR       UNDROP ICEBERG TABLE it
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 20.
ERR       UNDROP TABLE IDENTIFIER('"1234567"')
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 23.
ERR       UNDROP TABLE IDENTIFIER($id)
          ParseError: Invalid expression / Unexpected token. Line 1, Col: 23.
OK        DROP TABLE t
          DROP TABLE t
OK        DROP DYNAMIC TABLE dt
          DROP DYNAMIC TABLE dt
[assistant] Current behaviour: every `UNDROP` form fails, and `UNDROP ACCOUNT` silently mis-parses as `SELECT UNDROP AS ACCOUNT`. I'll check how Snowflake handles similar statement keywords and `IDENTIFIER(...)`, so the fix follows existing patterns.
[tool_use Bash] {"command": "grep -n \"STATEMENT_PARSERS\\|IDENTIFIER\\|\\\"UNDROP\\|UNDROP\\|TokenType.COMMAND\\|\\\"ANALYZE\\|\\\"COPY\\|\\\"LIST\\\"\\|\\\"REMOVE\\\"\\|\\\"PUT\\\"\" sqlglot/dialects/snowflake.py | head -60; grep -n \"_parse_table_parts\\b\" sqlglot/parser.py | head -3; grep -n \"\\\"IDENTIFIER\\\"\" sqlglot/parser.py sqlglot/dialects/*.py | head", "description": "Find Snowflake statement parsers and IDENTIFIER handling"}
[tool_result] 3 matches in 3 files:

154:0:TokenType.PUT,
155:0:TokenType.COMMAND,
156:0:TokenType.COMMAND,
24 matches in 2 files:

1073:0:lambda self: self._parse_table_parts(),
0 matches for '"IDENTIFIER"'
[assistant] The grep output is being summarised oddly, so I'll read the relevant parts of `snowflake.py` directly.
[tool_use Bash] {"command": "grep -n \"class \\|STATEMENT\\|IDENTIFIER\\|UNDROP\\|COMMAND\\|def _parse_\" sqlglot/dialects/snowflake.py | head -120", "description": "List Snowflake dialect classes and parser hooks"}
[tool_result] 6 matches in 6 files:

127:0:
133:0:
155:0:TokenType.COMMAND,
156:0:TokenType.COMMAND,
16:0:
sqlglot/dialects/snowflake.py:185:COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
[assistant] The shell grep wrapper is mangling results, so I'll read the file with the Read tool.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "offset": 100, "limit": 200}
[tool_result] 100	    }
101	
102	    DATE_PART_MAPPING = {
103	        **Dialect.DATE_PART_MAPPING,
104	        "ISOWEEK": "WEEKISO",
105	        # The base Dialect maps EPOCH_SECOND -> EPOCH, but we need to preserve
106	        # EPOCH_SECOND as a distinct value for two reasons:
107	        # 1. Type annotation: EPOCH_SECOND returns BIGINT, while EPOCH returns DOUBLE
108	        # 2. Transpilation: DuckDB's EPOCH() returns float, so we cast EPOCH_SECOND
109	        #    to BIGINT to match Snowflake's integer
…[2854 chars elided]…

172	            # FLOAT is a synonym for DOUBLE in Snowflake
173	            "FLOAT": TokenType.DOUBLE,
174	        }
175	        KEYWORDS.pop("/*+")
176	
177	        SINGLE_TOKENS = {
178	            **tokens.Tokenizer.SINGLE_TOKENS,
179	            "$": TokenType.PARAMETER,
180	            "!": TokenType.EXCLAMATION,
181	        }
182	
183	        VAR_SINGLE_TOKENS = {"$"}
184	
185	        COMMANDS = tokens.Tokenizer.COMMANDS - {TokenType.SHOW}
186	
187	    Generator = SnowflakeGenerator
188	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "offset": 1, "limit": 99}
[tool_result] 1	from __future__ import annotations
2	
3	from sqlglot import exp, jsonpath, tokens
4	from sqlglot.dialects.dialect import (
5	    Dialect,
6	    NormalizationStrategy,
7	)
8	from sqlglot.generators.snowflake import SnowflakeGenerator
9	from sqlglot.parsers.snowflake import (
10	    SnowflakeParser,
11	)
12	from sqlglot.tokens import TokenType
13	from sqlglot.typing.snowflake import EXPRESSION_METADATA
14	
15	
16	class Snowflake(Dialect):
17	    # https://docs.snowflake.com/en/sql-reference/iden
…[2404 chars elided]…
",  # internal representation for ±HH:MM
90	        "tzh:tzm": "%:z",
91	        "TZH": "%-z",  # internal representation ±HH
92	        "tzh": "%-z",
93	        '"T"': "T",  # remove the optional double quotes around the separator between the date and time
94	        # Seems like Snowflake treats AM/PM in the format string as equivalent,
95	        # only the time (stamp) value's AM/PM affects the output
96	        "AM": "%p",
97	        "am": "%p",
98	        "PM": "%p",
99	        "pm": "%p",
[assistant] The parser and generator live in `sqlglot/parsers/snowflake.py` and `sqlglot/generators/snowflake.py`. I'll look at the statement hooks there.
[tool_use Bash] {"command": "wc -l sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py && python3 - <<'EOF'\nimport re\nfor f in [\"sqlglot/parsers/snowflake.py\"]:\n    for i,l in enumerate(open(f),1):\n        if re.search(r\"STATEMENT|IDENTIFIER|COMMAND|PUT|GET|SHOW|_parse_drop|DROP|Drop|def _parse_table_parts|TABLE_PARTS\", l):\n            print(i, l.rstrip())\nEOF", "description": "Find statement and DROP hooks in Snowflake parser"}
[tool_result]     1365 sqlglot/parsers/snowflake.py
    1163 sqlglot/generators/snowflake.py
    2528 total
524         "GET": exp.GetExtract.from_arg_list,
525         "GETDATE": exp.CurrentTimestamp.from_arg_list,
526         "GET_PATH": lambda args, dialect: exp.JSONExtract(
758     STATEMENT_PARSERS = {
759         **parser.Parser.STATEMENT_PARSERS,
760         TokenType.GET: lambda self: self._parse_get(),
761         TokenType.PUT: lambda self: self._parse_put(),
762         TokenType.SHOW: lambda self:
…[63 chars elided]…
xpression(exp.ComputeProperty()),
814     SHOW_PARSERS = {
846     SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
992         # GET_DDL outputs #unknown_policy when the user lacks privileges to see the policy name
1054     def _parse_table_parts(
1129         if self._match_text_seq("IDENTIFIER", "("):
1134             return self.expression(exp.Anonymous(this="IDENTIFIER", expressions=[identifier]))
1199         # If we detect GET( then we need to parse a function, not a statement
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "offset": 750, "limit": 70}
[tool_result] 750	            exp.Set(
751	                tag=self._match_text_seq("TAG"),
752	                expressions=self._parse_csv(self._parse_id_var),
753	                unset=True,
754	            )
755	        ),
756	    }
757	
758	    STATEMENT_PARSERS = {
759	        **parser.Parser.STATEMENT_PARSERS,
760	        TokenType.GET: lambda self: self._parse_get(),
761	        TokenType.PUT: lambda self: self._parse_put(),
762	        TokenType.SHOW: lambda self: self._parse_show(),
763	    }
764	
76
…[2232 chars elided]…
06	        ),
807	    }
808	
809	    TYPE_CONVERTERS = {
810	        # https://docs.snowflake.com/en/sql-reference/data-types-numeric#number
811	        exp.DType.DECIMAL: build_default_decimal_type(precision=38, scale=0),
812	    }
813	
814	    SHOW_PARSERS = {
815	        "DATABASES": _show_parser("DATABASES"),
816	        "SCHEMAS": _show_parser("SCHEMAS"),
817	        "OBJECTS": _show_parser("OBJECTS"),
818	        "TABLES": _show_parser("TABLES"),
819	        "VIEWS": _show_parser("VIEWS"),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "offset": 1050, "limit": 100}
[tool_result] 1050	                exp.alias_(lateral, "_flattened", table=columns, copy=False)
1051	
1052	        return lateral
1053	
1054	    def _parse_table_parts(
1055	        self,
1056	        schema: bool = False,
1057	        is_db_reference: bool = False,
1058	        wildcard: bool = False,
1059	        fast: bool = False,
1060	    ) -> exp.Table | exp.Dot | None:
1061	        # https://docs.snowflake.com/en/user-guide/querying-stage
1062	        if self._match(TokenType.STRING, advance=False):
10
…[2926 chars elided]…
r()._parse_id_var(any_token=any_token, tokens=tokens)
1137	
1138	    def _parse_show_snowflake(
1139	        self, this: str, terse: bool = False, iceberg: bool = False
1140	    ) -> exp.Show:
1141	        scope = None
1142	        scope_kind = None
1143	
1144	        history = self._match_text_seq("HISTORY")
1145	
1146	        like = self._parse_string() if self._match(TokenType.LIKE) else None
1147	
1148	        if self._match(TokenType.IN):
1149	            if self._match_text_seq("ACCOUNT"):
[assistant] I'll check how the existing `PUT`/`GET` keywords are registered in the token enum and whether they're allowed as identifiers, since `UNDROP` would need the same treatment.
[tool_use Bash] {"command": "grep -rn \"PUT\\b\" sqlglot/tokens.py sqlglot/parser.py sqlglot/parsers/snowflake.py sqlglot/parsers/*.py sqlglot/tokens*.py 2>/dev/null | head -20; ls sqlglot/ | head -80; grep -rn \"def _parse_get\\|def _parse_put\" -A12 sqlglot/parsers/snowflake.py | head -60", "description": "Trace PUT/GET token and parser registration"}
[tool_result] sqlglot/parser.py:732:        TokenType.PUT,
sqlglot/parser.py:1280:        "INPUT": lambda self: self.expression(exp.InputModelProperty(this=self._parse_schema())),
sqlglot/parser.py:1297:        "OUTPUT": lambda self: self.expression(exp.OutputModelProperty(this=self._parse_schema())),
sqlglot/parser.py:3382:        elif self._match_text_seq("NULL", "ON", "NULL", "INPUT"):
sqlglot/parsers/snowflake.py:761:        TokenType.PUT: lambda self: self._parse_put(),
sqlglot/parsers/postgres.py:90:   
…[1897 chars elided]…
self._index - 2)
sqlglot/parsers/snowflake.py-1202-            return self._parse_expression()
sqlglot/parsers/snowflake.py-1203-
sqlglot/parsers/snowflake.py-1204-        target = self._parse_location_path()
sqlglot/parsers/snowflake.py-1205-
sqlglot/parsers/snowflake.py-1206-        # Parse as command if unquoted file path
sqlglot/parsers/snowflake.py-1207-        if self._curr.token_type == TokenType.URI_START:
sqlglot/parsers/snowflake.py-1208-            return self._parse_as_command(start)
[tool_use Bash] {"command": "grep -n \"PUT\\|GET\\b\\|STAGE\\b\" sqlglot/tokenizer_core.py | head; grep -rln \"class TokenType\" sqlglot/ ; grep -rn \"    PUT = \\|    GET = \\|    STAGE = \\|    REMOVE\" sqlglot/ | head; sed -n 720,740p sqlglot/parser.py", "description": "Locate TokenType definitions for PUT and GET"}
[tool_result] 3 matches in 1 files:

sqlglot/tokenizer_core.py:102:STAGE = auto()
sqlglot/tokenizer_core.py:306:GET = auto()
sqlglot/tokenizer_core.py:386:PUT = auto()
sqlglot/tokenizer_core.py
sqlglot/tokenizer_core.py:102:    STAGE = auto()
sqlglot/tokenizer_core.py:306:    GET = auto()
sqlglot/tokenizer_core.py:386:    PUT = auto()
        TokenType.NATURAL,
        TokenType.NEXT,
        TokenType.OFFSET,
        TokenType.OPERATOR,
        TokenType.ORDINALITY,
        TokenType.OVER,
        TokenType.OVERLAPS,
        TokenType.OVERWRITE,
        TokenType.PARTITION,
        TokenType.PERCENT,
        TokenType.PIVOT,
        TokenType.PRAGMA,
        TokenType.PUT,
        TokenType.RANGE,
        TokenType.RECURSIVE,
        TokenType.REFERENCES,
        TokenType.REFRESH,
        TokenType.RENAME,
        TokenType.REPLACE,
        TokenType.RIGHT,
        TokenType.ROLLUP,
[assistant] `TokenType` lives in `tokenizer_core.py`, and `PUT` is in the base `ID_VAR_TOKENS`, so I'll follow that precedent. Next I'll look at the `Drop` generator and the `Put` expression for the output shape.
[tool_use Bash] {"command": "grep -n \"def drop_sql\" -A22 sqlglot/generators/*.py sqlglot/generator.py | head -40; grep -n \"def put_sql\\|def get_sql\" -A12 sqlglot/generators/snowflake.py; grep -n \"class Put\\b\\|class Put(\" -A12 sqlglot/expressions/*.py; grep -n \"UNDROP\\|Undrop\" -r tests | head", "description": "Read Drop and Put generator and expression definitions"}
[tool_result] sqlglot/generators/tsql.py:589:    def drop_sql(self, expression: exp.Drop) -> str:
sqlglot/generators/tsql.py-590-        if expression.args["kind"] == "VIEW":
sqlglot/generators/tsql.py-591-            expression.this.set("catalog", None)
sqlglot/generators/tsql.py-592-        return super().drop_sql(expression)
sqlglot/generators/tsql.py-593-
sqlglot/generators/tsql.py-594-    def options_modifier(self, expression: exp.Expr) -> str:
sqlglot/generators/tsql.py-595-        options = self.expres
…[2834 chars elided]…
essions/query.py-939-class Get(Expression):
sqlglot/expressions/query.py-940-    arg_types = {"this": True, "target": True, "properties": False}
sqlglot/expressions/query.py-941-
sqlglot/expressions/query.py-942-
sqlglot/expressions/query.py-943-class Table(Expression, Selectable):
sqlglot/expressions/query.py-944-    arg_types = {
sqlglot/expressions/query.py-945-        "this": False,
sqlglot/expressions/query.py-946-        "alias": False,
sqlglot/expressions/query.py-947-        "db": False,
[assistant] The plan is taking shape. I'll add a `TokenType.UNDROP` keyword (Snowflake-only, mapped in the dialect tokenizer), a `UNDROP` statement parser, an `exp.Undrop` expression, and a generator method. First I'll check the token enum layout and the `_match_text_seq` contract.
[tool_use Bash] {"command": "grep -n \"UNION\\|UNIQUE = \\|UNNEST\\|UPDATE = \\|USE = \\|UNPIVOT\\|UUID\\|UNKNOWN\" sqlglot/tokenizer_core.py | head -20; grep -n \"def _match_text_seq\" -A22 sqlglot/parser.py | head -30; grep -n \"Drop\\|Put\\b\" sqlglot/typing/snowflake.py | head -5; grep -n \"class Put\\|Put(\" sqlglot/generators/snowflake.py | head", "description": "Inspect token enum neighbours and _match_text_seq"}
[tool_result] 9 matches in 1 files:

sqlglot/tokenizer_core.py:101:WAREHOUSE = auto()
sqlglot/tokenizer_core.py:189:UUID = auto()
sqlglot/tokenizer_core.py:232:UNKNOWN = auto()
sqlglot/tokenizer_core.py:434:UNION = auto()
sqlglot/tokenizer_core.py:435:UNNEST = auto()
sqlglot/tokenizer_core.py:436:UNPIVOT = auto()
sqlglot/tokenizer_core.py:437:UPDATE = auto()
sqlglot/tokenizer_core.py:438:USE = auto()
sqlglot/tokenizer_core.py:450:UNIQUE = auto()
1955:    def _match_text_seq(self, *texts: str, advance: bool = 
…[403 chars elided]…
   self._retreat(index)
1967-
1968-        return True
1969-
1970-    def _is_connected(self) -> bool:
1971-        prev = self._prev
1972-        curr = self._curr
1973-        return bool(prev and curr and prev.end + 1 == curr.start)
1974-
1975-    def _find_sql(self, start: Token, end: Token) -> str:
1976-        return self.sql[start.start : end.end + 1]
1977-
0 matches for 'Drop\|Put\b'
rg: regex parse error:
    (?:class Put|Put()
    ^
error: unclosed group
0 matches for 'class Put\|Put('
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "offset": 430, "limit": 25}
[tool_result] 430	    TRUNCATE = auto()
431	    TRIGGER = auto()
432	    TYPE = auto()
433	    UNCACHE = auto()
434	    UNION = auto()
435	    UNNEST = auto()
436	    UNPIVOT = auto()
437	    UPDATE = auto()
438	    USE = auto()
439	    USING = auto()
440	    VALUES = auto()
441	    VARIADIC = auto()
442	    VIEW = auto()
443	    SEMANTIC_VIEW = auto()
444	    VOLATILE = auto()
445	    VOLUME = auto()
446	    WHEN = auto()
447	    WHERE = auto()
448	    WINDOW = auto()
449	    WITH = auto()
450	    UNIQUE = auto()
451	    UTC_DATE = auto()
452	    UTC_TIME = auto()
453	    UTC_TIMESTAMP = auto()
454	    VERSION_SNAPSHOT = auto()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "offset": 1080, "limit": 20}
[tool_result] 1080	    }
1081	
1082	    STATEMENT_PARSERS: t.ClassVar = {
1083	        TokenType.ALTER: lambda self: self._parse_alter(),
1084	        TokenType.ANALYZE: lambda self: self._parse_analyze(),
1085	        TokenType.BEGIN: lambda self: self._parse_transaction(),
1086	        TokenType.CACHE: lambda self: self._parse_cache(),
1087	        TokenType.COMMENT: lambda self: self._parse_comment(),
1088	        TokenType.COMMIT: lambda self: self._parse_commit_or_rollback(),
1089	        TokenType.COPY:
…[183 chars elided]…
nType.DESC: lambda self: self._parse_describe(),
1093	        TokenType.DESCRIBE: lambda self: self._parse_describe(),
1094	        TokenType.DROP: lambda self: self._parse_drop(),
1095	        TokenType.GRANT: lambda self: self._parse_grant(),
1096	        TokenType.REVOKE: lambda self: self._parse_revoke(),
1097	        TokenType.INSERT: lambda self: self._parse_insert(),
1098	        TokenType.KILL: lambda self: self._parse_kill(),
1099	        TokenType.LOAD: lambda self: self._parse_load(),
[assistant] I have what I need. Edits, in order: the token enum, the Snowflake keyword, the base ID-var set, the `Undrop` expression, the statement parser, and the generator. I'll start with the token enum.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py", "old_string": "    UNCACHE = auto()\n    UNION = auto()", "new_string": "    UNCACHE = auto()\n    UNDROP = auto()\n    UNION = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Bash] {"command": "python3 -c \"\nimport re\nlines=open('sqlglot/parser.py').read().split('\\n')\nfor i,l in enumerate(lines,1):\n    if 'TokenType.UNCACHE' in l or 'TokenType.UNION,' in l or 'TokenType.UNNEST' in l: print(i,l)\n\"; grep -n \"class Drop\" -A3 sqlglot/expressions/ddl.py | head -3", "description": "Find UNION/UNNEST entries in parser token sets"}
[tool_result] 445         TokenType.UNION,
754         TokenType.UNNEST,
858         TokenType.UNNEST,
940         TokenType.UNION,
1107         TokenType.UNCACHE: lambda self: self._parse_uncache(),
4983         if not self._match_pair(TokenType.UNNEST, TokenType.L_PAREN, advance=False):
345:class Drop(Expression):
346-    arg_types = {
347-        "this": False,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "offset": 750, "limit": 12}
[tool_result] 750	        TokenType.TOP,
751	        TokenType.TRUE,
752	        TokenType.TRUNCATE,
753	        TokenType.UNIQUE,
754	        TokenType.UNNEST,
755	        TokenType.UNPIVOT,
756	        TokenType.UPDATE,
757	        TokenType.USE,
758	        TokenType.VOLATILE,
759	        TokenType.WINDOW,
760	        TokenType.CURRENT_CATALOG,
761	        TokenType.LOCALTIME,
[tool_use Bash] {"command": "python3 -c \"\nlines=open('sqlglot/parser.py').read().split('\\n')\nimport re\nfor i in range(754,0,-1):\n    m=re.match(r'^    (\\w+)[:=]',lines[i-1])\n    if m: print(i,m.group(1)); break\n\"", "description": "Identify the parser token set containing UNNEST"}
[tool_result] 666 ID_VAR_TOKENS
[assistant] `ID_VAR_TOKENS` is the set I need. I'll add `UNDROP` in alphabetical order, ahead of `UNIQUE`, so it can still be used as an identifier outside Snowflake's statement position.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py", "old_string": "        TokenType.TRUNCATE,\n        TokenType.UNIQUE,\n        TokenType.UNNEST,", "new_string": "        TokenType.TRUNCATE,\n        TokenType.UNDROP,\n        TokenType.UNIQUE,\n        TokenType.UNNEST,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py", "old_string": "            \"TOP\": TokenType.TOP,\n            \"VOLUME\": TokenType.VOLUME,", "new_string": "            \"TOP\": TokenType.TOP,\n            \"UNDROP\": TokenType.UNDROP,\n            \"VOLUME\": TokenType.VOLUME,"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/dialects/snowflake.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py", "old_string": "class DropPrimaryKey(Expression):\n    arg_types = {}", "new_string": "class Undrop(Expression):\n    arg_types = {\"this\": True, \"kind\": True}\n\n\nclass DropPrimaryKey(Expression):\n    arg_types = {}"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/expressions/ddl.py has been updated successfully.
[assistant] Next, the Snowflake statement parser. I'll read the end of `_parse_get` so the new method goes in the right place.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "offset": 1196, "limit": 30}
[tool_result] 1196	    def _parse_get(self) -> exp.Expr | None:
1197	        start = self._prev
1198	
1199	        # If we detect GET( then we need to parse a function, not a statement
1200	        if self._match(TokenType.L_PAREN):
1201	            self._retreat(self._index - 2)
1202	            return self._parse_expression()
1203	
1204	        target = self._parse_location_path()
1205	
1206	        # Parse as command if unquoted file path
1207	        if self._curr.token_type == TokenType.URI_START:
1208	 
…[270 chars elided]…
ationProperty:
1215	        self._match(TokenType.EQ)
1216	        return self.expression(exp.LocationProperty(this=self._parse_location_path()))
1217	
1218	    def _parse_file_location(self) -> exp.Expr | None:
1219	        # Parse either a subquery or a staged file
1220	        return (
1221	            self._parse_select(table=True, parse_subquery_alias=False)
1222	            if self._match(TokenType.L_PAREN, advance=False)
1223	            else self._parse_table_parts()
1224	        )
1225	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        return self.expression(\n            exp.Get(this=self._parse_string(), target=target, properties=self._parse_properties())\n        )\n\n    def _parse_location_property(self) -> exp.LocationProperty
…[370 chars elided]…
      kind\n                for kind in self.UNDROP_KINDS\n                if self._match_text_seq(*kind.split())\n            ),\n            None,\n        )\n        if not kind:\n            return self._parse_as_command(start)\n\n        return self.expression(exp.Undrop(this=self._parse_table_parts(schema=True), kind=kind))\n\n    def _parse_location_property(self) -> exp.LocationProperty:"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now the `UNDROP_KINDS` constant and the statement-parser registration.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py", "old_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n    }\n\n    PROPERTY_PARSERS = {", "new_string": "        TokenType.SHOW: lambda self: self._parse_show(),\n        TokenType.UNDROP: lambda self: self._parse_undrop(),\n    }\n\n    UNDROP_KINDS = (\n        \"ACCOUNT\",\n        \"DATABASE\",\n        \"DYNAMIC TABLE\",\n        \"EXTERNAL VOLUME\",\n        \"ICEBERG TABLE\",\n        \"NOTEBOOK\",\n        \"SCHEMA\",\n        \"SNAPSHOT\",\n        \"STREAMLIT\",\n        \"TABLE\",\n        \"TAG\",\n        \"TYPE\",\n    )\n\n    PROPERTY_PARSERS = {"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/parsers/snowflake.py has been updated successfully.
[assistant] Now the generator. I'll find a sensible spot in the Snowflake generator for `undrop_sql`.
[tool_use Bash] {"command": "python3 -c \"\nlines=open('sqlglot/generators/snowflake.py').read().split('\\n')\nfor i,l in enumerate(lines,1):\n    if l.startswith('    def ') : print(i,l)\n\" | head -80", "description": "List method definitions in Snowflake generator"}
[tool_result] 53     def _builder(args: list) -> E:
102     def _flatten_structured_type(expression: exp.Expr) -> exp.Expr:
619     def sortarray_sql(self, expression: exp.SortArray) -> str:
626     def nthvalue_sql(self, expression: exp.NthValue) -> str:
677     def with_properties(self, properties: exp.Properties) -> str:
680     def values_sql(self, expression: exp.Values, values_as_table: bool = True) -> str:
686     def datatype_sql(self, expression: exp.DataType) -> str:
717     def tonumber_sql(self, e
…[1749 chars elided]…
l(self, expression: exp.Array) -> str:
1082     def currentdate_sql(self, expression: exp.CurrentDate) -> str:
1093     def dot_sql(self, expression: exp.Dot) -> str:
1107     def modelattribute_sql(self, expression: exp.ModelAttribute) -> str:
1110     def format_sql(self, expression: exp.Format) -> str:
1116     def splitpart_sql(self, expression: exp.SplitPart) -> str:
1126     def uniform_sql(self, expression: exp.Uniform) -> str:
1140     def window_sql(self, expression: exp.Window) -> str:
[assistant] I'll place `undrop_sql` just before `generatedasidentitycolumnconstraint_sql`, which keeps it near the other DDL-ish generators.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py", "old_string": "    def generatedasidentitycolumnconstraint_sql(", "new_string": "    def undrop_sql(self, expression: exp.Undrop) -> str:\n        return f\"UNDROP {expression.args['kind']} {self.sql(expression, 'this')}\"\n\n    def generatedasidentitycolumnconstraint_sql("}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/sqlglot/generators/snowflake.py has been updated successfully.
[assistant] Now I'll re-run the same probe to check the parse, round-trip and generated output for each object type.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat <<'EOF' | $PY .lithify/harness/scripts/probe_parse.py --read snowflake\nUNDROP TABLE t\nUNDROP TABLE db.s.t\nUNDROP SCHEMA s\nUNDROP SCHEMA db.s\nUNDROP DATABASE d\nUNDROP ACCOUNT a\nUNDROP NOTEBOOK nb\nUNDROP SNAPSHOT snap\nUNDROP STREAMLIT st\nUNDROP TAG tg\nUNDROP TYPE ty\nUNDROP DYNAMIC TABLE dt\nUND
…[343 chars elided]…
ines():\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', repr(e.args.get('kind')), '|', e.sql('snowflake'), '|', e.sql('duckdb'))\n    except Exception as x: print('ERR', s, x)\n\" \nUNDROP TABLE t\nUNDROP DYNAMIC TABLE db.s.dt\nUNDROP TABLE IDENTIFIER('\"1234567\"')\nUNDROP FOO x\nEOF", "description": "Probe UNDROP forms and round-trip after the change"}
[tool_result] Traceback (most recent call last):
  File "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/.lithify/harness/scripts/probe_parse.py", line 22, in <module>
    import sqlglot
ModuleNotFoundError: No module named 'sqlglot'
---
'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
ERR UNDROP TABLE t Unsupported expression type Undrop
ERR UNDROP DYNAMIC TABLE db.s.dt Unsupported expression type Undrop
ERR UNDROP TABLE IDENTIFIER('"1234567"') Unsupported expression type Undrop
Command | None | UNDROP FOO x | UNDROP FOO x
[assistant] Two things to fix in the probe itself. I left out `PYTHONPATH` on the first run. The `Unsupported expression type Undrop` errors come from my second script calling `.sql('duckdb')`, which is expected because `UNDROP` is Snowflake-only. I'll re-run both with the right settings.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat <<'EOF' | PYTHONPATH=$PWD $PY .lithify/harness/scripts/probe_parse.py --read snowflake\nUNDROP TABLE t\nUNDROP TABLE db.s.t\nUNDROP SCHEMA s\nUNDROP SCHEMA db.s\nUNDROP DATABASE d\nUNDROP ACCOUNT a\nUNDROP NOTEBOOK nb\nUNDROP SNAPSHOT snap\nUNDROP STREAMLIT st\nUNDROP TAG tg\nUNDROP TYPE ty\nUNDROP DYNAM
…[296 chars elided]…
PY -c \"\nimport sys, sqlglot\nfor s in sys.stdin.read().splitlines():\n    try:\n        e = sqlglot.parse_one(s, read='snowflake'); print(type(e).__name__, '|', repr(e.args.get('kind')), '|', e.sql('snowflake'))\n    except Exception as x: print('ERR', s, x)\n\" <<'X'\nUNDROP TABLE IDENTIFIER('\"1234567\"')\nUNDROP TABLE db.s.t\nX", "description": "Re-probe UNDROP forms with repo on PYTHONPATH"}
[tool_result] 'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
'UNDROP FOO x' contains unsupported syntax. Falling back to parsing as a 'Command'.
OK        UNDROP TABLE t
          UNDROP TABLE t
OK        UNDROP TABLE db.s.t
          UNDROP TABLE db.s.t
OK        UNDROP SCHEMA s
          UNDROP SCHEMA s
OK        UNDROP SCHEMA db.s
          UNDROP SCHEMA db.s
OK        UNDROP DATABASE d
          UNDROP DATABASE d
OK        UNDROP ACCOUNT a
          UNDROP ACCOUNT a
OK
…[588 chars elided]…
UNDROP DATABASE IDENTIFIER('"01b2c3d4-0000"')
          UNDROP DATABASE IDENTIFIER('"01b2c3d4-0000"')
OK        UNDROP TABLE IDENTIFIER($id)
          UNDROP TABLE IDENTIFIER($id)
OK        undrop table t
          UNDROP TABLE t
OK        SELECT undrop FROM t
          SELECT undrop FROM t
OK        UNDROP FOO x
          UNDROP FOO x
OK        DROP TABLE t
          DROP TABLE t
---
Undrop | 'TABLE' | UNDROP TABLE IDENTIFIER('"1234567"')
Undrop | 'TABLE' | UNDROP TABLE db.s.t
Column | None | X
[assistant] All forms parse and round-trip. `IDENTIFIER(...)` and the case-insensitive lowercase input both work, and `SELECT undrop` still works as an identifier. The `Column | None | X` line in the second output is an artifact of my heredoc, not a result. Next I'll add tests next to the existing Snowflake DROP tests.
[tool_use Bash] {"command": "python3 -c \"\nlines=open('tests/dialects/test_snowflake.py').read().split('\\n')\nfor i,l in enumerate(lines,1):\n    if 'DROP' in l or 'def test_' in l and 'ddl' in l.lower(): print(i,l)\n\" | head -40", "description": "Find DROP-related test locations in Snowflake tests"}
[tool_result] 4238     def test_ddl(self):
4304             "DROP FUNCTION my_udf (OBJECT(city VARCHAR, zipcode DECIMAL(38, 0), val ARRAY(BOOLEAN)))"
4394         for action in ("SET", "DROP"):
5352         ast = self.validate_identity("DROP ICEBERG TABLE t")
5354         self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
5355         ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT")
5357         self.validate_identity("DROP ICEBERG TABLE IF EXISTS t RESTRICT")
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "offset": 5345, "limit": 25}
[tool_result] 5345	            write={
5346	                "snowflake": "ALTER ICEBERG TABLE t RENAME TO x",
5347	                "duckdb": "ALTER TABLE t RENAME TO x",
5348	            },
5349	        )
5350	
5351	    def test_drop_iceberg_table(self):
5352	        ast = self.validate_identity("DROP ICEBERG TABLE t")
5353	        self.assertTrue(ast.args["iceberg"])
5354	        self.validate_identity("DROP ICEBERG TABLE IF EXISTS t")
5355	        ast = self.validate_identity("DROP ICEBERG TABLE t RESTRICT"
…[267 chars elided]…
entity("SHOW PRIMARY KEYS IN ACCOUNT")
5362	        self.validate_identity("SHOW PRIMARY KEYS IN DATABASE")
5363	        self.validate_identity("SHOW PRIMARY KEYS IN DATABASE foo")
5364	        self.validate_identity("SHOW PRIMARY KEYS IN TABLE")
5365	        self.validate_identity("SHOW PRIMARY KEYS IN TABLE foo")
5366	        self.validate_identity(
5367	            'SHOW PRIMARY KEYS IN "TEST"."PUBLIC"."foo"',
5368	            'SHOW PRIMARY KEYS IN TABLE "TEST"."PUBLIC"."foo"',
5369	        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py", "old_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRICT\")\n\n    def test_show_primary_keys(self):", "new_string": "        self.validate_identity(\"DROP ICEBERG TABLE IF EXISTS t RESTRI
…[538 chars elided]…
        \"TYPE\",\n        ):\n            with self.subTest(kind=kind):\n                self.validate_identity(f\"UNDROP {kind} x\")\n\n        self.validate_identity(\"UNDROP TABLE IDENTIFIER('\\\"1234567\\\"')\")\n        self.validate_identity(\"UNDROP DATABASE IDENTIFIER($id)\")\n        self.validate_identity(\"undrop table t\", \"UNDROP TABLE t\")\n\n    def test_show_primary_keys(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-3abf279ffb90/20261029-164303-snowflake-dialect-snowflake-s-ti/base-1/tests/dialects/test_snowflake.py has been updated successfully.
[assistant] I'll confirm the test module imports `exp`, then run the Snowflake test file along with the project's pytest command.
[tool_use Bash] {"command": "head -12 tests/dialects/test_snowflake.py | grep -n \"import\"; <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_snowflake.py -k \"undrop or drop\" 2>&1 | tail -15", "description": "Run Snowflake undrop and drop tests"}
[tool_result] 1:from unittest import mock
3:from sqlglot import ParseError, UnsupportedError, exp, parse_one
4:from sqlglot.parser import logger as parser_logger
5:from sqlglot.optimizer.annotate_types import annotate_types
6:from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
7:from sqlglot.optimizer.qualify_columns import quote_identifiers
8:from tests.dialects.test_dialect import Validator
..                                                           [100%]
2 passed, 94 deselected, 12 subtests passed in 0.13s
[assistant] The targeted tests pass. Next I'll run the lint/format check on the changed files and then the full suite as the final gate.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; FILES=\"sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/tokenizer_core.py sqlglot/expressions/ddl.py tests/dialects/test_snowflake.py\"; ($PY -m ruff --version && $PY -m ruff format --check $FILES; $PY -m ruff check $FILES) 2>&1 | tail -20", "description": "Check formatting and lint on changed files"}
[tool_result] ruff 0.15.6
error: Failed to format sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/tokenizer_core.py sqlglot/expressions/ddl.py tests/dialects/test_snowflake.py: No such file or directory (os error 2)
E902 No such file or directory (os error 2)
--> sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/tokenizer_core.py sqlglot/expressions/ddl.py tests/dialects/test_snowflake.py:1:1

Found 1 error.
[assistant] zsh doesn't word-split unquoted variables, so I'll pass the file list literally.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/tokenizer_core.py sqlglot/expressions/ddl.py tests/dialects/test_snowflake.py 2>&1 | tail -5; $PY -m ruff check sqlglot/parsers/snowflake.py sqlglot/generators/snowflake.py sqlglot/dialects/snowflake.py sqlglot/parser.py sqlglot/tokenizer_core.py sqlglot/expressions/ddl.py tests/dialects/test_snowflake.py 2>&1 | tail -5", "description": "Run ruff format and lint checks on changed files"}
[tool_result] Would reformat: sqlglot/parsers/snowflake.py
1 file would be reformatted, 6 files already formatted
All checks passed!
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format sqlglot/parsers/snowflake.py && git diff --stat && git diff sqlglot/parsers/snowflake.py | head -80", "description": "Apply ruff formatting and show parser diff"}
[tool_result] 1 file reformatted
sqlglot/dialects/snowflake.py    |  1 +
 sqlglot/expressions/ddl.py       |  4 ++++
 sqlglot/generators/snowflake.py  |  3 +++
 sqlglot/parser.py                |  1 +
 sqlglot/parsers/snowflake.py     | 28 ++++++++++++++++++++++++++++
 sqlglot/tokenizer_core.py        |  1 +
 tests/dialects/test_snowflake.py | 26 ++++++++++++++++++++++++++
 7 files changed, 64 insertions(+)
sqlglot/parsers/snowflake.py | 28 ++++++++++++++++++++++++++++
 1 file changed, 28 insertions(+)

--- C
…[1017 chars elided]…
 )
  +        if not kind:
  +            return self._parse_as_command(start)
  +
  +        return self.expression(exp.Undrop(this=self._parse_table_parts(schema=True), kind=kind))
  +
       def _parse_location_property(self) -> exp.LocationProperty:
           self._match(TokenType.EQ)
           return self.expression(exp.LocationProperty(this=self._parse_location_path()))
  +28 -0
[This command modified 1 file you've previously read: sqlglot/parsers/snowflake.py. Call Read before editing.]
[assistant] Formatting is applied; the notice about the file changing is just my own `ruff format` run. Now the full suite as the final gate.
[tool_use Bash] {"command": "timeout 580 <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run the full test suite", "timeout": 600000}
[tool_result] (eval):1: command not found: timeout
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -25", "description": "Run the full test suite", "timeout": 600000}
[tool_result] .................................. [  3%]
...................................................................... [  9%]
............................................. [ 13%]
.................................................................... [ 19%]
..................... [ 21%]
............................................................................... [ 28%]
................................................ [ 32%]
...............................................................................
…[376 chars elided]…
.................. [ 71%]
........................................................... [ 77%]
............................................ [ 81%]
...................................................................... [ 87%]
........................ [ 89%]
.................................................................. [ 95%]
............................................ [ 99%]
........                                                            [100%]
1121 passed, 18188 subtests passed in 45.71s
[assistant] `UNDROP` now parses and generates for all twelve Snowflake object types, including the `IDENTIFIER(...)` form. The full suite passes: 1121 tests, 18188 subtests.

**Before:** every `UNDROP <type> <name>` raised `ParseError`. `UNDROP ACCOUNT` was worse: it silently parsed as `SELECT UNDROP AS ACCOUNT`.

**After:** each form round-trips in the Snowflake dialect, e.g. `undrop table db.s.t` → `UNDROP TABLE db.s.t`, and `UNDROP TABLE IDENTIFIER('"1234567"')` is preserved as written.

Changes:
- `sqlglot/tokenizer_core.py`: new `TokenType.UNDROP`.
- `sqlglot/parser.py`: `UNDROP` added to `ID_VAR_TOK
…[425 chars elided]…
h `this` and `kind`.
- `sqlglot/generators/snowflake.py`: `undrop_sql`.
- `tests/dialects/test_snowflake.py`: `test_undrop` covers all kinds, the `IDENTIFIER` form, and lowercase input.

Design choice: the object name is parsed with the existing `_parse_table_parts`, so dotted names and `IDENTIFIER(...)` work without special-casing.

Not verified: I had no live Snowflake account, so the test SQL is checked only by parse and round-trip, not executed against Snowflake. The exact `IDENTIFIER` literal shape for restore-by-ID should be confirmed against a real account. I haven't committed anything.
