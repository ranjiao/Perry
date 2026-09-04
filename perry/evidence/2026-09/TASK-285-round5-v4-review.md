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

Criteria: `TASK-285-spec.md` (`## Deliverable`, `## Verification`, `## Bound`,
`## Out of scope`), `TASK-285-round5-result.md`, and the three prior V4
verdicts — `TASK-285-round2-v4-review.md`, `-round3-`, `-round4-`.

---

STUB — batteries in progress.
