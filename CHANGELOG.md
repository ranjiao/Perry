# Perry changelog

Generated from release/records.jsonl; edit records through the release tool.

## 0.1.0 — 2026-09-16

baseline · phase 004-guided · TASK-462 · delivery TASK-462-baseline

### Changes

Establish the first product-version baseline for Perry at phase 004 (guided). Perry already provides goals, work and decision lanes; typed task, risk, intake, ask, cadence and OKR/linkage records; deterministic CLI reports; and adapters for Claude Code, OpenCode and Codex CLI. This baseline includes TASK-462: canonical release records, generated version/changelog, integration checks, manual publishing and verified release-channel updates. Earlier development is retained in Git history and is not reconstructed as historical releases.

### Upgrade notes

Use the release channel for a clean consumer checkout, including symlink installations via the explicit --channel release option. Developer checkouts remain report-only. Until a GitHub Release is actually published, release-channel checks refuse; they do not fall back to main. Existing project state is not migrated by this baseline.

### Breaking changes

Product versions follow Perry delivery milestones, not strict SemVer. Minor and patch releases can include compatibility changes; read these notes before upgrading. This release mechanism does not version projects managed by Perry.
