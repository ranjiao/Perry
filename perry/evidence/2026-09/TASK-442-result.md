# TASK-442 — result

> Branch: `coding/task-442-next-section` · Base: `bb178072` · Executor: claude-subagent
> Written incrementally; each section is dated to the step that produced it.

## 0. Base check

- Worktree HEAD at dispatch: `0b5bf99e`. `git merge-base --is-ancestor HEAD bb178072` → 0,
  `bb178072` → HEAD → 1: HEAD was a strict ancestor and the tree was clean, so
  `git merge --ff-only bb178072` fast-forwarded it. Branch created at `bb178072`.
- Read in full before changing anything: `ARCHITECTURE.md`, `bin/ARCHITECTURE.md`,
  `perry/evidence/2026-09/TASK-442-spec.md`, `perry/design/DESIGN-020-guided-planning.md`
  (all of it, including § 5.1–5.4, § 6 phase A and the § 9 entry of 2026-09-15),
  and `USER-934` in `perry/asks.jsonl`.

## 1. Baseline at `bb178072` (measured in this worktree)

`bash tests/run` (PERRY_PROJECT and PERRY_HOME unset): **140 modules · 3934 tests ·
2 modules red · 10 tests failed.** Each red module was re-run alone with
`python3 tests/parallel <module>` and failed identically:

| Module | Alone | What fails |
|---|---|---|
| `test_md_store` | 9 of 76 red | objective ids minted 14 ≠ 10; the store holds 0 KRs against 13 KR lines in `perry/OKR.md` |
| `test_okr_krs_render` | 1 of 40 red | `perry/OKR.md` carries 13 KR table rows (`\| O1-KR1 \| carried → v4 …`) |

Both read this repository's own `perry/OKR.md` / `okr.jsonl`, which the base commit
itself rewrote to OKR v4 (`15369956`, `bb178072`). Neither touches `perry-state`.

## 2. Step 1 — the `next` block, the rule file, the rule page

(filled in as the work lands)
