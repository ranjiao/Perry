# TASK-285 — round 7 result

> Status: implemented and measured; **not reviewed**.
> Executor: the PMO session, inline, on `main`'s working tree.
> Rung: undecided. See § 4 — this is the round's one open question and it is
> the user's, not this document's.

Round 6 was dispatched 2026-09-04 and its agent was killed by a session rate
limit with only a stub committed. Nothing was salvaged. This round implements
the repair the **round-5 reviewer** specified and verifies it with the control
that reviewer named.

## 1. The defect round 5 was failed on

`test_every_mention_of_the_rule_is_inside_a_governed_region` keyed a line by
its **content**:

```python
spans.append((path, set(src[a:b].splitlines())))
inside = any(p == path and line in lines for p, lines in spans)
```

`src[a:b]` includes the **declared-free rationale block**, which `USER-914`
makes legal, unpinned and green to edit. So the free zone was a
**line-injection oracle**: write the retraction once inside it, and the
identical sentence becomes a legal member of the span's line set anywhere else
in the same file — no re-pin, no test change, whole suite green.

## 2. The repair

Gate on **where the line is**, not on what it says. A line number cannot be
injected.

```python
spans.append((path, src[:a].count("\n") + 1, src[:b].count("\n") + 1))
inside = any(p == path and lo <= n < hi for p, lo, hi in spans)
```

Two lines of mechanism. The comment above `spans.append` and the docstring
paragraph that claimed line-set membership were rewritten to say what the code
now does; leaving either would have been the third round in a row where the
prose and the mechanism disagreed.

## 3. Measurement, and the negative control

`work/reference/dispatch.md` was pinned at
`74d6c0e43db746cc8898eb44e53cf274a5c1f1c08dffc63c01ec8f1115936767` before the
first plant and restored to that digest after every one; `git status` on
`work/reference/` is empty. The retraction planted is one naturally wrapped,
full-length line carrying both keywords, placed three lines above
`## The tree the agent works in` — outside every span.

| | positional (this round) | content-keyed (round 5) |
|---|---|---|
| BASELINE, unmodified tree, 13 tests | GREEN | GREEN |
| **X2** retraction + a copy in the free block | **RED** `dispatch.md:173` | **GREEN** |
| X2b retraction alone | RED `dispatch.md:173` | RED `dispatch.md:173` |
| REMEDY innocent mention inside the free block only | GREEN | GREEN |

**The right-hand column is the control and it is the point.** Reverting the two
mechanism lines to round 5's form takes X2 back to GREEN and leaves X2b RED, so
the positional gate is what closes the oracle and nothing else in this round is
doing that work. The `Over-fires:` paragraph's remedy — *"green inside the free
rationale block"* — survives, which the content-keyed alternative would have
destroyed.

`tests/test_spec_scannability.py` alone: 64 tests, OK.

Full suite: **3 of 3,665 failed, in 2 modules** —
`test_contract_key_parity` (2) and `test_resume` (1). Both reproduce when run
alone, so neither is order-dependent, and both are pre-existing: the failing
key is `conformance.in_progress_with_no_live_run[].means`, which is observable
because `TASK-285` and `TASK-436` are `in_progress`, and those two rows are
**byte-identical between `HEAD` and this working tree**. `test_spec_scannability`
is green in the suite run and alone.

## 4. The rung, unresolved

`ADR-020`'s gate asks whether the row touched a write path or
`schema/state-schema.json`. It touched `tests/test_spec_scannability.py` and
this row's spec. The answer is **no**, which puts it at **V2**.

Against that, `review.md § 0` says *"a test that is **wrong** — green while the
code is broken — is a product finding wearing a test's clothes and does go to
V4"*, and this guard was green with the repository's own isolation rule
retracted, five rounds running. It also says **when the answer is genuinely
unclear, run it**.

And `perry-lint --reviews` reports `review-rounds-exhausted` on this row: it has
FAILed its counted rounds and never PASSed, and the page's own instruction is
that another round is not the next step — file the ask, name the readings, let
the user choose.

So this round does not pick. The readings are:

- **V2** — `ADR-020`'s gate is a rule, it answers cleanly, and the whole point
  of the rule is that the session does not re-litigate the rung per row.
- **V4** — the row is the named exception, and a guard that has been wrong five
  times is the last place to spend the round that was saved.
- **Neither, yet** — `review-rounds-exhausted` says a row failing this many
  times is failing on a principle nobody has picked, and the ask comes before
  any further round.

## 5. Declared limits, now in the spec's `## Bound` rather than only here

- **Zone 5, open**: the vocabulary is matched with a plain regex over text that
  has only HTML comments stripped — no emphasis, no entities, no Unicode
  normalisation. A homoglyph or entity spelling is outside reach. Round 5's
  `X3`.
- **Zone 6, latent**: the sweep is `glob("*.md")`, not `rglob`, so a
  subdirectory of `work/reference/` is unseen. Harmless today — that directory
  is flat, 15 files — and live the day someone adds one. Round 5's `X6`.
