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
3. **The ask and risk read surfaces are built from `BOARD.md`, not from their
   stores**, and fail silently without it. Measured 2026-09-14 on a `git archive`
   of `d358a2cf` with the stores unchanged, the file present and then deleted:

   | surface | `BOARD.md` present | `BOARD.md` deleted |
   |---|---|---|
   | `perry-task asks --all --json` `count` (store: 33) | 33 | **0**, exit 0 |
   | `perry-task list --json` `risks` | 2 | **0** |
   | `perry-task list --json` `drift.drift` | 0 | **97** |
   | `perry-state --json` `risks.count` / `source` | 2 / `table` | **0 / `none`** |
   | `perry-task list --json` `tasks` | 97 | 97 |
   | `perry-tasks board` | 157,364 B | 157,364 B (cmp-equal) |

   `cmd_asks` reads `P.load_snapshot(...).board.user_input_queue`, which parses
   `BOARD.md`. Deleting the file before these surfaces read their stores would
   turn "no asks" and "no risks" into answers the tools give confidently. This
   is deliverable-3 work. It opens no row. The published contracts (`perry-asks/list/1.0`,
   `perry-task/list/2.0`) name the fields and would not need to change.

## Amendment 2026-09-14 (3): deliverable 3, deleting `BOARD.md`, is authorised and split in two

**The user's consent, in their words, 2026-09-14:** "删除board.md可以做" (deleting
BOARD.md can go ahead). The PMO reads it as covering every change the deletion
needs and that this spec names as needing consent:

- the `schema/state-schema.json § files[id=board]` edit (`required: true`, and
  the claim);
- the `ARCHITECTURE.md § 2` change that the header block says to stop and ask
  about;
- the `.perry/hook.md` line naming `perry/BOARD.md` as the roadmap source of
  truth;
- deleting `perry/BOARD.md` itself.

Anything wider than those is still a stop.

Deliverable 3 is split so that the risky half can be measured before the file
goes. Both parts share the Bound above: derive the call-site set, do not take
a number from here. On 2026-09-14 a `grep -c` of `BOARD.md` over `bin/` and
`viewer/` gave roughly 250 mentions in 15 files; that is a size warning, not a
census.

### Deliverable 3a: nothing needs `BOARD.md` (the file stays on disk)

1. **Every read surface answers from its store.** With `BOARD.md` deleted, every
   published read payload must equal the payload with it present. That covers
   `perry-task list` / `asks` / `events`, `perry-state --json`,
   `perry-goals list` and `perry-decide list`. Two exceptions:
   - fields that describe the file itself, each named in the result with its
     board-less value;
   - `generated_at`-style clocks.
   The three measured silent failures are the floor, not the list:
   - `asks --all` 0 of 33;
   - `list` risks 0;
   - `perry-state` risks.count 0.
   `TASK-268` (top_risks from `BOARD.md`) is inside this item; say so in the
   result.
2. **Every `perry-task` write succeeds without `BOARD.md`.** The write lands
   the store record, the journal line and the event in both states. While the
   file exists it is still re-rendered, so a project that keeps the file is not
   broken by this step.
3. **`perry-lint` on a board-less project** reports the same errors as with
   the file, except the `[missing-file] BOARD.md` error that 3b removes.
4. **Published contracts keep their field names and versions.** If a field
   cannot keep its meaning without the file, stop and report; do not bump the
   contract.

**Must not:**
- edit `schema/state-schema.json` (that is 3b);
- delete `perry/BOARD.md` in the worktree;
- change `perry-tasks board` output;
- write any store outside a test fixture or scratch copy.

**Verification (3a):**
- A payload-diff table per read surface, present against deleted, measured
  on a `git archive` copy.
- A write matrix: every `perry-task` write subcommand, in both states, with
  exit code and the resulting store record compared.
- Mutations: put a `BOARD.md` read back into the ask, risk and intake read
  paths, and into one write path. Each must redden a named test.
- The suite, with pre-existing reds named.

### Deliverable 3b: the file is gone (after 3a is merged and re-measured)

1. Change `files[id=board]` so a board-less project is conformant, and update
   the claim.
2. Delete `perry/BOARD.md`.
3. Decide what `perry-tasks render` / `diff` / `verify` and the `*-render
   --write` hand-backs become, and argue it in the result. There is nothing to
   write to any more.
4. Rewrite every lane doc that tells a reader to read or edit `BOARD.md`:
   - `work/SKILL.md` and its references;
   - `ARCHITECTURE.md § 2`;
   - `.perry/hook.md`;
   - `bin/README.md`.
5. `perry-lint` is clean on this repository without the file.
6. The V4 round for this row runs once, after 3b, over deliverables 1, 2
   and 3 together.

`TASK-434` (answered asks never leave the board) is **not** retired by the
deletion: `perry-tasks board` prints every ask record.

## Amendment 2026-09-14 (4): what a consumer needs from a board-less Perry, added to 3b

aiMark's feedback was verified by the PMO on `e1b171d2`; the record is
`evidence/2026-09/2026-09-14-aimark-feedback-task-237.md`. The user decided
three things on 2026-09-14, and all three join deliverable 3b. None opens a
row.

1. **An `installed` boolean on every published read payload.**
   - It goes on `perry-task/list`, `perry-asks/list`, `perry-events/list`,
     `perry-goals/list`, `perry-decide/list` and `perry-knowledge/list`.
     `perry-roles/list` rides `perry-state --json`, which already carries
     `installed`.
   - The change is additive, so it is a minor bump per `schema/README.md`,
     with one `semantics[]` entry per contract and the parity baseline
     re-recorded. The only baseline diffs are these keys and versions.
   - On a non-Perry directory each payload keeps its empty shape and exit 0, and
     says `installed: false`.
   - `schema/asks-list-contract.md § Exit codes` is reconciled with that: a
     directory with no register is not an unreadable register.
2. **One `installed` criterion, written down.**
   - A project is installed when `.perry/config.jsonl` exists at its root, or
     any canonical store declared in `schema/state-schema.json § claims`
     exists under its state root.
   - `BOARD.md` alone no longer counts, and neither does `OKR.md`, `phase/`
     or `design/` alone.
   - `perry-state` and every payload in item 1 share one predicate. Its
     criterion is written once in `schema/README.md` and cited by each contract.
   - The deliverable-2 detection walks that OR in `BOARD.md` are changed to the
     same predicate.
   - **Stop and report** if a project shape Perry supports today loses
     `installed`. Enumerate the test fixtures and the adoption paths
     (`/perry adopt`, a goals-only start) before changing the predicate, and
     report any that would.
3. **`perry-tasks board` for a human reader.**
   - On a project that is not installed it refuses: exit 1, the reason on
     stderr, nothing on stdout.
   - The title names the project: from a `.perry/config.jsonl` setting if one
     is declared, and from the project directory's name otherwise. Measured:
     this repository has no such setting. **Do not add a config key**; that is
     a schema change beyond this consent.
   - The template's instruction prose, text written for a person filling the
     file in, is not printed. Headings and tables stay.
   - This replaces D1 layout choice C1. The `DECLARED_BOARD_CHOICES` entry and
     its guards are updated, and `{{` must not appear anywhere in the output.

**Verification additions for 3b:**
- On an empty directory, every read command in item 1 returns exit 0 with
  `installed: false`, and `board` exits 1.
- On a directory holding only `BOARD.md`, every surface reports
  `installed: false`.
- On a directory holding only `.perry/config.jsonl`, and on one holding only
  `tasks.jsonl` under a declared state root, every surface reports
  `installed: true`.
- Mutations: drop `installed` from one payload; accept `BOARD.md` in the
  predicate again; let `board` print on a non-installed directory; print one
  `{{` placeholder. Each reddens a named test.

## Amendment 2026-09-14 (5): cadence gets a store; 3b is split into 3b and 3c

3a merged at `47dce04a` (`evidence/2026-09/TASK-237-d3a-result.md`). It stopped on
cadence: cadence rows exist only in `BOARD.md § Cadence`, so without the file
`cadence-add` and `cadence-done` refuse.

**The user's decisions, 2026-09-14:**

1. **Cadence is kept and gets its own store (answer A, "给 cadence 建存储").** This
   is consent for one more `schema/state-schema.json` change: a new
   `work`-owned claim for the cadence store. Consent was asked for and given
   with the uses measured:
   - this repository: 0 rows, 0 events;
   - `Gimegime-pmo`: 5 hand-written rows, with prose in `Next due` and the
     aperiodic frequencies `continuous` and `hourly`;
   - `aimark`: 1 row, `per task` / `ongoing`.
2. **`asks[].idle` reading `""` instead of `"—"` is accepted.** It is announced
   in `perry-asks/list` 1.1 `semantics`, and no further change is needed.

**3b is split so that each round stays reviewable:**
- **3b** makes everything work with the file still on disk.
- **3c** deletes it.

### Deliverable 3b: the store-backed features a board-less project still lacks (the file stays)

1. **A cadence store.**
   - The store is `cadence.jsonl` under the state root, declared in
     `schema/state-schema.json § claims` beside `risks.jsonl`, `intake.jsonl`
     and `asks.jsonl`, in the same shape as those claims.
   - Records carry the register's columns: id, recurring task/title, owner,
     frequency, next due, last run, last evidence, and order.
   - **A cell is stored as written.** Prose in `Next due` and aperiodic
     frequencies are live data on a real register; it is reported by
     `perry-state § cadence`, never normalised.
   - `cadence-add` and `cadence-done` write the store, the event and the
     journal. While `BOARD.md` exists they also re-render its `## Cadence`
     section, exactly like the other registers after 3a.
   - `perry-state § cadence` and `perry-tasks board` read the store.
   - **An import for a project whose cadence lives only on its board:** the
     same one-way `--from-board` shape the risks, intake and asks registers
     already have. It refuses unless the claim is declared and the section is a
     readable table, and it round-trips the section.
   - Measure the import on **copies** of `Gimegime-pmo/BOARD.md` and
     `aimark/perry/BOARD.md` in scratch space only. **Never write to either
     project.**
2. **Amendment (4) in full:**
   - `installed` on the six read payloads, as a minor bump with `semantics`;
   - one `installed` predicate, where `BOARD.md` alone does not count;
   - `perry-tasks board` refuses on a non-installed directory;
   - `board` titles itself with the project name and drops the template's
     instruction prose.
   The cadence store is a canonical store for the predicate.
3. **The board-less gaps 3a named**, each fixed or argued in the result:
   - `perry-diagnose` still reads asks and intake from `BOARD.md`.
   - Three `perry-lint` checks go quiet with the file absent.
   - Without the file, `perry-state § project.name` is the state root's
     directory name (`perry`). Resolve it with the same rule as the board title
     in Amendment (4): a declared config setting, else the **project** root's
     directory name.
   - A test that notices a shipped `semantics` entry being removed.

**Must not:**
- delete or edit `perry/BOARD.md`;
- flip `files[id=board].required`, which is 3c;
- edit `ARCHITECTURE.md`, `.perry/hook.md` or the lane docs, which is 3c;
- write any real store in the worktree;
- touch any other project on disk.

**Verification (3b):**
- 3a's payload-diff and write matrix, extended to `cadence-add`,
  `cadence-done` and the cadence section of `perry-state` and `board`.
  Measure present and deleted states, plus a fixture carrying a periodic row,
  an aperiodic row and a prose `Next due` row.
- The import round-trips both scratch copies.
- Amendment (4)'s verification list.
- Mutations: put a `BOARD.md` read back into the cadence read and the cadence
  write; lose a prose cell on import; drop `installed`; accept `BOARD.md` in the
  predicate; print a `{{` placeholder; let `board` print on a non-installed
  directory. Each must redden a named test.
- The suite.

### Deliverable 3c: the file is gone (after 3b is merged and re-measured)

Amendment (3)'s 3b list, unchanged:
- `files[id=board]` so that a board-less project conforms;
- delete `perry/BOARD.md`;
- the fate of `render` / `diff` / `verify` and the `*-render --write`
  hand-backs;
- the docs: `work/`, `ARCHITECTURE.md § 2`, `.perry/hook.md`, `bin/README.md`,
  and `modes/queue.md`'s cadence text;
- `perry-lint` clean without the file.
Then one V4 over deliverables 1–3.

## Amendment 2026-09-14 (6): every start creates the config store first (user answer A); the rest of 3b is 3b′

3b merged partially at `161c927c` (`evidence/2026-09/TASK-237-d3b-result.md`)
and stopped on the `installed` predicate. Four documented starts write only
markdown, so under Amendment (4)'s rule they would read as not installed and
be offered the bootstrap on every session:
- the `work` bootstrap;
- a decide-only start;
- `goals init` before `plan-phase`;
- `/perry adopt --only=design,knowledge,arch`.

The cause is that first-time setup still tells the agent to write
`.perry/config.md`, which ADR-019 deleted.

**User's decision, 2026-09-14: A.** Every start writes `.perry/config.jsonl`
first, through `perry-config set`, and then the predicate lands. Measured the
same day: `perry-config set --root <empty dir> "Document language" English` exits
0, creates `.perry/config.jsonl`, and `perry-state --section installed` goes from
`false` to `true`.

### Deliverable 3b′: the rest of 3b

1. **Every start writes the config store first.** Enumerate every documented
   way a project begins: `/perry setup`, the `work` bootstrap, a decide-only
   start, `goals init` and every `/perry adopt --only=` subset. Enumerate them
   from the docs and the router, not from this list.
   - Each start's first write becomes `perry-config set` on `.perry/config.jsonl`.
   - Every instruction that still writes `.perry/config.md` is corrected.
   - These are lane-doc edits: `SKILL.md`, `work/`, `goals/`, `decide/` and
     `reference/adoption*.md`. They are allowed for exactly this purpose.
2. **Amendment (4) items 1 and 2, now unblocked.**
   - `installed` on the six read payloads, as a minor bump with `semantics`
     and the parity baseline re-recorded.
   - One predicate: config store, or any declared canonical store, and
     `BOARD.md` alone does not count. It is written once in
     `schema/README.md` and cited by each contract.
   - The deliverable-2 detection walks change to that predicate.
   - `perry-tasks board` refuses on a non-installed directory.
   - The `asks` contract's exit-code text is reconciled.
3. **Re-run the start enumeration after the change.** Every start, executed as
   its doc now says in a scratch directory, ends with `installed: true`. A doc
   step that cannot be executed mechanically is followed by hand and
   recorded.

**Must not:**
- flip `files[id=board].required`, delete `BOARD.md`, or change
  `ARCHITECTURE.md` or `.perry/hook.md` (all 3c);
- edit any other schema;
- write any real store;
- touch any other project.

**Verification (3b′):**
- Amendment (4)'s four-directory list: empty, `BOARD.md`-only,
  `config.jsonl`-only, and `tasks.jsonl`-only.
- The start re-run in item 3.
- Mutations:
  - drop `installed` from one payload;
  - accept `BOARD.md` in the predicate;
  - let `board` print on a non-installed directory;
  - restore one start's `.perry/config.md` instruction (a doc guard must
    notice).
- The suite.

3c is unchanged.

### 3c addition 2026-09-14: root documents a deletion rewrites

A root-document audit on 2026-09-14 corrected what was already false (commit
below) and left, on purpose, every line that is true while `BOARD.md` exists.
3c rewrites these when it deletes the file:
- `AGENTS.md`: "Do not derive a dashboard by eyeballing `perry/BOARD.md`" and
  "do not hand-edit `BOARD.md`".
- `ARCHITECTURE.md`:
  - §2 `viewer/parsers.py` "Owns: `BOARD.md`, `OKR.md` …";
  - §4 the write diagram's "BOARD.md re-rendered from the record";
  - §6 NN-2's projection wording.
- `README.md` and `README_cn.md`: the file tree's `BOARD.md` line.
- `SKILL.md`: the lane ownership table's `BOARD.md (incl. ## Intake, ## Cadence)`.

`SKILL.md`'s five `.perry/config.md` mentions belong to the running 3b′ (start
docs). The PMO sweeps any left over after 3b′ merges.

`bin/` documents, audited the same day. These lines stay true until the file
is deleted:
- `bin/ARCHITECTURE.md` §1: "an agent that opens `BOARD.md` and counts…".
- `bin/README.md § For an agent`: "On a non-zero exit … fall back to reading
  `BOARD.md` and `OKR.md` directly".
- The tool-table and usage wording that describes `render` / `diff` as
  regenerating `BOARD.md`.
- `bin/perry-tasks`' own `SURFACE` summary, "the task store and the three
  registers beside it". This is code, not a document; it now has four
  registers.

## Amendment 2026-09-14 (7): installed needs `.perry/` (user); 3c's full list

3b′ merged at `0ec65094` (`evidence/2026-09/TASK-237-d3b-prime-result.md`).
Its row R1: under Amendment (4) item 2, any folder that happens to hold a file
named `tasks.jsonl` (or another store name) reads as an installed Perry project.
The PMO reproduced this: a directory holding only `tasks.jsonl` reports
`installed: true` on every surface.

**User's decision, 2026-09-14: tighten.** A project is installed when
`.perry/config.jsonl` exists at its root, **or** when a `.perry/` directory
exists at its root **and** a canonical store declared in `§ claims` exists
under its state root. A store file with no `.perry/` beside it no longer counts.
Every documented start writes `.perry/config.jsonl` first (3b′), so no supported
start is affected. Measure that again rather than assuming it.

### Deliverable 3c: the file is gone (after 3b′, which is merged)

1. **The predicate tightening above.**
   - `viewer/parsers.py § installed` and `schema/README.md § installed` change.
   - Each contract that cites the rule is re-read for a sentence the change
     makes false.
   - `tests/test_installed_is_one_predicate` gains the `tasks.jsonl`-only-
     without-`.perry/` directory as a `false` case.
   - `test_explain_typed_tasks`, which 3b′ inverted, is inverted back if its
     fixture has no `.perry/`.
   - **This is a meaning change** to a published field. Announce it with a
     `semantics` entry on each of the six contracts, as a minor bump. Stop and
     report if a contract rule says it must be major.
2. **`files[id=board]`.** Make a board-less project conform (`required`, and
   the claim). This is the consented schema edit.
3. **Delete `perry/BOARD.md`.**
4. **`perry-tasks render` / `diff` / `verify` and the `*-render --write`
   hand-backs.** Decide what each becomes when there is no file, and argue it in
   the result. Delete what has no subject, as `perry-config`'s five verbs were
   deleted under ADR-019. The register import verbs (`*-write --from-board`) stay
   while other projects still hold boards.
5. **Every writer stops rendering a file that no longer exists.** No command
   may create `BOARD.md`. `perry-lint` is clean on this repository without it.
6. **Documents.** Every line in this spec's two "3c addition" lists:
   - root: `AGENTS.md`, `ARCHITECTURE.md` §2/§4/§6, `README.md`, `README_cn.md`,
     and the `SKILL.md` ownership table;
   - `bin/`: `bin/ARCHITECTURE.md` §1, `bin/README.md § For an agent`'s board
     fallback, and the `render`/`diff` wording;
   - `bin/perry-tasks`' SURFACE summary ("three registers");
   - `ARCHITECTURE.md § 2` and `.perry/hook.md`'s roadmap-source line.

   Plus 3b′'s rows:
   - **R3:** the docs that still name `.perry/config.md` — relocate,
     `reference/config.md`, the i18n language-switch section,
     `reference/diagnose.md`, `modes/`, and the ADR template.
   - **R5:** `work/reference/bootstrap.md` step 2 writes `BOARD.md` "at the
     project root". With no board it writes nothing there; re-derive what that
     step now does.

   Also `modes/queue.md`'s cadence text.
7. **`perry-tasks board` is the board.** Every doc that tells a reader to open
   `BOARD.md` names `perry-tasks board` (for a person) or `perry-task list --json`
   (for a program).

**Must not:**
- change any published payload's keys, except the item-1 `semantics` entries
  and versions;
- write this repository's other stores;
- touch another project;
- edit `ARCHITECTURE.md § 1`, a §3 Forbidden line, or a §6 confirmed rule
  without stopping to ask. NN-6 still binds: §2, §4 and §8 are descriptive and
  may change; NN-2's wording is a confirmed rule, so report it rather than
  rewriting it.

**Verification (3c):**
- On a `git archive` of the final commit, `BOARD.md` is absent and:
  - `perry-lint --root .` exits 0 with no `[missing-file]`;
  - every `perry-task` write subcommand exits 0 and creates no `BOARD.md`;
  - every published read payload equals the pre-deletion payload (the archive
    of the base with the file deleted), except the item-1 entries and versions;
  - `perry-tasks board` exits 0.
- Every documented start is re-run and ends `installed: true`.
- The five-directory table:
  - empty: `false`;
  - `BOARD.md`-only: `false`;
  - `tasks.jsonl`-only without `.perry/`: `false`;
  - `.perry/` plus `tasks.jsonl`: `true`;
  - config-only: `true`.
- `grep -rn 'BOARD\.md'` over `bin/ viewer/ SKILL.md AGENTS.md README*.md
  ARCHITECTURE.md work/ goals/ decide/ modes/ reference/`: every remaining hit is
  listed with a reason (history, the import verbs, fixtures).
- Mutations, each reddening a named test:
  - put a `BOARD.md` render back into one writer;
  - accept a store without `.perry/` in the predicate;
  - make `perry-lint` require the file again;
  - restore one doc's `open BOARD.md` instruction, if a doc guard exists.
    If none exists, say so; do not build one for prose meaning.
- The suite.

Then one V4 round over deliverables 1–3.

## Amendment 2026-09-14 (8): the user's decisions on 3c's stops; 3d is the doc sweep

3c merged at `0f1ed007`: `perry/BOARD.md` is deleted
(`evidence/2026-09/TASK-237-d3c-result.md`). It stopped on four documentation
points. The user decided all four on 2026-09-14.

1. **V5 sign-off on the hand-off contract: SIGNED, as proposed** (3c result
   § 5.3). The `work` row of `SKILL.md § The hand-off contract` names
   `tasks.jsonl` and its four register stores (`perry-tasks board` prints them)
   instead of `BOARD.md`. The refusal case "`goals` writing `BOARD.md`" becomes
   "`goals` writing `tasks.jsonl`". The signature is the user's answer
   "签，按建议文本" (sign, per the proposed text), 2026-09-14. It covers exactly
   that text, plus the same substitution in:
   - `tests/test_ownership.py`'s `SCHEMA_PATH_TO_CONTRACT`, `FOREIGN_WRITES` and
     the refusal-case literal;
   - `goals/SKILL.md:51`;
   - `reference/adoption.md:29`.
2. **`ARCHITECTURE.md` NN-2 and § 5: both as proposed.** The PMO applied this
   on main before 3d; it is not 3d's.
3. **`work/reference/git-boundaries.md:11`: edit and re-pin.** Remove `BOARD.md`
   from the work-docs list, or replace it with the store if the sentence needs a
   noun. Update `test_spec_scannability`'s SHA-256 pin in the same commit, and
   let the commit message give the reason.
4. **The remaining documents: a small doc-only round (3d), then one V4 over
   deliverables 1–3.**

### Deliverable 3d: documents only

1. Item 1, exactly as signed. `SKILL.md` has about 23 B of byte-budget
   headroom and the new row costs about 45 B, so compress equal text **elsewhere
   in `SKILL.md`** without changing any other rule's meaning. Say what was
   compressed.
2. Item 3.
3. **3c result § 8.2's "sweep (R3)" lines.** Each describes the board as a file
   Perry keeps. Rewrite each so it is true of a project with no `BOARD.md`, and
   point to `perry-tasks board` (a person) or `perry-task list --json` (a
   program). The frontmatter descriptions of `work/SKILL.md:3` and
   `goals/SKILL.md:3` are routing text; keep their trigger words.
4. **3c result § 11 R10's `.perry/config.md` mentions.** History lines stay,
   marked as history.

**Must not:** change code in `bin/` or `viewer/`, or change the schema, a
contract, a store, `ARCHITECTURE.md`, or any rule's meaning beyond the signed
substitution.

**Verification (3d):**
- `grep` census before and after, per file.
- `tests/test_ownership.py`, `tests/test_spec_scannability.py` and
  `tests/test_router_budget.py` green, with the new SHA shown.
- Mutations, each reddening a named test:
  - restore the old ownership row;
  - restore the old git-boundaries line without re-pinning;
  - grow `SKILL.md` past its budget.
- The full suite, run on the final commit.
