# `perry-goals list --json` — the goals contract

> Contract: **`perry-goals/list/2.0`**
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
  "contract":     "perry-goals/list/2.0",
  "project_root": "/abs/path",
  "state_root":   "/abs/path",
  "conformance":  { /* below */ },
  "okr":          { "present": true, "version": "v3: 2026-01-01", "mission": "…",
                    "operating_principles": [], "anti_goals": [],
                    "objectives": [ {"title": "…", "krs": ["KR1"]} ] },
  "phase":        { /* below, or null */ },
  "krs":          [ /* below */ ],
  "answered_by":  "linkage",               // linkage | prose | none
  "unlinked_task_ids": ["REL-009"],        // DECLARED, never inferred
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
| `title` | string | |
| `metric` | string | free text — `median ≤ 12 min`, `count = 3`. Often empty on a real project. |
| `qualifier` | string | |
| `linked_to` | string | the overall KR this phase KR rolls up to, or `""` |
| `stretch` | bool | |
| `target` | number \| null | from the linkage register only |
| `current` | number \| null | from the linkage register only |
| `due` | string | from the register, else the KR row |
| `task_ids` | array | task ids attributed to this KR by the register |

### The phase

| Key | Type | Notes |
|---|---|---|
| `id` | string | the phase number, `004` |
| `name` | string | the phase slug, `004-process-layer` |
| `number` | string | same as `id`; kept because Perry's own docs say "phase #NNN" |
| `slug` | string | same as `name` |
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
| `krs_without_numbers` | array | ids missing `target`, `current`, or both — a bar cannot be drawn for these |
| `krs_not_in_linkage` | array | phase KRs the register never mentions |
| `duplicate_kr_ids` | array | ids used more than once |

## `answered_by` and `unlinked_task_ids`

| Key | Type | Meaning |
|---|---|---|
| `answered_by` | string | which source answered: `linkage` (the register, so targets/currents/edges exist), `prose` (`OKR.md` and the phase file only), or `none`. A cascade with nothing to show should say **"no register"**, not "no progress" — those are different facts and only one is about the work. |
| `unlinked_task_ids` | array | board tasks serving no KR. **Declared, never inferred.** A task absent from every `task_ids` might be unlinked, or might be a payload the consumer truncated; only Perry can tell those apart, so Perry says which. |

## Two things a consumer must not assume

- **There is no `progress` field, deliberately.** `target` and `current` are
  emitted as numbers or `null` and **never as a pre-computed percentage**, because
  Perry cannot tell which direction a KR runs. Half of a real OKR's targets are
  ceilings rather than goals, and a max-drawdown limit rendered two-thirds
  achieved is the worst thing a dashboard can say. Perry's own test fixture
  makes the point without needing a risk metric: a KR reading `manual steps = 0`
  has `target: 0`, and `current / target` is a division by zero. Only the
  project knows the direction, so only the project draws the bar.
  (`progress` shipped in `1.0` and is removed here. That is what makes this
  `2.0`; it was live for one day and no consumer had adopted it.)
- **`id` is not unique.** The same live project reuses `KR1`, `KR2`, `KR3` and
  `KR6` across levels and objectives. Key by `(level, objective, id)` or by
  array index; `duplicate_kr_ids` tells you when it matters. Nothing is
  collapsed on your behalf — de-duplicating would drop a KR the user wrote.

Both are consequences of the same thing: `OKR.md` is prose a human argues with,
and this contract reports what that human wrote rather than a tidied version of
it.

## Not here

**A pre-computed percentage.** See above.

**Objective ids invented from position.** `OKR.md` writes `### Objective 1 —
<title>`, and that "1" is ordinal prose, not a handle. `objectives[].id` is
filled from the linkage register when it names one and left `""` otherwise.
Deriving `O1`, `O2` from order would mint a key the file never stated, and a
consumer would key on it right up until two headings were reordered.

**Writes.** `perry-goals` is read-only. `OKR.md` and `phase/` are still
hand-authored — DESIGN-005 § 6 step 3.
