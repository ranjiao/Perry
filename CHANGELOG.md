# Perry changelog

Generated from release/records.jsonl; edit records through the release tool.

## 0.1.18 — 2026-09-22

patch · phase 004-guided · TASK-480 · delivery TASK-480-backlog-0.1.17-to-0.1.18

### Changes

Product deliveries integrated on main's first-parent line after f31c5d78 (0.1.17), up to 1e57b2f4:
- TASK-474 (ac256a3a, 8b6078f7, ccf47608): `perry-goals phase new|activate|close` writes the phase lifecycle, so opening or closing a phase needs no hand edit of the phase file or `phase/CURRENT`.
- TASK-471 (abfd6cd5): session budgets are checked at safe task boundaries; `perry-context-budget` exports no identity on any Claude Code session, so its gate reports `unknown` there and autopilot falls back to `--max-dispatches`.
- TASK-469 (3f397a85, 728db267): the router sends explanations, state queries and mutations through a bounded startup; explanations read no project state, and the lanes no longer repeat the router's startup steps.
- TASK-472 (25cb21d7, 78a9c5fa, e23065a0): execution and review contracts that bound tool output and repeated review work.
- TASK-470 (dc3e1f51, ecfa2245): smaller runtime instructions and per-command load sets (router about 25% and work lane about 35% smaller); input-quality rubrics move to `reference/input-quality-rubrics.md`.
- TASK-475 (b9680b8f, 3ba47d05, 7d7e9605, 80fda999): `perry-goals objective add` writes a phase objective; `objective add` and `kr add` select a phase by number and refuse an unreadable store.
- USER-978/980/981 (16124fb0, b77b61ed, de595d1f, 0425f82d, c9262965, 6c2cbc79): every `phase/CURRENT` read in `bin/` goes through `viewer/parsers.py`, the phase writer checks the parser, and ARCHITECTURE.md records the release/ pointer exception to NN-1.
- TASK-451 (db74c48a): the schema anchors ARCHITECTURE.md at the code root; `perry-lint --architecture-module PATH` lints a selected component architecture document.
- TASK-476 (af328b36): test_v5_signoff resolves V5 evidence at the state or repo root.
- TASK-452 (13733b21): `perry-state` finds ARCHITECTURE.md where the code is, not under the state root.
- USER-987 (664ca039) and USER-989 (5651e663): ARCHITECTURE.md §7 OQ-1 closed and its preamble updated after TASK-451, TASK-452 and TASK-477.
- TASK-477 (9259f0c6): `perry-diagnose` matches each Perry-owned path at its own anchor, so the code-root ARCHITECTURE.md is no longer reported as an orphan.
- TASK-478 (e4e851a9): `release/manage.py check` accepts a range that introduces the release record together with later versions.
- TASK-479 (672330db): `perry-state --section next` is `perry-next/1.1`, with next-step rules for unstaffed key results, undeclared checks, retro before score-phase, and a mid-week rule that stays unknown; `goals check <KR>` is listed in the goals subcommand index.
- Test-harness commits (3e0255df, 6d471770, 67fa5e3c, 5d661ec6, adfa0720, a2a12a8f, 3d4f0906, cff4d22e, 502eba91 record merge-gate durations; 645791ea makes the fake GNU stat portable to Linux CI): no user-visible change.
Combined allocation for deliveries since 0.1.17, USER-997; later deliveries are allocated one patch each.


### Upgrade notes

- A consumer of `perry-state --section next` sees contract `perry-next/1.1`. It only adds fact names; no key or meaning changes, and `semantics` stays `[]`. A consumer that matches the exact string `perry-next/1.0` must accept 1.1.
- Open, activate and close phases with `perry-goals phase new|activate|close`, and add phase objectives with `perry-goals objective add`, rather than editing the phase file or `phase/CURRENT` by hand. `goals check <KR>` declares a key result's check; the new R-checks-undeclared rule recommends it for a commit key result that has none.
- A project's ARCHITECTURE.md is read at the code root, not under the state root. `perry-state` and `perry-diagnose` look for it there, and `perry-diagnose` no longer calls it an orphan. A project with a separate state root that keeps ARCHITECTURE.md under that state root should move it to the code root. A legacy `Status:` line in ARCHITECTURE.md is no longer read, so `perry-state` no longer warns that it is still a draft.
- On Claude Code the context-budget gate reports `unknown` in every session, main included, and autopilot relies on `--max-dispatches`.
- The release check fix (TASK-478) changes only Perry's own CI; nothing to do for a user.
Local allocation only; no public release.


### Breaking changes

None.


## 0.1.17 — 2026-09-18

patch · phase 004-guided · TASK-468 · delivery TASK-468-20260918

### Changes

`perry-context-budget` binds usage to the actual host and session: an explicit `--session` source or a verified host identity, never the newest transcript file. Claude and Codex adapters report input, cached input, cache creation, output and reasoning separately, deduplicate repeated records, take deltas of cumulative counters, and subtract a forked Codex child's inherited counter. Reports carry host, transcript host, session and parent identity, source, freshness, coverage (Workflow and unmatched children make it partial) and a not_measured list; cost and quota stay unknown. A frozen pre-change baseline is recorded in perry/evidence/2026-09/TASK-468-baseline/.


### Upgrade notes

On Claude Code Desktop the main session and its subagents carry the same identity, so the gate reports `unknown` there and autopilot falls back to --max-dispatches. On the plain Claude CLI a subagent may bind its main session (unverified; settle in TASK-471 before relying on the gate there). OpenCode reports unknown. `scanned_whole_file` is gone; a verdict may be `historical`; a refused bill exits 1. Local allocation only; no public release.


### Breaking changes

The implicit newest-transcript selection is removed: without an explicit --session or a verified host identity the verdict is `unknown`. JSON output drops scanned_whole_file and adds transcript_host, coverage and not_measured.


## 0.1.16 — 2026-09-18

patch · phase 004-guided · TASK-457 · delivery TASK-457-rebased-20260918

### Changes

Five subcommands carry a declared, read-only context bill (DESIGN-017 E2): `perry-context-budget --bill <snapshot|add-task|close-task|dispatch|plan-phase>` sums L0, the lane file and the L2 pages its index row names, and each bill has a pinned budget that a test enforces. Plan-phase's budget is 110,000 bytes (measured 107,747) after main's planning content grew it.


### Upgrade notes

The bill measures declared bytes, not tokens or dynamic reads. It does no session discovery. Local allocation only; no public release.


### Breaking changes

None.


## 0.1.15 — 2026-09-18

patch · phase 004-guided · TASK-456 · delivery TASK-456-rebased-20260918

### Changes

Shipped prose gets per-tier byte budgets (DESIGN-017 E1): L2 reference pages are capped at 32,768 bytes and L3 pages at 24,576, and a page over its tier turns the suite red. The three over-budget pages (work/reference/subcommands.md, work/reference/dispatch.md, reference/diagnose.md) are split along their own sections with every section preserved and every exact reference re-pointed. The root SKILL.md relocate paragraph is a pointer to reference/router-subcommands.md, which carries its rules and reasons.


### Upgrade notes

Links into the three split pages now resolve to their new part pages; old section anchors are re-pointed in shipped files. Local allocation only; no public release.


### Breaking changes

None.


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
