# trajectory base-1

final message:
The Exasol alias rewrite now matches unquoted aliases case-insensitively, so the reported query works:

```
sqlglot.transpile("SELECT 1 AS idField FROM t GROUP BY idfield", read="mysql", write="exasol")
→ ['SELECT 1 AS idField FROM t GROUP BY LOCAL.idfield']
```

The full suite passes (1107 tests, with the Exasol file's 19 tests included), and ruff check and format are clean.

**What changed**

- `sqlglot/generators/exasol.py`: a small `_identifier_key` helper normalizes identifiers the way Exasol does. Unquoted names are upper-cased and quoted names are kept as-is. `_add_local_prefix_for_aliases` now keys both the alias map and the column lookups by that key, in WHERE, GROUP BY, HAVING, and the select-list alias tracking.
- `tests/dialects/test_exasol.py`: two cases added next to the existing alias-LOCAL tests. One covers the case-mismatched unquoted alias. The other checks that a quoted `"idField"` alias is still matched only by the exact quoted spelling.

**Decision to check:** a quoted alias is still case-sensitive. `SELECT 1 AS "idField" ... GROUP BY idfield` is left unrewritten, because Exasol would resolve `idfield` to `IDFIELD`, which doesn't match. That is the behavior the Exasol identifier rules imply, but say if you'd rather it be handled differently.

## events
[tool_use Bash] {"command": "grep -rn \"LOCAL\\.\" sqlglot/ | head -30", "description": "Find LOCAL alias rewrite code"}
[tool_result] (Bash completed with no output)
[tool_use Bash] {"command": "grep -rn -i \"local\" sqlglot/dialects/exasol.py sqlglot/dialects/mysql.py | head -30; grep -rn \"LOCAL\" sqlglot/*.py sqlglot/optimizer/*.py | head", "description": "Search for LOCAL references in dialects"}
[tool_result] sqlglot/tokens.py:329:        "LOCALTIME": TokenType.LOCALTIME,
sqlglot/tokens.py:330:        "LOCALTIMESTAMP": TokenType.LOCALTIMESTAMP,
sqlglot/generator.py:1751:        local = "LOCAL " if expression.args.get("local") else ""
sqlglot/generator.py:2902:        local = " LOCAL" if expression.args.get("local") else ""
sqlglot/generator.py:5972:        return self.func("LOCALTIME", this) if this else "LOCALTIME"
sqlglot/generator.py:5976:        return self.func("LOCALTIMESTAMP", this) if this else "LOCALTIMESTAMP"
sqlglot/tokenizer_core.py:196:    LOCALTIME = auto()
sqlglot/tokenizer_core.py:197:    LOCALTIMESTAMP = auto()
sqlglot/parser.py:761:        TokenType.LOCALTIME,
sqlglot/parser.py:762:        TokenType.LOCALTIMESTAMP,
[tool_use Bash] {"command": "grep -rn -i \"exasol\" sqlglot/ --include=*.py | grep -v \"^sqlglot/dialects/exasol.py\" | head; grep -n -i \"alias\" sqlglot/dialects/exasol.py | head -40", "description": "Locate Exasol alias handling"}
[tool_result] (eval):1: no matches found: --include=*.py
[tool_use Bash] {"command": "grep -rln -i \"exasol\" sqlglot/; echo ---; grep -n -i \"alias\" sqlglot/dialects/exasol.py | head -40", "description": "Locate Exasol dialect and alias handling"}
[tool_result] sqlglot/parsers/exasol.py
sqlglot/dialects/__init__.py
sqlglot/dialects/dialect.py
sqlglot/dialects/exasol.py
sqlglot/generators/exasol.py
---
[tool_use Bash] {"command": "grep -n -i \"alias\\|local\" sqlglot/generators/exasol.py sqlglot/parsers/exasol.py sqlglot/dialects/exasol.py | head -60", "description": "Search Exasol generator and parser for alias code"}
[tool_result] sqlglot/parsers/exasol.py:31:    TABLE_ALIAS_TOKENS = parser.Parser.TABLE_ALIAS_TOKENS | {
sqlglot/parsers/exasol.py:143:            and table_ident.name.upper() == "LOCAL"
sqlglot/generators/exasol.py:37:# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10
sqlglot/generators/exasol.py:38:def _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:
sqlglot/generators/exasol.py:40:        aliases: dict[str, bool] = {
sqlglot/generators/exasol.py:41:     
…[1959 chars elided]…
asol.py:290:    # https://docs.exasol.com/db/latest/sql_references/data_types/datatypealiases.htm
sqlglot/generators/exasol.py:307:        # Exasol supports a fixed default precision of 3 for TIMESTAMP WITH LOCAL TIME ZONE
sqlglot/generators/exasol.py:310:            return "TIMESTAMP WITH LOCAL TIME ZONE"
sqlglot/generators/exasol.py:396:                _add_local_prefix_for_aliases,
sqlglot/generators/exasol.py:648:        "localtime",
sqlglot/generators/exasol.py:649:        "localtimestamp",
[tool_use Bash] {"command": "sed -n 30,90p sqlglot/generators/exasol.py; sed -n 385,400p sqlglot/generators/exasol.py; grep -n \"NORMALIZATION_STRATEGY\\|normalize\" sqlglot/dialects/exasol.py", "description": "Read alias-prefix rewrite logic"}
[tool_result]     if unit not in DATE_UNITS:
        self.unsupported(f"'{unit}' is not supported in Exasol.")
        return self.function_fallback_sql(expression)

    return self.func(f"{unit}S_BETWEEN", expression.this, expression.expression)


# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10
def _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:
    if isinstance(expression, exp.Select):
        aliases: dict[str, bool] = {
            alias.name: bool
…[2396 chars elided]…
st: rename_func("HASHTYPE_MD5"),
        # https://docs.exasol.com/db/latest/sql/create_view.htm
        exp.CommentColumnConstraint: lambda self, e: f"COMMENT IS {self.sql(e, 'this')}",
        exp.Select: transforms.preprocess(
            [
                _qualify_unscoped_star,
                _add_local_prefix_for_aliases,
                _group_by_all,
            ]
        ),
        exp.SubstringIndex: _substring_index_sql,
16:    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE
[tool_use Bash] {"command": "grep -rn \"def quoted\\|class Identifier\" sqlglot/expressions/*.py | head; grep -n \"class Column(\" -A12 sqlglot/expressions/*.py | head -30; grep -rn \"exasol\" tests/dialects/test_exasol.py | grep -i \"alias\\|local\" | head", "description": "Check Identifier.quoted and Column definition"}
[tool_result] sqlglot/expressions/core.py:1766:class Identifier(Expression):
sqlglot/expressions/core.py:1772:    def quoted(self) -> bool:
sqlglot/expressions/core.py:1673:class Column(Expression, Condition):
sqlglot/expressions/core.py-1674-    arg_types = {"this": True, "table": False, "db": False, "catalog": False, "join_mark": False}
sqlglot/expressions/core.py-1675-
sqlglot/expressions/core.py-1676-    @property
sqlglot/expressions/core.py-1677-    def table(self) -> str:
sqlglot/expressions/core.py-167
…[260 chars elided]…
ore.py-1683-
sqlglot/expressions/core.py-1684-    @property
sqlglot/expressions/core.py-1685-    def catalog(self) -> str:
tests/dialects/test_exasol.py:1000:            write={"exasol": "SELECT city, COUNT(*) AS cnt FROM t GROUP BY LOCAL.cnt"},
tests/dialects/test_exasol.py:1006:            write={"exasol": "SELECT YEAR(TO_DATE(a_date)) AS a_year FROM t GROUP BY LOCAL.a_year"},
tests/dialects/test_exasol.py:1018:            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
[tool_use Bash] {"command": "sed -n 1766,1780p sqlglot/expressions/core.py; sed -n 990,1030p tests/dialects/test_exasol.py", "description": "Read Identifier.quoted and existing alias tests"}
[tool_result] class Identifier(Expression):
    arg_types = {"this": True, "quoted": False, "global_": False, "temporary": False}
    is_primitive = True
    _hash_raw_args = True

    @property
    def quoted(self) -> bool:
        return bool(self.args.get("quoted"))

    @property
    def output_name(self) -> str:
        return self.name


class Opclass(Expression):
            write={
                "exasol": "SELECT TABLE_NAME FROM SYS.EXA_ALL_TABLES WHERE TABLE_SCHEMA = CURRENT_SCHEMA"
            },

…[825 chars elided]…
 city, COUNT(*) FROM t GROUP BY city",
            read={"mysql": "SELECT city, COUNT(*) FROM t GROUP BY city"},
            write={"exasol": "SELECT city, COUNT(*) FROM t GROUP BY city"},
        )
        # HAVING alias -> LOCAL prefix
        self.validate_all(
            "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1",
            read={"mysql": "SELECT COUNT(*) AS cnt FROM t HAVING cnt > 1"},
            write={"exasol": "SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1"},
        )
[assistant] I have the picture: `_add_local_prefix_for_aliases` in `sqlglot/generators/exasol.py` keys its alias map by the raw name, so `idfield` never matches `idField`. I'll key both sides by Exasol's normalized form: unquoted identifiers upper-cased, quoted ones kept as-is.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "# https://docs.exasol.com/db/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n     
…[499 chars elided]…
b/latest/sql/select.htm#:~:text=If%20you%20have,local.x%3E10\ndef _add_local_prefix_for_aliases(expression: exp.Expr) -> exp.Expr:\n    if isinstance(expression, exp.Select):\n        aliases: dict[str, bool] = {\n            _identifier_key(alias): alias.quoted\n            for sel in expression.selects\n            if isinstance(sel, exp.Alias) and (alias := sel.args.get(\"alias\"))\n        }"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "            if isinstance(node, exp.Column) and not node.table:\n                if node.name in visible_aliases:\n                    return exp.Column(\n                        this=exp.to_identifier(node.n
…[216 chars elided]…
.Column) and not node.table and isinstance(node.this, exp.Identifier):\n                if (key := _identifier_key(node.this)) in visible_aliases:\n                    return exp.Column(\n                        this=exp.to_identifier(node.name, quoted=visible_aliases[key]),\n                        table=exp.to_identifier(\"LOCAL\", quoted=False),\n                    )\n            return node"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "                alias_node = sel.args.get(\"alias\")\n\n                seen_aliases[sel.alias] = bool(alias_node and getattr(alias_node, \"quoted\", False))", "new_string": "                alias_node = sel.args.get(\"alias\")\n\n                seen_aliases[_identifier_key(alias_node)] = alias_node.quoted"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py", "old_string": "                alias_node = sel.args.get(\"alias\")\n\n                seen_aliases[_identifier_key(alias_node)] = alias_node.quoted", "new_string": "                if alias_node := sel.args.get(\"alias\"):\n                    seen_aliases[_identifier_key(alias_node)] = alias_node.quoted"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/sqlglot/generators/exasol.py has been updated successfully.
[assistant] Now a regression test next to the existing alias-LOCAL tests, covering the reported case plus the quoted-alias case that must stay case-sensitive.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py", "old_string": "        # HAVING alias -> LOCAL prefix\n        self.validate_all(\n            \"SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1\",\n            read={\"mysql\": \"SELECT COUNT(*) AS cnt FROM t HAVING cn
…[620 chars elided]…
": \"SELECT 1 AS idField FROM t GROUP BY idfield\"},\n            write={\"exasol\": \"SELECT 1 AS idField FROM t GROUP BY LOCAL.idfield\"},\n        )\n        # Quoted aliases stay case-sensitive\n        self.validate_all(\n            'SELECT 1 AS \"idField\" FROM t GROUP BY \"idField\"',\n            write={\"exasol\": 'SELECT 1 AS \"idField\" FROM t GROUP BY LOCAL.\"idField\"'},\n        )"}
[tool_result] The file ~/.cache/lithify/work/repo-90e86f132b84/20261028-125228-mysql-exasol-when-alias-referenc/base-1/tests/dialects/test_exasol.py has been updated successfully.
[assistant] Running the Exasol dialect tests with the project's interpreter, then the style check.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_exasol.py 2>&1 | tail -15; <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3; <work>/env-sqlglot/bin/python -m ruff check sqlglot/generators/exasol.py tests/dialects/test_exasol.py 2>&1 | tail -3", "description": "Run Exasol tests and ruff checks"}
[tool_result] ...................                                                    [100%]
19 passed, 578 subtests passed in 0.36s
Would reformat: sqlglot/generators/exasol.py
1 file would be reformatted, 1 file already formatted
All checks passed!
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m ruff format sqlglot/generators/exasol.py && git diff sqlglot/generators/exasol.py && <work>/env-sqlglot/bin/python -c \"\nimport sqlglot\nprint(sqlglot.transpile('SELECT 1 AS idField FROM t GROUP BY idfield', read='mysql', write='exasol'))\nprint(sqlglot.transpile('SELECT COUNT(*) AS cnt FROM t HAVING cnt > 1', read='mysql', write='exasol'))\nprint(sqlglot.transpile('SELECT 1 AS \\\"idField\\\" FROM t GROUP BY idfield', read='mysql', write='exasol'))\n\"", "description": "Apply formatter, show diff, verify reported case"}
[tool_result] 1 file reformatted
diff --git a/sqlglot/generators/exasol.py b/sqlglot/generators/exasol.py
index cd44625e6..f0eb68ab9 100644
--- a/sqlglot/generators/exasol.py
+++ b/sqlglot/generators/exasol.py
@@ -34,11 +34,16 @@ def _date_diff_sql(self: ExasolGenerator, expression: exp.DateDiff | exp.TsOrDsD
     return self.func(f"{unit}S_BETWEEN", expression.this, expression.expression)
 
 
+# Exasol folds unquoted identifiers to upper case, quoted identifiers are case-sensitive
+def _identifier_key(identi
…[2017 chars elided]…
           seen_aliases[_identifier_key(alias_node)] = alias_node.quoted
                 new_selects.append(sel)
             else:
                 new_selects.append(sel.transform(lambda node: prefix_local(node, seen_aliases)))
['SELECT 1 AS idField FROM t GROUP BY LOCAL.idfield']
['SELECT COUNT(*) AS cnt FROM t HAVING LOCAL.cnt > 1']
['SELECT 1 AS "idField" FROM t GROUP BY idfield']
[This command modified 1 file you've previously read: sqlglot/generators/exasol.py. Call Read before editing.]
[assistant] The reported case now rewrites to `LOCAL.idfield`. The quoted alias `"idField"` is correctly left alone, since unquoted `idfield` folds to `IDFIELD` and doesn't match it. Running the full suite now.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -5; git status --short", "description": "Run full test suite and show status"}
[tool_result] ......................................................................................................... [ 82%]
........................................ [ 86%]
................................................................ [ 91%]
.........................................................................................                                [100%]
1107 passed, 18014 subtests passed in 55.61s
 M sqlglot/generators/exasol.py
 M tests/dialects/test_exasol.py
[assistant] The Exasol alias rewrite now matches unquoted aliases case-insensitively, so the reported query works:

```
sqlglot.transpile("SELECT 1 AS idField FROM t GROUP BY idfield", read="mysql", write="exasol")
→ ['SELECT 1 AS idField FROM t GROUP BY LOCAL.idfield']
```

The full suite passes (1107 tests, with the Exasol file's 19 tests included), and ruff check and format are clean.

**What changed**

- `sqlglot/generators/exasol.py`: a small `_identifier_key` helper normalizes identifiers the way Exasol does. Unquoted names are upper-cased and quoted names are kept as-is. `_add_local_prefix_for_alia
…[82 chars elided]…
UP BY, HAVING, and the select-list alias tracking.
- `tests/dialects/test_exasol.py`: two cases added next to the existing alias-LOCAL tests. One covers the case-mismatched unquoted alias. The other checks that a quoted `"idField"` alias is still matched only by the exact quoted spelling.

**Decision to check:** a quoted alias is still case-sensitive. `SELECT 1 AS "idField" ... GROUP BY idfield` is left unrewritten, because Exasol would resolve `idfield` to `IDFIELD`, which doesn't match. That is the behavior the Exasol identifier rules imply, but say if you'd rather it be handled differently.
