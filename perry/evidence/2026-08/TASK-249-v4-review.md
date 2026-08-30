# TASK-249 — V4 review, round 1

**FAIL.** The work itself is good and I could not break the fix: the call site is
correctly identified, the guard fires on every exit path I could reach, its own
test is real, its control can fail, and M8 reproduces exactly. The row fails on
its **§ 5 baseline**, which is wrong in a way that matters more here than
anywhere else: the result publishes a corrected number for `main`'s fork point,
uses it to conclude that "the PMO measured a working tree with uncommitted board
edits", and the correction does not survive a clean `git archive` of that commit.
A row whose subject is *the suite corrupting its own measurements* cannot ship a
mis-stated measurement that blames another agent's correct one.

Everything below was done on **copies** (`git archive` of `49d83fc` / `1f7a13f`
into `scratchpad/rj249/rj249-*`), never in the reviewed worktree. Nothing was
written into `/Users/bytedance/proj/Perry` or into
`scratchpad/review-249`, and no write-side Perry tool was run against either.
The four files in `scratchpad/review-249` were hashed at 09:39 and are
byte-identical now:

    19370b5e4817143e6bcf4a8bf564cdb9  .perry/events.jsonl
    084728c777af398acda59fc48dc3e843  perry/BOARD.md
    b73d602268fabb1b647265518de117a0  perry/intake.jsonl
    b9a6eaed43359fe26ffad193ee6f709c  perry/journal/2026-08/2026-08-30.md

---

## The defect — § 5's baseline correction, and the accusation resting on it

The result says:

> | `49d83fc`, as delivered by the PMO | 08:48, quiet | 103 | 3098 | 4 |
> | `49d83fc`, `git archive`d to a scratch dir and re-run here | 09:21-09:26 | 103 | 3098 | **3** |
>
> The fourth failure in the PMO's 08:48 figure does not reproduce against the
> fork point's committed tree an hour later … the PMO measured a working tree
> with uncommitted board edits in it.

It does reproduce. Commands:

    cd scratchpad/review-249
    git archive 49d83fc | tar -x -C scratchpad/rj249/rj249-base
    cd scratchpad/rj249/rj249-base && bash tests/run      # 09:43-09:48

Output (`rj249-base.log`):

    ✗ test_diagnose.py
      FAIL: test_the_queue_register_reconciles_with_the_queue_on_this_repository
            AssertionError: 3 != 1 : diagnose and perry-task disagree about how
            many queue rows are waiting on the user
      FAIL: test_perry_itself_passes_its_own_id_checks
      Ran 141 tests … FAILED (failures=2)
    ✗ test_heading_title.py           FAILED (failures=1)
    ✗ test_kr_progress_provenance.py  FAILED (failures=1)
    103 modules · 3098 tests · 288.8s · 8 workers
    ✗ 3 module(s) red

**Four failing tests in three red modules.** Deterministic — `test_diagnose`
re-run alone on the same archive is `Ran 141 tests … FAILED (failures=2)`.

The same shape on the branch (`git archive 1f7a13f`, full `bash tests/run`,
09:48-09:59, `rj249-branch.log`):

    104 modules · 3111 tests · 652.6s · 8 workers
    ✗ 3 module(s) red        ← same four failing tests, by name
      ✓ nothing under …/rj249-branch moved

So **the fork point and the branch are both 4 failing tests / 3 red modules.**
The branch adds no failure — that half of the claim is true and I confirm it.
But the "3" is the runner's own `✗ 3 module(s) red` line read as a failure
count, and the consequences are three:

1. **The named list is short one failure.** § 5 names
   `test_diagnose § test_perry_itself_passes_its_own_id_checks`,
   `test_heading_title § test_none_of_them_contains_its_own_id` and
   `test_kr_progress_provenance § …` as "the same three failures, by name".
   `test_diagnose § test_the_queue_register_reconciles_with_the_queue_on_this_repository`
   is missing. It is one of the two board-data-dependent tests this row's own
   summary is about ("two of the suite's three standing failures are
   data-dependent on board state") — the single most relevant failure in the
   suite to this row, dropped from the row's own baseline.
2. **The PMO's 4 is correct**, and it was measured on a tree that behaved
   exactly like a clean archive. The charge that it "measured a working tree
   with uncommitted board edits — which is this row's own point" is unfounded
   and should be withdrawn. It is also contradicted by the project's own filed
   intake row of 2026-08-29, which already records "the `tests/run` baseline is
   **4 failures on a clean archive copy** and 5 on a worktree carrying today's
   intake rows".
3. It is the one number in the document nobody downstream can re-derive from the
   document, and it was used to discredit a measurement rather than to describe
   this branch.

**Which baseline is right: the PMO's.** `49d83fc` is 103 modules / 3098 tests /
**4 failing tests** (3 red modules) on a clean `git archive`, at 08:48 and again
at 09:43. This branch is 104 / 3111 / **4 failing tests** (3 red modules) — the
same four by name, `+1 module / +13 tests` being exactly `tests/test_tree_guard.py`.
No number here was measured through the defect this row closes.

## Second defect — the ignore-list pin does not pin the list that matters most

§ 6.3 and `tree_guard.py`'s own comment claim the ignore list is pinned so that
"growing it — the cheapest way to make a red run green — has to change a line a
reviewer looks at". There are **three** ignore lists and the pin covers two:

    IGNORE_DIRS      pinned by test_the_ignore_list_is_the_documented_one
    IGNORE_SUFFIXES  pinned by the same test
    IGNORE_NAMES     NOT pinned by anything

`IGNORE_NAMES` is the list that takes **file names**, i.e. the shape that can
name a state file. Mutation on a copy of the branch:

    IGNORE_NAMES = frozenset({".DS_Store", "events.jsonl", "intake.jsonl"})
    python3 -m unittest discover -s tests -p test_tree_guard.py
    → Ran 13 tests in 66.557s
      OK

The whole guard module stays green while the guard is made structurally blind to
`.perry/events.jsonl` and `perry/intake.jsonl` — two of the four files this row
exists to protect. (`BOARD.md` is incidentally covered, because
`TestThePlantedWrite` asserts the literal string `M perry/BOARD.md`; every other
state filename is not.) One line added to the existing test closes it.

---

## checked

**The call site.** `tests/test_task_writer.py:1359` at `49d83fc` is correct, and
the mechanism is exactly as described: `bin/perry-task:7101-7102` resolves
`--root` → `$PERRY_PROJECT` → cwd, and `tests/run:31` cds to `$ROOT`.

**Claim 1 — the four md5s move before the fix and not after.** Own measurement,
two scratch copies, one intake row discharged in each (`Outcome` set to prose;
no identifier minted), the single test run alone:

    python3 -m unittest discover -s tests -p test_task_writer.py \
            -k test_every_accepted_command_runs_and_is_advertised

| file | 49d83fc before | 49d83fc after | 1f7a13f before | after |
|---|---|---|---|---|
| `.perry/events.jsonl` | `19370b5e…` | `3d096503…` | `19370b5e…` | `19370b5e…` |
| `perry/BOARD.md` | `bd51703b…` | `6352b630…` | `bd51703b…` | `bd51703b…` |
| `perry/intake.jsonl` | `b73d6022…` | `53bccb3a…` | `b73d6022…` | `b73d6022…` |
| `perry/journal/2026-08/2026-08-30.md` | `b9a6eaed…` | `f535a39e…` | `b9a6eaed…` | `b9a6eaed…` |

The test was **green both times**. The event that landed, from my run:

    {"ts": "2026-08-30T09:42:18+08:00", "event": "intake-sweep", "id": "",
     "title": "", "count": 1, "actor": "agent", "from": "intake", "to": "journal"}

My `perry/BOARD.md` and `perry/intake.jsonl` after-hashes are **identical to the
result's table** (`6352b630…`, `53bccb3a…`), which is a good independent
corroboration of that measurement.

**One writer among 29.** Own sweep, each name run bare against a fresh untar of a
pristine `49d83fc` + one discharged row, whole tree hashed after
(`rj249-sweep29b.sh`):

    28 × "clean <name> rc=1"
    WRITER intake-sweep rc=0
    ... second sweep on the same tree: refused, IDEMPOTENT: second sweep moved nothing

**Enumerating every in-repo-root invocation — 106 not reproduced; the shape is.**
I instrumented `bin/perry-task` in a pre-fix copy at *process start* (so
argparse-refusals are logged too), recording argv, cwd, `$PERRY_PROJECT`, the
root that would be resolved and the process chain, and ran one full
`bash tests/run`:

    total perry-task invocations during one run: 1979
    by root-resolution source: {'--root': 1891, 'cwd': 88}
    resolved to the REPO ROOT: 110   ({'cwd': 88, '--root': 22})

So **88 un-rooted invocations against the live checkout** (plus 22 that pass
`--root <the repo root>` deliberately). Breakdown of the 88: `list --json` ×22,
`list --all --json` ×16, `events --json` ×16, `--help` ×3, `list` ×2, and the
29-name loop plus `nonesuch`. Exactly one of them writes: `intake-sweep`.
I could not land on 106 — it is a tree-and-revision-dependent number the result
quotes unqualified — but "many reads, exactly one writer" is confirmed, and the
one writer is the one named.

**Verdict on the 105 (87) reads against the live checkout: acceptable, with one
qualification worth a board row.** They cannot mutate, and several read this
repository's board on purpose. But the result's justification (§ 6.5, "reading
this repository's own board") assumes `$PERRY_PROJECT` is unset. Root resolution
is `--root` → `$PERRY_PROJECT` → cwd, so with that variable exported — a live
hazard this session's own dispatch commit names — those 88 calls read *someone
else's* project, and the assertions built on them are then about the wrong tree.
That is a wrong-answer risk, not a corruption risk, so it is a finding rather
than a blocker. (See D5 below for the pre-fix corruption version of it.)

**The EXIT trap fires on the abort paths it claims.** Both tested on a branch
copy with a write planted inside `bin/perry-lint` so that step 1 itself dirties
the tree:

- `--lint` early exit (line 83): guard ran, `+ rj249-lint-plant.txt   (created)`,
  `✗ failures above`, `rc=1`.
- a bare `false` under `set -e` inserted after step 1: same guard output, same
  red banner, `rc=1`.
- a failing step 2 followed by step 3's `[ "$fail" = 0 ] && echo …`: I expected
  an errexit abort there and there is none — both `49d83fc` and `1f7a13f` reach
  step 4. Not a hole; recording it because it is the obvious one to suspect.

**Wiring mutations (my own, on top of the author's seven).** Each applied to a
copy, `TestThePlantedWrite` re-run:

    MR1 the EXIT trap is not installed            RED
    MR3 verify never runs (the trap calls true)   RED
    MR4 a moved tree does not set fail            RED

**Every guard in `tree_guard.py`, not only the seven.** Applied to a copy,
`TestTheManifest` + `TestTheCLI` re-run:

    A  grow IGNORE_NAMES                          GREEN  ← survives; see above
    B  grow IGNORE_DIRS                           RED
    C  shrink IGNORE_SUFFIXES                     RED
    D  directories are not recorded               RED
    E  symlink target recorded as a constant      RED
    F  verify always exits 0                      RED
    G  the failure drops the perry-task hint      RED
    H  a bad invocation exits 1, not 2            RED

**Claim 2 — the guard's test is real, and the control can fail.**
`python3 -m unittest discover -s tests -p test_tree_guard.py -v` → 13 tests, OK.
It does copy the repo, plant into the copy, and drive the real
`bash tests/run --only …`. Two independent falsifications:

- Control can fail: I made `CONTROL` write one file into its own root instead of
  only into a temp dir. `test_a_module_that_stays_in_a_temp_root_is_green` →
  `FAILED (failures=1)`. It is not vacuous.
- Mechanism can fail: I replaced `python3 tests/parallel "$only"` with `true` so
  `--only` runs nothing. `test_the_same_run_is_green_when_the_guard_is_neutered`
  → RED with `"planted by TASK-249's guard test" not found in …`. A broken
  `--only` cannot masquerade as a working guard.

Timing note: 13 tests took 66-102s here, not the claimed 5.1s. My machine was
running three other suites; I did not get a quiet re-measurement, so I am not
calling the 5.1s wrong — only unverified. Guard cost is right: 0.19s warm /
0.92s cold to hash 811 entries, `bash tests/run --lint` 0.50s end to end.

**Claim 3 — M8 reproduces exactly.** Branch copy, `--root` taken back off the
call site, one intake row discharged:

    bash tests/run --only test_task_writer

    1 modules · 281 tests · 178.2s · 8 workers
    ✓ all green                                    ← the module passed
    tests/tree_guard.py: THE SUITE WROTE INTO THE TREE IT RAN IN — …
      M .perry/events.jsonl   (changed)
      M perry/BOARD.md   (changed)
      M perry/intake.jsonl   (changed)
      M perry/journal/2026-08/2026-08-30.md   (changed)
    ✗ failures above                               rc=1

Exactly the four files, from a green module. This is the claim that matters and
it holds.

**The guard is unnecessary on this branch, and I proved it rather than assumed
it.** Full `bash tests/run` on a byte-identical copy of `1f7a13f`: the four files
were unchanged before and after, and step 0 printed
`✓ nothing under …/rj249-branch moved`. The same full run at `49d83fc` also left
them unchanged — because that archive has no discharged intake row for the sweep
to find, which is the idempotence, measured.

**Claim 4 — I found four more ways to defeat the guard.** Each is one planted
module run through the real `bash tests/run --only …` on a fresh branch copy;
each run came back `✓ all green` while the checkout had genuinely moved:

- **D1 · file mode.** `os.chmod(ROOT/"bin"/"perry-lint", 0o600)` — the manifest
  hashes bytes only. `git status` reports a mode change; the guard does not.
  This project ships executables in `bin/` and `templates/*/bin/`.
- **D2 · any directory *named* like a cache, at any depth.** `perry/node_modules/BOARD.md`,
  `.perry/__pycache__/BOARD.md`, `perry/.git/BOARD.md` all invisible —
  `IGNORE_DIRS` is matched on the basename anywhere in the walk, not on a
  top-level path.
- **D3 · any ignored suffix or name, anywhere.** `perry/BOARD.pyc` and
  `perry/.DS_Store` invisible. Combined with the unpinned `IGNORE_NAMES` above,
  this is the same weakness twice.
- **D4/D5 · anything outside `$ROOT` — the one that matters here.** The guard
  hashes `$ROOT` and only `$ROOT`. Demonstrated with the real defect: branch
  copy, `--root` reverted, `PERRY_PROJECT` pointed at a *second* checkout:

      PERRY_PROJECT=…/rj249-victim bash tests/run --only test_task_writer

      0. tree guard — the tree the suite started in is the tree it ends in
        ✓ nothing under …/rj249-m8env moved          ← the runner tree, clean

      victim  .perry/events.jsonl   19370b5e… → 3a9d18c9…
      victim  perry/BOARD.md        bd51703b… → 6352b630…
      victim  perry/intake.jsonl    b73d6022… → 53bccb3a…
      victim  perry/journal/…-30.md b9a6eaed… → f535a39e…

  All four files of this row moved in a *different* Perry checkout and the guard
  said the tree was clean. This repository runs several worktrees at once and
  `$PERRY_PROJECT` is on this session's own hazard list, so it is not
  hypothetical. The `--root` fix immunises this call site (`--root` beats
  `$PERRY_PROJECT`, `bin/perry-task:7101`), so it is a limitation of the guard,
  not a live defect — but it belongs in `tree_guard.py`'s "what it does NOT
  catch" list beside the three that are already there.

**The fixture-was-unreachable argument: the author is right.** The pre-fix call
site is

    r = subprocess.run(
        ["python3", str(PERRY_HOME / "bin" / "perry-task"), name],
        capture_output=True, text=True)

— a bare `subprocess.run` on a hand-built argv. It constructs no `Project()`,
touches no fixture, and passes through no helper that could have refused an
in-repo root. A fixture-side guard would have protected exactly the call sites
that were already passing `--root` and would have been structurally incapable of
seeing this one. Taking the guard was the right call, and taking the call-site
fix as well was right too: the guard only reddens where the sweep has a row to
find, so without the fix the defect is live on every fresh clone and merely
invisible on an already-swept tree. One correction to the framing: the committed
`perry/evidence/2026-08/TASK-249-spec.md` (from `f92aed1` on `main`; it is not on
this branch) contains no "two shapes" — its Deliverable is `—`, and neither the
board row nor the dispatch commit names a fixture option. "The spec offered two
shapes" is not checkable against anything in the repository.

## not-checked

- The author's harness `task249_tree_guard_mutation_harness.py` is scratch and
  not committed, so I could not re-run their seven mutations as written. I ran
  eleven of my own instead (A-H, MR1/MR3/MR4), which cover the same surface and
  one they did not.
- The 5.1s figure for `test_tree_guard.py` — the machine never went quiet.
- The `106` figure — see above; I measured 88 un-rooted / 110 total against the
  repo root and cannot reconstruct which tree gives 106.
- Whether `test_the_queue_register_reconciles_with_the_queue_on_this_repository`
  and `test_perry_itself_passes_its_own_id_checks` are themselves correct. They
  are pre-existing and not this row's.
- The flake (`test_host_support § test_concurrent_mixed_registers_do_not_exceed_global_cap`)
  did not fire in either of my full runs. Recording it as flaky rather than
  filing it was the right call; I have nothing to add.

## what would clear this

1. Correct § 5: the fork point and the branch are both **4 failing tests / 3 red
   modules**, name all four, withdraw the "the PMO measured a working tree"
   inference, and say plainly that the branch adds no failure — which is true.
2. Pin `IGNORE_NAMES` in `test_the_ignore_list_is_the_documented_one`.
3. Add "anything outside `$ROOT` — including another checkout, when
   `$PERRY_PROJECT` is set" and "file mode" to `tree_guard.py`'s "what it does
   NOT catch" list, and to § 6.

Nothing in 1-3 touches the fix or the guard, both of which I tried hard to break
and could not.
