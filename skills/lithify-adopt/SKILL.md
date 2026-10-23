---
name: lithify-adopt
description: Review and adopt (or reject) pending lithify harness proposals — changes to CLAUDE.md/AGENTS.md rules, skills or scripts that a lithify run found but did not promote automatically. Use when the user says /lithify-adopt or asks to review harness proposals.
---

# Review harness proposals

Adopting a proposal changes the instructions every future agent session in this repository
receives, so review it with the user rather than adopting silently.

1. `lithify adopt --list` to see pending proposals.
2. For each one the user wants to look at, read `.lithify/proposals/<id>/PROPOSAL.md` and
   `harness.diff`. Summarise each changed component in one line, with the reflector's verdict
   (`helped`, `hurt`, `no observed effect`, `confounded`) and the evidence it cites.
3. Flag anything that should not be adopted: rules that copy test expectations or fixture
   values, task-specific facts written as permanent memory, instructions to edit or skip
   tests, credentials, or always-on text that a skill could carry instead.
4. Adopt only what the user approves:
   - everything: `lithify adopt <id>`
   - some components: `lithify adopt <id> --only guardrails.md skills/<name>`
   - drop it: `lithify adopt <id> --reject`
5. Show the resulting `git diff --stat -- .lithify CLAUDE.md AGENTS.md .claude .agents` and
   remind the user to commit it.
