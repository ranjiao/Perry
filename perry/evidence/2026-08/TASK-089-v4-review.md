# TASK-089 — V4 review: `perry-task` writes the store, not the board

Fresh-context round. Criteria: the row's `Deliverable` / `next_action` as
`bin/perry-task list --json` prints them, `perry/decisions/ADR-007-fields-are-typed-prose-is-not.md`,
and `perry/evidence/2026-08/TASK-088-renderer.md` (§ *What does NOT hold, and
belongs to TASK-089*).

**Everything destructive ran on copies.** The project was copied to
`…/scratchpad/rv089/base` (`tar` minus `.git`, `.claude`, `__pycache__`) and
each experiment ran in a fresh `cp -R` of it. Nothing in this checkout was
written except this file. The two mutated files under `§ F. What the tests
pin` were mutated in throwaway copies which were never reverted and never
merged; `__pycache__` was removed at copy time so no stale bytecode could
answer for the mutation.

The three surfaces the prompt requires: `python3 tests/parallel` — **53
modules · 1504 tests · green** (on the copy); `python3 bin/perry-lint` on this
checkout — **clean**; `python3 tests/parallel test_contract_invariance` —
**green**. The verdict below does not rest on any of them being red.

Ground already covered by the dispatching round is not re-run: the bad row
refused by name while its neighbour writes, 31/66 orders vs nulls with none at
`0`, the one-line diff, `diff` reporting identical after a write. All four
still hold in my copies. They are not what this round is about.

---

## A. Atomicity — the pair is not atomic, and the honest claim is still overstated

`commit()` states the guarantee twice, in the module docstring
(`bin/perry-task:17`) and in its own (`bin/perry-task:1626`): *"staged to temp
files and renamed (atomic on POSIX), so either both land or neither does."*
Four failures, each forced on a copy:

| what was made to fail | how | state left behind |
|---|---|---|
| store directory unwritable | `chmod a-w perry/` | **nothing written** — correct. Surfaced as an uncaught `PermissionError` traceback out of `lib.stage` |
| journal directory unwritable | `chmod a-w perry/journal/2026-08` | **nothing written** — correct, and the staged store temp was cleaned. Traceback again |
| `BOARD.md` unwritable | `chflags uchg perry/BOARD.md` | store + journal + event landed; board stale; **warning printed, exit 0**. Exactly as designed |
| event log unwritable | `chmod 444 .perry/events.jsonl` | store + journal + board landed; **warning printed, exit 0**. Exactly as designed |

The two derived artefacts behave as documented. The pair does not.

**A5 — the store lands without its journal line.** The two canonical files are
staged together and then renamed **one after the other** in a loop
(`bin/perry-task:1712-1717`). Two `os.replace` calls are two atomic
operations, not one, so anything that fails or interrupts between them leaves
the first landed and the second not. Forced two independent ways on copies:

```
# (a) the journal file cannot be replaced
chflags uchg perry/journal/2026-08/2026-08-19.md
python3 bin/perry-task status <an open row> --status in_progress --next "…"
  → PermissionError traceback
  → perry/tasks.jsonl   : status = in_progress      ← landed
  → journal 2026-08-19  : unchanged                 ← lost
  → BOARD.md            : unchanged (still not_started)
  → .perry/events.jsonl : no event
  → one orphaned tmp file left in perry/journal/2026-08/

# (b) no filesystem flags at all — a crash in the window
#     (copy patched: os.kill(os.getpid(), 9) after the store's rename)
  → identical outcome: store in_progress, journal line absent, board stale,
    no event, one orphaned tmp
```

This is the state the whole design exists to forbid — *"a stored record
without its journal line is exactly the state-vs-history divergence this tool
exists to remove, which makes a partial write there strictly worse than a
refusal."* It is now reachable, it is silent (a traceback names `os.replace`,
not the divergence), and the row is left claiming a status no journal line and
no event support.

The docstring's own history makes this the sharper defect rather than a
theoretical one: it already retired one version of this claim — *"Four
surfaces used to say 'none of the three if any would fail', which is stronger
and false"*. The replacement claim is weaker and still false.

**A6 — a failed stage is a traceback, not a refusal.** Rows 1 and 2 of the
table: `lib.stage` raising `PermissionError` propagates out of `main()`
uncaught (`main()` catches only `UnrenderableCell` and `Refused`). Nothing was
written, so the state is right and the message is wrong — and the same
docstring criticises the previous version for precisely this shape (*"an
uncaught traceback"*). Every other unwritable-path refusal in this tool says
*nothing was written*; these two say `Traceback (most recent call last)`.

**A7 — the failing rename orphans its own temp.** `bin/perry-task:1716` pops
the entry *before* attempting `os.replace`, so if that call raises, the popped
temp is no longer in `staged` and the `finally` clause cannot unlink it.
Observed in both A5 runs (`1` stray `.tmp` beside the target). The comment
directly above explains that pop-as-we-go exists to prevent an orphan; it
moves the orphan from the earlier file to the failing one.

---

## B. Row identity — the writer and the store do not agree what a row is

This is the finding I would fix first, because it puts values into the
projection that never reach the truth, and the phase's remaining rows
(090/092/094/095) inherit the store as given.

**Six live answers to "which `|` lines of this section are rows", with three
different stop rules:**

| site | rule |
|---|---|
| `Board.last_row` — `bin/perry-task:536-540` | stops at any non-blank non-`\|` line |
| `Board.rows` — `bin/perry-task:555-557` | stops at any non-blank non-`\|` line |
| `Board.task_tables` — `bin/perry-task:632-635` | stops at a non-blank non-`\|` line **unless** it starts with `#` or `>` |
| `Board.section_rows` — `bin/perry-task:824-828` | as `task_tables` |
| **`perry_store.plan`** — `bin/perry_store.py:280-283` | as `task_tables` — a fourth hand-written copy of the rule, not a shared one |
| **`Board.find`** — `bin/perry-task:653-660` | **never stops**; every `\|` line to the next `## ` heading |
| `Board.ensure_columns` — `bin/perry-task:720-721` | never stops |

`find()` is the writer's locator (and the row-scope gate's). `task_tables` +
`plan` are the store's reader and the renderer. They disagree, and both
disagreements produce silent damage.

**B1 — a write whose payload never reaches the store.** Copy, `## P2` given a
prose line and then a second table (the section walker stops at the prose;
`find()` does not):

```
python3 bin/perry-task status <that row> --status in_progress --next "moved by the writer"
  → perry-task: wrote <row> (status) → store + journal + BOARD.md + event
  → BOARD.md   : Status = in_progress, Next action = "moved by the writer"
  → tasks.jsonl: status = in_progress (from the EVENT, not the row),
                 next_action = ""            ← the value the write was about
                 group = "", order = null
  → perry-tasks diff : identical: true, rows_verbatim: [],
                       cells_the_store_and_board_disagree_on: []
  → perry-lint       : ✓ clean, 0 row(s) drifted
```

The canonical file lost the thing the command wrote; the projection kept it;
every reporting surface says the projection reproduces the store. Before this
task the canonical file was `BOARD.md` and this write was recorded correctly —
so this is a regression introduced by moving the write target.

**B2 — the store mints a record out of a markdown header row.** Copy, `## P2`
given an ordinary `### Deferred until the next phase` sub-heading and a
continuation table **with the same columns** (`task_tables` and `plan` do not
stop at `#`, so the second table's header line is read as a row):

```
python3 bin/perry-task status <an unrelated row> --status in_progress --next x
  → perry/tasks.jsonl now carries
    {"id": "ID", "title": "Title", "owner": "Owner", "group": "P2", "order": 11, …}
  → perry-lint       : ✓ clean — 0 row(s) drifted
  → perry-tasks diff : identical: true
```

98 records for 97 tasks, a fabricated id in the tracked truth file, and no
check anywhere reports it — the row is *in* the store, so it renders from the
store and `cells_verbatim` / `rows_verbatim` stay empty. (`rows_verbatim` did
catch the second separator line, `---`, which is how close the report gets.)
The variant where the second table has *different* columns is caught, but by
`table-columns`, i.e. by accident of shape rather than by the store's own
accounting.

TASK-088's evidence rests the honesty of this design on that accounting —
*"the report counts every cell the layout had to keep VERBATIM"*. The count
cannot see either B1 or B2.

---

## C. Decision 1 — the row-scope gate is bypassed by a duplicate id

`refuse_unstorable_status` resolves the row with `ctx["board"].find(tid)`
(`bin/perry-task:1575`), and `find()` returns the **first** matching line
(`bin/perry-task:653-660`). `cmd_list`, which the store is built from, takes
the **last**. So one id on the board twice — first row clean, second row
carrying the cell decision 1 exists for — splits them:

```
# copy: an existing P2 row duplicated, the copy given
#       Status = **迁移 done，占比目标 not_started**
python3 bin/perry-task status <that id> --status review --next "via the clean copy"
  → perry-task: wrote <id> (status) → store + journal + BOARD.md + event   ← NOT refused
  → tasks.jsonl : status = "",  next_action = "—"     ← the typed value never arrives
  → perry-tasks diff : identical: true, rows_verbatim: [],
                       cells_the_store_and_board_disagree_on: []
  → perry-lint       : 0 row(s) drifted
```

The gate approved a write that moved a row "from a state that does not exist"
and stored it as `status: ""` — the two things its docstring names as the
reason it exists. `perry-lint` does report `bad-enum` on the cell, which is the
board's shape, not this write; and a board carrying such a cell is exactly the
premise decision 1 was written for, so this is inside the case, not outside it.

**On the enumeration the prompt asked for:** `route`, `intake`,
`resolve-intake`, `intake-sweep`, `ask`, `answer`, `cadence-add`, `risk-add`,
`risk-clear`, `risk-migrate` all reach `commit()` and therefore the store, and
none of them passes the gate — correctly, since none moves a task row (each
was run against a board carrying an unstorable cell on a copy: all proceeded,
the bad row stored as `status: ""` each time, records unchanged in count).
Every command that *does* name a task row — `start`, `status`, `done`, `drop`,
`prioritize`, `stage`, `retitle`, `rung`, `evidence`, `depends` — is refused.
So the gate's coverage is right; its **row resolution** is not, and C above is
the one way through it I found.

Two further notes on decision 1, neither blocking:

- **The refusal has no tool-side exit.** It tells the user to *"give the row
  the one state it is actually in, or split it into the separate rows it
  already describes"*, and every command that could do either is refused on
  that row. The only way out is a hand edit to `BOARD.md` — the file ADR-007
  decision 2 has just declared rendered output — followed by `perry-tasks
  write`. The message should say so.
- `status_cells_the_store_cannot_hold` is computed on every write
  (`bin/perry-task:1605`) and appears only in `--json`. The human line prints
  `→ store + journal + BOARD.md + event` and nothing else, so on the project
  this decision was measured on, four rows are stored as `status: ""` on every
  write with no word said outside a payload.

---

## D. `order` — the type nothing validates kills the lint

Duplicates, gaps and negatives are all tolerated: a store hand-edited to carry
`order` `2` twice in one section, `-5`, and `99` produces no crash, and
`_order_drift` still reports the section (`sorted` is stable and both sides
sort the same id list, so a tie is resolved identically on both sides — it
cannot crash, and it also cannot see a swap between two rows that share an
order). A hand-inserted board row is adopted into the store on the next write
with a fresh `order`, and the section's other rows shift by one without being
reported — which is what `_order_drift` was built for and it works.

**A wrong-typed `order` does not degrade, it kills the run.** One record
hand-edited to `"order": "3"`:

```
python3 bin/perry-lint    → perry-lint: TypeError: '<' not supported between
                            instances of 'str' and 'int'      (rc 2, no findings, no --json)
python3 bin/perry-tasks diff → TypeError at bin/perry_store.py:330
```

`bin/perry-lint:2144` (`in_store = sorted(ids, key=lambda t: stored[t]["order"])`)
sorts a value read straight off disk, and it runs **after**
`check_store_drift`'s `except Exception` guard (`bin/perry-lint:2054`), which
covers only the `build()` call. That guard's own docstring is the reason this
counts: *"Four reachable store states used to kill the whole lint … The
sibling guard eight lines down states the rule this broke: one check may not
kill the lint."* TASK-089 added a nineteenth field and a sort over it, and the
fifth state was not enumerated. `perry/tasks.jsonl` is tracked now, so a merge
or a hand edit is how it arrives.

---

## E. Second writers of the truth, and which way drift is resolved

- **`bin/perry-tasks:196` writes `perry/tasks.jsonl` with `dest.write_text(...)`
  — no project lock and no staging.** Demonstrated on a copy: with
  `lib.project_lock` held by another process, `perry-task status` refused after
  10s while `perry-tasks write` completed immediately. So the canonical file
  has one writer that serializes and stages and one that does neither;
  `write_text` truncates before it writes, so an interruption there is the
  torn store, and a concurrent `perry-task` commit is last-writer-wins over the
  whole file. Two concurrent `perry-task` writes are fine — both landed, both
  events appended, board correct, `diff` identical — the lock does cover the
  read, the store write and the render.
- **The remedy `perry-lint` prints can destroy a committed write.** After the
  `BOARD.md`-unwritable case (§ A, row 3) the store is right and the file is
  stale; `store-drift` offers *"or run `perry-tasks write` to re-derive the
  store from the file"*, and running it silently reverted the row to
  `not_started` while the event log still records the transition. The message
  does not say which side is authoritative in which case; after a failed
  render only `perry-tasks render` is safe.
- **The writer never reads the store.** `store_records` derives from the board,
  so an edit to `perry/tasks.jsonl` — now a tracked file, so merges will make
  them — is reported by `perry-lint` and then silently discarded by the next
  unrelated `perry-task` write (verified: an owner edited in the store was gone
  after one `status` on another row, no warning, no event). Drift is resolved
  in the board's favour, silently, in the direction opposite to the one ADR-007
  decision 2 describes. This is consistent with the slice (TASK-090 is where
  the board reader goes) but it is not what "the store is the write target"
  reads like, and it is worth one sentence in the row.
- `bin/perry-migrate` is the only remaining direct writer of `BOARD.md`
  (`write_atomic` at `:1510`, restore/undo at `:1591`) and contains **no
  reference to `tasks.jsonl`** — a migration leaves the store stale by
  construction, and its restore point cannot restore it. No other tool writes
  the board.
- Every commit resets `perry/tasks.jsonl`, `BOARD.md` and the journal file to
  **0600**, because `lib.stage` uses `mkstemp` (`bin/lib/__init__.py:72`) and
  never restores the target's mode. Pre-existing for the board and journal;
  new for the tracked store (`git ls-files -s` says `100644`, disk says
  `-rw-------`). Cosmetic on one machine, not in a shared checkout.

---

## F. What the tests pin

`tests/test_store_is_the_write_target.py` is 26 tests and it does bite — two
control mutations went red immediately: neutering the `raise` in
`refuse_unstorable_status`, and making `record()` store `0` instead of `None`
for a row off the board. Two mutations did **not**:

1. **The staged pair replaced by two independent `lib.write_atomic` calls** —
   the mechanism `commit()` calls *"the whole guarantee here … not expressible
   as two `write_atomic` calls"* — and the **entire suite stays green: 53
   modules, 1504 tests**. Nothing in this repository pins the atomicity of the
   canonical pair. `TestTheStoreAndTheJournalAreThePair` asserts the happy path
   and the *event* failing; the journal failing, which is the case that breaks
   the guarantee, is not tested.
2. **`_order_drift` made to return `[]` unconditionally** (`bin/perry-lint:2135`)
   — `test_store_drift` and `test_store_is_the_write_target` both stay green.
   No test in `tests/` mentions the finding it emits; the docstring cites
   `test_store_drift § test_a_row_the_store_never_saw_is_reported` as the test
   that found the amplification bug, and that test does not assert the fix.

---

## What I did not check

- **No second project.** Everything ran on copies of Perry's own board. The
  four real `off_enum_status` cells that decision 1 was measured against live
  on gimegime-pmo and I did not copy it; C is demonstrated on a synthetic
  duplicate of one of Perry's rows instead.
- **No CRLF board, no non-UTF-8 board, no localized (`| 状态 |`) board** through
  the write path; `FIELD_BY_COLUMN`'s resolution through `ops.norm` was read,
  not exercised.
- **No Windows path** and no filesystem other than APFS. The A5 failures were
  forced with `chflags uchg` and with a SIGKILL; NFS/SMB rename semantics
  untested.
- **`--dry-run` beyond the refusal preview**, and the `perry-conform` enforce
  gate interaction with the new refusal.
- **`answer` / `cadence-done` / `risk-clear` against a board with an unstorable
  cell in the section they write** (I ran them against a board whose bad cell
  was in a task table, not in their own section).
- I did not attempt to price how often a board carries two tables under one
  `##` heading. B1 and B2 are demonstrated, not surveyed.
- The event-log format, `mint_id`, and everything the store does not touch.

---

=== VERDICT ===
task: TASK-089
rung: V4
result: FAIL
criteria: the row's Deliverable/next_action via `perry-task list --json`;
          ADR-007; perry/evidence/2026-08/TASK-088-renderer.md § What does NOT
          hold
checked: all four failure modes forced on copies (read-only store dir, journal
         dir, uchg BOARD.md, unwritable event log); a SIGKILL and a uchg
         journal in the rename window; two concurrent writes; the lock vs
         `perry-tasks write`; every writer subcommand against a board carrying
         an unstorable Status cell; order duplicated/negative/gapped/mistyped;
         six section-row scanners enumerated; four mutations, two green
not-checked: no second project (gimegime-pmo's four real cells); no CRLF,
         non-UTF-8 or localized board through the write path; no Windows; no
         non-APFS filesystem; `answer`/`cadence-done`/`risk-clear` against a
         bad cell in their own section
proof: bin/perry-task:1712-1717 renames the store and the journal in two
       sequential `os.replace` calls, so a failure or crash between them leaves
       the store written and the journal line lost (reproduced twice; the whole
       1504-test suite stays green with the staged pair removed). And
       bin/perry-task:653-660 (`find`, no stop) disagrees with
       bin/perry_store.py:280-283 and bin/perry-task:632-635 (stop at prose,
       swallow `#`) about which lines are rows: a write to such a row stores
       `next_action: ""` while the board shows the typed value, a second
       table's header row is stored as a record with `id: "ID"`, and
       `perry-tasks diff` reports `identical: true` with `perry-lint` clean in
       both cases. bin/perry-task:1594 resolves the gate's row with the first
       `find()` match while the store takes the last, so a duplicated id lets a
       write the gate exists to refuse through unrefused.
=== END VERDICT ===
