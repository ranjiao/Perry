# TASK-421 — result

> Written incrementally and committed as it was produced, per the brief.
> Branch: `task-421-scratch-collisions`, cut from `70458893`.

## 0 · Conditions of this round

**Scratch path used.** `/private/tmp/claude-501/-Users-bytedance-proj-Perry/b59246e8-0d9c-4c63-9ac3-03f73fedf40b/scratchpad/task421-<pid>-<epoch>/`

**Why I believe it was private, and the part of that belief that is wrong.** The
parent — the directory this session was handed as "your scratchpad" — is *not*
private. It held **519 entries when I arrived**, with mtimes spanning 2026-09-09
to 2026-09-11, including `baseline.txt`, `mutate.py`, `merge368.log`, and a
`probe.py` last written at **13:31-13:37 today**. That `probe.py` is the
TASK-368 collision described in the brief, still sitting there. So the directory
advertised as session-private is shared in fact, and I confirmed it by listing
it rather than by trusting its name.

What is private is the **leaf** I created inside it, whose name carries my
shell's pid and an epoch second. That is uniqueness by *my* good behaviour —
exactly the mechanism this row exists to say does not work. **I am the sixth
agent told to pick a careful name, and the reason I did not collide is that I
picked one, not that I could not.** That is the finding, not the mitigation.

**Suite baseline, measured in this worktree, at `70458893`, before any edit:**

```
2 of 124 MODULE(S) red
3 of 3578 TEST(S) failed
```

- `test_contract_key_parity` — 2 of 35. Data-dependent on the live board
  (recorded 2026-08-30 in the journal).
- `test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale` — 1 of 49.
  Clock-dependent.

Neither is mine and neither is touched by this row. Two other agents (TASK-436,
TASK-431) were running concurrently; this baseline was taken in my own tree, not
in the primary checkout.
