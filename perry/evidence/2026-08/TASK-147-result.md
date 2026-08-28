# TASK-147 — two flips reddened nothing, and that is the row

**From `coding/task-147` @ `fe61262`.** Rung **V3**. **One file changed** —
`tests/test_md_store.py`, +254/−0. `bin/`, `perry/`, `tests/fixtures/`
byte-untouched, verified.

## The enumeration, which was the first deliverable

**`describe_cell` has exactly two call sites**, both in `bin/perry_store.py`:

| line | caller | `escape` |
|---|---|---|
| 416 | `row_descriptor` — a markdown table cell | defaulted `True` |
| 447 | `slot_descriptor` — a `- Key: value` bullet | `escape=False` |

**My spec's "five references in two files" was a grep for the name, and this
time it over-counted.** Only **one** of the five is a call
(`tests/test_md_store.py:515`), and it passes no `escape` at all; the other four
are prose in docstrings. `bin/perry-tasks:124` re-binds the name and never calls
it.

I have been wrong about call-site counts six times in two days by under-counting.
**This is the first time the same method over-counted**, and the failure is
identical: grepping a name answers a different question from grepping a call.

`escape` is **decided** in four places, two per call site — the argument, and
the descriptor's `escape` key that `render_line` reads back (`:410`, `:416`,
`:441`, `:447`). Two places read it: `:316` (`cell_text`) and `:332`
(`pad = " " if escape else ""`) — **one flag doing both escaping and padding**,
exactly as the docstring claims.

## Question 2: there is one answer, so nothing needed unifying

`bin/perry_md_store.py § plan:662` dispatches on `site["how"] == "table"` (set
at `:368`, `:504`, `:563`), and both branches land in the two builders above.

**`viewer/tables.py § render_row` and friends escape unconditionally — and they
are not a second answer.** Every caller (`perry-task`, `perry-goals`,
`perry-decide`, `perry-conform`, `perry-migrate`) hands them a table row. **They
never ask the question.**

That distinction is why `bin/perry_store.py` stayed out of the diff. I had told
the row that two independent deciders would make it bigger than its title and I
wanted that reported rather than fixed; the honest answer was *one*, and it said
so instead of finding a second to justify a larger change.

## The mutation proof is the finding

| flip | red before | red after |
|---|---|---|
| M1 `row_descriptor` → `escape=False` | **0** | 2 |
| M2 `row_descriptor` `desc["escape"]` → `False` | 7 | 11 |
| M3 `slot_descriptor` → `escape=True` | 3 | 7 |
| M4 `slot_descriptor` `desc["escape"]` → `True` | **0** | 4 |
| M5 `render_line` default → `False` | 0 | 0 |

**Two flips reddened nothing across the whole suite.**

### M1 is invisible to `cmp`, and the reason is worth reading twice

Describing a table cell with `escape=False` makes it a **disagreement**. The
descriptor's own `escape=True` then **re-escapes the stored value into exactly
the bytes already on disk**. `perry-config diff` returns 0.

The only witness is **the plan** — which reports a cell the two sides agree on
as drifted, and prints `file` and `store` as **the same string**, because line
421 re-escapes the store side too.

**`cmp` is this module's stated bar and cannot see M1.** So the new test asserts
the *report*, not just the bytes. A test written to the module's own standard
would have missed this.

### M4 is a corpus gap, not a code defect

Flipping it **wrote `\|` into every config bullet** and **nothing in 2574 tests
noticed** — because no bullet anywhere in the repo or its fixtures carries a
pipe.

## Question 3: yes, and the test exploits it

`.perry/config.md` carries **both shapes** — preamble settings on the bullet
path, `## Tracks` rows on the table path. One `perry-config write --from-file` /
`render` / `diff` / `verify` round trip through the real `--root` seam crosses
the boundary in both directions.

`TestTheTableAndBulletPathsStaySeparated` (5 tests) **writes its own config**:
one stored value containing `|` reaches the file **escaped in the cell and raw
in the bullet**, reads back as itself through `viewer/tables.py § split_row`,
and moves in both shapes when the store moves.

And it names why it does not point at Perry's own config: **no setting or track
cell here carries a pipe**, so a test aimed at the live file *would pass against
a renderer that escapes nothing.* That is the trap I warned about, answered with
a measurement rather than a promise.

## Reported, not fixed

- **`render_line`'s `desc.get("escape", True)` default is unreachable from
  production** — both builders always set the key. Only a hand-built descriptor
  in a test reaches it. (M5 reddening nothing is consistent with this, not a
  second gap.)
- The `store:` string in a drift finding (`:421`, `:452`) is cosmetic, and under
  M1 it prints two identical-looking strings as a disagreement — **the shape
  that makes a reader conclude the report is broken** rather than the code.

## Where my spec was wrong

I quoted the invariant as *"`describe_cell` … its own comment, at 266-269"*.
Those lines are **`cell_text`'s** docstring (function at 255).
`describe_cell` restates the rule at 321-331 for the padding half. Nothing turns
on it; the row followed the code.

## A process hazard worth more than this row

An earlier mutation sweep was **SIGTERM'd at a 10-minute tool cap and its
`finally` never ran**, leaving a mutation in `bin/perry_store.py` and its test
file reverted. It caught this via `git status`, restored from git, and re-ran the
sweep **detached, with signal handlers**.

**Other agents run mutation sweeps in place.** A sweep killed mid-flight leaves
the tree mutated, and the next thing to read that file — including a merge —
reads a deliberate defect as if it were the work. Filed.

## Verification

- `perry-lint` before and after: **0 errors, 3 warnings, 173 records, 0 rows
  drifted** — unchanged, and re-run by me after the merge check.
- Suite: **86 modules · 2579 tests · 1 red** (`test_diagnose`, standing). Was
  2574; +5 is this class.
- Every mutation reverted, `git status --porcelain` empty after the sweep, and I
  confirmed independently that `bin/` is byte-identical on the branch.
- One "kill" in the before-M7 row was `test_host_support.TestOpenCodeDispatchLimit`
  — a timing-sensitive concurrency test that passed 3/3 unmutated and killed 0
  after. **Called a flake and excluded, rather than counted.** It is the same
  contention flake merge-check reported earlier tonight.
