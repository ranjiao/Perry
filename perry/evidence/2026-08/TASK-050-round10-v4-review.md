# TASK-050 — V4 review round 10: **FAIL**

> Fresh-context reviewer, 2026-08-30, against
> `perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
> option C`, which binds.
> Under review: `4c2f07a`, the read-only worktree at `scratchpad/review-050r10`
> — round 10's code plus `main` merged in by the PMO after the author's numbers
> were recorded. **Every plant, mutation and suite run below happened on
> `git archive` exports and `cp -R` copies under `scratchpad/rjv4r10/`**, never
> on the reviewed tree. No write-side Perry tool was run. No identifier was
> minted. The reviewed worktree was verified byte-identical to its commit at
> the start and at the end.

**Round 9's charge is genuinely closed, and the author's counter-claim is
TRUE.** I reproduced it myself: the reviewer's `bin/perry-tasks` plant crosses
two independent holes, and the bare-`squash` variant with no alias at all
escapes round 9's tree identically. The alias half is now shut — all ten of
round 9's probe shapes are caught and both criterion-4 controls stay silent —
and the cross-module half is covered by driving the reader. Every mutation I
spot-checked reproduces, several pinning exactly one corpus entry.

**It fails because the answer the round gives to the half it did not close
statically is measured wrong, and I can falsify the amendment's own sentence on
a live production file with the plainest possible spelling — no alias, no
exotic shape.** A header row carried through a **dict key** is invisible to
`offenders_by_symbol`, *including when the dict is built two lines above in the
same function*; and `["header"]` is this repository's dominant idiom for
holding a header row — **17 live sites, 12 of them in functions the runtime
watch never reaches.** § 7 limit 1 says *"every converted reader is now driven,
so the uncovered set is empty today."* It is not empty. It is twelve.

---

## THE RULING THIS REVIEW EXISTS FOR

### 1. The author is right that the reviewer's plant crossed two holes. Measured.

`scratchpad/rjv4r10/rjv4r10_crossmod.py`, one plant at a time into full copies,
replaying the round 9 review's own two-site plant in three spellings:

```
tree-r9   alias        -> []     # `_fold = squash`, the reviewer's own plant
tree-r9   bare         -> []     # SAME plant, bare `squash`, NO alias
tree-r9   bare_direct  -> []     # folded straight off the cross-module call
tree-r10  alias        -> []
tree-r10  bare         -> []
tree-r10  bare_direct  -> []
```

The bare variant escapes round 9's tree identically. **The alias was never the
whole story**, and round 9's prescribed fix could not have closed that
demonstration. That framing is vindicated, not a rationalisation.

### 2. Closing a static hole with a runtime watch CAN satisfy the amendment — the mechanism is legitimate. This round's execution of it is not.

I rule **for** the mechanism and **against** the claim made for it.

The amendment asks for a *smaller surface*, and its verification section is
about behaviour: *"reverting it now reddens a test."* Nothing in it says the
one-symbol check must be static. Round 9's accepted ruling already rests on
exactly this: `SECOND_RULE` is `0 of 41` and is acceptable **because the class
is covered dynamically** — `test_every_decorated_header_cell_reached_header_index`
goes red when a reader grows its own rule. A reviewer who accepts a dynamic
cover for the second-rule class and rejects one for the cross-module row is
applying two standards.

And the cover is real. R10-10 reproduces on my copies: the reviewer's plant, in
all three spellings, turns `test_every_fold_of_a_header_cell_came_from_header_index`
**RED** on the round 10 tree, while the same plants are **OK** on round 9's:

```
tree-r10 alias / bare / bare_direct : FAIL test_every_fold_of_a_header_cell_came_from_header_index (Ran 8, FAILED 1)
tree-r9  alias / bare               : Ran 7 tests  OK
```

**But a dynamic cover is only as good as its reach, and the reach is asserted
in this round as a fact rather than measured.** That is where it fails. A
runtime watch that covers 5 of 17 live instances of the exact shape it is
offered for is not a cover; it is a sample. The rule I apply, and the one the
next round should be held to: *a dynamic cover discharges a static hole only if
the round measures which sites it reaches and states the remainder.* This round
states the remainder as empty and it is twelve.

---

## Finding — the FAIL. A header row carried through a dict key is invisible to BOTH halves, and it is the repository's own idiom

### The escape, on a copy of the reviewed tree

`bin/perry_store.py § risk_plan` already reads its header out of a dict key
(`header, keys = table["header"], table["keys"]`, line 854). One inserted line,
bare `squash`, no alias:

```python
# scratchpad/rjv4r10/uncovered-store/bin/perry_store.py:854-855
     header, keys = table["header"], table["keys"]
+    keys = [squash(c) for c in header]
```

```
$ python3 -c "import sys;sys.path.insert(0,'tests');
              from header_rule import offenders_by_symbol;print(offenders_by_symbol('.'))"
[]
$ python3 -m unittest discover -s tests -p 'test_header_index_is_the_only_fold.py'
Ran 8 tests in 1.514s   OK
$ python3 -m unittest discover -s tests -p 'test_one_header_rule.py'
Ran 13 tests in 2.732s  OK
$ python3 -m unittest discover -s tests -p 'test_row_integrity.py'
Ran 33 tests in 0.859s  OK
$ bash tests/run
102 modules · 3034 tests · 331.8s · 8 workers
✗ 2 module(s) red
```

The whole suite on that planted copy is **byte-for-byte the failure set of the
unplanted tree** — the same two red modules and the same three names. Nothing
in this repository notices.

That is *"a call to `squash` on a row cell outside `header_index()`"* — the
amendment's sentence, verbatim — on a converted reader, in a file the round
counts as driven, with every guard this row ships reporting nothing.

### It is NOT the cross-module hole the round declares, and the round's own reason for not closing it does not apply

§ 7 limit 1 attributes the gap to another module and to a file-local walk being
unable to see across one: *"closing that statically would be interprocedural
row-source recognition across module and dict boundaries — the widening the
amendment rejects by name."* Measured, that attribution is wrong. The shape
escapes with **no module boundary at all** — with the dict literal built two
lines above, inside the same function (`scratchpad/rjv4r10/rjv4r10_dict.py`,
planted one at a time into copies, control included):

```
tree-r10  P1_local_dict_var    ESCAPED   t = table_of(line); hdr = t['header']; [squash(c) for c in hdr]
tree-r10  P2_inline_dict       ESCAPED   t = {'header': split_row(line)}; [squash(c) for c in t['header']]
tree-r10  P3_list_of_dicts     ESCAPED   [squash(c) for c in tables_of(line)[0]['header']]
tree-r10  P5_attr_object       ESCAPED   t = T(line); [squash(c) for c in t.header]
tree-r10  P4_control_direct    CAUGHT    [squash(c) for c in split_row(line)]
```

and with the repository's other spelling of the rule, `ops.norm`:

```
tree-r10  Q1_opsnorm_dict      ESCAPED   t = {'header': split_row(line)}; [ops.norm(c) for c in t['header']]
tree-r10  Q2_opsnorm_direct    CAUGHT    [ops.norm(c) for c in split_row(line)]
```

`P2` is **local dataflow in one function**. `_RowLocals` already follows
assignment, subscript, slicing, walrus, iterable wrappers, one comprehension
unwrap, a parameter this file passes a row to, and *what a file-local function
returns* — including `_, ihdr = ctx["board"].section_table("Intake")`, which I
confirmed is caught (planted at `bin/perry-task:6456`, reported as
`bin/perry-task:6456: [squash(c) for c in ihdr]`). Adding "a subscript of a
dict this file built, or of what a file-local function returned" is one more
`source()` case in machinery that already does the harder ones. **It is not
option A.** Option A is widening recognition of the *fold expression*; this is
the *row source*, and round 9's design deliberately expanded exactly that side.

So the round's own justification — that the only alternative is the rejected
widening — is not available for the shape that actually escapes.

### § 4.2's first row and § 7 limit 1 are both falsified

§ 4.2 claims `offenders_by_symbol` sees *"the rule applied to a row a **local**
dataflow reaches, under any alias."* `P2` is a local dataflow and it is not
seen.

§ 7 limit 1 claims *"every converted reader is now driven, so the uncovered set
is empty today; it is one unwatched conversion away from not being."* Measured
on the reviewed tree:

- **17 live sites** read a header row out of a dict key
  (`table["header"]`, `tables[0]["header"]`, `tbl["header"]`, `site["header"]`)
  across `bin/perry-task`, `bin/perry-tasks`, `bin/perry_store.py` and
  `bin/perry_md_store.py`.
- Driving the watch's own workload and collecting every function on a recorded
  stack, **12 of the 17 sit in functions the watch never reaches at all**:
  `_cmd_list_from_board`, `_task_sections`, `ask_plan`, `ask_section_shape`,
  `ensure_columns`, `ensure_section_columns`, `find`, `plan`,
  `refuse_foreign_risk_table`, `risk_plan`, `risk_section_shape`,
  `task_tables`.
- `WATCHED` is 16 functions; **59 `header_index`/`header_keys` call sites sit
  in 45 enclosing functions, 34 of which are not in `WATCHED`.**

The uncovered set is not empty today, and the limit is not one conversion away
from growing — it already covers most of the places this repository holds a
header row.

### And the corpus does not plant it — the same structure as round 9's charge

I enumerated every `DRIFT`, `CLEAN` and `SECOND_RULE` body. **No `DRIFT` entry
carries a row through a dict or an attribute.** The corpus plants the alias
passed to `map` and the alias used as a `sorted` key — two indirections a
reader would have to reach for — and does not plant the one that is written
seventeen times in the tree under review. That is the sentence round 9 wrote
about `fold = squash`, with a different noun.

### Why this fails the round rather than being recorded

The three tests that were supposed to make the limits trustworthy are the
reason. This round's whole answer to "the static half is blind here" is "the
dynamic half is not", and § 7 re-states the limits *from scratch* precisely
because round 9's list was found incomplete. The re-stated list gets the
mechanism of the residual hole wrong (module boundary, when a dict literal in
one function suffices), gets its size wrong (empty, when it is twelve), and
justifies leaving it open by an exclusion — option A — that does not cover the
shape. A declared limit that misdescribes what it declares is not a declared
limit; it is the gap in a shape the next reviewer cannot check against.

**It is also small to fix, and in the same idiom the design already uses:**
teach `source()` that a subscript of a dict literal whose value is a row, or of
what a file-local function returned, is a row (`_RowLocals.returns` already
carries tuple positions; a string key is the same bookkeeping) — then plant the
dict-carried and attribute-carried rows in `DRIFT` with their provenance, and
either drive the twelve functions or state them by name.

---

## What holds, measured independently

**The tree matches its commit.** Every tracked blob re-hashed against
`git ls-tree -r HEAD`: **721 files, 0 mismatches**; `git status --porcelain`
empty; `git ls-files -o --exclude-standard` empty. The hand restore the round
volunteered (R10-7's line-indexed `MISMATCH`) left no residue. The round 10
code diff is exactly three files under `tests/` — `git diff --stat b5e7be3
a1ff426` is 366 insertions / 13 deletions — and the PMO's merge did not touch
any of them (`git diff a1ff426 HEAD -- tests/header_rule.py
tests/test_header_rule_harness.py tests/test_header_index_is_the_only_fold.py
tests/test_one_header_rule.py` is empty).

**The alias fix is real, and it is over the binding rather than the name.**
`scratchpad/rjv4r10/rjv4r10_alias.py`, one plant at a time into copies, every
drift body `[fold(c) for c in split_row(line)]`, controls included:

| shape | round 9 | round 10 |
|---|---|---|
| `fold = lambda s: squash(s)` | CAUGHT | CAUGHT |
| `def fold(s): return squash(s)` | CAUGHT | CAUGHT |
| `fold = squash` | ESCAPED | **CAUGHT** |
| `fold = squash`, scalar on a cell | ESCAPED | **CAUGHT** |
| `from tables import squash as fold` | ESCAPED | **CAUGHT** |
| `import tables; fold = tables.squash` | ESCAPED | **CAUGHT** |
| `keyof = squash` (the repo's idiom, renamed) | ESCAPED | **CAUGHT** |
| `a = squash; fold = a` (transitive) | ESCAPED | **CAUGHT** |
| alias bound inside the reader | ESCAPED | **CAUGHT** |
| alias bound OUT OF ORDER (`if:` then use) | ESCAPED | **CAUGHT** |
| `map(fold, row)` / `sorted(row, key=fold)` | ESCAPED | **CAUGHT** |
| CONTROL plain `squash` | CAUGHT | CAUGHT |
| `tidy = str.strip` used on a row (criterion 4) | silent | **silent** |
| alias used as a VALUE normalizer (criterion 4) | silent | **silent** |

Round 9's FAIL is closed, and closed as a property of the *binding*: the two
non-rule controls stay silent, so this is not a widened list of names.

**Nine mutations reproduced on `cp -R` copies, each anchored by line and
asserted against the exact old text before replacing. All seven anchors in
`tests/header_rule.py` contain what the result says they contain.**

| # | mutation | corpus entries reddened (mine) | claimed |
|---|---|---|---|
| R10-1 | `a.name in BLESSED` → `in ()` | **`D26` only** | D26 only ✓ |
| R10-2 | `target = self._alias_target(…)` → `None` | `D25 D27 D28 D29 D30 D31` **+ `D32 D33`** (8) | 6 — **under-reported** |
| R10-3 | `name = value.attr` → `return None` | **`D27` only** | D27 only ✓ |
| R10-4 | fixpoint `range(4)` → `range(1)` | **`D30` only** | D30 only ✓ |
| R10-5 | `rows.blessed` → `BLESSED` | **`D32` `D33`** | D32 D33 ✓ |
| R10-6 | `rows.rule` → `THE_RULE` | **`D28` only** | D28 only ✓ |
| R10-7 | `is_python` back to round 8's | **`D20` AND `D21`** | D20 and D21 ✓ |
| R10-8 | `NO_SHEBANG` → `frozenset()` | `test_the_no_shebang_entries_are_planted_without_one` RED | ✓ |
| R10-9 | `for attr in ("squash","norm")` → `for attr in ()` | `test_the_rebinding_loop_watches_a_readers_own_reference` RED | ✓ |

Four single-entry mutations verified, which is the precision claimed. R10-2's
under-report is in the safe direction (the guard is broader than advertised)
and is consistent with the table having been written before `D32`/`D33` existed
— recorded, not charged.

**The two GREEN mutations are honestly reported and the re-plants are real.**
`D30`'s body is `if os.name == "posix": a = squash` **then** `fold = a`, so
`ast.walk`'s breadth-first order reaches the second link first and one pass
cannot close it — my own out-of-order probe confirms this independently, and
R10-4 (`range(1)`) reddens `D30` and only `D30`. **The fixpoint now earns its
place.** `D32`/`D33` pass the alias without calling it, so the scalar half
cannot see them, and R10-5 reddens exactly those two. Both re-plants do the
work they are claimed to do.

**R10-7 is the `D20` regression check and it holds.** Round 8's `is_python`
reddens `D20` **and** `D21`, where R9-6 reddened `D21` alone. `_plant` writes
`body if where in NO_SHEBANG else SHEBANG + body`, and
`test_the_no_shebang_entries_are_planted_without_one` asserts the bytes on
disk, that every exempted path is a real entry, and that the label set and the
path set agree in **both** directions.

**The `Watch` rebinding loop no longer survives its own deletion.** `for attr
in ():` reddens `test_the_rebinding_loop_watches_a_readers_own_reference`
(1 failure of 8). The test is not vacuous: it asserts `lint.norm is
tables.squash` first, asserts the rebinding actually happened inside the
context, folds a decorated cell **through the reader's own reference**, asserts
the watch recorded it, and asserts `__exit__` restored it.

**The corpus measures what the round says.** `measure()` on a `git archive`
export: `{'drift_escaped': [], 'clean_flagged': [], 'second_rule_caught': []}`,
`DRIFT 33 / CLEAN 12 / SECOND_RULE 41 / UNRECOVERABLE 2`. I read all nine new
`DRIFT` bodies against the round 9 review's own escape list: `D25`←ESCAPED B,
`D26`←ESCAPED E, `D27`←ESCAPED F, `D28`←ESCAPED C, `D29`←ESCAPED G,
`D31`←the review's "a rebinding is not obliged to sit at module level",
`D30`/`D32`/`D33`←this round's two green mutations. **None was invented to be
easy**, and `D26`'s provenance note is exactly right that `D06` aliases onto
`norm`, a name already in `BLESSED`.

**`0 of 41` on `SECOND_RULE` is unchanged and I do not re-litigate it.** Round
9's ruling stands.

**The live tree is clean and the "exactly one alias" claim survives my own
enumeration.** `offenders_by_symbol('.') == []` on the reviewed tree.
Independently of the round's machinery I AST-swept every Python file in the
repository — not only `readers_under` — for any binding of
`squash`/`norm`/`header_index`/`header_keys` to another name by assignment,
`import … as`, container literal or `return`. Outside `tests/` there is exactly
one: **`bin/perry-lint:250 norm = squash`**, already blessed. (The three hits
inside `tests/` are the `Watch` machinery; two apparent "container" hits in
`bin/perry-goals` and `bin/perry_md_store.py` are `out = [squash(canonical)]`,
a call, not the function object.)

**R10-11 reproduces, both halves, and the contrast is the proof.** Planted into
copies, `keyof = squash` at `bin/perry-lint:250` plus `value = keyof(key)` at
`:348`:

```
tree-r10                offenders -> ['bin/perry-lint:349: keyof(key)']
tree-r10 + round 9's header_rule.py   offenders -> []      <-- ESCAPED
tree-r9                 offenders -> []                    <-- ESCAPED
```

and on the round 10 tree the plant reddens three named tests:
`test_nothing_outside_header_index_maps_squash_across_a_row`,
`test_value_normalizers_are_not_flagged` (13 tests, 2 failures) and
`test_the_static_net_is_the_one_that_sees_dead_code` (8 tests, 1 failure).

**Baselines — I name the tree for each.** All on `git archive` exports under
`scratchpad/rjv4r10/`.

| runner | tree | modules | tests | failures |
|---|---|---|---|---|
| `bash tests/run` | **`4c2f07a`, the reviewed merged tree** | **102** | **3034** | **3** |
| `python3 -m unittest discover -s tests -p test_header_index_is_the_only_fold.py` | `4c2f07a` | — | **8** | 0 |

This matches the PMO's measurement exactly and it is a **different tree from
the author's 99 / 2897 / 3**, which its result documents and which I did not
treat as a discrepancy. The three failures are the three this row has carried:
`test_diagnose.DecisionsAreCountedPerRecordNotPerMention.test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
`test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`.
Note that § 7 limit 11 — *"this branch is not rebased on `main`"* — is no longer
true of the tree I reviewed; that is the PMO's merge, post-dating the document,
not an author error.

**§ 7's 13 limits genuinely re-derive round 9's nine plus what the review
found, rather than renumbering.** Mapped one by one: R9-1→R10-3, R9-2→R10-4
(and R10-1 for the newly-found half), R9-3→R10-6, R9-4→R10-7, R9-5→R10-8,
R9-6→R10-9, R9-7→R10-10, R9-9→R10-12. R9-8 (the harness's `DIRTY` line) is
dropped, correctly, because the harness was fixed. Five are new: R10-1
(cross-module row), R10-2 (three unresolved alias shapes), R10-5 (`Watch` now
reaches a CLI, so round 9's `GATE_OFF` sentence no longer holds — an honest
retraction of the author's own prior claim), R10-11 (unrebased) and R10-13
(`test_the_row_splitter_half_is_owned_by_criterion_3` still asserts half its
docstring). The re-derivation is real work. It is the *content* of limit 1 that
this review fails, not its bookkeeping.

**`grep -rn "ROW_NAMES" tests/ bin/ viewer/` returns two lines**, both prose,
no code. The correction is right.

**No new test is green for a wrong reason that I could find.** None of the
three modules greps its own source (`__file__` appears only as `PERRY_HOME` and
`sys.path` roots; the single `read_text()` is the `NO_SHEBANG` bytes assertion
on a planted file). `drive_intake_write`'s fixture is not vacuous: the workload
records **34 distinct functions folding a decorated header cell**, and
`cmd_intake_write` is among them. The `assertEqual(rc, 0)` and the
`intake.jsonl` assertion are genuinely redundant — neutralising either leaves
all 8 tests green — but the property they claim ("a refusal cannot pass as
coverage") is still enforced, by
`test_every_reader_this_module_claims_to_watch_actually_folds_one`, which I
confirmed goes RED when `self.drive_intake_write()` is deleted.

**Guards checked for surviving their own deletion, beyond the mutated set.**

| deletion | result |
|---|---|
| `for attr in ("squash","norm")` → `for attr in ()` | **RED** (`test_the_rebinding_loop…`) — round 9's minor closed |
| `self.drive_intake_write()` → `pass` | **RED** (`test_every_reader_this_module_claims_to_watch_actually_folds_one`) |
| `"cmd_intake_write"` removed from `WATCHED` | **ALL GREEN** — see below |
| `assertEqual(rc, 0, …)` neutralised | ALL GREEN (redundant, property held elsewhere) |
| `assertTrue((root/"intake.jsonl").exists())` neutralised | ALL GREEN (same) |

The third row is the answer to the brief's question about limit 1's growth.
`WATCHED` is asserted in one direction only — every listed reader must fold —
and there is **no converse check**: nothing fails when a converted reader is
absent from the list. I verified by deletion. Combined with the finding above,
this is not merely "no guard against growing": the list is already short of the
readers that matter.

---

## Smaller results, reported because they are results

- **R10-2 reddens eight corpus entries, not the six § 3.1 lists** (`D32` and
  `D33` are also alias-resolution dependents). Safe direction; the table
  appears to predate those entries.
- **A row carried on an object attribute escapes too** (`t = T(line);
  [squash(c) for c in t.header]`, `P5`), on both trees. Same family as the
  dict; recorded so the fix covers both.
- **`_, ihdr = ctx["board"].section_table("Intake")` IS resolved.** I planted
  `[squash(c) for c in ihdr]` at `bin/perry-task:6456`, inside
  `_cmd_list_from_board`, a function the watch never reaches, and the static
  net caught it. The tuple-unpack-of-a-returned-row machinery is strong; it is
  specifically the dict/attribute step that is missing.
- **`WATCHED` cannot distinguish two readers with the same function name.**
  `header_language` exists in both `bin/perry-goals` and `bin/perry-task`, and
  the watch records bare function names, so one entry can be satisfied by
  either. Not load-bearing today; recorded.
- **`viewer/parsers.py § parse_decisions`** is still a live instance of the
  scalar second-rule class and still dead code. Agreed out of scope, per § 7.7.

---

## Verdict

```
=== VERDICT ===
task: TASK-050
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
         option C (binds)
checked: Worktree verified byte-identical to 4c2f07a (721 tracked blobs
         re-hashed, 0 mismatches; porcelain and ls-files -o both empty) at
         start and end. Round 10 code diff confirmed to be three files under
         tests/ (366+/13-) and untouched by the PMO's merge.
         bash tests/run on a git archive export of the REVIEWED MERGED TREE
         4c2f07a: 102 modules / 3034 tests / 3 failures, the three names this
         row has carried; test_header_index_is_the_only_fold 8 tests OK. The
         author's 99/2897/3 is a different tree and was not treated as a
         discrepancy.
         Round 9's ten alias shapes replanted one at a time into copies of BOTH
         trees: all escapes reproduce on round 9 and all are CAUGHT on round
         10, with both criterion-4 controls silent, so the guard is over the
         binding and not the name.
         Nine mutations reproduced on cp -R copies, each anchored by line and
         asserted on the exact old text: R10-1 -> D26 only, R10-3 -> D27 only,
         R10-4 -> D30 only, R10-6 -> D28 only (four single-entry mutations
         verified), R10-5 -> D32+D33, R10-7 -> D20 AND D21 (the D20 regression
         check holds), R10-8 and R10-9 red. R10-2 reddens EIGHT entries, not
         the six claimed — safe direction, recorded.
         D30's out-of-order re-plant confirmed genuine and the fixpoint now
         earns its place. R10-11 reproduced both halves: keyof=squash at
         perry-lint:250 reports 'bin/perry-lint:349: keyof(key)' and reddens
         three named tests, while the identical plant against round 9's
         header_rule.py returns []. R10-10 reproduced: the reviewer's plant
         reddens test_every_fold_of_a_header_cell_came_from_header_index on
         round 10 and is OK on round 9.
         Corpus measured 33/12/41+2 with nothing escaping or falsely flagged;
         all nine new DRIFT bodies read and traced to the round 9 review or to
         this round's green mutations — none invented to be easy.
         "Exactly one alias" verified by my own repo-wide AST sweep, not the
         round's machinery: bin/perry-lint:250 norm = squash, and nothing else
         outside tests/. offenders_by_symbol('.') == [] on the reviewed tree.
         Guard-deletion survival checked beyond the mutated set (five
         deletions, table above). § 7's 13 limits mapped one-by-one onto round
         9's nine; the re-derivation is real, not a renumbering.
         Worktree re-verified byte-identical at the END of the review (721
         blobs, 0 mismatches, porcelain and ls-files -o empty).
         Every plant, mutation and suite run on git-archive exports and cp -R
         copies under scratchpad/rjv4r10; no write-side Perry tool; no
         identifier minted.
not-checked: did not drive any reader end-to-end from argv — round 8's
         four-CLI byte-identical differential is carried, not re-measured; did
         not re-run bash tests/run on round 9's tree or on the author's own
         99/2897 export; did not investigate the three pre-existing failures
         beyond confirming their names; did not re-derive round 9's ruling that
         0 of 41 on SECOND_RULE is acceptable, which I carry; did not audit the
         write side, localized headers, or non-Python readers; did not verify
         R9-6's original D21-only attribution myself (carried from the round 9
         review, and R10-7's two-entry result is consistent with it).
proof: The amendment's sentence — "no call to `squash` on a row cell exists
       outside `header_index()`" — is falsified on a live production file with
       the plainest possible spelling: no alias, no wrapper, no exotic shape.
       A header row carried through a DICT KEY is invisible to
       offenders_by_symbol, and `["header"]` is this repository's own idiom
       for holding one.
       On a full copy at scratchpad/rjv4r10/uncovered-store, one line inserted
       into bin/perry_store.py § risk_plan, which already reads
       `header, keys = table["header"], table["keys"]` at :854:
           +    keys = [squash(c) for c in header]
         offenders_by_symbol('.')                            -> []
         test_header_index_is_the_only_fold.py   Ran 8 tests   OK
         test_one_header_rule.py                 Ran 13 tests  OK
         test_row_integrity.py                   Ran 33 tests  OK
       and bash tests/run on that same planted copy: 102 modules / 3034 tests /
       the SAME two red modules and three failure names as the unplanted tree
       (331.8s, 8 workers). Nothing in this repository notices.
       The round's stated reason for leaving this open does not apply to it.
       § 7 limit 1 calls it "interprocedural row-source recognition across
       module and dict boundaries — the widening the amendment rejects by
       name". It is not interprocedural: the shape escapes with NO module
       boundary at all (scratchpad/rjv4r10/rjv4r10_dict.py, copies, one plant
       at a time, control included):
         ESCAPED  t = {'header': split_row(line)}; [squash(c) for c in t['header']]
         ESCAPED  t = table_of(line); hdr = t['header']; [squash(c) for c in hdr]
         ESCAPED  [squash(c) for c in tables_of(line)[0]['header']]
         ESCAPED  t = T(line); [squash(c) for c in t.header]
         ESCAPED  t = {'header': split_row(line)}; [ops.norm(c) for c in t['header']]
         CAUGHT   CONTROL [squash(c) for c in split_row(line)]
       The first is local dataflow inside one function. _RowLocals already
       follows assignment, subscript, slicing, walrus, wrappers, a comprehension
       unwrap, a parameter this file passes a row to, and what a file-local
       function RETURNS — I confirmed it catches
       `_, ihdr = ctx["board"].section_table("Intake")` planted at
       bin/perry-task:6456. A dict subscript is one more source() case in that
       same machinery, not recognition of a fold expression, so option A is not
       the alternative here.
       And the dynamic half does not cover it. § 7 limit 1 asserts "every
       converted reader is now driven, so the uncovered set is empty today."
       Measured on the reviewed tree: SEVENTEEN live sites read a header row
       out of a dict key across bin/perry-task, bin/perry-tasks,
       bin/perry_store.py and bin/perry_md_store.py; driving the watch's own
       workload and collecting every function on a recorded stack, TWELVE of
       them sit in functions the watch never reaches at all — _cmd_list_from_board,
       _task_sections, ask_plan, ask_section_shape, ensure_columns,
       ensure_section_columns, find, plan, refuse_foreign_risk_table, risk_plan,
       risk_section_shape, task_tables. WATCHED is 16 functions against 45
       enclosing functions holding the 59 header_index/header_keys call sites,
       and it is asserted in ONE direction only: removing "cmd_intake_write"
       from WATCHED leaves all 8 tests green, so nothing fails when a reader is
       absent from the list.
       The corpus does not plant this shape. No DRIFT entry carries a row
       through a dict or an attribute, while D32 and D33 plant an alias passed
       to map and to sorted(key=) — the same structure as round 9's charge that
       "the corpus plants both HARDER indirections and neither easy one", with
       a different noun.
       RULING ON THE QUESTION THE ROUND TURNS ON: closing a static hole with a
       runtime watch DOES satisfy the amendment in principle, and I rule for
       the mechanism. The amendment nowhere requires the one-symbol check to be
       static, its own verification section is stated as "reverting it reddens a
       NAMED test", and round 9's accepted ruling on 0 of 41 already rests on a
       dynamic cover for the second-rule class — a reviewer cannot accept that
       and reject this. The cover is real and I measured it: the round 9
       reviewer's plant, in all three spellings, reddens
       test_every_fold_of_a_header_cell_came_from_header_index on round 10 and
       is OK on round 9. But a dynamic cover discharges a static hole only if
       the round MEASURES which sites it reaches and states the remainder. This
       round states the remainder as empty and the remainder is twelve. That is
       what fails.
       ALSO RULED, FOR THE AUTHOR: the claim that the reviewer's bin/perry-tasks
       plant crosses two independent holes is TRUE, reproduced here — the same
       plant written with a bare `squash` and no alias escapes round 9's tree
       identically ([] on tree-r9 for alias, bare, and bare-direct spellings).
       Round 9's prescribed fix could not have closed that demonstration, and
       the framing is not a rationalisation. Round 9's actual charge — the guard
       stated over the spelling — is fully closed: ten alias shapes caught, two
       criterion-4 controls silent, four mutations each reddening exactly one
       corpus entry. The three minor findings are closed with evidence, the two
       green mutations were reported as findings and their re-plants do real
       work, and the harness incident was recorded rather than re-run.
       The fix is again small and in the design's own idiom: teach source()
       that a subscript of a dict this file built — or of what a file-local
       function returned — is a row; plant the dict-carried and
       attribute-carried rows in DRIFT with their provenance; and either drive
       the twelve named functions or state them by name instead of "empty".
=== END VERDICT ===
```
