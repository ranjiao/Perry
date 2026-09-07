# TASK-281 — round 2 result

`DESIGN-015 § 6` row F, after the V4 FAIL. Criteria:
`perry/evidence/2026-09/TASK-281-spec.md`. Branch:
`worktree-agent-a09fb1ff425d70184`.

## Base

**Verified base: `339f553`** (*ADR-017 step 2 merged: one grammar at both
levels, and the template that undoes it*), which was `main`'s tip.

**The worktree was handed to me stale — the `TASK-381` defect, again.**
`git log --oneline -1` reported `d49964e`, a 2026-09-02 commit on an unrelated
lineage, **570 commits behind**, and `git merge-base --is-ancestor 339f553 HEAD`
was false. The branch had **no commits of its own** and the tree was clean, so I
reset onto `339f553` before reading anything. `git merge-base --is-ancestor
339f553 HEAD` passes. This is the same handoff the V4 reviewer got — it reset
off `d49964e` too — so the staleness is being reproduced per-agent, not fixed.

`16ea01d` and `c72acf1`, this row's two commits, are ancestors of my base.

Everything below is measured on `339f553` or on my own four commits descending
from it. **Every mutation restore was verified with `git diff --quiet HEAD`
against my own branch's commits, never `main`.**

## Baseline, measured twice

`tests/run` on `339f553`, before any edit, twice, cleanly:

| Run | Result | Load at start |
|---|---|---|
| 1 | **3 of 120 modules red, 4 of 3448 tests** — 107.9s | 13.18 |
| 2 | **3 of 120 modules red, 4 of 3448 tests** — 233.7s | 22.18 |

| Module | Failures | Attributed |
|---|---|---|
| `test_contract_key_parity` | 2 | `TASK-335` |
| `test_diagnose` | 1 | `TASK-380` |
| `test_linkage_import` | 1 | `TASK-383` |

Exactly the briefed set, both times. Tree guard clean at both ends of both runs.

**One baseline run was discarded, and the tree guard is why.** My first attempt
at run 2 was launched and then I edited `bin/lib/__init__.py` and
`bin/perry-task` while it was still going. It reported **6 modules / 18 tests**
red — `test_contract_invariance` (8) and `test_semantics_on_every_payload` (3)
appearing out of nowhere — and the guard named the cause exactly: *"THE SUITE
WROTE INTO THE TREE IT RAN IN — M bin/lib/__init__.py (changed)"*. I stashed and
re-ran clean. Recording it because the two phantom modules were a contract gate,
and had I trusted that run I would have spent the round on a contract change that
was not needed (see *the contract gate* below).

Timing figures above are reported with their load and no claim rests on them.

## The number, before and after

| | `P003-O3-KR2` | Population |
|---|---|---|
| **On my base, before any change** | **15.38%** — 2 of 13 | `TASK-381` … `TASK-393` |
| **After, on the same data** | **15.38%** — 2 of 13 | unchanged |

`linked_at_add = [TASK-382, TASK-383]` in both cases. **The fix does not move
today's number**, and that is the honest outcome: both live rows hold a real
`via: "add"` edge, so both survive a numerator that checks for one. What changes
is what the number does on the inputs below.

Store: 123 records — `{('unlinked','link'): 100, ('edge','link'): 15,
('kr',None): 6, ('edge','add'): 2}`.

## Defect 1 — the numerator never read `linkage.jsonl`

`bin/lib/__init__.py:765-766` admitted a row on the `add` event's word alone:

```python
if event.get("kr") is not None:
    linked.append(tid)
```

`perry-task add --kr "   "` writes a **truthy** `kr` onto the event
(`bin/perry-task:3652`, `args.kr or None`); `linkage_edge_change` strips it to
`""` and returns `None`, so **no edge is written**; and the `if not args.kr`
warning never fires, for the same truthiness.

### Before, on a `git archive` copy of `339f553`

```
$ bin/perry-task add --title "whitespace kr probe" --deliverable … \
      --verification … --summary … --kr "   " --track main --actor agent
perry-task: wrote TASK-394 (add) → tasks.jsonl + intake.jsonl + journal +
                                   BOARD.md + event        ← no linkage.jsonl

  current  15.38  (2/13)  →  21.43  (3/14)
  linked_at_add            = [TASK-382, TASK-383, TASK-394]
  perry/linkage.jsonl      = 123 records, unchanged, zero for TASK-394
  event                    = {"id":"TASK-394","kr":"   "}
  store_edge_without_event = []            ← nothing reported
```

**Typing three spaces raised the KR.** No warning, no store record, and the
writer's own success line omits `linkage.jsonl` — it knows it wrote no edge —
while the computation reports the row as one that answered in its own `add`.

### After, on the same data

```
  current  15.38  (2/13)  →  14.29  (2/14)     ← DOWN, not up
  linked_at_add                = [TASK-382, TASK-383]
  event_kr_without_store_edge  = [TASK-394]    ← named
```

The probe row is still in the **population** — its `add` event carries the
gate's `kr` key, so the gate did run on it — which is why the number must fall
rather than stay put. `WhitespaceCannotRaiseTheNumber.test_the_probe_row_is_in_
the_population` is the guard on that confound: had the row merely been dropped
from the denominator, "it is not in the numerator" would have passed while the
number was still moving on an input nobody should be able to move it with.

**And the input is now refused at the writer** (below), so the event above can
no longer be produced at all. Both belts were verified separately.

## Defect 2 — the store could not move the number

`bin/lib:740-741` required `{"kind":"unlinked","via":"add"}` for the store's
only numerator path, and no writer emits one. So the store contributed nothing.

### Before

```
$ (delete every record with via == "add" from perry/linkage.jsonl)
  123 records → 121
  current  15.38  (2/13)  →  15.38  (2/13)     ← IDENTICAL
```

Every `via: "add"` record can be deleted by `perry-tasks linkage-write --root .
--from-register`, the documented reconciliation, and the published number does
not move. The Deliverable — *"computed from `linkage.jsonl` and
`.perry/events.jsonl`"* — was not met in substance.

### After

```
  123 records → 121
  current  15.38  (2/13)  →  0.0  (0/13)
  event_kr_without_store_edge = [TASK-382, TASK-383]
```

The store is now load-bearing: removing its half takes the numerator to zero and
names both rows as half-landed.

## What the numerator is now

Half one takes **both files, and requires them to name the same KR**: the `add`
event's `kr` is non-null AND `linkage.jsonl` holds an `edge` for that row with
`via: "add"` naming that same id. § 5.3 writes the two under one `commit()`, so
*"linked in the same action"* means **the transaction landed whole** — the only
reading neither file can fake alone. A desync can now only ever **lower** the
score it exists to expose; before, one silently raised it.

Half two — `unlinked` with `via: "add"` — is left wired and is **unreachable**;
see below.

## Blank `--kr`: a refusal, and why

**Decision: `--kr ""` and `--kr "   "` are REFUSED, at
`bin/perry-task § cmd_add`, before the value is stamped onto the event.**

```
$ bin/perry-task add … --kr "   "
perry-task: refused — --kr '   ' is blank. It is not a way to say this row
serves no KR — omit `--kr` for that, which files the row and warns, or use
`perry-goals link --unlinked` to declare it outright. Passing the flag with
nothing in it would stamp a `kr` on the row's `add` event that no linkage edge
backs. Nothing was written
```

Three reasons, and the axis is the flag's **presence**:

1. **It is ambiguous in a way a default cannot resolve.** Treating it as "no KR"
   guesses at intent; treating it as an id writes a dangling edge. Omitting the
   flag is the unambiguous way to say "no KR", and it already exists.
2. **The two writers of one store must validate alike.** `perry-goals link`
   refuses a blank or unresolvable KR hard. Asymmetric validation on one store
   is how two surfaces come to disagree — the defect `DESIGN-015` exists to
   remove.
3. **Refusing costs one re-run at the only moment the mistake is cheap.** A
   warning leaves a row already filed and already in the denominator, and
   warnings on stderr are what nobody reads. `--summary` in the same function
   already refuses whitespace-only for exactly this reason, so this is the
   file's existing shape rather than a new one.

**This does not make `--kr` mandatory** — the decision `DESIGN-015 § 5.2` did
not take. Omitting it still files the row and still warns, verified end to end
and pinned by
`test_omitting_the_flag_still_files_the_row_and_warns`, which exists so that a
refusal cannot quietly turn the flag into a requirement. A **padded but real**
id is stripped, not refused, and normalised once so the event and the store
record cannot disagree about it.

**Deliberately not checked here: whether the id resolves.** `--kr NOT-A-REAL-KR`
is still accepted. That is row D's question (`TASK-279`) and out of this Bound;
what this row owed was that a value the store-writer will silently discard
cannot reach an event.

## The desync detector's new gate

The old detector was gated on the artefact whose absence it detects:

```python
disagreements = sorted(tid for tid in edge_at_add
                       if tid in seen and tid not in set(linked))
```

`seen` **is** the population, and the population is built from the `add` event.
`TASK-279`'s V4 drove the crash matrix to seven points and found this reporting
empty at two of them — the event append is `open(..., "a")`, not a canonical
rename, so the shipped harness never kills there and a crash leaves the store's
half alone in the tree.

**The new gate is the STORE — the half that survives.** The event is asked only
*"does it corroborate"*, and "there is no event" is a perfectly good no. Three
shapes, measured before and after:

| | Shape | Old | New |
|---|---|---|---|
| A | store edge, **no `add` event at all** | `[]` blind | reported |
| B | store edge, `add` event `kr: null` | reported | reported |
| C | store edge, `add` event **without the `kr` key** | `[]` blind | reported |
| — | store edge naming a **different KR** than the event | `[]` | reported |
| — | control: a matched pair | `[]` | `[]` |
| — | control: an ordinary later `via: "link"` edge | `[]` | `[]` |

Deliberately **not** track-filtered: the record carries no track, and in shape A
there is no event to read one off. A `via: "add"` edge whose event is gone is a
desync on any track, and inventing a track for it would reintroduce the guess.

A second detector, `event_kr_without_store_edge`, reports the other half-landed
direction — the one defect 1 produced.

## `unlinked`-at-add is unreachable, and the check now says so

I enumerated every writer of `perry/linkage.jsonl`. `via` is a hardcoded literal
at all three:

| Site | `via` | kinds |
|---|---|---|
| `bin/perry-task:2798` (`linkage_edge_change`) | `"add"` | **`edge` only** |
| `bin/perry-goals:1782` (`linkage_store_text`) | `"link"` | `edge`, `unlinked` |
| `bin/perry-tasks:1684`, `:1691`, `:1848` | `LINKAGE_IMPORT_VIA = "link"` (`:1429`) | `kr`, `edge`, `unlinked` |

No `--via` flag exists anywhere in `bin/`; `schema/state-schema.json:924-928`
and `:954-958` pin the field to `^(add|link)$` and **permit** the combination;
and there is no `perry-task add --unlinked` for the declaration to be made by.
**So `{"kind":"unlinked","via":"add"}` has no writer.**

**Stated, not fixed, and the reason is the Bound.** Giving `add` an `--unlinked`
flag is a new writer on this store and a change to what `add` accepts — row D's
territory. What row F owed the reader is that the gap is **named where the
number is published**, instead of a `declared_unlinked_at_add: []` that reads
like an observation about today's data when it is a fact about the code. So:

- `lib.UNLINKED_AT_ADD_HAS_NO_WRITER` carries the claim and its evidence;
- the payload carries `declared_unlinked_at_add_reachable: false`;
- the numerator's second path stays **wired**, so it counts on its own the day a
  writer appears;
- and the claim is asserted **behaviourally** — by driving `linkage_edge_change`
  and by running `perry-task add --unlinked` through the real binary — rather
  than by grepping for a literal.

**This is the correction to M13.** Round 1 read the emptiness as a property of
today's data and closed M13 against a fixture holding `unlinked(task, "add")` —
a record Perry cannot produce. `unlinked(task, "add")` appeared three times in
the repository, all hand-built in the test file. The reachability claim now
reddens the day somebody implements the flag `DESIGN-015 § 5.5` asks for, and
`test_the_fixture_can_actually_file_a_row` is the control that stops it rotting
green on a broken fixture.

**The consequence, which is upstream of this row.**
`phase/003-storage-code.md § DoD` item 5 offers a row two ways to comply — *"a
KR edge **or** an `unlinked` declaration written by its own `add`"*. The second
is unsatisfiable as shipped, so a row that honestly serves no KR cannot say so
at `add` and pins the denominator permanently: **the 100% target is unreachable
by construction.** That is a finding about the DoD and about row D's missing
lane, not a defect this row may fix.

## Readers of `current` — the field, not the prose beside it

The V4 FAIL was that round 1 verified *"nothing else reads the asserted value"*
by enumerating readers of **`metric`**. The field whose provenance changed is
**`current`**. Enumerated by call site:

### Publishers of a KR's `current`

| # | Site | Calls `computed_kr_current`? |
|---|---|---|
| 1 | `bin/perry-state:1774-1783` (`encode_linkage_objective`) | **yes** |
| 2 | `bin/perry-goals:930, 939-946` (`kr_rows` → `list --json`) | **yes** |
| 3 | `bin/perry-goals:3267` (`cmd_krs` → `krs --json`) | **NO** |
| 4 | `bin/perry-goals:3528-3543` (`list`'s terminal renderer) | prints the number, then labels it `asserted` |

**Three surfaces, two answers**, reproduced on this repo:

```
perry-goals krs  --json  → P003-O3-KR2  "current": null    (no provenance keys)
perry-goals list --json  → P003-O3-KR2  15.3846…  state "measured"
perry-state --section linkage →         15.3846…  state "measured"
```

Site 4 has no `measured` branch at `:3535-3536`, so a measured KR falls through
to the literal `"asserted"`, and `:3542-3543` prints *"no `current` here is a
measurement"* unconditionally — while `P003-O3-KR2` is measured.

**`computed_kr_current`'s docstring claim — *"Every reader that publishes a KR's
`current` calls this"* — is false as shipped, at sites 3 and 4.** Both belong to
`TASK-382`. **I did not touch `bin/perry-goals`**, per the boundary.

**My change adds no fifth publisher.** Every edit is inside
`same_action_linkage`, behind the single dispatch point, so sites 1 and 2 pick it
up unchanged and sites 3 and 4 are no worse than they were.

### Readers that do not publish it

`viewer/parsers.py:1149` (dataclass field), `:3837` (document parse), `:3949`
(store parse); `bin/perry-goals:883`, `:911` (internal), `:1054`
(`krs_without_numbers`, null test only), `:1066-1067` (staleness), `:2227` (the
`updated`-bump warning, publishes ids); `bin/perry-state:2174-2187`
(`attribution.kr_currents`, aggregate counts); `bin/perry-lint:4401` (drift,
document-vs-store, publishes only "differs"); `bin/perry-tasks:1672` (import
copies it into a `kr` record), `:1741-1743` (cross-check);
`schema/state-schema.json:875, 886`; `schema/goals-list-contract.md:107,
110-149`.

**Doc drift found, not fixed:** `schema/goals-list-contract.md:141` still says
`current_provenance.measured` is *"always `false` today"* while the payload now
emits `true`. Round 1's, and adjacent to `TASK-382`.

## The contract gate

Adding `event_kr_without_store_edge` and `declared_unlinked_at_add_reachable`
grows the payload (they reach it through `kr_progress_provenance`'s
`current_measurement`). `test_contract_invariance` and
`test_semantics_on_every_payload` both pass: the contract's own rule is that
**adding** a key is a `1.x` change and allowed, and a `semantics` entry is
required only where an existing value's **meaning** changes
(`bin/perry-goals § LIST_SEMANTICS`). Checked by running both modules against
the change rather than by reading the rule — they were the two phantom reds from
the poisoned baseline, and they are green.

## Mutation table

21 planted. Anchored by line number **with an assert on the old text at that
line** — one anchor mismatch was caught and re-measured rather than applied
blind; `__pycache__` cleared and the clock walked past the next whole second
after every write; **every restore verified with `git diff --quiet HEAD` against
my own branch's commits.**

| # | Mutation | Site | Verdict |
|---|---|---|---|
| N01 | numerator takes the `add` event's word alone again | `lib:865` | red (7) |
| N02 | any `via:add` edge counts, KR value unchecked | `lib:865` | red (1) |
| **N03** | `store_edge_without_event` re-gated on `tid in seen` | `lib:906` | **GREEN** |
| N03b | the same, after the `elif` was removed | `lib:940` | red (2) |
| N03c | the same, after the predicate was shared | `lib:945` | red (2) |
| N04 | the reverse desync stops being surfaced | `lib:890` | red (3) |
| N05 | the blank `--kr` refusal is deleted | `perry-task:3562` | red (3) |
| N06 | `--kr` is no longer stripped | `perry-task:3576` | red (1) |
| N07 | `UNLINKED_AT_ADD_HAS_NO_WRITER = False` | `lib:721` | red (1) |
| N08 | **no-op control** (`+ 0`) | `lib:948` | GREEN *by design* |
| N09 | *mis-planted — comment only, no behaviour change* | `perry-state:1781` | GREEN *(harness error)* |
| N09b | **M13 re-run** — `perry-state` stops passing the store | `perry-state:1782` | red (3) |
| N10 | population reads `.get("kr")`, not key presence | `lib:873` | red (12) |
| N11 | `unlinked` accepted with any `via` | `lib:833` | red (1) |
| N12 | empty population reports 0% | `lib:948` | red (4) |
| **N13** | the `_NO_ADD_EVENT` sentinel collapses into `None` | `lib:857` | **GREEN** |
| N14 | any `via:add` edge corroborates any claim | `lib:749` | red (1) |
| **N15** | `_corroborates`'s `claimed is None` guard deleted | `lib:747` | **GREEN** |
| N15r | the same, after the closure | `lib:747` | red (1) |
| N16 | a later `via:"link"` edge corroborates an `add` | `lib:846` | red (2) |
| N17 | a null `kr` takes the linked branch too | `lib:888` | red (3) |

**5 green, of which N08 is the deliberate no-op control** — there so a harness
reporting all-red can be told from one measuring noise — **and N09 was my own
harness error**: I planted a comment and measured nothing. It is listed rather
than dropped, because a green that proves nothing is exactly what a tally is for.

**3 real greens. All closed, none footnoted, each on a user-producible input.**

### N09b is the one that matters most

Round 1's M13 — blanking `perry-state`'s store argument — was **green against
the live repository**, because the whole numerator came from the event log and
the store contributed nothing. It reddened only against the unreachable fixture.
Under this round's numerator the same mutation reddens **three** tests, and two
of them read the **live repository**:

```
FAIL  BothReadersPublishTheOneNumber.test_the_number_matches_recomputing_it_here
FAIL  BothReadersPublishTheOneNumber.test_the_two_agree_on_the_number
FAIL  PerryStateReallyReadsTheStore.test_the_store_only_answer_reaches_the_payload
```

That is the difference between a closure that reaches production and one that
does not, and it is a consequence of the defect-1 fix rather than of a new test.

### N03 — an `elif` was doing the work

Re-gating the detector on the very event it detects came back **GREEN**, and not
because a test was missing. The detector was an `if`/`elif` pair that looked
like two cases and was one: `str(None)` and `str(sentinel)` are never KR ids, so
the `elif` already caught everything the `if` did. **A branch that cannot change
the answer is a branch no mutation can measure**, and it would have hidden the
next reader's re-gating too. Closed by collapsing both directions onto one
`_corroborates(claimed, store_krs)` predicate — the numerator asks it from the
event's side, the detector from the store's side, and they were always the same
question. Two spellings of it are how a row gets counted in the numerator **and**
reported as a desync, or neither. Re-run as N03b and N03c: red.

### N13 — dead code, in code I had just written

The `_NO_ADD_EVENT` sentinel kept three shapes apart — no `add` event, a missing
`kr` key, `kr: null`. Nothing downstream ever asked which one it was: all three
mean *"the event does not name a KR"*, which is the only thing either direction
needs. **Deleted rather than pinned**, on round 1's own precedent for M14 — a
test over a distinction that changes no answer tells the next reader it does
something. All three shapes are still reported; the reason for the deletion sits
where the sentinel was, so it is not reintroduced.

### N15 — green, and the guard was load-bearing anyway

Deleting `_corroborates`'s `claimed is None` guard was green against every test
then present. It is **not** dead code, unlike N13: `str(None)` is `"None"`, and a
user can file `perry-task add --kr "None"` — KR-existence is row D's question
and deliberately not asked here — which the store takes as
`{"kind":"edge","kr":"None","via":"add"}`. **Verified end to end against a real
store**, not reasoned about:

```
perry-task: wrote TASK-396 (add) → … + linkage.jsonl + …
{"kind":"edge","task":"TASK-396","kr":"None",…,"via":"add"}
```

Lose that row's `add` event to a crash and the absent event reads as `None`, the
store says `"None"`, and without the guard the two "match" — the detector
silently blind on precisely the row shaped to defeat it. Closed with two tests on
that input rather than by deleting the guard. N15r: red.

## Final state

- `tests/run` on `9be09b8`: **3 of 120 modules red, 4 of 3479 tests** — the same
  three modules and the same four tests as both baseline runs. Tree guard clean.
- `bin/perry-lint --root .`: **0 errors**, 29 warnings, `linkage store: 123
  record(s), 1 row(s) drifted`. **Identical at my base `339f553`** — I ran lint
  on a clean `git archive` of it to check, rather than assuming. The drifted row
  is the `test_linkage_import` / `TASK-383` seam.
- `tests/test_same_action_linkage.py`: 36 tests → **67**.
- Files changed against `339f553`: `bin/lib/__init__.py`, `bin/perry-task`,
  `tests/test_same_action_linkage.py` — **and nothing else.**

**Boundary.** `bin/perry-goals` untouched (`TASK-382` owns it). No other module
under `tests/` touched (ADR-017 step 3 owns them). No state file, no register,
no board cell, and `perry/phase/003-linkage.md`'s `updated:` not bumped — I made
no edit anywhere under `perry/` except this file.

**Isolation.** All destructive work on `git archive` copies under
`/tmp/f-r2-65226/`, outside the repository. Nothing was written to the primary
checkout at `/Users/bytedance/proj/Perry`. **No row was filed with `--kr`
against the repository under review** — every probe went into a scratch copy. No
id was written into a board cell.

## What I did not check

- **A third baseline run, and per-module re-runs of the three reds.** I have two
  clean full runs that agree exactly, plus a third that the tree guard correctly
  invalidated. Per `a-single-baseline-run-is-not-a-baseline.md` two agreeing runs
  are better than one and are still not a settled baseline; I did not re-run any
  red module alone, and I did not investigate any of the three.
- **The full suite under mutation.** N01–N17 were judged on
  `test_same_action_linkage`, plus `test_kr_progress_provenance` and
  `test_add_writes_the_edge` where the site touched them. A mutation that reddens
  my module and greens something in the other 117 would not have been seen.
- **Whether the two new payload keys reach `viewer/` or the board renderers.** I
  checked the two JSON contracts and the contract gate; I did not open the render
  surfaces.
- **`perry-goals krs` and `perry-goals list`'s terminal renderer.** I enumerated
  them, reproduced both defects, and left them alone — `TASK-382`'s. I did not
  check whether `TASK-382`'s eventual fix collides with anything here.
- **The `kr: "None"` crash shape end to end.** I produced the store record with
  the real CLI and I asserted the computation on the resulting pair, but I did not
  kill `perry-task` mid-transaction to produce the missing event for real.
- **`perry-lint` against a dangling `NOT-A-REAL-KR` edge**, which `add --kr`
  still accepts. Carried over unchecked from the V4 review.
- **The `route` bypass.** `bin/perry-state:1345` says two events create a row and
  `route`'s carries no `kr` key, so a routed row is absent from the denominator
  rather than counted against it. Latent today — `route` refuses a `project`-mode
  track — and I did not build a queue-mode `main` track to see it land.
- **The phase-004 upper bound.** Rows filed under the gate after phase 003 closes
  still join this denominator. Named by round 1, still true.
- **Concurrent-write flakiness** of the live-repo assertions. I added two more
  tests that read the live store and event log; I did not construct the race.
- **Whether the DoD's unsatisfiable half should change, or row D should gain
  `--unlinked`.** Named above; both are outside this Bound.
- **The other five KRs (`TASK-231`) and row E (`TASK-280`).** Out of Bound. I
  assert only that the other five stay uncomputed.

## Commits

- `90f216f` — the numerator reads both files; the desync detector is re-gated;
  blank `--kr` is refused; the unreachable path is named
- `a57b223` — N03's finding: one predicate for both directions
- `156aa0e` — N13's finding: the dead sentinel is deleted
- `9be09b8` — N15's closure: the null guard, on a user-producible input
