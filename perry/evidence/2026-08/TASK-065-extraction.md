# TASK-065 — `bin/lib/`, and the four bugs the copies hid

## What the rung is, and why it is not V4

**V3, not V4.** The implementation was done by a dispatched agent; I verified it
independently — full gate, `perry-lint`, and the one behaviour change measured
against `HEAD` in a scratch copy. That is a reproducible run, which is V3.

It is **not** V4, because V4 is *a fresh-context reviewer against written
acceptance criteria* and no such reviewer has seen this. I closed it at V4 first
and corrected it: claiming a rung nobody ran is precisely what
`perry-lint --reviews` exists to report, and doing it in the same session that
built that check would be worth more as an example than as a close.

## The verification that was run

```
bash tests/run                 # ✓ all green, all four steps
python3 tests/parallel         # 45 modules · 1385 tests · green
python3 bin/perry-lint         # ✓ clean
```

Independent check of the one behaviour change, against `HEAD` rather than
against the claim:

```
git archive HEAD | tar -x -C <scratch>
chmod 644 <copy>/perry/BOARD.md
(cd <scratch> && python3 bin/perry-task next TASK-0NN --root <copy> --next x)
stat -f %Sp <copy>/perry/BOARD.md      # -rw------- ALREADY, before the change
```

## What was unified

`write_atomic` 5→1 · `project_lock` 4→1 · `load_schema` 5→1 (the five that
raise) · `resolve_state_root` 2→1 · a `stage` split absorbing `perry-task`'s
inline copy. **No existing test needed editing.**

## The four differences, each a bug in at least one copy

| Copy | What differed | Kept |
|---|---|---|
| `perry-knowledge.project_lock` | lost `time.sleep(0.05)` — a busy spin at 100% of a core for the full 10s timeout | the sleeping version |
| `perry-diagnose.resolve_state_root` | matched `State root:` with an **ASCII colon only**, so a project declaring `State root：docs` moved for every tool except this one | the canonical one |
| `perry-task.project_lock` | `try/flock(UN) finally: close` — an `OSError` on unlock replaces the exception the body was raising | suppress; closing the fd releases the lock |
| `write_atomic` | two bodies — `mkstemp`+fsync+cleanup vs a fixed `.tmp` name that two writers collide on and that survives a failure | `mkstemp` |

## Three that looked like duplicates and were not

- **`heading_re`** — a name collision with one **dead** side. `perry-task`'s
  had zero callers despite a docstring claiming some. Deleted, not merged.
- **`mint_id`** — three id grammars over three source sets, sharing
  `max(...) + 1` and nothing else. A shared *rule*, not an implementation.
- **`load_schema`** — one file read with **three** error contracts. Three
  readers fall back to a default on purpose and were left alone.

## What must be true when this is done

1. Every named primitive has one implementation reachable by every tool that
   uses it. **Met** for the five above.
2. No behaviour changes except where two implementations disagreed, and each
   such change is named with the reason. **Met** — one change, the file mode,
   measured against `HEAD` and found to pre-date the extraction for three of
   the four tools.
3. The category is guarded by something that asks what a file *does*.
   `tests/test_one_primitive.py`, verified against three plants including one at
   `bin/sub/deep.py`.

## What was NOT checked

- **A fresh reviewer has not seen it.** That is the whole gap between this and
  V4, and it is why the row is not closed at V4.
- **`bin/perry-knowledge` carries copies named in no report**, and schema
  loading is 5 named plus **9 inline** reads. The nine share the non-raising
  contract and want a different primitive. Not done, not counted here.
- **Neither `write_atomic` preserves the target's original mode.** Real, and
  TASK-079's territory — fixing it changes four tools rather than merging two.
- gimegime-pmo and PolyForge were not re-run against the extracted tools.

=== VERDICT ===
task: TASK-065
rung: V3
result: PASS
criteria: this file § What must be true when this is done
checked: full gate and lint on the merged tree; the file-mode change measured
         against HEAD in a scratch copy rather than taken from the report; the
         patch applied three-way so a same-file change made after the worktree
         forked survived, and confirmed present afterwards
not-checked: no fresh reviewer; perry-knowledge's unreported copies; the nine
             inline schema reads; mode preservation; the two real projects
proof: (none — this is a PASS)
=== END VERDICT ===
