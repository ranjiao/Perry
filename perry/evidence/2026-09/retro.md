# Retro — phase #003 `storage-code`

> Phase: #003-storage-code · started 2026-08-28 · scored 2026-09-15
> Written by the `work` lane from the goals lane's retro summary
> (`goals/reference/phases.md § score-phase` step 5). The scores and the
> retro itself live in `phase/003-storage-code.md § Retro — phase scored`, and the
> frozen copy is `phase/snapshots/2026-09-15-003-storage-code-final.md`.

## Scores (each KR status is the user's answer)

| Objective | score | KRs |
|---|---|---|
| O1 — every declared store exists, and one command checks all of them | 1.0 | KR1, KR2 and KR3 achieved |
| O2 — the code reads a store, not a rendered file | 0.75 | KR1 achieved; KR2 dropped 2026-09-02; KR3 partial (0.5, the PMO's number) |
| O3 — the phase's KRs cover the work that actually runs | 0.33 | KR2 partial, 20 of 60 (1 of 1 since the refusing gate) |

**Definition of Done:**
- Must-have items 1–4 are met.
- Must-have item 5 is met only on the refusing-gate reading; the user scored its KR partial.
- Nice-to-have item 6 was delivered but is partial in effect.
- Nice-to-have item 7 is met.

## Work closed in the phase's last two days

- **`TASK-237`** (V4): `BOARD.md` deleted; the board is what `perry-tasks board` prints. A write refuses where nothing is installed.
- **`TASK-262`** (V3):
  - the board names each section's store and writers, and marks what is not stored;
  - a `BOARD.md` a project still holds is retired across every reader;
  - `perry-task/list` 2.4, `perry-asks/list` 1.4, `perry-goals/list` 3.4;
  - NN-2 restated with the user;
  - the user's reading is recorded.
- **`TASK-335`** (V3): the parity tests read a frozen copy, so the suite has no standing reds.
- **`TASK-439`** (V4): `add` refuses when a register declares the phase. **`TASK-253`**, **`TASK-268`** and **`TASK-198`** closed too.

## Lessons

- **A gate that only warns cannot move a KR phrased "in the same action as `add`".** The 40 rows filed under the advisory gate cannot be repaired.
- **Take a person's reading early when a KR's property is what a reader sees.** One reading at round 1 would have reworded the section line.
- **Grep the contract pages when writing a spec that changes a behaviour.** `TASK-262` round 3 stopped on three pins.
- **Commit after every coherent step.** Background agents were interrupted three times in one day (one stall, two API 403s), and step commits are what kept the work.

## Carry-overs proposed for `plan-phase` 004

- **The 40 never-answered rows**, per DoD item 5's restatement: re-declared against the new KRs, not copied.
- **O2-KR3's remaining gap:** a section line that tells a reader where to change a cell, and a second reading.
- **`R5`:** retire the `render` / `diff` / `verify` verbs after the consumer projects are upgraded (`reference/version-compatibility.md`).
- **`OKR.md` v2 Objective 3** needs `/perry goals revise`.
- **`TASK-262` findings kept in its evidence, no rows:** F16, F21, F22, F30, F35.
