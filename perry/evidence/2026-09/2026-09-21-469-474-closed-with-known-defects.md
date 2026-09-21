# TASK-469 and TASK-474 — closed with known defects

Date: 2026-09-21. Closed by: Ran Jiao, in session. Recorded by: PMO Agent.

Both rows were closed **at V3, not V4**, and the distinction is the point of this
file. V4 means a fresh reviewer ran against written criteria and passed it. That
was attempted three times on each row and returned **FAIL three times on each**.
The evidence each closure cites is the round-3 FAIL verdict itself, so the board
cannot be read as saying these passed review.

What V3 does cover was run, and is real:

| | TASK-469 | TASK-474 |
|---|---|---|
| Branch suite | 157 modules / 4426 tests green | 157 modules / 4432 tests green |
| Merge result, verified separately | 157 / 4434 green | 157 / 4434 green |
| Mutations | 6 structural, all killed | 7, six killed |

## What is shipped on `main` and known to be broken

**TASK-474 — `bin/perry-goals:4721`.** `splice_header` restores a **trailing**
`\r` only. A break character with content after it on the same `split("\n")`
line is still consumed by `.*$`, so `phase close` deletes the rest of that line,
exits 0, and reports that it flipped one cell. Reproduced on a fixture:
2,618 → 2,610 bytes, the planted trailer gone. Nine of the ten boundaries do
this; the one that survives is CRLF, which is the only case
`tests/test_phase_lifecycle.py` constructs. The named fix, which was not
applied: `viewer/tables.py:294 splice_cell` keeps `line[b:]` and cannot do this.

**TASK-469 — `tests/test_startup_routing.py` `ROUTE_RULES`.** Three of the four
sites carry a positive assertion. The fourth, `reference/config.md § Conditional
consumers`, carries none and rests on a four-string blacklist — the instrument
`USER-974`'s answer refused by name. The prose rule itself is correct at all
four sites; it is the guard that stops at three. The named fix, which was not
applied: an entry in `ROUTE_RULES`, and pinning the flattened rule paragraph
with `assertEqual` on the extraction `test_every_site_states_the_route_rule_at_
the_instruction` already performs.

**No rows were opened for either.** Findings go in the evidence; opening the
follow-ups is the user's decision and was not taken.

## Three claims this session had to retract

Recorded because they bear on how much weight a future reader should give this
session's own reports of its own work. All three were caught by independent
reviewers, none by the author:

1. **A mutant was mislabelled.** Round 2 of TASK-474 reported "F5 gate order
   restored — killed" under a *no survivors* heading. The mutant had replaced
   `if active:` with `if False:` — deleting the gate rather than reordering it.
   It killed on the gate's existence and said nothing about its order, so the
   F5 fix shipped with no regression surface and a "fixed" label for a whole
   round.
2. **Two byte figures were wrong**: a trim was reported as freeing 129 bytes
   when 129 was the shortfall and 238 was freed, and headroom was quoted
   against the looser of two limits (the 20,480 cap rather than the binding
   20,457 no-growth guard).
3. **"Prose cannot be guarded by string tests" was false.** Stated in a result
   file as a property of the medium, and passed to the next reviewer in the
   dispatch. An `assertEqual` on the flattened paragraph holds it, using an
   extraction the author's own test already performed. The real answer was a
   trade-off about brittleness that was never weighed.

## Why the rounds rule did not fit, and why the threshold was not raised

`work/reference/review.md § 6` stops a row after two FAILs on the diagnosis that
it is "failing on a PRINCIPLE nobody has picked". Both rows did that, both asks
were filed (`USER-973`, `USER-974`), both were answered, and round 3 applied the
chosen principle. Both reviewers then stated independently that the rule's
diagnosis no longer described the situation: the principle was picked, was
working, and the remaining findings were ordinary defects with named fixes.

The rule counts FAILs and cannot distinguish *we disagree about what we are
building* from *you missed a spot*. `§ 6` provides the knob for this
(`review_fail_rounds_before_escalation`) and names the condition — work that
converges by accretion, which these did: 4 → 2 → 1 findings on TASK-474,
5 → 2 → 2 on TASK-469.

**The threshold was not raised.** The PMO declined to raise a gate to admit its
own work, and the user closed the rows instead.
