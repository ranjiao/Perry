# TASK-249 — round 3 V4 review (the three round-2 fixes, attacked)

- **Branch / tip reviewed**: `coding/task-249-suite-writes` @ `03493d6`
- **Baselines measured in this session**: `main` @ `7ef27db` and `main` @ `014dc6a`
  (`main` moved under me too — see § 5)
- **Merge probes**: `7ef27db` + branch = `425ffea`, and `014dc6a` + branch =
  `23dfef3`. Both `ort`, clean, 6 files, no conflicts.
- **Reviewer**: fresh-context V4, read-only. Every experiment ran in my own
  detached worktrees under the scratchpad and in a `tar` copy of the tip.
  **No tree under review was modified**; `git status --porcelain` was empty and
  the tracked-file md5 identical at both ends of every suite run, and the live
  checkout at `/Users/bytedance/proj/Perry` was never written to. No write-side
  Perry tool was run against the project or any worktree of it. No identifiers
  minted. `perry/BOARD.md` and `perry/tasks.jsonl` untouched.
- **Verdict: PASS**, with one material documentation defect and three sharp
  edges. Nothing I found makes the guard fail to do what the row claims, and
  the three round-2 fixes are each real.

---

## 0. What I measured, and with what

Machine: macOS 26.5.2, Python 3.11.15, 14 cores, shared with other agents'
runs — wall times are recorded, not comparable.

**I took no baseline from the brief.** Counting rule obeyed: the failure count
is the **sum of the per-module `FAILED (failures=N)` lines**, with `errors=`
counted separately where present. Command on every log:

```
grep -o 'FAILED ([a-z=0-9, ]*)' <log>
grep -o 'failures=[0-9]*\|errors=[0-9]*' <log> | awk -F= '{s[$1]+=$2} END {for (k in s) print k, s[k]}'
```

**The counting trap reproduced on my own logs before I trusted any of them.**
On all five runs the three readings disagree the same way:

```
grep -c '^FAIL:'                       -> 3   (wrong: a header was eaten)
the "✗ N module(s) red" line           -> 3   (right, but it counts MODULES)
sum of the `FAILED (failures=N)` lines -> 4   (the failure count)
```

The eaten header is `test_diagnose`'s first. It is verifiably eaten rather than
absent: `test_the_queue_register_reconciles_with_the_queue_on_this_repository`
appears in every log as a bare traceback line
(`main.log:10`) with no `FAIL:` header above it, while `test_diagnose` reports
`FAILED (failures=2)` and prints only one header. `tests/parallel:283` is the
mechanism, filed as TASK-251.

| tree | modules | tests | seconds | **failures** | red modules | step 0 | tracked md5 (pre → post) |
|---|---|---|---|---|---|---|---|
| `main` @ `7ef27db` | 104 | 3124 | 243.3 | **4** | 3 | n/a (no guard on `main`) | `5ecea1e1…` → `5ecea1e1…` |
| branch tip `03493d6` | 104 | 3119 | 335.2 | **4** | 3 | `✓ nothing under … moved` | `4c6ec57e…` → `4c6ec57e…` |
| merge probe `425ffea` (`7ef27db` + tip) | 105 | 3145 | 346.4 | **4** | 3 | `✓ nothing under … moved` | `0f21088c…` → `0f21088c…` |
| `main` @ `014dc6a` | 104 | 3124 | 234.0 | **4** | 3 | n/a | `5c4495f5… → 5c4495f5…` |
| merge probe `23dfef3` (`014dc6a` + tip) | 105 | 3145 | 249.7 | **4** | 3 | `✓ nothing under … moved` | `486cad85… → 486cad85…` |

`git status --porcelain` was empty at both ends of all five.

**The same four by name on every tree**, and none is in a file this branch
touches:

- `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
- `test_diagnose § test_perry_itself_passes_its_own_id_checks`
- `test_heading_title § test_none_of_them_contains_its_own_id`
- `test_kr_progress_provenance § test_no_current_in_the_payload_claims_to_be_a_measurement`

**No `test_host_support`.** The known intermittent did not recur in any of my
five runs. My baseline is 4 failures across 3 red modules, and it agrees with
the row's own `main` figure taken at `1274587` — measured on three different
board states now (see § 5).

**The test arithmetic closes exactly, re-derived here.** `diff` of the two
`tests/test_*.py` listings shows exactly one module each way —
`test_register_substitution.py` on `main` only, `test_tree_guard.py` on the
branch only. Counted directly with `python3 -m unittest discover`:
`test_register_substitution` is **26** and `test_tree_guard` is **21** (and
green standalone, `Ran 21 tests … OK`). So `3124 − 26 + 21 = 3119` on the
branch and `3124 + 21 = 3145` merged. Both observed to the test. The row's
correction of round 2's "22" to 26 is right.

---

## 1. The docstring pin — the cleverest thing here, and the most worth breaking

`TestTheDocstringSaysWhichMechanismShipped` claims the two ways to close the
ambient `$PERRY_PROJECT` case are mutually exclusive, that each leaves a
distinct token in `tests/run` (a non-comment `export PERRY_PROJECT=` vs the
`refusing to run: PERRY_PROJECT` banner), that it reads which one shipped,
requires **exactly one**, and requires the bullet to use that mechanism's word
and not the other's.

Baseline: the class is GREEN on the tip (2 tests, 0.002 s). Seven attacks,
each anchored, unique-checked and restored by md5:

| # | attack | pin verdict | whole module |
|---|---|---|---|
| P3 | **MD-2 re-run**: a real `export PERRY_PROJECT="$ROOT"` added beside the refusal | **RED** — both tests | — |
| P7 | **MD-3 re-run**: still refuses, banner reworded to `declining to start` | **RED** — one FAIL, one ERROR | — |
| P1 | bullet keeps the word "refuses" and asserts the **opposite** behaviour | **GREEN** | **GREEN (21/21)** |
| P2 | bullet reduced to the four words `**\`tests/run\` refuses.**` | **GREEN** | **GREEN (21/21)** |
| P4 | re-aim spelled `PERRY_PROJECT="$ROOT"` + `export PERRY_PROJECT` **ahead of** the refusal | **GREEN** | RED (2 behaviour tests) |
| P5 | re-aim spelled `export "PERRY_PROJECT=$ROOT"` ahead of the refusal | **GREEN** | not run (pin only) |
| P6 | third mechanism: `unset PERRY_PROJECT`, refusal left in the file but under `if false` | **GREEN** | RED (2 behaviour tests) |

**P3 and P7 confirm the row's MD-2 and MD-3.** The exactly-one assertion really
does catch the "belt and braces" edit that adds the withdrawn mechanism beside
the shipped one, and really does catch a refusal that ships neither token. Two
notes on P7: the complaint arrives as one `FAIL` (`0 != 1 … implements neither`)
plus one **`IndexError: list index out of range`** from
`self._implemented(self.run_src)[0]` — an unhandled error rather than a
diagnostic, in a test whose value is the sentence it prints. Cheap to fix with
a `skipTest`/guard; it does not change the verdict.

### The admitted accuracy gap is total, and P1/P2 measure how wide

The pin's own docstring says it cannot judge whether the description is any
good. **It is worth writing down how little it does judge.** P1 rewrites the
bullet to:

> **`tests/run` refuses to start** when `$PERRY_PROJECT` is UNSET. When it names
> a completely different checkout the run proceeds and the writes land there,
> which is safe because the guard follows the variable.

That is the exact inversion of both the shipped behaviour *and* the hazard the
whole row exists for, and **all 21 tests in the module stay green**. P2 reduces
the bullet to four words — `**\`tests/run\` refuses.**` — and the module is
green again. The pin requires the substring `refuses` present and the substring
`export` absent, in the bullet, and nothing else. Round 2's Defect 1 was a
bullet that named the wrong mechanism; a bullet that names the right mechanism
and describes it backwards is not caught. The row says so; I am putting a
measurement next to the sentence.

### They are not mutually exclusive, and the two tokens are read asymmetrically

`_implemented` looks for the re-aim only on a **non-comment** line
(`^[^#\n]*\bexport[ \t]+PERRY_PROJECT=`) but looks for the refusal as a **plain
substring anywhere in the file, comments included**. Two consequences, both
measured:

- **A live re-aim can be invisible.** P4 (`PERRY_PROJECT="$ROOT"` then a bare
  `export PERRY_PROJECT`) and P5 (`export "PERRY_PROJECT=$ROOT"`) are ordinary
  shell spellings of the same statement that the regex does not match. Placed
  ahead of the refusal they make the refusal unreachable — the variable always
  equals `$ROOT` by the time it is compared — and the pin reads `["refuse"]`,
  finds exactly one, sees `refuses` in the bullet, and passes. The shipped
  mechanism is the re-aim; the pin says it is the refusal.
- **A dead refusal still reads as shipped.** P6 replaces the guard with
  `unset PERRY_PROJECT` and leaves the whole refusal block under `if false`.
  The banner string is still in the file, so the pin reads `["refuse"]` and
  passes, on a `tests/run` that cannot refuse anything.

**The suite as a whole is not fooled**: P4 and P6 both kill
`test_a_foreign_perry_project_refuses_the_run` and
`test_other_spellings_of_this_root_are_this_root`, which run the real script and
assert `rc=2`. So this is not a hole in the row's protection — it is a hole in
*this test's* stated claim. The pin does not "read which mechanism shipped"; it
reads which of two strings is present in a file. Where the two answers diverge,
the behaviour tests are the ones doing the work.

**And a third mechanism is a real possibility, not a hypothetical.** P6's
`unset PERRY_PROJECT` genuinely closes the ambient case: with the variable
gone, `perry-task` falls back to the cwd, which `cd "$ROOT"` already set. It is
a legitimate design the pin structurally cannot express. § 8.7 item 6 of the
result says this; P6 is the demonstration.

**One fragility for the next editor.** `setUp` does
`doc[start:doc.index("\n- **", start + 1)]` — if the *"A write to a DIFFERENT
checkout"* bullet is ever moved to the end of the "What it does NOT catch" list,
`str.index` raises `ValueError` and both tests error out. The uniqueness guard
above it is careful; the terminator is not.

---

## 2. `tests/run`'s root resolution — the highest-blast-radius edit in the row

### It invokes the real script

`run_suite` (`tests/test_tree_guard.py:108-125`) does
`subprocess.run(["bash", "tests/run", "--only", <module>], cwd=str(root), …)`
against a `copy_repo` of the repository, with `PERRY_PROJECT` popped from the
inherited environment and re-set only when a test asks. **It is the real
entry point, not a reimplementation of its logic** — confirmed by reading, and
confirmed behaviourally by MR-1/MR-3 below, which change only `tests/run` and
are seen.

### MR-3 re-run, and the claim about why the old test was blind

On a `tar` copy of the tip, whole module, baseline GREEN (21 tests) before and
after, restores md5-verified:

| # | mutation of `tests/run` | verdict | test(s) that died |
|---|---|---|---|
| MR-1 | comparison reverted to raw strings against `pwd -P` (the `8dfd25e` behaviour) | RED | **`test_other_spellings_of_this_root_are_this_root`, alone** |
| MR-3 | **the plausible half-fix**: `${PERRY_PROJECT%/}` only, symlinks unresolved | RED | **`test_other_spellings_of_this_root_are_this_root`, alone** |

**`test_perry_project_equal_to_the_root_is_allowed` — the old test — is GREEN
under both.** That is the row's claim restated as a measurement, and it holds:
the old test passed `str(root.resolve())`, the one spelling a raw comparison
cannot trip, so it could not observe the bug it existed to catch. Only the new
test dies, under the full revert and under the half-fix alike.

### Spellings the six do not cover

`bash tests/run --lint` in the `tar` copy, eighteen values of `$PERRY_PROJECT`
(`REFUSED` = rc 2 before step 1):

| # | spelling | result | right? |
|---|---|---|---|
| 1 | `$ROOT` exactly | ACCEPTED | yes |
| 2 | `$ROOT/` trailing slash | ACCEPTED | yes (round-2 Sharp edge 1, closed) |
| 3 | symlink alias of `$ROOT` | ACCEPTED | yes (closed) |
| 4 | `/tmp` spelling of a `/private/tmp` root | ACCEPTED | yes (closed) |
| 5 | `$ROOT/.` | ACCEPTED | yes |
| 6 | `$ROOT` with a doubled slash | ACCEPTED | yes |
| 7 | `$ROOT/tests/..` | ACCEPTED | yes |
| 8 | **`.` (relative; cwd is `$ROOT`)** | **ACCEPTED** | **see below** |
| 9 | **`tests/..` (relative)** | **ACCEPTED** | **see below** |
| 10 | `..` (relative, parent) | REFUSED | yes |
| 11 | **the whole path UPPERCASED** | **REFUSED** | **no — false refusal** |
| 12 | **one component case-flipped** | **REFUSED** | **no — false refusal** |
| 13 | a genuinely foreign directory | REFUSED | yes |
| 14 | a path that does not exist | REFUSED | yes, and it says `resolves to = (nothing …)` |
| 15 | a **file**, not a directory | REFUSED | yes |
| 16 | the empty string | ACCEPTED | yes — matches `os.environ.get(…) or Path.cwd()` |
| 17 | a subdirectory of `$ROOT` | REFUSED | yes |
| 18 | `$ROOT` with a trailing space | REFUSED | yes |

Two findings, both minor, both new to this round.

**Sharp edge A — case-differing spellings are still falsely refused.** This
filesystem is case-insensitive: `cd /PRIVATE/TMP/…` succeeds, and `pwd -P`
resolves symlinks but does **not** canonicalise case, so it returns the string
as typed. `Path(…).resolve()` in CPython does not canonicalise case either — so
`perry-task` would compute the same differently-cased string and write into the
**same real directory**, inside the tree step 0 hashes. This is precisely the
class of false refusal Defect 3 was raised to close, one spelling further out,
and it survives. The message is also unhelpful here: because
`PERRY_PROJECT_REAL` equals `$PERRY_PROJECT`, the `resolves to =` line is
suppressed and the reader is shown two paths that differ only in case with no
explanation. Low likelihood (nobody types a path in the wrong case), fails safe,
not a blocker.

**Sharp edge B — the fix newly accepts relative paths, whose meaning is
cwd-dependent.** At `8dfd25e` a raw comparison refused `.` and `tests/..`;
`cd … && pwd -P` accepts them, because `tests/run` resolves them against **its
own** cwd. `perry-task` resolves them against **each subprocess's** cwd, and
tests routinely set `cwd=` to somewhere else. So `PERRY_PROJECT=.` is a value
`tests/run` certifies as "this tree" and `perry-task` may read as some other
tree. In practice the other tree is a `tempfile` directory, which is harmless,
and I could not construct a case in this suite where it is not — so this is a
residual to name, not a defect to fix. It is the cost of `cd`-based resolution
and the row does not mention it.

Neither edge is reachable without deliberately spelling `$PERRY_PROJECT` oddly,
and both fail in the refuse/harmless direction. The six spellings the new test
does cover are the ones that were actually observed to bite.

---

## 3. The count — derived, and non-vacuously so

Re-derived with my own commands on the tip:

```
git ls-tree -r HEAD | awk '$1=="100755"' | wc -l              -> 24
git ls-tree -r HEAD | awk '$1=="100755" {print $4}' | grep -c '^bin/'  -> 18
find . -type f -perm -u+x -not -path './.git/*' | wc -l       -> 24
```

The six outside `bin/` are exactly `setup`, `templates/knowledge-base/bin/
kb-lint`, `templates/ops/bin/deliverable-lint`, `tests/merge-check`,
`tests/parallel`, `tests/run` — the six the new test names. 24 / 18 confirmed.

**The number is out of the assertion.** `test_the_executables_this_repository_
ships_carry_their_mode` derives the set from `TG.manifest(PERRY_HOME)` and
asserts shape, not size.

**It is not `len(X) == len(X)`.** I broke it in both directions:

| # | mutation of `tests/tree_guard.py` | verdict | test(s) that died |
|---|---|---|---|
| MX-1 | `manifest` hardcodes mode `0o777` — **everything** looks executable | RED | `test_the_executables_…_carry_their_mode`, `test_a_permission_change_is_a_change` |
| MX-2 | `manifest` hardcodes mode `0o644` — the derived set is **empty** | RED | the same two |
| ME-1 | `chmod -x bin/perry-task` (not one line of Python touched) | RED | `test_the_executables_…_carry_their_mode`, alone |

MX-1 is caught by the `os.access(X_OK)` cross-check — the test does not read
its own answer back. MX-2 is caught by `assertTrue(execs)` /
`assertTrue(shipped)` — a degenerate empty set cannot pass. ME-1 is the tree
change the mode token exists to see, caught by the test that replaced the
invented count.

**Correction to the brief, and one observation.** The brief asks me to confirm
the literal number appears in **neither** file. It does appear, twice, in
docstring prose rather than in any assertion:

- `tests/tree_guard.py:188` — *"It was written here, as **eleven**, and the tree
  held two dozen"*. Historical, no live count. Fine.
- `tests/test_tree_guard.py:515-518` — *"`git ls-tree -r HEAD | awk
  '$1=="100755"' | wc -l` says **24**, **18** of them under `bin/`"*. This is a
  present-tense count, correct today, that nothing checks — written into the
  docstring of the test whose stated reason for existing is that *"a number in
  a comment is a claim nothing checks"*. It carries its instrument, which is
  more than "eleven" did, and the assertion does not depend on it. I would
  still cut it, and I record it rather than rule on it.

---

## 4. The `.claude` hole — reproduced, and it is wider than the row's example

Using `tree_guard` directly in temp trees:

**(A) The row's scenario, reproduced verbatim.** A subagent worktree, a
`.gstack/` and a `.ruff_cache/` all appearing between snapshot and verify:

```
+ .ruff_cache   (created)
+ .ruff_cache/0.4.2   (created)
```

`.claude/worktrees/agent-1/f` and `.gstack/cache` are invisible, **and so is
`+ .claude` itself** — `os.walk`'s `dirnames` are filtered *before* the loop
that records directory entries (`tree_guard.py:198-204`), so the parent is
never written to the manifest. The row's account of the mechanism is exactly
right.

**(B) A file written inside an ignored directory is invisible too — yes.** With
`.claude/` already present at snapshot time, the manifest records only
`['perry']`: `.claude` is not in it at all. A "test" then rewriting
`.claude/settings.local.json` — the agent harness's own permission allowlist —
and creating `.claude/hooks.json` produces `compare() == []`. Nothing reported.
This is the hole § 8.4 and § 7 item 5 take knowingly, and it is real.

**(C) The ignore is by name at any depth, which the row's examples do not
show.** A directory named `.claude` or `.gstack` **anywhere** in the tree is
skipped whole. Writes to `perry/evidence/.claude/TASK-0NN-result.md` and
`perry/.gstack/tasks.jsonl` both produce `compare() == []`. Control: the same
writes to `.claudex/` and `perry/BOARD.md` are reported normally, so the
mechanism is the name match and not the experiment.

No such path exists in the repository today, and `bin/perry-diagnose:94` and
`bin/lib/__init__.py:922` already skip `.claude` at any depth, so the choice is
internally consistent. The `#:` comment above `IGNORE_DIRS` does say "matched by
name at any depth". It is a widening of the hole beyond the root-level harness
directory the prose argues for, and worth one clause.

### Defect 1 (MATERIAL) — the widest hole is missing from the list whose job is to name the holes

`tests/tree_guard.py`'s **"What it does NOT catch, said plainly"** list has six
bullets: the idempotent write, the different checkout, `.git`, `__pycache__` /
`*.pyc` / `*.pyo`, `.DS_Store`, and the reverted write. **`.claude` and
`.gstack` are not among them.** They are explained forty lines lower, in a new
section titled *"What is ignored, and the one rule that decides it"* — which
reads as a justification of the ignore list, not as a statement of what the
guard misses.

`.DS_Store` and `__pycache__` — strictly narrower holes — each get a bullet.
The row's own § 8.4 calls the `.claude` hole *"a real hole and … the widest of
the five"*, and § 7 item 5 of the result document records it properly. The
**evidence document is complete; the code is not**, and the code is what the
next reader consults.

This is round-2 Defect 1's shape one turn later: the one list in the codebase
whose entire job is to tell the next reader what is uncovered, not telling them.
Round 2 asked for `.claude`/`.gstack` "there or in `IGNORE_DIRS`"; the row read
that as a choice and took `IGNORE_DIRS`. I read the list's own opening sentence
— *"They are listed so that the next reader inherits the list rather than
rediscovering it"* — as settling it the other way. **Fix is one bullet.**

---

## 5. The two gaps the row declares

### (a) `main` moved mid-round, and the board-dependent failures — closed, from a third board state

The row's § 8.7 item 1 is honest and the gap is real: its `main` baseline is
`1274587`, its merge probe is against `7ef27db`, the delta between them is a
PMO record commit that changes `perry/BOARD.md`, `perry/tasks.jsonl`,
`.perry/events.jsonl` and a journal file, and **three of the four failures read
board state**. It did not run a fourth suite to prove the board edit inert.

I have now run that suite, and then a fifth, because `main` moved again under
me — from `7ef27db` to `014dc6a`, two more record commits, `git diff
--name-only 7ef27db 014dc6a -- tests bin schema viewer` empty, `perry/BOARD.md`
and `perry/tasks.jsonl` changed again.

So the branch has now been measured against **three different board states**:

| board state | `main` full suite | merge probe with the branch |
|---|---|---|
| `1274587` | 4 failures / 3 red (the row's § 8.6) | — (the row did not probe this board) |
| `7ef27db` | **4 / 3 (mine)** | 4 / 3 — the row's `f069a51` and `67a6f80`, and **mine, `425ffea`** |
| `014dc6a` | **4 / 3 (mine)** | **4 / 3 (mine, `23dfef3`)** |

Same four failures by name in every one of those runs; `104 modules / 3124
tests` on every `main` and `105 / 3145` on every merge, to the test. **The board
edits are inert with respect to the failure count**, measured rather than
assumed, across two successive record commits that each touched `perry/BOARD.md`
and `perry/tasks.jsonl`. The board-dependence of three of the four failures is
real — it is why the caveat was right to write down — but the row's missing
fourth run is now supplied: `main` @ `7ef27db` reads 4 / 3, which is the board
state its own merge probes ran on, and `main` @ `014dc6a` reads 4 / 3 as well.

**The gap is closed and the row's numbers stand.** I would add one line to
§ 8.7 item 1 saying so, rather than leave the caveat standing.

### (b) The contaminated run it discarded

§ 8.7 item 7 self-reports editing two files in `wt-249` while a run's step 0
snapshot was open, killing that run rather than reporting the red it had caused.

**This strengthens the numbers rather than undermining them, and it should be
read that way.** The alternative — reporting a red the author created — is the
precise failure mode this row exists to prevent, and the discipline that
detected it is the guard the row shipped. The five runs in this document and the
five in the row's § 8.6 are all on trees whose tracked-file md5 was identical at
both ends, with `git status --porcelain` empty; a contaminated run cannot hide
inside that bracket. I checked for residue: nothing on the branch carries a
figure from the discarded run, and § 8.6's table is consistent with my own five
measurements taken independently.

### (c) One figure round 2 left unverified, now verified

Round 2 did not check the "nine tests in `test_config_store_readers`" figure
behind the decision not to export. On a `tar` copy of the tip:

```
env -u PERRY_PROJECT python3 -m unittest discover -s tests -p test_config_store_readers.py
  -> Ran 44 tests in 1.647s   OK
PERRY_PROJECT=<copy>  python3 -m unittest discover -s tests -p test_config_store_readers.py
  -> FAILED (failures=7, errors=2)          (9 `FAIL:`/`ERROR:` headers)
```

**Nine, exactly as stated**, and the docstring is right to spell it as 7 + 2
because `grep -c '^FAIL:'` on that output returns 7. The exported run also
rendered `.perry/config.md` in the copy, as the docstring says.

One precision point on that last clause: the render is **idempotent** — I
diffed the whole copy against the tip afterwards and it is byte-identical, so
the tree guard would *not* have reported it. Calling it "the mechanism in
miniature" is therefore half right: it is the write, but it is the class of
write the guard's own first declared blind spot excludes. A clause, not a
defect.

---

## 6. Mutations — nine of my own, plus the seven in § 1

On a `tar` copy of the tip (`.git`, `__pycache__`, `*.pyc` excluded), never on
a reviewed tree. Discipline, enforced by the harness rather than remembered:
refuse to start on a dirty copy; **baseline asserted GREEN (21 tests, rc=0)
before the first mutation and re-asserted GREEN after the last**; every anchor
asserted **present and unique** before replacing; `__pycache__` cleared and a
sleep past the whole-second boundary before every run; restore by writing back
the captured original bytes and asserting **md5 equality**. Runner:
`python3 -m unittest discover -s tests -p test_tree_guard.py -v` with
`PERRY_PROJECT` popped — deliberately not through `tests/run --only`, whose
25-line truncation eats `FAIL:` headers.

| # | mutation | verdict | test(s) that died |
|---|---|---|---|
| MR-1 | `tests/run` comparison reverted to raw strings | RED | `test_other_spellings_of_this_root_are_this_root` |
| MR-3 | half-fix `${PERRY_PROJECT%/}`, symlinks unresolved | RED | `test_other_spellings_of_this_root_are_this_root` |
| P4* | re-aim in a regex-evading spelling, ahead of the refusal | RED | `test_a_foreign_perry_project_refuses_the_run`, `test_other_spellings_…` |
| P6* | `unset PERRY_PROJECT`, refusal left dead under `if false` | RED | the same two |
| ME-1 | `chmod -x bin/perry-task` | RED | `test_the_executables_…_carry_their_mode` |
| MX-1 | `manifest` hardcodes `0o777` (everything executable) | RED | that one + `test_a_permission_change_is_a_change` |
| MX-2 | `manifest` hardcodes `0o644` (derived set empty) | RED | the same two |
| MI-1 | `.claude` dropped from `IGNORE_DIRS` | RED | `test_all_three_ignore_lists_are_the_documented_ones` |
| MI-2 | `perry` smuggled **into** `IGNORE_DIRS` (the list GREW) | RED | that one + `test_the_four_files_of_this_row_are_never_invisible` + `test_a_module_that_writes_into_the_root_turns_the_suite_red` |

**9/9 red, no survivors**, baseline GREEN at both ends, every restore
md5-verified, and the copy byte-identical to the tip afterwards (`diff -rq`,
no output). This is an independent set from the row's nine and from round 2's
twelve; MR-3, ME-1 and MI-1 overlap by design because the brief asked for them
re-run, and all three reproduce.

**Four of them are worth more than the count.**

- **MR-1 and MR-3 both kill exactly one test, and it is the new one.** The old
  `root.resolve()` test is green under a full revert to the buggy comparison.
  The row's explanation of why the old test was blind is confirmed, not assumed.
- **MX-2 is the vacuity check the brief asked for.** A derivation that produced
  an empty set would pass a `len(X) == len(X)` test; here `assertTrue(execs)`
  fires. MX-1 is the other direction, caught by the `os.access` cross-check.
- **MI-2 is the direction that matters** — a list that grew — and it is caught
  three ways, including by consequence.
- **P4\* and P6\* are green mutations, and that is the § 1 finding.** They are
  red only because the *behaviour* tests fire; the pin that claims to read which
  mechanism shipped reads both as "refuse".

---

## 7. What I did NOT verify

1. **I did not reproduce the original write.** Same position as round 2 and as
   the row: the sweep is idempotent and every tree I ran is already swept, so a
   clean run cannot re-derive the defect. § 4's M8 on a seeded copy is the
   evidence; I checked the call-site fix by reading it and by confirming that
   `--root` wins over `$PERRY_PROJECT` in `bin/perry-task:7282`
   (`Path(args.root)… if args.root else Path(os.environ.get("PERRY_PROJECT")
   or Path.cwd()).resolve()`).
2. **One run per tree, five trees.** The four failures agree by name across all
   five, which is why I did not repeat. A single run cannot separate a fifth
   flake from a real failure, and the absence of `test_host_support` in five
   runs is evidence about that flake's rate, not proof it is gone.
3. **`--serial` was not run.** All five used the default parallel path.
4. **I did not observe a real subagent worktree appearing during a real run.**
   § 4's (A) is the mechanism in a temp tree, as the row says.
5. **I did not re-derive § 1's instrumentation figures** ("106 hits",
   "88 + 22 = 110").
6. **I did not audit the rest of `tests/tree_guard.py`'s prose** against the
   code. § 1 measures how little the pin covers; I checked the one bullet the
   pin reads and the `IGNORE_DIRS` paragraphs, not every sentence.
7. **Sharp edge B is reasoned, not exploited.** I did not find a test in this
   suite where an accepted relative `$PERRY_PROJECT` actually sends a write
   outside `$ROOT`; I am reporting the divergence between the two resolution
   rules, not a live escape.
8. **P5 was run against the pin class only**, not the whole module. P4 is the
   same edit in a different spelling and I ran that one whole-module; I am
   naming the shortcut rather than reporting P5's module result as measured.
9. **I did not verify the `.claude`/`.gstack` decision against future intent** —
   only that nothing is tracked under either today (`git ls-files .claude
   .gstack` is empty on both `main` and the tip) and that no test in the suite
   writes there.

---

## Verdict

**PASS.**

All three round-2 fixes are real and each is load-bearing. The resolution fix
closes every spelling round 2 found refused, and MR-1/MR-3 show the new test —
and only the new test — is what catches a revert or a half-fix, which is the
row's own claim about the old test's blindness confirmed by measurement. The
count is genuinely derived and non-vacuous in both directions. The retraction
and the two recorded decisions are complete. Nine mutations of mine are 9/9 red
with a named test each, baseline green at both ends. The merge is clean against
two successive `main` tips and moves the failure count nowhere: 4 across 3, the
same four by name, on five independent trees.

**Fix before merge (1 item):**

- **Defect 1** — `.claude` and `.gstack` are absent from `tests/tree_guard.py`'s
  **"What it does NOT catch, said plainly"** list, while `.DS_Store` and
  `__pycache__` — strictly narrower holes — each have a bullet. The row's own
  § 8.4 calls this the widest of the five holes. One bullet, saying that
  anything under a directory named `.claude` or `.gstack`, **at any depth**, is
  invisible to the guard, including the directory's own creation.

**Fix, or file (4 items):**

- **The pin's claim is stronger than the pin.** `TestTheDocstringSaysWhich
  MechanismShipped` reads which of two *strings* is in `tests/run`, not which
  mechanism shipped: a live re-aim spelled `export "PERRY_PROJECT=$ROOT"` or
  `PERRY_PROJECT=…; export PERRY_PROJECT` is invisible to the regex, and a
  refusal left dead under `if false` still reads as shipped. Either anchor the
  refuse token to a non-comment line too (symmetry with the export check), or
  narrow the docstring's claim to what it does. Both P4 and P6 are caught by the
  behaviour tests, so this is a documentation-of-the-test issue, not a hole.
- **P7's second failure is an `IndexError`**, not a message. Guard
  `self._implemented(...)[0]`.
- **Sharp edge A** — case-differing spellings of `$ROOT` are still falsely
  refused (`cd` succeeds, `pwd -P` does not canonicalise case, and neither does
  `Path.resolve()`), and the refusal suppresses its `resolves to =` line in
  exactly that case, showing the reader two paths that differ only in case with
  no explanation.
- **`24` / `18` in `tests/test_tree_guard.py:516`** is a present-tense count in
  a comment, in the docstring of the test whose reason for existing is that a
  count in a comment is a claim nothing checks. It carries its instrument and
  nothing depends on it; I would still cut it.

*Every experiment ran on copies or in my own detached worktrees. `perry/BOARD.md`
and `perry/tasks.jsonl` untouched; no write-side Perry tool was run against the
project or any worktree of it; `perry-conform declare` and `perry-tasks render`
were never invoked; no identifiers minted.*
