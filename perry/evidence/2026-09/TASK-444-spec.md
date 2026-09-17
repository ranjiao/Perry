# TASK-444 — Editable planning draft, resume and explicit finalization

Date: 2026-09-17. Owner: Coding Agent. Priority: P1. Required verification: V4, since writes and approval boundaries affect canonical state.

> Dispatch mode: manual
> Executor: codex
> Subjective verification: independent edit/approve walkthrough
> Touches architecture: existing goals/work ownership, typed draft lifecycle and state readers
> Deployed: no

## Readiness and authorization

Locked DESIGN-020 decision 5 already consents to plans/ under state root; no repeated namespace consent is required. User prioritizes this experience. USER-959 permits isolated implementation before TASK-191; the real interview remains release acceptance through TASK-465. TASK-264 still blocks complete finalization. A bounded draft-only child may implement persistence independently, without closing this parent or claiming unsupported canonical writers. Missing KR writers and first-phase/overall creation writers must be inventoried rather than assumed supplied by import commands.

## Acceptance criteria

1. A draft under plans/<horizon>/<date>-<slug>.md uses the existing locked design's typed frontmatter and a human-editable body. The body is meaningful from the first answer. Python treats body prose as opaque; the agent interprets it.
2. Lifecycle follows interviewing, drafted, approved, finalized or abandoned. Resume after question three preserves the first answers and points to the next unanswered question. Existing adoption/diagnosis recovery safety remains ahead of any startup writes.
3. Chat edits change the requested section; file edits are re-read and preserved. Show <=12 lines of draft summary and a usable file path. Choosing to edit stops for the user; silence and continued discussion are not approval.
4. Approval applies to the actual current draft. A subsequent change must not reuse stale approval. Use explicit typed integrity/state checks and fresh content comparison, never natural-language consent classifiers. Specify exact public fields before implementing them and remain within the existing approved schema scope.
5. Before canonical writes, check writer availability for the full destination. A missing writer leaves all canonical goal/phase stores and phase/CURRENT byte-identical and reports the missing capability. perry-okr write --from-file is an importer, not an excuse to manually author a canonical file first.
6. On successful owning-writer completion, record finalized references. Partial failures do not mark the entire draft finalized. Repeated resume/finalize cannot silently duplicate goals. Preserve the existing writer's transaction/derived-event limits; do not advertise cross-file atomicity without implementing it.
7. The interrupted and next surfaces discover draft state via typed metadata. Invalid or escaping paths and malformed metadata must be visible rather than guessed as no draft. A finalized draft is history, not another canonical goal store.
8. Test interruption/resume, direct file editing, stale approval, missing writer, failed writer and successful isolated supported-writer completion. Independently review the complete user-visible flow. Synthetic cases remain separate from TASK-191 real interview evidence.

## Scope and sequencing

Prefer existing goals CLI and state/read surfaces, a compact goals planning reference and approved plans/ claim. Before dispatch enumerate exact files and existing transaction mechanisms from a bounded implementation proposal. No new service, dependency, generic workflow framework or semantic parser. No live SkyTonight changes, release/publication, rubric rewrites or decided architecture changes.

A useful draft-only slice may be demonstrated separately, but the task is not done until the promised supported finalize path is verified. Unsupported horizons must remain explicitly unavailable. TASK-264 KR writes do not automatically create the whole overall/phase document; any remaining writer gap must be reported as a concrete follow-up rather than silently expanded scope.

## Verification and limits

Exact base/head, targeted tests, committed affected tier, bounded negative/restoration proof and fresh independent V4. Current phase requires net Python/test lines <=0; report feasibility before implementation if the bounded work cannot meet it without weakening tests. Full/slow merged verification and release allocation belong to integration, not this task's author.
