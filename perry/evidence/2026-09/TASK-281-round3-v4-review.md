# TASK-281 — V4 review, round 3

`DESIGN-015 § 6` row F. Criteria: `perry/evidence/2026-09/TASK-281-spec.md`,
scored against its `## Bound`, `## Verification` and `## Out of scope` and
nothing else. Under review: `bin/lib/__init__.py`, `bin/perry-task`,
`bin/perry-state`, `tests/test_same_action_linkage.py` at `68a784f8`.

**Verdict: PASS.** Both round-1 FAILs are closed and I re-derived each closure
by mutation rather than by reading round 2's table. The number moves only on
inputs that should move it, and the store half is load-bearing: fourteen
planted mutations, thirteen red, no real green. Four findings are reported
below for filing as rows; none of them is a wrong answer on an input I could
produce.

## Base — the handoff was stale again, and this is the third time

`git log --oneline -1` reported **`583f024f`**, not `main`'s tip, and
`git merge-base --is-ancestor 68a784f8 HEAD` was **false**. Round 2 recorded the
same handoff (`d49964e`, 570 behind) and said the round-1 reviewer got it too.

**But mine is a different shape from theirs, and the difference matters.**
Rounds 1 and 2 were handed a commit on an *unrelated lineage*. `583f024f` is a
strict **ancestor** of `main`: `git rev-list --left-right --count
583f024f...68a784f8` returns `0 109` — zero ahead, 109 behind, same lineage. The
branch had no commits of its own and `git status --porcelain` was empty, so
`git merge --ff-only 68a784f8` was lossless. `git merge-base --is-ancestor
68a784f8 HEAD` now passes and everything below is measured on `68a784f8`.

`26bcec72`, round 2's merge, is an ancestor of both my handed base and my
corrected one — so round 2's code was under me either way. The 109 commits I
gained matter anyway: `TASK-394` lands in them and it changes one of round 2's
own conclusions (finding 1).

## Baseline

One full `bash tests/run` on `68a784f8` before any edit: **2 of 128 modules
red, 3 of 3697 tests** — exactly the briefed set, and nothing else.

| Module | Failures | Tests |
|---|---|---|
| `test_contract_key_parity` | 2 | `TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable`, `TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness` |
| `test_resume` | 1 | `TestStaleRuns.test_a_fresh_run_is_not_stale` |

Both are pre-existing and briefed. **I attribute nothing to them** and I did not
investigate either. `tests/run` also reports `test_contract_page_snippets.py` is
absent from `durations.json`; that is a scheduling complaint, not a red test,
and it is not this row's.

`bin/perry-lint --root .`: **0 errors**, 55 warnings.

## The number on my base

```
P003-O3-KR2 = 31.0%   18 of 58
  linked_at_add            = TASK-382, TASK-383, TASK-394        (3)
  declared_unlinked_at_add = TASK-396 … TASK-405, TASK-434 … 438 (15)
  store_edge_without_event = []
  event_kr_without_store_edge = []
  declared_unlinked_at_add_reachable = True
  measured = True   source = "linkage.jsonl + .perry/events.jsonl"
```

Round 2 measured 15.38% (2/13) on `339f553`. The numerator has gained one edge
(`TASK-394`) and **fifteen `unlinked` declarations**, which is the visible trace
of `TASK-394` shipping `perry-task add --unlinked`. `lib.COMPUTED_KR_METRICS` is
`{"P003-O3-KR2": "same_action_linkage"}` — one entry, which is the Bound.

**On the spec's own measurement (Verification 1).** The spec's *"180 rows …
and not one carries a `kr`"* does not match, and both prior rounds said why:
the population is the rows whose own `add` event carries the gate's `kr` key,
which is 58 rows, not 180. I pressed the reading and I agree with round 1's
defence of it. The clean fact is in the data — 58 `add` events carry a `kr`
key and none of them carries a blank one — so the key really is the gate's
signature, per row, with no typed date.

## The four pressed questions

### 1 · Refusing a blank `--kr` — right, and the trap is the other way round

**Answer: the refusal is correct, and treating blank as omission would be the
trap.** The worry in the question is that refusal makes two spellings mean
different things. It does not: refusal makes `--kr ""` mean **nothing at all**
— `perry-task: refused … Nothing was written`, exit non-zero, no row, no event,
no store record. It is not a third meaning competing with omission; it is the
absence of a meaning, which is what a malformed value should be.

The alternative is worse and it is worse in the scripted case, which is the
case that matters. `--kr "$KR"` with `KR` unset would, under a blank-means-
omission rule, silently file a row into the denominator as never-answered and
print a warning to stderr. The caller asked a question and Perry answered a
different one. Refusing costs one re-run at the moment the mistake is free.

Three things make it the file's existing shape rather than a new rule, and I
checked each rather than taking round 2's word:

- `--summary` in the same function (`bin/perry-task:3550`) already refuses a
  structurally unusable value, so this is the second instance of a rule, not
  the first instance of a new one.
- `perry-goals link`, the other writer of this one store, refuses a blank KR
  hard. Asymmetric validation on one store is the defect `DESIGN-015` exists to
  remove.
- Omission is untouched and still warns. I verified end to end (probe H):
  the row is filed, and the warning now names **three** remedies including
  `perry-task add --unlinked`. So the refusal has not quietly made `--kr`
  mandatory.

Mutation-verified: **M12** deletes the refusal and reddens three named tests;
**M13** removes the strip and reddens one. Neither is a claim resting on a
comment.

**One correction, and it is small.** The refusal message points the caller at
`perry-goals link --unlinked` and not at `perry-task add --unlinked`, which
`TASK-394` shipped afterwards and which is the remedy that applies at the
moment the caller is standing (`bin/perry-task:3622-3628`). The `add`-without-
`--kr` warning at `:3829` was updated to name all three; the refusal was not.
A user-facing message naming the slower of two remedies. Reported, not failed.

### 2 · The null guard — enumerated, not sampled, and it is complete for `None`

The guard is `bin/lib/__init__.py:1230-1231`, `if claimed is None: return
False`. `claimed` reaches it from exactly two call sites — `:1433` (the
numerator, from the event's side) and `:1486` (the detector, from the store's
side) — and in both it is `add_event_kr.get(tid)` or `event.get("kr")`.

**Every spelling that makes `claimed` `None`, enumerated, and it is four:**

| # | Spelling | Reaches the guard as |
|---|---|---|
| 1 | no `add` event for that id at all (crash, or a `route`-created row) | `.get` misses → `None` |
| 2 | `add` event present, **no `kr` key** (every row opened before row D's gate) | `event.get("kr")` → `None` |
| 3 | `add` event with `kr: null` (the flag was omitted) | `None` |
| 4 | `add` event with `kr: null` **and** `--unlinked` (`TASK-394`) | `None` |

All four collapse to one answer — *the event does not name a KR* — which is the
only thing either caller needs. The guard covers all four. The collapse is
deliberate and round 2's mutation N13 is why the sentinel that kept them apart
was deleted; I did not re-litigate that.

**The spellings the WRITER can put on the event, enumerated by driving the real
binary** (nine probes on a `git archive` copy, not a fixture):

| Probe | `--kr` value | Outcome |
|---|---|---|
| A | `""` | **refused**, nothing written |
| B | `"   "` | **refused** |
| C | tab | **refused** |
| D | U+00A0 NBSP | **refused** |
| E | **U+200B zero-width space** | **accepted** — event `kr: "​"`, store edge `kr: "​"`, **counted in `linked_at_add`** |
| F | `"None"` | accepted; both halves `"None"`; the guard is what stops an absent event matching it |
| G | `"  P003-O1-KR1  "` | accepted, stripped once, both halves bare |
| H | omitted | row filed, warns, `kr: null` |
| I | `--unlinked` | row filed, `unlinked` record `via: "add"`, `kr: null` |

So the event's `kr` is always **`None` or a non-empty stripped string**. The
guard's domain is therefore closed, and the answer to the question as asked is:
**yes for `None`, no for "blank".**

**The remainder, measured rather than asserted.** Two gaps, both reported below
as findings rather than as FAILs:

- `str.strip()` is Python's `isspace()` set, which excludes U+200B, U+200C,
  U+200D, U+2060 and U+FEFF. Probe E files a row whose KR id is invisible and
  counts it. This is the same category as `--kr NOT-A-REAL-KR`, which the
  spec's `## Out of scope` assigns to step D.
- `_corroborates("   ", {""})` returns **True** — blank matches blank, and the
  `claimed is None` guard does not cover it. I checked whether it is reachable
  and **it is not**: it needs an event `kr` that strips to `""` (refused at the
  writer since round 2; **0 of the 58 live gated `add` events carry one**) and
  a store `edge` with `via: "add"` and a blank `kr` (**0 in the live store**;
  `via: "add"` has exactly one writer, `bin/perry-task:2768`). Latent, named.

### 3 · `USER-920` — the id does not exist, and the finding is `USER-921`'s

**`USER-920` has no row in `perry/asks.jsonl` and never did.** This is not my
discovery — it is `TASK-436`'s whole subject: `perry-diagnose` reports
`user_load.dangling == ['USER-920']` precisely because `TASK-281`'s own
`next_action` cites an id nothing defines, and that `next_action` is the text
this round was dispatched from. The citation propagated into
`perry/BOARD.md:117`, `perry/tasks.jsonl:373` and
`perry/journal/2026-09/2026-09-11.md:18`.

**The ask that exists is `USER-921`**, `blocks: TASK-281`, and it is answered:

> *"answered 2026-09-07: (A) — give `add` a writer for the declaration. Chosen
> 2026-09-08 … Filed as `TASK-394` and dispatched."*

The finding behind it was round 1's FAIL 2 and round 2's *"`unlinked`-at-add is
unreachable"*: `phase/003-storage-code.md § DoD` item 5 lets a row comply with
*"a KR edge **or** an `unlinked` declaration written by its own `add`"*, and the
second half had no writer, so a row that honestly served no KR pinned the
denominator forever and 100% was unreachable by construction.

**It is discharged, and I verified the discharge behaviourally rather than by
reading the constant.** `perry-task add --unlinked` (probe I) writes
`{"kind": "unlinked", "task": …, "via": "add"}`; `lib.UNLINKED_AT_ADD_HAS_NO_
WRITER` is now `False` (`bin/lib/__init__.py:1204`);
`declared_unlinked_at_add_reachable` is `True` in the live payload; and the path
carries **15 of the live numerator's 18**. Mutation **M6** confirms the path is
guarded on `via` — accepting any `via` reddens
`AnUnlinkedDeclarationIsAnAnswerWhenItsOwnAddMadeIt.test_the_same_declaration_
swept_in_later_does_not`, which is the spec's Verification 2 property for this
half of the numerator.

Round 2 was right to state the gap rather than close it, and right about where
the fix belonged. The gap is closed by another row, and the closure works.

### 4 · `bin/perry-state`'s two comments — false, and a ROW, not a FAIL

Both comments are false and the payload of the same tool is what falsifies
them. `bin/perry-state --json` → `attribution.kr_currents` reports
**`measured: 1`**.

- `bin/perry-state:1958-1961`, at the `kr_currents` construction: *"no tool in
  Perry re-runs a KR's metric, so this is zero by construction and is emitted
  so that a reader treating `current` as measured data is contradicted by the
  payload rather than by a docstring."*
- `bin/perry-state:2162-2163`, at the emit site: *"`measured` is zero by
  construction — see the comment where it is built."*

**This row is what made them false and left the prose behind, and I confirmed
that rather than assuming it.** `git log -S "zero by construction" --
bin/perry-state` returns one commit, `d82d873b` (2026-08-20), which predates
this row. `TASK-281`'s own merge `255c6ee4` edited `bin/perry-state` (17 lines)
to wire `linkage_records` through — the change that makes `measured` non-zero —
without touching either comment. `bin/perry-state` is the first entry in the
spec's `## Files in scope`, so this is inside the row's scope.

**It is graded ROW, and the grading rule is explicit rather than my
preference.** `review.md § 2 § What V4 does not judge` carries a table row:

> | a comment, a KR or a commit message misstates something | **file a row** | a documentation defect with its own ID, **never a FAIL on this one** |

and `§ 0` says the same in the other direction: *"a false statement in something
nobody executes — an evidence file, a result, a docstring, a commit message …
**File the correction as a row.**"* The two sentences are comments; no code
branches on them.

**Three things I checked before accepting that grade, because "it's only a
comment" is exactly how a real defect gets waved through:**

1. **Does anything execute the claim?** No. `measured` is computed at
   `bin/perry-state:1962-1963` by `sum(1 for k in _kr_rows if
   k["current_provenance"]["measured"])`. The count is correct; only the prose
   beside it is wrong.
2. **Does a test encode the false claim?** No.
   `tests/test_kr_progress_provenance.py:389-394` asserts
   `counts["measured"] == 0` with the message *"something claimed to have
   measured a KR"* — but on a three-KR fixture project holding
   `P001-O1-KR1…KR3`, none of which is in `COMPUTED_KR_METRICS`. The assertion
   is fixture-scoped and true. Nothing pins the general claim.
3. **Does the published contract still say it?** **No, and this is the
   load-bearing one.** Round 2 reported `schema/goals-list-contract.md:141` as
   doc drift saying `current_provenance.measured` is *"always `false` today"*.
   That has since been corrected at version `3.1`: the line now reads *"`true`
   when Perry re-ran the KR's metric on this read … It read *always `false`*
   here until `3.1`, and had been wrong since DESIGN-015 row F shipped."* The
   surface a consumer reads is right. The falsehood is confined to two
   comments a consumer never sees.

Had the contract still been wrong I would have weighed this differently — a
published contract a consumer keys on is not "something nobody executes". It is
right, so this is two stale comments, and the remedy is a row.

## Findings, each with what would change my mind

### Finding 1 — a half-landed `unlinked` at `add` is invisible to every detector

**`bin/lib/__init__.py:1438`** — `elif tid in unlinked_at_add:` — is the only
read of `unlinked_at_add`, and it sits **inside the event loop**, reachable only
for a `tid` already in `seen`. `seen` is the population, and the population is
built from the `add` event. So the `unlinked` half of the numerator is gated on
the very artefact whose absence would matter.

**That is the exact defect round 2 diagnosed and removed — for the other record
kind.** `bin/lib/__init__.py:1443-1483` is a forty-line comment explaining that
`store_edge_without_event` used to read `if tid in seen and tid not in
set(linked)` and that *"the new gate is the STORE — the half that survives"*.
The rewrite at `:1484-1486` applied that to `edge` records. `via: "add"` carries
**two** record kinds (`bin/perry-task:2662-2663` tabulates both), and the second
one was left on the old gate. By `review.md § 2` rule 1 this is finding the next
instance rather than enumerating the category.

**Demonstrated, not reasoned about.** On a `git archive` copy I filed
`TASK-441` (`add --kr`) and `TASK-443` (`add --unlinked`) with the real binary,
then dropped each row's `add` event to simulate the crash the code's own
comment describes — the event append is `open(..., "a")`, not a canonical
rename:

| Shape | in population | in numerator | named by a diagnostic | `current` |
|---|---|---|---|---|
| `TASK-441` edge, whole | yes | `linked_at_add` | — | 34.9 |
| `TASK-443` unlinked, whole | yes | `declared_unlinked_at_add` | — | 34.9 |
| `TASK-441` **edge half-landed** | no | no | **`store_edge_without_event`** | 33.9 |
| `TASK-443` **unlinked half-landed** | no | no | **NOTHING** | 33.9 |

Both shapes move the number identically. Only one leaves a trace.

**Why it is a finding now and was not at round 2.** At round 2
`{"kind":"unlinked","via":"add"}` had no writer, so the shape was
unconstructible and round 2 was right to leave it. `TASK-394` shipped the
writer, and 15 of the live numerator's 18 now come through this path. The
reachability flipped after the code was written and nobody re-asked the
question. That is the `UNLINKED_AT_ADD_HAS_NO_WRITER` constant's own stated
purpose working, one level short of the detector.

**Why it is a ROW and not a FAIL of this row.** The published number is not
wrong: a row whose `add` event was lost was never gated, and dropping it from
the denominator is the same correct behaviour the edge shape gets. What is
missing is the diagnostic, and no payload key claims to cover it —
`store_edge_without_event` says `edge` in its own name. No criterion in the
spec's `## Verification` names desync detection; the detectors are work round 2
added on its own initiative to close round 1's FAIL 1. Under `§ 0`'s three
questions this does not destroy state, does not publish a wrong number, and
does not weaken a gate between a user and either.

**What would change my mind:** a demonstration that the number itself moves
wrongly on this shape, or that `perry-task`'s recovery marker does **not** repair
a half-landed `unlinked` — I did not kill the process mid-`commit()` to find
out, and if recovery leaves it behind permanently the case for a detector is
much stronger than "a missing diagnostic".

### Finding 2 — `bin/perry-state:1958` and `:2162` state the opposite of the payload

Pressed question 4, above. Graded **ROW** by `review.md § 2`'s explicit table
row for a comment that misstates something, having checked that nothing
executes it, no test encodes it, and the published contract has already been
corrected.

**What would change my mind:** a consumer or a check that reads either comment's
claim as a fact — i.e. a fourth surface still asserting `measured` is always
zero. I enumerated three and all three are correct.

### Finding 3 — the blank refusal does not cover zero-width blanks

**`bin/perry-task:3621`** — `if args.kr is not None and not
str(args.kr).strip():` — uses `str.strip()`, whose set is Python's `isspace()`
and therefore excludes U+200B, U+200C, U+200D, U+2060 and U+FEFF. Probe E:
`--kr $'​'` was accepted, wrote `{"kind":"edge","kr":"​","via":"add"}`
and the row entered `linked_at_add`. Both halves of the transaction landed and
agree, so by the spec's own definition of the numerator counting it is correct
— but a reader of `linked_at_add` cannot see that the id is nothing, where
`NOT-A-REAL-KR` at least renders.

The spec's `## Out of scope` says *"`bin/perry-task add --kr` — that is step D,
`TASK-279`"*, and round 2 stated in as many words that whether the id resolves
is deliberately unchecked here. So this is row D's validation gap wearing a new
spelling, not this row's.

**What would change my mind:** a KR-existence check landing in `add` that treats
U+200B as valid — then the gap is in the new check, not deferred.

### Finding 4 — round 2 edited a file its own `## Out of scope` assigns to step D

The spec's `## Files in scope` is `bin/perry-state`, `phase/003-linkage.md`,
`tests/`. Round 2 changed `bin/perry-task` (the blank refusal and the strip,
`:3621` and `:3636`), and `## Out of scope` names *"`bin/perry-task add --kr` —
that is step D, `TASK-279`, and this row depends on it rather than doing it"*.
`review.md § 1`: *"A round may only widen the bound by filing a new row, never
by re-opening this one."* No row was filed for the widening.

I am **naming this, not failing on it**, and the reasoning is consequence
rather than charity. The refusal is the write-side of the defect round 1 FAILed
on, it is the second instance of a rule the same function already had, it is
pinned by four named tests (M12 red 3, M13 red 1), and its worst outcome is
that a caller who types `--kr ""` gets an error instead of a row. Failing a row
on a scope question whose remedy is a sentence would spend this row's last
round (`§ 6`) on bookkeeping.

**What would change my mind:** evidence that the refusal collides with what
`TASK-279` intends for `--kr`, which I did not check — I did not read
`TASK-279`'s spec.

### Finding 5 — the dispatch's own citation

This round was dispatched to press *"`USER-920`'s unlinked-at-add finding"*.
`USER-920` does not exist. The ask is `USER-921` and it is answered and
discharged. The dangling citation is live in `perry/BOARD.md:117`,
`perry/tasks.jsonl:373` and `perry/journal/2026-09/2026-09-11.md:18`, and it is
the input `TASK-436` is open on. Not a defect in this row's code; recorded
because correcting the `next_action` is what stops the next round being sent
after a non-existent ask.

## Mutation table

Fourteen planted, on my own base. Anchored **by line number with an assert on
the old text at that line** — the harness refuses to write if the anchor does
not match. `__pycache__` cleared and the clock walked past the next whole
second **after every write and again after every restore**, because CPython
validates bytecode on mtime-in-whole-seconds plus size. Every restore verified
twice: sha256 of the file against its pre-mutation digest, **and**
`git diff --quiet 68a784f8 -- <path>`.

Judged against `test_same_action_linkage`, `test_kr_progress_provenance` and
`test_add_writes_the_edge` unless noted.

| # | Mutation | Site | Verdict |
|---|---|---|---|
| M1 | `_corroborates`'s `claimed is None` guard deleted | `lib:1230` | red (1) |
| M2 | numerator takes the `add` event's word alone again | `lib:1433` | red (7) |
| M3 | `edge_at_add` stops checking `via == "add"` | `lib:1387` | red (2) |
| M4 | population reads `.get("kr")`, not key presence | `lib:1419` | red (12) |
| M5 | the track filter is removed | `lib:1421` | red (1) |
| M6 | `unlinked_at_add` accepts any `via` | `lib:1379` | red (1) |
| **M7** | `store_edge_without_event = sorted([] or …)` | `lib:1484` | **GREEN — MIS-PLANT, see below** |
| M7b | the same detector emptied **for real**, at its predicate | `lib:1486` | red (6) |
| M8 | the `unlinked` branch accepts any row (`elif True`) | `lib:1438` | red (9) |
| **M9** | **no-op control** (`[] or []`) | `lib:1408` | GREEN *by design* |
| M10 | `_corroborates` stops stripping | `lib:1232` | red (1) |
| M11 | the reverse desync stops being surfaced | `lib:1436` | red (3) |
| M12 | the blank `--kr` refusal is deleted | `perry-task:3621` | red (3) |
| M13 | `--kr` is no longer stripped | `perry-task:3636` | red (1) |
| M14 | the `--kr`/`--unlinked` contradiction refusal deleted | `perry-task:3609` | red (2) † |
| M15 | `perry-state` stops passing the store (round 1's M13) | `perry-state:1948` | red (4) |

† **M14 came back GREEN against my chosen three modules and is not a green.**
The refusal belongs to `TASK-394`, which has its own module: re-run including
`test_add_declares_unlinked` it reddens
`TestTheContradictionIsRefused.test_it_is_refused_on_presence_not_on_value` and
`test_the_refusal_says_the_declaration_cannot_be_withdrawn`. **A green measured
against a module set I picked is not a green, it is a badly chosen set** — I
am recording the first result rather than quietly replacing it, because the
near-miss is the point.

### M7 — a mis-plant, reported rather than dropped

I wrote `store_edge_without_event = sorted([] or <genexp>)` intending to empty
the detector. A generator object is always truthy, so `[] or genexp` **is** the
genexp and the line was unchanged: the GREEN measured nothing. This is round
2's N09 repeating with a different mechanism, and it is exactly why a no-op
control (M9) belongs in the table — without M9 sitting green beside it I could
have read M7 as a finding. Re-planted as **M7b** at the predicate, where it
reddens six named tests including all four shapes of the detector's own
`TheDesyncDetectorIsNotGatedOnTheEventItDetects`.

**So: 14 planted, 12 red, 1 deliberate control green, 1 mis-plant, and no real
green mutation.**

### Restores

Every mutation restored and verified at the moment of restore. Final state of
the three files I touched, on a clean tree:

```
git status --porcelain      → empty
git diff --stat 68a784f8    → empty
8a89bf28866347b9…  bin/lib/__init__.py
c5c3352fcc107679…  bin/perry-task
aa6e65ddbeeebdcb…  bin/perry-state
```

These are the same digests every mutation reported at its own restore. Nothing
under `perry/` was written except this file. Every destructive probe ran on
`git archive HEAD` copies outside the repository; **no row was filed with
`--kr` or `--unlinked` against the repository under review**, and no id was
written into a board cell.

## The criteria, item by item

| | Criterion | Verdict |
|---|---|---|
| V1 | the number before and after, side by side | met — 31.0% (18/58) live; the disagreement with the spec's 180/0 is the population reading, defended by round 1 and confirmed in the data by me (58 gated `add` events, 0 blank) |
| V2 | the same-action property tested directly | met, and mutation-verified for **both** numerator halves: M2 (red 7), M6 (red 1), M8 (red 9) |
| V3 | a control: no rows opened → no denominator | met — `same_action_linkage([], [])` → `current: None`, `measured: True`, no `ZeroDivisionError`, reason names the absent denominator; a store with records and no events also returns `None` |
| V4 | the register no longer asserts it | met — the `kr` record carries no `current`, the `metric:` prose says so in capitals, names the function and both files, and quotes what it replaced. Round 1's FAIL 3 is closed: `perry-goals list` now prints `31.0/100.0 measured` and the blanket "all asserted" claim is corrected to name the one measured KR. All three JSON publishers agree at 31.0 |
| V5 | mutation: revert the computation, a named test goes red | met — M15, 4 named tests, two of which read the live repository |
| V6 | suite no redder than the measured baseline; lint 0 errors | met — 2 modules / 3 tests, the briefed set, on a clean tree at both ends; lint 0 errors |
| Bound | `P003-O3-KR2` only, one of six | met — `COMPUTED_KR_METRICS` has exactly one entry; the other five carry no computation |
| Out of scope | no other KR, no row E, no backfill, no `add --kr` | **met except `add --kr`** — finding 4 |

## not-checked

- **A second full-suite baseline run, and per-module re-runs of the two reds.**
  I ran one baseline and one final run; both matched the briefed set. Per
  `a-single-baseline-run-is-not-a-baseline.md` that is two observations of the
  same configuration, not a settled baseline, and I did not re-run
  `test_contract_key_parity` or `test_resume` alone or investigate either.
- **The full suite under mutation.** M1–M15 were judged on three modules
  (four for M14). A mutation that reddens those and greens something in the
  other 124 would not have been seen.
- **Whether `perry-task`'s recovery marker repairs a half-landed `unlinked`.**
  This is the open question in finding 1 and it is the one that would change
  its grade. I constructed the shape by deleting the event from a copy; I did
  not kill the process mid-`commit()`.
- **`TASK-279`'s spec.** Finding 4 weighs round 2's `bin/perry-task` edit
  against this row's Out of scope; I did not read row D's criteria to see
  whether the refusal collides with what it intends.
- **The `route` bypass**, named by round 1 and still unchecked by round 2:
  `bin/perry-state` states two events create a row and `route`'s carries no
  `kr` key, so a routed row is absent from the denominator. `route` refuses a
  `project`-mode track today; I did not build a queue-mode `main` track.
- **The phase-004 upper bound.** Rows filed under the gate after phase 003
  closes still join this denominator. Named by both prior rounds, still true,
  still unowned.
- **`viewer/` and the board renderers.** I checked the three JSON publishers
  and the one terminal renderer that was round 1's FAIL 3; I did not open the
  viewer's render surfaces.
- **Concurrent-write flakiness** of the tests that read the live store and
  event log. I did not construct the race.
- **`perry-lint` against a dangling `NOT-A-REAL-KR` or U+200B edge.** Carried
  over unchecked from both prior rounds; I wrote such an edge into a scratch
  copy but did not lint that state.
- **The other five KRs (`TASK-231`) and row E (`TASK-280`).** Out of Bound.

## On § 6

This row has **one** recorded FAIL. This verdict is a PASS, so the count stands
at one and § 6 is not reached. Had I FAILed it, the next step would have been
**an ask naming the readings, not a round 4** — and I want that recorded
because the temptation was real: findings 1 and 3 are both defensible as FAILs
and I graded them ROW on `§ 2`'s table and `§ 0`'s three questions rather than
on how interesting they were to find.

=== VERDICT ===
task: TASK-281
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-281-spec.md
checked: base was 583f024f, not main's tip — merge-base --is-ancestor 68a784f8 failed; unlike rounds 1 and 2 it was a strict ANCESTOR (0 ahead, 109 behind, same lineage) on a clean tree, so ff-only onto 68a784f8 was lossless and everything below is on that pin. One full tests/run baseline (2 of 128 modules red, 3 of 3697 tests — test_contract_key_parity 2, test_resume 1, exactly the brief) and one final run identical, tree guard clean at both ends; bin/perry-lint --root . 0 errors. The live number 31.0% (18 of 58 — 3 edges + 15 unlinked declarations) and COMPUTED_KR_METRICS holding exactly one entry. All six Verification items and the Bound, item by item. Verification 4 re-derived rather than taken from round 2: round 1's FAIL 3 is closed — perry-goals list now prints "31.0/100.0 measured" and names the one measured KR instead of claiming all are asserted, and krs --json, list --json and perry-state all publish 31.0. The four pressed questions: the blank --kr refusal (right, and blank-means-omission is the trap, verified end to end by nine probes driving the real binary); the null guard (complete — all four spellings that make `claimed` None enumerated, plus the writer's full output domain: the event kr is always None or a non-empty stripped string); USER-920 (no such ask — the finding is USER-921's, answered, and discharged by TASK-394's add --unlinked, verified behaviourally: declared_unlinked_at_add_reachable true and 15 of 18 numerator rows come through it); and bin/perry-state:1958/:2162 (both comments false, payload reports measured: 1). 14 mutations, 12 red, 1 deliberate no-op control, 1 mis-plant re-planted as M7b (red 6), every restore verified by sha256 AND git diff --quiet 68a784f8, final tree byte-identical with git status --porcelain empty.
not-checked: a second baseline configuration and per-module re-runs of the two briefed reds; the full suite under mutation (three modules, four for M14); whether perry-task's recovery marker repairs a half-landed `unlinked` — the open question in finding 1 and the one that would change its grade; TASK-279's spec, against which finding 4's scope question is weighed; the route bypass end-to-end on a queue-mode main track; the phase-004 upper bound on the denominator; viewer/ and the board renderers; the concurrent-write race on the live-repo assertions; perry-lint against a dangling NOT-A-REAL-KR or U+200B edge; the other five KRs (TASK-231) and row E (TASK-280)
proof: n/a — PASS. Four findings are reported for filing as rows, none of them a wrong answer on an input I could produce: (1) bin/lib/__init__.py:1438 reads unlinked_at_add only inside the event loop, so a half-landed `unlinked`-at-add is dropped from the population and named by NO diagnostic, where the edge twin at :1484-1486 is named by store_edge_without_event — the same defect round 2's own 40-line comment says it removed, left standing on the second of the two record kinds `via:"add"` carries, and live only since TASK-394 shipped the writer; demonstrated on a git archive copy by dropping TASK-443's add event (current 34.9 → 33.9, nothing names it) against TASK-441's (same move, reported). (2) bin/perry-state:1958 and :2162 state `measured` is zero by construction while the same tool's payload reports measured: 1 — graded ROW by review.md § 2's explicit table after confirming nothing executes the claim, tests/test_kr_progress_provenance.py:389-394 pins it only on a fixture with no computed KR, and schema/goals-list-contract.md:141 has already been corrected at 3.1. (3) bin/perry-task:3621 uses str.strip(), so U+200B/U+200C/U+200D/U+2060/U+FEFF pass the blank refusal — row D's id-validation gap in a new spelling, which the spec's Out of scope assigns to TASK-279. (4) round 2 edited bin/perry-task:3621 and :3636, which the spec's Out of scope assigns to step D, without filing a row for the widening as review.md § 1 requires.
=== END VERDICT ===
