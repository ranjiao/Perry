# DESIGN-016 — acceptance criteria for the V4 round

Written 2026-09-10 by the author (PMO), **before** the round it governs. It
covers all fourteen rows of `perry/design/DESIGN-016-the-bin-contract.md § 6`
as one round, because § 4 of `work/reference/review.md` says independent rows
go out together and these fourteen share one parser.

**This file did not exist for rounds 1, 2 and 3, and that is the finding that
produced it.** Three reviews ran against an inferred bar. Each found real
defects the previous one had approved, which is the non-convergence
`review.md § 1` predicts, not evidence that the reviewers disagreed. The
criteria below are written from `DESIGN-016 § 2`'s fourteen numbered goals,
which were locked before any code landed — so this is a bar being *stated*,
not a bar being *negotiated* after a result.

- **Under review:** `4ebc0693..HEAD` on `bin-contract-phase-a`, restricted to
  `bin/`, `schema/`, `reference/snapshot.md` and `tests/`.
- **Rows:** TASK-359, 360, 361, 362, 363, 364, 365, 366, 367, 406, 407, 408,
  409, 410.
- **The design's goals are the authority.** Where this file and
  `DESIGN-016 § 2` disagree, § 2 wins and the disagreement is a defect in this
  file worth reporting.

## What must be true when this is done

Each criterion is a claim about behaviour a user can reach. A criterion is met
only if breaking the code that implements it turns a **named** test red
(`review.md § 2` rule 2). A criterion whose test stays green has not been
established, regardless of whether the product code looks correct.

**Read § "What a criterion may do to a row" below before judging any of these.**
Eight of the fourteen may fail a row. The other seven are checked to the same
standard and produce a filed row instead, because their worst outcome does not
answer yes to any of `review.md § 0`'s three questions. Which is which is
settled there, not here, and not by the round.

1. **`--root` beats `$PERRY_PROJECT`.** For each of the fourteen files listed
   under Bound A, invoking it with `--root <dirA>` while `$PERRY_PROJECT` is
   `<dirB>` reads `<dirA>`.
2. **`-h` / `--help` prints, exits, and never writes.** On each of the twenty
   executables in Bound B, from first, middle and last argument position. On a
   writer, the store's bytes are unchanged after the call.
3. **An unknown argument is refused with exit 2** on each of the six
   surface-declaring tools of Bound C, and the message names the legal set.
4. **Every writer accepts `--dry-run` and `--json`, and `--dry-run` writes
   nothing.** Bound D lists the writers. `--dry-run` must print what would land
   and leave the store byte-identical.
5. **A standup reads its state for under 5,000 tokens.** `perry-state
   --compact` is a strict projection of `--json`: every key it emits carries the
   same value as the corresponding key in `--json` from the same process.
   `SKILL.md` step 3 calls it.
6. **`perry-task list` is bounded.** No invocation returns more than
   `LIST_DEFAULT_LIMIT` rows unless the caller asked; the payload says how many
   rows exist beyond the bound; the contract version in `schema/` matches the
   version the tool emits.
7. **One declaration drives the parser.** For each tool in Bound C, the flags
   the parser accepts and the flags `SURFACE` declares are the same set in both
   directions — a declared flag that no code reads, and a flag code reads that
   is not declared, are both defects.
8. **Subcommand help costs one call and returns only that subcommand.**
   `--describe <sub>` on each of the fifty-seven declared subcommands in
   Bound E.
9. **`render --write` refuses rather than losing a record.** With a stored
   record that has no line to land in, it exits non-zero and names the record.
   Its success line counts lines changed, not records read.
10. **No tool exits through a traceback.** For the twenty executables of
    Bound B, no invocation in Bound F's enumerated shapes prints a Python
    traceback; every refusal is one line and exit 1, every bad invocation is
    exit 2.
11. **`bin/README.md`'s executable examples run.** Every fenced `bash` block in
    that file executes against a scratch project and exits 0, or is marked
    non-executable in a way the test reads.
12. **A flag is accepted only where it is declared.** For each declared
    flag/subcommand pair in Bound G, the flag on a non-declaring subcommand is
    refused with exit 2 rather than silently dropped.
13. **This project's vocabulary is one small call.** `perry-state --compact`
    carries tracks, their modes, and the stages legal on each, and those values
    equal what `.perry/config.jsonl` and `schema/` hold.
14. **One mechanism answers "what does this tool take".** `perry describe`,
    the README table and the generated usage blocks all read the same
    declaration; no second copy of the surface exists that a test does not
    compare against the first.

## What a criterion may do to a row

**Added 2026-09-10, after round 4 returned seven FAILs and four of them were
below `review.md § 0`'s line.** This section is the correction, and it is a
correction to *this file*, not to the reviewers — they applied the bar they
were given, exactly.

The defect was mine and it is worth naming precisely: **§ 1 above imports all
fourteen of the design's goals as gates of equal weight.** Goal 2, "help prints
from any argument position", and goal 9, "a write that cannot do what it is
documented to do refuses", became the same kind of gate. One is polish and one
is data loss.

`review.md § 0` already carries the test, and nobody applied it per criterion:

> Send a row to V4 when a defect in it would **destroy or corrupt state that
> cannot be recreated**, **make a tool report a wrong answer to someone with no
> way to tell**, or **weaken a gate standing between a user and either**.

So each criterion below now says which of two things it may do:

- **FAIL** — a defect here answers yes to one of those three. It fails the row.
- **ROW** — a defect here is real and worth fixing and answers no to all three.
  **It is still checked and still reported**; what changes is that the round
  files it and moves on instead of failing the row and buying another round.

**This is not the bar being lowered.** Nothing stops being tested, the bounds
are unchanged, and a criterion marked ROW that turns out to hide a wrong answer
is a FAIL on the spot — the classification is a claim about consequence, and a
round that shows the consequence is worse than claimed has refuted it, which is
a finding. What changes is the price of the finding.

| # | what it checks | may do | why |
|---|---|---|---|
| 1 | `--root` beats `$PERRY_PROJECT` | **FAIL** | a writer that resolves the wrong project writes into it |
| 2a | `--help` never runs a write | **FAIL** | a gate against a write nobody asked for |
| 2b | `--help` prints from any position | ROW | worst outcome is exit 2 and a line naming `--help` |
| 3 | an unknown argument is refused, exit 2 | **FAIL** | `--wrte` used to render, write nothing, and exit 0 — the caller was told the run succeeded |
| 4a | `--dry-run` writes nothing | **FAIL** | same gate as 2a |
| 4b | every writer accepts `--dry-run` and `--json` | ROW | a missing feature announces itself; § 1.6 says withdraw the claim instead |
| 5 | `--compact` is a strict projection | **FAIL** | a key result at 43% published as 100%, and the reader cannot tell |
| 6 | `perry-task list` is bounded and says so | **FAIL** | a truncated list presented as complete is a wrong answer to a counter |
| 7 | declaration and parser agree both ways | **FAIL** | accepted-and-silently-dropped is § 1.4, the complaint this design was opened on |
| 8 | subcommand help is one call | ROW | a cost, not a wrong answer |
| 9 | `render --write` refuses rather than losing a record | **FAIL** | § 1.5, the one place a Perry command reported a write it did not perform |
| 10a | a refusal is exit 1, a bad invocation exit 2 | **FAIL** | callers branch on these; `perry-diagnose` gaining an exit 2 already broke a documented promise |
| 10b | no tool prints a Python traceback | ROW | ugly and loud. A crash is not a silent wrong answer |
| 11 | the README's examples run | ROW | `review.md § 0` names documentation explicitly: file the correction as a row |
| 12 | a flag is accepted only where declared | **FAIL** | 7 in its user-visible form |
| 13 | the vocabulary equals the store and the schema | **FAIL** | a wrong answer about what this project's tracks and stages are |
| 14a | the published `--describe` payload is right | **FAIL** | a payload a consumer trusts |
| 14b | no uncompared second copy of the surface exists | ROW | an architecture claim; each copy that drifts is its own row |

Eight FAIL, seven ROW, and criteria 2, 4, 10 and 14 split because each was
carrying two claims of different consequence in one sentence.

### What this would have done to round 4

Round 4's seven FAILs, re-read against the table: **TASK-362, TASK-364 and
TASK-408 stand.** TASK-360, TASK-365, TASK-407 and TASK-410 would have been
rows.

The verdicts in `DESIGN-016-round4-v4-review.md` are left exactly as written.
A verdict records what was true when it was reached, and rewriting one because
the author later preferred a different bar is the thing `review.md § 1` calls
a negotiation with the result. What is recorded here instead is that those four
were charged at the wrong rung, and the charge was the author's.

**Three of the seven rows round 4 FAILed were never V4 rows.** Measured
2026-09-10 off the store, not inferred: TASK-365 and TASK-407 carry `V3`,
TASK-408 carried no rung at all, and only TASK-360, TASK-362 and TASK-364 are
filed at `V4`. This file's § "Which row each criterion decides" mapped criteria
onto rows without once reading the rung those rows were filed at, so a round was
bought at V4 for rows their own authors had put a rung below. `review.md § 0`
says raising a rung is cheap and reversible, so nothing was wrong with looking —
what was wrong was FAILING them there, and doing it without recording the
decision.

**What that produced, and it is the correction:** TASK-365 and TASK-410 are
closed at V3, on the round-4 review plus the tests it forced, because their
remaining exposure is ROW-grade and a second round buys nothing. TASK-408 is
raised to V4 deliberately and recorded here, because criterion 14a is a payload
a consumer trusts. TASK-407 stays in round 5 at a raised rung for the same
reason and by the same permission, because criterion 10a is an exit code callers
branch on.

**The bill, so the next person can weigh it.** Answering the four below-the-line
FAILs cost 227 new lines in `tests/test_bin_argument_contract.py` — the whole of
that file's growth — plus 104 of the 112 changed lines of product code, all of
it defending against `chmod 000` on a state directory and `-h` in second
position. The three that stand cost less than half of that. The work was worth
doing; buying a FAIL and a re-review round for it was not.

## Which row each criterion decides

A verdict block is emitted per row (`review.md § 3`), so this is the map from
the criteria above to the fourteen blocks the round must return.

| row | phase | criteria that decide it |
|---|---|---|
| TASK-359 | A1 `--root` precedence | 1 |
| TASK-360 | A2 a real parser | 2, 3 |
| TASK-361 | A3 `--dry-run` / `--json` | 4 |
| TASK-367 | A4 `add --design` | 4 (the flag is written, not dropped) |
| TASK-406 | A5 `render --write` refuses | 9 |
| TASK-407 | A6 no traceback | 10 |
| TASK-362 | B1 `--compact` | 5, 13 |
| TASK-363 | B2 the bound | 6 |
| TASK-364 | C1 the declaration | 7, 14 |
| TASK-365 | C2 usage-first help | 2, 14 |
| TASK-366 | C3 subcommand help | 8 |
| TASK-408 | C4 `bin/perry` | 14 |
| TASK-409 | C5 `--register` | 7 (the register is a declared parameter, not a name) |
| TASK-410 | D1 the README | 11 |

## Bound

```
A  --root readers            grep -ln '"--root"' bin/*            → 14 files on HEAD
B  executables               find bin -maxdepth 1 -type f -perm +111  → 20 files
C  surface-declaring tools   grep -ln '^SURFACE' bin/*            → 6 files
D  writers                   perry-task, perry-tasks, perry-config, perry_md_store.py → 4
E  declared subcommands      sum over C of len(SURFACE.subcommands) → 57
                             (perry-config 5, perry-okr 5, perry-task 30,
                              perry-tasks 17, perry-state 0, perry-diagnose 0)
F  traceback shapes          no argument; unknown flag; unknown subcommand;
                             flag on a non-declaring subcommand; missing
                             required value; unreadable project root; a store
                             file that is not JSON → 7 shapes per tool
G  flag/subcommand pairs     the declared pairs in the six SURFACE blocks
```

**Remainder, out of scope for this round and named so the next one need not
rediscover it:** the **thirteen** tools that declare no surface, listed by
`bin/perry list` under "not yet declaring a surface". Criteria 3, 7, 8, 12 and
14 do not reach them by construction. `DESIGN-016 § 3` rules them out of this
design; a defect found in one of them is a new row, not a FAIL on these
fourteen.

A finding that widens any bound above is filed as a new row, never as a
re-opening of this round (`review.md § 1`).

## Baseline

- **Known red before the branch: THREE tests in two modules**, all red on
  `main` at `4ebc0693` as well. Measure it in your own tree.
  - `tests/test_contract_key_parity.py`, two tests.
  - `tests/test_resume.py`, `TestStaleRuns.test_a_fresh_run_is_not_stale`.
    **This one was missing from the baseline when round 4 was dispatched**, and
    two of its three reviewers independently re-derived it, one by extracting
    `4ebc0693` with `git archive` and running it there. An incomplete exhibit
    is the author's to fix before dispatch (`review.md § 2`), and this is the
    correction. It is clock-dependent: `stale_run_days: 30` against a fixture
    stamped two days ago.
- **Green expectation:** 122 modules, two modules red — the three above.
- `bash tests/run` takes about 118 seconds wall on 8 workers.

## What rounds 1 to 3 already changed

Listed so the round can weigh where a regression is likeliest, **not** as
ground it may skip. `review.md § 2` rule 3 applies: do not trust the previous
round's verdict, including the fixes it accepted.

| round | what it found | where the fix landed |
|---|---|---|
| 1 | `perry-config track --mode` regression shipped in phase A | the declaration conversion |
| 2 | the README `add` example was never executed by its own test | `tests/test_bin_surface.py` |
| 3 | `perry-tasks` fall-through reaches `verify`; `perry-config unset` reports a write that did not happen; `bin/perry` crashes on a non-UTF-8 file; the contract page taught consumers to reject its own 2.0; four tests that did not test their names | `2ba2c565` |

Round 3's own test for the fall-through named `perry-tasks` and exercised
`perry-config`. **Check that the round-3 fixes are tested by tests that reach
them**, by mutation, not by reading.

## Two questions the author has not decided

Report on these; do not FAIL a row for them, they are open by the author's
choice and are recorded here so the round does not spend itself on them.

1. `bin/README.md`'s quick-start block ends with three lines (`start`,
   `status`, `done`) that cannot run in a fresh project because they need an id
   the block never captures.
2. `perry list --json` compares subcommand *counts* with each tool's
   declaration, not subcommand *names*.
