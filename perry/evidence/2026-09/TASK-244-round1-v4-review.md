# TASK-244 — round 1, V4 review

**Criteria**: `perry/evidence/2026-09/TASK-244-spec.md` (read at
`coding/task-247-config-predicate`), including its `## Bound` and the
`### Correction, 2026-09-02` subsection. The Bound wins over the mid-run
message: **this row is the binding module only.**

**Under review**: `8829174` on `coding/task-244-suite-floor` —
`tests/header_rule.py` (+119/−48), `tests/test_header_rule_harness.py`
(+103/−3).

**Method**: everything below ran in a scratch directory, never in the live
checkout. `git archive coding/task-244-suite-floor` was unpacked to
`…/scratchpad/v4-244/tree` (the branch, tracked files only, no `.claude`);
`tree_old` is the same tree with `tests/header_rule.py` and
`tests/test_header_rule_harness.py` replaced by their `8829174^` versions;
`tree_mut` is the mutation copy. All plants went into those copies. Two
read-only scans were run against the live checkout at
`/Users/bytedance/proj/Perry` (`readers_under`, `offenders_by_symbol`,
`header_sites`) — reads only, no writes.

**Machine**: 14 cores, `load averages` reported at the head of every timing
below. **This was not a quiet machine** — load ran between 6.0 and 38.0 across
the session, with other agents' suites live. Every wall figure here is
therefore an upper bound and a ratio, not a quiet-machine number.

---

## What holds up

### 1 · The soundness argument is correct, and it is a property of the code

The claim is that `offenders_by_symbol` carries no state across files, so
`offenders_at` can answer about one file without reading the tree. Verified
structurally, not by reading the author's paragraph:

- Every module-level binding in `tests/header_rule.py` is a `frozenset` or a
  `tuple` of literals (`BLESSED`, `THE_RULE`, `ITERABLE_WRAPPERS`,
  `ROW_PRODUCERS`, `NOT_A_READER`, `CARRIED_KEYS`). No cache, no
  `lru_cache`, no `global`, no accumulator.
- `_RowLocals.__init__` takes `tree: ast.AST` and nothing else. Its `funcs`,
  `bodies`, `by_name`, `aliases`, `blessed` and `rule` are all derived by
  `ast.walk` over that one tree. It never touches the filesystem.
- The only filesystem reads in the module are `is_python`, `readers_under`
  and `_offenders_in_reader`, each on a single path.

So the analysis of a file is a pure function of that file's bytes plus the
reader gate. The **only** place old and new can disagree is the gate — and
`offenders_at` calls `is_reader`, which is `readers_under`'s own membership
test, extracted verbatim.

### 2 · Equivalence, measured, including a hunt for a 112th plant

`equiv.py` loaded both `header_rule.py` versions side by side and compared
**OLD `offenders_by_symbol(root)` filtered to `rel`** against **NEW
`offenders_at(root, rel)`**, for every reader in the tree, under ten tree
states. Nine of those states were plants constructed specifically to break the
per-file claim:

| plant | shape | old | new |
|---|---|---|---|
| `alias-import-fold` | `from viewer.tables import squash as fold` | 2 | 2 |
| `cross-file-def` | symbol reached through a second module (`helper_mod.squash`) | 2 | 2 |
| `needs-sibling` | offends only via `from sibling import squash as fold`, sibling present | 2 | 2 |
| `needs-sibling-absent` | the same file, sibling **removed** | 2 | 2 |
| `scalar-half` | branch (c), one cell | 1 | 1 |
| `no-suffix-no-shebang` | the `D20`/`S12` admission shape | 2 | 2 |
| `deep-dir` | `templates/x/bin/…` | 1 | 1 |
| `excluded-dot-perry` | inside `.perry` | 0 | 0 |
| `the-rule-definer` | beside `viewer/tables.py` | 1 | 1 |

No divergence anywhere, and `needs-sibling` vs `needs-sibling-absent` is the
informative pair: the verdict does not move when the second file is deleted,
which is the per-file property demonstrated rather than asserted. **I could
not construct a 112th plant that disagrees, and the structural reason above
says none exists** as long as the analysis stays file-local.

### 3 · The speedup is real, independently reproduced

Same scratch tree, same machine, both runs full-module:

| | tests | wall | load at start → end |
|---|---|---|---|
| `8829174^` (`tree_old`) | 13 | **265.996s** | 7.01 → 10.28 |
| `8829174` (`tree`) | 15 | **20.041s** | 5.99 → 7.31 |

**13.3×**, against the author's reported 263.18s → 19.98s. Both runs green.
Note this tree contains **no `.claude`**, so this ratio is the per-file
decomposition alone — the `.claude` exclusion contributes nothing here and is
measured separately below.

### 4 · The `.claude` exclusion is justified and is the larger multiplier

Read-only, against the live checkout, both gates:

| | readers | `offenders_by_symbol` | `header_sites` |
|---|---|---|---|
| pre-change `NOT_A_READER` | **339** (320 in `.claude/`) | 0 offenders, **47.60s** | **1350** sites (1275 in `.claude/`) |
| branch `NOT_A_READER` | **19** | 0 offenders, **3.50s** | **75** sites (59 `bin/`, 16 `viewer/`) |

Nothing under `.claude` is tracked (766 tracked files on the branch, zero
under `.claude`; the live `.claude/` holds `settings.local.json` and
`worktrees/`). `readers_under` finds 19 readers on the live checkout with the
new gate — identical to the 19 in the archived tree — so the exclusion removes
duplicates and nothing else. **Excluding `.claude` hides nothing a
reader-detecting guard should see.** `tests/tree_guard.py:195` already made
the same call. `.gstack/` and `.trae/` exist in the live checkout and are *not*
excluded, but contribute zero readers today, so they cost nothing.

One imprecision worth recording, not a defect: `.gitignore` names
`.claude/worktrees/`, not `.claude`, while `NOT_A_READER` excludes the whole
directory. The gap is `.claude/settings.local.json` and any future
untracked sibling — none of which this repository ships.

`test_header_index_is_the_only_fold` is **green on this branch**: 10 tests OK
in the archived tree, and its two `.claude`-sensitive quantities on the live
tree are the fixed ones above (0 offenders; 75 sites, none in `.claude`).

### 5 · Mutations that behave as claimed

All in `tree_mut`, line-anchored, `__pycache__` cleared and 2s slept on both
sides of every edit, revert verified by re-asserting the anchor line.

| id | mutation | result |
|---|---|---|
| M1 | disable branch (c), the scalar half | **8 failures** — matches the author |
| M2 | restore round 8's `is_python` (`if p.suffix: return False`) | **1 failure, `D21` red and `D20` NOT red** — matches the author and round 9's R9-6 prediction exactly |
| M3 | `offenders_at` → `return []` | **53 failures** — matches the author |
| M4 | plant a real second header rule in `viewer/parsers.py` | harness **red** (1) *and* the shipped guard `tests/test_one_header_rule.py` **red** (2) |
| MY-A | `offenders_at` returns only its **first** hit — a subtly wrong result, not an empty one | **red**, and *only* the new pin catches it: `test_a_planted_file_gets_the_same_verdict_either_way [bin/probe-d20]` and `[bin/perry-probe-d01]` |
| MY-B | `offenders_at`'s gate drifts from `is_reader` to suffix-or-shebang | **red** at `D20` in the corpus *and* at `bin/probe-d20` in the pin |
| MY-C2 | a project-wide symbol table the **walk** consults and `offenders_at` cannot (`extra={"strip"}`) | **red**: `test_the_walk_is_the_union_of_its_files` |

MY-A is the answer to "does the pin fail on a subtly wrong result or only an
empty one": it fails on a truncated list, it is the *only* thing that fails,
and the corpus does not notice — the corpus asserts a hit exists, never how
many. The pin is load-bearing and it works.

---

## Finding — the harness stopped testing that the walk reaches every directory

`_hits` is the harness's only route to the net for **105 of its 111 plants**.
It no longer walks, so **no test that goes through `_hits` can observe a
defect in `readers_under`'s enumeration.** That is not an inference; it is the
call graph: `offenders_at` calls `is_reader`, and never `readers_under`.

Round 4's actual, historical hole — *"a Python reader outside `bin/` and
`viewer/` was invisible"* — was a defect of the enumeration, and it shipped
through rounds 5, 6, 7 and 8. The corpus encodes it in two entries whose
labels are their whole subject, `D19 planted in a SUBDIRECTORY` and
`D22 OUTSIDE 'bin/' and 'viewer/'`, and in
`test_the_control_is_caught_at_every_path_the_corpus_uses`, whose docstring
states the discrimination in as many words:

> otherwise "escaped" and "the scan never looked here" are the same result

Under `offenders_at`, "the scan never looked here" is impossible by
construction. The control is still green, and it is now green for a reason
that has nothing to do with what it claims to measure.

### Measured, three ways

**MY-E** — blind `readers_under`'s *walk* only (line 182, the `rglob` loop),
leaving the shared `is_reader` gate untouched, so the enumeration loses
`packs/` and the per-file gate does not:

| harness | result |
|---|---|
| `8829174^` (`tree_old`) | **RED, 2 failures**: `test_the_control_is_caught_at_every_path_the_corpus_uses [packs/perry-probe-control]`, `test_each_drift_shape_is_caught [D22 OUTSIDE 'bin/' and 'viewer/']` |
| `8829174` (`tree_mut`) | **GREEN — Ran 15 tests, OK** |

**MY-F** — the same, blinding the walk to `bin/lib` and `viewer`. This removes
`viewer/parsers.py`, a **real reader in the live tree**, from the walk:

- branch: **GREEN — Ran 15 tests, OK.**

**Causation** — on the branch, with MY-F applied, revert *only* the one line
this row changed in `_hits`, `offenders_at(root, where)` →
`offenders_by_symbol(root)`, and change nothing else (the new pin stays in
place):

- **RED, 3 failures**: `test_the_control_is_caught_at_every_path_the_corpus_uses
  [bin/lib/perry-probe-control]`, `[viewer/perry-probe-control]`,
  `test_each_drift_shape_is_caught [D19 planted in a SUBDIRECTORY]`.

So the green is caused by `tests/test_header_rule_harness.py:1165`, and the
new pin does not recover it.

### Why nothing else catches it

Enumerating every test in the module that still touches the walk, and what
each does under a `readers_under` that has lost a directory:

| test | why it stays green |
|---|---|
| `test_an_unplanted_copy_reports_nothing` | asserts `offenders_by_symbol(copy) == []`; a narrower walk returns fewer offenders, so it goes *more* green |
| `test_the_copy_carries_the_readers` | compares `len(readers_under(copy))` with `len(readers_under(PERRY_HOME))` — both are the same blinded walk |
| `test_the_walk_is_the_union_of_its_files` | iterates the blinded `readers_under(root)` on both sides; self-consistent by construction |
| `test_a_planted_file_gets_the_same_verdict_either_way` | its sample is `bin/probe-d20`, `bin/probe-s12`, `bin/perry-probe-d01`, `bin/perry-probe-c01` — **four plants, all in `bin/`**, of the corpus's four directories `bin`, `bin/lib`, `packs`, `viewer` |
| `tests/test_one_header_rule.py` (the shipped guard) | `assertEqual(offenders_by_symbol(PERRY_HOME), [])` — a narrower walk still returns `[]`; `READERS` at line 65 is only iterated, never counted |

This is the criterion the spec named as the acceptance —

> **Mutation, and it is the acceptance**: break the header rule the harness
> guards and the harness must still go red. A faster harness that stopped
> catching the thing is the failure mode

— and it is `Out of scope`'s last bullet, *"Weakening the header-rule guard
`TASK-050` built"*. The commit message's *"nothing is dropped and no assertion
is weakened"* is true of the assertion **text** and false of what two of them
**discriminate**. `_hits`'s own new docstring keeps the sentence *"which is how
a scan that never looked at a directory reports success there"* directly above
the line that removed the scan.

### What would make it pass, and what it costs

The reclaimed time is 246s; restoring the discrimination costs about **14s** of
it, at ~2.4s per whole-tree scan measured here:

- route `test_the_control_is_caught_at_every_path_the_corpus_uses` through
  `offenders_by_symbol` rather than `_hits` — 4 scans, one per corpus
  directory; and
- assert `D19` and `D22` against the walk as well as against `offenders_at` —
  2 scans.

Equivalently: widen `TestTheSingleFileScanAgreesWithTheWalk`'s planted sample
from four `bin/` files to one plant per distinct corpus directory, which is
the same six scans and keeps the pin as the single place the equality lives.
Either leaves the module near 34s — rank ~20 of 103, nowhere near the floor —
so the row's result survives the fix.

---

## Two reporting notes (not part of the FAIL)

1. **One reported number is a diagnosis, not a constant.** The unfixed
   `header_sites` figure is a function of how many agent worktrees were on disk
   that minute. I measured **1350 sites / 48.75s**; TASK-303 measured 1350 /
   55.54s; the report says 1800 / 65.30s. The *stable* half reproduces tightly
   — **75 sites / 3.50s** here against TASK-303's 75 / 3.94s and the report's
   75 / 3.43s. The report should mark which of its numbers are
   worktree-count-dependent.
2. **A second module this row speeds up, unmentioned.**
   `tests/test_one_header_rule.py:65` binds `READERS = readers_under(PERRY_HOME)`
   at **module import**, and the module calls `offenders_by_symbol(PERRY_HOME)`
   twice more. On the live tree that walk is 339 readers / 47.60s per scan
   before and 19 / 3.50s after. It is green both ways, so it never appeared in
   any failure set — and it is absent from the before/after ranking the Bound
   asks for.

## The `git archive` question — both calls are right

`TASK-258` switched `test_tree_guard.py`'s `copy_repo` to `git archive` of
HEAD; this row **declined** the same for `_copy`. Both are correct, for
different reasons, and the reason is what the fixture has to be:

- `test_tree_guard.py`'s fixture is a **stand-in repository** to run
  `bash tests/run` inside. It wants the *committed* tree precisely so a write
  landing mid-walk cannot take it down, and it fences the three files whose
  live version decides the answer (`tests/run`, `tests/tree_guard.py`,
  `tests/parallel`) with an explicit overlay. Nothing it asserts depends on an
  untracked file existing.
- `_copy`'s fixture **is the population under measurement**. What the
  header-rule net sees is the whole question — round 4's hole was a file the
  scan could not see — and `git archive` would make every uncommitted reader
  invisible to `readers_under`, `test_the_copy_carries_the_readers` and the
  new union test. Narrowing the population of a scan whose subject is its
  population is the one substitution this file cannot make.

The specific benefit `git archive` would have bought here — excluding
`.claude/worktrees` — is bought directly by `NOT_COPIED`, at no cost to what
the copy can see. The author's reasoning is sound.

`_copy` retains `TASK-258`'s *other* exposure — `shutil.copytree` over a live
tree raises when a file vanishes mid-walk — but that is `TASK-258`'s class and
outside this row's Bound of one module, one measurement, one cut.

## The Bound's three items

1. **Ranked per-module list.** Produced, after: `python3 tests/parallel --times`
   on the branch tree, 108 modules / 3005 tests / **162.4s** / 8 workers, all
   green, load 20.89 → 38.01 (my own 8 workers plus other agents'). In the
   recorded `tests/durations.json`, `test_header_rule_harness.py` sits at
   **rank 24, 25.53s**, behind `test_migrate.py` at 97.25s. **The binding
   module no longer owns the floor** — the Bound's ending condition is met.
   Before: the module alone was 265.996s on the same tree. The full-suite
   before/after on a *quiet* machine is not established here; see
   `not-checked`.
2. **Internal profile at test granularity.** Not re-derived independently; the
   commit's attribution (three tests owning 93%, 112 scans) is consistent with
   the 112 corpus entries and with the 265.996s ÷ 112 ≈ 2.4s per scan I
   measured, but I did not re-profile per test.
3. **The change plus the mutation.** The change is sound and fast; the
   mutation half is where it fails, above.

---

## Verdict

The performance work is correct, the soundness argument is real rather than
asserted, the `.claude` exclusion is justified and is the bigger multiplier,
and the new pin is a genuine tripwire that fires on a subtly wrong result. But
the row's own acceptance criterion is a mutation, and a class of mutation that
was red before this commit is green after it: the harness no longer detects a
`readers_under` that stops reaching a directory — which is round 4's actual
defect, the one the corpus's `D19` and `D22` and the path control exist to
catch, and the one that shipped for five rounds. The fix is about 14s of the
246s reclaimed.

=== VERDICT ===
task: TASK-244
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-244-spec.md
checked: per-file soundness argument verified structurally (no module-level mutable state; _RowLocals takes only an AST; the only fs reads are single-path); OLD offenders_by_symbol == NEW offenders_at over all 19 readers under 10 tree states plus 9 constructed plants including a cross-file import, a symbol defined in one file and folded in another, and a file whose sibling was then deleted; module 265.996s (13 tests) -> 20.041s (15 tests) on one scratch tree, load 7.01->10.28 and 5.99->7.31; live-tree readers 339 (320 in .claude) -> 19, offenders_by_symbol 47.60s -> 3.50s, header_sites 1350 (1275 in .claude) -> 75, all read-only; test_header_index_is_the_only_fold 10 tests OK on the branch tree; full suite on the branch 108 modules / 3005 tests / 162.4s / 8 workers all green, load 20.89->38.01, harness at rank 24 (25.53s) behind test_migrate.py (97.25s); mutations M1 (8 failures), M2 (1 failure, D21 red and D20 not), M3 (53 failures), M4 (harness red AND tests/test_one_header_rule.py red) reproduced; MY-A offenders_at truncated to its first hit -> red only in the new pin; MY-B gate drifted from is_reader -> red in corpus and pin; MY-C2 walk-only project-wide symbol table -> red in the union test; MY-E and MY-F blinding the walk's enumeration -> RED on 8829174^ and GREEN on 8829174; causation isolated by reverting only line 1165 with everything else on the branch intact -> RED, 3 failures; all work in scratch copies at …/scratchpad/v4-244, nothing planted in the live checkout
not-checked: the full-suite 311.9s -> 106.2s headline on a QUIET machine — this machine ran at load 6.0 to 38.0 throughout and my suite figure (162.4s) is not comparable to the author's; the module's internal per-test profile was not independently re-derived; the dynamic half of test_header_index_is_the_only_fold against the live checkout with worktrees present (TASK-303 reports measuring it; I did not re-run it); symlinked paths and case-differing rel arguments as a gate divergence between root/rel and the rglob walk — not tested because creating symlinks is outside this round's permissions; non-UTF8 and Windows paths; the concurrency exposure _copy retains from shutil.copytree over a live tree (TASK-258's class, outside this Bound); tests/parallel itself and the other 32 tree-walking modules (TASK-303); whether the 105 corpus verdicts are individually correct — I checked that they are unchanged, not that they are right
proof: tests/test_header_rule_harness.py:1165 — `return [o for o in offenders_at(root, where) if o.startswith(where + ":")]`. With `readers_under`'s rglob loop (tests/header_rule.py:182) blinded to a directory while the shared `is_reader` gate is left intact, 8829174^ goes red at `test_the_control_is_caught_at_every_path_the_corpus_uses` and at `D22 OUTSIDE 'bin/' and 'viewer/'`, and 8829174 stays green (15 tests, OK). Reverting only line 1165 to `offenders_by_symbol(root)`, with the rest of the branch including the new pin unchanged, turns it red again: 3 failures at `[bin/lib/perry-probe-control]`, `[viewer/perry-probe-control]` and `D19 planted in a SUBDIRECTORY`.
=== END VERDICT ===
