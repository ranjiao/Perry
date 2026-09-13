# TASK-236 — round 5: the join is an identity (USER-929 answer C)

**Rung:** V4. **Authority:** `USER-929`, answer **C**, given 2026-09-13.
Round 4 FAILed (`evidence/2026-09/TASK-236-round4-v4-review.md`), the second
FAIL since `USER-927`, so `review.md § 6` sent it to the user rather than to a
fifth round of the same move.

---

## 0. Why this round is different from the last four

Four V4 rounds FAILed `objective_id == obj["id"]`, each on a different bad
value, and each fix excluded exactly that value:

| round | input | effect | fix |
|---|---|---|---|
| 2 | a KR matching no objective | **lost 1 row** | a residual that refuses |
| 3 | a KR with no `version` | slipped past the residual's scope | `version` required at the validator |
| 3 | blank `objective_id` (permitted by that fix) | **invented 75** | blank key matches nothing |
| 4 | a **duplicate** objective id | **invented 3** | — this round |

The round-4 reviewer named the principle none of those fixes addressed:
**nothing made the comparison an identity.** The user chose to fix the join
itself (A) and the tool that produced round 4's input (B).

## 1. A — the render: identity first, then a lookup

`overall_kr_model` now keys a version's objectives by id **before** placing a
single key result, and refuses a version in which two objectives share one.
Key results are then placed by dictionary lookup. A dict cannot hold two
objectives under one key, so a key result belongs to at most one objective
**by construction** rather than by a filter someone has to keep correct.

**Blank ids are not keys, deliberately.** Every KR naming a blank or unknown
`objective_id` stays unplaced and round 2's residual refuses **naming each
KR** — which is what a reader with a `DESIGN-009` step-1 store needs to act on.
Refusing at the precondition instead would name objectives, not rows.

Ids are compared stripped on both sides, and **both strips are now pinned** —
round 4's reviewer deleted either with all 33 tests green.

Measured:

| store | before | after |
|---|---|---|
| round 4's reproduction: 3 KRs, 2 objectives sharing `O-1` | 6 rows, rc 0 | **refused**, names `O-1`, `Objective A`, `Objective B` |
| the live project | 19 under 5 | 19 under 5 |
| objective id `" O-1 "`, KR `"O-1"` | — | 3 placed, rc 0 |

## 2. B — the mint stops producing the input

`mint_objective_ids` keys `by_title` on title alone, deliberately — an
objective restated in a later version keeps its id and the title is the link.
Inside one version that key cannot tell two objectives apart, so both were
minted **one** id. A pass zero now refuses when two titled objectives in a
single version share a title.

It refuses rather than choosing. What distinguishes two same-titled objectives
inside a block — heading, order — has no answer on record, and minting on a
guess would fasten key results to whichever objective the guess preferred.
That sidesteps the design question the earlier recommendation said B carried.

B also closes a path round 4 did not name: an objective that **already carries**
`O-1` and a same-titled twin with no id would have been handed `O-1` silently
through pass two's `reused` list.

## 3. B3 CAME BACK GREEN, AND WHAT IT FOUND WAS A FALSE COMMENT OF MINE

While writing B I added a skip to pass zero so that untitled objectives would
not be grouped, on the theory that two untitled headings would otherwise be
told they "share a title" and lose the more specific "carry no title"
diagnosis. Above the skip I wrote:

> Measured: with blanks included, the existing untitled test still passed on
> its heading assertions while the message it was written to pin was never
> printed for that input.

**I had not measured that, and it cannot happen.** Mutating the skip away (B3)
left all 76 tests green. The reason is in the function: the untitled guard sits
**above** pass zero and refuses *any* objective without a title — even one —
before pass zero runs. No blank title ever reaches the grouping. The skip was
unreachable, and the test beside it passed because the earlier guard refused
first, not because of anything pass zero did.

So a sentence reading as evidence was a hypothesis, and the green mutation is
the only reason it did not ship. That is this project's recurring defect in its
least forgivable form: not a measurement artefact, a measurement that never
happened.

**What changed.** The skip and the false comment are removed. The comment now
states the real invariant — every record reaching pass zero has a title,
because the guard above guarantees it. The test is renamed
`test_the_untitled_guard_runs_before_pass_zero` and pins what actually
protects the diagnosis, which is **ordering**: it asserts `carry no title` is
the message.

**B3′, the mutation that can falsify it:** move pass zero above the untitled
guard. Two untitled headings then group under `""` and are told they share a
title. Result recorded in § 5.

## 4. Tests

- `TestTheJoinIsAnIdentity` (render), seven — including the cross-version
  anti-vacuity control and both padded-id pins.
- Four in `TestTheObjectiveIdIsMinted` (mint), including the restated-objective
  control.

## 5. Mutations

| # | mutation | result |
|---|---|---|
| A1 | duplicate-id refusal removed | **RED** — 4 |
| A2 | a second same-id objective silently overwrites the first | **RED** — 4 |
| A3 | objective-side strip deleted | **RED** — 2 |
| A4 | key-result-side strip deleted | **RED** — 1 |
| A5 | collision checked across all versions, not per version | **RED** — 23 |
| B1 | pass-zero refusal removed | **RED** — 2 |
| B2 | grouping ignores version (refuses restated objectives) | **RED** — 9 + 1 error |
| B3 | untitled records grouped too | **GREEN** — the skip was dead code; § 3 |
| B3′ | pass zero moved above the untitled guard | **RED** — `test_the_untitled_guard_runs_before_pass_zero` |

A5 and B2 are the boundary controls: each makes the rule refuse correct
multi-version stores, and each reddens broadly.

## 5a. The suite caught an unrooted hand-back in A's own refusal

The first full run reddened `test_handed_back_root` on two tests. Re-run alone,
both reproduced:

```
bin/perry-goals:2985 'perry-okr migrate-ids'   — a writer handed back with no root
66 != 68                                        — two new paste-able writer phrases
```

A's duplicate-id refusal names `perry-okr migrate-ids` as the likeliest source
of such a store, and I wrote it without the root — so a reader copying it would
run the migration against whatever project their cwd resolves to. That is
TASK-253's category, caught by the guard TASK-253 repaired **the same morning**.
`project_root` was already in `overall_kr_model`'s signature and a sibling
refusal a few lines up roots its hand-back the same way; the fix is
`{lib.root_flag(project_root)}`.

The count goes 66 → 68, and unlike this morning's rise both are real new
hand-backs: A's (now rooted) and pass zero's `perry-okr write --from-file`
(rooted from the start). The constant's comment names both.

**The same run carried one more red, and it is not this change.**
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_registers_do_not_exceed_opencode_cap`
passed three runs out of three alone — a concurrency flake under the parallel
suite. And `bin/perry-task:1447` emits a `DeprecationWarning` for `'\\w'`; `git
blame` dates that line to 2026-08-18, so it is recorded here and not touched.

## 6. The other finding, recorded not fixed

The user declined to open round 3's remaining finding. `load_okr_store` does
not validate, so `perry-goals list` and `perry-state` read a store `perry-goals
krs` refuses — measured, `list` prints `18 KR(s)` at rc 0 where `krs` exits 1.
Making the shared reader validate reddens 15 of 35 in
`test_contract_key_parity`, the published-key contract. Two readers
disagreeing about whether a store is usable is now a **recorded property**, to
be reopened if it bites.

## 7. Suite

Final run, after § 5a's root was added:

```
130 modules · 3814 tests · 77.2s · 8 workers
✗ 3 of 3814 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`. The host-support
flake from the first run did not recur.
