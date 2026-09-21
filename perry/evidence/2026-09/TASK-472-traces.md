# TASK-472 — the two traces criterion 6 asks for

Date: 2026-09-21. Author: PMO Agent (Claude Opus 5).

Round 1 did not produce these. It shipped a five-bullet incident list under the
name, and the V4 was right that a bounded command trace needs no telemetry.
These are built from the suite logs on disk, not from memory, and every count
below can be re-derived from them.

## Method, and what it cannot show

Each full-suite run on 2026-09-20/21 left a log in this session's scratch
directory. A run is classified by its **last line**, not by searching for a
word: a first attempt that grepped for `MODULE(S) red` classified
`t472-base.log` as green, when its last line is `✗ failures above` — the tree
guard's failure prints no module count. That classifier bug would have put a
contaminated baseline into this table as a clean one.

**This is n = 1 per class, run by the author, who knew it was being measured.**
It is a trace, as the criterion says, and not an experiment. No token figure
appears anywhere below: this host reports Claude's token usage as `unknown`
(USER-972), and the iteration plan forbids substituting anything else for it.

## Trace 1 — a reviewed delivery

**Baseline: TASK-474, rounds 1–3**, delivered before any of these contracts
existed. Every full-suite run it caused:

| Log | Result | Why red |
|---|---|---|
| `t474-baseline` | green | — |
| `t474-full` | **red** | four guards caught four real defects in this session's code |
| `t474-final` | **red** | six unregistered write sites — a real defect |
| `t474-final2` | green | — |
| `t474-merge` | green | merge-result verification |
| `t474r2` | green | — |
| `t474r2-merge` | green | merge-result verification |
| `t474r3` | green | — |
| `r3-merge` | **red** | **TASK-272 flake** (shared with TASK-469's merge) |
| `r3-merge2` | green | re-run to obtain the merge claim after the flake |

**10 full-suite runs. 3 red. Two of the three are the suite doing its job** —
catching defects that then got fixed — and are not waste by any definition.
**One run, `r3-merge2`, exists only because of a flake.**

**After: TASK-472 round 2 (this round).** Recorded as it happened, in
`perry-scratch-derivation`'s directory:

| Step | Runs |
|---|---|
| Re-pin a span digest after a prose edit | 1 targeted module (`test_spec_scannability`, 71 tests, 4.4 s) — no full suite |
| Final verification | *(appended when run)* |
| Merge-result verification | *(appended when run)* |

## Trace 2 — a small change

**Baseline**: across 2026-09-20, small prose edits in this session were already
followed by a targeted module before any full suite — e.g. TASK-469 round 3's
budget move ran `test_startup_routing` and `test_context_budget` (61 tests)
first. **After**: the digest re-pin above, one targeted module.

**There is no meaningful difference between these two**, and saying so is the
point of recording it.

## What the comparison actually shows

**Criterion 6's flake rule saves zero full-suite runs on either delivery.** Both
flakes on 2026-09-20 (`t469-merge` → `t469-merge2`, `r3-merge` → `r3-merge2`)
were handled exactly as the new rule prescribes: the module re-run alone three
times, then the full suite once. The rule writes down what was already done.
Its value, if it has any, is stopping a *later* agent from re-running more than
once — which a trace of an agent that did not do so cannot demonstrate.

**The waste these contracts target is real, but it is not in these two
traces.** It sits in places this method does not reach, and each is counted
once and attributed:

- **Criterion 2, lost output** — in a *reviewer's* round, not this author's:
  TASK-469 round 2's V4 harness discarded failing output and needed three
  isolated re-runs to recover two mutants. Its own review records it.
- **Criterion 3, `&`** — `t472-merge.log` has no totals because this session
  launched it with a bare `&`, **after writing the contract that forbids it**,
  then stopped it by pid and re-ran it tracked as `t472-merge2`. One whole
  partial run, caused by the author of the rule, minutes after writing it.
- **Criterion 1, shared scratch** — the directory these logs were read from
  also holds `full.log`, `slow.log`, `affected-review*.log`, `r2rev-*.log`,
  `mutate.log`, `whyred*.log` and `affected*.log`, **written by the review
  agents**. Reviewers and author shared one scratch directory for two days. It
  was noticed only while assembling this table.
- **Criterion 4, base without criteria** — TASK-469 round 2's verdict carried
  `citation-not-on-branch` on every exhibit. Its review records it.

## Verdict on the evidence

The contracts are grounded in real incidents, and four of the six have one on
record. Whether they *reduce* cost is not shown here: the one contract that
bears on full-suite count codifies behaviour that was already happening, and
the incidents the others address are single occurrences. A reviewer asking
"does this row make reviews cheaper?" should get the answer this file supports:
**not demonstrably, on this evidence.**

## Round 2's own trace

Recorded as it happened (`$PERRY_SCRATCH/trace.md`), not rebuilt afterwards.

| Step | Suite runs | Reason |
|---|---|---|
| Re-pin the constraints span | 1 module (`test_spec_scannability`) | targeted; no full run needed |
| Build this file from logs | none | reads only |
| M1–M5 mutations | 1 module each | targeted |
| Branch gate | **1 full** — 157 / 4434 green, 108.2 s | new changes; the one justified run |

One slip: the result file was edited in this tree while that run was in
flight — the failure the tree guard caught in round 1. The guard passed, most
likely because its final check ran before the write landed. The full run on
the merge result covers the final content, so no extra run was spent on it.
