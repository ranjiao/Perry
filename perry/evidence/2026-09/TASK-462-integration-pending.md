# TASK-462 — implementation ready, architecture authorization pending

Date: 2026-09-16. User approved version/release implementation in chat.
This is not a completion or publication receipt.

## Candidate

Branch codex/task-462-version-core at
5ffd98bbdb3110a93cfcb5e759c31d9a414545ad, containing updater
4c7311be65508e820d287f531e69700cbdc8bbe4. Both implementation worktrees are
clean. VERSION is 0.1.0 at phase 004-guided. The primary checkout has not merged
the implementation; no tag, push, Release or installed self-update occurred.

Author results are committed on the candidate under
perry/evidence/2026-09/TASK-462-core-result.md and TASK-462-update-result.md.
The change includes canonical release records and projections, strict allocation
and integration checks, a manually triggered exact-commit release workflow,
release-default consumer updates and a safe explicit symlink release channel.

## Verification so far

- Updater: independent 20 tests passed. Main/detached local-version handling
  was initially wrong, then repaired and independently reproduced as fixed.
  Tag/VERSION binding mutation was red; annotated-tag detached update passed.
- Core: independent 18 tests passed. Three initially green mutations exposed
  missing negative coverage; exact-checkout SHA, version order and phase
  repetition/reversal now each have independently red mutations. Production
  guards were already present; new tests close the verification gaps.
- Parent merged preview 69864990624ce95f47edd67b6578b79ef579b1b1 (main bccc15f8
  plus earlier code pin fe48c3f4) ran the full suite: 153 modules / 4,282 tests
  in 122.9s. It FAILED in three modules: missing architecture component,
  missing vocabulary coverage for new paths, and test-entry quote convention.
  This is not counted as a passing full gate; slow was not run after failure.
- Candidate 5ffd98bb fixes vocabulary coverage and the test-entry convention.
  Author checks: entry-point guard 2 tests, vocabulary 53 tests, router budget
  9 tests passed. Independent delta review confirmed coverage expansion, with
  four injected withdrawn-command examples all refused; no guard was bypassed.
- Explicit-base version check and exact-SHA preparation passed on the prior
  combined candidate. No real network publication was used in verification.

## Required remaining step

USER-953 asks permission to add only the proposed release/ component entry to
ARCHITECTURE.md section 2. Exact text: TASK-462-architecture-proposal.md.
The architecture file explicitly reserves its edits to the user. It has not
been changed, and test_architecture_rules has not been exempted.

After authorization: record the answer, amend the spec's architecture scope,
have the coding agent add exactly that entry on its branch, independently
review the delta, run final merged full and slow gates plus version checks,
then merge, record the receipt and close. If authorization is withheld, retain
the candidate and the blocker. Release publication remains a separate action.
