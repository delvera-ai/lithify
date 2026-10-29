---
name: parse-failure-triage
description: Use when a SQL statement is reported to fail to parse, transpile or round-trip in a dialect (e.g. "X fails to parse", a ParseError, a clause such as FORMAT JSON or JSON_TABLE), and you must reproduce it and fix the parser or generator.
---

# Parse failure triage

1. Reproduce the statement exactly as reported. Write it to a scratch file outside the
   repository, one statement per line, then run:
   `<python> -I .lithify/harness/scripts/probe_parse.py --read <dialect> < stmts.sql`
   Use the interpreter named in `memory.md`.

2. If the reported statement is OK, do not stop there. Put every variant of the clause the
   report names into the same file: input forms (qualified column, bind variable, function call,
   literal, CAST), clauses that can follow the input (ENCODING, ERROR ON ERROR, ON EMPTY), and
   placements (JOIN, CTE, subquery, IN). Probe them all in one run.

3. A reproduced ERR whose shape matches the report's wording is the bug, even when the report did
   not name that exact variant. Fix it in the parser or generator that owns the clause, following
   the helpers the surrounding code uses. ERR outside the reported construct is not part of this
   fix: list it in your final message.

4. Add a case for each fixed statement to the existing test function for that dialect, using the
   same assertion style. Do not edit or delete existing assertions.

5. Re-run the probe on the reported statement and its variants: every line must read OK. Then run
   the dialect's test file, then the full suite (command in `memory.md`). You are done when the
   probe is clean and the full suite exits 0 in output you have read.

6. If nothing reproduces, say so and quote the probe output for every variant you tried. Do not
   change code on speculation.
