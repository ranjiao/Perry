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
purpose of.

- **Never `git checkout`, `git stash`, `git reset`, or `git clean`.** Each one
  can destroy work that is not yours and not recoverable.
- Reading history is fine: `git log`, `git diff`, `git show`.
- Do not commit, push, or open a PR. The round's output is a verdict.

## Do not run the write side against what you are reviewing

A Perry tool that writes — `perry-task`, `perry-goals`, `perry-decide` —
changes board rows, journal lines and the event log. Running one against the project under review injects
your own events into the history you are checking.

Read tools are safe and are the point: `perry-task list --json`,
`perry-state --json`, `perry-lint`.

**Never run `setup`.** Its `sweep_legacy_links` step removes symlinks under the
host's skills directory, and on a developer machine those are real installs.

## Do not mint identifiers

Example IDs written into a state file become dangling references the next lint
run reports as real (`LOAD-02`). Use placeholders — `<TASK-ID>`, `TASK-0NN` —
in anything that lands in a file or in your report.

## Report the blocker; do not route around it

If a constraint stops you from checking something, that goes in `not-checked:`
with the reason. A round that quietly substitutes a weaker check for the one it
could not run produces a PASS that means nothing, and nobody downstream can
tell which kind of PASS they got.
