# TASK-292 — round 1, V4 review

- **Criteria**: `perry/evidence/2026-09/TASK-292-spec.md`
- **Under review**: `coding/task-292-fixture-isolation` @ `4403ddf`, base `d49964e`
- **Reviewer**: fresh context, isolated worktree `agent-a604e0380f9a4fa4b`, base `d49964e`
- **Duplicate**: `review/task-292-v4` @ `326df49` — verified byte-identical
  (`326df49^{tree}` = `4403ddf^{tree}` = `f677288`) with the same parent
  `d49964e`. Reviewed `4403ddf`.

---

## 1 · What I verified independently, and how

### 1.1 The worktree hazard is real, and it disarms the naive reproduction

The spec asked me to confirm or refute the report that a dispatched agent saw
the suite green on the same commit range. **Confirmed.** `.perry/events.jsonl`
is git-tracked, so each checkout carries its own copy frozen at its branch
point:

| ref | rows | rows naming `DESIGN-001` |
|---|---|---|
| `main` (= `d49964e`, = this worktree's base) | 1478 | **0** |
| `coding/task-247-config-predicate` (spec branch) | 1644 | **8** |
| live shared tree `/Users/bytedance/proj/Perry/.perry/events.jsonl` | 1644 | **8** |

`git rev-parse main` returns `d49964eee33940108893aa7f4edeb4e49e4ef668` — main
*is* the base of this worktree.

Consequence, and I established it before drawing any conclusion from a green or
a red: **at base `d49964e` in this checkout the whole of `tests/test_parsers.py`
passes — 57 tests, OK — including
`test_locked_design_without_impl_rows_is_flagged`.** It passes for the wrong
reason. The walk still climbs out of the fixture; it just lands on a copy of the
log that happens not to name the id. A reviewer who ran the suite here and
stopped would have reported "already green, nothing to fix".

This is why the round's choice to pin the property in a rebuilt tempdir geometry
rather than assert against the checkout's own log is the load-bearing design
decision of the change, and I treat it as such below.

### 1.2 Reproduction — re-derived myself, from the real host log

I rebuilt the geometry in a private scratch directory: a host repo owning
`.perry/events.jsonl` (the spec branch's **real** 1644-row log), with the
**base** fixture — `.perry/` present, no log — replanted at
`hostrepo/tests/fixtures/sample-project`, exactly three directories down. Ran
this worktree's `bin/perry-state --root <fixture> --json` at base code.

```
BASE d49964e / real host log
  pending_handoff : []                      <- should be ['DESIGN-001']
  impl_refs       : DESIGN-001 8,  DESIGN-002 13
```

**Attribution control** — the same tree, twice more, changing only the host log:

```
BASE / host log EMPTY (0 rows)   -> pending ['DESIGN-001'],  refs 001=0, 002=0
BASE / host log ABSENT           -> pending ['DESIGN-001'],  refs 001=0, 002=0
```

So **8 of 8** `DESIGN-001` references and **13 of 13** `DESIGN-002` references
came from the host repository's log; the fixture's own tree contributes none.
`grep -rn 'DESIGN-001' tests/fixtures/sample-project/` returns exactly one hit,
the design document's own H1 — the fixture genuinely has no implementation rows,
which is precisely what the test asserts.

The walk's four probes, for the record: `…/sample-project/.perry` (miss),
`…/fixtures/.perry` (miss), `…/tests/.perry` (miss), `hostrepo/.perry`
(**hit**) — `viewer/parsers.py:3298-3311`.

**The events it read.** All eight rows naming the id in the host log:

| ts | event | id |
|---|---|---|
| 2026-09-02T12:07:37 | next | TASK-282 |
| 2026-09-02T13:38:27 | next | TASK-212 |
| 2026-09-02T14:06:13 | intake | — |
| 2026-09-02T14:25:54 | route | TASK-292 |
| 2026-09-02T14:26:29 | retitle | TASK-292 |
| 2026-09-02T14:26:31 | next | TASK-292 |
| 2026-09-02T15:52:19 | next | TASK-293 |
| 2026-09-02T17:05:04 | next | TASK-284 |

**Five of the eight are TASK-292's own PMO rows** — the row describing the bug
is the majority of its own evidence. The spec measured 2 at 14:0x and 6 at
15:3x; I measure **8**. It is still growing, and the growth is still pure PMO
prose with no change to the fixture.

### 1.3 After the fix, the answer does not move

The fixture now ships a 9-row `.perry/events.jsonl`, so the walk stops at its
first probe. Appending to a **scratch copy** of the host tree — the real
`/Users/bytedance/proj/Perry/.perry/events.jsonl` was never written:

| host log | rows naming `DESIGN-001` | `pending_handoff` | `impl_refs[DESIGN-001]` |
|---|---|---|---|
| real | 8 | `['DESIGN-001']` | 0 |
| real + 3 appended | 11 | `['DESIGN-001']` | 0 |
| real + 25 appended | 33 | `['DESIGN-001']` | 0 |

Pinned under a fourfold increase in host mentions. The spec asked for one
appended event; I appended 3 and then 25.

`DESIGN-002` moves 13 → **1**, and the 1 is the fixture's own `done` row on
`REL-003` citing `DESIGN-002`. So the fixture still exercises the event-log half
of `impl_refs` rather than merely being isolated from it — the round's stated
intent, confirmed by measurement rather than by reading its claim.

The new log is coherent with the fixture: board ids are `REL-001/002/009`, and
the log adds a closed `REL-003` correctly absent from the board — the "closures
that have already left the board" case `viewer/parsers.py:3280-3291` documents.

### 1.4 `tests/test_parsers.py` is green

59 tests, OK. 57 → 59, as claimed.

### 1.5 `bash tests/run` — baseline failure count

```
2. parser / extractor / linter contract tests
   108 modules · 3005 tests · 456.6s · 8 workers
   ✓ all green
3. bin/ scripts …                    ✓ all bin/ scripts OK
4. sample projects lint clean        0 error(s), 5 warning(s)
0. tree guard                        ✓ nothing under <worktree> moved
✓ all green
EXIT=0
```

**Baseline failure count: 0.** Produced by the repo's own `tests/run`, step 2's
parallel runner at **8 workers**, 456.6s wall clock — slower than the spec's
300s budget because another agent's `tests/run` (PID 14377) was running
concurrently on this machine; I left it alone and killed nothing.

Step 4's independent lint of the fixed fixture reports **0 errors, 5 warnings**,
which matches both the commit's claim and my own separate `perry-lint --root`
run on a scratch copy.

### 1.6 Mutation — red, not green

Removed `tests/fixtures/sample-project/.perry/events.jsonl`, cleared every
`__pycache__`, waited past the second boundary, re-ran:

```
FAILED (failures=1)
FAIL: test_a_host_log_thick_with_the_id_does_not_move_the_answer
AssertionError: False is not true : the fixture has no events.jsonl of its own
```

The reproduction returns. **Exactly one failure** — and the significant half of
that result is which test did *not* fail: the original
`test_locked_design_without_impl_rows_is_flagged` **stayed green under the
mutation**, in this checkout, because this checkout's log names the id zero
times. That is the direct demonstration that here the new guard, not the
original assertion, is what carries the property, and it is why an
assertion against the checkout's own state would have been the wrong shape.

### 1.7 The refused third route was not taken

`git diff d49964e 4403ddf -- tests/test_parsers.py` contains **zero deleted
lines** — 90 insertions, 0 deletions. The original assertion is untouched at
`tests/test_parsers.py:447-449` and is still the strict form:

```python
self.assertEqual(
    [d["id"] for d in self.payload["design"]["pending_handoff"]], ["DESIGN-001"])
```

No `assertIn`, no count, no subset check. The assertion was not weakened.

### 1.8 Scope and bound respected

The diff is exactly two files — the fixture's new log and `tests/test_parsers.py`.
Nothing in `perry/BOARD.md`, `perry/tasks.jsonl`, the event log,
`schema/state-schema.json`, any declaration file, or any other project. Within
the spec's Bound of 3 (one test module, one fixture, one function), and the
function was deliberately left alone.

### 1.9 The category is enumerated, and the live one is complete

Rule 1 of `work/reference/review.md` asks for the category, not the next
instance. `find tests/fixtures -maxdepth 2 -name design -type d` returns
**one** directory: `tests/fixtures/sample-project/design`. Three other fixtures
(`second-project`, `interrupted-adoption`, `sample-project-zh`) do still carry a
`.perry/` with no `events.jsonl`, so the walk still escapes them — but they ship
no design documents. I measured each against an empty host log and against the
real 1644-row log: `impl_refs {}` and `pending_handoff []` in both cases,
identical. **Latent, not live.** The round fixed the whole of the live category.

### 1.10 The round's own decision record

The spec required the row to say which defect it took and why it left the other.
The commit message does both, at length and with measurements: defect 1 (test
isolation) taken; defect 2 (the walk) named, left, and justified by a measured
consequence — dropping the walk outright reddens `test_design_handoff §
test_the_state_root_may_sit_under_the_project_root`. I confirmed that test
exists, at `tests/test_design_handoff.py:77`. This satisfies the spec's
condition for accepting fix 1 alone.

---

## 2 · Findings

**None that fail the round.**

Per `work/reference/review.md § What V4 does not judge`, V4 answers one
question: does this code do the wrong thing on an input the user can produce?
Within the bound, after this change, it does not — established by mutation and
by attribution controls rather than by reading the author's account. Everything
else I found is recorded below as a filing, which is where that page routes it.

---

## 3 · Observations — filings, not the verdict

### OBS-1 · The anti-vacuity test pins the defect and will redden when TASK-297 lands

`test_and_the_harness_above_really_does_bite` asserts `pending == []` and
`refs["DESIGN-001"] == NOISE` — that is, it asserts the cross-project read
**still happens**. It is a legitimate and clearly documented anti-vacuity
device and I am not charging it. But it has a consequence the commit does not
name.

I applied the *minimal defect-2 fix the commit message itself proposes* —
honour an explicit `project_root` exactly, walk only when it is `None` — at
`viewer/parsers.py:3298-3311`, cleared `__pycache__`, crossed the second
boundary, and ran the module:

```
FAILED (failures=1)
FAIL: test_and_the_harness_above_really_does_bite
AssertionError: Lists differ: ['DESIGN-001'] != []
```

The commit says that minimal form "was measured green on the existing suite".
That is consistent with the suite as it stood *before* this commit — the only
failure I saw is in a test this commit introduces — but it is **false of the
suite this commit ships**: the change installs the tripwire that fires on it.
Whoever takes TASK-297 must retire or invert this test in the same commit, or a
correct fix will read as a regression and invite its own revert.

This is a finding about the round's artifact rather than the product, which
`review.md` explicitly routes away from the verdict. **File as a note on
TASK-297.**

### OBS-2 · Two commit-message numbers I could not reproduce

Per `review.md`: "a comment, a KR or a commit message misstates something → file
a row, never a FAIL on this one." Both are recorded on that basis; neither
touches the direction of the argument, which my own measurements independently
support.

(a) *"This checkout (d49964e, 1478 rows) names DESIGN-001 zero times; main's
copy (1574) and the spec branch's (1584) name it six."* — `main` resolves to
`d49964e`, so the sentence describes the same file as both 1478/zero and
1574/six. Today's real figures are main 1478/0 and spec branch 1644/8.

(b) *"`reconcile_drift` reports `drift 0, unrecorded 0`."* — `perry-lint --root`
on the fixed fixture reports the opposite framing — "no `tasks.jsonl` — drift
against the store is **unchecked, not clean**" — and `perry-state --json` emits
no drift key for this fixture at all. The claim is not observable by either
obvious route. The fixture is nonetheless lint-clean and board-coherent, which I
did verify, so the substance of the point stands even though the cited number
does not.

### OBS-3 · Three fixtures are latently exposed

`second-project`, `interrupted-adoption` and `sample-project-zh` each carry a
`.perry/` with no `events.jsonl`, so the four-parent walk still leaves them.
They are inert today only because they ship no `design/` directory (measured:
identical payload under an empty and under the real 1644-row host log). Adding
one design document to any of them re-opens this defect there. The spec's Bound
says explicitly that another fixture reading host state is a new row — filing it
as such, not as an extension of this round.

### OBS-4 · TASK-297 reconfirmed, and it is not free

The `viewer/parsers.py:462` prose/code disagreement is real and reproduces as
already filed; I did not charge it, as instructed. New information for that row:
closing it costs more than the docstring gap suggests — it reddens the guard
this round installed (OBS-1), so the two must land together.

---

## 4 · What I did not check

So round 2 neither re-covers this ground nor inherits my blind spots:

- **The full suite under the defect-2 patch of OBS-1.** I ran only
  `tests/test_parsers.py` with that patch applied. Whether
  `test_design_handoff.py` and the other 107 modules stay green under the
  *minimal* form (as opposed to the outright drop the commit measured) is
  unverified, and it is the first thing TASK-297 should establish.
- **`test_diagnose.py` and `test_i18n.py` individually** — only as part of the
  3005-test `bash tests/run`, which was green.
- **Non-design consumers of the walk.** Within `walk_design` the log lines feed
  `task_blobs`, which feed only `impl_refs`, so the blast radius I measured is
  the design path. I did **not** enumerate other readers of host state elsewhere
  in `bin/` and `viewer/` — apparently the subject of the separate
  `coding/task-303-walkers-see-one-repo` branch, which I did not open.
- **`impl_refs`' substring semantics** — TASK-282, out of scope by the spec.
- **Case-insensitive / Windows filesystem behaviour** of the four probes. macOS
  APFS only.
- **`NOISE = 8` (`tests/test_parsers.py:519`) coinciding with today's real count
  of 8.** I did not check whether that is deliberate. It is not load-bearing for
  either assertion, but a reader comparing the two numbers could be misled into
  thinking the synthetic noise is the live log.
- **Whether the fixture's 9 new log rows are the *best* PMO content** — only
  that they are lint-clean, board-coherent, and exercise the done-row path.
- **Flakiness or order-dependence of the two new tests.** Each builds its own
  `TemporaryDirectory`, which I read but did not stress with repeat runs.
- **Any project other than Perry's own**, and any push / PR / merge path — none
  was taken.
- **`review/task-292-v4`** beyond confirming its tree and parent are identical
  to `4403ddf`.

---

=== VERDICT ===
task: TASK-292
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-292-spec.md
checked: reproduced independently before reading the author's numbers (base fixture replanted 3 levels under a host repo carrying the real 1644-row log: pending_handoff [] with DESIGN-001 impl_refs 8 and DESIGN-002 13, while empty-host-log and absent-host-log controls both give ['DESIGN-001'] and 0/0, so 8/8 and 13/13 of the references came from the host, and 5 of those 8 rows are TASK-292's own); after the fix pending_handoff is ['DESIGN-001'] and impl_refs 0 and stays there while host mentions are driven 8 -> 11 -> 33 by appends to a SCRATCH copy (the real log was never written); tests/test_parsers.py 59 OK (57 -> 59); bash tests/run green, 108 modules / 3005 tests / 456.6s / 8 workers, EXIT=0, baseline failure count 0, tree guard clean; mutation RED not green (fixture log removed, __pycache__ cleared, second boundary crossed, exactly 1 failure, and the ORIGINAL assertion stayed green under it, proving the new guard carries the property here); zero deleted lines in tests/test_parsers.py so the refused loosening was not taken and :447 is still a strict assertEqual; diff is exactly 2 files with no out-of-scope file touched; sample-project is the only fixture with a design/ dir so the live category is complete; worktree hazard CONFIRMED - main IS d49964e and names DESIGN-001 zero times, so all 57 base tests pass here for the wrong reason
not-checked: the full suite under the OBS-1 defect-2 patch (only test_parsers.py was run with it); test_diagnose.py and test_i18n.py other than via tests/run; other host-state readers in bin/ and viewer/ outside walk_design (the coding/task-303-walkers-see-one-repo branch, unopened); impl_refs substring semantics (TASK-282); Windows and case-insensitive probe behaviour; whether NOISE=8 at tests/test_parsers.py:519 coinciding with today's real count of 8 is deliberate; flakiness or order-dependence of the two new tests; any project other than Perry's own; review/task-292-v4 beyond tree and parent identity
proof: tests/fixtures/sample-project/.perry/events.jsonl (new, 9 rows) stops the four-probe walk at viewer/parsers.py:3298-3311 on its first probe, so the fixture's DESIGN-001 impl_refs held at 0 and pending_handoff at ['DESIGN-001'] while the host log's mentions of that id were driven from 8 to 33, against impl_refs 8 and pending_handoff [] on the same geometry with no fix
=== END VERDICT ===
