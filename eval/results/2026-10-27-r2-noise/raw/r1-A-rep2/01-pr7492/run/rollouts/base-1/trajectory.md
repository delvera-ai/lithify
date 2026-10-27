# trajectory base-1

final message:
Oracle `MERGE` now parses and round-trips the optional `WHERE` on `WHEN MATCHED THEN UPDATE ...` and `WHEN NOT MATCHED THEN INSERT ... VALUES ...`. Dialects without support emit an unsupported warning and drop the clause.

- **AST:** `exp.When` has a new optional `where` arg (`sqlglot/expressions/dml.py`).
- **Parser:** `_parse_when_matched` reads an optional `WHERE` after each action (`sqlglot/parser.py`). I put this in the base parser, since the base dialect is the superset, so it also parses in the default dialect.
- **Generator:** `when_sql` emits the clause only if the new `SUPPORTS_MERGE_WHERE` flag is set (`sqlglot/generator.py`). Oracle sets it to `True` (`sqlglot/generators/oracle.py`). Other generators call `self.unsupported(...)` and drop it.
- **Tests:** added `test_merge_when_where` in `tests/dialects/test_oracle.py`. It covers the round-trip and checks that DuckDB raises under `ErrorLevel.RAISE` and drops the clause under `ErrorLevel.IGNORE`.

The full suite gives 1080 passed and 1 failed. The failure is `test_lazy_load`, which shells out to a bare `python` that isn't on PATH in this environment. It passes with the project venv's bin directory prepended to PATH. Ruff check and format are clean on the changed files.

Nothing is committed.

## events
[assistant] I'll start by finding how MERGE is parsed and generated, and how the Oracle dialect currently handles it.
[tool_use Bash] {"command": "grep -n \"Merge\\|_parse_when_matched\\|WHEN_MATCHED\\|whens\" sqlglot/parser.py | head -80; echo ---; grep -n \"merge\\|Merge\\|whens\" sqlglot/generator.py sqlglot/dialects/oracle.py | head -40; echo ---; grep -n \"class When\\|class Merge\" -A 12 sqlglot/expressions.py", "description": "Locate MERGE handling across parser, generator, oracle"}
[tool_result ERROR] Exit code 2
17 matches in 6 files:

1056:0:lambda self: self._parse_when_matched(),
1377:0:lambda self: self.expression(exp.MergeTreeTTL(expressions=[self._parse_bitwis...
3039:0:
8884:0:
8905:0:
sqlglot/parser.py:2194:return self.expression(exp.MergeTreeTTLAction(this=this, delete=True))
sqlglot/parser.py:2197:exp.MergeTreeTTLAction(this=this, recompress=self._parse_bitwise())
sqlglot/parser.py:2201:exp.MergeTreeTTLAction(this=this, to_disk=self._parse_string())
sqlglot/parser.py:2205:exp.Merge
…[1019 chars elided]…
s_sql(self, expression: exp.Whens) -> str:
sqlglot/generator.py:4469:def merge_sql(self, expression: exp.Merge) -> str:
sqlglot/generator.py:4475:# T-SQL syntax is MERGE ... <target_table> [WITH (<merge_hint>)] [[AS] table_...
sqlglot/generator.py:4480:whens = self.sql(expression, "whens")
sqlglot/generator.py:4491:whens = f"{whens}{returning}"
sqlglot/generator.py:4497:f"MERGE INTO {this}{table_alias}{sep}{using}{sep}{on}{sep}{whens}",
---
grep: sqlglot/expressions.py: No such file or directory
[tool_use Bash] {"command": "sed -n 8880,8960p sqlglot/parser.py; echo ---; sed -n 4460,4500p sqlglot/generator.py; echo ---; grep -rn \"class When\\b\\|class Merge\\b\" -A 10 sqlglot/expressions/*.py; echo ---; grep -n \"Merge\\|WHEN\" sqlglot/dialects/oracle.py | head", "description": "Read MERGE parser, generator, and expression defs"}
[tool_result]                 update_options=update_options,
            )
        )

    def _parse_merge(self) -> exp.Merge:
        self._match(TokenType.INTO)
        target = self._parse_table()

        if target and self._match(TokenType.ALIAS, advance=False):
            target.set("alias", self._parse_table_alias())

        self._match(TokenType.USING)
        using = self._parse_table()

        return self.expression(
            exp.Merge(
                this=target,
                using=using,
…[4611 chars elided]…
.py:517:class When(Expression):
sqlglot/expressions/dml.py-518-    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
sqlglot/expressions/dml.py-519-
sqlglot/expressions/dml.py-520-
sqlglot/expressions/dml.py-521-class Whens(Expression):
sqlglot/expressions/dml.py-522-    """Wraps around one or more WHEN [NOT] MATCHED [...] clauses."""
sqlglot/expressions/dml.py-523-
sqlglot/expressions/dml.py-524-    arg_types = {"expressions": True}
---
0 matches for 'Merge\|WHEN'
[assistant] Oracle inherits the base MERGE parser, which stops after the `THEN` action, so a trailing `WHERE` is not consumed. Next I'll check the `When` generator and the `Update`/`Insert` arg types.
[tool_use Bash] {"command": "sed -n 4420,4462p sqlglot/generator.py; echo ---; grep -n \"^class Insert\\|^class Update\" -A 22 sqlglot/expressions/dml.py | grep -n \"class\\|arg_types\\|where\\|\\\"\" | head -60; echo ---; grep -n \"def update_sql\" -A 25 sqlglot/generator.py | head -40", "description": "Read When generator and Insert/Update arg types"}
[tool_result]     def tag_sql(self, expression: exp.Tag) -> str:
        return f"{expression.args.get('prefix')}{self.sql(expression.this)}{expression.args.get('postfix')}"

    def token_sql(self, token_type: TokenType) -> str:
        return self.TOKEN_MAPPING.get(token_type, token_type.name)

    def userdefinedfunction_sql(self, expression: exp.UserDefinedFunction) -> str:
        this = self.sql(expression, "this")
        expressions = self.no_identify(self.expressions, expression)
        expressions 
…[3610 chars elided]…
: exp.Values, values_as_table: bool = True) -> str:
2483-        values_as_table = values_as_table and self.VALUES_AS_TABLE
2484-
2485-        # The VALUES clause is still valid in an `INSERT INTO ..` statement, for example
2486-        if values_as_table or not expression.find_ancestor(exp.From, exp.Join):
2487-            args = self.expressions(expression)
2488-            alias = self.sql(expression, "alias")
2489-            values = f"VALUES{self.seg('')}{args}"
2490-            values = (
[assistant] Both branches already get their `THEN` action built in the parser and emitted in `when_sql`. My plan is to add an optional `where` arg on `exp.When`, parse it after the action, and emit it only when the target generator supports it. Before editing, I'll check how unsupported-feature warnings and generator flags are done, and where the existing MERGE tests live.
[tool_use Bash] {"command": "grep -n \"self.unsupported(\" sqlglot/generator.py | head -5; grep -n \"^    [A-Z_]*SUPPORTS[A-Z_]* = \\|MATCHED_BY_SOURCE\" sqlglot/generator.py | head -20; echo ---; grep -n \"MATCHED_BY_SOURCE\\|class Generator\" sqlglot/dialects/*.py | head; echo ---; grep -n \"class Generator\" -A 3 sqlglot/dialects/oracle.py; echo ---; grep -rln \"WHEN MATCHED\\|MERGE INTO\" tests/dialects/ | head; echo ---; grep -n \"def where_sql\" -A 4 sqlglot/generator.py", "description": "Inspect unsupported helper, flags, Oracle generator, merge tests"}
[tool_result] rg: regex parse error:
    (?:self.unsupported()
    ^
error: unclosed group
0 matches for 'self.unsupported('
21 matches in 1 files:

sqlglot/generator.py:321:MATCHED_BY_SOURCE = True
sqlglot/generator.py:407:SUPPORTS_TABLE_COPY = True
sqlglot/generator.py:437:SUPPORTS_SINGLE_ARG_CONCAT = True
sqlglot/generator.py:440:LAST_DAY_SUPPORTS_DATE_PART = True
sqlglot/generator.py:443:SUPPORTS_TABLE_ALIAS_COLUMNS = True
sqlglot/generator.py:455:SUPPORTS_SELECT_INTO = False
sqlglot/generator.py:458:SUPP
…[702 chars elided]…
Generator(Generator):
---
---
tests/dialects/test_snowflake.py
tests/dialects/test_bigquery.py
tests/dialects/test_oracle.py
tests/dialects/test_duckdb.py
tests/dialects/test_dialect.py
tests/dialects/test_tsql.py
tests/dialects/test_postgres.py
---
3221:    def where_sql(self, expression: exp.Where) -> str:
3222-        this = self.indent(self.sql(expression, "this"))
3223-        return f"{self.seg('WHERE')}{self.sep()}{this}"
3224-
3225-    def window_sql(self, expression: exp.Window) -> str:
[tool_use Bash] {"command": "grep -n \"self.unsupported\" sqlglot/generator.py | head -3; grep -n \"def unsupported\" -A 3 sqlglot/generator.py; echo ---; sed -n 570,580p sqlglot/generator.py; echo ---; grep -n \"class Generator\" -A 12 sqlglot/dialects/oracle.py | head -30; grep -n \"MERGE\" tests/dialects/test_oracle.py | head; echo ---; grep -n \"SUPPORTS_BETWEEN_FLAGS\\|SUPPORTS_LIKE_QUANTIFIERS\" sqlglot/dialects/*.py | head -4", "description": "Check unsupported helper, Oracle generator, merge tests"}
[tool_result] 49 matches in 8 files:

4943:0:{style_value}")
30:def unsupported_args(
31-    *args: str | tuple[str, str],
32-) -> t.Callable[[GeneratorMethod], GeneratorMethod]:
33-    """
--
953:    def unsupported(self, message: str) -> None:
954-        if self.unsupported_level == ErrorLevel.IMMEDIATE:
955-            raise UnsupportedError(message)
956-        self.unsupported_messages.append(message)
---
    # Whether SYMMETRIC and ASYMMETRIC flags are supported with BETWEEN expression
    SUPPORTS_BET
…[90 chars elided]…
SOME
    SUPPORTS_LIKE_QUANTIFIERS = True

    # Prefix which is appended to exp.Table expressions in MATCH AGAINST
    MATCH_AGAINST_TABLE_PREFIX: str | None = None

    # Whether to include the VARIABLE keyword for SET assignments
    SET_ASSIGNMENT_REQUIRES_VARIABLE_KEYWORD = False
---
1 matches in 1 files:

tests/dialects/test_oracle.py:895:"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id...
---
0 matches for 'SUPPORTS_BETWEEN_FLAGS\|SUPPORTS_LIKE_QUANTIFIERS'
[assistant] The `grep` here behaves like ripgrep and mishandles some patterns, so I'll use `rg` with fixed strings. Next I'll look at the Oracle dialect's generator class and the existing MERGE test.
[tool_use Bash] {"command": "rg -n \"class Generator|SUPPORTS_|TRANSFORMS = \\{|class Parser|class Tokenizer\" sqlglot/dialects/oracle.py | head -30; echo ---; rg -n -B2 -A8 \"MERGE INTO my_table USING\" tests/dialects/test_oracle.py; echo ---; rg -n \"unsupported\" tests/dialects/test_oracle.py | head -3; rg -n \"SUPPORTS_UNIX_SECONDS|SUPPORTS_SELECT_INTO = True\" sqlglot/dialects/*.py | head -3", "description": "Inspect Oracle dialect classes and MERGE test"}
[tool_result] 1 matches in 1 files:

59:0:
---
893-        self.assertEqual(
894-            merge_stmt.sql("oracle"),
895:            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
896-        )
897-
898-    def test_pseudocolumns(self):
899-        ast = self.validate_identity(
900-            "WITH t AS (SELECT 1 AS COL) SELECT col, ROWID FROM t WHERE ROWNUM = 1"
901-        )
902-        self.assertIsNone(ast.find(exp.Pseudocolumn))
903-
---
0 matches for 'unsupported'
0 matches for 'SUPPORTS_UNIX_SECONDS|SUPPORTS_SELECT_INTO = True'
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/dialects/oracle.py"}
[tool_result] 1	from __future__ import annotations
2	
3	import typing as t
4	
5	from sqlglot import exp, tokens
6	from sqlglot.dialects.dialect import (
7	    Dialect,
8	    NormalizationStrategy,
9	)
10	from sqlglot.generators.oracle import OracleGenerator
11	from sqlglot.parsers.oracle import OracleParser
12	from sqlglot.tokens import TokenType
13	
14	
15	class Oracle(Dialect):
16	    ALIAS_POST_TABLESAMPLE = True
17	    LOCKING_READS_SUPPORTED = True
18	    TABLESAMPLE_SIZE_IS_PERCENT = True
19	    NULL_OR
…[2607 chars elided]…
: TokenType.MATCH_RECOGNIZE,
78	            "MINUS": TokenType.EXCEPT,
79	            "NVARCHAR2": TokenType.NVARCHAR,
80	            "ORDER SIBLINGS BY": TokenType.ORDER_SIBLINGS_BY,
81	            "SAMPLE": TokenType.TABLE_SAMPLE,
82	            "START": TokenType.BEGIN,
83	            "TOP": TokenType.TOP,
84	            "VARCHAR2": TokenType.VARCHAR,
85	            "SYSTIMESTAMP": TokenType.SYSTIMESTAMP,
86	        }
87	
88	    Parser = OracleParser
89	
90	    Generator = OracleGenerator
91	
[assistant] The Oracle dialect now delegates to `sqlglot/generators/oracle.py` and `sqlglot/parsers/oracle.py`. I'll check those files and the base flag block for where MERGE-related flags belong.
[tool_use Bash] {"command": "rg -n \"class |SUPPORTS_|MATCHED|merge|Merge|When\" sqlglot/generators/oracle.py sqlglot/parsers/oracle.py | head -60; echo ---; rg -n \"MATCHED_BY_SOURCE\" -B3 -A1 sqlglot/generator.py | head -20; echo ---; rg -n \"MERGE_|_parse_when_matched|CONFLICT_ACTIONS\" sqlglot/parser.py sqlglot/parsers/*.py | head", "description": "Inspect Oracle generator/parser modules and flag conventions"}
[tool_result] 7 matches in 2 files:

sqlglot/generators/oracle.py:23:class OracleGenerator(generator.Generator):
sqlglot/generators/oracle.py:26:SUPPORTS_UESCAPE = False
sqlglot/generators/oracle.py:34:LAST_DAY_SUPPORTS_DATE_PART = False
sqlglot/generators/oracle.py:35:SUPPORTS_SELECT_INTO = True
sqlglot/generators/oracle.py:37:SUPPORTS_WINDOW_EXCLUDE = True
sqlglot/generators/oracle.py:39:SUPPORTS_DECODE_CASE = True
sqlglot/parsers/oracle.py:22:class OracleParser(parser.Parser):
---
318-    CREATE_FUNCTION_R
…[393 chars elided]…
on = self.sql(expression, "condition")
---
6 matches in 1 files:

sqlglot/parser.py:1056:exp.Whens: lambda self: self._parse_when_matched(),
sqlglot/parser.py:1562:CONFLICT_ACTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:3468:action = self._parse_var_from_options(self.CONFLICT_ACTIONS)
sqlglot/parser.py:8900:whens=self._parse_when_matched(),
sqlglot/parser.py:8905:def _parse_when_matched(self) -> exp.Whens:
sqlglot/parser.py:8947:then = self._parse_var_from_options(self.CONFLICT_ACTIONS)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "limit": 45}
[tool_result] 1	from __future__ import annotations
2	
3	
4	from sqlglot import exp, generator, transforms
5	from sqlglot.dialects.dialect import (
6	    no_ilike_sql,
7	    rename_func,
8	    strposition_sql,
9	    to_number_with_nls_param,
10	    trim_sql,
11	)
12	
13	
14	def _trim_sql(self: OracleGenerator, expression: exp.Trim) -> str:
15	    position = expression.args.get("position")
16	
17	    if position and position.upper() in ("LEADING", "TRAILING"):
18	        return self.trim_sql(expression)
19	
20	
…[360 chars elided]…
UMN_KEYWORD = False
32	    LIMIT_FETCH = "FETCH"
33	    TABLESAMPLE_KEYWORDS = "SAMPLE"
34	    LAST_DAY_SUPPORTS_DATE_PART = False
35	    SUPPORTS_SELECT_INTO = True
36	    TZ_TO_WITH_TIME_ZONE = True
37	    SUPPORTS_WINDOW_EXCLUDE = True
38	    QUERY_HINT_SEP = " "
39	    SUPPORTS_DECODE_CASE = True
40	
41	    AFTER_HAVING_MODIFIER_TRANSFORMS = generator.AFTER_HAVING_MODIFIER_TRANSFORMS
42	
43	    TYPE_MAPPING = {
44	        **generator.Generator.TYPE_MAPPING,
45	        exp.DType.BLOB: "BLOB",
[assistant] I have what I need. The plan:

1. Add an optional `where` arg to `exp.When`.
2. Parse an optional `WHERE` after the action in `_parse_when_matched` (base parser, so it is a superset like the rest of the MERGE grammar).
3. Emit it in `when_sql` only when the generator sets a new `SUPPORTS_MERGE_WHERE` flag, which Oracle enables. Otherwise call `self.unsupported` and drop it.

Starting with the expression definition.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py", "old_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True}", "new_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True, \"where\": False}"}
[tool_result ERROR] <tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "            whens.append(\n                self.expression(\n                    exp.When(matched=matched, source=source, condition=condition, then=then)\n                )\n            )", "new_string": "            whens.append(\n                self.expression(\n                    exp.When(\n                        matched=matched,\n                        source=source,\n                        condition=condition,\n                        then=then,\n                        where=self._parse_where(),\n                    )\n                )\n            )"}
[tool_result ERROR] <tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE WHEN [NOT] MATCHED ... THEN <action> may be followed by a WHERE clause\n    SUPPORTS_MERGE_WHERE = False\n"}
[tool_result ERROR] <tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        where = self.sql(expression, \"where\")\n        if where:\n            if self.SUPPORTS_MERGE_WHERE:\n                then = f\"{then}{where}\"\n            else:\n                self.unsupported(\"WHERE clause in MERGE WHEN [NOT] MATCHED is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}\""}
[tool_result ERROR] <tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py", "old_string": "    SUPPORTS_DECODE_CASE = True\n", "new_string": "    SUPPORTS_DECODE_CASE = True\n    SUPPORTS_MERGE_WHERE = True\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generators/oracle.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Four of the five edits failed because I hadn't read those files yet. I'll read the relevant sections and retry them.
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py", "offset": 516, "limit": 5}
[tool_result] 516	
517	class When(Expression):
518	    arg_types = {"matched": True, "source": False, "condition": False, "then": True}
519	
520	
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "offset": 8944, "limit": 14}
[tool_result] 8944	            elif self._match(TokenType.DELETE):
8945	                then = self.expression(exp.Var(this=self._prev.text))
8946	            else:
8947	                then = self._parse_var_from_options(self.CONFLICT_ACTIONS)
8948	
8949	            whens.append(
8950	                self.expression(
8951	                    exp.When(matched=matched, source=source, condition=condition, then=then)
8952	                )
8953	            )
8954	        return self.expression(exp.Whens(expressions=whens))
8955	
8956	    def _parse_show(self) -> exp.Expr | None:
8957	        parser = self._find_parser(self.SHOW_PARSERS, self.SHOW_TRIE)
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "offset": 4440, "limit": 25}
[tool_result] 4440	    def kwarg_sql(self, expression: exp.Kwarg) -> str:
4441	        return self.binary(expression, "=>")
4442	
4443	    def when_sql(self, expression: exp.When) -> str:
4444	        matched = "MATCHED" if expression.args["matched"] else "NOT MATCHED"
4445	        source = " BY SOURCE" if self.MATCHED_BY_SOURCE and expression.args.get("source") else ""
4446	        condition = self.sql(expression, "condition")
4447	        condition = f" AND {condition}" if condition else ""
4448	
4449	     
…[423 chars elided]…
          if isinstance(then_expression.args.get("expressions"), exp.Star):
4457	                then = f"UPDATE {self.sql(then_expression, 'expressions')}"
4458	            else:
4459	                expressions_sql = self.expressions(then_expression)
4460	                then = f"UPDATE SET{self.sep()}{expressions_sql}" if expressions_sql else "UPDATE"
4461	
4462	        else:
4463	            then = self.sql(then_expression)
4464	        return f"WHEN {matched}{source}{condition} THEN {then}"
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "offset": 319, "limit": 4}
[tool_result] 319	
320	    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed
321	    MATCHED_BY_SOURCE = True
322	
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py", "old_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True}", "new_string": "    arg_types = {\"matched\": True, \"source\": False, \"condition\": False, \"then\": True, \"where\": False}"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/expressions/dml.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py", "old_string": "            whens.append(\n                self.expression(\n                    exp.When(matched=matched, source=source, condition=condition, then=then)\n                )\n            )", "new_string": "            whens.append(\n                self.expression(\n                    exp.When(\n                        matched=matched,\n                        source=source,\n                        condition=condition,\n                        then=then,\n                        where=self._parse_where(),\n                    )\n                )\n            )"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/parser.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "        else:\n            then = self.sql(then_expression)\n        return f\"WHEN {matched}{source}{condition} THEN {then}\"", "new_string": "        else:\n            then = self.sql(then_expression)\n\n        where = self.sql(expression, \"where\")\n        if where:\n            if self.SUPPORTS_MERGE_WHERE:\n                then = f\"{then}{where}\"\n            else:\n                self.unsupported(\"WHERE clause in MERGE WHEN [NOT] MATCHED is not supported\")\n\n        return f\"WHEN {matched}{source}{condition} THEN {then}\""}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py", "old_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n", "new_string": "    # Whether MERGE ... WHEN MATCHED BY SOURCE is allowed\n    MATCHED_BY_SOURCE = True\n\n    # Whether MERGE WHEN [NOT] MATCHED ... THEN <action> may be followed by a WHERE clause\n    SUPPORTS_MERGE_WHERE = False\n"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/sqlglot/generator.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] All source edits are in. Next I'll add tests next to the existing Oracle MERGE test, and check how other tests assert unsupported warnings.
[tool_use Bash] {"command": "rg -n \"unsupported_level=ErrorLevel.RAISE|assertRaises\\(UnsupportedError\\)|unsupported_messages\" tests/dialects/test_oracle.py tests/dialects/test_dialect.py | head -4; rg -n \"def test_merge\" -A3 tests/dialects/test_oracle.py | head; sed -n 880,897p tests/dialects/test_oracle.py", "description": "Find unsupported-warning test pattern and Oracle merge test"}
[tool_result] 2 matches in 1 files:

tests/dialects/test_dialect.py:98:with self.assertRaises(UnsupportedError):
tests/dialects/test_dialect.py:99:expression.sql(write_dialect, unsupported_level=ErrorLevel.RAISE)
884:    def test_merge_builder_alias(self):
885-        merge_stmt = exp.merge(
886-            "WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1",
887-            "WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        self.valid
…[504 chars elided]…

            using="(SELECT * FROM something) source_table",
            on="my_table.id = source_table.id",
            dialect="oracle",
        )
        self.assertEqual(
            merge_stmt.sql("oracle"),
            "MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my_table.id, my_table.col1) VALUES (source_table.id, source_table.col1)",
        )
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "            \"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my
…[1053 chars elided]…
ad=\"oracle\",\n        )\n        with self.assertRaises(UnsupportedError):\n            expression.sql(\"duckdb\", unsupported_level=ErrorLevel.RAISE)\n        self.assertEqual(\n            expression.sql(\"duckdb\", unsupported_level=ErrorLevel.IGNORE),\n            \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c\",\n        )\n\n    def test_pseudocolumns(self):"}
[tool_result ERROR] <tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "limit": 12}
[tool_result] 1	from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one
2	from tests.dialects.test_dialect import Validator
3	from sqlglot.optimizer.qualify import qualify
4	
5	
6	class TestOracle(Validator):
7	    dialect = "oracle"
8	
9	    def test_oracle(self):
10	        self.validate_identity("1 /* /* */", "1 /* / * */")
11	        self.validate_all(
12	            "SELECT CONNECT_BY_ROOT x y",
[tool_use Bash] {"command": "rg -n \"ErrorLevel\" tests/dialects/test_dialect.py | head -2", "description": "Check ErrorLevel import path used in tests"}
[tool_result] 4 matches in 1 files:
[tool_use Bash] {"command": "rg -n \"import.*ErrorLevel|ErrorLevel,\" tests/dialects/test_dialect.py tests/test_transpile.py | head -3", "description": "Find ErrorLevel import line in tests"}
[tool_result] 2 matches in 2 files:

tests/dialects/test_dialect.py:8:ErrorLevel,
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_dialect.py", "limit": 12}
[tool_result] 1	import typing as t
2	import unittest
3	
4	
5	from sqlglot import (
6	    Dialect,
7	    Dialects,
8	    ErrorLevel,
9	    ParseError,
10	    TokenError,
11	    UnsupportedError,
12	    exp,
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "from sqlglot import exp, UnsupportedError, ParseError, parse, parse_one", "new_string": "from sqlglot import exp, ErrorLevel, UnsupportedError, ParseError, parse, parse_one"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully. (file state is current in your context — no need to Read it back)
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py", "old_string": "            \"MERGE INTO my_table USING (SELECT * FROM something) source_table ON my_table.id = source_table.id WHEN MATCHED THEN UPDATE SET my_table.col1 = source_table.col1 WHEN NOT MATCHED THEN INSERT (my
…[1053 chars elided]…
ad=\"oracle\",\n        )\n        with self.assertRaises(UnsupportedError):\n            expression.sql(\"duckdb\", unsupported_level=ErrorLevel.RAISE)\n        self.assertEqual(\n            expression.sql(\"duckdb\", unsupported_level=ErrorLevel.IGNORE),\n            \"MERGE INTO t USING s ON t.id = s.id WHEN MATCHED THEN UPDATE SET t.c = s.c\",\n        )\n\n    def test_pseudocolumns(self):"}
[tool_result] The file ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1/tests/dialects/test_oracle.py has been updated successfully. (file state is current in your context — no need to Read it back)
[assistant] Edits and tests are in place. Now I'll run the Oracle test module, then the full suite with the project's command.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_oracle.py 2>&1 | tail -30", "description": "Run Oracle dialect tests"}
[tool_result] ........................                                                      [100%]
24 passed, 211 subtests passed in 0.39s
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -30", "description": "Run full test suite"}
[tool_result]                 err_msg = err_msg.decode()
            except ValueError:
                exception_name = b'SubprocessError'
                hex_errno = b'0'
                err_msg = 'Bad exception data from child: {!r}'.format(
                              bytes(errpipe_data))
            child_exception_type = getattr(
                    builtins, exception_name.decode('ascii'),
                    SubprocessError)
            if issubclass(child_exception_type, OSError) and hex_errno:
   
…[559 chars elided]…
 raise child_exception_type(errno_num, err_msg, err_filename)
E                   FileNotFoundError: [Errno 2] No such file or directory: 'python'

~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/lib/python3.12/subprocess.py:1955: FileNotFoundError
=========================== short test summary info ============================
FAILED tests/dialects/test_dialect.py::TestDialect::test_lazy_load - FileNotF...
1 failed, 1080 passed, 17834 subtests passed in 62.78s (0:01:02)
[assistant] One test failed: `test_lazy_load` shells out to a bare `python`, which isn't on PATH here. I'll rerun it with the project venv's bin directory on PATH to confirm it's environmental.
[tool_use Bash] {"command": "PATH=<work>/env-sqlglot/bin:$PATH <work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_dialect.py -k test_lazy_load 2>&1 | tail -3", "description": "Rerun lazy-load test with venv on PATH"}
[tool_result] .                                                                        [100%]
1 passed, 97 deselected in 0.11s
[assistant] That test passes with the venv on PATH, so the failure was environmental. Last, a lint check on the changed files since the `When.arg_types` line is long.
[tool_use Bash] {"command": "cd ~/.cache/lithify/work/repo-fe4f63bc3f99/20261027-125902-oracle-dialect-support-the-optio/base-1 2>/dev/null; <work>/env-sqlglot/bin/python -m ruff check sqlglot/expressions/dml.py sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -5; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/expressions/dml.py sqlglot/parser.py sqlglot/generator.py sqlglot/generators/oracle.py tests/dialects/test_oracle.py 2>&1 | tail -5", "description": "Lint and format-check changed files with ruff"}
[tool_result] All checks passed!
5 files already formatted
[assistant] Oracle `MERGE` now parses and round-trips the optional `WHERE` on `WHEN MATCHED THEN UPDATE ...` and `WHEN NOT MATCHED THEN INSERT ... VALUES ...`. Dialects without support emit an unsupported warning and drop the clause.

- **AST:** `exp.When` has a new optional `where` arg (`sqlglot/expressions/dml.py`).
- **Parser:** `_parse_when_matched` reads an optional `WHERE` after each action (`sqlglot/parser.py`). I put this in the base parser, since the base dialect is the superset, so it also parses in the default dialect.
- **Generator:** `when_sql` emits the clause only if the new `SUPPORTS_MERGE
…[71 chars elided]…
(`sqlglot/generators/oracle.py`). Other generators call `self.unsupported(...)` and drop it.
- **Tests:** added `test_merge_when_where` in `tests/dialects/test_oracle.py`. It covers the round-trip and checks that DuckDB raises under `ErrorLevel.RAISE` and drops the clause under `ErrorLevel.IGNORE`.

The full suite gives 1080 passed and 1 failed. The failure is `test_lazy_load`, which shells out to a bare `python` that isn't on PATH in this environment. It passes with the project venv's bin directory prepended to PATH. Ruff check and format are clean on the changed files.

Nothing is committed.
