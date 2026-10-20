# Perry changelog

Generated from release/records.jsonl; edit records through the release tool.

## 0.1.29 — 2026-10-20

patch · phase 004-guided · TASK-494 · delivery TASK-494-native-cutover-20261020

### Changes

Retire the finite remaining legacy source/check surface under the actual user-approved 423 exact drops and R0096 Context/Loads grammar narrowing. Keep May touch/Must escalate safety and all retained generic kernel guards. Preserve the source audit as a proposal inventory, separate from actual approval records and final H/V5 acceptance.


### Upgrade notes

Review the immutable retirement disposition, actual approval records and new source acceptance suite. Update old bin/schema/viewer/test consumers to the retained native CLI, skill procedures and tools/. Historical state and evidence stay preserved. Live reconciliation and named human H/V5 sign-off remain separate; no publication is performed.


### Breaking changes

Old executables, typed-state schema/contracts, viewer parsers and obsolete test corpus are removed. The new full/slow gates validate the native kernel and retained skill helpers and do not claim the retired corpus passed. Offline merge receipts replace duration-artifact imports; test receipts are unsigned evidence, not approval or final H/V5 sign-off.


## 0.1.28 — 2026-10-20

patch · phase 004-guided · TASK-493 · delivery TASK-493-native-cutover-20261020

### Changes

Root and lane snapshots, current-state facts, next-step reasoning and shared references use native kernel queries with pagination and explicit unknown/error handling. Startup and high-stakes/ownership safety checks remain skill-side procedures and retained helpers; next-step meaning remains agent work, with no extra kernel method concepts.


### Upgrade notes

Use bin/perry for current structured state and the documented tools/ helpers for host, architecture, startup safety and report-only telemetry. Update consumer command paths. Retain user-owned configuration, safety policy and narrative attachments. Source integration precedes separately verified live activation.


### Breaking changes

Legacy perry-state/next renderers and current-state fallbacks are retired. Snapshot payloads and helper paths change; consumers must follow the native query contract rather than read the frozen legacy registers.


## 0.1.27 — 2026-10-20

patch · phase 004-guided · TASK-492 · delivery TASK-492-native-cutover-20261020

### Changes

Goals and decide structured records move to the native kernel through the process template and a reviewed one-shot additive migration plan. Exact legacy labels, versioned identities, attachments and historical evidence are retained. The user-approved generic template-apply ceiling revision 32bcf99c adds optional monotonic prefix floors; the budget remains eight concepts, twelve command groups and four guard kinds.


### Upgrade notes

Before live use, back up each actual native store and source documents, validate a fresh reviewed plan and source hashes, then perform the documented additive native CLI migration. Do not replace a populated store or seed fabricated history. Preserve frozen legacy material. Integrate required consumers with the source switch; the release itself performs no live migration.


### Breaking changes

The process template and native surface advance for the approved optional template apply.ceilings parameter. Goals and decide consumers must use bin/perry and native item/query/event contracts; retired structured writers and direct config/parser reads are removed.


## 0.1.26 — 2026-10-19

patch · phase 004-guided · TASK-496 · delivery TASK-496-context-report-only-20261019

### Changes

Session context usage is report-only. Valid live, explicit, historical and unknown-telemetry reports return exit 0 regardless of token volume, without a fixed, environment or project ceiling or a forced rollover. Session rollover belongs to the agent environment and user. Static byte-bill checks, invalid CLI usage, and task-count, duration, failure, review and safety gates retain their existing behavior.


### Upgrade notes

Consumers must stop treating session report verdicts OVER or OK as enforcement decisions: the verdict is now measured or report_only, with no default threshold. Existing session_context_ceiling project settings and PERRY_CONTEXT_CEILING environment settings are ignored. An explicitly supplied legacy --ceiling remains an advisory comparison only and does not change a valid report exit status. Missing telemetry is reported without requiring a session decision.


### Breaking changes

The session-report verdict and exit-status contract changes: usage no longer blocks work, and OVER/OK session verdicts are replaced by measured/report_only. Update consumers that parsed the prior session verdicts or relied on threshold exit codes. Explicit --ceiling comparisons are advisory. Invalid invocations and static --bill checks remain nonzero where appropriate.


## 0.1.25 — 2026-10-18

patch · phase 004-guided · TASK-490 · delivery TASK-490-kernel-cutover-20261018

### Changes

Phase E switches the work lane to the authoritative kernel and freezes all legacy perry-task writer verbs. The old reader remains available for migration inputs. Kernel imports and native work use happen after local integration under separate recorded cutover checks. Goals, decide, and dashboard migration remain later phases. TASK-491 supplies the coupled aiMark adapter in its external repository.


### Upgrade notes

Preserve and back up legacy task and event stores. Complete or recover pending legacy transactions using the pre-cutover release before importing. After integrating Perry together with the coupled aiMark TASK-491 adapter, run the documented perry-kernel-migrate preflight/import verification before using native kernel work commands. Existing projects without imported kernel state must follow the documented explicit initialization or migration path. No live stores are changed by this release allocation.


### Breaking changes

Every legacy perry-task writer now refuses with kernel migration guidance; retained legacy reads do not recover pending transactions. Work automation and external consumers must use the authoritative kernel adapter. This is the phase-E work cutover only; goals, decide, and dashboard paths retain their declared later-phase boundary.


## 0.1.24 — 2026-10-12

patch · phase 004-guided · TASK-495 · delivery TASK-495-architecture-analysis-lifecycle

### Changes

Architecture analysis now combines static Python facts with host-agent interpretations, cited target rules, and offline source evidence. Start and delivery checkpoints retain durable task baselines, compare target and source changes, and flag new blind spots. Direct work, automated dispatch, manual delegation and task-close guidance describe the same checkpoint procedure. Reports open on attention results; no scheduler is introduced.


### Upgrade notes

Regenerate prototype fact snapshots, host analyses, semantic reviews and checkpoints for fact source version 3. Checkpoint verification now binds saved HTML bytes with a report hash and rejects missing or changed reports. Preserve older evidence for audit; do not replace a recorded pre-edit start baseline with a post-edit scan. Existing work without a valid pre-edit baseline must report that limitation instead of claiming a verified comparison. The analysis covers static Python source and explicit supported rules; interpretation remains a host-agent responsibility.


### Breaking changes

Older prototype facts and checkpoints fail freshness or integrity verification under source version 3 and the HTML-hash requirement; regenerate new runs as described in the upgrade notes while preserving historical evidence.


## 0.1.23 — 2026-09-23

patch · phase 004-guided · TASK-484 · delivery TASK-484-operations-next-rules

### Changes

- TASK-484 (USER-1002): `perry-state --section next` covers cadence and operations. A file waiting in `inputs/` is recommended for `/perry work digest <name>`; a cadence row past its next due for `/perry work triage`; the top open risk carrying a declared high-severity marker (`H`, `高`, `🔴`) for `/perry work risk`; an `ARCHITECTURE.md` reviewed 180 days ago or longer for `/perry work architecture-audit`, where the project's declared packs include `software-ops` — which they do by default, a project opting out only by naming other packs or leaving its `Packs` cell blank. Severity is read from a declared marker and never from the sentence: an unmarked risk ranks `""` and fires nothing. `work rollover` is classified never-recommended rather than given a rule — it is the phase-transition procedure, reached after `goals score-phase`, so a month boundary would start it at the wrong time. The standup's stale-architecture warning now compares at-or-over, so it and the rule speak on the same day. `perry-next/1.4`.


### Upgrade notes

- `perry-next/1.4` adds the facts `operations.inputs`, `operations.first_input`, `cadence.overdue_count`, `cadence.first_overdue`, `risks.top_rank`, `architecture.days_since_review` and `project.packs`, and the payload key `architecture.days_since_review`; nothing is removed.
- The rule file's predicate operators gain `contains`, the mirror of `in` for a fact that is a list.
- A project whose `ARCHITECTURE.md` is exactly 180 days past its last review now gets the standup warning on that day rather than the next, which is the same day the new `R-architecture-stale` recommends the audit.


### Breaking changes

None.


## 0.1.22 — 2026-09-23

patch · phase 004-guided · TASK-427 · delivery TASK-413-427-autonomous

### Changes

- TASK-427 (autonomous round, 2026-09-17): a tool that declares its flag surface now answers an undeclared flag with exit 2 and the accepted set, instead of exit 2 alone — for example `perry-task list --xyzzy` lists the flags `list` accepts. The message is derived from the same `SURFACE` declaration, so a newly declared flag appears without a second edit.
- TASK-413 (same round): `perry-task list --json`'s `bound.open_total` and `bound.closed_total`, published to dashboards, are now asserted by the suite; before this nothing in `tests/` checked their values.


### Upgrade notes

- No action. A tool that declares no flag surface still answers `(try --help)`.


### Breaking changes

None.


## 0.1.21 — 2026-09-22

patch · phase 004-guided · TASK-483 · delivery TASK-483-execution-next-rules

### Changes

- TASK-483 (USER-1001): `perry-state --section next` sees the execution loop. A row at `review` owed a V4 verdict is recommended for `/perry work review`; one whose latest V4 verdict (ordered by review round) is PASS for `/perry work close-task`; a startable P0/P1 row whose spec says `Dispatch mode: auto` for `/perry work dispatch`, after the finishing rules; a stale block for `/perry work triage`. Verdict blocks and spec headers are read through `viewer/parsers.py`; the dependency rule moved to `bin/lib`. `work review` is listed in the work subcommand index. `perry-next/1.3`.


### Upgrade notes

- `perry-next/1.3` adds the facts `board.review_owed`, `board.closable`, `board.dispatchable`, `board.blocked_stale` (each with a first id and title) and the payload key `board.execution[]`; nothing is removed.
- A spec opts a row into R-dispatchable only with a single `Dispatch mode: auto` in its header block; two different values read as ambiguous.


### Breaking changes

None.


## 0.1.20 — 2026-09-22

patch · phase 004-guided · TASK-482 · delivery TASK-482-midweek-fact

### Changes

- TASK-482 (USER-999): `R-midweek` can now fire. `/perry work midweek-check` ends by recording an occurrence on a cadence row titled `midweek-check` (`perry-task cadence-add` once, `cadence-done` each run); `perry-state` reports `week.midweek_checked` for the current ISO week, and on a Wednesday with no record it recommends `midweek-check`. The schema reserves that cadence title (`reserved_titles` on the `cadence.jsonl` claim). `perry-state --section next` is `perry-next/1.2`.


### Upgrade notes

- `perry-next/1.2` replaces the fact `today.journal_has_midweek` (always unknown in 1.1) with `week.midweek_checked`; `semantics` stays `[]`. A consumer matching the exact string `perry-next/1.1` must accept 1.2.
- The cadence title `midweek-check` is reserved: a cadence row with that title is read as the mid-week check's record.


### Breaking changes

None.


## 0.1.19 — 2026-09-22

patch · phase 004-guided · TASK-481 · delivery TASK-481-retro-phase-header

### Changes

- TASK-481 (USER-998): `end-phase-retro` opens `evidence/<YYYY-MM>/retro.md` with the `> Phase: #<NNN>-<slug> · started <date> · scored —` header, so `perry-state` sees the retro and `R-phase-scorable` recommends `score-phase`; `score-phase` step 5 sets the header's scored date and appends its summary instead of writing a new retro.


### Upgrade notes

- A retro written by `end-phase-retro` now carries the `> Phase:` header; an existing retro without it is not recognised by `phase.retro_recorded` until the header is added.


### Breaking changes

None.


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
