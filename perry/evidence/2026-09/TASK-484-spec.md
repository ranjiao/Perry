# TASK-484 — DESIGN-020 I: next-step rules for cadence and operations

Date: 2026-09-23. Owner: Coding Agent. Priority: P2. Required verification: V4.
KR: P004-O1-KR1. Design: `perry/design/DESIGN-020-guided-planning.md § 5.10`
(batch 3, the "Event" table rows marked 3) and § 6 row I. ADR-023.
> Touches architecture: bin/perry-state next facts, reference/next-rules.json, the coverage guard.
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-990, USER-992, USER-994, USER-1002 (2026-09-22/23).

## Deliverable

1. **Facts** in `bin/perry-state § NEXT_FACTS` / `next_facts`, each a typed value
   or an `unknown[]` reason, read through the existing payload or the one reader
   (NN-1) — never a second reader:
   - `operations.inputs` (int) and `operations.first_input` (path): files waiting
     under `inputs/`. The payload already carries `operations.inputs`; add the
     first path if it is not there.
   - `cadence.overdue_count` (int) and `cadence.first_overdue` (id or title):
     from the payload's existing `cadence.overdue`.
   - `risks.top_rank` (string): the top open risk's `severity_rank`, which
     `viewer/parsers.py § split_severity_marker` derives from a **declared
     marker** in the statement (`H ·`, `🔴`, …). A risk with no marker has rank
     `""` and must **not** fire the rule — absence is a fact, not an unknown, and
     the tool must not infer severity from prose (NN-4). Say in the RESULT which
     ranks exist and which you fire on.
   - `architecture.days_since_review` (int): today minus
     `architecture.last_reviewed`; `unknown` when the document is absent or the
     date does not parse. `bin/perry-state` already computes a stale-review
     warning (~line 2042) — reuse that computation, do not write a second one.
2. **Rules** in `reference/next-rules.json`, in § 5.10's order (after
   `R-review-due` and `R-midweek`, before `R-phase-heartbeat`):
   - **R-inputs-waiting** → `/perry work digest {operations.first_input}`
     when `operations.inputs > 0`.
   - **R-cadence-overdue** → `/perry work triage` when
     `cadence.overdue_count > 0`; the reason names the first overdue item.
   - **R-risk-raised** → `/perry work risk` when `risks.top_rank` is a rank you
     declare as above `watch` (justify the set; `""` never fires).
   - **R-architecture-stale** → `/perry work architecture-audit` when
     `architecture.days_since_review` is at or over a threshold declared in the
     rule file's `thresholds` (propose 180, matching the existing warning) **and**
     the `software-ops` pack is active for the project. If no fact reports pack
     activity, add one from the existing payload rather than assuming.
3. **`R-rollover` is not added.** `work rollover` is the phase-transition
   procedure (`work/reference/subcommands.md § rollover` step 1 onward), reached
   after `score-phase` through `R-no-phase`; the month-boundary trigger in
   § 5.10 would recommend it at the wrong time. Classify `rollover` as
   **never-recommended** in the coverage guard, with that one-line reason.
4. **Coverage guard** (`tests/test_next_closing.py` `UNCOVERED`): no `pending I`
   entry is left — `digest`, `risk` and `architecture-audit` are named by their
   rules, `rollover` is `never`.
5. **`reference/next.md`** entries for the four rules and the new facts, and
   **`schema/next-contract.md`** → `perry-next/1.4` (additive fact names).

## Acceptance criteria

1. A fixture with a file under `inputs/` yields `R-inputs-waiting` whose command
   names that file; an empty `inputs/` does not fire it.
2. A fixture with an overdue cadence item yields `R-cadence-overdue`, and its
   reason names the item; a cadence item due later does not fire it.
3. A fixture risk marked with a declared high-severity marker yields
   `R-risk-raised`; the same statement without a marker does not fire it, and
   the fact is `""`, not unknown.
4. A fixture whose architecture review is older than the threshold yields
   `R-architecture-stale`; a fresh review does not; a project without
   `ARCHITECTURE.md` leaves the fact unknown and never fires the rule; a project
   without the `software-ops` pack does not fire it.
5. Deleting each new rule from a copy of the rule file reddens its fixture. The
   existing fixtures keep their primaries.
6. The coverage guard is green with no `pending I` left, and `rollover` is
   classified `never`.
7. On this repository `perry-state --section next` runs without `rule_errors`.
   Report the block before and after and each new fact's value here.
8. Unmodified candidate and `--tier affected` green.

## Files in scope

`bin/perry-state`; `reference/next-rules.json`; `reference/next.md`;
`schema/next-contract.md`; `tests/test_next_section.py`;
`tests/test_next_closing.py`. `viewer/parsers.py` only if a first-input path or
pack fact needs a reader that does not exist; say why.

## Bound

Four rules and the facts above. Net new Python/test physical lines ≤ +250
against the base. No `schema/state-schema.json` change — stop and report if one
seems needed. The router `SKILL.md` is not edited. No new subcommand.

## Verification

Isolated fixtures, candidate PERRY_HOME, PERRY_PROJECT unset, fresh TMPDIR under
the scratch derivation. `bash tests/run --tier affected --base <pinned base>`.
One reverting proof per new rule, plus one showing an unmarked risk does not
fire. `__pycache__` purged between mutants, restores verified against
`git show <your commit>:<path>`. `git diff --check`. Record the exact commit and
line delta.

## Out of scope

`R-rollover`; `week.planned` (TASK-444); phase duration (UD 13); running
`digest`, `risk` or `architecture-audit`; `schema/state-schema.json`; release
allocation (the integrator's); live PMO state; publication; main integration.
