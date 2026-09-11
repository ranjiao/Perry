# TASK-415 — a measured KR gets a target

Delivered 2026-09-10 on `dc88a032`, verified by the PMO before it landed.
Asked by aiMark, reading `perry-goals/list/3.0` against Perry's own project.

## The problem, in one line

`P003-O3-KR2` is the most rigorously measured row in the register — recomputed
from `linkage.jsonl` and `.perry/events.jsonl` on every read — and it is the
only row aiMark renders nothing for, because it publishes a `current` with
`target: null`. Its objective then reads as *"nobody wrote down what done would
mean"* beside a number Perry recomputes from two event logs.

## The brief was wrong about where the KR lives, and the round said so

The row's deliverable named `perry/OKR.md` and `perry/okr.jsonl`. **Phase KRs
are in neither.** TASK-157 and ADR-019 made `perry/linkage.jsonl` their single
home; `OKR.md` carries only the overall register. The target landed there.

`target` was already declared and *optional* on
`stores.declared["linkage.jsonl"].records.kr`, so `schema/state-schema.json` was
not touched and neither was `claims` — the claim surface was never approached.

## Why `target: 100` and not the count form

aiMark offered `target: 100` (current stays a percentage) or `target: 30,
current: 13` (the count form every other phase KR uses) and said it could not
pick, because picking is inferring. The PMO chose the first on a fact aiMark
could not have: **this KR's denominator is computed** — `bin/lib §
same_action_linkage` derives it as *the rows that were asked* — so it grows
every time a row is opened during phase 003. A target that moves when someone
opens a row is a denominator, not a target. The other phase KRs are counts
because their targets are *fixed* counts.

## The precision rule, which nobody asked for

`43.333333333333336` is float noise in a published payload; every consumer
rounds it differently or not at all. **One decimal place, with `0.0` and
`100.0` reserved for the exact cases**, implemented once in
`bin/lib § measured_percent`.

The reserved ends are the part worth defending: `1999/2000` is `99.95`, which
one decimal rounds to `100.0` — *every row answered*, about a phase with a row
that was not. That is not a direction (contract `2.0` removed `progress`
precisely because Perry cannot know direction); it is exactness.
`numerator`/`denominator` stay unrounded in `current_measurement`, so "is it
met" has an exact answer that does not route through `current`.

## Two rows on the contract page that had been wrong since DESIGN-015

Found while writing the new ones, and corrected: `current_provenance.measured`
was documented as **"always `false` today"** on a page whose own payload has
emitted it for months, and `.state` listed only `asserted`/`unasserted`.

## Before and after

| | before | after |
|---|---|---|
| `perry-goals list --json` | `target: null`, `current: 34.21052631578947`, contract `3.0` | `target: 100.0`, `current: 34.2`, contract `3.1` |
| `current_provenance` | `measured: true`, `asserted_at: ""` | **byte-identical** |

## Nothing was re-dated

The TASK-155 hazard. All 25 KRs diffed across `target`, `current`,
`current_provenance`, `current_staleness`, `linked_task_completion` and
`current_measurement`: **2 fields differ, both on `P003-O3-KR2`.
`current_provenance` identical on 25 of 25.** All 251 linkage records keep their
`declared_at`/`asserted_at` byte-for-byte; `.perry/events.jsonl` untouched — no
event appended; the KR record still has no `current` and no `asserted_at`,
because its number is measured rather than asserted.

## Mutation evidence

11 mutations, all red, across `tests/test_measured_krs_declare_a_target.py`
(15 tests): removing the target; stopping the rounding; dropping the `100.0`
and `0.0` clamps separately; making `same_action_linkage` divide for itself
again (which proves the payload goes through the helper);
`MEASURED_PERCENT_PLACES = 2`; an empty denominator returning `0.0`; the rule
written as `if not k["target"]`, caught by `test_a_target_of_zero_is_a_target`;
`COMPUTED_KR_METRICS` emptied, caught by the anti-vacuity guard; and watering
down the page's rule or reverting the tool's version.

## Suite

123 modules, 3,496 tests, the three declared reds, tree guard clean.
`perry-lint` 0 errors, identical to a pristine `git archive` of the base.

## Left for another row

`krs[].current_measurement` is emitted and **undocumented** on
`schema/goals-list-contract.md` — the same pre-existing gap as the
"measured is always false" line. The precision rule leans on `.numerator` and
`.denominator`, so it names them in prose, but they have no key-table rows.
Adding them risks the parity fixture's `documented_not_emitted: []`, so it needs
its own row rather than a drive-by.
