# Four docstrings cite a directory on this machine as their evidence

> Found 2026-08-28 across three rows in one night — TASK-124, TASK-125 and a
> re-read of `bin/perry-conform`. **Each row filed its own; they are one
> defect.** Consolidated here rather than left as four intake lines in a
> register already at 41.

## The shape

A docstring or a README states a claim, and cites as its evidence **a directory
that exists on the author's machine**. The claim is usually true. What is wrong
is that **nothing a fresh checkout can run will confirm it**, so the next person
either takes it on faith or concludes it was never true.

It is the documentation half of the defect this project has spent the most
nights on — *a check that reads the project living around it as its expected
value*. Here the reader is a human, and the "check" is a sentence.

## The four instances

| where | claim | why the citation is dead |
|---|---|---|
| `bin/README.md:234` and `bin/perry-conform:273-274` | TASK-047 cost 1: *"`BOARD.md` goes 3 errors → 1"* | measured on `~/proj/gimegime-pmo`. **TASK-124 removed that read**; the suite now measures the same property on a constructed board. The prose stays true; its citation runs nowhere. |
| `bin/perry-conform:283` | both TASK-047 costs are *"pinned as executable tests in `tests/test_conformance.py § 7`"* | **cost 1 is pinned in § 6**, not § 7. Wrong before either row touched it — an internal citation that was never checked. |
| `bin/perry-goals:459` (`insert_section`) | the fallback order is justified by *"the four real `OKR.md` files on this machine"* | two of those four are `~/proj/gimegime-pmo` and `~/proj/aimark`. **After TASK-125 the shape it argues for is pinned by a committed fixture** — the argument is now checkable and the docstring does not say so. |
| `bin/perry-goals:334` (`Okr` class) | same justification, same four files | same. |

## Why one row rather than four

All four want the same edit: **replace "the N real files on this machine" with
the name of the test that now checks it.** Three of the four are only fixable
*because* TASK-124 and TASK-125 built those tests tonight — the citation could
not have pointed at a test before the test existed.

The fourth (`perry-conform:283`) is different and easier: it already points at a
test, at the wrong section number.

## What a fix must not do

**Do not delete the reasoning.** *"One nests `### Anti-Goals` inside a version,
one carries a section Perry's template has never heard of, one has `v2` and `v4`
with no `v3`"* is why the fallback exists, and it is good. What changes is where
the reader is sent to verify it.

## The general form, which is the part worth keeping

**A citation is a promise that someone can check the claim.** A citation to a
path outside the repository is a promise only the author can keep, and it
expires silently — nobody gets a failing test when it stops being true. This is
exactly what happened to `bin/README.md:234` tonight: TASK-124 removed the
measurement and **nothing anywhere went red**, because prose has no test.

`perry-lint` cannot catch this and should not try. The cheap version is a
convention: **when a docstring cites evidence, cite a test.**
