# `perry-goals list --json` — the goals contract

> Contract: **`perry-goals/list/3.3`**
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
`perry-state` uses. A third reader of `OKR.md` would be a third
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
  "contract":     "perry-goals/list/3.3",
  "installed":    true,                    // false: not a Perry project — schema/README.md § installed
  "semantics":    [ /* below */ ],         // meaning changes, oldest minor first
  "project_root": "/abs/path",
  "state_root":   "/abs/path",
  "conformance":  { /* below */ },
  "okr":          { "present": true, "version": "v3: 2026-01-01", "mission": "…",
                    "operating_principles": [], "anti_goals": [],
                    "objectives": [ {"id": "", "title": "…", "krs": ["KR1"]} ] },
  "phase":        { /* every key in the table below, and: */
                    "objectives": [ {"id": "O1", "title": "…",
                                     "krs": ["P<NNN>-O1-KR1"]} ] },   // or null
  "krs":          [ { /* every key below; the three provenance blocks in full */
      "id": "KR1", "level": "phase", "objective": "…", "title": "…",
      "metric": "…", "qualifier": "", "linked_to": "", "stretch": false,
      "target": 0, "current": 0, "due": "", "task_ids": ["TASK-094"],
      "current_provenance": {
        "state": "asserted", "measured": false, "source": "linkage-store",
        "asserted_at": "2026-08-20T20:32:00Z", "asserted_scope": "kr" },
      "current_staleness": {
        "stale": true, "evaluated": true, "since": "2026-08-20T20:32:00Z",
        "reason": "1 linked task changed state after 2026-08-20T20:32:00Z: …",
        "moved_tasks": [ { "id": "TASK-094", "from": "review", "to": "done",
                           "at": "2026-08-21T09:10:00Z" } ] },
      "linked_task_completion": {
        "total": 2, "done": 1, "dropped": 0, "open": 1, "unknown": 0 }
  } ],
  "answered_by":  "linkage",               // linkage | prose | none
  "unlinked_task_ids": ["REL-009"],        // DECLARED, never inferred
  "linkage":      { "present": true, "phase": "002-…", "error": "" },
  "counts":       { "objectives": 3, "krs": 12, "stretch": 1 }
}
```

### `installed`

`true` when the directory read is an installed Perry project, by the one
criterion in `schema/README.md § installed` — `.perry/config.jsonl` at the
project root, or a `.perry/` directory there and a canonical store under the
state root (a store with no `.perry/` beside it stopped counting in 3.3). On
any other
directory every other key keeps its empty shape and the call exits 0, so
**read `installed` before reading an empty `krs` as "nothing here"**. Added in 3.2.

### `semantics[]` — the entry, key by key

**The minors under which a value already in this payload started meaning
something else**, oldest minor first. Rule 2 says `2.x` only adds keys, that is
true and unbroken, and it is not the whole risk: `2.2` added no key and changed
what three timestamps say. A consumer records the minor it read against and
reports every entry newer than that — a slice, which it is only while the array
is sorted, so this is ordered and nothing is inserted into the middle of it.

It is **not the Changelog**. The Changelog below records every shipped minor,
including the ones that only added keys; this array carries only the strictly
smaller set a working consumer has to act on. `2.1` added four keys and is
therefore absent by design: a consumer sitting on `2.0` has never seen those
keys, and telling it their meaning moved would be a false alarm.

The array is **always present**, `[]` included, for the same reason `contract`
is — a consumer checks before it looks. Same shape as
`perry-task/list § semantics[]`, on purpose.

| Key | Type | Meaning |
|---|---|---|
| `version` | string | the minor the change shipped in, `"2.2"`. A string, not a number: `2.10` sorts below `2.9` numerically and above it correctly. Compare it as a pair of ints, or as the string against a same-shaped string — never as a float |
| `fields` | array | the payload paths whose meaning moved, as strings, in this payload's own dotted notation — `"krs[].current_staleness.since"`. Paths to read against, not keys to look up at the top level |
| `note` | string | prose, always populated: what the value used to mean, what it means now, and what a consumer that hardcoded the old meaning does wrong. Meant to be shown, not branched on |

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
| `target` | number \| null | from the linkage register only. **Never `null` when `current_provenance.measured` is `true`** — see below |
| `current` | number \| null | from the linkage register when `current_provenance.measured` is `false`; recomputed by Perry when it is `true`, and then rounded — see below |
| `due` | string | from the register, else the KR row |
| `task_ids` | array | task ids attributed to this KR by the register |
| `current_provenance` | object | who asserted `current` and when |
| `current_staleness` | object | whether a linked task has moved since |
| `linked_task_completion` | object | how many linked tasks are closed. **Not progress** |

### `current` is an assertion unless it says it was measured, and these three blocks say which

Added in `2.1`. Until then the payload emitted `target` and `current` as bare
numbers, and both of the readings a consumer could take from Perry's own
register on 2026-08-21 were wrong — in opposite directions:

- `P002-O1-KR1` read `0.0 / 1.0`, i.e. nothing done, while all four of its linked
  tasks were closed and the thing it asks for had shipped.
- `P002-O2-KR2` read `0.0 / 0.0`, i.e. **met**, while the task under it had measured
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
| `current_provenance.state` | string | `asserted` when the register gave a number, `unasserted` when it did not, **`measured` when Perry recomputed it on this read** — the third value, undocumented here until `3.1` though the payload has emitted it since DESIGN-015 row F. **An absent `current` is `null` and `unasserted`, never `0`** — that default is what makes a drive-to-zero KR read as met before the work starts. `measured` with `current: null` is a fourth thing again and not a fifth: the metric ran and found no denominator, which is not a number nobody wrote down |
| `current_provenance.measured` | bool | **`true` when Perry re-ran the KR's metric on this read**, `false` when `current` is whatever the register was given. It read *always `false`* here until `3.1`, and had been wrong since DESIGN-015 row F shipped `bin/lib § COMPUTED_KR_METRICS`: a KR named there is recomputed from its sources on every read and publishes `state: "measured"`. Emitted rather than implied, so a consumer showing "measured" has an explicit answer to key on — and so it has something to gate the two rules below on |
| `current_provenance.source` | string | `linkage-store`, or `""` when unasserted |
| `current_provenance.asserted_at` | string | **this KR's own** `asserted_at`, **in UTC, with a `Z`** — when its `current` was arrived at. `""` when the record carries none, which is a real state and not an error: nobody wrote the date down. Unreadable text is `""` too, never a half-interpreted value. It is NOT defaulted to the time of any write |
| `current_provenance.asserted_scope` | string | `kr` when a date was recorded, `""` when none was. It read `register` until `2.4`, because the date was the register document's one file-level `updated:` stamp and belonged to the whole file; that document is gone (ADR-019) and the field is per KR |
| `current_staleness.stale` | bool | a linked task changed state after `asserted_at` |
| `current_staleness.evaluated` | bool | whether staleness could be decided at all. `false` with `stale: false` means *nobody asked*, not *nothing moved* — a KR with no `asserted_at`, or a project with no event log, cannot answer |
| `current_staleness.since` | string | the timestamp compared against, in UTC with a `Z`, or `""` |
| `current_staleness.reason` | string | prose, always populated, in both directions |
| `current_staleness.moved_tasks` | array | the tasks that moved, each `{id, from, to, at}`. `at` is the event's timestamp **in UTC, with a `Z`** — not the text the log holds, which is local. `from` is `""` for a task created after the assertion |
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

#### A measured `current` always has a `target` beside it

**`3.1`. If `current_provenance.measured` is `true`, `target` is not `null`.**
It is a rule about the register rather than about this tool — nothing here
invents a target — so it is enforced where it can be, by
`tests/test_measured_krs_declare_a_target.py` over this payload, and a project
whose register breaks it reddens rather than publishing the pair.

The rule exists because the pair is what a consumer draws from, and the row it
was written for is the one that had the most to draw. `perry-goals/list/2.0`
removed `progress` on the ground that only the project knows which direction a
KR runs, so a consumer draws a bar only when `target` and `current` are both
numbers — and the strictest thing a consumer can do with that rule is show
NOTHING for a KR that fails it. Perry's own `P003-O3-KR2` failed it: a KR
recomputed from two event logs on every read, publishing `current` beside
`target: null`, so the single most rigorously measured row in the register was
also the only row that rendered as *nobody wrote down what done would mean*.
Its target had been written — as the first three words of `metric`, "Target
100%." — and **prose is the one place a consumer may not read a number from**,
which is the whole of rule 1 in `schema/README.md § Three of its rules are
load-bearing`.

An `asserted` or `unasserted` `current` is untouched by this: a register that
gave a number and no target is a register a human wrote that way, and a KR
whose target is genuinely prose ("≤ 15% drawdown") carries no `target` by
design. The rule binds only where Perry itself produced the number, because
that is the only case where nobody can say the omission was authored.

#### A measured `current` is rounded, and the ends mean something

**`3.1`. A measured `current` is published to ONE DECIMAL PLACE, and `0.0`
and `100.0` are reserved for the exact cases.** `bin/lib § measured_percent`
is the one implementation; `MEASURED_PERCENT_PLACES` beside it is the one
place the digit is written; and
`tests/test_measured_krs_declare_a_target.py § TheMeasuredPercentIsPublishedToOneDecimal`
holds both halves of the rule, including the reserved ends and the fact that
the live payload goes through the helper rather than dividing for itself.

Before `3.1` the raw quotient went out: `13 / 38` published as
`34.21052631578947`, seventeen significant figures of a ratio of two small
integers, sixteen of them an artefact of binary floating point rather than
anything measured. Nothing about the measurement justified any of them, and
every consumer rounded them differently or not at all, so one measurement
rendered as several different numbers and none of them was Perry's answer.

**The reserved ends are not a direction.** `2.0` removed `progress` because
Perry cannot tell which way a KR runs, and this must not smuggle that back
in — there is no *good* end here to round away from. What Perry can tell is
EXACTNESS. `1999 / 2000` is `99.95`, which one decimal place rounds to
`100.0`: a claim that every row was answered, about a phase with a row that
was not. `0` and `100` are the two values a consumer may read as a whole fact,
so they are the two values this only ever returns from a whole fact —
`numerator == 0` and `numerator == denominator`. A ratio strictly between the
ends is published at the nearest value that is not an end, `0.1` or `99.9`.
That is still a rounding, and it is the only one of the four that cannot be
read as a completeness claim Perry did not measure.

**Nothing is lost, and the exact question has an exact answer.**
`krs[].current_measurement.numerator` and `.denominator` are published beside
it, unrounded and as integers. A consumer that wants the full ratio divides
them. A consumer that wants to know whether the KR is **met** compares them —
which is the comparison it should have been making anyway, and the one the
reserved ends exist to stop it getting wrong through `current`.

An **asserted** `current` is not rounded and never was. It is the number the
register was given, and rounding a number a human typed would be this
contract editing its own source.

**Every timestamp in these three blocks is UTC and says so** (`2.2`,
TASK-144). They are compared on one clock, and the rule each shape is read by
is stated once, in `bin/lib § ts_moment`, which is the only place in the tree
that decides what a timestamp means:

| Written as | Read as |
|---|---|
| `2026-08-21T10:04:08Z`, `2026-08-28T02:15:22+08:00` | itself, converted to UTC. Both writers emit a zone: the register stamps UTC, the event log stamps local wall clock **with its offset** |
| `2026-08-28T02:15:22` — no zone | **the reading machine's local time.** `.perry/events.jsonl` is append-only and holds hundreds of these; `datetime.now()` wrote them, so local wall clock is what they hold. They are not rewritten — that is a migration and a separate decision — and the cost is stated rather than hidden: a log carried to another zone reads its older lines by the new machine's offset |
| `2026-08-21` — a date | UTC midnight. A date carries no wall clock to be local about, and the register is the only surface that writes one |
| anything else | `""`, and staleness reports that it could not be evaluated. Never a half-interpreted value, which would sort against real ones |

Until `2.2` the two were compared **as text** with the `Z` stripped, so a task
that moved inside the machine's offset of the assertion was reported on the
wrong side of it — `stale: true` for a move that predated the number on a
positive offset, and `stale: false` for a real one on a negative offset. A
date-only `updated` still errs toward reporting staleness on purpose: a false
*recheck this* costs a look, a false *this number is fine* costs the number.

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
| `2.2` | 2026-08-28 | **no key added, one value's meaning changed, TASK-144.** `current_provenance.asserted_at`, `current_staleness.since` and `moved_tasks[].at` are now UTC and carry a `Z`; `at` in particular is no longer the local text the event log holds. Before this the register's UTC and the log's local wall clock were compared as text, and staleness answered wrongly inside the machine's offset in one direction or the other. The minor moves for the same reason `perry-task/events/1.1` moved: no key changed and the same key returns something different. |
| `3.0` | 2026-09-08 | **breaking: `linkage.updated` removed, and three values' meaning changed. TASK-155 / ADR-019.** The key was the deleted `phase/<NNN>-linkage.md`'s one file-level `updated:` stamp; there is no file left for it to be the stamp of, and keeping it at `""` would be a value a consumer reads as *never updated* when the truth is *that is not a thing any more* — the same mistake `progress` was at `2.0`. And, under three keys that did not move: `current_provenance.source` reads `linkage-store` where it read `linkage-register`; `.asserted_scope` reads `kr` (or `""`) where it read `register`; `.asserted_at` is the KR record's own `asserted_at` field rather than `phase/<NNN>-linkage.md`'s file-level `updated:` stamp, which that ADR deleted along with the document. **The consequence a consumer must handle:** an *asserted* `current` can now carry `asserted_at: ""` and `asserted_scope: ""` — nobody recorded when the number was arrived at — and `current_staleness.evaluated` is then `false`. Before this the date was never empty on an asserted number, because it belonged to the file rather than to the number: that is the defect, and it meant appending one edge to one KR re-dated every asserted `current` in the phase. The value changes alone would have been a minor, on `2.2`'s reading; the REMOVAL is what makes it a major, and rule 2 — `2.x` only adds keys — is why it cannot be anything else. |
| `2.3` | 2026-08-28 | **additive, TASK-205.** One key added, none removed or retyped: top-level `semantics`, the array documented above. A consumer could read this payload's minor and had nowhere to find out what a minor had changed, so `CONTRACT_TESTED` against `2.2` could never go red — the same gap `perry-task/list` closed at `1.7` and `perry-events/list` at `1.1`. Adding the key changed no value, so the array itself carries no `2.3` entry; it carries `2.2`. |
| `2.0` | 2026-08-19 | **unchanged by TASK-091.** `OKR.md § Commitments` split `By when` into a typed `Due` and a prose `By when note`, and this payload does not carry that register — so no key here was added, removed or retyped, and `tests/test_contract_invariance.py` is right to see nothing. The columns are documented under *Not here* for consumers that parse the markdown. |
| `3.1` | 2026-09-10 | **no key added, one value's meaning changed, and one invariant written down. TASK-415.** A **measured** `current` — one whose `current_provenance.measured` is `true` — is now rounded to one decimal place, with `0.0` and `100.0` reserved for the exact cases; `P003-O3-KR2` reads `34.2` where it read `34.21052631578947`. Same key, different number, which is exactly what moved `2.2`, and rule 2 is untouched: nothing removed, nothing retyped. The invariant is that a KR with `measured: true` carries a non-null `target`, held by `tests/test_measured_krs_declare_a_target.py`; it adds no key either, and is recorded here because a consumer cannot rely on a guarantee nobody stated. The page also stopped saying `current_provenance.measured` is *always false* and `current_provenance.state` is only `asserted` or `unasserted` — both had been wrong since DESIGN-015 row F shipped `COMPUTED_KR_METRICS`, and correcting a page to match a payload that already shipped is not itself a version move (the `2.1`/TASK-131 precedent). |
| `3.2` | 2026-09-14 | **additive, TASK-237 3b′.** One key added, none removed or retyped: top-level `installed`, `true` exactly when `schema/README.md § installed` holds. On a directory that is not a Perry project this payload answered its empty shape at exit 0 — `okr.present` false, `krs` empty, `phase` null — which a consumer could not tell from a project with nothing in it. `semantics` carries a `3.2` entry for it, at the user's decision (Amendment (4) item 1), although a key addition is normally a changelog row only. |
| `3.3` | 2026-09-14 | **no key added, one value's meaning changed, TASK-237 3c.** `installed` is narrower (Amendment (7), the user's decision): at `3.2` a canonical store under the state root counted on its own, so a folder holding only another tool's `tasks.jsonl` read `installed: true`. From `3.3` a store counts only with a `.perry/` directory at the project root beside it (`schema/README.md § installed`); such a directory now answers `installed: false` with the empty shape at exit 0. `semantics` carries a `3.3` entry. A narrowed meaning is not a removal or a retype, so this is a minor. |

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
