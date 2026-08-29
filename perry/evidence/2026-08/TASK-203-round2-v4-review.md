# TASK-203 — V4 review round 2: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-203-spec.md`.
> Under review: `9b4ae3d`. All destructive work on scratch copies; the worktree
> was read-only and clean at start and end.

## What round 2 fixed, verified

**Finding 2's original door is shut.** Whole-tree SHA-256 before/after an
unrelated `add` with the section missing: `intake.jsonl` byte-identical.

**The data-keyed check subsumes the command-name exemption for the ordinary
shapes** — ten board mutations run end-to-end, nine correct.

**Crash safety re-verified with the 3-entry canonical set** — `os._exit(9)`
after the 1st, 2nd and 3rd `os.replace`: clean forward recovery at all three,
no leftovers.

**`REGISTER_EVENTS` is still complete both ways.** The new reverse guard walks
25 `cmd_*`, finds 11 naming a section, checks the 10 that emit an event literal.

**Baseline accurate in both runners** — `9b4ae3d` 2808/8 vs `45a355d` 2786/8,
byte-identical failure sets. *"The round-1 complaint about reporting one runner
without saying which has been fixed."*

## Finding 1 — BLOCKING. The data it asks is not unique

`bin/perry-task:2192-2193` decides identity on `(request, arrived)`. **Two
intake rows with the same Request on the same day is not exotic — it is the
same thing filed twice, which is the ordinary reason a row gets `dropped —
duplicate`.** Every row `perry-task intake` writes gets today's date, so on a
busy day `arrived` contributes nothing and identity collapses to the Request
string alone.

```
STORE, correct:
{"order":2,"request":"fix the login bug","outcome":"dropped … folded in","discharged":true}
{"order":3,"request":"fix the login bug","outcome":"—","discharged":false}

  ← the dropped duplicate tidied out by hand
  ← perry-task add "an ordinary task"      (rc 0)

{"order":2,"request":"fix the login bug","outcome":"—","discharged":true}   ←
perry-lint: {"records": 3, "drifted": 0}
```

Round 1's Finding 1, unchanged, and carried forward permanently by two further
writes. `bin/perry-tasks:1313` computes `undischarged` off store records, so the
row is now invisible to the count that makes an over-cap queue mean "not being
drained".

> *"The commit message's own framing applies to itself: keying on the command
> name was the wrong question, and keying on a non-unique tuple is the same
> mistake one level down."*

**The fix is five lines** — refuse the join when the stored identity tuples are
not unique. The reviewer applied it on a copy: correct result, **and all 22
shipped register tests stay green**, which is itself proof no test distinguishes
the two behaviours.

## Finding 2 — BLOCKING. One door of four

`bin/perry-task:2237` guards only `has_section == False`. The derivation returns
`[]` for **four** board states: `intake_section_shape` returns `None` for
`absent`, **`prose`** and **`foreign`** too. Measured, rc 0 each time:

```
A. the table replaced by a sentence      → intake.jsonl 0 bytes
B. `Request` column renamed to `Ask`     → intake.jsonl 0 bytes
C. a legend table added under `## Intake`→ intake.jsonl 0 bytes
```

And on asks the truncating command is the register's **own**: a legend table
under `## User Input Queue`, then `perry-task ask` → `asks.jsonl` 0 bytes.

> *"The commit message states the correct principle — 'A board that lost a
> section while its store still holds records is DRIFT' — and then implements it
> for one of the four shapes that lose the rows. The shipped test asserts
> exactly the one case that was reported and no other; that is what left the
> other three standing."*

## Finding 3 — BLOCKING. The merge is still untested, and my mutation measured a crash

My `current = None` mutation is red **incidentally**: `current` now feeds
`positions_still_hold`, whose comprehension raises `TypeError` before any merge
happens. The honest form — `current = []` — is **GREEN across all 2808 tests**,
`TestTheStoredRecordMergeIsRealAndBounded` included.

The reason is in the test: `test_a_discharged_flag_survives_an_unrelated_write`
discharges via `resolve-intake`, which writes `dropped … folded in` into the
`Outcome` cell, and `intake_record` **re-derives** `discharged` from that cell
when the store says nothing. The flag it asserts survives is re-derivable from
the board, so deleting the merge cannot make it fail.

Three more, each green across 448 tests: dropping `arrived` from the identity
tuple; `was is None` → `return False`; passing `current` to the probe.

Only one of my four reported counts is exact.

## Finding 4 — non-blocking. The reverse guard is evadable, and `SECTION_OF` is still dead

Two plants pass silently: one building its event name from a variable (the
regex finds nothing, `if not events: continue` skips it), one reaching the
section through `perry_store.INTAKE_SECTION` — *"the guard is keyed on the
spelling the codebase's own comment discourages, which is also why it cannot
see a localized board."*

And `sections = set(self.SECTION_OF.values())` is **assigned and never read** —
the guard hardcodes the same literals four lines later. *"Round 1's Finding 4
was a comment asserting a guard that does not exist; this is a smaller instance
of the same shape."* The `{"cadence-add", "cadence-done"}` exemption is keyed on
command names, in the test that exists because keying on command names was the
defect.

## (a) The double derivation — sound, and cheap

Equivalent for the question asked; 0.16s / 0.24s / 0.45s at 100 / 1000 / 4000
rows. One waste: the probe is computed unconditionally, including for `risks`
and `asks` where the answer is `True` without reading it.

## (c) `positions_still_hold` and a new row — correct, and untested

Append-at-end preserves the merge; insert-at-0 and insert-mid correctly drop it.
*"The branch is correct — and m6 shows nothing tests it."*

## Verdict

```
=== VERDICT ===
task: TASK-203
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-203-spec.md
proof: bin/perry-task:2192-2193 — `(request, arrived)` is not a unique key. Two
       intake rows with the same Request on the same day, the discharged one
       tidied out by hand, then `perry-task add` (rc 0): the survivor is written
       `"discharged": true` with `"outcome": "—"`, perry-lint reports
       {"records": 3, "drifted": 0}, and two further writes carry it forward.
       Second: bin/perry-task:2237 with bin/perry_store.py:1039-1040 — the gate
       covers only the missing section; the derivation also returns [] for
       `prose` and `foreign`, so a 3-record intake.jsonl goes to 0 bytes on an
       unrelated `add` when the Request column is renamed, a sentence replaces
       the table, or a legend table joins the section — and a 1-record
       asks.jsonl goes to 0 bytes on `perry-task ask`. Third:
       `current = []` at bin/perry-task:2261 is green across all 2808 tests, so
       the two-source merge is still uncovered; the mutation the commit reports
       as red goes red on a TypeError, not on the merge.
=== END VERDICT ===
```
