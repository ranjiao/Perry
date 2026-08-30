# TASK-234 — V4 review, round 4 (delta on the round-3 corrections)

Subject: branch `coding/task-234-conformance-store`, tip `f783dd5`.
Base: `main` at `014dc6a`. `main` is live and moved twice during this round —
`1163f74` when the worktrees were cut, `014dc6a` when the baseline ran,
`1cbc025` by the time this file was written. Every number below is against
`014dc6a`, and the merge probe is `014dc6a` + `f783dd5` = `e5296a1`.

Reviewer worked in its own detached worktrees (`scratchpad/r234r4-tip`,
`-main`, `-probe`, `-mut`, `-mut2`) and its own branch. The project under
review was never modified. Every mutation was applied inside a private
worktree, restored by exact text with the file `md5` asserted, and the tree
verified clean by `git status --porcelain` before and after each run.

**Verdict: FAIL — one live, measured defect on the standard this row has now
been reopened on twice, plus three green mutations.** The round-3 FAIL itself
is genuinely fixed; the sweep, the end-to-end proof and the two GREEN findings
(M35, M36) all hold up. The FAIL is § 1.

---

## 0 · Baselines, counted the correct way, measured this session

The count is the sum of the per-module `FAILED (failures=N)` lines. The summary
line counts MODULES; `grep -c '^FAIL:'` undercounts because `tests/parallel:283`
truncates a red module's stderr to its last 25 lines with nothing visibly
elided, and `test_diagnose`'s first `FAIL:` header falls outside that window.

```
grep -oE 'FAILED \(failures=[0-9]+' <log> | grep -oE '[0-9]+$' | paste -sd+ - | bc
```

| tree | modules | tests | seconds | modules red | **test failures** | `grep -c '^FAIL:'` (the trap) |
|---|---|---|---|---|---|---|
| `main` @ `014dc6a` | 104 | 3124 | 298.5 | 3 | **4** | 3 |
| tip `f783dd5` | 103 | 3141 | 326.1 | 3 | **4** | 3 |
| merge probe `014dc6a` + `f783dd5` = `e5296a1` | 104 | 3167 | 264.4 | 3 | **4** | 3 |

`FAILED (errors=…)` sums to **0** in all three — failures and errors are
different words and both were counted. Red set identical in all three, by name:
`test_diagnose.py` (2), `test_heading_title.py` (1),
`test_kr_progress_provenance.py` (1). The merge is clean (no conflicts) and
introduces no new red. **`test_host_support` did not appear in any of the three
runs**, so none of these numbers depends on the known intermittent being quiet
in one run and not another.

The three runs were sequential on one machine, not parallel, so the seconds are
comparable.

**md5 bracket** (`git ls-files -z | xargs -0 md5 -q | md5 -q`), before and
after each suite run, `git status --porcelain` empty after each:

| run | before | after |
|---|---|---|
| `main` @ `014dc6a` | `5c4495f56f488259b6e8c406d2370f28` | `5c4495f56f488259b6e8c406d2370f28` |
| tip `f783dd5` | `a1dfc6930646ffb168d02a7311e3bb90` | `a1dfc6930646ffb168d02a7311e3bb90` |
| probe `e5296a1` | `bbc44d42fbcf8882a9d9b009c10b336a` | `bbc44d42fbcf8882a9d9b009c10b336a` |

---

## 1 · THE DEFECT — the handed-back command is built unquoted

This is the same standard as the round-3 FAIL, one register further down. Round
3: the command named the wrong project. Round 4: the command names the right
project **in a form the reader cannot run**.

`bin/perry-conform § _root_flag` is the whole of it:

```python
def _root_flag(root_arg: str | None) -> str:
    return f" --root {root_arg}" if root_arg else ""
```

No quoting, and `shlex.quote` appears nowhere in `bin/` or `viewer/` — checked,
not assumed.

**Measured end to end on a planted project** (a throwaway fixture of my own
making, under `scratchpad/r4space/My Project`; nothing was run against Perry or
any worktree of it):

```
$ cd .../r4space/elsewhere
$ python3 bin/perry-conform migrate --root "/…/r4space/My Project"
    --- .perry/conformance.md
    +++ what Perry reads out of it
    @@ -15,3 +15 @@
     | BOARD.md | 2 | 2026-08-20 | declare |
    -
    -reminder: check OKR.md

Fix those lines, then run:
    perry-conform migrate --root /…/r4space/My Project        ← unquoted
**Nothing was written.**
```

The reader fixes the file exactly as told, then copies that line:

```
$ python3 bin/perry-conform migrate --root /…/r4space/My Project
perry-conform: refused — usage: perry-conform migrate — it takes no file. The
conversion carries the WHOLE record across or refuses; …
rc=1
```

`Project` was parsed as a file argument. The reader's `.perry/conformance.md`
is still there, no `.perry/conformance.jsonl` was written, and the error message
is about a mistake the reader did not make. With the same root quoted, the same
command exits 0 and converts — so the file was always fine and only the
handed-back spelling was wrong.

Why this is in scope rather than pre-existing noise:

- **It is in the sentence this round wrote.** Both `migrate_record` refusals
  gained `{r}` in this round's `c184164`. Before it they had no root at all
  (the round-3 FAIL); after it they have one that does not survive a copy.
- **The row's own standard names it.** § 1.2: *"a named command that errors is
  worse than none"*. This is that case, measured.
- **It is the whole class, not one site.** Every one of the 14 handed-back
  commands `bin/perry-conform` emits and all four in `bin/perry-migrate` are
  built by `_root_flag`. That includes the `message_for` legacy branch the
  round-3 reviewer verified as *"yes, verified"* — verified against a
  space-free `tempfile` root. Reproduced on that branch too:

```
  perry-conform migrate --root /…/r4space/My Project
```

- **The row's own end-to-end proof is one character from catching it.**
  `test_the_named_command_converts_the_readers_project_from_elsewhere` takes the
  command out of the message and runs it through `shlex.split` — the exact
  parser that exposes this — but `Project()` uses
  `tempfile.TemporaryDirectory()`, which never yields a path with a space. I
  replayed the test's own steps verbatim with a spaced root:

```
named:       ['perry-conform migrate --root /…/r4space/My Project']
shlex.split: ['perry-conform', 'migrate', '--root', '/…/r4space/My', 'Project']
rc = 1 ; reader's store written? False ; markdown still there? True
```

  So the proof would go red today if a single fixture root contained a space.

- **Neither guard sees it.** `assert_every_command_carries` asserts
  `f"--root {root}" in cmd`, which is true of the broken line;
  `tests/sweep_handed_back_commands.py`'s `ROOT` regex asks only whether
  `--root` is present, never whether the phrase is runnable.

**Severity, stated plainly so it is not overstated.** This is strictly less
harmful than the round-3 defect: it fails loudly (rc=1) rather than succeeding
about someone else's project, and it only bites a project path containing a
space. It is also a pre-existing spelling that this round propagated to five
new sites rather than one it invented. But it is the same standard, in the same
sentence, found by doing the same thing round 3 did — running the command the
refusal hands back — and the fix is one call to `shlex.quote` in `_root_flag`.

---

## 2 · Green mutations

Discipline for all of them: anchored on exact text with a uniqueness assertion,
`__pycache__` cleared, slept past the whole-second boundary before and after,
`PYTHONDONTWRITEBYTECODE=1`, target asserted **GREEN** before mutating,
restored by exact text with the file `md5` asserted and the tree re-checked
clean. Harness: this reviewer's own, in `scratchpad/r234r4-mut` and `-mut2`.
Target set for every run below: **the whole of `tests.test_conformance` and
`tests.test_migrate`** unless noted.

### 2.1 · R-N3 and R-N4 — two of three call sites drop the root, green

`bin/perry-migrate § apply_plan` calls `rollback_message` three times. Round 4
threaded `root_arg` into all three. Only one of the three is pinned.

| id | site | mutation | result |
|---|---|---|---|
| R-N3 | `apply_plan`, the **write failed** path (`raise Refused(rollback_message(point, e.key, exc, root_arg=root_arg))`) | `root_arg=None` | **GREEN — SURVIVOR** |
| R-N4 | `apply_plan`, the **digest mismatch** path (`allow_changed=allow_changed, root_arg=root_arg`) | `root_arg=None` | **GREEN — SURVIVOR** |
| R-N5 | `apply_plan`, the **declaration refused** path (`}, root_arg=root_arg)`) | `root_arg=None` | RED (1) |

The two survivors are TASK-044 guarantee 3's own paths — a write that fails
(read-only directory, full disk, permission revoked mid-run) and a write that
lands with the wrong digest. Both hand the reader
`perry-migrate restore <run-id>` as the way back. With the root dropped there,
a reader who ran `perry-migrate apply --root /their/project` from elsewhere is
handed a restore command that looks for the restore point under whatever
project they are standing in.

**Why they are green is the round-3 defect one file over.** The tests that
exercise those two paths call `M.apply_plan(plan, SCHEMA)` — positionally, with
no `root_arg` — so `root_arg` is `None` on both sides of the mutation and
`_root_flag` returns `""` either way. The assertion about the handed-back
command is being made from inside a run that never passed a root. That is
verbatim the sentence § 11 of the RESULT writes about the 16 helper
invocations.

Controls, so this is not an artefact of my target set: **R-N6** (make
`bin/perry-migrate § _root_flag` return `""` unconditionally) is RED on two
tests, and **M36** (mutate `rollback_message` itself) is RED — so the function
is guarded; only two of its three call sites are not.

### 2.2 · R-N8 — the sweep's ok/bad decision is unguarded

`tests/test_conformance.py § test_no_refusal_in_perry_conform_names_a_command
_without_the_root` **imports** `tests/sweep_handed_back_commands.py` rather
than restating its rule — which the RESULT argues for, correctly. The cost is
that the rule is now shipped code with no positive control.

| id | site | mutation | result |
|---|---|---|---|
| R-N8 | `sweep § ROOT` | `re.compile(r"...")` → `re.compile(r"")` (match everything, so nothing is ever MISSING) | **GREEN — SURVIVOR** (whole of `tests.test_conformance`) |
| R-N9 | `sweep § CUE` | `re.compile(r"(?!x)x")` (match nothing, so no phrase is ever an instruction) | RED (1) — the `assertGreaterEqual(len(handed), 12)` fires |

The test's non-vacuity check guards against the sweep finding **nothing**. It
does not guard against the sweep calling **everything ok**. A one-character
edit to `ROOT` turns the source guard into a no-op *and* makes
`python3 tests/sweep_handed_back_commands.py --all …` report a census of zero
members, which is the number § 1.2's table is built from. The row's own name
for this shape is "an assertion sitting beside the thing that matters".

The missing control is cheap: assert the sweep reports MISSING on a known-bad
snippet.

### 2.3 · R-N13 — the restore point's expected-after entry is unpinned

| id | site | mutation | result |
|---|---|---|---|
| R-N13 | `bin/perry-migrate § apply_plan`, the `update_expected_after(point, P.CONFORMANCE_LEGACY_FILE, …)` call | delete it (`pass`) | **GREEN — SURVIVOR** (whole of `tests.test_migrate`) |

That call was introduced by this branch (`095b5da`). Without it the restore
point keeps the pre-declaration digest for `.perry/conformance.md`, while a run
that converted the record has deleted the file — so `undo` is comparing against
a signature the run itself invalidated. Corroborated by coverage: the only two
places `tests/test_migrate.py` names `conformance.md` are the symlink preflight
(line 732) and the unconvertible-record refusal (line 905). **No test applies a
migration to a project holding a legacy record and then restores it**, which is
the round trip this call exists for.

I did not demonstrate a wrong answer out of it — only that a call this branch
added, on the recovery path, is unpinned.

### 2.4 · R-N10, R-N11, R-N12 — unpinned by construction, recorded not charged

| id | site | mutation | result |
|---|---|---|---|
| R-N10 | `tests/test_conformance.py`, the `overclaim` regex | `re.compile(r"(?!x)x")` | GREEN |
| R-N11 | `bin/perry-conform § declare` | `*, root_arg: str | None = None` (give the keyword-only parameter a default back) | GREEN |
| R-N12 | `bin/perry-conform § migrate_record` | same | GREEN |

None of these is charged as a defect. R-N10 mutates a test's own matcher, which
is green almost everywhere. R-N11 and R-N12 are green because no caller in the
tree omits the argument — the no-default shape protects a *future* caller, and
no test can hold that. They are recorded so a later sweep does not re-find them
and file them as findings. (A signature assertion via `inspect` would pin them
if the row wants the shape guaranteed rather than merely written.)

---

## 3 · The three same-line mutations — two claims do not survive measurement

§ 6.1 argues: *"M32 is invisible to the source guard … M34 is invisible to
**both** … and is caught only by the end-to-end test … Three layers, one per
failure mode, each demonstrated by the mutation the other two miss."*

Measured, whole of `test_conformance` + `test_migrate`, distinct failing
methods in brackets:

| mutation | failures | distinct methods | source guard red? | helper red? | end-to-end red? |
|---|---|---|---|---|---|
| M30 / M40 (`{r}` deleted from the fixed-point template) | 8 | 6 | **yes** | yes (4) | yes |
| M34 (`--root /nowhere-at-all`, spelled correctly) | 7 | 5 | no | **yes (4)** | yes |
| M32 (`_root_flag(None)` — the runtime value) | 20 | 18 | no | yes (16) | yes |

- **M34 is *not* invisible to the helper.** `assert_every_command_carries`
  asserts `f"--root {root}"` — the *exact* root, not the presence of a
  `--root` — so a correctly-spelled wrong root reddens every helper invocation
  that reaches the fixed-point branch. Four of them do, and all four go red.
  The claim that only the end-to-end test catches M34 is false as measured. The
  layer that is genuinely alone on M34 is not needed for M34; what the
  end-to-end test uniquely covers is *running* the command, which is what
  caught § 1 above.
- **M40 is the same bytes as M30**, so "M40 is caught only by reading the
  source" cannot be true of either; it reddens the source guard, the helper and
  the end-to-end test together.
- **M32's "reddens all 16 at once" checks out.** 20 failures = the 16 helper
  invocations + 4 other tests; 18 distinct methods = the 14 helper methods + 4.
  That is an independent confirmation of § 1.1's corrected **14 methods / 16
  invocations**, and of its 4 / 12 split: M34, which mutates only the
  fixed-point branch, produces exactly 4 helper failures.

The three layers are all real and all load-bearing. The *argument* for why
three are needed is weaker than stated.

---

## 4 · M35 and M36 — re-run, both now red for the stated reason

| id | mutation | result | failing |
|---|---|---|---|
| M35 | `apply_plan` stops carrying its root into `C.declare` (`root_arg=None`) | RED (1) | `test_an_unconvertible_markdown_record_refuses_and_names_the_way_back` |
| M36 | `rollback_message` drops `{_root_flag(root_arg)}` from `perry-migrate restore <id>` | RED (1) | same |

**M36's original path is still covered.** The reason M36 was green when first
pointed at the successful-run test is that `perry-migrate restore <id>` is
named on two code paths. I mutated the *other* one:

| id | mutation | result |
|---|---|---|
| R-N7 | `render`'s `undo with: perry-migrate restore {applied['run']}{r}` → drop `{r}` | RED (1) — `test_every_way_back_this_tool_names_carries_the_root` |

So both surfaces are guarded, and re-pointing M36 did not abandon the first
one. Two more plumbing hops I added, both RED:

| id | mutation | result |
|---|---|---|
| R-N1 | the CLI stops passing `root_arg` into `apply_plan` | RED (1) |
| R-N2 | the CLI stops passing `root_arg` into `do_restore` | RED (1) |

---

## 5 · The sweep, reviewed as code

### 5.1 · It does what the RESULT says on the trees it names — confirmed

```
$ python3 tests/sweep_handed_back_commands.py bin/perry-conform
14 handed-back command(s), 16 mention(s); 0 handed back without the caller's root
rc=0
```

And the before/after census reproduces exactly. Run over
`git show 7d3f93f:bin/perry-conform` and `…:bin/perry-migrate`:

```
7 handed back without the caller's root      (2 in perry-conform, 5 in perry-migrate)
```

and over the tip's eight files with the row's own command: **3 left, all in
`bin/perry-migrate`**, rc=1. The `14 / 2 → 14 / 0` and `7 / 5 → 7 / 3` table in
§ 1.2 is correct.

I also read all 16 of `bin/perry-conform`'s "mention" rulings by hand. Every
one is genuinely a mention — usage strings, provenance values, prose naming a
tool the reader is told *not* to run. No false negative there.

### 5.2 · Recall — the blind spot is five shapes, not the one the docstring names

The sweep's docstring states one blind spot: *"a command built into a name that
says nothing, e.g. `s = "perry-x …"`"*. I planted **15 genuinely root-dropping
handed-back commands**, in a file of my own, and ran the shipped sweep over it:

| # | spelling | found? |
|---|---|---|
| 1 | f-string, indented continuation line (the shipped shape) | ✔ |
| 2 | f-string, ``run `perry-conform migrate` `` inline | ✔ |
| 3 | `"…".format(n=3)` | ✔ |
| 4 | `"…" % 3` | ✔ |
| 5 | `+` concatenation across two literals | ✔ |
| 6 | `+` concatenation splitting the command mid-word | ✔ |
| 7 | module constant `MIGRATE_HINT`, interpolated | ✘ |
| 8 | local `fix = "perry-conform migrate"`, interpolated | ✘ |
| 9 | `msg = …` then `msg += "    perry-conform migrate\n"` | ✔ |
| 10 | the same, split mid-word (phrase reported truncated to `perry-conform`) | ✔ |
| 11 | `"\n".join([...])` | ✔ |
| 12 | a nested helper `def way_out(): return "perry-conform migrate"` | ✘ |
| 13 | prose cue the CUE list does not contain (*"is spelled …"*) | ✘ |
| 14 | a dict of fixes, `FIXES["legacy"]` | ✘ |
| 15 | two bare `print()` calls | ✔ |

**10 found, 5 missed — recall 67 % on plausible spellings.** The `.format`,
`%`, `+`-concatenation and multi-statement cases the brief asked about are all
caught, and that is a real strength: the AST walk earns its keep. What escapes
is any command that reaches the message **through a name** — module constant,
local, dict value, helper return — unless that name happens to match
`NAMED_AS_COMMAND`, plus any instruction whose cue word is not one of
`run / with / is / try / use`.

Consequence for the RESULT's wording: § 1.2 says *"this is a class, and here is
how many members it has"* and prints `7` and `3`. Those are **lower bounds
under one rule**, not a census. The row is honest that a blind spot exists; it
under-describes its size. Note that § 1's defect is a sixth shape the sweep
cannot see at all, because the phrase it looks for is present and correct.

### 5.3 · The three excused members — the excuse is inaccurate for two

§ 10.9 excuses the three remaining `bin/perry-migrate` members as *"all three
name a different tool, all three sit in functions with no root in scope"*.
Resolved the enclosing function of each off the AST:

| site | phrase | enclosing function | root in scope? |
|---|---|---|---|
| `bin/perry-migrate:672` | `perry-goals commit --migrate` | `fix_tables(lines, spec, schema, changes, rewritten)` | **no** — excuse holds |
| `bin/perry-migrate:1681` | `perry-tasks render --write` | `_plan_task_store(plan)` | **yes** — `plan.project_root` and `plan.state_root`, used two lines above |
| `bin/perry-migrate:1681` | `perry-tasks write --from-board` | same | **yes** |

The *caller's typed* `root_arg` is genuinely not in scope, and threading it
would change `plan_project`'s signature — that part of § 10.9 is right. But
"functions with no root in scope" is not, for two of the three, and it is the
half of the sentence that makes the exemption sound structural.

More importantly, **§ 10.9 does not say what those two commands do.**
`perry-tasks render --write` accepts `--root` (`bin/perry-tasks:1258`) and
without it writes `state_root / "BOARD.md"` under the reader's *current
directory* (`bin/perry-tasks:220`). `_plan_task_store` is reached from
`plan_project`, which runs on both the dry run and the apply. So a reader who
runs `perry-migrate --root /their/project` from elsewhere and hits the
store-baseline refusal is handed a command that, copied, **rewrites a different
project's board** — strictly worse than the rc=0 no-op the round-3 FAIL was
about. The row files these three as lower priority than the ones it fixed; on
harm they are higher.

I did not build the fixture that triggers that refusal end to end (§ 8).

---

## 6 · The signature change

`root_arg` is keyword-only with no default on both functions, confirmed by
`inspect`:

```
migrate_record: (project_root: 'Path', *, root_arg: 'str | None') -> 'dict | None'
declare       : (…, run: 'str' = '', *, root_arg: 'str | None') -> 'dict'
```

- **Callers, enumerated.** `migrate_record`: two, both in `bin/perry-conform`
  (`declare`, and the `migrate` subcommand). `declare`: two —
  `bin/perry-conform § main` and `bin/perry-migrate § apply_plan` via
  `C.declare`. No test calls either directly (`tests/` mentions them only
  inside `tests/mutate_task_234.py`'s anchor strings). `bin/perry-task`,
  `bin/perry-goals` and `bin/perry_md_store.py` load `perry-conform` as a
  module but reach only `gate()`, `_root_flag()`, `lint()`, `load_schema()`
  and `state_files()` — checked, not assumed. **No call site works only by
  passing positionally, and none is stubbed.**
- **Omission is a `TypeError`, and nothing swallows it.** Verified by calling
  both with the argument missing:
  `TypeError: migrate_record() missing 1 required keyword-only argument: 'root_arg'`.
  `bin/perry-conform § main` and `bin/perry-migrate § main` both catch
  `Refused` only; `apply_plan`'s handler is
  `except (OSError, Refused, C.Refused, ValueError)`. The one
  `except (…, TypeError)` in `bin/perry-migrate` (line 2033) is inside
  `load_restore_payload` and is nowhere near this path. `bin/perry-diagnose`'s
  broad `except Exception` blocks never reach `declare`.
- **The discipline stops at the file boundary, and that is worth saying.**
  `bin/perry-migrate`'s three new root parameters all keep a silent default:

```
apply_plan       (plan, schema, declare=True, root_arg: str | None = None)
rollback_message (point, key, why, allow_changed=None, root_arg: str | None = None)
do_restore       (project_root, positional, do_list, as_json, root_arg=None)
```

  The RESULT's own argument for the no-default shape — *"a new caller cannot
  inherit the omission by saying nothing"* — does not apply to any of these,
  and § 2.1's two green survivors are exactly a caller saying nothing.

---

## 7 · What else was checked and holds

- **The end-to-end extraction is genuinely programmatic.** `commands_named`
  reads the message text; the test does `argv = shlex.split(cmd)` and runs
  `["python3", CONFORM, *argv[1:]]`. Nothing in the path reconstructs the
  expected command. The two assertions that touch the command's shape are
  negative (`assertNotEqual(argv[1:], ["migrate"])`) and an identity check on
  `argv[0]`. Step 2 measures the harm on the live tree before step 4 runs the
  named command, so a tree where the bare command *worked* would be reported
  rather than silently passed.
- **No call site of `assert_conversion_refuses` was weakened.** I diffed
  `tests/test_conformance.py` across `7d3f93f..f783dd5`: every change is an
  addition; no assertion was deleted or relaxed. `assert_every_command_carries`
  is applied unconditionally at the helper, not behind a flag.
- **`perry-conform` really is at zero.** Sweep rc=0, empty finding list, and
  all 16 mention rulings read by hand.
- **Ten of the row's own numbered mutations re-run independently, all RED:**
  M4, M6, M11, M12, M16, M30/M40, M32, M34, M35, M36. M4, M6, M11, M12 and M16
  are in the M1–M21 block that round 3 explicitly did **not** re-run, so they
  had never been reproduced by anyone. M12 reddens two tests, one of which is
  the new end-to-end proof — a useful sign that the proof is wired to real
  behaviour and not only to the message.
- **The CRLF guard is real but narrower than "the phrase describing what the
  file is compared against".** The regex is
  `byte[- ]for[- ]byte(\s+identical)?\s+(to\s+)?what`. Of nine plausible
  overclaims I put to it, it caught 3 and **evaded 5**: *"byte-for-byte
  identical to the file … wrote"*, *"compared byte-for-byte against what …"*,
  *"byte-for-byte with what …"*, the same phrase with a U+2011 non-breaking
  hyphen, and *"bytewise"*. It does catch M38's exact shape. The positive pins
  are **not vacuous** — `"ine-for-line, not byte-for-byte"` occurs exactly once
  in each of `bin/perry-conform` and `bin/README.md`, in the correcting
  sentence itself, and deleting it reddens the test (M39). But the pin is a
  substring check: a file could keep that sentence and contradict it elsewhere
  in an evading spelling.
- **The corrected numbers are correct.** 14 helper methods / 16 invocations,
  and the 4 / 12 fixed-point / unreadable split, both independently confirmed
  by the M34 and M32 failure counts (§ 3).

---

## 8 · What I did NOT verify

1. **The row's `40/40`.** I re-ran 10 of the 40 and added 13 of my own. M1–M3,
   M5, M7–M10, M13–M15, M17–M21, M31, M33, M37, M38, M39 were not re-run by me,
   so `40/40` remains unconfirmed beyond the 10 I checked plus the 8 round 3
   checked. R-N13 is adjacent to the row's M17 but is a different site — treat
   it as mine, not a reproduction of theirs.
2. **The `_plan_task_store` refusal end to end.** I established statically that
   `plan.project_root` is in scope, that the refusal is reachable from
   `plan_project` on both dry run and apply, and that `perry-tasks render
   --write` writes the cwd project's `BOARD.md` when given no `--root`. I did
   not build a fixture whose task store disagrees with its board and watch the
   message come out.
3. **The `fix_tables` / `perry-goals commit --migrate` member**, beyond
   confirming no root is in scope there.
4. **A `.perry/conformance.md` hand-maintained by anyone but Perry.** Same gap
   the RESULT declares in § 10.3 and round 3 declared. I did not look for one.
5. **The board and `perry/tasks.jsonl`.** Untouched and unread; the PMO owns
   them. No identifiers were minted.
6. **`bin/perry-lint`'s 22 fix hints** (§ 10.10). Not re-measured.
7. **Whether `_root_flag`'s unquoted output breaks on characters other than a
   space** — quotes, `$`, newlines in a project path. Only the space case was
   measured.
8. **`schema/state-schema.json`, `reference/config.md`, `bin/README.md`**
   beyond reading the diff and the two sentences the CRLF guard pins.
9. **Anything under `.perry/events.jsonl`.** No write-side Perry tool was run
   against the repository or any worktree of it. `perry-conform declare` was
   run **only** inside my own throwaway fixtures under `scratchpad/r4space`,
   never against Perry. `perry-tasks render --write` was never run anywhere.

---

## 9 · Verdict

**FAIL.**

The round-3 FAIL is genuinely closed: the two refusals carry the caller's root,
`declare` and `migrate_record` cannot silently inherit an omission, the sweep's
census reproduces, the end-to-end proof extracts and runs the command rather
than constructing it, and M35 and M36 — the two the row found GREEN and
recorded rather than re-pointed quietly — are both red for the stated reason,
with M36's original surface still covered (R-N7). Six of the row's mutations
that nobody had ever reproduced are red. The corrected counts (14/16, 4/12) are
right.

The FAIL is § 1: **the command the refusal hands back is built by unquoted
string interpolation, so on a project path containing a space the reader who
copies it gets `rc=1` and a usage error about a file argument they never
typed** — measured on a planted project, on the sentence this round rewrote, on
the standard the row states in its own § 1.2. The row's own end-to-end proof
would catch it if one fixture root had a space in it; `shlex.quote` in
`_root_flag` closes it in one line.

Four green mutations support the verdict rather than carry it: two of
`rollback_message`'s three call sites can drop the caller's root undetected
(§ 2.1), the sweep's ok/bad decision can be disarmed with the suite green
(§ 2.2), and the restore point's expected-after entry for the legacy record —
a call this branch added on the recovery path — can be deleted with the whole
of `tests.test_migrate` green (§ 2.3). Two claims in the RESULT do not survive measurement — M34 is not
invisible to the helper (§ 3), and § 10.9's *"no root in scope"* is untrue for
two of the three excused members, where the handed-back command writes to the
wrong project rather than no-opping (§ 5.3).

---

*checked:* every suite run, mutation and probe was performed in this reviewer's
own detached worktrees (`scratchpad/r234r4-tip`, `-main`, `-probe`, `-mut`,
`-mut2`), never in `/Users/bytedance/proj/Perry`. Destructive verification was
done on planted throwaway projects under `scratchpad/r4space`, never on the
repository. Every mutated file was restored by exact text with its `md5`
asserted; one mutation left in place by an external timeout was restored the
same way and the tree digest re-checked against the pre-mutation value. No
`git checkout`, `stash`, `reset` or `clean` was run in any tree. No write-side
Perry tool was run against the project or any worktree of it. No identifiers
were minted; `perry/BOARD.md` and `perry/tasks.jsonl` were not touched.
