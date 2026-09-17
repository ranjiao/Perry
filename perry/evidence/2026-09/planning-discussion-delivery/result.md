# TASK-192 / TASK-193 / TASK-194 isolated implementation delivery

Implementation delivered for fresh independent review, not task closure or
release acceptance. TASK-191 remains incomplete. USER-959 authorizes this isolated
implementation sequence only; no V4/V5 or architecture PASS is awarded here.

- Branch: `codex/okr-discussion-192-194-20260917`
- Checkout / PERRY_HOME: `/private/tmp/perry-scratch/Perry/okr-isolated-20260917/planning-discussion`
- Actual base (main 0.1.9 plus PMO authorization): `9051a43f78bb4e2f892c678c9b4ab54df8bfa376`
- Final combined HEAD: `1867c7d54651d51f07b82b58933a019b1581270f`
- PERRY_PROJECT and PYTHONPATH unset; TMPDIR: `/private/tmp/perry-scratch/planning-discussion/20260917/tmp`
- Worktree clean; exact commit ancestry and paths checked in [delivery integrity](logs/delivery-integrity.json).

| Task | Exact product commit | Scope and resulting behavior |
|---|---|---|
| TASK-192 | `1d4bc71759c59480d95c2e9313b4e6979e8eca6c` | goals/SKILL.md, setup.md, elicitation.md: declared horizon/spine routing, sourced answer reuse, revision impact and preserved wording; commitment route retains explicit writer |
| TASK-193 | `3a01c057515d1a5e9d993b0ec5dd23b1d1446d40` | setup.md, elicitation.md: response reflection, one push, consequential recommendations, refusal escape, premise disagreement and separate draft approval |
| TASK-194 | `1867c7d54651d51f07b82b58933a019b1581270f` | goals/SKILL.md, phases.md, elicitation.md: shared phase discussion, ten sections, prior learning/capacity/scope reuse, supported-writer boundary |

Final changed paths, all product prose:

```
goals/SKILL.md
goals/reference/elicitation.md
goals/reference/phases.md
goals/reference/setup.md
```

No Python or test edits; net Python/test lines = 0. No schema, runtime, locked
design, architecture, PMO state/evidence/journal/ask, host installation, live
SkyTonight or release allocation changes. No push, publication, delegation or
merge. Main was not modified by this work.

## Criteria and hypothetical review material

All three scenario files are **NOT real human transcripts**. They contain authored
user inputs, actual proposed agent responses, draft consequences and criteria.
They are semantic walkthroughs for an independent reviewer, not automated proof
that a model will behave this way. No live project writer was exercised by them.

| Written criteria | Implementation/review material |
|---|---|
| 192.1, 192.4 | Shared route table, per-turn gap/destination; caps 8/5/5/3; selected horizon never silently starts another |
| 192.2, 192.3 | Provenance and correction rules; revision before/after with unaffected wording retained; no append/finalize fallback |
| 192.5 | [192 scenarios A–D](TASK-192-scenarios.md): rich-context first OKR, revision, conflicting beneficiary/capacity, queue promise and explicit writer handoff |
| 193.1–193.3 | Shared response handling keeps TASK-466 propagation; one consequential question then wait; one outcome rewrite with practical consequences and no invented metrics |
| 193.4 | One offer of up to two remaining questions within cap; second refusal yields with incomplete draft, no appended approval question |
| 193.5, 193.6 | [193 scenarios A–D](TASK-193-scenarios.md): rejected recommendation, activity goal, unknown baseline, both escape branches, fully pasted OKR, premise correction and later section edit |
| 194.1–194.3 | Phase gaps map to the single bank; five-question ceiling; ten sections and quality/architecture/release gates retained; unknowns stay unknown |
| 194.4, 194.5 | [194 scenarios A–C and expanded draft](TASK-194-scenarios.md): first/subsequent phases, prior learning, reduced scope, user-chosen changed threshold, capacity correction, missing writer and overall-only approval |

One inherited discrepancy was reported during implementation: phases.md's old
3–5 KRs instruction conflicted with the lane's existing maximum of 4. The phase
procedure now uses that existing cap and the unchanged rubric's solo/fewer rule.
No new count policy or rubric was introduced.

## Verification receipts

Runner source was read; `tests/run --help` was never invoked. One suite at a time,
4 workers for module runs, no full/slow suite. All runs used the canonical env
above. [run-check.sh](run-check.sh) records command, HEAD, date, exit and tree
hash guard; no durations or checkout files are written. Iteration runs named a
committed parent plus the scoped working diff; final runs used a clean combined HEAD.

| Check | Result | Log |
|---|---|---|
| TASK-192 targeted | 5 modules / 155 tests pass | [log](logs/task-192-targeted.log) |
| TASK-193 targeted | 3 modules / 43 tests pass | [log](logs/task-193-targeted.log) |
| TASK-194 targeted | 5 modules / 191 tests pass | [log](logs/task-194-targeted.log) |
| Boundary clarification targeted | 3 modules / 65 tests pass | [log](logs/task-194-boundary-fix.log) |
| Final HEAD smoke | pass, tree guard unchanged | [log](logs/final-smoke-revised.log) |
| Final HEAD committed affected selection | 18 modules / 595 tests pass; 17.8s; 4 workers; tree unchanged | [log](logs/final-affected-revised.log), [JSON](logs/final-affected-revised.json) |
| Exact ancestry, paths, rubric/design/schema hashes, clean tree, diff check | pass | [integrity JSON](logs/delivery-integrity.json) |

The smoke command was `bash tests/run --tier smoke`. This runner rejects
`--workers` for affected, so the committed module command was:

```
python3 tests/parallel --tier affected --base 9051a43f78bb4e2f892c678c9b4ab54df8bfa376 -j 4 --results /private/tmp/perry-scratch/planning-discussion/20260917/logs/final-affected-revised.json
```

That is the same affected selector used by tests/run; smoke and the external tree
guard cover its surrounding gates. It selects 18/158 modules (7.3% of recorded
module-seconds), not a repository-wide green claim.

An initial affected run on superseded TASK-194 candidate `bc0c9e67` had 594/595
passing tests: [failure log](logs/final-affected.log). The procedure guard read the
noun “records” in a field inventory as a write instruction. The source now states
this as the future writer's returned-field contract; no test or exemption changed.
That clarification was folded into TASK-194 before final-head validation. The
failed candidate is not an extra product commit in the delivered branch.

## Unchanged rubric and limitations

`reference/input-quality.md` is byte-identical to the actual base. SHA-256 before
and after: `399cdb615d6ae7b87c5a82f5a2e26e82d9951607b0e39ac9d5bce50465a74e88`.
Integrity checks also compared the locked DESIGN-011/020, architecture and schema.

The deliverable is authored discussion procedures. It does not implement plans/
persistence, resume, phase/overall finalize or the missing KR creation path.
TASK-444 retains phase persistence/finalize ownership. Generic import/render and
`perry-goals link` are not substitutes. Read-only command receipts:
[goals writer surface](logs/goals-writer-surface.log),
[OKR writer surface](logs/okr-writer-surface.log).
The supported explicit commitment writer and its refusal behavior remain intact.

Existing score-phase, snapshot, pivot and weekly procedures were not redesigned;
none is authorized here as an alternate phase-start/finalize path. Existing
out-of-scope claims and asked decisions remain unresolved. PMO owns registration
of delivery evidence and any later state changes. Fresh independent conversational
review and the real-user TASK-191 release acceptance are still required.
