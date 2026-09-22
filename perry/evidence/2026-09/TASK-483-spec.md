# TASK-483 — DESIGN-020 H: next-step rules for the execution loop

Date: 2026-09-22. Owner: Coding Agent. Priority: P1. Required verification: V4.
KR: P004-O1-KR1. Design: `perry/design/DESIGN-020-guided-planning.md § 5.10`
(batch 2, "Event" table and fact rows marked 2) and § 6 row H. ADR-023.
> Touches architecture: viewer/parsers.py (reader moves in), bin/perry-lint, bin/lib, bin/perry-state, work/SKILL.md index (boundary path).
> Dispatch mode: auto
> Executor: claude-subagent
> Subjective verification: independent review against the written bounded criteria
> Deployed: no

Authorization: USER-990, USER-992, USER-994, USER-1001 (2026-09-22).

## Deliverable

1. **One reader for verdict blocks and spec headers (NN-1).** Today only
   `bin/perry-lint` parses `=== VERDICT ===` blocks (`parse_verdicts` ~2402)
   and spec header lines such as `> Dispatch mode:`. A tool may not import
   another tool, so move the parsing into `viewer/parsers.py`, the one reader.
   `perry-lint` then imports it from there. Moved lines count once. Behaviour
   of `perry-lint --reviews` and `--specs` stays byte-identical on this
   repository (criterion 6).
2. **Shared row computations.** `startable` and `blocked_stale` are computed in
   `bin/perry-task` (see its list contract ~line 124). If `perry-state` needs
   them and they live only in `perry-task`, move the computation to `bin/lib`
   (or `viewer/parsers.py`) and have both import it. No second implementation.
3. **Facts** in `bin/perry-state`, each a typed value or an `unknown[]` reason,
   each with a first id and its title for the reason template (the TASK-479
   `*_title` pattern):
   - `board.review_owed`: open rows at `review` whose rung is V4 and which no
     evidence document's verdict block names.
   - `board.closable`: open rows at `review` whose latest verdict block naming
     them reads `result: PASS` for rung V4. "Latest" by a declared, deterministic
     order — say which (e.g. file mtime is not acceptable, since it is not in git;
     prefer the evidence path's month and the block's order, or the rung's review
     round naming) — and report its limits.
   - `board.dispatchable`: open `not_started` rows, `startable`, priority P0 or
     P1, whose spec `evidence/<YYYY-MM>/<ID>-spec.md` declares
     `Dispatch mode: auto`.
   - `board.blocked_stale`: count of rows marked `blocked_stale`.
4. **Rules** in `reference/next-rules.json`, placed as § 5.10's order says:
   … R-week-unplanned · **R-review-owed** (→ `/perry work review
   {board.first_review_owed}`) · **R-closable-row** (→ `/perry work close-task
   {board.first_closable}`) · R-sla-breach · R-wip-over-limit ·
   R-*-commitment-due · R-asks-waiting · **R-blocked-stale** (→ `/perry work
   triage`) · **R-dispatchable** (→ `/perry work dispatch
   {board.first_dispatchable}`) · R-review-due · … Batch-3 rules (`R-rollover`
   and others) are **not** added.
5. **`work review` index row** in `work/SKILL.md § Subcommand index` (it has a
   procedure in `work/reference/review.md` but no index row), so R-review-owed's
   command resolves. Keep the file within its byte budget
   (`tests/test_router_budget.py`). Give it a `next-close` pointer and a
   closing-inventory entry only if review is state-changing per the existing
   inventory's rule. Otherwise classify it read-only there, and say which.
6. **Coverage guard**: move `dispatch`, `close-task` and `review` from
   `pending H` in `tests/test_next_closing.py`'s `UNCOVERED` to being named by
   their rules. `triage` is already named.
7. **`reference/next.md`** entries for the four rules and the new facts, and
   **`schema/next-contract.md`** → `perry-next/1.3` (additive fact names).

## Acceptance criteria

1. Fixture: a V4 row at `review` with no verdict naming it → `R-review-owed`
   (unless an earlier rule fires). With a PASS verdict block for it →
   `R-closable-row`. With a FAIL block → neither closable nor owed.
2. Fixture: a startable P1 `not_started` row whose spec says `Dispatch mode:
   auto` → `R-dispatchable`. `Dispatch mode: manual` or a missing spec → not
   dispatchable. A P2 row → not dispatchable.
3. Fixture: a `blocked_stale` row → `R-blocked-stale`.
4. **Busy-board order**: a fixture holding a review-owed row, a closable row and
   a dispatchable row gives a finishing rule (`R-review-owed` or
   `R-closable-row`) as primary, never `R-dispatchable`.
5. Deleting each new rule from a copy of the rule file reddens its fixture. The
   existing fixtures keep their primaries.
6. `perry-lint --reviews` and `perry-lint --specs` print byte-identical output
   before and after on this repository. Show the `cmp`.
7. On this repository `perry-state --section next` runs without `rule_errors`.
   Report the block before and after, and each new fact's value here.
8. The coverage guard is green, with no `pending H` entries left.
9. Unmodified candidate and `--tier affected` green.

## Files in scope

`viewer/parsers.py`; `bin/perry-lint` (import instead of parse); `bin/lib/__init__.py`
and `bin/perry-task` (only to share `startable`/`blocked_stale`); `bin/perry-state`;
`reference/next-rules.json`; `reference/next.md`; `schema/next-contract.md`;
`work/SKILL.md` (one index row, pointer if needed); `tests/test_next_section.py`;
`tests/test_next_closing.py`; existing lint tests only if an import path moves.

## Bound

Four rules, the facts above, one index row. Net new Python/test physical lines
≤ +300 against the base, with moved code counted once. The router `SKILL.md`
is not edited. No `schema/state-schema.json` change; stop and report if one
seems needed.

## Verification

Isolated fixtures, candidate PERRY_HOME, PERRY_PROJECT unset, fresh TMPDIR under
the scratch derivation. `bash tests/run --tier affected --base <pinned base>`.
One reverting proof per new rule. A proof that the busy-board order reddens when
`R-dispatchable` is moved above the finishing rules. `__pycache__` purged
between mutants. `git diff --check`. Record the exact commit and line delta.

## Out of scope

Batch 3 (DESIGN-020 § 6 I); running any dispatch or review; changing
`perry-lint`'s findings; `schema/state-schema.json`; release allocation (the
integrator's); live PMO state; publication; main integration.

## Note after delivery (2026-09-22, PMO)

- **Bound reading.** "Moved code counted once" means a move nets to zero: its
  lines are added at the destination and removed at the source. The candidate's
  `git diff --numstat` over Python and tests is +402 / −157 = **net +245**,
  within +300.
- **Spec error.** Deliverable 1 said `perry-lint` parses `> Dispatch mode:`
  header lines. It does not; nothing under `bin/` read that field at the base.
  `parsers.spec_header_fields` is therefore a new reader, not a moved one.
- **Scope.** `tests/test_ask_is_a_node.py` and `tests/test_answered_ask_is_legible.py`
  pinned the dependency rule's location in `bin/perry-task`. Moving it to
  `bin/lib` (Deliverable 2) required updating them. This is read as the
  "import path moves" allowance in Files in scope.
