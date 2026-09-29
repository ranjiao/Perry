# TASK-488 — dispatch record, 2026-09-26

Spec: `TASK-488-spec.md`. Design: DESIGN-023 § 6 row C. Required verification: V3.
Executor: claude-subagent (background, `isolation: worktree`). Cycle time: 43 min.
Branch: `coding/task-488-work-template` at `ab457264`. Base: `4a6d1323`.
Worktree: `.claude/worktrees/agent-a40c4af0d36bb036a`.

## Pre-flight

- **Budget:** UNKNOWN. The user chose to dispatch.
- **High-stakes screen:** allow. The files in scope are
  `templates/process/perry.json`, `kernel/tests/`, the kernel architecture
  document and a new section file, three bounded root `ARCHITECTURE.md` edits,
  and `bin/ARCHITECTURE.md` NN-B3 plus § 8. None of these matches a list entry.
- **Architecture:** the round touches the § 3 copy list and the NN-1 and NN-2
  sunset wording in § 6. The user decided both texts on 2026-09-25 and
  2026-09-26.

## Result, as re-verified by the PMO

- **Commits:**
  - `4dc3a4dc` holds only the carried document work;
  - `ab457264` holds the template and its tests.
- **Paths changed** (`4a6d1323..ab457264`):
  - `M ARCHITECTURE.md`
  - `M bin/ARCHITECTURE.md`
  - `M kernel/ARCHITECTURE.md`
  - `A kernel/architecture/sections/§5-contracts.md`
  - `M kernel/tests/test_vocabulary.py`
  - `A kernel/tests/test_work_template.py`
  - `A templates/process/perry.json`

  All of these are in scope, and the worktree is clean.
- **Kernel suite:** `python3 kernel/tests/run.py` → 233 OK, 1 existing skip. The
  live store was absent before and after the run.
- **Executor's affected tier:** green over 159 modules and 4,489 tests. It
  widened to the full suite because the `§` path is quoted by
  `tests/selection.py`. This is not a green suite.
- **Template mutants:** 63, all caught. The template was restored against
  `git show HEAD`.
- **perry-lint:**
  - root: 0 errors; the file is 500/500 as perry-lint counts;
  - `bin/`: 0 errors;
  - kernel: 0 errors;
  - section file: **refused by name**, exit 2. `--architecture-module` accepts
    only `<component>/ARCHITECTURE.md`. The lint's own module checks, run from
    a scratch script, give 0 errors. This is a gap in criterion 5.

## Method rules the kernel cannot express

Under DESIGN-023 § 7 row 2 the executor stopped on each of these and did not
change the kernel.

1. **V0 through `item update`.** `item update` runs no guards, so it can store
   V0.
2. **A queue row born in its track's first stage.** This was TASK-137. It needs
   an equality or maximum test, and `entry_stage` is deliberately set to the
   second stage today.
3. **Stage vocabulary per track.** This needs a condition on two fields.
4. **WIP.** The rule counts every open row in a track's stage, with limits per
   track and stage. The kernel counts only the target state. The template
   carries the schema's mode defaults keyed by stage name as a stand-in.
5. **Cadence recurrence.** Working out `next_due` and checking the frequency
   grammar is computation, and root § 3 forbids a lane computing a number.
6. **Either-or requirements.** Two rules need one of two inputs: blocked needs
   `--on` or `--reason`, and V5 needs checked items or `--also`. The template
   requires one field for each, and the skill fills that field from the other
   input.
7. **Meaning and content checks.** These stay with the skill:
   - a summary that only repeats the title;
   - a verification that is only a rung;
   - V4 reviewer freshness;
   - FAIL proofs;
   - high-stakes classification;
   - KR linkage, which belongs to TASK-492.
8. **`route`.** Creating the task and discharging the intake row are two
   writes. They are no longer one transaction.
9. **Mode-dependent create rules.** Queue rows need `arrived`, and pipeline
   and inquiry rows need `stage_since`. Both depend on the track.
10. **Cadence has no retire step.** A terminal state `discontinued` is declared
    with no transition into it.
11. **Advisory rung rules become hard refusals.** `required` has no warn mode.
    The schema already says advisory "for one release, then a hard gate".

**Renames forced by kernel-vocabulary collisions**, to satisfy the Goal 1 grep:

| Type | Old | New |
|---|---|---|
| task | `summary` | `gist` |
| risk | text field | `concern` |
| risk | state `open` | `active` |
| ask | `needed` | `question` |
| ask | `asked` | `asked_on` |
| intake | `deferred` | `postponed` |
| (all) | `reason` | `block_reason`, `drop_reason`, `clear_reason`, `resolve_reason` |
| cadence | `retired` | `discontinued` |

## The executor's proposal on tracks and settings (criterion 4, for the user)

- **Tracks** go in the applied template. The skill composes `perry.json` with
  the project's track declarations and applies it as a new template version.
  `track` becomes an enum, and each track's default rung becomes a `when` guard
  on `done`.
  - **Why:** guards read only the item's own fields. Tracks stored as items
    would put every track rule out of reach.
  - **Deadline:** this must be decided before TASK-489 imports anything,
    because changing a field from text to enum after values are stored is
    `template_incompatible`.
- **Settings** stay in `.perry/config.jsonl` and are read by the skill.

## Other findings, outside scope

- `SKILL.md:42`'s carve-out and `templates/README.md` do not describe
  `templates/process/`, which is applied to the store rather than copied.
- `tests/test_kernel_suite.py` `COVERS` omits `templates/process/`.
- `tests/selection.py:353` quotes non-ASCII paths, which widens the tier.
- `work/reference/task-close.md:34` lists per-mode default rungs of
  V3/V5/V2/V4. The schema and ADR-020 say V2 for every mode.
