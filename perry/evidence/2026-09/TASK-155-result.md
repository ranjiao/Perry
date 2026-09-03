# TASK-155 — per-KR assertion date

**Status:** STOPPED AT THE HAND-OFF, by the spec's own rule. No production code
changed. The defect is reproduced, measured, and specified for the `goals` lane.

## Provenance

- Worktree: `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a282ede4b7198ffc8`
- Worktree was cut at `d49964e` — **5 commits behind `main`**, so the cut point was
  NOT the stated baseline. The branch was created explicitly at the baseline instead.
- Branched from: `00078bd` (`main`, "TASK-155's round lost to the watchdog, re-dispatched")
- Branch: `coding/task-155-per-kr-assertion-date-w2`
  - The brief's name `coding/task-155-per-kr-assertion-date` **already exists** at
    `061ee7b` — an ancestor of `main`, zero commits of work, the dead attempt's cut
    point — and is checked out in the still-present worktree
    `agent-a0026df7d47f00efd`. git refuses a second checkout of a branch, and
    removing another agent's worktree is shared-state destruction I did not perform.
    The PMO can fast-forward or rename; nothing is lost either way.

## 1. The before-state: the re-dating, reproduced

On a `git archive HEAD` copy in an agent-unique scratch directory
(`t155-a282ede4-lab/`), untouched by any other workload.

**Read the register as it stands:**

```
kr_currents: {"total": 6, "asserted": 3, "unasserted": 3, "measured": 0,
              "stale": 1, "stale_ids": ["P003-O1-KR2"]}
register updated: 2026-09-03T06:06:45Z

  P003-O1-KR1: asserted_at='2026-09-03T06:06:45Z' scope='register' stale=False
  P003-O1-KR2: asserted_at='2026-09-03T06:06:45Z' scope='register' stale=True
  P003-O1-KR3: asserted_at='2026-09-03T06:06:45Z' scope='register' stale=False
```

`P003-O1-KR2` is **genuinely stale**: `TASK-067` moved after the register's
`updated`. This is a real staleness signal about a real number.

**Append one edge to a completely unrelated, `unasserted` KR:**

```
perry-goals link TASK-077 P003-O3-KR2
```

The writer warns, exactly as the spec says it does — it is **not silent**:

> ⚠ this write bumps `updated`, which is also where `current`'s assertion date is
> read from (`asserted_scope: register` — there is no per-KR date). 3 KR(s) with an
> asserted `current` will read as freshly asserted and lose any staleness signal:
> P003-O1-KR1, P003-O1-KR2, P003-O1-KR3. Nothing about those numbers changed.

**Read again:**

```
kr_currents: {"total": 6, "asserted": 3, "unasserted": 3, "measured": 0,
              "stale": 0, "stale_ids": []}

  P003-O1-KR1: asserted_at='2026-09-03T08:18:49Z' scope='register' stale=False
  P003-O1-KR2: asserted_at='2026-09-03T08:18:49Z' scope='register' stale=False
  P003-O1-KR3: asserted_at='2026-09-03T08:18:49Z' scope='register' stale=False
```

The date moved on all three. The real staleness signal on `P003-O1-KR2` was
**destroyed by a write to a different KR**. Nothing about KR2's number changed.

**Control A (the write is the cause, not time or read nondeterminism):** two
consecutive reads of an untouched copy, no write in between, both return
`stale: 1 · stale_ids: ["P003-O1-KR2"]` and `updated: 2026-09-03T06:06:45Z`.
The reset in the sequence above is attributable to the `link` write alone.

## 2. Control B — and the direction nobody has disclosed

The spec's control is "a KR whose `current` is genuinely re-measured must still
re-date". Measured on a third clean copy: change `P003-O1-KR2`'s `current` from
`6` to `5` — a real re-measurement — and touch nothing else.

```
  P003-O1-KR2: current=5.0  asserted_at='2026-09-03T06:06:45Z'  stale=True
```

**The date did not move.** A number that was just re-measured still reports the
assertion date of the *previous register write*, and still reports `stale: true` —
"this number is out of date" about a number measured seconds ago.

So the field is wrong in **both** directions:

| direction | a write that... | effect on `asserted_at` | disclosed? |
|---|---|---|---|
| 1 | changes **nothing about any number** (an edge elsewhere) | re-dates **every** asserted KR, erasing real staleness | yes, three times |
| 2 | changes **a number itself** (a re-measurement) | re-dates **nothing** — stale date persists, false `stale: true` | **no, nowhere** |

Direction 2 is not in the contract note, not in the writer's warning, and not in
the reader's counts. All three describe direction 1 only. **This is a new finding,
not a fourth disclosure**, and it is the stronger half of the defect: direction 1
makes a number look fresher than it is (a lost warning), direction 2 makes a
freshly measured number look stale (a false warning that trains readers to ignore
the signal).

It also settles the fix's shape. Direction 2 cannot be reached from the writer at
all — no `link` write is involved — so a per-KR date has to be written *by whatever
asserts `current`*, not derived at the moment the register is edited.

## 3. Why no reader-or-contract-only fix exists

The deliverable needs a KR to report *the date its own `current` was asserted*.
A reader can only report a date that was recorded somewhere. Checked, exhaustively:

1. **The register frontmatter** — one `updated:` key, register-wide. There is no
   per-KR date field. (`perry/phase/003-linkage.md`)
2. **The event log** — 1880 events across 23 kinds. **Zero** carry a `current`,
   `target`, `asserted` or `metric` key. The 14 events with a `kr` key are
   `link-edge` events recording which KR a task was attached to, not assertions.
   Nothing in Perry has ever recorded a `current` being asserted.
3. **A store** — `schema/state-schema.json § claims[]` declares `phase/` as
   `kind=dir owner=goals` with **no store file**. `okr.jsonl` (`owner=goals`) is
   `OKR.md`'s commitments register, not phase KRs, and does not exist in this
   project. Phase KRs are markdown-only.
4. **The `metric:` prose** — the three asserted KRs *do* carry their real dates,
   as free text: "Measured 2026-09-01…", "Measured by TASK-229…". This is the
   only trace of the truth in the repository, and it is a never-validated prose
   field. Date-scraping it would be a heuristic that silently returns the wrong
   date the first time an author words it differently — a guess presented as
   provenance, which is the failure mode `perry-goals § resolve` refuses by
   design ("a writer that guesses is worse than no writer").

There is no fourth source. **A reader cannot report a date that was never
recorded**, so the fix cannot live in the readers and the contract.

Two independent places in the codebase already reach the same conclusion:

- `bin/perry-goals:2049-2051` — "It is NOT fixed here: a per-KR assertion date is
  a new field in `schema/state-schema.json`, which is behind this project's safety
  gate (TASK-119 § verification 5)."
- `tests/test_linkage_writer.py:550` docstring — "The fix is a new field in
  `schema/state-schema.json`, which is a decision the user makes."

## 4. HAND-OFF — what `goals` would need to write

Per the spec and the brief, the round **stops here**. `perry/phase/003-linkage.md`
was not edited; the only writes were to `git archive` copies in scratch.

**The field.** One optional per-KR key beside `current`, in
`phase/<NNN>-linkage.md`, written by whatever asserts `current`:

```yaml
      - id: P003-O1-KR1
        target: 6
        current: 6
        current_asserted: "2026-09-01T00:00:00Z"   # NEW — when THIS number was arrived at
```

**Why it must be the writer of `current`, not the writer of the register.** Control
B shows a re-measurement leaves no trace anywhere. Only the actor that sets
`current` knows the number changed, so only it can date it. A date derived at
`link` time — the one write path that exists today — reproduces direction 1
exactly.

**What blocks it, in order:**

1. **There is no writer of `current` at all.** `bin/perry-goals:1141`: "Nothing
   here writes either field." `perry-goals krs` is read-only by construction and
   refuses `--write` (`cmd_krs`, `:3046`). `goals/reference/phases.md:212` says
   nothing in the linkage file is edited by hand once it exists. So the three
   `current: 6` values in the live register were hand-written — the crossing
   recorded in `USER-912`'s answer. **That gap is `TASK-264`, and this row is
   blocked on it**: a per-KR assertion date is meaningless until something other
   than a human hand asserts the number it dates.
2. **The field is `schema/state-schema.json`**, behind the project's safety gate
   (TASK-119 § verification 5) — a user decision, and explicitly out of bounds for
   this round.
3. **`phase/` is `owner=goals`** and `work` is not its writer.

**Recommended sequencing:** `TASK-264` (build the KR write path) → schema field
under the safety gate → then this row's reader and contract change, which becomes
small and mechanical once the data exists.

## 5. Contract version consequence

`schema/goals-list-contract.md` is at **`2.3`** (`LIST_CONTRACT =
"perry-goals/list/2.3"`, `bin/perry-goals:522`). **Not bumped in this round** — no
value changed, so a bump now would announce a change that did not happen.

When the fix lands it is a **minor to `2.4`, no key added, one value's meaning
changed** — the `2.2`/TASK-144 precedent exactly:

- `current_provenance.asserted_scope` stops being the constant `"register"` and
  becomes `"kr" | "register"`. Its domain widens, so **every consumer that
  hardcoded `== "register"` changes behaviour** — the case rule 2 does not cover.
- `current_provenance.asserted_at` starts returning a per-KR date where one exists,
  and `current_staleness.since` follows it.

Because a value's meaning moves, the fix **must also append a `2.4` entry to
`LIST_SEMANTICS`** (`bin/perry-goals:537`) naming
`krs[].current_provenance.asserted_at`, `krs[].current_provenance.asserted_scope`
and `krs[].current_staleness.since`. That array exists (added at `2.3`, TASK-205)
precisely so a value-meaning change is discoverable; landing `2.4` without an entry
would reproduce the gap TASK-205 closed.

Registers written before the field exists keep `asserted_scope: "register"`, so the
change is backward-readable rather than a break.

## 6. The warning at `bin/perry-goals:2055-2062`

**KEPT, and it must be.** It is only redundant beside a landed fix, and no fix
landed — the condition it warns about is fully live and was re-triggered verbatim
in section 1. Removing it would delete the single most useful artefact in the
system with nothing put in its place.

It is also **not the fourth disclosure the spec warns about**, because this round
added no disclosure: no prose, no comment, no warning, no contract note was written
to production code. The only new text is this evidence file.

One note for the fix's round: the warning covers direction 1 only. When the per-KR
date lands, direction 1 stops being possible and the warning becomes false — at
which point it should be **deleted, not amended**, because direction 2 is not a
condition the `link` writer can observe.

## 7. Corrections to the spec and the brief

Every claim in the brief and the spec was checked. Four are wrong.

1. **`bin/perry-state:1971` is not a reader of the register's `updated`.** Both
   the brief and the spec state the register's `updated` is "read as freshness at
   `bin/perry-state:1971` (`idle_days`)" and carried at `:1968`. Both lines sit
   inside `def scan_interrupted` (`bin/perry-state:1939`) and read
   `fm.get("updated")` from an **interrupted adoption dossier's** frontmatter — a
   different field, different file, different owner. The spec's own Bound excludes
   exactly this class of confusion ("a different field with a different owner").
   The real readers are `:2160` (passes `updated=link.updated` into
   `kr_progress_provenance`, the only site that matters) and `:2381` (payload
   passthrough). **The reader surface is 2 sites, not 4.**
2. **`stale` is `1` today, not `0`.** The spec records `stale 0` on `5c76aa2`;
   measured on `00078bd` it is `stale: 1 · stale_ids: ["P003-O1-KR2"]`, because
   `TASK-067` moved after the register's `updated`. This made the round *better* —
   it supplied a real staleness signal to watch get destroyed, rather than a
   hypothetical one. The spec's framing ("`stale: 0` is not evidence any of them is
   fresh") is still exactly right, and is now demonstrated rather than argued.
3. **The register's `updated` is `2026-09-03T06:06:45Z`, not `2026-09-02T11:51:23Z`.**
   Link writes have landed since the spec was measured. Immaterial, noted for the
   record.
4. **The suite is green and the tree guard needed no fixture work.** The brief says
   "the suite has not been reliably green today" and that `tests/test_tree_guard.py`
   "needs its scratch copy to be a real git repo". `bash tests/run` on `00078bd` in
   this worktree: **111 modules · 3134 tests · 175.1s · 8 workers · all green,
   exit 0**, first attempt, no intervention. The tree guard passed at both ends and
   confirmed nothing under the worktree moved.

The spec's central claim — one `updated:` field carrying two facts, written at
`bin/perry-goals:2063`, making `stale` computable only register-wide — is
**correct**, and is now reproduced rather than asserted.

## 8. Verification ledger

| # | Spec item | Result |
|---|---|---|
| 1 | Reproduce the re-dating first | **Done** — §1, on a `git archive` copy |
| 2 | After the fix, the untouched KR is left alone | **N/A** — no fix landed; hand-off §4 |
| 3 | The warning becomes unnecessary, or the round says why | **Kept, reason given** — §6 |
| 4 | Mutation: revert the per-KR date, show a named test go red | **N/A** — no per-KR date to revert. Substituted Control A (§1), which falsifies the reproduction itself |
| 5 | Control: a genuinely re-measured KR must still re-date | **Run, and it FAILS today** — §2, Control B. The requirement is recorded for the fix |
| 6 | Suite no redder than baseline; `perry-lint --root .` at 0 errors | **Equal** — no production file changed; §7.4 |

**Mutations: 1 planted, 1 red, 0 green.** No production code changed, so the
mutation target was the round's own reproduction rather than a fix. Control A is
that mutation in negative form: remove the `link` write — the single thing claimed
to cause the reset — and the reset does not occur (`stale` stays `1` across two
reads). Had it still reset, the reproduction would have been a false positive.
Control B's anchor asserted on the old text (`current: 6`) before writing and would
have aborted loudly on a miss, per the project's anti-no-op rule.

## 9. Files changed

One, this file. `perry/phase/003-linkage.md` was **not** touched;
`schema/state-schema.json`, `schema/goals-list-contract.md`, `bin/` and `claims`
were **not** touched. All experimental writes went to `git archive` copies under
`scratchpad/t155-a282ede4-lab/`, an agent-unique directory (the shared scratchpad
already held another workload's `add-duration-abd3fb21.py`, the collision the brief
warned about).
