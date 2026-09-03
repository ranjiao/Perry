# TASK-273 — result (IN PROGRESS)

- **Branch**: `coding/task-273-duplicate-ids`
- **Branched from**: `9c9670e` ("TASK-273 in_progress before dispatch") — the
  `main` tip named as the baseline in the brief.
- **Worktree cut correction**: the agent worktree was created at `d49964e`
  ("chore: consolidate test suite and project state"), ~140 commits behind
  `main`, where this spec does not exist. Branch was cut from `9c9670e`
  explicitly rather than from the worktree HEAD.

## What this round is about to do

1. Reproduce **direction 1** — a duplicate id on a *board* section silently
   drops a stored record on an ordinary write (`risk_records` / `ask_records`
   `seen` skip).
2. Reproduce **direction 2** — a duplicate id *in the store* collapses under
   `by_id = {...}` and leaks the survivor's `cleared` onto the other row.
3. Refuse rather than resolve, per `USER-904` / `USER-906` / `USER-915`:
   a board-side duplicate becomes a `perry-task` refusal (exit 1, write
   nothing); a store-side duplicate becomes a `perry-lint` report.
4. Decide whether `perry/tasks.jsonl`'s builder (`perry_store.py:202-248`)
   shares the hole, and say so either way.

Reproduction, controls, mutations and the tasks.jsonl verdict are filled in
below as they land.
