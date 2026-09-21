# TASK-475 V4 review, round 3 — `perry-goals objective add` (USER-979)

Date: 2026-09-21. Reviewer: Review Agent (Claude Opus 5), fresh context. I did not write this
code or either earlier round.

Under review: the whole delivery `801cf912..80fda999`. Round 3 itself is `ccf02a04` (code and
tests) plus `0ec9892d` (result), merged at `80fda999`. The worktree was fast-forwarded to
`82893086`; `bin/`, `viewer/` and `tests/` there are identical to `80fda999`
(`git diff 80fda999 82893086 -- bin viewer tests` is empty). The USER-978/980 changes to
`bin/perry-goals`' phase verbs are in the range. I judged them only where they touch
`objective add` or `kr add`: both now reach the pointer through `current_phase` →
`phase_pointer` → `parsers.read_phase_pointer`.

**Criteria.** The task record has no Deliverable or Verification text. Rounds 1 and 2
reviewed against the TASK-475 entry in `perry/journal/2026-09/2026-09-21.md` (§ New tasks
added), and so did I. USER-979 adds its own scope: compare phase numbers in three places,
with one test each. The three places are `objective add`'s reused-id check, `kr add`'s
objective lookup and `kr add`'s per-objective KR cap.

**Method.** All probes and mutations ran on a `git archive 80fda999` copy in the
`perry-scratch-derivation` directory, outside the repository. I ran no write-side Perry tool
against this repository's `perry/`.

## The three USER-979 sites — hold

At `80fda999`, all three sites compare `P.linkage_phase_number(r.get("phase"))` with the
current phase's number:

- `bin/perry-goals:4190`, the objective lookup;
- `:4253`, the cap;
- `:4423`, the reused-id check.

I checked the rename route from round 2 end to end. The phase is planned with O1 and one KR.
Then the document is renamed to `<NNN>-renamed.md` and `CURRENT` is repointed.

- `objective add O1` is refused and writes nothing.
- `kr add P<NNN>-O1-KR2 --objective O1` succeeds. `krs` lists O1 with both KRs, once.
- `objective add O2` writes a record under the new slug. `krs` then lists O1 and O2 together.

I also pre-seeded O1 under the other spellings of the same number that round 2 used:
`<NNN>-other`, `<NNN>-fresh ` (trailing space), `<NNN>-FRESH` and `<NNN>-renamed`. Each one is
refused, and the store and the event log are unchanged. When four active KRs are filed under
`<NNN>-other`, a fifth `kr add` is refused by the cap.

**Round 1's F1 input still refuses.** I appended a conflict marker to a store whose phase
declares O1. `objective add O1` and `objective add O2` both exit 1 with the
"cannot be read as JSONL" refusal and write nothing. `kr add` also writes nothing: its
records are read as empty, so it refuses with "it has none". **Round 2's F2 input still
refuses**: O1 seeded under `<NNN>-other` is refused.

## The category, enumerated

I searched for every place that selects linkage records by comparing their `phase` field.
Commands: `grep -n 'get("phase")\|linkage_phase_number\|linkage_records_for_phase\|load_linkage('`
over `bin/perry-goals`, and a search over `bin/` and `viewer/` for every tool that names the
linkage store.

| site @80fda999 | how it selects | agrees with the readers? |
|---|---|---|
| `perry-goals:4190` `kr add` objective lookup | number == number | yes. It is a superset of the reader's set; see below |
| `perry-goals:4253` `kr add` cap | number == number | same |
| `perry-goals:4423` `objective add` reuse | number == number | same |
| `perry-goals:1446-1469` the `Linkage` writer for `link`/`register` | `P.load_linkage(number)`, which is the reader. It refuses a slug with no number | it is the reader |
| `perry-goals:2915-2952` `krs` | `phase_number_to_read` → `P.load_linkage` | it is the reader |
| `perry-goals:3499-3531` `resolve_kr_for_writer` (check, measure, restate, withdraw) | KR id across the whole store; the phase is *taken from* the record, not compared | no phase comparison |
| `perry-goals:3552-3557` `refuse_closed_kr` | opens `phase/<record's slug>.md` | a lookup by slug, not a selection; see Observations |
| `perry-task:2911-2918`, `:2930-2938` the `unlinked` writer | `startswith(f"{number}-")` | yes, the reader's own rule |
| `viewer/parsers.py:4458-4495` `linkage_records_for_phase` | `startswith(f"{number}-")` | this is the reader |

No other writer of `linkage.jsonl` selects by phase. `perry-lint:1382` and `:4963` collect
the distinct `phase` values and select nothing.

**Where the writers and the reader still differ.** The reader places a record by
`str(phase).startswith("<NNN>-")`. The writers use `linkage_phase_number`, which strips
whitespace first and then accepts `^\d{3}\b`. So the writers' set contains the reader's set,
and it also contains `phase` values the reader does not place: `<NNN>` alone,
` <NNN>-slug` (leading space), `<NNN>.slug` and `<NNN> slug`. I seeded each one by hand:

- `objective add O1` is refused because of an O1 that `krs` does not show. Nothing is written.
- the cap refuses a fifth KR when the four existing KRs are filed under bare `<NNN>`. Nothing is written.
- `kr add` accepts an objective whose only record is under bare `<NNN>`. The new KR is written
  under the proper slug, and `krs` renders it under that objective.

None of these writes a duplicate or adds to a published count. All of them need a hand-made
`phase` value that no Perry writer produces. The reverse gap, where the reader places a
record that a writer misses, cannot happen here: any value that starts with `<NNN>-` has the
number `<NNN>`.

## Does `'' == ''` let a bad record count?

**Not when the current phase has a number.** On `<NNN>-fresh`, I seeded O1 with its `phase`
absent, `""`, `null`, `"junk"`, `5` and `["<NNN>-x"]`. Each time `objective add O1` wrote O1,
and the readers ignore the malformed record.

**Yes, when `phase/CURRENT` itself names no number**, for example a hand-written `draft`. Then
`number == ""`, and every objective record whose `phase` has no number counts as this
phase's: absent, `""`, `null`, `"junk"` or `"draft"`. `objective add O1` is then refused.
That is a false refusal, and it writes nothing. `kr add` never reaches `'' == ''`: its
`P<NNN>-` id check refuses first ("names phase <NNN>, and the current phase is draft").

The same input shows a neighbour that does not depend on `'' == ''` and predates round 3.
With a `CURRENT` of `draft`, `<NNN>` or `<NNN>.fresh`, `objective add O2` **exits 0** and
appends `{"phase": "<that value>"}` and an event, and no reader places that record.
`perry-state` reports the phase with `kr_total: 0`, and `perry-lint` adds only the record
count. `kr add` does the same under a bare `<NNN>` or `<NNN>.fresh` pointer. The `link`
writer refuses the numberless case ("does not name a phase"), and `objective add` does not.

I do not charge this as a FAIL:

- The input is a `CURRENT` outside the pointer grammar. `phase new` writes only
  `<NNN>-<slug>`, and `phases.md` step 7 prescribes `(none)`.
- Nothing is duplicated or double-counted. The next step shows the user that something is
  wrong: `kr add` refuses under `draft`, and under `<NNN>` `krs` says the phase declares no
  key result.
- The same gap exists in `kr add` and predates this row. That makes it a category for its
  own row, not a fourth round of this one: every linkage writer should refuse, or normalise, a
  current phase slug that `linkage_records_for_phase` would not place. This round does not
  file that row.

## Mutation — every round-3 comparison, plus F1's and the reuse guard

Method for each mutant:

- anchored by line number, with the anchor text asserted before the edit;
- `__pycache__` purged, and more than 1 s waited on each side of the write;
- 6 modules run on the copy: `test_goals_objective_add`, `test_goals_kr_writer`,
  `test_goals_kr_revisions`, `test_okr_store_is_the_source`, `test_actor_required` and
  `test_a_write_refuses_where_nothing_is_installed`, 161 tests;
- restored and compared byte for byte against `git show 80fda999:bin/perry-goals`, taken from
  the live worktree, not from a snapshot.

The six modules were green before the loop and green after it.

| mutant (`bin/perry-goals` @80fda999) | result | red tests |
|---|---|---|
| M1 `:4423` back to exact slug | red | `test_objective_add_refuses_an_id_filed_under_the_old_slug` |
| M2 `:4190` back to exact slug | red | `test_kr_add_finds_the_objective_filed_under_the_old_slug`, and the cap test |
| M3 `:4253` back to exact slug | red | `test_the_kr_cap_counts_krs_filed_under_the_old_slug` |
| M4 `:4423` phase condition dropped | red | 7, including `test_the_same_id_in_another_phase_is_not_a_reuse` |
| M5 `:4190` phase condition dropped | red | `test_objective_then_kr_on_a_phase_with_none` |
| M6 `:4253` phase condition dropped | red | `test_add_beyond_the_cap_counts_active_krs_only`, and the cap test |
| M7 `:4420` current number blanked | red | `test_an_id_the_phase_already_declares`, and the rename test |
| M8 `:4250` current number blanked | red | the same two cap tests as M6 |
| M9 `:4407` F1 unreadable-store guard deleted | red | `test_an_unreadable_store` |
| M10 `:4424` reuse refusal deleted | red | `test_an_id_the_phase_already_declares`, and the rename test |

**10 of 10 red.** Each USER-979 test goes red under the mutant of its own site: M1, M2 and M3
each hit the test written for that site.

## Test tier

`bash tests/run --tier affected --base 801cf912` on the worktree at `82893086` selected 162 of
162 modules. The range touches `viewer/parsers.py`, which selects everything. 4 slow-tier
modules were held back. 158 modules and 4459 tests passed: green for affected, which is not a
green suite. The count matches the PMO's full run. The author's result reports a full-suite
count and does not include a tier selection block.

## Observations (not FAILs)

- **The numberless or unplaceable `CURRENT` write gap** above. It is shared by
  `objective add` and `kr add`, and it predates round 3. It is a candidate row.
- `refuse_closed_kr` (`:3552-3557`) finds a KR's phase document by the slug stored on the KR
  record. After a hand rename of a **scored** phase, `phase/<old slug>.md` does not exist, so
  `check` and `measure` would not see "scored". Not probed. It predates this row and is outside
  `objective add` and `kr add`.
- The result's "Listed boundary paths: false … none of `viewer/parsers.py`" is true of round
  3's own commit, not of the whole range. USER-978/980 changed `viewer/parsers.py` in the
  range. That is a documentation matter (review.md § 2), not judged here.

## Not checked

- The slow tier, and the full suite beyond the 158 modules that affected selected.
- The viewer front end beyond `krs` and `perry-state --json`.
- Locking and concurrency.
- The USER-978/980 phase verbs, except as `current_phase` feeds `objective add` and `kr add`.
- `refuse_closed_kr` after a rename, which was not run.
- Round 1's M1–M13 and round 2's R5 were not re-run on this base. M9 and M10 cover F1's guard
  and the reuse guard.
- Windows paths and SkyTonight.

=== VERDICT ===
task: TASK-475
rung: V4
result: PASS
criteria: perry/journal/2026-09/2026-09-21.md
checked: on a git-archive copy of 80fda999: USER-979's three sites (:4190, :4253, :4423) compare phase numbers; rename route end to end (objective add refused, kr add finds O1, cap counts renamed KRs, krs lists O1 once); 4 same-number spellings refused with store and log unchanged; F1 input (conflict marker) and F2 input still refuse and write nothing; category enumerated over perry-goals, perry-task and parsers (9 sites, all number-based or the reader); writer set is a superset of the reader's (bare/leading-space/dotted phase values give false refusals only, never a duplicate); '' == '' reachable only under a numberless CURRENT, false refusal only; 10/10 mutants red, each USER-979 test red under its own site's mutant, restores compared to git show; affected tier 158/4459 green on 82893086
not-checked: slow tier; viewer UI; locking; USER-978/980 phase verbs beyond current_phase; refuse_closed_kr after a rename, by run; round-1 M1-M13 and round-2 R5 on this base; Windows; SkyTonight
proof: bin/perry-goals:4190, :4253 and :4423 @80fda999 select by P.linkage_phase_number on both sides; with O1 seeded under <NNN>-other and CURRENT at <NNN>-fresh, objective add O1 exits 1 and moves no byte of linkage.jsonl or events.jsonl, and M1/M2/M3 each turn their own USER-979 test red
=== END VERDICT ===
