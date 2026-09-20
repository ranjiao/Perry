# TASK-474 result — the phase lifecycle writer

Date: 2026-09-20. Author: PMO Agent (Claude Opus 5), acting as the implementer.
Not reviewed: V4 is owed from a fresh reviewer. No merge to `main`, no push, no
tag, no release allocation. **No verb in this change was run against this
repository's own `perry/` state** — USER-959 authorizes isolated implementation
and explicitly does not approve live project goal writes.

## Identity

- **Base:** `8a08179063` (`main`, after TASK-474's row and spec landed).
- **Branch:** `coding/task-474-phase-lifecycle`, worktree
  `/private/tmp/perry-scratch/Perry/task-474`.
- **Head:** `ebfb2b8d`.
- **Baseline measured in this worktree before any edit:** 155 modules / 4379
  tests / green.

## What changed

`perry-goals phase new | activate | close`, routed from `main()` beside
`draft`, with its own flag table and sub-parser. Every mode runs inside one
`project_lock`, writes only through this tool's `write_atomic` (and so behind
`assert_owned`), requires a single-line `--actor`, and takes `--dry-run` and
`--json`.

- **`new`** assigns the next unused number from the phase directory's
  top-level documents, writes `phase/<NNN>-<slug>.md` from the supplied body,
  splices `Started` to today and `Status` to `active`, and writes
  `phase/CURRENT` — document first, pointer second.
- **`activate`** re-points `CURRENT` at an existing document.
- **`close`** writes `phase/snapshots/<YYYY-MM-DD>-<NNN>-<slug>-final.md`,
  flips `Status` to `scored` in place, and clears `CURRENT`. It is
  `score-phase` steps 6 and 7 as one write and computes no scores.

`current_phase` now delegates to `phase_pointer`. `DRAFT_MISSING` drops its
stale clause. `phases.md`, `planning.md`, `goals/SKILL.md` and `setup.md` now
describe what exists; all four still say the overall-OKR author is missing.

## Acceptance criteria → evidence

| AC | Evidence | Verdict |
|---|---|---|
| 1. Next number, document from the body, Started/Status stamped, CURRENT written, one operation | `test_new_assigns_the_next_number_stamps_the_header_and_activates` (M2/M11) | Met |
| 2. Refused with no overall OKR | `test_new_is_refused_without_an_overall_okr` (M1) | Met |
| 3. Refused over the tier-1 cap, cap read from the schema | `test_new_is_refused_over_the_tier_one_cap_and_names_both_numbers` (M3) | Met |
| 4. `new` and `activate` refused while another phase is active | `test_new_is_refused_while_a_phase_is_active` (M2), `test_activate_is_refused_while_another_phase_is_active` (M6) | Met |
| 5. `close` snapshots, flips in place, clears the pointer | `test_close_snapshots_flips_status_in_place_and_clears_the_pointer` (M8/M9/M12) | Met |
| 6. `--dry-run` writes nothing; `--actor` required, exit 2 | `test_dry_run_writes_nothing_in_any_mode` (M11), `test_every_mode_exits_two_without_an_actor` | Met |
| 7. Every refusal leaves the tree byte-identical, by hash | `Fixture.refused` hashes all of `phase/` before and after every refusal | Met |
| 8. The pages that declared the path unavailable now describe it | `phases.md § Writing it`, `planning.md`, `goals/SKILL.md` ×2, `setup.md` | Met |
| 9. `DRAFT_MISSING` drops the stale clause | `test_finalize_is_refused_and_changes_no_byte`, now asserting the identity as well as the count | Met |

## Mutation proof

12 mutants, `__pycache__` purged before each, the file restored and md5-verified
after each. **No survivors**, and every kill was an assertion failure rather than
an ERROR.

| Mutant | Killed by |
|---|---|
| M1 no-OKR gate removed | new-refused-without-okr |
| M2 `new` active-phase gate removed | new-refused-while-active |
| M3 tier-1 cap gate removed | cap-refusal-names-both-numbers |
| M4 slug gate removed | refused-on-a-non-slug |
| M5 scored gate removed | activate-refused-on-scored |
| M6 `activate` active gate removed | activate-refused-while-active |
| M7 `close` is-active gate removed | close-refused-on-non-active |
| M8 `close` keeps the pointer | close-clears-the-pointer, activate-refused-on-scored |
| M9 `close` skips the snapshot | close-snapshots |
| M10 numbering walks `snapshots/` | only-top-level-documents-number |
| M11 `--dry-run` writes anyway | dry-run-writes-nothing |
| M12 `close` re-renders instead of splicing | close-rewrote-a-line-other-than-Status |

**M10 survived its first run, and that was the finding.** The test planted a
real snapshot name, `2026-01-01-002-release-pipeline-final.md`. Snapshots are
written year-first, so `[0-9][0-9][0-9]-*.md` cannot match one however the
directory is walked, and making the glob recursive left the suite green — the
test proved nothing. It now plants `003-copy.md`, a name that does match, which
is what makes the non-recursive walk load-bearing. The original weak version is
recorded in the test's own docstring.

## What the suite caught, and what was done about it

Five guards refused this change before it was green. None was worked around by
editing a guard's rule or by claiming an exemption.

1. **`test_actor_required`** — a new bullet in `planning.md` read as an
   executable example and named no `--actor`. Rewritten as prose.
2. **`test_kr_progress_provenance`** — the event used
   `datetime.now().astimezone()`, deciding what a zone means, which
   `bin/lib § ts_moment` is the only place allowed to do. It also invented the
   key `"at"`; this tool's events use `"ts": lib.event_stamp()`. Both corrected.
3. **`test_goals_writer`** — asserted two missing writers. Updated to one, and
   an assertion on the remaining clause's identity was added so that retiring
   the last one cannot pass by arithmetic.
4. **`test_blank_cell_is_one_rule`** — the first draft added a **fourth** copy
   of the `phase/CURRENT` sentinel set. Its `EXEMPT` list already names the set
   as "three copies of one rule", so an exemption would have blessed the
   duplication it complains about. `current_phase` was pointed at
   `phase_pointer` instead: this tool now has one copy where it had two.
5. **`test_okr_store_is_the_source`** — six new write call sites, which that
   guard requires be read and registered rather than waved through. Registered,
   each with why it is gated and why the writes are ordered as they are.

## A guard defect found in passing, filed and not fixed

`tests/sweep_blank_cell_sites.py` keys its `bound` map by **bare variable
name across the whole module**, and treats an `Assign` whose value is a
container or `BinOp` as binding every declared blank spelling inside it —
including a hyphen that is only a separator in an f-string. So
`target = state_root / "phase" / f"{num}-{slug}.md"` bound `target` to `-`,
and because the key is the bare name, the guard then reported
`cmd_kr_add`, `link_alias` and `link_project` — three functions this row never
touched — as deciding blankness for themselves.

This change did not fix that and did not exempt around it: adding EXEMPT rows
for other people's functions would have recorded this row's noise as their
defect. The local names were changed instead (`pid` built as an f-string, which
is not a container; the local `result` renamed `payload`), which took
`bin/perry-goals` from five reported sites back to the one legitimate sentinel.

**Filed here as a finding, not opened as a row.**

## Suites

With `PERRY_PROJECT` and `PERRY_HOME` unset, in this worktree:

- Baseline before any edit, at `8a08179063`: 155 modules / 4379 tests / green.
- At `ebfb2b8d`: **156 modules / 4395 tests / 86.9s / 8 workers / all green**,
  tree guard clean.
- `git diff --check`: clean.

`tests/durations.json` lists `test_phase_lifecycle.py` as `sec: null,
source: null` — "not measured", which its schema allows. Measured figures
belong at integration, as with TASK-468 and TASK-469. The first attempt at this
entry re-sorted the whole file and produced a 44-line diff for a one-line fact;
it was reverted and inserted in place, +4 lines.

## Not claimed

- **The slow tier was not run here.** Full and slow merged verification belongs
  to integration.
- **No V4.** The author wrote both the code and its tests; the rung requires a
  fresh reviewer against the written criteria, and that is owed.
- **No live use.** Phase 004 is still active and phase 005 does not exist. This
  change builds the writer; running it against this project's own state is the
  user's decision, and phase 004 is on day 6 with 12 of 12 commit KRs unmeasured.
- **The overall-OKR authoring writer is still missing**, so
  `perry-goals draft finalize` on the `okr/first` route still refuses and
  `/perry goals init` still ends at an approved draft.

## Deviations

1. **The spec's criterion 1 was corrected before implementation, not after.**
   It first required `new` to leave `phase/CURRENT` alone, read out of
   `plan-phase`'s sentence about the chat draft. Four paragraphs later the same
   page states the writer's result must identify the activated pointer. The
   correction and its reasoning are recorded in the spec itself.
2. **A refusal was added that no written procedure asked for**: a scored phase
   cannot be reactivated. Found by running the verbs in sequence.
3. **`tests/test_blank_cell_is_one_rule.py` and
   `tests/test_okr_store_is_the_source.py` were edited by the author of the
   code they guard.** Both edits are registrations the guards demand by design
   rather than relaxations — one moves an existing EXEMPT key to the function
   that now holds the literal, the other adds six call sites with their
   rationale. A reviewer should check exactly that framing, because it is the
   shape a weakened guard would also take.
