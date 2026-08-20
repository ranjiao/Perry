# TASK-150 / TASK-151 / TASK-152 — result

> Date: 2026-08-21 · Executor: claude-subagent · Merged locally
> Branch: `coding/task-150-live-state-instances` · Cycle time: ~55 min
> 5 test files, +343/−65. **No new fixture files** — all three fixtures are
> written by the tests themselves.
> **The floor: 7 → 4, all four false positives, nothing silenced.**

## Each repair kept the property and moved the guard

**TASK-150.** `assertGreater(len(krs), 20)` is gone. The live test keeps its
independent-count property; the guard became
`TestTheScannerReadsAnOkrToItsLastLine`, which **generates** an OKR (3 versions ×
3 objectives × 3 table KRs + 4 bullet KRs = 39) and asserts the roster comes back
**in file order** — *a list, not a count, so an early stop returns a prefix and
the failure names the id it stopped at.* It also pins that the **final** version
block contributes both KR forms, because a scanner that read every table and no
bullet would still return a long list.

**TASK-151.** The round-trip is now quantified over whatever the live board holds
and asserts nothing about how much. The not-empty guard moved to a seven-row
constant carrying the shapes the format actually produces — an empty cell, the
`—` marker, **an escaped `\|`**, CJK, a long cell — plus a `## Done this period`
row that must **not** appear, so *"the reader found nothing"* and *"the reader
started returning unprioritised rows"* are **different reds rather than one
silence**.

**TASK-152, and its invisible half.** The neighbour is now its own test. Both
build `ctx` from a two-record store written to a tmpdir and loaded through the
real `load_task_records`, so the reader under test is still the shipped one. The
neighbour asserts both routes into `known` — the families `perry-task` declares
in its own source, and the prefixes read out of the store it is handed — and its
docstring says plainly why the sweep never flagged it (`[]` is not closed) and
that it was **one id family leaving Perry's board away from failing.**

## Item 2 is the best thing in this row

With no instances left, *"every entry is a false positive"* and *"the guard has
gone blind"* **produce the same floor.** The agent did not paper over that:

> the floor alone can no longer tell them apart — so the test does not pretend it
> can.

The discrimination claim **moved to where the instances are permanent**: the
three modules reconstructed out of git, each of which must still be flagged. That
deliberately duplicates another class, and the docstring says why — *"the claim
being made here is 'this floor is empty of instances AND the guard still finds
them', and half a claim checked in another class is a claim nothing checks."*

Proved failable three ways, and **the third is the one that matters**: removing
`"set"` from `PURE_CTORS` leaves the live floor at exactly 4 all-false-positive
while making the sweep walk past a reconstructed module — **red only on the new
half. Under the old assertion it would have passed silently.**

It also corrected the module docstring paragraph that this row's outcome
falsified, and flagged doing so, since the spec had scoped that file narrowly.

## Item 3 — four mutations, four different reds, none overlapping

| mutation | red |
|---|---|
| `scan_okr`: `sites = sites[:20]` | TASK-150 only |
| `render_row`: drop the pipe escape | TASK-151 only |
| `idish_tokens…`: add `"ROUND"` to `known` | TASK-152 only |
| `idish_tokens…`: remove `"ADR"` from `known` | the neighbour only |
| *(extra)* `known = set()` instead of the store-derived set | the neighbour only |

M2 was chosen deliberately: **Perry's live board contains no escaped pipe**, so
it breaks a row shape that exists *only* in the fixture — *"the separation is
structural, not luck."*

## The floor, final

Four entries, every verdict and reason **preserved by `--record`**. Line numbers
moved (296→405 and so on) purely because the new class sits above them; the sweep
keys findings without the line number, so all four carried. **The sweep found no
new hits — nothing had to be judged, and nothing was silenced to reach 4.**

## One question handed back

`bin/perry-task § idish_tokens_that_resolve_nowhere` hard-codes its citation
families in the tool's own source. That is code, so correctly outside the guard's
class — but **a project declaring a family Perry has not heard of gets advisory
noise on every legitimate citation of it.** Noted because TASK-152's neighbour is
now the test that would notice if it moved.

## Merged

`--no-ff`, after `merge-check` attributed the one red to the base and nobody.
