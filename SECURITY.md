# Security policy

lithify runs coding agents headlessly with permission prompts disabled inside disposable git
worktrees, and runs your configured gate commands. Treat it with the same care as any tool that
executes code on your machine.

## Reporting a vulnerability

Please report vulnerabilities privately through
[GitHub security advisories](https://github.com/delvera-ai/lithify/security/advisories/new).
Do not open a public issue. We aim to acknowledge reports within three business days.

## Scope

In scope: escaping the probe worktree, prompt-injection paths that make lithify itself execute or
promote untrusted content, harness validation bypasses (e.g. credentials reaching the rendered
harness), and anything that causes lithify to commit, push or exfiltrate data.

Out of scope: behaviour of the underlying agent CLIs, and the effects of gate commands you configure.

## Hardening tips

- Tighten `[adapter_args]` (it replaces the default permission flags).
- Keep `auto_adopt = false` until you trust the loop on your repository.
- Use a `holdout_cmd` that lives outside the repository.
- Run lithify in a container or VM for untrusted repositories.
