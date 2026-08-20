# TASK-159 — the viewer and `bin/` disagree about what a project root is

> Source: `perry/evidence/2026-08/TASK-146-result.md`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: small
> Subjective verification: no
> Touches architecture: no — it makes two existing readers agree
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Measured 2026-08-21

| where | what it means by "project root" |
|---|---|
| `viewer/parsers.py § _resolve_project_root` | the directory holding `BOARD.md` — **the state root** |
| `bin/perry-viewer` | exports `PERRY_PROJECT` as **the project root** |
| `bin/perry-state --root` | expects **the project root** |

On a project whose state lives in a subdirectory — **Perry's own, `State root:
perry`** — those are different directories, and **the viewer renders an empty
snapshot when pointed where its own launcher points it.**

This is the missing inverse `viewer/parsers.py` already documents: there is no
stored inverse of `resolve_state_root`, so it walks up four levels rather than
solve it. TASK-146 hit the same wall from the other side and is now the second
thing that depends on it.

## Deliverable

The two agree. A viewer pointed at a project root renders that project's real
snapshot, whether its state sits at the root or in a subdirectory.

**Which side moves is the decision**, and it is not obvious:

- teaching the viewer to resolve a project root → state root is the same walk
  `resolve_state_root` already does, and there would then be **one** answer;
- teaching the launcher to export the state root instead makes the viewer's
  current reading correct but leaves `perry-state --root` disagreeing with both;
- **storing the inverse** — so nobody has to walk — is the answer the existing
  comment says nobody has written, and it is the one that would stop this
  recurring.

Say which you took and what the other two would have cost.

## Verification — V3

1. **Perry's own configuration.** The viewer pointed at `/Users/…/Perry` — the
   project root, which is what `bin/perry-viewer` exports — renders the real
   board, not an empty snapshot. Prove it by rendering, not by asserting on a
   helper.
2. **A project whose state IS at its root still works**, unchanged. That is the
   configuration every non-Perry project has, and it is what a fix keyed on the
   wrong side would break.
3. **Both entrances agree on a fixture with a subdirectory state root**:
   `viewer/parsers.py`'s resolution and `perry-state --root`'s land on the same
   two directories, asserted as a pair rather than one at a time.
4. **Reverting reddens the render**, per TASK-146's precedent — a resolution
   change proved only by a unit test on the resolver is not proved.
5. `python3 tests/parallel -j 4`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`, `git diff -- perry/` empty.

## Files in scope

- `viewer/parsers.py`, `bin/perry-viewer`, and `viewer/serve.py` only where the
  resolution reaches it
- focused tests and fixtures

## Out of scope

- The chain card TASK-146 landed — read it, do not change it. Its degraded-mode
  behaviour (*"no event log, so whether a linked task has moved cannot be
  evaluated"*) is **correct** and must survive.
- `schema/state-schema.json` — if storing the inverse needs a declared field,
  **stop and say so**; that is a per-task release the user gives.
- Every other viewer route.
