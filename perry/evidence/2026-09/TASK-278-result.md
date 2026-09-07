# TASK-278 — result

> Design: `design/DESIGN-015-linkage-is-a-store.md`, implementation plan row **C**
> Branch: `coding/task-278-six-read-sites`, cut from `main` at `1032e76`
> Executor: claude-subagent (the spec said codex; the dispatch routed here)

## What landed

The six call sites `DESIGN-015 § 5.6` names read `linkage.jsonl` instead of
`phase/<NNN>-linkage.md`. `perry-lint`'s seventh census line stopped saying
*"comparison incomplete"* and started printing a verdict it computed.

## The six sites, re-derived

**The spec's line numbers are from 2026-09-02 and every one of them has
moved.** They were re-derived by reading the exact line at `d49964e` — the
commit the spec measured on — and finding where that line sits today, rather
than by grepping a name. Phase 002's most expensive recurring defect was
locating an implementation by its name, about ten times over.

| # | Site | Spec (`d49964e`) | Today (`1032e76`) | Before → after |
|---|---|---|---|---|
| 1 | `bin/perry-goals` · `register_path`, the `link` writer | 1657 | **1644** | `return state_root / "phase" / f"{number}-linkage.md"` → the decisions are taken from `reg.graph` (store-first) and the edge is written to `linkage.jsonl` beside the document |
| 2 | `bin/perry-goals` · `cmd_krs` | 3033 | **3020** (path) / **3039** (read) | `P.parse_linkage(path.read_text(…))` → `P.load_linkage(state_root, path)` |
| 3 | `bin/perry-task` · `live_references` | 4491 | **4813** | `for path in sorted(glob("*-linkage.md")): … re.match(r"\s*tasks:", line)` → `json.loads` per line of `linkage.jsonl` |
| 4 | `bin/perry-lint` · the linkage check | 1200 | **1324** | `link = P.parse_linkage(lf.read_text())` → the authority is chosen **per phase**, store-first |
| 5 | `bin/perry-lint` · the exclusion | 1231 | **1355** | `[m for m in mine if not m.name.endswith("-linkage.md")]` → `[… if not _is_linkage_register(m)]`, a named predicate stating both halves of the register |
| 6 | `viewer/parsers.py` · `load_snapshot` | 4503 | **4527** | `linkage = parse_linkage(linkage_file.read_text())` → `linkage = load_linkage(root, linkage_file)` |

`viewer/parsers.py` had shrunk by 474 lines when TASK-339 removed the
escalation scanner, and site 6 still moved *forward* by 24 lines — which is
why the arithmetic could not be guessed and each line was read.

## One seam, not six decisions

`viewer/parsers.py` gains `load_linkage_store`, `linkage_from_store` and
`load_linkage`. The split between what the store owns and what the document
keeps is read off `schema/state-schema.json § stores.declared["linkage.jsonl"]`
rather than re-decided at each call site:

- **From the store**: objectives, KR ids, `title`, `target`, `current`,
  `stretch`, `linked`, every `edge`, every `unlinked`.
- **From the document**: `spec`, `phase`, `updated`, `projects[]`, `agents[]`,
  and per KR `metric` and `due`. None of those is a declared store field.
  `metric` is Decision 2 and the schema's own `derived_not_stored` block says
  so; the rest simply have no `kr`-record counterpart. These are exactly the
  fields that survive row E.

Verified before any code was written: on this project the store and the
document agree on **every** schema'd field, in order — 6 KRs, 15 edges across
6 KRs, 100 `unlinked`, all identical.

## The two instructions that were easy to half-do

**`bin/perry-task`'s regex is replaced by `json.loads`, not by a second
regex.** The comment beside it said why the regex existed — *"this file is
markdown with a YAML-shaped block in it, not a YAML document"* — and that
reason does not survive the source becoming JSONL. There is no `re.match`,
`re.search` or `re.findall` anywhere in the rewritten reader, and
`test_site_3_uses_no_regex_over_the_store` asserts that against the source,
because the behaviour cannot tell a working regex from a parse.

Two things improved for free: the refusal's line number is now **exact**
(one record is one line), and `unlinked` records are deliberately *not*
counted as live references — `perry-lint` files `linkage-unlinked-exists` at
`warn` on the stated ground that a stale declaration is "a record to correct
rather than a file to refuse", and refusing on it here would have overturned
that by the back door.

**`bin/perry-lint`'s exclusion and its check are rewritten, not deleted.**
Every finding still fires, on the same rule and at the same severity. What
changed is where the graph comes from — and it is chosen **per phase**, which
is the one piece of care this needed. Row B imported phase 003 only;
`phase/001-linkage.md` and `002-linkage.md` still carry 16 further KRs, 12
edge lists and 27 `unlinked` declarations. A store-wide sweep would have
stopped checking all of them and reported zero findings for a reason having
nothing to do with the graph being sound — `DESIGN-015 § 7`'s "the move
silently drops existing edges" risk, arriving through the linter.

`projects[]` is graded and reported against the **document**: it has no record
kind in the store, so a finding must name the file carrying the line.

## What `perry-lint` prints now, and whether drift is real

    before:  · linkage store: 121 valid record(s), comparison incomplete — drift is unchecked, not clean
    after:   · linkage store: 121 record(s), 0 row(s) drifted

**The verdict is real, not deferred.** Seven stores now answer in one shape.
Three things make `0` mean "compared and found nothing" rather than "did not
look":

1. `comparison_performed` is driven by `_linkage_drift_rows`'s `compared`
   count — the number of registers there was actually a document to compare
   against — and not by "the store parsed". With the register document
   removed, the line goes back to `unchecked, not clean`, which is
   `P003-O1-KR3`'s rule reaching the seventh store.
2. It was shown able to go red by hand: `target: 6` → `99` on one `kr` record
   produced `⚠ linkage.jsonl [linkage-store-drift] P003-O1-KR1 differs
   between the store and phase/003-linkage.md` and `1 row(s) drifted`.
   Restored, back to `0`.
3. `TestTheDriftVerdictIsReal` pins all three states the line can now give.

Only the schema'd half is compared, which is not a shortcut: a comparison
that reported `metric` as drift would report Decision 2 as a defect on every
run.

## The gate, shown able to go red

The fixture seeds the store and the document to **disagree** — the store puts
`TASK-100` under `KR1`, the document under `KR2` — so every assertion says
which file the reader read, not merely that it produced something. A fixture
whose halves agree is green with the readers moved, green with them still on
the document, and green with them deleted.

Restoring any one site turns exactly the test named for it red. From the
mutation round:

| Site | Mutation | Named test | Result |
|---|---|---|---|
| 6 | `load_snapshot` back to `parse_linkage(<document>)` | `test_site_6_perry_state_attribution_reads_the_store` | RED |
| 2 | `cmd_krs` back to `parse_linkage(<document>)` | `test_site_2_perry_goals_krs_reads_the_store` | RED |
| 3 | `live_references` back to the document glob | `test_site_3_perry_task_names_the_store_and_its_line` | RED |
| 4 | the lint sweep back to the document | `test_site_4_the_lint_check_grades_the_stores_edges` | RED |
| 5 | the exclusion deleted | `test_site_5_the_register_is_never_its_own_comparand` | RED |
| 1 | `link_edge` judges from `reg.model` again | `test_site_1_link_refuses_on_what_the_store_says` | RED |

Site 4 also carries a **refutation**: a dangling edge in the document alone
must produce no finding. Without it the positive case would pass with both
files being read.

## Mutations — 17 planted, 3 GREEN in round 1, every green a finding

Each mutation is anchored by line number **and** asserted against the text
that has to be on that line; a non-matching anchor aborts the whole round
rather than silently no-opping into a false green. `__pycache__` cleared and
the clock pushed past the whole-second boundary before every run. The tree
was restored and its sha256 re-checked after each one.

**Round 1: 14 red, 3 GREEN. All three were holes in the tests, and all three
were real.**

- **M5 — deleting site 5's exclusion left the suite green.** The fixture
  named the phase document `002-earlier.md`, which sorts *before*
  `002-linkage.md`, so the fallback's `mine[0]` was the right file whether
  the exclusion ran or not. The exclusion was never exercised. Renamed to
  `002-zeta`, which puts the register first: without the filter the register
  becomes its own comparand, the KR id it names in its own `projects[]` looks
  declared, and the finding disappears.

- **M12 — dropping a line the writer cannot parse left the suite green,
  because the test asserted a branch it never reached.** A store with one
  unparseable line makes `load_linkage_store` answer `None` for the *whole*
  store, so `reg.graph` falls back to the document, no retraction is ever
  requested, and `linkage_store_text`'s `except json.JSONDecodeError` branch
  is not entered — through `link`, it is unreachable. The branch is kept
  (this function reads the file itself, not through that reader) and its
  comment now **says so out loud** instead of looking load-bearing. The test
  now asserts the reachable half — the line survives the append — and checks
  the store was actually rewritten, so "kept" cannot be confused with "never
  written".

- **M16 — filing a `projects[]` finding against the store left the suite
  green**, because the only fixture with a `projects[]` entry sat on a phase
  the store does not cover, where `rel` and `doc_rel` are the same string. A
  second test puts the entry on store-covered phase 003, where they differ.

**Round 2: 17 planted, 17 red, 0 green.** Including the guards that exist for
wrong input, which is TASK-277's finding applied forward — its round found
that every test in its module checked the happy path, so five guards could
each be deleted with the suite still green. Reached here by name: absent
store ≠ empty store, empty ≠ absent, malformed does not half-parse, a phase
the store does not declare keeps its document, an unparseable document is
still a failure, an orphan KR is kept titleless rather than dropped, `link`
on a store-less project creates no store, and the superseded `unlinked`
record is retracted.

## Control — this row is invisible to the surfaces a user reads

    perry-goals krs --root perry              byte-identical  (diff, empty)
    perry-state --root perry --section attribution   byte-identical
    perry-state --root perry --section linkage       byte-identical

The full `perry-state` payload differs only in `generated_at` — and in
`design.by_status`'s **key order**, which is not this row's. It depends on
`PYTHONHASHSEED`: seeds 0 and 2 give `['locked', 'draft']`, seeds 1, 3, 4 and
5 give `['draft', 'locked']`, on the same tree and the same data. Reproduced
at the branch base `1032e76` as well, so it is pre-existing. Filed as a
separate suggestion; it makes `perry-state` unusable as a byte-comparison
control until it is fixed.

## Tests

**Baseline measured in this agent's own tree**, at the branch base
`1032e76`: **1 red test** —
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
(Perry trips its own `LOAD-03`). That base run also showed `test_tree_guard`
(8) and `test_one_header_rule` (1) red, and both are artifacts of measuring
in an extracted archive with no `.git` (*"fatal: not a git repository"*) —
they are green in this worktree, so they are not part of the baseline.

**After: 1 red test, the same one.** `117 modules · 3346 tests · 122.1s · 8
workers`, against the baseline's `116 modules · 3320 tests · 122.0s`.

`bin/perry-lint --root .` — **0 errors, 38 warnings**, unchanged.

Three modules row C moves out from under were updated rather than left red:

- `tests/durations.json` — the new module is listed and **measured**, not
  filed as never-measured, following `task-276-linkage-store` and
  `task-277-linkage-import`: three serial runs with `__pycache__` cleared,
  2.97 / 4.07 / 3.75s, largest recorded so the hint never under-books.
- `tests/test_okr_store_is_the_source.py` — the write-call-site census gains
  `cmd_link`'s second write. The register is two files now; both go through
  this tool's own `write_atomic`, so both pass `assert_owned`.
- `tests/test_linkage_import.py` — TASK-277's two tests pinned the B-to-C
  window. Row C closes it. The argument they carried is **kept**: one test
  now asserts the verdict is computed, and a **new third test** carries the
  old argument one state further on — with the register document removed
  there is nothing to compare and the line still reads `unchecked, not
  clean`.

## Load, said out loud

The machine was never quiet: load1 sat between 10.2 and 19.0 for the whole
round, load5/load15 between 16 and 18. Timing figures taken here are worth
little. What can be said is that this was **not** the load-114 regime the
`task-277-linkage-import` note warns about — a bare `python3 -c pass`
measured 17–19ms throughout, against the 4,467ms recorded on this box at
load 114 — and that the two suite runs, baseline and after, were taken under
the same load band, so their comparison is worth more than either number
alone.

## Out of scope, untouched

`schema/state-schema.json` (row A owns it), the 16 never-asked and 75
declared rows (phase 004), `tasks.jsonl`'s `Next action` prose
(`DESIGN-015 § 8`), and **what `add` writes** — that is row D, and `via` on
every record this row writes is `"link"`, never `"add"`. `P003-O3-KR2` counts
`via: "add"`, so nothing here can inflate it.

## Numbers that have moved since the spec was written

The spec's verification asks for `linked=5`, 75 declared, 16 never-asked.
Measured today, before and after, identically: **`linked=6`, 100 declared,
66 never-asked**, over 121 store records (6 `kr`, 15 `edge`, 100 `unlinked`).
The spec's figures are from 2026-09-02 and the register has moved twice
since. The control that matters is before-equals-after, and it holds byte
for byte.
