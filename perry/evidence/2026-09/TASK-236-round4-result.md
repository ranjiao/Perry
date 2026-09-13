# TASK-236 — round 4: a blank join key is not a wildcard

**Rung:** V4. **Round 3 verdict:** FAIL, two findings
(`evidence/2026-09/TASK-236-round3-v4-review.md`). This round closes F-2 and
**measures** F-1 rather than fixing it, because the measurement turns F-1 into
a decision the user has to take.

`review.md § 6`'s guard reads this row at **one** FAIL since `USER-927` picked
the principle, not three of two, so a round is the allowed next step.

---

## 1. F-2 — the severe one, and the direction it inverts

Round 3 required a non-blank `version` in the validator and deliberately
**permitted** a blank `objective_id`, because `DESIGN-009` step 1 has `derive`
write it blank and step 3's `migrate-ids` is the only thing that fills it.
Requiring it condemns every store between those two steps — measured at 21
tests red, which is why the narrowing was right.

It then assigned that case to round 2's residual. **The residual cannot hold
it.** The join is `objective_id == obj["id"]`; when both sides are `""`, every
key result matches every objective, and nothing is left over to strand.

Measured on `88fea9fe`, blanking the field on all 38 `kr` records and the `id`
on all 10 objectives, no other edit:

| | |
|---|---|
| distinct `kr` ids in the store | 20 |
| rows `krs --level overall` printed | **95** |
| exit code | 0 |
| `perry-okr verify` / `diff` / `perry-lint` | all 0 |

**Round 2 lost one row; round 3 invented seventy-five.** The direction
inverted and the defect class did not: a count printed as fact over a table
that is not the store.

## 2. What landed

One condition. A blank key matches **no** objective rather than all of them:

```python
oid = str(obj.get("id") or "").strip()
rows = [k for k in krs
        if k.get("version") == version and oid
        and str(k.get("objective_id") or "").strip() == oid]
```

Such a record is then unplaced, the residual strands it, and the render
refuses. That is the loud failure a half-migrated store deserves, and it is
round 2's rule rather than a new one.

Same store, after:

```
perry-goals: refused — 19 key result(s) in the store belong to no objective
and would be dropped from this render: O1-KR1, O1-KR2, … O5-KR4.
rc=1
```

The refusal's sentence was widened to name **both** ways a key is unplaceable
— blank, or orphaned — because a reader with a half-migrated store told only
about orphans will go looking for the wrong thing.

The correct store is untouched: 19 key results under 5 objectives, rc 0, on
this project and on the fixture.

## 3. F-1 — MEASURED, NOT FIXED, and the measurement is the point

`viewer/parsers.py § load_okr_store` never calls `validate_records`, and
`parse_okr` inside `load_snapshot` feeds from it — the read path the file's own
comment calls the one every tool and the viewer share. Confirmed by reading,
and confirmed live: with one `version` dropped, `perry-goals krs` refuses at 1
while `perry-goals list` and `perry-state --section okr` exit 0.

**So I probed the fix.** `load_okr_store` made to call `validate_records`:

```
✗ test_contract_key_parity.py — 15 of 35 test(s) failed
```

That module is the published-key contract. Making the shared reader validate
changes which keys are observable, which is a **contract change**, not a bug
fix — so it is not mine to make inside a round. Probe reverted and verified
sha256-identical to `git show HEAD:viewer/parsers.py`.

**One correction to round 3's review**, so the next round does not chase it.
The reviewer reported `perry-goals list` printing "18 of 19 at rc=0" on the
damaged store. It does not: that reader's output is **byte-identical** to the
clean one. The observable defect is that two readers disagree about whether
the store is usable, not that one silently drops a row.

## 4. Tests — `TestABlankJoinKeyIsNotAWildcard`, seven

| test | what it pins |
|---|---|
| `test_it_refuses_rather_than_rendering_the_cross_product` | the FAIL |
| `test_the_refusal_names_every_unplaced_record` | every one, not a sample |
| `test_the_refusal_says_a_blank_key_is_not_a_wildcard` | the sentence a reader acts on |
| `test_no_table_is_printed_at_all` | not a short table — nothing |
| `test_a_blank_objective_id_alone_is_enough` | the rule is about the key, not about both sides coinciding |
| `test_the_correct_store_still_renders` | **anti-vacuity** |
| `test_every_kr_is_placed_exactly_once` | the cross product, asserted on a CORRECT store |

Module: **33 tests, all green.**

**Two drafting defects found while writing them, both worth recording.**

1. The refusal lands on **stdout** as `{"refused": …}` under `--json`, not on
   stderr. Assertions over `res.stderr` were reading `""` and passing for
   free. A `refusal()` seam now asserts the non-zero exit and parses stdout.
2. `test_every_kr_is_placed_exactly_once` first checked uniqueness **across**
   versions, where an OKR id is stable by design — `O1-KR1` is in v1 and v2.
   That is the store's property, not a violation. Scoped per version, with an
   assertion that each version placed something.

## 5. Mutations — five, one green and corrected

| # | mutation | result |
|---|---|---|
| M1 | the blank guard removed — the cross product returns | **RED** — 4 tests |
| M2 | the join matches everything in the version | **RED** — 13 tests |
| M3 | the residual stops firing | **RED** — 11 tests |
| M4 | the refusal stops naming `blank` | **GREEN, then RED after the fix below** |
| M5 | the refusal drops the wildcard sentence | **RED** |

**M4's green is the useful one.** The test asserted the word `"blank"`, which
the message contains **twice**, so deleting one occurrence changed nothing it
could see. A test over a word that appears more than once cannot say which
sentence it is holding. Re-asserted on the claim — `"not a wildcard"` and
`"is blank"` as separate checks — and M4 and M5 now redden on their own
sentences.

## 6. Suite

```
130 modules · 3796 tests · 79.8s · 8 workers
✗ 3 of 3796 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.

Worth naming because § 3 touches the same module: those two reds are the
**pre-existing** pair, not the fifteen the `load_okr_store` probe produced.
The probe was reverted before this run and the file is sha256-identical to
`git show HEAD:`.

## 7. What this round leaves open

F-1 is measured and not fixed, and the measurement says why: making the shared
reader validate is a contract change to the published-key surface, which is
the user's call rather than a round's. Nothing else from round 3 is
outstanding — its third finding was graded ROW by the reviewer and stands as a
correction rather than work.
