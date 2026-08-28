# TASK-123 — the two writers were never in agreement; the check never asked

**From `coding/task-123`.** Rung **V3**. `perry/` untouched.

## Question 1: `perry-lint` does not cover `OKR.md` at all

`check_store_drift` (~2424) opens **`state_root/tasks.jsonl` and `BOARD.md`, and
nothing else.** Its own module docstring says so at line 16: *"when `<state
root>/tasks.jsonl`…"*. `okr.jsonl` reaches `perry-lint` only through
`_md_store_module()` → `looks_like_perry_record` — **"did Perry write this
file", not "has it drifted".**

Confirmed independently:

```
store_drift.records            173
wc -l perry/tasks.jsonl        173      ← exactly, so the census is tasks-only
perry/okr.jsonl                 36      ← outside it entirely
.perry/config.jsonl             —       ← outside it entirely
```

**So the two writers were not in accidental agreement. The check never asked.**
That was the question I said mattered more than the fix, and it does: **I have
been quoting "0 rows drifted" in the handoff all night as a whole-project
figure.** It is a tasks-only figure. Corrected in `4995aa5`.

It left widening the census as a **finding rather than a fix** — doing it would
move the `173 record(s)` line my own verification pins, and `bin/perry-lint` was
out of scope. Correct call; it is its own row.

## Question 2: one subcommand, two call sites

Grepping **the write**, not the name: `write_atomic` / `lib.write_atomic` are the
only calls that put bytes on disk. `OKR.md` is reached only via
`write_okr_and_store`, from `cmd_commit` at **2371** (`--migrate`) and **2625**
(ordinary). `cmd_link` writes the linkage register; `list` reads.

**Pinned by a test that reads the source and asserts the exact call-site list**,
so a new one goes red. That is the durable version of a fact I have got wrong
seven times in two days.

## Where my spec was wrong about the live state

**`perry/OKR.md` has no `## Commitments` section.** The store holds 34 `kr` rows
and 2 `version` rows — **zero commitments**. Verified.

So `perry-goals commit` has **never written this file**, and *that* — not
agreement, not coverage — is the immediate reason nothing was drifting here.
Every case it built is a temp project through `--root`.

## Four defects, reproduced before anything changed

1. A hand edit to a row the command **touches** was written into the store and
   **not reported at all** — `store_drift: []`, because `md_store.touches`
   excuses that row's key as the write's own doing.
2. A hand edit to an **untouched** row was reported as drift **and written into
   the store anyway** — reported *and* honoured. ADR-007 says reported *rather
   than* honoured.
3. **Data loss, and it is the serious one.** `perry-okr write --from-file` puts
   rows in the store and not in the log, so a hand-deleted row left its id where
   neither the table nor the log could see it. `commit --track ops` then minted
   **`ops/1` a second time, for a different promise**, with `store_drift: []` —
   **the record it destroyed was the one it was named after.** That is
   `mint_commitment_id`'s own documented *"one failure mode worse than a dangling
   link"*, reached in practice.
4. Found on the way: deriving the store from post-edit text meant a hand-deleted
   row **deleted the canonical record** — the exact loss `perry-okr write
   --from-file` refuses by name.

## What changed

`register_drift` / `check_register_drift` compare `okr.jsonl` to the register
**before any decision**, over all seven value fields, and **refuse** on
disagreement. `--accept-hand-edit` is the way through, unchanged in meaning;
`--dry-run` and `--migrate` are gated too. `mint_commitment_id` searches the
store as a third list. `write_okr_and_store` keeps a record whose row has left,
and names it. **Nothing re-renders `OKR.md`.**

## The test it reversed, and why the argument holds

`test_a_hand_edit_is_reported_by_the_writer_and_not_swallowed` asserted
report-and-proceed — **and proceeding is what absorbed the edit.**

> The Operating Principle isn't broken — the edit stands in the file, untouched;
> what refuses is the write that would decide against it, which `check_hand_edit`
> has done since TASK-042. **Readers report and proceed; writers refuse and name
> the way out.**

That distinction is the right one and it is not in ADR-007's text. Reversing a
green test needs exactly this kind of argument, and it made it.

## Numbers

- **Mutation proof**, distinct test methods red: gate removed → **7**; store ids
  out of the mint → **2**; kept records dropped → **1**. Controls green under all
  three.
- **`perry-okr diff`: `identical: true`, before and after.** `render` output
  `cmp`-equal to `perry/OKR.md` (12431 bytes) — the constraint I set, met.
- **`perry-lint`: 0 errors, 3 warnings, 173 records, 0 rows drifted** — unchanged.
- **Suite: 87 modules**, one red — `test_diagnose`, standing.
- No contract bump, with the reason: `LIST_CONTRACT` covers `list`; `commit`'s
  payload is Perry-internal and the two new keys are additive.

## For you

**No migration command is needed on this project** — `perry/OKR.md` has no
register to migrate and `perry-okr verify --root .` is clean. On a project that
*does* have one, the one-time import is `perry-okr write --from-file --root
<project>`, and `perry-okr render --write` is the way back if the file has
drifted.
