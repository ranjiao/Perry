# TASK-489 — review round 3: V4 FAIL, architecture PASS, on 44cfbb53

Candidate: `9509170c78ef47d4c0ee907f0b71e7a2df2f2dbc..44cfbb536071a5d82d782dc01606066157661fe0`.
Two fresh-context reviewers ran, each in its own isolated worktree. Both
reported that both projects' `.git/perry` were absent before and after their
runs.

## V4 review round 3 — FAIL (TASK-489's third)

**Criteria 1–5 hold for both projects.**
- Each project's `items.jsonl` has the same sha256 as round 4's: this
  repository `a516bd22…`, SkyTonight `a8ce77e9…`.
- The reviewer ran 19 mutants, and every one was killed.
- The affected tier was green before and after: 160 modules and 4,550 tests.
  This is not a green suite.

**The FAIL.** A crafted export can still import a value the template forbids.
- The input: one event holds a field change, then a template change, then
  the item's `type` change.
- `type_of` (`commands.py:1163–1166`) checks the field against the template
  in force at that position.
- The template change's strand check (`incompatibilities`, `:381–424`) walks
  only `store.all_item_ids()`, so it never sees the untyped item's value row.
- The other five orders of the same changes are refused.
- No kernel command and not the importer writes such an event.

**Finding.** A pending `perry-task` recovery marker is ignored when the
project has no asks, because then no `perry-task` runs. On a copy of
SkyTonight with a marker, the import went ahead.

The full verdict block is in the session transcript of 2026-10-09. Its proof
line names `commands.py:1163-1166` and `:381-424` and the SkyTonight event 5
input.

## Architecture review round 4 — PASS

**Result.** No contradiction, and no user decision is needed.
- `describe` is byte-identical at base and head.
- Drift item 1 from the round-3 review is corrected in all four places.

**Non-blocking wording.** Two places name the cause of a changed project file
too firmly:
- `bin/ARCHITECTURE.md:113–117`;
- the refusal message at `bin/perry-kernel-migrate:731–737`.

They should say "most likely a pending recovery marker". One source line at
`:117` is also too long.

## Disposition

The third V4 FAIL went to the user under `review.md` § 6. The user chose
option A, which is spec § Round 6:
- a structural rule, so that no event mixes a template change with item
  changes;
- a recovery-marker check that runs before any read;
- a narrow V4 check afterwards.
