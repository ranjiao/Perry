# TASK-235 — `DECISIONS.md` stops existing; `perry-decide list` is the surface

> Branch: `coding/task-235-decisions-index`, forked from `main` at `ee0b36a`.
> DESIGN-013 § 5.3 and User Decision 3, answered 2026-08-29: **delete it.**
> Every synthetic id below is backticked on purpose: `bin/perry-diagnose`
> reads a bare `ADR-0NN` in `evidence/` as a dangling reference, measured on
> this tree before this file was written.

## 1 · What changed

**Deleted.** `perry/DECISIONS.md`, `decide/state/DECISIONS_TEMPLATE.md`, and
the four fixture indexes (`tests/fixtures/sample-project`,
`sample-project-zh`, `witness-project` — see § 6, they were not all pure
projections).

**`bin/perry-decide`** — the writer. `render_index` and `index_rows` are gone;
`bootstrap` creates `decisions/` and nothing else; `new`, `supersede` and
`status` write only the ADR body they are about. `read_adrs` is now
`parsers.read_adr_records` rather than a second copy of the same reader (§ 3).
`mint_id` reads the files alone (§ 2). The `list` payload loses three
`conformance` keys and the contract goes to `perry-decide/list/2.0` (§ 4).
The human-readable `list` output now prints `missing_type` and
`off_enum_status`, which were reachable only through `--json` — it used to
print the two index divergences and nothing else, and dropping half a payload
on the surface that is now the only surface is the same defect one layer up.

**`viewer/parsers.py`** — the reader. `parse_decisions(text)` parsed the
`## Active` table of the index; it now takes the state root and reads
`decisions/ADR-*.md`. **This one was mandatory, not tidying**: leaving it would
have made `perry-state`'s `decisions.count` zero on every project forever,
which is verbatim the defect `bin/perry-decide`'s own docstring says the tool
was built to end. Verified equal, field by field, against the old reader on the
old file — § 6.

**Schema and contracts.** `claims[path=DECISIONS.md]` and
`files[id=decisions]` removed from `schema/state-schema.json`; the
`.perry/conformance.md` declaration row removed;
`schema/decide-list-contract.md` rewritten and given a `2.0` changelog row.

**Docs.** `SKILL.md`, `decide/SKILL.md`, `decide/reference/decisions.md`,
`work/SKILL.md` and four `work/reference/` pages, `goals/SKILL.md` and two
`goals/reference/` pages, four root `reference/` pages, `bin/README.md`,
`packs/software-ops/architecture.md`, both READMEs, and the two `work/state/`
templates now name `decisions/` or `perry-decide list`.

**No replacement index, under any name.** DESIGN-013 § 4.1 says the markdown
link surface into `decisions/ADR-*.md` is given up and that the implementing
row must not quietly re-add it. `tests/test_decide_writer.py §
TestNothingWritesAnIndex` is that sentence as a test, and it is written as
*"after this command the only files that exist are ADR bodies"* rather than
`assertFalse(DECISIONS.md.exists())` — a guard shaped round one filename is
satisfied by `ADRS.md`. Mutation 4 in § 5 plants exactly that and it goes red.

## 2 · The `mint_id` contract answer

**`perry-decide` reissues a deleted ADR number. `perry-task purge` does not.
The two tools disagree, and this one is the weaker.** Measured, not reasoned:

```
$ perry-decide bootstrap --root .          # creates decisions/ only
$ for i in 1..10: perry-decide new …       # ADR-001 … ADR-010
$ perry-decide new eleven --title Eleven --type Process
perry-decide: wrote ADR-011
$ ls DECISIONS.md
ls: DECISIONS.md: No such file or directory     ← minted with the index absent
$ rm decisions/ADR-011-eleven.md
$ perry-decide new twelve --title Twelve --type Process
perry-decide: wrote ADR-011                     ← REISSUED
```

`bin/perry-task § minting_records` takes the opposite rule for `TASK-` ids:
`purge` removes the record and `.perry/events.jsonl` keeps the number,
*"retired, not freed"*, because a reissued id inherits the dead row's timeline.

**`perry-decide` cannot follow that rule today and TASK-235 does not make it.**
The rule needs an append-only log and this lane writes no events at all — there
is no `.perry/events.jsonl` line with `perry-decide` on it. Retiring an ADR
number means teaching the lane to write events first, which is a lane-shaped
change and its own row. The exposure is smaller than `perry-task`'s: there is
no `perry-decide purge`, so an ADR leaves `decisions/` only when a human
deletes the file, and nothing resolves ADR ids against a log. It is still a
disagreement between two minters in one project, and it is now *stated* — in
`mint_id`'s docstring and in
`tests/test_decide_writer.py §
TestMintingReadsTheFilesAlone.test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge`,
whose failure message says what to change and where if this ever becomes false.

## 3 · TASK-214 — closed, and it was worse than it read

TASK-214 is **closed by this change**. Nothing survives of the `max(files ∪
index)` shape: there is no index, `mint_id` reads `read_adrs` and returns.

What the row does not say, and this tree does: **the union was not merely
self-erasing, it made reissue non-deterministic.** Measured on `main`'s
`bin/perry-decide` at `ee0b36a`, in a throwaway project:

```
files: ADR-001 … ADR-010, ADR-012, ADR-013
$ rm decisions/ADR-013-thirteen.md
index still names ADR-013?  1
$ perry-decide status ADR-001 --status archived    # an UNRELATED write
after that write, index names ADR-013?  0          # render_index rebuilt it
$ perry-decide new fourteen --title Fourteen --type Process
perry-decide: wrote ADR-013                        ← REISSUED anyway
```

So `main` reissued too. The union bought exactly one command of memory, and
whether an id came back depended on how many writes happened in between —
which is worse than not remembering, because nobody could say which case they
were in. After this change the behaviour is one thing, always, and § 2 names
it.

**A second thing closed on the way, which TASK-214 did not name.** `cmd_new`
stamps `> Status: active` into every ADR it writes, and nothing bound that
literal to `enums.decision_status`. The refusal that existed came from
`render_index` asking `statuses()` for its count line — an accident of the
renderer, and deleting the renderer took it. `bin/perry-decide § BORN_STATUS`
is that binding stated where the value is written; mutation 7 proves it.

## 4 · The contract: `perry-decide/list/2.0`

`conformance` loses `index_present`, `indexed_without_file` and
`filed_without_index_row`. Each compared `DECISIONS.md` against `decisions/`;
with one side of every comparison deleted they could only report a constant,
and a conformance field that cannot vary reads to a consumer as a check being
performed.

`schema/decide-list-contract.md § Adding a status is not a break` names the
break in the contract's own words — *"renaming or removing a key, or narrowing
a documented field"* — so this is a **major**, and the changelog carries a
`2.0` row saying what a consumer of the three should read instead.

Two baselines had to move with it and **neither was regenerated wholesale**:

- `tests/fixtures/contract-shapes.json` — only the `perry-decide/list` entry
  was spliced. Keys gone: the three. Keys added: `semantics` (TASK-205's
  addition, which the fixture had never been re-recorded for). No type moved.
- `tests/fixtures/contract-key-parity.json` — only the `perry-decide/list`
  entry, re-keyed `1.1` → `2.0`. **A `--record` was run and then discarded**:
  it also rewrote `perry-task/list/1.18`'s `emitted` from 126 to 115 and
  populated its `not_observable`, drift no test in that module asserts on. That
  is a finding for someone else's row (§ 8) and absorbing it here would have
  been the golden-file regeneration `test_contract_invariance`'s own docstring
  refuses.

`test_contract_invariance § test_the_major_version_did_not_move` compares the
recorded major against the live one, so re-recording is the only way to get it
green after a legitimate bump — and re-recording is exactly what that module
says must not be how a break is absorbed. So the bump got a door that a
re-record cannot open: **`test_the_shipped_version_is_recorded_in_its_own_changelog`**
requires the version a tool ships to appear in its own contract page's
Changelog. It is standing rather than transitional — it fires on every run for
all three contracts, not only across the bump — and mutation 9 proves it.

## 5 · Mutations

Every one: anchored by line number, old text asserted before replacing,
`__pycache__` cleared, 1.2 s past the whole-second boundary either way,
restored with an `md5` check that printed `OK`. Harness:
`scratchpad/t235/mutate.py`. A mutation that survived would exit 5; none did.

| # | Anchor | Mutation | Named test that went red |
|---|---|---|---|
| 1 | `bin/perry-decide:379` `write_atomic(path, body)` | `new` writes `DECISIONS.md` again | `test_decide_writer.TestWriting.test_ids_are_minted_and_the_files_are_the_only_output` (+6 more) |
| 2 | `bin/perry-decide:288` `d.mkdir(parents=True, exist_ok=True)` | `bootstrap` writes an index again | `test_decide_writer.TestTheBootstrapThatDidNotExist.test_bootstrap_creates_the_directory_and_no_file` (+8) |
| 3 | `bin/perry-decide:418` `_flip(sr, args.id, "superseded", args.new)` | `supersede` writes an index again | `test_decide_writer.TestNothingWritesAnIndex.test_supersede_writes_no_index` (only) |
| 4 | `bin/perry-decide:435` `_flip(sr, args.id, args.status)` | `status` writes **`ADRS.md`** — the index under another name | `test_decide_writer.TestNothingWritesAnIndex.test_status_writes_no_index` (only) |
| 5 | `bin/perry-decide:254` `seen = {…read_adrs(state_root)…}` | `mint_id` reads an index instead of the files | `test_decide_writer.TestReadingIsTolerant.test_ids_are_minted_above_a_hand_added_file` (+4) |
| 6 | `bin/perry-decide:457` `"off_enum_status": …` | the three removed `conformance` keys come back | `test_decide_writer.TestListContract.test_the_three_index_keys_are_gone_and_stay_gone` (+2, across 2 modules) |
| 7 | `bin/perry-decide:345` the `BORN_STATUS` check (6 lines) | the enum binding on the status a new ADR is born with is removed | `test_decide_status_enum.TestOneBinding.test_the_status_a_new_adr_is_born_with_is_one_the_schema_declares` (+1) |
| 8 | `viewer/parsers.py:2671` `for r in read_adr_records(state_root)` | the snapshot's ADR reader returns nothing | `test_project_root_resolution.TestPerrysOwnConfiguration.test_the_snapshot_off_perrys_own_project_root_is_not_empty` (+2 modules) |
| 9 | `bin/perry-decide:107` `LIST_CONTRACT` | version bumped to `2.1` with no changelog row | `test_contract_invariance.TestNothingIsRemovedOrRetyped.test_the_shipped_version_is_recorded_in_its_own_changelog` (only) |

Mutations 3, 4 and 9 each go red **alone**, which is the answer to *"a guard
that can be deleted with the suite unchanged is not a guard"*: nothing else in
2,900 tests catches those three.

## 6 · Findings

**A · The index was not a pure projection in every project, and DESIGN-013
§ 5.3's "Nothing is lost by deleting it" is true of Perry and not in general.**
For Perry's own record it is exactly true — the old index reader and the new
file reader were run side by side over `perry/decisions/` and returned the same
ten ADRs with the same id, title, type, date and path. The single difference:
`sunset_or_notes` was `"—"` and is now `""`, because the em dash was the
*rendering's* placeholder for empty and the old parser read it back as data.
Nothing consumes that field except `perry-state § expired_sunsets`, where
`days_since` returns `None` for both.

But `tests/fixtures/sample-project`'s ADR files carried **only** `> Status:
active` — their `Type`, `Date` and sunset lived in the index and nowhere else,
and `tests/fixtures/sample-project-zh` had an index and **no `decisions/`
directory at all**. Deleting the file would have destroyed those fields. I
rebuilt the ADR bodies from the index rows before deleting (the fixtures now
model a project whose files are the record), but **for a real project in the
same state there is no migration step and nothing warns.** `perry-decide`
always rendered the index from the files, so a project that only ever used the
tool is safe; a project that hand-edited it (which its own header forbade) or
adopted Perry through `decide/reference/decisions.md § Migration` can be in the
fixtures' state. That is a row, not something to fix here.

**B · `perry-decide` no longer takes an ADR-004 conformance gate, and that is a
loss rather than a simplification.** `DECISIONS.md` was the only file this tool
wrote that `schema/state-schema.json § files[]` gives a shape. `decisions/ADR-*.md`
has no `files[]` entry and never had one, so `perry-conform.verdict` returns
`absent` for it and `absent` passes — a gate on it could not fire, which this
project removes on sight. A gate on `design/*.md` would be a gate on a file
this tool does not write, which `bin/perry-goals § main` names as the mistake in
so many words. So the gate is removed and named rather than faked. Restoring it
means giving `decisions/ADR-*.md` a `files[]` shape — new claim surface, its own
row, and `.perry/hook.md` calls that a high-stakes operation.

Two consequences already visible in the suite: `test_conformance`'s
per-file-not-per-project test was written on `perry-decide`/`DECISIONS.md` and
is now written on `perry-goals`/`OKR.md`, and its § 8
(*"a file that does not exist yet is not a stranger's file"*) had used
`perry-decide bootstrap` as **the one shipped case of a tool creating the very
file it gated on**. There is no stand-in — `perry-task` refuses on a missing
board, `perry-goals link` on a missing register, `perry-goals commit` on a
missing `OKR.md` — so those two now call `verdict`/`gate` directly. The property
survives; the end-to-end delivery of it does not.

**C · The web link surface is gone and nothing replaces it, exactly as
DESIGN-013 § 4.1 accepts.** A reader browsing this repository lands in
`perry/decisions/` and reads a directory listing of ten filenames, which do
carry the slug. What is lost is status, type, date and the active/historical
split at a glance. I did not re-add an index and I am not recommending one —
recording it because § 4.1 asks for it to be reported if it matters.

**D · A content grep cannot see a file NAMED `DECISIONS.md`.** Four fixture
indexes and two shipped scaffolds were invisible to `grep -rn 'DECISIONS.md'`
because nothing inside them contains the string. `find . -name 'DECISIONS*'`
found them. The V4 check as written would have passed over the fixtures.

**E · `tests/fixtures/contract-key-parity.json` has drifted from live on
`perry-task/list/1.18`** in fields no test in that module asserts — `emitted`
126 vs 115, and `not_observable` empty vs five `tasks[].depends_on_resolved[]`
keys. Not mine, not touched, reported.

## 7 · Baselines, by runner and tree

| Tree | Runner | Result |
|---|---|---|
| `coding/task-235-decisions-index` at `ee0b36a` (= `main`, before any edit) | `bash tests/run` | **98 modules · 2882 tests · 3 failures** |
| this branch, after the change | `bash tests/run` | see § 7.1 |

The three baseline failures, all pre-existing and unrelated:

- `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository` — `2 != 0`. Reconciles against the LIVE board; this tree carries different intake rows.
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` — `['ACTION-7', 'D009-1', 'D010-2', 'PROJ-003', 'SPEC-007']`.
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`.

`unittest discover` was **not** run on either tree — see § 8.

### 7.1 · After

FINAL_RUN_PLACEHOLDER

## 8 · What I did not do, and what I could not verify

- **`unittest discover` was not run**, on either tree. The machine carried five
  other agents' full suites throughout (load average 38–41) and `tests/run`
  alone took 763 s against the baseline's 576 s. The row's brief says that
  runner shows 3 more failures from a module-double-import artefact in
  `test_risks_store`; I did not confirm that number on this tree, and I am not
  reporting it as if I had.
- **`viewer/parsers.py` is on another agent's list and I edited it anyway.**
  Reported here as the brief asks. The edit is contained — the
  `# ── DECISIONS.md ──` section is replaced by a `# ── decisions/ADR-*.md ──`
  section, and two lines in `load_state` — but it is not small, because the
  tolerant ADR header reader moved down into it from `bin/perry-decide` rather
  than being copied. Leaving a copy in each would have been the second
  implementation of one reader, which is the defect `split_row` reached six
  copies of before TASK-234 found the last one. **`bin/perry-goals` also has two
  lines changed** (one docstring sentence, one dead `HANDOFF` key); both are
  one-word removals of `DECISIONS.md` and neither touches behaviour.
  `bin/perry-task`, `bin/perry-state` and `bin/perry-conform` are untouched.
- **`grep -rn 'DECISIONS.md'` does not return zero over `bin/`, `tests/`,
  `schema/`, `reference/`, `templates/` and the `SKILL.md`s.** It returns 47,
  and every one is deliberate. By category: my own explanatory notes recording
  what was deleted and why (`bin/perry-decide` 6, `bin/README.md` 6,
  `schema/decide-list-contract.md` 3, `viewer/parsers.py` 3,
  `tests/test_decide_writer.py` 3, and one each in `test_contract_invariance`,
  `test_row_integrity`, `test_i18n`); historical narrative in test docstrings
  about defects that happened (`tests/test_ownership.py` 8,
  `test_procedures_call_the_tool.py` 2, `test_conformance.py` 2); and
  **foreign-project references, which are live and correct** —
  `bin/perry-diagnose`'s `DECISION_NAMES` and its `FIT-02` / `TRK-04`
  prescriptions (4), `reference/project-archetypes.md`'s three-file floor (2),
  `templates/{ops,software}/{AGENTS,STATE}.md` (4),
  `tests/test_diagnose.py`'s foreign fixtures (3),
  `decide/reference/decisions.md § Migration: old monolithic DECISIONS.md`,
  and one fixture filename in `test_heading_defines.py`. The foreign ones are
  correct under DESIGN-013 § 5.1 itself: a project with no store has no schema,
  so a document is where its decisions belong. `bin/perry-diagnose` and
  `reference/project-archetypes.md` now say so in place, so the next reader
  does not "fix" them.
- **`.perry/events.jsonl`, `perry/BOARD.md` and `perry/tasks.jsonl` still name
  the file and I did not touch them** — the PMO owns those.
- **I did not update the board or `perry/tasks.jsonl`.**
- **The `bin/README.md` conformance transcript is kept verbatim as history.** It
  was measured on 2026-08-20 against `perry-decide bootstrap`, whose gate this
  row removed, so those exact commands cannot be re-run. I first restated it
  against `perry-goals` and reverted that: a measurement quoted against a
  command that can no longer produce it is a measurement nobody took. It is
  labelled as history and the property it demonstrates is the gate's.
- **I did not verify the viewer's HTML rendering of ADRs.** `snap.adrs` is
  consumed by `bin/perry-state` (`decisions.count` / `last` /
  `expired_sunsets`, all checked) and by a `__main__` print in `parsers.py`;
  `grep` found no other consumer, and `sunset_or_notes` has none at all.
