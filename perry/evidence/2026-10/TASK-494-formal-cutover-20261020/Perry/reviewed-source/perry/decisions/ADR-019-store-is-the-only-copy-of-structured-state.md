# ADR-019 — Structured state lives only in the store; the projected markdown files stop existing

> Status: active
> Type: Architecture
> Date: 2026-09-08
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

`ADR-007` made JSONL stores canonical and rendered markdown a projection of
them. `DESIGN-013` stated the rule that follows from it — *a fact with a schema
lives in the store; a document holds what has none*. Neither said what happens
to a document that is **entirely** schema, and two of them are.

**Measured 2026-09-08, on `104873da`.**

`.perry/config.md` — nothing reads it as truth. Of 100 mentions in `bin/` and
`viewer/`, exactly 11 touch the file, in four groups:

| Group | Sites | What they do |
|---|---|---|
| store-first, markdown fallback | 5 | `perry-task:8161`, `perry-context-budget:135`, `perry-lint:2601`, `viewer/parsers.py:371`, `perry-state:1169` — read `.perry/config.jsonl`, reach the markdown only when there is no store |
| existence test | 2 | `perry-goals:2354`, `viewer/parsers.py:405` — "is this project configured", satisfied by either file |
| drift comparison | 3 | `perry-state:191`, `:995`, `:1065` — read the markdown **in order to** compare it to the store |
| projection definition | 1 | `perry_md_store.py:819`, `CONFIG = Doc(...)` |

`phase/<NNN>-linkage.md` — 91 lines, of which **61 are YAML frontmatter and 30
are prose**. The frontmatter is duplicated in `linkage.jsonl` record for
record: 6 KRs against 6 `kr`, the `tasks:` arrays against 18 `edge`, and an
`unlinked:` array of **100 ids against 100 `unlinked` records**.

The linkage document already declares this ADR's rule in its own header —
*"Both Perry and the frontend read the frontmatter above — this body is
documentation, never a second source of truth"* — and the boundary did not
hold. Its 30-line prose body carries four claims that are false today:

1. *"`current` is absent on every KR above"* — four of six carry one.
2. *"`P003-O3-KR1` drives that number to zero"* — that KR was withdrawn 2026-08-31.
3. *"`TASK-099` and `TASK-050` under `P003-O2-KR2`"* — that KR was withdrawn 2026-09-02.
4. *"`TASK-199` under `P003-O2-KR3`"* — `TASK-199` was dropped and re-scoped into `TASK-262`.

All four rot the same way: nothing checks prose. A declared boundary inside one
file is not a boundary.

**The cost is not tidiness.** Drift can only exist where there is overlap.
`perry-lint` today reports `linkage store: 124 record(s), 1 row(s) drifted`,
and the drifted row is `P003-O3-KR2` — this phase's own computed KR, disagreeing
between the store and the document. `TASK-155` is the same shape one layer
down: `phase/<NNN>-linkage.md`'s `updated:` frontmatter field feeds
`declared_at` on 115 linkage records (`bin/perry-tasks:1612`) **and**
`current_provenance.asserted_at` on every KR (`bin/lib/__init__.py:1066`), so
recording one fresh measurement re-dates 115 records and marks four asserted
numbers fresh. That defect exists because a document header is timestamping
store records.

Five open rows are each one instance of this: `TASK-155`, `TASK-236` (`OKR.md`
drops its KR tables), `TASK-237` (`BOARD.md` stops existing), `TASK-280`
(`phase/<NNN>-linkage.md` sheds its schema'd half), and the config question
above. They were being argued separately, and `TASK-280` has been blocked
since 2026-09-08 on `schema/state-schema.json § krs[].title required: true`.

## Options

1. **Option A — keep both files as projections, keep the drift checks.**
   - Pros: nothing to migrate; a human can open a markdown file today.
   - Cons: every overlapping field stays a place two answers can disagree.
     The drift checks are the ongoing cost of the duplication, not a fix for
     it. `TASK-155`'s class stays open, and the four stale prose claims above
     are what "keep the document authoritative for prose" produced in eleven
     days.

2. **Option B — the store is the only copy of structured state; the projected
   markdown files stop existing.**
   - Pros: the drift class becomes **impossible rather than detected**.
     `TASK-155` dissolves — one field cannot carry three facts if the document
     that holds it is gone. `TASK-280` unblocks. The five rows above become one
     decision instead of five arguments.
   - Cons: the human editing surface for tracks, KRs and the board becomes a
     command rather than a file. This is a real loss and it is the thing
     `TASK-236` and `TASK-237` were opened to measure; this ADR takes the
     decision those rows were going to inform, ahead of their measurement.
     Roughly 775 live references and 122 test files change.

3. **Option C — split each file: frontmatter to the store, prose stays.**
   - Pros: keeps a place for the reasoning a schema cannot hold.
   - Cons: this is what the linkage document already does, with the boundary
     written in its own header, and the prose half is four-for-four stale.
     The option is not hypothetical — it has been running and it failed.

## Chosen

**Option B.** Structured state lives only in the store. `.perry/config.md` and
`phase/<NNN>-linkage.md` stop existing, along with the machinery that projects
and diffs them.

The argument that decides it is Option C's evidence rather than Option B's
promise: the split was already implemented, declared in the file's own header,
and it produced four false statements in thirty lines. A boundary nothing
checks is not a boundary, so there is no version of "keep the document for the
prose" that is not this.

## Consequences

**What becomes impossible rather than checked.** `config-store-drift` and
`linkage-store-drift` cannot occur once there is one copy. `perry-lint`'s
verdicts for those two stores, `perry-config`'s five subcommands
(`build`/`verify`/`render`/`write`/`diff`), `perry_md_store.CONFIG`, and the
three drift-comparison readers in `perry-state` all lose their subject.

**What changes for a human.** Editing a track, a KR or an intake row is a
command, not a file edit. `SKILL.md § Configuration` called `.perry/config.md`
"a tier-1 file the user owns and edits directly"; that promise is withdrawn
here explicitly rather than eroded. `perry-config --help` has carried the
tension unresolved since `TASK-092` — *"it is a change to what the user was
promised about this particular file, and TASK-092 leaves the decision with them
rather than making it silently"*. This is that decision, made rather than left.

**What this settles for phase 003.** The read-side commitment in
`phase/003-storage-code.md § User Commitments` is answered in the strongest
direction: nothing reads the file because the file is gone. Scope-reduction
trigger #2, armed to fire 2026-09-10, is moot — it would have collapsed
`P003-O2-KR1`, already measured at 0 against a target of 0.

**What must NOT change.** The 387 historical references to these two filenames
in `perry/evidence/` (64), `perry/journal/` (12), `perry/design/` (10),
`perry/handoff/` (3) and `perry/decisions/` (2) **stay exactly as written**.
They are the record of what was true when they were written, `evidence/` and
`journal/` are append-only by Perry's own contract, and rewriting them would be
falsifying the account. **This ADR is what a future reader finds when a name in
those files resolves to nothing** — that is the reason it exists as a record
and not only as a commit.

**What it costs.** ~775 live references across ~120 files, of which 188 lines
in 81 test files construct or read `.perry/config.md` and 156 references across
41 test files touch the linkage document. `schema/state-schema.json` changes,
which is on `.perry/hook.md § High-stakes operations` under the claim surface;
the user authorized that edit in session on 2026-09-08.

**What is deliberately not decided here.** Whether the 30-line prose body of
`phase/<NNN>-linkage.md` is worth keeping as a separate file at all, or belongs
in `phase/<NNN>-<slug>.md` and `phase/snapshots/`. Open question, not blocking.

## Relationship to ADR-015, stated precisely

`ADR-015` (2026-09-02, active) draws Perry's hand-edit boundary at the audience
tier: *"Tier 1 stays the user's, and hand editing it stays legitimate. `OKR.md`,
`phase/<NNN>-<slug>.md`, `.perry/hook.md`, `.perry/roles/*.md`. These are
authored, not projected; the user must be able to read and change them raw."*

`work/SKILL.md § Axis B` puts `.perry/{config,hook}.md` in tier 1. **So this
ADR deletes a tier-1 file, and that contradicts ADR-015 for one entry.**

**What is narrowed: `.perry/config.md` only.** `ADR-015`'s rule stands
unchanged for `OKR.md`, `phase/<NNN>-<slug>.md`, `.perry/hook.md` and
`.perry/roles/*.md`, and its tier-2 half — a hand edit to a projection is
refused, not reported — is unaffected. `ADR-015` stays `active`; a dated note
was appended to it pointing here, so the contradiction is discoverable from
either side. This follows `ADR-010`'s precedent, which superseded exactly one
sentence of `ADR-007` and left `ADR-007` active.

**And the contradiction predates this ADR.** `ADR-015`'s own list calls
`.perry/config.md` *"authored, not projected"*. It had already been a
projection for three days when that was written: `USER-903` settled the write
side on 2026-08-28 and `TASK-233` moved the prose out on 2026-08-30, after
which `perry-config render` writes the file and `perry-lint` reports a hand
edit to it as drift. `ADR-015` was wrong about this file on the day it was
filed. This ADR resolves that by removing the file rather than by correcting
the claim, which is the cheaper of the two and the only one that also removes
the drift class.

## Evidence

- `perry/evidence/2026-09/midphase-review-003-storage-code.md` — findings 1-5, and the structural-blocker section naming the claim surface
- `perry/evidence/2026-09/2026-09-08-kr-remeasurement.md` — the two-consumer proof for `updated:`, with both code sites
- `bin/perry-goals:2209-2224` — the write site that documents the defect and declines to fix it
- `bin/perry-tasks:1612` and `bin/lib/__init__.py:1066` — the two readers of one field
- `bin/perry-config --help` — the tension named and left to the user since `TASK-092`
- `perry/phase/003-linkage.md` — the header declaring the boundary, and the 30 lines that show it did not hold
- Commit `104873da` — the tree every number above was measured on

## Sunset criteria

None. Permanent.
