# TASK-330 — spec

> Dispatch mode: auto
> Executor: claude-subagent (repository-local, stdlib only, no MCP)
> Estimated cycle: small
> Subjective verification: (none) — a rule is gone or it is not
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists

**User decision, 2026-09-03**: checks of the shape *"does this prose read like
prose"* are not Perry's to make. Quality of a summary is the writing agent's
responsibility, and Python should not be scoring it.

`TASK-325` shipped four rules in `bin/lib § summary_shape`. Two are
deterministic facts about typed fields and stay. Two are judgements about
language and go:

| rule | what it decides | verdict |
|---|---|---|
| `summary-missing` | absent, empty, or whitespace only | **stays** — a fact |
| `summary-repeats-title` | folded equality, or one a prefix of the other | **stays** — two typed fields compared |
| `summary-has-no-sentence` | *"no sentence terminator anywhere"* | **remove** |
| `summary-is-a-fragment` | *"fewer than `SUMMARY_MIN_WORDS` tokens"* | **remove** |

`TASK-325`'s own round drew this line one step further out than `ADR-007`
does, and said so in its docstring — *"what it does not judge is part of its
contract"*, with readability, reading-level, vocabulary, hedging and tone all
excluded, and `opens-with-a-bare-id` rejected after measuring that all ten such
summaries were good. This row moves the line to where the ADR puts it.

## Measured before dispatch, on `main`

```
summary-missing          194 records (12 of them open rows)
summary-repeats-title      0
summary-has-no-sentence    0
summary-is-a-fragment      0
```

**The two rules being removed currently catch nothing** — all 129 existing
summaries pass them. So this change is behaviour-neutral on today's corpus, and
what changes is only what `perry-task add` and `perry-task summary` will refuse
from now on. Re-derive those four numbers yourself; if any is non-zero, say so,
because it changes what the removal costs.

**Note the argument order**: the signature is `summary_shape(title, summary)`.
The PMO called it reversed while measuring and got four nonsense figures before
noticing. Check yours.

## The coupling that must not be broken

`summary-repeats-title` — **which stays** — currently uses both
`summary_tokens` and `SUMMARY_MIN_WORDS` in its prefix arm:

```python
added = abs(summary_tokens(fs) - summary_tokens(ft))
if fs == ft or ((fs.startswith(ft) or ft.startswith(fs))
                and added < SUMMARY_MIN_WORDS):
```

So **deleting `SUMMARY_MIN_WORDS` and `summary_tokens` outright would break a
rule this row keeps.** Either keep them as internal helpers of
`summary-repeats-title`, or re-express that arm without them — **your choice,
but say which and why**, and if they stay, their docstrings must stop
presenting them as a general "how long should a summary be" facility, because
that is the thing being removed.

## Files in scope

- `bin/lib/__init__.py` — `summary_shape`, its docstring's rule list and its `NOT CHECKED` list, and the fate of `SUMMARY_MIN_WORDS` / `summary_tokens` / `_SUMMARY_SENTENCE`.
- `bin/perry-lint` — the two rule names in its help text at `:118-120`, and the `SUMMARY_MIN_WORDS` re-export at `:1756` if it becomes unused.
- `bin/perry-task` — the writer gate, which refuses on `summary_shape`'s output and must stop refusing on the two removed rules.
- `tests/test_summary_is_asked_for.py` and `tests/test_task_summary.py` — the assertions that pin the removed rules, and the corpus-agreement test between the two tools.

## Deliverable

The two language rules are gone from the predicate, from both tools' output,
and from the documented contract. `summary-missing` and
`summary-repeats-title` behave exactly as they do today.

The `NOT CHECKED` list in `summary_shape`'s docstring gains these two **with
the reason** — *the user decided on 2026-09-03 that prose quality is the writing
agent's responsibility, not a check's* — because that list is the record of
what this predicate deliberately declines, and a rule removed without a reason
reads as an oversight to the next author.

## Verification

1. **Before**: reproduce the four counts above on `main`.
2. **After**: `summary-missing` and `summary-repeats-title` produce byte-identical
   findings across all 323 records; the other two produce none because they no
   longer exist.
3. **The writer stops refusing.** `perry-task add --summary "Short."` — a
   summary that is both a fragment and, if you drop the full stop, sentence-less
   — is accepted. Show the refusal before and the acceptance after.
4. **The writer still refuses a missing summary**, and still refuses one that
   restates the title. A change that removes the gate entirely passes item 3 and
   is wrong.
5. **The two tools still agree.** `bin/perry-task` and `bin/perry-lint` share
   this predicate precisely so they cannot diverge; whatever test pins that
   agreement must still pass.
6. **Mutation**: revert the removal and show a named test go red. Anchor by line
   number *with an assert on the old text*; clear `__pycache__`; wait past the
   whole-second boundary. **Verify restores with `git show <ref>:<path>`,
   single-path only** — `bin/perry-restore-check` has an open FAIL on its
   multi-path interface (`TASK-256`). A green mutation is the finding.
7. Full suite no redder than the baseline **you measure**; `perry-lint --root .`
   at 0 errors.

## Bound

```
Enumeration: grep -rn "has-no-sentence\|is-a-fragment\|SUMMARY_MIN_WORDS\|summary_tokens\|_SUMMARY_SENTENCE" bin/ tests/
Size:        14 sites on this commit — bin/lib/__init__.py 9, bin/perry-lint 3,
             tests/test_summary_is_asked_for.py 1, plus the writer gate's call
Remainder:   `schema/task-list-contract.md`'s definition of the field is NOT in
             scope — it describes what a summary is FOR, not what is checked,
             and TASK-325 already argued the contract version does not move.
             If the round finds it does describe the removed rules, that is a
             finding to report, not a file to edit.
```

## Out of scope

- The 74 backfilled summaries and the coverage figure. Nothing is rewritten.
- `summary-missing` and `summary-repeats-title`.
- Any new check of any kind. This row only removes.
- The `## Bound` / escalation-gate prose-parsing question, which is `TASK-290`
  and `TASK-308` and is a different decision.
