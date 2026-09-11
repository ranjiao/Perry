# TASK-411, TASK-412, TASK-419, TASK-431 — round 1, V4

> Reviewer: fresh context. Did not write any of this code.
> Branch: `v4-round-411-412-419-431`, from `main` at `076ae21a`.
> Worktree: `.claude/worktrees/agent-a4cba585579eac7c4`
> Scratch: `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/v4quad-411-412-419-431/`
> (agent-suffixed path nobody else would pick; a full `git clone` of the
> worktree lives under it as `clone/` and every destructive check runs there,
> `review-constraints.md § You are a reader`)
> Written incrementally and committed as each section was measured.

All four rows are the same question — **a guard was added; does it bite?** —
and that is the question this document answers, four times.

## 0 · Baseline, taken in this tree before anything else

`bash tests/run` at `076ae21a`, no edits in the tree, `git status` clean:

```
126 modules · 3655 tests · 165.8s · 8 workers
✗ 4 tests failed
    test_contract_key_parity.TestAWitnessProjectMakesAnEmptyCollectionObservable
        .test_without_the_witness_the_four_are_unobservable
    test_contract_key_parity.TestTheWitnessedKeysRedden
        .test_the_same_mutation_is_silent_without_the_witness
    test_diagnose.TestUserLoadFindings.test_perry_itself_passes_its_own_id_checks
    test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale
0. tree guard — nothing under the worktree moved
```

**All four of the declared known reds fired here**, including
`test_diagnose`'s, which TASK-412's and TASK-431's results both record as
*green* in their trees. That difference is explained and is not a finding for
either row: the diagnose red is `user_load.dangling ==
['USER-920', 'V4-1', 'V4-2', 'V4-3']`, and the three `V4-N` tokens are minted
identifiers in `perry/evidence/2026-08/TASK-027-round4-review.md` and
`-round5-`, which are on `main` and were not on either agent's branch base.
They belong to TASK-436's territory, not to any row in this round.

So the bar for "this reviewer broke nothing" is: exactly these four.

### How every mutation below was run

`…/scratchpad/v4quad-411-412-419-431/mutate.py`, against the **clone**, never
this worktree. It anchors by line number *and* a substring that must occur
exactly once on that line, refusing rather than mutating otherwise; clears
`__pycache__` and sleeps 1.2 s past the whole-second boundary either side;
restores by writing back the bytes of `git show HEAD:<path>` — not the bytes it
snapshotted; and verifies with `bin/perry-restore-check`. It also refuses to
start if the file already differs from the ref, so a corrupted baseline cannot
be restored onto and reported OK. **Every mutation below ended
`restore-check rc=0`.**

## 1 · TASK-412 — the page's own block is what the tests run now

### 1.1 · The repair is real, verified rather than believed

The result says its first mutation round came back green on two cases because
they recomputed `pair(a) > pair(b)` in the test instead of executing the page,
and that `commit d6b91201` repaired it with a `drive()` helper. **Verified at
the source, not from the claim.** `tests/test_contract_page_snippets.py:315`
`drive()` builds a synthetic payload, `exec`s
`compile(snippet(), …)` — where `snippet()` is the page's fenced text, read off
disk — and returns the block's own namespace together with whatever the block
actually passed to `warn`. Both repaired cases go through it, and
`test_the_drift_gate_is_a_ceiling_per_major_over_the_forward_space` asserts on
`ns["tested"]`, a value that exists only inside the block.

Then mutated. Seven, applied one at a time to the **page**, each reddening a
named test. Three are the result's own (a, c, d); **four are mine and none of
them appears in its table** (b, e, f, g):

| # | line | mutation | result |
|---|---|---|---|
| a | `:592` | the string compare restored at the call site — the exact case that was green in the first round | **RED** `test_the_filter_warns_about_exactly_the_entries_newer_than_the_pin`: `['1.2'…'1.9','2.0'] != ['2.0']` |
| **b** *(mine)* | `:592` | `> tested` → `>= tested`, an off-by-one nobody restored | **RED** same test, twice — `['1.18','2.0'] != ['2.0']` at pin 1.18 and `['2.0'] != []` at pin 2.0 |
| c | `:589` | the ceiling back across majors, `max(SUPPORTED.values())` | **RED** 6 failures, `(2,18) != (2,0)` |
| d | `:592` | `TESTED_MINOR_STR` restored — the name bound nowhere | **RED** 2 failures + 12 errors; `test_it_references_no_name_the_page_does_not_supply` names it directly |
| **e** *(mine)* | `:830` | the marker's *reason* changed to `I do not want to run it` | **RED** `test_a_marker_cannot_hide_a_broken_block`: *"gives a reason this module does not know how to check"* |
| **f** *(mine)* | `:111` | the payload block types `open` as `"3"` instead of `3` | **RED** `test_the_jsonc_blocks_describe_the_live_payload`: *"types `open` as str; the payload returns int"* |
| **g** *(mine)* | `:663` | a **seventh** fenced block inserted into live prose, carrying a marker the module does know | **RED** ×3 — the bounded count (`7 != 6`), the indent-aware-vs-naive case (`6 != 5`), *and* the no-runner-no-marker case, because the marker's position test correctly refused to excuse a block above `## Changelog` |

Mutation **b** is the one worth keeping: an off-by-one at the call site is what
a later author edits into this block, it is not in the result's table, and the
guard caught it in both directions. Mutation **e** is the answer to the
question the result invites — the `not-executable` reason is an *enumerated*
allowlist checked against the block's own position, not a string anybody can
write. Mutation **g** shows the count is a real bound and not decoration.

### 1.2 · What I could not shake

- The three green-by-construction cases the result names are exactly the three
  I found: `test_the_string_compare_is_wrong_on_this_very_space` is a
  description and says so in its own docstring; it stayed green under mutation
  a, as its docstring predicts. **An ungrudged green that announces itself is
  not a finding** — it is the honest label § 2 rule 2 asks for.
- 20 tests in the module, 20 green at `HEAD` in the clone before every
  mutation and after every restore.

### 1.3 · One finding, and it is not TASK-412's

`bin/perry-restore-check --root DIR` does **not** resolve a relative `<path>`
against `DIR`. It resolves it against the process cwd and then refuses,
printing *"The restore did NOT put the file back"* for a file that was in fact
correctly restored:

```
$ cd <scratch> && perry-restore-check --root <scratch>/clone HEAD schema/task-list-contract.md
The restore did NOT put the file back. Do not report this round's result until it does.
  ✗ <scratch>/schema/task-list-contract.md: … is not under <scratch>/clone
rc=1
```

Its own `--help` says `--root DIR  repository to resolve <path> and <ref>
against`. The wrong answer is **loud** — exit 1, and the message names both
paths — and it errs toward "your restore failed", which is the safe direction,
so by § 0 it fails no row. It is out of scope for all four rows here; I hit it
because `review-constraints.md` recommends exactly this invocation to a
reviewer working from a copy. Reported, not filed (see § 5).

*(sections follow as they are measured)*
