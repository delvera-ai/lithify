# trajectory base-1

final message:
`PRAGMA full_column_names=on;` now parses in the SQLite dialect and round-trips as `PRAGMA full_column_names = on`. The full suite passes (1072 tests), and ruff lint and format are clean.

**Cause:** `on` is a reserved keyword token, and the generic statement parser parsed the right-hand side of `=` as an ordinary expression, so it failed on `ON`. Values like `off`, `1` and `2` were plain identifiers or numbers, which is why they worked.

**Fix:** I added a SQLite-specific `_parse_pragma` in `sqlglot/parsers/sqlite.py` and registered it for `TokenType.PRAGMA`. The name side is parsed as before. After `=`, the value is parsed as a unary/literal expression, or as any token, so keywords like `ON`, `FULL`, `DELETE` and `DEFAULT` are accepted. Output is unchanged for all other forms.

**Tests:** I added `test_pragma` to `tests/dialects/test_sqlite.py`. It covers `ON`/`OFF`, `1`/`2`, `-2000`, quoted strings, schema-qualified names, `table_info("t")` and bare pragmas. I also checked that `quick_check`, `journal_mode`, `synchronous`, `foreign_keys` and about 30 other forms parse.

**Things to know:**
- Parenthesised pragmas are not byte-exact. `PRAGMA table_info(t)` comes out as `PRAGMA TABLE_INFO(t)`, because the function-call form goes through the generic function generator, which uppercases the name. It is semantically identical in SQLite, since pragma names are case-insensitive. Preserving the case would mean changing the AST shape, so I left it alone.
- I scoped the change to SQLite. The generic `PRAGMA` rule in `parser.py` still has the same limitation for other dialects, such as DuckDB. Say if you want it fixed in the base parser too.
- Changes are uncommitted in the worktree.

## events
[tool_use Bash] {"command": "grep -rn -i \"pragma\" sqlglot/ tests/ --include=*.py | head -60", "description": "Search for PRAGMA references in sources and tests"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rn -i \"pragma\" sqlglot/ tests/ | head -60; echo ---; ls sqlglot/dialects | head -50", "description": "Search for PRAGMA references in sources and tests"}
[tool_result] sqlglot/tokenizer_core.py:378:    PRAGMA = auto()
sqlglot/tokens.py:342:        "PRAGMA": TokenType.PRAGMA,
sqlglot/parser.py:708:        TokenType.PRAGMA,
sqlglot/parser.py:1080:        TokenType.PRAGMA: lambda self: self.expression(exp.Pragma(this=self._parse_expression())),
sqlglot/generator.py:2756:    def pragma_sql(self, expression: exp.Pragma) -> str:
sqlglot/generator.py:2757:        return f"PRAGMA {self.sql(expression, 'this')}"
sqlglot/expressions/ddl.py:161:class Pragma(Expression):

…[601 chars elided]…

tests/fixtures/identity.sql:826:PRAGMA schema.synchronous = FULL
tests/fixtures/identity.sql:827:PRAGMA schema.memory_limit = '1GB'
---
__init__.py
athena.py
bigquery.py
clickhouse.py
databricks.py
dialect.py
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
[tool_use Bash] {"command": "sed -n 155,175p sqlglot/expressions/ddl.py; echo ---; sed -n 1070,1090p sqlglot/parser.py; echo ---; sed -n 2750,2760p sqlglot/generator.py; echo ---; cat sqlglot/dialects/sqlite.py | head -80; echo ---; grep -n \"PRAGMA\\|pragma\" -i tests/dialects/test_sqlite.py; ls <work>/env-sqlglot/bin/python 2>&1", "description": "Inspect Pragma expression, parser, generator, and SQLite dialect"}
[tool_result] class Kill(Expression):
    arg_types = {"this": True, "kind": False}


class Pragma(Expression):
    pass


class Declare(Expression):
    arg_types = {"expressions": True, "replace": False}


class DeclareItem(Expression):
    arg_types = {"this": True, "kind": False, "default": False}


class Set(Expression):
    arg_types = {"expressions": False, "unset": False, "tag": False}

---
        TokenType.DESC: lambda self: self._parse_describe(),
        TokenType.DESCRIBE: lambda self: self._pars
…[2404 chars elided]…
r.KEYWORDS,
            "ATTACH": TokenType.ATTACH,
            "DETACH": TokenType.DETACH,
            "INDEXED BY": TokenType.INDEXED_BY,
            "MATCH": TokenType.MATCH,
        }

        KEYWORDS.pop("/*+")

        COMMANDS = {*tokens.Tokenizer.COMMANDS, TokenType.REPLACE}

    Parser = SQLiteParser

    Generator = SQLiteGenerator
---
<work>/env-sqlglot/bin/python
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor q in ['PRAGMA full_column_names=on;','PRAGMA full_column_names=off','PRAGMA journal_mode','PRAGMA table_info(t)','PRAGMA main.table_info(\\\"t\\\")','PRAGMA cache_size=-2000','PRAGMA foreign_keys = ON
…[80 chars elided]…
'PRAGMA index_info(idx)']:\n    try: print(repr(sqlglot.parse_one(q, read='sqlite')), '=>', sqlglot.transpile(q, read='sqlite', write='sqlite'))\n    except Exception as e: print(q, 'ERR', e)\n\"; cat sqlglot/parsers/sqlite.py | head -150; wc -l sqlglot/parsers/sqlite.py sqlglot/generators/sqlite.py; git log --oneline -1", "description": "Reproduce PRAGMA parse failures and inspect SQLite parser"}
[tool_result] PRAGMA full_column_names=on; ERR Required keyword: 'expression' missing for <class 'sqlglot.expressions.core.EQ'>. Line 1, Col: 27.
  PRAGMA full_column_names=[4mon[0m;
Pragma(
  this=EQ(
    this=Column(
      this=Identifier(this=full_column_names, quoted=False)),
    expression=Column(
      this=Identifier(this=off, quoted=False)))) => ['PRAGMA full_column_names = off']
Pragma(
  this=Column(
    this=Identifier(this=journal_mode, quoted=False))) => ['PRAGMA journal_mode']
Pragma(
  this=A
…[3940 chars elided]…
ession(exp.ModuleProperty(this=name, expressions=expressions))

    def _parse_attach_detach(self, is_attach=True) -> exp.Attach | exp.Detach:
        self._match(TokenType.DATABASE)
        this = self._parse_expression()

        return (
            self.expression(exp.Attach(this=this))
            if is_attach
            else self.expression(exp.Detach(this=this))
        )
      83 sqlglot/parsers/sqlite.py
     322 sqlglot/generators/sqlite.py
     405 total
d342c60ff lithify: probe base
[tool_use Bash] {"command": "grep -n \"def _parse_var\\b\\|def _parse_primary\\|def _parse_column\\b\\|def _parse_column_ops\\|def _parse_field\\|def _parse_table_parts\\|def _parse_function\\b\\|def _parse_id_var\\|def _parse_unary\\|def _parse_var_or_string\\|def _parse_string\\b\\|def _parse_number\" sqlglot/parser.py sqlglot/parsers/*.py; grep -n \"Pragma\\|PRAGMA\" sqlglot/parser.py sqlglot/parsers/*.py sqlglot/generators/*.py sqlglot/generator.py; grep -n \"PRAGMA\\|pragma\" -ri tests/ | grep -v identity.sql | head; sed -n 1,20p tests/dialects/test_sqlite.py", "description": "Locate parser helpers and existing PRAGMA test references"}
[tool_result] sqlglot/parser.py:4528:    def _parse_table_parts_fast(self) -> t.Optional[exp.Table]:
sqlglot/parser.py:4591:    def _parse_table_parts(
sqlglot/parser.py:5963:    def _parse_unary(self) -> t.Optional[exp.Expr]:
sqlglot/parser.py:6388:    def _parse_column(self) -> t.Optional[exp.Expr]:
sqlglot/parser.py:6575:    def _parse_column_ops(self, this: t.Optional[exp.Expr]) -> t.Optional[exp.Expr]:
sqlglot/parser.py:6673:    def _parse_primary(self) -> t.Optional[exp.Expr]:
sqlglot/parser.py:6695:   
…[2664 chars elided]…
ntity("SELECT * FROM t INDEXED BY i")
        self.validate_identity("SELECT * FROM t NOT INDEXED")
        self.validate_identity("SELECT match FROM t")
        self.validate_identity("SELECT rowid FROM t1 WHERE t1 MATCH 'lorem'")
        self.validate_identity("SELECT RANK() OVER (RANGE CURRENT ROW) FROM tbl")
        self.validate_identity("UNHEX(a, b)")
        self.validate_identity("SELECT DATE()")
        self.validate_identity("SELECT DATE('now', 'start of month', '+1 month', '-1 day')")
[tool_use Bash] {"command": "sed -n 8227,8295p sqlglot/parser.py; sed -n 6673,6695p sqlglot/parser.py; grep -n \"def _parse_statement\" -A30 sqlglot/parser.py | head -50", "description": "Read parser helper implementations"}
[tool_result]     def _parse_id_var(
        self,
        any_token: bool = True,
        tokens: t.Optional[t.Collection[TokenType]] = None,
    ) -> t.Optional[exp.Expr]:
        expression = self._parse_identifier()
        if not expression and (
            (any_token and self._advance_any()) or self._match_set(tokens or self.ID_VAR_TOKENS)
        ):
            quoted = self._prev.token_type == TokenType.STRING
            expression = self._identifier_expression(quoted=quoted)

        return express
…[4033 chars elided]…
ression = self._parse_pipe_syntax_query(expression)
2259-
2260-        return self._parse_query_modifiers(expression)
2261-
2262-    def _parse_drop(self, exists: bool = False) -> exp.Drop | exp.Command:
2263-        start = self._prev
2264-        temporary = self._match(TokenType.TEMPORARY)
2265-        materialized = self._match_text_seq("MATERIALIZED")
2266-        iceberg = self._match_text_seq("ICEBERG")
2267-
2268-        kind = self._match_set(self.CREATABLES) and self._prev.text.upper()
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nfrom sqlglot.dialects.sqlite import SQLite\nfrom sqlglot.tokens import TokenType\nprint('ON' , TokenType.ON in SQLite.Parser.RESERVED_TOKENS, 'FULL', TokenType.FULL in SQLite.Parser.RESERVED_TOKENS, 'DELETE', TokenType.D
…[73 chars elided]…
A main.table_info(\\\"t\\\")','PRAGMA wal_checkpoint(TRUNCATE)','PRAGMA journal_mode=DELETE','PRAGMA synchronous=FULL','PRAGMA journal_mode = WAL','PRAGMA x = NULL','PRAGMA temp_store = DEFAULT']:\n    try: print(q, '=>', sqlglot.transpile(q, read='sqlite', write='sqlite'))\n    except Exception as e: print(q, 'ERR', str(e)[:120])\n\"", "description": "Check reserved tokens and more PRAGMA forms"}
[tool_result] ON False FULL False DELETE False
PRAGMA main.table_info("t") => ['PRAGMA main.table_info("t")']
PRAGMA wal_checkpoint(TRUNCATE) => ['PRAGMA WAL_CHECKPOINT(TRUNCATE)']
PRAGMA journal_mode=DELETE => ['PRAGMA journal_mode = DELETE']
PRAGMA synchronous=FULL => ['PRAGMA synchronous = FULL']
PRAGMA journal_mode = WAL => ['PRAGMA journal_mode = WAL']
PRAGMA x = NULL => ['PRAGMA x = NULL']
PRAGMA temp_store = DEFAULT => ['PRAGMA temp_store = DEFAULT']
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY - <<'EOF'\nimport sqlglot\nvals = ['ON','OFF','on','off','TRUE','FALSE','YES','NO','1','0','2','-2000','FULL','NORMAL','EXTRA','DELETE','TRUNCATE','PERSIST','MEMORY','WAL','EXCLUSIVE','DEFAULT','FILE','NONE','NULL',\"'1GB'\",'\"x\"']\nfor v in vals:\n    q = f'PRAGMA full_column_names={v}'\n    try: print(q, '=>', sqlglot.transpile(q, read='sqlite', write='sqlite'))\n    except Exception as e: print(q, 'ERR', str(e).splitlines()[0][:100])\nEOF", "description": "Survey which PRAGMA value keywords fail to parse"}
[tool_result] PRAGMA full_column_names=ON ERR Required keyword: 'expression' missing for <class 'sqlglot.expressions.core.EQ'>. Line 1, Col: 27.
PRAGMA full_column_names=OFF => ['PRAGMA full_column_names = OFF']
PRAGMA full_column_names=on ERR Required keyword: 'expression' missing for <class 'sqlglot.expressions.core.EQ'>. Line 1, Col: 27.
PRAGMA full_column_names=off => ['PRAGMA full_column_names = off']
PRAGMA full_column_names=TRUE => ['PRAGMA full_column_names = TRUE']
PRAGMA full_column_names=FALSE => [
…[1004 chars elided]…
]
PRAGMA full_column_names=EXCLUSIVE => ['PRAGMA full_column_names = EXCLUSIVE']
PRAGMA full_column_names=DEFAULT => ['PRAGMA full_column_names = DEFAULT']
PRAGMA full_column_names=FILE => ['PRAGMA full_column_names = FILE']
PRAGMA full_column_names=NONE => ['PRAGMA full_column_names = NONE']
PRAGMA full_column_names=NULL => ['PRAGMA full_column_names = NULL']
PRAGMA full_column_names='1GB' => ["PRAGMA full_column_names = '1GB'"]
PRAGMA full_column_names="x" => ['PRAGMA full_column_names = "x"']
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-ac71fed373fa/20261026-132112-sqlite-dialect-support-the-full/base-1/sqlglot/parsers/sqlite.py", "old_string": "        TokenType.DETACH: lambda self: self._parse_attach_detach(is_attach=False),\n    }", "new_string": "        TokenType.DETACH: lambda self: self._parse_attach_detach(is_attach=False),\n        TokenType.PRAGMA: lambda self: self._parse_pragma(),\n    }"}
[tool_result] The file ~/.cache/lithify/work/repo-ac71fed373fa/20261026-132112-sqlite-dialect-support-the-full/base-1/sqlglot/parsers/sqlite.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-ac71fed373fa/20261026-132112-sqlite-dialect-support-the-full/base-1/sqlglot/parsers/sqlite.py", "old_string": "        return self.expression(exp.ModuleProperty(this=name, expressions=expressions))\n", "new_string": "        return self.expression(exp.ModuleProperty(this=name, expressions=expressions))\n\n    def _parse_p
…[3 chars elided]…
ma(self) -> exp.Pragma:\n        # https://sqlite.org/pragma.html: values may be keywords such as ON, FULL or DELETE\n        this = self._parse_column()\n        if self._match(TokenType.EQ):\n            value = self._parse_unary() or self._parse_var(any_token=True)\n            this = self.expression(exp.EQ(this=this, expression=value))\n        return self.expression(exp.Pragma(this=this))\n"}
[tool_result] The file ~/.cache/lithify/work/repo-ac71fed373fa/20261026-132112-sqlite-dialect-support-the-full/base-1/sqlglot/parsers/sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -I - <<'EOF'\nimport sys; sys.path.insert(0, '.')\nimport sqlglot\nqs = ['PRAGMA full_column_names=on;','PRAGMA full_column_names=ON','PRAGMA full_column_names=off','PRAGMA full_column_names=1','PRAGMA full_column_names=2','PRA
…[565 chars elided]…
', 'PRAGMA auto_vacuum = FULL', 'PRAGMA page_size = 4096', 'PRAGMA defer_foreign_keys = yes', 'PRAGMA locking_mode = EXCLUSIVE', 'PRAGMA cache_size = -2000;']\nfor q in qs:\n    try: print(q, '=>', sqlglot.transpile(q, read='sqlite', write='sqlite'))\n    except Exception as e: print(q, 'ERR', str(e).splitlines()[0][:120])\nEOF", "description": "Verify PRAGMA forms parse and round-trip in SQLite"}
[tool_result] PRAGMA full_column_names=on; => ['PRAGMA full_column_names = on']
PRAGMA full_column_names=ON => ['PRAGMA full_column_names = ON']
PRAGMA full_column_names=off => ['PRAGMA full_column_names = off']
PRAGMA full_column_names=1 => ['PRAGMA full_column_names = 1']
PRAGMA full_column_names=2 => ['PRAGMA full_column_names = 2']
PRAGMA journal_mode => ['PRAGMA journal_mode']
PRAGMA table_info(t) => ['PRAGMA TABLE_INFO(t)']
PRAGMA main.table_info("t") => ['PRAGMA main.table_info("t")']
PRAGMA cache_size
…[832 chars elided]…
y_alter_table=ON => ['PRAGMA legacy_alter_table = ON']
PRAGMA writable_schema = on => ['PRAGMA writable_schema = on']
PRAGMA incremental_vacuum(10) => ['PRAGMA INCREMENTAL_VACUUM(10)']
PRAGMA auto_vacuum = FULL => ['PRAGMA auto_vacuum = FULL']
PRAGMA page_size = 4096 => ['PRAGMA page_size = 4096']
PRAGMA defer_foreign_keys = yes => ['PRAGMA defer_foreign_keys = yes']
PRAGMA locking_mode = EXCLUSIVE => ['PRAGMA locking_mode = EXCLUSIVE']
PRAGMA cache_size = -2000; => ['PRAGMA cache_size = -2000']
[assistant] All forms from the SQLite docs now parse and round-trip. Next I'll add regression tests to the SQLite test file.
[tool_use Bash] {"command": "grep -n \"def test_\\|def validate_identity\" tests/dialects/test_sqlite.py tests/dialects/test_dialect.py | head -40; grep -n \"def test_\" tests/dialects/test_sqlite.py | tail -3; tail -5 tests/dialects/test_sqlite.py", "description": "Inspect SQLite test structure"}
[tool_result] tests/dialects/test_sqlite.py:10:    def test_sqlite(self):
tests/dialects/test_sqlite.py:200:    def test_strftime(self):
tests/dialects/test_sqlite.py:223:    def test_datediff(self):
tests/dialects/test_sqlite.py:237:    def test_hexadecimal_literal(self):
tests/dialects/test_sqlite.py:246:    def test_window_null_treatment(self):
tests/dialects/test_sqlite.py:254:    def test_longvarchar_dtype(self):
tests/dialects/test_sqlite.py:260:    def test_warnings(self):
tests/dialects/test_sqlite.py
…[1979 chars elided]…
(self):
tests/dialects/test_dialect.py:2953:    def test_nullsafe_eq(self):
tests/dialects/test_dialect.py:2966:    def test_nullsafe_neq(self):
278:    def test_ddl(self):
347:    def test_analyze(self):
351:    def test_create_trigger(self):

        self.validate_identity(
            "CREATE TRIGGER view_insert INSTEAD OF INSERT ON employee_view BEGIN INSERT INTO employees (id, name, department) VALUES (NEW.id, NEW.name, NEW.department) END",
            check_command_warning=True,
        )
[tool_use Bash] {"command": "cat >> tests/dialects/test_sqlite.py <<'EOF'\n\n    def test_pragma(self):\n        self.validate_identity(\"PRAGMA full_column_names = ON\")\n        self.validate_identity(\"PRAGMA full_column_names = OFF\")\n        self.validate_identity(\"PRAGMA full_column_names = 1\")\n        self.validate_identity(\"PRAGMA full_column_names = 2\")\n        self.validate_identity(\"PRAGMA jour
…[488 chars elided]…
identity(\"PRAGMA full_column_names=on\", \"PRAGMA full_column_names = on\")\nEOF\nPY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py 2>&1 | tail -15", "description": "Add PRAGMA regression test and run SQLite tests"}
[tool_result] .......... [ 83%]
..                                                                      [100%]
12 passed, 63 subtests passed in 0.17s
[assistant] SQLite tests pass. Now the full project suite, plus lint on the changed files.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -8; ($PY -m ruff check sqlglot/parsers/sqlite.py tests/dialects/test_sqlite.py && $PY -m ruff format --check sqlglot/parsers/sqlite.py tests/dialects/test_sqlite.py) 2>&1 | tail -5; git status --short", "description": "Run full test suite, ruff lint and format check"}
[tool_result] ........ [ 64%]
................................................................................... [ 71%]
............................................. [ 76%]
............................................. [ 80%]
........................................................................................ [ 88%]
................................................................................................................... [ 99%]
........                                                            [100%]
1072 passed, 17805 subtests passed in 45.75s
All checks passed!
Would reformat: tests/dialects/test_sqlite.py
1 file would be reformatted, 1 file already formatted
 M sqlglot/parsers/sqlite.py
 M tests/dialects/test_sqlite.py
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --diff tests/dialects/test_sqlite.py 2>&1 | head -30", "description": "Show the formatting diff for the test file"}
[tool_result] --- tests/dialects/test_sqlite.py
+++ tests/dialects/test_sqlite.py
@@ -375,7 +375,7 @@
         self.validate_identity("PRAGMA cache_size = -2000")
         self.validate_identity("PRAGMA memory_limit = '1GB'")
         self.validate_identity("PRAGMA schema.synchronous = 2")
-        self.validate_identity("PRAGMA main.table_info(\"t\")")
+        self.validate_identity('PRAGMA main.table_info("t")')
         self.validate_identity("PRAGMA quick_check")
         self.validate_identity("PRAGMA QUICK_CHECK(0)")
         self.validate_identity("PRAGMA full_column_names=on", "PRAGMA full_column_names = on")

1 file would be reformatted
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-ac71fed373fa/20261026-132112-sqlite-dialect-support-the-full/base-1/tests/dialects/test_sqlite.py", "old_string": "        self.validate_identity(\"PRAGMA main.table_info(\\\"t\\\")\")", "new_string": "        self.validate_identity('PRAGMA main.table_info(\"t\")')"}
[tool_result] The file ~/.cache/lithify/work/repo-ac71fed373fa/20261026-132112-sqlite-dialect-support-the-full/base-1/tests/dialects/test_sqlite.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m ruff format --check sqlglot/parsers/sqlite.py tests/dialects/test_sqlite.py && $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_sqlite.py 2>&1 | tail -2; git diff sqlglot/", "description": "Recheck formatting, rerun SQLite tests, show source diff"}
[tool_result] 2 files already formatted
..                                                                      [100%]
12 passed, 63 subtests passed in 0.08s
diff --git a/sqlglot/parsers/sqlite.py b/sqlglot/parsers/sqlite.py
index 68eb69046..78ca9e87e 100644
--- a/sqlglot/parsers/sqlite.py
+++ b/sqlglot/parsers/sqlite.py
@@ -47,6 +47,7 @@ class SQLiteParser(parser.Parser):
         **parser.Parser.STATEMENT_PARSERS,
         TokenType.ATTACH: lambda self: self._parse_attach_detach(),
         TokenType.DETACH
…[388 chars elided]…
.html: values may be keywords such as ON, FULL or DELETE
+        this = self._parse_column()
+        if self._match(TokenType.EQ):
+            value = self._parse_unary() or self._parse_var(any_token=True)
+            this = self.expression(exp.EQ(this=this, expression=value))
+        return self.expression(exp.Pragma(this=this))
+
     def _parse_attach_detach(self, is_attach=True) -> exp.Attach | exp.Detach:
         self._match(TokenType.DATABASE)
         this = self._parse_expression()
[assistant] `PRAGMA full_column_names=on;` now parses in the SQLite dialect and round-trips as `PRAGMA full_column_names = on`. The full suite passes (1072 tests), and ruff lint and format are clean.

**Cause:** `on` is a reserved keyword token, and the generic statement parser parsed the right-hand side of `=` as an ordinary expression, so it failed on `ON`. Values like `off`, `1` and `2` were plain identifiers or numbers, which is why they worked.

**Fix:** I added a SQLite-specific `_parse_pragma` in `sqlglot/parsers/sqlite.py` and registered it for `TokenType.PRAGMA`. The name side is parsed as before
…[504 chars elided]…
ow:**
- Parenthesised pragmas are not byte-exact. `PRAGMA table_info(t)` comes out as `PRAGMA TABLE_INFO(t)`, because the function-call form goes through the generic function generator, which uppercases the name. It is semantically identical in SQLite, since pragma names are case-insensitive. Preserving the case would mean changing the AST shape, so I left it alone.
- I scoped the change to SQLite. The generic `PRAGMA` rule in `parser.py` still has the same limitation for other dialects, such as DuckDB. Say if you want it fixed in the base parser too.
- Changes are uncommitted in the worktree.
