# TASK-156 — a linkage edge to a task no record carries is now a finding

**From `coding/task-156` @ `8d7eb36`.** Rung **V3**. A fifth code in the family,
`linkage-task-exists`, 16 tests in five classes, every case built in a temp
project and read through the real `--root` seam.

## The spec was wrong twice and the agent followed the code

### 1. "The case cannot be produced by any writer" — it can

I wrote that `perry-goals link` *"presumably will not write an edge to a row it
cannot resolve"*. **Presumably** was doing the work, and it was wrong.
`link_edge` resolves and double-checks the **KR** half and asks nothing at all
about the task id.

Measured, and pinned as an executable test rather than a sentence:

```
perry-goals link TASK-999 P-O1.1   (store holds neither)
  → returns 0
  → appends the edge
  → bumps `updated`
  → signs off with "↪ validate: perry-lint --root ."
     — which had nothing to say about it
```

`test_link_writes_the_edge_and_the_lint_then_reports_it` **passes** — it does not
skip. The shipped writer produces this state today, and then recommends the
check that was blind to it.

**The pin skips rather than fails** the day `perry-goals link` grows that check,
turning into an assertion that the refusal names the id. That is the right shape:
a test that would otherwise start failing for a *good* reason.

So the row was not the hypothetical I described. It closes a hole the writer can
walk through, with the writer's own success message pointing at the tool that
could not see it.

### 2. "Nothing proves a task the graph names exists" — true of lint, not of the toolchain

`perry-diagnose`'s `user_load.dangling` notices *some* of these. It asks a
different question — **is this id defined in the markdown** — and the two answers
come apart on the most ordinary case in this repository:

> a `done` row leaves `BOARD.md` and stays in the store (ADR-007)

I checked this independently before merging: `TASK-145` and `TASK-175` are both
`done`, both present in `perry/tasks.jsonl`, and both **absent from `BOARD.md`**.
A markdown-defined check calls such a row undefined.

**That is why the comparand here is the store and not the board**, and the case
is pinned. The diagnose-side defect is latent on this repository today — the
dangling list holds five ids and none is a store record — so it was correctly
left untouched and named rather than fixed.

## The three decisions, as stated

**1 · Severity `warn`**, matching `linkage-kr-exists`. Two arguments, and the
second is the better one: an `error` in this tool asserts a file is
**malformed**, and the register is well-formed — its referent is absent, which
can be benign (an id typed for a row not yet opened). Splitting the severities
would also say the KR half of an edge matters more than the half
`kr_progress_provenance` actually counts. `--strict` still promotes it, asserted.

**2 · No task store ⇒ the sweep does not run.** It reads the contract
`viewer/parsers.py § load_task_store` already states — `None` is *not adopted*,
`[]` is *adopted and empty* — instead of inventing a rule. **Reading absence as
an empty id set is TASK-117's inversion one check over**, and TASK-117 is the row
where `perry-lint` called 175 of 175 rows drifted because the log was missing.

An **unreadable** store gets the same skip: `store-unreadable` already says why,
and deriving N findings from that one fact is the noise it exists to avoid. An
**empty** store is a different case and its edges *are* reported — that boundary
has its own test.

**3 · An old phase IS judged against today's store**, and `perry-lint:1082`'s
reasoning does **not** transfer. The distinction is exact: a **KR id is
phase-scoped** — `P-O1.1` names different KRs in `001` and `002` — which is
precisely why that guard had to re-derive its comparand per file. A **task id is
global**: one `tasks.jsonl`, ids minted across phases, no per-phase store to
prefer.

The consequence is deliberate and points at the row running beside this one: **a
row TASK-167's removal path takes out makes a scored phase's edge dangle —
correctly.**

## Mutation proof

| mutation | reddens |
|---|---|
| guard deleted | **9** tests (7 failures + 2 errors) |
| `None` read as an empty id set | **4**, all in `TestNoStoreIsSilent` |
| old registers exempted | **1** — `test_a_scored_phases_edge_to_a_removed_row_is_reported` |

Each decision has a mutation that reddens only it. The second and third rows are
what stop decisions 2 and 3 from being prose.

## On this repository

`perry-lint` before and after: **`0 error(s), 3 warning(s)`, `176 record(s), 0
row(s) drifted`, rc 0 — identical.**

**And not vacuous**: it evaluates all **31** ids (18 in `001-linkage.md`, 13 in
`002-linkage.md`) against 176 records, and all 31 resolve. The spec's trap —
a check that reads the project around it as its expected value — is avoided by
construction: the guard's own correctness is proved in tmp projects, and this
repository is only evidence that it is quiet when it should be.

## Fixtures: it declined the one I suggested, with a reason

I pointed it at `tests/fixtures/witness-project/`. It used tmp projects instead,
because **`witness-project` can hold at most one of the three cases** — it has a
store, so the no-store case is impossible inside it — and its README forbids
editing its findings. It followed the sibling guard's own suite
(`test_cadence § TestLinkageBelongsToItsOwnPhase`).

Each tmp fixture is authored complete enough to **lint at 0 errors**, which is
what makes *"the finding did not refuse the lint"* and *"`--strict` promotes it"*
observable at all. A fixture that already errors cannot show either.

## One thing left undone, deliberately

`bin/perry-migrate § CROSS_FILE_INPUTS` mirrors only `phase`, `design` and
`BOARD.md` into its scratch tree, so `check_cross_file` sees no store there and
this check declines in the dry run's newly-visible delta. **That is decision 2
behaving correctly on a tree that genuinely has no store** — and it costs a
newly-visible finding a migration could otherwise surface. Adding `"tasks.jsonl"`
to that tuple is a one-word fix in a file this row does not own. Filed.
