# trajectory base-1

final message:
MySQL now accepts backtick-quoted index and constraint names that look like keywords (`` `Unique` ``, `` `Index` ``, `` `Key` ``). They parse, keep their names, and round-trip. The full suite passes (1087 tests) and ruff is clean. The changes are uncommitted in the worktree.

**Cause:** the bug is in the shared parser, not MySQL-specific code. `_parse_unique_key` and `_parse_unique` matched on token text, so a quoted identifier whose text equals a constraint keyword was consumed as the keyword.

**Fix** (`sqlglot/parser.py`):
- `_parse_unique_key` no longer rejects an IDENTIFIER token just because its text matches a constraint keyword.
- `_parse_unique` only consumes `KEY`/`INDEX` when the next token isn't a quoted identifier, so `` UNIQUE `Key` (c) `` keeps `Key` as the name.

**Test** (`tests/dialects/test_mysql.py`): added a `validate_identity` case with all three names. I didn't change any existing test.

**Output convention:** the `KEY`/`INDEX` keyword is dropped on output, matching existing tests (`UNIQUE KEY d (b)` → `UNIQUE d (b)`). So the input `UNIQUE KEY `Unique` (a)` comes out as `` UNIQUE `Unique` (a) ``. That is the same MySQL meaning, but it is not byte-identical to the input. If you want the keyword kept, that's a separate change.

**Not fixed:** a column-level Postgres `UNIQUE "Unique"` still produces `UNIQUE UNIQUE`. The output is identical before and after my change, so it's pre-existing and outside this MySQL fix.

## events
[tool_use Bash] {"command": "rtk git status --short | head; grep -n \"UNIQUE\\|\\\"KEY\\\"\\|INDEX\\|CONSTRAINT_PARSERS\\|_parse_index_constraint\\|_parse_unnamed_constraint\" sqlglot/dialects/mysql.py | head -60; grep -n \"def _parse_index_constraint\\|def _parse_unnamed_constraint\\|CONSTRAINT_PARSERS = \\|def _parse_constraint\\|def _parse_unique\\b\\|def _parse_unique(\" sqlglot/parser.py", "description": "Check git status and find constraint parsing code"}
[tool_result] (eval):1: command not found: rtk
86:            "KEY": TokenType.KEY,
7226:    def _parse_constraint(self) -> exp.Expr | None:
7234:    def _parse_unnamed_constraints(self) -> list[exp.Expr]:
7244:    def _parse_unnamed_constraint(
7269:    def _parse_unique(self) -> exp.UniqueColumnConstraint:
[tool_use Bash] {"command": "git status --short; sed -n 7180,7300p sqlglot/parser.py; grep -n \"INDEX_CONSTRAINT\\|KEY_CONSTRAINT\\|_parse_index_constraint\" sqlglot/parser.py sqlglot/dialects/mysql.py | head -40", "description": "Check git status and read constraint parsing code"}
[tool_result]             if not identity:
                this.set("expression", self._parse_range())
            elif not this.args.get("start") and self._match(TokenType.NUMBER, advance=False):
                args = self._parse_csv(self._parse_bitwise)
                this.set("start", seq_get(args, 0))
                this.set("increment", seq_get(args, 1))

            self._match_r_paren()

        return this

    def _parse_inline(self) -> exp.InlineLengthColumnConstraint:
        self._match_text_se
…[3900 chars elided]…
CADE"
                elif self._match_text_seq("RESTRICT"):
                    action = "RESTRICT"
                elif self._match_pair(TokenType.SET, TokenType.NULL):
                    action = "SET NULL"
                elif self._match_pair(TokenType.SET, TokenType.DEFAULT):
                    action = "SET DEFAULT"
sqlglot/parser.py:1625:    KEY_CONSTRAINT_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
sqlglot/parser.py:7307:                    self.KEY_CONSTRAINT_OPTIONS, raise_unmatched=False
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in 'CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY `Unique` (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))' 'CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a))' 'CREATE TABLE t (a INT, KEY `Index` (a))' 'CREATE TABLE t (a INT, UNIQUE INDEX `Key` (a))' 'CREATE TABLE t (a INT, UNIQUE `Unique` (a))' 'CREATE TABLE t (a INT, KEY `Key` (a))'; do $PY -c \"\nimport sys, sqlglot\ns=sys.argv[1]\ntry:\n  print(sqlglot.transpile(s, read='mysql', write='mysql'))\nexcept Exception as e: print('ERR', str(e)[:300])\n\" \"$s\"; done", "description": "Reproduce MySQL quoted index name parse failures"}
[tool_result] ERR Expecting ). Line 1, Col: 56.
  CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY [4m`Unique`[0m (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))
ERR Expecting ). Line 1, Col: 42.
  CREATE TABLE t (a INT, UNIQUE KEY [4m`Unique`[0m (a))
['CREATE TABLE t (a INT, INDEX `Index` (a))']
ERR Expecting ). Line 1, Col: 41.
  CREATE TABLE t (a INT, UNIQUE INDEX [4m`Key`[0m (a))
ERR Expecting ). Line 1, Col: 38.
  CREATE TABLE t (a INT, UNIQUE [4m`Unique`[0m (a))
['CREATE TABLE t (a INT, INDEX `Key` (a))']
[tool_use Bash] {"command": "grep -n \"_parse_unique_key\\|_parse_index_constraint\\|_parse_unique\\b\" sqlglot/parser.py sqlglot/dialects/*.py | head -30; grep -n \"def _parse_index_constraint\" -A25 sqlglot/parser.py | head -50; grep -n '\"UNIQUE\"' sqlglot/parser.py sqlglot/dialects/mysql.py", "description": "Locate unique key and index constraint parser code"}
[tool_result] sqlglot/parser.py:1382:        "UNIQUE": lambda self: self._parse_unique(),
sqlglot/parser.py:7264:    def _parse_unique_key(self) -> exp.Expr | None:
sqlglot/parser.py:7269:    def _parse_unique(self) -> exp.UniqueColumnConstraint:
sqlglot/parser.py:7274:                this=self._parse_schema(self._parse_unique_key()),
sqlglot/parser.py:1382:        "UNIQUE": lambda self: self._parse_unique(),
sqlglot/parser.py:1448:        "UNIQUE",
sqlglot/parser.py:7861:        if self._match_text_seq("WITH", "UNIQUE"):
sqlglot/parser.py:7863:        elif self._match_text_seq("WITHOUT", "UNIQUE"):
[tool_use Bash] {"command": "grep -n \"CONSTRAINT_PARSERS\\|SCHEMA_UNNAMED_CONSTRAINTS\" -A3 sqlglot/dialects/mysql.py sqlglot/parser.py | head -80; grep -n '\"INDEX\"\\|\"KEY\"\\|FULLTEXT\\|\"SPATIAL\"' sqlglot/dialects/mysql.py sqlglot/parser.py | head", "description": "Inspect MySQL constraint parser registrations"}
[tool_result] sqlglot/parser.py:1326:    CONSTRAINT_PARSERS: t.ClassVar = {
sqlglot/parser.py-1327-        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py-1328-        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
sqlglot/parser.py-1329-        "CASESPECIFIC": lambda self: self.expression(exp.CaseSpecificColumnConstraint(not_=False)),
--
sqlglot/parser.py:1441:    SCHEMA_UNNAMED_CONSTRAINTS: t.ClassVar = {
sqlglot/parser.py-1442-        "CHECK",
sqlglot/parser.py-1
…[2207 chars elided]…
parser.py:3947:            self._parse_wrapped_id_vars() if self._match_text_seq("USING", "KEY") else None
sqlglot/parser.py:4464:            if self._match_text_seq("USING", "INDEX", "TABLESPACE")
sqlglot/parser.py:5520:            elif self._match_text_seq("FOR", "KEY", "SHARE"):
sqlglot/parser.py:5522:            elif self._match_text_seq("FOR", "NO", "KEY", "UPDATE"):
sqlglot/parser.py:7270:        self._match_texts(("KEY", "INDEX"))
sqlglot/parser.py:7797:        self._match_text_seq("KEY")
[tool_use Bash] {"command": "grep -n \"INDEX\\|KEY\" sqlglot/dialects/mysql.py | head -40; sed -n 7375,7410p sqlglot/parser.py; grep -n \"def _parse_schema\" -A30 sqlglot/parser.py | head -50", "description": "Inspect MySQL index/key parsing and schema parsing"}
[tool_result] 78:        KEYWORDS = {
79:            **tokens.Tokenizer.KEYWORDS,
86:            "KEY": TokenType.KEY,
130:            "_KEYBCS2": TokenType.INTRODUCER,
        self,
        wrapped_optional: bool = False,
        in_props: bool = False,
        named_primary_key: bool = False,
    ) -> exp.PrimaryKeyColumnConstraint | exp.PrimaryKey:
        desc = (
            self._prev.token_type == TokenType.DESC
            if self._match_set((TokenType.ASC, TokenType.DESC))
            else None
     
…[1756 chars elided]…
uted_column: bool = True
7018-    ) -> exp.Expr | None:
7019-        # column defs are not really columns, they're identifiers
7020-        if isinstance(this, exp.Column):
7021-            this = this.this
7022-
7023-        if not computed_column:
7024-            self._match(TokenType.ALIAS)
7025-
7026-        kind = self._parse_types(schema=True)
7027-
7028-        if self._match_text_seq("FOR", "ORDINALITY"):
7029-            return self.expression(exp.ColumnDef(this=this, ordinality=True))
[tool_use Bash] {"command": "grep -n \"IndexColumnConstraint\\|\\\"INDEX\\\":\\|\\\"KEY\\\":\" sqlglot/parser.py | head; sed -n 1326,1345p sqlglot/parser.py; sed -n 1441,1460p sqlglot/parser.py", "description": "Find index constraint parser registrations"}
[tool_result]     CONSTRAINT_PARSERS: t.ClassVar = {
        "AUTOINCREMENT": lambda self: self._parse_auto_increment(),
        "AUTO_INCREMENT": lambda self: self._parse_auto_increment(),
        "CASESPECIFIC": lambda self: self.expression(exp.CaseSpecificColumnConstraint(not_=False)),
        "CHARACTER SET": lambda self: self.expression(
            exp.CharacterSetColumnConstraint(this=self._parse_var_or_string())
        ),
        "CHECK": lambda self: self._parse_check_constraint(),
        "COLLATE"
…[705 chars elided]…
DE",
        "FOREIGN KEY",
        "LIKE",
        "PERIOD",
        "PRIMARY KEY",
        "UNIQUE",
        "BUCKET",
        "TRUNCATE",
    }

    NO_PAREN_FUNCTION_PARSERS: t.ClassVar = {
        "ANY": lambda self: self.expression(exp.Any(this=self._parse_bitwise())),
        "CASE": lambda self: self._parse_case(),
        "CONNECT_BY_ROOT": lambda self: self.expression(
            exp.ConnectByRoot(this=self._parse_column())
        ),
        "IF": lambda self: self._parse_if(),
    }
[tool_use Bash] {"command": "grep -n \"TokenType.INDEX\\|TokenType.KEY\\b\" sqlglot/parser.py | head -20; grep -n \"def _parse_index\\b\\|def _parse_index(\" -A30 sqlglot/parser.py | head -60; grep -n \"KEY\\|INDEX\" sqlglot/parser.py | sed -n 1,200p | grep -i \"create\\|constraint\\|table_constraint\\|_parse_schema\\|_parse_table_constraint\" ", "description": "Locate index and key token handling in parser"}
[tool_result] 630:        TokenType.INDEX,
644:        TokenType.INDEX,
827:        TokenType.INDEX,
1671:        TokenType.INDEX,
1672:        TokenType.KEY,
2414:        elif create_token_type == TokenType.INDEX:
4500:            if not self._match(TokenType.INDEX):
4533:                self._match_set((TokenType.INDEX, TokenType.KEY))
4785:        if self._match(TokenType.INDEXED_BY):
8742:        if self._match(TokenType.TABLE) or self._match(TokenType.INDEX):
4484:    def _parse_index(
4485-        self,
…[857 chars elided]…
p.Index(
4510-                this=index, table=table, unique=unique, primary=primary, amp=amp, params=params
4511-            )
4512-        )
4513-
4514-    def _parse_table_hints(self) -> list[exp.Expr] | None:
1625:    KEY_CONSTRAINT_OPTIONS: t.ClassVar[OPTIONS_TYPE] = {
2414:        elif create_token_type == TokenType.INDEX:
2415:            # Postgres allows anonymous indexes, eg. CREATE INDEX IF NOT EXISTS ON t(c)
7307:                    self.KEY_CONSTRAINT_OPTIONS, raise_unmatched=False
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor s in ['CREATE TABLE t (a INT, KEY \\`Index\\` (a))','CREATE TABLE t (a INT, KEY \\`Key\\` (a))','CREATE TABLE t (a INT, KEY idx (a))','CREATE TABLE t (a INT, UNIQUE KEY idx (a))','CREATE TABLE t (a INT, UNIQUE KEY \\`idx\\` (a))']:\n  print(repr(sqlglot.parse_one(s, read='mysql')))\n  print()\n\" 2>&1 | head -60; grep -n \"KEY\\|INDEX\" sqlglot/dialects/mysql.py sqlglot/tokens.py | head", "description": "Inspect AST for MySQL KEY and UNIQUE cases"}
[tool_result] Create(
  this=Schema(
    this=Table(
      this=Identifier(this=t, quoted=False)),
    expressions=[
      ColumnDef(
        this=Identifier(this=a, quoted=False),
        kind=DataType(this=DType.INT, nested=False)),
      IndexColumnConstraint(
        this=Identifier(this='Index', quoted=True),
        expressions=[
          Ordered(
            this=Column(
              this=Identifier(this=a, quoted=False)),
            nulls_first=True)],
        index_type=False)]),
  kind=TABLE,
  r
…[1239 chars elided]…
           "KEY": TokenType.KEY,
sqlglot/dialects/mysql.py:130:            "_KEYBCS2": TokenType.INTRODUCER,
sqlglot/tokens.py:55:    KEYWORDS: t.ClassVar[dict[str, TokenType]]
sqlglot/tokens.py:75:    _KEYWORD_TRIE: t.ClassVar[dict[str, object]]
sqlglot/tokens.py:106:        if cls.HINT_START in cls.KEYWORDS:
sqlglot/tokens.py:108:        cls._KEYWORD_TRIE = new_trie(
sqlglot/tokens.py:111:                *cls.KEYWORDS,
sqlglot/tokens.py:196:    _KEYWORD_TRIE: t.ClassVar[dict[str, object]] = {}
[tool_use Bash] {"command": "grep -n \"def _match_texts\" -A10 sqlglot/parser.py; grep -n '\"KEY\":\\|\"INDEX\":' sqlglot/parser.py", "description": "Read _match_texts helper and key constraint entries"}
[tool_result] 1927:    def _match_texts(self, texts: t.Collection[str], advance: bool = True) -> bool:
1928-        if self._curr.token_type != TokenType.STRING and self._curr.text.upper() in texts:
1929-            if advance:
1930-                self._advance()
1931-            return True
1932-        return False
1933-
1934-    def _match_text_seq(self, *texts: str, advance: bool = True) -> bool:
1935-        index = self._index
1936-        string_type = TokenType.STRING
1937-        for text in texts:
[assistant] The root cause is in the shared parser, not MySQL-specific code: `_parse_unique_key` and `_parse_unique` match on token text, so a backtick-quoted `` `Unique` `` / `` `Key` `` / `` `Index` `` (which has IDENTIFIER token type) is treated as a keyword. I'll make both checks skip identifier tokens.
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161235-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", "old_string": "    def _parse_unique_key(self) -> exp.Expr | None:\n        if self._curr and self._curr.text.upper() in self.CONSTRAINT_PARSERS:\n            return None\n        return self._parse_id_var(any_token=False)\n\n    def 
…[202 chars elided]…
curr\n            and self._curr.token_type != TokenType.IDENTIFIER\n            and self._curr.text.upper() in self.CONSTRAINT_PARSERS\n        ):\n            return None\n        return self._parse_id_var(any_token=False)\n\n    def _parse_unique(self) -> exp.UniqueColumnConstraint:\n        if self._curr.token_type != TokenType.IDENTIFIER:\n            self._match_texts((\"KEY\", \"INDEX\"))"}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161235-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py has been updated successfully.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; for s in 'CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY `Unique` (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))' 'CREATE TABLE t (a INT, UNIQUE `Key` (a))' 'CREATE TABLE t (a INT, UNIQUE INDEX `Unique` (a))' 'CREATE TABLE t (a INT UNIQUE KEY `Index`)' 'CREATE TABLE t (a INT, UNIQUE KEY idx (a))' 'CREATE TAB
…[186 chars elided]…
[0])\nexcept Exception as e: print('ERR', str(e)[:300])\n\" \"$s\"; done; $PY -c \"\nimport sqlglot\nprint(sqlglot.transpile('CREATE TABLE t (a INT, CONSTRAINT \\\"Unique\\\" UNIQUE (a))', read='postgres', write='postgres'))\nprint(sqlglot.transpile('CREATE TABLE t (a INT, UNIQUE \\\"Unique\\\" (a))', read='postgres', write='postgres'))\"", "description": "Re-run repro cases after the parser fix"}
[tool_result ERROR] Exit code 1
CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))
CREATE TABLE t (a INT, UNIQUE `Key` (a))
CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (a INT UNIQUE `Index`)
CREATE TABLE t (a INT, UNIQUE idx (a))
CREATE TABLE t (a INT, UNIQUE (a))
CREATE TABLE t (a INT UNIQUE CHECK (a > 0))
Traceback (most recent call last):
  File "<string>", line 4, in <module>
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161235-m
…[2677 chars elided]…
b04f649b80/20261027-161235-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", line 9188, in _match_r_paren
    self.raise_error("Expecting )")
  File "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161235-mysql-dialect-quoted-index-or-co/base-1/sqlglot/parser.py", line 1977, in raise_error
    raise error
sqlglot.errors.ParseError: Expecting ). Line 1, Col: 38.
  CREATE TABLE t (a INT, UNIQUE [4m"Unique"[0m (a))
['CREATE TABLE t (a INT, CONSTRAINT "Unique" UNIQUE (a))']
[assistant] Backtick-quoted cases now parse and keep their names. The double-quoted Postgres case still fails, so I'm checking whether that's a pre-existing gap or something my change missed.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; $PY -c \"\nimport sqlglot\nfor d,s in [('postgres','CREATE TABLE t (a INT, UNIQUE \\\"Unique\\\" (a))'),('postgres','CREATE TABLE t (a INT, UNIQUE \\\"idx\\\" (a))'),('postgres','CREATE TABLE t (a INT UNIQUE \\\"Unique\\\")'),('sqlite','CREATE TABLE t (a INT, UNIQUE \\\"Unique\\\" (a))')]:\n  try: print(sqlglot.transpile(s, read=d, write=d)[0])\n  except Exception as e: print('ERR', d, s, str(e).splitlines()[0])\n\"", "description": "Check quoted UNIQUE names in other dialects"}
[tool_result] ERR postgres CREATE TABLE t (a INT, UNIQUE "Unique" (a)) Expecting ). Line 1, Col: 38.
ERR postgres CREATE TABLE t (a INT, UNIQUE "idx" (a)) Expecting ). Line 1, Col: 35.
CREATE TABLE t (a INT UNIQUE UNIQUE)
ERR sqlite CREATE TABLE t (a INT, UNIQUE "Unique" (a)) Expecting ). Line 1, Col: 38.
[tool_use Bash] {"command": "PY=<work>/env-sqlglot/bin/python; rm -rf /tmp/orig_sg && mkdir /tmp/orig_sg && git archive HEAD sqlglot | tar -x -C /tmp/orig_sg && cat > /tmp/cmp.py <<'EOF'\nimport sqlglot\ncases = [('postgres','CREATE TABLE t (a INT UNIQUE \"Unique\")'),('postgres','CREATE TABLE t (a INT UNIQUE \"idx\")'),('mysql','CREATE TABLE t (a INT UNIQUE KEY idx)'),
…[139 chars elided]…
   try: print(sqlglot.transpile(s, read=d, write=d)[0])\n    except Exception as e: print('ERR', d, s, str(e).splitlines()[0])\nEOF\necho NEW; $PY -I -c \"import sys; sys.path.insert(0,'.'); exec(open('/tmp/cmp.py').read())\"; echo OLD; $PY -I -c \"import sys; sys.path.insert(0,'/tmp/orig_sg'); exec(open('/tmp/cmp.py').read())\"", "description": "Compare old and new parser output on sample cases"}
[tool_result] NEW
CREATE TABLE t (a INT UNIQUE UNIQUE)
ERR postgres CREATE TABLE t (a INT UNIQUE "idx") Expecting ). Line 1, Col: 34.
CREATE TABLE t (a INT UNIQUE idx)
CREATE TABLE t (a INT, UNIQUE `Unique` (a))
CREATE TABLE t (a INT, UNIQUE `Unique` (a))
OLD
CREATE TABLE t (a INT UNIQUE UNIQUE)
ERR postgres CREATE TABLE t (a INT UNIQUE "idx") Expecting ). Line 1, Col: 34.
CREATE TABLE t (a INT UNIQUE idx)
ERR mysql CREATE TABLE t (a INT, UNIQUE KEY `Unique` (a)) Expecting ). Line 1, Col: 42.
ERR mysql CREATE TABLE t (a INT, UNIQUE `Unique` (a)) Expecting ). Line 1, Col: 38.
[assistant] Old code rejects the MySQL cases and the new code accepts them. The Postgres column-level `UNIQUE "Unique"` → `UNIQUE UNIQUE` output is identical before and after, so it's pre-existing and outside this MySQL fix. Next I'll check how existing tests expect `UNIQUE KEY` to round-trip, then add coverage.
[tool_use Bash] {"command": "grep -rn \"UNIQUE KEY\\|UNIQUE INDEX\\|UNIQUE \\`\" tests/ | head -20", "description": "Find existing tests covering UNIQUE KEY syntax"}
[tool_result] tests/dialects/test_doris.py:98:            "CREATE TABLE IF NOT EXISTS example_tbl_unique (user_id BIGINT NOT NULL, user_name VARCHAR(50) NOT NULL, city VARCHAR(20), age SMALLINT, sex TINYINT) UNIQUE KEY (user_id, user_name) DISTRIBUTED BY HASH (user_id) BUCKETS 10 PROPERTIES ('enable_unique_key_merge_on_write'='true')"
tests/dialects/test_doris.py:135:        self.validate_identity("CREATE TABLE test_table (c1 INT, c2 INT) UNIQUE KEY (c1)")
tests/dialects/test_doris.py:141:            "CREATE 
…[1345 chars elided]…
: "CREATE UNIQUE INDEX my_idx ON TABLE tbl(a, b)",
tests/dialects/test_dialect.py:2843:                "sqlite": "CREATE UNIQUE INDEX my_idx ON tbl(a, b)",
tests/dialects/test_dialect.py:2846:                "hive": "CREATE UNIQUE INDEX my_idx ON TABLE tbl(a, b)",
tests/dialects/test_dialect.py:2847:                "postgres": "CREATE UNIQUE INDEX my_idx ON tbl(a NULLS FIRST, b NULLS FIRST)",
tests/dialects/test_dialect.py:2848:                "sqlite": "CREATE UNIQUE INDEX my_idx ON tbl(a, b)",
[tool_use Bash] {"command": "grep -n \"KEY\\|INDEX\" tests/dialects/test_mysql.py | grep -i \"create\\|unique\\|quoted\\|\\`\" | head -30; grep -n \"def test_ddl\" tests/dialects/test_mysql.py", "description": "Find MySQL DDL tests mentioning keys and indexes"}
[tool_result] 23:        self.validate_identity("CREATE TABLE temp (id SERIAL PRIMARY KEY)")
29:        self.validate_identity("CREATE TABLE foo (a BIGINT, INDEX USING BTREE (b))")
30:        self.validate_identity("CREATE TABLE foo (a BIGINT, FULLTEXT INDEX (b))")
31:        self.validate_identity("CREATE TABLE foo (a BIGINT, SPATIAL INDEX (b))")
36:        self.validate_identity("ALTER TABLE t ADD INDEX `i` (`c`)")
62:            "CREATE TABLE `oauth_consumer` (`key` VARCHAR(32) NOT NULL, UNIQUE `OAUTH_CONS
…[1750 chars elided]…
TE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
194:                "mysql": "CREATE TABLE x (id INT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id))",
195:                "sqlite": "CREATE TABLE x (id INTEGER NOT NULL AUTOINCREMENT PRIMARY KEY)",
1131:            "CREATE TABLE z (a INT DEFAULT NULL, PRIMARY KEY (a)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"
1141:              PRIMARY KEY (`id`)
1150:  PRIMARY KEY (`id`)
12:    def test_ddl(self):
[assistant] The existing tests fix the convention: `UNIQUE KEY d (b)` normalizes to `UNIQUE d (b)`. I'll add the quoted-name cases in the same style.
[tool_use Bash] {"command": "sed -n 155,172p tests/dialects/test_mysql.py", "description": "Read the surrounding MySQL DDL test block"}
[tool_result]         self.validate_identity(
            "CREATE TABLE t (c DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC",
            "CREATE TABLE t (c DATETIME DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP()) DEFAULT CHARACTER SET=utf8 ROW_FORMAT=DYNAMIC",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), KEY idx_a (a DESC))",
            "CREATE TABLE `foo` (a VARCHAR(10), INDEX idx_a (a DESC))",
        )
        self.validate_identity(
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE INDEX idx_a (a))",
            "CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))",
        )

        self.validate_all(
            "insert into t(i) values (default)",
            write={
                "duckdb": "INSERT INTO t (i) VALUES (DEFAULT)",
                "mysql": "INSERT INTO t (i) VALUES (DEFAULT)",
[tool_use Edit] {"replace_all": false, "file_path": "~/.cache/lithify/work/repo-fdb04f649b80/20261027-161235-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py", "old_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n\n        self.validate_all(", "new_string": "            \"CREATE TABLE `foo` (a VARCHAR(10), UNIQUE idx_a (a))\",\n        )\n        self.validate_identity(\n            \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE KEY `Unique` (a), KEY `Index` (b), UNIQUE INDEX `Key` (c))\",\n            \"CREATE TABLE t (a INT, b INT, c INT, UNIQUE `Unique` (a), INDEX `Index` (b), UNIQUE `Key` (c))\",\n        )\n\n        self.validate_all("}
[tool_result] The file ~/.cache/lithify/work/repo-fdb04f649b80/20261027-161235-mysql-dialect-quoted-index-or-co/base-1/tests/dialects/test_mysql.py has been updated successfully.
[assistant] Now the full check, using the project's test command from the harness notes.
[tool_use Bash] {"command": "<work>/env-sqlglot/bin/python -m pytest -q -p no:cacheprovider --color=no 2>&1 | tail -15", "description": "Run the full project test suite"}
[tool_result] ............................................. [ 11%]
...................................................... [ 16%]
........ [ 17%]
................................. [ 20%]
............................................................................................................................................................................................................................................................... [ 43%]
........................ [ 45%]
......................... [ 48%]

…[167 chars elided]…
.............................................................. [ 68%]
............................................... [ 72%]
........................................................... [ 78%]
....................................................................................................................................... [ 90%]
............................... [ 93%]
.....................................................................      [100%]
1087 passed, 17844 subtests passed in 56.11s
[assistant] All 1087 tests pass. I'll run the linter on the two changed files and clean up the temp copy.
[tool_use Bash] {"command": "rm -rf /tmp/orig_sg /tmp/cmp.py; (<work>/env-sqlglot/bin/python -m ruff check sqlglot/parser.py tests/dialects/test_mysql.py && <work>/env-sqlglot/bin/python -m ruff format --check sqlglot/parser.py tests/dialects/test_mysql.py) 2>&1 | tail -5; git diff --stat", "description": "Lint changed files and show diff stats"}
[tool_result] All checks passed!
2 files already formatted
 sqlglot/parser.py            | 9 +++++++--
 tests/dialects/test_mysql.py | 4 ++++
 2 files changed, 11 insertions(+), 2 deletions(-)
[assistant] MySQL now accepts backtick-quoted index and constraint names that look like keywords (`` `Unique` ``, `` `Index` ``, `` `Key` ``). They parse, keep their names, and round-trip. The full suite passes (1087 tests) and ruff is clean. The changes are uncommitted in the worktree.

**Cause:** the bug is in the shared parser, not MySQL-specific code. `_parse_unique_key` and `_parse_unique` matched on token text, so a quoted identifier whose text equals a constraint keyword was consumed as the keyword.

**Fix** (`sqlglot/parser.py`):
- `_parse_unique_key` no longer rejects an IDENTIFIER token just bec
…[257 chars elided]…
y` case with all three names. I didn't change any existing test.

**Output convention:** the `KEY`/`INDEX` keyword is dropped on output, matching existing tests (`UNIQUE KEY d (b)` → `UNIQUE d (b)`). So the input `UNIQUE KEY `Unique` (a)` comes out as `` UNIQUE `Unique` (a) ``. That is the same MySQL meaning, but it is not byte-identical to the input. If you want the keyword kept, that's a separate change.

**Not fixed:** a column-level Postgres `UNIQUE "Unique"` still produces `UNIQUE UNIQUE`. The output is identical before and after my change, so it's pre-existing and outside this MySQL fix.
