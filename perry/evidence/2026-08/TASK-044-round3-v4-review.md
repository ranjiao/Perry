# TASK-044 — round 3 V4 review

> Reviewer: fresh context, did not build any of this. Scored against
> `perry/evidence/2026-08/TASK-044-spec.md`'s five guarantees.
> Method: run it. No guarantee below is scored from reading a claim.
> Reviewed: the `feat/work-modes` working tree (head `ca5260f`), snapshotted.

## Verdict: **FAIL** — on guarantee 3, for the third round running.

**But ADR-004 stands.** See § ADR-004 verdict — the distinction between
"fails guarantee 3 today" and "proves unbuildable to guarantee 3" is the whole
point of this review, and the second is not true.

| # | Guarantee | Verdict | Basis |
|---|---|---|---|
| 1 | Dry run first, always | **PASS** | Bytes of the whole tree unchanged by `--dry-run` (sha256 per file, 509 files). 582 lines of output carrying 380 unified-diff hunk lines — a complete diff, not a count. Deterministic: two dry runs byte-identical. Dry-run hunks vs apply hunks: **identical, 380 = 380**; the only transcript differences are the header verb and the apply-only restore-point tail. |
| 2 | Nothing is lost | **PASS** | gimegime-pmo copy: 365 ids before → 380 after, **none lost**; all 15 additions are minted `SRC-*`. The tool asserts and refuses on its own — `BOARD.md` left **byte-identical** rather than guess at `半解`. Exercised on the hardest real case available, not on a board Perry wrote. |
| 3 | Recoverable | **FAIL** | Three of the five project-write sites in the apply/restore path are unguarded. One leaves a stranger's project fully migrated with the restore point **never named**. Details below. |
| 4 | The user declares | **PASS** (one caveat) | Never a side effect; goes through `bin/perry-conform declare` with `route="migrate"` — one record, per-file re-check. Refusal matches `risk-add`'s shape. Caveat = TASK-079, judged below. |
| 5 | Partial migration is a state | **PASS** | gimegime-pmo: 30 files migrated, 4 left as found, each with the finding that blocked it named. Both halves work. A pre-write failure (F2) leaves the project **valid**, which is the definition guarantee 5 asked for. |

## Baselines reproduced first

| Baseline | Stated | Measured | |
|---|---|---|---|
| Test suite | 1284 passing | **1284, OK** (210s) | ✓ |
| `perry-lint` on Perry | clean | **0 errors, 0 warnings** | ✓ |
| gimegime-pmo before | 59 errors | **59** | ✓ |
| gimegime-pmo after | 15 errors | **15** | ✓ |
| files declared | 30 | **30** | ✓ |
| PolyForge | 11, refuses in one sentence | **11**, one-sentence refusal to stderr | ✓ |

The 15 residual errors are each a fact about the project rather than about its
shape: 6 × `locked-design-has-plan`, 4 × `missing-section`, 2 × `table-columns`,
2 × `size-cap`, 1 × `bad-enum`. The spec's measurement clause is satisfied.

Restore round-trip on the gimegime-pmo copy: **every file back to its exact
before-sha**, lint back to 59, the only residue the restore point itself.

## The third crash — guarantee 3

Both previous fixes were in the right family and the wrong place. So rather
than guess a third place, I enumerated **every site in `bin/perry-migrate` that
writes to the project**, and checked each for a guard:

| # | Site | Line | Stage | Guarded? |
|---|---|---|---|---|
| 1 | `cross_file_delta` scratch mirror | 1336 | planning | ✓ round 2's `chmod` fix |
| 2 | `restore_point` → `.perry/migrate/<run>.json` | 1435–1438 | pre-write | ✗ **unguarded** |
| 3 | `write_atomic(e.path, e.after)` apply loop | 1460 | writing | ✓ round 1's `except OSError` |
| 4 | `C.declare` → `.perry/conformance.md` | 1489 | **post-write** | ✗ **unguarded** |
| 5 | `undo` via `do_restore` | 1526–1529 | recovery | ✗ **unguarded** |

Rounds 1 and 2 guarded sites 3 and 1. **Sites 2, 4 and 5 remain**, and site 4
is the one that matters.

### The axis nobody tested: a read-only *directory*, not a read-only *file*

TASK-079 already records the operative fact — *a rename needs write permission
on the **directory**, not on the target*. Every existing test drives the
read-only axis through a **file** (`test_migrate.py:1525`,
`BOARD.md.chmod(0o444)`). No test in `test_migrate.py` ever chmods a directory.
The only directory-mode test in the whole suite is `test_task_writer.py:268`,
for a different tool — so the codebase already knows this failure mode, and
`perry-migrate` is the one place that does not.

### F1 — the declaration crashes *after* every file has landed · **blocking**

`apply_plan` writes all the state files inside the round-1 `try/except`, then
calls `C.declare(...)` **outside it**. `declare` ends in
`write_atomic(project_root / ".perry/conformance.md", ...)`, whose `.tmp`
creation needs a writable `.perry/`.

Reproduced (`scen_a.py`) on a project migrated once before — so
`.perry/migrate/` exists and is writable — with `.perry/` itself at `0555`:

```
exit=1   Traceback in stderr: YES
PermissionError: [Errno 13] Permission denied: '.../.perry/conformance.md.tmp'

  BOARD.md was rewritten              : True
  restore point on disk               : ['2026-08-18-162718.json']
  restore point NAMED in output/stderr: False
  stdout                              : ''
```

That is round 1's failure mode verbatim, moved one stage downstream: a
stranger's project migrated, a restore point sitting on disk, and a raw
traceback naming neither. It additionally breaks the migration/declaration
pairing — the files end up migrated and **undeclared**, which under an
enforcing gate is the one state guarantee 5 says must not happen silently.

`.perry/` unwritable while `.perry/migrate/` is writable is not exotic: it is
any project whose `.perry/` was created by a different user or a restrictive
umask, and then migrated once.

### F2 — `restore_point` itself is unguarded · **minor**

Same condition, first-ever run (no `.perry/migrate/` yet): `PermissionError`
out of `out.parent.mkdir()`. Pre-write, so **the project is untouched and
valid** — guarantee 5 holds. But it is a traceback where a refusal belongs.

### F3 — the recovery path half-completes, and says nothing · **blocking**

`do_restore` calls `undo` unguarded. `undo` restores the state files *and*
`.perry/conformance.md` (the restore point deliberately carries it). With
`.perry/` unwritable after a successful run:

```
exit=1   Traceback in stderr: YES
PermissionError: ... '.perry/conformance.md'
  BOARD.md actually restored: True
```

`BOARD.md` is rolled back, the conformance record is **not** — so the record
now claims conformance for a file that no longer has it, which is precisely
what `restore_point`'s own docstring says it exists to prevent. Guarantee 3
requires the recovery path be *shown working*; here it half-works and reports
a traceback.

### F4 — bytes are recoverable; the *file* is not · **finding, not a blocker**

`write_atomic` and `undo` both reconstruct a file rather than preserve it. Two
measured consequences:

- **Mode is not restored.** A `0444` `BOARD.md` is migrated (as TASK-079 says),
  and after `perry-migrate restore` it comes back `0644`. Bytes back: yes.
  Read-only bit: **gone**.
- **A symlink is silently converted to a regular file.** A symlinked `BOARD.md`
  is replaced by `tmp.replace()`; the link is destroyed, the link target is
  left untouched, and `restore` brings back a regular file, never the link.
  Exit 0, no warning — and the spec says migration is *"not silent"*.

Content is never lost, so this is not a guarantee-2 failure. It is a
qualification on guarantee 3: recoverable **to the byte**, not **to the file**.
Same root cause as TASK-079 and it belongs in that row, not in a mid-fix
decision.

### F5 — plan/apply TOCTOU · **noted, not actionable**

A file edited between planning and applying is silently clobbered, and the
restore point stores the **plan-time** bytes, so a restore would not recover
the concurrent edit either. `apply` re-plans in the same process, so the window
is milliseconds. Recorded so it is a known, bounded gap.

## The TASK-079 judgement: guarantee **4**, not guarantee 3

- **Not guarantee 3.** Verified directly: the restore point carries the
  read-only file's before-bytes and `restore` puts them back exactly. Recovery
  of the *content* is intact. (The mode is not restored — F4 — but that is a
  separate, smaller claim than "not recoverable".)
- **Yes guarantee 4.** Guarantee 4 is the consent guarantee — ADR-004 § 4,
  *"never means the tool may perform it unasked."* The read-only bit is the
  strongest per-file statement a user can make that a file should not be
  written. The dry run is the artifact the user consents on, and I confirmed it
  **never mentions the mode**: no "read-only", no "mode", no "permission"
  anywhere in the output for a `0444` file it is about to rewrite. The preview
  is complete in content and silent about the one fact that would change the
  user's mind about that file.

This does **not** flip guarantee 4 to FAIL: all three of its spec checkboxes
hold, the behaviour is pinned by a test that says it is pinned on purpose, and
it is on the board as its own row. It is a known open policy question, which is
the correct place for it. Scored PASS with the caveat named.

## The smallest change that fixes the FAIL

~20 lines, no restructuring. Prototyped and measured:

1. Wrap `C.declare(...)` in `try/except OSError` →
   `Refused(rollback_message(point, P.CONFORMANCE_FILE, exc))`.
   `rollback_message` already does the right thing: rolls back, names the
   restore point unconditionally, and reports separately whether the rollback
   itself worked.
2. Wrap `restore_point(...)` in `try/except OSError` → `Refused("could not
   write the restore point … nothing was migrated — a run that cannot be undone
   is not started.")`
3. Wrap `undo(point)` in `do_restore` → `Refused("the restore stopped partway …
   re-run once the permission is fixed; the restore point is unchanged and
   re-running is safe.")`

| Scenario | Before | After |
|---|---|---|
| A · declare, `.perry/` ro | traceback, project migrated, point unnamed | **refused**, rolled back, point named |
| B · restore_point, `.perry/` ro | traceback | **refused**, project untouched |
| C · recovery path, `.perry/` ro | traceback, half-restored | **refused**, names the safe re-run |

Full suite against the prototype: **all green, exit 0** — no regression.

F4 and F5 are **not** covered by this change and should not be — they are
policy, and TASK-079 is where they belong.

Regression tests to add alongside: the mirror of
`TestAReadOnlyFileDoesNotCrashPlanning` with the chmod on the **directory**
rather than the file, asserting `"Traceback" not in stderr` and
`"perry-migrate restore" in output` for each of the three sites.

## ADR-004 verdict

ADR-004's reopening criterion is *"migration proves unbuildable to the five
guarantees"*. **It has not been met. ADR-004 stands. TASK-045 and TASK-047 are
not cancelled.**

The reasoning, explicitly:

- Guarantees 1, 2, 4 and 5 hold **on the hardest real case available** — a
  year-old project of somebody else's, 509 files, 365 ids, headings in two
  languages, and a status word Perry has no value for. 59 → 15 errors with
  nothing lost and four files honestly refused. That is not a tool struggling
  to reach its guarantees.
- Guarantee 3 fails on a **closed, enumerated** list. There are exactly five
  project-write sites; all five are listed above; three lacked a guard; a
  ~20-line change closes all three and was confirmed to do so with the suite
  still green. "Unbuildable" would mean the guarantee cannot be reached — this
  is unfinished error handling on an exhaustible surface, which is the ordinary
  condition of code before its third review.
- The recurrence is real and worth naming: three rounds, three crashes, same
  family. But the pattern across them is diagnostic rather than damning — each
  round guarded the site it had *seen* rather than the *class*. The correct
  response is the enumeration above, adopted as the standing check, not the
  reopening of ADR-004.

What would change this answer: if the guarded surface were open-ended, or if a
guarantee failed on content rather than on error handling — for instance if
losslessness could not hold on gimegime-pmo's board. It does hold, measured.

## What I ran

- `bash tests/run` on a snapshot of the working tree — 1284 passed; then again against the prototype fix — all green.
- `perry-lint` on Perry, and on both real-project snapshots before and after migration.
- `perry-migrate` dry run ×2, `apply`, and `restore` on copies of gimegime-pmo and PolyForge, with per-file sha256 trees and id sets captured at each step.
- Five scenario probes: declaration-stage crash, restore-point crash, recovery-path crash, mode/symlink preservation, and plan/apply TOCTOU.

Isolation held: one snapshot each of `~/proj/gimegime-pmo` and
`~/proj/PolyForge`, verified faithful against source with `rsync -an --delete`
(no drift), all runs against throwaway copies. `setup` was never run. No Perry
state file was written. `__pycache__` was cleared around every mutation run.

> **Filing note.** This agent is worktree-isolated and could not write to
> `/Users/bytedance/proj/Perry/perry/evidence/2026-08/`. The file lives at
> `.claude/worktrees/agent-a101807b90369f5c4/perry/evidence/2026-08/TASK-044-round3-v4-review.md`
> and needs copying into the shared checkout.
