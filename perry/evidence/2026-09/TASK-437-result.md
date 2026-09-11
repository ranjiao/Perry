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

*(§ 3 judgement of the 16, § 4 the fix, § 5 what I did not check, still being
written.)*
