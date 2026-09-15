# TASK-441 — result

> Spec: `evidence/2026-09/TASK-441-spec.md` · Rung: V3 · Change: tests only
> Branch: `worktree-agent-a9636397149d8c12a` · Code commits: `8e6dea40`,
> `3486e687`, `64fc2630`; this file and `tests/durations.json` first at
> `d4591de9`; then the code fix `afae3f71` (F5), and this revision

The six modules asserted against this repository's live current phase. Each now
reads **a copy of the tree with `phase/CURRENT` pinned to `003-storage-code`**
inside the copy. Each also has a control that reads a copy pinned to `(none)`
and shows the same predicate fails there. The copy is built by one new helper,
`tests/pinned_phase.py`, which is `TASK-335`'s frozen-copy shape. No fixture was
needed. Nothing under `bin/`, `viewer/` or `schema/` changed, and neither did
any contract page, fixture baseline or store in the checkout.
`perry/phase/CURRENT` in the checkout still reads `(none)`.

## 0 base check

- On arrival HEAD was `583f024f` and the tree was clean.
  `git merge-base --is-ancestor 67dada54 HEAD` exited 1.
- I ran `git merge --ff-only 67dada54` on this branch only, and re-asserted:
  exit 0. Arrived at **`67dada54`**. `perry/phase/CURRENT` read `(none)`.
- **Recount at base.** `python3 tests/parallel` on the six modules, in this
  worktree:

| module | tests | red | what failed |
|---|---|---|---|
| `test_same_action_linkage` | 76 (1 skipped) | 7 | 5 × `BothReadersPublishTheOneNumber`, 2 × `EveryPublisherOfAComputedKrAgrees` (`perry-goals krs` exited 1) |
| `test_contract_invariance` | 27 | 2 | `test_no_key_disappeared` (`perry-goals/list: phase.*`), `test_no_key_changed_type` (`phase was dict, now NoneType`) |
| `test_contract_key_parity` | 40 | 1 | `test_no_documented_key_stopped_being_emitted` (`phase.objectives` and 3 keys under it) |
| `test_kr_progress_provenance` | 29 | 1 | `test_no_asserted_current_claims_to_be_a_measurement` ("the register carries no asserted `current`") |
| `test_measured_krs_declare_a_target` | 15 | 1 | `test_at_least_one_kr_is_measured` |
| `test_phase_kr_declared_once` | 29 | 1 | `test_the_regression_case_carries_its_target_in_one_file` (`KeyError: 'objectives'`) |

  6 modules, 216 tests, **13 red**. That matches the spec's enumeration.

- **The pin alone accounts for all 13.** One probe copy with `003-storage-code`
  and one with `(none)` gave these readings through the real tools:

| reading | `003-storage-code` | `(none)` |
|---|---|---|
| `perry-goals krs --json` | exit 0, `objectives` present | exit 1 |
| `perry-goals list --json` measured KRs | `['P003-O3-KR2']` | `[]` |
| asserted `current`s | 4 | 0 |
| `phase` | object | `null` |
| `perry-state --section linkage` KRs | six `P003-*` | none |

## 1 the helper: `tests/pinned_phase.py`

- **`copy_of_perry(dest)`** copies the whole tree with `shutil.copytree`,
  leaving out `.git`, `.claude` and `__pycache__`. This is `TASK-335`'s
  function and its fidelity argument: evidence cells resolve against files
  anywhere in the tree. Measured copy time here is 0.77–1.17 s.
- **`refuse_the_checkout(root)`** raises when `root` resolves to the checkout
  or to a path inside it.
- **`pin_phase(root, phase)`** calls the guard first. It then requires
  `perry/phase/CURRENT` to exist in the copy, and requires `<phase>.md` beside
  it unless the pin is `(none)`. Only then does it write the pointer. A layout
  change therefore fails loudly and writes no stray file.
- **`pinned_copy(owner, phase)`** caches one copy per (test module, phase),
  and removes it through `unittest.addModuleCleanup`. The key includes the
  module, so a serial `discover` run cannot hand one module's removed copy to
  the next.
- **`SCORED_PHASE = "003-storage-code"`.** Every test in the six was written
  while it was current. Its `objective`/`kr` records stay in
  `perry/linkage.jsonl` after scoring, so the pin keeps working after later
  phases are planned. **`NO_PHASE = "(none)"`** is written explicitly for the
  controls. It is not read from the checkout, so a control keeps its meaning
  after `plan-phase 004`.
- **`ThePinnedCopyGuards`** is a mixin, not a `TestCase`, so it is collected
  only where a module mixes it in. Each module declares one host class. It has
  three cases:
  - the copy is not the checkout;
  - the copy's `phase/CURRENT` is `003-storage-code`;
  - the guard refuses the checkout, `perry/` and `perry/phase/`, and accepts
    the copy. This case calls only the guard, never a writer.

The tools under test are still the checkout's `bin/`. Only the `--root` they are
pointed at is the copy.

## 2 per module

Every module is **frozen copy**, not fixture. In each, the payload under test is
a projection of this repository's real register, and a fixture would have
replaced the thing the test is about (the live `P003-O3-KR2`, the real
`phase.*` shape, the real regression KR).

### `test_same_action_linkage` — 7 red at base

- **Pinned:** `project()` returns `pinned_copy(__name__, SCORED_PHASE)`.
- **Moved to the copy:**
  - `BothReadersPublishTheOneNumber`: `state_kr`, `goals_kr`,
    `test_the_other_five_krs_are_not_reported_measured`.
  - `test_the_number_matches_recomputing_it_here`: its recomputation now reads
    the copy's `linkage.jsonl` and `events.jsonl`, the files the payload was
    computed from. Read live, a concurrent write to the checkout could make
    the two disagree.
  - `EveryPublisherOfAComputedKrAgrees`: `from_state`, `from_goals_list` and
    `from_goals_krs` take an optional `root` that defaults to the copy, and
    both terminal renders read the copy.
- **Changed expectations:** none. At base,
  `test_the_footer_does_not_deny_the_row_above_it` **skipped** ("no measured
  KR"), and `test_the_terminal_renderer_says_measured_and_not_asserted` passed
  over zero rows. Both now run on a measured KR.
- **Control — `TheScoredPhaseIsLoadBearing`:**
  - In a `(none)` copy, `from_state` and `from_goals_list` return `None` for
    every id in `COMPUTED_KR_METRICS`. `from_goals_krs` refuses, which counts
    as `None`.
  - With the pin, all three publish it.
  - It calls the class's own lookups through one never-run instance, not a
    copy of them.
- **Left on the live tree, and why:**
  - `TheRegisterNoLongerAssertsIt` reads the store's `kr` record.
  - `TheStoreIsLoadBearingOnTheLiveNumber` calls `same_action_linkage` on the
    live store and log directly.
  - Neither goes through a current phase, and both are green in both states.

### `test_contract_invariance` — 2 red at base

- **Pinned:** `project()`, as above.
- **Moved to the copy:**
  - `read()` and `capture()` take `root`, and pass `--root` to all three
    commands, which ran with `cwd=ROOT` and no `--root` before.
  - Two of the three direct `perry-task list` calls also pass the copy:
    `test_a_minor_bump_carries_a_semantics_entry` and
    `test_the_live_payload_reads_the_same_reordered`. They do not read the
    phase.
  - **The third stays on the checkout:**
    `test_typed_status_alias_change_is_announced`. It reads `semantics`, which
    the tool builds from its own constants. It is also a recorded, judged
    entry in `tests/fixtures/live-state-expectations.json`. I first moved it
    too, and that made the floor's finding "gone", reddening two tests in
    `test_live_state_expectations` (F5). Re-recording that fixture baseline is
    outside this row, and the call does not need to move, so it was put back.
- **`--record`** now records from a pinned copy in a temporary directory.
  Recording the checkout between phases would have written a baseline with no
  `phase.*` paths.
- **Refactor, no expectation changed:** the loops of `test_no_key_disappeared`
  and `test_no_key_changed_type` moved verbatim into `disappeared()` and
  `retyped()`. The tests still assert `== []`.
- **Control — `TestTheScoredPhaseIsLoadBearing`:** on a `(none)` copy, the same
  two functions report the following, and **nothing outside the `phase`
  subtree** (asserted):
  - `perry-goals/list: phase.objectives` among the disappeared paths;
  - exactly `['perry-goals/list: phase was dict, now NoneType']` as retyped.

### `test_contract_key_parity` — 1 red at base

- **Pinned:** `frozen_copy()` (TASK-335) now calls
  `pinned_phase.pin_phase(root, SCORED_PHASE)` before `freeze_the_clock`. This
  is the one copy the module already built, not a second one.
- **Moved to the copy:** `TestTheTwoWayDiffIsHeldToItsBaseline.setUp` reads
  `parity.measure(frozen_copy())` instead of `parity.measure()`.
- **Changed expectations:** none. `tests/contract_key_parity.py` and the
  baseline are unchanged.
- **Guard host:** `TestThePinnedCopy` overrides `pinned_root()` to return
  `frozen_copy()`, so the guard checks the copy the module really reads.
- **Control — `TestTheScoredPhaseIsLoadBearing`:**
  - On a `(none)` copy, `compare(goals-list-contract.md)` gives a
    `documented_not_emitted` that differs from the recorded one, and
    `phase.objectives` is among the added keys.
  - On the frozen copy it equals the recorded list.
- **Left on the live tree:**
  `test_the_live_roles_page_names_no_collection_and_stays_unassigned` reads
  `roles.cards`, which does not depend on a current phase.

### `test_kr_progress_provenance` — 1 red at base

- **Pinned:** `own_project()`.
- **Moved to the copy:** `TestBothOfTodaysWrongReadingsFlip.own_repo`. Its three
  users are the failing case, `test_a_drive_to_zero_kr_is_not_reported_as_met`
  and the tally case.
- **Refactor, no expectation changed:** the list comprehension became
  `asserted_currents()`, and `assertTrue(asserted, …)` is unchanged.
- **Control — `TestTheScoredPhaseIsLoadBearing`:** `asserted_currents` is `[]`
  on a `(none)` copy and non-empty with the pin.

### `test_measured_krs_declare_a_target` — 1 red at base

- **Pinned:** `project()`.
- **Moved to the copy:** `goals_payload()` and `state_krs()` take an optional
  `root` that defaults to the copy.
- **Refactor, no expectation changed:** the comprehension in
  `test_at_least_one_kr_is_measured` became `measured_ids()`.
- **Control — `TheScoredPhaseIsLoadBearing`:** `measured_ids` is `[]` on a
  `(none)` copy and non-empty with the pin.

### `test_phase_kr_declared_once` — 1 red at base (the Bound's last element)

- **Pinned:** `own_project()`.
- **Moved to the copy:**
  `test_the_regression_case_carries_its_target_in_one_file` reads the phase
  document, the store and the `carriers` glob from the copy. It gets its KR
  rows from `declared_krs(copy, "P003-O2-KR1")`.
- **One changed failure mode, explained.**
  - **Was:** `metric["objectives"]` indexed a payload with no `objectives` and
    raised `KeyError`.
  - **Now:** `declared_krs` reads `payload.get("objectives") or []`, so the
    same state yields `[]`, and the unchanged `assertEqual(len(kr), 1, kr)`
    fails with the rows it saw.
  - **Why it is the same check:** the requirement is still exactly one
    declared row, and a payload that declares none still fails. What changes
    is that it fails as an assertion that names the rows, rather than as an
    `ERROR`. The control needs that function to return, not raise.
- **Control — `TestTheScoredPhaseIsLoadBearing`:** `declared_krs` is `[]` on a
  `(none)` copy and has length 1 with the pin.
- **Left on the live tree:**
  - `test_perry_owns_no_phase_document_with_a_kr_table` scans documents.
  - `test_every_linked_value_names_an_overall_kr_this_project_declares` reads
    the overall level and the store.
  - Neither depends on a current phase.

## 3 remainder

A scan of every other `tests/test_*.py` looked for a `perry-goals` /
`perry-state` call against the checkout, within four lines. It found one call:
`test_okr_krs_render.TestTheShippedOkr.test_every_stored_kr_reaches_the_render`.
It reads `krs --level overall --version all`, which does not depend on a
current phase. It is green with `(none)` in the final suite run (section 6).
I did not run it with a phase current. Within the six modules, the
live reads that stay are named under each module above. A text scan is not
proof; see "What I did not check".

## 4 mutation table

The harness is `scratchpad/mutate441.py 64fc2630`. For every row:

- a fresh `git archive` of `64fc2630`, which is not a git repository and in
  which `perry/phase/CURRENT` reads `(none)`, the same as main;
- every anchor is asserted to occur exactly once;
- `__pycache__` is cleared;
- the named modules (or one class) run with `python3 -m unittest tests.<m>`;
- each mutated file is restored and compared byte for byte with `git show
  64fc2630:<path>`: **equal in all 21 runs**;
- the archive's `perry/phase/CURRENT`, `perry/linkage.jsonl`,
  `perry/okr.jsonl`, `perry/tasks.jsonl` and `.perry/events.jsonl` are
  compared with the commit.

None of the six modules calls git, so `test_blank_cell_is_one_rule` and
`test_one_header_rule` do not arise here. The unmutated control run (C0) is the
separator anyway.

| # | mutation | modules run | result | red tests | stores moved |
|---|---|---|---|---|---|
| C0 | none (control) | six | **all OK**: 81 / 33 / 45 / 34 / 20 / 34 | — | none |
| M1 | `pinned_copy` builds the copy **unpinned** (helper) | six | 5 of 6 red | every original red of the five helper-pinned modules (`BothReaders…` × 5, `EveryPublisher…` × 2, `test_no_key_disappeared`, `test_no_key_changed_type`, `test_no_asserted_current_claims_to_be_a_measurement`, `test_at_least_one_kr_is_measured`, `test_the_regression_case_carries_its_target_in_one_file`), plus `test_the_copy_reads_the_scored_phase` in each of the five, and the control's pinned half in the four that have one (`test_contract_invariance`'s control has none). `test_contract_key_parity`: OK (see F1) | none |
| M2a | `test_measured_krs…`: `project()` defaults to `(none)` | 1 | failures=2 | `test_at_least_one_kr_is_measured`, `test_with_the_scored_phase_pinned_one_is` | none |
| M2b | `test_kr_progress…`: `own_project()` defaults to `(none)` | 1 | failures=2 | `test_no_asserted_current_claims_to_be_a_measurement`, `test_with_the_scored_phase_pinned_some_are` | none |
| M2c | `test_phase_kr…`: `own_project()` defaults to `(none)` | 1 | failures=2 | `test_the_regression_case_carries_its_target_in_one_file`, `test_with_the_scored_phase_pinned_it_is_declared_once` | none |
| M2d | `test_contract_invariance`: `project()` defaults to `(none)` | 1 | failures=2 | `test_no_key_disappeared`, `test_no_key_changed_type` | none |
| M2e | `test_contract_key_parity`: the `pin_phase` line removed from `frozen_copy` | 1 | failures=3 | `test_no_documented_key_stopped_being_emitted`, `test_the_copy_reads_the_scored_phase`, `test_with_the_scored_phase_pinned_the_page_matches_its_baseline` | none |
| M2f | `test_same_action_linkage`: `project()` defaults to `(none)` | 1 | failures=8 | the original 7 + `test_with_the_scored_phase_pinned_every_reader_publishes_it` | none |
| M3a | `goals_payload` reads the checkout | 1 | failures=1 | `test_at_least_one_kr_is_measured` | none |
| M3b | `own_repo` reads the checkout | 1 | failures=1 | `test_no_asserted_current_claims_to_be_a_measurement` | none |
| M3c | the regression case reads `ROOT` | 1 | failures=1 | `test_the_regression_case_carries_its_target_in_one_file` | none |
| M3d | the invariance gate reads `read(ROOT)` | 1 | failures=2 | `test_no_key_disappeared`, `test_no_key_changed_type` | none |
| M3e | the parity baseline reads `parity.measure()` | 1 | failures=1 | `test_no_documented_key_stopped_being_emitted` | none |
| M3f | `test_same_action_linkage`'s `project()` returns `PERRY_HOME` | 1 | failures=8 | the original 7 + `test_with_the_scored_phase_pinned_every_reader_publishes_it` | none |
| M3g | only `from_state`'s default root is the checkout | 1 | **OK — green** | — (see F2) | none |
| M4 | `refuse_the_checkout` never refuses | six | failures=3 in each | `test_the_pin_refuses_the_checkout` (3 subtests) in all six | none |
| M5 | `copy_of_perry` returns the checkout, guard intact | six | red in all six | `test_the_copy_is_not_the_checkout` / `test_the_pin_refuses_the_checkout` in the five helper-copy modules, and each module's `setUpClass` or tests erroring on the refusal; `test_contract_key_parity`: only its control | none |
| M4+M5 | both | six | red in all six | `test_the_pin_refuses_the_checkout` in all six; `test_the_copy_is_not_the_checkout` in the five helper-copy modules; the control's pinned half in the four modules whose half reads `pinned_copy` (`same_action`, `kr_progress`, `measured_krs`, `phase_kr`) | **none — but see F3** |
| M6 | `NO_PHASE = "003-storage-code"`: the controls read a pinned copy | six | failures=1 or 2 in each | every "with no phase current" case, and nothing else: `test_with_no_phase_current_no_reader_publishes_a_computed_kr`, `…_the_phase_paths_disappear` + `…_phase_is_retyped_to_null`, `…_a_phase_key_stops_being_emitted`, `…_no_current_is_asserted`, `…_no_kr_is_measured`, `…_the_kr_is_declared_nowhere` | none |
| M7 | M5, on one class alone (`TheRuleHoldsOnTheLivePayload`) | 1 class | errors=1 | `setUpClass` (the guard refuses) | **none**, and `CURRENT` still `(none)` |
| M8 | M4+M5, on the same class alone | 1 class | **OK**, 4 tests | — | **`perry/phase/CURRENT`**, now `003-storage-code` |

**Re-run on `afae3f71`.** That commit changed one line of
`test_contract_invariance`, and the line is in no anchor. So I re-ran every
row that runs that module or edits its file: C0, M2d, M3d, M4 and M6. The
results were identical to the table above, the restores byte-equal, and no
store moved. The other rows were not re-run: their files and modules are
unchanged between `64fc2630` and `afae3f71`.

M6 is the controls' own mutation. With `NO_PHASE` equal to the scored phase,
each control's `current_phase` check passes by construction, so every red in
that row is the control's predicate firing and not its precondition.

**Findings.**

- **F1 — M1 is green on `test_contract_key_parity`, by construction.** That
  module pins inside its own `frozen_copy()` (TASK-335's copy, extended), not
  through `pinned_copy`, so the helper's pin is not the one it depends on.
  M2e removes *its* pin, and three tests go red. So F1 is not a gap.
- **F2 — M3g is green: a publisher that silently drops a computed KR passes
  `EveryPublisherOfAComputedKrAgrees`.**
  - Under M3g, `from_state` reads the `(none)` checkout and returns `None`.
  - `test_every_computed_kr_is_published_by_at_least_one_reader` asks for
    *at least one* publisher, and `test_the_three_json_publishers_agree_on_the_number`
    compares only the publishers that returned a row. Both stay green.
  - `BothReadersPublishTheOneNumber` does not catch it either, because its
    `state_kr` builds its own argv.
  - This predates TASK-441. The same shape passes whenever one of the three
    tools stops emitting the KR. I did not change it: requiring all three
    publishers is a stronger assertion than either test states, and choosing
    it belongs to that class's owner, not to a pinning row.
  - My control's pinned half asserts all three publish, but it passes `root`
    explicitly, so it does not see a lookup whose *default* moved.
- **F3 — the store comparison cannot see a write the controls undo.**
  - In M4+M5 the harness reported no store moved, and the writes still
    happened. Each module's main copy wrote `003-storage-code` into the
    archive's `CURRENT`, then its control wrote `(none)` back. Those are the
    original bytes.
  - The red `with_the_scored_phase_pinned_*` halves in that row are the sign:
    they read `(none)` from the "copy" that was the archive.
  - M7 and M8 run one main class with no control after it. They show the
    effect directly: with the guard, nothing is written. Without it,
    `perry/phase/CURRENT` in the archive, which stands in for the checkout,
    becomes `003-storage-code` **and the class passes green**. That is exactly what the guard exists to
    prevent, and it would have left main in phase 003.
- **F4 — the "reads the checkout" mutations (M3a–M3f) are red only because main
  has no phase current.**
  - Every one of them reads the archive, where `CURRENT` is `(none)`.
  - Once `plan-phase 004` makes a phase current, pointing a module back at the
    checkout would read phase 004. Whether that reddens depends on 004's
    register, not on these tests. For example, with no computed KR in 004,
    M3a still reddens. With an asserted `current` in 004, M3b does not.
  - The guard classes check the copy the helper builds, not the root each
    payload was read from. None of these payloads is checked to have come
    from the copy.
  - This is the limit TASK-335 recorded for its M5. See "What I did not
    check".
- **F5 — my first result commit, `d4591de9`, reddened another module.**
  - `bash tests/run` on it: 140 modules, 3934 tests, 1 module red, 2 tests:
    `test_live_state_expectations.TestTheFloorIsRecordedNotAssumed.test_the_baseline_and_the_sweep_agree`
    and `…test_the_floor_is_not_claimed_to_be_zero`.
  - Both were red again when that module ran alone. The cause was mine:
    `test_contract_invariance.test_typed_status_alias_change_is_announced` is a
    judged entry in `tests/fixtures/live-state-expectations.json`, and moving
    its `perry-task list` call to the copy removed the finding from the sweep.
  - The six-module runs could not see it, and neither could the mutation
    harness, which ran only the six.
  - That call reads no phase, so it went back on the checkout (the commit
    after `d4591de9`), and the fixture baseline is unchanged. Both modules are
    green together afterwards (54 tests).

## 5 durations

Method: each module timed alone three times with `python3 tests/parallel -j 1
--times <module>`, one module per foreground command, on a `git archive` copy
of each commit, and recorded at the median of the harness's own per-module
seconds. The base modules were red, and a red module stops early.

| module | `67dada54` (base) | median | `64fc2630` (final code) | median | Δ |
|---|---|---|---|---|---|
| `test_same_action_linkage` | 4.19 / 3.61 / 3.47 (76) | 3.61 | 8.13 / 6.38 / 6.83 (81) | **6.83** | +3.22 |
| `test_contract_invariance` | 3.66 / 3.52 / 3.52 (27) | 3.52 | 7.20 / 6.89 / 6.24 (33) | **6.89** | +3.37 |
| `test_contract_key_parity` | 7.56 / 6.03 / 5.95 (40) | 6.03 | 7.86 / 7.27 / 7.64 (45) | **7.64** | +1.61 |
| `test_kr_progress_provenance` | 2.95 / 3.00 / 3.14 (29) | 3.00 | 5.71 / 5.79 / 5.87 (34) | **5.79** | +2.79 |
| `test_measured_krs_declare_a_target` | 0.55 / 0.45 / 0.46 (15) | 0.46 | 3.36 / 3.33 / 3.31 (20) | **3.33** | +2.87 |
| `test_phase_kr_declared_once` | 2.67 / 1.99 / 2.17 (29) | 2.17 | 4.49 / 4.86 / 4.83 (34) | **4.83** | +2.66 |

- **Every module moved by more than 0.5 s**, so all six are re-recorded in
  `tests/durations.json` under a new source, `2026-09-15-task441`
  (`ref` `64fc2630`, `workers` 1).
- **Why they grew:**
  - Five modules now build two whole-tree copies each: the pinned copy and
    the `(none)` copy for the control, at 0.8–1.2 s apiece. They also run the
    controls' tool calls.
  - `test_contract_key_parity` adds only the control copy, because its frozen
    copy already existed.
  - Some base figures are low partly because the red tests failed early. At
    base, `perry-goals krs` refused at once, and `setUpClass` in
    `test_measured_krs_declare_a_target` read a payload with no measured KR.
- `load1` was 11.08–20.02 across the six timing commands, so the absolute
  figures are noisy. The base and final runs of each module ran back to back
  under the same load.
- **Considered, not done:** building the pinned and `(none)` copies from one
  tree copy would save about 1 s per module. I kept them independent, as
  TASK-335's control did, so the control cannot read state left by the main
  readings.

## 6 suite on the final commit

Two runs are made on the commit that carries this file and
`tests/durations.json`:

- `bash tests/run` in the foreground, in this worktree, with the tree still
  and `perry/phase/CURRENT` reading `(none)`;
- the six modules in a `git archive` copy of that commit with
  `perry/phase/CURRENT` set to `003-storage-code`.

Their totals and the SHA are in the dispatch report. Writing them here would
create another commit, and that commit would then not be the one the suite ran
on. That is TASK-335's reason too.

- **The first such run, on `d4591de9`, was red:** 1 module and 2 tests, both in
  `test_live_state_expectations`, and caused by this row (F5). The fix is
  `afae3f71`.
- On `afae3f71`, C0 counted all six modules green with `(none)` in an archive
  copy: 81 / 33 / 45 / 34 / 20 / 34 tests, 247 in all.
- `test_live_state_expectations` and `test_contract_invariance` ran green
  together in the worktree: 54 tests.

## 7 rows named (none minted)

- `TASK-441`: this row. Not changed.
- `TASK-335`: the precedent. Cited only.

No row was opened, closed or edited, no ask or risk was filed, and no store in
the checkout was written.

## What I did not check

- **No board-independent check that a payload came from the copy (F4).**
  - The guard classes prove the helper's copy is not the checkout and has the
    scored phase. They do not prove each module's readers use it.
  - A reader pointed back at the checkout is caught today only because main
    has no phase current.
  - Asserting a root field on each payload would close it. I did not check
    whether all three tools publish one, and it is not needed for the spec's
    deliverable.
- **F2 is not fixed.** It is a pre-existing gap in
  `EveryPublisherOfAComputedKrAgrees`, found by this row's mutation and left
  to that class's owner.
- **`SCORED_PHASE` is a literal.** It is safe while `phase/003-storage-code.md`
  and phase 003's records exist. `pin_phase` refuses loudly if the document
  goes. If a later row deletes or renames phase 003's records while keeping
  the document, the six modules go red for a reason `pin_phase` does not
  name.
- **A scored phase made current again.**
  - In the copy, `phase/CURRENT` names `003-storage-code`, whose document now
    reads `> **Status**: scored` and carries only a `Started` date.
  - The tools accept that. The probe in section 0 read every expected payload,
    and all six modules are green.
  - I did not trace whether `status: scored` or the phase's age changes any
    other key. `bin/perry-goals` compares a phase date against `date.today()`
    around line 2578 (TASK-335's note). No assertion in the six modules reads
    either.
- **The remainder scan is textual.** It looked for `perry-goals` /
  `perry-state` with a checkout root within four lines. A call built through a
  helper or an `argv` variable elsewhere would be missed. Those modules are
  green with `(none)` on the final commit (section 6), so none of them depends
  on a phase being current. A module green in both states could still read the
  live phase.
- **`PERRY_HOME` override.** Three of the modules take `bin/` from `$PERRY_HOME`
  when set, while `tests/pinned_phase.py` always copies its own checkout. With
  `PERRY_HOME` pointing at another checkout, the tools and the copied project
  would come from two trees. `tests/run` does not set it. Before this row, the
  same override also chose the project read.
- **Other machines and zones.** Everything ran on this machine only (darwin,
  UTC+8).
