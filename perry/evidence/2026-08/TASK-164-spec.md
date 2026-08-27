# TASK-164 spec — the state root is assigned to a global that means the project root

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: small
> Verified live 2026-08-28.

## The measurement

`bin/perry-state:1998-2002`:

```python
root = P.resolve_state_root(project_root)   # the STATE root
# parsers.py resolves PROJECT_ROOT at import time from cwd; override it so
# --root works regardless of where the script was invoked from.
P.PROJECT_ROOT = root                        # ...into the PROJECT root global
```

`viewer/parsers.py:347` defines that global as the **project** root, and its own
comment says when the lie is invisible:

> The same directory as `PROJECT_ROOT` on every project that has not moved its
> state, **which is every project but Perry's own.**

On this repository they differ:

```
_resolve_project_root()  ->  /Users/bytedance/proj/Perry
resolve_state_root()     ->  /Users/bytedance/proj/Perry/perry
```

**This is a live hazard, not only a naming lie.** After the assignment, any
`parsers.py` code that reads `PROJECT_ROOT` to find a *project-root-anchored*
file looks in the state root:

```
.perry/ exists at the project root ->  True
.perry/ exists under the state root ->  False
```

## They have already been bitten by it once

Fifteen lines below the assignment, in the same function:

> `project_root`, **NOT** `root`: `.perry/` is anchored at the project root even
> when state lives in a subdirectory … **Handing this the state root silently
> returned zero fragments and a clean `unarmed`** — a gate reporting that it has
> nothing to check.

That is this defect, found once, and **fixed at one call site rather than at the
global.** Every other reader of `PROJECT_ROOT` after the assignment is still
exposed.

## The scope

Make the global mean what its name says, or give the two roots two names.

**Before choosing, enumerate every reader of `parsers.PROJECT_ROOT`** and say,
for each, which root it actually wants. That list is the deliverable — the fix
is small and the audit is not. Some readers genuinely want the state root, which
is why the assignment was written; the question is which.

**The `--root` requirement that motivated the assignment is real** and must
survive: `perry-state --root <anywhere>` has to work regardless of the cwd the
script was invoked from. A fix that breaks `--root` has traded a silent wrong
answer for a loud one.

## Verification

1. The enumeration: every reader of `PROJECT_ROOT`, and which root each wants.
2. `perry-state --root <path>` still works from an unrelated cwd — prove it from
   `/tmp`.
3. **A project-root-anchored file is found when state lives in a subdirectory.**
   `.perry/hook.md` is the case that has already failed once; assert it directly
   rather than through a gate's verdict.
4. Mutation: restoring the assignment reddens a test that names the confusion —
   not merely "something broke".
5. `perry-state --json` on this repository is **unchanged** except for anything
   your enumeration says was wrong. List every difference.
6. `perry-lint --root .` — 0 errors.

## Out of scope

- **Renaming `viewer/`.** It stopped being a viewer tonight and that is filed
  separately; it touches 44 files' imports.
- Do not touch `schema/state-schema.json` or `perry/`. `git diff -- perry/` must
  end empty.

## Ground rules

- Branch `coding/task-164-two-roots-one-global`, commit there, **no PR, no
  push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `PYTHONNOUSERSITE=1 /usr/bin/python3` explicitly — Perry is stdlib-only and
  that flag is what proves it.
- `tests/parallel -j 4`. Verify yours is the only one with a pattern that
  **cannot match your own argv**:
  `ps -Ao pid,command | grep "python3 tests/paralle[l]"`. Write scratch files to
  a path containing your own branch name — two agents sharing a scratch filename
  overwrote each other's baselines tonight.
- Expected baseline: roughly **81 modules · ~2418 tests · 2 red** —
  `test_contract_invariance` (a union-typed key) and `test_diagnose` (two
  failures, one of them order/parallel sensitive). **Neither is yours.**
