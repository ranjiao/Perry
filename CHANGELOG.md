# Perry changelog

Generated from release/records.jsonl; edit records through the release tool.

## 0.1.14 — 2026-09-18

patch · phase 004-guided · TASK-264 · delivery TASK-264-D3-20260918

### Changes

KRs are added, restated and withdrawn through `perry-goals kr add|restate|withdraw` at both levels. Each change appends a `kr_revision` record to the store that holds the KR (linkage.jsonl for phase KRs, okr.jsonl for overall KRs); one fold rule in bin/lib applies revisions in revised_at order. Every KR reports status and revisions with before/after values. A withdrawn KR leaves every denominator, is reported as withdrawn with its reason, and refuses check, measure and new task links. perry-goals/list is 3.6. The OKR template no longer carries KR table rows.


### Upgrade notes

Stop hand-appending KR records: use `perry-goals kr add|restate|withdraw`. Restate may change any non-identity field, including a target; the change is visible in revisions[]. perry-state's phase.kr_total now excludes withdrawn KRs and phase.kr_withdrawn counts them; perry-goals list's phase.kr_total still counts them. An OKR.md that still carries pre-TASK-236 KR table rows refuses overall kr writes; move KRs to okr.jsonl first. `draft finalize` still refuses. Local allocation only; no public release.


### Breaking changes

perry-state phase.kr_total excludes withdrawn KRs.


## 0.1.13 — 2026-09-18

patch · phase 004-guided · TASK-444 · delivery TASK-444-draft-child-20260918

### Changes

First-OKR planning drafts persist under plans/okr/ through `perry-goals draft create|show|update|approve|abandon|finalize`. A draft resumes at its next unanswered question, records questions_asked, and binds approval to the current content by digest; any later update clears approval and decided_by. Draft read errors surface as non-blocking drafts.errors rows, and dotfiles and editor backups under plans/ are ignored. perry-state reports drafts, and an interviewing draft appears as an interrupted plan run.


### Upgrade notes

Only the first-OKR horizon is supported, and only on an installed project with no existing OKR. `finalize` refuses and names the missing writers: no canonical OKR, phase, KR or task write is supplied, so an approved draft remains unfinalized until TASK-264 and the finalize writers land. decided_by is hand-editable and is a record, not proof of consent. This local allocation does not accept a real-user interview or constitute a public release.


### Breaking changes

None.


## 0.1.12 — 2026-09-17

patch · phase 004-guided · TASK-194 · delivery TASK-194-discussion-20260917

### Changes

Phase planning reuses the shared response-sensitive interview and approved overall wording or prior learning to produce a ten-section phase draft. Approval of the current phase draft is separate from overall approval and from activation. The procedure discloses the unavailable phase writer and forbids manual phase, pointer or KR-store writes to bypass that boundary.


### Upgrade notes

This local allocation supplies discussion instructions only. Planning-draft persistence and full overall/phase writers are not supplied; there is no automatic finalize, phase activation or week start. Overall and phase drafts remain unfinalized until the owning approval/persistence/writer flow supports the requested operation. The existing commitment writer is usable only for supported explicitly approved operations with required terms. This allocation does not accept a real-user interview or constitute a public release.


### Breaking changes

None.


## 0.1.11 — 2026-09-17

patch · phase 004-guided · TASK-193 · delivery TASK-193-discussion-20260917

### Changes

Goal discussions propagate user corrections into dependent proposals, review meaningful premises against the current draft, and preserve accepted intent, rejected suggestions and unknowns. The bounded refusal escape offers only the remaining consequential questions within budget and yields an incomplete draft on a second refusal. Premise review, draft edits and approval remain separate; the advisory rubric is unchanged.


### Upgrade notes

This local allocation supplies discussion instructions only. Planning-draft persistence and full overall/phase writers are not supplied; there is no automatic finalize, phase activation or week start. Overall and phase drafts remain unfinalized until the owning approval/persistence/writer flow supports the requested operation. The existing commitment writer is usable only for supported explicitly approved operations with required terms. This allocation does not accept a real-user interview or constitute a public release.


### Breaking changes

None.


## 0.1.10 — 2026-09-17

patch · phase 004-guided · TASK-192 · delivery TASK-192-discussion-20260917

### Changes

Goal discussions route by the requested horizon and declared track spine, reusing explicit answers and accepted wording with their sources. First-OKR, revision, phase and commitment routes share the question bank with bounded question budgets. Commitment handoff asks only for missing or changed terms: already supplied To whom and Due are reused, and an explicit complete create/amend instruction can already authorize the existing commitment writer.


### Upgrade notes

This local allocation supplies discussion instructions only. Planning-draft persistence and full overall/phase writers are not supplied; there is no automatic finalize, phase activation or week start. Overall and phase drafts remain unfinalized until the owning approval/persistence/writer flow supports the requested operation. The existing commitment writer is usable only for supported explicitly approved operations with required terms. This allocation does not accept a real-user interview or constitute a public release.


### Breaking changes

None.


## 0.1.9 — 2026-09-17

patch · phase 004-guided · TASK-466 · delivery TASK-466-first-okr-response-propagation-20260917

### Changes

First-OKR conversations now carry user corrections through dependent KR, threshold and commitment proposals, preserve accepted facts and rejected suggestions, and choose the next consequential unresolved gap. Replacement targets remain proposals until accepted, within the existing eight-question draft budget.


### Upgrade notes

None.


### Breaking changes

None.


## 0.1.8 — 2026-09-17

patch · phase 004-guided · TASK-446 · delivery TASK-446-one-screen-snapshot-20260917

### Changes

The initial combined snapshot uses at most 12 lines and 1200 Unicode characters, with honest progress and complete supporting details one level down.


### Upgrade notes

Use the detail view for complete objectives, pending choices, alternate recommendations and unknown causes. Mandatory safety and selector information remains visible, with any budget exception disclosed. No data migration is required.


### Breaking changes

No breaking CLI changes. No data migration is required.


## 0.1.7 — 2026-09-17

patch · phase 004-guided · TASK-455 · delivery TASK-455-independent-architecture-review-20260917

### Changes

Integration now selects independent architecture review against the exact integration candidate using six diff triggers, replacing author self-attestation.


### Upgrade notes

Record all six trigger facts for the final base/head. A true trigger requires a fresh independent review; unknown or missing module context blocks acceptance. Rebind selection after any candidate change. No data migration is required.


### Breaking changes

No breaking CLI changes. No data migration is required.


## 0.1.6 — 2026-09-17

patch · phase 004-guided · TASK-447 · delivery TASK-447-next-action-400-20260917

### Changes

Next-action lint now advises a 400 Unicode-character limit and directs users to preserve full accounts in evidence with pointers from concise actions.


### Upgrade notes

Existing actions over 400 Unicode characters now warn without a write-time refusal. Preserve the full account before shortening an action and retain its evidence pointer. No data migration is required.


### Breaking changes

No breaking CLI changes. No data migration is required.


## 0.1.5 — 2026-09-17

patch · phase 004-guided · TASK-460 · delivery TASK-460-typed-position-20260917

### Changes

Derive KR progress counts from declared typed checks, fix ceiling direction comparisons, and keep undeclared checks unmeasured.


### Upgrade notes

No data migration is required. Users may see unmeasured progress until checks are declared.


### Breaking changes

No breaking CLI changes.


## 0.1.4 — 2026-09-17

patch · phase 004-guided · TASK-450 · delivery TASK450-merge-gate

### Changes

Run full merge acceptance through the complete tests/run pipeline on an isolated exact merge tree, preserve typed failure attribution, and export requested timing records with verifiable provenance.


### Upgrade notes

Use tests/merge-check --tier full --record with a new directory outside the caller checkout for full acceptance. --checks is selected-check diagnosis, not a full gate. Preserve exact input refs through verification; import only the emitted durations artifact on the tested code, commit it through the authorized coding role, and verify the receipt, artifact and code identity before acceptance. A separate slow gate remains required.


### Breaking changes

A full merge gate refuses on every failed suite stage, including failures already present on the base. Moved input refs, changed tested code or a mismatched recorded artifact invalidate the acceptance receipt. No automatic main merge or caller-checkout write is performed.


## 0.1.3 — 2026-09-17

patch · phase 004-guided · TASK-464 · delivery TASK464-pack-controls

### Changes

Add discoverable project pack controls, selection-source explanations and conditional software-ops routes and gates using the existing config writer and loader.


### Upgrade notes

Explicit empty Packs disables defaults; unset restores software-ops. Disabled packs preserve artifacts and independently required project policies, including approved release policies. Pack activation alone never means a release adapter is ready.


### Breaking changes

Optional software-ops routing and checks now follow effective selected-and-present pack status. Explicit project requirements and core verification/safety gates remain binding; no project records are deleted.


## 0.1.2 — 2026-09-17

patch · phase 004-guided · TASK-443 · delivery TASK443-proactive-next

### Changes

Add one shared proactive closing step after completed outer state-changing procedures, using the existing deterministic next payload and requiring an explicit choice before running anything.


### Upgrade notes

Set Proactive next steps to off through perry-config to silence proactive closing for this project; absent or on enables it. Passive standup recommendations remain. Dispatched sessions and unfinished planning skip closing.


### Breaking changes

Proactive next steps accepts exactly on or off. Invalid new values refuse; existing invalid values are reported instead of guessed.


## 0.1.1 — 2026-09-17

patch · phase 004-guided · TASK-190 · delivery TASK190-first-okr-bank

### Changes

Add a first-OKR interview bank with drafted answers, bounded questions and an explicit distinction between known facts, proposed targets and unknowns.


### Upgrade notes

First initialization now stops at a visible chat draft and advisory rubric feedback. Persistent planning drafts, resume and finalization are not implemented by this delivery; do not treat the interview as saved OKR state or automatically start a phase.


### Breaking changes

The first-init procedure no longer implies it can persist or finalize goals when no owning writer flow exists. Existing project records are not migrated.


## 0.1.0 — 2026-09-16

baseline · phase 004-guided · TASK-462 · delivery TASK-462-baseline

### Changes

Establish the first product-version baseline for Perry at phase 004 (guided). Perry already provides goals, work and decision lanes; typed task, risk, intake, ask, cadence and OKR/linkage records; deterministic CLI reports; and adapters for Claude Code, OpenCode and Codex CLI. This baseline includes TASK-462: canonical release records, generated version/changelog, integration checks, manual publishing and verified release-channel updates. Earlier development is retained in Git history and is not reconstructed as historical releases.

### Upgrade notes

Use the release channel for a clean consumer checkout, including symlink installations via the explicit --channel release option. Developer checkouts remain report-only. Until a GitHub Release is actually published, release-channel checks refuse; they do not fall back to main. Existing project state is not migrated by this baseline.

### Breaking changes

Product versions follow Perry delivery milestones, not strict SemVer. Minor and patch releases can include compatibility changes; read these notes before upgrading. This release mechanism does not version projects managed by Perry.
