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

## 2026-08-20 — `.perry/agents.jsonl` → `.perry/roles/` moves to `work`

The third ownership change, and the second to carry its own signature.

**What moved.** One row: `work`'s "Only writer of" cell gained
`.perry/agents.jsonl` → `.perry/roles/`. `goals` and `decide` are byte-identical
across the edit.

**Why it needed a signature at all.** `.perry/roles/*.md` was `owner: user` —
deliberately outside every lane's write contract, on the reasoning that a role
card is a declaration the project makes about itself, like `.perry/hook.md`.
DESIGN-007 decision #2 (signed 2026-08-19) made the store the definition and the
card rendered output, which means something renders it, which means a lane
writes it. `tests/test_ownership.py` refused the lane-owned path while this
table did not list it, and it was right to; `schema/state-schema.json`'s own
note said in advance that this was the shape the change would take.

**Why `work` and not `decide`.** The dispatch pre-flight and `delegate` read a
role card on every run, and both are `work` procedures. `work` already renders a
store to markdown (`perry/tasks.jsonl` → `BOARD.md`), so the pattern is the one
it has. Putting the file behind `decide` would have made a read-hot path depend
on a lane that is not loaded when the read happens.

**What it costs, recorded because it was known before the signature and not
after.** A hand edit to a role card is now drift, the same behaviour `BOARD.md`
has had since ADR-007 decision 2. `SKILL.md` lands at 20,457 bytes against a
20,480 cap — 23 bytes of headroom, so the next ownership change forces a trim of
the router before it can be written, and the account above is here rather than
there for that reason. The paragraph under the table still reads "Two changes
from the previous contract"; it describes the 2026-08-16 edit accurately and
gains no mention of this one, so the table alone no longer carries its own
history.
