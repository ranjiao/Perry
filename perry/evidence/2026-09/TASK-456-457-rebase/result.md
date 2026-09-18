# TASK-456 + TASK-457 — merged onto current main

Date: 2026-09-18. Author: Coding Agent (Claude). Branch: `task-456-457-rebase-20260918`.
Not merged to main, not pushed, no release allocated, no PMO state edited.

## SHAs

| Role | SHA |
|---|---|
| Base (main tip; the worktree was fast-forwarded from stale `0b5bf99e` with no local commits) | `262d487c` |
| TASK-456 input: reviewed r2 candidate (old base `434c979e`) | `5c7618f1` |
| TASK-457 input: delivery (built on pre-r2 `f5656a1c`) | `b8978116` |
| Merge 1: `--no-ff` merge of `5c7618f1` | `9dbaf42a` |
| Merge 2: `--no-ff` merge of `b8978116` | `777d45fe` |
| Fix-up 1: L0 stub, plan-phase cap, TMPDIR | `2fe31648` |
| Fix-up 2: router within `test_next_section`'s no-growth bound | `3124e3b8` |
| Result commit (adds only this file) | child of `3124e3b8` |

Merges, not rebases: both reviewed commits keep their identity and are ancestors of the head.

## Conflicts

**Textual: none.** Git auto-merged both. `SKILL.md` was the only file both sides touched (main at lines 71/125, TASK-457 at 180–185). The hunks are disjoint.

Main's 67 commits since `434c979e` touch none of the pages TASK-456 split (`work/**`, `reference/diagnose.md`). They also touch none of TASK-456's or TASK-457's test/tool files. **So no main edit had to be moved into a split part.** On the head, the split pages, `tests/test_router_budget.py` and both module maps are byte-identical to `5c7618f1`: `git diff 5c7618f1 3124e3b8 -- work reference/diagnose.md reference/diagnose-explanations.md tests/test_router_budget.py tests/ARCHITECTURE.md release/ARCHITECTURE.md` is empty. No section was dropped.

**Semantic: two, plus one latent defect.**

| # | File | Main side | Delivery side | Resolution |
|---|---|---|---|---|
| 1 | `SKILL.md` (L0: cap 20,480; `test_next_section` also pins it at ≤ 20,457, "must not grow") | TASK-444: +126 B (`plans/` in the ownership table, `planning.md` pointer). 20,321 → 20,447 | TASK-457: +134 B (Reference column plus the explicit `snapshot` row its spec AC1 requires) | Auto-merge gave **20,581 B, over both bounds**. Both additions are required content and were kept. Under DESIGN-017 P1 ("L0 points; it restates no L1 or L2 procedure"), the `/perry relocate` body became a stub. It keeps every rule: moves claimed paths; sets `State root` via `perry-config set`; `.perry/` never moves; refuses on a dirty tree; moves come from `claims[]`; confirms every `from → to` first; never moves a file it did not put there; never deletes; `NS-01` recommends it. It points at `reference/router-subcommands.md § /perry relocate` for the rationale it drops ("holds the pointer", "the `git mv` set is the only thing making it reversible", "never a hand-written list", the `NS-01` catalog citation). That page already carries all four. The heading stays, because `test_claims` and `perry-lint` stderr (`test_state_root_unset`) cite `SKILL.md § /perry relocate`. That gave 20,472, still over the 20,457 no-growth bound. So TASK-457's new help-row Reference cell `(handled here)` became `—`, because the section already opens "Handled here, not in a lane", and "Why and steps:" became "Steps:". **Result: 20,453 B.** Neither constant was raised. |
| 2 | `goals/SKILL.md` plan-phase index row → `plan-phase` bill | DESIGN-020/TASK-444: the row now declares `reference/phases.md` + `reference/elicitation.md`. `phases.md` 25,222 → 30,061 (TASK-444/264); `goals/SKILL.md` 21,964 → 22,415 | TASK-457: `plan-phase` cap 80,000 (rounded up from 77,030) | Declared total on the head is **107,747 B**. The bill's own rule rounds the declared total up to the next 5,000, and the other four caps still satisfy it unchanged. Applying it here raises the **cap to 110,000**. The change is in `BILL_BUDGETS` and the test's pinned dict, and the dated comment now names both measurements. The load set was not trimmed, because `elicitation.md` is a decided DESIGN-020 plan-phase read. |
| 3 | `tests/test_context_budget.py` | — | `b8978116` fails `test_bytes_dedup_read_only_and_no_session_discovery` under macOS's default TMPDIR (`/var/folders/…`). The tool resolves to `/private/var/…`, and the read-only `open` patch compares against unresolved paths. It passes only with an already-resolved TMPDIR. Reproduced on a clean export of `b8978116`. | `BudgetCase.setUp` resolves `tempfile.mkdtemp()` (a one-line edit). This is pre-existing, not caused by the merge. The assertion is unchanged. |

Observed, not a conflict: `work/reference/planning.md` (TASK-456, plan-week/triage) and `goals/reference/planning.md` (TASK-444, first-OKR drafts) share a basename. Every reference in shipped pages is lane-relative inside its own lane, or fully qualified (`goals/reference/planning.md`) from shared pages. Nothing is ambiguous today.

Main's added prose contains no new mention of `subcommands.md`, `dispatch.md` or `diagnose.md`, so no pointer needed redirecting. `test_pointers_resolve`, section-citation resolution and `test_shipped_vocabulary` are green with no edits to them.

## Tier budgets (DESIGN-017 §5.4, `tests/test_router_budget.py`, caps unchanged)

| Page | Tier | Cap | TASK-456 `5c7618f1` | Merged, before fix | Head |
|---|---|---|---|---|---|
| `SKILL.md` | L0 | 20,480 (≤ 20,457 by `test_next_section`) | 20,321 | **20,581 (over)** | 20,453 |
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

All 47 L2 pages are within 32,768. Only L0 went over, and no budget was raised. `phases.md` is the L2 page closest to its cap, with 2,707 B left.

## Context bills (`bin/perry-context-budget --bill all`, bytes)

| Bill | Declared files (head) | `b8978116` total / cap | Merged, before fix | Head total / cap | Cap changed? |
|---|---|---|---|---|---|
| snapshot | L0 + snapshot, host-capabilities, i18n, next | 75,921 / 80,000 | 77,385 | 77,257 / 80,000 | no |
| add-task | L0 + work L1 + add-task, input-quality, okr-linkage | 99,353 / 100,000 | 99,479 | 99,351 / 100,000 | no (649 B left) |
| close-task | L0 + work L1 + promotion, subcommands (`packs/software-ops/runbooks.md` excluded, non-L2) | 90,215 / 95,000 | 90,341 | 90,213 / 95,000 | no |
| dispatch | L0 + work L1 + dispatch, dispatch-preflight, git-boundaries | 113,560 / 115,000 | 113,686 | 113,558 / 115,000 | no |
| plan-phase | L0 + goals L1 + elicitation (new on main), phases, input-quality | 77,030 / 80,000 | **107,875 (over)** | 107,747 / **110,000** | **80,000 → 110,000** |

Per-file moves behind these numbers: L0 20,455 → 20,453. `reference/snapshot.md` 15,760 → 16,426 and `reference/next.md` 18,601 → 19,273 (TASK-444). `goals/SKILL.md` 21,964 → 22,415, `phases.md` 25,222 → 30,061, and `elicitation.md` newly declared at 25,429.

Mutation: setting `plan-phase` to 110,001 in a scratch copy turns `test_each_fixed_cap_and_one_byte_over` red. The existing cap/cap+1 loop covers the new value.

## Line deltas (Python/test: `bin/` + `tests/`, excluding `.md`)

| Scope | + | − | Net |
|---|---|---|---|
| TASK-456 own (`434c979e..5c7618f1`) | 56 | 63 | −7 |
| TASK-457 own (`f5656a1c..b8978116`) | 280 | 280 | 0 |
| This merge's fix-ups (`777d45fe..3124e3b8`) | 4 | 4 | 0 |
| Head vs base (`262d487c..3124e3b8`) | 337 | 344 | −7 |

## Suites (`PERRY_PROJECT`/`PERRY_HOME` unset, default TMPDIR)

| Run | Tree | Result |
|---|---|---|
| Base line `--tier slow` | `262d487c` | green, 159 modules / 4,471 tests |
| `tests/run` (full) | `2fe31648` | 1 red: `test_next_section` no-growth bound → fixed in `3124e3b8` |
| targeted (budget, pointers, vocabulary, context, claims, state-root, next-section) | `3124e3b8` | 191 OK |
| `tests/run` (full) | `3124e3b8` | green, 155 modules / 4,373 tests |
| `tests/run --tier slow` | `3124e3b8` | 1 red: `test_host_support.TestOpenCodeDispatchLimit.test_concurrent_registers_do_not_exceed_opencode_cap` (cap=2 won=3). Re-run alone 3×: OK each time. The merge changes one pointer line in that module and no dispatch/register code, so this is load-dependent and not attributed to the merge. |
| final full + slow on the result commit | result commit | reported by the agent in its hand-back (this file cannot carry its own commit's results) |

`git diff --check 262d487c 3124e3b8`: clean.

## Unresolved without changing meaning

- **L0 headroom is 4 bytes** against `test_next_section`'s no-growth bound, and 27 against the L0 cap. The relocate stub and the `—` cell are the only content judgements in this merge. A reviewer should confirm that moving the relocate rationale to the reference page is acceptable under P1.
- **The plan-phase bill cap rose by 37.5%** because main's decided load set grew. Lowering the bill instead would mean trimming `elicitation.md` or `phases.md`, or dropping `elicitation.md` from the plan-phase row. Both change DESIGN-020 content, so neither was done. TASK-470 (load-set reduction) is the natural owner.
- **TASK-457 still has no independent review**, and this merge adds a cap change and a test fix on top of it. TASK-456's review was on `434c979e`. Its reviewed bytes are unchanged here, but the L0 edits are new.
- `test_host_support`'s concurrency cap test flaked once under slow-tier load. This is pre-existing behaviour and outside this merge's scope.
