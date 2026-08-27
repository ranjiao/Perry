# TASK-117 — drift is unchecked, not clean, and `perry-lint` was the wrong half

**Merged locally 2026-08-28** from `coding/task-117-drift-unchecked-not-clean` @
`9355e0c`. Rung **V3**. `merge-check`: nothing new is red.
`perry-task/list` **1.15 → 1.16**, by a PMO overrule — see the last section.

## It inverted my framing, with a measurement

My spec said *"one tool learned the lesson and the other did not"*, casting
`perry-lint` as the tool that had. Measured on the scratch fixture — Perry's own
`BOARD.md` and `tasks.jsonl` with `.perry/events.jsonl` removed:

```
no log                                        175 of 175 "drifted"
log restored, board and store byte-identical    0 of 175
```

**Nothing about the two files being compared changed.** What lint was measuring
was *the log's absence wearing the board's name*:

- **137** are store-only records — `done` removes a row, so closed tasks are
  re-derivable only from the log.
- **38** differ on `created` **and nothing else**, and `created` is in
  `perry_store.STORED` and **not** in `FIELD_BY_COLUMN`. **No board column
  renders it.** The spec's suspicion, confirmed: that is not drift, it is a
  field the projection never carried being read as if it had been erased.

`check_store_drift`'s left-hand side is `perry-tasks.build()`, which reads the
board **and** the log; the log is derived and disposable (DESIGN-004 § 5.3);
`build()` degrades silently when it is gone, so lint could not detect a state it
already has a name for.

**The corroboration that settles it:** the remedy the finding *printed* —
`perry-tasks write --from-board` — would have **discarded 137 canonical records
and 38 real timestamps** on a board the user never touched.

## How a consumer cannot read unchecked as clean

**A null in every findings-shaped field, governed by one predicate.** Not just
the two counts: `len(orphaned)` reads exactly the way `drift` does, so nulling
only the counts leaves the same hole three keys over.

Null rather than key omission, on the contract's own **rule 1**, which names
`""` / `null` / `[]` as this payload's unknown value and forbids a missing key.
And it fails **loudly** — a consumer that skipped the flag gets `None + None`,
not a reassuring number.

## The tool I held up as the model had the same trap

`perry-lint` had learned the lesson **only in prose**. Its `--json` payload
carried `drifted: 0` beside `comparison_performed: false` in all three of its
own unchecked states. Four exact-dict assertions now pin it.

And the two tools were never measuring the same pair: lint compares board ↔
`perry/tasks.jsonl`; state compares board ↔ `.perry/events.jsonl`. They agree
now because **both** comparisons depend on the log — state's directly, lint's
through `build()`.

## The overrule: 1.15 → 1.16

The agent recorded the change as **"Not a version"** and explicitly flagged it
as the one judgement worth overruling. **I overruled it.**

The page said, at base, in as many words:

> `checked` | bool | `false` when there is no event log … **Everything else is
> then zero or empty.**

That is a **documented guarantee on a versioned payload**, and a consumer
reading `drift == 0` as "no drift" was *following the documented text*. The
precedent the agent cited itself — **1.5** — is a meaning change with no key
change that moved the minor and gained a `semantics` entry. TASK-040's "Not a
version" precedent is different in kind: that was *documenting what already
ships*. Here five values genuinely change.

So: `1.16`, with a `semantics` entry naming all five fields, and the changelog
entry promoted from "Not a version" to `### 1.16`. Seven files pinned `1.15`;
all updated.

**Two things my own bump broke, both caught by tests that existed:**

1. I inserted the entry at the **head** of `LIST_SEMANTICS`.
   `test_the_semantics_list_is_ordered_oldest_first` — which came from aiMark's
   production report — caught it.
2. TASK-170's `test_the_contract_moved_and_the_document_says_why` asserted
   `LIST_SEMANTICS[-1]["version"] == "1.14"`, to record that 1.15's *absence* of
   an entry was deliberate. **That assertion encoded a moment, not the rule** —
   it held only while 1.15 was newest. Rewritten to assert what it means: there
   is no `1.15` entry, and 1.14's exists. Its docstring now says why.

Post-bump: **80 modules · 2400 tests · 2 red**, both pre-existing.
KR-O2.4 = 0 across all six contracts.

## Two findings filed rather than fixed

- **`bin/perry-state:1762` builds `design.by_status`'s keys from a set**, so the
  payload's key order flips with the hash seed — verified here, three runs each
  way in six. `perry-state --json` cannot be byte-compared until that is fixed.
- **Two agents running `tests/parallel` write to the same scratchpad baseline
  path** and overwrite each other's readings.
