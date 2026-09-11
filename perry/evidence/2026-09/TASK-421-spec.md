# TASK-421 — spec

> Design: none. `work/reference/review-constraints.md` is the document this row
> extends, and the dispatch prompts are the other half
> Dispatch mode: manual
> Executor: claude-subagent — but see "What it must not do" item 1: this row is
> about agents colliding, and running it carelessly is the defect
> Estimated cycle: small for the constraint, medium for the isolation
> Subjective verification: where a private scratch path comes from, and whether
> a prompt can be trusted to carry it
> Touches architecture: the dispatch path
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P1 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

On 2026-09-10 an agent drafting four specs redirected a baseline to
`scratchpad/baseline.txt` while a sibling agent in `scratchpad/fixA` was
writing the same path. Seeing the wrong tree name in the output, it ran
`pkill -f 'tests/run'`. `fixA`'s log shows `Terminated: 15`.

**It is known only because the agent that did it reported itself.** Nothing in
the tooling would have surfaced it, and the sibling would have seen a run that
died for no reason.

**The blast radius was wider than the agent knew.** `ListAgents` showed seven
interactive peer sessions on this machine at the time, two of them other Perry
sessions. A pattern kill on `tests/run` reaches every session's suite, not just
this one's subagents.

**Fourth collision of one root cause in two days.** V4 round 4's `r4b` and `r4c`
both wrote `scratchpad/baseline.txt` and one clobbered the other mid-run; round
5 the same; round 6 the same; and then a clobber that escalated into a process
kill. Three times it cost a re-measurement. The fourth time it cost another
agent's work.

## The two fixes are different sizes and the second is the row

**(1) The constraint, which is cheap.**
`work/reference/review-constraints.md § "The repository is live"` already
forbids `git checkout`, `stash`, `reset` and `clean` by name, with the reason
that each can destroy work that is not yours and not recoverable. **It says
nothing about signals.** The reasoning transfers verbatim. Add `pkill`,
`killall` and `kill -9`, with the reason stated: on a shared machine a pattern
kill cannot tell your process from someone else's, and the agent running one
cannot see who else is working.

**(2) The dispatch side, which is the actual root cause.** Every prompt in that
session handed out one scratchpad directory and told the agent to namespace
inside it. **That is advice, not isolation**, and it failed four times in two
days with four different agents who were each told the same thing. A private
path per agent removes the collision instead of asking the fifth agent to
remember.

A fix that only does (1) leaves the thing that caused all four collisions in
place. A fix that only does (2) leaves the escalation path open.

## Files in scope

- `work/reference/review-constraints.md` — fix (1).
- Whatever constructs a dispatched agent's prompt and its working paths — fix
  (2). **Find it rather than assuming**; the report names it.
- `work/reference/dispatch.md` and the other files that tell an agent where to
  work, read and changed as the sweep requires.
- `tests/` — where the guard lands, if the answer admits one.
- `perry/evidence/2026-09/TASK-421-result.md` — written.

## Bound

```
Commit:      fe0292fb
Enumeration: every place a dispatched agent is told where to put a scratch
             file. DERIVE the set — search the reference documents and the
             dispatch path for the scratchpad directory and for instructions to
             namespace within it
Size:        state the number. Four known collisions came through it
Also:        every destructive-command prohibition already written down, so the
             new ones are added in one place and phrased like their neighbours,
             not appended in a second list somewhere else
Last element: the lowest-precedence document that still tells an agent a path
```

## Deliverable

1. The signal prohibition, in the file that already carries the others, phrased
   with its reason the way they are.
2. A private scratch path per dispatched agent, such that two agents dispatched
   at the same time cannot write the same file **without being told to be
   careful**.
3. `perry/evidence/2026-09/TASK-421-result.md`: the sweep, both fixes, and a
   demonstration that two concurrently dispatched agents now get different
   paths.

## What it must not do

1. **It must not run a pattern kill, at any point, for any reason.** Including
   while testing this row. If a demonstration seems to need one, that is the
   finding; write it down instead.
2. **It must not make the isolation advisory.** "Tell the agent to use a
   unique name" is what failed four times. If the honest answer is that only
   advice is possible, say so and explain why, and then make the advice
   impossible to miss rather than one line among many.
3. **It must not touch `/Users/bytedance/proj/Perry`.** Another session writes
   there, which is this row's whole subject.
4. **It must not silence the symptom** by making a clobbered file non-fatal. A
   baseline overwritten mid-run must still be loud.

## Verification

1. **Two agents, two paths, shown.** Construct the concurrent case and print
   both paths. If they can still collide, say under what conditions.
2. **The four historical collisions, replayed against the fix.** `r4b`/`r4c`,
   round 5, round 6 and the 2026-09-10 one. State for each whether the fix
   prevents it. A fix that prevents three of four is a partial fix and must say
   which one it misses.
3. **The constraint is where the others are**, reads like them, and carries its
   reason. Quote the neighbouring bullets and the new one together.
4. **Mutation.** Revert the isolation and show a named test go red, if the fix
   admits a test. If it does not — a documentation-only fix cannot be mutated —
   say so plainly rather than inventing a test that passes on both sides.
5. **Say what a fifth collision would look like** after this row, and whether
   anything would report it.

## Out of scope

- The four past collisions' lost measurements.
- Agent worktree isolation, which is a separate mechanism and already works.
- Anything about other sessions' processes beyond not signalling them.
