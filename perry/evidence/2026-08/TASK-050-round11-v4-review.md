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

---
---

# Delta confirmation, `901d89e` → `642091f`: **CONFIRMED**

> Same reviewer, same day. Scope is the delta only — the PASS above stands and
> nothing in it is re-derived except the two numbers I was asked to re-check.
> Everything below ran on a `git archive` export of `642091f` at
> `scratchpad/rjr11d/` and `cp -R` copies of it; the reviewed worktree at
> `scratchpad/review-050r11` was re-hashed against `git ls-tree -r HEAD` after
> all of it — **722 files, 0 mismatches**, still at `901d89e`, `git status
> --porcelain` and `git ls-files -o` both empty. Nothing was run inside it.
> `git diff --stat 901d89e..642091f -- bin/ viewer/ schema/ templates/ packs/
> modes/` is empty: still no production code.

**All three corrections are real, and correction 3's new machinery does what it
claims.** The four newly-found branches were genuinely unpinned before and are
each pinned by exactly one entry now; `R11-24` reddens `D43` alone; the twenty
greens I spot-checked are green and none is a detection branch; the anchors work.
The remainder did not move.

I found one thing worth the next round's attention, and it is the answer to
question 3: **the sweep's stated bound does hide a class, and I can demonstrate
it.** Dropping *one conjunct of an `and`* makes the net report a legitimate value
normalizer — criterion 4's failure mode, the thing round 8 was failed for — with
the entire 47-entry corpus still clean. The bound is honestly stated and no claim
is falsified by this; it is a gap in what would be noticed if the code broke, and
it closes with one `CLEAN` entry.

---

## 1. Correction 3 — the four new branches were really unpinned, and are now pinned singly

`scratchpad/rjr11/rjr11_unpinned.py` neutralises each branch on **both** trees
and runs the whole corpus (per-file planting, validated against `measure()`):

```
########## OLD 901d89e ##########  (42-entry corpus)
  D43 branch: YieldFrom step                             escaped=[] -> UNPINNED
  D44 branch: _rpaths_of by ATTRIBUTE name               escaped=[] -> UNPINNED
  D45 branch: _bind_element on a comprehension generator escaped=[] -> UNPINNED
  D46 branch: the cell() half of the tuple unpack        escaped=[] -> UNPINNED
  D47 branch: the SUBSCRIPT half of the carried write    escaped=[] -> UNPINNED
  ast.Set in the literal branch                          escaped=[] -> UNPINNED

########## NEW 642091f ##########  (47-entry corpus)
  D43 branch  escaped=['D43']   D44 branch  escaped=['D44']
  D45 branch  escaped=['D45']   D46 branch  escaped=['D46']
  D47 branch  escaped=['D47']
  ast.Set     n/a on this tree (deleted)
```

**All five were genuinely unpinned at `901d89e`** — the corpus stayed fully
caught with each one neutralised — and each is now a single-entry mutation. No
`CLEAN` entry was flagged and no `SECOND_RULE` entry was caught in any run.
`ast.Set` is gone and the reasoning for deleting rather than planting it is
sound: a row is a list, a list is unhashable, so the branch is unreachable.

**Corpus on the corrected tip: `DRIFT 47 / CLEAN 14 / SECOND_RULE 41`,
`{escaped: [], flagged: [], second_rule_caught: []}`.**

### The four mutations, run from the anchors the table now gives

```
R11-24 :420 yield-from adds an element level        ANCHOR-LINE-OK  escaped ['D43']
R11-25 :520 a SUBSCRIPT write carries nothing       ANCHOR-LINE-OK  escaped ['D47']
R11-26 :454 a comprehension generator binds no table ANCHOR-LINE-OK escaped ['D45']
R11-27 :504 a tuple unpack has no cell() half       ANCHOR-LINE-OK  escaped ['D46']
```

**`R11-24` reddens `D43` and only `D43`.** Confirmed.

### Do the new entries plant the live shape, or a shape built to be caught?

Three of five plant a live shape; two plant a plausible shape with no live
instance, and the round is honest about one of them and loose about the other.

| entry | live? | evidence |
|---|---|---|
| `D44` | **yes**, minus the cross-module root | `.task_tables()` appears 6× (`bin/perry-task:811,894,918,6129`, `bin/perry_store.py:164,528`). The doc says "minus the cross-module root" — honest. |
| `D45` | **yes** | `bin/perry_md_store.py:490` and `:549` are `{r["line"] for t in tables for r in t["rows"]}`; `bin/perry_store.py:585` likewise |
| `D46` | **yes** | `bin/perry_store.py:858` is `i, cells = row["line"], row["cells"]` (the doc cites `:857`, off by one line; the line is there) |
| `D47` | **no live instance** | I AST-swept every reader for a subscript assignment whose value the net resolves as a row: **0 hits**. The provenance line calls it "`D24`'s sibling", which is honest, but § 1.5's column heading is "the live shape". |
| `D43` | **no live instance** | `grep -rn "yield from" bin/ viewer/` returns nothing |

Neither `D47` nor `D43` is contrived to be caught — both are ordinary reader
spellings of a producer pattern the file already handles, and `D43` exists
because the alternative was carrying an unmeasured branch. But § 1.5's table
should not present all five as live shapes when two are not. (`D37`, from the
earlier round, is the same: **0 live attribute writes of a row**; its provenance
is a reviewer's plant, which is a legitimate source and is what it says.)

---

## 2. The twenty greens — five spot-checked, all green, none a detection branch

Each neutralised alone on `642091f`, judged on the author's own two-sided
criterion (whole corpus caught **and** `test_header_index_is_the_only_fold`
unmoved):

```
G1 L877 census ATTRIBUTE half                    GREEN  corpus clean · watch Ran 10 OK
G2 L696 source() _source_direct short-circuit    GREEN  corpus clean · watch Ran 10 OK
G3 L418 owner filter in the yield loop           GREEN  corpus clean · watch Ran 10 OK
G4 L513 the `bound` continue                     GREEN  corpus clean · watch Ran 10 OK
G5 L694 source() default-scope normalisation     GREEN  corpus clean · watch Ran 10 OK
```

That includes **both** of the ones the author says were re-verified by hand
(L418 and the L694/L695 pair) — confirmed, the sweep and a hand check agree —
and **both** of the "dead attribute half" ones I was asked to be suspicious of.

**On the census's attribute half being dead, and why deleting it would be the
wrong call here.** I confirmed it is dead: of the 17 live carried sites, **zero**
are attribute reads — all are subscripts. But this is a *different* kind of dead
from `ast.Set`. `ast.Set` is unreachable by a type argument and can never fire.
The census's attribute half is perfectly reachable: a reader that writes
`t.header` tomorrow would be counted, and its sibling in `_paths` (the detection
side) **is** pinned, by `D37`. Keeping the measurement symmetric with the
detection it measures, and stating it as a limit (§ 7.14), is the right call.
The distinction the author draws — delete the impossible, declare the merely
unexercised — is correct and I would not have it the other way.

The other three are correctly classified too, and the reason is legible from the
source: `_paths` calls `_source_direct` itself at `:623`, so `source()`'s
short-circuit at `:696` is genuinely defence in depth; every caller passes
`scope`, so `:694` never fires; and the `bound` flag's job is stopping a generic
fall-through from marking `_` a row, which no live site and no corpus entry
exercises.

**The sweep's own control holds.** I round-tripped `tests/header_rule.py`
through `ast.parse`/`ast.unparse` with no mutation: corpus `escaped [] flagged []
s2 []`, `test_header_index_is_the_only_fold` `Ran 10 OK`. So the sweep's verdicts
are attributable to the mutations and not to the round trip.

---

## 3. The sweep's bounds — honestly stated, AND they hide a class. Reproducible.

The declared bound is *"it mutates whole `if` tests, not individual conjuncts of
an `and`"*. That is honest and it is exactly the right thing to have written
down. It also hides something, and the coordinator's question deserves a
demonstration rather than an opinion.

I ran the conjunct sweep the bound excludes: every operand of every `BoolOp` on
a new-or-changed line of `tests/header_rule.py`, each replaced with the identity
constant for its operator, AST-built and unparsed
(`scratchpad/rjr11/rjr11_conj.py`). **36 operands: 25 green in the corpus, 10
unneutralisable, 1 red** (`:507` `() in sub_p` → `D38`).

The greens are not all equal. Most are widenings of a guard nothing exercises.
But a specific family is load-bearing in the direction this row has already been
failed for once — the conjuncts that make path matching **selective**:

- `:659` `if p and p[0] == f"attr:{node.attr}"`
- `:631` `isinstance(k, ast.Constant) and isinstance(k.value, str)`
- `:502` / `:579` `q and q[0] == f"pos:{i}"`
- `:532` `holder.id == "self" and self.class_of.get(f)`

Drop the second conjunct of `:659` — one operand, nothing else — and:

```
$ sed -n '659p' tests/header_rule.py
                if p and p[0] == f"attr:{node.attr}":
# mutant: replace with `if p:`

# a legitimate value normalizer over VALUES, on an object that also carries a row
class T:
    def __init__(self, line, recs):
        self.header = split_row(line)
        self.statuses = [r.get("status", "") for r in recs]
def read(line, recs):
    t = T(line, recs)
    return [squash(s) for s in t.statuses]

MUTANT (one conjunct of an `and` dropped)    -> ['bin/pr.py:9: [squash(s) for s in t.statuses]',
                                                'bin/pr.py:9: squash(s)']
SHIPPED                                      -> []

$ corpus on the mutant:
DRIFT escaped: []   CLEAN flagged: []   S2 caught: []
```

**The mutant reports correct code — criterion 4's failure mode, and the exact
thing round 8 was failed for — and the entire 47-entry corpus is silent about
it.** No `CLEAN` entry carries a decoy attribute (or a decoy key) beside a real
row on the same object, so the selectivity of the path match is unpinned.

This falsifies no claim the round makes: the bound says conjuncts are not
mutated, and it does not say they are pinned. The shipped code is correct. It is
a gap in what would be *noticed*, and it closes cheaply — **one `CLEAN` entry**
in the shape of `C13`/`C14`: an object that carries a header row on one attribute
and values on another, folded over the values; plus its dict sibling for `:631` /
`:502` / `:579`. That single pair would pin the whole family.

Recorded for the next round. It is the finding that most nearly changed my mind
about this confirmation, and the reason it did not is that the bound was
declared, the behaviour is right, and the fix is an entry rather than machinery.

---

## 4. Corrections 1 and 2

**Correction 1 is in all three places**, and each says the same thing:

| place | says it? |
|---|---|
| `tests/test_header_index_is_the_only_fold.py`, `UNCOVERED`'s comment | ✓ "FIVE are rooted in a call into ANOTHER MODULE… THREE — the `bin/perry-lint` checks — are NOT… `_paths` has no comprehension branch… the honest target for the next round is FIVE, not zero" |
| result § 2.3 | ✓ five/three split, names `tables()` at `:194` and `tables_with_lines()` at `:209` as same-file, states the target as 5 |
| result § 7, new limit **2** | ✓ "`_paths` has no comprehension branch, and that is a FILE-LOCAL hole" |

The author reproduced my synthetic-file proof itself and says so. The
`_bind_element`-versus-`_paths` distinction it draws in limit 2 is right and I
verified it: `_bind_element` *is* called for a comprehension's generators (that
is `D45`), so the residual hole is specifically `_paths` stopping at the element
expression.

**Correction 2's anchors are usable.** I replayed **five of the nine** I could
not verify from the first draft's table, using the line anchors alone; every
anchor line held the text the row describes, and every result matched:

| # | anchor | my measurement | table |
|---|---|---|---|
| R11-9 | `header_rule.py:530` | `D37 D47` | D37 D47 ✓ |
| R11-10 | `:532` | **`D37` only** | D37 only ✓ |
| R11-11 | `:538` | `D34 D35 D37 D38 D40 D41 D46` | same ✓ |
| R11-13 | `:639` | `D36 D38 D39` | same ✓ |
| R11-14 | `:643` | `D38 D39` | same ✓ |

and `R11-16` (`:666`) reproduces at `D35 D36 D37 D38 D39 D42 D43 D44 D45`,
exactly the re-measured row — `D42` now included, which was my finding.

**Two bookkeeping defects survive the correction, both in the same family as the
thing correction 2 exists to fix.**

1. **Three anchors are stale, and they are stale by exactly the amount
   correction 1 added.** `R11-20 :435`, `R11-21 :126` and `R11-22 :270` are the
   *pre-correction* line numbers. On `642091f` those lines are a comment, a
   comment and a blank line; the real ones are `:449`, `:136`–`:143` and `:284`
   — **+14, the lines correction 1 added to `UNCOVERED`'s comment.** All 20
   `header_rule.py` anchors are correct, so the table was re-measured against
   the code file and not against the test file. This is the third time on this
   row that a table has been published against a state older than itself, and
   this time it is the correction that fixes the previous two.
2. **`D44` has no single-entry row in § 5.** § 1.5 says each of `D43`–`D47` "is
   a single-entry mutation in § 5"; `D44` appears only in six multi-entry rows.
   The claim is true in substance — I measured `_rpaths_of`'s attribute branch
   and it reddens `D44` and only `D44` — but the row is missing.

*(And § 7 now has two limits numbered **3**: the new one inserted for correction
1 collided with the existing spelling limit, so the list runs 1, 2, 3, 3, 4 … 15
over sixteen entries. § 7 is the list the next round is held to.)*

*(§ 7 limit 1 still attributes the eleven unresolved carried sites to
`bin/perry-task`, `bin/perry-tasks` and `bin/perry_md_store.py`; the eleventh is
`bin/perry_store.py:533 § plan`. That was item 4 of my original charge, outside
correction 1's scope, and it is carried.)*

---

## 5. Baselines and the ruling number — unmoved

On a `git archive` export of `642091f`, md5s of `.perry/events.jsonl`,
`perry/BOARD.md` and `perry/intake.jsonl` recorded first:

```
offenders_by_symbol('.')  ->  []

bash tests/run
102 modules · 3036 tests · 218.7s · 8 workers
✗ 2 module(s) red
```

the same three failing names, unchanged:
`test_diagnose … test_the_queue_register_reconciles_with_the_queue_on_this_repository`,
`test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks`,
`test_kr_progress_provenance … test_no_current_in_the_payload_claims_to_be_a_measurement`.

**The remainder did not move.** Re-measured with my own tracer on the corrected
tip:

```
sites 76   static-blind 27
REMAINDER by function-entry: 8   (same eight members)
REMAINDER by line-execution: 8   (same eight members)
func == stated: True
```

Deleting `ast.Set` changed nothing in the census, which is what "unreachable"
predicts. **The ruling stands: 8 of 76, measured and listed, discharges the
amendment.**

*(The write hazard reproduced a second time: all three tracked files moved after
`bash tests/run` in the export. Disposable copy; the reviewed worktree was never
run in.)*

---

## Delta verdict

**CONFIRMED.** Correction 1 is in all three places and says the right thing.
Correction 2's anchors work — five of the nine I previously could not verify now
replay from the table alone and all five match, `D42` included. Correction 3's
rebuilt sweep found four real, genuinely-unpinned detection branches, each now
pinned by exactly one corpus entry planted on a shape three of which are live;
`R11-24` reddens `D43` alone; `ast.Set` was correctly deleted rather than
planted; the twenty greens survive spot-checking and none is a detection branch;
and the sweep's own unparse control holds.

**Carried to the next round, not blocking:** one `CLEAN` entry with a decoy
attribute and one with a decoy key, which would close the conjunct class § 3
demonstrates; the three stale `only_fold.py` anchors (+14); the missing `D44`
row in § 5; the duplicated limit number 3; and § 7 limit 1's eleventh site.
