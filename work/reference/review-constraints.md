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

## Verify a restore against an independent source

A mutation round (`review.md § 2 rule 2`) ends by putting the file back.
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

`bin/perry-restore-check <ref> <path> …` does exactly this, exits non-zero on a
mismatch, and refuses to answer while its own bytes differ from the copy
committed in its repository. Use it or hand-roll it — but the comparison is
against the ref either way.

## Do not mint identifiers

Example IDs written into a state file become dangling references the next lint
run reports as real (`LOAD-02`). Use placeholders — `<TASK-ID>`, `TASK-0NN` —
in anything that lands in a file or in your report.

## Report the blocker; do not route around it

If a constraint stops you from checking something, that goes in `not-checked:`
with the reason. A round that quietly substitutes a weaker check for the one it
could not run produces a PASS that means nothing, and nobody downstream can
tell which kind of PASS they got.
