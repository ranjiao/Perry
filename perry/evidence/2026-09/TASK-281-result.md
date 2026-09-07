# TASK-281 — result

DESIGN-015 § 6 row F. `P003-O3-KR2` is computed from `perry/linkage.jsonl` and
`.perry/events.jsonl` instead of read as prose out of the register.

## Base

**Verified base: `6551d00`** (`The data-loss hazard is closed on main, and the
acceptance test was mine to break`), which was `main`'s tip when this row
started.

**The worktree was handed to me stale, as `TASK-381` predicts.** `git log
--oneline -1` reported `d49964e` — a 2026-09-02 commit on an unrelated lineage,
shared with the `task-304` worktree — and `git merge-base --is-ancestor 6551d00
HEAD` was false. The branch had no commits of its own and the tree was clean, so
I reset onto `6551d00` before reading anything. Everything below was measured on
that base or on my own commits descending from it.

The three dependencies were confirmed present on it, not assumed:

| Dependency | Verdict |
|---|---|
| `bin/perry-lint --root .` | `linkage store: 121 record(s), 0 row(s) drifted` — a real verdict |
| `bin/perry-goals krs --root perry --phase 001` | prints **P001**'s KRs (O1-KR1..KR4, O2-KR1..KR2, O3) |
| `perry-task add --help` / `bin/perry-task` | `[--kr KR-ID]` present; `"via": "add"` at `bin/perry-task:2798` |

## Baseline, measured in this worktree

`tests/run` on `6551d00` before any edit: **1 of 118 modules red, 1 of 3378
tests failed** —
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
(`TASK-380`). Re-run alone: still red. That is the one expected pre-existing red
and no code change clears it.

One baseline artefact worth recording: the first run tripped the **tree guard**,
because I had put my scratch directory at `.scratch/` inside the worktree and the
suite's own output landed there mid-run. The guard was right and its ignore list
is pinned by `tests/test_tree_guard.py` with an explicit "do not extend this list
to make a red run green". I moved my scratch to `.claude/t281/` — already
ignored, because the harness creates `.claude` — rather than touching the guard.
No commit contains it.

Final run, on `c72acf1`: **1 of 119 modules red, 1 of 3414 tests failed** — the
same `test_diagnose` case, confirmed alone. Tree guard clean. `bin/perry-lint
--root .`: **0 errors**, `linkage store: 121 record(s), 0 row(s) drifted`.

Load was 5.7–23 across the session and never quiet; no timing claim here depends
on it except the durations entry, which records its own load.

## The number, before and after

| | Value | Where it lived |
|---|---|---|
| **Asserted, before** | `metric: "100% of rows added this phase (baseline 0 — the edge is a separate step nobody takes)"` | prose in `perry/phase/003-linkage.md` |
| **`current` field, before** | **absent** — `unasserted` | the `kr` record carries no `current`, and never did |
| **Computed, after** | **0.0% — 0 of 1** | re-run on every read from the store and the event log |

**The asserted value was never a number in a field.** `P003-O3-KR2`'s `kr`
record has no `current` (the schema's own note says so: *"Measured on this
project: `P003-O2-KR1`, `P003-O2-KR3` and `P003-O3-KR2` carry no `current`"*).
The assertion was the `metric:` prose's `baseline 0`. So "the register stops
carrying an asserted value" is a change to the prose, and there was no stale
number for another reader to pick up — which is verification 4's second half,
checked below rather than assumed.

The PMO's orientation figures reproduce exactly: **190 `add` events this phase
(all `main`-track), exactly 1 carrying a `kr` key, 0 `via: "add"` edges in the
store** (the store's 15 `edge` and 100 `unlinked` records are all `via: "link"`).

## The population decision, and why

**Decision: the population is the `main`-track rows whose own `add` event carries
a `kr` KEY, whatever that key's value. Today that is 1 row (`TASK-381`), and the
KR is 0 of 1.**

The spec's framing — *"180 rows opened since the phase started and not one
carries a `kr`"* — was written 2026-09-04, before row D landed. Taken literally
it makes the KR permanently unreachable: those rows' `add` already happened
without a gate to ask them, and no future work can give them an answer *at
`add`*. The KR would be measuring the size of a backlog rather than whether the
gate holds.

`phase/003-storage-code.md § Definition of Done` item 5, restated 2026-08-31, is
the authority and says the opposite in as many words:

> every `main`-track row opened **after the gate lands** carries a KR edge or an
> `unlinked` declaration written by its own `add`. The rows that were never asked
> before the gate are phase 004's.

So "after the gate landed" has to be decided from the data — and the gate left a
signature in it. **Row D changed the shape of the `add` event.** Before it, no
`add` event has a `kr` key; after it, every `add` writes one, `null` when the
flag was absent (DESIGN-015 § 5.2, "record and warn"). `"kr" in event` is
therefore the gate's own mark on each row it governed: per row, derived, and
needing no typed date, no commit SHA and no clock — none of which live in the two
files this KR is supposed to be computed from. Putting a date in the code would
have reintroduced the typed constant this row exists to remove.

**Both readings return 0% today.** 0/1 and 0/190. They differ only in the
denominator, so the choice changes nothing about today's number and everything
about whether tomorrow's can move. I did not have to break a tie on the value,
which is worth saying plainly: had they disagreed, that disagreement would have
been the finding.

**I do not think the DoD restatement and the spec are in conflict.** The spec's
sentence is a *measurement taken on 2026-09-04*, not a criterion; its own
"Verification 1" invites the computation to disagree with it. The criterion is
the KR title plus DoD item 5, and those are consistent with each other and with
what I built. The one thing I would not claim is that the spec's author, writing
on the 4th, had the post-gate reading in mind — they could not have.

**One boundary I chose not to paper over.** The population has no upper bound: it
is "opened under the gate", not "opened under the gate during phase 003". While
the gate and the phase coincide that is correct. When phase 004 opens, rows filed
under it will keep joining this KR's denominator unless a phase bound is added.
`same_action_linkage` is written so that bound is a parameter's worth of change,
and it is named in *what I did not check* rather than guessed at now.

## The same-action property, tested directly

This is where rounds go wrong, so the test is built to be falsifiable rather than
plausible. `TheSameActionPropertyIsWhatIsCounted` constructs two rows:

- **`TASK-901`** — linked *in* its `add`: the `add` event carries
  `kr: "P003-O1-KR1"`, and the store has `{"kind":"edge", …, "via":"add"}`.
- **`TASK-902`** — added under the gate *without* `--kr`, so its event carries
  `kr: null`, then linked an hour later by a separate `perry-goals link`, which
  writes `{"kind":"edge", …, "via":"link"}`.

`TASK-901` counts; `TASK-902` does not. The result is 1 of 2.

**`test_both_rows_are_in_the_population` is the guard on the confound, and it is
the assertion I care most about.** Both rows are in the denominator by
construction. If `TASK-902` were merely excluded from the population instead of
from the numerator, every other assertion in that class would pass while the
computation was blind to the property it is supposed to measure — a wrong PASS
that looks exactly like a right one.

`test_a_store_only_reading_would_count_them_both` states the failure mode as an
assertion rather than a comment: both rows hold an `edge` record naming the same
KR, so a computation answering from `linkage.jsonl` alone sees two linked rows
out of two and publishes **100%**. The test asserts the published number is not
100.0.

The `unlinked` half is tested the same way: declared by its own `add` counts;
the identical declaration swept in later with `via: "link"` does not. That
second case is not hypothetical — it is how all 100 `unlinked` records in the
live store were made.

## The control

`APhaseWithNoRowsOpenedHasNoDenominator`: an empty population reports
`current: None`, and the tests assert it is **neither** `0.0` (nothing linked)
**nor** `100.0` (nothing unlinked) — both are inventions out of an absence — and
that it does not divide by zero. It also asserts the provenance still reads
`measured`, not `unasserted`: *measured to have no denominator* and *nobody typed
a number* are different facts, and if the empty case reported `unasserted` this
KR would be indistinguishable from the five that are still typed.

## The register, and who reads it

`perry/phase/003-linkage.md`'s `metric:` for this one KR now states the target,
says in capitals that no current value is written there, names the function that
computes it and the two files it reads, and quotes the sentence it replaced.

Written the documented way: edit the **document**, then `bin/perry-tasks
linkage-write --root . --from-register`, then confirm the verdict. Result:
`121 linkage record(s): 6 kr + 15 edge + 100 unlinked`, `003-linkage.md is
byte-unchanged`, and `diff` against the pre-write copy shows the store is
**byte-identical** — `metric` is document-only (`derived_not_stored.metric`), so
there was nothing for the store to gain.

**`updated:` was NOT bumped (the `TASK-155` trap).** It still reads
`"2026-09-03T06:06:45Z"`. Verified by consequence rather than by intent: all
**115** `edge` and `unlinked` records still carry `declared_at` dated
**2026-09-03**, not today. Had I bumped it, all 115 would now claim a declaration
that never happened.

**Nothing else reads the old asserted value.** Checked by call site, not by name:
`metric` is read at `bin/perry-goals:917`, `:1052`, `:3266`, `:3299`,
`viewer/parsers.py:3903` and `kr_metric_cell` — every one of them treats it as a
string to display or to test for emptiness. Nothing parses a number out of it.
`bin/perry-lint:4401`'s drift comparison reads `metric` from the document on
*both* sides and so does not compare it, and it deliberately does **not** see the
computed value: the computation sits at the render seam, not inside
`linkage_from_store`, so lint still compares document to store and reports
`0 row(s) drifted`.

## Call sites, not names

`perry-state` was the file the spec scoped, but `perry-goals` publishes the same
field. Computing in one and not the other would have left the two disagreeing —
the exact defect the deliverable forbids. So the computation lives in
`bin/lib/__init__.py` (where `kr_progress_provenance` already lives, for the same
stated reason: *"a second implementation is how the two would come to disagree"*),
and `kr_progress_provenance` returns `current` for a computed KR so both callers
splice the measured value in from **one** place rather than growing an
`if kr.id == …` each. Mutations M18 and M19 disable each reader separately and
both go red, including on `test_the_two_agree_on_the_number`.

## Mutation table

23 planted. Anchored by line number with an assert on the old text at that line
(three anchor mismatches were caught and re-measured rather than applied blind);
`__pycache__` cleared and the clock walked past the next whole second after every
write; **every restore verified with `git diff --quiet HEAD`** against this
branch's own commits, never `main`.

### Round 1 — on `16ea01d`

| # | Mutation | Verdict |
|---|---|---|
| M01 | population reads `.get("kr")` instead of key presence | red |
| **M02** | at-add edge set accepts any `via` | **GREEN** |
| M03 | `unlinked` accepted with any `via` | red |
| M04 | empty population reports 0% | red |
| M05 | empty population reports 100% | red |
| M06 | `kr: null` counts as linked-at-add | red |
| M07 | `main`-track restriction dropped | red |
| M08 | duplicate `add` events double-count | red |
| M09 | half-landed transaction stops being surfaced | red |
| M10 | a second KR added to the dispatch table (the Bound) | red |
| M11 | **computed value stops replacing the register's — the spec's named mutation 5** | red |
| M12 | **no-op control** (`None or …`) | GREEN *by design* |
| **M13** | `perry-state` stops reading the store | **GREEN** |
| **M14** | `current = computed.get("current")` deleted | **GREEN** |
| **M15** | measured KR reports staleness unevaluable | **GREEN** |
| M16 | register goes back to asserting the number | red |
| M17 | every unanswered row counts as declared-unlinked | red |

**5 green, of which M12 is the deliberate no-op control** — it is there so that a
harness reporting all-red can be told from one measuring noise. **4 real greens,
all closed, none footnoted.**

### The four greens, and what each one was

**M13 is the one worth reading.** Blanking `perry-state`'s
`load_linkage_store(root)` call was green against the live repository — because
this project has **zero** `unlinked` records with `via: "add"` today, so the
store contributes nothing to the live number and the entire numerator comes from
the event log. Every live-repo assertion in my new module passed with half the
computation's inputs unplugged. That is precisely the "looks right, measures
something else" shape, and it was a hole in my own new guard. Closed with
`PerryStateReallyReadsTheStore`: a fixture project where the store's half is the
only thing that can answer — one row, `kr: null` on its `add` event, its
`unlinked` declaration made by that same `add`. Read correctly it is 1 of 1; with
the store unplugged it is 0.

**M02** let any `via` into the at-add edge set. No total moved, because that set
feeds only `store_edge_without_event` — so instead of a wrong number it turned
ordinary later linking into a false half-landed-transaction alarm. Closed by
asserting that set is empty in the two-row fixture.

**M15** flipped a measured KR's staleness to `evaluated: False`. Nothing asserted
that block at all. A recomputed number has no interval to age over, and
"could not be evaluated" invites a recheck it does not need. Closed with
`AMeasuredNumberCannotGoStale`.

**M14 was not a missing test — it was dead code, in the code I had just
written.** `current = computed.get("current")` in `kr_progress_provenance`
overwrote the register's value before `asserted = current is not None`, which
reads as "the measurement wins". It does nothing: every branch a computed KR
reaches ignores `asserted`, and the value actually reaches the payload from
`out["current"]` at the end of the function. **Deleted rather than pinned** — a
test over dead code would have told the next reader it did something. The comment
that replaced it says so.

### Round 2 — on `c72acf1`, after the closures

| # | Mutation | Verdict |
|---|---|---|
| M02r | re-run of M02 | **red** |
| M13r | re-run of M13 | **red** |
| M15r | re-run of M15 | **red** |
| M12r | no-op control again | GREEN *by design* |
| M18 | `perry-state` alone stops computing | red |
| M19 | `perry-goals` alone stops computing | red |

**Tally: 23 mutations, 6 green, of which 2 are the same intentional no-op
control. 4 real greens, all closed and all re-verified red.**

## Other things this row changed, and why

**`tests/test_kr_progress_provenance.py`** asserted that *no* KR in the live
payload claims `measured`. That was true because no tool re-ran a KR's metric —
the invariant this row deliberately ends. I **narrowed** it rather than deleted
it: the exemption is exactly `lib.COMPUTED_KR_METRICS`, so a KR claiming
`measured` while nothing re-runs its metric still fails, which is the case the
test was written to catch. Renamed to
`test_no_asserted_current_claims_to_be_a_measurement`.

**`tests/durations.json`** gained an entry for the new module — the runner
refuses an unregistered module on disk. Measured the way the file's own
convention demands: three serial runs with `__pycache__` cleared before each
(1.14 / 1.08 / 1.04s), **largest recorded**, at `load1` 5.73 rising to 5.83,
with the reason for the tight spread recorded in the source note.

## What I did not check

- **Whether the other five KRs should also be computed.** Out of scope by the
  Bound; that is `TASK-231`. I asserted only that they stay uncomputed.
- **Whether the number is *right* in the sense of being achievable.** It is 0 of
  1 because the single post-gate row was filed without `--kr`. I did **not**
  backfill it or any other row — this row measures and does not improve what it
  measures, and a round that backfilled would have made its own verification
  unfalsifiable.
- **The phase-004 upper bound.** As shipped, rows filed under the gate after
  phase 003 closes will keep joining this denominator. Correct while the gate and
  the phase coincide; wrong the day phase 004 opens. Named above, not fixed here.
- **Concurrent-write flakiness of the live-repo tests.** Four assertions read
  `.perry/events.jsonl` and `perry/linkage.jsonl` as they are. If another PMO
  session appends between `perry-state`'s read and the test's recomputation,
  `test_the_number_matches_recomputing_it_here` could flake. I judged this
  acceptable — other modules here read the live repo the same way — but I did not
  construct the race to see how narrow the window is.
- **Row E / `TASK-280`.** The document still carries its schema'd half. The
  design says E may lag.
- **`perry-lint`'s behaviour if a computed KR ever gained a `current` in the
  store.** The computation would win at the render seam and lint would still
  compare document to store, so the two would not disagree — but I did not
  construct that state and test it.
- **Whether `test_diagnose`'s red is genuinely unrelated.** I confirmed it is
  present at my base, reproduces alone, and is the `TASK-380` case named in the
  dispatch. I did not investigate it further.

## Files

- `bin/lib/__init__.py` — `COMPUTED_KR_METRICS`, `same_action_linkage`,
  `computed_kr_current`; `kr_progress_provenance` gains `computed=`
- `bin/perry-state` — passes the store records and the dispatch result
- `bin/perry-goals` — the same, at its own call site
- `perry/phase/003-linkage.md` — the `metric:` prose for `P003-O3-KR2`
- `tests/test_same_action_linkage.py` — 36 tests, new
- `tests/test_kr_progress_provenance.py` — the narrowed invariant
- `tests/durations.json` — the new module registered

## Commits

- `16ea01d` — the computation, both readers, the register
- `c72acf1` — the four green mutations closed
