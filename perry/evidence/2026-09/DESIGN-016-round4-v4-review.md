# DESIGN-016 — V4 round 4

Three fresh-context reviewers, dispatched 2026-09-10 against
`perry/evidence/2026-09/DESIGN-016-spec.md`, the first written criteria these
fourteen rows have had. Base `0fb373a4`. Slices: writers and refusals
(criteria 1, 2, 3, 4, 9, 10), payloads and contract (5, 6, 13), the
declaration (7, 8, 11, 12, 14).

**Seven PASS, seven FAIL.** `134afea6` answers six of the seven FAILs; the
seventh is filed as TASK-411 rather than fixed under the round, because it
needs five per-tool AST readers and inventing those inside a review is how a
guard ends up wrong in a way nobody checks.

## The round cost a full dispatch before it started

All three reviewers were handed a worktree at `d49964ee`, 653 commits behind
the base — the same commit four agents got on 2026-09-07 at 496 behind. The
code under review did not exist there: no tool declared a `SURFACE` and the
criteria file was absent. All three stopped at the base gate and issued no
verdict. **The gate held only because each dispatch prompt named the required
SHA**; nothing in the harness checks it. Recorded on TASK-381, which now
carries the workaround: `git worktree add --detach <path> <sha>` from the
primary checkout, then a non-isolated agent pointed at that path.

## Two costs the author owes the round

- **The declared baseline was short by one test.** `tests/test_resume.py`'s
  `test_a_fresh_run_is_not_stale` is red at `4ebc0693` too, and two reviewers
  independently re-derived that — one by extracting the commit with
  `git archive`. An incomplete exhibit is the author's to fix before dispatch.
  The criteria file now names all three; the test itself is TASK-414.
- **Three reviewers shared one scratchpad directory** and two of them wrote a
  baseline to the same filename. One detected the clobber and re-measured;
  the other's first baseline named a sibling's tree.

## What each FAIL was, and what closed it

| row | the defect, in the reviewer's proof | closed by |
|---|---|---|
| TASK-360, TASK-365 | `bin/perry-restore-check:176` recognises `-h` at `argv[0]` alone, so `--root /tmp -h` exits 2 printing "unknown option". Every help assertion in the suite iterates the six declaring tools and this is not one | `134afea6` — scan the whole vector, plus a help sweep over all twenty executables |
| TASK-407 | `viewer/parsers.py:303` and `bin/perry-context-budget:117` let five of twenty executables exit through a traceback on an unreadable project root | `134afea6` — one primitive, six sites, found by a behavioural sweep after each of the first five hid the next |
| TASK-362 | `tests/test_compact_payload.py:83` computes its expectation with `project_value`, the function under test. Adding 1 to every integer it returns left 3,440 tests green while `--compact` reported 239 board lines against `--json`'s 238 | `134afea6` — the six rules get a second author, fed values built to distinguish them |
| TASK-408 | `lib.describe_surface` emitting empty flag lists left the suite green while `perry describe task` said `add` takes 4 flags, not 27. Nothing compared that payload's flags | `134afea6` — names and flags compared, not counts |
| TASK-410 | `bin/README.md:204` is not valid bash; two more blocks act on ids a fresh project has not got; the guard read one line of one block | `134afea6` — five blocks run whole, four are marked synopsis with a checked reason, the lifecycle block captures its id from `add --json` |
| TASK-364 | Direction B is unguarded on all six tools: `--rung` declared on `start`, whose handler never reads it, exits 0 and stores `rung=None`. Direction A is guarded on `perry-task` alone | **partly.** `134afea6` closes both directions for `perry-task`; the other five are TASK-411 |

Also filed, both correctly declined as FAILs: TASK-412 (the contract page's
rule-3 snippet compares minors as strings and nothing executes it) and
TASK-413 (`bound.open_total` / `bound.closed_total` are published to
dashboards and asserted nowhere in 3,440 tests).

## Mutations that were green and are now red

Each was replayed against `134afea6` and each turns a named test red.

| what was planted | was | is |
|---|---|---|
| `project_value` adds 1 to every integer | green, full suite | red — `test_each_kind_maps_its_input_to_the_declared_output` |
| `objectives_with_progress` puts `target` in the `current` slot | green | red — same case, `objectives_with_progress` subtest |
| `describe_surface` emits `"flags": []` | green | red — `test_the_published_payload_carries_each_subcommands_flags` |
| `--rung` declared on `perry-task start` | green | red — `test_every_flag_it_declares_for_a_subcommand_is_read_by_that_handler` |
| the README lifecycle block's LAST line broken | green | red — `test_every_block_is_either_marked_or_runs` |
| README block 1 broken | green | red — same |
| a runnable block parked behind the synopsis marker | n/a | red — `test_a_marker_cannot_hide_a_broken_example` |
| the suite marker used to excuse a non-suite command | n/a | red — same |
| the parsers primitive loses its `except` | n/a | red — `TestAnUnreadableProjectRootIsRefusedNotCrashed` |
| `perry-restore-check` back to `argv[0]` | n/a | red — `TestHelpPrintsFromAnyPositionOnEveryTool` |

## An earlier draft of this work put four rows on Perry's own board

`TASK-411` to `TASK-414` in the first sense of those ids — the README blocks
are real writes, and `PERRY_HOME` must point at the live checkout for them to
run at all. Reverted, and the runner now fingerprints `BOARD.md`,
`tasks.jsonl` and `events.jsonl` around every block, so an example that
resolves the wrong project fails there rather than quietly opening rows.

## Verdicts

The fourteen blocks below are the reviewers' own, verbatim and unedited. Six
of the seven FAILs have since been answered in `134afea6`; a FAIL is a record
of what was true at `0fb373a4`, not a status, and none of these rows moves on
this document alone.

```
=== VERDICT ===
task: TASK-359
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 1 on 13 of Bound A's 14 tools (perry_md_store.py reached as
         perry-okr), positively rather than by absence — `perry-task list --root
         <named>` returns 1 row while $PERRY_PROJECT's project holds 3, and with
         no --root the environment correctly wins; inverting the precedence at
         bin/lib/__init__.py:484-485 turned
         test_every_project_scoped_tool_prefers_the_flag (3 subtests) and
         test_the_store_tools_count_the_named_projects_records red.
not-checked: Windows paths; symlinked roots; --root pointing at a project whose
         state root is relocated
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-360
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 3 PASSES — all six declaring tools exit 2 on an unknown flag
         and name the legal set. Criterion 2 swept as 76 --help invocations over
         Bound B's 20 executables from first, middle and last position, after
         correcting a harness error that ran four bash tools under Python.
         Writers' bytes checked by sha256 of every file: 24 invocations, zero
         changes.
not-checked: criteria 7, 12, 14; --describe on all 57 subcommands
proof: bin/perry-restore-check:176 tests `argv[0] in ("-h","--help")` only, so
       `perry-restore-check --root /tmp -h` prints "unknown option -h" and exits
       2 with no help. Criterion 2's population is Bound B's 20 executables, and
       the spec's remainder exempts the 13 non-declaring tools from criteria
       3/7/8/12/14 — not from 2.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-361
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 4 on all four Bound D writers x {no flag, --dry-run, --json,
         --dry-run --json}: every control writes, every --dry-run leaves the
         project byte-identical, every --json parses, no traceback. The
         perry-tasks control was vacuous at first and was re-run with the store
         deleted, which writes.
not-checked: --dry-run under a concurrently held project lock; --json schema
         against schema/
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-362
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 5 by enumerating all 53 keys COMPACT declares against --json
         with an independent reimplementation of the six projection kinds; 4
         mutations inside project_value / project_compact; criterion 13 by
         rewriting a track's mode, stages, wip, sla, cycle and default_rung in a
         COPY of the project, and by blanking `stages` to force the schema
         fallback
not-checked: --compact against a non-UTF-8 or malformed store; the 5,000-token
         half of criterion 5; SKILL.md step 3's call site
proof: bin/perry-state:2360 — mutating the `value` branch of project_value so
       every integer is +1 makes `--compact` report board.lines=239, board.cap=201
       while `--json` from the same state reports 238, 200, and the full suite
       stays at its baseline reds. bin/perry-state:2371 — making
       objectives_with_progress carry `target` in the `current` slot makes
       `--compact` report P002-O1-KR1 current=3.0 where `--json` reports 1.0, so
       reference/snapshot.md step 4 renders 100% for a KR that is at 33%; full
       suite green. The cause is tests/test_compact_payload.py:83, which computes
       its expectation with STATE.project_value — the same function under test.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-363
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: (a) the bound, by mutating LIST_DEFAULT_LIMIT and by disabling
         truncation — both red under named tests; (b) the overflow report on a
         404-row store: 200 returned, truncated=true, open_total=156,
         closed_total=248, matched against ground truth from --limit 0; (c) the
         version, mutated in BOTH directions; the page's consumer snippet
         EXECUTED — accepts 2.0 against a live payload, accepts 1.18, rejects
         3.0; the changelog guard mutated four ways, all four red
not-checked: paging beyond the ceiling; --track interaction with the bound;
         the other consumers named in the page; lock behaviour under concurrency
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-364
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 7 both directions by mutation on all six Bound-C tools;
         criterion 14 by mutating five separate surface copies. Direction A is
         guarded on perry-task alone, by the AST test; direction B is guarded on
         NO tool: planting it on all six at once left 3,440 tests at baseline.
not-checked: the thirteen undeclared tools; criteria 1-6, 9, 10, 13; whether any
         of the 1,277 negative-space refusals is wrong about WHICH flags it
         names as accepted
proof: bin/perry-task:8043 — declaring "--rung" on `start`, whose cmd_start
       never reads it, leaves the whole suite green while
       `perry-task start TASK-001 --next "do it" --rung V4` exits 0, prints
       "wrote TASK-001 (start)", and stores rung=None. Second site:
       bin/perry-config:248 — removing "--wip" from `track`'s declared flags
       makes `perry-config track a --mode project --wip 6` exit 2 while
       bin/perry-config:289 still reads it, suite at baseline. The existing
       guard, tests/test_bin_surface.py:542, is a hand-listed table of ten pairs
       against a negative space of 1,277.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-365
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 2 over Bound B's 20 executables from first, middle and last
         argument position (76 invocations); the six declaring tools are all
         usage-first and guarded. Every help test in the suite iterates DECLARED,
         which is why the 14 non-declaring executables are untested for this.
not-checked: criterion 14, which decides this row jointly and belongs to another
         reviewer's slice
proof: bin/perry-restore-check:176 — help is recognised at argv[0] only, so
       `perry-restore-check --root /tmp --help` exits 2 printing "unknown
       option". Same defect and line as TASK-360's; one fix closes both.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-366
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 8 over all 57 declared subcommands of Bound E —
         `--describe --json <sub>` returns exit 0, the right `subcommand` key
         and no whole-tool payload, 57/57; `<tool> <sub> --help` returns one
         call, only that subcommand, 591 bytes at the largest. Both halves
         mutated and both redden.
not-checked: the token cost claim in DESIGN-016 § 1.3 (bytes were measured, not
         tokens); help from a non-first argument position; the thirteen
         undeclared tools
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-367
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 4's "the flag is written, not dropped" — replacing
         bin/perry-task:3780 `"design_refs": design_ids` with `[]` reproduces
         the accepted-and-dropped defect and test_the_edge_lands_in_the_store
         goes red. Live: `add --design DESIGN-042` writes the edge into the
         store record, and `--design DESIGN-999` with no document is refused
         without opening the row.
not-checked: --design on subcommands other than add; repeatable --design
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-406
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 9 by mutation on BOTH implementations — bin/perry-tasks:183
         and bin/perry_md_store.py:1178 each turned a differently-named test
         red, so neither copy is unguarded; bin/perry-tasks:199 turned the
         counter back to records-read and test_a_clean_write_says_what_it_changed
         went red. Converse verified live: with one stored record whose board
         line was deleted, `render --write` exits 1, names TASK-001, leaves the
         board byte-identical, prints no traceback; a clean write reports
         "0 line(s) changed, 34 unchanged, from 4 stored record(s)".
not-checked: the risks/intake/asks registers' own refusal paths beyond the
         shared write_board_or_refuse; concurrent writers racing the probe render
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-407
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: Bound F over Bound B — 20 executables, executed directly so shebangs
         are honoured, across no-argument / unknown flag / unknown subcommand /
         missing required value / unreadable root / non-JSON store, with the
         unreadable-root shape expanded into 5 spellings. Category enumerated,
         not chased. Separately, the perry-tasks fall-through guard was verified
         by mutation and the same category enumerated across all six declaring
         tools.
not-checked: shapes on a project whose store is a directory; Windows ACLs
proof: viewer/parsers.py:303 `if not path.exists():` — Path.exists() raises
       PermissionError rather than returning False when the parent directory is
       unsearchable, so perry-config, perry-task, perry-tasks and perry-okr all
       exit through a traceback on `<tool> <sub> --root <dir with mode 000>`.
       bin/perry-context-budget:117 is an independent second site with the same
       shape. 5 of 20 executables.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-408
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 14 against bin/perry's three answers. `perry list`,
         `perry list --tools`, `perry describe <tool> [<sub>]` and forwarding
         all read SURFACE through lib. Enumerated the count-not-name category
         repo-wide: exactly two instances.
not-checked: `perry list` timing/token claims; the undeclared-tail ordering;
         non-UTF-8 handling beyond surface_of's narrowed except
proof: bin/lib/__init__.py:694 — making describe_surface emit an empty flag set
       per subcommand leaves 3,440 tests at baseline while `perry describe task`
       and `perry-task --describe --json` (TASK-396's published write contract)
       both report that `add` takes 4 flags rather than 27. The only test that
       reads it, tests/test_bin_surface.py:727-728, asserts
       len(payload["subcommands"]) and the `tool` key and nothing else.
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-409
rung: V4
result: PASS
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: the register as a declared parameter rather than a name. The four
         register names come from schema/state-schema.json § claims, not a
         literal. `--register` is declared on build/verify/write/render/diff and
         honoured on all five; on the twelve prefixed aliases and everywhere
         else it is not declared it is refused with exit 2 — covered by a
         1,277-probe negative-space sweep, 0 accepted. Mutating
         bin/perry-tasks:1651 to make `--register` a no-op on the two verbs that
         can lose data reddens test_the_parameter_and_the_alias_are_the_same_call.
not-checked: whether the twelve aliases behave identically on a project where
         `## Top risks` is a readable table; the alias removal path
proof: n/a
=== END VERDICT ===
```

```
=== VERDICT ===
task: TASK-410
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/DESIGN-016-spec.md
checked: criterion 11 BY EXECUTION. All 10 fenced bash blocks extracted and run
         against a fresh scratch project, whole-block and per-logical-command.
         No block carries a non-executable marker and the test has no marker
         mechanism to read. 6 blocks run clean. Breaking block 1, and breaking
         block 5's OWN last line, both leave 3,440 tests at baseline.
not-checked: block 10 (`bash tests/run`) — it is the suite itself and cannot run
         against a scratch project, which is itself a criterion-11 gap;
         whether block 8's perry-codex-preflight failure is environment-specific
proof: bin/README.md:204 — `"$PERRY_HOME/bin/perry-decide" new <slug> --title
       "…" --type <T>` is not valid bash. `bash -n` refuses it outright, so the
       whole fenced block exits 2. Two further blocks refuse: :140
       `perry-explain REL-002` exits 1, and :205 `supersede ADR-003 ADR-007`
       exits 1, both on ids the block never creates. The guard reaches one line
       of one block: tests/test_bin_surface.py:440 stops at the first line not
       ending in a backslash.
=== END VERDICT ===
```
