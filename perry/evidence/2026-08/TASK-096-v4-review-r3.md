# TASK-096 — V4 review, round 3: full mutation inventory and bounded PASS

**Canonical criteria**: `perry/evidence/2026-08/TASK-096-spec.md`.

**Under review**: `tests/test_procedures_call_the_tool.py`, plus the live lane
procedure corpus that module discovers. The implementation scope remained the
single test module. This document records two review passes over the same
round: an initial FAIL, followed by a bounded re-review after two focused tests
were added.

All destructive trials ran in disposable copies under `/tmp`. Each mutation
copy excluded `.git` and `__pycache__`, removed any newly created bytecode
caches before execution, set `PYTHONDONTWRITEBYTECODE=1`, slept 1.05 seconds
across filesystem timestamp boundaries, and ran the module in a fresh Python
process. No mutation was applied to the live implementation.

---

## 1. Initial review result — FAIL on two acceptance gaps

The stock focused suite was green:

```text
python3 tests/parallel test_procedures_call_the_tool
  1 module · 17 tests · 0.3s · all green

python3 -m unittest tests.test_procedures_call_the_tool
  Ran 17 tests in 0.292s · OK
```

The complete historical inventory from round 2 was also held: all 25 concrete
mutations representing G1–G21 were red (§2). That was not sufficient for PASS,
because two requirements stated directly by the canonical spec still had no
mutation-sensitive fixture.

### FAIL 1 — the bullet branch could be deleted

The scanner declared numbered and bulleted items as procedure units:

```python
re.match(r"^\s*(?:\d+\.|[-*])\s", line)
```

But `test_paragraph_steps_lists_and_leading_prose_are_all_scanned` used only
numbered items. On a disposable copy this mutation stayed green:

```text
(?:\d+\.|[-*])  →  (?:\d+\.)
Ran 17 tests · OK
```

The implementation still worked for bullets, but the behavior could be
removed without a test failing. This violated Deliverable 4's explicit
"numbered and bulleted step segmentation" requirement and Verification 1's
stock-green / mutation-red rule.

### FAIL 2 — suppression line and stacked-heading scope could be disabled

`scan()` peels every contiguous heading and advances the source line once per
heading. The existing suppression tests placed blank lines between headings
and procedure prose, so neither half of that behavior was load-bearing. Both
mutations stayed green:

```text
bstart += 1  →  bstart += 0
Ran 17 tests · OK

while lines and lines[0].lstrip().startswith("#"):
  → if lines and lines[0].lstrip().startswith("#"):
Ran 17 tests · OK
```

The missing behavioral fixture was the contiguous shape the scanner's own
comment says it supports:

```markdown
# page
## Import existing decisions
1. Edit the target ADR: flip its `Status:` header.
```

For this input, the first mutation reports the wrong source line. The second
leaves the adoption heading unpeeled, loses the owning section, and reports an
R1 finding instead of the observable adoption suppression. This violated
Deliverable 3 and Verification 3's requirement to prove the reported page,
line or section, exemption identity, target, and step through `scan()` itself.

---

## 2. Historical G1–G21 inventory — 25 red, 0 green

The review re-ran every semantic mutation named by the round-2 inventory. G19,
G20, and G21 each had multiple concrete variants, so 21 categories produced
25 trials.

| ID | Exact weakening or widening | Result and focused control |
|---|---|---|
| G1 | `section = lines[0]` → `section = section + lines[0]` | RED — adoption scope and observed suppression tests |
| G2 | `from_target_template(...)` → unconditional `True` | RED — target-template and target-positive tests |
| G3 | owner subcommand `` `[a-z]+-[a-z-]+` `` → `` `[a-z]+[a-z-]*` `` | RED — `test_owner_boundary_and_both_proximity_directions` |
| G4 | `BEFORE, AFTER = 60, 90` → `60, 0` | RED — both-direction proximity control |
| G5 | disable the `BOARD.md row` pattern | RED — declared-target positive/negative fixture |
| G6 | disable the `OKR.md § Commitments` pattern | RED — declared-target positive/negative fixture |
| G7 | paragraph/no-marks branch returns `[]` | RED — paragraph coverage fixture |
| G8 | force `marks = []`, disabling step segmentation | RED — observed adoption/template controls |
| G9 | `if marks[0]` → `if False` | RED — prose-before-first-list fixture |
| G10 | R2 uses `spec["pattern"]` instead of `cell` | RED — `test_r2_cell_and_multiple_targets_are_independent` |
| G11 | R2 target-loop `continue` → `break` | RED — same multi-target fixture |
| G12 | remove bounded `import` adoption vocabulary | RED — adoption scope/vocabulary fixtures |
| G13 | remove `adopt` | RED — adoption vocabulary fixture |
| G14 | remove `legacy` | RED — adoption vocabulary fixture |
| G15 | remove `pre-existing` | RED — adoption vocabulary fixture |
| G16 | remove `no` from `PROHIBITION` | RED — prohibition observability fixture |
| G17 | remove `it` from `DESCRIPTIVE` | RED — descriptive observability fixture |
| G18 | remove descriptive adverbs (`already`, `also`, etc.) | RED — descriptive observability fixture |
| G19a | remove append forms from `WRITE` | RED — journal target positive fixture |
| G19b | remove flip forms from `WRITE` | RED — ADR-header target positive fixture |
| G19c | remove update/edit/insert forms from `WRITE` | RED — DECISIONS/Commitments and proximity fixtures |
| G20a | reduce `READ` to `reads?` | RED — read-anchor fixture and live corpus control |
| G20b | remove the trailing `READ` anchor | RED — proximity fixture |
| G21a | lane shape requires only `SKILL.md` | RED — synthetic lane-shape fixture |
| G21b | lane shape requires only `reference/` | RED — synthetic lane-shape fixture |

Harness summary:

```text
SUMMARY 25 RED 0 GREEN 0 SETUP_ERROR
```

This establishes that the two initial FAILs were additional acceptance gaps,
not regressions in the already enumerated G1–G21 categories.

---

## 3. Bounded fixes

The implementation added only two tests to
`tests/test_procedures_call_the_tool.py`; scanner behavior was unchanged.

1. `test_bulleted_steps_keep_exemptions_inside_their_item` uses both Markdown
   bullet markers in adjacent items: `- Do not edit BOARD.md`, followed by
   `* Add a row to BOARD.md by hand`. It proves that a prohibition in one
   bullet cannot suppress the next bullet.
2. `test_stacked_headings_preserve_suppression_location_and_scope` writes the
   contiguous three-line fixture from §1 and asserts the complete
   `Suppression`: page, line 3, final section heading, exemption identity,
   target, and exact step.

The fixes are bounded to the two failed criteria. They do not widen the corpus,
add target families, change exemption semantics, or absorb TASK-101 work.

---

## 4. Bounded re-review — PASS

The stock module is green after the two tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_procedures_call_the_tool
  Ran 19 tests in 0.322s · OK

python3 tests/parallel test_procedures_call_the_tool
  1 module · 19 tests · 0.4s · all green
```

The exact three previously green mutations are now red:

| Mutation | Result |
|---|---|
| bullet regex `(?:\d+\.|[-*])` → `(?:\d+\.)` | RED — `test_bulleted_steps_keep_exemptions_inside_their_item` |
| `bstart += 1` → `bstart += 0` | RED — `test_stacked_headings_preserve_suppression_location_and_scope` |
| contiguous heading peel `while` → `if` | RED — `test_stacked_headings_preserve_suppression_location_and_scope` |

Each mutation had exactly one replacement site. There were no setup errors.

### Live corpus and TASK-101 boundary

The final live measurement was independent of the zero-count test:

```text
lanes ['decide', 'goals', 'work']
pages 26
findings 0
incidents_in_scope False
state_pages_in_scope False
```

The corpus therefore remains exactly the lane-shaped procedure trees:
`SKILL.md` plus recursive `reference/**/*.md`. Lane `state/` pages remain out
of scope. `packs/software-ops/incidents.md` remains out of scope and its known
hand-edit instruction remains owned by TASK-101. The module does not claim a
project-wide zero.

---

## 5. Criteria map

| Canonical acceptance item | Initial review | Final result | Evidence |
|---|---|---|---|
| Deliverable 1 — invariant and observable narrow suppressions | PASS | PASS | stock focused suite and live zero |
| Deliverable 2 — lane-shaped discovery, recursive references, no state pages | PASS | PASS | G21 variants red; synthetic fourth lane; final corpus measurement |
| Deliverable 3 — suppression page/location/section/identity/target/step | FAIL | PASS | new full-record stacked-heading fixture; both metadata mutations red |
| Deliverable 4 — bounded exemption fixtures including numbered and bulleted segmentation | FAIL | PASS | new mixed-bullet fixture; bullet-removal mutation red |
| Deliverable 5 — every TARGET positive/negative, `cell`, multi-target continuation | PASS | PASS | G5, G6, G10, G11 red |
| Deliverable 6 — G1–G21 semantic categories | PASS | PASS | 25 red / 0 green |
| Deliverable 7 — live in-scope corpus zero | PASS | PASS | 26 pages / 0 findings |
| Deliverable 8 — TASK-101 owns whole-tree expansion | PASS | PASS | packs and lane state excluded; module wording remains bounded |
| Verification 1–3 — mutation-sensitive behavioral proof | FAIL | PASS | three former-green mutations now red |
| Verification 4 — focused suite, broader suite, lint, diff check | PASS with unrelated broader failures separated | PASS for bounded re-review | exact results below |
| Verification 5 — disposable copies, cache and timestamp hygiene | PASS | PASS | `/tmp` copies, cache deletion, 1.05s waits, fresh processes |
| Verification 6 — no unresolved in-scope violation | FAIL | PASS | both failed criteria closed; live corpus remains zero |

**Final V4 result: PASS.** The implementing session did not award this rung;
the initial FAIL and bounded PASS were both performed in a fresh review
context against the canonical spec.

---

## 6. Exact commands and results

Initial stock and repository checks:

```text
find . -type d -name __pycache__ -prune -exec rm -rf {} +
python3 tests/parallel test_procedures_call_the_tool
  → 17 tests, all green

python3 -m unittest tests.test_procedures_call_the_tool
  → 17 tests, OK

python3 bin/perry-lint
  → 0 errors, 2 store-drift warnings for TASK-090 and TASK-104

git diff --check
  → clean

bash tests/run
  → 56 modules, 1632 tests, 4 modules red
```

The four broader-suite failures were separated from TASK-096:

| Module | Failure | Relation to TASK-096 |
|---|---|---|
| `test_board_render.py` | live Board renderer used verbatim `Depends on` cells | unrelated task-store/projection work |
| `test_host_support.py` | concurrent mixed dispatch registered 4 successes, expected 3 | unrelated dispatch-limit concurrency behavior |
| `test_router_budget.py` | root `SKILL.md` 556 bytes over its cap | unrelated file, outside TASK-096 diff |
| `test_store_is_canonical.py` | expected zero drift, saw TASK-090/TASK-104 drift | unrelated live Board/store state |

Initial mutation commands were generated by a disposable-copy harness and ran:

```text
python3 -m unittest tests.test_procedures_call_the_tool
  → once per mutation, 25 historical trials
  → 25 RED / 0 GREEN / 0 SETUP_ERROR

bullet-numbered-only mutation
  → 17 tests, OK (initial FAIL)

suppression-line-not-advanced mutation
  → 17 tests, OK (initial FAIL)

only-one-stacked-heading mutation
  → 17 tests, OK (initial FAIL)
```

Bounded re-review:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_procedures_call_the_tool
  → 19 tests, OK

python3 tests/parallel test_procedures_call_the_tool
  → 19 tests, all green

bullet-numbered-only mutation
  → RED, bullet fixture failed

suppression-line-not-advanced mutation
  → RED, stacked-heading fixture failed

only-one-stacked-heading mutation
  → RED, stacked-heading fixture failed

PYTHONPATH=tests python3 <live-corpus measurement>
  → three lanes, 26 pages, 0 findings
  → incidents_in_scope=False, state_pages_in_scope=False

git diff --check
  → clean
```

---

## 7. Not checked and residual risks

- The full 25-mutation G1–G21 matrix was not re-run after the bounded fixes.
  It was fully red immediately before them, the fixes added tests only, and the
  final 19-test stock run was green. The re-review deliberately re-ran only the
  three mutations that had caused the initial FAIL.
- `bash tests/run` was not re-run after the bounded fixes. Its initial four
  failures were outside `tests/test_procedures_call_the_tool.py` and were
  recorded rather than omitted.
- Root `SKILL.md`, root `reference/`, `packs/`, `modes/`, `templates/`, lane
  `state/`, and `packs/software-ops/incidents.md` were not scanned as procedure
  corpus. This is the agreed TASK-096 boundary, not an assertion that those
  trees are clean. TASK-101 owns expansion and the known incidents violation.
- Target families outside the current closed `TARGETS` table were not added or
  evaluated. TASK-101 separately records known deterministic writers omitted
  from that table.
- No deterministic writer was executed, and no task state, Board projection,
  journal, or decision record was mutated by the review.
- Windows path behavior, non-English `Document language`, and procedure prose
  outside the declared English target vocabulary were not tested.
- The worktree contained concurrent TASK-091/task-store changes. They were not
  reverted, staged, reformatted, or attributed to TASK-096.

During the initial review, an untracked mutation helper was briefly created at
the repository root because `apply_patch` used the repository working
directory. It was immediately deleted with `apply_patch` before the verdict.
No helper remained, and no tracked code or Perry state was changed by that
review action.

```text
=== VERDICT ===
task: TASK-096
rung: V4
result: PASS
criteria: perry/evidence/2026-08/TASK-096-spec.md
checked: initial stock 17/17; complete historical G1-G21 inventory as 25/25
         red; two additional acceptance gaps demonstrated by three green
         mutations; bounded fixes reviewed; final stock 19/19; all three
         former-green mutations red; live lane corpus 26 pages / 0 findings;
         TASK-101 boundary unchanged; lint and broader-suite failures separated;
         git diff --check clean.
not-checked: full 25-mutation rerun and full tests/run after the bounded tests;
             whole-tree/TASK-101 corpus; new target families; writer behavior;
             Windows and non-English procedure vocabulary.
proof: test_bulleted_steps_keep_exemptions_inside_their_item makes removing
       `[-*]` red. test_stacked_headings_preserve_suppression_location_and_scope
       makes both source-line advancement and repeated heading peeling red,
       while asserting the complete observable Suppression record.
=== END VERDICT ===
```
