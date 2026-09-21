# TASK-479 — DESIGN-020 G: next-step rules for the phase lifecycle

Date: 2026-09-21. Owner: Coding Agent. Priority: P1. Required verification: V4.
KR: P004-O1-KR1. Design: `perry/design/DESIGN-020-guided-planning.md § 5.10`
(batch 1) and § 6 row G, as corrected by the § 9 entry of 2026-09-21 (USER-996).
> Touches architecture: bin/perry-state next facts, reference/next-rules.json, goals/SKILL.md index (boundary path).
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-990, USER-992, USER-994, USER-995, USER-996 (2026-09-21).
`ADR-023`.

## Deliverable

1. **Facts** in `bin/perry-state § NEXT_FACTS` / `next_facts`, each a typed
   value or an `unknown[]` reason, never a guess:
   - `phase.krs_unstaffed` (int) and `phase.first_unstaffed_kr` (id): active,
     non-withdrawn **commit** KRs of the current phase with zero linkage edges to
     tasks, **less** those whose DESIGN-022 position is measured and met
     (DESIGN-020 UD 14). Read through the existing linkage and KR-position code
     (`bin/lib § kr_position`, `perry-goals krs` data); no second reader.
   - `phase.kr_progress.undeclared` (int) and `phase.first_undeclared_kr` (id):
     commit KRs whose position is `undeclared`.
   - `phase.retro_recorded` (bool): an `evidence/<YYYY-MM>/retro.md` exists
     whose `> Phase:` header field names the current phase (e.g.
     `#004-guided`). This is a header field, not prose. Say how you read it
     and through which reader (NN-1). If two phases could share a month's file,
     report that limit.
   - a midweek fact for `R-midweek`. It must be deterministic and must not
     require a `schema/state-schema.json` edit. If no such source exists (the
     journal declares no midweek heading today), declare the rule with its fact
     reported `unknown` and a reason, as `R-phase-heartbeat` does. **Stop short
     of a schema edit and report it.**
2. **Rules** in `reference/next-rules.json`, in this place in the order:
   R-setup · R-no-okr · R-no-phase · R-phase-closable (narrowed: also
   `phase.retro_recorded = false`) · **R-phase-scorable** (closable conditions
   and `phase.retro_recorded = true` → `/perry goals score-phase`) ·
   **R-kr-unstaffed** (active phase, `phase.krs_unstaffed > 0` → `/perry goals
   plan-week`) · **R-checks-undeclared** (active phase,
   `phase.kr_progress.undeclared > 0` → `/perry goals check`) ·
   R-week-unplanned · … (rest unchanged) · **R-midweek** placed after
   R-review-due (`today.weekday = Wednesday` and the midweek fact → `/perry work
   midweek-check`). Reasons name the first KR id **with its title**.
   Thresholds, if any, come from the rule file's thresholds or the schema.
3. **`reference/next.md`**: one entry per new or changed rule, in the same
   shape as the existing entries.
4. **`goals check`**: a Subcommand-index row in `goals/SKILL.md` and its
   procedure in `goals/reference/phases.md`. It declares a KR's checks through
   `bin/perry-goals check`, with per-Objective user approval (DESIGN-022 § 5.6),
   and ends with the closing step. Add its `next-close` pointer and add it to the
   closing inventory in `tests/test_next_closing.py`.
5. **`goals/reference/weekly.md` step 1**: when `phase.krs_unstaffed > 0`, the
   unstaffed KRs (and the phase document's Projects seeds) are the first input
   to the candidate tasks. The rest of plan-week is unchanged.
6. **Coverage guard**: a declared never-recommended list, in the rule file or
   extending the read-only inventory in `tests/test_next_closing.py` (one list,
   not two), matching DESIGN-020 § 5.10. A test asserts that every command in
   every lane's Subcommand index is either some rule's `command` token or on
   that list, and that no command is on both. Batches 2 and 3 rules that do not
   exist yet are on neither; classify their commands as "pending batch H/I" so
   the guard is honest, not falsely complete.
7. **`schema/next-contract.md`**: the new fact names, as a minor version
   (`perry-next/1.0` → `1.1`), with the payload's `contract` string updated in
   the same change.

## Acceptance criteria

1. A fixture project with an active phase whose commit KRs have no linkage
   edges yields primary `R-kr-unstaffed`, whose reason names the first KR with
   its title. Giving every KR an edge makes it fall through.
2. A fixture KR that is measured and met, with no task, does not count toward
   `phase.krs_unstaffed`.
3. A fixture with an undeclared commit KR (and every KR staffed) yields
   `R-checks-undeclared`.
4. A closable fixture phase with no retro yields `R-phase-closable`. The same
   phase with a `retro.md` naming it yields `R-phase-scorable`. A retro naming
   another phase does not count.
5. `R-midweek` either fires on a Wednesday fixture whose midweek fact is false,
   or is declared with its fact unknown and a stated reason (Deliverable 1).
6. Deleting any new rule from a copy of the rule file reddens its fixture, in
   the existing `test_each_fixtures_primary_depends_on_its_own_rule` style. The
   five existing fixtures keep their primaries, including the existing
   `closable_phase` fixture, which must now name its retro state.
7. The coverage guard reddens when a Subcommand-index row is added that no rule
   names and no list classifies.
8. On this repository `perry-state --section next` still runs without
   `rule_errors`. Report its primary and alternates before and after.
9. Unmodified candidate and `--tier affected` green.

## Files in scope

`bin/perry-state`; `reference/next-rules.json`; `reference/next.md`;
`schema/next-contract.md`; `goals/SKILL.md` (index row and pointer only);
`goals/reference/phases.md`; `goals/reference/weekly.md`;
`tests/test_next_section.py`; `tests/test_next_closing.py`. If a reader must be
added, add it to `viewer/parsers.py` (the one reader) or `bin/lib`, and say why.

## Bound

Rules: exactly the batch-1 set above, with no batch 2 or 3 rule. Facts: the five
above plus one midweek fact. Fixtures: one per new or changed rule, plus the
UD 14 exemption. Net Python/test physical lines ≤ +300 against the base. Lane
and reference pages stay within the byte budgets the suite already enforces
(`test_router_budget`, the L2 tier budget). The router `SKILL.md` is not
edited.

## Verification

Isolated fixtures, candidate PERRY_HOME, PERRY_PROJECT unset, fresh TMPDIR
under the scratch derivation. `bash tests/run --tier affected --base <pinned
base>`. One reverting proof per new rule (delete its rule), plus one for the
UD 14 exemption. `__pycache__` purged between mutants. `git diff --check`.
Record the exact commit and line delta.

## Out of scope

`schema/state-schema.json` (stop and report if a fact seems to need it);
DESIGN-020 § 5.10 batches 2 and 3; `week.planned`'s source (TASK-444); phase
duration (UD 13); `/perry plan`; live PMO state; release allocation;
publication; main integration.
