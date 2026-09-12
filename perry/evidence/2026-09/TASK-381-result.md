# TASK-381 — result

> Status: implemented and measured; **not reviewed**.
> Executor: the PMO session, inline on `main`, per `ADR-018 § B`.
> Rung: **V3**, the row's own. `ADR-020`'s gate strictly answers no —
> `dispatch.md` is prose, not a write path — and it is kept at V3 because the
> change edits a **governed span** whose digest three tests pin, and getting
> that wrong silently un-pins this repository's most-attacked rule.

## 0. Eleven instances across three days, and what separates them

| when | instances | cost |
|---|---|---|
| 2026-09-02 | 4 | agents cut from a `main` carrying none of the specs they were told to read |
| 2026-09-07 | 3 | **three different** recovery protocols invented for one defect; one reviewer could not check out at all and rebuilt the tree from `git archive` |
| 2026-09-12 | **5** | **zero** — every agent caught it, fast-forwarded losslessly, and reported it |

Two of 2026-09-12's five were handed a tree that **did not contain the code
they were sent to review**, and it still cost nothing.

**The only difference between the second row and the third is that every brief
on 2026-09-12 pinned the base SHA and told the agent to assert it.** That
practice lived in the dispatcher's head and in no file. This row moves it into
the file.

## 1. What was measured about the cause, and what could not be

- The recurring base `583f024f` was **already 102 commits behind** when this
  session started, so the worktree is not cut from `main`'s tip.
- The eight branches still sitting exactly on it have **no worktree attached**,
  so it is not a pool of pre-created checkouts either.
- The dispatch at 23:40 got `main`'s tip exactly, so the behaviour is not
  uniform.

**The worktree is cut by the harness, outside this repository. Perry has no
code on that path.** This row does not claim to repair it, and the rule it
writes says so in its own text.

## 2. The change

`work/reference/dispatch.md § The tree the agent works in`. One bullet,
6 lines out and 36 in, nothing else in the file moved.

It was *"State the worktree's branch point in the prompt"* — half the rule, and
the half that does not work alone: it tells the agent what to expect and leaves
it to notice. It is now the full protocol, on both sides:

- the brief **names the base SHA**, says main's tip, and says what to do when
  they differ;
- the agent runs `git log --oneline -1` and
  `git merge-base --is-ancestor <base> HEAD`, **fast-forwards its own branch
  only** on a strict ancestor with a clean tree, and **reports what it found
  either way** — including when the base was correct, because *"I checked and
  it was fine"* and *"I did not check"* are different answers and only one is
  evidence.

**A first draft dropped the 2026-09-02 incident sentence while rewriting the
bullet.** It was restored before the digest was pinned: the record accumulates
rather than being swapped, and a rule's evidence is the part that makes it
survive its next reader.

## 3. The pin, re-pinned deliberately

The guard caught the edit, which is the machinery working:

```
dispatch.md § the tree + § Executor: claude-subagent changed.
If the rule really changed, re-pin it deliberately: 0338efa0…
```

Previous pin `3780eb88…` (TASK-421); new pin `0338efa0…`. **The diff was read
before the digest was pasted** — that is `GOVERNED_SHA`'s own stated procedure
and § 2 above is the reading.

## 4. THE LIMIT, declared rather than promised away

**A dispatch brief is a prompt, not a file, so no test can assert that a given
brief carried its base.** This row cannot build the guard that would catch the
next omission. What it can do is what it did: the rule is written where the
dispatcher reads it, and the governed digest makes any future *edit* to that
rule deliberate. A check over briefs would need briefs to be recorded, which is
a different row and is not filed here.

## 5. Mutations — three, none green

| # | Broken | Result |
|---|---|---|
| M1 | the rule's own sentence reverted to the old half | RED — `test_the_governed_regions_are_pinned` |
| M2 | a wrong digest pasted | RED — same test, different direction |
| M3 | the agent-side ASSERT half deleted, dispatcher half kept | RED |

## 6. A harness defect in my own mutation round, found and corrected

The first pass reported **`BASELINE-restored → RED`** with both files verified
byte-identical by sha256. They were identical. The `.pyc` was not.

`M2` mutated a **test module**, and CPython validates a cached `.pyc` against
the source's mtime **in whole seconds** and its size. Write a variant, run,
restore the same size within the same second, and Python trusts the stale
bytecode. This project already has a knowledge card for it —
`knowledge/toolchain/pycache-staleness`, from `TASK-072` — and my harness did
not clear the cache.

Re-run with `__pycache__` cleared before every run: BASELINE green, M2 red,
BASELINE-restored green. **The finding is not about the code; it is that a
mutation harness which mutates a Python module and does not clear the cache
reports a result about the wrong bytes** — the third measurement-artefact of
this session, after the shell stripping trailing newlines (`TASK-327`) and the
mis-anchored replace (`TASK-379`).

## 7. Suite

`bash tests/run`: **3 of 3,757 failed** — `test_contract_key_parity` (2) and
`test_resume` (1), the pre-existing set by name. Tree guard clean:
*nothing under /Users/bytedance/proj/Perry moved*. `perry-lint`: 0 error(s).
