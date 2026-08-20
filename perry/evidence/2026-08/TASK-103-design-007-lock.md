# TASK-103 — DESIGN-007 locked at V5

**Design**: `perry/design/DESIGN-007-the-entity-model.md`. **Rung**: V5.
**Signed off**: Ran Jiao, 2026-08-19 — the signature block is in the doc's own
header, not here, so a reader of the design never has to find this file to know
it was signed.

## The row's own acceptance criteria, run

The task's `verification` cell stated two mechanical conditions. Both were
checked before the lock, not asserted:

| Condition | Result |
|---|---|
| every row of `## 4 User Decisions` carries a Chosen value and a date | **10 of 10**, 0 unresolved |
| no field marked `**new.**` in § 5.2 is unscheduled by § 6 | **4 fields** (`id`, `phase`, `serves`, `supervised_by`), **0 unscheduled** |

Checked by parsing the document rather than by reading it, because "every row"
and "no field" are claims a scan answers and an eye does not.

## What the lock changes

`decide/SKILL.md` states the lane's rule: *"refuses to mark a doc Design locked
unless the User Decisions section is fully resolved — it would rather show an
open question than write fiction."* That gate is now satisfied by measurement.

The document is **append-only from here**: further edits go in `## 9 Changes`,
and a structural change needs `revise` or `supersede`. Ten answered decisions
are what the twelve implementation steps are ordered against.

## The second V5 this document schedules

Step 2 of § 6 is **another human gate**, and it is worth naming here so it is
not discovered later: decision #2 makes a lane the writer of `.perry/roles/*.md`,
which moves an ownership row in `SKILL.md § The hand-off contract`. That table
carries a signature and `tests/test_ownership.py` refuses a lane-owned path the
signed contract does not list. **No Agent work starts before that signature
exists** — steps 3, 4 and 12 all sit behind it.

## What this evidence does not claim

The § 1 and § 5.8 measurements were **not independently re-run** as part of the
sign-off; they are the author's, and each names the file and count it came from
so a later round can. And § 5.8's recommendation — not to reset Perry's own
history, against an explicit authorisation to do so — **was not accepted or
rejected in words**, and the signature reads it as left in force. That
inference is stated in the doc's header rather than buried here, because a V5
that quietly infers is the failure mode the rung exists to prevent.
