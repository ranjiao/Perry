# TASK-125 — the gap was the middle branch, and half the test was duplicating itself

**From `coding/task-125` @ `67b492b`.** Rung **V3**. **One file changed** —
`tests/test_goals_writer.py`, +172/−59. `bin/`, `perry/` and `tests/fixtures/`
byte-untouched, verified.

## The structure my spec did not name

`bin/perry-goals § insert_section` (453) takes an **ordered** fallback list and
`Okr.section` matches at **level 2 only**:

```python
for pattern in before:
    if self.has_section(pattern):
        at = self.section(pattern)[0]; break
if at is None:
    at = len(self.lines)
```

So there are **three** branches — `Anti-Goals`, then `v<n>:`, then
`Versioning`/end-of-file — and `TestCreatingTheSection` already pinned the
**first** and the **last**.

**The gap is exactly the middle one**: when the only `Anti-Goals` is a `###`
nested inside `## v2`, the level-2 scan skips it and the version heading wins.
My spec said "the insert case"; the truth is one specific branch of three, and
saying which is what made the test buildable.

## The two `ELSEWHERE` tests were not the same test twice

I told the agent to establish that rather than assume, and the answer is worth
the check:

- **`test_both_refuse_and_change_nothing`** builds the copy with `tracks=None`,
  so there is *no* `.perry/config.md` at all. **Nothing about the real file's
  content matters** — any `OKR.md` lacking `## Commitments` gives the same
  answer, and its `assertEqual(source.read_text(), before)` is a self-check on
  the harness, not on the writer.
- **`test_a_declared_queue_track_makes_the_section_land_cleanly`** is the actual
  insert.

## Half of it was duplicating in-repo coverage on one machine

Both `ELSEWHERE` files exist here, and I confirmed the split myself:

```
~/proj/gimegime-pmo/OKR.md    level-2 Anti-Goals 0 · nested ### 3   → version branch
~/proj/aimark/perry/OKR.md    level-2 Anti-Goals 1 · nested ### 0   → branch 1
```

**`aimark`'s file takes branch 1, which the in-repo corpus already covers.** So
one of the two real projects was buying nothing that a committed fixture was not
already proving — on the only machine that has it.

## What it built, and the fixture decision

Two tests in `TestCreatingTheSection`, beside the two branch tests they complete.
The input is **constructed, not captured**: `tests/fixtures/second-project/
OKR.md` **minus its `## Commitments` block** — the one edit that puts the writer
on the create branch.

The assertion is a property: no `## v<n>:` and no `## Versioning` may precede the
new section, the version block holding the nested heading is byte-identical, no
existing line rewritten, the seam is still a blank line.

**It extended the existing fixture at 0 bytes changed**, and the reason is the
better half of the answer:

> a second committed copy of the shape could drift out of step with the copy the
> round trip reads

So the insert is tested against **the same bytes** the round trip proves. Two
test-local helpers deliberately **re-implement `Okr.section` the dumb way**, so a
mutation of the scanner is *caught* rather than followed — a checker that reuses
the code under test cannot see that code change.

Plus the anti-vacuity guard in the same change:
`test_the_fixture_still_carries_the_nested_anti_goals_shape`.

## `ELSEWHERE` survives, narrowed — and the argument is the interesting part

`TestTheRealFilesOnThisMachine` deleted; `ELSEWHERE` and the round-trip test
kept. The distinction it drew:

> byte identity over prose nobody generated is **breadth no fixture can fake**,
> and a round trip cannot become load-bearing. A **structural placement**
> assertion is the opposite — its only input is the heading skeleton, which a
> fixture captures exactly — so running it live bought no breadth and cost a
> skip-counting idiom that was dead everywhere but one machine, and **would have
> gone quiet if a directory were renamed.**

That is a sharper rule than "delete the outside-the-repo read", and it disagrees
in the right direction with TASK-124, which deleted its equivalent. **The two
rows reached opposite conclusions about superficially identical mechanisms**,
each with a reason tied to what the test actually asserts. That is the outcome I
wanted from telling both to argue it either way.

`test_the_corpus_is_entirely_inside_the_repository` and
`test_the_corpus_actually_disagrees` untouched, verified by diff; `ELSEWHERE`
stays out of the latter.

## Mutation proof: 8 mutations, 16 invocations, 10 red, 0 survived

Six in `bin/perry-goals` — reorder the fallback list, scanner forgets the heading
level, insert at the section's end not its start, drop the version fallback,
ignore `before` entirely, drop the blank line — each killed by the insert test.
**Two in the fixture** — promote the nested heading to level 2, delete the
register — each killed by the guard, **which is what proves the guard is not
decorative.** All reverted byte-for-byte.

## Runs

- **`$HOME` = empty directory**: `TestCreatingTheSection` — **6 tests, OK, 0
  skips**; the insert runs. Whole module: 114 tests, OK, 1 skip (the `ELSEWHERE`
  round trip, naming both absent paths).
- Suite, normal `$HOME` and empty `$HOME`: **86 modules · 2574 tests · 1 red** —
  `test_diagnose`, the standing one.

## Finding reported, not fixed

`bin/perry-goals:459` and the `Okr` class docstring at `:334` both justify the
fallback order by *"the four real `OKR.md` files on this machine"*. **For two of
those four that justification runs nowhere on a fresh checkout**, and after this
row the shape it argues for is pinned by a committed fixture instead.

**This is the third instance tonight of one defect**: a citation pointing at a
directory rather than at the test that checks it. TASK-124 filed two
(`bin/perry-conform:273-274`, `bin/README.md:234`); this is the third and fourth.
They should be one row, not four intake lines.

No writer change was needed — `--root` (TASK-132) was already sufficient seam.
