# TASK-412 — result

> Spec: `perry/evidence/2026-09/TASK-412-spec.md`
> Branch base: `main` @ `575f9dee` (the spec's bound is `fe0292fb`; the page's
> two defective lines are byte-identical at both, see § Bound drift)
> Worktree: `.claude/worktrees/agent-abcccc4a17f2a4955`
> Scratch: `…/scratchpad/task412-abcccc4a` (agent-id suffixed, per the
> shared-scratch collision history)

## 1 · The sweep

`schema/task-list-contract.md` is 1268 lines and carries **6 fenced blocks**.
`grep -n '^```'` finds only 5 fence *lines* worth of them because the rule-3
block is indented three spaces inside a numbered list item — the enumeration
has to match ` *``` `, not `^``` `, or it misses the block this row is about.

| # | line | lang | what it is | executed by a test before this row |
|---|---|---|---|---|
| 1 | `:13` | `bash` | the `perry-task list` invocation a consumer copies | no |
| 2 | `:98` | `jsonc` | the payload's top-level shape | no — `test_count_fields` regexes two *numbers* out of it (`:100`, `:110`), nothing parses it |
| 3 | `:120` | `jsonc` | `bound`'s shape | no |
| 4 | `:578` | `python` | rule 3's version/semantics gate | **no** — this is the row |
| 5 | `:804` | (none) | 1.14 changelog transcript, a state fixed since | no |
| 6 | `:980` | (none) | 1.12 changelog line, a state fixed since | no |

**Executed by a test today: 0 of 6.**

The spec says the rule-1 version gate "the reviewer did execute". It is not a
separate block — it is lines 5–6 *inside* block 4 (`if major not in {m for m, _
in SUPPORTED}: raise SystemExit`). A reviewer ran it by hand against a live
payload; no test does. So the asymmetry the row names is real but finer than
"one block tested, one not": **one half of one block was executed by a human,
once, and nothing on the page is executed by the suite.**

## 2 · The defects

Reproduced at `575f9dee` before any edit:

```
D2  '1.5'  > '1.18'  = True    (correct: False)  -> warns about an OLDER change
D2  '1.12' > '1.9'   = False   (correct: True)   -> silently SKIPS a newer one
D1  max({(1,18),(2,0)}) = (2, 0)
D1  (1,19) > (2,0)   = False   (correct: True)   -> 1.x drift unreportable
```

The second D2 line is the direction the spec's prose does not name and is the
worse one: a string compare does not merely add a false warning, it **drops a
true one** whenever the newer minor has fewer digits than the tested minor.

A third defect the sweep turned up, which is why the block had to be executed
rather than read: **`TESTED_MINOR_STR` is bound nowhere on the page.** The
snippet as shipped raises `NameError` on any payload that reaches line 9. It
could not have been executed by anything, which is consistent with nothing
having executed it.

