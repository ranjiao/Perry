# TASK-285 — round 5, V4 review

> **Checkout**: isolated worktree `.claude/worktrees/agent-ab537c23477b52f8e`,
> on `review/task-285-round5-v4-fresh`, cut from `main` **by ref** at
> `dda8d5f`. The worktree's own HEAD was an unrelated older commit
> (`d49964e`), so round 5 and its predecessors existed only on `main`; `main`
> was never checked out, switched, merged into or pushed. No push, no PR.
>
> **Base pinned once**, per the standing correction:
> `BASE = merge-base HEAD main = dda8d5f8da369e831bcc52895783c29abf405eab`.
> Every restore in every battery is a byte copy from pristine extracts taken
> from **that sha** — never from `main`, which moves — and every restore is
> asserted to return the file's sha256 to its pre-mutation value. All four
> files in scope were confirmed byte-identical to `BASE` before the first
> plant.
>
> Every plant is anchored **by line number AND by an assertion on the old text
> at that line**; a miss aborts loudly rather than no-opping.
> Between plant and run: `find . -name __pycache__ -prune -exec rm -rf {} +`
> and `sleep 1.15`, past the whole-second boundary. Scoring is by
> **differencing the failing-test set against baseline**, never pass/fail.
> Harness: `scratchpad/w285r5/mut.py`, batteries `bA.py`, `bA2.py`, `bB.py`,
> `bC.py`, `bX2suite.py`; digests recomputed independently in `digests.py`.

Criteria: `TASK-285-spec.md` (`## Deliverable`, `## Verification`, `## Bound`,
`## Out of scope`), `TASK-285-round5-result.md`, and all three prior V4
verdicts — `-round2-`, `-round3-`, `-round4-`, read in full before scoring.

---

## Verdict in one line

**FAIL.** The one-line fix is correct and it does what round 4's review asked:
the three exact-mechanism cases are red, the natural-wrap control is still red,
the four declared greens are still green, and the round's two corrections to
the record are substantially right. The round fails on **the same category for
the fourth consecutive time**, one variant out: a retraction that **uses both
keywords**, written on a **naturally wrapped full-length line**, placed
**outside every governed span, four lines above the rule's own heading** in the
file this row designates as the rule's single home, is **GREEN** — including
against the whole suite — provided the identical sentence is also written once
inside the **declared-free rationale block**, which is a legal, unpinned,
green edit by `USER-914`.

The containment check keys on a line's **content**, not its **position**:
`inside = any(p == path and line in lines …)` where `lines = set(span.splitlines())`.
The free block is *inside* `span[a:b]`. So the free zone is a **line-injection
oracle**: anything written there becomes a legal member of the span's line set
and may then be repeated anywhere else in the same file for free.

The control isolates it exactly. The same retraction above the rule **without**
the free-block copy is RED (`X2b`); **with** it, GREEN (`X2`). The legal edit
licenses the illegal one, in the same commit, with no re-pin.

That also falsifies the round's own stated cost model. The spec's new
`## Bound` says an innocent or retracting mention *"anywhere else costs one
deliberate re-pin, which is the friction this rule is meant to carry."* It
costs no re-pin at all — it costs one copy into the zone the same paragraph
names as the free remedy.

---

## Criteria

*(filled in below — see the battery sections)*
