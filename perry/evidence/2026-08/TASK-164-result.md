# TASK-164 — each root global gets the root its name means

**Merged locally 2026-08-28** from `coding/task-164-two-roots-one-global` @
`5546f74`. Rung **V3**. `perry/` untouched, 0 bytes.

## The enumeration was the deliverable, and it inverted my claim

Five reads and one write, repo-wide. **Today there are zero call-time readers of
either global, so the assignment was a dead write.**

| site | reads | wants | exposed? |
|---|---|---|---|
| `parsers.py:352` `STATE_ROOT = resolve_state_root(PROJECT_ROOT)` | `PROJECT_ROOT` | **project** | No — module scope, runs at **import**, strictly before `bin/perry-state` can assign |
| `parsers.py:3484` `load_snapshot(root=STATE_ROOT)` | `STATE_ROOT` | **state** | No — the default is bound at **def** time; every caller passes `root` explicitly |
| three test sites | both | one each | No — all read after `importlib.reload` |

My spec said *"every other reader after the assignment is still exposed."*
**There are no other readers.** The hazard is real and **latent**, and the
journal entry of 2026-08-21 already had it right — *"a no-op today because
`load_snapshot` binds its default at def time."* **My spec was less accurate than
the journal it came from.**

That also explains why the escalation-scan bite came through an *argument*
(`escalation_scan(root)` rather than `project_root`) and not through the global.

## A second defect the spec did not name

**`P.STATE_ROOT` was never assigned at all.** On `perry-state --root
<other-project>` invoked from inside a Perry-shaped repo, `STATE_ROOT` silently
kept the **invoking cwd's** state root. The mutation run proves it directly.

## The fix, and why not deletion

Paired assignment, each global to the root its own name means. Deleting the dead
write removes the lie but leaves both globals resolved by walking up from the
cwd — which for `perry-state --root /elsewhere` run from inside another project
points `PROJECT_ROOT` at **an entirely different project**. A strictly worse
silent wrong answer, and it abandons the `--root` intent.

## Verification 3 asserts the file, never a verdict

```
hook_under_project_root == True
hook_under_state_root  == False   ← proves the fixture separates them
```

The second assertion is the guard that the first *could* have failed. **A gate
can report "unarmed" for two different reasons, and that is how this hid the
first time.**

Mutation: 6 of 7 new tests redden, the headline one naming the confusion in
words. `perry-state --json` before/after × in-repo/from-`/tmp`: all four
identical apart from `generated_at`.

## Two follow-ups it flagged rather than took

- `load_snapshot`'s def-time-bound `STATE_ROOT` default is *why* the assignment
  is inert. Changing a public signature default is not this row.
- `--json`'s `project.root` still reports the **state** root — a third name for
  the same confusion, and a published contract the existing tests explicitly
  refuse to rename.
