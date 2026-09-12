# TASK-382 — result

> Status: implemented and measured; **not reviewed**.
> Executor: the PMO session, inline on `main`, per `ADR-018 § B` — the fix
> shape, the sites and the verifying test were all already stated on the row.
> Rung: **V2**, lowered from V3 by the user on `ADR-020`'s gate. `kr_rows`,
> `cmd_krs` and the terminal renderer are READ paths in `bin/perry-goals`; no
> write path, no `schema/state-schema.json`.

## 0. Reproduced first, on today's `main`, in three commands

One KR, `P003-O3-KR2`, the only entry in `lib.COMPUTED_KR_METRICS`:

```
perry-goals list            →  P003-O3-KR2  31.0/100.0  asserted
                               footer: no `current` here is a measurement
perry-goals list --json     →  current 31.0, provenance: measured
perry-goals krs  --json     →  current None, no current_provenance key at all
perry-state --section linkage → current 31.0, provenance: measured
```

**The same command, the same invocation, one flag apart, gives two different
answers** — and the terminal prints a blanket denial two lines under the row it
is false about.

The row's cited line numbers were stale: today's `TASK-236` merge took
`bin/perry-goals` from 3,147 to 3,334 lines, so `cmd_krs` is at 2772 rather
than 3267 and the renderer at 3286/3295 rather than 3535/3544. Every site is
otherwise exactly as described, found by content.

## 1. The three changes

**`cmd_krs` splices the computation** instead of reading `k.current` off the
register record, through the same `lib.computed_kr_current` that
`bin/perry-state` and `kr_rows` already use, and off the same `"current"` key
that `lib § kr_progress_provenance` reads (`out["current"] =
computed.get("current")`). A second spelling of that key is how three
publishers would drift again; `M4` below is the mutation that proves the key is
load-bearing.

**`measured` becomes a third answer in the terminal renderer.** The branch
folded every non-`unasserted` state into the word `asserted`. Staleness is
deliberately not consulted for a measured number: a value re-derived on this
read cannot be stale, and asking `current_staleness` about it would print
`STALE` for something computed a millisecond ago.

**The footer is derived from the payload rather than asserted about it.** It
now names which KRs are measured and how many, and falls back to the old
sentence only when none are. A claim that quantifies over the rows has to be
computed from the rows, or it stays true exactly until the first exception.

## 2. All four publishers, after

```
perry-state --section linkage       31.0
perry-goals list --json             31.0
perry-goals krs --json              31.0
perry-goals list (terminal)         31.0/100.0 measured
footer: 1 `current` here is measured, re-run on this read (P003-O3-KR2);
        the rest are asserted by an author
```

## 3. A FIFTH site, found by sweeping the field rather than the row

The row says why all four were missed and it is one miss: `TASK-281` enumerated
readers of `metric` when the field whose provenance it changed is `current`. So
this round swept `current` and its provenance across both tools, and found one
more — **in `bin/perry-state`, and it is prose, not code**:

```python
# Not a placeholder for a number nobody filled in: no tool in Perry
# re-runs a KR's metric, so this is zero by construction and is emitted
# so that a reader treating `current` as measured data is contradicted
# by the payload rather than by a docstring.
"measured": sum(1 for k in _kr_rows …)
```

and again at the emit site: *"`measured` is zero by construction — see the
comment where it is built."*

`perry-state --json` reports `kr_currents: {"total": 6, "asserted": 4,
"unasserted": 1, "measured": 1, …}`. **The counter is correct and the two
comments beside it are false**, four lines apart, and false in exactly the way
the footer was.

**FOUND, NOT FIXED, and the reason is this project's own rule.** `TASK-281` is
at `review` awaiting round 3, and its spec declares `bin/perry-state` as the
first entry in its Files in scope — *"where the computation goes"*. A comment
about that computation's own result is inside that scope, not beside it, so
editing it now is the hazard that blocked `TASK-383` for a week: *"editing it
mid-review would invalidate that round"*. This round changed nothing in
`bin/perry-state`, and the full-suite run below is on a tree where that file is
untouched.

It is handed to round 3 rather than filed as a row: that round is already
reading this file and this claim, and two false sentences are cheaper to
correct inside a round that is happening than to carry as a row of their own.
`review.md § 0` also puts "a false statement in something nobody executes" on
the do-not-spend-a-round list, which is the right call for *dispatching* a
reviewer and is not a reason to leave it standing in front of one.

**This class is outside what the new test can catch, and that is declared
rather than papered over.** The guard compares published VALUES; a comment is
not published.

## 4. The guard

`tests/test_same_action_linkage.EveryPublisherOfAComputedKrAgrees`, 4 tests.
It **quantifies over `lib.COMPUTED_KR_METRICS`, not over one id**, which is
what makes it catch a second computed KR and a fifth publisher rather than
re-checking this one.

Two anti-vacuity layers, both assertions and not comments:

- `computed_ids()` fails if `COMPUTED_KR_METRICS` is empty, because every
  assertion in the class would otherwise quantify over nothing.
- `test_every_computed_kr_is_published_by_at_least_one_reader` fails if a
  computed KR reaches no publisher, because the agreement tests would then
  compare an empty set.

`from_goals_krs` looks at both `--level phase` and `--level overall`: a lookup
that knew only one level would return `None` for a KR filed under the other and
report that as agreement.

Shape and agreement, never a pinned value. The live number moves the moment a
row is filed with `--kr`; a guard that pinned `31.0` would be red for the
project working. That is the rule the class above it in this module already
states, kept.

## 5. Mutations — five, none green

| # | Broken | Result | Reddened |
|---|---|---|---|
| M1 | `cmd_krs` reads the register again | RED | the three-publisher agreement |
| M2 | `measured` folded back into `asserted` | RED | the terminal renderer test |
| M3 | the footer asserts the universal again | RED | the footer test |
| M4 | `computed.get("value")` instead of `"current"` | RED | the three-publisher agreement |
| M5 | `COMPUTED_KR_METRICS` emptied | RED | all four, via the anti-vacuity assert |

`M4` is the mutation for the key name — the wrong spelling was this round's
first draft, so it is planted rather than imagined. `M5` was planted in
`bin/lib/__init__.py` and that file was restored and **sha256-verified
unchanged**; `git diff` on it is empty. `TASK-281` is at `review` awaiting
round 3 and its round 2 edited that file, so nothing in this round may land in
it.

## 6. Suite and the V2 attestation

`bash tests/run`: **3 of 3,697 failed**, the three pre-existing by name —
2 in `test_contract_key_parity`, 1 in `test_resume` — tree guard clean
(*nothing under /Users/bytedance/proj/Perry moved*). The suite grew by exactly
the 4 tests this row adds.

`perry-lint`: 0 error(s). `test_same_action_linkage`: 75 tests, OK.

## 7. Scope held

`bin/perry-goals` and one test module. **`bin/lib/__init__.py` and
`bin/perry-state` are both untouched**, verified by `git diff`. `TASK-281`'s
spec declares its Files in scope as `bin/perry-state`, `phase/003-linkage.md`
and `tests/`; `bin/perry-goals` is in none of them, so its round 3 is not
disturbed by anything this round did, and § 3's finding is handed to it rather
than applied under it.

## 8. Not done

`perry-goals krs --json` publishes `current` and still carries **no
`current_provenance` key at all**, so a consumer of that payload cannot tell a
measured number from an asserted one. Adding one is a payload shape change on a
command whose nested payload is not described by
`schema/goals-list-contract.md`, and it is a decision rather than a fix. Left
open deliberately, recorded here.
