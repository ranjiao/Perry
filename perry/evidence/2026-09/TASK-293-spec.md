# TASK-293 — spec

> Source: the 2026-09-02 design-register audit (28 documents, 7,404 lines, 19 findings)
> Dispatch mode: manual — **the gate refused, CORRECTLY, and the user is the escalation it demands.**
> Executor: claude-subagent, run through `delegate` rather than auto-dispatch.
>
> `perry-state --escalation-scan` returns `verdict: refuse`, `refuse: ['design/']`.
> **Unlike `TASK-263` and `TASK-099`, this refusal is not a false positive.**
> Those two named a path they merely cited; this row genuinely writes into
> `design/`, and `.perry/hook.md` lists it because that directory holds the
> decision records. An agent editing locked design documents unsupervised is
> exactly what the fragment is there to stop.
>
> The spec was **not** reworded to pass. What satisfies the gate is the thing
> the gate is for: the refusal escalates to the user, and the user authorised
> this work explicitly on 2026-09-02 after reading the audit and the plan,
> choosing to run the eleven mechanical items as a subagent. That authorisation
> is recorded here so the run is auditable, and it covers **these eleven edits
> only** — the eight findings under "Out of scope" were withheld from it on
> purpose.
> Estimated cycle: medium
> Subjective verification: whether each Changes entry says the right thing — a human reads them
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## The one rule that governs every edit here

**Every document in scope is `locked`.** `decide/SKILL.md § Status model`: after
lock a doc is frozen except for `## Changes` entries; structural pivots need
`revise` or `supersede`. So exactly two edit shapes are permitted:

1. a `> Revisits: <file> § <section>` line in the **header block** of the newer
   document — the existing convention, present on 7 of 15 designs today; and
2. a `## Changes` entry, `YYYY-MM-DD — <what> — <why>`, appended to the older
   document.

**Do not rewrite locked body text.** Where a body sentence is now false, the
`## Changes` entry says so and quotes it; the sentence stays. That is the whole
point of an append-only record.

Designs are tier 2 with **no line cap** (`schema/state-schema.json § files[]`,
id `design`), so length is not a constraint here.

## Files in scope

`perry/design/` and `perry/decisions/` only:

- `DESIGN-001-resumable-pipelines.md`
- `DESIGN-004-deterministic-writes.md`
- `DESIGN-005-state-and-contracts.md`
- `DESIGN-006-*.md`
- `DESIGN-007-the-entity-model.md`
- `DESIGN-010-autopilot-writes-its-own-specs.md`
- `DESIGN-014-how-much-python.md`
- `DESIGN-015-linkage-is-a-store.md`
- `decisions/ADR-007-*.md`

## The eleven edits

### C-01 · DESIGN-010 ↔ DESIGN-007 §5.7 — a spec is required at creation, and is also written at dispatch

`DESIGN-007` decision 5 takes the strict line: no exemption, no flag, the
refusal is at creation. `DESIGN-010`, locked nine days later, is built on the
opposite pattern and calls it correct — the PMO writes a spec **at dispatch**.
Its §1 measurement (32 of 36 open rows with no spec) is only possible in a
world where decision 5 was never enforced. DESIGN-010 does not cite DESIGN-007
anywhere, including References.

**The reconciliation already exists and neither document points at it**:
`DESIGN-007 § 5.9` makes the spec per-Run, rewritten rather than edited, so a
re-verified spec at dispatch is a **second spec on run 2**, not a violation.

Edit: `> Revisits:` on DESIGN-010 naming DESIGN-007 § 5.7; `## Changes` on
DESIGN-007 naming DESIGN-010 and § 5.9 as the reconciliation.

### C-02 · DESIGN-007 #2 ↔ DESIGN-006 §5.2/§5.5 — the role card is the definition, and is also rendered output

DESIGN-006 decision 2 puts role cards in `.perry/roles/` **because they are
tier-1 and user-owned**; its §5.5 lists that under "Unchanged, deliberately".
DESIGN-007 decision 2 reverses it — "the store is the definition, the card is
rendered output" — and names the cost. DESIGN-006 §9 still holds a single
2026-08-17 entry, so a reader landing on the document that *defines* the role
card is told the opposite of the current decision.

Edit: `> Revisits:` on DESIGN-007; `## Changes` on DESIGN-006.

### C-04 · DESIGN-004 §2 goal 6 and §3 Non-Goal still promise the deleted architecture

DESIGN-004 was corrected in §5.1 and §5.3 but not in §2/§3, which is where a
reader looks for what the design commits to. Goal 6 — *"The markdown stays
canonical and human-editable… the tool is a better path, never the only path"*
— and the Non-Goal *"Not a database. Markdown remains the source of truth."*

Three active decisions overrule them: ADR-007 decision 2 (a hand edit is
drift), ADR-010 (the artifact is removed), DESIGN-013 §5.1 (a fact with a
schema lives in exactly one store).

Edit: `## Changes` on DESIGN-004 quoting both sentences and naming all three.
**Leave the sentences in place.**

### P-02 · DESIGN-001 — which half still has a caller

DESIGN-001 exists for `/perry adopt` **and** `/perry diagnose`; its contract,
its `declarations[]`, its interrupted-run card and its user decision 4 are all
reasoned from having two. Its 2026-09-02 `## Changes` entry re-verified the
machinery thoroughly against artifacts and recorded nothing about adoption no
longer running — true of the mechanism, beside the point for half the subject.

Edit: one `## Changes` line on DESIGN-001 saying which half has a caller.
**Verify before writing which half that is** — measure, do not inherit this
spec's framing.

### P-03 · DESIGN-014 decision 3 — the objection is stated and not answered

Decision 3 states the objection sharply: *"`perry-diagnose` is not adoption and
does not depend on the deleted migrator. But USER-910 answered that Perry is
never pointed at a foreign project, and `diagnose`'s whole subject is a folder
that is not yet Perry-shaped."* §5.1's justification answers a different
question — category, not whether the folder exists.

Edit: `## Changes` on DESIGN-014 marking it **unanswered**. Do not invent an
answer; DESIGN-014's own §2 goal 2 requires one and this is the row where it
was not supplied.

### D-01 · DESIGN-014 goal 1 is not met by DESIGN-014

Goal 1: *"Every tool in `bin/` and `viewer/` is placed in exactly one of three
categories — with the reason stated per tool."* §5.1 leaves these unplaced:
`bin/perry-okr`, `bin/perry-config`, `bin/perry-codex-preflight`,
`bin/perry-detect-host`, `bin/perry-update-check`, `viewer/tables.py`. Plus
`bin/perry-goals` at 3,380 lines, of which only `perry-goals link` is
categorized — the same "part of" admission §6 step 1 makes about `perry-task`
and `perry-lint`, not extended to it.

Edit: `## Changes` on DESIGN-014. **Re-derive the unplaced list yourself** and
report your count; do not copy this one.

### D-02 · DESIGN-014's 10:1 headline counts the test suite as product

§1 opens with 97,474 lines of Python against 9,810 of prose, "10:1". That
97,474 is `bin/` + `viewer/` + `tests/`. The document then argues against its
own framing twice: §3's first Non-Goal ("Not a line-count target") and §8's
second open question, which uses the correct denominator.

Measured 2026-09-02: `bin/` 36,371 · `viewer/` 4,993 · `tests/` 64,501.
**Re-measure and state your instrument.** The §5.1 conclusion survives on the
real number; the headline does not need the test suite to be true.

Edit: `## Changes` on DESIGN-014 with the corrected ratio.

### D-03 · DESIGN-015 says "five stores" where there are six

Three places say five: goal 4 ("as it does for the other five stores"), §5.1
("beside the five stores already there") and the §7 risk row. `perry-lint`
prints **six** store lines — tasks, risks, intake, ask, OKR, config. §5.1 is
therefore self-contradictory: a *seventh* store beside *five*.

This matters because **goal 4 is written as a checkable acceptance criterion**,
and one naming the wrong count is checked against the wrong thing.

Edit: `## Changes` on DESIGN-015 correcting the count and naming all three
sites. Confirm the six by running `perry-lint` yourself.

### D-04 · DESIGN-004 and DESIGN-005 are dated after they were locked

`DESIGN-004  Date: 2026-08-18 · Locked: 2026-08-16`
`DESIGN-005  Date: 2026-08-18 · Locked: 2026-08-17`

Both were correctly edited after lock (they carry the ADR-006 corrections), but
the `Date:` field moved with the edit, and the header is not a `## Changes`
entry. These two are the documents whose history is most cited — ADR-006,
DESIGN-013 and DESIGN-014 all reason from *when* a claim in them became false.

Edit: **derive each document's real authoring date from `git log --follow`**,
show the evidence, restore `Date:`, and record the correction in `## Changes`.
If git cannot settle it, say so and leave the field alone rather than guessing.

### D-05a · DESIGN-007 §5.3 names a file that does not exist

The table at `DESIGN-007:433` reads `| Goal + KR | perry/goals.jsonl |`. The
file, and the `claims[]` entry, are `perry/okr.jsonl`. DESIGN-009's References
carry the correction — which puts a footnote in one document where a `## Changes`
entry belongs in another.

Edit: `## Changes` on DESIGN-007.

### D-05b · ADR-007's header describes a defect that is fixed

ADR-007's header is a five-paragraph account of `perry-decide` hardcoding
`STATUSES` with no word for "drafted, awaiting a decision". That is fixed:
`decision_status` is a schema enum, it includes `proposed`, and `bin/perry-decide`
refuses to fall back to its own copy. The header still describes it as live.

Edit: a `## Status change`-style note in the ADR body recording that the defect
its header narrates was fixed and where. **Confirm the fix yourself** before
writing it.

## Out of scope — these need a DECISION and are going to the user separately

Do not touch, and do not "fix in passing":

- **G-01** — ADR-010 is `active`, titled "BOARD.md stops existing", and the file
  exists at 85,611 bytes while its own gate never ran.
- **G-04** — ADR-013's high-water mark lives in a file declared disposable.
- **C-03** — the two-level KR id grammar; the repository sided with DESIGN-009
  without recording the reversal.
- **C-05** — "zero new claimed paths" (DESIGN-003/004 goal 5), silently retired.
- **P-01 / G-03** — the V4 boundary, and the projection-newer direction.
- **P-04** — lives in `perry/OKR.md`, which is the **goals** lane's file.
- **L-01** — `perry-lint`'s NS-01 firing on Perry's own files: a code row.

## Verification

- Each of the eleven exists as a named entry in the named document, in one of
  the two permitted shapes.
- **Every number and path you write reproduces.** You re-derive D-01's unplaced
  list, D-02's line counts, D-03's six stores, D-04's dates and D-05a/b's
  claims; report each instrument. A Changes entry carrying a number nobody
  re-measured is the defect this audit is about.
- `git diff` shows **no change to any locked body text** — only header
  `> Revisits:` lines, `## Changes` / `## Status change` additions, and
  D-04's two `Date:` fields.
- `python3 bin/perry-lint --root .` stays at 0 errors.
- `python3 bin/perry-decide list` still parses every ADR.
- No file under `perry/OKR.md`, `perry/phase/`, `perry/BOARD.md`,
  `perry/journal/` or `perry/tasks.jsonl` is touched — those belong to other
  lanes.

## Bound

**Eleven edits across nine documents.** Size 11, enumerated above by finding id:
C-01, C-02, C-04, P-02, P-03, D-01, D-02, D-03, D-04, D-05a, D-05b.

The round ends when those eleven are written. **A twelfth finding you notice is
a new row**, recorded and left — not an extension. The audit's other eight are
listed under "Out of scope" precisely so this round can end.
