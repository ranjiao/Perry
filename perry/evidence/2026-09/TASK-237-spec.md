# TASK-237 — spec

> Design: `ADR-010` (the decision), `DESIGN-013 § 5.4` and its risk table,
> `ADR-011` Tier C, `ADR-015` (tier 2), `ADR-019`
> Dispatch mode: auto
> Executor: claude-subagent
> Estimated cycle: large
> Subjective verification: whether the CLI render is a good enough reading
> surface **for a board**, measured on its own and not inherited from TASK-236
> Touches architecture: yes — `ARCHITECTURE.md § 2` names `viewer/parsers.py`
> as the reader of `BOARD.md`. Stop and ask before changing that section
> (`DESIGN-017` decisions 2 and 4).
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: TASK-235 (done 2026-08-30), **TASK-236 (merged 687579bd,
  AT REVIEW — see Preconditions)**
- **KR linkage**: declared unlinked. `TASK-262` and `P003-O2-KR3` wait on the
  surface this row creates; they are not this row's deliverable.
- **Verification rung**: **V4**, clearing `ADR-020`'s gate rather than inheriting
  it. `perry-tasks render --write` is a write path, and of `review.md § 0`'s
  three questions the first answers yes: this row **deletes a 142 KB file** on
  the strength of a store, and if the store is wrong on a row the row is gone.

## Preconditions, and one of them is not satisfied yet

| | |
|---|---|
| TASK-235 (`DECISIONS.md` stops existing) | done 2026-08-30 at V4 |
| TASK-236's read-surface report, **the gate** | written and POSITIVE — `TASK-236-result.md § 3` |
| TASK-236 itself | **merged, not closed.** Its V4 was dispatched 2026-09-12 |

**Do not start the deletion until TASK-236's verdict is in.** The gate
`DESIGN-013`'s risk table names is the REPORT, and that report exists and is
affirmative — so this row is not blocked on the design any more. What it is
blocked on is ordinary: `TASK-236` is the same pattern on a smaller file, and
building the larger deletion on a foundation that may be sent back is how a
round gets thrown away. Write the spec's measurements and the plan now; cut
`BOARD.md` after the verdict.

## Why

`BOARD.md` is a projection of `tasks.jsonl` and nothing else reads it as truth.
Measured 2026-09-12 on `85c6f747`:

| | |
|---|---|
| size | 190 lines, **142,306 bytes** |
| inside table rows | **135,627 bytes — 99%** |
| table lines | 153 of 190 |

`DESIGN-013 § 5.4` measured 42,099 of 43,289 bytes at 97%. **The file has
tripled since and the ratio went up**, which is the argument getting stronger
rather than older: what is not a table is the title, a header line and eight
section headings.

## Files in scope

- `perry/BOARD.md` — deleted.
- `bin/perry-tasks` — `render` / `diff` / `verify` are the projection's
  machinery. What of it survives a file that does not exist is this row's
  judgement, argued in the report.
- `bin/perry-task` — reads the board today through `viewer/parsers.py`.
- `viewer/parsers.py` — the markdown register readers. **Measure what actually
  retires; do not take a number from this spec.** See below.
- `bin/perry-state`, `bin/perry-lint`, `bin/perry-goals` — read the board
  through the same reader. Enumerate; do not sample.
- `tests/` — the guards and the reconciliation.
- `perry/evidence/2026-09/TASK-237-result.md` — written.

## Bound

```
Enumeration: every call site in bin/ and viewer/ that reads BOARD.md, directly
             or through viewer/parsers.py § parse_board
Size:        DERIVE IT. A number is not given here on purpose — see below.
Remainder:   BOARD_TEMPLATE.md and the fixtures under tests/. A template is not
             a projection and a fixture is not a project; both stay.
Last element: the lowest-ranked call site in your own enumeration's order
```

**Why this Bound gives no number, and it is a lesson paid for twice.**
`TASK-236`'s spec asserted that deleting the KR tables would retire
`_parse_krs`, 26 lines of `viewer/parsers.py`. It retires **zero**:
`parse_phase` calls that function unconditionally, because phase files carry
their own KR tables, and a comment four lines above says so. The number was
written from a grep and not from the call graph. Do the same thing here and you
will be wrong by the same mechanism. **Derive the set, publish it, and say
which sites you were surprised by.**

## The gate this row must not inherit

`TASK-236`'s report is POSITIVE **for the OKR's key results**, and its own
§ 3.4 says in as many words that the verdict must not be generalised: the OKR
had two surfaces and only one was adequate. `perry-goals list --level overall`,
the command a reader tries first, prints 19 of 38 rows, truncates the text and
shows three columns as `—`.

**The same trap is live here and it is worse.** Measured 2026-09-12,
`perry-task list` — the discoverable replacement for `BOARD.md` — prints
**id, priority, status and a truncated title**. `BOARD.md` carries fifteen
columns, and its `Next action` cells run to the 1,000-byte cap. So the
obvious command drops most of what the file holds.

**This row must answer the reading question for a BOARD, on its own
measurement.** If the answer is that no command is an adequate reading surface
for a row's next action, that is a finding and a stop, not a detail to fix
later.

## What is EASIER here than it was for TASK-236, and it should be said

`ADR-015` makes `BOARD.md` **tier 2** — a projection, where a hand edit is
refused rather than reported. `OKR.md` is tier 1, and the whole of
`TASK-236 § 3.5` is an argument about a tier-1 document losing its content.
That argument does not arise here, and the spec says so rather than leaving the
executor to re-derive it.

`TASK-236`'s finding F-2 — the row closed the only supported path for a user to
AUTHOR a KR — also does not transfer: `perry-task` is a complete writer for a
task row, with `add`, six statuses, `next`, `retitle`, `evidence`, `rung`,
`prioritize` and `depends`. **Show that it is complete for every column
`BOARD.md` carries**, rather than assuming it; a column with no writer is F-2
in this row's clothes.

## Deliverable

1. `perry/BOARD.md` does not exist; the board is what a command prints.
2. **The read-surface report for a board**, as a named section of the result,
   measured here and not inherited.
3. The enumerated call-site set, with what retires and what does not.
4. `perry/evidence/2026-09/TASK-237-result.md`.

## What it must not do

1. **It must not delete before gating.** Order: render, byte-compare, then
   delete. `TASK-236` proved this is not merely prudent — run its byte gate
   AFTER the rows were gone and it returns `identical: true` AND
   `every_line_and_cell_came_from_the_store: true` at exit 0, with the records
   stranded and `records_not_in_the_file` empty. **A gate run second says
   nothing.** Expect the same blindness here and check for it explicitly.
2. **It must not edit `schema/state-schema.json`.** High-stakes list; needs the
   user's authorisation. If the board's file declaration must change, that is a
   finding you report.
3. **It must not edit `ARCHITECTURE.md § 2`** without stopping to ask.
4. **It must not leave a column with no writer.** See above.
5. **It must not start before `TASK-236`'s verdict.** See Preconditions.

## Verification

1. Every open row reachable through a command after the deletion, enumerated
   and compared field by field against `tasks.jsonl` — not sampled.
2. The byte gate run BEFORE, quoted; and run AFTER, with its blindness stated
   either way.
3. **Mutation.** Corrupt one record and show a named test go red. Delete a
   record entirely and show a different named test go red.
4. **Anti-vacuity.** Empty `tasks.jsonl` of its open rows in a scratch copy and
   show the guard reddens. A guard that builds its expectation from the file it
   compares against is the bar `TASK-182` already caught once.
5. The suite, with the pre-existing reds named rather than counted.

## Out of scope

- `TASK-262` and `P003-O2-KR3`. They consume the surface this row creates.
- The `risks`, `intake` and `ask` registers' own projections, except where
  deleting `BOARD.md` forces a decision about them — in which case name it and
  stop, do not widen.
- `viewer/parsers.py`'s tier-1 readers (`OKR.md`, phase files, role cards).

---

## Amendment 2026-09-14 — the first deliverable is the reading surface (USER-931 answer A)

**Everything above still describes the deletion. None of it runs yet.** The
reading gate this spec requires was measured on 2026-09-14
(`evidence/2026-09/2026-09-14-task-237-gate.md`) and it stopped the row: the one
command that prints a board row whole, `perry-tasks render`, fills the task rows
**in place** over `BOARD.md` and refuses when the file is gone. And a Perry
project is recognised by that file in eight code sites and four prose sites. The
user chose to build what the deletion needs first, as this row's first
deliverable, with no new row.

### Deliverable 1 — a board render from the store alone

A command that prints the whole board from `tasks.jsonl` (and the register
stores the board already renders from) **with no `BOARD.md` on disk**: every
section, every row, every column, every cell whole, to stdout.

**Where the skeleton comes from — measured, not invented.** Today it comes from
the file: `perry_store.plan(board, …)` iterates `board.lines`. A render with no
file needs it from somewhere else, and the tree already declares most of it:

| part of the board | declared today in |
|---|---|
| section order | `schema/state-schema.json § files[id=board].headings` — P0, P1, P2, Cadence, User Input Queue, Top risks |
| per-section columns | `§ files[id=board].tables[]` — required `columns` plus `optional_columns` |
| the title and header prose | `work/state/BOARD_TEMPLATE.md` — but its task tables carry **6** columns and the live board carries **15**, so it is not the live skeleton as-is |

Where the schema and template cannot reproduce the live file, that is a
**finding to report**, not a gap to paper over by reading the file.

**The acceptance is byte-identity.** On a project where `BOARD.md` still exists,
the store-only render must be byte-identical to it. Measured baseline:
`perry-tasks render` on `HEAD` is byte-identical to `perry/BOARD.md` at
154,151 bytes — that is the bar, now without the file.

### Deliverable 2 — a Perry project is not recognised by `BOARD.md` existing

Every site that decides "is this a Perry project / where is its state root" by
the file must decide it another way — `bin/lib § ` `configured(d)` already does
for projects with `.perry/config.jsonl`. **Enumerated 2026-09-14; re-enumerate,
do not trust this list:**

| code | prose |
|---|---|
| `bin/perry-task:669`, `:8720` | `work/SKILL.md:43`, `:108`, `:292` |
| `bin/perry-explain:663` | `work/reference/bootstrap.md:3` |
| `bin/perry-lint:4906`, `:5882` | |
| `bin/perry-state:2595` | |
| `viewer/parsers.py:579` | |
| `bin/lib/__init__.py:540` | |

Several accept `OKR.md` as an alternative. Perry's own repository would survive
on that; a project with neither would bootstrap on every session. Measure it on
a board-less, OKR-less configured project.

### Files in scope for deliverables 1 and 2

- `bin/perry-tasks`, `bin/perry_store.py` — the renderer.
- the twelve detection sites above, re-enumerated.
- `schema/state-schema.json` and `work/state/BOARD_TEMPLATE.md` — **read only.**
- `tests/` — the guards.
- `perry/evidence/2026-09/TASK-237-result.md` — written.

### Bound for deliverables 1 and 2

Enumeration: `grep -rnE 'BOARD\.md' bin/ viewer/ SKILL.md work/ goals/ decide/ reference/` filtered to existence and detection checks, plus every call path of `perry_store.plan`. Size: the enumeration's count, stated before the first edit. Remainder: every site not changed, each with a reason.

### What deliverables 1 and 2 must not do

1. **Must not delete `BOARD.md`.** Deletion is deliverable 3 and runs only after
   1 and 2 are measured — the order this spec already required.
2. **Must not edit `schema/state-schema.json`.** High-stakes; if the declared
   skeleton cannot reproduce the live board, report it.
3. **Must not build the render by reading `BOARD.md`.** A render that reads the
   file it replaces proves nothing — the blindness `§ What it must not do` item 1
   already names.
4. **Must not change what `perry-tasks render` does today** while the file
   exists, beyond what byte-identity allows.

### Verification for deliverables 1 and 2

1. **Byte-identity, in both states.** With `BOARD.md` present, the store-only
   render `cmp`-equal to the file. With `BOARD.md` deleted in a scratch copy, the
   render exits 0 and TASK-391's 2,218-byte next action is in its output whole.
2. **Detection on a board-less project.** A scratch project with
   `.perry/config.jsonl`, `tasks.jsonl` and no `BOARD.md` or `OKR.md` is
   recognised by every enumerated site; the session bootstrap in
   `work/SKILL.md` is not triggered.
3. **Mutation.** Reorder one declared heading, drop one optional column, corrupt
   one record: each reddens a named test.
4. **Anti-vacuity.** A guard that builds its expected bytes from `BOARD.md` is
   the defect, not the check — the expectation must come from a file the render
   does not read.
5. The suite, with the pre-existing reds named.

## Amendment 2026-09-14 (2): deliverable 1 is accepted cell-whole, not byte-identical (USER-932 answer 3)

Deliverables 1 and 2 ran and were merged at `9549626e`
(`evidence/2026-09/TASK-237-result.md`).

- **Deliverable 2 was delivered and re-measured by the PMO.** Each of the nine
  detection sites, with `configured(...)` replaced by `False`, reddens its
  named test. A project holding only `.perry/config.jsonl` reports
  `installed: true`.
- **Deliverable 1 stopped at hard limit 5.** A board built only from the
  declared skeleton is 157,422 B against the live 157,242 B, with 2,349 B on
  matching lines. The gap is 12 kinds of layout that exist only in the file.
  Every cell is already held in a store.

USER-932 answered **3: drop the byte clause.**

### Deliverable 1, re-stated

A board render that reads **only** `tasks.jsonl`, `asks.jsonl`, `risks.jsonl`,
`intake.jsonl`, `.perry/config.jsonl`, `schema/state-schema.json` and
`work/state/BOARD_TEMPLATE.md`. With `BOARD.md` absent, it prints every row,
every column and every cell whole.

- **Layout** follows the declared skeleton. Where the skeleton leaves a choice
  open, the render makes it once and says so; it does not copy the live file.
- **Byte-identity with the live file** is not a criterion.
- **Replaces** the retired `### Verification for deliverables 1 and 2` item 1.
  Items 2–5 stand.

### Verification for deliverable 1 (replaces item 1 above)

1. **Cell-whole, in both states.** Run in a scratch copy with `BOARD.md`
   deleted, and again with it present:
   - every store row appears exactly once in its declared section;
   - every column the section declares is present;
   - every cell equals the store value, after the one documented escaping of
     `|` and newlines;
   - TASK-391's 2,218-byte next action is whole.
2. **Independence from the file.** The same run with `BOARD.md` replaced by
   garbage prints the same bytes. The guard's expectations come from the stores,
   never from `BOARD.md`.
3. **Mutation.** Each of these reddens a named test:
   - drop one declared column;
   - truncate one cell;
   - skip one store row;
   - read one byte of `BOARD.md`.

### Still before deletion (deliverable 3), measured 2026-09-14 on `5fa66a7f`

Neither blocker opens a row; both are TASK-237's own deliverable-3 work.

1. **With `BOARD.md` deleted, `perry-task` writes refuse.** `perry-task next`
   answers "no BOARD.md … this command needs the projection layout to render
   its write".
2. **`schema/state-schema.json § files[id=board]` still has `required: true`,**
   so a board-less project lints red (measured: `perry-lint --root` on an archive of
   `5fa66a7f` with `BOARD.md` deleted exits 1 with `[missing-file] required state file not found`;
   the same archive with the file exits 0, 0 errors).
   - Changing it is a schema edit: it needs the user's consent and appears on
     `.perry/hook.md § High-stakes operations`.
