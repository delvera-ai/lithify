# lithify improvement library

Each entry: what situation a lesson applies to, and the harness operation that helped.
Read an entry's EXPERIENCE.md and harness/ before reusing a component.

- [20261029-144515-oracle-dialect-json-table-fails](20261029-144515-oracle-dialect-json-table-fails/EXPERIENCE.md) — **when** A bug report says a clause of a SQL construct fails to parse (here, JSON_TABLE with FORMAT JSON). The reported form already parses. Probing sibling variants of that same clause finds one that errors with the report's message shape, and the repo has no local grammar reference for that variant. **then** In skills/parse-failure-triage step 3, keep the bound that an accepted clause needs its parent construct, but do not make the fix conditional on verifying the grammar. State that an in-scope ERR matching the report's wording is fixed in the owning parser, and that the grammar source goes in the final message as a disclosure. The conditional wording in comp-1 was read as a veto and produced no fix, the unconditional wording in inv-1 produced the fix, and base-1 with no skill also produced no fix.
