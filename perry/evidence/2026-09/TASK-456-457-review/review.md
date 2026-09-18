# TASK-456 + TASK-457 — independent V4 review of the merged candidate

Date: 2026-09-18. Reviewer: independent agent (Claude). I did not write any part of the candidate.
Target: branch `task-456-457-rebase-20260918`, head `af1e8fba`, base `262d487c` (main).
Scope: TASK-457 in full (its first independent review), TASK-456 re-checked on this tree, and the integration fix-ups `2fe31648` and `3124e3b8`.
Contract: `perry/evidence/2026-09/TASK-456-spec.md`, `TASK-457-spec.md`, and DESIGN-017 §5.4 (tiers L0–L3, P1–P5, decision 9). Also `bin/ARCHITECTURE.md` §5 and §6.

VERDICT: PASS-WITH-FINDINGS

Neither delivery has a blocking defect. The five bills match their index rows byte for byte. All three splits keep every section. Every mutation aimed at the bill, the budgets or the tier caps turns a named test red. Both suites are green. The findings are two Medium issues (a gap in the guard's coverage, and missing evidence) and several Low ones. None of them changes a number or a rule on this tree.

## Findings, ranked

| # | Sev | Where | Finding |
|---|---|---|---|
| 1 | Medium | `tests/test_router_budget.py:228-235` | **The tier enumeration is not pinned.** Two mutants survive: T6 removes `modes` from the L3 list, and T7 removes the three lane `reference/` dirs from L2. With either one, the suite stays green, so a later edit could quietly stop budgeting most of L2 or L3. The enumeration also misses root `state/adoption_dossier_TEMPLATE.md` (4,688 B) and `state/diagnosis_TEMPLATE.md` (5,298 B). Both are §5.4 L3 "templates / scaffolds" but are not in `*/state` for a lane. Both are under the 24,576 cap today, so nothing is over budget now. A pinned page count, or a check that every §5.4 location is non-empty, would kill T6 and T7. |
| 2 | Medium | (evidence) | **TASK-457 has no committed author result.** Its spec asks for several things: the budget measurement and rationale "in the result"; retained per-file source/hash/byte receipts; the index mapping; and the fixture, negative and revert proof. I searched every git ref for `perry/evidence/2026-09/TASK-457*`, and the only match is the spec. The rationale lives only in the comment at `bin/perry-context-budget:239` and in the integrator's `TASK-456-457-rebase/result.md`. My own measurements below stand in for those receipts, but the author's hand-back cannot be audited. |
| 3 | Low | `bin/perry-context-budget` (module docstring; `declared_ceiling`, `resolve_ceiling`, `last_usage`, `composition` docstrings; the `--root ""` comment), `tests/test_context_budget.py` (class and test docstrings) | **Rationale was deleted to hold the net-0 line bound.** About 90 lines of explanation on code this task did not otherwise change are gone. Examples: the ADR-019 "a store without the key is an answer" note; the pointer to `lib.empty_root_error`; the "found by mutation" history; and the note that ceiling resolution is unit-tested rather than spawned *because extra subprocesses made `test_host_support` flake*. Behaviour is unchanged: every legacy test survives and assertions went from 44 to 60. But the spec's Bound says "preserve … concise rationale". The deleted text is recoverable from `262d487c`. Line 268 is also a 150-character conditional one-liner that is hard to read. |
| 4 | Low | `bin/perry-context-budget:343`, `:335` | **Exit 2 is used for data errors.** A bill that is `unknown` (missing declared file, root escape, or an ambiguous or missing row) exits 2. `bin/ARCHITECTURE.md §5` reserves 2 for "bad invocation", and 1 is "refused, reason printed". The reason also goes to stdout, not stderr. This is documented in the tool's `--help` and tested, so it is consistent, but it departs from the module contract. |
| 5 | Low | `bin/perry-context-budget:354-358` | **NN-B1 edge case.** `--help --bill bogus` exits 2 with an argparse `invalid choice` error instead of printing help, because `choices=` validation runs before the `args.help` check. NN-B1 is "hard" and says `--help` prints "in any argument position". Valid `--bill X --help` prints help and exits 0. |
| 6 | Low | `bin/perry-context-budget:298` | **References after a parenthetical are dropped silently.** Only backticked references before the first `" ("` in a Reference cell are read. The cut is needed for `work/SKILL.md:54`, whose parenthetical contains a backticked `` `work/reference/` ``. But a cell shaped like `` `a.md` (x) + `b.md` `` would lose `b.md` at zero cost with no error, and AC2 forbids a silent zero-cost result. No current row has that shape: all five bills equal my independent `wc -c` sums over the rows as written. |
| 7 | Low | `work/SKILL.md:254` vs `:33` | **The dispatch index row and the Reference file table disagree.** After the split, the Subcommand-index `dispatch` row still names only `reference/dispatch.md`. The Reference file table names `dispatch.md` + `dispatch-preflight.md`. The bill is right only because it takes the union of both tables. P3 says literally "the L2 pages its index row names", and decision 9 says "the lane index reference column". The same pattern holds for `add-task` (`input-quality.md` and `okr-linkage.md` come only from the Reference file table). The spec's AC1 allows the union, so I record this as a precision note, not a defect. |
| 8 | Info | — | **Headroom is thin.** `add-task` has 649 B left against its 100,000 bill. In practice that makes the bill, not the L1 cap (2,005 B left), the binding limit on `work/SKILL.md` and on L0 growth. L0 has 4 B left against `test_next_section`'s 20,457 no-growth bound. Both are working as designed and will bite on the next router or work-lane edit. |

## TASK-457 — declared context bills

**Bills match P3 and the index rows.** I read the rows myself and summed the files with `wc -c`. That gives the same numbers as `--bill all` on the head:

| Bill | Rows read | Files (bytes) | Total / cap | Headroom |
|---|---|---|---|---|
| snapshot | `SKILL.md:183` (new explicit row; no lane) | SKILL.md 20,453 · reference/snapshot.md 16,426 · host-capabilities 6,023 · i18n 15,082 · next 19,273 | 77,257 / 80,000 | 2,743 |
| add-task | `work/SKILL.md:270`, `:45`, `:54`, `:55` | L0 · work/SKILL.md 36,907 · work/reference/add-task.md 22,159 · reference/input-quality.md 9,389 · reference/okr-linkage.md 10,443 | 99,351 / 100,000 | 649 |
| close-task | `:271`, `:36`, `:37`, `:47` | L0 · L1 · work/reference/promotion.md 8,668 · work/reference/subcommands.md 24,185; `packs/software-ops/runbooks.md` reported as excluded (non-L2) | 90,213 / 95,000 | 4,787 |
| dispatch | `:254`, `:33`, `:48` | L0 · L1 · dispatch.md 31,487 · dispatch-preflight.md 18,848 · git-boundaries.md 5,863 | 113,558 / 115,000 | 1,442 |
| plan-phase | `goals/SKILL.md:127`, `:30`, `:32`, `:37` | L0 · goals/SKILL.md 22,415 · elicitation.md 25,429 · phases.md 30,061 · reference/input-quality.md 9,389 | 107,747 / 110,000 | 2,253 |

- **No duplicate counting.** `subcommands.md`, `add-task.md` and `dispatch.md` each appear in two rows and are each counted once.
- **Matching is token-only.** Rows are matched on backticked command tokens. Prose mentions such as "dispatch compliance gate" in `:39` do not match. Python makes no judgement about meaning.
- **Read-only.** The test replaces `Path.open` with a read-mode, known-path guard, and compares a before/after byte and mtime snapshot. Mutants B11 (session discovery) and B12 (a write) turn it red. Bill mode returns before `lib` is imported and before any project-root or transcript lookup.
- **No session discovery.** Neither `newest_transcript` nor `glob`/`iterdir` is reached (B11). `$PERRY_HOME` and `$PERRY_PROJECT` pointing at a fixture do not move the default root off the installation. That is asserted.
- **Over budget turns a test red.** B7, B8 and B17 are all red. The `all` bill running on the real tree must exit 0, so any real bill that goes over reddens `test_cli_conflicts_and_installation_default`.
- **Flags and exit codes.**
  - `--bill` rejects `--session`, `--composition`, `--ceiling` and `--root` with exit 2.
  - `--bill-skill-root` without `--bill` exits 2, and so does an empty value.
  - Unknown bill names exit 2.
  - Legacy default `--json` keeps its keys (`ceiling, ceiling_from, context, transcript, verdict, why`).
  - Two departures are noted as findings 4 and 5.
- **Net Python/test lines ≤ 0.** For `f5656a1c..b8978116`: `bin/perry-context-budget` +174/−185 and `tests/test_context_budget.py` +106/−95, so net 0. Head against base over `bin/` and `tests/` (non-`.md`): net −7. No test was removed: all 28 legacy test names are kept and 5 were added. Cost: finding 3.
- **Legacy refactors.** The legacy code was refactored in four places:
  - `last_usage` now scans in reverse and seeks from the end;
  - an `unknown()` helper was added;
  - `declared_ceiling` loses a redundant `return`;
  - `composition` gains a `ranked()` helper.

  All are behaviour-preserving as far as I can read them, and all legacy tests pass.

## TASK-456 — tier budgets and splits on this tree

**Section preservation.** I compared `262d487c` against `af1e8fba` with a script. It extracts headings from each original page and counts non-blank lines, fence-aware, before and after the split.

| Original (bytes) | Split into | Headings kept | Original lines missing from union | Lines added |
|---|---|---|---|---|
| `work/reference/subcommands.md` 84,862 | subcommands 24,185 · planning 29,756 · add-task 22,159 · decisions-risk 9,647 | 24/24 | 3 | 26 |
| `work/reference/dispatch.md` 49,922 | dispatch 31,487 · dispatch-preflight 18,848 | 20/20 | 6 | 11 |
| `reference/diagnose.md` 36,740 | diagnose 25,347 · diagnose-explanations 11,977 | 21/21 | 0 | 11 |

- **All 9 "missing" lines are rewritten, not lost.** Each has a rewritten counterpart that differs only in a path or `§` pointer. For example, "`close-task` is in this same file and does load it" became "`subcommands.md § close-task` loads this rule". The cross-references to "pre-flight 5a" and "§ Architecture review below" became file-qualified.
- **Added lines are pointers.** They are:
  - stub headings, with one `See <page> § <section>` line each;
  - three new H1 titles;
  - `After completed writes, follow subcommands.md § Completion routing` (on each of 3 new pages);
  - the pointer `Read planning.md § triage for the stage-change invariant` in `close-task`.
- **No procedure body appears twice.**
- **Guarded content is present.** The host-eligibility, isolation, step 4 high-stakes, no-self-merge and architecture-review sections are all present verbatim or re-pointed. `test_spec_scannability`'s step-3 window now runs to the end of `add-task.md`. That end used to be the `### close-task` heading, and the only extra text in the window is the completion-routing pointer, so the check is not weakened.

**Exact references resolve.** `test_pointers_resolve`, section-citation resolution, `test_shipped_vocabulary` and `test_claims` are green in the full run.

**Tier budgets on this tree** (script over the §5.4 locations):

| Tier | Pages | Total | Max | Cap |
|---|---|---|---|---|
| L0 | 1 | 20,453 | 20,453 | 20,480 (and 20,457 by `test_next_section`) |
| L1 | 3 | 83,403 | work 36,907 | per file, all within |
| L2 | 47 | 621,137 | `work/reference/dispatch.md` 31,487 | 32,768 |
| L3 | 49 | 172,300 | `modes/queue.md` 22,809 | 24,576 |

The L3 median is 1,861 B, which matches the test's docstring. Twenty-two shipped `.md` files fall outside every tier. These are root docs, `bin/`, `release/` and `schema/` contracts, `.perry/hook.md`, and the two root `state/` templates from finding 1.

**Negative guards work.** A real L2 page at 32,769 is red and at 32,768 is green (T1/T2). A real L3 page at 24,577 is red (T3). Raising either cap by 1 is red (T4/T5), and so is loosening the comparison by 1 (T8). The coverage gap is finding 1.

## Fix-ups

- **Relocate pointer (`SKILL.md` §`/perry relocate`).** The stub drops no rule. The removed clauses are "because it holds the pointer", "the `git mv` set is the only thing making the move reversible" and "`(reference/diagnose.md § Finding catalog)`". All three appear verbatim in `reference/router-subcommands.md` §`/perry relocate` at lines 32-33, 70-71 and 37. The stub still states every rule: claimed paths move; `State root` is set by `perry-config set`; `.perry/` never moves; the command refuses on a dirty tree; moves are computed from `claims[]`; each `from → to` is confirmed; it never moves a file it did not put there; it never deletes; and `NS-01` recommends it. This is acceptable under P1. `(handled here)` → `—` loses nothing, because the section opens with "Handled here, not in a lane".
- **plan-phase cap 80,000 → 110,000.**
  - **Honest.** The declared total on the head is 107,747, and rounding up to the next 5,000 gives 110,000. The other four caps also satisfy the same rule, both at `b8978116` and on the head. The rise comes from decided main content: DESIGN-020 added `elicitation.md` to the row, and `phases.md` grew.
  - **Pinned.** A 110,001 budget turns `test_each_fixed_cap_and_one_byte_over` red (B9). A real bill 1 byte over, made by padding `phases.md` until the total is 110,001, turns `test_cli_conflicts_and_installation_default` red (B17). At exactly 110,000 it is green (B18).
- **Temp-path fix.** `BudgetCase.setUp` now resolves `mkdtemp()`. It is correct and does not weaken the test. Under a TMPDIR that is a symlink (as macOS `/var` is), reverting the fix turns `test_bytes_dedup_read_only_and_no_session_discovery` red (F1). With the fix in place, the same test still catches a write (B12) and session discovery (B11). Under an already-resolved TMPDIR, F1 is green, which is why the defect escaped the author. The integrator's diagnosis is right.
- **Router no-growth.** Growing `SKILL.md` by 5 B turns `test_next_section.test_the_router_points_at_the_page_without_growing` red (F2).

## Mutation table

Before every mutant: all `__pycache__` dirs were purged. Each run used `python3 -B -m unittest discover -s tests -p <module>.py` with `PERRY_PROJECT` and `PERRY_HOME` unset. Every restore was checked clean against HEAD with `git status --porcelain`.

| ID | Mutation | Result | Killing test(s) |
|---|---|---|---|
| B1 | bill total − 1 | RED | `test_bytes_dedup_read_only_and_no_session_discovery`, `test_cli_conflicts_and_installation_default` |
| B2 | count characters, not bytes | RED | same two |
| B3 | dedup broken (sum repeated path) | RED | those two + `test_each_fixed_cap_and_one_byte_over` |
| B4 | drop a page: last ref of every row | RED | `test_shared_lane_and_non_l2_paths` |
| B5 | drop a page: ignore Reference-file table rows | RED | `test_shared_lane_and_non_l2_paths` |
| B6 | drop the L1 lane file | RED | `test_shared_lane_and_non_l2_paths` |
| B7 | over-budget reported within (`> cap+1`) | RED | `test_each_fixed_cap_and_one_byte_over` |
| B8 | over-budget exits 0 | RED | `test_each_fixed_cap_and_one_byte_over` |
| B9 | plan-phase cap 110,001 | RED | `test_each_fixed_cap_and_one_byte_over` |
| B10 | dispatch cap 115,001 | RED | `test_each_fixed_cap_and_one_byte_over` |
| B11 | session discovery in bill mode | RED | `test_bytes_dedup_read_only_and_no_session_discovery` |
| B12 | bill writes a file | RED | `test_bytes_dedup_read_only_and_no_session_discovery` |
| B13 | root containment removed | RED | `test_missing_ambiguous_and_escaping_declarations_fail` |
| B14 | ambiguous (two primary rows) accepted | RED | `test_missing_ambiguous_and_escaping_declarations_fail` |
| B15 | `--root` accepted with `--bill` | RED | `test_cli_conflicts_and_installation_default` |
| B16 | missing reference declaration → skipped | RED | `test_missing_ambiguous_and_escaping_declarations_fail` |
| B17 | real plan-phase bill = 110,001 | RED | `test_cli_conflicts_and_installation_default` |
| B18 | real plan-phase bill = 110,000 (control) | green | — (expected) |
| F1 | revert `mkdtemp().resolve()` (symlinked TMPDIR) | RED | `test_bytes_dedup_read_only_and_no_session_discovery` |
| F2 | `SKILL.md` +5 B (20,458) | RED | `test_next_section.test_the_router_points_at_the_page_without_growing` |
| T1 | real L2 page 32,769 | RED | `test_every_budgeted_file_is_within_its_cap` |
| T2 | real L2 page 32,768 (control) | green | — (expected) |
| T3 | real L3 page 24,577 | RED | `test_every_budgeted_file_is_within_its_cap` |
| T4 | L2 cap 32,769 | RED | `test_new_tiers_accept_exact_cap_and_reject_one_byte_over` |
| T5 | L3 cap 24,577 | RED | `test_new_tiers_accept_exact_cap_and_reject_one_byte_over` |
| T6 | L3 enumeration drops `modes/` | **green — survived** | finding 1 |
| T7 | L2 enumeration drops lane `reference/` dirs | **green — survived** | finding 1 |
| T8 | overflow check `> cap+1` | RED | `test_new_tiers_accept_exact_cap_and_reject_one_byte_over` |

## Suites

Both runs used `PERRY_PROJECT` and `PERRY_HOME` unset, `__pycache__` purged, and an isolated TMPDIR under the session scratchpad.

- `bash tests/run` (full): **green**, 155 modules, 4,373 tests, 157.0 s, 8 workers. Tree guard clean.
- `bash tests/run --tier slow`: **green**, 159 modules, 4,476 tests, 157.5 s. The `test_host_support` concurrency flake the integrator saw **did not reproduce**. No module went red, so no isolation re-run was needed.
- `git diff --check 262d487c af1e8fba`: clean.

## Integrator's account (`TASK-456-457-rebase/result.md`), checked

- **Confirmed:**
  - `git diff 5c7618f1 3124e3b8` over `work`, the diagnose pages, `tests/test_router_budget.py` and both module maps is empty.
  - `434c979e..262d487c` does not touch the split pages or the TASK-456/457 tool and test files.
  - Line deltas: TASK-456 −7, TASK-457 0.
  - All five head bill totals, and the round-up rule.
  - The relocate rule inventory.
  - The TMPDIR diagnosis.
- **Not reproduced:** the slow-tier `test_host_support` flake. It did not occur in my run.
- **Stated incompletely:** "rounded up from 77,030" and "107,766" are the pre-`3124e3b8` figures. The head is 107,747, and the same cap follows.

## Could not verify

- **The TASK-457 author's own receipts, hashes and revert proof**, and the reviewed state of TASK-456 at `434c979e`. The first are not in git (finding 2). For the second, I re-checked the content on this tree rather than relying on the earlier review.
- **Runtime behaviour on hosts other than macOS/Darwin** (for example Linux TMPDIR, or Windows paths in the `$PERRY_HOME/` join).
- **Whether the transitive and conditional context the bill excludes is small.** Examples are `packs/software-ops/architecture.md` during `dispatch`, and pages that `snapshot.md` tells the agent to read. This is out of scope by the spec and is labelled in the tool's output, but the bill is a lower bound, not the real load.
- **The architecture-review verdict for `tests/ARCHITECTURE.md` and `release/ARCHITECTURE.md`.** That is the separate exact-candidate architecture gate.
