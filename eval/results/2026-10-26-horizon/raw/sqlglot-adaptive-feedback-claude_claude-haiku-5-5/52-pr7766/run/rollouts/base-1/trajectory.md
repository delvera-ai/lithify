# trajectory base-1

final message:
Postgres now accepts `@?`: `SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'` tokenizes, parses into `exp.JSONBPathExists`, and generates back as `@?`. The full suite passes: `SUMMARY: 1121 passed, 18178 subtests passed in 50.77s`, `EXIT: 0`, run after my last edit. I did not commit.

**What changed**
- `sqlglot/tokenizer_core.py`: new `TokenType.AT_QMARK`.
- `sqlglot/dialects/postgres.py`: `"@?"` keyword mapped to `AT_QMARK`, Postgres only.
- `sqlglot/expressions/json.py`: new `JSONBPathExists(Binary, Func)` node, modelled on `JSONBContainsAllTopKeys`.
- `sqlglot/parser.py`: a range-parser entry so `@?` binds like the other comparison operators.
- `sqlglot/generators/postgres.py`: `jsonbpathexists_sql` emits `@?` for the two-argument form.
- `tests/dialects/test_postgres.py`: operator round-trip, node class check, and the function forms.

**A regression I caught and fixed:** my first version registered `jsonb_path_exists` as a plain two-argument function. That broke Postgres's valid three- and four-argument calls (`vars`, `silent`), which had previously round-tripped as a generic function. The node now accepts those optional args and the generator falls back to the function form when they are present.

**Verified**
- `jsonb_path_exists(doc, '$.a')` now also parses into the node and comes back as `doc @? '$.a'`, which is the same operation.
- The three- and four-argument function forms still round-trip as `JSONB_PATH_EXISTS(...)`.
- `tests/dialects/test_postgres.py`: 26 passed.
- `ruff check` and `ruff format --check` are clean on the changed files.

**Open item:** transpiling to other dialects emits `JSONB_PATH_EXISTS(doc, '...')`. DuckDB, Snowflake and MySQL don't define that function, so the output won't run there. I didn't map it to something like DuckDB's `json_exists`, because that path language has no filter expressions and the result wouldn't be equivalent. The request was Postgres round-trip, so I left it. If you want a target mapping, tell me which engine and whether a partial equivalent is acceptable.

## events
[assistant] I'll start by finding how the Postgres dialect already handles the `@>`/`@@` JSONB operators, and where the skill files and test runner live.
[tool_use Bash] {"command": "git status --short | head && ls .lithify/harness/skills/ && grep -rn '\"@@\"\\|\"@>\"\\|\"<@\"\\|AT_GT\\|AT_AT\\|JSONBContains\\|ParseJSON\\|JSONBExists' sqlglot/tokens.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/expressions/*.py sqlglot/dialects/postgres.py | head -50", "description": "Check repo state and find existing JSONB operator handling"}
[tool_result] sqlglot-clause-element-lists
sqlglot-data-types
sqlglot-ddl-statements
sqlglot-dialect-functions
sqlglot-json-table
sqlglot-lineage
sqlglot-null-ordering
sqlglot-optimizer-rewrites
sqlglot-parser-options
sqlglot-query-modifiers
sqlglot-time-parsing
sqlglot-upsert-on-conflict
sqlglot/parsers/postgres.py:315:    def _parse_jsonb_exists(self) -> exp.JSONBExists:
sqlglot/parsers/postgres.py:317:            exp.JSONBExists(
sqlglot/generators/postgres.py:326:        exp.JSONBContains: lambda self, e:
…[227 chars elided]…
xpressions/json.py:53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:57:class JSONBContainsAnyTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:65:class JSONBExists(Expression, Func):
sqlglot/expressions/json.py:234:class ParseJSON(Expression, Func):
sqlglot/dialects/postgres.py:77:            "@@": TokenType.DAT,
sqlglot/dialects/postgres.py:78:            "@>": TokenType.AT_GT,
sqlglot/dialects/postgres.py:79:            "<@": TokenType.LT_AT,
[assistant] Before editing I need to read the skills that match this task. The JSON skill and the dialect-functions skill both apply.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-json-table/SKILL.md && echo ===== && cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md", "description": "Read the JSON and dialect-functions skill guides"}
[tool_result ERROR] Exit code 1
---
name: sqlglot-json-table
description: Load when a task touches SQL/JSON syntax in sqlglot — JSON_TABLE (its COLUMNS / NESTED PATH / FOR ORDINALITY column definitions), the FORMAT JSON / ENCODING clauses, JSON_OBJECT / JSON_OBJECTAGG RETURNING, Oracle JSON_ARRAY / JSON_ARRAYAGG / JSON_EXISTS, or T-SQL OPENJSON — including any "fails to parse" report that mentions one of them in any dialect.
---

# SQL/JSON syntax (JSON_TABLE, FORMAT JSON) in sqlglot

## Who owns what (verified in 
…[3681 chars elided]…
arser is shared.

## Done means, read from output after your last edit
- The exact SQL from the task parses, and so does each `FORMAT JSON` position you probed.
- `repr()` of the parsed `exp.JSONTable` shows the clause stored on the node it belongs to
  (`this` → `FormatJson` for the input; the `JSONColumnDef` for a column), and the Oracle
  round-trip prints it back in place.
- `tests/dialects/test_oracle.py` and `tests/dialects/test_mysql.py` pass, then the full suite.
(eval):1: ==== not found
[tool_use Bash] {"command": "sed -n 60,110p sqlglot/dialects/postgres.py; echo ====; grep -n 'AT_GT\\|LT_AT\\|DAT\\b\\|QMARK_AMP\\|HASH_ARROW\\|PLACEHOLDER\\|\"@\"\\|AT_AT' sqlglot/tokens.py sqlglot/parsers/postgres.py sqlglot/generators/postgres.py sqlglot/parser.py sqlglot/generator.py | head -60; echo ====; sed -n 40,75p sqlglot/expressions/json.py", "description": "Inspect Postgres tokenizer, operator and JSON expression code"}
[tool_result ERROR] Exit code 1
        "yyyy": "%Y",  # 2015
        "YYYY": "%Y",  # 2015
    }

    class Tokenizer(tokens.Tokenizer):
        BIT_STRINGS = [("b'", "'"), ("B'", "'")]
        HEX_STRINGS = [("x'", "'"), ("X'", "'")]
        BYTE_STRINGS = [("e'", "'"), ("E'", "'")]
        BYTE_STRING_ESCAPES = ["'", "\\"]
        HEREDOC_STRINGS = ["$"]

        HEREDOC_TAG_IS_IDENTIFIER = True
        HEREDOC_STRING_ALTERNATIVE = TokenType.PARAMETER

        KEYWORDS = {
            **tokens.Tokenizer.KEYWORDS
…[1006 chars elided]…
 TokenType.SERIAL,
            "SMALLSERIAL": TokenType.SMALLSERIAL,
            "TEMP": TokenType.TEMPORARY,
            "TYPE": TokenType.TYPE,
            "REGCLASS": TokenType.OBJECT_IDENTIFIER,
            "REGCOLLATION": TokenType.OBJECT_IDENTIFIER,
            "REGCONFIG": TokenType.OBJECT_IDENTIFIER,
            "REGDICTIONARY": TokenType.OBJECT_IDENTIFIER,
            "REGNAMESPACE": TokenType.OBJECT_IDENTIFIER,
            "REGOPER": TokenType.OBJECT_IDENTIFIER,
(eval):1: === not found
[assistant] The skill guide is the JSON one: it covers `FORMAT JSON` and JSON_TABLE, not jsonpath operators, so the dialect-functions skill is the one that applies. Next I'll look at how `@>` and `?&` flow through the tokenizer, parser and generator.
[tool_use Bash] {"command": "cat .lithify/harness/skills/sqlglot-dialect-functions/SKILL.md | head -150; echo; echo ---; grep -rn 'AT_GT\\|LT_AT\\|QMARK_AMP\\|JSONBContainsAllTopKeys\\|JSONBExists\\b' sqlglot/ | grep -v '^sqlglot/dialects/postgres.py:7[0-9]'", "description": "Read dialect-functions skill and find JSONB operator usages"}
[tool_result] ---
name: sqlglot-dialect-functions
description: Load when a task reports SQL that fails to parse, round-trips wrongly or transpiles wrongly in a sqlglot dialect (ParseError, "Invalid expression", unsupported function syntax such as ClickHouse parametric aggregates f(p)(x)), or when a dialect must accept a shorthand / optional-keyword form of a function it already parses (e.g. DATE_ADD / DATE_SUB with a bare number instead of INTERVAL), or when adding/mapping a dialect function — any change to a
…[12148 chars elided]…
           "?&": TokenType.QMARK_AMP,
sqlglot/dialects/duckdb.py:82:            "@>": TokenType.AT_GT,
sqlglot/dialects/duckdb.py:83:            "<@": TokenType.LT_AT,
sqlglot/expressions/json.py:53:class JSONBContainsAllTopKeys(Expression, Binary, Func):
sqlglot/expressions/json.py:65:class JSONBExists(Expression, Func):
sqlglot/generators/singlestore.py:168:        exp.JSONBExists: lambda self, e: self.func(
sqlglot/generators/duckdb.py:1611:        exp.JSONBExists: rename_func("JSON_EXISTS"),
[assistant] The `?&` operator already has a dedicated node (`JSONBContainsAllTopKeys`), so `@?` should follow that pattern. Next I'll check the binary-operator wiring and whether a jsonpath-exists node or function already exists.
[tool_use Bash] {"command": "grep -rni 'path_exists\\|PathExists\\|jsonb_path\\|JSONB_PATH' sqlglot/ tests/ | head -20; echo ---; sed -n 1180,1205p sqlglot/parser.py; echo ---; sed -n 40,70p sqlglot/expressions/json.py; echo ---; sed -n 195,215p sqlglot/generator.py; echo ---; sed -n 320,335p sqlglot/generators/postgres.py; echo ---; grep -n 'JSONBContains\\|\"?\"\\|QMARK' sqlglot/parsers/postgres.py sqlglot/dialects/postgres.py sqlglot/tokenizer_core.py sqlglot/tokens.py | head; echo ---; grep -n 'DAT\\b' sqlglot/parser.py sqlglot/generator.py sqlglot/generators/postgres.py | head", "description": "Inspect JSONB operator parsing, nodes and generator mappings"}
[tool_result] ---
            self.expression(exp.Placeholder(this=self._prev.text))
            if self._match_set(self.COLON_PLACEHOLDER_TOKENS)
            else None
        ),
    }

    RANGE_PARSERS: t.ClassVar = {
        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
        TokenType.BETWEEN: lambda self, this: self._parse_between(this),
        TokenType.GLOB: binary_range_parser(exp.Glob),
        TokenType.ILIKE: binary_range_parser(exp.ILike),
        TokenType.IN: lambda self, this:
…[3969 chars elided]…
ies: no_map_from_entries_sql,
---
sqlglot/dialects/postgres.py:80:            "?&": TokenType.QMARK_AMP,
sqlglot/dialects/postgres.py:81:            "?|": TokenType.QMARK_PIPE,
sqlglot/tokenizer_core.py:30:    DCOLONQMARK = auto()
sqlglot/tokenizer_core.py:31:    DQMARK = auto()
sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
sqlglot/tokenizer_core.py:81:    QMARK_PIPE = auto()
sqlglot/tokens.py:161:        "?": TokenType.PLACEHOLDER,
sqlglot/tokens.py:241:        "??": TokenType.DQMARK,
---
[assistant] The plan is settled: add a `JSONBPathExists` node next to `JSONBContainsAllTopKeys`, a `@?` token, and a range-parser entry. Before editing I'll confirm the Python environment and record the current behaviour.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls -la $PY; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\nsql=\\\"SELECT * FROM events WHERE doc @? '\\$.a[*] ? (@ > 2)'\\\"\ntry:\n    t=sqlglot.parse_one(sql, read='postgres'); print(repr(t.args['where']))\nexcept Exception as e: print('ERR', type(e).__name__, e)\n\"; sed -n 55,85p sqlglot/tokenizer_core.py; grep -n 'AT_GT\\|QMARK_AMP' sqlglot/tokens.py sqlglot/*.py | head", "description": "Check Python env and baseline @? parse behaviour"}
[tool_result] lrwxr-xr-x@ 1 user  wheel  84 Oct 26 08:58 <work>/env-sqlglot/bin/python -> ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12
ERR ParseError Invalid expression / Unexpected token. Line 1, Col: 32.
  SELECT * FROM events WHERE doc [4m@[0m? '$.a[*] ? (@ > 2)'
    CARET = auto()
    CARET_AT = auto()
    TILDE = auto()
    ARROW = auto()
 
…[355 chars elided]…
T = auto()
    AMP_GT = auto()
    ADJACENT = auto()
    XOR = auto()
    DSTAR = auto()
    QMARK_AMP = auto()
    QMARK_PIPE = auto()
    HASH_DASH = auto()
    EXCLAMATION = auto()

    URI_START = auto()
sqlglot/parser.py:1187:        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
sqlglot/parser.py:1200:        TokenType.QMARK_AMP: binary_range_parser(exp.JSONBContainsAllTopKeys),
sqlglot/tokenizer_core.py:68:    AT_GT = auto()
sqlglot/tokenizer_core.py:80:    QMARK_AMP = auto()
[assistant] Baseline confirms the bug: `@?` fails at the operator. Now I'll read the regions I'm about to edit (the Edit tool needs a prior Read).
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "offset": 76, "limit": 8}
[tool_result] 76	    AMP_GT = auto()
77	    ADJACENT = auto()
78	    XOR = auto()
79	    DSTAR = auto()
80	    QMARK_AMP = auto()
81	    QMARK_PIPE = auto()
82	    HASH_DASH = auto()
83	    EXCLAMATION = auto()
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "offset": 49, "limit": 25}
[tool_result] 49	class JSONBContains(Expression, Binary, Func):
50	    _sql_names = ["JSONB_CONTAINS"]
51	
52	
53	class JSONBContainsAllTopKeys(Expression, Binary, Func):
54	    pass
55	
56	
57	class JSONBContainsAnyTopKeys(Expression, Binary, Func):
58	    pass
59	
60	
61	class JSONBDeleteAtPath(Expression, Binary, Func):
62	    pass
63	
64	
65	class JSONBExists(Expression, Func):
66	    arg_types = {"this": True, "path": True}
67	    _sql_names = ["JSONB_EXISTS"]
68	
69	
70	class JSONBExtract(Expression, Binary, Func):
71	    _sql_names = ["JSONB_EXTRACT"]
72	
73	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "offset": 1186, "limit": 3}
[tool_result] 1186	    RANGE_PARSERS: t.ClassVar = {
1187	        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),
1188	        TokenType.BETWEEN: lambda self, this: self._parse_between(this),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py", "offset": 325, "limit": 3}
[tool_result] 325	        exp.JSONBExtractScalar: lambda self, e: self.binary(e, "#>>"),
326	        exp.JSONBContains: lambda self, e: self.binary(e, "?"),
327	        exp.ParseJSON: lambda self, e: self.sql(exp.cast(e.this, exp.DType.JSON)),
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "offset": 77, "limit": 4}
[tool_result] 77	            "@@": TokenType.DAT,
78	            "@>": TokenType.AT_GT,
79	            "<@": TokenType.LT_AT,
80	            "?&": TokenType.QMARK_AMP,
[assistant] All five files are read. I'm making the edits now: a new token type, the Postgres keyword, the expression node, the range parser, and the Postgres generator mapping. The generator entry goes in the Postgres dialect only, since no other engine has this operator.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py", "old_string": "    QMARK_PIPE = auto()\n    HASH_DASH = auto()", "new_string": "    QMARK_PIPE = auto()\n    AT_QMARK = auto()\n    HASH_DASH = auto()"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/tokenizer_core.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBExtract(Expression, Binary, Func):\n    _sql_names = [\"JSONB_EXTRACT\"]\n", "new_string": "class JSONBExtract(Expression, Binary, Func):\n    _sql_names = [\"JSONB_EXTRACT\"]\n\n\nclass JSONBPathExists(Expression, Binary, Func):\n    pass\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py", "old_string": "        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),\n        TokenType.BETWEEN:", "new_string": "        TokenType.AT_GT: binary_range_parser(exp.ArrayContainsAll),\n        TokenType.AT_QMARK: binary_range_parser(exp.JSONBPathExists),\n        TokenType.BETWEEN:"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py", "old_string": "        exp.JSONBContains: lambda self, e: self.binary(e, \"?\"),\n", "new_string": "        exp.JSONBContains: lambda self, e: self.binary(e, \"?\"),\n        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py", "old_string": "            \"@>\": TokenType.AT_GT,\n            \"<@\": TokenType.LT_AT,", "new_string": "            \"@>\": TokenType.AT_GT,\n            \"@?\": TokenType.AT_QMARK,\n            \"<@\": TokenType.LT_AT,"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/dialects/postgres.py has been updated successfully.
[assistant] Edits are in. Now I'll probe the AST for the task's example and some variants, comparing against the sibling `?&` operator, which is the shape the skill says to copy.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_atq.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\ncases = [\n    \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n    \"SELECT doc @? '$.a' AS hit FROM events\",\n    \"SELECT * FROM events WHERE N
…[979 chars elided]…
e(ref.this).__name__, type(ref.expression).__name__)\nprint(\"repr:\", repr(sqlglot.parse_one(\"doc @? '$.a'\", read=\"postgres\")))\nfor d in [\"duckdb\", \"snowflake\", \"mysql\"]:\n    print(d, \"=>\", sqlglot.transpile(\"SELECT doc @? '$.a[*] ? (@ > 2)'\", read=\"postgres\", write=d)[0])\nEOF\nPYTHONPATH=. $PY /tmp/probe_atq.py", "description": "Probe AST shape and round-trip for @? variants"}
[tool_result] OK   SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)' | nodes: 1
      this: Column | expression: Literal | '$.a[*] ? (@ > 2)'
OK   SELECT doc @? '$.a' AS hit FROM events | nodes: 1
      this: Column | expression: Literal | '$.a'
OK   SELECT * FROM events WHERE NOT doc @? '$.a' | nodes: 1
      this: Column | expression: Literal | '$.a'
OK   SELECT * FROM events WHERE doc @? path_col AND id = 1 | nodes: 1
      this: Column | expression: Column | path_col
OK   SELECT * FROM events AS e JOIN
…[354 chars elided]…
es: 1
      this: Column | expression: Literal | '$.a'
OK   SELECT * FROM events WHERE doc ?& ARRAY['a'] | nodes: 0
sibling ?& node: JSONBContainsAllTopKeys -> Column Array
repr: JSONBPathExists(
  this=Column(
    this=Identifier(this=doc, quoted=False)),
  expression=Literal(this='$.a', is_string=True))
duckdb => SELECT J_S_O_N_B_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
snowflake => SELECT J_S_O_N_B_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
mysql => SELECT J_S_O_N_B_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
[assistant] The operator parses and round-trips, and the node has the same shape as the `?&` sibling. But the cross-dialect output is wrong: the auto-derived function name becomes `J_S_O_N_B_PATH_EXISTS`. I'll set the SQL name explicitly to `JSONB_PATH_EXISTS`, as `JSONBContains` does, and rerun.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBPathExists(Expression, Binary, Func):\n    pass\n", "new_string": "class JSONBPathExists(Expression, Binary, Func):\n    _sql_names = [\"JSONB_PATH_EXISTS\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY /tmp/probe_atq.py 2>&1 | tail -8; PYTHONPATH=. $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile(\\\"SELECT jsonb_path_exists(doc, '\\$.a')\\\", read='postgres', write='postgres')[0])\nprint(type(sqlglot.parse_one(\\\"SELECT jsonb_path_exists(doc, '\\$.a')\\\", read='postgres').selects[0]).__name__)\nprint(sqlglot.transpile(\\\"SELECT jsonb_path_exists(doc, '\\$.a')\\\", read='postgres', write='postgres')[0])\n\"", "description": "Rerun probes after naming fix and check function-form output"}
[tool_result] sibling ?& node: JSONBContainsAllTopKeys -> Column Array
repr: JSONBPathExists(
  this=Column(
    this=Identifier(this=doc, quoted=False)),
  expression=Literal(this='$.a', is_string=True))
duckdb => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
snowflake => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
mysql => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
SELECT doc @? '$.a'
JSONBPathExists
SELECT doc @? '$.a'
[assistant] The function-form `jsonb_path_exists(doc, path)` now also maps to the node, which is semantically the same. The risk is the three-argument form (`vars` argument), which previously parsed as a generic function. I'll check that it still round-trips.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; PYTHONPATH=. $PY -c \"\nimport sqlglot\nfor s in [\\\"SELECT jsonb_path_exists(doc, '\\$.a', '{\\\"x\\\": 1}')\\\", \\\"SELECT jsonb_path_exists(doc, '\\$.a', '{\\\"x\\\": 1}', true)\\\"]:\n    try:\n        print(sqlglot.transpile(s, read='postgres', write='postgres')[0])\n    except Exception as e: print('ERR', type(e).__name__, str(e).splitlines()[0])\n\"; git stash list | head -0; git show HEAD:sqlglot/expressions/json.py >/dev/null && echo \"baseline check:\" && git -c core.pager=cat log -1 --oneline", "description": "Check three-argument jsonb_path_exists form still works"}
[tool_result]   File "<string>", line 3
    for s in ["SELECT jsonb_path_exists(doc, '$.a', '{"x": 1}')", "SELECT jsonb_path_exists(doc, '$.a', '{"x": 1}', true)"]:
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: invalid syntax. Perhaps you forgot a comma?
head: illegal line count -- 0
baseline check:
3f07ecded lithify: probe base
[assistant] My inline quoting broke the script. I'll put the probe in a file instead.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_fn.py <<'EOF'\nimport sqlglot\nfor s in [\n    \"SELECT jsonb_path_exists(doc, '$.a', '{\\\"x\\\": 1}')\",\n    \"SELECT jsonb_path_exists(doc, '$.a', '{\\\"x\\\": 1}', true)\",\n]:\n    try:\n        print(sqlglot
…[98 chars elided]…
t(\"ERR\", type(e).__name__, str(e).splitlines()[0])\nEOF\nPYTHONPATH=. $PY /tmp/probe_fn.py; echo \"--- baseline (HEAD) for same:\"; rm -rf /tmp/basewt && git worktree add -q --detach /tmp/basewt HEAD 2>/dev/null; cd /tmp/basewt && PYTHONPATH=. $PY /tmp/probe_fn.py; cd - >/dev/null; git worktree remove --force /tmp/basewt", "description": "Compare 3-arg jsonb_path_exists output before and after"}
[tool_result] ERR ParseError The number of provided arguments (3) is greater than the maximum number of supported arguments (2). Line 1, Col: 48.
ERR ParseError The number of provided arguments (4) is greater than the maximum number of supported arguments (2). Line 1, Col: 54.
--- baseline (HEAD) for same:
SELECT JSONB_PATH_EXISTS(doc, '$.a', '{"x": 1}')
SELECT JSONB_PATH_EXISTS(doc, '$.a', '{"x": 1}', TRUE)
[assistant] This is a regression I need to fix. Postgres accepts `jsonb_path_exists(target, path, vars, silent)`, and the new `Func` registration rejects anything over two arguments. The old generic parse round-tripped it correctly, so the operator node must not claim the function name. I'll check how the generator handles a non-`Func` expression with no transform, to see whether a plain `Binary` node is viable.
[tool_use Bash] {"command": "grep -n 'def sql(' -A45 sqlglot/generator.py | grep -n 'handler\\|Func\\|function_fallback\\|unsupported\\|_sql' | head -30; grep -n 'def sql_names\\|_sql_names' sqlglot/expressions/core.py | head", "description": "Inspect generator fallback for non-Func expressions"}
[tool_result] 19:1102-        handler = self._dispatch.get(expression.__class__)
21:1104-        if handler:
22:1105-            sql = handler(self, expression)
23:1106-        elif isinstance(expression, exp.Func):
24:1107-            sql = self.function_fallback_sql(expression)
26:1109-            sql = self.property_sql(expression)
32:1115-    def uncache_sql(self, expression: exp.Uncache) -> str:
34:1117-        exists_sql = " IF EXISTS" if expression.args.get("exists") else ""
35:1118-        return f"UNCACHE TABLE{exists_sql} {table}"
37:1120-    def cache_sql(self, expression: exp.Cache) -> str:
1648:        _sql_names (list): the SQL name (1st item in the list) and aliases (subsequent items) for this
1655:    _sql_names: t.ClassVar[list[str]] = []
1673:    def sql_names(cls) -> list[str]:
1678:        if not cls._sql_names:
1680:        return cls._sql_names
2012:    _sql_names = ["APPROX_DISTINCT", "APPROX_COUNT_DISTINCT"]
2315:    _sql_names = ["POWER", "POW"]
[assistant] A non-`Func` node would have no generator path for other dialects, so I'll keep `Func` and make the node accept the optional `vars` and `silent` arguments. The Postgres generator will emit the `@?` operator only for the two-argument form, and fall back to the function form otherwise.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py", "old_string": "class JSONBPathExists(Expression, Binary, Func):\n    _sql_names = [\"JSONB_PATH_EXISTS\"]\n", "new_string": "class JSONBPathExists(Expression, Binary, Func):\n    arg_types = {\"this\": True, \"expression\": True, \"vars\": False, \"silent\": False}\n    _sql_names = [\"JSONB_PATH_EXISTS\"]\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/expressions/json.py has been updated successfully.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py", "offset": 320, "limit": 12}
[tool_result] 320	            suffix=f"{self.sql(e, 'order')})",
321	        ),
322	        exp.JSONExtract: _json_extract_sql("JSON_EXTRACT_PATH", "->"),
323	        exp.JSONExtractScalar: _json_extract_sql("JSON_EXTRACT_PATH_TEXT", "->>"),
324	        exp.JSONBExtract: lambda self, e: self.binary(e, "#>"),
325	        exp.JSONBExtractScalar: lambda self, e: self.binary(e, "#>>"),
326	        exp.JSONBContains: lambda self, e: self.binary(e, "?"),
327	        exp.JSONBPathExists: lambda self, e: self.binary(e, "@?"),
328	        exp.ParseJSON: lambda self, e: self.sql(exp.cast(e.this, exp.DType.JSON)),
329	        exp.JSONPathKey: json_path_key_only_name,
330	        exp.JSONPathRoot: lambda *_: "",
331	        exp.JSONPathSubscript: lambda self, e: self.json_path_part(e.this),
[assistant] The lambda won't fit the new conditional, so I'll turn it into an auto-discovered method (the form the skill prefers). I'll look at where the existing methods are in the Postgres generator to place it.
[tool_use Bash] {"command": "grep -n '    def [a-z_]*sql(self' sqlglot/generators/postgres.py | head -30", "description": "List Postgres generator method definitions"}
[tool_result] 264:    def lateral_sql(self, expression: exp.Lateral) -> str:
402:    def schemacommentproperty_sql(self, expression: exp.SchemaCommentProperty) -> str:
406:    def commentcolumnconstraint_sql(self, expression: exp.CommentColumnConstraint) -> str:
410:    def columndef_sql(self, expression: exp.ColumnDef, sep: str = " ") -> str:
422:    def unnest_sql(self, expression: exp.Unnest) -> str:
453:    def bracket_sql(self, expression: exp.Bracket) -> str:
460:    def matchagainst_sql(self, expressio
…[396 chars elided]…
-> str:
515:    def isascii_sql(self, expression: exp.IsAscii) -> str:
518:    def ignorenulls_sql(self, expression: exp.IgnoreNulls) -> str:
523:    def respectnulls_sql(self, expression: exp.RespectNulls) -> str:
529:    def currentschema_sql(self, expression: exp.CurrentSchema) -> str:
532:    def interval_sql(self, expression: exp.Interval) -> str:
542:    def placeholder_sql(self, expression: exp.Placeholder) -> str:
549:    def arraycontains_sql(self, expression: exp.ArrayContains) -> str:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py", "offset": 456, "limit": 10}
[tool_result] 456	            expression.set("this", exp.paren(expression.this, copy=False))
457	
458	        return super().bracket_sql(expression)
459	
460	    def matchagainst_sql(self, expression: exp.MatchAgainst) -> str:
461	        this = self.sql(expression, "this")
462	        expressions = [f"{self.sql(e)} @@ {this}" for e in expression.expressions]
463	        sql = " OR ".join(expressions)
464	        return f"({sql})" if len(expressions) > 1 else sql
465	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py", "old_string": "        exp.JSONBPathExists: lambda self, e: self.binary(e, \"@?\"),\n", "new_string": ""}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py", "old_string": "    def matchagainst_sql(self, expression: exp.MatchAgainst) -> str:\n        this = self.sql(expression, \"this\")\n        expressions = [f\"{self.sql(e)} @@ {this}\" for e in expression.expressions]\n   
…[291 chars elided]…
 e in expression.expressions]\n        sql = \" OR \".join(expressions)\n        return f\"({sql})\" if len(expressions) > 1 else sql\n\n    def jsonbpathexists_sql(self, expression: exp.JSONBPathExists) -> str:\n        if expression.args.get(\"vars\") or expression.args.get(\"silent\"):\n            return self.function_fallback_sql(expression)\n        return self.binary(expression, \"@?\")\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/sqlglot/generators/postgres.py has been updated successfully.
[assistant] Now I'll rerun the full probe set: the operator forms, the function form at 2, 3 and 4 arguments, and the cross-dialect output.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_final.py <<'EOF'\nimport sqlglot\nfrom sqlglot import exp\nfor sql in [\n    \"SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'\",\n    \"SELECT doc @? '$.a' AS hit FROM events\",\n    \"SELECT * FROM events WH
…[798 chars elided]…
__name__, str(e).splitlines()[0])\nfor d in [\"duckdb\", \"snowflake\", \"mysql\"]:\n    print(d, \"=>\", sqlglot.transpile(\"SELECT doc @? '$.a[*] ? (@ > 2)'\", read=\"postgres\", write=d)[0])\nprint(sqlglot.transpile(\"SELECT doc @? '$.a'\", read=\"postgres\", write=\"postgres\")[0])\nEOF\nPYTHONPATH=. $PY /tmp/probe_final.py", "description": "Probe all @? and jsonb_path_exists forms after fix"}
[tool_result] OK  SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)' | node: JSONBPathExists | vars/silent: False False
OK  SELECT doc @? '$.a' AS hit FROM events | node: JSONBPathExists | vars/silent: False False
OK  SELECT * FROM events WHERE NOT doc @? '$.a' | node: JSONBPathExists | vars/silent: False False
OK  SELECT * FROM events WHERE doc @? path_col AND id = 1 | node: JSONBPathExists | vars/silent: False False
OK  SELECT * FROM events AS e JOIN t ON e.doc @? t.p | node: JSONBPathExists | vars/silent
…[207 chars elided]…
 False False
OK  SELECT doc @? '$.a' | node: JSONBPathExists | vars/silent: False False
OK  SELECT JSONB_PATH_EXISTS(doc, '$.a', '{"x": 1}') | node: JSONBPathExists | vars/silent: True False
OK  SELECT JSONB_PATH_EXISTS(doc, '$.a', '{"x": 1}', TRUE) | node: JSONBPathExists | vars/silent: True True
duckdb => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
snowflake => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
mysql => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
SELECT doc @? '$.a'
[assistant] All ten forms now parse, and the 3- and 4-argument function forms keep their `vars` and `silent` args. Next is the test. I'll find where the Postgres tests cover the neighbouring `?&` and `@>` operators.
[tool_use Bash] {"command": "grep -n '?&\\|@>\\|<@\\|jsonb_path\\|JSONBContainsAllTopKeys' tests/dialects/test_postgres.py | head -20; grep -n 'def test_' tests/dialects/test_postgres.py | head -5", "description": "Find existing Postgres JSONB operator tests"}
[tool_result] 215:            "SELECT ARRAY[1, 2, 3] <@ ARRAY[1, 2]",
216:            "SELECT ARRAY[1, 2] @> ARRAY[1, 2, 3]",
516:            "SELECT ARRAY[1, 2, 3] @> ARRAY[1, 2]",
518:                "duckdb": "SELECT [1, 2, 3] @> [1, 2]",
521:                "duckdb": "SELECT [1, 2, 3] @> [1, 2]",
523:                "postgres": "SELECT ARRAY[1, 2, 3] @> ARRAY[1, 2]",
1045:        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
1047:            """SELECT '["a", "b"]'::jsonb ?& array['a', 'b']""",
1048:            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
1452:        for op in ("=", ">=", "<=", "<", ">", "&&", "||", "@>", "<@"):
10:    def test_postgres(self):
1125:    def test_ddl(self):
1466:    def test_unnest(self):
1491:    def test_array_offset(self):
1514:    def test_bool_or(self):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "offset": 1040, "limit": 14}
[tool_result] 1040	        self.validate_identity(
1041	            """SELECT '{"a":1, "b":2, "c":3}'::jsonb ?| array['b', 'c']""",
1042	            """SELECT CAST('{"a":1, "b":2, "c":3}' AS JSONB) ?| ARRAY['b', 'c']""",
1043	        )
1044	
1045	        self.validate_identity("a ?& b").assert_is(exp.JSONBContainsAllTopKeys)
1046	        self.validate_identity(
1047	            """SELECT '["a", "b"]'::jsonb ?& array['a', 'b']""",
1048	            """SELECT CAST('["a", "b"]' AS JSONB) ?& ARRAY['a', 'b']""",
1049	        )
1050	
1051	        self.validate_identity("a #- b").assert_is(exp.JSONBDeleteAtPath)
1052	        self.validate_identity(
1053	            """SELECT '["a", {"b":1}]'::jsonb #- '{1,b}'""",
[assistant] I'll add the tests next to the `?&` block, covering the operator in a query, the node class, the function form normalising to the operator, and the 3- and 4-argument function forms that must keep working.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py", "old_string": "            \"\"\"SELECT CAST('[\"a\", \"b\"]' AS JSONB) ?& ARRAY['a', 'b']\"\"\",\n        )\n\n", "new_string": "            \"\"\"SELECT CAST('[\"a\", \"b\"]' AS JSONB) ?& ARRAY['a', 'b']\"\"\",\n      
…[216 chars elided]…
   self.validate_identity(\n            \"\"\"SELECT jsonb_path_exists(doc, '$.a')\"\"\",\n            \"\"\"SELECT doc @? '$.a'\"\"\",\n        )\n        self.validate_identity(\n            \"\"\"SELECT JSONB_PATH_EXISTS(doc, '$.a', '{\"x\": 1}')\"\"\",\n        )\n        self.validate_identity(\n            \"\"\"SELECT JSONB_PATH_EXISTS(doc, '$.a', '{\"x\": 1}', TRUE)\"\"\",\n        )\n\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1/tests/dialects/test_postgres.py has been updated successfully.
[assistant] Next I'll run the Postgres dialect test file, using the project's pytest command from the harness notes.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_postgres.py 2>&1 | tail -30", "description": "Run Postgres dialect test file"}
[tool_result] ..........................                  [100%]
26 passed, 389 subtests passed in 0.26s
[assistant] The Postgres file passes (26 tests). Next I'll run the linter and formatter on the changed files, then the full suite as its own call.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; FILES=\"sqlglot/tokenizer_core.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py tests/dialects/test_postgres.py\"; $PY -m ruff check $FILES 2>&1 | tail -5; $PY -m ruff format --check $FILES 2>&1 | tail -5; git status --short", "description": "Lint and format-check changed files"}
[tool_result] E902 No such file or directory (os error 2)
--> sqlglot/tokenizer_core.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py tests/dialects/test_postgres.py:1:1

Found 1 error.
error: Failed to format sqlglot/tokenizer_core.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py tests/dialects/test_postgres.py: No such file or directory (os error 2)
 M sqlglot/dialects/postgres.py
 M sqlglot/expressions/json.py
 M sqlglot/generators/postgres.py
 M sqlglot/parser.py
 M sqlglot/tokenizer_core.py
 M tests/dialects/test_postgres.py
[assistant] The ruff error is my own mistake: zsh doesn't word-split `$FILES`, so ruff got one bogus path. I'll list the files literally.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff check sqlglot/tokenizer_core.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py tests/dialects/test_postgres.py; $PY -m ruff format --check sqlglot/tokenizer_core.py sqlglot/expressions/json.py sqlglot/parser.py sqlglot/generators/postgres.py sqlglot/dialects/postgres.py tests/dialects/test_postgres.py", "description": "Run ruff lint and format check on changed files"}
[tool_result] All checks passed!
6 files already formatted
[assistant] Lint and format are clean. Now the full suite, run in the foreground with the 600-second timeout as the harness requires.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 1 other pytest process(es) running; expect slower runs:
  34207 03-15:56:43 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-f4ef283b54.log
ELAPSED: 51s
SUMMARY: 1121 passed, 18178 subtests passed in 50.77s
EXIT: 0
[assistant] The full suite passes after my last edit: `SUMMARY: 1121 passed, 18178 subtests passed`, `EXIT: 0`. One open point is the cross-dialect output, which is a function call that DuckDB, Snowflake and MySQL don't define. I'll check whether that matches the pre-change output, so I can say whether it's a regression or a pre-existing gap.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; cat > /tmp/probe_xd.py <<'EOF'\nimport sqlglot\nfor d in [\"duckdb\", \"snowflake\", \"mysql\"]:\n    print(d, \"=>\", sqlglot.transpile(\"SELECT doc @? '$.a[*] ? (@ > 2)'\", read=\"postgres\", write=d)[0])\nEOF\nPYTHONPATH=. $PY /tmp/probe_xd.py; rm -rf /tmp/basewt2; git worktree add -q --detach /tmp/basewt2 HEAD && cd /tmp/basewt2 && echo \"--- baseline:\" && PYTHONPATH=. $PY /tmp/probe_xd.py; cd - >/dev/null; git worktree remove --force /tmp/basewt2; git worktree list | head -3", "description": "Compare cross-dialect output against baseline worktree"}
[tool_result] duckdb => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
snowflake => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
mysql => SELECT JSONB_PATH_EXISTS(doc, '$.a[*] ? (@ > 2)')
--- baseline:
Traceback (most recent call last):
  File "/tmp/probe_xd.py", line 3, in <module>
    print(d, "=>", sqlglot.transpile("SELECT doc @? '$.a[*] ? (@ > 2)'", read="postgres", write=d)[0])
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp
…[1497 chars elided]…
back-claude_claude-haiku-5-5/repo 004b3e122 [eval]
~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/base-1                                                                                           3f07ecded (detached HEAD)
~/.cache/lithify/work/repo-55c905b0df68/20261027-112539-postgres-dialect-support-the-jso/snapshot                                                                                         004b3e122 (detached HEAD)
[assistant] The baseline can't parse `@?` at all, so there's no earlier cross-dialect output to compare against. The `JSONB_PATH_EXISTS(...)` call for DuckDB, Snowflake and MySQL is a generic function-call fallback, and those engines don't define it. I'll leave that as an open item rather than invent a mapping. Last, I'll review the full diff.
[tool_use Bash] {"command": "git diff --stat && git diff -- sqlglot/", "description": "Review final source diff"}
[tool_result]  sqlglot/dialects/postgres.py    |  1 +
 sqlglot/expressions/json.py     |  5 +++++
 sqlglot/generators/postgres.py  |  5 +++++
 sqlglot/parser.py               |  1 +
 sqlglot/tokenizer_core.py       |  1 +
 tests/dialects/test_postgres.py | 15 +++++++++++++++
 6 files changed, 28 insertions(+)
diff --git a/sqlglot/dialects/postgres.py b/sqlglot/dialects/postgres.py
index c79d25697..aa053b765 100644
--- a/sqlglot/dialects/postgres.py
+++ b/sqlglot/dialects/postgres.py
@@ -76,6 +76,7 @@ class Po
…[2063 chars elided]…
f, this: self._parse_between(this),
         TokenType.GLOB: binary_range_parser(exp.Glob),
         TokenType.ILIKE: binary_range_parser(exp.ILike),
diff --git a/sqlglot/tokenizer_core.py b/sqlglot/tokenizer_core.py
index 77fdcb33c..0685314d8 100644
--- a/sqlglot/tokenizer_core.py
+++ b/sqlglot/tokenizer_core.py
@@ -79,6 +79,7 @@ class TokenType(IntEnum):
     DSTAR = auto()
     QMARK_AMP = auto()
     QMARK_PIPE = auto()
+    AT_QMARK = auto()
     HASH_DASH = auto()
     EXCLAMATION = auto()
[assistant] Postgres now accepts `@?`: `SELECT * FROM events WHERE doc @? '$.a[*] ? (@ > 2)'` tokenizes, parses into `exp.JSONBPathExists`, and generates back as `@?`. The full suite passes: `SUMMARY: 1121 passed, 18178 subtests passed in 50.77s`, `EXIT: 0`, run after my last edit. I did not commit.

**What changed**
- `sqlglot/tokenizer_core.py`: new `TokenType.AT_QMARK`.
- `sqlglot/dialects/postgres.py`: `"@?"` keyword mapped to `AT_QMARK`, Postgres only.
- `sqlglot/expressions/json.py`: new `JSONBPathExists(Binary, Func)` node, modelled on `JSONBContainsAllTopKeys`.
- `sqlglot/parser.py`: a range-parse
…[851 chars elided]…
(...)`.
- `tests/dialects/test_postgres.py`: 26 passed.
- `ruff check` and `ruff format --check` are clean on the changed files.

**Open item:** transpiling to other dialects emits `JSONB_PATH_EXISTS(doc, '...')`. DuckDB, Snowflake and MySQL don't define that function, so the output won't run there. I didn't map it to something like DuckDB's `json_exists`, because that path language has no filter expressions and the result wouldn't be equivalent. The request was Postgres round-trip, so I left it. If you want a target mapping, tell me which engine and whether a partial equivalent is acceptable.
