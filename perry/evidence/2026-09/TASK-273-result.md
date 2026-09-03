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

## Reproduction — first pass

Harness: a throwaway project (`State root: .`, so the register stores sit at
the project root, not under `perry/`), three P-sections and a four-column
`## Top risks` table, driven through `bin/perry-task risk-add`.

**Direction 2 REPRODUCES, exactly as the spec describes it.**

Store before (two records, one id, differing on `cleared`):

```
{"id":"RX-001","title":"first risk","status":"open","cleared":""}
{"id":"RX-001","title":"a stale duplicate of RX-001","status":"cleared 2026-02-02","cleared":"2026-02-02"}
{"id":"RX-002","title":"second risk","status":"open","cleared":""}
```

After an ordinary `perry-task risk-add --title "another new risk"` (rc **0**):

```
{"id":"RX-001","risk":"first risk","opened":"2026-01-01","cleared":"2026-02-02","status":"open","order":0}
```

`RX-001` is `status: open` and now carries `cleared: 2026-02-02` — a date that
belonged to the other record. `by_id` (`:748`) kept the LAST record for the id,
and `risk_record`'s `if stored is not None and stored.get("cleared")` carried
its `cleared` onto the surviving row. Exit code 0.

**Direction 1 does NOT reproduce as written**, and the reason matters — see the
matrix below.
