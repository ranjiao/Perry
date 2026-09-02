# DESIGN-015: The linkage register is a store, and the edge is made at `add`

> Status: locked
> Date: 2026-09-02 · Locked: 2026-09-02
> Author: PMO Agent   · Implementation owner: Coding Agent
> Linked OKR: P003-O3-KR2 (this design is what makes that KR reachable)
> Supersedes: —   · Superseded by: —

## 1. Problem

`P003-O3-KR2` requires that a row opened during phase 003 "take a KR edge or an
`unlinked` declaration **in the same action as `add`**". Its baseline is 0 and it
cannot move, because the code path does not exist.

**Measured 2026-09-02 on `d49964e`:**

- `perry-task add` accepts `--kr KR-ID`. Its entire effect is one line of journal
  prose at `bin/perry-task:3352` — `f"- **KR linkage**: {args.kr or 'unlinked'}"`.
  The `add` event dict immediately below it carries `title`, `track`, `mode`,
  `priority`, `actor`, `summary`, `depends_on`, `from`, `to` — and **no `kr`
  field**. Nothing on that path writes an edge or an event that records one.
- The register that holds edges is `phase/003-linkage.md`. In
  `schema/state-schema.json § claims[]`, `phase/` has `owner: goals`.
  `perry-task` is the `work` lane's writer, and `SKILL.md § The hand-off
  contract` forbids a lane writing outside its own files. **So `add` cannot
  create the edge — not as an oversight, but structurally.**
- The only writer is `perry-goals link <TASK-ID> <KR-ID>`, run separately and
  in batches.

**The consequence is visible in today's numbers.** Of 62 open rows opened since
phase 003 began (2026-08-28): 2 are linked, 44 are declared `unlinked`, and
**16 have never been asked** (`TASK-253`–`259`, `TASK-267`–`275`, oldest 3 days).
The 44 declarations were not made at `add`; they were swept in later. So by the
KR's own criterion the count is 0 out of 62, and the 16 are what leaks between
sweeps.

This is not a new diagnosis. **`DESIGN-013 § 8`, open question 2, already
recorded it and deliberately left it unanswered:**

> `phase/00N-linkage.md` is YAML frontmatter with no table and 27-46% prose,
> machine-written and machine-read. Under § 5.1's rule it is a store with the
> wrong extension. TASK-157 touches it; whether it should be renamed is not
> asked there.

`DESIGN-013 § 5.1`'s rule is locked: *"A fact that has a schema lives in exactly
one store. A document holds what has no schema. No field lives in both."*
`phase/003-linkage.md` declares its own schema version (`linkage: 1`), holds
`objectives → krs → tasks[]` with typed `target` / `current` / `stretch` fields,
and is not one of the six stores. Measured today it is 7,820 B, of which 3,370 B
(43%, 7 `metric:` fields, longest 976 B) is prose inside those records — so it
violates § 5.1 in **both** directions at once, the same pair the design names.

The user's own account of the cost, 2026-09-02: doing ordinary work requires
switching between the goals and work lanes to keep attribution current.

## 2. Goals

1. `perry-task add --kr <KR-ID>` writes a durable edge in the same action that
   creates the row, and `add` with neither `--kr` nor an explicit unlinked
   declaration is refused or recorded as never-asked — never silently skipped.
2. `perry-state --section attribution` reports a row opened through that path as
   `linked` or `declared_unlinked` immediately after the `add` returns, with no
   second command run.
3. No lane writes a file owned by another lane. The hand-off contract is
   unchanged and needs no second signature.
4. `perry-lint --root .` prints a record count and a drift verdict for
   `linkage.jsonl` as it does for the other five stores, and
   `phase/<NNN>-linkage.md` contains no field declared in
   `schema/state-schema.json`. Both halves of `DESIGN-013 § 5.1` are then
   checkable by command rather than by reading.
5. `P003-O3-KR2` becomes measurable — the metric can be computed from the store
   and the event log rather than asserted.

## 3. Non-Goals

- **Not backfilling the 16 never-asked rows, or the 75 declared ones.**
  `P003-O3-KR1` covered the backfill and was withdrawn 2026-08-31 to phase 004.
  This design governs how a row is opened from here on.
- **Not changing what a KR is, how phases are scored, or the shape of
  `okr.jsonl`.** Only where task→KR edges live and when they are written.
- **Not guessing an attribution.** `reference/okr-linkage.md`'s rule stands: a KR
  is resolved by stable ID or asked. Making the question cheap is the point;
  answering it automatically is not.
- **Not solving the general prose-in-store problem.** `DESIGN-013 § 8` question 1
  (`tasks.jsonl`'s `Next action`) is the same shape and stays open. This design
  handles the `metric:` field only because it must move something.
- **Not rewriting `perry-goals link`.** It stays the goals-lane path for
  declaring an edge after the fact.

## 4. User Decisions

ALL rows must be resolved before this doc can move to `Status: locked`.

| # | Decision | Options | Chosen | Date |
|---|---|---|---|---|
| 1 | Where the linkage register lives | Seventh store, owner `perry` (Recommended) / Store under `phase/`, owner `goals` / Proposal event, goals discharges | **Seventh store, owner `perry`** | 2026-09-02 |
| 2 | Where the 43% `metric:` prose goes | Stays in `phase/<NNN>-linkage.md` as a document / Its own document / Stays in the store | **Stays in `phase/<NNN>-linkage.md`** | 2026-09-02 |
| 3 | What `add` does with no `--kr` | Refuse the add / Record never-asked, warn (Recommended) / Silently allow | **Record never-asked, warn** | 2026-09-02 |

**Decision 2 was asked with an ambiguous option and is recorded on the reading
that is executable.** The option read "stays in `phase/<NNN>-<slug>.md`", and
`phase/` holds two file classes that `schema/state-schema.json` separates
explicitly: the phase document `phase/[0-9][0-9][0-9]-*.md` is **tier 1, hard cap
300**, and carries `exclude: phase/*-linkage.md`; the linkage file
`phase/[0-9][0-9][0-9]-linkage.md` is **tier 2, no cap**. Measured 2026-09-02,
`phase/003-storage-code.md` is at **300 lines of 300** — so moving 3,370 B of
prose into it is refused by the tier-1 cap, one of Perry's three hard blocks.
The prose therefore stays where it already is, in the linkage **file**, which
survives this design as a document holding what has no schema, while the edges
and the typed fields move to the store. That also answers § 8's first open
question, which asked whether the file survives the move: it does, with its
schema'd half removed.

**Decision 1 — the recommendation, and why.** `.perry/events.jsonl` is declared
`owner: perry` in `claims[]`, not owned by any lane, and both `perry-task` and
(per `ADR-013`, 2026-09-02) `perry-decide` write it without breaching the
contract. A linkage store with the same ownership lets `work` write an edge at
`add` and `goals` write one at `link`, with neither touching the other's
directory — Goal 3 satisfied without amending the contract. The rejected
alternatives: a store still under `phase/` keeps `owner: goals` and therefore
keeps `add` unable to write it, which is the defect; a proposal event that goals
discharges leaves the edge unreal until a second command runs, so Goal 2 fails
and the sweep this design exists to remove survives under a new name.

**Decision 2** is what stops the new store from repeating `DESIGN-013 § 5.1`'s
second violation. A `metric:` value is an argument about how a number was
reached — 976 B of it in one case — and arguments are what a document is for.
The phase document is the natural home; the cost is that a KR's metric and its
target then sit in two files.

**Decision 3** is the difference between a gate and a suggestion. `P003-O3-KR2`
says 100% of rows added this phase, which only holds if the question cannot be
skipped — but a refusal makes `add` fail in scripts and in intake routing, where
the asker often does not know the KR. Recording never-asked with a warning keeps
the row creatable and the number honest.

## 5. Architecture

### 5.1 · The store

`linkage.jsonl`, declared in `schema/state-schema.json § claims[]` with
`owner: perry`, `anchor: state` — so it resolves to `perry/linkage.jsonl`, beside
the five stores already there. `owner: perry` is the same declaration
`.perry/events.jsonl` carries, and it means the file belongs to no lane, not that
it belongs to everyone: see § 5.5.

Flat JSONL with a `kind` discriminator, matching `okr.jsonl` and
`.perry/config.jsonl` rather than inventing a shape. Three kinds:

```jsonc
// 1 — the typed half of a KR. Written by `goals`.
{"kind": "kr", "phase": "003-storage-code", "objective": "O1",
 "id": "P003-O1-KR1", "title": "Stores declared in `claims[]` that exist on disk",
 "target": 6, "current": 6, "stretch": false, "linked": "KR-O2.1",
 "current_provenance": {"state": "asserted", "measured": false, "…": "…"}}

// 2 — one edge, one record. Written by `work` at `add`, by `goals` at `link`.
{"kind": "edge", "task": "TASK-247", "kr": "P003-O2-KR1",
 "declared_at": "2026-09-02T14:03:11+08:00", "actor": "PMO Agent", "via": "add"}

// 3 — a declaration that this row serves no KR. Same two writers.
{"kind": "unlinked", "task": "TASK-253",
 "declared_at": "…", "actor": "…", "via": "link"}
```

`metric` is **absent** from the `kr` record — that is Decision 2. `target`,
`current` and `current_provenance` stay, because they are the number and its
audit, not the argument for it.

### 5.2 · never-asked is derived, not stored

There is no fourth kind. A task is **never-asked** when the store holds neither
an `edge` nor an `unlinked` record for it — exactly the computation
`bin/perry-state:2133-2146` already performs against `link.unlinked`. Storing it
would require deleting the record the moment an answer arrives, which is a second
write and a chance to desync; absence cannot drift.

**What Decision 3 records, then, is on the event, not in the store.** `add`
called without `--kr` and without an explicit unlinked declaration still creates
the row, writes `kr: null` on its `add` event, and warns on stderr. The event log
shows the question was reached and left unanswered; the store shows the row in
neither state; the two agree by construction. *(This is an interpretation of
Decision 3 — "record and warn" was answered before the store's shape existed. If
the intent was an explicit `never_asked` record, this section is what changes.)*

### 5.3 · What `add` writes, in one action

```
perry-task add "<title>" --kr P003-O2-KR1
  ├─ tasks.jsonl          the row                              (work, unchanged)
  ├─ linkage.jsonl        {"kind":"edge", …, "via":"add"}      (perry-owned, NEW)
  ├─ .perry/events.jsonl  add event, now carrying `kr`         (perry-owned)
  ├─ BOARD.md             rendered                             (work, unchanged)
  └─ journal/             the spec block                       (work, unchanged)
```

All five land under `perry-task`'s existing recovery marker and `commit()`, so
the edge is not a second transaction that can half-land. The `add` event gaining
a `kr` field is what makes Goal 5 computable: `P003-O3-KR2` becomes a count over
events — *rows whose `add` event carried a non-null `kr`, or for which an
`unlinked` record exists with `via: "add"`* — rather than a number typed into a
register by hand.

### 5.4 · What the document keeps

`phase/<NNN>-linkage.md` survives with its schema'd half removed: the 7
`metric:` arguments and nothing else. It is **not** a render of the store — a
render would put `target` and `current` in a second place, which is the
violation being removed. It stays `tier: 2` and keeps `owner: goals`; its
`exclude` from the tier-1 cap rule in `schema/state-schema.json` is already
there and is why the prose has somewhere to sit (`phase/003-storage-code.md` is
at 300 of its 300-line hard cap).

### 5.5 · Who writes which kind

`owner: perry` removes the *file-level* barrier the hand-off contract imposes;
it does not make the file a free-for-all. The discipline is per record kind:

| Kind | `work` (`perry-task`) | `goals` (`perry-goals`) |
|---|---|---|
| `kr` | never | `link`, `plan-phase`, `score-phase` |
| `edge` | `add --kr` | `link` |
| `unlinked` | `add` with an explicit unlinked declaration | `link --unlinked` |

This is a new class of rule — record-level rather than file-level — and nothing
mechanical enforces it today. § 7 carries it as a risk with its detection.

### 5.6 · The six readers

Measured 2026-09-02 on `d49964e`; call sites, not names:

| # | Site | Role |
|---|---|---|
| 1 | `bin/perry-goals:1657` | the only writer today (`link`) |
| 2 | `bin/perry-goals:3033` | `krs` read |
| 3 | `bin/perry-task:4491` | globs `*-linkage.md`, matches `tasks:` by regex |
| 4 | `bin/perry-lint:1200` | the linkage lint check |
| 5 | `bin/perry-lint:1231` | excludes linkage from a second check |
| 6 | `viewer/parsers.py:4503` | what `perry-state`'s attribution reader is built on |

Site 3 is its own argument for this design. `perry-task` already has to read the
edges, and its own comment says why it does so by line regex: *"this file is
markdown with a YAML-shaped block in it, not a YAML document."* A JSONL store is
`json.loads` per line — stdlib, no regex, no shape guessing.

## 6. Implementation plan

Task ids are not minted here; `add-task` mints them after lock (`TASK-NNN` below
is the placeholder form, not a row that exists).

| Phase | Scope | Proposed PMO task(s) | Owner |
|---|---|---|---|
| A | Declare `linkage.jsonl` in `claims[]` with `owner: perry`; write the three record schemas into `schema/state-schema.json`. No reader or writer moves. | `TASK-NNN` | Coding Agent |
| B | One-time import from `phase/003-linkage.md`. **Acceptance is a count, measured 2026-09-02: 7 `kr` + 11 `edge` + 75 `unlinked` = 93 records.** `agents: []` and `projects: []` are empty and import to nothing. | `TASK-NNN` | Coding Agent |
| C | Move the six readers in § 5.6 to the store. Site 5's exclusion and site 4's check are rewritten against the store, not deleted. | `TASK-NNN` | Coding Agent |
| D | `add --kr` writes the `edge` record and the `add` event carries `kr`; no-`--kr` warns per § 5.2. Lands **after** C. | `TASK-NNN` | Coding Agent |
| E | `phase/<NNN>-linkage.md` sheds its schema'd half, keeping the 7 `metric:` arguments. | `TASK-NNN` | Coding Agent |
| F | `perry-state` computes `P003-O3-KR2` from store + events instead of an asserted `current`. | `TASK-NNN` | Coding Agent |

**The one hard ordering constraint is C before D**: a writer pointing at a store
the readers have not moved to is the failure mode, and it is silent — the edge
lands, every reader still answers from the document, and `attribution` reports
never-asked for a row that was just linked. A and B are independent of each
other only in the sense that B needs A's schema to validate against.

E is separable and can lag; F is what turns the KR from asserted into measured
and should not.

## 7. Risks & mitigations

| Risk | Detection | Mitigation |
|---|---|---|
| The move silently drops existing edges | `perry-state --section linkage` reports fewer `tasks[]` entries than `phase/003-linkage.md` holds today (5 linked rows, 7 KRs) | Count before and after; the byte-comparison gate the other five stores already use |
| A seventh store with `owner: perry` becomes the precedent for putting anything shared there | `perry-lint --claims` growth; review of `claims[]` at phase close | Decision 1 records the reason as ownership-of-a-relationship, not convenience — a fact spanning two lanes, like the event log |
| `add` gains a required flag and breaks intake routing, where the KR is unknown | `perry-task route` and `intake` paths fail or start recording false `unlinked` | Decision 3; and route/intake inherit never-asked rather than a fabricated declaration |
| The metric prose moves and the KR's number loses its provenance | `perry-state` KR `current_provenance` reports `asserted` with no source | Keep `current_provenance` in the store with the number; only the argument moves |
| Declaring `linkage.jsonl` in `claims[]` makes Perry occupy that path in **every** project, not just this one — a project with a file of that name gets an NS-01 collision it did not have yesterday | `perry-lint --claims --root .` reports it; this project already carries 5 NS-01 warnings from exactly this mechanism, and `RX-001` is the standing risk | The name is specific enough to be unlikely, and `/perry relocate` is the documented remedy NS-01 already names. Worth stating because a new claim is a change to every Perry project, and none of the six phases below touches another project's files |
| A lane writes a record kind § 5.5 does not give it — the file-level contract cannot see this, because the file has no lane owner | `perry-lint` has no check for it today; the `actor` and `via` fields on every `edge` / `unlinked` record are what a check would read | Write `actor` and `via` from the start so the rule is auditable before it is enforced; a lint check is a candidate row, not part of this design |

## 8. Open questions

- ~~Does `phase/<NNN>-linkage.md` remain as a rendered view of the new store, the
  way `perry-decide list` replaced `DECISIONS.md`, or does it disappear
  entirely?~~ **Answered 2026-09-02 by Decision 2**: it remains, as a document
  holding the `metric:` arguments and nothing schema'd. It is not a rendered
  view — a render would put the typed fields back in a second place, which is
  the violation this design removes.
- `DESIGN-013 § 8` question 1 — `tasks.jsonl`'s `Next action` prose — is the same
  violation and is **deliberately not answered here**. Asked and decided
  2026-09-02, before lock: it gets its own design later. The two halves of
  § 5.1's rule are the same shape but not the same size — this design moves 7
  `metric:` fields out of one register, while `Next action` reaches 2,825 B
  across 269 task records, and it is the reason a `tasks.jsonl` line is
  unreadable and its diff unusable. Binding them would make an implementable
  design wait on an unscoped one. **This is a deferral, not an omission**: after
  this design locks, `DESIGN-013 § 8` question 1 is the only half of § 5.1 still
  open, and nothing else records that.

## 9. Changes (append-only after lock)

- **2026-09-02 — "the other five stores" is six. Three sites say five, and one
  of them is goal 4, which is written as a checkable acceptance criterion.**
  Confirmed by running the tool this document cites — `python3 bin/perry-lint
  --root .` prints **six** store lines, in this order:

  ```
    · store: …            ← the task store; this line is unlabelled in the output
    · risks store: …
    · intake store: …
    · ask store: …
    · OKR store: …
    · config store: …
  ```

  Six on both trees checked on 2026-09-02 — `main` at `d49964e` and
  `coding/task-247-config-predicate` at `d3f9f4b`. Only the record counts differ
  between them (tasks 269 vs 288, asks 14 vs 16), which is why the count of
  *lines* is the durable fact and the counts inside them are not quoted here.
  The three sites, left as written:

  | § | as written | should read |
  |---|---|---|
  | `§ 2` goal 4 | *"prints a record count and a drift verdict for `linkage.jsonl` **as it does for the other five stores**"* | the other **six** |
  | `§ 5.1` | *"so it resolves to `perry/linkage.jsonl`, beside **the five stores** already there"* | beside the **six** |
  | `§ 7`, row 1 mitigation | *"the byte-comparison gate **the other five stores** already use"* | the other **six** |

  **`§ 5.1` is self-contradictory as it stands**: it places a store *beside
  five*, while `§ 7` row 2 calls the same store *"a seventh store with
  `owner: perry`"* and `§ 1` says `phase/003-linkage.md` *"is not one of the six
  stores."* Six is the count this document uses everywhere except these three
  places, and `linkage.jsonl` is the seventh.

  **Goal 4 is why this is worth an entry rather than a shrug.** It is not prose;
  it is the acceptance criterion an implementer runs `perry-lint` against. One
  that names the wrong count is checked against the wrong thing — a reviewer who
  reads "five" and counts five has confirmed a green gate on a false premise,
  which is precisely the class of defect `§ 5.2`'s derive-don't-store rule is
  arguing about one layer down. Read goal 4 as: **seven store lines after this
  lands, six before.**

  Not corrected in place: this document is `locked`, and `decide/SKILL.md §
  Status model` allows only a `## Changes` entry after that.

## 10. References

- `perry/design/DESIGN-013-one-place-per-fact.md` § 5.1 (the rule), § 8 question 2
  (this design's origin — the question it left unanswered)
- `perry/decisions/ADR-013-adr-ids-are-never-reissued.md` — the precedent that a
  `perry`-owned store may be written by more than one lane
- `perry/phase/003-storage-code.md` § Objective 3 — the phase-002 measurement that
  produced this KR: 13 tasks declared, 47 run, 43 open rows resolving to no KR
- `reference/okr-linkage.md` — the never-guess rule this design must not weaken
- `bin/perry-task:3352` — the journal line that is `--kr`'s entire current effect
