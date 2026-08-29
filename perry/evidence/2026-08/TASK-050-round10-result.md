# TASK-050 round 10 — result

> Branch `coding/task-050-header-index`, forked from `main` at `6c0d041`.
> Written against `perry/evidence/2026-08/TASK-050-spec.md § Amendment
> 2026-08-29 — USER-904, option C`, which binds.
>
> **This document supersedes `TASK-050-round9-result.md` for everything it
> restates.** Round 9's result is NOT retracted — its review ruled its core
> correct — so it stays in place as the record of what round 9 did, with a
> pointer here and one factual correction made in place (§ 4.3). There is one
> result of record and it is this one.

Round 9's review was a FAIL and mostly a vindication. It ruled for the round on
the question the round turned on — **0 of 41 on `SECOND_RULE` is ACCEPTABLE
under option C** — verified the deletion of every variable-name allowlist,
re-enumerated all 39 `squash`/`norm` call sites by its own AST walk and found no
third live one, reproduced all ten mutations, rebuilt the corpus independently
and found no pruning, and confirmed the argument for deleting the shape net by
planting round 8's own declared false positive.

It failed the round on the **corollary of that vindication**: with the shape net
gone, the drift half carries the whole static claim, and the drift half
recognised the one rule by the **function's name** rather than by the symbol.

**Round 10 is that five-line gap, closed, plus the three minor findings and the
two green mutations that closing it exposed.** No production code changed:
`git diff --stat b5e7be3 HEAD` is three files, all under `tests/`.

---

## 0. What changed, in one list

| # | change | why |
|---|---|---|
| 1 | `_RowLocals` resolves a **direct alias binding** — bare assignment, `from … import … as`, attribute access — to a fixpoint; `_blessed_calls` and the scalar half ask the file's own resolved sets | round 9 review, the FAIL: `fold = squash` walks past a check stated over the spelling |
| 2 | corpus `D25`–`D33`, nine entries, each quoting the review line it comes from | the corpus planted both HARDER indirections and neither easy one |
| 3 | `_plant` stops prepending a shebang to `D20` and `S12`; `NO_SHEBANG` and a new auditability test | round 9 review, minor 1: `D20` could not discriminate the hole it names |
| 4 | `Watch.__enter__`'s rebinding loop is **kept and given a test** | round 9 review, minor 2: it survived its own deletion with all 7 tests green |
| 5 | `bin/perry-tasks` is **driven** by the runtime watch (`cmd_intake_write`), and added to `WATCHED` | round 9 § 6.2's own declared limit, and the file the reviewer planted its escape into for exactly that reason |
| 6 | `D30` re-planted out of order; `D32`/`D33` added | two of this round's own mutations came back GREEN — § 3.2 |

---

## 1. The FAIL, closed — the guard is now over the SYMBOL

### 1.1 What escaped, reproduced first

The reviewer's probe, replayed on `b5e7be3` before touching anything
(`scratchpad/r10/probe_alias.py`, one plant at a time into a copy, every body
`[fold(c) for c in split_row(line)]`, control included):

```
CAUGHT  A  fold = lambda s: squash(s)   (== corpus D10)
ESCAPED B  fold = squash
ESCAPED C  fold = squash, SCALAR on a cell
CAUGHT  D  def fold(s): return squash(s)  (== corpus D09)
ESCAPED E  from tables import squash as fold
ESCAPED F  import tables; fold = tables.squash
ESCAPED G  the repo's OWN idiom renamed: keyof = squash
CAUGHT  H  CONTROL: plain squash
ESCAPED I  transitive: a = squash; fold = a
ESCAPED J  function-local alias inside the reader
```

Reproduced exactly, including the two the reviewer recorded without charging.
The two *harder* indirections were resolved and the one-liner was not, and
**why** is worth stating: `def fold(s): return squash(s)` and `fold = lambda s:
squash(s)` are caught not by the alias machinery but by parameter
provenance — the row cell reaches the wrapper's parameter, so `squash(s)`
inside it is a scalar fold of a cell. A bare `fold = squash` has no body for a
cell to reach.

### 1.2 The fix

`_RowLocals` now builds `self.aliases: dict[str, str]` — *local name → the
BLESSED name it IS* — from three binding shapes, run to a fixpoint, and exposes
two per-file frozensets:

- `rows.blessed` = `BLESSED` ∪ every name this file bound to one of them;
- `rows.rule` = `THE_RULE` ∪ every name this file bound to `squash`/`norm`.

`_blessed_calls(elt, rows.blessed)` and `name in rows.rule` replace the module
constants at the four sites that asked them.

**This is not a list of names.** A name is in `aliases` because a binding in
*this file* put the blessed function object in it, and for no other reason —
the same standard `by_name` already meets for `def` and `lambda`. File-wide
rather than per-function, because an import binds at module level and is called
from every function in the file.

Deliberately **not** resolved, and recorded as a limit in § 6 rather than
widened: a rebinding through a container (`FOLDS["k"] = squash`), a function
that *returns* the rule, and a binding made in another module.

### 1.3 After

All ten probe cases now resolve as they should, and both clean controls stay
silent:

```
CAUGHT  A B C D E F G H I J
ESCAPED K  alias of a NON-rule name (tidy = str.strip) used on a row
ESCAPED L  alias of the rule used as a VALUE normalizer, not on a row
```

`K` and `L` are the criterion-4 half of the same change and they are why it is
stated over the *binding* and not over the *name*.

### 1.4 On the live tree, nothing moved

```
$ offenders_by_symbol('.')  ->  []
$ every alias in the whole tree:
  bin/perry-lint  {'norm': 'squash'}
```

**One alias exists in this repository and it was already blessed.** That is the
point of the finding: `bin/perry-lint:250` is literally `norm = squash`, and it
was seen only because `norm` happens to sit in `BLESSED`.

---

## 2. The live demonstration — the repository's own idiom, renamed

`R10-11`, on `bin/perry-lint` itself, two sites, anchored and asserted on the
exact old text (`scratchpad/r10/mutate_lint.py`):

```
bin/perry-lint:250   norm = squash            +  keyof = squash
bin/perry-lint:348   value = key              ->  value = keyof(key)
```

That is R9-1's site with one difference: the alias is spelled with an
untrusted name.

```
baseline: both targets GREEN
test_one_header_rule                    RED: test_nothing_outside_header_index_maps_squash_across_a_row
                                             test_value_normalizers_are_not_flagged
test_the_static_net_is_the_one_that_sees_dead_code   RED
offenders_by_symbol -> ['bin/perry-lint:349: keyof(key)']
restore md5 OK  e1c277b2336f22b6ed490c8205fd2f0f   tree after restore: clean
```

Counter-check, the same plant against round 9's own `tests/header_rule.py`
(`git archive b5e7be3`):

```
round 9 header_rule, same plant -> []  <-- ESCAPED
```

Caught here, silent there, on a live reader.

---

## 3. Mutations — eleven, each anchored by line and asserted on the old text

Harness: `scratchpad/r10/mutate.py`. It **refuses a dirty tree**, **asserts the
target test is GREEN before mutating**, clears `__pycache__`, waits past the
whole-second boundary, restores the whole file and verifies `md5` plus a clean
`git status`. Round 9's reviewer confirmed that discipline is why round 9's
hand restore was clean; it is unchanged.

### 3.1 The nine that reddened a named test

| # | site | target | RED |
|---|---|---|---|
| R10-1 | `header_rule.py:337` `a.name in BLESSED` → `in ()` | `test_each_drift_shape_is_caught` | **`D26`** only |
| R10-2 | `header_rule.py:342` `target = self._alias_target(…)` → `None` | same | **`D25` `D27` `D28` `D29` `D30` `D31`** |
| R10-3 | `header_rule.py:310` `name = value.attr` → `return None` | same | **`D27`** only |
| R10-4 | `header_rule.py:332` fixpoint `range(4)` → `range(1)` | same | **`D30`** only |
| R10-5 | `header_rule.py:584` `rows.blessed` → `BLESSED` | same | **`D32` `D33`** |
| R10-6 | `header_rule.py:611` `rows.rule` → `THE_RULE` | same | **`D28`** only |
| R10-7 | `header_rule.py:132` `is_python` back to round 8's (`suffix ⇒ .py`, else shebang) | same | **`D20` AND `D21`** |
| R10-8 | `test_header_rule_harness.py:84` `NO_SHEBANG` → `frozenset()` | `test_the_no_shebang_entries_are_planted_without_one` | RED |
| R10-9 | `test_header_index_is_the_only_fold.py:213` `for attr in ("squash","norm")` → `for attr in ()` | `test_header_index_is_the_only_fold.py` | `test_the_rebinding_loop_watches_a_readers_own_reference` |

**The three alias forms the brief names, each pinned to its own mutation:**
`fold = squash` → R10-2 (`D25`); `from tables import squash as fold` → R10-1
(`D26`, and *only* `D26`); `import tables; fold = tables.squash` → R10-3
(`D27`, and *only* `D27`).

**R10-7 is the D20 regression check the brief asked for.** Round 9's R9-6
reddened `D21` and **not** `D20`, which was the reviewer's proof that the entry
could not discriminate. The same mutation now reddens both. The problem is
closed, not moved.

### 3.2 The two that came back GREEN, and what they cost

Both were run before the entries below existed, and both are reported because a
green mutation is the finding.

- **R10-4 was GREEN.** `D30`'s alias chain (`a = squash; fold = a`) was written
  in order, and `ast.walk` is breadth-first, so one pass already resolves it —
  the fixpoint was dead weight the corpus could not see. `D30` is re-planted
  with its first link nested inside an `if`, which reverses the order the walk
  reaches the two links in and is valid Python. R10-4 then reddens `D30` and
  only `D30`.
- **R10-5 was GREEN.** Every alias entry in the corpus was *redundantly* caught
  by the scalar half, because an alias inside a comprehension is a `Call` node.
  `D32` (`map(fold, row)`) and `D33` (`sorted(key=fold)`) pass the alias
  without calling it, so the mapping half is the only thing that can see them.
  R10-5 then reddens exactly those two.

### 3.3 R10-10 — the reviewer's own end-to-end plant, replayed verbatim

`scratchpad/r10/mutate_tasks.py`, the two sites exactly as the round 9 review
states them:

```
bin/perry-tasks:80   from tables import header_index, squash   +  _fold = squash
bin/perry-tasks:926  keys = header_index(perry_store.intake_table(board, ops)["header"],
                                         alias=ops.norm)
                  -> _hdr = perry_store.intake_table(board, ops)["header"]
                     keys = [ops.norm(_fold(c)) for c in _hdr]
```

```
baseline: both targets GREEN
test_every_fold_of_a_header_cell_came_from_header_index   RED
test_one_header_rule                                      RED: NOTHING
offenders_by_symbol (the STATIC half) -> []
restore md5 OK  4a8ce792a8ce15d24b49f182c53da431   tree after restore: clean
```

**Read that second and third line, because they are the honest part of this
round.**

---

## 4. What the reviewer's end-to-end case actually was, and it was not only the alias

The round 9 review's prescribed fix — *"resolve module-level `NAME = <blessed>`
and `from tables import squash as NAME` bindings into the blessed set … then add
B/E/F to `DRIFT`"* — is implemented in full, and **it does not close the
reviewer's `bin/perry-tasks` demonstration.** Measured, not argued:

```
$ # round 10 tree, the reviewer's plant, static half only
offenders_by_symbol('bin/perry-tasks') -> []
```

The reason is not the alias. It is `_hdr`:

```python
_hdr = perry_store.intake_table(board, ops)["header"]
```

`intake_table` lives in **another module** and the row is carried through a
**dict key** (`perry_store.markdown_tables` builds `{"header": split_row(…), …}`).
`_RowLocals` is file-local by construction, so `_hdr` is not a row to it — with
or without the alias. The same plant written with a bare `squash` escapes round
9's tree identically, which is the proof the two holes are independent:

```
$ round 9's own header_rule, `[squash(c) for c in _hdr]`, no alias at all
ESCAPED
```

**Closing that statically would be interprocedural row-source recognition
across module and dict boundaries — the widening the amendment rejects by
name** ("Option A, widening the source-expression recognition for an eighth
round"). So it is not closed statically, and the design's own answer is used
instead.

### 4.1 `bin/perry-tasks` is now driven

Round 9 § 6.2 declared it: *"`bin/perry-tasks` is converted and not driven."*
The reviewer planted there for exactly that reason. `cmd_intake_write(root,
["--from-board"])` now runs **in process** inside `Watch`, against a throwaway
root carrying a `**Arrived**` intake header, and `cmd_intake_write` is added to
`WATCHED` so the claim is asserted rather than listed. The driver asserts `rc ==
0` and that the store was written, so a refusal cannot pass as coverage.

Under the plant, `_fold("**Arrived**")` is called straight from
`cmd_intake_write` with no `header_index` in the stack, and
`test_every_fold_of_a_header_cell_came_from_header_index` goes **RED**. That is
a named test, and it is the half of the design that is blind to spelling
altogether.

### 4.2 So what covers what

| the shape | seen by | how |
|---|---|---|
| the rule applied to a row a **local** dataflow reaches, under any alias | `offenders_by_symbol` | § 1, § 2 — statically, in dead code too |
| the rule applied to a row a **cross-module** call produced | `test_header_index_is_the_only_fold` | § 4.1 — at runtime, if a parse reaches it |
| a reader that invents its **own** rule | `test_every_decorated_header_cell_reached_header_index` | it stops reaching `header_index` |

The reviewer's ruling on the third row is carried rather than re-derived, and it
is measured rather than argued: reverting `viewer/parsers.py:1833` reddens
`test_every_decorated_header_cell_reached_header_index`, and so did the
reviewer's own **value-identical** alias fold at the same site, reporting
`missing: ['due', 'kr']`. That is what makes 0 of 41 a stated limit and not a
hole.

### 4.3 The correction to round 9's result

`grep -rn "ROW_NAMES" tests/ bin/ viewer/` returns **two** prose lines, not the
four round 9's result claims. Both are prose saying the set was deleted; there
is no code. The load-bearing half of the sentence was true and the count was
wrong. Corrected in `TASK-050-round9-result.md` in place, so the two documents
do not disagree.

---

## 5. The corpus and the three fractions

`python3 -c "import test_header_rule_harness as H; print(H.measure())"` on this
tree:

```
{'drift_escaped': [], 'clean_flagged': [], 'second_rule_caught': []}
DRIFT 33   CLEAN 12   SECOND_RULE 41   UNRECOVERABLE 2
```

| corpus | size | result |
|---|---|---|
| `DRIFT` — must all be caught | **33** (was 24) | **33 of 33 caught** |
| `CLEAN` — criterion 4, must all be silent | **12** | **0 of 12 flagged** |
| `SECOND_RULE` — the declared limit, asserted to escape | **41** (+2 unrecoverable) | **0 of 41 caught** |

The nine new `DRIFT` entries and their provenance:

| entry | shape | source |
|---|---|---|
| `D25` | `fold = squash` | round 9 review, ESCAPED B |
| `D26` | `from tables import squash as fold` | round 9 review, ESCAPED E — the case `D06` does not cover, because `D06` aliases onto `norm`, a name already in `BLESSED` |
| `D27` | `fold = tables.squash` | round 9 review, ESCAPED F |
| `D28` | bare alias applied to ONE CELL | round 9 review, ESCAPED C |
| `D29` | `keyof = squash`, the repo's own idiom renamed | round 9 review, ESCAPED G |
| `D30` | a chain of aliases, bound OUT OF ORDER | round 9 review's prescribed fix + this round's R10-4 |
| `D31` | an alias bound inside the reader | round 9 review, and a rebinding is not obliged to sit at module level |
| `D32` | `map(fold, row)` — alias never CALLED | this round's R10-5 |
| `D33` | `sorted(key=fold)` — alias never CALLED | round 7 Finding 2, planted for an alias |

`0 of 41` is unchanged and is the same declared limit round 9's review ruled
ACCEPTABLE, for the reason it gave: detecting a from-scratch fold *is* source-
expression recognition, so failing the row on it orders the option the
amendment rejects by name. R9-9 reproduces — the row inference that would raise
that number is the same inference that reports `C06` — so 41-of-41 and 0-of-12
cannot both be had.

---

## 6. Baselines — runner AND tree, every one measured here

| runner | tree | modules | tests | failures |
|---|---|---|---|---|
| `bash tests/run` | round 10 `HEAD` = `a1ff426`, on a `git archive` export | **99** | **2897** | **3** |
| `bash tests/run` | `main` @ `3c7c8ba`, on a `git archive` export | 101 | 3019 | 3 |
| `python3 -m unittest discover -s tests` | round 10 `HEAD`, same export | — | **2897** | **6** |

The three under `bash tests/run` are identical on both trees and are the three
this row has carried since round 8:

```
test_diagnose.DecisionsAreCountedPerRecordNotPerMention
    .test_the_queue_register_reconciles_with_the_queue_on_this_repository
test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip
    .test_no_current_in_the_payload_claims_to_be_a_measurement
```

`discover` is exactly 3 more, and the three extra are the
`test_risks_store.TestTheReadersAreOneFunction` double-import artefact round 9's
reviewer corroborated independently and measured `OK` in isolation. That closes
the last carried figure on this row.

**`+2` over round 9's 99 / 2895 / 3** is `test_the_no_shebang_entries_are_planted
_without_one` and `test_the_rebinding_loop_watches_a_readers_own_reference`.
Nothing else moved.

**`main` has moved and this branch has not been rebased.** Round 9 was reviewed
against `main` @ `6c0d041` (98 / 2882 / 3); `main` is now `3c7c8ba` at 101 /
3019 / 3 — 3 modules and 137 tests this branch has never seen. The failure set
is the same three on both, so nothing here is hidden by the gap, but the merge
is a real one and is named in § 7.

**Call sites: 59, unchanged.** Counted by AST (`ast.Call` whose callee is
`header_index` or `header_keys`) over `readers_under(.)`. No reader was
converted this round; `git diff --stat b5e7be3 HEAD` is three files, all under
`tests/`, 366 insertions and 13 deletions.

---

## 7. What was NOT done, and what is not proven

**Round 9's § 6 declared nine limits and the reviewer found a tenth that was
in none of them.** That is the charge this round is answering, so this list is
re-stated from scratch rather than amended, and the two entries the review
created are first.

1. **The static net does not see a row a CROSS-MODULE call produced.** § 4.
   `perry_store.intake_table(board, ops)["header"]` is a row and
   `offenders_by_symbol` cannot tell; the same is true of any row reaching a
   reader through another module's dict, attribute or return. This is the hole
   the round 9 reviewer's end-to-end plant actually walked through — the alias
   was only half of it — and it is **not closed statically**, because closing
   it is interprocedural source recognition and the amendment rejects that by
   name. What covers it is the runtime watch, and only for readers a parse
   reaches: `bin/perry-tasks` is now one of them, and the plant reddens
   `test_every_fold_of_a_header_cell_came_from_header_index`. A converted
   reader that is **not** driven and takes its row from another module is
   covered by neither half. Every converted reader is now driven, so the set is
   empty today; it is one unwatched conversion away from not being.
2. **Three alias shapes are resolved and three are not**: a rebinding through a
   container (`FOLDS["k"] = squash`), a function that RETURNS the rule
   (`def picker(): return squash`), and a binding made in another module. The
   first two are the second-rule class by another road; the third is (1).
3. **The static net cannot see a second RULE — 0 of 41, measured.** Unchanged,
   and ruled ACCEPTABLE by the round 9 review under option C. § 5.
4. **The runtime watch only sees code a parse reaches.** A fold in a branch
   these fixtures do not take, or for a ninth column beyond the eight in
   `HEADER_KEYS`, is still invisible. `WATCHED` is now 16 readers and every one
   is asserted.
5. **`Watch` now reaches a CLI command function.** `cmd_intake_write` writes a
   store to a throwaway root. Round 9's result could say "none reaches a CLI, so
   `tests/gate.py`'s `GATE_OFF` is not involved"; that sentence no longer holds.
   The driver builds its own `.perry/config.md` without `GATE_OFF` and asserts
   `rc == 0`, so a gate refusal would fail the test rather than pass silently.
6. **Round 5's probe cases `B` and `I` are unrecoverable** and are counted, not
   invented.
7. **`viewer/parsers.py:2582` (`parse_decisions`) is untouched** — a live
   instance of the scalar second-rule class, established as dead code by rounds
   3, 4 and 8. Not in scope; recorded so round 11 does not rediscover it.
8. **`bin/perry-state § cells_of` was not removed** and `viewer/` was not
   renamed. Separate rows, per the spec's closing note.
9. **The three pre-existing failures were not investigated**, only measured as
   identical on both trees under both runners.
10. **No reader was driven end-to-end from `argv`.** Round 8's reviewer's
    four-CLI byte-identical differential is **carried, not re-measured**.
    `cmd_intake_write` is driven as a function, not through `main()`.
11. **This branch is not rebased on `main`** (§ 6). 3 modules and 137 tests
    exist on `main` that this branch has never run together with its own
    changes.
12. **`squash`'s docstring still says "do not map this across a header row"**,
    which is half the rule. A one-line docs edit, not made, so this round's diff
    stays what it says it is.
13. **`test_the_row_splitter_half_is_owned_by_criterion_3` still asserts half
    its docstring** — round 9's review, minor. It checks `SPLIT_RE` and not the
    scan's coverage of `bin/` and `viewer/`. The reviewer verified that half by
    planting; it is recorded, not fixed, because the lean is on another module's
    test and widening this one duplicates it.

---

## 8. The three minor findings, closed

1. **`D20` could not discriminate the hole it names.** `_plant` prepended
   `SHEBANG` unconditionally, so `D20 "no suffix and NO SHEBANG"` and `S12`,
   same subject, were planted **with** one. **Fixed on the plant side**, not on
   the entry: `NO_SHEBANG` is two paths — keyed on the path the corpus already
   guarantees unique via `test_no_two_entries_are_planted_at_the_same_path` — and
   `test_the_no_shebang_entries_are_planted_without_one` asserts the bytes on
   disk, that every exempted path is a real entry, and that the set and the
   labels agree in both directions. Regression check, per the reviewer's own
   proof: R10-7 (round 8's `is_python`) now reddens **`D20` and `D21`**, where
   R9-6 reddened `D21` alone.
2. **The `Watch` rebinding loop survived its own deletion.** **Kept and given a
   test.** What it protects is real and is what this row forbids — a reader
   holding its own reference to the rule and calling it directly — and nothing
   does that today, which is why the loop was silent. So it is exercised
   deliberately: `bin/perry-lint` holds `norm = squash`, and
   `test_the_rebinding_loop_watches_a_readers_own_reference` asserts the loop
   redirects it, that a fold through it reaches the watch, and that `__exit__`
   puts it back. R10-9 (`for attr in ():`) reddens it.
3. **`grep ROW_NAMES` returns two lines, not four.** § 4.3. Corrected here and
   in round 9's result.
