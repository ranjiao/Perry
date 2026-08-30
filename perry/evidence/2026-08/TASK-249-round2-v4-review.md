# TASK-249 — round 2 V4 review (delta on the corrections)

- **Branch / tip reviewed**: `coding/task-249-suite-writes` @ `8dfd25e`
- **Baseline tree**: `main` @ `5367c06` (main moved to `70bf490` mid-round; `tests/` and `bin/` are byte-identical between the two, so the baseline still stands)
- **Merge probe**: `main` @ `70bf490` + branch, `ort`, clean, no conflicts
- **Reviewer**: fresh-context V4, read-only. Every experiment ran in my own worktrees and in a `tar`-copy under the scratchpad. **The reviewed tree was never modified**; `git status --porcelain` was empty at both ends of every suite run and the tracked-file md5 bracket matched.
- **Verdict: PASS**, with two documentation defects (one material) and two sharp edges named below. Nothing I found makes the guard fail to do what the row claims it does.

---

## 0. What I measured, and with what

Machine: macOS 26.5.2, Python 3.11.15, 14 cores, **shared with other agents' suite runs** — wall times are recorded, not comparable.

Failure counting rule, obeyed: **sum of the per-module `FAILED (failures=N)` lines**. Command used on every log:

```
grep -o 'FAILED (failures=[0-9]*\(, errors=[0-9]*\)\?)' <log>
```

I confirmed the trap on my own `main` log before trusting anything: `grep -c '^FAIL:'` returned **4** where the `FAILED (…)` sum was **5**, and `✗ N module(s) red` said **4** (modules). Three readings, one right. `tests/parallel:283` is the mechanism, as the branch says.

| tree | modules | tests | seconds | **failures** | red modules | tree guard | tracked-file md5 |
|---|---|---|---|---|---|---|---|
| `main` @ `5367c06`, fresh worktree, first run | 104 | 3124 | 292.9 | **5** | 4 | n/a (no guard on main) | `21ea2073…` → `21ea2073…` unchanged |
| branch tip `8dfd25e` | 104 | 3115 | 313.1 | **4** | 3 | `✓ nothing under … moved` | `3e2a1e25…` → `3e2a1e25…` unchanged |
| merge probe (`70bf490` + branch) | 105 | 3141 | 315.6 | **4** | 3 | `✓ nothing under … moved` | `c5e5cd66…` → `c5e5cd66…` unchanged |

Command in all three cases: `bash tests/run` from the worktree root with `PERRY_PROJECT` unset, bracketed by `git ls-files -z | xargs -0 md5 -q | md5 -q`.

**The four failures are the same by name on the tip and on the merge probe**, and they are a subset of `main`'s five:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id`
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

`main`'s fifth was `test_host_support § TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap` — the flake the branch already recorded at `1f7a13f`, in a module this branch does not touch. It did not recur on either of my other two runs.

### Two corrections to the numbers I was handed

1. **The task prompt's baseline — "4 failures across 2 red modules" — has the module count wrong.** It is **3** red modules on the branch's fork point and on the tip (`test_diagnose` ×2, `test_heading_title` ×1, `test_kr_progress_provenance` ×1). The branch's own § 5.1 says 3 and is right; the prompt is the thing that is off. On a *clean `main`* worktree the number is **5 failures across 4 red modules** on a first run, the extra one being the recorded flake.
2. **`104 → 3115` on the branch versus `104 → 3124` on `main` is not a regression.** The branch was cut before TASK-243 landed and is missing `tests/test_register_substitution.py` (22 tests) while adding `tests/test_tree_guard.py` (17). `diff` of the two `tests/test_*.py` listings shows exactly that one file each way. The merge probe restores it: 105 modules / 3141 tests. Nothing is lost by merging.

---

## (a) The refusal guard — the highest-risk change

**Behaviour, exercised by hand on a copy:**

| environment | result |
|---|---|
| `PERRY_PROJECT` unset | runs; step 0 green (all three full runs above) |
| `PERRY_PROJECT="$ROOT"` | runs; step 0 green |
| `PERRY_PROJECT=/tmp/somewhere-else` | `rc=2`, refuses **before step 1**, names both paths, and prints `Run it as:  env -u PERRY_PROJECT bash tests/run` |
| `bash tests/run --lint` | runs step 1 then the trap's step 0 verify, `✓ all green` — the `--lint` early exit really is covered |

The message is actionable: it names the offending value, names `$ROOT`, explains the mechanism in three lines, and gives the exact command to recover. This is the good version of a refusal.

**The companion test is real and it is load-bearing.** Two independent mutations of the condition kill it by name:

- `M-B` — condition replaced with `if true` (refuse everything): `test_perry_project_equal_to_the_root_is_allowed` **FAILS** (along with three others whose inner `tests/run` also gets refused).
- `M-B2` — condition weakened to `if [ -n "${PERRY_PROJECT:-}" ]` (refuse whenever it is set at all, which is the *plausible* wrong version, not the strawman): **exactly one test dies, `test_perry_project_equal_to_the_root_is_allowed`.** That is the cleanest possible proof that the refusal cannot be satisfied by refusing everything.
- `M-A` — condition replaced with `if false` (never refuse): `test_a_foreign_perry_project_refuses_the_run` **FAILS**, alone.

So claim 4 holds in both directions.

### Sharp edge 1 — the refusal is string equality against `pwd -P`, and `perry-task` resolves

`tests/run:30` computes `ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"`, and the guard compares `"$PERRY_PROJECT" != "$ROOT"` as raw strings. `bin/perry-task:7283` does `Path(os.environ.get("PERRY_PROJECT") or Path.cwd()).resolve()`. The two disagree about what "the same directory" means. Measured:

```
PERRY_PROJECT=/tmp/…/mut249     (a symlink alias of $ROOT, realpath-identical)  → REFUSED
PERRY_PROJECT=/private/tmp/…/mut249/   (trailing slash)                          → REFUSED
```

Both of those environments are *harmless* — `perry-task` would resolve them to `$ROOT` and write inside the tree step 0 hashes — and the suite refuses to run anyway. On this machine, where worktrees live under `/private/tmp` and `/tmp` is a symlink to it, an agent with `PERRY_PROJECT` spelled the `/tmp` way cannot run the suite at all until it reads the message.

**This fails in the safe direction** (a refusal never produces a wrong answer, and the printed escape hatch works), so it is not a blocker. But it is a false refusal in a guard whose stated cost model is "refusing costs nothing", and the guard's own tests never exercise it — `test_perry_project_equal_to_the_root_is_allowed` passes `str(root.resolve())`, which is precisely the one spelling that cannot trip. A one-line fix (`realpath`/`cd … && pwd -P` on `$PERRY_PROJECT` before comparing) would close it.

---

## (b) Claim 3 — shrinking `IGNORE_DIRS` from six names to two

**The factual half of the claim is true.** `.pytest_cache`, `.mypy_cache`, `.ruff_cache` and `node_modules`:

- zero hits in `git ls-files` (no tracked file, no `package.json`, no `pyproject.toml`, no `requirements*.txt`, no `tox.ini`, no `setup.cfg`, no `.pre-commit-config.yaml`);
- zero hits on disk under the live checkout (`find … -maxdepth 4`);
- no tool in the repo makes one — `.github/workflows/ci.yml` installs nothing ("stdlib only") and runs `bash tests/run` on a clean checkout; `.vscode/settings.json` is `{"python.languageServer": "None"}`;
- the only in-repo mention of `.pytest_cache` is `bin/lib/__init__.py:923`, an unrelated scan-exclusion list inside `perry-diagnose`.

So the deletions match nothing today, and the guard is 811 entries / 0.42 s per walk — the cost is not the issue either.

**But the deletion is internally inconsistent with the file's own stated principle, and I can show the consequence.** In a temp tree, with a cache directory appearing *during* the window between snapshot and verify:

```
SHIPPED two-name IGNORE_DIRS : ['  + .ruff_cache   (created)', '  + .ruff_cache/0.4.2   (created)']
DELETED six-name IGNORE_DIRS : []
```

Nine lines above the deletion, the same docstring justifies excluding `.git` with: *"a guard that is red for reasons the reader did not cause is a guard that gets switched off."* An editor-side `ruff`/`mypy` server, a stray `pytest` in a neighbouring terminal, or a `npx` invocation during a five-minute run is exactly a red the reader did not cause. The four entries cost nothing and were the cheap insurance against it.

**What I could not find is a way for this to make the suite silently wrong.** The failure mode of the deletion is a spurious *red*, never a missed write. On that basis it does not fail the row — but I disagree with the reasoning, and I would restore the four names. "Matches nothing today" and "is a blind spot" are not the same statement: an ignore entry for a directory *no test may legitimately write* is not a blind spot, it is a scope declaration.

**Two directories the ignore list does not name and probably should.** Both exist in the live checkout, both are gitignored, and both are written by tooling rather than by tests:

- `.claude/worktrees/` — `.gitignore` says verbatim "Subagent worktrees — temporary, created by the Agent tool". A subagent spawning a worktree during a suite run turns step 0 red.
- `.gstack/`

Neither is named in the docstring's "What it does NOT catch, said plainly" list, which is otherwise the best part of the file. They belong there or in `IGNORE_DIRS`.

---

## (c) Claim 2 — is "by consequence" actually load-bearing?

Yes, and I tested it the only way that settles it: **blind a list AND delete the equality assertion that covers it**, then see whether anything still dies.

| mutation | tests killed |
|---|---|
| `M-C` `IGNORE_DIRS` += `"perry"` | `test_all_three_ignore_lists_are_the_documented_ones`, `test_the_four_files_of_this_row_are_never_invisible`, `test_a_module_that_writes_into_the_root_turns_the_suite_red` |
| `M-D` `IGNORE_SUFFIXES` += `".md", ".jsonl"` | same three |
| `M-E` `IGNORE_NAMES` += `"events.jsonl", "intake.jsonl"` (the exact round-1 defeat) | `test_all_three_ignore_lists_are_the_documented_ones`, `test_the_four_files_of_this_row_are_never_invisible` |
| **`M-C` + equality pin for `IGNORE_DIRS` replaced with `pass`** | `test_the_four_files_of_this_row_are_never_invisible`, `test_a_module_that_writes_into_the_root_turns_the_suite_red` |
| **`M-D` + equality pin for `IGNORE_SUFFIXES` replaced with `pass`** | same two |
| **`M-E` + equality pin for `IGNORE_NAMES` replaced with `pass`** | **`test_the_four_files_of_this_row_are_never_invisible`, alone** |

The last row is the one that matters. With the equality assertion gone — the assertion that "is satisfied by any list" — the consequence test still catches the exact defeat that got past round 1, on its own. Claim 2's load-bearing half is real.

`M-E` is also the round-1 defeat reproduced and closed: the first version left thirteen tests green under it; the tip kills two.

---

## (d) Mutations, re-derived — I did not trust 12/12

Twelve mutations of my own, on a `tar` copy of the tip (`.git`, `__pycache__`, `*.pyc` excluded). Discipline: anchor asserted **present and unique** before replacing; `__pycache__` cleared before every run; a sleep past the whole-second boundary before every run; restore by writing back the captured original and asserting md5 equality against the pre-mutation baseline; **baseline asserted GREEN (17 tests, 6.59 s, rc=0) before the first mutation and re-asserted GREEN after the last**.

Runner: `python3 -m unittest discover -s tests -p test_tree_guard.py -v` in the copy, with `PERRY_PROJECT` popped from the env. I deliberately did **not** count through `tests/run --only`, because the 25-line truncation in `tests/parallel:283` eats the `FAIL:` headers — my first pass through `tests/run` returned unnamed failures for six of twelve mutations, which is the same trap in a smaller room.

| # | mutation | verdict | test that died |
|---|---|---|---|
| M-A | `tests/run` refusal condition → `if false` | RED | `test_a_foreign_perry_project_refuses_the_run` |
| M-B | refusal condition → `if true` | RED | `test_perry_project_equal_to_the_root_is_allowed` (+3) |
| M-B2 | refusal condition → `if [ -n "$PERRY_PROJECT" ]` | RED | `test_perry_project_equal_to_the_root_is_allowed` |
| M-C | `IGNORE_DIRS` += `"perry"` | RED | 3 named above |
| M-D | `IGNORE_SUFFIXES` += `".md", ".jsonl"` | RED | 3 named above |
| M-E | `IGNORE_NAMES` += the two stores | RED | 2 named above |
| M-F | mode dropped from the file token | RED | `test_a_permission_change_is_a_change` |
| M-G | `trap finish EXIT` removed | RED | `test_a_module_that_writes_into_the_root_turns_the_suite_red` (+2) |
| M-H | `lines = compare(...)` → `lines = []` | RED | `test_the_same_run_is_green_when_the_guard_is_neutered`, `test_verify_is_one_and_names_the_path` (+1) |
| M-C2 | M-C with its equality pin also removed | RED | `test_the_four_files_of_this_row_are_never_invisible` (+1) |
| M-D2 | M-D with its equality pin also removed | RED | `test_the_four_files_of_this_row_are_never_invisible` (+1) |
| M-E2 | M-E with its equality pin also removed | RED | `test_the_four_files_of_this_row_are_never_invisible` |

**12/12 red. No mutation survived.** The agent's own 12/12 is independently corroborated by a different set of twelve, and every one of mine names the test that killed it.

Note `M-H` also kills `test_the_same_run_is_green_when_the_guard_is_neutered` — the mutation-half test asserts the neutered run comes back GREEN, and neutering it twice over is red. That is correct behaviour, not a defect.

---

## (e) Is the retraction complete?

**Yes.** § 5.1 of `perry/evidence/2026-08/TASK-249-result.md` withdraws both halves in bold and in the first sentence — the number *and* the accusation — names the failure its list dropped, and says the project had already filed the right figure. Commit `42e8213`'s message carries the same retraction. I grepped the branch for surviving assertions of the withdrawn claim:

- no occurrence of "3 failures", "failures=3", "uncommitted board edits" or an equivalent claim anywhere in `tests/`, `bin/`, or the result document, other than inside the retraction itself where the old claim is quoted in order to be withdrawn;
- § 5.2 and § 5.3 both report **4**, and § 5.3's table is consistent with my own measurements;
- the earlier commits (`1a5dedd`, `1f7a13f`) predate the retraction and their messages do not assert the number.

This is a real retraction, not a deletion. It also does the thing the row was actually about: it explains the mechanism rather than quietly swapping the figure.

### Defect 1 — a *different* withdrawn claim is still standing, in the guard's own docstring (MATERIAL)

`tests/tree_guard.py:60-67`, inside the "What it does NOT catch, said plainly" list:

> **`tests/run` closes the ambient case** by exporting `PERRY_PROJECT="$ROOT"` for the whole run, which pins every un-rooted write into the tree the guard is watching rather than letting it escape to a neighbour.

**`tests/run` does not do this.** It refuses. `tests/run:52-58` and `tests/test_tree_guard.py:136-139` both say so explicitly, and both say exporting was *tried first and rejected* because it reddens nine tests in `test_config_store_readers`. The docstring describes the approach that was withdrawn, and describes it as shipped.

This is not cosmetic in this row. The sentence is in the one list in the codebase whose entire job is to tell the next reader what the guard does and does not cover; it names a *mechanism* (a pin) with different properties from the one that shipped (a refusal); and a reader who believes it will conclude that running with a foreign `PERRY_PROJECT` is safe and silently re-aimed, when in fact the suite will stop dead. Round 1 failed this row partly for a guard that could not fail on the thing it named; this is the documentation equivalent, in the same file, surviving the correction that was supposed to replace it.

Fix is one paragraph. **This is the only finding I would insist be fixed before merge.**

### Defect 2 — "eleven executables", declared and wrong, twice (SMALL)

`tests/tree_guard.py:129` and `tests/test_tree_guard.py:348` both say:

> this repository ships **eleven** executables whose bit is load-bearing

Measured on the tip: **24** files carry mode `100755` in the tree (`git ls-tree -r HEAD | awk '$1=="100755"'`), of which **18** are under `bin/`, plus `setup`, two template linters and three files in `tests/`. On disk: `find . -type f -perm -u+x -not -path './.git/*'` → 24. No grouping I can construct gives eleven.

The result document (§ 6 item 2) says "this repository ships executables whose bit is load-bearing" — no number. So the hedge was applied in the write-up and not in the two places a future reader will actually read. Claim 5 ("file mode recorded as measured, not declared") is true of the *token* — `M-F` proves the mode is really recorded and really pinned — and false of the sentence next to it. In a row whose subject is that numbers must be measured, an invented count sitting in the guard's docstring is the wrong thing to leave behind.

---

## (f) Claim 7 — the report about a file it did not change

**Confirmed, and the characterisation is fair.** `tests/live_state_expectations.py:451-461` reads, verbatim:

```
"""A Perry tool pointed at this repository, not at a fixture.

A test says which project it means in one of three places, read in
this order: `--root <dir>`, `cwd=<dir>`, or a state path among the
arguments. **With none of them the answer is no** — the tool would in
fact inherit the runner's cwd and so read this repository, but
`--help` and `--version` runs are the bulk of that population and none
of them touches state. A stated blind spot, not a claim: say
`cwd=ROOT` and the guard sees you.
"""
```

The row's quote is that sentence with the trailing clause trimmed at the colon; nothing load-bearing is dropped. The implementation matches the docstring (`--root`, then `cwd=` kwarg, then `is_live_path` over the operands, else `False`).

And the characterisation is right: TASK-249's call site was `subprocess.run(["python3", <perry-task>, name], capture_output=True, text=True)` — no `--root`, no `cwd=`, no state path — so `_tool_reads_this_project` returned `False` and the expectation checker looked past it. `intake-sweep` is a genuine counterexample to "none of them touches state". **The file is unchanged on the branch** (`git diff main...8dfd25e` touches six files and this is not one of them), which is the right call: it guards *reads*, not writes, and widening it is a different row.

I did not change it either.

---

## (g) Merge probe

`git merge coding/task-249-suite-writes` into `main` @ `70bf490`: clean, `ort`, 6 files, no conflicts. Full suite on the merged tree: **105 modules · 3141 tests · 315.6 s · 8 workers · 4 failures across 3 red modules** — the same four by name as the tip. Step 0 green (`✓ nothing under … moved`). Tracked-file md5 `c5e5cd66…` identical before and after.

No test in `test_register_substitution` (TASK-243's, absent from the branch) reddens under the merge, and no test the branch adds reddens against the newer `main`.

---

## What I did NOT verify

1. **I did not independently reproduce the original write.** A full `bash tests/run` on a fresh clean `main` worktree left every tracked file byte-identical (`21ea2073…` both ends) and `git status` empty. That is *consistent* with the row's central claim — the sweep is idempotent and this tree has already been swept — but it means my run does not re-confirm the defect from scratch. Four agents and the branch's own before/after md5s at `e322925` are the evidence for that; I checked the reasoning and the call-site fix, not the original write.
2. **I did not verify the "nine tests in `test_config_store_readers`" figure** behind the decision not to export `PERRY_PROJECT="$ROOT"`. Given Defect 1, the ship *is* the refusal, so the figure is now only a justification for a path not taken — but it is unchecked.
3. **I did not re-derive the "106 hits" / "88 + 22 = 110" instrumentation figures** in § 1 of the result.
4. **I did not test the guard against a genuinely concurrent out-of-band writer** on the live checkout (a `ruff` server, a subagent worktree appearing under `.claude/worktrees/`). The `.ruff_cache` demonstration in (b) is the mechanism shown in a temp tree, not that scenario observed in the wild.
5. **I did not run `--serial`.** All three full runs used the default parallel path.
6. **I ran each tree's full suite once.** The four failures agreed across three independent trees, which is why I did not repeat; a single run cannot separate a fifth flake from a real failure, and `main`'s fifth is only classified as a flake because the branch's own three re-runs (green/green/red) say so.

---

## Verdict

**PASS.**

Every claim I was asked to attack survived the attack. The refusal guard works in all three environments and its companion test dies under two independent "refuse everything" mutations. The three ignore lists are pinned by consequence as well as by equality, and the consequence half kills the round-1 defeat *with the equality pin removed*. Twelve mutations of my own, independent of the agent's, are 12/12 red with a named test each. The retraction is complete, explicit, and explains the mechanism rather than hiding the error. Claim 7's quote is verbatim and its reading of the blind spot is fair. Merge is clean and moves the failure count nowhere.

**Fix before merge (1 item):**

- **Defect 1** — `tests/tree_guard.py:60-67` still asserts that `tests/run` "closes the ambient case by exporting `PERRY_PROJECT="$ROOT"`". It refuses instead. Replace the paragraph. This is a withdrawn approach described as shipped, in the guard's own statement of what it does not catch.

**Fix, or file (3 items):**

- **Defect 2** — "eleven executables" in `tests/tree_guard.py:129` and `tests/test_tree_guard.py:348`. Measured: 24 (18 under `bin/`). Either state the measured number or drop it, as the result document already does.
- **Sharp edge 1** — the refusal compares raw strings against `pwd -P` while `perry-task` resolves. A `/tmp` symlink alias or a trailing slash refuses a harmless environment; the guard's own test uses the one spelling that cannot trip. Resolve `$PERRY_PROJECT` before comparing.
- **Sharp edge 2** — I disagree with the `IGNORE_DIRS` deletion (fails safe, so not a blocker), and `.claude/worktrees/` and `.gstack/` are unnamed in either the ignore list or the "does not catch" list despite both existing in the live checkout and both being written by tooling rather than by tests.

*Checked on copies and in my own worktrees throughout. `perry/BOARD.md` and `perry/tasks.jsonl` untouched; no write-side Perry tool was run against the project or any worktree of it; no identifiers minted.*
