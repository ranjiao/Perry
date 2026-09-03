# TASK-256 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: medium
> Subjective verification: (none) — the check either catches a corrupted baseline or it does not
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists, and why it is worth more than its size

Filed 2026-08-30 from `TASK-249`'s round-4 result. The agent found the defect
**in its own instrument**, reported it rather than quietly re-running, rebuilt
the copy and re-ran. That handling was right, and it is exactly why this needs a
row: **the harness pattern is prescribed by the PMO in every dispatch brief**, so
this is a defect in the project's verification discipline rather than in one
agent's script.

Every V4 round on this board rests on it.

## The defect, demonstrated

The prescribed pattern snapshots the bytes and their digest **before** mutating,
then writes the bytes back and compares the digest:

```python
BASE = (f.read_bytes(), md5(f))   # snapshot
f.write_text("MUTATED")            # mutate
f.write_bytes(BASE[0])             # restore
assert md5(f) == BASE[1]           # "verify"
```

**That assertion cannot fail when the write succeeds**, because `BASE[1]` is the
digest of `BASE[0]` and `BASE[0]` is what was just written. It verifies *the
write happened*. It does not verify *the file is what it should be*. Run
2026-09-03:

```
honest restore     : True · file is ORIGINAL
corrupted baseline : True · file is ALREADY-WRONG   <-- reports OK while wrong
```

**This is not hypothetical.** `TASK-325`'s agent reported finding
`bin/perry-task` already carrying a mutation at a point before it had run its
harness, and could not account for how. Under this check a restore onto that
baseline reports OK.

## Deliverable

**The correct pattern, written where an agent will actually read it, plus
whatever makes it cheap to follow.**

1. **State the rule where reviewers read it.** `work/reference/review-constraints.md`
   is referenced by path from every review prompt and is the natural home;
   `work/reference/review.md § 2 rule 2` states the mutation discipline and does
   not currently say how to verify a restore. Put it in one place and reference
   it from the other — **do not write two copies**, which is a defect this
   project names repeatedly.
2. **The rule itself**: a restore is verified against an **independent source** —
   `git show <ref>:<path>` — never against the bytes the harness snapshotted.
   Say *why* in one sentence, because a rule with no reason attached gets
   reverted by the next author.
3. **Consider shipping the harness rather than prescribing it.** Six briefs
   this week hand-rolled the same loop. If a small shared helper is the right
   answer, say so and build it; if it is not — because a harness that lives in
   the tree can itself be mutated — say that instead. **Either answer is
   acceptable; an unstated one is not.**

## Verification

1. **Reproduce the circularity** with a control that fails on the old rule and
   passes on the new one: a baseline snapshotted from an already-corrupted file
   must be **caught** by the new pattern and **missed** by the old.
2. **A named test** asserts the guidance says what it must. If you ship a
   helper, the test mutates the helper and shows the check go red.
3. **Do not build a linter for other people's harnesses.** Agents write these
   ad hoc in scratch directories that no check can reach. This row fixes the
   *instruction* and optionally the *tool*; it cannot police the practice, and a
   check that claims to would be the fourth guard-over-behaviour failure here
   this week.
4. Full suite no redder than the baseline **you measure**; `perry-lint --root .`
   at 0 errors.

## Bound

```
Enumeration: grep -rn "md5\|restore" work/reference/review.md \
                                     work/reference/review-constraints.md \
                                     work/reference/dispatch.md
Size:        0 sites state how to verify a restore today — that absence IS the
             finding, and the bound is the set of files a reviewer or a
             dispatched agent is told by path to read: review-constraints.md,
             review.md, dispatch.md, delegate.md  (4)
Remainder:   the PMO's own briefs are ephemeral and out of reach of any check;
             the memory file that carried this prescription was corrected by
             the PMO on 2026-09-03 and is outside the repository
```

A fifth file that should carry it is **a new row**, not a widening.

## Out of scope

- Auditing past rounds' mutation results. The defect makes a restore
  *unverified*, not *wrong*; re-running months of rounds is not proportionate
  and nothing suggests a specific result is false.
- `TASK-298` (shared-scratchpad collisions) and `TASK-313` (the dispatch-limiter
  race). Neighbouring, separately filed.
- Any check that tries to detect a bad harness in an agent's scratch directory.
