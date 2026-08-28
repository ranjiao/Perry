# TASK-037 — one `perry-goals` refusal names the flag the user typed and its sibling does not

**Merged locally 2026-08-21** from `coding/task-037-refusal-names-flag` @ `7fadd7e`.
Rung **V3**. `tests/merge-check --base feat/work-modes t037=… t040=…`: nothing
new is red on the merged result.

## What the row was re-scoped to, and why

The row was opened with a V4 target against findings from three earlier review
rounds. Before dispatch those findings were checked against today's code and
**most no longer existed**:

| earlier finding | 2026-08-21 |
|---|---|
| the refusal path raises `NameError: name 'args' is not defined` | fixed — a proper refusal returns |
| `viewer/tables.py` raises an undefined `Refused` | fixed — line 230 is a comment explaining the history |
| the flag-naming block sits in module scope | fixed — it is in function scope and names its flag |

Most likely carried out by TASK-119's rewrite of `bin/perry-goals`. What
survived was one inconsistency, against a rule the same file states at line
1897: the whitespace refusal names its flag and its line-break sibling does not.

The row was retitled to that sentence and the rung dropped V4 → V3.

## Verified independently

Not taken from the agent's report.

**The whitespace refusal is byte-identical across the merge.** md5 of the block
from `# **Whitespace-only is a refusal on create` through
`Nothing was written")`:

```
feat/work-modes                      b8f29f90e8c71f941a290acf0792d092
coding/task-037-refusal-names-flag   b8f29f90e8c71f941a290acf0792d092
```

**The second defect it reports is real.** On the base, `UnrenderableCell` is
caught at exactly one place — line 2797, inside the `if __name__ == "__main__":`
block that begins at 2790, **outside** `main()` (2616), where `args` does not
exist. So no line-break refusal could ever reach the `--json` branch: exit 1,
stdout empty. On the branch it is also caught at 2815, inside `main()` (2721).

```
BEFORE (stderr; stdout empty under --json)
  perry-goals: refused — was given 'a\n\nb', which contains a line break — …

AFTER (stderr)
  perry-goals: refused — --promise was given 'a\n\nb', which contains a line break — …

AFTER (--json, stdout, rc 1 — previously nothing at all)
  {"refused": "--promise was given 'a\\n\\nb', which contains a line break — …"}
```

**`perry/` untouched, `schema/state-schema.json` untouched** — `git diff
--name-only <merge-base> <branch> -- perry/` is empty.

## The count, which is the deliverable

`bin/perry-goals` has 68 `raise Refused` sites plus one `UnrenderableCell`
translation channel. **45 refusal paths are reachable from a user-supplied
value**; the other 33 take no user value at all — they are about the file, the
store, the schema, the lock, or the writer's own bugs.

Of the 45, **32 now name the flag**. The 13 that do not each have a reason:

- **12 are in `link`**, which takes its values **positionally** —
  `goals/reference/linkage.md` writes the grammar that way, so there is no flag
  to name. The three that reject a value's *form* used to say only
  `argument 1`; they now name the **slot**, read out of the same `usage` string
  the arity refusal prints, so the refusal cannot quote a placeholder the
  grammar no longer has.
- **one** is `{cid} is already closed` — about that row's state, not about where
  the user's words went, and the id is already echoed.
- **`track_named` when the track came out of the file** names no flag on
  purpose. The value was never typed, so naming `--track` would send the user
  to fix a flag they never passed. Asserted as
  `test_a_track_read_out_of_the_file_names_no_flag`, and a mutation that names
  the flag *unconditionally* reddens it.

## Why the two prior V4 rounds failed, and what stopped it repeating

Both failed the same way: **the named path was fixed and its sibling was left
carrying the same defect.** Round 4's verdict on round 2 was that its central
sentence was false; round 4 itself moved an undefined name from one file to
another — *"only the name changed."*

So verification item 2 asked for an **enumeration of every refusal path
reachable from user input, with a count** — not for one path to be fixed. That
is the table above.

Seven mutations were applied one at a time and reverted. **Each reddens its own
refusal and no other** — no shared assertion catches them all, which is what
makes the count load-bearing rather than decorative.

## Left open

1. `bin/perry-decide` and `bin/perry-conform` **do not catch `UnrenderableCell`
   at all** (`grep -c`: `perry-task` 2, `perry-goals` 2, `perry-decide` 0,
   `perry-conform` 0). A line-break value reaching a cell in either is still a
   traceback, not a refusal. Out of this row's scope; worth its own.
2. `perry-task`'s flag naming is still a match-back heuristic over a hand-kept
   list of 12 attribute names — exact-match-or-nothing, so two flags carrying
   the same string name whichever comes first, and a thirteenth free-text flag
   joins silently unnamed. `perry-goals` now names at the write site instead.
