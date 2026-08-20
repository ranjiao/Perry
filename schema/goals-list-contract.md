# `perry-goals list --json` — the goals contract

> Contract: **`perry-goals/list/2.1`**
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
  "contract":     "perry-goals/list/2.1",
  "project_root": "/abs/path",
  "state_root":   "/abs/path",
  "conformance":  { /* below */ },
  "okr":          { "present": true, "version": "v3: 2026-01-01", "mission": "…",
                    "operating_principles": [], "anti_goals": [],
                    "objectives": [ {"id": "", "title": "…", "krs": ["KR1"]} ] },
  "phase":        { /* every key in the table below, and: */
                    "objectives": [ {"id": "O1", "title": "…",
                                     "krs": ["P-O1.1"]} ] },   // or null
  "krs":          [ { /* every key below; the three provenance blocks in full */
      "id": "KR1", "level": "phase", "objective": "…", "title": "…",
      "metric": "…", "qualifier": "", "linked_to": "", "stretch": false,
      "target": 0, "current": 0, "due": "", "task_ids": ["TASK-094"],
      "current_provenance": {
        "state": "asserted", "measured": false, "source": "linkage-register",
        "asserted_at": "2026-08-20T20:32:00", "asserted_scope": "register" },
      "current_staleness": {
        "stale": true, "evaluated": true, "since": "2026-08-20T20:32:00",
        "reason": "1 linked task changed state after 2026-08-20T20:32:00: …",
        "moved_tasks": [ { "id": "TASK-094", "from": "review", "to": "done",
                           "at": "2026-08-21T09:10:00" } ] },
      "linked_task_completion": {
        "total": 2, "done": 1, "dropped": 0, "open": 1, "unknown": 0 }
  } ],
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
| `current` | number \| null | from the linkage register only. **Asserted by a human, never measured** — see below |
| `due` | string | from the register, else the KR row |
| `task_ids` | array | task ids attributed to this KR by the register |
| `current_provenance` | object | who asserted `current` and when |
| `current_staleness` | object | whether a linked task has moved since |
| `linked_task_completion` | object | how many linked tasks are closed. **Not progress** |

### `current` is an assertion, and these three blocks say so

Added in `2.1`. Until then the payload emitted `target` and `current` as bare
numbers, and both of the readings a consumer could take from Perry's own
register on 2026-08-21 were wrong — in opposite directions:

- `P-O1.1` read `0.0 / 1.0`, i.e. nothing done, while all four of its linked
  tasks were closed and the thing it asks for had shipped.
- `P-O2.2` read `0.0 / 0.0`, i.e. **met**, while the task under it had measured
  13 row splits and 87 header resolutions still live.

The second is the systemic one. Six of that register's eight phase KRs drive a
count to zero, and the register template writes `current: 0`, so a
drive-to-zero KR reads as achieved on the day it is written.

**What is NOT here, and will not be.** `linked_task_completion` is a count of
tasks and never a fraction of the KR. A KR's metric is a count of something in
the repository — *"0 occurrences of `CLOCK_RE`"* — and a closed task does not
establish that the count is zero; only re-running the count does. Rolling the
edges up into `current` would publish a fabricated measurement, which
`perry/OKR.md § Operating Principles` forbids in its first line. The two
numbers are emitted side by side, in different units, and the consumer draws
whatever conclusion it likes from the pair. Perry draws none.

| Key | Type | Notes |
|---|---|---|
| `current_provenance.state` | string | `asserted` when the register gave a number, `unasserted` when it did not. **An absent `current` is `null` and `unasserted`, never `0`** — that default is what makes a drive-to-zero KR read as met before the work starts |
| `current_provenance.measured` | bool | **always `false` today.** No tool in Perry re-runs a KR's metric, so nothing it publishes as `current` is a measurement. Emitted rather than implied, so a consumer showing "measured" has an explicit answer to key on |
| `current_provenance.source` | string | `linkage-register`, or `""` when unasserted |
| `current_provenance.asserted_at` | string | the register's own `updated` timestamp, or `""` |
| `current_provenance.asserted_scope` | string | `register` — the date above belongs to the **whole register**, not to this KR. Emitted with the date so it cannot be read as "when this number was arrived at" |
| `current_staleness.stale` | bool | a linked task changed state after `asserted_at` |
| `current_staleness.evaluated` | bool | whether staleness could be decided at all. `false` with `stale: false` means *nobody asked*, not *nothing moved* — a register with no `updated`, or a project with no event log, cannot answer |
| `current_staleness.since` | string | the timestamp compared against, or `""` |
| `current_staleness.reason` | string | prose, always populated, in both directions |
| `current_staleness.moved_tasks` | array | the tasks that moved, each `{id, from, to, at}`. `from` is `""` for a task created after the assertion |
| `linked_task_completion.total` | int | ids in `task_ids` |
| `linked_task_completion.done` | int | |
| `linked_task_completion.dropped` | int | counted apart from `done`: a dropped task closed without advancing anything |
| `linked_task_completion.open` | int | in any non-terminal status |
| `linked_task_completion.unknown` | int | an id neither the board nor the event log knows — a dangling edge, never silently counted as open |

A task closed with `perry-task done` may be off `BOARD.md` altogether, so a
task's status is taken from the board first and from the last state-moving
event second. `moved_tasks` reads the event log only, and an event counts as a
state move when its `to` is a task status — `next`, `evidence` and `rung` also
carry `from`/`to` and hold prose, a path and a rung.

**One honest limit.** The register writes `updated` as an ISO datetime with a
`Z`; the event log writes `ts` as a naive local datetime with no zone. There is
no conversion between those that is not a guess, so the `Z` is stripped rather
than applied. A register written within a few hours of a task move can
therefore order wrongly, and `stale: false` is that much weaker than it looks.
A date-only `updated` is read as midnight, which errs toward reporting
staleness on purpose: a false *recheck this* costs a look, a false *this number
is fine* costs the number.

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
| `objectives` | array | the phase's own objectives, nested, each `{id, title, krs}` — see below. This is the **nested** shape; `krs` at the top level is the flat one, and the two are different views of the same rows, not two sets of rows |

`phase` is `null` on a project running goals with no current phase. That is a
normal state, not an error.

### An objective — and why it is sketched rather than tabulated

The same three-key entry appears twice: under `okr.objectives[]` and under
`phase.objectives[]`.

- **`id`** — string. `O1` in a phase file, which writes `### O1 — <title>`.
  **`""` under `okr.objectives[]`**, because `OKR.md` writes
  `### Objective 1 — <title>` and that "1" is ordinal prose rather than a
  handle — see *Not here* below. Never invented from position, in either place.
- **`title`** — string. The objective's title, as written.
- **`krs`** — array of strings. The ids of the KRs filed under it, in document
  order. **Ids only**: the KRs themselves are in the flat top-level `krs`
  array and are not duplicated here.

**Why this is a list and not a key table, deliberately.**
`tests/contract_key_parity.py` places a key table by matching its key set
against the payload's containers and breaks ties on precision.
`okr.objectives[]` and `phase.objectives[]` carry *exactly* the same three
children, so a table of `id`, `title`, `krs` scores 1.00 coverage and 1.00
precision against **both**, ties, and is placed on neither — it would be
reported as unassigned and all four paths would stay uncounted. Writing the
table would therefore make the page look documented and leave the count where
it was. The four paths are declared in the payload sketch above instead, which
carries real nested paths and has no ambiguity to resolve, and the checker
reads the sketch and the tables alike. Nothing here is exempt from the check;
it is declared in the half of the page that can express the nesting.

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
| `krs_with_stale_current` | array | ids whose linked tasks moved after `current` was asserted. There is deliberately no companion entry for *`current` disagrees with its tasks*: that judgement needs the metric re-run |

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

**The commitments register.** `OKR.md § Commitments` is written by
`perry-goals commit` (TASK-042) and is **not** carried in this payload. See the
Changelog below for why that was a decision rather than an oversight.

Its columns changed under TASK-091 and this payload still did not move. For a
consumer that parses the markdown — which is what `modes/pipeline.md § Triage`
step 3 still instructs — the register now reads:

- `Id`, `Track`, `Promise`, `To whom`, `Status` — as before.
- **`Due`** — an ISO date (`2026-09-30`) or an SLA token (`3d`, `2w`, `24h`).
  Typed: nothing else can be written into it.
- **`By when note`**, optional — prose recording how the deadline was worded to
  the party it was promised to. Never validated.

(These are markdown columns of a file, not keys of this payload. Nothing in the
JSON above changed — that is the point of the row this task added to the
Changelog.)

They replace one `By when` column that held both, which needed one regular
expression to decide whether a sentence named a clock. It failed five V4 review
rounds in four shapes and is deleted rather than fixed again (ADR-007, decision
3). A consumer may now **sort and compare `Due` without parsing it**, and must
not read anything out of `By when note`. A register written before the split is
converted once, by `perry-goals commit --migrate`.

**Writes, in this command.** `list` is read-only, takes no lock, and is not
gated. The tool as a whole is no longer read-only — see `perry-goals --help`
and `goals/reference/phases.md § commit <promise>`.

## Changelog

| Version | Date | Change |
|---|---|---|
| `1.0` | 2026-08-17 | first published. Carried a per-KR `progress` percentage. |
| `2.0` | 2026-08-17 | **breaking**: `progress` removed. Perry cannot tell which direction a KR runs, and half of a real OKR's targets are ceilings; a max-drawdown limit rendered two-thirds achieved is the worst thing a dashboard can say. Live for one day, no consumer had adopted it. |
| `2.0` | 2026-08-18 | **unchanged by TASK-037.** The writer shipped and this payload gained no key. |
| `2.1` | 2026-08-21 | **additive, TASK-120.** Four keys added, none removed or retyped: `krs[].current_provenance`, `krs[].current_staleness`, `krs[].linked_task_completion` and `conformance.krs_with_stale_current`. `current` itself is unchanged in type and in value; what changed is that the payload now says it is an author's assertion rather than a measurement, and says when a linked task has moved since. |
| `2.1` | 2026-08-21 | **unchanged by TASK-131.** The payload sketch now carries `okr.objectives[].id` and the whole of `phase.objectives[]`, and *The phase* gained an `objectives` row. All five paths have shipped since `1.0`; only the page moved, so the version does not. Why the objective entry is a list rather than a key table is stated where it is written. |
| `2.0` | 2026-08-19 | **unchanged by TASK-091.** `OKR.md § Commitments` split `By when` into a typed `Due` and a prose `By when note`, and this payload does not carry that register — so no key here was added, removed or retyped, and `tests/test_contract_invariance.py` is right to see nothing. The columns are documented under *Not here* for consumers that parse the markdown. |

**Why the writer did not move the minor.** `OKR.md § Commitments` now has a
deterministic writer and still has no deterministic *reader* — a consumer that
wants the register parses the markdown, exactly as `modes/pipeline.md § Triage`
step 3 already instructs. Adding a `commitments` array here would have been
additive and useful, and it was declined for two reasons worth writing down:

1. **A writer is not a read-contract change.** These are versioned separately
   from `perry-task/list/*` precisely so a consumer does not re-check its code
   for a change in a domain it does not read (DESIGN-005 § 4, decision 5). The
   same argument applies within this contract: nothing about `krs`,
   `objectives` or `phase` moved.
2. **The same call was already made once, deliberately.** TASK-059 declined to
   add an agents roster to this payload on the grounds that freezing a shape
   into an additive contract ahead of the design that defines it is the
   expensive kind of mistake. A commitments array has the same property: the
   register's consumers are `modes/pipeline.md` and `modes/queue.md`, whose
   triage steps are still agent procedures. When one of them becomes a tool
   with a real read, that tool's needs — not a guess at them — should set the
   shape.

If it is added later it is `2.1`, additive, and this table records it.
