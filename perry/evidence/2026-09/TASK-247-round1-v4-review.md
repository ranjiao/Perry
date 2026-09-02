# TASK-247 — round 1, V4 review

Reviewer: fresh context, own worktree
(`.claude/worktrees/agent-a469012d8f4c6c24f`). Did not write the code.

- **Criteria**: `perry/evidence/2026-09/TASK-247-spec.md` (read from
  `coding/task-247-config-predicate`; the file is not on `main`).
- **Bound honoured**: three call sites, size 3. A fourth site would be a new
  row. I looked for one, found none in `bin/` or `viewer/`, and did not widen
  the set.
- **Under review**: `b93736d` on `coding/task-247-config-predicate`.
- **Baseline for comparison**: `76f895b`, the parent commit.

## How this round was run

Every check below was run on **copies**, never on the shared checkout. Two
trees were extracted with `git archive` into the session scratchpad:

    scratchpad/b93736d/   git archive b93736d      (under review)
    scratchpad/parent/    git archive 76f895b      (pre-change baseline)

and five further copies (`m1 m2 m3 q4 q5`) carried one mutation each. The
worktree itself was never modified: `git status --porcelain` is empty apart
from this document. Every mutation was applied **by line index in Python**,
asserting the old text before writing it, never by `str.replace`; every mutated
tree had `__pycache__` removed and slept 3 s past the second boundary before
running, and every mutation also changed the line's length, so the CPython
mtime+size bytecode trap could not have fired either way.

## Environmental noise, as I actually saw it

1. **Tree guard (`tests/run` step 0): GREEN in my copies, all five full-suite
   runs.** `✓ nothing under …/<tree> moved`. I did not run `tests/run` in the
   shared checkout, so I neither confirm nor contradict the filed failure
   there — I only report that the guard is not intrinsically red.
2. **`test_parsers.py::test_locked_design_without_impl_rows_is_flagged`: RED,
   and pre-existing.** It is red identically on the parent `76f895b`
   (`Lists differ: [] != ['DESIGN-001']`), so it is not this row's. **It does
   not interact with this row**: the walk that causes it is
   `viewer/parsers.py:3303`, a four-step walk probing `.perry/events.jsonl`, a
   different anchor from `.perry/config.md`, in a function `b93736d` does not
   touch. `parsers.py`'s only change is docstring text (proved below).

## 1 · The grep — confirmed, with one stale citation

On `b93736d`:

    $ grep -rn 'config\.md.*\.\(is_file\|exists\)()' bin/ viewer/
    bin/perry-goals:2158:    if not (perry / "config.jsonl").exists() and not (perry / "config.md").exists():
    viewer/parsers.py:405:    return (perry / "config.jsonl").exists() or (perry / "config.md").exists()

On the parent `76f895b`, the same command returns five, and the extra three are
exactly the three the bound names, at exactly the lines the spec names:

    bin/perry-diagnose:1376 · bin/perry-diagnose:2515 · bin/perry-lint:657

So the population was derived, not asserted, and the set closed. I also widened
the grep myself, because the author's regex is narrow: every remaining mention
of `config.md` in `bin/` and `viewer/` (`perry-task:7272`,
`perry-context-budget:135`, `perry-lint:670/2114`, `perry-state:193/997/1067/1171`,
`perry_md_store.py:453`, `parsers.py:371`) **reads the file's contents** behind a
store-first path or is a drift check about the markdown itself. None is an
existence-as-configured predicate. `bin/perry-state-cost:400` tests
`(project_root / ".perry").is_dir()`, which is a wider predicate, not a narrower
one. **No fourth site of this category exists in `bin/` or `viewer/`. Nothing to
record as a new row on that count.**

*Documentation defect, not a FAIL (review.md § "What V4 does not judge"): the
commit message reports this grep's output as `viewer/parsers.py:402`. On the
branch it is `:405` — 402 is the pre-change line, before the docstring grew.
The spec file says `:405` and is correct. File a row; do not fix it here.*

## 2 · The fixture — built independently, and it discriminates

I did not reuse the author's fixture. I built my own
(`scratchpad/fixture_probe.sh`): a directory with `.perry/config.jsonl` only —
**no `.perry/config.md`, no `OKR.md`, no `BOARD.md`, and no ancestor anywhere
above it holding a `.perry/`** (checked explicitly, six levels up, and printed).
So no other disjunct in any of the three OR-chains can answer in the
predicate's place, and no ancestor can rescue the walk.

Run against the two trees, same fixture, nothing else changed:

| probe | parent `76f895b` | branch `b93736d` |
|---|---|---|
| `tracking.perry.config` | `false` | `true` |
| `tracking.perry.installed` | `false` | `true` |
| `namespace.applicable` (= `is_perry`) | `False` | `True` |
| `_track_context(proj/BOARD.md, "main")` | `{'track': 'main', 'mode': 'project', 'spine': 'phase/', 'default rung': 'v4'}` | `{}` |

The last row is the one that matters: on the pre-change code the walk **climbed
out of the project and typed the cell against the ancestor's register** — a
different repository's `mode` and `default rung`, returned as if it were this
project's. That is the harm, reproduced by me, not taken from the report.

`namespace.applicable` is a sound proxy for `is_perry`: `scan_namespace`
(`bin/perry-diagnose:1643`) returns `{"applicable": False, …}` for every root
where `is_perry` is false, so `True` cannot be reached with `is_perry` false.
`installed` is `perry["config"] or (perry["okr"] and perry["board"])`
(`bin/perry-diagnose:1391`), and the fixture has neither state file, so it
follows `config` alone. Both proxies are tight in the direction asserted.

## 3 · The mutations — three sites, one at a time, full suite each

Each site reverted to its exact pre-change text, one tree per mutation, whole
`bash tests/run` on each (108 modules, 3006 tests, 8 workers).

| tree | mutated line | new failure | other new failures |
|---|---|---|---|
| `m1` | `bin/perry-diagnose:1385` → `(root / ".perry" / "config.md").is_file()` | `test_scan_tracking_calls_a_store_only_project_configured` | none |
| `m2` | `bin/perry-diagnose:2530` → same narrow test | `test_is_perry_counts_a_store_only_project_as_perry` | one load-induced flake, below |
| `m3` | `bin/perry-lint:667` → same narrow test | `test_the_linter_walk_stops_at_the_project_not_at_an_ancestor` | none |

Baseline for all three: `b93736d` unmutated, same runner, `108 modules · 3006
tests · 8 workers`, **one** red module —
`test_parsers::test_locked_design_without_impl_rows_is_flagged`, the
pre-existing one. `m1` and `m3` came back with exactly two red modules: that
one, plus the named test. **The author's "exactly one named test and no other"
claim reproduces.**

`m3`'s failure message names the harm in the harm's own terms:

> the walk climbed past the configured project and typed the cell against
> …/checkouts/.perry/config.md — another project's register

`m2` additionally reddened
`test_host_support::TestOpenCodeDispatchLimit::test_concurrent_registers_do_not_exceed_opencode_cap`
(`AssertionError: 3 != 2`). **That is a load flake, not this row.** It measures
how many of N concurrent registrations get past a 2-slot cap, and it was run
while three full suites shared one machine. Re-run alone on the same mutated
`m2` tree: `Ran 35 tests … OK`. Worth its own row as test-suite flakiness;
nothing to do with `config.md`.

### Are the three tests three independent guards?

Yes, and I checked it from both directions.

- **Downward** — each site reverted alone reddens its own test and neither of
  the other two (the table above; also confirmed at module level on three
  further copies `q1 q2 q3`, one failure each).
- **Upward** — narrowing the shared predicate itself
  (`viewer/parsers.py:405`, `q5`, dropping the `config.jsonl` disjunct)
  reddens **all three** plus four older guards
  (`test_a_store_with_no_markdown_is_configured`,
  `test_the_linter_calls_a_store_only_project_adopted`,
  `test_the_installed_gate_counts_a_store_only_project_as_installed`,
  `test_the_walk_finds_a_store_only_project_from_a_subdirectory`) — 7 of 41.
  So the three new tests really do depend on the predicate under test; none of
  them is green for an unrelated reason.

Three sites sharing one predicate, guarded once each and once collectively. The
structure is what the author says it is.

## 4 · `viewer/parsers.py` is docstring-only — proved, not read

Parsed both revisions with `ast`, stripped every module/class/function
docstring, compared `ast.dump`:

    parsers.py AST (docstrings stripped) identical: True

No behaviour change. The docstring's new count is also correct: `configured(`
has exactly nine call sites in `bin/` + `viewer/` outside its own definition
(perry-diagnose ×2, perry-lint ×3, perry-state ×2, perry-explain, parsers).

## 5 · Is `configured` the right question at all three sites?

**Site 1 (`scan_tracking`) and site 2 (`is_perry`): yes.** Both feed
"is this a Perry project", and both already OR the `.perry/` answer with the
state-file answer. Widening only the `.perry/` disjunct is the minimal change.

**Leaving the `OKR.md`/`BOARD.md` half of `is_perry` alone was right.** It
answers a different question — "are the state files here" — and it differs per
caller, which is exactly why `configured` is documented as answering about
`.perry/` only. Folding it in would have given `configured` two meanings. It is
also out of the bound, so widening it would have been a rule-1 violation, not a
thoroughness win.

**Site 3 (the lint walk): yes, and it moves toward the house convention.**
`bin/perry-lint` already stops two other project-root walks on `P.configured`
(`:3736`, `:4265`), as does `bin/perry-state` (`:2027`, `:2617`). This was the
odd one out. It is true that `viewer/parsers.py § resolve_project_root` answers
"where does the project start" with `.perry/`-is-a-directory plus a round trip,
which is a *third* spelling — but that divergence pre-dates this row, and the
change narrows the gap rather than widening it. Not a defect of TASK-247.

## 6 · Can `configured` be satisfied in a way that leaves a caller worse off?

I could not construct one for these three sites, and I think the reason is
structural: the change is **monotone**. `(p/"config.md").is_file()` implies
`(p/"config.jsonl").exists() or (p/"config.md").exists()` for every input —
`exists()` is a superset of `is_file()` for regular files, and both return
`False` on the same `OSError` paths. So there is no input on which the new
predicate says `False` where the old said `True`. The three consumers all treat
the widened direction as the correct one:

- `config`/`installed` → `True` on a genuinely configured project. Correct.
- `is_perry` → `True` populates `perry_owned` and runs the namespace/archetype
  scans. I checked the one new crash candidate this opens —
  `state_root.relative_to(root)` at `bin/perry-diagnose:2534`, now reachable on
  projects where it was not before. It cannot raise: `parsers.resolve_state_root`
  returns `project_root` unless the resolved root is strictly under it
  (`viewer/parsers.py:432-436`), and `lib.resolve_state_root` is a re-export of
  that same function.
- the walk → stops earlier. Stopping earlier on a store-only nested project
  yields `{}`, which `_track_context`'s own docstring defines as the permissive
  case. The worst reachable new behaviour is *fewer* typed-cell checks, never a
  false error against a foreign register.

Two edges I did find, both in the predicate rather than at these sites, and
both harmless enough that I am recording them rather than failing on them: a
**directory** named `.perry/config.md` or `.perry/config.jsonl` now reads as
configured where `is_file()` said no, and a **zero-byte** `config.jsonl` counts.
Nothing in `bin/` writes an empty store as a marker (checked every writer of
`config.jsonl`), so neither is reachable by a user doing anything ordinary. The
predicate is out of the set in any case.

## 7 · A green mutation — reported, and it is NOT this row's failure

Rule 2 says a green mutation is a finding either way, so here it is.

I disabled `_track_context`'s upward walk entirely — `bin/perry-lint:666`,
`for _ in range(5):` → `for _ in range(0):`, leaving `P.configured` untouched —
and ran the **whole** suite. Result: `108 modules · 3006 tests`, one red module,
and it is the pre-existing `test_parsers` one. **Nothing in 3006 tests notices
that the walk stopped walking.** On any project whose state root is not its
project root — which is Perry's own layout, `State root: perry` — that mutation
would silently stop typing every track cell.

Why this is not a FAIL on TASK-247:

- The walk's *existence* is pre-existing code that `b93736d` did not write and
  the criteria do not ask about. The row's mutation criterion is "revert one of
  the three sites to the narrow test and a named test goes red", and that is
  satisfied three times over in § 3.
- `b93736d` strictly **increased** coverage of this function: before it, no
  test exercised `_track_context` at all.
- Demanding that every mutation of the surrounding loop be caught is precisely
  the unbounded criterion `review.md` says costs eleven rounds.

**Record it as a new row** (a `bin/perry-lint § _track_context` guard that the
walk actually walks — the natural fixture is a project whose state root is a
subdirectory), under `P003-O2-KR1` or the test-quality track.

## 8 · Confirmed on the author's remaining claims

- **OKR / board state untouched.** `b93736d` touches four files:
  `bin/perry-diagnose`, `bin/perry-lint`, `tests/test_config_store_readers.py`,
  `viewer/parsers.py`. Nothing under `perry/`, `state/`, `goals/` or `decide/`.
- **`import parsers as P` in `bin/perry-diagnose:57`** follows the convention
  every other `bin/` script uses (10 files), does not shadow any local `P`, and
  cannot resolve to a `bin/parsers.py` because none exists.
- **The data-authority read is still there and is correctly out of scope**:
  after the walk stops, `bin/perry-lint:670` still reads the track register out
  of `.perry/config.md`. The spec names this and files it separately. I confirm
  it is still present; it is not this round's defect.
- **PMO's two pre-verified items both reproduce**: the grep (§ 1) and the
  `m3` mutation reddening
  `test_the_linter_walk_stops_at_the_project_not_at_an_ancestor` with a message
  naming the harm (§ 3).

## Verdict reasoning

Every acceptance bullet in the criteria is met and was re-derived rather than
read: the grep returns zero narrow sites and I widened it myself to check;
a fixture I built from scratch shows all three paths flipping from the wrong
answer to the right one; each of the three sites, reverted alone, reddens
exactly one named test across the full 3006-test suite; and the full suite
shows no new failures against a named, reproduced baseline. No behaviour a
user can produce is worse after this change than before it. **PASS.**

Three things to file as their own rows, none of them a defect of this row:
the commit message's stale `parsers.py:402` citation; the unguarded
`_track_context` walk (§ 7); and the load-sensitive
`test_concurrent_registers_do_not_exceed_opencode_cap` flake.

=== VERDICT ===
task: TASK-247
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-247-spec.md
checked: worked entirely on git-archive copies of b93736d and parent 76f895b in the scratchpad, never on the shared checkout (worktree git status empty); the spec's grep reproduced on both revisions (5 sites before, 2 after, the 3 removed are exactly the bound's members at the spec's line numbers) and widened by me over every remaining config.md mention in bin/ and viewer/, finding no fourth existence-predicate site; an independently built store-only fixture with no config.md, no OKR.md, no BOARD.md and no .perry-bearing ancestor, showing tracking.perry.config false->true, installed false->true, namespace.applicable False->True and _track_context returning the ancestor's register {'track':'main','mode':'project','spine':'phase/','default rung':'v4'} -> {}; all three sites mutated one at a time by line index with __pycache__ cleared and a 3s wait, each under a full `bash tests/run` (108 modules, 3006 tests, 8 workers), each reddening exactly its own named test against a baseline whose only red is the pre-existing test_parsers one; the shared predicate viewer/parsers.py:405 narrowed as a fourth mutation, reddening all three new tests plus four older guards, proving they depend on the predicate; viewer/parsers.py proved docstring-only by ast.dump comparison with docstrings stripped; the nine configured() call sites counted against the new docstring's claim; monotonicity of exists() over is_file() and the state_root.relative_to(root) crash candidate at perry-diagnose:2534 ruled out via resolve_state_root's escape guard; commit touches only 4 files, none under perry/ or state/; tree guard green in all five of my full-suite runs
not-checked: the shared checkout — I never ran tests/run there, so I neither confirm nor contradict the filed step-0 failure; the OKR.md/BOARD.md half of is_perry, which is out of the bound and was reasoned about but not mutated; the two out-of-set wide sites bin/perry-goals:2158 and viewer/parsers.py:405 as call sites (only the latter as a predicate mutation); the six pre-existing configured() callers (perry-lint:3736/4265, perry-state:2027/2617, perry-explain:541, parsers:506) were not mutated; the data-authority read at bin/perry-lint:670 that still reads the register out of config.md, confirmed present but out of scope by the spec; anything outside bin/ and viewer/ (setup/, packs/, modes/, templates/, the frontend) was not grepped for the narrow predicate; Windows or non-POSIX path behaviour; any real user project — every measurement is on Perry's own tree and synthetic fixtures; the runtime cost of the added `import parsers` in perry-diagnose; whether test_host_support's dispatch-cap flake reproduces on unmutated code under equal load
proof: (none — PASS)
=== END VERDICT ===
