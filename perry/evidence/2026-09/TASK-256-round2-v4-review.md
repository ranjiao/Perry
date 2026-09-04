# TASK-256 — round 2, V4 review

> Reviewer: dispatched review agent (fresh context; did not write this change)
> Criteria: `perry/evidence/2026-09/TASK-256-spec.md` — the only authority
> Answering: `perry/evidence/2026-09/TASK-256-round2-result.md`
> Under review: `main` at `651a5ca`
> Result: NOT YET CHECKED

## 0. Checkout provenance

NOT YET CHECKED

## 1. Re-planting the round-1 FAIL

NOT YET CHECKED

## 2. The second half — `unverifiable`

NOT YET CHECKED

## 2b. FINDING — a ninth mutation comes back GREEN, and it reopens the half of § 3 this round claims to have closed

The round reports **"8 planted · 8 red · 0 GREEN."** I reproduced all eight
(§ 1 below). A ninth, which the round did not plant, is **GREEN**.

`bin/perry-restore-check:118` — the `not inside a git repository` branch of
`self_check()`:

```python
    root = repo_root(SELF)
    if root is None:
        return "unverifiable", f"{SELF} is not inside a git repository"
```

Flip that one token, `"unverifiable"` → `"clean"`:

```
E2 bin/perry-restore-check:118  ran=25  rc=0  *** GREEN ***  skipped=1
```

**All 25 tests pass.** And the way they pass is the finding:

```
test_helper_outside_any_repository_refuses (TestHelperSelfCheck)
A `git archive` copy has no `.git` — and that is the prescribed workflow. ...
  skipped 'the temp directory is itself inside a git repository,
           so this case is not reachable here'
```

The one test written this round to close the outside-a-repository half of § 3
**skips itself**, and the reason it prints is false — the temp directory is not
inside a git repository. The skip fires because the test establishes its own
precondition by *running the helper under test and asking it for its own
verdict*:

```python
probe = self.run_helper("--allow-modified-self", "--json", …, helper=dest)
if json.loads(probe.stdout)["self_check"] != "unverifiable":
    self.skipTest(…)
```

A helper that misreports the verdict therefore disables the guard that exists to
catch it misreporting the verdict. That is a self-disabling guard, not coverage.

### Is it an equivalent mutant?

No. It changes behaviour an agent sees, and in the worst direction.

NOT YET CHECKED — end-to-end demonstration

### Which claim does it falsify, and is it code the round wrote?

It does not touch the aggregate verdict (§ 2.1, `all` → `any` — genuinely closed,
M1 red). It does not touch the gate (`:215`, M5 red). It falsifies the round's
coverage claim for the **`unverifiable` refusal**, specifically its
outside-a-repository half — one of the two halves the round's own headline says
it fixed. The mutated line is **pre-existing code the round left alone**, but the
*test that was supposed to pin it* is code the round wrote this round, and it is
the reason the mutation is invisible.

## 3. Controls

NOT YET CHECKED

## 4. The declared breaking change

NOT YET CHECKED

## 5. The standing "use `git show` instead" warning

NOT YET CHECKED

## 6. Suite and lint

NOT YET CHECKED

## 7. The six unfixed findings

NOT YET CHECKED

## 8. Criteria

NOT YET CHECKED

=== VERDICT ===
NOT YET CHECKED
=== END VERDICT ===
