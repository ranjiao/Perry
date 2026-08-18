# The hand-off contract — what changed, and why it needed no second signature

Tier 1. Loaded on demand from `SKILL.md § The hand-off contract (the most
important rule)`.

**The signed section stayed in the router.** Its V5 sign-off line, the
invariant, the ownership table and the refusal cases are all still in
`SKILL.md`; what moved here on 2026-08-18 (TASK-064) is the change history
around them. The ownership set the signature was given against is
byte-identical before and after the move, which is the same test the section
itself applies to its own earlier edit below.

**Two changes from the previous contract, and why.**

1. **`DECISIONS.md` + `decisions/` move from `work` to `decide`.** A settled
   decision and the document that settles it now have one owner. `work` was
   the largest lane and the record of *what was decided* sat one lane away from
   the RFCs that decided it, which is where "where do I record this?" became
   ambiguous.
2. **`OKR.md § Commitments` is explicitly `goals`.** Pipeline- and queue-mode
   tracks put their spine there (`modes/pipeline.md`, `modes/queue.md`) and
   both disclaim the objectives→KRs cascade — which read as though they owned
   the section. They do not. A commitment to a named party *is* a goal; a KR is
   the special case where the party is the project itself, so the two live in
   one file under one writer. Settled 2026-08-16 after an independent review
   found the section written by two modes and claimed by no lane.

**The lane names and the directories now agree.** They did not when this
section was signed: the contract stated target names beside their then-current
directories (`goals` (today `okr/`), …) precisely so it would never name a
directory that did not exist — the defect `reference/user-load.md` forbids.
TASK-027 landed the rename, and the parentheticals were collapsed as that
section itself instructed.

**Why this edit did not need a second signature.** What was signed is the
ownership set — which lane may write which files — and that is byte-identical
before and after. The edit removed a scaffold the contract carried for one
release and put in writing that the scaffold's job is done. An edit that
*changed* an ownership row would need a fresh V5, and this one is recorded here
rather than silently applied so the distinction stays visible.

## Why one rule keeps the lane set composable

This single rule is what keeps the set composable and lets you drop in a fifth
lane later (e.g. `research-journal`, `risk-review`) without breakage — a new
lane is a directory with a `SKILL.md`, a row in the table above, and an entry in
the routing reference.
