# The linkage store, and why attribution is by ID

Loaded on demand from `okr-linkage.md`, which keeps the attribution rule, its resolution order and the ask. Moved out of it on 2026-09-21 (TASK-470), unchanged: the store's shape matters to its writers (`perry-task add`'s `--kr`, `perry-goals link`) and to the frontend, not to a session resolving one task's KR.

## Why ID, not name

- A KR's ID encodes its phase AND its Objective: `P002-O1-KR2` **is** phase 002's `O1`. Neither edge drifts, and neither is recovered from position (DESIGN-007 decision #4).
- A Project has a stable ID; its human-readable **name is a label that may change**.
- **The link is always the ID. The name is only for humans and is resolved *to* an ID via the graph.** Matching progress reports on names directly is the bug this file exists to kill.

## Why the three buckets are disjoint

From `okr-linkage.md § Resolution order`.

Until TASK-228 the code implemented two states where this page described
three: `unlinked` meant "did not resolve to a KR", which is true of a declared
row too, so every declared id was counted in both buckets. Measured on Perry's
own board after declaring 48 rows — `linked=8, unlinked=48,
declared_unlinked=48`, the two sets byte-identical — and on 2026-08-29 that
number was read off the payload and reported to the user as 52 rows owing an
answer when the true count was 0. `tests/test_attribution_buckets.py` is the
agreement between this paragraph and the payload.

## The linkage graph — `linkage.jsonl`

**Owner: `perry`** — the store belongs to no lane, which is what lets `work`
write an `edge` at `perry-task add`'s `--kr` and `goals` write one at `perry-goals
link` without either touching the other's directory. Within `goals`,
`perry-goals link` is the only writer. **PMO reads it for roll-up + resolution.**

It is **one JSON object per line**, machine-written and machine-read by Perry
*and* by the frontend. Six record kinds, declared field by field in
`$PERRY_HOME/schema/state-schema.json § stores.declared["linkage.jsonl"]`.

**It was `phase/<NNN>-linkage.md` until ADR-019** (2026-09-08). That document's
61 lines of frontmatter duplicated this store record for record — 6 KRs against
6 `kr` records, its `unlinked:` array of 100 ids against 100 `unlinked` records
— and `perry-lint` reported the two disagreeing about one of them on the day the
ADR was written. The document is deleted and the drift class with it.

```jsonl
{"kind": "objective", "phase": "002-release-pipeline", "id": "O1", "title": "Automate the deploy path"}
{"kind": "kr", "phase": "002-release-pipeline", "objective": "O1", "id": "P002-O1-KR1", "title": "Deploy script green in staging", "metric": "3 consecutive green runs", "target": 3, "current": 1, "stretch": false, "asserted_at": "2026-08-14T09:15:00Z"}
{"kind": "edge", "task": "REL-001", "kr": "P002-O1-KR1", "declared_at": "2026-08-14T09:15:00Z", "actor": "goals", "via": "link"}
{"kind": "unlinked", "task": "REL-009", "phase": "002-release-pipeline", "declared_at": "2026-08-14T09:15:00Z", "actor": "goals", "via": "link"}
{"kind": "project", "phase": "002-release-pipeline", "id": "REL-001", "kr": "P002-O1-KR1", "name": "Deploy script hardening", "aliases": ["deploy-hardening"], "declared_at": "2026-08-14T09:15:00Z", "actor": "goals", "via": "link"}
{"kind": "agent", "phase": "002-release-pipeline", "id": "Coding Agent", "task": "REL-001", "declared_at": "2026-08-14T09:15:00Z", "actor": "goals", "via": "link"}
```

**One edge is one record**, which is the whole point: a `tasks: [...]` array
could not carry `via`, and `via` is what says whether the edge was declared in
the same action as the row's `add` or swept in later. **Every phase's records
live in the same file**, each naming its own `phase`, so a scored phase's graph
is still readable — `perry-goals krs --phase 002` prints it — and nothing is
snapshotted or carried forward.

Three rules earn their place, and all three exist to stop a reader from showing a
number nobody wrote down:

1. **`target` / `current` are numbers or absent.** A KR whose target is
   "≤ 15% drawdown" gets no `target` — half of real KRs are *ceilings*, and
   rendering a limit as completion turns a risk budget into a progress bar.
   Omit rather than coerce; the prose stays in `metric`, which is always safe.
2. **`unlinked` is declared, never inferred.** Set arithmetic (every board task
   minus every linked task) would report the whole un-triaged backlog as drift
   on the day the file is first written.
3. **A KR may legitimately carry zero tasks.** That is the single most valuable
   thing the view shows — a commitment nobody is working on — not a parse error.
4. **`asserted_at` is absent unless somebody measured the number.** It says when
   THIS KR's `current` was arrived at, and `""` means nobody wrote that down —
   a different fact from "just now", and the only one of the two that a writer
   which did not measure it can honestly report. TASK-155: the register document
   had one file-level `updated:` stamp read as every KR's assertion date, so
   appending one edge marked every number in the phase freshly asserted.

## Integrity invariants (checked by `bin/perry-lint`)

- A task id may carry at most one `edge` record per phase — two would make its attribution ambiguous.
- Every `project` record must serve a KR under an Objective its phase declares. (The record stores no `objective` of its own: the KR id encodes it, and a second field is a second place for the two to disagree.)
- No two projects may share a `name` or an alias — that is the "duplicate name" trap.
- Every KR id named in the graph should exist in the current phase file's KR set.
- A task whose Project resolves to no entry → `unlinked`, surfaced.
