<p align="center"><img src="assets/icon.png" width="120" alt="lithify"></p>

<h1 align="center">lithify</h1>

<p align="center"><b>Your agent harness hardens itself as you work.</b><br>
Harness²-style Propose → Probe → Compose for Claude Code, Codex and Antigravity — with a dynamic
exploration budget that starts wide and cools to a single run once your project's harness is stable.</p>

---

Coding agents are only as good as the harness around them: the `CLAUDE.md`/`AGENTS.md` rules,
skills, helper scripts and subagents that tell a frozen model how *this* repository works. Writing
and maintaining that harness by hand is tedious, and it drifts.

**lithify** turns the harness into something the project improves from evidence. When a task runs
through lithify, candidate harness edits are tested against each other on that very task, in
disposable git worktrees, checked by your own tests first. Edits that demonstrably helped are
promoted; the reasoning behind every edit is kept in a library that guides the next one. As the
harness stops needing changes, lithify stops paying for exploration.

```
genesis  ███████  wide parallel probes, many candidate harnesses        k = max_k
build    ███      one contrastive step per task                         k = 1
cruise   █        execute once; escalate only when a gate fails         k = 0
```

## Quickstart

```bash
# 1. install the CLI (zero dependencies, Python ≥ 3.11)
uv tool install git+https://github.com/delvera-ai/lithify     # or: pipx install git+https://…

# 2. see the whole loop work, no credentials or tokens needed
lithify demo

# 3. set it up in your repository
cd your-repo
lithify init --test-cmd "npm test --silent"      # detected automatically when it can be
git add .lithify CLAUDE.md AGENTS.md .claude .agents .gitignore && git commit -m "lithify init"

# 4. run work through it
lithify run "add rate limiting to the public API"
lithify status        # stability, phase, next k, pending proposals
lithify report        # per-task cost and the stability curve
```

### Install as a plugin

The repository is simultaneously a Claude Code plugin, a Codex plugin and an Antigravity plugin.
The plugin adds skills (`lithify-run`, `lithify-init`, `lithify-status`, `lithify-adopt`,
`lithify-compact`) and, on Claude Code, a fail-open `SessionStart` hook that tells the agent the
harness's stability and any proposals awaiting review. The skills call the `lithify` CLI, so
install that first.

Codex: with codex-cli 0.163.0, plugin-bundled hooks did not run in `codex exec` (even with
`--dangerously-bypass-hook-trust`; `codex features list` reports `plugin_hooks` as removed),
while user-level hooks do. To get the session-start hint in Codex, add it to
`~/.codex/hooks.json` yourself and trust it with `/hooks`:

```json
{"hooks": {"SessionStart": [{"hooks": [{"type": "command",
  "command": "command -v lithify >/dev/null 2>&1 && lithify hook session-start || true"}]}]}}
```

| CLI | Install |
|---|---|
| Claude Code | `/plugin marketplace add delvera-ai/lithify` then `/plugin install lithify@delvera-ai` |
| Codex | `codex plugin marketplace add delvera-ai/lithify` then `codex plugin add lithify@delvera-ai` (or enable it in the plugin browser) |
| Antigravity | `agy plugin install https://github.com/delvera-ai/lithify` |

Inside any of them: *"/lithify-run add a CSV export to the reports page"*.

## How it works

lithify implements the two levels of recursion from
[Harness²](https://github.com/google-research/harness2) (Xu et al., 2026) inside a single
repository, and changes the parts that matter when you have tests and a token budget.

```
                 ┌─────────────────────── task-level recursion (one task) ───────────────────────┐
 task ──► k? ──► │ base rollouts ──► INV + DOM proposers ──► probe each ──► composers ──► probe   │
                 │      (current harness)   (edit copies)      (worktrees)    (merge)              │
                 └───────────────┬──────────────────────────────────────────────────────────────┘
                                 ▼
                    deterministic gates (tests · lint · typecheck · holdout)   ← zero tokens
                                 ▼
                    blind selector over gate-passing deliverables  ──► patch applied to your tree
                                 ▼
                 ┌──────────────── harnessing-level recursion (across tasks) ─────────────────────┐
                 │ reflector attributes every edit: helped / hurt / no effect / confounded          │
                 │ ──► library entry (EXPERIENCE.md + harness)  ──► promote `helped` components     │
                 └──────────────────────────────────────────────────────────────────────────────┘
```

1. **One canonical harness, rendered everywhere.** `.lithify/harness/` holds eight file-backed
   components (system prompt, guardrails, memory, tool guidance, skills, scripts, subagents,
   middleware). `lithify sync` renders them into a managed block in `CLAUDE.md` and `AGENTS.md`,
   into `.claude/skills/` and `.agents/skills/` (read by Claude Code, Codex and Antigravity), and
   subagents into `.claude/agents/`. Your own content outside the managed block is never touched.
2. **Scoped proposers.** Each step drafts *invariant* candidates (how the agent works: verification,
   tool use, procedure) and *domain* candidates (what a maintainer of this repo knows: invariants,
   helpers, layout). The paper's ablation found this split among the largest single contributors.
3. **Probes in isolated worktrees, outside the repo.** Claude Code reads every `CLAUDE.md` up the
   directory tree, so worktrees nested in the repo would leak the parent harness into every probe.
   lithify puts them under `~/.cache/lithify/work/`.
4. **Gates before judges.** Every rollout runs your test, lint, typecheck and optional *holdout*
   commands. Only gate-passing deliverables reach the LLM selector, and identical deliverables
   skip it entirely. Probes that edit pre-existing tests fail their gate by default.
5. **Blind selection.** The selector sees anonymised, shuffled patches and never learns which
   harness produced which. Ties on an identical deliverable prefer the unchanged harness.
6. **Evidence-gated promotion.** The reflector writes one row per edited component with a
   verdict tied to a trajectory moment. With `auto_adopt = true` only `helped` components are
   promoted; with the default `false`, everything becomes a proposal you review with
   `lithify adopt`.
7. **Dynamic k.** Stability `S = first_pass_rate × (0.7 + 0.3 × (1 − churn))` over a rolling window
   picks the exploration width. A cruise-mode failure escalates to `k = 1` on the same task (reusing
   the failed run as the base rollout); two consecutive failures re-heat to `max_k`.

### What lithify changes relative to Harness²

| | Harness² (paper) | lithify |
|---|---|---|
| Setting | open-world tasks, no verifier | software repo: tests, lint, typecheck exist |
| Exploration budget | fixed `k` per run | dynamic `k` from a stability score; `k = 0` cruise |
| Selection | LLM selector over all deliverables | deterministic gates first; LLM only among passing, distinct patches |
| When base already passes | still proposes | nothing to contrast: deliver and skip proposals |
| Harness carried across tasks | library only (each task restarts from H₀) | library **and** a live harness, promoted only on `helped` evidence |
| Oracle gaming | — | edits to pre-existing tests fail the gate; optional holdout checks |
| Executors | OpenCode, Codex | Claude Code, Codex, Antigravity — any role can be any CLI or model |
| Harness growth | future work | budget warnings and `lithify compact` janitor pass |

## A simulated run

`lithify demo` builds a fixture service whose conventions are enforced by a real check script,
then runs 14 tasks under three strategies with a scripted agent. Worktrees, gates, rendering,
validation, the library and the schedule are all real; only the model is simulated, so read the
ratios, not the absolute token counts. A new `billing` area arrives at task 9.

```
strategy   delivered 1st-pass executions role-calls  sim-tokens always-on final S
baseline        0/14     0/14         14          0     185,752       142    0.00
static         14/14    12/14         18         44     874,532       295    0.83
adaptive       14/14    12/14         22         11     635,177       295    0.83

adaptive   k per task  2 2 2 2 1 1 0 0 1 1 0 0 0 0
           S curve     ▁▂▄▅▇▇██▇▇▇▇▇▇
```

`static` (a vanilla Harness² step on every task) and `adaptive` reach the same quality, but static
pays a proposal tax on every task forever; adaptive explores harder early, cools to single runs,
re-heats for one task when the new area appears, and then cools again.

## A live run

Three sequential tasks on a small Python repo, executor `claude@claude-haiku-5-5`, editor roles on
Claude Code's default model, `max_k = 1`. A holdout script outside the repo enforced a convention
the code documents (`app/audit.py`: record every rejected input before raising) but neither the
task text nor the neighbouring functions follow.

| task | base harness | what lithify did | executions | role sessions | cost |
|---|---|---|---|---|---|
| `parse_age` | passed holdout | delivered; no exploration | 1 | 0 | $0.01 |
| `parse_email` | **failed** holdout | INV, DOM and composed harnesses all passed it; blind selector picked the composition; proposal adopted | 4 | 5 | $0.71 |
| `parse_phone` (same convention) | **passed** holdout | delivered; no exploration | 1 | 0 | $0.01 |

The DOM proposer traced the failure to the moment the agent skipped `app/audit.py` and wrote the
invariant as a sourced fact, including that existing validators are *not* a model to copy. Three
tasks is an illustration, not a benchmark — see [docs/benchmarking.md](docs/benchmarking.md).

## Configuration

`.lithify/config.toml` (written by `lithify init`, fully commented):

| key | default | meaning |
|---|---|---|
| `executor` | first CLI found | `claude`, `codex`, `agy`, or `cli@model` (e.g. `claude@claude-haiku-5-5`) |
| `test_cmd`, `lint_cmd`, `typecheck_cmd` | detected | deterministic gates run in every probe |
| `holdout_cmd` | — | checks the agents never see (e.g. a script outside the repo) |
| `max_k` | 2 | widest exploration (genesis and anomaly spikes); see `eval/RELEASE_READINESS.md` |
| `mode` | `parallel` | or `sequential` (k chained steps) |
| `auto_adopt` | `false` | promote `helped` components automatically |
| `allow_test_edits` | `false` | let probes modify tests that existed before they started |
| `skip_when_base_passes` | `true` | no proposals when every base rollout passes |
| `[roles]` | executor's CLI | which CLI/model plays `propose_inv`, `propose_dom`, `compose`, `select`, `reflect`, `compact` |
| `[schedule]` | 0.4 / 0.8 / 10 | genesis and cruise thresholds, rolling window |
| `[budget] always_on_tokens` | 2500 | warn when always-on harness text exceeds this |
| `[adapter_args]` | permission flags | per-CLI flags; **replaces** the defaults, so you can tighten them |

A cheap executor with a stronger editor is the configuration the paper used. Using a different
vendor for `select` (lithify's default when two vendors are installed) reduces self-preference
bias when judging the executor's work.

## Safety model

* Probes run headless with permission prompts disabled (Claude Code and Antigravity:
  `--dangerously-skip-permissions`; Codex: `--sandbox workspace-write`, which never prompts in
  `codex exec`) **inside disposable worktrees outside your repository**. Tighten with
  `[adapter_args]`. Gates run your own commands with your own environment.
* Isolation covers the repository, not your user-level configuration: probes still load your
  global `~/.claude/` or `~/.codex/` instructions, hooks and plugins.
* lithify applies the selected patch to your working tree and **never commits, pushes or opens PRs**.
* Role sessions are told that everything under `context/` is evidence, not instructions, and never
  to execute scripts found in candidate harnesses.
* `lithify validate` rejects harnesses with credentials, uncompilable scripts, skills without a
  trigger, or scripts that are referenced but not shipped — before any tokens are spent probing them.
* Harness changes that reach your repo are either reviewed by you (`lithify adopt`) or backed by a
  `helped` verdict (`auto_adopt`).

## Status

**Alpha (0.1).** The full loop runs on real worktrees, gates and the Claude Code, Codex and
Antigravity CLIs; the simulated demo and test suite run in CI. Known limits:

* Middleware hooks (component C8) are stored and validated but not yet rendered into CLIs.
* Antigravity's headless JSON has no tool trajectory, so proposers see less evidence when agy is
  the executor; Antigravity plugin hooks are observe-only, so the session-start hint is Claude
  Code only (Codex: user-level hook, see above).
* Untracked files are not copied into probe worktrees — commit or stage what the task needs.
* Cost scales with `k`: a `k = 1` step is up to 4 executions and 5 role sessions. Use
  `lithify run --dry-run` to see the plan before spending anything.

See [docs/architecture.md](docs/architecture.md) and
[docs/benchmarking.md](docs/benchmarking.md) for the live evaluation protocol.

## Credit

lithify implements ideas from *Harness²: Recursive Agent Harnessing for an Open World*
(Xu, Chen, CuiZhu, Dalvi Mishra, Ming, Yu, Han, Lee and Pfister, 2026;
[arXiv:2610.14224](https://arxiv.org/abs/2610.14224),
[code](https://github.com/google-research/harness2)). It contains no code from that project and
is not affiliated with Google. Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
