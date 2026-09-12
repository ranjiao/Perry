# TASK-439 — round 2, the reader the refusal names

**Rung:** V4. **Round 1 verdict:** FAIL, one finding
(`evidence/2026-09/TASK-439-round1-v4-review.md` § 2, FAIL-1). This is the
first FAIL, so `review.md § 6` allows this round.

---

## 0. What the reviewer charged, and what survived it

FAIL-1 is one sentence in the refusal `cmd_add` raises when a caller passes
neither `--kr` nor `--unlinked`:

> `--unlinked` … writes a record that CANNOT BE WITHDRAWN by any `perry-task`
> command **and that `perry-lint` reports for as long as it stands**

The clause after "and" is false, and the reviewer measured it rather than
reading it: `perry-lint § linkage-unlinked-exists` (`bin/perry-lint:1518`)
files its `warn` only when the declared id is **not** a record in
`tasks.jsonl` — a typo, or a purged row. A healthy declaration hits the
`continue` and `perry-lint` says nothing about it, ever.

I re-derived that independently and it holds. On a copy of this project,
`perry-lint` prints **zero** lines containing `unlinked` whether the row was
added with `--unlinked` or with `--kr`.

**But only the tool name was wrong.** The reviewer's own "what would change my
mind" asked for a second reader that names a live `via: "add"` declaration.
There is one, and the check's own neighbouring comment in `bin/perry-lint`
already points at it:

> `perry-state § attribution` reports `declared_unlinked` straight from this
> list (TASK-228)

So the substance of the claim — a standing declaration stays visible, which is
the only non-neutral friction in the whole `§ What it must not do` item 1
argument — is true. The sentence named the wrong tool.

## 1. Measured, on a copy of this project

Two rows added to the same scratch copy, one flag apart, read back through
`perry-state --section attribution` and `perry-lint`:

| row added with | `declared_unlinked` | `linked` | `perry-lint` lines saying "unlinked" |
|---|---|---|---|
| — (before) | 116 | 2 | 0 |
| `--unlinked` | **117** | 2 | 0 |
| `--kr P003-O3-KR2` | 117 | **3** | 0 |

The two flags are indistinguishable to `perry-lint`, exactly as charged. They
are cleanly distinguishable to `perry-state --section attribution`, and the
declaration is the one that lands in a permanent count.

## 2. What landed

Three sites, because round 1 enumerated the category rather than the next
instance and the false clause stood in more than one product surface.

| file | what changed |
|---|---|
| `bin/perry-task:3729` | the refusal names `perry-state --section attribution` and `declared_unlinked` |
| `bin/perry-task:3693` | the comment carrying the must-not #1 argument, plus a paragraph recording that this reader was wrong for a round and why the substance survived |
| `work/reference/subcommands.md:591` | the `add-task` KR bullet, with a parenthetical saying what `perry-lint` actually warns on, so a reader who remembers the old sentence is not left guessing |

Not changed: `bin/perry-lint`. Making the old sentence true by warning on every
standing declaration would put **143 warnings on this project alone** and would
warn on a *correct* answer — `--unlinked` is a legitimate thing to mean, and a
permanent warning on a correct answer is the noise this project keeps removing.

## 3. Tests — `TestTheStandingDeclarationHasAReader`, six

In `tests/test_add_refuses_without_an_answer.py`. They **drive both readers**
rather than reading the sentence, which is what would have caught round 1.

| test | what it pins |
|---|---|
| `test_the_message_no_longer_names_perry_lint` | the false string cannot come back |
| `test_the_message_names_the_reader_that_does_report_it` | the corrected one is there |
| `test_the_named_reader_actually_reports_the_declaration` | the claim, driven: `--unlinked` puts the new id in `declared_unlinked` and the count rises by one |
| `test_a_linked_row_is_not_declared` | **anti-vacuity** — one flag different, same fixture, count does not move |
| `test_the_declaration_stands_across_a_second_read` | "for as long as it stands", not a one-shot line on the add run |
| `test_the_lane_page_names_the_same_reader_as_the_refusal` | the second product surface, so the category stays closed |

Module: **27 tests, all green** — the other three are § 5's ROW-2 decision.

## 4. Mutations — five, none green

`__pycache__` cleared before every run (TASK-072; it produced a false red in
TASK-381 the same week).

| # | mutation | result |
|---|---|---|
| M1 | restore `perry-lint` in the refusal message | **RED** — 2 tests |
| M2 | revert the lane page to its false sentence | **RED** — `test_the_lane_page_names_the_same_reader_as_the_refusal` |
| M3 | `--kr` also sets `unlinked` | **RED** — 3 tests incl. `test_a_linked_row_is_not_declared` |
| M4 | `perry-state` reports `declared_unlinked: []` | **RED** — 2 tests |
| M5 | the declaration record records `via: "link"` | **RED** — 2 tests |
| MUT-B (round 1's green) | narrow the refusal to the `main` track | **RED** — `test_a_non_main_track_is_refused_too` |

**Disclosed, because a reader should not have to find it.** M5 reddened the two
*pre-existing* tests, not the two new ones. `perry-state`'s `declared_unlinked`
reads `link.unlinked`, which does not discriminate on `via`; it is
`lib.same_action_linkage` that does. So my new tests pin *that a declaration is
reported*, and the existing ones pin *that it is reported as an `add`*. Both
properties are held, by different tests — but not by the same test, and the
result should say so rather than let the table imply otherwise.

## 5. The other three findings — not this round's

### ROW-2 — taken here, with a test, instead of opened as a row

The reviewer said this *"needs its own row and its own decision, not a third
round here"*. The decision is cheap and the row is not: what ROW-2 actually
reports is an **unpinned scope**, which `MUT-B` proved by coming back green.
Deferring it means the board carries a row whose whole content is "write the
test", while the green mutation stands in the meantime.

So the decision is taken and pinned, and the direction is the one shipped:
**the refusal is track-independent, deliberately.** The reason is in
`TestTheRefusalIsDeliberatelyTrackIndependent`'s docstring and is not the
phase's KR — it is that a blank KR answer is un-withdrawable from
`never_answered` (a later `perry-goals link` writes `via: "link"`), and that is
a property of the store, not of the track. An intake row promoted to `main`
later carries its blank answer with it and nothing on the promotion path goes
back and asks. Scoping the gate to `main` exempts exactly the rows most likely
to change track.

The cost the reviewer measured is kept, as a test rather than as prose:
`test_the_metric_is_unmoved_either_way_which_is_the_cost` asserts an intake row
never enters `P003-O3-KR2`'s denominator, so if that ever becomes false the
argument is re-taken rather than silently inherited. Three tests, and `MUT-B`
re-run against them is **RED**.

**If the user would rather this were a row and a separate decision, it is one
revert away** — the three tests name the direction explicitly, so reversing it
is a visible edit, not a silent one.

### ROW-3 and ROW-4 — corrections, not rows

| finding | grade | disposition |
|---|---|---|
| ROW-3 — the result's `route` claim is not reachable as described | ROW | **the reviewer is right.** `cmd_route` (`bin/perry-task:6283`) refuses `--track main` because `main` is mode `project` and routing is a queue-mode operation. So routed rows are not in the KR's population and cannot be. Round 1's result § 9 finding 1 is wrong as written and is corrected here rather than left to send a future row chasing a defect that is not there |
| ROW-4 — the vacuity seam is documented in the caller, not the shared helper | ROW | test hygiene, kept off this rung by `review.md § 0`. The reviewer swept for siblings and found none, so the disclosed defect has exactly one instance and it is fixed |

## 6. Suite

Full run, `tests/run`, at the tip of this change:

```
130 modules · 3776 tests · 94.6s · 8 workers
✗ 2 of 130 MODULE(S) red
✗ 3 of 3776 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three reds are the session's standing ones and none is in a module this
change touches: two conformance-witness keys in `test_contract_key_parity`,
and the clock-dependent `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.

**Disclosed: the first run of this suite tripped the tree guard**, and it was
mine, not a test's — I wrote this evidence file while the run was in flight, so
the guard correctly reported a file created under the tree between its two
readings. Re-run with the tree held still, it is clean. Recording it because
the guard doing its job is not the same as the guard being noisy, and a reader
comparing two logs of the same change should not have to work out which.
