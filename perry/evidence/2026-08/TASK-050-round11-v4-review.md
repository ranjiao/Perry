# TASK-050 — V4 review round 11: **PASS**

> Fresh-context reviewer, 2026-08-30, against
> `perry/evidence/2026-08/TASK-050-spec.md § Amendment 2026-08-29 — USER-904,
> option C`, which binds.
> Under review: `901d89e`, tip of `coding/task-050-header-index`, in the
> read-only worktree at `scratchpad/review-050r11`. The code at `901d89e` is
> byte-identical to `9d00f1b` (`git diff 9d00f1b..HEAD -- tests/ bin/ viewer/`
> is empty); the two later commits are evidence only.
> **Every plant, mutation, trace and suite run below happened on `git archive`
> exports and `cp -R` copies under `scratchpad/rjr11/`**, never on the reviewed
> tree. No write-side Perry tool was run against any live checkout. No
> identifier was minted. Every file I wrote is prefixed `rjr11`.
> The reviewed worktree was re-hashed against `git ls-tree -r HEAD` at the end:
> **722 files, 0 mismatches**, `git status --porcelain` empty,
> `git ls-files -o --exclude-standard` empty.

**The number this round turns on is right, and I rebuilt it twice with my own
instrument.** The remainder is **8 of 76**, by function entry and by line
execution, with the same eight members as `UNCOVERED`. I then went one level
below that and validated the census's *static* verdict exhaustively: I planted
`[squash(_c) for _c in <the site's own expression>]` at all **76** sites, one at
a time, and `offenders_by_symbol`'s answer agreed with `header_sites()`'s
`static` flag **76 times out of 76**. The static half of the measurement is not
a self-report; it is exactly what it claims to be.

**The dict-carried case is genuinely closed, and the "provenance, not a
key-name list" framing survives adversarial testing.** A row put into a key
named `zulu` — a name in no list anywhere — is CAUGHT; a value put into a key
named `header` is silent. `CARRIED_KEYS` is a census spelling and
`offenders_by_symbol` never reads it.

**`WATCHED` no longer survives its own deletion, in both directions**, and the
"short by eight" claim is true: I measured, under round 10's own workload, that
`is_intake_register_header` was already being driven and already absent from
round 10's sixteen-name list.

I found three defects, all recorded below, none of which I judge a FAIL: the
round misdescribes the *mechanism* of 3 of its 8 declared uncovered sites (they
are file-local, not cross-module); the mutation table omits `D42` from five rows
so "nine single-entry mutations" is eight; and two branches of the round's own
new machinery still survive their own deletion, which its eighteen-probe sweep
did not reach.

---

## THE RULING THE BRIEF ASKS FOR

### A measured, listed remainder of 8 out of 76 DOES discharge the amendment.

Round 10's ruling — which I do not re-litigate — accepted that a runtime watch
can close a static hole. The rule it laid down for doing so was: *a dynamic
cover discharges a static hole only if the round MEASURES which sites it reaches
and STATES the remainder.* That is a rule about **knowing the number**, not
about the number being zero, and the round 10 FAIL was for asserting `empty`
against a measured twelve.

Round 11 supplies the measurement and I verified it three ways:

1. The **enumeration** is 76 sites — 59 `convert` (an argument of
   `header_index`/`header_keys`, derived from the blessed call and therefore
   spelling-free) and 17 `carried`. I reproduced 59/17, 51 convert-functions,
   17 carried-functions.
2. The **static verdict** is not asserted: 76 of 76 sites' verdicts match what
   an actual plant on that site's own expression does (§ 3 below).
3. The **dynamic reach** is measured, not claimed, and the remainder recomputes
   to 8 under a profiler I wrote myself and under a line-level trace, with the
   same eight members (§ 2).

And the remainder is asserted by a live named test that fails in **both**
directions — grow it and it goes red, shrink it and it goes red — which I
confirmed by three separate mutations (R11-21, R11-22, R11-23), one neutralising
the static half of the measurement and one the dynamic half.

Against that: it is true that the amendment's own sentence is falsifiable on a
live production file. I planted a bare dict-comprehension second rule at
`bin/perry-lint § check_cross_file` and all three header modules stayed green
(§ 6). But that site is one of the eight, named by file and function in
`UNCOVERED`, and its being listed is precisely what round 10 was failed for not
doing. Requiring the number to be 0 would require either whole-project
interprocedural analysis — which the amendment rejects by name — or driving
three CLIs end-to-end from `argv` and constructing a `Board` and a `ctx` for the
other five, which is a workload-engineering task the amendment nowhere asks for.

**If a future round wants a smaller number, the honest target is 5, not 0**:
the three `bin/perry-lint` sites are closable statically with one more `_paths`
case (§ 1), and the remaining five are genuinely rooted in a cross-module call.
I would not fail a round for 8, and I would fail one for stating a number it did
not measure.

---

## Finding 1 — the structural explanation for 3 of the 8 is wrong, and the fix is file-local

This is the round's principal defect and it is the same species as round 10's,
one rung smaller: a declared limit that misdescribes what it declares.

`UNCOVERED`'s docstring and § 2.3 both say:

> *"All eight are rooted in a call into ANOTHER MODULE — `perry_store.markdown_tables`,
> `perry_store.intake_table`, `board.task_tables()` — which is the
> interprocedural step `tests/header_rule.py` is file-local against by
> construction."*

For five of the eight that is true and I checked each one. For the three
`bin/perry-lint` sites it is false. `bin/perry-lint:1376` is:

```python
for header, rows in tables(strip_comments(board.read_text())):
    got = header_index(header)
```

and **both** `tables` (`bin/perry-lint:194`) and `tables_with_lines`
(`bin/perry-lint:209`) are defined in `bin/perry-lint`. There is no module
boundary in that chain. What defeats the static half is that `_paths` has no
comprehension branch, so `return [(h, [c for c, _ in r]) for h, r in
tables_with_lines(section)]` carries nothing.

Reproduced on a synthetic file with **no cross-module call anywhere**
(`scratchpad/rjr11/probe/rjr11_lint.py`):

```
L1_lint_shape_file_local       ESCAPED  []
L2_no_comprehension_link       CAUGHT   ['bin/pr.py:12: [squash(c) for c in header]', ...]
```

`L1` is `perry-lint`'s exact four-link shape, all file-local. `L2` is the same
file with the one comprehension link replaced by a plain `return
tables_with_lines(section)` — and it is CAUGHT. The escape is the comprehension,
not the module.

**Why this is recorded and not a FAIL.** It misstates *why* three entries are
open, not *which* or *how many*. The eight are named by file and function, the
count is right, and the guard that recomputes it is red in both directions. The
downstream harm is bounded and specific: a next round reading § 2.3 will believe
these three are behind the widening the amendment rejects, when they are one
`_paths` case away. § 2.3 and the `UNCOVERED` docstring should say so.

*(A smaller sibling: § 7 limit 1 says the eleven unresolved carried sites are
"in `bin/perry-task`, `bin/perry-tasks` and `bin/perry_md_store.py`". Ten are.
The eleventh is `bin/perry_store.py:533 § plan`, in the file the limit says
resolves — seven carried sites live in `perry_store.py` and six of them resolve.
§ 2.3 lists it correctly. Bookkeeping, not substance.)*

---

## What I verified independently, with the commands

### 2. The remainder is 8, and I rebuilt it without reusing `Reach` or `UNCOVERED`

`scratchpad/rjr11/rjr11_reach.py` runs the module's own `parse_everything()`
under my own `sys.settrace`, collecting both `call` and `line` events, and
recomputes the difference against `header_sites()`:

```
sites 76 static-blind 27

REMAINDER by function-entry: 8
   ('carried', 'bin/perry-task',        '_cmd_list_from_board')
   ('carried', 'bin/perry_md_store.py', 'plan')
   ('carried', 'bin/perry_store.py',    'plan')
   ('convert', 'bin/perry-lint',        'check_cross_file')
   ('convert', 'bin/perry-lint',        'check_reviews')
   ('convert', 'bin/perry-lint',        'check_verification')
   ('convert', 'bin/perry-task',        'task_projection_row')
   ('convert', 'bin/perry_store.py',    'plan')

REMAINDER by line-execution: 8   (identical members)
stated UNCOVERED: 8
func == stated: True
```

**The reconciliation to round 10 also reproduces, exactly.**
`scratchpad/rjr11/r10w/rjr11_rem10workload.py` — round 11's tree (so
`static-blind 27`, as § 2.2 states) driven by round 10's `parse_everything()`:

```
REMAINDER (func-entry), r11 tree + r10 workload: 20
REMAINDER (line-level): 20   same members: True
```

**20, on the nose**, and the line-level trace agrees. And the twelve:

```
carried sites in functions round10's workload never enters: 13
distinct names: 12
['_cmd_list_from_board', '_task_sections', 'ask_plan', 'ask_section_shape',
 'ensure_columns', 'ensure_section_columns', 'find', 'plan',
 'refuse_foreign_risk_table', 'risk_plan', 'risk_section_shape', 'task_tables']
```

**13 sites in 12 names — the round 10 reviewer's twelve, exactly, with `plan`
standing for two files.** Nine of them are now driven.

*(One wording slip: § 0.3 says the 20 was measured "under round 10's tree and
workload". Under round 10's actual tree — where the static half is round 10's,
`static-blind 36` — I measure **25**, not 20. § 2.2 states it correctly as
`9d00f1b` plus round 10's workload, and pins `static-blind=27` in every row. § 0
is loose where § 2.2 is right.)*

### 3. The static verdict is validated exhaustively, not asserted — 76 of 76

This is the check that decides whether the number can hide anything.
`scratchpad/rjr11/rjr11_plantall.py`: for each of the 76 sites, insert
`_rjprobe = [squash(_c) for _c in (<that site's own expression>)]` immediately
after the enclosing statement, in a mini root holding only that file, and ask
`offenders_by_symbol` whether the planted line is reported.

```
sites: 76
agree: 76 of 76
static True: 49  plant CAUGHT: 49
```

(My first pass reported 3 mismatches at `viewer/parsers.py`; all three were my
harness un-parenthesising an `IfExp` into a syntax error. With a `compile()`
guard and parentheses added, agreement is total. Recorded because a reviewer's
own artefact reported as a finding is the failure mode this row keeps meeting.)

So `static=True` means precisely what the round says it means, and the 27
static-blind sites are the real ones.

### 4. "Provenance, not a key-name list" — tested adversarially, and it holds

Rounds 5 through 9 were failed twice for allowlists, so this was the claim I
attacked hardest. `scratchpad/rjr11/probe/rjr11_probe.py`, one plant at a time
into a mini root:

```
A_odd_key_local_dict     CAUGHT   t = {"zulu": split_row(l)};  [squash(c) for c in t["zulu"]]
B_odd_key_returned       CAUGHT   t = table_of(l);             [squash(c) for c in t["zulu"]]
C_odd_attr               CAUGHT   t = T(l);                    [squash(c) for c in t.zulu]
D_header_key_values      ESCAPED  t = {"header": [rec.get("status"), ...]}; [squash(c) for c in t["header"]]
E_header_key_literal     ESCAPED  t = {"header": ["a", "b"]};   [squash(c) for c in t["header"]]
F_control_direct         CAUGHT   [squash(c) for c in split_row(l)]
G_control_values         ESCAPED  [squash(x["status"]) for x in recs]
```

A key name nothing has ever heard of is caught; the key name `header` holding
values is silent. `grep -rn CARRIED_KEYS tests/ bin/ viewer/` confirms the three
census names are read only inside `header_sites()` and never by
`offenders_by_symbol`. **This is provenance.** `ROW_NAMES` stays deleted.

### 5. The reviewer's exact plant, replayed

`bin/perry_store.py:855`, one line, bare `squash`, no alias:

```
$ python3 -c "... offenders_by_symbol('.')"
['bin/perry_store.py:855: [squash(c) for c in header]',
 'bin/perry_store.py:855: squash(c)']

test_header_index_is_the_only_fold  Ran 10  FAILED (failures=1)
    test_the_static_net_is_the_one_that_sees_dead_code
test_one_header_rule                Ran 13  FAILED (failures=2)
    test_nothing_outside_header_index_maps_squash_across_a_row
    test_value_normalizers_are_not_flagged
test_row_integrity                  Ran 33  OK  (not its criterion)
```

Three named tests, as claimed.

### 6. The dynamic cover is real where it is claimed

I planted `[squash(_c) for _c in table["header"]]` inside `bin/perry-task §
find` — static-blind, dynamically covered — and
`test_every_fold_of_a_header_cell_came_from_header_index` goes **RED**
(`stray == ['<listcomp>']`), with `offenders_by_symbol` still `[]`. So the
runtime half genuinely carries the sites the static half cannot see.

Conversely, at `bin/perry-lint § check_cross_file` — one of the declared eight —
`got = {squash(c): i for i, c in enumerate(header)}` leaves
`offenders_by_symbol` `[]` and all three header modules **OK**. That is the
remainder doing exactly what the round says it does, at a site the round names.

*(A caution for the next round, from my own harness: when I planted after a
`return` statement, the plant was unreachable and the watch stayed green. That
is § 7 limit 4 — function entry is not line execution — made visible. The
line-level trace in § 2 returns the same 8 today, so nothing is hiding behind
it, but the limit is real.)*

### 7. `WATCHED`, both directions

| mutation | result |
|---|---|
| **R11-18** delete `"cmd_intake_write"` (the round 10 reviewer's own deletion) | **RED** `test_watched_is_exactly_…` |
| **R11-19** drop `"is_intake_register_header"` (convert-and-forget) | **RED** `test_watched_is_exactly_…` |
| *my own*: ADD a bogus name `"rj_bogus"` | **RED** ×2 (`test_watched_is_exactly_…`, `…_actually_folds_one`) |
| `self.drive_the_carried_row_readers()` → `pass` | **RED** ×3 modules-worth (9 failures) |
| `self.drive_intake_write()` → `pass` | **RED** (4 failures) |

**The "short by eight" is true and I measured its most interesting half
independently.** Running *round 10's* `parse_everything()` (from `4c2f07a`)
against round 11's `Watch` and `header_sites()`:

```
round10 workload, converted readers folded through: 17
round10 WATCHED: 16
in workload but NOT in round10 WATCHED: ['is_intake_register_header']
in round10 WATCHED but not in workload: []
```

The *"one unwatched conversion away"* round 10 declared as a future risk had
already happened, exactly as § 3 says. 16 → 24; the eight added are
`is_intake_register_header`, `is_user_register_header`, `check_header`,
`ensure_columns`, `ensure_section_columns`, `task_section_headings`,
`replace_row`, `canonical_of`.

### 8. The corpus, and the two new controls really discriminate

`measure()` on a `git archive` export:

```
DRIFT 42  CLEAN 14  SECOND_RULE 41
{'drift_escaped': [], 'clean_flagged': [], 'second_rule_caught': []}
```

42/42, 0/14, 0/41. I read `D34`, `D36`, `D38`, `D39`, `D42`, `C13`, `C14`
against the round 10 review's own escape list; each quotes the line it comes
from and none was invented to be easy.

**`C13` and `C14` are not controls that cannot fail.** Swapping only what goes
into the dict — value → row, key name and shape unchanged — flips both:

```
C13_as_shipped     silent    d = {"status": record.get("status","")};  squash(d["status"])
C13_row_instead    CAUGHT    d = {"status": split_row(record)};        squash(d["status"][0])
C14_as_shipped     silent    yield {"status": r.get("status","")};     [squash(d["status"]) ...]
C14_row_instead    CAUGHT    yield {"status": split_row(r)};           [squash(c) ...]
```

and `D39` rewritten with the key `qq` instead of `header` is still CAUGHT. The
corpus discriminates on provenance, not on spelling.

### 9. Mutations — eight of the code mutations reproduced independently, all red

Run through my own fast corpus probe (each entry planted alone into a mini root;
validated against the full `measure()` on the unmutated tree — both report 0
escaped, 0 flagged, 0 second-rule caught).

| mutation | my measurement | claimed |
|---|---|---|
| attribute carries nothing (R11-3) | **`D37` only** | D37 only ✓ |
| `yield` is not a producer (R11-4) | **`D39` only** | D39 only ✓ |
| `out.append(...)` fills nothing (R11-5) | `D38` **and `D42`** | D38 only — **under-reported** |
| tuple UNPACK carries no paths (R11-6) | **`D38` only** | D38 only ✓ |
| loop targets carry no paths (R11-7 + R11-12) | `D39`, `D42` | D39 only / D42 only ✓ |
| an `IfExp` carries nothing (R11-17) | **`D38` only** | D38 only ✓ |
| a call carries nothing from its callee (R11-16) | `D35 D36 D37 D38 D39` **+ `D42`** | without D42 — under-reported |
| the path fixpoint runs once (R11-8) | `D37 D38` **+ `D42`** | D37 D38 — under-reported |

Plus, from my branch hunt: `source()` no longer consults `_paths` (R11-1) reddens
seven **+ `D42`**, and a dict literal carrying nothing (R11-2) reddens seven
**+ `D42`**.

**No mutation flagged a `CLEAN` entry and none made a `SECOND_RULE` entry
caught**, in any run.

**Finding 2 — the mutation table omits `D42` from five rows**, and one
consequence is that **"nine single-entry mutations" is eight**: R11-5 reddens
`D38` and `D42`. `D42` was added late (§ 1.5 says so — it came out of the
eleventh survival probe), and the table evidently predates it, exactly as round
10's R10-2 predated `D32`/`D33` — the very error this round corrects in § 8.
Every discrepancy is in the safe direction: the machinery is pinned by *more*
corpus entries than the table claims, never fewer.

**R10-2's correction verified:** `target = self._alias_target(...)` → `None`
reddens **eight** entries, `D25 D27 D28 D29 D30 D31 D32 D33`. § 8 is right.

**R11-1's honest exception verified:** it does *not* redden `D38`, because the
tuple-unpack branch writes into `self.scope` directly. Reported rather than
tidied, as § 5 says.

### 10. Baselines — runner AND tree

`bash tests/run` on a `git archive` export of `901d89e` (whose `tests/`, `bin/`
and `viewer/` are byte-identical to `9d00f1b`), at
`scratchpad/rjr11/base`:

```
102 modules · 3036 tests · 212.3s · 8 workers
✗ 2 module(s) red
```

three failures, the same three names the round states:

- `test_diagnose … test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`
- `test_kr_progress_provenance.TestBothOfTodaysWrongReadingsFlip.test_no_current_in_the_payload_claims_to_be_a_measurement`

**102 / 3036 / 3 reproduced.** I did not re-run `4c2f07a`; the 3034 figure was
measured by the round 10 reviewer and by the PMO, and 3036 − 3034 is exactly the
two new tests in `test_header_index_is_the_only_fold.py` (8 → 10), which I did
verify.

**The write hazard reproduces.** Before that run I recorded the md5s of
`.perry/events.jsonl`, `perry/BOARD.md` and `perry/intake.jsonl` in the export;
all three changed afterwards. TASK-249 confirmed independently. Nothing was run
in the reviewed worktree.

---

## Finding 3 — two branches of the round's own new machinery still survive their own deletion

The round's strongest self-check is § 1.5: eighteen survival probes, ten deleted
because nothing measured them. That work is real and I confirmed the deletions
landed — `extend`/`update`/`insert`/`setdefault`, the iterable-wrapper,
`.copy()`, `.get("k")` and `BoolOp` cases in `_paths`, the slice branch, the
integer-subscript branch and the parameter path-carrying are all absent from the
shipped `tests/header_rule.py`.

**The sweep did not reach everything.** I ran twelve further neutralisations,
each alone, checking the whole corpus *and* the live census (`sites`,
`static-blind`, `offenders`) — the same two-sided criterion the round used:

```
baseline census (sites, static-blind, offenders): (76, 27, 0)

YieldFrom step                     SURVIVES   escaped=[] flagged=[] census=(76, 27, 0)
ast.Set in list/tuple literal      SURVIVES   escaped=[] flagged=[] census=(76, 27, 0)
_bind_element scope add            pinned     census=(76, 28, 0)
unpack `() in sub_p` half          pinned     escaped=['D38']
pos: on a literal                  pinned     escaped=['D38','D39']  census=(76, 31, 0)
elem on a literal                  pinned     escaped=['D36']        census=(76, 29, 0)
Subscript elem fallback            pinned     escaped=['D36','D38']  census=(76, 35, 0)
self.header -> class rpaths        pinned     escaped=['D37']
attribute assignment target        pinned     escaped=['D37']
plain name carries paths           pinned     escaped=[D34 D35 D37 D38 D40 D41]
Dict literal carries nothing       pinned     escaped=[D34 D35 D36 D42 D38 D39 D40 D41]
source() no longer consults _paths pinned     escaped=[D34 D35 D36 D42 D37 D39 D40 D41]
```

Two survive: the `YieldFrom` step in `_pass`
(`step = () if isinstance(node, ast.YieldFrom) else ("elem",)` — no corpus entry
uses `yield from`, no live site depends on it) and `ast.Set` in the
list/tuple/set literal branch of `_paths`. Both are strictly widening and both
are five characters, so the harm is small; but § 1.5 and § 9.2 present the sweep
as this row's own lesson applied to its own code, and the ten deleted branches
were deleted on exactly this evidence. These two should have gone with them, or
been planted.

**Smaller survivors, same category as round 10's redundant `assertEqual(rc, 0)`:**

| deletion | result |
|---|---|
| `assertGreater(len(sites), 60)` removed | ALL GREEN |
| `assertGreater(len(converters), 40)` removed | ALL GREEN |
| `with self.assertRaises(task.Refused):` → plain `try/except` | ALL GREEN |
| `assertEqual(rc, 0, …)` neutralised | ALL GREEN (carried from round 10) |

The first two are tripwires against a future degenerate census, not guards over
today's behaviour, and I do not charge them. The third means the refusal
assertion is a correctness check, not a coverage one — entering the function is
what the watch needs, and `try/except` still enters it.

---

## Green-for-the-wrong-reason: none found

Checked against the four modes this row has produced before.

- **No test greps its own source.** `__file__` appears three times across
  `test_header_index_is_the_only_fold.py` and `test_one_header_rule.py` and
  every occurrence is a `PERRY_HOME` or `sys.path` root. There is no
  `read_text()` over a source file in either.
- **The condemned test is gone.** `grep -rn
  test_the_cross_module_case_is_the_price tests/` returns nothing.
- **No fixture parses zero rows.** `drive_the_carried_row_readers` asserts real
  values off the parse — `board.find("TASK-001")[0] == "Work"`, `"Verification"`
  in `ensure_columns(...)`, `"Severity"` in `ensure_section_columns(...)`,
  `"TASK-001"` in `replace_row(...)`, `canonical_of("**Title**") == "title"` —
  and neutralising the whole method reddens three tests.
- **No control that cannot fail.** `C13`/`C14` proved discriminating above.
- Both new tests are proven non-vacuous by mutation on both of their halves
  (R11-21/22/23 for the remainder; R11-18/19 and my bogus-name plant for
  `WATCHED`).
- `grep -rn ROW_NAMES tests/ bin/ viewer/` returns three lines, all prose in
  docstrings. Correct.

---

## What I did NOT check

- **I did not reproduce all 23 mutations.** I reproduced 14 (eight code
  mutations through my own corpus probe, R11-18/19/21/22/23 through the test
  module, plus R10-2), chose to spend the rest of the budget on the exhaustive
  76-site plant sweep and the independent remainder rebuild, and hunted twelve
  further branches of my own choosing. The nine I did not run are R11-2, R11-9,
  R11-10, R11-11, R11-13, R11-14, R11-15, R11-20 and part of R11-1 — though my
  branch hunt covers the same code for R11-1, R11-2, R11-9, R11-10, R11-11 and
  R11-15 with my own anchors, and all six were pinned.
- **I did not run `test_header_rule_harness.py` as a module** (147 s). I ran
  `measure()`, which is its subject, plus the corpus-audit invariants by
  reading.
- **I did not re-run `bash tests/run` on `4c2f07a`.** The 3034 figure is the
  round 10 reviewer's and the PMO's; I verified only 3036 on this tip and the
  +2 accounting.
- **Criterion 2 (`perry-lint`'s `norm` IS `squash`, by identity) and criterion 5
  (a decorated header resolves across four tools)** I did not re-derive; they
  are carried by suites that are green on this tip.
- **Round 8's four-CLI byte-identical differential** is carried, not
  re-measured — § 7 limit 12 says so.
- **The write side, localized headers and non-Python readers** are out of scope
  per § 7 limit 9, and `viewer/parsers.py § parse_decisions` remains agreed out
  of scope.
- **One census-completeness question I could only bound, not close.** § 7 limit
  3 states that `CARRIED_KEYS` undercounts a header row held under a fourth key
  name. I swept the tree for dict values and attribute targets the static net
  resolves as rows and found only `header`, `keys`, `end`, `cells` and `_cells`
  — none of the last four is a *header* row read back for folding today. There
  is a further class the census does not cover at all: a header row held in a
  plain local from a cross-module call, never subscripted and never passed to
  `header_index`. I found no live instance, but the census would not count one.

---

## Summary of what is charged and what is not

**Charged (recorded, not fatal):**

1. § 2.3 and `UNCOVERED`'s docstring misdescribe 3 of the 8 as cross-module.
   `bin/perry-lint § tables` and `§ tables_with_lines` are both file-local; the
   escape is `_paths` having no comprehension branch, and a minimal file-local
   reproduction with the comprehension link removed is CAUGHT. Fix the sentence,
   or close the three — the honest target for the next round is 5, not 0.
2. The mutation table omits `D42` from five rows, so **"nine single-entry
   mutations" is eight**. Safe direction; the same predates-the-corpus-entry
   bookkeeping the round corrects for round 10 in § 8.
3. Two branches of the new machinery — the `YieldFrom` step and `ast.Set` in the
   literal branch — still survive their own deletion, corpus fully caught and
   live census unmoved. Delete them or plant them.
4. § 7 limit 1 attributes eleven carried sites to three files; one of the eleven
   (`bin/perry_store.py:533 § plan`) is in the file the limit says resolves.
   § 2.3 has it right.
5. § 0.3's "20 under round 10's tree and workload" is loose — under round 10's
   actual tree it is 25. § 2.2 states it correctly.

**Not charged, and verified:** the remainder of 8 (twice, two instruments); the
static verdict at all 76 sites; the dict/attribute closure and its provenance
framing under adversarial key names; the reviewer's exact plant and its three
named tests; the 6/11 split; the reconciliation to 20 and to the reviewer's
twelve; `WATCHED` in both directions and the "short by eight" including
`is_intake_register_header` already being driven; the corpus at 42/14/41 with
0/0/0 and two controls that genuinely discriminate; fourteen mutations all red;
R10-2 at eight; the baseline 102/3036/3 with the same three names; and the ten
deleted branches actually being gone.

**Verdict: PASS.** Round 10's rule was *measure the reach and state the
remainder*. This round measures it, states it, asserts it in a guard that fails
in both directions, and the number survives an independent rebuild and an
exhaustive validation of the instrument that produced it. Eight of seventy-six,
named by file and function, discharges the amendment.
