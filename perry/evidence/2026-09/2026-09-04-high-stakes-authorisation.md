# High-stakes authorisation — TASK-276 and TASK-346, 2026-09-04

> Granted by Ran Jiao, in these words: **「task 276 346可以放行」**.
> Recorded by the `work` lane. Scoped to these two rows at the deliverables
> described below. **Not a standing permission**, and not transferable to a
> later round of either row whose scope has changed.

## Why this record exists at all

This is the **first** high-stakes dispatch decided under the procedure that
replaced `bin/perry-state --escalation-scan`. `USER-916` deleted that scanner on
2026-09-04 because Python must not judge a document's meaning; `TASK-339`
removed it and wrote the judgement into `work/reference/dispatch.md`.

So the refusal was mine, reached by reading the two specs against
`.perry/hook.md § High-stakes operations`, and it is written down here because a
judgement nobody can inspect is worse than a scanner nobody can fix.

## The judgement, per row

**TASK-276 — REFUSED without authorisation.** Its deliverable declares
`linkage.jsonl` in `schema/state-schema.json § claims[]`. The hook names the
claim surface — `claims`, `state-schema.json` — and this row **writes** it. It
is DOING, not naming: the file is in `## Files in scope` and the change is the
deliverable itself, not a citation of one.

**TASK-346 — REFUSED without authorisation.** It edits `.perry/hook.md`, which
is Tier 1 and whose own header says *"Owned by you, not by Perry"*, and
`work/state/hook_TEMPLATE.md`, which ships to every project Perry adopts.
`dispatch.md § 4.5` — the standing entry TASK-339 wrote — refuses a round that
rewrites or widens the gate constraining it, and this row edits the gate's own
prose. **TASK-339's round declined to touch these files for exactly this reason
and said so**, which is why the row exists rather than the fix having been made
quietly at the time.

## What is authorised, and what is not

| | Authorised | NOT authorised |
|---|---|---|
| **TASK-276** | Adding a `linkage.jsonl` claim and its three record schemas | Changing any existing claim's path or owner |
| **TASK-346** | The sentence describing **who reads** the high-stakes list | Any change to **what is on** the list — the fragments are the user's |

TASK-346's fragment list must come out byte-identical. That is a verification
item on the row, not a hope.

## The rows this unblocks

TASK-276 is the head of `DESIGN-015`: **276 → 277 → 278 → 279 → 281**, and
TASK-281 is what turns phase KR `P003-O3-KR2` from a number somebody typed into
a number something counted. That is why this row was the one worth asking about.
