# OMP sandbox plugin porting workspace

This workspace contains disposable clones for the planned Pi-to-OMP ports.
No GitHub remotes for `luluthehungrycat` have been added yet.

## Upstream clones

| Local directory | Upstream | Suggested GitHub repository |
|---|---|---|
| `plugins/pi-bash-wrap` | `https://github.com/JerryAZR/pi-bash-wrap.git` | `luluthehungrycat/omp-pi-bash-wrap` |
| `plugins/pi-sandbox-oddsjam` | `https://github.com/oddsjam/pi-sandbox.git` | `luluthehungrycat/omp-pi-sandbox` |
| `plugins/pi-sandbox-carderne` | `https://github.com/carderne/pi-sandbox.git` | reference only; do not publish a fork initially |
| `plugins/pi-gondolin` | `https://github.com/pasky/pi-gondolin.git` | `luluthehungrycat/omp-pi-gondolin` |
| `plugins/pi-mono` | `https://github.com/badlogic/pi-mono.git` | reference only; do not publish a fork |

Every clone currently has only an `upstream` remote. Add an `origin` remote only after the corresponding GitHub repository exists.

## Planned order

1. Port and test the simple Bubblewrap Bash wrapper.
2. Port the richer Sandbox Runtime integration, including in-process path guards.
3. Port the Gondolin tool-routing extension.
4. Add OMP-specific adversarial tests and TUI smoke tests.
5. Package only after fail-closed behavior and compatibility are verified.

## Non-negotiable security requirements

- A missing or failed sandbox must not silently fall back to host execution.
- `eval`, user `!` commands, subagents, MCP/custom tools, and extensions must be audited separately from the built-in Bash tool.
- Tests must use disposable workspaces and a separate OMP state/profile.
- No production credentials, SSH agent, broad home mount, or Docker socket in test runs.
