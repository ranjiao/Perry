# TASK-446 implementation delivery

- Branch: `codex/task-446-phase004-20260917`
- Exact base: `6a0cdb79a2d845a02d91dd8212f69794f312a352`
- Exact committed head: `1ea193f8b22b9f7e15825a35d8c13134bc032903`
- Checkout / canonical PERRY_HOME: `/private/tmp/perry-scratch/Perry/phase004-k4_waa0n/task-446`
- Child verification environment: PERRY_PROJECT unset; TMPDIR `/private/tmp/perry-scratch/task-446/phase004/tmp`; one suite at a time, at most 4 workers.
- Authorized scope: USER-957 continuation, TASK-446 only. Product paths: `reference/snapshot.md`, `reference/next.md`. Exact-path commit; +76/-31 documentation lines. Net product Python/test lines = 0. No dependency, renderer, schema, command or store added.

## Behavior

Combined `/perry` initial rendering has a 12-line / 1,200-Unicode-character budget, including whitespace, links, next block, note and any question. Project/phase position, honest progress, task counts, pending decisions and the selector's primary remain visible. One explicit detail pointer retains full pending requests, titled objective/KR measures, secondary facts, every returned alternate and unknown cause, plus capture provenance. Already authorized work continues without demanding a fresh question; an unscoped invocation keeps its question. No automatic execution of selector advice.

Recovery and interrupted-run startup gates, active-pack glossary, tracks_source guidance, and lane routing are unchanged. The next reference only adds the combined-view cross-reference; lane standups and the shared closing procedure remain intact.

## Captured renderings and measurements

Source calls: `bin/perry-state --compact` -> `compact.json`; `bin/perry-state --section next` -> `next.json`, at pinned checkout. Compact generated_at `2026-09-17T16:39:09`. `bin/perry-explain` captures for missing titles are retained as ID.txt. Recovery was nonblocking; interrupted list empty. Source reports project name `task-446` (checkout name), not a renamed main project.

`before.txt` is an agent-authored rendering of the pre-change procedure from these fresh facts, not a claim that a historical UI screen was captured. `normal.initial.txt` + `normal.details.md` retain those facts and all pending requests/unknowns. Other examples are explicitly synthetic typed JSON fixtures; no fake tool-capture claim.

| Rendering | Lines | Unicode characters | UTF-8 bytes |
|---|---:|---:|---:|
| Before | 30 | 2423 | 2513 |
| Normal/live after | 7 | 676 | 703 |
| Many objectives/long titles/pending items | 8 | 432 | 449 |
| Unknown/absent measures, null primary | 8 | 438 | 453 |
| Blocking recovery startup | 5 | 328 | 334 |

Counts include newline/Markdown link text conservatively. `measure.py` and `measurements.json` retain deterministic count evidence. Python only handles literal text/typed fields and counts; it does not judge prose meaning. All original initial fixtures pass; the old rendering fails both limits. UI wrapping is not controlled or claimed.

## Verification

- Read `tests/run` and affected runner source before invocation; never invoked `tests/run --help`.
- `bash tests/run --tier smoke`: PASS; checkout tree guard unchanged (`smoke.log`).
- `python3 tests/parallel test_next_section test_next_closing test_router_budget test_tracks_source_documented -j 4`: PASS, 4 modules / 64 tests (`targeted.log`).
- Committed `python3 tests/parallel --tier affected --base 6a0cdb79a2d845a02d91dd8212f69794f312a352 -j 4`: PASS, 14 modules / 318 tests / 12.5s (`affected.log`, includes complete printed selection and reasons). 14 of 158 modules selected; this is not a full-suite claim.
- `git diff --check` and `git diff --cached --check`: PASS. Final tree clean.
- Bounded existing pointer guard: replace only snapshot's `--section next` invocation with `--section removed`, run the single pointer-contract test -> FAIL; restore exact original bytes -> PASS. SHA256 restoration in `pointer-mutation.log`; driver `pointer-mutation.py`. No mutation committed.
- Bounded rendered mutations: `mutations/omitted-pending.details.md` drops one of six requests, `mutations/omitted-unknown.details.md` drops a returned unknown cause, `mutations/oversized.initial.txt` is 87 lines / 2036 characters. Independent reviewer rejects all three. Valid originals are retained unchanged; mutation/revert means returning to those originals, not altering PMO state. Structural tests are not presented as semantic verification.
- Independent fresh-context review: `review.md`; reviewer requested retention of all supplied KR targets, now included with current null/unknown and titled IDs. This review is evidence for main PMO, not an implementing-session award of V4/V5 or task closure.

## ARCHITECTURE COMPLIANCE

Existing procedure applies until TASK-455 is independently accepted. Reviewed against frozen architecture §2 lanes/reference ownership, §3 forbidden boundaries and NN-4: changes are agent-rendering instructions only; `perry-state` remains source of all state figures and recommendation ordering. No new reader, runtime decision engine, semantic classifier, deterministic prose judgement, store, schema or command. No frozen architecture edits. No TASK-455 dispatch/review or TASK-447 linter changes. Evidence counters are external scratch and cannot select recommendations or interpret requests. Git scope and zero Python/test delta support these claims; independent reviewer checks semantic fidelity.

## Limitations and handoff

Four bounded fixtures demonstrate the budget; arbitrary mandatory selector reasons or safety errors may exceed it. The procedure requires an honest exception rather than suppressing required facts or claiming a passing count. This is an agent-authored procedure, not a new runtime enforcement mechanism. The safety fixture demonstrates the recovery-first stop; interrupted choice/card text and no-auto-resume rules remain unchanged rather than being reimplemented.

No full/slow run: main integrator owns merged full/slow verification and release allocation. No push, merge, publish, version allocation, task state, asks, journal, live/copied PMO store, PMO evidence or decided architecture writes. All evidence here is external scratch for main PMO to persist. No V4/V5 self-award or task closure.
