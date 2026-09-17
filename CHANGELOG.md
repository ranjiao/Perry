# Perry changelog

Generated from release/records.jsonl; edit records through the release tool.

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
