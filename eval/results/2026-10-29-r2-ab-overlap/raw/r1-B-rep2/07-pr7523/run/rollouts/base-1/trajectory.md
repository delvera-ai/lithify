# trajectory base-1

final message:
`UPDATE` and `DELETE` now accept optimizer hints in the MySQL dialect, and the hints round-trip. The full test suite passes (1087 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, matching what `Select` and `Insert` already have.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` parse the hint right after the keyword. The tokenizer already emitted hint tokens after `UPDATE` and `DELETE`, so no tokenizer change was needed.
- **`sqlglot/generator.py`**: `update_sql` and `delete_sql` emit the hint after the keyword.
- **`tests/dialects/test_mysql.py`**: three identity tests covering an `UPDATE` hint, a `DELETE` hint, and a multi-table `DELETE` hint.

I put the change in the base parser and generator rather than the MySQL class, since that is where `SELECT` and `INSERT` hints already live. Other dialects that tokenize hints will now also parse hints on `UPDATE` and `DELETE`.

I did not commit anything.

## events
[tool_use Bash] {"command": "git status --short && grep -n \"HINT\\|hint\" sqlglot/parser.py | head -80 && grep -n \"hint\" sqlglot/dialects/mysql.py sqlglot/generator.py | head -40", "description": "Find hint handling in parser and generator"}
[tool_use Bash] {"command": "grep -n \"/\\*+\" tests/dialects/test_mysql.py | head -30; grep -n \"hint\" tests/dialects/test_mysql.py | head -30", "description": "Locate hint handling and existing MySQL hint tests"}
[tool_result] 5 matches in 1 files:

tests/dialects/test_mysql.py:126:"/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
tests/dialects/test_mysql.py:127:"/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
tests/dialects/test_mysql.py:249:self.validate_identity("SELECT /*+ BKA(t1) NO_BKA(t2) */ * FROM t1 INNER JOIN...
tests/dialects/test_mysql.py:250:self.validate_identity("SELECT /*+ MERGE(dt) */ * FROM (SELECT * FROM t1) AS ...
tests/dialects/test_mysql.py:251:self.validate_identity("SELECT /*+ INDEX(t, i) */ c1 FROM t WHERE c2 = 'value'")
3 matches in 1 files:

tests/dialects/test_mysql.py:126:"/*left*/ EXPLAIN SELECT /*hint*/ col FROM t1 /*right*/",
tests/dialects/test_mysql.py:127:"/* left */ DESCRIBE /* hint */ SELECT col FROM t1 /* right */",
tests/dialects/test_mysql.py:298:# Index hints
[tool_result] ok35 matches in 18 files:

1042:0:lambda self: self._parse_hint_body(),
1656:0:t.ClassVar = {TokenType.FORCE, TokenType.IGNORE, TokenType.USE}
4098:0:
4106:0:
4109:0:
4117:0:self._parse_hint_function_call() or self._parse_var(upper=True),
4131:0:
4132:0:
4387:0:
4509:0:
4510:0:list[exp.Expr] = []
4512:0://learn.microsoft.com/en-us/sql/t-sql/queries/hints-transact-sql-table?view=s...
4524:0://dev.mysql.com/doc/refman/8.0/en/index-hints.html
4525:0:
6339:0:col_name Type
7994:0:str) -> exp.JoinHint
…[2148 chars elided]…
3063:hint = self.sql(expression, "hint")
sqlglot/generator.py:3109:...p_distinct = f"{distinct}{hint}{top}" if self.LIMIT_IS_TOP else f"{top}{hint}{di...
sqlglot/generator.py:4439:def joinhint_sql(self, expression: exp.JoinHint) -> str:
sqlglot/generator.py:4484:hints = table.args.get("hints")
sqlglot/generator.py:4485:if hints and table.alias and isinstance(hints[0], exp.WithTableHint):
sqlglot/generator.py:4486:...-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_alias]
[tool_use Bash] {"command": "sed -n 3385,3440p sqlglot/parser.py; echo ----; sed -n 3790,3840p sqlglot/parser.py; echo ----; sed -n 4095,4135p sqlglot/parser.py; echo ----; sed -n 1825,1840p sqlglot/generator.py; echo ----; sed -n 2150,2200p sqlglot/generator.py; echo ----; sed -n 3055,3070p sqlglot/generator.py; echo; sed -n 2140,2160p sqlglot/generator.py | head -0", "description": "Read hint parsing and generation code paths"}
[tool_result ERROR] Exit code 1
            expression = parse_conditional_insert()

        return self.expression(
            exp.MultitableInserts(kind=kind, expressions=expressions, source=self._parse_table()),
            comments=comments,
        )

    def _parse_insert(self) -> exp.Insert | exp.MultitableInserts:
        comments: list[str] = []
        hint = self._parse_hint()
        overwrite = self._match(TokenType.OVERWRITE)
        ignore = self._match(TokenType.IGNORE)
        local = self._match_
…[8304 chars elided]…
       into = expression.args.get("into")
        if not self.SUPPORTS_SELECT_INTO and into:
            into.pop()

        hint = self.sql(expression, "hint")
        distinct = self.sql(expression, "distinct")
        distinct = f" {distinct}" if distinct else ""
        kind = self.sql(expression, "kind")

        limit = expression.args.get("limit")
        if isinstance(limit, exp.Limit) and self.LIMIT_IS_TOP:
            top = self.limit_sql(limit, top=True)

head: illegal line count -- 0
[tool_use Bash] {"command": "grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_insert\\|def _parse_select\" sqlglot/parser.py; grep -n \"class Update\\|class Delete\\|class Insert\\|class Select\" sqlglot/expressions/*.py sqlglot/expressions.py 2>/dev/null; grep -n \"def update_sql\\|def delete_sql\" -A30 sqlglot/generator.py | head -80", "description": "Locate update/delete parsing and generation"}
[tool_result] 7 matches in 6 files:

3392:0:
3450:0:
3582:0:
3605:0:
8384:0:bool = False) -> exp.Expr | None:
sqlglot/parser.py:3735:def _parse_select(
sqlglot/parser.py:3760:def _parse_select_query(
5 matches in 2 files:

sqlglot/expressions/dml.py:71:class Delete(Expression, DML):
sqlglot/expressions/dml.py:194:class Insert(Expression, DDL, DML):
sqlglot/expressions/dml.py:293:class Update(Expression, DML):
sqlglot/expressions/query.py:79:class Selectable(Expr):
sqlglot/expressions/query.py:1122:class Selec
…[2935 chars elided]…
490-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2491-            args = self.expressions(expression)
2492-            alias = self.sql(expression, "alias")
2493-            values = f"VALUES{self.seg('')}{args}"
2494-            values = (
2495-                f"({values})"
2496-                if self.WRAP_DERIVED_VALUES
2497-                and (alias or isinstance(expression.parent, (exp.From, exp.Table)))
2498-                else values
2499-            )
[tool_use Bash] {"command": "sed -n 71,90p sqlglot/expressions/dml.py; echo ----; sed -n 194,215p sqlglot/expressions/dml.py; echo ----; sed -n 293,310p sqlglot/expressions/dml.py; echo ----; grep -n \"UPDATE\\|DELETE\\|def _parse_update\\|def _parse_delete\" sqlglot/parser.py | head -40; echo ----; grep -n \"HINT\" sqlglot/tokens.py sqlglot/dialects/mysql.py | head", "description": "Inspect DML expression args and update/delete parsing"}
[tool_result] class Delete(Expression, DML):
    arg_types = {
        "with_": False,
        "this": False,
        "using": False,
        "where": False,
        "returning": False,
        "order": False,
        "limit": False,
        "tables": False,  # Multiple-Table Syntax (MySQL)
        "cluster": False,  # Clickhouse
    }

    def delete(
        self,
        table: ExpOrStr,
        dialect: DialectType = None,
        copy: bool = True,
        **opts: Unpack[ParserNoDialectArgs],
    ) -> De
…[2231 chars elided]…
ches in 1 files:

sqlglot/tokens.py:54:HINT_START: t.ClassVar[str]
sqlglot/tokens.py:64:TOKENS_PRECEDING_HINT: t.ClassVar[set[TokenType]]
sqlglot/tokens.py:106:if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:107:cls._COMMENTS[cls.HINT_START] = "*/"
sqlglot/tokens.py:184:HINT_START = "/*+"
sqlglot/tokens.py:186:TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, T...
sqlglot/tokens.py:204:HINT_START: TokenType.HINT,
sqlglot/tokens.py:560:hint_start=self.HINT_START,
[tool_use Bash] {"command": "sed -n 180,190p sqlglot/tokens.py; grep -n \"TOKENS_PRECEDING_HINT\" -B3 -A10 sqlglot/tokens.py | sed -n 1,60p; echo ----; grep -n \"def _parse_update\\|def _parse_delete\\|def _parse_delete_update\" sqlglot/parser.py; grep -n \"_parse_update\\b\\|_parse_delete\\b\" sqlglot/parser.py sqlglot/dialects/*.py | head", "description": "Check hint tokenization and update/delete parser methods"}
[tool_result]     STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS = True

    NESTED_COMMENTS = True

    HINT_START = "/*+"

    TOKENS_PRECEDING_HINT = {TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE}

    # Autofilled
    _COMMENTS: t.ClassVar[dict[str, str | None]] = {}
    _FORMAT_STRINGS: t.ClassVar[dict[str, tuple[str, TokenType]]] = {}
61-    HEREDOC_TAG_IS_IDENTIFIER: t.ClassVar[bool]
62-    STRING_ESCAPES_ALLOWED_IN_RAW_STRINGS: t.ClassVar[bool]
63-    NESTED_COMMENTS: t.ClassVar[bool]
…[2042 chars elided]…
mbers_can_be_underscore_separated=self.dialect.NUMBERS_CAN_BE_UNDERSCORE_SEPARATED,
571-            numbers_can_have_decimals=self.NUMBERS_CAN_HAVE_DECIMALS,
----
2 matches in 2 files:

3582:0:
3605:0:
4 matches in 1 files:

sqlglot/parser.py:1075:TokenType.DELETE: lambda self: self._parse_delete(),
sqlglot/parser.py:1093:TokenType.UPDATE: lambda self: self._parse_update(),
sqlglot/parser.py:3582:def _parse_delete(self) -> exp.Delete:
sqlglot/parser.py:3605:def _parse_update(self) -> exp.Update:
[tool_use Bash] {"command": "sed -n 3582,3635p sqlglot/parser.py; echo ----; sed -n 240,260p tests/dialects/test_mysql.py; grep -n \"OPTION\\|hint\" tests/dialects/test_tsql.py | head -5", "description": "Read update/delete parser methods and existing tests"}
[tool_result]     def _parse_delete(self) -> exp.Delete:
        # This handles MySQL's "Multiple-Table Syntax"
        # https://dev.mysql.com/doc/refman/8.0/en/delete.html
        tables = None
        if not self._match(TokenType.FROM, advance=False):
            tables = self._parse_csv(self._parse_table) or None

        returning = self._parse_returning()

        return self.expression(
            exp.Delete(
                tables=tables,
                this=self._match(TokenType.FROM) and self._par
…[3224 chars elided]…
identity("""SELECT * FROM foo WHERE 'ab' MEMBER OF(content)""")
        self.validate_identity("SELECT CURRENT_TIMESTAMP(6)")
        self.validate_identity("SELECT CURRENT_ROLE()")
        self.validate_identity("SELECT CURTIME()", "SELECT CURRENT_TIME()")
        self.validate_identity("x ->> '$.name'")
10 matches in 3 files:

2090:0:
635:0:"SELECT col FROM t OPTION(LABEL = 'foo')",
tests/dialects/test_tsql.py:598:# These should be un-commented once support for the OPTION clause is added fo...
[assistant] The hint tokenizer already emits `HINT` tokens after `UPDATE` and `DELETE`, so the gap is in the parser and generator. I'll add a `hint` arg to `Update` and `Delete`, parse it, and emit it.
[tool_use Bash] {"command": "python3 - <<'EOF'\nimport re\ndef edit(path, old, new, count=1):\n    s = open(path).read()\n    assert s.count(old) == count, (path, s.count(old), old[:60])\n    open(path, \"w\").write(s.replace(old, new))\n\nedit(\"sqlglot/expressions/dml.py\",\n'''class Delete(Expression, DML):\n    arg_types = {\n        \"with_\": False,\n''',\n'''class Delete(Expression, DML):\n    arg_types = 
…[3376 chars elided]…
-c \"\nimport sqlglot\nfor s in ['UPDATE /*+ NO_MERGE */ t1 SET c1 = 1 WHERE c2 = 2','DELETE /*+ QB_NAME(del) */ FROM t1 WHERE c1 = 1','DELETE /*+ NO_MERGE */ t1, t2 FROM t1 INNER JOIN t2 ON t1.id = t2.id','UPDATE /*+ X */ t SET a=1 FROM u WHERE t.id=u.id']:\n    print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n\"", "description": "Apply hint support edits and check round-trip output"}
[tool_result]  sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 3 +++
 4 files changed, 12 insertions(+), 2 deletions(-)
UPDATE /*+ NO_MERGE */ t1 SET c1 = 1 WHERE c2 = 2
DELETE /*+ QB_NAME(del) */ FROM t1 WHERE c1 = 1
DELETE /*+ NO_MERGE */ t1, t2 FROM t1 INNER JOIN t2 ON t1.id = t2.id
UPDATE /*+ X */ t JOIN u ON TRUE SET t.a = 1 WHERE t.id = u.id
[assistant] Round-trips look right. The last output's `JOIN ON TRUE` rewrite is existing MySQL `UPDATE ... FROM` behavior, not something this change touches. Now the project's test command:
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15; (ruff --version && ruff check sqlglot tests/dialects/test_mysql.py && ruff format --check sqlglot tests/dialects/test_mysql.py) 2>&1 | tail -5", "description": "Run project test suite and lint checks"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[309 chars elided]…
.......................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 51.45s
Ruff format: 1 files need formatting
═══════════════════════════════════════
1. test_mysql.py

[hint] Run `ruff format` to format these files
[assistant] All 1087 tests pass. Ruff flags the test file, so I'll format it and check that only my lines changed.
[tool_use Bash] {"command": "ruff format tests/dialects/test_mysql.py && ruff check sqlglot tests/dialects/test_mysql.py && ruff format --check sqlglot tests/dialects/test_mysql.py && git diff --stat && git diff tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -2", "description": "Format test file, re-lint, and rerun MySQL tests"}
[tool_result] 1 file reformatted
Ruff: No issues found
174 files already formatted
sqlglot/expressions/dml.py   | 2 ++
 sqlglot/generator.py         | 6 ++++--
 sqlglot/parser.py            | 3 +++
 tests/dialects/test_mysql.py | 5 +++++
 4 files changed, 14 insertions(+), 2 deletions(-)
tests/dialects/test_mysql.py | 5 +++++
 1 file changed, 5 insertions(+)

--- Changes ---

tests/dialects/test_mysql.py
  @@ -249,6 +249,11 @@ class TestMySQL(Validator):
  +        self.validate_identity("UPDATE /*+ NO_MERGE 
…[131 chars elided]…
f.validate_identity(
  +            "DELETE /*+ NO_MERGE */ t1, t2 FROM t1 INNER JOIN t2 ON t1.id = t2.id"
  +        )
           self.validate_identity("SELECT @a MEMBER OF(@c), @b MEMBER OF(@c)")
           self.validate_identity("SELECT JSON_ARRAY(4, 5) MEMBER OF('[[3,4],[4,5]]')")
           self.validate_identity("SELECT CAST('[4,5]' AS JSON) MEMBER OF('[[3,4],[4,5]]')")
  +5 -0
....................                                              [100%]
50 passed, 481 subtests passed in 0.17s
[assistant] `UPDATE` and `DELETE` now accept optimizer hints in the MySQL dialect, and the hints round-trip. The full test suite passes (1087 tests), and ruff check and format are clean.

Changes:
- **`sqlglot/expressions/dml.py`**: added a `hint` arg to `Update` and `Delete`, matching what `Select` and `Insert` already have.
- **`sqlglot/parser.py`**: `_parse_update` and `_parse_delete` parse the hint right after the keyword. The tokenizer already emitted hint tokens after `UPDATE` and `DELETE`, so no tokenizer change was needed.
- **`sqlglot/generator.py`**: `update_sql` and `delete_sql` emit the hint after the keyword.
- **`tests/dialects/test_mysql.py`**: three identity tests covering an `UPDATE` hint, a `DELETE` hint, and a multi-table `DELETE` hint.

I put the change in the base parser and generator rather than the MySQL class, since that is where `SELECT` and `INSERT` hints already live. Other dialects that tokenize hints will now also parse hints on `UPDATE` and `DELETE`.

I did not commit anything.
