# TASK-229 — *no store* and *clean* are different answers, and that has been measured for two of six stores

> Serves **P003-O1-KR3** (`phase/003-storage-code.md`): *stores that report `unchecked` rather than `clean` when the store file is removed, **measured by removing each one***. Target **6 of 6**, baseline **2 of 6**.
>
> Dispatch mode: manual
> Executor: manual — the procedure removes state files. It is safe only against a scratch copy, and "run it on a copy" is an instruction an autonomous run can get wrong exactly once. Cheap enough to do by hand.
> Estimated cycle: small
> Subjective verification: (none) — six removals, six quoted outputs
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Rung**: V3
- **Dependencies**: TASK-209 — two of the four unmeasured stores print nothing at all today, so there is no answer to test until the census covers them
- **KR linkage**: `P003-O1-KR3`

> **Correction to this row's own record.** The `Deliverable` line in
> `journal/2026-08/2026-08-28.md § New tasks added` is missing the word
> `perry-lint`: the `add` call passed it inside backticks in a double-quoted
> shell string and zsh ran it as command substitution. The journal block is
> tool-written and is left as it stands; **this file is the authoritative
> deliverable.**

## Why this is not covered by TASK-209

They ask different questions about the same command:

| | asks |
|---|---|
| `P003-O1-KR2` (TASK-209) | does the census **print a verdict at all** for this store? |
| `P003-O1-KR3` (this row) | when the store file is **gone**, does it say `unchecked` — or does it say `clean`? |

The second is the more dangerous half. A census can cover six stores and still
report a missing one as clean, and at that point *"no store"* and *"no drift"*
have been folded into one sentence — the second of which is a guarantee nobody
checked. `perry-lint` already draws the distinction correctly for the two
absent stores, in those words: *"drift against the intake store is
**unchecked, not clean**."*

TASK-209's verification includes removing **one** store file as a self-check on
its own work. This row removes **six**.

## Baseline, measured 2026-08-28

**2 of 6.** `intake.jsonl` and `asks.jsonl` are absent right now, and
`perry-lint --root .` reports each as `unchecked, not clean`.

The other four — `tasks.jsonl`, `okr.jsonl`, `risks.jsonl`,
`.perry/config.jsonl` — are **unmeasured**, and must not be reported as passing
until each has actually been removed. That word is the whole reason this row
exists: the identically-numbered KR one phase ago, `P002-O1-KR3`, scored
**0.33** because its metric said "reported" without saying by what, and the
phase ran nine days before anyone edited a cell in each file to find out.

## Deliverable

Each of the six declared stores is removed in turn and `perry-lint` is shown to
report it as **unchecked**, not clean. One evidence file records the result per
store with the command's actual output — six quoted outputs, not a summary
sentence. Where a store reports `clean` while absent, that is the finding, and
it is fixed in this row.

## Verification — V3

1. **The measurement is the deliverable.** Six removals, six outputs, quoted.
2. **Run against a copy of the state root, never the live project.** Copy
   `.perry/` and `perry/` into a scratch directory and pass `--root <copy>`;
   this was confirmed to work on 2026-08-28.
3. Do not take any measurement while a dispatch is modifying `bin/perry-lint`.
   That happened during this row's own baseline attempt: the working tree
   carried an in-flight `+210`-line change to that file, so any number read at
   that moment described neither the before nor the after. Check
   `git status bin/perry-lint` is clean first.
4. `python3 -m unittest discover -s tests` green if any code changes.

## Out of scope

- Making a store exist — **TASK-203**.
- Making the census cover six stores — **TASK-209**. This row measures what the
  census says when a store is **gone**, which is a different property from
  whether it prints a verdict when the store is there.
