# TASK-285 — spec

> Dispatch mode: manual
> Executor: manual (a procedure edit to Perry's own lane files; the PMO writes it)
> Estimated cycle: small
> Subjective verification: (none) — the rule is either in the file a reader sees, or it is not
> Touches architecture: (none) — Perry has no `ARCHITECTURE.md`
> Deployed: no

- **Owner**: PMO Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: unlinked

## Why this row exists

`work/reference/dispatch.md` tells a dispatched agent to work on a feature
branch and says **nothing at all** about tree isolation — measured 2026-09-03:
neither `worktree` nor `isolation` appears anywhere in the file. What it does
say, at `dispatch.md:55`, is *"Sub-agent shares parent cwd"*, stated as a
neutral fact about the executor.

It is not neutral. Observed twice:

1. **2026-09-02** — TASK-247 was dispatched as a `claude-subagent` instructed to
   create `coding/task-247-config-predicate`. The agent ran `checkout -b` in the
   shared working tree, so **the PMO's own checkout moved onto that branch**.
   Every PMO write afterwards — journal, evidence, board — committed there. A
   `git add -A` in the agent's commit would have swept two lanes into one code
   commit.
2. **2026-09-03** — the consequence surfaced: four V4 review documents (515 +
   329 + 528 + 69 lines) and 91 journal lines were on that branch and not on
   `main`, while `d146c15 Merge branch 'coding/task-247-config-predicate'` sat
   in `main`'s history and a commit message asserted *"main carries both round
   2s, and the report is live on it"*. True of the code, false of the records.
   Recovering it cost a merge and a verification pass.

`git-boundaries.md`'s whole premise is that one agent must not silently rewrite
another's lane. The isolation rule is what makes that premise true, and it was
never written down.

**The `Agent` tool supports `isolation: "worktree"`.** The capability existed
throughout; the procedure just never asked for it.

## The scope widened once, on a user decision taken 2026-09-03

The row was filed as "dispatch.md never says isolate". Writing that rule
surfaced a second contradiction in the same three files, and it is live rather
than cosmetic:

- `git-boundaries.md:17` — *"Coding Agent pushes a feature branch and opens a
  PR"*
- `delegate.md:159` — *"**Push the branch and open a PR**; provide PR URL in the
  RESULT block"*

Neither is what this project does. The PR round-trip was removed on 2026-08-21
because it put the user at a keyboard in the middle of every row; agent branches
have been merged locally since. And `git push`, `origin` and `publish` are on
`.perry/hook.md § High-stakes operations` under *"Publishing to a public repo"* —
`ranjiao/Perry` is public, so an agent following these two lines publishes.

**Asked and answered 2026-09-03.** Three options were put to the user: PR flow
with the V4 reviewer merging, PR flow with the user merging, or keeping the
local merge. **Answer: keep the local merge.** The reason it cannot be
delegated into the worktree was measured rather than assumed — a worktree cannot
merge into a `main` the primary checkout has checked out:

```
$ git checkout main                      # from the second worktree
fatal: 'main' is already used by worktree '.../wtprobe'
$ git push ../wtprobe HEAD:main
 ! [remote rejected] HEAD -> main (branch is currently checked out)
```

So the merge is the one code operation the primary checkout performs, and
"the primary checkout only maintains the Perry store" is true of everything
except that single `git merge --no-ff` per row.

## Files in scope

- `work/reference/dispatch.md` — the isolation rule, stated where the executor is chosen, replacing the bare *"Sub-agent shares parent cwd"*.
- `work/reference/git-boundaries.md` — the role table's premise, and the stale push/PR expectation in its Rules list.
- `work/reference/delegate.md` — the paste-back path's code-work block, same two corrections.
- `tests/test_spec_scannability.py` — the guard, alongside the existing `dispatch.md` text guards that already use `visible()`.

## Deliverable

**One rule, stated once and referenced twice**, so there is no second
authoritative copy to rot:

> A dispatched agent works in its own git worktree. The primary checkout is
> never switched by an agent; it merges the agent's branch afterwards, and that
> merge is the only code operation it performs.

- `dispatch.md` carries the rule and the reason, at the point where the executor
  is selected. `Sub-agent shares parent cwd` is corrected rather than deleted —
  it is true of the *process* and false as a licence for the *tree*.
- `git-boundaries.md` states it as the premise its role table depends on, and
  its Rules list stops instructing a push and a PR.
- `delegate.md` states it for the paste-back path, same correction.
- A named test in `tests/test_spec_scannability.py` that fails when the rule
  stops being visible in each file it must appear in.

## Bound

Written **before** the round, per `work/reference/review.md § 1`. Without it
this round inherits TASK-067's failure — the criterion "the rule is stated
where it needs to be" is a universal negative over a growing set of files.

```
Enumeration: grep -l "The tree the agent works in" work/reference/*.md
Size:        3 on this commit — dispatch.md defines the rule;
             git-boundaries.md and delegate.md reference it
Remainder:   work/reference/autopilot.md dispatches rows and carries NO copy.
             Out of scope, and deliberately: autopilot.md:218 runs "the full
             /pmo dispatch flow (see dispatch.md)", so it inherits the rule by
             reference. A fourth copy would be this project's own
             "N implementations of one rule" defect.
```

Two further bounds, both finite and both countable today:

```
Guard:       tests/test_spec_scannability.py::TestTheAgentGetsItsOwnTree
Size:        13 tests   (7 at filing; 11 after round 3; 13 after round 4 —
             updated 2026-09-04, per the round-3 V4 review's second cosmetic
             note: the bound was the thing that was supposed to be countable)
Mutations:   9 named mutations at filing; 19 planted in round 4, each with a
             stated anchor AND an assertion on the old text at that line; the
             round may re-run them and must treat any GREEN as a finding
```

**Round 4 changed the guard's shape, and the bound with it.** Rounds 1–3
enumerated the regions to pin; the V4 review showed the enumeration is the
defect, because a retraction inserted *beside* a pinned region touches nothing
in it. What is countable now is the complement:

```
Enumeration: three contiguous governed spans, pinned as
             (span minus its declared free rationale blocks)
Size:        dispatch.md   § The tree … → § Executor: opencode-subagent
                           86 lines, 4,121 chars pinned, 1,150 declared free
             git-boundaries.md § Git Role Boundaries → § Time Estimation
                           26 lines, all pinned
             delegate.md   § Required fields … → § Role ≠ executor
                           39 lines, all pinned
Remainder:   exactly one free block, at the tail of `dispatch.md`'s section
             under `### Why it is a rule and not a preference`. It is bytes
             this suite does not read, by `USER-914`'s decision, and no test
             can tell an improved explanation there from a retraction.
```

A K+1th file that should carry the rule is **a new row, not a re-opening of
this one**.

## Verification

1. `worktree` and `isolation` appear in `work/reference/dispatch.md`, in the
   executor section, and a reader who reads only that section learns to pass
   `isolation: "worktree"`.
2. The new guard is **mutated**: delete the rule from each of the three files in
   turn and show the named test goes RED each time; restore and show it GREEN.
   A guard that cannot go red is the finding, not a formality.
3. The guard uses `visible()`, so commenting the rule out — including with an
   **unclosed** `<!--`, which is the mutation that caught this project's guards
   twice — reddens it rather than leaving it green.
4. No file in `work/reference/` still instructs an agent to push or open a PR
   as the default path. Grep is the check, and the assertion is a NOT-in.
5. `python3 tests/parallel -j 4` no redder than the pre-change baseline.
6. `python3 bin/perry-lint --root .` at 0 errors.

## Out of scope

- **The code-fence hole.** A rule inside a fenced block is invisible to a reader
  in the way a comment is, and `visible()` does not strip fences. That is
  `TASK-318`, already filed, and fixing it here would fix one guard rather than
  the class.
- Changing `bin/perry-dispatch-limit`, the executor enum, or anything that
  allocates slots. This row writes a procedure, not a mechanism.
- Pushing the 99 unpushed commits, or any change to what `.perry/hook.md`
  escalates. The local-merge answer leaves both untouched, which is most of why
  it was chosen.
- Retroactively re-isolating any branch already on disk.
