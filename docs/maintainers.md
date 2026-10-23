# Maintainer notes

Repository settings for `delvera-ai/lithify`, what is applied, and what is waiting for the
repository to become public (the `delvera-ai` organisation is on GitHub Free, where several
protections are unavailable for private repositories). Last verified 2026-10-23.

## Applied

| Setting | Value | How |
|---|---|---|
| Visibility | private | `gh repo create` (owner decision: private until release) |
| Description, topics | `agents, claude-code, codex, antigravity, agent-skills, harness, self-improvement, developer-tools` | `gh repo edit --add-topic …` |
| Merge methods | squash only (title = PR title, body = PR body); merge commits and rebase off | `gh api -X PATCH repos/delvera-ai/lithify -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false …` |
| Delete head branches | on | same call, `delete_branch_on_merge=true` |
| Dependabot alerts | on | `gh api -X PUT repos/delvera-ai/lithify/vulnerability-alerts` |
| Dependabot security updates | on | `gh api -X PUT repos/delvera-ai/lithify/automated-security-fixes` |
| Dependabot version updates | GitHub Actions, weekly | `.github/dependabot.yml` |
| `pypi` environment | deployable only from tags matching `v*` | `gh api -X PUT …/environments/pypi` with `custom_branch_policies`, then `POST …/deployment-branch-policies name=v* type=tag` |
| Labels | `bug`, `enhancement`, `adapter:claude`, `adapter:codex`, `adapter:agy`, `prompts`, `safety`, `eval`, `docs`, `good first issue`, `release-blocker` | `gh label create … --force` |
| CODEOWNERS | owner on everything; prompts, gates, worktree, validate called out | `.github/CODEOWNERS` |
| Tracking issue | #6 "0.1.0 release readiness", pinned | `gh issue create`, `gh issue pin` |

## Not available while private on GitHub Free

Each of these was attempted; the API response is recorded.

| Setting | API response | Apply when public |
|---|---|---|
| `main` ruleset | `403 Upgrade to GitHub Pro or make this repository public` | `gh api -X POST repos/delvera-ai/lithify/rulesets --input .github/settings/ruleset-main.json` |
| Auto-merge | `allow_auto_merge` stays `false` | `gh api -X PATCH repos/delvera-ai/lithify -F allow_auto_merge=true` |
| Secret scanning + push protection | `422 Secret scanning is not available for this repository` | `gh api -X PATCH repos/delvera-ai/lithify --input -` with `{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}` |
| Private vulnerability reporting | `404` | `gh api -X PUT repos/delvera-ai/lithify/private-vulnerability-reporting` (SECURITY.md links to it) |
| `pypi` required reviewer | `422 … billing plan supports the required reviewers protection rule` | `gh api -X PUT repos/delvera-ai/lithify/environments/pypi --input -` with `{"reviewers":[{"type":"User","id":83458797}],"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}` |

Until the ruleset is active, the PR-only workflow is a convention, not an enforced rule: no
direct pushes to `main`, no force-pushes, squash-merge only after CI is green.

### The `main` ruleset (`.github/settings/ruleset-main.json`)

- Applies to the default branch.
- Requires a pull request (0 approvals so a sole maintainer can merge; squash only; stale
  reviews dismissed on push).
- Requires these status checks, with the branch up to date (`strict`): `plugin`,
  `test (ubuntu-latest, 3.11)`, `test (ubuntu-latest, 3.12)`, `test (ubuntu-latest, 3.13)`,
  `test (macos-latest, 3.11)`, `test (macos-latest, 3.12)`, `test (macos-latest, 3.13)`.
  These are the job names as they appear in the `ci` workflow's runs; update the list if the
  matrix changes.
- Blocks deletion and non-fast-forward pushes; requires linear history.
- Bypass: repository admin role only (actor 5, `RepositoryRole`), i.e. the owner.

## CI

- `test`: Ubuntu and macOS × Python 3.11–3.13: ruff, ruff format, mypy, pytest with coverage,
  `lithify demo`.
- `plugin`: JSON parse of every manifest, then
  `npx -y @anthropic-ai/claude-code@2.1.309 plugin validate . --profile directory --strict`.
  The root `CLAUDE.md` (contributor context from dogfooding) is removed in the job first,
  because the validator warns that a plugin-root `CLAUDE.md` is not loaded as plugin context.
  Bump the pinned Claude Code version deliberately and re-verify.

## Dogfooding

lithify runs on itself: `.lithify/` holds the canonical harness (project rules in
`guardrails.md`, a module map in `memory.md`, skills `adapter-change` and `prompt-change`),
rendered into `CLAUDE.md`, `AGENTS.md`, `.claude/skills/` and `.agents/skills/` by
`lithify sync`. Edit `.lithify/harness/`, never the rendered copies. Gates: `pytest -q`,
`ruff check . && ruff format --check .`, `mypy`. `auto_adopt = false`.

## Release (owner only)

1. Make the repository public; apply everything in the table above.
2. Configure PyPI trusted publishing for workflow `release.yml`, environment `pypi`.
3. Bump the version in `pyproject.toml`, `plugin.json`, `.claude-plugin/plugin.json`,
   `.codex-plugin/plugin.json` (the workflow checks they match the tag), merge, then tag `vX.Y.Z`.
