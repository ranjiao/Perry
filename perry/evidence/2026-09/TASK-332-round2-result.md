# TASK-332 round 2 — the guard never located `summary_shape`

Branch `coding/task-332-round2-ast-locator`, cut from `main` explicitly at
`7db530b` because the worktree's HEAD (`d49964e`) was not `main` and the V4
review exists only on `main`. `BASE=$(git merge-base HEAD main)` =
`7db530b22b959596614c4fea5c22b9cabee76fa0`; **every restore in this document is
verified against that base, single path only, never against `main`.**

Under review: the V4 FAIL in
`perry/evidence/2026-09/TASK-331-332-v4-review.md` — TASK-332 criterion 5. I
did not write the row; the PMO did, in the main session, because HTTP 529 was
killing subagents.

---

## Baseline, measured on this branch

```
$ bash tests/run
114 modules · 3251 tests · 125.4s · 8 workers
✓ all green
0. tree guard — ✓ nothing under <worktree> moved

$ bin/perry-lint --root .
  0 error(s), 37 warning(s)
  · summaries: 103 of 115 open row(s) carry one · 12 blank · 0 shape finding(s)
```

**Zero attributable failures.** None of the four known unrelated reds —
`test_contract_key_parity` (TASK-335), `test_one_primitive` /
`test_one_choke_point` (TASK-341), `test_host_support` (TASK-313) — fired in
the baseline run, so nothing needed re-running alone before attribution.

**Mutation discipline.** Every mutation goes through a harness taking `path`,
`lineno` and a string that MUST be present on that line; it aborts with
`ANCHOR FAILED` and touches nothing otherwise. It aborted once during this
round, on a wrong guess at `bin/lib/__init__.py:1170`, which is the anchor
doing its job. `__pycache__` is cleared and the run waits past the whole-second
boundary before each verdict. After each restore, `git diff --stat <BASE>` is
shown.

---

## The defect

`tests/test_summary_is_asked_for.py:322` did:

```python
src = (ROOT / "bin" / "lib" / "__init__.py").read_text(encoding="utf-8")
head, sep, rest = src.partition("NOT CHECKED")
register = rest.split('"""')[0]
```

`src` is the **whole 2,100-line module**. The test never located
`summary_shape`. It pinned the first occurrence of the English phrase `NOT
CHECKED` anywhere in the file, and today there happens to be exactly one:

```
$ grep -n "NOT CHECKED" bin/lib/__init__.py
1129:    NOT CHECKED, deliberately, each for a measured reason:
```

That coincidence was the only thing holding the guard up.

---

## Both probes reproduced BEFORE any change

### Probe C — false negative. Register deleted in full, test GREEN.

Deleted `bin/lib/__init__.py:1129–1163` — `summary_shape`'s entire register,
all seven bullets, every word TASK-330 and TASK-332 were required to write —
and gave `summary_fold`, one function earlier, a decoy carrying the four owed
tokens:

```python
def summary_fold(s: str) -> str:
    """Case- and punctuation-insensitive key for comparing summary to title.

    NOT CHECKED here, in a totally unrelated function: summary-has-no-sentence,
    summary-is-a-fragment, 2026-09-03, TASK-330.
    """
```

```
$ grep -n "NOT CHECKED" bin/lib/__init__.py
1098:    NOT CHECKED here, in a totally unrelated function: …
                          ← summary_shape's register: GONE

$ python3 -m unittest …test_a_removed_rule_stays_named_in_the_not_checked_register
Ran 1 test in 0.002s
OK
```

**GREEN — reproduced exactly.** This is TASK-330's mutation M5 again,
generalised, surviving the fix written to close it.

### Probe D — false positive. Register intact, test RED.

Left `summary_shape`'s register completely untouched (`grep -c
summary-has-no-sentence` = 1, unchanged) and gave `summary_fold` an ordinary
register of its own — the exact reuse of the pattern TASK-330 and TASK-332 are
jointly advertising:

```python
    NOT CHECKED, deliberately: whether the fold is reversible. It is not, and
    nothing depends on it being so.
```

```
AssertionError: 'summary-has-no-sentence' not found in ', deliberately: whether
the fold is reversible. It is not, and\n    nothing depends on it being so.\n
' : the NOT CHECKED register no longer names 'summary-has-no-sentence'. …
FAILED (failures=1)
```

**RED — reproduced exactly**, blaming a register that is perfectly intact and
sending the next author to the wrong place.

Both restored single-path; `git diff --stat <BASE>` named only the evidence
file at that point.

---

## The fix

The correct locator was already in the same file, thirty lines up, written by
the same author an hour earlier for TASK-331. It is now used here too:

```python
src = (ROOT / "bin" / "lib" / "__init__.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "summary_shape")
head, sep, register = (ast.get_docstring(fn) or "").partition("NOT CHECKED")
```

Two properties worth naming. `ast.get_docstring(fn)` bounds the search to *this
function's* docstring by construction, so no edit anywhere else in the module
can move the target. And `register` now runs to the **end of the docstring**
rather than to the next `"""`, so a second `NOT CHECKED` heading inside the
same docstring is still covered rather than truncating the register.

### After the fix

| probe | before | after |
|---|---|---|
| C — register deleted behind a decoy | **GREEN** (the finding) | **RED** |
| D — register intact, innocent neighbour | **RED** (false alarm) | **GREEN** |

Probe C was re-run with the decoy **padded past 600 characters**, so the
emptiness floor below could not be what turned it red. It fails on the locator:

```
AssertionError: '' is not true : summary_shape no longer has a NOT CHECKED
register — that register IS the deliverable of TASK-330 and TASK-332
```

---

## `SUMMARY_RULES_REMOVED` — **taken**, and for a reason the review did not name

The reviewer argued the `(rule, date, row)` tuple is data pretending to be
prose. I agree, but the decisive argument is one step further on, and it is
about a defect that exists today rather than an improvement in tidiness.

**The old test hardcoded the record itself:**

```python
for owed in ("summary-has-no-sentence", "summary-is-a-fragment",
             "2026-09-03", "TASK-330"):
```

That is a **third copy** of the record — contract, docstring, and now a tuple
inside a test file — and it is the invisible one. The next author to remove a
rule writes the docstring entry, never thinks about this test, and the guard
stays green over a removal it is not pinning. That is TASK-330's M5 again, one
removal later, and the round-1 fix would not have touched it. Driving the loop
from a module-level constant is what closes it: adding a row to
`SUMMARY_RULES_REMOVED` is what arms the guard, and mutation **M6 below proves
the new behaviour** — a removal recorded in the constant and never explained in
the register is now red, where before the constant existed no such check
could fire at all.

The DESIGN-013 "two copies" objection does not apply, and the distinction
matters: DESIGN-013 is about copies that **drift silently**. These two cannot.
The test asserts every field of every constant entry appears in the register,
so the constant and the prose fall together or not at all.

**The prose reason stays in the docstring, as the review required**, and I did
not weaken that. Its value is being on the same screen as `summary_shape` when
someone opens it wondering why there is no sentence check; a sidecar would
separate the reason from the code it explains. To hold that line against the
obvious abuse — satisfy the constant-driven asserts with a bare token line and
delete the explanation — the test carries an **emptiness floor**:

```python
self.assertGreater(len(register), 600, …)
```

The register is 2,295 characters today; a bare four-token line is 85. This is a
floor, not a content pin: it says the register is still prose, never what the
prose says. It deliberately **cannot** catch one bullet being gutted while six
others stand, because judging that would mean asking Python whether English
reads like an explanation — the question this module refuses. M5 below proves
the floor is live.

I did **not** take the reviewer's further suggestion that TASK-331's guard
assert the live and removed sets stay disjoint. It is a good idea and a real
property, but it is a different property in a different test, and widening past
this row's deliverable is what TASK-330's `## Bound` and the TASK-331 scope
finding both argue against. Noted for whoever files it.

---

## Mutation ledger

Every mutation anchored by line number **and** by a string asserted present on
that line; `__pycache__` cleared and the whole-second boundary passed before
each verdict; each restored single-path and checked against `BASE`.

| | mutation | expected | observed |
|---|---|---|---|
| **C** | register deleted in full, padded decoy in `summary_fold` | red | **RED** |
| **D** | register intact, innocent second register in `summary_fold` | green | **GREEN** |
| **C1** | Changelog names the removed rules again | green | **GREEN** |
| **C2** | docstring-only edit inside `summary_shape`, register untouched | green | **GREEN** |
| **C3** | bare-id `NOT CHECKED` entry reworded end to end | green | **GREEN** |
| **M3** | TASK-330's M5 — strip both names, the date, the row id | red | **RED** |
| **M4** | rename the register heading to `DELIBERATELY NOT MEASURED` | red | **RED** |
| **M5** | keep all four tokens, delete the reason entirely | red | **RED** |
| **M6** | a third rule recorded in the constant, never explained | red | **RED** |
| **M7** | `SUMMARY_RULES_REMOVED` emptied | red | **RED** |

**Ten planted, five red, five green — and every green is an intended control.
No mutation survived that should have died.**

Notes on the three controls that had to stay green:

- **C1** — a fresh Changelog paragraph naming `summary-has-no-sentence`,
  `summary-is-a-fragment` and an invented `summary-under-five-words`. Green:
  the Changelog's job is to record what left, and a guard red here would make
  a removal impossible to write down.
- **C2** — a paragraph inside `summary_shape`'s docstring, above the register
  and touching no part of it, naming all three rule names in plain prose.
  Green: the guard reads the register, not the whole docstring.
- **C3** — the bare-id bullet rewritten end to end, with `TASK-218` and
  `DESIGN-012 I1` both dropped (`grep -c TASK-218` → 0). Green: **the guard
  does not freeze the docstring.** This is also the control that proves the
  assertion is not the `USER-916` mistake — a full rewrite of a neighbouring
  entry moved nothing, because the test counts identifiers rather than judging
  prose.

M5 is worth one more line. All four owed tokens were present and every
`assertIn` passed; the floor is what turned it red:

```
AssertionError: 116 not greater than 600 : the NOT CHECKED register has shrunk
to roughly its identifiers — the reason each rule left is the half a constant
cannot hold, and it is why the register is in the docstring at all (TASK-332)
```

---

## What this was, one level up

The reviewer's framing is right and worth restating in the test itself, which
is where I put it. `assertIn("summary-has-no-sentence", register)` attempts no
judgement about meaning: it asks whether an identifier with exactly one
spelling is still written down, which is a fact about bytes, and C3 proves the
distinction is real. The `USER-916` rule was broken not by **what** the test
asserts but by **how it locates what to assert on**. `str.partition` over a
human-authored heading is Python judging document structure, and Probes C and D
are that judgement losing in both directions — the same way five rounds of a
scanner on this project lost to a full stop and to a markdown italic.

"The docstring of the function named `summary_shape`" is deterministic and
`ast` gives it for free. "Whatever follows the first `NOT CHECKED` in the file"
is not.

---

## Closing state

```
$ bash tests/run
114 modules · 3251 tests · 114.7s · 8 workers
✓ all green
0. tree guard — ✓ nothing under <worktree> moved

$ bin/perry-lint --root .
  0 error(s), 37 warning(s)

$ git status --porcelain
(empty)

$ git diff --stat 7db530b22b959596614c4fea5c22b9cabee76fa0
 bin/lib/__init__.py                              | 26 +++++++++
 perry/evidence/2026-09/TASK-332-round2-result.md | …
 tests/test_summary_is_asked_for.py               | 72 +++++++++++++++++++-----
```

Identical to the baseline: 3251 tests, all green, 0 lint errors.

No state file was written: `perry/tasks.jsonl`, `perry/BOARD.md`,
`perry/journal/`, `.perry/events.jsonl`, `schema/state-schema.json` and
`claims` are untouched. This branch was never pushed and no PR was opened;
`main` was never switched to, merged into or modified.
