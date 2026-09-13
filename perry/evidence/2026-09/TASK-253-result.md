# TASK-253 — the last rootless hand-back, and the guard that could not see it

**Rung:** V3 — a reproducible run: command, inputs, output, re-runnable.

This row sat at `review` carrying `evidence: —` and **no document of any kind**,
while its `Next action` cell said *"the mutation table and the negative control
are in the evidence"*. That sentence was false when it was written. This file is
the run it promised, and `perry-lint --reviews § review-with-no-run` is what
surfaced the gap.

---

## 0. Where the row actually stood

The row has two halves and its own summary says so.

| half | state before this run |
|---|---|
| `perry-tasks` honours `--dry-run` | **done.** Fixed under TASK-361; V4 round 8 pinned it at 8 of 8 commands with a per-command control |
| every writer hand-back carries the root, and a test holds the count | **mostly done, and one site short** |

The original site (`bin/perry-migrate § _plan_task_store`) was deleted with
`perry-migrate` under USER-910, so the row was re-scoped to the category:
`lib.root_flag` exists, `tests/test_handed_back_root.py` holds the rule, and
four of the five `perry-lint` sites the summary names were already rooted.

## 1. The site that was left, measured

```
$ grep -n "render --write" bin/perry-lint bin/perry_md_store.py
bin/perry_md_store.py:1703:  `{tool} render --write{lib.root_flag(root)}`     rooted
bin/perry-lint:3966:         `perry-tasks render --write{_r}`                 rooted
bin/perry-lint:4107:         `perry-tasks risks-render --write{_r}`           rooted
bin/perry-lint:4254:         `perry-tasks intake-render --write{_r}`          rooted
bin/perry-lint:4382:         `perry-tasks asks-render --write{_r}`            rooted
bin/perry-lint:4715:         `perry-{doc.name} render --write`                BARE
```

`check_md_store_drift` prints **two** writer commands and neither carried a
root, while `project_root` sat in that function's own signature. The second,
`perry-{doc.name} write --from-file`, *"DISCARDS the stored values"* by its own
message — so the harm is worse than the one the row was opened on, in the tool
a reader runs when something is already wrong.

Fixed the way its four siblings already were: `_r = lib.root_flag(project_root)`
once, pasted into both commands.

## 2. THE GUARD DID NOT SEE THE FIX, AND THE MUTATION IS HOW I FOUND OUT

After the fix I took the root back off both commands and ran the module.

```
=== M1: take the root back off both hand-backs ===
Ran 22 tests in 4.813s
OK                                              ← GREEN
```

**A green mutation is the finding.** The guard whose whole subject is "every
writer hand-back carries the root" could not see either of these hand-backs,
which means the fix above was unverified and the count beside it was over a
population two smaller than it claimed.

### Why

`phrase_pattern`'s head is `perry-[a-z][a-z-]*`. It cannot match
`perry-{doc.name}`, because `{` is not in `[a-z-]`. **The tool name is itself a
format field**, and that whole shape was outside the population.

The alias mechanism does not rescue it. `tool_aliases` reads
`tool = f"perry-{doc.name}"` and `bin/perry_md_store.py` does bind that name —
but `bin/perry-lint` interpolates inline with no variable, and
`tool_aliases(tree)` returns the **empty set** for that file, measured.

### The fix, and the count that proves it

The head pattern now accepts a format field, and the tool half is expanded the
same way the subcommand half already was — the module's own rule, *"a writer iff
something matches and everything that matches writes"*, applied one token to the
left.

```
AssertionError: 64 != 66 : the number of paste-able writer command phrases in
bin/ has changed.
```

The held count caught the widening, which is what it is for, and the two rows it
gained are exactly the two sites:

```
bin/perry-lint 4721 rooted=True 'perry-{doc.name} render --write'
bin/perry-lint 4721 rooted=True 'perry-{doc.name} write --from-file'
```

`PASTEABLE_WRITER_PHRASES` goes 64 → 66. The rise is the **reader widening**,
not new hand-backs being written, and the comment above the constant says so.

## 3. A second defect, third occurrence, fixed rather than re-pinned

Adding eight lines to `bin/perry-lint` reddened
`test_every_call_to_one_of_them_passes_a_real_flag` over a call this change
never touched. `NO_ROOT_TO_GIVE` is keyed by **line number**, so every edit
above an exemption moves the exemption off its target.

The comment above the table already recorded two occurrences on 2026-09-12
(5714 → 5778, then → 5778 again) and proposed a fix: *"re-keying it on the
enclosing function is a row of its own."*

**That proposed fix would not have worked.** Both `check_file` call sites are
inside `main` — `:5786` for the templates and `:5827` for a real project — so
the enclosing function does not tell them apart, and an exemption keyed on it
would have excused the **rooted** call too. That is the silent direction of this
failure and the reason it is worth fixing rather than re-pinning: a coordinate
that drifts reddens loudly, but an exemption matching the wrong call passes
quietly.

Re-keyed on the call's own source, `ast.unparse(node)`. Stable under every edit
above it, it names the distinguishing fact out loud (`is_template=True`), and it
stops matching the moment the call itself changes — which is exactly when a
human should look again.

**And the table had no anti-vacuity control.** `MENTIONS` has had
`test_every_mention_still_names_something` since it was written;
`NO_ROOT_TO_GIVE` had nothing, which is why its three drifts each cost a suite
run to diagnose. `test_every_exemption_still_matches_a_real_call` is that
control.

## 4. Mutations — four, none green

`__pycache__` cleared before every run; restores verified against the file on
disk and the working diff.

| # | mutation | result |
|---|---|---|
| M1 | take the root off both `check_md_store_drift` hand-backs | **RED** — `test_no_pasteable_writer_is_handed_back_without_the_root` (**this mutation was GREEN before § 2's fix, and that green is this run's main finding**) |
| M2 | revert the head pattern, keep the root | **RED** — `test_the_count_of_pasteable_writer_hand_backs_is_held` |
| M3 | key `NO_ROOT_TO_GIVE` on `node.lineno` again | **RED** — `test_every_call_to_one_of_them_passes_a_real_flag` |
| M4 | make the exemption entry stale (`is_template=False`) | **RED** — 2 tests, including the new control |

Module: 22 tests, all green.

## 5. What is NOT closed, and why the row is not done

`tests/sweep_handed_back_commands.py` — the diagnostic a human runs by hand — is
a **second, divergent implementation of the same rule**, and its `ROOT` regex
knows `{r}`, `{_root_flag(...)}` and a literal `--root`. It does not know `{_r}`,
`{root_flag}` or `{lib.root_flag(...)}`, which are the spellings the tree
actually uses. Measured:

```
$ python3 tests/sweep_handed_back_commands.py bin/perry-lint bin/perry-task \
      bin/perry-goals bin/perry-state bin/perry_md_store.py
28 handed-back command(s), 145 mention(s);
12 handed back without the caller's root, 26 interpolating a value raw
```

Most of those 12 are false: `perry-tasks render --write{_r}` is reported as
*"no root"* while `{_r}` **is** the root flag. So the script and
`tests/handed_back.py` disagree about the same rule, and the stale one is the
one a human reads. That is this board's recurring shape — one rule with several
enforcement points — and it is the remaining work on this row, not something
this run closed.

Also not closed: run with no arguments the sweep prints
`0 handed-back command(s) … 0 handed back without the caller's root`, which
reads as a clean bill of health for a run that examined nothing.

## 6. Suite

Full run, `tests/run`:

```
130 modules · 3777 tests · 134.9s · 8 workers
✗ 2 of 130 MODULE(S) red
✗ 3 of 3777 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three reds are the session's standing ones, none in a module this change
touches: two conformance-witness keys in `test_contract_key_parity`, and the
clock-dependent `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`.
