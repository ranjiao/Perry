# P004-O2-KR2 · `hand-appends-after` — census, 2026-09-21

Measured by a read-only fresh-context subagent on the PMO's brief; report copied
here by the PMO (the subagent could not write files). Pairing script kept at
`/private/tmp/perry-scratch/Perry/census-hand-appends/pair.py` (scratch, not
retained). **Value recorded: 0.**

## Audit window

| | SHA | Date |
|---|---|---|
| Primary start (exclusive) | `3449e8a1` — TASK-264 accepted and closed | 2026-09-18 15:03:57 +0800 |
| Secondary start (exclusive) | `778a1587` — TASK-264 D3 integrated | 2026-09-18 |
| End (inclusive) | `37e5de12` (main HEAD when measured) | 2026-09-21 |

98 first-parent commits, 177 in all (43 merges). `git log 778a1587..HEAD --
perry/okr.jsonl perry/linkage.jsonl` lists 5 commits, all single-parent on the
first-parent line; `--first-parent -m` lists the same 5, so no merge adds a store
change. No duplicate records by content.

## How a record is paired to its tool event (read from the writers)

| Record (store) | Writer | Event | Compared |
|---|---|---|---|
| `unlinked` / `edge` `via:"add"` (linkage) | `perry-task add --unlinked` / `--kr` | `add` with `kr` key | task, actor, `declared_at` vs `ts` |
| `check` (linkage) | `perry-goals check` | `check`, `file: linkage.jsonl` | kr, okr_version, id, direction, target, baseline, actor, time |
| `measurement` (linkage) | `perry-goals measure` | `measure` | kr, okr_version, check, value, evidence, actor, time |
| `kr_revision` | `perry-goals kr restate` / `withdraw` | `kr_restate` / `kr_withdraw` | kr, reason, file, actor, fields vs `changes[].after`, time |

## Result — primary window (3449e8a1, 37e5de12]

- `perry/okr.jsonl`: 0 added, 0 deleted or modified.
- `perry/linkage.jsonl`: 32 added, 0 deleted or modified; all 32 paired.

| Commit | Records | Paired events |
|---|---|---|
| `262d487c` | 6 `unlinked` (TASK-468–473) | 6 `add`, `kr: null`; TASK-473 1 s apart, others same second |
| `8a081790` | 1 `unlinked` (TASK-474) | `add`, same second |
| `801cf912` | 1 `unlinked` (TASK-475) | `add`, same second |
| `f2e3055c` | 13 `check`, 1 `kr_revision`, 8 `measurement` | 13 `check`, 1 `kr_restate`, 8 `measure`, same second, fields equal; restate's `before` matches the `kr` record |
| `37e5de12` | 2 `measurement` | 2 `measure`, same second |

Reverse direction: 32 store-writing events in the window, each with its record.
`.perry/events.jsonl` lost no lines. Secondary window (from `778a1587`): the
same 32 records, 0 hand appends.

## Limits

1. A matched pair shows an event exists, not that the tool ran; a hand-typed
   record plus a hand-typed event would pass. Key order, sub-second timestamps
   and the two stamp spellings support tool authorship; that is not proof.
2. Committed history only; a line added and removed between commits is invisible.
3. main's first-parent line only; unmerged branches are outside the window.
4. Pairing rules come from the writers at HEAD.
5. The window is set by commit order; all 32 records are dated after `3449e8a1`.
6. This checks that a tool wrote each record, not that the write was authorised.

`VALUE hand-appends-after = 0`
