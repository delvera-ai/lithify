# lithify improvement library

Each entry: what situation a lesson applies to, and the harness operation that helped.
Read an entry's EXPERIENCE.md and harness/ before reusing a component.

- [20261023-125452-add-parse-age-value-to-app-users](20261023-125452-add-parse-age-value-to-app-users/EXPERIENCE.md) — **when** Adding or changing a user-input validator where nearby legacy validators omit a documented rejection side effect. **then** In skills/input-validation, require reading the authoritative rejection contract before copying neighboring validators, preserving original inputs for required audit calls, and testing rejection side effects alongside accepted results. Explain explicitly when legacy validators predate the contract.
