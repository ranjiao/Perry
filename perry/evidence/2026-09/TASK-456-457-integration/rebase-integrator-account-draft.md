# TASK-456 + TASK-457 — merged onto current main

Date: 2026-09-18. Author: Coding Agent (Claude). Branch: `task-456-457-rebase-20260918`.
Not merged to main, not pushed, no release allocated, no PMO state edited.

## SHAs

| Role | SHA |
|---|---|
| Base (main tip, worktree fast-forwarded from stale `0b5bf99e`) | `262d487c` |
| TASK-456 input: reviewed r2 candidate (old base `434c979e`) | `5c7618f1` |
| TASK-457 input: delivery (built on pre-r2 `f5656a1c`) | `b8978116` |
| Merge 1: `--no-ff` merge of `5c7618f1` | `9dbaf42a` |
| Merge 2: `--no-ff` merge of `b8978116` | `777d45fe` |
| Fix-up: budgets and TMPDIR | `2fe31648` |
| Code head that was tested (this file is added in the next commit only) | `2fe31648` |

Merges, not rebases: both reviewed commits keep their identity and are ancestors of the head.

## Conflicts

**Textual: none.** Git auto-merged both. `SKILL.md` was the only file both sides touched (main at lines 71/125, TASK-457 at 180–185). The hunks are disjoint.

Main's 67 commits since `434c979e` touch none of the pages TASK-456 split (`work/**`, `reference/diagnose.md`). They also touch none of TASK-456's or TASK-457's test/tool files. **So no main edit had to be moved into a split part.** On the head, the split pages, `tests/test_router_budget.py` and both module maps are byte-identical to `5c7618f1` (`git diff 5c7618f1 2fe31648 -- work reference/diagnose*.md tests/test_router_budget.py tests/ARCHITECTURE.md release/ARCHITECTURE.md` is empty).

**Semantic: two, plus one latent defect.**

| # | File | Main side | Delivery side | Resolution |
|---|---|---|---|---|
| 1 | `SKILL.md` (L0, cap 20,480) | TASK-444: +126 B (`plans/` in the ownership table, `planning.md` pointer). 20,321 → 20,447 | TASK-457: +134 B (Reference column + explicit `snapshot` row, required by its spec AC1) | Auto-merge gave **20,581 B, 101 over**. Both additions are required content, so neither was cut. Under DESIGN-017 P1 ("L0 points; it restates no L1 or L2 procedure"), the `/perry relocate` body became a stub. It keeps every rule: moves claimed paths; sets `State root` via `perry-config set`; `.perry/` never moves; refuses on a dirty tree; moves come from `claims[]`; confirms every `from → to`; never moves a file it did not put there; never deletes; `NS-01` recommends it. It points at `reference/router-subcommands.md § /perry relocate` for the rationale it drops ("holds the pointer", "`git mv` set is the only thing making it reversible", "never a hand-written list", the `NS-01` catalog citation). That page already carries every one of those, verbatim or as a stronger procedure step. The heading stays: `test_claims` and `perry-lint` stderr (`test_state_root_unset`) cite `SKILL.md § /perry relocate`. **Result: 20,472 B (8 B of room).** |
| 2 | `goals/SKILL.md` plan-phase index row → `plan-phase` bill | DESIGN-020/TASK-444: row now declares `reference/phases.md` + `reference/elicitation.md`; `phases.md` 25,222 → 30,061 (TASK-264); `goals/SKILL.md` 21,964 → 22,415 | TASK-457: `plan-phase` cap 80,000 (rounded up from 77,030) | Declared total on the head is **107,766 B**. The bill's own rule is "round the declared total up to the next 5,000", which the other four caps still satisfy unchanged. Applying it here raises the **cap to 110,000**. The change is in `BILL_BUDGETS` and the test's pinned dict; the dated comment now names both measurements. The load set was not trimmed: `elicitation.md` is a decided DESIGN-020 plan-phase read. |
| 3 | `tests/test_context_budget.py` | — | `b8978116` fails `test_bytes_dedup_read_only_and_no_session_discovery` under macOS's default TMPDIR (`/var/folders/…`). The tool resolves to `/private/var/…`, and the read-only `open` patch compares against unresolved paths. It passes only with an already-resolved TMPDIR. Reproduced on a clean export of `b8978116`. | `BudgetCase.setUp` now resolves `tempfile.mkdtemp()` (a one-line edit). This is pre-existing, not caused by the merge. The assertion is unchanged. |

Observed, not a conflict: `work/reference/planning.md` (TASK-456, plan-week/triage) and `goals/reference/planning.md` (TASK-444, first-OKR drafts) share a basename. Every reference in shipped pages is lane-relative inside its own lane, or fully qualified (`goals/reference/planning.md`) from shared pages. Nothing is ambiguous today.

Main's added prose contains no new mention of `subcommands.md`, `dispatch.md` or `diagnose.md`, so no main pointer needed redirecting. Section-citation resolution and `test_pointers_resolve` are green without edits.

## Tier budgets (DESIGN-017 §5.4, `tests/test_router_budget.py`, caps unchanged)

| Page | Tier | Cap | TASK-456 `5c7618f1` | Merged, before fix | Head |
|---|---|---|---|---|---|
| `SKILL.md` | L0 | 20,480 | 20,321 | **20,581 (over)** | 20,472 |
| `goals/SKILL.md` | L1 | 22,528 | 21,964 | 22,415 | 22,415 |
| `work/SKILL.md` | L1 | 38,912 | 36,907 | 36,907 | 36,907 |
| `decide/SKILL.md` | L1 | 24,576 | 24,081 | 24,081 | 24,081 |
| `work/reference/dispatch.md` | L2 | 32,768 | 31,487 | 31,487 | 31,487 |
| `goals/reference/phases.md` | L2 | 32,768 | 25,222 | 30,061 | 30,061 |
| `work/reference/planning.md` | L2 | 32,768 | 29,756 | 29,756 | 29,756 |
| `goals/reference/elicitation.md` | L2 | 32,768 | 12,766 | 25,429 | 25,429 |
| `reference/diagnose.md` | L2 | 32,768 | 25,347 | 25,347 | 25,347 |
| `work/reference/subcommands.md` | L2 | 32,768 | 24,185 | 24,185 | 24,185 |
| `goals/reference/planning.md` (new on main) | L2 | 32,768 | — | 7,164 | 7,164 |
| max L3 (`modes/queue.md`, 49 pages) | L3 | 24,576 | 22,809 | 22,809 | 22,809 |

47 L2 pages, all within 32,768. Only L0 went over, and no budget was raised. The largest L2 margin consumed by main is `phases.md`, with 2,707 B left.

## Context bills (`bin/perry-context-budget --bill all`, bytes)

| Bill | Files (head) | `b8978116` total / cap | Merged-before-fix total | Head total / cap | Cap changed? |
|---|---|---|---|---|---|
| snapshot | L0 + snapshot, host-capabilities, i18n, next | 75,921 / 80,000 | 77,385 | 77,276 / 80,000 | no |
| add-task | L0 + work L1 + add-task, input-quality, okr-linkage | 99,353 / 100,000 | 99,479 | 99,370 / 100,000 | no (630 B left) |
| close-task | L0 + work L1 + promotion, subcommands (runbooks excluded, non-L2) | 90,215 / 95,000 | 90,341 | 90,232 / 95,000 | no |
| dispatch | L0 + work L1 + dispatch, dispatch-preflight, git-boundaries | 113,560 / 115,000 | 113,686 | 113,577 / 115,000 | no |
| plan-phase | L0 + goals L1 + elicitation (new on main), phases, input-quality | 77,030 / 80,000 | **107,875 (over)** | 107,766 / **110,000** | **80,000 → 110,000** |

Per-file changes behind the moves: L0 20,455 → 20,472. `reference/snapshot.md` 15,760 → 16,426 and `reference/next.md` 18,601 → 19,273 (TASK-444). `goals/SKILL.md` 21,964 → 22,415, `phases.md` 25,222 → 30,061, and `elicitation.md` newly declared at 25,429.

Mutation: `plan-phase` set to 110,001 in a scratch copy turns `test_each_fixed_cap_and_one_byte_over` red. The existing cap/cap+1 loop covers the new value.

## Line deltas (Python/test, `bin/` + `tests/` excluding `.md`)

| Scope | + | − | Net |
|---|---|---|---|
| TASK-456 own (`434c979e..5c7618f1`) | 56 | 63 | −7 |
| TASK-457 own (`f5656a1c..b8978116`) | 280 | 280 | 0 |
| This merge's fix-ups (`777d45fe..2fe31648`) | 4 | 4 | 0 |
| Head vs base (`262d487c..2fe31648`) | 337 | 344 | −7 |

## Suites (head `2fe31648`, `PERRY_PROJECT`/`PERRY_HOME` unset, default TMPDIR)

SUITE_RESULTS

## Unresolved without changing meaning

- **L0 headroom is 8 bytes.** Any further router line needs another stub or a section move. The relocate stub is the only content judgement in this merge. A reviewer should confirm that dropping the rationale from L0 is acceptable under P1.
- **The plan-phase bill cap rose by 37.5%** because main's decided load set grew. Lowering the bill instead would mean trimming `elicitation.md` or `phases.md`, or removing `elicitation.md` from the plan-phase row. That changes DESIGN-020 content, so it was not done. TASK-470 (load-set reduction) is the natural owner.
- **TASK-457 still has no independent review**, and this merge adds a cap change and a test fix on top of it. TASK-456's review was on `434c979e`. Its reviewed bytes are unchanged here, but the L0 fix is new.
