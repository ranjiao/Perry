# Instruction for aiMark's coding agent — catch up with Perry, 2026-08-18

> **Revision 3.** Written after reading `doc/perry-contract-gaps-2.md`.
> **All four of your round-2 asks are answered and shipped**; the contract is
> now `perry-task/list/1.7`. Section 0 below is new and is the part to read
> first. Revision 2's body is kept underneath, corrected where 1.7 moved it —
> nothing was softened.
>
> One of your asks was **not** implemented in the shape you proposed, and § 0.2
> says why. You were right about the problem and the proposed default would
> have been false.

You are working in `~/proj/aimark`. Perry is installed at `~/.claude/skills/perry/`
(hereafter `$PERRY`). This instruction is self-contained.

You already migrated aiMark off markdown parsing and onto Perry's three read
contracts, and you wrote `doc/perry-contract-gaps.md`. **That report was read and
acted on.** This tells you what changed, what did not, and what to do next.

Everything below was measured on 2026-08-18 against the installed Perry. Where a
number is stated, reproduce it before relying on it.

---

## 0 · Your round-2 report — all four, shipped

Read `$PERRY/schema/task-list-contract.md § Changelog § 1.7` for the contract's
own account. This is the short version and the one place we disagreed.

### 0.1 · The minor that hides a meaning change — `semantics`, new top-level key

You were right and the fault was ours: **§ The three rules, rule 3, taught the
opposite of what a minor means.** Its snippet took the major and discarded the
rest, so a consumer following the contract's own safety instruction exactly
could not see 1.5 — the one version that existed *because* two fields changed
meaning.

Shipped as the first of your two options, because the second is not enough on
its own:

```json
"semantics": [
  {"version": "1.5",
   "fields": ["evidence_paths", "conformance.evidence_not_found"],
   "note": "Evidence spans are now resolved for CLOSED rows too, and every span that resolves nowhere is reported. …"},
  {"version": "1.7",
   "fields": ["timeline[].from", "timeline[].to"],
   "note": "These were a status transition on every event until `prioritize` shipped, where they are board sections. …"}
]
```

**It is a list, not the current version's entry**, because a front-end jumping
1.4 → 1.7 must still learn about 1.5. Compare each `version` against your
`CONTRACT_TESTED` and surface every entry above it. Rule 3 now shows exactly
that, and says **do not refuse on a minor** — your instinct there was right.

An empty list is the normal case and means what it says: keys were added, no
meaning moved.

### 0.2 · `timeline[].field` — shipped, and not in the shape you asked for

You asked for `"status"` on every existing event and `"section"` on
`prioritize`. **That default is false**, so we did not ship it: `retitle`'s
`from`/`to` are titles, `next`'s are next-action prose, `rung`'s are rungs. A
wrong word in the field whose entire job is to stop you guessing would be the
same defect living inside its own fix.

It is a full map over all thirteen task events:

| `field` | on |
|---|---|
| `status` | `add` `route` `start` `status` `done` `drop` |
| `section` | `prioritize` — `P2` → `P1`, or a project's own heading |
| `stage` | `stage` |
| `title` | `retitle` |
| `next_action` | `next` |
| `verification` | `rung` |
| `evidence` | `evidence` |
| `depends_on` | `depends` |

Always present. **Delete `SECTION_MOVE_EVENTS` and read `field`** — your set of
special cases goes to zero, and it stays zero when we add an event.

A test asserts this map's keys equal the writer's own event set, so an event
cannot ship without declaring what its pair means. It earned that immediately:
`depends` — added hours earlier by the 1.6 work — was already missing, and the
guard found it, not a human.

### 0.3 · The event enum listed 7 of 13 — fixed

`prioritize`, `retitle`, `next`, `rung`, `evidence` and `depends` were all
shipping and none was named in `§ A timeline entry`. Exactly as you said: a
front-end building its event handling from the spec met them first at runtime.

### 0.4 · `add --rung` missing from the usage — fixed

And the usage now says the thing that trips people: **`--rung` fills the
`Verification` column; `--verification` is the spec's prose and does not.**
That is how one of our own rows shipped with an empty rung.

### 0.5 · Your round-1 leftover is closed by measurement, not by work

You checked `asks` / `risks` / `drift` at 1.5 and correctly found them absent.
**They landed in 1.6 the same day.** Your `parseStateExtras` swap point in
`src/perry-cli.ts` is ready to delete — the payload carries all three, the
severity a human wrote is preserved, and `idle` is an integer.

## 1 · Your six findings, and where each one stands

### 1.1 · `evidence_paths` empty on every closed row — **fixed**

Resolution moved out of the board walk into a pass over **every** row after the
event merge. A closed row has no cells left to read, so its `evidence` comes off
the `done` event; resolving after the merge is what makes both agree.

Verified by a full lifecycle run on a fresh project — create → start → review →
prioritize → done — after which `grep -c TASK-001 BOARD.md` is `0` and the same
call returns:

```json
{ "evidence": "evidence/2026-08/probe.md",
  "evidence_paths": ["perry/evidence/2026-08/probe.md"],
  "open": false }
```

On Perry's own board this took 32 closed rows from **0 → 29** resolved, with 13
spans correctly reported in `conformance.evidence_not_found` (they are symbols
and prose, not paths).

**The contract minor moved 1.4 → 1.5 for this.** No key was added, removed or
retyped — but two fields changed meaning under a live consumer, and the version
handle is the only way you find that out. `schema/task-list-contract.md §
Changelog` says what a consumer sees.

### 1.2 · asks / risks / drift have no contract — **landed, at 1.6**

`perry-task/list/1.7`. Top level now carries `risks`, `asks` and `drift`
alongside `tasks`, so the *needs-you* list and board drift are no longer behind
the unversioned tool. Both shape defects you reported are fixed, not carried
across: the severity a human wrote is the `severity`, the list marker is gone
from the `title`, the severity letter is no longer the `id`, and `idle` is an
integer number of days.

**You get a dependency graph you did not ask for and will want.** Per task:
`depends_on` (the declared edge, verbatim), `blocked_by` (the unfinished half),
`blocks` (reverse edge), and **`startable`** — a boolean that is true when the
row is open, its status is not `blocked` or `review`, and nothing it waits on is
unfinished. That is "what can actually be picked up right now", computed before
`--track` and `--all` filtering so the graph does not change per query. On
Perry's own board today: 32 open, **18 startable**.

New `conformance` keys to read before rendering: `depends_on_unknown`,
`dependency_cycles`, `blocked_without_dependency`. The last one is the honest
signal that a row says `blocked` and never says on what — Perry's own board has
four.

### 1.3 · No agents edge anywhere — **the data exists, in the wrong place**

This is the finding whose answer is the most useful to you and the least
satisfying.

`phase/<NNN>-linkage.md` **does** carry `agents: [{id, tasks}]`, in exactly the
shape you had. Perry's own register was rebuilt on 2026-08-18 and now reports:

```
linkage.agents = [ {id: "Coding Agent", tasks: [15 ids]},
                   {id: "User + Agent", tasks: [1 id]} ]
```

**But `perry-goals/list/2.0` does not carry it.** Confirmed: its `linkage` key
holds only `{present, phase, updated, error}`. The roster is reachable **only**
through `perry-state --json → linkage.agents` — which is the unversioned tool,
i.e. your finding 1.2 again, wearing different clothes.

So: **keep `DeclaredAgent` in `src/perry-agents.ts` and keep it unused.** Do not
wire it to `perry-state`. The roster's real shape is being settled by
`DESIGN-006` (role cards), where a roster is a *view over roles* rather than a
registry of its own — shipping the view before the object would freeze the wrong
shape, which is why TASK-059 was rescoped there rather than patched into the
goals contract. Your `source: owner` fallback is the right thing to keep
displaying until that lands.

### 1.4 · `mint_id` does not adopt the board's own prefix — **fixed, with a rule you should know**

Both halves: `--prefix` wins outright, and absent it the board's own prefix is
adopted **only when the board carries exactly one family**.

The reason for "exactly one" matters to you, because it is why your board keeps
its own family and another project would not. `~/proj/gimegime-pmo` carries **36**
distinct id families, and they are not stylistic — `IPS-*`/`ALLOC-*` mean one
workstream, `TECH-*`/`DATA-*` another, filed in separate sections deliberately.
A plurality winner there would mint an id claiming a workstream nobody assigned,
and **an id is permanent and never reissued**, so the claim could not be
withdrawn. A foreign-looking `TASK-001` claims nothing.

Guarded refusals you may hit: reserved families (`USER`, `RX`, `CAD`), and a
whole id passed where a prefix belongs — pass `--prefix AIM`, never a complete
id. (A family with no numbered member is left alone rather than numbered:
inventing a first number for it would be Perry choosing a scheme the project
never did.)

### 1.5 · The five small things — **partly done, and one you found for us**

- **stderr is not the failure channel** — still true. Your `--json`-on-writes
  workaround is correct and should stay: it silences the advisory line and puts
  the verdict in the payload. Writing it into the contract docs is TASK-061 and
  is still open.
- **`event_written`** — being documented. Your reading of it is right: it is the
  difference between "the row moved" and "the row moved and its timeline will
  have a hole".
- **Two events can share a timestamp** — still true and now deliberate. Timeline
  order is array order. Do not sort by `ts`.
- **`rows_with_no_computable_age` fires on every row when there is no event
  log** — being addressed; your decision to show the `has_event_log: false`
  strip instead of 17 ids was the right call and is the behaviour being adopted.

### 1.6 · What the old instruction got wrong — **acknowledged**

You were right that the `perry-goals` state-root bug was already fixed, and
right to delete `src/perry-adapter.ts` rather than wait.

---

## 2 · What is new since your report, that you did not ask for

### `perry-task prioritize` — a task's priority can now be changed

There was no writer for it. `add` set it once; `route` takes an *intake row
number* and mints a *new* id. So the one thing triage means — re-prioritising —
could only be done by hand-editing the board, which lands with no event and
shows up as unrecorded drift.

```
perry-task prioritize <ID> --priority P0|P1|P2 [--reason "…"]
perry-task prioritize <ID> --group "<heading>"      # boards with no P0/P1/P2
```

**What this changes for you:** `priority` is now a field a user can act on from
your UI, and the move appears in `timeline` as
`{event: "prioritize", from: "P1", to: "P0"}`.

**Read that carefully — `from`/`to` are the SECTION here, not the status.**
Every other event uses them for status. `event: "prioritize"` is what
disambiguates, and it is the only thing that does. If your timeline renderer
maps `from`/`to` onto a status badge, it will render a priority move as a status
change.

### `add --verification` now refuses a bare rung

`--verification` is the falsifiable **check**; `--rung` is the rung and the cell
the board shows. `--verification V4` used to be accepted silently and filed
`"V4"` as though it were a check. It is now refused, naming `--rung`. If you
expose task creation, send them as two fields.

---

## 3 · Three things that will still give you a wrong answer

1. **`--all` is not optional.** Without it the payload reports `closed: 0`,
   because `BOARD.md` holds open work only.
2. **`created` is absent for tasks that predate the event log.**
   `conformance.has_event_log: false` says so; fall back to the row's date
   cells. On your own board that is every row.
3. **`mode` is derived** from the row's `track` plus the project's track
   register, not read back from the log.

And the general rule, unchanged and the most important one: **read
`conformance` before rendering anything.** It is the payload's account of what
it could not classify.

---

## 4 · What to do

1. **Re-read the three contract specs** — `$PERRY/schema/task-list-contract.md`,
   `goals-list-contract.md`, `decide-list-contract.md` — and check the version
   each reports at runtime against what your code expects. Fail loudly on a
   mismatch rather than parsing optimistically.
2. **Handle `evidence_paths` on closed rows** — delete the struck-through "Perry
   resolved it to no file that exists" fallback for that case; it now resolves.
3. **Do not render a `prioritize` event as a status change.**
4. **Leave the agents roster alone** — `DeclaredAgent` stays unused.
5. **Report back the same way you did last time.** That report is the single
   most useful document Perry has received; the four sections above marked
   *fixed* exist because of it. Concretely: a field you needed and did not find,
   a field whose meaning was ambiguous, a shape you had to work around.

## 5 · One decision made after revision 1 that changes what you will read later

`ADR-006` (`perry/decisions/ADR-006-task-store-is-not-the-log.md`, user-decided
today) splits the task store from the event log. Today the log is canonical for
closed rows; it will not be. Three layers: `perry/tasks.jsonl` as truth,
`BOARD.md` as the rendered open subset, `.perry/events.jsonl` as history that is
genuinely disposable again.

**This does not change `perry-task/list`'s shape** — where a value is read from
is not a contract fact — so you have nothing to do about it. It is here because
two things you rely on get *better* and you should not build workarounds for
them: full-set reads stop being O(events), and `conformance.has_event_log:
false` stops meaning "your closed tasks are invisible".

The measurement behind it, if you want it: deleting the log today takes the
payload from 39 open + **35 closed** to 39 + **0**, while the design document
declared the log "derived and disposable … what is lost is history resolution
and drift detection, not truth". That claim was false, and the split makes it
true rather than editing it.

Do not modify anything under `$PERRY`. If a change is needed there, describe it
and stop.
