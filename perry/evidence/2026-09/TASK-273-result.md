# TASK-273 — result

- **Branch**: `coding/task-273-duplicate-ids`
- **Branched from**: `9c9670e` ("TASK-273 in_progress before dispatch") — the
  `main` tip named as the baseline.
- **Worktree cut correction**: the agent worktree was created at `d49964e`
  ("chore: consolidate test suite and project state"), ~140 commits behind
  `main`, where this spec does not exist. The branch was cut from `9c9670e`
  explicitly. Line numbers in the spec were taken at `548f206` and are still
  exact at `9c9670e` — `risk_records:737`, `by_id:748`, `seen:750`,
  `continue:759`, `ask_records:1362` — so nothing had to be re-derived.

## Reproduction, before anything was changed

### Direction 2 — REPRODUCES, exactly as specified

Store holding two records for `RX-001`, differing on `cleared`; board clean;
one ordinary `perry-task risk-add`:

```
before  {"id":"RX-001","risk":"first risk","status":"open","cleared":""}
        {"id":"RX-001","risk":"a stale duplicate","status":"cleared 2026-02-02","cleared":"2026-02-02"}
        {"id":"RX-002","risk":"second risk","status":"open","cleared":""}

after   {"id":"RX-001","risk":"first risk","opened":"2026-01-01","cleared":"2026-02-02","status":"open","order":0}
```

Exit code **0**. `RX-001` is `status: open` and now carries a `cleared` date
that belonged to the other record. `by_id` (`:748`) kept the LAST record for
the id; `risk_record`'s `if stored is not None and stored.get("cleared")`
carried its `cleared` onto the survivor's row.

### Direction 1 — DOES NOT reproduce as described, and the real defect is worse

The spec's mechanism is that the `seen` skip drops the second row, so "the
record it would have produced is not in the rebuilt set". **Measured over five
cases, that is true and harmless.** The second row with a given id produces no
record, but the record for that id is already in the set from the FIRST row, so
the record set is intact:

| case | board | store before | rc | records destroyed |
|---|---|---|---|---|
| C | `RX-001, RX-002, RX-002, RX-003` (exact duplicate row) | 3 | 0 | **none** |
| D | `RX-001, RX-002, RX-002(different prose), RX-003` | 3 | 0 | **none** |

What the duplicate destroys arrives one step later, and it is silent:

| case | board | store before | rc | stderr | destroyed |
|---|---|---|---|---|---|
| B | `RX-001, RX-002, RX-001` (3rd row's id mistyped) | `RX-001, RX-002, RX-003` | **0** | *(nothing)* | `RX-003 · "third, id mistyped as RX-001"` |
| E | same board | `RX-001, RX-002, RX-003` | **0** | *(nothing)* | `RX-003 · "the record that is about to be overwritten"` |

The chain: the duplicate makes `RX-003` absent from the board's **text**;
`mint_risk_id` reads that text (its own docstring names reissue as the failure
it fears, and defers the fix to "the day `risks.jsonl` exists" — that day was
`TASK-203`); `risk-add` therefore mints `RX-003` a **second** time and the live
stored record under that id is overwritten. `refuse_to_shrink` sees three
records become three. `substituted_away` joins on `REGISTER_IDENTITY["risks"] =
r.get("id")`, sees `RX-003` on both sides, and reports nothing. Every existing
guard is looking somewhere else and each is right about where it looks.

Case A is worth recording as the counter-example: with no growth, the duplicate
makes the derived set genuinely smaller and `refuse_to_shrink` refuses loudly.
**The dangerous shape is precisely a command that adds a row** — the count is
preserved and USER-906's invariant is silent by design.

### And `perry-lint` already does Deliverable 2's job

A duplicate id in the store is already reported today:

```
⚠ risks.jsonl [risk-store-badly-typed] 'RX-001' — `id` is RX-001, expected unique risk id.
  2 error(s)
```

That surface needed nothing. What it cannot do is survive a write: **the first
ordinary write launders the corruption.** The store is rewritten from the
collapsed set, the duplicate is gone, the wrong `cleared` stays, and the linter
has nothing left to report. So the remaining hole on the store side was never
the report — it was that the writer read a store the linter calls corrupt and
replaced it anyway.

## The fix

One report per side in `bin/perry_store.py`, and refusals at the choke points
that read them. Neither `seen` nor `by_id` was made cleverer; both are
unchanged, and now sit behind checked inputs.

| # | surface | site | what it refuses |
|---|---|---|---|
| 1 | `perry-task` (exit 1, writes nothing) | `register_change` | a repeated id on the board section, naming every id and both lines |
| 2 | `perry-task` (exit 1, writes nothing) | `load_register_records` | replacing a store that holds two records for one id |
| 3 | `perry-tasks` (exit 1, writes nothing) | `cmd_risks_write` / `cmd_asks_write`, ahead of the byte gate | the same board state on the explicit `--from-board` import |
| — | `perry-lint` | unchanged | still reports the corrupt store, byte for byte as before |

**Why each half got the surface it got**, in the refusal itself so the next
reader cannot unify them: *the linter is asked what is wrong with the store as
it stands, and this tool is asked to REPLACE it* — and a write that reads a
corrupt store launders it, leaving the wrong value behind with the duplicate
that explained it gone.

**Why the store-side refusal lives in `load_register_records`.** That
function's own docstring already forbids dropping a record it cannot read,
because "silently discarding a record would let the next write persist the
smaller set as truth". A store with two records under one id is a store one of
whose records the CALLER cannot read. Returning the list intact and letting
`by_id` collapse it one frame up would be this function dropping a record after
all, just not with its own hands.

**Why (3) exists.** `bin/perry-tasks` claims in two places that its byte gate
catches the duplicate-id class, measured on eleven inputs. Re-measured here: it
catches the duplicates whose **prose differs**. Two rows sharing an id and
carrying **identical cells** render back byte for byte, the gate has no
question to fail, and three board rows imported as two records at exit code 0.
A gate asked about bytes cannot be asked about counts. This is one more caller
of `risk_records` / `ask_records`, not a fourth `seen` site — the lines guarded
are still `:748` and `:759-761`.

### After the change, no record is lost in either case

Both refusals leave the store **byte-identical** — asserted, not assumed
(`test_the_record_the_write_would_have_destroyed_is_still_there`,
`test_an_ordinary_write_over_a_duplicated_store_is_refused`).

## Deliverable 3 — `perry/tasks.jsonl` is SAFE. No new row.

Three separate things make it safe, and none of them is care taken at a
duplicate site:

1. **Its `seen` set is in a VALIDATOR, not in a board-walking builder.**
   `perry_store.py:202-248` is `validate_records`, and `:238` — the
   "different-looking handling" the spec points at — is `elif tid in seen:`
   appending a **finding** (`expected: unique task id`) where the register
   builders write `continue`. It reports exactly where they skipped.
2. **No ordinary write rebuilds the task store from the board.** `## P0/P1/P2`
   is rendered output under ADR-007; `perry-task` mutates the record set and
   re-renders the board from it. There is no board-to-record derivation for a
   board duplicate to corrupt. The board-to-store direction exists only behind
   the explicit `perry-tasks write --from-board`.
3. **Its findings gate rather than advise.** `load_task_records` and `commit`
   both run `validate_records` and refuse, so a duplicated `tasks.jsonl` stops
   a write instead of being collapsed into one — verified end to end.

What TASK-273 changed is that the two id-keyed **registers** now behave the way
tasks already did.

## Out-of-scope registers, checked as the spec asked

- **`intake` is OUT, and it is not merely harmless.** `intake_records` has no
  `seen` set, no `by_id` and no id column — it enumerates positionally and
  keys `by_order` on the record's own `order`; `INTAKE_STORED` carries no `id`
  at all. Two `## Intake` rows for the same request on the same day is the
  ordinary shape of a thing filed twice, and it still writes. Declared out on
  both sides (`REGISTER_ID_KEYED`, and `None` in `REGISTER_SPEC`).
- **`cadence` has no store in `perry_store.py`** — `grep -n cadence
  bin/perry_store.py` returns nothing — so the two lines do not serve it.
- `:541` (the section walker) untouched, as bounded.

**One correction to the spec's Bound.** It states "3 `seen` sets on `548f206`".
`grep -n "seen" bin/perry_store.py` finds **ten** declarations — `:202, :541,
:750, :779, :856, :1066, :1143, :1377, :1404, :1476`. The three named are the
right three for this class; the others are validators (`:779, :1404`), plan
walkers (`:856, :1476`) and the intake pair (`:1066, :1143`). The count is
wrong, the scope it draws is not.

## Verification

**Control 1 — a board with no duplicates writes exactly as before.**
`perry-lint --root .` on this repository, before and after: `diff` is
**empty**, rc 0 → rc 0, `0 error(s), 26 warning(s)` both times. Re-checked
after every commit that touched a writer.

**Control 2 — a legitimately repeated value that is not an id is not caught.**
Two risks opened on the same day; two risks with the same status AND the same
sentence; two asks asked on the same date; two intake rows for the same request
on the same day; rows the table treats as layout. All write at rc 0.

**Mutation — 12 planted, 12 red, 0 green** at the final HEAD. Each reverts one
half to its pre-TASK-273 behaviour; each anchor is asserted **unique on the old
text** before the edit (a miss aborts the run rather than no-opping), each test
is required GREEN before mutation, `__pycache__` is cleared and the run waits
past the whole-second boundary, and every restore is verified with
`bin/perry-restore-check HEAD <path>` — against git's object store, never
against a snapshot the harness took.

**Two mutations came back GREEN first, and each was a real finding:**

- **`"intake"` added to `REGISTER_ID_KEYED`** — nothing went red. The mutation
  is inert: `INTAKE_STORED` has no `id`, so `duplicate_record_ids` returns `[]`
  for intake however the set is spelled. `REGISTER_ID_KEYED` is a second lock
  on a door the missing field already locks. Fine to keep, not fine to leave
  undefended — the exclusion is now asserted directly on both sides, and a
  second mutation (giving intake an id column in `REGISTER_SPEC`) confirms the
  board-side half bites.
- **`if not rid:` → `if rid is None:` in `duplicate_row_ids`** — nothing went
  red, and the first replacement test stayed green too. Two reasons, both
  worth recording: `strip_handle` only removes decoration, so prose in an ID
  cell comes back as prose and two different notes are two different ids; and
  the branch is **unreachable from any board**, because `markdown_tables`
  already drops a line with no first cell. It is now tested where it is
  reachable — directly, on a hand-built table — and the unreachability is
  stated in the test so the next reader does not rediscover it with a
  mutation. A third mutation (removing `strip_handle`) is now caught by a
  struck-out-duplicate test.

**Tests**: 3193 pass / 3193 total, 114 modules, tree guard clean, rc 0.
Baseline measured on `9c9670e` before any change: 3162 / 3162, 113 modules
(the baseline run's tree guard tripped on my own concurrent edit to this file,
not on a test — every test step was green).

## Two existing tests were changed, and why

Both asserted the byte gate's specific wording for a duplicate id. The
outcome each protects — exit 1, store byte-identical — is unchanged and still
asserted; what moved is which check speaks, because the specific diagnosis now
runs ahead of the general one.

- `test_asks_store.TestTheByteGateIsLoadBearingHere.test_the_duplicate_is_refused_before_a_byte_is_written`
  — now asserts the duplicate refusal, and still asserts "byte for byte"
  appears, so a reader is told the gate exists and what it cannot see. The
  render-level measurement of the same class
  (`test_a_repeated_user_id_is_caught_by_the_bytes`) is untouched and green.
- `test_risks_store.TestTheOneWayImport.test_a_section_the_records_cannot_reproduce_is_refused_by_row_and_cell`
  — its stated requirement is *name the ROW, not the line number*, because
  "line 23 differs" does not tell anyone which row was misread. Rather than
  weaken it, the new refusal was made to print each duplicate row's text, so
  `a duplicate somebody pasted` is still asserted in the output. Only the
  `column Risk` assertion is gone: the new refusal diagnoses by id and line,
  not by column.

Two further failures were housekeeping on the new module, both fixed:
`tests/durations.json` now carries a **measured** entry for it (three serial
runs, largest recorded, taken under `load1 25.4` and said so rather than
rounded away), and the diagnostic row preview joins with ` · ` and not ` | `,
because `tests/test_one_choke_point.py` correctly flagged a pipe-joined cell
list as a second table-row builder. That rule is right, and "it is only for an
error message" is how the second builder always starts.

## Files changed

- `bin/perry_store.py` — `duplicate_row_ids`, `duplicate_record_ids`,
  `__all__`, and the TASK-273 paragraphs on `risk_records` / `ask_records`
- `bin/perry-task` — `REGISTER_ID_KEYED`, `DUPLICATE_IDS_SHOWN`, the sixth
  `REGISTER_SPEC` element, the board refusal in `register_change`, the store
  refusal in `load_register_records`
- `bin/perry-tasks` — `refuse_duplicate_ids` and its two call sites
- `tests/test_duplicate_ids_are_refused.py` — new, 31 tests
- `tests/test_asks_store.py`, `tests/test_risks_store.py` — the two handovers
- `tests/durations.json` — the new module's measured entry
