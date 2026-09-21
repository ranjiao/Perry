# Standing constraints for a review agent

Read by every V4 round (`review.md § 2`). It is referenced by path rather than
pasted into the prompt on purpose: a constraint list retyped per round is a
constraint list that loses an entry per round, and the entry it loses is the one
nobody remembered to retype.

A project adds its own on top via `.perry/hook.md` (`extending.md`) — machine
paths, snapshot locations, and "never touch X" rules belong there, not here.

## You are a reader

**Do not modify the project under review.** Not to fix what you find, not to
add a test that proves your point, not to "just try" a change. A reviewer that
writes has altered the thing it is judging, and its verdict now describes a
state that never existed.

To verify something destructively — a migration, a refusal, a crash path — copy
the project to a scratch directory and work there. Say in `checked:` that you
worked on a copy.

**This includes planting a file to test a guard.** "Add a reader that breaks
the rule and check the guard reports it" is the right test and it is still a
write: for the seconds it exists, the shared checkout has a file that makes
that guard legitimately red, and anything else running the suite — the author's
own gate, another reviewer — sees a failure that is real, reproducible-looking,
and about nothing. **Plant into a copy.** Learned by planting into the live
tree while five other rounds and a full-suite gate were running against it, and
watching a correct guard report a defect that did not exist.

## The repository is live

Other work is in the tree, including uncommitted work you cannot see the
purpose of. **And other work is in the process table**, including runs started
by sessions you cannot enumerate.

- **Never `git checkout`, `git stash`, `git reset`, or `git clean`.** Each one
  can destroy work that is not yours and not recoverable.
- **Never `pkill`, `killall`, or `kill -9`.** A pattern kill cannot tell your
  process from someone else's, and you cannot see who else is working. To stop
  something you started, stop it by its own job or pid — never by a pattern.
- Reading history is fine: `git log`, `git diff`, `git show`.
- Do not commit, push, or open a PR. The round's output is a verdict.

The signal bullet is the same argument as the `git checkout` bullet, one layer
down: both are commands whose blast radius is the machine rather than the thing
you aimed them at. On 2026-09-10 an agent that saw an unexpected tree name in
its own output ran `pkill -f 'tests/run'`; a sibling agent's log shows
`Terminated: 15`, and seven peer sessions were open at the time. **Seeing a
result you cannot explain is a reason to stop and read, not a reason to
signal** — the wrong output was a shared-path collision, and killing processes
could not have fixed it.

## Your scratch files are yours alone

A round writes harnesses, mutant tables and captured output. **Put them under
the one scratch derivation Perry has: `$PERRY_HOME/work/reference/dispatch.md §
The tree the agent works in`, the block headed `perry-scratch-derivation`.**
Re-derive it in each command rather than remembering a name. Its uniqueness
comes from the worktree directory, not from anything you add, which is why it
survives across commands and a log path you report is still there when someone
opens it.

There is deliberately no second recipe on this page. The first version of this
section had one, built from `git rev-parse --short HEAD` and `$$`: both are
contributed by the caller, which is the thing that block says must not be the
mechanism, and `$$` changes on every shell invocation — so the log path the next
section promises would not have survived to the next command. It was a second
spelling of a byte-pinned rule, marked *do not edit without re-reading
TASK-421*, and the V4 round caught it (TASK-472).

Two incidents, one shape. The `pkill` incident above began as "an unexpected
tree name in its own output", which was a **shared-path collision**. On
2026-09-20 it happened again with no signal sent: two review rounds ran
concurrently, the second overwrote the first's harness in a shared scratch
directory **while a mutant was live in the tree**, and the first round only
knew because it restored from `git show` and checked. Nothing escaped, and
nothing about the collision was visible in either round's own output.

A mutation round is the worst case for this: between planting and restoring,
the tree is deliberately wrong, and a harness that changes underneath you can
make a survivor look like a kill or the reverse.

## Batch what is independent; sequence what is not

**Reads that do not depend on each other go out together**, in one turn:
listing files, reading several pages, running two unrelated read-only commands.
Doing them one per turn costs a full turn each for no information the previous
one supplied.

**Everything with an order stays in order**: a mutation and the run that tests
it, a restore and the check that verifies it, a write and the read that
confirms it, anything that needs someone's approval first. Batching those does
not save a turn — it produces a result you cannot attribute, because you no
longer know which state the check saw.

The test is one question: *does this step need the output of that one?* If not,
batch them. If so, do not, however much faster it would look.

## Report what failed, in full

**Never discard failing output.** A harness that keeps stdout on success and
drops it on failure is worse than one that keeps nothing: it is silent exactly
when you need it, and the round pays for the information twice — once by not
having it, once by re-running to get it back. On 2026-09-20 a round lost two
mutants' output this way and needed three isolated re-runs to recover what one
capture would have held.

- **Success**: the status line and the evidence paths. Not the whole log.
- **Failure**: the exit code, enough of the diagnostic to act on, and the path
  to the full log — which still exists.
- **Structured output**: filter it *structurally* (`--json` into a parser) or
  keep it whole. **Never feed a truncated JSON document back as if it were a
  valid one**; a half-parsed contract is a wrong answer wearing a schema.

## Let the host tell you it finished

A suite run, a mutation loop or a build is long. **If the host tracks
background work and notifies on completion, start it that way and wait for the
notification.** Launching the same command with a bare `&` opts out of the
notification you would otherwise have been given, and the round then pays for
it with a polling loop it wrote by hand.

Where no completion event exists, poll with a **bounded** loop and a delay
matched to how long the work actually takes — not a fixed one-second tick.
Record how many calls you made and how long you waited; that number is part of
the round's cost.

Do not build a scheduler, and do not report a tool-call count as if it were a
model-turn count. They are different quantities and only one of them is what a
round costs.

## Do not run the write side against what you are reviewing

A Perry tool that writes — `perry-task`, `perry-goals`, `perry-decide` —
changes board rows, journal lines and the event log. Running one against the project under review injects
your own events into the history you are checking.

Read tools are safe and are the point: `perry-task list --json`,
`perry-state --json`, `perry-lint`.

**Never run `setup`.** Its `sweep_legacy_links` step removes symlinks under the
host's skills directory, and on a developer machine those are real installs.

## Verify a restore against an independent source

A mutation round (`review.md § 2`, rule 2) ends by putting the file back.
**Verify that restore against `git show <ref>:<path>` — never against the bytes
your own harness snapshotted.**

```python
TRUE = subprocess.run(["git", "-C", root, "show", f"{REF}:{REL}"],
                      capture_output=True, check=True).stdout   # independent
...
f.write_bytes(BASE[0])                                          # restore
assert f.read_bytes() == TRUE                                   # verify
```

The reason, because a rule with no reason attached gets reverted by the next
author: this project prescribed `BASE = (f.read_bytes(), md5(f))` before the
mutation and `assert md5(f) == BASE[1]` after the restore, and **that assertion
cannot fail when the write succeeds** — `BASE[1]` is the digest of `BASE[0]`,
and `BASE[0]` is what was just written back. It verifies that the write
happened, not that the file is right. So a file already carrying a mutation
when your harness started is restored *to that mutation* and reported OK:

```
                     old check | new check | actual file state
honest restore     :      True |      True | file is ORIGINAL
corrupted baseline :      True |     False | file is ALREADY-WRONG
```

Not hypothetical. `TASK-325` found `bin/perry-task` already mutated at a point
before its harness had run and could not account for how; every round that
restored onto a baseline like that reported OK without checking anything.

`bin/perry-restore-check <ref> <path> …` does exactly this, exits non-zero if
**any** of the paths differs, and refuses to answer unless its own bytes have
been *shown* to match the copy committed in its repository — including when
there is no committed copy to compare against, which is the case in a `git
archive` scratch copy and is the more dangerous one, not the safer. Pass
`--allow-modified-self` to override, and mean it — but from a scratch copy the
better move is usually to point the **live** repository's helper at the copy
with `--root <copy>`, which answers correctly and needs no override. Use it or
hand-roll it — but the comparison is against the ref either way.

## Do not mint identifiers

Example IDs written into a state file become dangling references the next lint
run reports as real (`LOAD-02`). Use placeholders — `<TASK-ID>`, `TASK-0NN` —
in anything that lands in a file or in your report.

## Report the blocker; do not route around it

If a constraint stops you from checking something, that goes in `not-checked:`
with the reason. A round that quietly substitutes a weaker check for the one it
could not run produces a PASS that means nothing, and nobody downstream can
tell which kind of PASS they got.
