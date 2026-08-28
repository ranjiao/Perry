# Perry configuration

- Document language: 中文（chat replies mirror user; written artifacts use 中文 for narrative + EN for technical IDs）
- Repo layout: split
- State root: .
- PMO repo path: /tmp/second-project-pmo
- Code repo path: /tmp/second-project
- Available executors: claude-subagent, codex
- Conformance gate: advisory
- Last updated: 2026-05-07 (post auto-trade push)

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|-------|------|-------|--------|-----|-----|-------|--------------|
| main | project | — | — | — | — | — | V3 |
| research | pipeline | OKR.md § Commitments | intake, screen, backtest, memo | screen:2, backtest:1 | — | — | V4 |
| ops | queue | OKR.md § Commitments | — | — | 3d | — | V2 |

## Notes

- Local-only PMO repo (no GitHub remote). User is sole owner.
- Cross-reference convention: PMO docs → code via `<commit-SHA> path/to/file.py`.
- Split was triggered 2026-05-05 after ≥3 branch-contention incidents.

## codex dispatch operational rules

These are non-negotiable when invoking `codex exec`. Failing any of them caused
multi-hour stalls.

1. **CLI version**: codex CLI must be ≥ 0.128.0.
2. **`< /dev/null`** is mandatory on every `codex exec` invocation.
3. **Each parallel codex must run in its own `git worktree`**.
