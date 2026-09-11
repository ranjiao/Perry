# TASK-368 — slice 1: eight modules measured in, eight measured out

> **Base**: `7f43a11c`. Every figure below was re-derived in this agent's own
> worktree on a clean tree, per the spec's Bound. The spec's own figures were
> taken at `583f024f`; `main` has since moved to `fe0292fb`, four merges ahead,
> two of which touch `tests/` (`tests/surface_reads.py` is new and
> `tests/test_bin_surface.py` grew by 349 lines). Neither is one of the eight
> modules this slice converts, but the suite totals below are `7f43a11c`
> numbers and should be re-taken at merge.
> **Machine**: 14 cores, 8 workers. **Not quiet** — another agent's suite runs
> held the load average between 8 and 24 throughout, and single full-suite
> measurements swung by 35%. That is why the suite total is an ALTERNATED
> before/after series rather than one run of each, and why the two borderline
> modules were probed three times.

## The row's title was wrong and this is the corrected claim

The row says *"the suite has no unit seam"*. It has one: `tests/inproc.py`,
added 2026-09-08 by `TASK-402`, four days after this row was filed. This slice
is not "build a seam", it is **"finish adopting one where adopting it pays"**,
and the second half is the part that did the work.

## Step 1 — the boundary as a share of ONE call

One in-process `main(argv)` against one subprocess call on the same root,
median of 7, `time.perf_counter()`, never `cProfile` (TASK-402 step 2). Every
call returned rc 0; a first pass where four of them returned rc 2 was thrown
away, because a tool that exits early does no work and its boundary share is
meaningless.

| call | subprocess | in-process | boundary | share |
|---|---|---|---|---|
| `perry-tasks render` (fixture) | 73.8 ms | 1.1 ms | 72.7 ms | **98.5%** |
| `perry-tasks diff` (fixture) | 79.3 ms | 1.2 ms | 78.1 ms | **98.5%** |
| `perry-okr build` (fixture) | 62.9 ms | 1.0 ms | 61.9 ms | **98.4%** |
| `perry-decide list` (fixture) | 66.1 ms | 2.4 ms | 63.7 ms | **96.4%** |
| `perry-explain V4` | 62.8 ms | 2.4 ms | 60.4 ms | **96.1%** |
| `perry-tasks build` (fixture) | 84.9 ms | 3.4 ms | 81.4 ms | **95.9%** |
| `perry-goals list` (fixture) | 77.3 ms | 4.2 ms | 73.2 ms | **94.6%** |
| `perry-task list --all --json` (fixture) | 108.0 ms | 8.5 ms | 99.5 ms | **92.1%** |
| `perry-state --json` (fixture) | 79.2 ms | 9.0 ms | 70.3 ms | **88.7%** |
| `perry-lint --json` (fixture) | 122.0 ms | 28.2 ms | 93.8 ms | **76.9%** |
| `perry-tasks render` (Perry's own board) | 108.6 ms | 24.7 ms | 83.9 ms | **77.2%** |
| `perry-tasks build` (Perry's own tree) | 164.4 ms | 84.3 ms | 80.1 ms | **48.7%** |
| `perry-state --json` (Perry's own tree) | 241.9 ms | 156.4 ms | 85.5 ms | **35.4%** |
| `perry-lint --json` (Perry's own tree) | 4164.4 ms | 4013.6 ms | 150.8 ms | **3.6%** |

**The share is a property of the CORPUS, not of the tool.** `perry-lint` is
76.9% boundary against a fixture and **3.6%** against Perry's own tree — the
same binary, a 44x difference in the answer. This is TASK-402's finding
reproduced on a third and fourth tool, and it is why the gate below is applied
per MODULE and not per tool: a module is convertible when the roots it works
against are small, and no amount of "it spawns a subprocess" substitutes for
measuring that.

**One TASK-402 number has expired.** `perry-explain V4` was 12% boundary on
2026-09-08. It is **96.1%** now, because the lazy-harvest fix removed the
`harvest(root)` call that used to be the other 88%. The premise's table is a
record of that day, not a standing property — which is the premise's own point.

## Step 2 — the per-module number, and the gate

Boundary seconds are the module's measured per-tool child seconds weighted by
that `(tool, root-kind)`'s step-1 share. Both halves are seconds measured on
this machine in the same minutes, so a load spike inflates numerator and
denominator together. Call counts are COUNTED at runtime by wrapping
`subprocess.run`/`Popen`, never inferred from grep (TASK-402 step 3) — the
literal call sites badly understate the calls: `test_track_move` has 4 sites
and makes 280 calls.

### Converted — eight modules

| module | calls counted | child % | **boundary %** | wall before | wall after |
|---|---|---|---|---|---|
| `test_register_store_invariant` | 246 `perry-tasks`, 94 `perry-task`, 2 `perry-lint` | 94.2 | **90.2%** | 13.8s | **1.7s** |
| `test_track_move` | 280 `perry-task`, 6 `perry-state`, 4 `perry-lint`, 2 `perry-tasks` | 97.2 | **89.3%** | 15.9s | **3.9s** |
| `test_register_substitution` | 170 `perry-tasks`, 68 `perry-task`, 12 `perry-lint` | 92.8 | **87.7%** | 11.2s | **6.9s** |
| `test_design_handoff` | via `store_fixture` + 2 own sites | 87.8 | **82.5%** | 2.1s | see note |
| `test_store_drift` | 110 `perry-lint`, 56 `perry-tasks`, 6 `perry-state`, 4 `perry-okr` | 89.7 | **73.5%** | 12.4s | **5.5s** |
| `test_store_is_canonical` | 62 `perry-lint`, 84 `perry-tasks` | 86.6 | **73.1%** | 10.9s | **5.9s** |
| `test_linkage_store_declared` | via `store_fixture` + 3 own sites | 85.3 | **65.6%** | 0.8s | see note |
| `test_board_render` | 158 `perry-tasks` | 47.6 | **46.5%** | 15.0s | **7.5s** |

**Note on the two smallest.** `test_design_handoff` and
`test_linkage_store_declared` were run TOGETHER after conversion — `2 modules ·
46 tests · 1.7s` against 2.1s + 0.8s probed separately before. A per-module
"after" figure for each is not quoted because it was not separately measured,
and inventing a split of 1.7s would be exactly the "count, do not infer" the
procedure forbids. Their boundary shares, which are what the gate turns on,
WERE measured per module and are in the table.

`tests/store_fixture.py` is the ninth file: a shared helper, not a module. All
four of its dependants were measured BEFORE it was touched, because converting
a shared helper converts every caller — the two above plus the two already
listed.

### Rejected — five modules, with their numbers

| module | child % | **boundary %** | why |
|---|---|---|---|
| `test_task_store` | 33.9 | **29.9%** | median of 3 (29.4 / 29.9 / 30.4). 4 of its calls run against Perry's own tree at 48.7% |
| `test_ns_collision` | 86.0 | **29.0%** | median of 3 (29.0 / 29.0 / 29.8) |
| `test_decoration_changes_nothing` | 35.6 | **28.9%** | median of 3 (27.0 / 28.9 / 34.7) |
| `test_claims` | 90.1 | **0%** reachable | its 238 children are `python3 -c <driver>`, not `bin/` tools; `inproc` cannot load them |
| `test_state_cost` | 75.0 | **0%** reachable | 510 of its 562 children are `python3 -c` drivers |

**`test_ns_collision` is this slice's counter-example and the reason the
procedure is not optional.** It is 86% subprocess — by the naive reading of
this row, an obvious conversion. It is **29%** boundary, because two of its
82 lint calls run against Perry's own tree and cost 4.27 of its 12.9 child
seconds at 3.6% boundary. Converting it would have bought a fraction of the
win and changed how 47 tests execute. Not converted.

## Verification

### 0. The suite total, and why one number is not enough

Baseline in this worktree at `7f43a11c`, clean tree, 8 workers:
**124 modules · 3561 tests · 174.5s** at load average ~8.

The suite was then run four more times as the machine's load swung between 8
and 76, because three other sessions were running `tests/parallel` on it
throughout. Every run reported the same 124 modules and 3561 tests:

| run | tree | load avg | wall |
|---|---|---|---|
| baseline | before | ~8 | **174.5s** |
| straight after-run | after | ~15.5 | 236.0s |
| alternated pair, arm 1 | before | ~60 | 319.8s |
| alternated pair, arm 2 | after | ~45 | 144.9s |
| **final, on the restored tree** | **after** | **~25** | **97.5s** |

**The headline pair is 174.5s → 97.5s**, and it is conservative: the after run
carried a load average roughly three times the baseline's and still finished in
56% of the time. The 236.0s run is the same tree as the 97.5s run — the
difference between them is the machine, not the code, which is the clearest
statement of why a single wall-clock pair could not have settled this.

**That is not a regression, and quoting the pair on its own would be a lie.**
Three other `tests/parallel` processes from other sessions were running on this
machine and the load average went from ~8 during the baseline to 15.5, then 24,
then 46, then 61. The suite got slower because the machine did.

Two things separate the two causes, and they agree.

**(a) The untouched modules as a control.** 109 of the 124 modules over 0.5s
were not touched by this row. Their median `after/before` ratio across the two
full runs is **1.456** — the machine was 46% slower during the after run — and
that alone accounts for 174.5s → 236.0s. Reading the eight converted modules
against that control:

| module | before | after | load-corrected | |
|---|---|---|---|---|
| `test_register_substitution` | 12.02s | 1.59s | **1.09s** | 90.9% faster |
| `test_register_store_invariant` | 20.16s | 3.56s | **2.44s** | 87.9% faster |
| `test_track_move` | 21.84s | 4.51s | **3.10s** | 85.8% faster |
| `test_store_drift` | 13.17s | 6.04s | **4.15s** | 68.5% faster |
| `test_store_is_canonical` | 11.37s | 6.04s | **4.15s** | 63.5% faster |
| `test_linkage_store_declared` | 2.85s | 1.64s | **1.13s** | 60.5% faster |
| `test_design_handoff` | 9.51s | 5.79s | **3.98s** | 58.2% faster |
| `test_board_render` | 22.17s | 15.08s | **10.36s** | 53.3% faster |
| **the eight together** | **113.09s** | **44.25s** | **30.39s** | **73.1% faster** |

**82.7 serial seconds removed**, load-corrected, out of the ~1018s of recorded
per-module serial time the suite holds. The ordering of the eight tracks the
boundary share that predicted it: the three at 87-90% boundary gained 86-91%,
and `test_board_render` at 46.5% gained 53%.

**(b) An ALTERNATED before/after pair**, so a drifting load crosses both arms
rather than one — the method `TASK-230` used on this same machine for this same
reason. The nine files are checked out from `7f43a11c`, the suite runs, the
files are restored, the suite runs again:

```
before   124 modules · 3561 tests · 319.8s · 8 workers
after    124 modules · 3561 tests · 144.9s · 8 workers
```

Both arms reported the full 124 modules and 3561 tests, which is the check
that the `before` checkout really was main's version and not a half-swapped
tree — `tests/parallel` fails any module contributing zero tests, so a
mis-swapped file would have reddened rather than quietly shrunk the total.

**Three pairs were planned and one was taken.** While the series ran, three
other sessions' `tests/parallel` processes were on this machine and the load
average reached 76; the remaining four runs would have taken most of an hour
and made the box worse for those sessions while producing noisier numbers than
(a) already gives. The series was stopped after the first complete pair. **It
was stopped one step too late**: the script had already checked out the
`before` files for pair 2 when it was killed, so the worktree was left holding
main's versions of all nine. That was checked with `git status` rather than
assumed, restored with `git checkout HEAD -- <the nine by name>`, and verified
two ways — `git diff HEAD` empty, and all nine files re-counted for
`inproc.run` present and `subprocess.run` absent.

**The two methods agree on direction and not on size**: (a) says the eight
modules got 73% faster, (b) says the whole suite halved. (b) is one pair on a
machine whose load was swinging by a factor of nine and it should be read as
corroboration, not as a measurement.

**The wall-clock suite total is the least trustworthy number in this report,
and it is the one the spec asks for.** It is quoted above as measured; the
control ratio is what it means. A re-run on a quiet machine at merge is worth
more than any of it.

### 1. The suite's red set is unchanged

Every one of the five full runs above reported **124 modules · 3561 tests** and
**4 failures**, and the failures are exactly the four known reds and no others.
Checked on the final run, taken on the restored tree:

```
test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable.test_without_the_witness_the_four_are_unobservable
test_contract_key_parity.TestTheWitnessedKeysRedden.test_the_same_mutation_is_silent_without_the_witness
test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks     (TASK-436, a dangling USER-920)
test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale
```

### 2. The `--ids` set diff is empty for every converted module

Per module, and then across the whole suite:

| module | ids before | ids after | diff |
|---|---|---|---|
| `test_track_move` | 30 | 30 | empty |
| `test_register_store_invariant` | 46 | 46 | empty |
| `test_register_substitution` | 26 | 26 | empty |
| `test_store_drift` | 46 | 46 | empty |
| `test_store_is_canonical` | 12 | 12 | empty |
| `test_board_render` | 14 | 14 | empty |
| `test_design_handoff` | 25 | 25 | empty |
| `test_linkage_store_declared` | 21 | 21 | empty |
| **whole suite** | **3561** | **3561** | **empty** |

The whole-suite diff is of the id AND outcome pairs, so it also carries
verification 1.

### 3. Mutation — the rung, and the thing the V5 signature does not cover

For each converted module: break the `bin/` code that module exists to cover,
and show a test in it **still goes red after conversion**. Every mutation was
reverted immediately and `git diff bin/ viewer/` is empty on this branch.

| # | module | mutation | result |
|---|---|---|---|
| 1 | `test_track_move` | `bin/perry-task` `cmd_track`: a queue-mode move sets `arrived = ""` instead of stamping today | **5 of 30 red** |
| 2 | `test_register_store_invariant` | `bin/perry-task` `refuse_to_shrink`: the guard returns unconditionally, so no write is ever refused | **34 of 46 red** |
| 3 | `test_register_substitution` | `bin/perry-task` `substituted_away`: `lost.append(record)` → `pass`, so a substituted-away record is never reported | **23 of 26 red** |
| 4 | `test_store_drift` | `bin/perry-lint` `check_store_drift`: marks the store present, then returns `[]` — drift is never reported | **17 of 46 red** |
| 5 | `test_store_is_canonical` | `bin/perry-tasks` `cmd_render`: `render --write` returns 0 without writing the board | **1 of 12 red** |
| 6 | `test_board_render` | `bin/perry_store.py` `render_line`: `escape = False`, so rendered cells stop being escaped | **5 of 14 red** |
| 7 | `test_design_handoff` | `bin/perry-task`: the explicit `design_refs` carry through `store_records` is dropped | **1 of 25 red** |
| 8 | `test_linkage_store_declared` | `bin/perry-lint`: `_JSONL_STORE_LABEL` renamed, so the census stops naming the linkage store | **4 of 21 red** |

**A green mutation, and why it was NOT a blind test.** The first mutation
tried for `test_store_is_canonical` — `bin/perry-tasks`' `if dest.exists():`
guard → `if False:` — came back **green**, which is the exact signature of the
defect this row is most likely to ship. It was not that. The unconverted
module was checked out and run against the same mutant and it was **green
too**, so the blindness pre-dated the conversion; running the tool by hand
then showed why: an earlier guard already refuses a board-to-store import
without `--from-board`, so the mutated line is unreachable on that path. The
mutation was a no-op, not a blinded test, and it was replaced with #5 above,
which is reachable and red. **A green mutation is a finding about the
mutation until the unconverted module has been run against it.**

### The hazard this conversion could have shipped, and what was measured

`tests/inproc.py` warns that module-level state in a tool persists between
calls where a child would start clean. Three of the eight modules converted
`perry-lint` call sites, and `bin/perry-lint` has one genuinely root-keyed
global:

```
bin/perry-lint:674   _TRACK_CONTEXTS: dict = {}
bin/perry-lint:771   key = str(root)
```

`bin/perry-diagnose`'s `_TEXT_CACHE` is cleared per run at line 2590 *because*
`tests/inproc.py` exists. **`_TRACK_CONTEXTS` is not cleared anywhere.** So an
in-process lint of a root whose track register changed between two calls would
be served the first answer.

Rather than reason about it, it was instrumented: `_track_context` was wrapped
over a full in-process run of each lint-converted module and the consultations
counted.

| module | `_track_context` consulted | cache reuse |
|---|---|---|
| `test_store_drift` | 0 | 0 |
| `test_store_is_canonical` | 0 | 0 |
| `test_linkage_store_declared` | 0 | 0 |

Zero, because the cache is populated only by a typed `Track` cell and none of
these fixtures writes one. The conversions are safe **as measured**, and the
number is recorded so the next slice does not have to re-derive it. The
uncleared cache itself is a finding and belongs in its own row — it is a
`bin/` change and this row may not make one.

### The byte/str distinction, which a conversion silently loses

`test_board_render`'s `rendered()` called `subprocess.run(..., capture_output=True)`
with **no `text=True`**, so it returned `bytes`, and `board_bytes()` compares it
against `read_bytes()`. `inproc.run` always decodes to `str`. A literal
conversion would have made `assertEqual(self.rendered(d), self.board_bytes(d))`
compare a `str` against `bytes` — which fails loudly — or, had the other side
been decoded to match, would have turned the byte comparison this module exists
for into a str comparison that stays green through a normalising renderer. That
is precisely the defect the module's own docstring says it exists to prevent:
*"a renderer with no byte comparison is the thing this task exists to prevent"*.

The conversion keeps it a byte comparison by encoding at that one site:

```python
    def rendered(self, root: pathlib.Path) -> bytes:
        proc = inproc.run("perry-tasks", ["render", "--root", str(root)])
        self.assertEqual(proc.returncode, 0, proc.stderr[:500])
        return proc.stdout.encode("utf-8")
```

Mutation #6 is the proof that it is still a byte comparison: breaking cell
escaping in the renderer reddens 5 of its 14 tests.

### Half-converted modules, which is how TASK-402's shared-helper rounds failed

Converting `tests/store_fixture.py` converted the fixture builder of four
modules at once. Two of them — `test_design_handoff` and
`test_linkage_store_declared` — had their own direct call sites as well, which
would have left them building fixtures in-process and asserting through
subprocesses. Both were measured (82.5%, 65.6%), both cleared the gate, and
both were finished rather than left mixed. `test_register_substitution` is the
same case against `test_register_store_invariant`'s `Base`.

## What the remaining un-adopted modules are worth

Of the ~107 modules that launch a subprocess, this slice converted 8 and
rejected 5 with numbers. **The next slice should expect the yield to fall.**
The eight converted here were chosen as the head of the cost ranking that also
works against small fixture roots, and they are the easy case: a single shared
helper or two, every call carrying an explicit `--root`, every fixture a fresh
`mkdtemp`. What is left divides into three, and only the first is worth a row:

1. **Mid-ranking fixture-only modules** — `test_add_declares_unlinked`,
   `test_add_writes_the_edge`, `test_linkage_writer`, `test_queue_sla`,
   `test_cadence`, `test_role_cards`, `test_purge`, `test_intake_store`,
   `test_work_modes`. 5-11s each, all `perry-task`/`perry-tasks`/`perry-lint`
   against fixtures, so the per-call boundary is already known to be 77-98%.
   Perhaps 60-80s of serial time, at roughly this slice's cost per module.
2. **Modules whose children are `python3 -c` drivers, not `bin/` tools** —
   `test_claims` (238), `test_state_cost` (510), part of `test_ns_collision`
   (26) and `test_restore_check`. `inproc` cannot touch these; a seam for them
   is a different tool and a different row.
3. **Modules that run tools against Perry's OWN tree** — where the boundary is
   3.6-48.7% and the fix is in the tool. `test_ns_collision`,
   `test_task_store`, `test_header_rule_harness`, `test_diagnose`'s expensive
   four. **This is where the remaining seconds actually are**, and this row is
   the wrong instrument for all of it. `perry-lint` spending 4.0 of 4.2
   seconds on its own work against Perry's tree is the single largest
   un-addressed number this slice measured.

## Out of scope, and not done

- No `bin/` or `viewer/` file changed. Every mutation was reverted and
  `git diff bin/ viewer/` is empty.
- `test_project_root_resolution`, `test_host_support` and `test_tree_guard`'s
  `PERRY_PROJECT` cases were excluded by name, not measured, and not touched.
- No Perry task store was written by this row.
