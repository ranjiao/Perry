# Perry hook — second-project

## Configuration notes

Moved out of `.perry/config.md` when ADR-019 deleted that file. These are
the prose sections a store cannot hold, in the place
`reference/config.md` has named for them since TASK-233.

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
