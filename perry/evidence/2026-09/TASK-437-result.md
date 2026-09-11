# TASK-437 — result

> Status: complete.
> Executor: claude-subagent, in an isolated worktree.
> Scratch: `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/task437-rootsweep-a6f12/`

## 0. Baseline, before anything was touched

Branched from `main` at `076ae21a` (*Merge spec-437*). `bash tests/run`:

```
✗ 4 of 3655 TEST(S) failed
  test_contract_key_parity.py — 2 of 35
    TestAWitnessProjectMakesAnEmptyCollectionObservable
      .test_without_the_witness_the_four_are_unobservable
    TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness
  test_diagnose.py — 1 of 158
    TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
  test_resume.py — 1 of 49
    TestStaleRuns.test_a_fresh_run_is_not_stale
```

These are exactly the four reds this round was told to expect, and no others.
Nothing in this report is attributed to them.

## 1. The three numbers, re-derived in my own tree

The spec measured at `9c30782a`. This tree is `076ae21a` and the board has
moved by one row since, so the numbers are one lower across the board — which
is itself the check that they are being read and not copied:

| | spec @ `9c30782a` | here @ `076ae21a` |
|---|---|---|
| `task_status_index(project_root)` | 157 | **156** |
| `task_status_index(state_root)` | 430 | **429** |
| records in `perry/tasks.jsonl` | 430 | **429** |

`snap.project_root` is the repository; `snap.state_root` is `perry/`. The 156
is `board.all_tasks` alone — `load_task_store(<repo>/tasks.jsonl)` finds no
file, returns `None`, and the store half of `task_status_index` contributes
nothing. So every KR's progress is computed over 156/429 = **36 percent** of
the work, and the answer is plausible.

## 2. The sweep

The spec's Bound asks for a derivation, not the named line: *find every
function taking a root parameter, decide from its body which root it needs, and
check every caller.* I ran it as four rounds, each of which was wrong in a way
worth recording, because the errors are what say how much the final list is
worth.

**What distinguishes the two roots.** `resolve_state_root`'s own docstring
gives the rule: `.perry/` never moves, because it holds the pointer to the
state root and so cannot sit behind it. So a body that joins `.perry` onto a
root needs the PROJECT root; a body that joins `BOARD.md`, `OKR.md`,
`tasks.jsonl`, `linkage.jsonl`, `okr.jsonl`, `risks.jsonl`, `intake.jsonl`,
`asks.jsonl`, `phase/`, `design/`, `evidence/`, `journal/`, `weekly/`,
`handoff/`, `decisions/` or `knowledge/` onto one needs the STATE root. That
list is `ls` of Perry's own two roots, not a guess.

| round | unit | flags | of which real |
|---|---|---|---|
| 1 | function, literal segments only | 33 "BOTH" | — (mostly propagation noise) |
| 2 | function, discounting `resolve_state_root` | 12 | — |
| 3 | function, module constants resolved | 12 | 1 |
| 4 | **root parameter, args bound to params** | 16 | see § 3 |

Round 3 is where `task_status_index` first became visible at all: its body
reads `Path(state_root) / TASK_STORE`, and `TASK_STORE` is a module constant,
not a literal. A sweep that cannot see its own named site is not a sweep, so
constants are resolved from `NAME = "literal"` module-level assignments.

Round 4 is the one I believe, and rounds 1-3 are why. They classified a
FUNCTION, which is the wrong unit: it flagged
`store_records(project_root, state_root, ...)`,
`Doc.store_path(project_root, state_root)` and the five
`check_*_store_drift(project_root, state_root)` as confused. They are not —
they take BOTH roots and every caller passes both correctly. **A function
holding two roots is not confused; the confusable unit is one root PARAMETER
and the one argument bound to it.** Eleven of round 3's twelve flags were that
mistake.

Round 4's size, which is the "state what your sweep returns" the Bound asks
for:

```
root parameters in bin/ and viewer/ : 222
   classified PROJECT                 69
   classified STATE                   58
   classified BOTH                     8
   UNKNOWN (no path evidence)         87
argument bindings judged              260
flagged                                16
```

The 87 UNKNOWN parameters carry no path evidence of their own and no forward
that reaches any — they hand the root to something outside `bin/` and
`viewer/`, or only to `.exists()` / `str()`. They are listed in § 5 as not
checked.

### Round 5, and why round 4 was still wrong

Round 4 flagged 16. Eleven were manufactured by two things:

* **Name collision.** Perry has three `load_store` (`perry_store.py`,
  `perry_md_store.py`, `perry-tasks`) and two `store_path`
  (`perry_store.py`, `perry_md_store.Doc`). Resolving a callee by bare name
  judged `perry_store.load_store(state_root)` against `perry-tasks:load_store`.
* **Methods.** `Doc.store_path(self, project_root, state_root)` bound by
  position against `doc.store_path(project_root, state_root)` lands every
  argument one parameter to the left, so `project_root` gets judged against
  `self`'s neighbour.

Round 5 resolves the callee by import alias, drops `self` for methods, and
refuses to flag a name it cannot resolve (counted instead). It also had to
learn Perry's deferred module accessors — `_parsers()`, `_task_module()`,
`_store_module()`, `_md_store_module()` — because without them **round 5
returned ZERO flags including the defect itself**: `task_status_index` reaches
`tasks.jsonl` only via `_parsers().load_task_store`. A sweep that drops its own
named site is measuring nothing, and that near-miss is why the accessor table
is in the script rather than assumed.

## 3. What the sweep returns — enumerated, not sampled

```
root parameters                                     222
argument bindings into a classified root parameter  303
   judged                                           284
   argument expression unclassifiable                19  (hand-judged, § 3.2)
FLAGGED: parameter needs one root, argument is the other   1
```

### 3.1 The one flag

```
bin/perry-goals:963  kr_rows() -> bin/lib/__init__.py:task_status_index(
    state_root: needs STATE, evidence ['tasks.jsonl'])
    arg = getattr(snap, "project_root", ".")
```

That is the site the spec names, and after § 4's fix the sweep returns **0**.

**So the answer to the Bound's question is: one call site, not a class.** The
spec said *one call site is a typo; a class of them is a defect in how roots
are passed.* Derived rather than assumed, it is a typo. What makes the class
not exist is visible in the shape of the code that survived the sweep: Perry's
convention is that a function needing both roots **takes both**, explicitly and
in that order — `store_records(project_root, state_root, ...)`,
`Doc.store_path(project_root, state_root)`,
`check_{risk,intake,ask,md}_store_drift(project_root, state_root)`,
`register_drift(state_root, project_root, okr)`,
`write_okr_and_store(state_root, project_root, ...)`,
`scan_tracking(root, state_root, inventory)`. A function that holds two roots
cannot be handed the wrong one. `kr_rows` is the site that took a `snap` and
picked an attribute off it instead, which is the one shape where picking wrong
is a one-word mistake — and the line two above it picks the right one.

### 3.2 The 19 bindings the script would not classify, judged by hand

Every one is listed; none is a defect.

| site | argument | verdict |
|---|---|---|
| `lib:resolve_project_root:540`, `parsers:resolve_project_root:548`, `parsers:_resolve_project_root:578`, `perry-lint:main:5641`, `perry-state:resolve_root:2596` | `d` | **correct.** `d` is a candidate directory in the walk up; `configured(d)` / `resolve_state_root(d)` is the probe that asks whether `d` is a project root. Passing a project-root candidate to a project-root parameter. |
| `perry-knowledge:cmd_propose:384`, `:cmd_promote:486` | `pr` | **correct.** `pr` is assigned from the project root; `declared_roles` reads `.perry/`. |
| `perry-knowledge:cmd_propose:427`, `:cmd_promote:549` ×2 | `sr` | **correct.** `sr` is the resolved state root; `read_cards` / `patch_index` read `knowledge/`. |
| `perry-churn:detect_perry:332` | `root` | **correct.** project root, handed to `resolve_state_root`. |
| `perry-diagnose:diagnose:2600, 2611, 2623` | `root` | **correct.** `diagnose(root)` takes the PROJECT root — it computes `state_root = lib.resolve_state_root(root)` on its first line — and these three want the project root. |
| `perry-explain:main:855`, `:entries_now:873` | `root` | **correct.** project root; `typed_task_lookup` and `harvest` read `.perry/`. |
| `perry-lint:_track_context:764` | `root` | **correct.** project root into `configured`. |
| `perry-lint:check_cross_file:1599` | `perry_dir.parent` | **correct.** the parent of `.perry/` is the project root by `resolve_state_root`'s own rule. |
| `perry-diagnose:diagnose:2625` | `root` into `scan_user_load` | **not a defect, but see § 6.** |

## 4. The fix

`bin/perry-goals § kr_rows`, one argument, with the sentence the line below it
has carried since TASK-120 moved up to cover both:

```python
status_by_id = lib.task_status_index(
    getattr(snap, "state_root", "."), getattr(snap, "board", None))
```

## 5. The KR numbers: none moved, and the reason is the finding

`perry-goals list --json --root .` on Perry's own project, before and after:
**25 KRs, 0 rows changed.** Not one field. That is a real answer and it needed
explaining, because the index it feeds went from 156 entries to 429.

What the 273 rows reach: `status_by_id` is consulted **only for task ids linked
to a KR**, and this project links 18. Of those 18, **14 were unresolvable
before the fix** — every one of them `done` in the store:

```
TASK-067 095 203 209 215 229 233 247 276 277 278 279 283 394
```

Six of the eight phase KRs were affected, four of them totally:

```
P003-O1-KR1  1 of 1 linked ids invisible     P003-O2-KR1  4 of 4 invisible
P003-O1-KR2  2 of 2 invisible                P003-O2-KR3  1 of 2 invisible
P003-O1-KR3  1 of 1 invisible                P003-O3-KR2  5 of 8 invisible
```

And yet `linked_task_completion` read `{total: 4, done: 4, open: 0, unknown: 0}`
for `P003-O2-KR1` both before and after. **A second source covered for the
missing one.** `bin/lib § kr_progress_provenance`:

```python
status = str(status_by_id.get(tid) or "") or last_status.get(tid, "")
```

`last_status` is built from `.perry/events.jsonl`, which is anchored at the
project root and so was found. Measured: **all 14 invisible ids are covered by
the event-log fallback, and all 14 agree with the store.** On this project the
log carries a state move for **every one of the 429** store ids — 2464 records,
432 ids, 0 store ids uncovered.

So the honest statement of verification 5 is: **no KR's published progress
moved, because on this project a redundant second source silently supplied
every value the primary one lost.** That is not reassurance. It is the reason
nothing detected the defect for as long as it existed, and it does not
generalise: the event log covers an id only if a Perry tool moved that id's
status. A project ADOPTED into Perry has a populated `tasks.jsonl` and no event
history for rows that were never moved by a tool — there the fallback is empty
and every linked row reports `unknown`. The class of project that would have
seen a wrong number is exactly the class that is not Perry itself.

## 6. Two things the sweep turned up that are not this row's fix

Neither is filed. Both are recorded here for the PMO to decide on; § 10 says
which I think meets `review.md § 0`'s bar.

### 6.1 `perry-diagnose § open_user_asks` finds the board by glob, not by resolver

`diagnose(root)` computes `state_root = lib.resolve_state_root(root)` on its
first line and hands it to `scan_tracking`, `scan_namespace` and
`scan_work_modes`. `scan_user_load` does not get it, and the function under it
locates the board this way (`bin/perry-diagnose:486`):

```python
board = root / "BOARD.md"
if not board.exists():
    for alt in sorted(root.glob("*/BOARD.md")):
        if explain.is_illustrative(str(alt.relative_to(root))):
            continue
        board = alt
        break
```

It is not a wrong answer today and it is not the `kr_rows` defect: the glob is
deliberate, commented, and on Perry's own project it finds `perry/BOARD.md`. But
it answers "where is this project's board" with a **one-level glob plus a
sort-order tie-break plus an `is_illustrative` filter**, where the same file
already holds the resolved state root. It reaches the wrong board on a project
whose state root is two levels down, and the one it picks among siblings depends
on sort order. This is `perry-diagnose`'s own territory — the tool deliberately
diagnoses projects that are not adopted at all, so it cannot simply assume a
state root — which is why I have left it alone rather than "fixed" it inside a
row about `perry-goals`. It is also adjacent to TASK-436's live work in
`test_diagnose`, which is a second reason not to touch it from here.

### 6.2 `resolve_state_root` discards a declared state root under a symlinked project root

Found by my own test fixture failing to be what it claimed. `resolve_state_root`
refuses a state root that escapes the project:

```python
root = (project_root / raw).resolve()
if project_root not in root.parents and root != project_root:
    return project_root
```

`.resolve()` is applied to the candidate and **not** to `project_root`. When the
project root contains a symlink — `/var` → `/private/var` on macOS, which is
where `tempfile.mkdtemp` puts everything, and `/tmp` likewise — the candidate's
parents are `/private/var/...` while `project_root` is still `/var/...`, the
containment test fails, and **the declared state root is discarded in silence**.
Measured on my fixture: `declared_state_root` returned `"perry"` and
`resolve_state_root` returned the project root.

The consequence on a real project is the failure `resolve_state_root`'s own
docstring already describes for a different cause: *"`perry-state --json` then
reports 'No Perry state found — run /perry for first-time setup' on a fully
populated project."* A user whose checkout sits under a symlinked path gets
exactly that. The one-line fix would be to resolve both sides before comparing;
I have not made it, because it is a change to the resolver every read in Perry
goes through and it belongs to a row with its own bound, not to a `--root`
argument in `perry-goals`.

## 7. The comparison, and where I put it

`tests/test_store_population_agrees.py`, 10 tests. The argument for its shape:

**Two sides that share no code.** The test reads `tasks.jsonl` itself —
`json.loads` per line, six lines, at `expected_population` — and imports neither
`lib` nor `viewer/parsers.py`. The other side is what each tool publishes in its
own JSON contract. The store on disk is the honest source the spec asked for,
and the only way both sides are wrong together is for the file itself to be
wrong, in which case both are right about it. It does not re-implement
`task_status_index` and it does not call it.

**It compares TOOLS, not functions.** `task_status_index` was never wrong; it
was handed the wrong directory by a caller, and callers live in tools. A unit
test on the function could not have caught this at any strength.

**One comparison covering every reader, not the two alive today.**
`TestTheCensusIsComplete` greps `bin/` for callers of `task_status_index` and
asserts that set equals the set of tools this module exercises. A third reader
added later reddens this test until somebody enters it. That is my answer to the
spec's subjective question *whether one comparison can cover every tool that
reads the task store*: not by itself, but a comparison plus a census that fails
when the census goes stale does.

**Two fixtures.** `state_root: perry` (Perry's own, roots differ) and
`state_root: ""` (roots coincide, most projects, verification 2). The fixture
that matters has three properties, each a property of a real project: the roots
differ; the store carries four terminal rows that are not on `BOARD.md`, because
a closed row leaves the board by design; and `.perry/events.jsonl` is **empty**.

## 8. Mutations

Six, and two of them are the ones worth reading.

| # | what was mutated | result |
|---|---|---|
| **M1** | the fixed site: `kr_rows` back to `project_root` | **RED** — 3 named tests, all `perry-goals`, all on `P001-O1-KR2`, all in `TestRootsDiffer`. `TestRootsCoincide` stays green, which is verification 2 in mutation form. |
| **M2** | **a second site**: `perry-state § build`, `task_status_index(root, board)` → `perry_root` | **RED** — 3 tests, symmetric, all `perry-state`, same KR. |
| M3 | drop `.resolve()` from the fixture's project root | **RED** — `test_the_fixture_has_the_roots_it_claims` ×3 |
| M4 | remove `perry-state` from `READERS` | **RED** — the census test |
| M5 | make the honest side read `tasks.jsonl` from the project root | **RED** ×6 |
| M6 | give the fixture an event log covering every id | GREEN, **by design — see below** |

### M2 is the one the spec asked for, and its answer is better than expected

The spec says: *swap it at a different site your sweep found and say whether
anything reddens — if nothing does, the guard covers one site and the report
must say so.* Something does. The guard covers the class, and the reason is the
census: `perry-state` is in `READERS` because it calls `task_status_index`, so
it is exercised against the same store file by the same assertions.

**And the whole rest of the suite does not catch M2.** I ran the full
`bash tests/run` with M2 applied: `7 of 3666` failed — the four known reds plus
exactly the three tests in my new module. So before this row, `perry-state`'s
root was as unguarded against this swap as `perry-goals`' was; it was simply
correct. That is the strongest thing I can say for the comparison existing.

### M6 is green on purpose, and it is the proof of § 5

M6 reintroduces the defect (M1) **and** gives the fixture an event log covering
every id. The result is **GREEN**: the wrong root costs nothing observable when
a second source can supply every value the first one lost. That is Perry's own
project exactly, it is why `list --json` showed no change in § 5, and it is why
the fixture's empty `events.jsonl` is load-bearing rather than incidental. A
fixture with an event log would have been a test that passes whether or not the
bug is present.

### The fixture was wrong twice before it was right, and both are recorded

This is the spec's *"must not add a test that computes its expectation the way
the code does"* showing up as its cousin — a test that passes for a reason that
is not the one claimed.

1. **`mkdtemp` and the symlink** (§ 6.2). `TestRootsDiffer` built a project whose
   roots COINCIDED and whose state files sat where no tool looked. Every
   assertion passed. **M1 still reddened it** — for a reason that had nothing to
   do with the defect. The premise is now asserted, from the tool's own
   published `project.root`, by `test_the_fixture_has_the_roots_it_claims`.
2. **The board did not parse.** The first draft headed the column `Task` instead
   of `Title` and filed store rows under `priority` rather than `group`, so
   `board.all_tasks` was empty and a wrong-root read returned an index of size
   **zero**. A tool returning nothing is caught by any check at all; the defect
   being reproduced returns a *plausible subset*. With the board parsing, a
   project-root read yields 3 of 7 — the 156-of-429 shape in miniature.

Both are in the module's own comments, at the lines they bit.

## 9. What I did not check

* **87 root parameters carry no path evidence** and no forward that reaches
  any. They hand a root to something outside `bin/` and `viewer/`, or only to
  `.exists()` / `str()` / `relative_to`. The sweep classifies them UNKNOWN and I
  did not judge them individually.
* **87 callee bindings could not be resolved** to a definition — 43 of them
  `relative_to`, 20 `Path`, 9 `str`, and a dozen in ones and twos. The sweep
  counts them rather than guessing; a name it cannot resolve is never flagged,
  which is the right bias but it is a coverage hole.
* **`tests/` was not swept.** The Bound says `bin/` and `viewer/`, and a test
  passing the wrong root fails loudly rather than lying quietly, but it is
  unswept.
* **Only `task_status_index`'s readers are compared.** The same two-root shape
  exists for `linkage.jsonl`, `okr.jsonl`, `risks.jsonl`, `intake.jsonl` and
  `asks.jsonl`; the census is for the task store alone. The module generalises
  by adding a census per store, and I did not do it.
* **`perry-goals krs --json`** is a second read-only surface on the same data
  and is not in `READERS`; the census greps for `task_status_index` callers by
  FILE, and `perry-goals` is in the table once.
* **Neither § 6 finding was fixed or reproduced beyond what is written there.**
  6.2 was reproduced on my own fixture; 6.1 is read from the source and not
  demonstrated on a two-level state root.
* **Performance.** Not measured. The fix changes which directory is read, not
  how much.

## 10. For the PMO — what I think meets `review.md § 0`'s bar

No row is filed; this is a recommendation and the decision is yours.

* **§ 6.2, the symlinked project root, I think does.** It is the second
  question — a tool giving a wrong answer to someone with no way to detect it —
  and the wrong answer is the worst one Perry has: *"No Perry state found"* on a
  fully populated project. It is one line, it is in the resolver every read goes
  through, and `/tmp` and `/var` being symlinks on macOS means it is reachable
  by anyone who checks out a project under one.
* **§ 6.1, `open_user_asks`' glob, I think does not** — not as its own row. It
  is a heuristic that is correct on the layouts it has met, in a tool whose job
  includes projects with no resolvable state root at all. It belongs as a note
  on whatever row next opens `perry-diagnose`'s user-load scan — which is
  TASK-436's neighbourhood right now.
* **The 87 unknown root parameters** are not a finding, they are the unswept
  remainder of this one. If the project wants the sweep closed rather than
  bounded, that is a row; the script is in the scratch path at the top of this
  file and runs in about two seconds.
