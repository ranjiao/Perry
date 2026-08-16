# `perry-goals list --json` — the goals contract

> Contract: **`perry-goals/list/1.0`**
> Locked by `tests/test_goals_contract.py`.
> DESIGN-005 § 6 step 2.

The third of Perry's read contracts, and the last one a front-end needs before
it can show a whole project — tasks, decisions, goals — without opening a single
markdown file.

```bash
"$PERRY_HOME/bin/perry-goals" list --json --root /path/to/project
```

`--level overall|phase` restricts the KR set. Read-only; writes nothing, takes
no lock.

## It parses nothing

Every field comes from `viewer/parsers.py § load_snapshot` — the same code
`perry-state` and the viewer use. A fourth reader of `OKR.md` would be a fourth
chance at the defect this project has already hit twice, most recently when
`perry-task` placed board cells by resolved header name while `viewer/parsers.py`
read them by position, and a board with one extra column reported every task's
owner as its track while `perry-lint` called it clean.

What this tool adds is a **flat `krs` array**. The nested objectives→krs shape is
already in `perry-state --json`; walking it and re-deriving progress in a
consumer is exactly the estimating `schema/README.md` forbids, done in a repo
Perry's tests cannot reach.

## The payload

```jsonc
{
  "contract":     "perry-goals/list/1.0",
  "project_root": "/abs/path",
  "state_root":   "/abs/path",
  "conformance":  { /* below */ },
  "okr":          { "present": true, "version": "v3: 2026-01-01", "mission": "…",
                    "operating_principles": [], "anti_goals": [],
                    "objectives": [ {"title": "…", "krs": ["KR1"]} ] },
  "phase":        { /* below, or null */ },
  "krs":          [ /* below */ ],
  "linkage":      { "present": true, "phase": "002-…", "updated": "…", "error": "" },
  "counts":       { "objectives": 3, "krs": 12, "stretch": 1 }
}
```

### A KR

| Key | Type | Notes |
|---|---|---|
| `id` | string | **not guaranteed unique** — see `conformance.duplicate_kr_ids` |
| `level` | string | `overall` (from `OKR.md`) or `phase` (from the current phase file) |
| `objective` | string | the objective's title, denormalized onto the row |
| `text` | string | |
| `metric` | string | free text — `median ≤ 12 min`, `count = 3`. Often empty on a real project. |
| `qualifier` | string | |
| `linked_to` | string | the overall KR this phase KR rolls up to, or `""` |
| `stretch` | bool | |
| `target` | number \| null | from the linkage register only |
| `current` | number \| null | from the linkage register only |
| `progress` | number \| null | `current / target`, rounded to 4dp. **`null` is not `0`** — see below. |
| `tasks` | array | task ids attributed to this KR by the register |

### The phase

| Key | Type | Notes |
|---|---|---|
| `number` | string | `004` |
| `slug` | string | `004-process-layer` |
| `status` | string | free text, in the document language |
| `started` | string | `YYYY-MM-DD` |
| `day` | int \| null | computed from `started`, not stored |
| `kr_total` | int \| null | counted from the phase's objectives |
| `cost_ceiling` | string | raw, as written |

`phase` is `null` on a project running goals with no current phase. That is a
normal state, not an error.

### `conformance`

| Key | Type | Meaning |
|---|---|---|
| `okr_present` | bool | |
| `phase_present` | bool | |
| `linkage_present` | bool | `false` means **no KR carries a target, a current, or a task edge** |
| `krs_without_metric` | array | ids whose `Metric / Target` cell the parser found empty |
| `krs_without_progress` | array | ids where `progress` is `null` |
| `krs_not_in_linkage` | array | phase KRs the register never mentions |
| `duplicate_kr_ids` | array | ids used more than once |

## Two things a consumer must not assume

- **`progress: null` is not `0`.** Without a linkage register there is no target
  and no current, so progress is unknown. Rendering 0% asserts no progress on
  work the payload knows nothing about. On a live project measured while writing
  this, **12 of 12 KRs** had `null` progress.
- **`id` is not unique.** The same live project reuses `KR1`, `KR2`, `KR3` and
  `KR6` across levels and objectives. Key by `(level, objective, id)` or by
  array index; `duplicate_kr_ids` tells you when it matters. Nothing is
  collapsed on your behalf — de-duplicating would drop a KR the user wrote.

Both are consequences of the same thing: `OKR.md` is prose a human argues with,
and this contract reports what that human wrote rather than a tidied version of
it.

## Not here

**Task→KR attribution.** It is a derived join over the board, and
`perry-state --json § attribution` already computes it from the same snapshot;
recomputing it in a second place is how the two would come to disagree.
`krs[].tasks` carries the edges the linkage register states directly.

**Writes.** `perry-goals` is read-only. `OKR.md` and `phase/` are still
hand-authored — DESIGN-005 § 6 step 3.
