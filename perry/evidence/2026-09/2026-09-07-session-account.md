# 2026-09-07 — the session's full account

> Moved here from `journal/2026-09/2026-09-07.md` on 2026-09-07, unchanged,
> when that entry hit the 300-line cap this session had just introduced at
> 1,970 lines. **Nothing is deleted** — this is the remedy the rule names:
> the account lives in evidence, the journal keeps what changed and why a
> decision went the way it did. The journal entry now points here.

## PMO session — phase 003 completion review

**The phase's remaining Must-Have is one serialized chain, and its only live
link was already running.** Phase 003's DoD items 1, 2 and 4 are met; item 3
(`P003-O2-KR1`) has all four linked rows `done` but no asserted `current`;
item 5 (`P003-O3-KR2`) is DESIGN-015 rows A-F. State at this session:

| DESIGN-015 | row | status |
|---|---|---|
| A | TASK-276 | `review` — merged, **V4 never ran** (its reviewer branch `review/v4-276-356-357-fresh` carries a 3-line stub and nothing else) |
| B | TASK-277 | `review` — merged, **V4 never ran**, result document was a 195-byte stub |
| C | TASK-278 | `in_progress` — **genuinely live**, verified by commit clock, not by the board |
| D | TASK-279 | `not_started` — hard-blocked on C by DESIGN-015 § 6's one ordering constraint |
| E | TASK-280 | `not_started` — separable, declared unlinked, may lag |
| F | TASK-281 | `not_started` — spec declares `Dependencies: TASK-279` |

**TASK-278 was confirmed running rather than assumed.** `perry-dispatch-limit
list` reports no active dispatches and says in its own words that this is
bookkeeping, not observation — it had just reaped two stale markers. The real
evidence is the branch: `coding/task-278-six-read-sites` carries three commits
and its most recent, site 2 of 6, is timestamped `2026-09-07 11:13:51`, seconds
after this session's `perry-state` snapshot. The worktree is locked and clean.
Sites 6 and 2 are done, four remain. **Nothing was dispatched against it**, and
nothing touching `bin/perry-state` or `viewer/parsers.py` was dispatched
alongside it.

**D and F were NOT dispatched, deliberately.** DESIGN-015 § 6 names C-before-D
as its one hard constraint and says the failure mode is *silent*: the edge
lands, every reader still answers from the document, and `attribution` reports
never-asked for a row that was just linked. F's own spec declares
`Dependencies: TASK-279`, and its verification 2 requires constructing a row
linked *in* the `add` action — which is the thing D builds. Dispatching either
now would buy a merge conflict in `bin/perry-state` and a round that cannot
verify itself.

### TASK-277's result document was written from the PMO's own measurements

`evidence/2026-09/TASK-277-result.md` was a stub: its agent was killed by a
rate limit with the work committed and no RESULT block. `work/reference/review.md
§ 2` puts an incomplete exhibit on the author before dispatch, not on the round,
so the document was completed to 148 lines before the review went out. **Every
claim in it is a command re-run this session against merged `main`, and the
document says so in its first section rather than presenting itself as the
agent's testimony.** What was verified:

- 121 records — `6 kr + 15 edge + 100 unlinked` — against the spec's stale
  `7 + 11 + 75 = 93` baseline measured 2026-09-02.
- **The delta is fully accounted for and none of it is invention**:
  `kr` 7→6 and `edge` −2 because `P003-O2-KR2` was withdrawn by `USER-911` on
  2026-09-02 and `TASK-050` / `TASK-099` sat under it — they survive in
  `phase/003-linkage.md:76` as prose, in no `tasks:` field; `edge` +6 for
  `TASK-283` and the five DESIGN-015 rows added after 09-02. `11 − 2 + 6 = 15`,
  and the 15 are field-for-field the six frontmatter `tasks:` lists.
- **All 115 `edge` and `unlinked` records carry `via: link`, none `via: add`** —
  enumerated, not sampled. This is the one that could have wrecked the chain:
  `P003-O3-KR2` counts rows linked in the same action as `add`, so `via: add`
  on records swept out of a document that does not record their provenance
  would have inflated the exact KR the design exists to make honest, in the
  store about to become its authority, undetectably.
- `phase/003-linkage.md` byte-unchanged across the merge (empty diffstat on
  `b493493^1..b493493`).
- `perry-lint` prints `linkage store: 121 valid record(s), comparison
  incomplete — drift is unchecked, not clean` — `unchecked`, not `clean`, which
  is the phase-003 operating rule and honest, because the readers have not
  moved yet. That move is C.

The document also records **four areas the PMO did not check** and hands them to
the round: the 747-line `test_linkage_import.py` was never mutated by anyone,
the 749-line importer in `bin/perry-tasks` was read for output only (idempotency
and re-run behaviour unmeasured), the 48-line `perry-lint` change was verified
only by the census line it prints, and no full-suite/lint baseline was recorded
at merge.

### Two V4 rounds dispatched, concurrently

Per `review.md § 4`, independent rows go out as one round with separate agents
and separate verdict blocks. Both are read-only against the tree and write only
their own review document, so neither collides with C.

- **TASK-276** — criteria `evidence/2026-09/TASK-276-spec.md`, under review
  `45923e7^1..d1ceb58` (four merges). The round is pointed at the author's
  central argument — that a deletion-free diff proves no existing claim's path
  or owner changed — and told to test the argument across all four merges, not
  just its arithmetic. Its most important property: with `perry/linkage.jsonl`
  moved aside, `perry-lint` must still say `unchecked`, not `clean`. **That
  file now exists**, imported by B after A landed, so the round must move it to
  test the property A was accepted on.
- **TASK-277** — criteria `evidence/2026-09/TASK-277-spec.md`, under review
  `b493493^1..b493493`. Told that its exhibit is second-hand and that rule 3
  applies to it with full force; pointed first at the never-mutated 747-line
  test file, and asked to decide for itself whether the two absent edges are a
  faithful import of a register that moved or a dropped edge.

Both rounds were told to measure their baseline in their own worktree, never
from a figure measured elsewhere, and to verify any mutation restore against
their own branch base rather than `main`.

### Hand-off to the `goals` lane — two KR numbers this lane cannot write

Neither is work; both are bookkeeping that `work` is forbidden to do:

1. **`P003-O1-KR2`'s asserted `current` is stale.** `perry-state` reports it
   directly: `TASK-067` moved `review → done` at `2026-09-04T03:06:30Z`, after
   the register's assertion at `2026-09-03T06:06:45Z`. The number is 6/6 and
   probably still right, but it is asserted, and the linked task moved under it.
   Re-measure, then `/perry goals score-phase`.
2. **`P003-O2-KR1` has no `current` at all.** All four linked rows — `TASK-095`,
   `TASK-233`, `TASK-247`, `TASK-283` — are `done`, the target is 0, and
   `current_provenance` reads `unasserted`. **DoD item 3 may already be met and
   nothing says so.** This needs a measurement of the `parse_tracks` call sites
   and an assertion by the lane that owns the register.

### Not advanced, and why

- **TASK-262** (`P003-O2-KR3`, DoD Nice-to-Have 6) — `not_started`, P2, blocked
  behind `TASK-235 → TASK-236 → TASK-237`, and `TASK-237` additionally waits on
  a written report from `TASK-236` that is a gate rather than a dependency edge.
  Not reachable this phase.
- **TASK-348** and **TASK-368** — both P0, both reset `in_progress → not_started`
  earlier today after their agents were killed on 09-04 without doing any work.
  Both are `unlinked` in the attribution set, so **neither serves a phase-003
  KR** and neither is phase-completing. They are the board's two highest
  priorities and they are not on this chain; raised to the user rather than
  dispatched, because dispatching P0 work that does not close the phase was not
  what this session was asked for.

## New tasks added

### TASK-372 — perry-restore-check --root cannot verify a git-archive scratch copy — the exact use review-constraints.md recommends

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: perry-restore-check verifies a restore inside a directory that is not a git repository, by taking the reference tree and the target directory as separate inputs rather than assuming they are the same place
- **Verification**: Build a git archive copy of this repo, mutate one file in it, restore it, and run the command review-constraints.md actually recommends. It must give a verdict instead of an error. Mutation: break the restore and show the same call go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-373 — Two concurrently dispatched agents share one 'session-specific, isolated' scratchpad and can overwrite each other's files mid-round

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: Concurrently dispatched agents get scratch space that cannot collide, or dispatch refuses to hand two live agents the same scratch path
- **Verification**: Dispatch two agents concurrently, have each write a file at the same relative scratch path, and show neither sees the other's bytes. Mutation: remove the isolation and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-374 — One malformed line in linkage.jsonl voids validation of every good record in the file

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Deliverable**: A malformed line is reported as one bad record among N validated, not as an unreadable file; extra undeclared fields are reported; and an existing file is never described as absent
- **Verification**: Append one stray line to a copy of the store and show the census report N-1 valid plus one named bad line. Mutation: revert the per-line handling and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-375 — linkage.jsonl has no uniqueness or mutual-exclusion invariant — a task that is both linked and declared unlinked passes every gate

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: The register lint or the store refuses a task that is both linked and declared unlinked, and refuses duplicate edge and duplicate unlinked records
- **Verification**: Feed each of the three contradictory registers in and show a named error where there is now silence. Mutation: revert the refusal and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-376 — The linkage importer's spec-version gate is unguarded — mutating it to if False: leaves the whole suite green

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Deliverable**: A test feeds the importer a register declaring a spec version other than linkage: 1 and asserts it is refused with nothing written
- **Verification**: Disable the gate at bin/perry-tasks:1534 and show the new test go red. That mutation is green today, which is what filed this row.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-377 — perry-state's design.by_status key order depends on PYTHONHASHSEED

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Deliverable**: The payload is byte-stable across runs given the same state, so it can serve as a control. Any other key whose order is incidental rather than declared is found in the same pass and named.
- **Verification**: Reproduce first: run perry-state twice with different PYTHONHASHSEED values and diff, quoting the differing keys. After the fix the two runs are byte-identical apart from generated_at. Control: a genuine state change still changes the payload. Mutation: revert the ordering and show a named test go red. perry-lint --root . 0 errors.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-378 — Every tool-mediated write is stamped actor: agent, so two concurrent PMO sessions cannot tell their writes apart — and one has already misattributed the other's to a dispatched agent

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A write's actor identifies who made it — at minimum PMO-session versus dispatched-agent, and enough to tell two concurrent sessions apart
- **Verification**: Make two writes from two different sessions and show the log distinguishes them. Replay the 2026-09-07 11:53:41 misattribution against the new field and show it is no longer possible to reach the wrong conclusion. Mutation: collapse the field back to a constant and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-379 — perry-lint guards the exit from review but not the waiting room — five rows sit at review with merged code and no verdict document, and nothing reports it

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: perry-lint reports a row that has sat at review beyond a declared threshold with no verdict block naming it
- **Verification**: Park a row at review with no verdict and show the new finding fire; give it a verdict and show it clear. Mutation: disable the check and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-380 — main cannot have a green suite through code alone — the one red module asserts Perry's user has answered their questions

- **Owner**: User + Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A decision, recorded, on whether an assertion whose truth depends on the user's decision backlog belongs in the suite — and the suite changed to match it
- **Verification**: After the change, main's suite is green, or its one red is a declared waiver the run prints by name so no agent re-diagnoses it. Mutation: reintroduce an unwaived user-dependent assertion and show the declared-waiver check go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-381 — Dispatched agents are handed a worktree 496 commits behind main, and a stale base produces work that looks correct

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: Dispatch pins the base commit and states it in the brief, so an agent asserts its base rather than discovering it is wrong
- **Verification**: Dispatch an agent and show the brief names the base SHA and the worktree is at it. Mutation: point dispatch at a stale ref and show a named check refuse before any work begins.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-382 — perry-goals krs still reads the register for a computed KR, so the surface a human is told to read shows None where two machine payloads show the measured value

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: All publishers of a KR's current agree, because they splice one computation rather than each reading their own source
- **Verification**: Assert every KR in COMPUTED_KR_METRICS reports the same current and provenance from perry-state, perry-goals list and perry-goals krs. Mutation: revert cmd_krs to the register read and show that test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: P003-O3-KR2

### TASK-383 — add --kr creates a linkage drift no tool can clear, because perry-goals link decides already-linked from the store and the drift is in the document

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A drift created by add --kr is clearable, either because the document is no longer a second list or because perry-goals link writes it
- **Verification**: File a row with --kr and clear the resulting drift with one documented command, ending at 0 row(s) drifted. Mutation: revert the fix and show a named test go red on the standing drift.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: P003-O3-KR2

### TASK-384 — summary is mandatory to write, reported by the linter, published by one payload and not the other, and declared in no schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: One answer about whether a task record has a summary: the schema declares it, and the payloads that publish task rows agree
- **Verification**: Assert the same row's summary is identical from perry-task list and perry-state, and that the schema names the field. Mutation: drop it from one publisher and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-385 — The scratch-isolation remedy reddens the repo-scanning tests, so an agent obeying its brief breaks the suite it is measured against

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: An agent can isolate its scratch work without reddening a test, either because the scan excludes a declared scratch path or because the brief names a per-agent location outside the tree
- **Verification**: Create the scratch directory the brief asks for and show the suite matches baseline. Mutation: remove the exclusion and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-386 — A pipe-written tasks value declares an edge the reader silently drops, because the id carries a trailing newline and the match is exact

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A tasks value that cannot resolve to an id is refused where it is written, or normalised so the edge it declares is honoured
- **Verification**: Write a register with a pipe-style tasks value and show the edge either resolves or is refused with a named error. Mutation: revert the fix and show a named test go red on the dropped edge.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-387 — A mitigation that lives in one writer's body was not inherited by the next writer that read the same field

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A writer cannot read the register's updated: as a date without reporting what it re-dates, enforced rather than documented
- **Verification**: Add a writer that reads the field without disclosing and show a named check refuse it. Mutation: remove the enforcement and show that check go green on the same writer.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-388 — ADR-017 is decided and unperformed: 20 overall KR ids still use the old grammar, and the new one is rejected by the readers

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: One KR id grammar at both levels, with every reader accepting it and no reference left dangling
- **Verification**: O3-KR1 resolves through every reader and KR-O3.1 appears nowhere as a live id; perry-lint at 0 errors with no new dangling-reference finding; the legacy phase-form refusal still fires. Mutation: revert a reader widening and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-389 — ADR-018 part C — classify the 73,863-line test suite by what a failure would mean, before anything is deleted

- **Owner**: Research Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A per-module classification into behaviour, convention and mixed, with line counts, runtime by class, and the cost of losing each convention guard
- **Verification**: Every number carries the command that produced it and the base SHA it was measured on, and the result carries a Bound naming how the module set was enumerated and its size.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-390 — A design's Linked OKR line is parsed into a field nothing reads, so a design can name a KR that does not exist and every instrument stays green

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: Either Linked OKR is resolved against the OKR store and reported when it dangles, or it leaves the header template as decoration
- **Verification**: Point a design's Linked OKR at an id that does not exist and show a named finding fire. Mutation: remove the resolution and show that finding go silent.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-391 — A documented flag combination writes a linkage record that permanently reddens the suite, and the writer has no retraction

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: The lane on a linkage record is stamped by the writer rather than supplied by the caller, or the assertion stops keying on a caller-controlled field
- **Verification**: Run the documented combination and show the suite unchanged. Mutation: revert the fix and show the named test redden again.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-392 — TASK-278's Bound undercounts its own set, a blank-line skip is unasserted, and the confound sweep misses evidence documents

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Deliverable**: The Bound names behaviours where it means behaviours and covers every placement the parser handles; the blank-line skip carries an assertion; the confound sweep includes evidence documents
- **Verification**: Re-derive the shape space from the parser's branches and show the Bound's size matches. Mutation: remove the blank-line assertion and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

### TASK-393 — The shipped OKR template still mints the retired KR grammar, so a new project starts in the form ADR-017 just removed

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: A new project's OKR is minted in the current grammar, with the id shape pinned by the same test that already checks shipped templates
- **Verification**: Create a project from the template and show its ids match the current grammar. Mutation: revert the template and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

## TASK-276's V4 returned PASS — verified, merged, closed

**DESIGN-015 row A is done at V4.** `P003-O3-KR2` moves from 0 of 5 linked rows
closed to 1 of 5. Board V4 closures 38 → 39. `perry-lint` 0 errors, board drift
0.

**The PASS was not taken on the reviewer's word.** Two claims carry the verdict,
and both were re-derived here before the merge:

1. *Deletion-free across the range.* `git diff 45923e7^1 d1ceb58 -- <file> |
   grep -cE '^-[^-]'` returns **0** for both `schema/state-schema.json` and
   `bin/perry-lint`. This is what discharges "no reader moves", because **2 of
   the 6 DESIGN-015 § 5.6 reader sites live in `bin/perry-lint`** — the file the
   row was allowed to touch.
2. *The NS-01 class pre-dates the row.* `TASK-275`, filed **2026-09-02**, already
   records `perry-lint` reporting the empty `perry/intake.jsonl` as foreign
   state. That is independent of the reviewer and predates the round, and it is
   what makes F1 a pre-existing class rather than a defect this row introduced.

The branch touched exactly one file, its worktree finished clean, and the merge
is doc-only.

**The round corrected the author, and the correction is worth keeping.** The
per-commit history is *not* deletion-free — `75a016f` deletes 2 lines of
`bin/perry-lint` — but both were added earlier in the same range by `8272d95`,
so no pre-range line changed and the cumulative claim holds across all four
merges. The exhibit's "187" is also stale against the range's 190 (F7). Neither
is a V4 defect; both are the kind of exhibit arithmetic `review.md § 2` assigns
to the author before dispatch.

**9 of 9 line-anchored mutations red, 0 green**, every restore verified against a
freshly re-read `git show 1032e76:<path>` — the **pinned** SHA, not the moving
`main`. All destructive work ran in `git archive` copies; the live tree finished
byte-identical.

### Two environment defects the round hit, both filed

Neither is about `TASK-276` and both cost this round real time:

- **`TASK-372`** (P1) — **`perry-restore-check --root` cannot verify a
  `git archive` scratch copy**, which is the exact call
  `review-constraints.md` recommends to every reviewer. `--root` repoints the
  tool's *git* queries too, so it answers `<ref> is not a commit in <copy>`.
  The reviewer fell back to hand-rolled byte comparison, and **that fallback is
  the finding**: the round still verified its restores, but by a method it
  invented on the spot — Perry's own recurring N-implementations-of-one-rule
  defect, this time in the procedure Perry hands out.
- **`TASK-373`** (P1) — **two concurrently dispatched agents share one
  "session-specific, isolated" scratchpad.** The other reviewer overwrote this
  one's mutation harness mid-round. Both agents had `isolation: worktree` and
  both were correctly isolated *in the tree*, which is what makes it dangerous:
  the dispatch surface reports an isolation that is real for git and not real
  for the scratchpad. **The failure is silent by construction** — an overwritten
  harness still runs and still prints a result. This session dispatched exactly
  two concurrent reviewers and hit it once.

### One product row filed, one folded into an existing row

- **`TASK-374`** (P2) — **one malformed line in `linkage.jsonl` voids validation
  of every good record.** The parse is a single comprehension in one `try`, so a
  stray line gives `linkage-store-unreadable` and 0 records validated instead of
  120 validated and one reported (F5), alongside undeclared fields passing
  silently (F4) and an existing file described as absent when `stores.declared`
  is missing (F6). **None of the three failed the round, and the reason is the
  phase's own operating rule**: every one errs toward `unchecked, not clean`, so
  the store never claims a comparison it did not perform. It matters because
  `TASK-281` is about to make this store the authority for `P003-O3-KR2`, and at
  that point a stray line silently zeroes a KR's evidence base.
- **F2 was folded into `TASK-275` rather than filed** — it is the same defect
  that row already names. What the round added is the row's **size and its fix**:
  all eight declared `.jsonl` claims were enumerated and `intake.jsonl` is the
  **only** one returning False, so it is the last one, not one of several; and
  `TASK-277`'s `_matches_a_declared_store` already repaired the identical defect
  for `linkage.jsonl` by reading `stores.declared`, so the remaining work is to
  declare intake's shape there, not to write a new recognizer.

**Board is 217 lines against a 200 cap** — three rows in, one closed. The
overrun predates this session (215 at snapshot) and `triage` is what clears it.

`TASK-277`'s round was still running when this was written.

## TASK-277's V4 returned PASS — and it corrected the exhibit I wrote

**DESIGN-015 rows A and B are both done at V4.** `P003-O3-KR2` goes 0 → 2 of 5
linked rows closed. Board V4 closures 38 → 40.

**The round beat the author on the central question, and the author was this
PMO.** The exhibit derived the count delta as `11 − 2 + 6 = 15`, reading the
spec's `11 edge` as a real measurement and attributing six edges to rows added
after 09-02. **That is wrong.** The round found better evidence *already in the
tree and unused*: `phase/snapshots/2026-09-02-003-linkage-pre-kr2-withdrawal.md`
holds the register as it stood that day and carries **17 edges, not 11** —
including `TASK-283` and all five DESIGN-015 rows. **Nothing was added after
09-02.** The reconciliation is structural, not arithmetic: `17 → 15` and
`7 → 6 kr`, the only change being `P003-O2-KR2` withdrawn taking exactly
`TASK-050` and `TASK-099`. Zero edges added, zero `unlinked` removed.

Re-derived here independently by parsing the snapshot before accepting it. The
exhibit's arithmetic reached the right total by a route that is not what
happened — `knowledge/verification/numbers-migrate-between-sentences.md` is
about exactly this, and the exhibit now carries the correction in place rather
than quietly reading better.

**The reviewer's blocking condition was real, and it was ours.** It refused to
recommend closing until the result document recorded the re-measurement, and it
was right on the state that counts: `TASK-277-result.md` was **still a 6-line
stub in committed `main`** while the 148-line rewrite sat uncommitted in the
working tree. Committed as `d482216` before the close, so the citation is true
of the repository and not only of a session's working directory.

**14 mutations, 12 red, 1 green, 1 re-run.** The green is `M10`, the `linkage: 1`
spec-version gate — and the round did the right thing with it: verified the
guard *behaviourally* (a `linkage: 2` register is refused, store untouched), so
it is a **test-coverage gap and not a live defect**, filed rather than explained
away. It also owed and paid a correction of its own: `M9` left a stray byte in
the register that survived into three later mutations; caught with
`git status`, restored from the ref, `M10` and `M1` re-run on a clean tree.
`phase/003-linkage.md` verified byte-clean on `main` here, independently.

**115 of 115** `edge`+`unlinked` records carry `via: link`, zero `via: add` —
enumerated, not sampled. **21 adversarial registers**, each on its own fresh
extraction; idempotent across three re-runs; the absent-store census still says
`unchecked, not clean`.

Two more rows filed: **`TASK-375`** (P1) — the store has **no uniqueness or
mutual-exclusion invariant**; a duplicate edge, a duplicate `unlinked`, or a task
that is *both* linked and declared unlinked all pass every gate, and
`DESIGN-015 § 5.2` derives *never-asked* as "neither", so a row holding both has
no defined reading. Pre-existing — the same register reports `0 error(s)` at the
merge base — and urgent only because `TASK-281` is about to compute a KR from
it. **`TASK-376`** (P2) — the unguarded spec-version gate.

## Row C finished while the reviews ran, and is at `review`, not merged

`TASK-278`'s agent completed at **11:52** and its worktree is clean. Moved off
`in_progress` the moment it stopped — leaving it there is the defect `TASK-371`
describes and the one this board committed twice on 09-04.

10 commits on `coding/task-278-six-read-sites`, 248-line result, **all six
DESIGN-015 § 5.6 readers moved**, re-derived by call site rather than by
grepping a name as the brief required. 1,687 insertions across 9 files —
`bin/perry-goals`, `bin/perry-lint`, `bin/perry-task`, `viewer/parsers.py`, and a
new 684-line `tests/test_linkage_store_readers.py`.

**Its mutation round is why it is credible and why it still needs its V4.**
Round 1 planted 17 and came back **14 red, 3 GREEN** — and the agent treated
every green as a finding rather than explaining it away: `M5` (deleting site 5's
exclusion), `M12` (dropping an unparseable line) and `M16` (filing a `projects[]`
finding against the store) each survived because of a fixture hole. It fixed all
three; round 2 came back **17 of 17 red, 0 green**.

**The ordering constraint is now the whole question.** `DESIGN-015 § 6` requires
C before D, and C must be **merged**, not merely done, before `TASK-279` is
dispatched — a writer pointing at a store whose readers have not moved is the
silent failure the design names.

## A constraint this session discovered about itself

`TASK-373` means **concurrent dispatch is no longer safe** until it is fixed:
two agents share one scratchpad and one overwrote the other's mutation harness
mid-round. Both rounds this session survived it — one by noticing, one by luck —
but the next pair should go out one at a time. That changes how row C's V4 and
`TASK-279` are sequenced, and it is a finding this session produced about its own
method, not about the product.

## Correction — two PMO sessions worked this board at once, and neither could see the other

**A second session merged `TASK-278` at 11:53:58 and continued working the same
board.** That is good news for the phase and it produced three false statements
on `main`, one of them mine. All three have one cause, now filed as
**`TASK-378`**.

**Mine, first.** My commit `e8cbd68` at **11:54:15** and the journal section
above it both say row C "is **NOT** merged". It had been merged **17 seconds
earlier**. I measured at 11:52 and wrote at 11:54 and did not re-check between —
the same shape as the exhibit error the `TASK-277` round caught me on this
morning, which is twice in one session that a number was true when taken and
false when written.

**The other two are charges against a dispatched agent, and they are wrong.**
The other session recorded, on `TASK-371`, on `TASK-278` and in commit
`df269b5`, that `TASK-278`'s agent **wrote to `perry/tasks.jsonl` in the primary
checkout against an explicit brief**, and that its RESULT block calling that
file untouched was therefore **false** — "a good motive does not excuse a false
report". It also wrote that the row's `NOT YET MERGED` text "was the agent's,
not mine".

**That write was mine.** Three facts settle it:

1. The `status` event at **`11:53:41`** moving the row `in_progress → review`
   carries **my own reason string, verbatim** — "…moved off in_progress the
   moment it stopped… which is the defect TASK-371 describes and which this
   board committed twice on 09-04".
2. `git diff --stat 1032e76 coding/task-278-six-read-sites -- perry/tasks.jsonl`
   is **empty**. The branch never touched the file.
3. The `NOT YET MERGED` text is mine too — I wrote it in the same command.

**The agent's RESULT block was accurate.** The charge of a dishonest report is
withdrawn on both rows.

**The misreading was reasonable, and that is the finding.** Every event in the
log is stamped `actor: "agent"` — **1,601 of them** — whether a PMO session or a
dispatched coding agent made the write. Today's writes are indistinguishable:
`11:51:40`, `11:51:52`, `11:52:41`, `11:53:41` from this session and `11:54:57`,
`11:56:01` from the other, all identical in that field. A session that saw
`perry/tasks.jsonl` modified in the shared checkout beside an agent-stamped
event **had no field that could have told it otherwise**. The vocabulary for the
distinction exists — `PMO Agent` (209), `PMO` (64), `Coding Agent` (5) — and the
writer does not use it.

`TASK-371` keeps its 09-04 evidence, which was always enough on its own, and
loses the claim that the gap "produces pressure on agents to reach outside their
worktree" — that was never observed.

**With `TASK-373` (shared scratchpad) this is the second isolation defect found
today, and they rhyme:** work that is isolated in the tree is not isolated in
the places the tree does not cover — the scratchpad, and the identity on a
write.

## Where the phase stands after the other session's merge

**Row C is merged and the linkage drift verdict is real** —
`linkage store: 121 record(s), 0 row(s) drifted`, where before it read
`comparison incomplete — unchecked, not clean`. `TASK-278` sits at `review`
awaiting its V4; the code is on `main`.

**The `DESIGN-015 § 6` ordering constraint is discharged.** C is merged, so
`TASK-279` (row D, `add --kr` writes the edge) is **no longer blocked** — it is
the next thing that moves `P003-O3-KR2`, and `TASK-281` (row F) follows it.

## Two KRs measured — and DoD item 3 turns out to have been met, unrecorded

Evidence: `evidence/2026-09/2026-09-07-kr-remeasurement.md`. Neither was work;
both were numbers nobody had taken.

**`P003-O2-KR1` is met at 0, and `current` is recorded for the first time.**
All four linked rows were already `done` while the KR carried **no asserted
value at all**. `grep -rn "parse_tracks(" bin/ viewer/` minus its own `def`
returns **exactly one** invocation — `bin/perry-state:1172` — inside
`declared_tracks_detail`, which reaches it **only when there is no store**;
`perry-state --json` reports `tracks_source = store` on this project. A
name-based grep returns **eighteen** hits across six files, seventeen of them
comments and docstrings, so counting names would have reported this KR as
massively unmet. That is this phase's first operating rule earning itself back.

**A Definition-of-Done item can sit met and unrecorded and nothing says so.**
That is worth more than the number.

**`P003-O1-KR2` is still met and its population has outgrown its target.** One
lint run now prints **seven** drift verdicts, not six — `linkage.jsonl` joined
during this phase and its verdict is **real**, where before row C merged the
same line read *comparison incomplete*. `current` left at 6 against target 6
**deliberately**: raising both to 7 is a KR change and belongs to the user.
Flagged for scoring as **7 of 7** on the honest reading.

**The drift verdict proved itself on an edit its own reviewer has not seen.**
Adding `current: 0` and not yet syncing produced
`linkage-store-drift · P003-O2-KR1 differs · 1 row(s) drifted`, naming the row
and saying which side is stale. It correctly did **not** flag the `metric:`
prose edits — `DESIGN-015 § 5.4` keeps prose in the document and typed facts in
the store, and the comparison covers the typed facts only.

### `TASK-155` reproduced live, 17 days past its SLA

Recording a measurement date meant bumping the register's `updated:` field —
which **rewrote `declared_at` on all 115 `edge` and `unlinked` records to
today**, 115 records claiming a declaration action that never happened. That is
`TASK-155` exactly: one field carrying two facts.

Reverted. The store now differs from its pre-edit copy by **exactly one field**,
verified by diffing both ways rather than by reading the code.

**The defect forces a choice between two falsehoods.** Bump `updated` and 115
provenance dates become false; leave it and `perry-state` reports today's
measurement as **stale**, which both KRs now wrongly show. **I took the stale
flag, because it is a visible wrong answer and a re-dated declaration is an
invisible one** — and the row now carries the fix shape the reproduction made
obvious: `declared_at` belongs per record, not derived from a file-level field.
`TASK-279` is in flight and writes edges with a per-action timestamp, so that
row is where the per-record shape arrives and `TASK-155` should follow it.

### A note on lane ownership

`phase/003-linkage.md` is the `goals` lane's file and this session wrote it
while acting as that lane, not as `work`. The store side went through
`perry-tasks linkage-write --from-register` rather than a hand edit.
`bin/perry-goals` still has **no writer for a KR `target` or `current`** — it
says so in its own `--help` — which is `KR-O2.1`'s open baseline, and is why
this measurement needed a document edit at all.

## The `review` column has never been verified — all five rows, measured

This morning's finding on `TASK-276` and `TASK-277` was not two rows. It is
**the whole column**, and `TASK-379` now carries it.

**Every row at `review` has zero verdict documents naming it** — `TASK-278`,
`TASK-336`, `TASK-341`, `TASK-356`, `TASK-357` — and **all five have their code
merged on `main`**.

Method with its control, because a detector nobody tested is how this project
gets a wrong number: `grep -rl "^task: <ID>$" perry/evidence/` returns the
verdict blocks naming a row. Run against `TASK-276` and `TASK-277`, whose rounds
landed today, it returns exactly their two review documents. 41 distinct tasks
carry a verdict block in the repository; **none of the five is among them.**

### The asymmetry is the defect

`perry-lint --reviews` reports:

| finding | count | what it guards |
|---|---|---|
| `v4-close-without-verdict` | 11 | a row **closed** at V4 with no verdict |
| `verdict-malformed` | 12 | a block a parser cannot read |
| `review-rounds-exhausted` | 1 | two FAILs and no ask |

**It guards the exit and says nothing about the waiting room** — and the waiting
room is exactly where the 2026-09-04 rate limit left everything. It killed the
reviewers mid-round, their branches carry stubs, and nothing re-dispatched them
or noticed. `TASK-276` sat that way from 09-04 until this morning, and the only
reason it moved is that **a person asked what the phase was blocked on**.

This is `TASK-371`'s class — state claiming an activity nobody is performing —
moved onto the verification column, and it is worse there, because the board's
reviewer of last resort is the linter and the linter is looking the other way.

**`review` means a result is out for verification.** For four of these five,
nothing is out and nothing ever was, while the code they describe is merged and
being built on.

### Not dispatched, and why

Four rounds are dispatchable right now and I did not send them. `TASK-373` —
found this morning — is that two concurrent agents share one scratchpad and can
overwrite each other's mutation harness mid-round; two are already running
(`TASK-279` and `TASK-278`'s V4). Sending four more would be running the
experiment that produced `TASK-373` five times over, having just filed it.
They go out after the current two land.

## main's own baseline, measured here rather than quoted from an agent

I had been repeating agents' baselines all session without taking one. On
`a9176e5`, load average 32.7 with two agents running mutation batteries:

```
117 modules · 3346 tests · 8 workers
✗ 1 of 117 MODULE(S) red
```

**One red, and it is the same one all three of today's agents reported** —
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`.
**Re-run alone and reproduced**, so it is not the parallel runner and not the
load. That matters: `TASK-326`, `TASK-272` and `TASK-269` are all order- or
load-dependent reds, and this one is none of them.

### The red cannot be cleared by writing code — `TASK-380`

The assertion is `assertNotIn("LOAD-03", ids(perry_root))` at
`tests/test_diagnose.py:561`, docstring *"The skill that reports this must not
commit it."* It trips on a finding that is **true**: `perry-diagnose` reports
**6 open questions waiting on the user**, and names all six with file and line —
`USER-917` and `USER-918` at `BOARD.md:205-206`, plus **four open questions in
`design/DESIGN-016-the-bin-contract.md:216-219`**, the one unlocked design of
sixteen.

**So main's baseline cannot be green through engineering alone.** It goes green
when the user answers six questions. Every agent that measures a baseline
inherits a red it must reason about, and **three separate agents paid for that
today** — `TASK-276`'s V4, `TASK-277`'s V4 and this session each independently
re-ran the module alone and wrote it up. That is the same cost paid three times
for a fact nobody had written down.

`TASK-380` puts the decision to the user rather than taking it: exclude the
user-measuring finding classes from the assertion and keep the structural ones
(recommended), or declare a named waiver the run prints. **Not** silently delete
it — it is the mechanism holding Perry to its own diagnosis.

### Perry had already diagnosed this morning's collision, and nothing routed it

`perry-diagnose` reports **`CON-02` — "Some files are rewritten by many
sessions"** — and ranks them: `perry/BOARD.md` **514 commits/90d**,
`.perry/events.jsonl` **502**, `perry/tasks.jsonl` **373**. Those are *precisely*
the three files the two PMO sessions collided on today. It also reports
**`CON-03` — "12 separate checkouts, but nobody reviews the combined result"**,
whose stated argument is exactly what happened: each piece correct, the combined
record wrong.

**Neither finding is new. Both were sitting in the diagnosis before the
incident.** That is worth more than the incident itself — the warning existed
and nothing routed it to a row. Added to `TASK-378`, along with the note that
`CON-02`'s own remedy (split a status-holding file into a small live file plus
an append-only dated history) is a **different** fix from that row's and may be
the better one.

Checked that filing these rows did not itself add a dangling reference: the
finding set after is identical to the set the failing test printed —
`LOAD-03, CON-02, CON-03, DOC-03, NS-01, DOC-05`, no `LOAD-02`.

## `TASK-278`'s V4 FAILED, and one defect is live data loss on `main`

Row C is **not** done. `evidence/2026-09/TASK-278-v4-review.md`, 554 lines.
The row is back at `in_progress` per `review.md § 5` — *a FAIL never leaves a
row at `review`* — and **raised to P0**, because its priority stopped being
about the phase the moment the defect could delete a record nothing can
recreate.

### Defect 1 — `bin/perry-task:4847`. Reproduced here, not taken on trust.

An `else:` makes the `phase/*-linkage.md` scan an **exclusive alternative** to
the store scan, so with `linkage.jsonl` present the 001 and 002 registers stop
counting as live references. **`purge` is irreversible and an id is never
reissued.**

Verified as a **differential**, `--dry-run` only, with the pre-merge code
extracted by `git archive` into a scratch copy:

| id | at `2acec65` (pre-merge) | on `main` today |
|---|---|---|
| `TASK-028` | **REFUSED** — `001-linkage.md:16` | **not refused** — *"would write … (purge)"* |
| `TASK-046` | **REFUSED** — `001-linkage.md:24` | **not refused** |
| `TASK-087` | **REFUSED** — `002-linkage.md:69` | **not refused** |

`TASK-027` still refuses — but only because an **unrelated** reference in
`reference/hand-off-contract.md` happens to name it. That is luck, not
protection. 21 further rows lost the register half of theirs.

### Defect 2 — `viewer/parsers.py:3975`

`load_linkage` hands the **whole** store to `linkage_from_store` with no filter
for the phase its `document_path` names. `perry-goals krs --phase 001` prints
**phase 003's** six KRs under phase 001's objective headings, above a line
saying they are declared in `001-linkage.md`, and drops all eight of 001's own
KRs and its 18 edges. Read-only — but a wrong answer one documented command
produces.

### Both are the row's own catch, not applied

Row C **discovered** that the check needed per-phase authority and applied it at
`bin/perry-lint`. Three of the other five seams did not get it. **It claimed one
shared seam; there are four.** And of five mutations against the per-phase rule
**four are green** — including applying the fix to `parsers.py`, which no test
notices. So the fix needs its own guard, not just the edit.

### Two exhibit corrections worth carrying

- *"12 edge lists"* in 001/002 is wrong: **14 KRs carry edges, 31 edges total.**
- **The branch row C called unreachable is reachable.** `linkage_graph` returns
  the document object, so `reg.graph.unlinked` is the document's list and a task
  the document declares unlinked **does** request a retraction — proved by
  dropping the line and watching the behaviour disappear. The code there is
  correct, so nothing hides behind it, but **the test was re-aimed away from a
  live guard** and "17/17 red" does not hold for it.

The drift verdict **is** real, independently confirmed: 11 classes caught, 4
schema-valid ones missed.

### Exposure assessed before deciding not to hot-patch

The hazard needs someone to deliberately run `perry-task purge <id> --reason …`.

- **3 purge events in the entire log**, all on 2026-08-28.
- **No lane procedure anywhere instructs an agent to run `purge`** — checked
  across `work/`, `goals/`, `decide/` and `reference/`.

So nothing automated reaches it. **The fix was not hand-applied**, for two
reasons: `TASK-279` is in flight and editing the same file, and patching code a
round just FAILed is how a fix escapes review. It goes out as a round once D
lands.

## Row D landed and verified — `P003-O3-KR2` can now move

`TASK-279` merged and at `review`. **The spec's one sequence works, and the PMO
ran it rather than reading the report** — in a `git archive` scratch copy of the
branch, nothing run in between:

```
before   linked = 4    store 121 records
after    linked = 5    store 122 records
record   {"kind":"edge","task":"…","kr":"P003-O3-KR2",
          "declared_at":"2026-09-07T04:41:04Z","actor":"agent","via":"add"}
```

`via: "add"` is the field that makes the KR computable at all, and
**`declared_at` is per-action** — the per-record shape `TASK-155` needs,
arriving exactly where that row predicted it this morning.

**Independent mutation, because a green suite is not evidence**: `via "add"` →
`"link"` at `bin/perry-task:2798`, `__pycache__` cleared and past the
whole-second boundary → **2 of 25 red**. Restored **from the ref**, not from my
snapshot, byte-verified `25bf200a9e4f93b0` both sides, 25/25 green again.

**The agent's own green is worth keeping.** 17 planted, 16 red, 1 green, closed
to 17/17. Deleting the `event != "add"` guard changed nothing — because **no
command Perry has today emits a non-`add` event carrying a `kr`**, so `route`
and `intake` were passing for the *wrong reason*: the absence of the key, not
the guard.

**Atomicity was tested, not argued.** A child imports the tool and `SIGKILL`s
itself before the Nth canonical rename — `SIGKILL`, so it cannot take the
already-covered deliberate-rollback path. At **all five** crash points the edge
never survived alone.

### The gate fired on its first real row

`TASK-381` was filed without `--kr` and `perry-task` said so on stderr, naming
both ways to resolve it. That is row D working on live state within minutes of
merging.

### `P003-O3-KR2`'s honest starting point, measured

```
add events this phase        190
carrying a `kr` key           1   (TASK-381, kr: null — never-asked)
via: add edges in the store   0
```

So the KR is **0**, and `DoD` item 5's restatement is what makes that fair: the
population is rows opened **after the gate lands**, not all 190 — the rows never
asked before it are phase 004's. **Row F must not measure the 190.**

### Why row F was NOT dispatched yet

`TASK-281` computes this KR from the store, and `TASK-278`'s open defect is that
the store is read **store-wide instead of per-phase**. F built on that would
compute from the wrong population and look right doing it. **F waits for the C
fix**, which is dispatched.

### `TASK-381` — the stale-base defect, filed

Three of four agents today were handed a worktree **496 commits behind main**,
each noticed independently, and each recovered **differently** — one reset to a
pinned SHA, one built `git archive` copies verified by `write-tree`, one reset
to main. Three protocols for one defect.

The danger is not lost time. In row D's own words, that stale ref *"is the exact
ref DESIGN-015 § 5.6 measured its line numbers against, so it would have looked
correct while every reader still answered from the document."* **A stale base
does not fail loudly** — it produces work that matches a spec written against
the same stale ref, passes its own tests, and is wrong about the tree it merges
into. The C-fix round dispatched after this row was given its base SHA to assert.

## The review backlog cannot be dispatched, and that is the second half of `TASK-379`

I went to clear it and **the process correctly refused me**.

`review.md § 1` refuses a V4 without written criteria — a fresh reviewer with no
criteria invents its own bar, which is why rounds stop converging. Checked all
four parked rows:

| row | `…-spec.md` | `verification` on the record |
|---|---|---|
| `TASK-336` | **absent** | empty |
| `TASK-341` | **absent** | empty |
| `TASK-356` | **absent** | empty |
| `TASK-357` | **absent** | empty |

Their `summary` describes the **defect**, not the acceptance bar.

**So the backlog is not four dispatches waiting to be sent — it is four rows
with no bar to judge against.** Writing that bar now means writing it with the
implementation already visible, which is the weaker form of the
negotiation-with-the-result problem § 1 warns about. I did not dispatch and did
not invent a bar.

**The rows did not skip a step that existed.** `perry-task add` takes
`--deliverable` and `--verification`, and the store keeps **no `deliverable`
field at all** — nothing carried them forward to a reviewer. That is why this
compounds `TASK-379` rather than repeating it: a parked-without-verdict check
would fire on all four, and **not one of them could be discharged by dispatching
a round**.

`TASK-278` is the argument for urgency, and it is not hypothetical: its V4
finally ran today and **FAILED on live irreversible data loss that had been
sitting on `main` since the merge**. Four more rows are in exactly that
position, and the reason they stay there is that nobody can be sent to look.

## The data-loss hazard is closed — and the acceptance test was confounded by me

`TASK-278` round 2 merged. Verified end-to-end on `main`: `TASK-028`, `TASK-046`
and `TASK-087` are **REFUSED again**, each naming `001-linkage.md:16`, `:24` and
`002-linkage.md:69`. `krs --phase 001` prints phase 001's own **eight** KRs
instead of phase 003's six. Drift verdict unregressed at `121 record(s), 0 row(s)
drifted`, lint 0 errors.

### The confound was mine, and it would have produced a wrong PASS

**When I filed the FAIL I wrote `TASK-028/046/087` into `TASK-278`'s own
`next_action` — and `next_action` is itself a live reference.** So all three
purges refuse *whether or not the defect is fixed*, and the refusal truncates at
60 characters, hiding which citation actually did the work.

The round caught it. **I had not**, and I would have confirmed a wrong PASS by
running exactly the three commands I had run before.

The original hazard measurement **stands**: it was taken *before* I wrote those
ids onto the board. Everything after that point was contaminated. The ids are
now out of the cell, the cell says why they are absent, and the differential was
re-run with a **control arm**:

| | fixed | unfixed `main` |
|---|---|---|
| the three probes | **all REFUSED**, register lines named | **all NOT REFUSED** |
| `krs --phase 001` | 001's own 8 KRs | 003's 6 KRs |

This is `CON-02` in miniature — the board is a file many sessions rewrite, and a
cell I wrote became an input to a test I later ran.

### Seams, and one deliberate non-merge

Six § 5.6 readers, **four** store-vs-document decisions, three defective sites,
now three seams. **Every one of the spec's six line numbers was stale** — site 6
had moved **forward 248 lines**. `perry-lint`'s seam **stays separate on
purpose**: its `unlinked` records attach to the **current** phase, not the phase
being read, so merging would have to discard one of the two rules. A **seventh**
reader exists that the failed review could not have seen — row D landed after
`6af6fd2` — but it is a writer, not a § 5.6 seam.

### 10 planted, 10 red, control green — and the best one is self-inflicted

Three came back green first and **all three were closed, not footnoted**. The
instructive one is in the round's **own new guard**: its first site-1 test called
the shared helper directly and never asked the helper's one caller, so **the
failed review's own V10/V11 hole survived into the fix for it**. It now drives
`perry-goals link` with `CURRENT` on an uncovered phase.

The branch row C called unreachable is confirmed **reachable**; test re-aimed,
source comment corrected. **14 KRs carry edges, 31 edges** — counted
independently for the third time, and "12 edge lists" is wrong for the third
time.

### `TASK-381` is now four agents out of five

This round's worktree arrived **508 commits behind main**. It reset onto the
pinned base I gave it — which is the row's own proposed fix, working.

## Row F merged — `P003-O3-KR2` is computed, and it moved off zero on live state

`TASK-281` merged and at `review`. **DESIGN-015's chain A→F is complete.**

```
P003-O3-KR2   current = 50.0   provenance = measured
              source  = linkage.jsonl + .perry/events.jsonl
```

**1 of 2 post-gate rows** — `TASK-382` was filed with `--kr` and counts,
`TASK-381` was filed without and does not. The whole chain worked end to end on
live state within minutes of landing: the gate marks the row, the store takes
the edge, and the KR counts it.

The register diff is **one line** — the `metric:` prose, which now says no
`current` is written there and why. **`TASK-155`'s trap avoided, verified by
consequence rather than by claim**: all 115 pre-existing records are still dated
`2026-09-03`, and only the new edge carries today's.

**The population decision is the round's real work.** The denominator is
`main`-track rows whose own `add` event carries a `kr` **key**, whatever its
value — row D changed the event's shape, so the key's presence *is* the gate's
mark on every row it governed. That reads DoD item 5's *"opened after the gate
lands"* off the data, with **no typed date or SHA**, which would have
reintroduced the very constant this row removes.

**23 mutations, 4 real greens, all closed.** `M13` is the one to keep: blanking
`perry-state`'s **store** read came back green against the live repo, because
there are zero `unlinked via:"add"` records, so the entire numerator came from
events and **every live assertion passed with half the inputs unplugged**. A
hole in its own new guard, closed with a fixture where the store's half is the
only thing that can answer.

### Two gaps I found after the round, both filed, neither reopening it

- **`TASK-382`** — `perry-goals krs` still reads the register for this KR.
  Measured on one tree: `perry-state` **0.0/measured**, `perry-goals list`
  **0.0/measured** (the `kr_rows` path the round fixed), `perry-goals krs`
  **None**. `cmd_krs` at `bin/perry-goals:3265` builds its own list off the
  model and never calls `computed_kr_current` — a **third publisher the round
  did not enumerate**, and it is the surface `goals/SKILL.md` calls *"the only
  surface"* for a phase's KRs. Not a regression; the KR never had an asserted
  `current`. But it is exactly the divergence the round's own comment says it
  prevents.
- **`TASK-383`** — **`add --kr` creates a drift no tool can clear.** Row D's
  result said the warning is one *"only `perry-goals link` can clear"*. It
  cannot: `add --kr` wrote the edge to the store, `perry-lint` reports the
  document stale, and `perry-goals link TASK-382 P003-O3-KR2` answers **"nothing
  to write — already linked"** and writes nothing. It is right about the store;
  the drift is in the document, where `grep` finds nothing. **It grows by one
  row per `add --kr`.**

**`TASK-280` (row E) raised P2 → P1.** It was filed *"separable and may lag"*
and the design says so too. That held while the document was the only register;
it stopped holding the moment D and F landed. Row E — shedding the document's
schema'd half — is the design's own answer to `TASK-383`. What makes it urgent
is what it protects: `TASK-278` round 2 was merged **hours ago** to make this
verdict *real* rather than deferred, and a store that drifts permanently and by
design converts that verdict straight back into noise.

Neither of these was hand-fixed, for the same reason `TASK-278`'s defect was
not: patching an agent's work outside its round is how a fix escapes review.

## Round 2's V4 FAILED — the defect is real, its attribution was not

`TASK-278` back to `in_progress`. **I corrected the verdict's diagnosis before
putting the row back**, because round 3 would otherwise chase a regression that
never happened.

### The defect, reproduced

Rewrite the phase-002 register's `tasks:` entry as a **block list** and
`purge --dry-run` on the row it names answers *"would write … (purge)"* instead
of refusing. `bin/perry-task:4994` requires the id on the **same physical line**
as `tasks:` — true of a flow list, false of a block list.

**The shape is legal, and every part of Perry agrees it is**: `perry-goals link`
writes it, `parse_linkage` reads it, `tests/test_linkage_writer.py:239` asserts
it, and `perry-lint` grades the block-list register **0 errors**.

### The attribution was wrong, and it matters

The verdict says *"the code this diff replaced **does** refuse"* — making this a
regression round 2 introduced. It is not. Measured on **three** `git archive`
copies, each **verified** to hold the identical block list, with my own
confounding `next_action` stripped from all three:

| | block list, store present |
|---|---|
| pre-row-C `2acec65` | **NOT REFUSED** |
| round 1 `0ef9ccb^1` | **NOT REFUSED** |
| round 2 `HEAD` | **NOT REFUSED** |

The identical line scan sits at `2acec65:4819`, **before row C existed**.

Round 1's structural `parse_linkage` read *does* see a block list — I confirmed
it, and it reports `002-linkage.md krs[].tasks` **with no line number** — but it
sits behind the `else:` that runs **only when the store is absent**, which was
round 1's own data-loss defect and the thing round 2 was sent to fix. The
reviewer appears to have measured that branch with the store removed and
generalised from it.

**So the FAIL stands on the rung's own question** — does this code do the wrong
thing on an input a user can produce — and round 2's mandate was exactly that
rows the 001/002 registers name stay protected. What changes is the fix: round 3
must make the document scan **structural and still carry a line number**. Round 2
traded the structural read *for* the line number, and that trade is the bug.
Reverting to `parse_linkage` would re-lose the line number that makes a refusal
actionable.

### Exposure: latent, not live — unlike round 1's

All **24** `tasks:` entries across `001/002/003-linkage.md` are flow lists, and
both probe rows are correctly refused on `main` right now. **Nothing is
deletable today.** Round 1's defect was live; this one needs a register to come
to use block style first. Recorded so urgency is not inherited by assumption.

### The rest of round 2 checks out

The reviewer confirmed independently: deconfounded two-armed `purge`
differentials, `krs --phase 001/002` printing their own KRs, site 6 going
**100 → 23** unlinked with `CURRENT` at 001, byte-identical output at 003, the
seam count four→three, the **deliberately** unmerged `perry-lint` seam (verified:
it returns `krs+edges` only and attaches store `unlinked` solely for the current
phase, so the rules genuinely conflict), the seventh reader's writer
classification, and the 16/14/31/27/16 counts. Its own 13 mutations: 10 red,
**3 green**, all in the new `parsers` helper — round 3's to close.

## Fixing the rows the clustering review exposed

The clustering critique was about my taxonomy, which is stored nowhere. What it
*did* surface was row-level data that is wrong or absent, and that is storable.

### Twelve rows could not explain themselves — and they were the stalled cluster

`perry-lint --summaries` reported 12 open rows with no summary. **Ten of them
are exactly the D009/D010/D011 rows I had flagged as the one cluster with zero
movement.** That correlation is the finding: **the workstream nobody picks up is
the one whose rows print their own title back when asked what they are.**

All twelve now carry one, written from the design documents rather than
paraphrased from the titles — `DESIGN-009 § 6`, `DESIGN-010 § 6`, `DESIGN-011 § 6`.
Each names why the row exists and what is true when it is done, and where a
design declares a **gate** the summary says so: `TASK-188` is D010's gate and
`TASK-189` may not run unless its refusals were right; `TASK-191` is D011's gate
and steps 3–5 are decoration if it fails.

Two were verified against behaviour rather than described from their titles:
`TASK-137` — the intake track declares `new → triaged → in_progress → resolved`
and **all 43 intake rows sit at `triaged`, none at `new`**, so the declared first
stage is unreachable; `TASK-327` — the guard tests `len(value.splitlines()) > 1`,
which a **trailing** newline passes because that call returns one element for it,
while the canonical `line_break_at` in `viewer/tables.py:76` catches it.

`146 of 146 open rows carry a summary · 0 blank`.

### `TASK-384` — found while fixing them, and it nearly aimed the fix wrong

Reading summaries out of `perry-state` made **every** row look blank, so
`TASK-186`/`187` appeared to need one when the store says they already carry it.
Measured three ways: `perry-state --section board` publishes 145 rows and **0**
carry a `summary` key — the key is absent, not empty; `perry-task list --json`
carries it on **133**, matching the linter exactly; and `summary` appears **zero
times** in `schema/state-schema.json`.

So it is a field `add` **refuses to write a row without**, that the linter reports
on, that `perry-explain` is built on, published by one payload and not the other,
and declared in no schema. Same shape as `TASK-271` and `TASK-382` — except those
are a *value* disagreeing and this is a field's *existence* disagreeing, which is
worse for a consumer because there is nothing to compare.

### Four `review` cells claimed an activity nobody was performing

All four opened with `V4 REVIEW.` — which reads as *a review is happening*. None
has ever had one, and none can be dispatched: no criteria exist. Each now says
so first, in front of the author's original cell, which is preserved verbatim.
**The point they now make out loud: this is unverified merged code, not work in
progress** — and `TASK-278`'s V4 finally ran today and FAILED on data loss that
had sat on `main` since its merge.

### `design-link` existed and not one row used it

**0 of 145.** That is the whole mechanical cause of `TASK-355`'s number. Declared
it for **20 rows whose title already names its design** — transcription of an
existing declaration, not attribution anybody guessed, which is what Perry's own
rule requires. `DESIGN-006` 1, `DESIGN-009` 3, `DESIGN-010` 4, `DESIGN-011` 5,
`DESIGN-015` 7 including the two already closed, since `design-link` is
store-only and survives `done` — *pending hand-off is a question about finished
work*.

**Pending hand-off 15 → 10.** `TASK-355`'s own headline — *every* locked design
reports zero — is now false for six, and the row is corrected to say what remains
and why it is different work: for the other ten, the rows do not name their
design, so linking them is a judgement rather than a transcription. It also now
records that `DESIGN-016` reported 9 references **without any `design-link`
record**, so `impl_refs` has a second source that row must identify before
prescribing a fix.

`perry-lint` warnings 39 → 29, 0 errors.

## Round 3 merged — the guard detects structurally and keeps its line number

`TASK-278` at `review`. Both round-1 defects and round 2's block-list gap are
closed. **Verified independently at the FINAL commit**, not at the one I checked
mid-round.

- **Two-armed differential**, both copies verified to hold a byte-identical
  block-list register (`md5 bde32dd4`), confound stripped from both: **before
  deletes, after refuses naming `002-linkage.md:70`** — the *item* line.
- **Flow lists unchanged**: all three probes still refuse, naming `:16`, `:24`,
  `:69`.
- **The quoted-key shape** refuses with `(line not located)` — detection covers
  it, line-location deliberately does not, and it **fails closed**.
- **My own mutation**: `parse_linkage(text)` → `parse_linkage("")` at
  `bin/perry-task:5091` turned **two named tests** red, both the quoted-key
  ones. Restored from the ref, byte-verified `1e034c85d98ae433`, 43/43 green.

### The round's best finding was about its own code

**`M9`: deleting the structural read *entirely* broke nothing.** This round's
deliverable was **dead weight as first tested**, because the textual locator
already found every fixture id. Closing that is what forced the **key** axis into
the enumeration — and the two tests my own mutation just reddened are the ones
that closure produced.

**Shapes: 3 axes, 28 cells, 16 id-carrying** — not the two it was handed. Value
(7 `parse_map` branches, 4 id-carrying) × key (`tasks:` vs quoted) × location
(`krs[]`, `agents[]`). Round 2 had **4 of 16** open. And the set has a **last
element**, which is what makes it a Bound: a flow list split across lines is not
a shape, because the parser raises on it.

Mutation **13 planted, graded three times: 7/6 → 12/1 → 13 red, 0 green**, with
round 2's three closed as well.

### A method finding worth more than the fix — now a knowledge card

The round **nearly filed a false "no new failures"**.
`test_contract_key_parity` was **green** in its baseline and red at the end. It
re-ran the module alone, as our own rule says — and that **did not settle it**,
because the test is red alone in *both* trees. Only a **full parallel run at the
base** showed it red there too. **The baseline's green was the flake.**

That refines a rule I hold and have acted on all week, so it is written down:
`knowledge/verification/a-single-baseline-run-is-not-a-baseline.md`. It also
records the three different, all-correct baselines measured on this repository
today — 1, 2 and 3 reds — and why: a baseline is a property of *a commit and an
invocation*, and one that records neither cannot be compared to anything.

### Three rows filed, two handed over by the round and one caused by me

- **`TASK-385`** — **the `TASK-373` remedy reddens the repo-scanning tests.**
  Every brief this session told agents to keep scratch inside their own
  worktree; an agent that obeys creates a directory of Perry source copies, and
  `test_header_index_is_the_only_fold` counts them as real readers. **My
  instruction, found by the agent I gave it to.**
- **`TASK-386`** — a **pipe-written `tasks:` value declares an edge the reader
  silently drops**: it parses to one string carrying a trailing newline, and the
  lookup matches exactly, so no KR counts it and no check reports it missing.
- **`TASK-294`** got a live reproduction rather than a new row. Writing that
  knowledge card **the documented way** took `perry-lint` from *"knowledge/ holds
  3 file(s) Perry did not write"* to **4** in the same run. The sharper half:
  `knowledge/INDEX.md` still reads `Active: 0 … (no digests yet)` beside four
  cards, while calling itself auto-maintained. **That is why NS-01 fires** — and
  the remedy it offers, `/perry relocate perry`, is a no-op, because the state
  root already *is* `perry`.

## `TASK-155` written up properly — and the write-up corrected my own framing twice

Recording today's reproduction on the row surfaced two things I had wrong.

**First: the row is not only about what I reproduced.** Its original subject is
**KR freshness** — bumping `updated:` moves the staleness reference of every
asserted `current`, because `asserted_at` is read from it at
`asserted_scope: register`. What I hit is a **second consumer**:
`perry/linkage.jsonl`, built today, takes `declared_at` from the **same field**.
So one field now carries **three** facts — when the graph changed, when a number
was arrived at, and when each edge was declared. I nearly filed my half as if it
were the whole row.

**Second, and sharper: the fourth writer inherited the defect and not the
mitigation.** The row's own summary warns that *"the cheapest wrong outcome here
is a fourth disclosure."* What shipped is worse — a fourth writer with **no**
disclosure:

| | reads `updated:` as a date | discloses what it re-dates |
|---|---|---|
| `bin/perry-goals:2226` | yes | **yes** — builds `redated`, returns `current_assertions_redated`, prints a ⚠ naming every KR |
| `bin/perry-tasks:1612` | yes | **no** — validates the *format*, refuses a day-only value, says nothing about the 115 records it rewrites |

`perry-goals`' own comment says why the disclosure exists: the real fix is **a
per-KR assertion date, a new field in `schema/state-schema.json`, behind this
project's safety gate** — so *"naming it on every write is what keeps it from
being discovered as a silent number months later."* **That purchase was not
carried forward.** Filed as **`TASK-387`**, and it is deliberately not "add the
warning to `linkage-write`": a mitigation living in one writer's body will be
skipped by the fifth writer too, so the question is whether the obligation gets
enforced or stays documentation.

**Third: I corrected my own proposed fix.** I had written that the fix shape was
"obvious — narrow `linkage-write`". The code says the real fix is the gated
schema field, which is **why this row is blocked**. My narrowing is a *smaller,
separate* option that addresses the provenance consumer without touching the
gated one — and it is now backed by evidence rather than argument:
`perry/linkage.jsonl` **already holds both kinds of date**, 115 at `2026-09-03`
via `link` derived from `updated:`, and 2 at `2026-09-07` via `add` written
per-action by row D. Per-record and file-derived dates coexist in one store
today, and only the import path still derives. Whether to take the small option
before the gated one is a question for the user, and the row now says so.

**The false alarm is recorded as a choice, not an accident.** `perry-state`
reports `P003-O2-KR1` and `P003-O1-KR2` stale, naming `TASK-283` and `TASK-067`
moving on 2026-09-04 — **after** the `2026-09-03` assertion timestamp and
**before** my 2026-09-07 measurement. Re-verified today that `O2-KR1` is still 0
(one `parse_tracks(` call site at `bin/perry-state:1172`, `tracks_source = store`).
The number is fresh; the timestamp attached to it is not. And the standing
warning's remedy — *re-measure and run `score-phase`* — **cannot clear it**.

## ADR-018 — the process is calibrated to consequence; Perry is not changed

The user asked why iteration is slow and whether the process can be cut. The
measurement, and the three parts they approved, are `ADR-018`.

**The ratio, measured**: skill prose — the product — **8,469 lines**; `bin/` +
`viewer/` **37,757**; `tests/` **73,863**. **Machinery to product is 13:1, and
the product is 7% of the repository.** `DESIGN-014` estimated 90/10 and was
optimistic. Tests are **1.96×** the code.

**Option 1 — one materialisation per fact, deleting the store/document split
and its 12 `build`/`write`/`diff` subcommands — was put to the user and
rejected**, along with reversing `ADR-017`. The reason is not cost-blindness:
**the consistency those 217 edits buy across the user's own documents is the
point**, and Perry's own pitch includes that its prose is good enough that an
agent reading it produces work a person would have asked for. A spec whose
identifiers disagree with themselves undermines exactly that. I had priced only
the cost.

### What landed, and it is prose in two pages rather than a mechanism

**`review.md § 0` — the rule that lowers a rung.** The schema has carried the
rule that *raises* one since `DESIGN-003` — consequence, not shape; V5 minimum
for anything outward-facing or irreversible — and **never had one that lowers**.
So a row got V4 because someone thought of it, and `§ 6` already measured that
bill: **20 rows entered V4 and 74 rounds were burned**, 3.7 each, two reaching
round 11. Now V4 is spent where a defect **destroys unrecreatable state, reports
a wrong answer to someone with no way to tell, or weakens a gate between a user
and either**. Below that line the rung is **V3 as a default, not a concession** —
**159 of 209 closures already are**. A test that is *wrong* — green while the
code is broken — stays V4; an untidy one does not.

**`dispatch.md § 0` — dispatch is not free.** Its fixed cost does not scale down
with the change, and its failure modes are not the change's. Across eight
dispatches in one session: **seven stale bases** (`TASK-381`), **two scratchpad
collisions** (`TASK-373`), one mutation left in a tree, and one agent that
**reddened the suite by obeying its isolation instruction** (`TASK-385`). Four
of that day's seventeen rows exist only because work was dispatched. The test is
not size — **it is whether a second context earns its setup**.

**Both edits were made inline rather than dispatched**, which is the rule
applying to itself.

**Part C is a measurement, not a deletion** — `TASK-389`. The suite is
classified per module into behaviour / convention / mixed by *what a failure
would mean*, with the cost of losing each convention guard named, and **the
round is forbidden from editing a test**. Deleting on an estimate is the
irreversible half.

## ADR-017 step 1 stopped at the gate, and my brief named the wrong lines

Zero readers widened, and stopping was right.

**The gate is `schema/state-schema.json:1303`** — `id_pattern` `^KR-O\d+\.\d+$`
on the OKR table's `Id` column, enforced per row at `bin/perry-lint:1203`, and
**reproduced rather than asserted**: a fixture in the new grammar draws
`OKR.md [bad-id] id 'O1-KR1' does not match`. **My brief guessed 863, 911 and
286 and all three were wrong** — the first two are the phase form, the third a
prose list. Verified here before merging.

**It declined to widen the parsers anyway, on a substantive ground**: 1303 *is*
the definition of an overall KR id, so widening `_RE_KR_ID` while it stands
would leave Perry's **parsers accepting an id Perry's own linter calls an
error** — the two-readers-one-grammar defect ADR-017 exists to close.

**Its enumeration beat mine and the method is worth reusing**: rather than my
six sites, it compiled every string literal across 152 files and evaluated each
against **both** ids in six contexts, counting a site **iff its answer differs
between them**. That cut four of my six as phase-only, folded two more as call
sites rather than patterns, found one I missed (`parsers.py:2267
_RE_KR_BULLET`), and established that `perry-explain:80` resolves **neither**
form today. Twelve differing sites.

`USER-919` puts the two additive schema edits to the user. Neither removes the
old form.

## ADR-017's document half: 50 classified, none renamed, and the trap is silent

**30 live references · 14 historical quotations · 6 mentions of the grammar
itself.** Nothing renamed, and that is the deliverable.

### The document half cannot land alone — but not for the reason I gave

My brief said a premature rename would create dangling ids **a linter reports**.
The round **tested that instead of believing it**: it renamed `DESIGN-011`'s
`Linked OKR` to a grammar nothing resolves and re-measured —

```
perry-lint            0 errors        (unchanged)
perry-diagnose        finding set     byte-identical, no LOAD-02
user_load.dangling    []              before AND after
```

**Verified here**: `viewer/parsers.py:3397` parses `Linked OKR` into a dataclass
field, sets it at `:3409`, and **nothing reads it** — no consumer in `bin/`, not
one reference in `tests/`. So a premature rename would dangle **silently with
every instrument green**. Passing lint there would have proved nothing.

Filed as **`TASK-390`**. It is the mirror of `TASK-355`/`TASK-282`: the
design→goal edge is unchecked in **both** directions, and `impl_refs` is the only
one of the two any tool computes.

### The round found that my brief contradicted a locked decision, and obeyed the decision

`ADR-017`'s Consequences: the design headers *"are locked; a `## Changes` entry
records the rename **rather than editing the header**, unless the lane decides
the header field is metadata rather than body."* **My brief named those same
headers as the clearest live references to rename.** It classified them live on
the merits and **did not touch them** — the correct handling of an instruction
that contradicts a locked decision, and it said so rather than quietly picking.

**The `decide` lane has now settled it**, in a `## Changes` entry on ADR-017:
**the field is metadata**, because it has no consumer, and that is measured
rather than argued. So the seven headers are edited directly **inside the atomic
rename** — *"one edit, not a sweep"* — rather than becoming seven `## Changes`
entries in locked designs.

### ADR-017's own count is off by one

Context says *"**Six** later design headers (008 through 014)"*. **There are
seven** — 008 through 014 inclusive — and **nine documents corpus-wide**.
Verified independently. The round left the sentence alone deliberately, as a
dated claim inside a quotation-bearing clause; the correction is in the Changes
entry, which is where it belongs.

### Its control was better than the one I asked for

`DESIGN-007:102` says a phase file *"**holds**"* a reproduced table row
containing `KR-O1.1` — and **that phase file contains zero occurrences of it
today**. The sentence already records a past state, so rewriting it would
fabricate a row that never existed **in either grammar**. A naive sweep also
turns line 258 into *"the new form replaces the new form."*

### What guards the quotation class: nothing, yet, and it said so

`reference/style.md` already requires `[[old-form]]` markers on deliberately
quoted obsolete ids, so `grep` returns deliberate survivors and nothing else.
The round **did not apply them** — `KR-O2.1` is not obsolete yet and marking it
today would assert something false. They belong in the same edit as the rename.
**Until then a wrongly rewritten quotation is caught by a person reading the diff
and by nothing else.**

## ADR-018 part C: the suite is a quarter convention, and my own numbers were wrong

**The hypothesis is only partly supported, which is what measuring is for.**

```
behaviour            55,297   74.9%
convention           17,619   23.9%
shared scaffolding      947
                     ──────
                     73,863
```

A **quarter** defends against contributors, not the majority I guessed. And
convention costs **less time than lines** — ~15% of module-seconds against 23.9%
of lines, stable across two runs.

### Both of ADR-018's Context numbers are mine and both overstated the case

| Context said | measured | why |
|---|---|---|
| `bin/`+`viewer/` **37,757** | **39,177** | my glob was `bin/*.py`; it does not recurse into `bin/lib/` |
| product prose **8,469** | **16,291** | four globs caught about half — missing `modes/`, `packs/`, `templates/`, `state/`, `schema/README.md`, most of `work/` |
| machinery : product **13:1** | **7.0:1** | `113,040 / 16,291 = 6.94` |

**The ratio was inflated because I undercounted the product, not because I
overcounted the machinery.** Verified independently, and recorded as an ADR-018
`## Changes` entry rather than edited quietly into the Context.

**Parts A and B still stand, on evidence that never used the ratio**: A rests on
`review.md § 6`'s own 20-rows-74-rounds, B on eight dispatches producing seven
stale bases, two scratchpad collisions, a mutation left in a tree, and an agent
reddening the suite by obeying its brief. **What weakens is the framing, not the
decisions.**

### The finding I was most likely to get wrong

**"Self-referential" is not a synonym for waste.** 7.6% of the suite tests the
suite — and the two strongest *keeps* are in it:

- **`live_state_expectations`** (1,202 lines) catches tests that read Perry's own
  live board as their expected value. **Eight recorded instances, and nothing
  else catches it.**
- **`tree_guard`** (1,337 lines, the slowest module in the suite) exists because
  a test once **discharged a real board row in the live checkout**, unnoticed for
  months.

My filename scan was half right, as I flagged it might be:
`test_spec_scannability` is **mixed** (483/847) and `test_shipped_vocabulary` is
**mostly behaviour** (~180 convention of 1,254) — it runs `--help` on every
shipped tool and checks templates copied verbatim into a user's repo.

### The deletion candidate is now narrow, and specific

`test_header_rule_harness.py` — **1,706 lines**, ~110 synthetic probes planted
into a temp copy, asserting what a **test helper** reports, with **zero
assertions touching a Perry command, document, store or payload**. Plus **399
lines of dead test code with no importer**, aimed at two deleted tools, and
**two tests that cannot fail for the reason they claim**.

**A few thousand lines, not a third of the suite.** No test was modified —
`git diff main -- tests bin viewer` is empty on the branch — and deletion stays
the user's decision.

**One process note worth keeping**: `ADR-018` did not exist when the round
started and landed on `main` mid-measurement. It read it and **corrected its own
report rather than publishing a claim that had just become false**, then showed
`bin/`, `viewer/` and `tests/` byte-identical between its base and the tip so
every number still stood.

## Four dispatched; `TASK-383` read before edited, and its own fix was wrong twice

**Dispatched on `e928ed4`**: ADR-017 step 2 (the atomic rename), and the three
DESIGN-015 V4 rounds — `TASK-278` round 3, `TASK-279`, `TASK-281`. All four
carry the pinned base, scratch **outside** the repo in a uniquely named
directory, and the instruction never to write an id into a board cell. The three
reviewers are told step 2 may land under them and to measure against their own
base, never a moving `main`.

Each V4 brief names **what the PMO already verified**, so the round is spent
where mine was not — and each names the one judgement worth pressing: for `278`
the **Bound** (3 axes, 28 cells, 16 id-carrying, and whether that is the right
count), for `279` the **five crash points** (is five the set?), for `281` the
**population choice** now that the numerator is no longer zero.

### `TASK-383`: I read the code first, and the row's fix was wrong twice

The row proposed making `perry-goals link` decide *already-linked* from the
document. **Both halves of that turn out to be wrong.**

1. *"`add --kr` should also write the document"* — **forbidden by the hand-off
   contract**, not merely undone. `phase/<NNN>-linkage.md` is the **`goals`**
   lane's file; `work` may not write it. `linkage_edge_change`'s own docstring
   says `add --kr` is *"the `work` lane's **one** permitted write to
   `linkage.jsonl`"*. The store-only write is the contract working.

2. *"`link` should read the document instead"* — **refuted by the code it would
   change**. `linkage_graph` is store-first **on purpose**: the refusals *"are
   answers about what is true of the project, and after row C what is true of
   the project is what the store says. **Asking the document instead would let
   `link` accept an edge every reader already carries**, or refuse one none of
   them does."* The suggestion would reintroduce exactly the defect that comment
   exists to prevent.

**What is actually true is structural.** `link` writes the document **and** the
store together under one lock, as a pair. `add --kr` writes only the store,
because it cannot write the other half. `DESIGN-015 § 5.5` permits an `edge`
from **both** lanes. So a `work`-written edge is invisible to the `goals`-owned
document until a `goals` action mirrors it — **and no such action exists.**

**So the drift check conflates two states**: *drift*, where the two disagree
about a record both should carry, and *pending*, where a `work`-written
`via: "add"` edge has not yet been mirrored. Reporting pending as drift is what
makes the verdict useless — and simply excusing `via: add` would be the
green-by-default trap, because the document would fall behind forever with
nothing saying so. **Count them separately; let `linkage-diff`'s exit follow
drift only.**

**Deferred, and not because it is hard**: that logic is `bin/perry-lint`'s
`_linkage_drift_rows` — **the exact code `TASK-278`'s V4 is reviewing right now**
and must verify the drift verdict of. Editing it mid-review would invalidate
that round. The row is `blocked` on those verdicts.

**This is the second time today that reading before editing overturned a fix I
had written down myself** — the first was row E, which I briefed as `TASK-383`'s
answer and which measurement showed to be a 58× worsening.

## `TASK-279` PASSes V4 — and the round went four places I did not

Closed at **V4**. `P003-O3-KR2`'s chain now has A, B and D verified.

**Seven crash points, not five, and the reason is structural.** Row D's harness
kills only before **canonical renames** — and the event append is
`open(...,"a")`, not a rename. So the crash point row D's own *"what I did not
check"* names was **unreachable by its own harness**. The round drove three more
with `SIGKILL`. **The spec's requirement holds at all seven**: the edge never
survived alone.

**But two of the new points expose a blind spot that belongs to row F, not row
D.** After a crash before the event append, `same_action_linkage` reports
`current=null`, denominator 0 — and **`store_edge_without_event`, the detector
built for exactly that half-landed shape, reports empty**, because it is gated on
the very `add` event the crash destroyed. Both arrived in `16ea01d` — **`TASK-281`**
— after row D and outside its file scope. `TASK-281`'s V4 is running
concurrently and **does not have this**; it is carried on that row for when it
returns, with the note that a PASS reached without seeing it rests on narrower
ground than it looks.

**The round-2 scope holds; its justification does not.** Mutating
`LINKAGE_IMPORT_ACTOR` reddens a test round 2 never mutated, and deleting the
anti-vacuity guard makes the test pass vacuously — so the scope is pinned and the
guard is load-bearing. But measuring `--actor agent` against `--actor goals`,
**the KR counter scores them identically at 100%**. Round 2's stated reason —
that such a record is *"a genuine lane lie"* — is **factually wrong**.

### `TASK-391` — a documented flag combination breaks the suite, permanently

**Reproduced before merging.** `--actor` is documented at `add --help` line 150.
`add --kr <KR> --actor goals` appends
`{"actor":"goals","via":"add"}` and takes `test_linkage_import` from 1 failure to
2. **The linkage writer is append-only with no retraction, so nothing Perry ships
can withdraw the record.** A user following the help text reddens the suite
permanently in one invocation.

Root cause is one asymmetry: `bin/perry-task:2797` takes the lane **from the
caller**, while the importer **hardcodes** it — and the test round 2 scoped to
`actor == "goals"` reads the field as if only the importer could write it.

**Filed rather than FAILed, on an argument I accept**: the spec never mentions
`actor`, `DESIGN-015 § 7` records that nothing enforces the lane table yet, the
record is **true** — the goals lane really did declare it — and the module is
already permanently red on any `add --kr` under `TASK-383`.

`TASK-372` confirmed again: the round could not use `perry-restore-check --root`
on a scratch copy and **hand-rolled the comparison rather than substituting a
weaker check**.

## `TASK-281` FAILS its V4 — the KR can be inflated by typing spaces

Row F is not done. Both defects **reproduced here before merging**, each in one
command.

### Defect 1 — whitespace inflates the KR, silently and upward

`bin/lib/__init__.py:765-766` admits a row on the **`add` event's word alone**.
`add --kr "   "` writes a **truthy** `kr` onto the event; `bin/perry-task:2778`
then strips it to `""` so **no edge is written**; and the `if not args.kr`
warning never fires, because the argument was not falsy where it is tested.

```
before   KR 18.18%   store 123 records
after    KR 25.0%    store 123 records   ← nothing written
event    kr = '   '
```

**A user can raise this KR by typing spaces**, and the success line does not even
mention `linkage.jsonl` while the computation claims the row *"answered the KR
question in their own `add`"*. **This is the exact dishonesty the KR exists to
prevent.**

### Defect 2 — the store's only numerator path has no writer

`bin/lib:740-741` requires `{"kind":"unlinked","via":"add"}`. `via: "add"` is
hardcoded on **edges only** (`bin/perry-task:2798`); the other writers hardcode
`"link"`. Measured: **deleting every `via:"add"` record — 123 → 121 — left the
number at exactly 25.0%.**

So the computation **reads only the events**. The spec's own warning was that *"a
round that reads only the store will produce a number that looks right and
measures something else"* — what shipped is the same failure from the other side.

### `M13`'s closure does not reach something real

I asked the round to press this hardest and it did. `unlinked(task, "add")`
appears **three times in the whole repository, all hand-built in the test file**.
Row F read the emptiness of that set as a property of **today's data**; it is a
property of the **code**. So `M13` was closed against fixtures that can never be
produced.

### It should have caught `TASK-382` — and the same miss produced a fourth publisher

The round verified *"nothing else reads the asserted value"* by enumerating
readers of **`metric`**. The field whose provenance it changed is **`current`**.

Confirmed here: `perry-goals list`'s **terminal** renderer prints the one
**measured** KR as `— asserted`, then a blanket footer — *"no `current` here is a
measurement — every one is asserted by an author"* — **in `bin/perry-goals`, the
file row F edited**. The `--json` and terminal halves of the same command,
one flag apart, now disagree: `0.0` measured versus `— asserted`.

`TASK-382` retitled and re-scoped: **four publishers, and the fourth states a
falsehood.** It is **one wrong search term**, not four oversights.

### Carried from `TASK-279`'s V4, which this round did not have

After a crash before the event append, **`store_edge_without_event` — the
detector built for exactly that half-landed shape — reports empty**, because it
is gated on the very `add` event the crash destroyed. It arrived in `16ea01d`,
row F's own commit. Also on the row.

### What the round got right and must not be redone

**The same-action property works with the real tools, not just fixtures** —
`add --kr` against `add`-then-`perry-goals link`, and the second stays
`never_answered` despite holding an edge to the same KR. The control holds, the
register change holds, and `TASK-155`'s trap was avoided with all 115
pre-existing records still dated `2026-09-03`.

## `TASK-278` PASSes V4 — proved as a superset, not sampled. Row C is done.

**DESIGN-015 row C closed at V4 after three rounds.**

**The round did not re-run my differential, which is why it was worth its cost.**
It enumerated the shape space from `viewer/parsers.py`'s own branches and
measured **15 cells** in a scratch copy, asking of each: does lint accept the
register, does a reader honour the edge, what does `purge` do.

```
refused   in all 11 cells a reader honours
proceeded in the 4 no reader resolves — 3 of which lint grades as errors
violations: 0
```

**Then it closed it as a proof rather than a sample**, which is the right shape
for this claim: `kr_for_task` (`viewer/parsers.py:1197`) iterates the same two
levels with the same membership test as the structural half and **does not
short-circuit** — so **the guard is a strict superset of what any reader can
resolve.** That is worth more than any number of cells.

### The Bound is wrong about its own size — my main worry, answered "yes, but safely"

Axis 1 reproduces. **Axis 2's "exactly 2" is a behavioural partition, not a
count**: `str.strip("\"'")` removes *any run* of quote characters, so the
spellings are unbounded while the behaviours are two. And **one placement sits
outside the three-axis model entirely** — `- tasks: [...]` as a KR list item's
first key, handled by `parse_list`'s own branch, lint-clean and reader-honoured.

**The guard refuses it anyway**, so it is a finding and not the FAIL. Filed with
two more instrument findings as **`TASK-392`**: mutation `V2` survived green (the
blank-line skip is unasserted — behaviour correct, coverage missing), and round
3's confound sweep covered board cells, stores and phase documents but **not
evidence documents** — harmless on that run *by luck rather than by sweeping*,
and the same class as the confound I created myself earlier today.

### A correction to a row I filed

**`TASK-386` said the pipe-written `tasks:` value drops an edge *silently*, with
"no check reporting it missing". That is false.** Reproduced here: it draws a
**hard lint error** — `[bad-type] objectives[2].krs[1].tasks must be a list`.

What survives is smaller and still real: the **reader** still drops the edge, so
the linter calls the register malformed while the reader half-honours it — two
answers to one question, not a silent loss. Row retitled, re-scoped, and
**downgraded P1 → P2**, because the P1 rested on the silence.

`M9`'s closure is **real and stronger than round 3 claimed** — the inline shape
is a second input making the structural half load-bearing, and unlike the quoted
key it is **not** reachable by widening the locator regex. `M5`'s comment gap is
**closed, not carried**.

## ADR-017 step 2 landed — one grammar at both levels, in one commit

**136 occurrences renamed**; repo-wide old-form count **557 → 421**.

```
OKR.md                41      okr.jsonl             40
phase/001-linkage.md  10      phase/003-linkage.md   6
linkage.jsonl          6      design/ + decisions/  33
```

Verified on the merged tree: **`OKR.md` carries all 20 ids in the new form and
zero in the old**; `perry-goals krs` and `list` both exit 0 with the
`Linked overall KR` column reading `O2-KR3`; `perry-state --section okr`
answers; lint 0 errors.

**18 quotations preserved, every one now carrying `[[old-form]]`** — 17 inline,
one in the introducing sentence for `DESIGN-009`'s fenced JSON per the rule's own
carve-out. **That marker is the only automated guard the quotation class will
ever have**, and this was the commit that could apply it, because the old form
became obsolete here. The control held: `DESIGN-007:102` and `:258` gained
markers and **no id changed** — the case where a naive sweep fabricates a table
row that never existed.

### It corrected three of my own instructions rather than quietly complying

- **Verification item 1 was unsatisfiable as written.** A whole-repo grep cannot
  return only quotations, grammar mentions and `tests/` — **421 old-form
  occurrences remain** in evidence, journal, handoff, snapshots, the event log,
  `goals/` and code comments. **Nobody had counted the corpus outside
  `design/decisions`**; the corpus round said so and I did not carry it. It gave
  the census by area and disposed of each by rule.
- **My table's `phase/*-linkage.md = 39` was the whole `perry/phase/` tree.** The
  glob holds **16**; the other 23 are two frozen snapshots and one closed phase's
  prose, left as history.
- **Nine documents carry a `Linked OKR` header, not the seven** I recorded in
  ADR-017's `## Changes`. All 16 header occurrences moved.

### And it refused a false success

The acceptance asked for **both stores at 0 drifted**. The linkage store was
**already at 1 at the base** — the pre-existing `TASK-383` row on
`P003-O3-KR2`'s `tasks[]` — so that half was **unsatisfiable on arrival**. It
verified the survivor is the *same* row and **said the criterion could not be
met**, rather than reporting it satisfied.

Three renames went beyond the classified 30, **none a silent reclassification**:
`ADR-003:39` and `DESIGN-015:154` were classed as quotations *because of* what
another file or the store said, and this commit changes both — the corpus round
names the `ADR-003` coupling explicitly.

### `TASK-393` — the migration would undo itself, one project at a time

`goals/state/OKR_TEMPLATE.md` still carries **six** old-form ids, and it is what
a new project's `OKR.md` is built from. **Every fresh Perry project would be
minted in the grammar this commit retired.**

It is not step 2's to fix and the distinction is real rather than scoping: step 2
owned **this project's data**; the template is **shipped product**. And a test is
already waiting for it — `ADR-018` part C found `test_shipped_vocabulary` checks
templates copied verbatim into a user's repo, which is why it classed that module
**behaviour**, not convention.

**The row is explicitly warned not to grow into a sweep of the other 420.** Most
of those are history: an evidence document records what was measured under the
old grammar, a journal entry records what was written. **The template is
different in kind — it is not a record of the past, it is an instruction for the
future.**


---

# 续：当日后半段（2026-09-08 从 journal 移入）

## Row F round 2 merged — and DoD item 5 turns out to be unreachable as written

Both FAIL defects fixed, **verified by the PMO in a scratch copy before merging**:

```
add --kr "   "            REFUSED at the writer, nothing written
delete every via:"add"    KR 15.38% → 0.00%   (before: unchanged — the
                          numerator never read the store at all)
```

**The number does not move** — 2 of 13 before and after — and that is the honest
outcome: both live rows hold a real edge and survive a numerator that checks.

Merge conflict in `bin/perry-task` — the one I flagged when dispatching —
resolved by **keeping both** validation blocks: they validate different flags at
the same anchor. Both refusals re-verified after the merge.

### `USER-921` — the phase's last Must-Have cannot be satisfied as written

`bin/lib:741` computes half the numerator from `{"kind":"unlinked","via":"add"}`.
**No writer anywhere produces that shape**: `via:"add"` is hardcoded at exactly
one site, `bin/perry-task:2798`, which writes **edges**; `bin/perry-goals:2022`
appends an `unlinked` record with **no `via` field at all**.

DoD item 5 reads *"a KR edge **or an `unlinked` declaration written by its own
`add`**"*. **The second half has no implementation.** A row that genuinely serves
no KR can only omit `--kr`, which the computation counts as *not answered* — so
**every honest no-KR row permanently lowers this KR**, and 100% is unreachable
**by construction**, not by work left undone.

**This is why the number looks the way it does.** 50% → 33% → 15.38% were never
regressions: the denominator grew as rows were filed, and most legitimately serve
no KR. **The KR measures honestly against a target it cannot reach.**

Two resolutions, and they are not equivalent — **(A)** give `add` a writer for
the declaration, which is what item 5 already describes and makes 100% reachable;
**(B)** restate the KR so omitting `--kr` counts as answered-with-none, which is
cheaper and **destroys the distinction the KR exists to measure** — never-asked
and declared-no-KR collapse into one reading, the exact state `DESIGN-015 § 5.2`
built the derivation to tell apart. **Recommended (A)**, because after (B) a KR
at 100% would tell you nothing about whether anyone was ever asked.

Phase-scoring participation is a User Commitment, which is why this is an ask.

## New tasks added

### TASK-394 — add has no way to declare a row serves no KR, so the honest answer is unrecorded and DoD item 5's second half has no writer

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: add can declare at creation that a row serves no KR, writing an unlinked record with via add inside the same transaction as the row
- **Verification**: File a row with the declaration and show it counts as answered, and that a row filed without it still counts as never asked. Kill the process between writes and show the declaration never survives alone. Mutation: revert the writer and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: P003-O3-KR2

### TASK-395 — perry-okr diff reports an id drift that render --write cannot repair, because render matches rows by the id that drifted

- **Owner**: Coding Agent
- **Priority**: P2
- **Track / mode**: main / project
- **Deliverable**: Either render repairs an id drift, or the limit is stated where a caller meets it — in render's own report and in diff's failure text
- **Verification**: Hand-edit an id, run render --write, and show the file either restored or the limit reported. Mutation: revert the fix and show a named test go red.
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked

## `USER-921` answered (A) — `TASK-394` dispatched, and the gate refused me first

**(A): build the writer, do not restate the KR.** The alternative was rejected
because after it **a KR at 100% would say nothing about whether anyone was ever
asked** — never-asked and declared-no-KR would collapse into one reading, which
is the distinction `DESIGN-015 § 5.2` built the derivation to tell apart.

**The design already specifies the record; only the writer was missing.** `§ 5.3`
counts a row as answered by a `kr` on its `add` event *or* an `unlinked` record
with `via: "add"`; `§ 5.5`'s table assigns that record to the **`work`** lane via
*"`add` with an explicit unlinked declaration"*; and `bin/lib:741` already reads
exactly that shape. So `TASK-394` builds **the one cell of that table never
implemented** and changes no reader.

**The KR will not jump when it lands, and should not** — rows already filed
without `--kr` stay never-asked, which is true of them.

### The length gate refused me within the hour, and I took the remedy

Filing the row, my own `--next` was **1,870 bytes** against the 1,000 I had set
an hour earlier. `perry-task` refused it. I put the account in
`evidence/2026-09/TASK-394-spec.md` and left the cell a pointer — **the remedy
the rule names**, which also satisfies `dispatch.md`'s pre-flight, since a
dispatched row needs a spec file anyway.

That is now **three times today a gate I built has refused me first**: the
journal cap (1,970 lines), this one, and `review.md § 0`, which says two of the
five V4 rounds I dispatched should not have been.

### What the brief carries that the spec could not

**The atomicity bar is seven crash points, not five.** Row D claimed five;
`TASK-279`'s V4 found seven, because row D's harness kills only before *canonical
renames* and the event append is an `open(...,"a")` — so the point row D's own
"what I did not check" named was **unreachable by its own harness**. `TASK-394`
inherits the seven.

**And the green-mutation lesson, by name**: `TASK-281` round 1 closed a green
against a fixture that **could never be produced**, and round 2 had to re-open
it. So every guard this round adds must redden on **an input a user can
produce**.
