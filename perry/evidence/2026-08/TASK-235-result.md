# TASK-235 — `DECISIONS.md` stops existing; `perry-decide list` is the surface

> Branch: `coding/task-235-decisions-index`, forked from `main` at `ee0b36a`.
> Commit: `0179c02` — 61 files, +1394 / -800.
> DESIGN-013 § 5.3 and User Decision 3, answered 2026-08-29: **delete it.**
> Every synthetic id below is backticked on purpose: `bin/perry-diagnose`
> reads a bare `ADR-0NN` in `evidence/` as a dangling reference, measured on
> this tree before this file was written.

## 1 · What changed

**Deleted.** `perry/DECISIONS.md`, `decide/state/DECISIONS_TEMPLATE.md`, and
the four fixture indexes (`tests/fixtures/sample-project`,
`sample-project-zh`, `witness-project` — see § 7 A, they were not all pure
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
old file — § 7 A.

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
satisfied by `ADRS.md`. Mutation 4 in § 6 plants exactly that and it goes red.

## 2 · Finding 1 — two tools disagree about whether an id can be reissued

**The most important thing this row produced, and it is DECLARED, not fixed.**
Somebody other than me should decide whether it is acceptable.

**`perry-decide` reissues a deleted ADR number. `perry-task purge` does not.**
An ADR id is an address — `perry/evidence/`, `perry/design/` and the ADR
bodies cite each other by it — so a reissued number means **two different
decisions can share one address**, and a citation written before the delete
resolves to the decision written after it. Nothing in the tree detects that.
Measured, not reasoned:

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

**The disagreement is between two tools over one contract**, and the contract
is `perry-task`'s: *an id, once issued, is never issued again.*
`bin/perry-task § minting_records` states it — *"a purged number is retired,
not freed"* — and gives the reason in the same breath: `.perry/events.jsonl`
is append-only and still carries the dead record's `add`, `drop` and `purge`,
so a new row wearing that number would inherit a timeline that is not its own.
Every word of that applies to an ADR except the mechanism.

**`perry-decide` cannot follow that rule today and TASK-235 does not make it.**
The rule needs an append-only log and this lane writes no events at all — there
is no `.perry/events.jsonl` line with `perry-decide` on it. Retiring an ADR
number means teaching the lane to write events first, which is a lane-shaped
change and its own row. The exposure is smaller than `perry-task`'s: there is
no `perry-decide purge`, so an ADR leaves `decisions/` only when a human
deletes the file, and nothing resolves ADR ids against a log. **That is a
reason it can wait, not a reason it is acceptable** — that call is not mine to
make and this row does not make it. It is now *stated* — in
`mint_id`'s docstring and in
`tests/test_decide_writer.py §
TestMintingReadsTheFilesAlone.test_a_deleted_adr_number_is_reissued_and_that_disagrees_with_purge`,
whose failure message says what to change and where if this ever becomes false.

## 3 · Finding 2 — TASK-214 is closed, and the defect was larger than filed

**Nothing survives.** There is no index; `mint_id` reads `read_adrs` and
returns. TASK-214 as filed is closed by this change.

**The row under-described its own defect, and that is the part worth keeping.**
It reads as *"the departed half erases itself"* — a redundant source going
quiet. What was there was worse: **reissue was NON-DETERMINISTIC.** The union
`max(files ∪ index)` gave a deleted id exactly one command of memory, because
the very next write re-rendered the index *from the files* and dropped the row
that was holding the number. So whether a deleted id came back depended on
**how many unrelated writes happened in between**. Nobody looking at a project
could say which case they were in, and the same sequence with one extra
`status` flip in it gives the opposite answer.

Reproduction, on `main`'s `bin/perry-decide` at `ee0b36a`, in a throwaway
project:

```
files: ADR-001 … ADR-010, ADR-012, ADR-013
$ rm decisions/ADR-013-thirteen.md
index still names ADR-013?  1
$ perry-decide status ADR-001 --status archived    # an UNRELATED write
after that write, index names ADR-013?  0          # render_index rebuilt it
$ perry-decide new fourteen --title Fourteen --type Process
perry-decide: wrote ADR-013                        ← REISSUED anyway
```

So `main` reissued too — it just needed one more command to do it. After this
change the behaviour is one thing, always, and § 2 names what that one thing
is. A row that closes by showing the defect was bigger than filed is worth
more than one that closes by meeting its own description, which is why this
paragraph is here and not only in the commit message.

**A second thing closed on the way, which TASK-214 did not name.** `cmd_new`
stamps `> Status: active` into every ADR it writes, and nothing bound that
literal to `enums.decision_status`. The refusal that existed came from
`render_index` asking `statuses()` for its count line — an accident of the
renderer, and deleting the renderer took it. `bin/perry-decide § BORN_STATUS`
is that binding stated where the value is written; mutation 7 in § 6 proves it.

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
all three contracts, not only across the bump — and mutation 9 in § 6 proves it.

## 5 · Finding 3 — `viewer/parsers.py` had to change, and the hunks, for `coding/task-050-header-index`

**Why it was mandatory rather than tidying.** `load_snapshot` read
`DECISIONS.md` and parsed its `## Active` table into `snap.adrs`.
`bin/perry-state` builds `decisions.count`, `decisions.last` and
`expired_sunsets` from that list. Delete the file and leave the reader, and
every project reports `decisions.count = 0` forever — **which is verbatim the
defect `bin/perry-decide`'s own module docstring says the tool was built to
end.** It would have been a silent zero, not an error: the exact "a check that
cannot fail on the thing it names" shape this project has caught six times.
Mutation 8 in § 6 is that regression, planted, and three modules go red.

**Exactly what moved. Three hunks, and the big one is a whole-section
replacement rather than edits inside it:**

| Hunk | Old | New | What |
|---|---|---|---|
| `@@ -2550,50 +2550,129 @@` | the `# ── DECISIONS.md ──` section: `parse_decisions(text)` **only** | `# ── decisions/ADR-*.md ──` section: `ADR_ID_RE`, `adr_header_fields(text)`, `read_adr_records(state_root)`, `parse_decisions(state_root)` | the section is replaced whole |
| `@@ -3860,7 +3939,6 @@` | `decisions_text = read(root / "DECISIONS.md")` | *(line removed)* | one deletion in `load_snapshot` |
| `@@ -3934,7 +4012,7 @@` | `adrs=parse_decisions(decisions_text) if decisions_text else []` | `adrs=parse_decisions(root)` | one line, `load_snapshot` |

Nothing else in the file is touched: `parse_board`, `parse_okr`,
`parse_phase`, `parse_linkage`, `parse_top_risks`, `walk_*`, `split_row`'s
callers and `resolve_state_root` are byte-identical to `main`.

**The one place it can collide with TASK-050, and how to resolve it.** The
deleted `parse_decisions` contained exactly two header/table call sites —

```python
in_active = heading_is(line[3:].strip(), "Active")     # old line 2562
cells = split_row(line)                                # old line 2572
```

— and **both are inside the replaced section**. If `coding/task-050-header-index`
converted either of them among its 16 header sites, that conversion is moot
here: **take the deletion.** The new reader parses `> Key: value` frontmatter
and has **zero** `heading_is`, `split_row` or header-normalization calls
(grepped, § 6 F). TASK-050's other sites are in functions this branch does not
touch, so the rest of that branch merges clean. The two `load_snapshot` hunks
are single lines and will not conflict unless TASK-050 also edits
`load_snapshot`'s local reads.

**Why the reader moved down here instead of staying in `bin/perry-decide`.**
`perry-decide` carried a tolerant ADR-header parser while `parsers.py` carried
a table parser for the *rendering* of the same records — one record, two
readers, bound by nothing. With the table gone I could have left a copy in
each. `split_row` reached **six** implementations before TASK-234 found the
last one; this is the same defect caught at two. `bin/perry-decide` now does
`read_adrs = P.read_adr_records` and carries no parser of its own.

## 6 · Mutations

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

### 6.1 · Three of the nine go red ALONE, and one of them is the whole decision

Mutations **3, 4 and 9** each go red with **exactly one** failing test in the
whole suite. That is the answer to *"a guard that can be deleted with the suite
unchanged is not a guard"*: delete any of those three and nothing else in
~2,900 tests notices the defect it names.

**Mutation 4 is the one that keeps the decision honest after I am gone.** It
re-adds the index as **`ADRS.md`** — a different filename, same artefact — and
the test that catches it is:

> `tests/test_decide_writer.py §
> TestNothingWritesAnIndex.test_status_writes_no_index`

with the message it printed under mutation:

```
after `status` the decide lane left ['ADRS.md']. Its whole record is
`decisions/ADR-*.md`; DESIGN-013 § 4.1 forbids re-adding an index under
any name.
```

DESIGN-013 § 4.1 accepts the loss of the web link surface **and warns in the
same paragraph that the implementing row must not quietly re-add an index to
avoid it**. A guard written the obvious way —
`assertFalse((root / "DECISIONS.md").exists())` — is satisfied by `ADRS.md`,
`INDEX.md` or `decisions/README.md`, so it would have permitted exactly the
move the design forbids. `TestNothingWritesAnIndex` instead asserts the
**complete set of files each write command may leave behind** (ADR bodies, and
nothing else), which is why it names no filename and catches all of them. Its
five members cover `bootstrap`, `new`, `new --supersedes`, `supersede` and
`status` — every command in the tool that writes.

## 7 · Findings

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

**G · `main` moved while this branch was open, and both overlapping files
merge clean.** The fork point is `ee0b36a`; `main` is now `7f934d5` (TASK-095
round 6, TASK-050 round 8 evidence, TASK-203 round 4, and a dispatch record).
Two files are touched by both: `bin/perry-diagnose` — mine at `@@ -129` and
`@@ -920`, main's at `@@ -1596`, `@@ -1903`, `@@ -2143`, `@@ -2189` — and
`bin/perry-goals` — mine at `@@ -52` and `@@ -613`, main's at `@@ -2161` and
`@@ -2172`. No hunk overlaps. This branch is **61 files, +1505 / -800 against
its fork point**; measured with `git diff $(git merge-base main HEAD)..HEAD`,
because `git diff main..HEAD` now reports 72 files and counts other people's
work as deletions.

**F · The new ADR reader parses no tables and no headings**, which is what
makes § 5's merge advice safe to act on. Grepped over the replaced section of
`viewer/parsers.py` at `0179c02`: zero `heading_is`, zero `split_row`, zero
header-normalization calls. The old `parse_decisions` had one of the first two
each. So this branch **removes** two header sites from that file and adds none.

**E · `tests/fixtures/contract-key-parity.json` has drifted from live on
`perry-task/list/1.18`** in fields no test in that module asserts — `emitted`
126 vs 115, and `not_observable` empty vs five `tasks[].depends_on_resolved[]`
keys. Not mine, not touched, reported.

## 8 · Baselines, by runner and tree

| Tree | Runner | Result |
|---|---|---|
| `coding/task-235-decisions-index` at `ee0b36a` (= `main`, before any edit) | `bash tests/run` | **98 modules · 2882 tests · 3 failures** |
| this branch at `b57a34a` | `bash tests/run` | see § 8.1 |
| this branch, 19 touched modules | `python3 tests/parallel` | **683 tests · all green** |

The three baseline failures, all pre-existing and unrelated:

- `test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository` — `2 != 0`. Reconciles against the LIVE board; this tree carries different intake rows.
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks` — `['ACTION-7', 'D009-1', 'D010-2', 'PROJ-003', 'SPEC-007']`.
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`.

`unittest discover` was **not** run on either tree — see § 9.

### 8.1 · After

**The targeted set is the number I stand behind without qualification.** Every
module this change touches, run on the committed tree with
`python3 tests/parallel`:

```
test_decide_writer test_decide_status_enum test_conformance
test_contract_invariance test_contract_key_parity test_ownership test_claims
test_pointers_resolve test_procedures_call_the_tool test_heading_defines
test_shipped_vocabulary test_row_integrity test_work_modes test_goals_writer
test_i18n test_parsers test_project_root_resolution test_router_budget
→ 19 modules · 683 tests · 98.1s · ✓ all green
```

**The full-suite run, and the one it caught.** `bash tests/run` completed at
**98 modules · 2892 tests · 594.6s**, with **4 failures across 3 modules**: the
three pre-existing ones above, plus
`test_procedures_call_the_tool.test_no_procedure_hand_edits_a_tool_owned_file`
— **which was mine.** Trimming `SKILL.md` back under its 20,480-byte cap had
put a write verb inside the guard's 60-character window before the
`OKR.md § Commitments` target, making `SKILL.md:75` an R1 finding. The guard
was right and the sentence was wrong; `b57a34a` fixes it, and candidate
wordings were run through `test_procedures_call_the_tool.scan` directly rather
than reworded until the suite went quiet.

**That run predates the fix, so it is not the number for this tree**, and a
clean `bash tests/run` on `b57a34a` was still executing when this row was
handed back — see § 9 for the load it was competing with. The expected result
is 2892 tests and the **3 pre-existing failures**, and `2892 − 2882 = +10` is
this branch's net test count: nine added (five in `TestNothingWritesAnIndex`,
two in `TestMintingReadsTheFilesAlone`, `test_the_three_index_keys_are_gone_and_stay_gone`,
`test_bootstrap_creates_the_directory_and_no_file`,
`test_a_project_that_never_bootstrapped_lists_cleanly_too`,
`test_the_status_a_new_adr_is_born_with_is_one_the_schema_declares`,
`test_the_shipped_version_is_recorded_in_its_own_changelog`) against two
removed with the index they tested (`test_an_index_row_with_no_file_is_reported`,
`test_a_project_with_no_proposal_renders_no_proposed_section`), plus the
subTest arithmetic in the two rewritten fixtures. **I am stating that as an
expectation, not as a measurement.**

## 9 · What I did not do, and what I could not verify

- **`unittest discover` was not run**, on either tree. The machine carried
  several other agents' full suites throughout — load average **32–48**,
  measured repeatedly — and `bash tests/run` took 576 s at baseline, 763 s
  mid-change and 595 s on the run that caught the `SKILL.md` defect. The row's
  brief says that runner shows 3 more failures from a module-double-import
  artefact in `test_risks_store`; I did not confirm that on this tree and am
  not reporting it as if I had.
- **The clean `bash tests/run` on `b57a34a` did not finish before this row was
  handed back**, under the load above. § 8.1 says what completed, what it
  caught, and what is an expectation rather than a measurement. The 19 modules
  this change touches are green on the committed tree; the full suite is green
  on every module except the three that were already red at `ee0b36a`, as of
  the 595 s run, whose only extra failure is the one `b57a34a` fixes.
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
- **There is no viewer HTML to verify, and I originally listed this as a gap
  before checking.** `viewer/` contains `parsers.py` and `tables.py` and
  nothing else — no template, no HTML. `snap.adrs` is consumed by
  `bin/perry-state` (`decisions.count` / `last` / `expired_sunsets`, all
  checked against the pre-change reader field by field) and by a `__main__`
  print in `parsers.py`. `sunset_or_notes` has **no** consumer anywhere, which
  is why its `"—"` → `""` change in § 7 A is inert.
