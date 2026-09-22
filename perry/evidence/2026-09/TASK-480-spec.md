# TASK-480 — release 0.1.18, one combined patch for the backlog

Date: 2026-09-22. Owner: Coding Agent. Priority: P1. Required verification: V3.
> Touches architecture: release/ records and projections only (no code).
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: (none)
> Deployed: no

Authorization: USER-997 (2026-09-21, in chat). It is a one-time exception to
`release/README.md` line 14 ("each product task delivery increments patch"):
the product deliveries integrated since 0.1.17 share one version.

## Deliverable

On its own branch `coding/task-480-release-0.1.18`, from the pinned base, run
`release/manage.py patch` exactly once:

- `--expected-version 0.1.17`, `--date 2026-09-22`, `--phase 004-guided`,
  `--task TASK-480`, `--delivery TASK-480-backlog-0.1.17-to-0.1.18`,
  `--integrator pmo-agent`.
- `--notes-file`: an authored list of every product delivery integrated on
  main's first-parent line after `f31c5d78` (the 0.1.17 allocation) and up to the
  base. Give each delivery one line: task or decision id, integration commit
  (short SHA), and what changed for a user of the skill. Enumerate from
  `git log --first-parent f31c5d78..<base>` and classify each commit by the paths
  it changes. `release/manage.py`'s own `PMO_FILES` / `PMO_PREFIXES` rule decides
  what is product. PMO-only commits are not listed. End the notes with one line
  naming the exception: "Combined allocation for deliveries since 0.1.17,
  USER-997; later deliveries are allocated one patch each."
- `--upgrade-file`: user-facing upgrade notes, or `None.`. Candidates to judge:
  `perry-next/1.0 → 1.1` (additive facts); the new `goals check` subcommand;
  `perry-goals objective add` (TASK-475); the phase lifecycle writer (TASK-474);
  ARCHITECTURE.md now anchored at the code root (TASK-451/452); perry-diagnose
  ownership by anchor (TASK-477); the release check range fix (TASK-478).
- `--breaking-file`: breaking changes, or `None.` with a one-line justification
  in the RESULT. Note the known deliberate break: old pre-ADR-019 projects are
  upgraded, not kept compatible (TASK-237 lineage). Include it only if a
  delivery in the range made it.

Commit the allocation (the record plus the tool-rendered `VERSION` and
`CHANGELOG.md`) as one commit. Edit no existing record.

## Acceptance criteria

1. `python3 release/manage.py show` on the candidate prints `0.1.18`.
2. `python3 release/manage.py check --base origin/main --ref HEAD` exits 0 on the
   candidate, where `origin/main` is `174f35b2` and so contains 0.1.0–0.1.17.
3. `python3 release/manage.py check --base <pinned base> --ref HEAD` exits 0.
4. Every integration merge on the first-parent line in `f31c5d78..<base>` that
   changes a product path appears in the notes. List them in the RESULT with
   their classification, and list the PMO-only commits you excluded by count.
5. `git diff <base> HEAD --name-only` is exactly `release/records.jsonl`,
   `VERSION` and `CHANGELOG.md`.
6. `bash tests/run --tier affected --base <pinned base>` green.

## Files in scope

`release/records.jsonl`, `VERSION`, `CHANGELOG.md`, all written by the tool.
Notes files go in scratch outside the checkout.

## Out of scope

Tags, `release/manage.py prepare`/`publish`, `gh release`, `git push`, editing
any existing record, code changes, live PMO state, main integration.
