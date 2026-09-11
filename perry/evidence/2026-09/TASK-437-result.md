# TASK-437 — result

> Status: in progress. Written incrementally and committed as it goes.
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

*(§ 6 the second finding, § 7 the comparison, § 8 mutations, § 9 not checked —
still being written.)*
