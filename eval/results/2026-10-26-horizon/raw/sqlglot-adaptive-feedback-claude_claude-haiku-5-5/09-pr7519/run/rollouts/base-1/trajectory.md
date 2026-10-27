# trajectory base-1

final message:
Quoted index and constraint names that look like keywords now parse and round-trip in MySQL. The full suite passes: `SUMMARY: 1087 passed, 17844 subtests passed in 71.01s`, `EXIT: 0`.

**Cause:** `Parser._parse_unique_key` in `sqlglot/parser.py` rejected any name whose text matched a constraint keyword, including backtick-quoted ones. `` `Unique` `` uppercases to `UNIQUE`, so it was refused, and the same happened for `` `Index` `` and `` `Key` ``. The `_parse_unnamed_constraint` path already skips IDENTIFIER tokens for this reason, so I applied the same check here.

**Change:**
- `sqlglot/parser.py`: `_parse_unique_key` only treats the current token as a keyword when it is not an IDENTIFIER token.
- `tests/dialects/test_mysql.py`: added a `validate_identity` case in `test_ddl` covering `UNIQUE KEY `Unique``, `KEY `Index`` and `UNIQUE INDEX `Key``. The expected output is `UNIQUE `Unique``, `INDEX `Index``, `UNIQUE `Key``.

**Verified:**
- Before the fix, the three `UNIQUE ...` forms failed with `Expecting )`.
- After the fix, they parse to `UniqueColumnConstraint` / `IndexColumnConstraint` with the quoted identifier as the name.
- `CONSTRAINT `Key` UNIQUE KEY `Index` (b)` also works.
- The MySQL test file passes: 50 tests.

**Things to know:**
- The `KEY` keyword in `UNIQUE KEY` is dropped on output, so it becomes `UNIQUE `Unique``. That matches the existing expectation for unquoted names (`UNIQUE KEY d (b)` → `UNIQUE d (b)`), so I kept it.
- I could not reproduce the failure for `KEY `Index`` or `INDEX `Key``. Both already parsed in `CREATE TABLE` and `ALTER TABLE ... ADD`. If you saw them fail, I'd need the exact statement.
- Not fixed: `FOREIGN KEY `Key` (b) REFERENCES ...` still fails to parse. MySQL allows an index name there, but it is a different parse path from the one in the report. `PRIMARY KEY `Key`` also fails, but MySQL does not allow a name there, so I left it alone.
- The fix is in the base parser, so it applies to every dialect that uses the shared constraint code, not only MySQL. The full suite covers that.

The change is not committed.

## events
[tool_use Skill] {"skill": "sqlglot-dialect-functions"}
[tool_result] Launching skill: sqlglot-dialect-functions
[user] Base directory for this skill: ~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/.claude/skills/sqlglot-dialect-functions

# Dialect functions and parse fixes in sqlglot

## The invariant: parse into the canonical expression, not a generic node
sqlglot is AST-first. If a function's meaning already has an expression class, the function must
parse into THAT class so it can transpile. The generic nodes `exp.Anonymous`, `exp.AnonymousAggFunc`,
`exp.ParameterizedAgg`, `exp.CombinedAggFunc` and `exp.CombinedParameterizedAgg` (all in
`sqlglot
…[9631 chars elided]…
late already in the file:
  - Parser: `FUNCTION_PARSERS["QUANTILE"] = lambda self: self._parse_quantile()`.
    `_parse_quantile` parses the first group, then `self._parse_func_params()`, which matches
    `)(` and parses the second group. With no second group it builds the non-parametric form.
  - Generator: `exp.Quantile: _quantile_sql` in `TRANSFORMS` emits
    `self.func("quantile", <param>) + f"({<arg>})"`.
  - `"quantile"` also stays in `AGG_FUNCTIONS`. The suffixed names (`quantileIf`, …) don't match
    the exact `FUNCTION_PARSERS` key, so they still parse through the combinator path.

[tool_use Bash] {"command": "cat .lithify/harness/memory.md 2>/dev/null; grep -n \"UNIQUE\\|CONSTRAINT_KEYWORDS\\|_parse_index_constraint\\|KEY\\b\" sqlglot/parsers/mysql.py | head -60; grep -rn \"CONSTRAINT_PARSERS\\|SCHEMA_UNNAMED_CONSTRAINTS\\|def _parse_index_constraint\\|def _parse_unnamed_constraint\" sqlglot/parser.py sqlglot/parsers/mysql.py | head -40", "description": "Load harness memory and find MySQL constraint parsing"}
[tool_result] - The project's checks run with `<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no`.
- Layout: expression classes live in `sqlglot/expressions/*.py` (there is no `expressions.py`). A dialect's parser is `sqlglot/parsers/<d>.py` and its generator is `sqlglot/generators/<d>.py`; `sqlglot/dialects/<d>.py` only wires them together.
- The full suite (~1085 
…[1771 chars elided]…
NT_PARSERS:
sqlglot/parser.py:7389:            and self._curr.text.upper() not in self.CONSTRAINT_PARSERS
sqlglot/parsers/mysql.py:243:    CONSTRAINT_PARSERS = {
sqlglot/parsers/mysql.py:244:        **parser.Parser.CONSTRAINT_PARSERS,
sqlglot/parsers/mysql.py:264:    SCHEMA_UNNAMED_CONSTRAINTS = {
sqlglot/parsers/mysql.py:265:        *parser.Parser.SCHEMA_UNNAMED_CONSTRAINTS,
sqlglot/parsers/mysql.py:343:    def _parse_index_constraint(self, kind: str | None = None) -> exp.IndexColumnConstraint:
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parsers/mysql.py", "offset": 240, "limit": 130}
[tool_result] 240	    SHOW_TRIE = new_trie(key.split(" ") for key in SHOW_PARSERS)
241	    SET_TRIE = new_trie(key.split(" ") for key in SET_PARSERS)
242	
243	    CONSTRAINT_PARSERS = {
244	        **parser.Parser.CONSTRAINT_PARSERS,
245	        "FULLTEXT": lambda self: self._parse_index_constraint(kind="FULLTEXT"),
246	        "INDEX": lambda self: self._parse_index_constraint(),
247	        "KEY": lambda self: self._parse_index_constraint(),
248	        "SPATIAL": lambda self: self._parse_index_constraint(k
…[4447 chars elided]…
      elif self._match_text_seq("VISIBLE"):
363	                opt = exp.IndexConstraintOption(visible=True)
364	            elif self._match_text_seq("INVISIBLE"):
365	                opt = exp.IndexConstraintOption(visible=False)
366	            elif self._match_text_seq("ENGINE_ATTRIBUTE"):
367	                self._match(TokenType.EQ)
368	                opt = exp.IndexConstraintOption(engine_attr=self._parse_string())
369	            elif self._match_text_seq("SECONDARY_ENGINE_ATTRIBUTE"):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "offset": 7205, "limit": 75}
[tool_result] 7205	        return None
7206	
7207	    def _parse_column_constraint(self) -> exp.Expr | None:
7208	        this = self._parse_id_var() if self._match(TokenType.CONSTRAINT) else None
7209	
7210	        procedure_option_follows = (
7211	            self._match(TokenType.WITH, advance=False)
7212	            and self._next
7213	            and self._next.text.upper() in self.PROCEDURE_OPTIONS
7214	        )
7215	
7216	        if not procedure_option_follows and self._match_texts(self.CONSTRAINT_PA
…[2196 chars elided]…
))
7271	        return self.expression(
7272	            exp.UniqueColumnConstraint(
7273	                nulls=self._match_text_seq("NULLS", "NOT", "DISTINCT"),
7274	                this=self._parse_schema(self._parse_unique_key()),
7275	                index_type=self._match(TokenType.USING) and self._advance_any() and self._prev.text,
7276	                on_conflict=self._parse_on_conflict(),
7277	                options=self._parse_key_constraint_options(),
7278	            )
7279	        )
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; ls .lithify/harness/skills/sqlglot-dialect-functions/scripts/ 2>/dev/null; $PY -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a))','CREATE TABLE t (a INT, b INT, UNIQUE KEY \\`Index\\` (b))','CREATE TABLE t (a INT, c INT, UNIQUE INDEX \\`Key\\` (c))','CREATE TABLE t (a INT, b INT, KEY \\`Index\\` (b))','CREATE TABLE t (a INT, b INT, INDEX \\`Key\\` (b))']:\n    try:\n        print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', str(e).splitlines()[0])\n\"", "description": "Reproduce quoted index name parse failures"}
[tool_result] ast_check.py
ERR Expecting ). Line 1, Col: 56.
ERR Expecting ). Line 1, Col: 48.
ERR Expecting ). Line 1, Col: 48.
CREATE TABLE t (a INT, b INT, INDEX `Index` (b))
CREATE TABLE t (a INT, b INT, INDEX `Key` (b))
[assistant] Reproduced: the three `UNIQUE ...` forms fail, while `KEY`/`INDEX` quoted names parse. The cause is `_parse_unique_key`, which tests the token's text without checking its type. `` `Unique` `` uppercases to `UNIQUE`, which is a constraint keyword, so the name is rejected. `_parse_unnamed_constraint` already guards against this with an IDENTIFIER check, so I'll apply the same guard here.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)", "new_string": "        if (\n            self._curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfrom sqlglot import exp\ncases=['CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY \\`Unique\\` (a))','CREATE TABLE t (a INT, b INT, UNIQUE KEY \\`Index\\` (b))','CREATE TABLE t (a INT, c INT, UNIQUE INDEX 
…[413 chars elided]…
     print('   ', [type(c.args.get('kind')).__name__ for c in e.find_all(exp.ColumnDef)][:0], [type(x).__name__ for x in e.find_all(exp.UniqueColumnConstraint, exp.IndexColumnConstraint, exp.Constraint)], [ (x.name) for x in e.find_all(exp.Identifier) if x.quoted])\n    except Exception as ex: print('ERR', str(ex).splitlines()[0])\n\"", "description": "Apply fix and check quoted constraint names"}
[tool_result] CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a))
    [] ['UniqueColumnConstraint'] ['Unique']
CREATE TABLE t (a INT, b INT, UNIQUE `Index` (b))
    [] ['UniqueColumnConstraint'] ['Index']
CREATE TABLE t (a INT, c INT, UNIQUE `Key` (c))
    [] ['UniqueColumnConstraint'] ['Key']
CREATE TABLE t (a INT, b INT, INDEX `Index` (b))
    [] ['IndexColumnConstraint'] ['Index']
CREATE TABLE t (a INT, b INT, INDEX `Key` (b))
    [] ['IndexColumnConstraint'] ['Key']
CREATE TABLE t (a INT, b INT, CONSTRAINT `Key` UNIQUE `Index` (b))
    [] ['Constraint', 'UniqueColumnConstraint'] ['Key', 'Index']
CREATE TABLE t (a INT, b INT, UNIQUE `Unique` (b))
    [] ['UniqueColumnConstraint'] ['Unique']
CREATE TABLE t (a INT, b INT, UNIQUE (b))
    [] ['UniqueColumnConstraint'] []
[assistant] The quoted names now parse as the right constraint nodes. Two things to check: whether dropping the `KEY` keyword in `UNIQUE KEY` is existing behaviour for unquoted names, and whether the `KEY`/`INDEX` forms fail in other statement positions (e.g. `ALTER TABLE`), since the report says they do.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\ncases=['CREATE TABLE t (a INT, b INT, UNIQUE KEY b (b))','CREATE TABLE t (a INT, b INT, UNIQUE KEY \\`Key\\` (b))','ALTER TABLE t ADD KEY \\`Index\\` (b)','ALTER TABLE t ADD UNIQUE KEY \\`Unique\\` (b)','
…[266 chars elided]…
REATE TABLE t (a INT, b INT, PRIMARY KEY \\`Key\\` (b))','CREATE TABLE t (a INT, b INT, FOREIGN KEY \\`Key\\` (b) REFERENCES u (x))']\nfor s in cases:\n    try: print(sqlglot.transpile(s, read='mysql', write='mysql')[0])\n    except Exception as e: print('ERR', str(e).splitlines()[0])\n\"; git stash list | head -0; git diff --stat", "description": "Test quoted names across more MySQL index forms"}
[tool_result] CREATE TABLE t (a INT, b INT, UNIQUE b (b))
CREATE TABLE t (a INT, b INT, UNIQUE `Key` (b))
ALTER TABLE t ADD INDEX `Index` (b)
ALTER TABLE t ADD UNIQUE `Unique` (b)
ALTER TABLE t ADD INDEX `Key` (b)
ALTER TABLE t ADD UNIQUE `Index` (b)
CREATE TABLE t (a INT, b INT, UNIQUE `Index` (b))
CREATE TABLE t (a INT, b INT, INDEX `Unique` (b))
CREATE TABLE t (a INT, b INT, FULLTEXT INDEX `Key` (b))
ERR Expecting ). Line 1, Col: 47.
ERR Expecting (. Line 1, Col: 47.
head: illegal line count -- 0
 sqlglot/parser.py | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)
[assistant] The `UNIQUE` forms are fixed. Two results to note: `PRIMARY KEY `Key`` fails, but MySQL doesn't allow a name there, so that's out of scope. `FOREIGN KEY `Key` (b)` also fails, but that's a separate parse path that the report doesn't mention. Next I'll add the regression test next to the existing MySQL constraint tests.
[tool_use Bash] {"command": "grep -n \"UNIQUE KEY\\|UNIQUE INDEX\\|def test_ddl\\|def test_.*index\\|def test_.*constraint\" tests/dialects/test_mysql.py | head -30", "description": "Find existing MySQL DDL index tests"}
[tool_result] 12:    def test_ddl(self):
140:            "CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`id`), UNIQUE KEY `id` (`id`))",
144:            "CREATE TABLE IF NOT EXISTS industry_info (a BIGINT(20) NOT NULL AUTO_INCREMENT, b BIGINT(20) NOT NULL, c VARCHAR(1000), PRIMARY KEY (a), UNIQUE KEY d (b), KEY e (b))",
164:            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
1289:    def test_show_index(self):
[tool_use Read] {"file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "offset": 136, "limit": 32}
[tool_result] 136	            "ALTER TABLE t ADD KEY `i` (`c`)",
137	            "ALTER TABLE t ADD INDEX `i` (`c`)",
138	        )
139	        self.validate_identity(
140	            "CREATE TABLE `foo` (`id` char(36) NOT NULL DEFAULT (uuid()), PRIMARY KEY (`id`), UNIQUE KEY `id` (`id`))",
141	            "CREATE TABLE `foo` (`id` CHAR(36) NOT NULL DEFAULT (UUID()), PRIMARY KEY (`id`), UNIQUE `id` (`id`))",
142	        )
143	        self.validate_identity(
144	            "CREATE TABLE IF NOT EXISTS industry
…[1022 chars elided]…
() ON UPDATE CURRENT_TIMESTAMP()) DEFAULT CHARACTER SET=utf8 ROW_FORMAT=DYNAMIC",
158	        )
159	        self.validate_identity(
160	            "CREATE TABLE `foo` (a VARCHAR(10), KEY idx_a (a DESC))",
161	            "CREATE TABLE `foo` (a VARCHAR(10), INDEX idx_a (a DESC))",
162	        )
163	        self.validate_identity(
164	            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
165	            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
166	        )
167	
[assistant] The existing tests already expect `UNIQUE KEY`/`UNIQUE INDEX` to normalize to `UNIQUE`, so I'll keep that normalization and add the quoted-name cases beside them.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n", "new_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY `Unique` (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))\",\n            \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))\",\n        )\n"}
[tool_result] The file ~/.cache/lithify/work/repo-55c905b0df68/20261026-184913-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py 2>&1 | tail -5; $PY -m pytest -q -p no:cacheprovider --color=no tests/dialects/test_mysql.py::TestMySQL::test_ddl 2>&1 | tail -3", "description": "Run MySQL dialect test file"}
[tool_result] .............................. [ 60%]
....................                                              [100%]
50 passed, 481 subtests passed in 0.37s
.                                                              [100%]
1 passed, 10 subtests passed in 0.07s
[assistant] The MySQL test file passes (50 tests). Now the full suite, which the harness requires because this change is in the base parser and affects every dialect.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY .lithify/harness/scripts/run_suite.py 2>&1 | tail -25", "description": "Run full test suite via harness script", "timeout": 600000}
[tool_result] WARNING: 3 other pytest process(es) running; expect slower runs:
   8642       00:23 <work>/env-sqlglot/b
   8855       00:14 <work>/env-sqlglot/b
  34207 02-23:18:48 /private/tmp/claude-501/-Users-user-Coding-delvera-foundational-lithify/19d43989-6c6b-4090-9032-1fdbf9e87d20/scratchpad/pr-work/env-tenacit
RUN: <work>/env-sqlglot/bin/python -m pytest -v -p no:cacheprovider --color=no
LOG: /var/folders/5n/5k3tqbk921zc6rdrr10wc7th0000gn/T/lithify-suite-ce9f641888.log
ELAPSED: 72s
SUMMARY: 1087 passed, 17844 subtests passed in 71.01s (0:01:11)
EXIT: 0
[assistant] Quoted index and constraint names that look like keywords now parse and round-trip in MySQL. The full suite passes: `SUMMARY: 1087 passed, 17844 subtests passed in 71.01s`, `EXIT: 0`.

**Cause:** `Parser._parse_unique_key` in `sqlglot/parser.py` rejected any name whose text matched a constraint keyword, including backtick-quoted ones. `` `Unique` `` uppercases to `UNIQUE`, so it was refused, and the same happened for `` `Index` `` and `` `Key` ``. The `_parse_unnamed_constraint` path already skips IDENTIFIER tokens for this reason, so I applied the same check here.

**Change:**
- `sqlglot/pars
…[888 chars elided]…
the failure for `KEY `Index`` or `INDEX `Key``. Both already parsed in `CREATE TABLE` and `ALTER TABLE ... ADD`. If you saw them fail, I'd need the exact statement.
- Not fixed: `FOREIGN KEY `Key` (b) REFERENCES ...` still fails to parse. MySQL allows an index name there, but it is a different parse path from the one in the report. `PRIMARY KEY `Key`` also fails, but MySQL does not allow a name there, so I left it alone.
- The fix is in the base parser, so it applies to every dialect that uses the shared constraint code, not only MySQL. The full suite covers that.

The change is not committed.
