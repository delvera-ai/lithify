---
name: adapter-change
description: Use when a task touches src/lithify/adapters/ (Claude Code, Codex, Antigravity or mock adapters, CLI flags or output parsing).
---

# Changing an adapter

1. Record the CLI version you tested against (`claude --version`, `codex --version`, `agy --version`) in the PR description and in a comment next to the format you parse.
2. Capture real output from that version (`lithify role <cli> "say hi"` or the CLI's headless mode), redact secrets, session ids and home paths, and save it as a fixture under `tests/fixtures/`.
3. Add a parse test that loads the fixture and checks `ok`, `text`, the transcript and the token/cost fields.
4. Keep parsing tolerant: unknown event types are skipped, missing usage fields default to 0, and a malformed line never raises.
5. Do not change default permission flags without updating the README safety model.
