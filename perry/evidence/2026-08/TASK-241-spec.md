# TASK-241 — a decorated path in `.perry/conformance.md` becomes a real declaration

> Found by the `TASK-226` V4 reviewer, 2026-08-30. Filed 2026-08-30.
> The file this concerns **gates every write under ADR-004's enforce gate.**

## Measured

`viewer/parsers.py § read_conformance` strips each cell with ``strip("` ")``. So
a row whose **path cell is in backticks** — or indented, or inside a fenced block
— parses to the **same plain key** as an undecorated row.

The reviewer ran seven traps where `TASK-226` had run five. **Three are not
inert.** Measured on a copy:

1. A decorated row flips a real file from `undeclared` to **`conformant`**.
2. The next legitimate `perry-conform declare` rewrites the whole file from the
   parsed declarations — `bin/perry-conform:423 render` — and therefore
   **launders the decorated row into a plain canonical row**, indistinguishable
   from one a person wrote on purpose.

Only the **asterisk** case is inert. `TASK-226`'s RESULT files the whole class as
*"inert … never affects a verdict"*, which is true of asterisks and false of the
class. That RESULT has been corrected; this row is the defect it was wrong about.

**It did not cause `TASK-226`'s phantom row.** That elimination rests on the
render fixed-point check — `render(parse(f)) == f` on both actual files, 0
unreadable — which the reviewer reproduced independently and calls a **complete
detector for the whole class**. The conclusion there is safe; the argument
offered for it was not.

## Deliverable

**A decorated row cannot silently become a declaration.** Either:

- the reader **refuses a row it cannot round-trip** — `render(parse(row)) == row`; or
- decoration is stripped **only where a documented rule says it may be**, and
  every other shape is **reported as unreadable** rather than parsed.

`ConformanceRecord` already distinguishes `unreadable` from `absent` and from
`declared`. **That distinction is where this belongs** — the reader is already
built to say "I could not read this row" and currently does not use it here.

## Verification — V4

1. Plant each of the three live traps — **backticked path, indented row, fenced
   row** — on a copy and show each is **refused or reported**, not parsed as a
   declaration.
2. Plant one, then run a legitimate `perry-conform declare`, and show the
   decorated row is **not laundered** into a canonical one.
3. **Mutation**: revert the guard and show a **NAMED test goes red for each of
   the three shapes** — not one test covering all three.
4. Confirm the **asterisk** case still behaves as it does today. A bolded
   `| **File** |` header row was once read as a declaration and `squash` already
   answers that; do not regress it.
5. Baselines name **both the runner and the tree** — see `TASK-233-spec.md § 4`
   for the current numbers.

## Out of scope

**Converting the file to `.perry/conformance.jsonl`.** That is `TASK-234`,
blocked on `TASK-050`, and it would **dissolve** this defect rather than fix it.
This row must not wait on it: the hole is live under the enforce gate today and
`TASK-234` has no date.

## One coordination note

`viewer/parsers.py` is also touched by `TASK-050` (header folding, in V4 review at
`b5e7be3`) and was touched by `TASK-235` (already merged, which replaced
`parse_decisions` wholesale). `read_conformance` is a different function from all
of those. Keep the edit inside it, and say so in the RESULT if that turns out not
to be possible.


---

## Correction, 2026-08-30 — the attribution above was mine and it was wrong

The original wording of the deliverable said the round trip was one
`"which the reviewer showed is a complete detector for this class"`. **The
TASK-226 reviewer showed no such thing about a per-ROW check.** Its detector was
`render(parse(f)) == f` over the **whole file**, and that claim was true as
written. The per-row form is mine, invented in this spec, and I attached
somebody else's proof to it.

The cost was not theoretical. TASK-241's author inherited the sentence, built the
per-row round trip, discovered by measurement that it does **not** close a fenced
row — a fenced row is byte-for-byte identical to a genuine one, so no row-local
property can see it — and reported that as *correcting the reviewer*. It was
correcting me. The reviewer's file-level claim was never contradicted.

Both halves of that are worth keeping. The **row-local invisibility** result is
sound and provable and was measured (mutation M2), and it is a real contribution.
The **attribution** was false, and it travelled through a spec, a RESULT and a
commit message before a second reviewer caught it.

The rule this spec should have followed: **a specification may state a property
it wants; it may not attribute that property to somebody who did not state it.**
