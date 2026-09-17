# `okr link` — owning `linkage.jsonl`

Loaded when `/okr link` fires, or whenever PMO hands over an attribution result.

The linkage graph is machine-written and machine-read on both sides: Perry
resolves KR attribution through it, and the frontend draws the project's
O→KR→task chain from it. In the `goals` lane `okr` is its **only writer** — PMO
reads it and hands changes over. (`bin/perry-task add`'s `--kr` writes an `edge` in
the same action as the row it opens, which is the one write this lane does not
make; the store is `owner: perry` for exactly that reason.)

**`bin/perry-goals link` is the write.** Every command on this page is that tool
with the arguments shown; nothing here is edited by hand. It **appends** a
record; the one exception is the retraction below, which removes an `unlinked`
record superseded by an edge. Every refusal is enforced by the tool, and a
refusal means **nothing was written**.

**It was `phase/<NNN>-linkage.md` until ADR-019** — YAML frontmatter spliced in
place, one line at a time, by ~530 lines of line-locating machinery that existed
because the target was markdown somebody might have reformatted. The store is
JSONL: one record is one line, appending is appending, and there is no second
copy for the write to disagree with.

Shape and field list: `schema/state-schema.json § stores.declared["linkage.jsonl"]`.
Attribution rules: `$PERRY_HOME/reference/okr-linkage.md`.

## The four moments it changes

| When | What |
|---|---|
| `plan-phase` | The phase's `objective` and `kr` records, and one `project` record per Project. No edges yet. See `phases.md`. |
| `plan-week` | One `edge` record per approved task. See `weekly.md` step 7. |
| **PMO hand-off** (`add-task`, `coordinate`, `digest`) | PMO resolved — or failed to resolve — a task's KR and hands the result here. This file. |
| `score-phase` | Nothing moves. Every record names its phase and stays where it is; the next phase appends its own. See `phases.md`. |

**There is no file-level stamp to bump, and that is TASK-155.** The register
document carried one `updated:` field, and three readers took it for three
different facts: when the graph last changed, when a KR's `current` was
asserted, and when each of 115 imported records was declared. So appending one
edge re-dated every asserted number in the phase — a `current` that reported
STALE because a linked task had moved read fresh afterwards, with nothing about
the number changed. The tool named the affected KR ids on stderr and wrote them
anyway.

Each of the three is its own per-record field now:

| Field | On | Written by | Means |
|---|---|---|---|
| `declared_at` | `edge`, `unlinked`, `project`, `agent` | the write that appends the record | when this declaration was made |
| `asserted_at` | `kr` | whatever writes `current`, and nothing else | when THIS number was arrived at |

`asserted_at` is optional and **absent is a real answer**: it means nobody
recorded when. It is never filled from the clock by a command that did not
measure the number — that is TASK-155 with a different spelling, and every
`current` would read as measured this second. A day-only value is dropped, not
guessed at.

## `link` — accepting PMO's hand-off

PMO's attribution gate (`work/reference/subcommands.md § add-task`) ends in one of
three outcomes, and each maps to one edit here. PMO prints the outcome; `okr`
performs the write.

### 1. Resolved → append the edge

```
"$PERRY_HOME/bin/perry-goals" link --actor goals --root . <TASK-ID> <KR-ID>
```

Appends one `edge` record. `<KR-ID>` may also be an **exact**
Project id or an **exact** registered alias, resolved in that order — the same
order `bin/perry-state § resolve_kr` reads with, and with the same fourth step,
which is to refuse. Anything matching two Projects, or none, is refused with its
candidates named; nothing is ever matched by resemblance. Refuses if:
- the KR id is not in this phase's graph → say so, list the phase's KR ids;
- the task already appears under a **different** KR → refuse and surface both.
  A task under two KRs makes its attribution ambiguous, and `bin/perry-lint`
  rejects it. Move it, don't duplicate it.

If the task currently carries an `unlinked` record, that record is retracted in
the same write — otherwise it renders as both attributed and drifting. This is
the only place this tool removes a record rather than appending one.

### 2. A name was confirmed as an existing Project → append the alias

```
"$PERRY_HOME/bin/perry-goals" link --actor goals --root . --alias <PROJECT-ID> "<the other name>"
```

Appends a second `project` record for that id, carrying the full alias list;
the readers take the file in order and the later record wins. This is what makes
name drift survivable:
a later progress report arriving under the old name resolves to the same KR
instead of failing. Refuse if another project already claims that name or alias
— that ambiguity is exactly what the registry exists to prevent, and the linter
rejects it.

**Only on the user's confirmation.** Never merge two names because they look
alike; that is the fuzzy match the whole gate forbids.

### 3. Unresolved → declare it unlinked

```
"$PERRY_HOME/bin/perry-goals" link --actor goals --root . --unlinked <TASK-ID>
```

Appends one `unlinked` record, carrying the phase it was declared against —
the store holds every phase at once, so a declaration with no phase would count
against all of them. This is a **declaration**, not an inference: never
populate the list by subtracting linked tasks from `BOARD.md`, which would report
the entire un-triaged backlog as drift the day the graph is written. Refused if
the task already carries an edge — it would render as attributed and drifting at
once.

An unlinked task is a User-Input-Queue item. Surface it at the next snapshot so
the user can attribute it; do not quietly attach it to the nearest-sounding KR to
make a number look complete.

### 4. A new Project appeared mid-phase

```
"$PERRY_HOME/bin/perry-goals" link --actor goals --root . --project <PROJECT-ID> <KR-ID> "<name>"
```

Appends one `project` record. `objective` is DERIVED from the KR id
(`P<NNN>-O1-KR2` → `O1`) and stored nowhere — the id already encodes it, and a
second field is a second place for the two to disagree. The tool checks that
derivation against the objective the KR is filed under and refuses when they
disagree rather than picking one. `status` is `active` when absent; append a
record with `done` / `dropped` as the Project resolves — the entry stays,
because a retired Project's name must keep resolving for historical progress
reports, and `resolve_target` names it rather than using it.

## After any write

```
"$PERRY_HOME/bin/perry-lint" --root .
```

It validates every record against its declared shape, so a pass means Perry
can read it. It also checks: no task under two KRs, no two projects sharing a
name or alias, every project serving a KR under an objective its phase declares,
every KR id naming the phase its records are filed under, and every KR id
agreeing with the objective it is declared under.

The last two used to be one check — *every KR id present in the phase file* —
which read the KR table the phase document carried. TASK-157 removed that
table, so the questions are asked of the id directly, which needs no second
file and is strictly stronger: a `P002-…` KR filed under phase 003 used to be
caught only because `003-storage-code.md` happened not to mention it.

**It does not report drift, and it never will again.** The store projected from
`phase/<NNN>-linkage.md` and `linkage-store-drift` compared the two; ADR-019
deleted the document, so the class is impossible rather than checked. The census
line reports how many records there are and how many match a declared shape.

## What `okr` must not do here

The first of these is the one the writer enforces by never writing either field;
the other three are yours, because no tool can tell an invented task from a real
one.

- **Not invent a number.** `target` / `current` are numbers or absent. `current`
  is an author's assertion, so it is **absent until asserted** — never `0`. Most
  KRs here drive a count down, so a defaulted zero reads as met on day one; that
  default was in the register template until TASK-119 removed it. A KR whose
  target is prose ("最大回撤 ≤15%", "vs 1pp 线") gets a `metric` string and no
  `target`. Half of real KRs are ceilings; a ceiling drawn as a progress bar
  reports a risk budget as two-thirds achieved. **And not invent a DATE**: write
  `asserted_at` only with the day the number was measured, never with today's
  clock because the record needed a value.
- **Not fill an empty KR.** A KR with zero tasks is the most valuable thing the
  chain shows — a commitment nobody is working on. Do not invent a task for it.
- **Not drop a done task.** Completed work keeps its `edge` record; that is what
  an achieved KR looks like.
- **Not hand-edit the store.** Every refusal on this page is enforced by the
  tool and by nothing else, so a record typed in by hand is a record no rule
  was applied to. `perry-lint` catches a shape it can name; it cannot catch an
  attribution somebody guessed.

## Completion routing

After completed writes from `link`, follow [the shared closing step](../../reference/next.md#closing-step); its skip rules apply.
<!-- next-close: goals link -->
