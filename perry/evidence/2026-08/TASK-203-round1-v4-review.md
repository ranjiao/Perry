# TASK-203 — V4 review round 1: **FAIL**

> Fresh-context reviewer, 2026-08-29, against `perry/evidence/2026-08/TASK-203-spec.md`.
> Under review: `690b8c2` on `coding/task-203-register-stores`.
> All destructive work on scratch copies; the worktree was read-only.

## What holds, verified rather than restated

**`REGISTER_EVENTS` is complete**, enumerated two ways. Statically: all ten
`cmd_*` reaching `append_section_row` / `find_section_row` / `ensure_section` /
`section_rows` against the three sections are declared. Empirically: all 26
mutating subcommands run against a fixture carrying intake rows, a risk, an ask
and a task, diffing each section against each store — **no command changed a
section without changing that register's store**. `route` and `add` do touch
`## Intake` and are declared; `cadence-add` / `cadence-done` touch none and are
correctly omitted.

**The canonical transaction is sound with three entries.** A crash harness
(`os._exit(9)` after the N-th `os.replace`) at both rename boundaries: 3-entry
marker, clean recovery, no leftovers, `drifted: 0`.

**The four reported mutations all go red** — and two counts were under-reported
upward (canonical-set drop was 8 not 6; the `answer` deletion was 2 not 1).

**Both converted tests are legitimate.** The `asks` one added a content
assertion and is stronger. The `intake` one is *"different, and stronger on the
hazard"* — and the dropped drift coverage is not lost, because
`test_a_row_deleted_by_hand_reports_every_row_it_renumbered` still carries it.

## Finding 1 — BLOCKING. The exemption is keyed on the command, the hazard is not

The commit message claims this defect was prevented. **It describes this
branch's behaviour.**

`REGISTER_RENUMBERING` exempts `intake-sweep` because that command moves rows.
But the hazard is *whether the board's intake rows have moved since the store
was last written*, which `register_change` never checks. `intake-sweep` is the
only command that moves rows **itself**; it is not the only way rows move.

Reproduced — a human tidies one discharged row out of `## Intake` by hand, then
does something else entirely:

```
STORE, correct:
{"order":0,"request":"A - already dropped","outcome":"dropped …","discharged":true}
{"order":1,"request":"B - still waiting","outcome":"—","discharged":false}
{"order":2,"request":"C - still waiting","outcome":"—","discharged":false}

  ← row A deleted from BOARD.md by hand
  ← perry-task add --title "unrelated task"      (rc 0)

STORE, after:
{"order":0,"request":"B - still waiting","outcome":"—","discharged":true}   ←
{"order":1,"request":"C - still waiting","outcome":"—","discharged":false}

perry-lint: {"records": 2, "drifted": 0}
```

A live, undischarged request is recorded as discharged, its `Outcome` cell
still reads `—`, and drift says clean — `discharged` has no board column to
compare against. `intake_record` then carries that `True` forward **on every
subsequent write, permanently.**

Enumerated across all five intake events: `add`, `intake`, `resolve-intake` and
`route` all reproduce it; only `intake-sweep` is protected. `add` is the worst
— on a project-mode track it does not touch `## Intake` at all, which is exactly
what the change's own comment says the design refuses to do.

Proof: `bin/perry-task:2163`, `:2212-2216`, `bin/perry_store.py:1012`.

## Finding 2 — BLOCKING. The gate lets an unrelated write truncate a store to zero

`bin/perry-task:2205`: `if not board.has_section(section) and not path.exists():`

When the store **exists** and the board section does **not**, the gate declines
to decline, the derivation returns `[]`, and `store_text([])` is written:

```
intake.jsonl before: 3 records (one discharged, two live)
BOARD.md: `## Intake` removed
perry-task add --title "an ordinary task"      rc 0
intake.jsonl after:  '' — 0 records
```

`load_register_records`' own docstring eleven lines above states the rule this
violates: *"these three are canonical, and silently discarding a record would
let the next write persist the smaller set as truth."* The write is inside the
canonical transaction, so it is durable and atomic; the store is not
recoverable from the board, because the board is what is missing.

The closing mutation — tightening to `if not board.has_section(section):` — is
**green across the full suite**. The clause that makes the wipe reachable is
load-bearing for no test at all.

## Finding 3 — green mutation. The stored-record merge is untested

Replacing `current = load_register_records(path)` with `current = None`, which
deletes the entire two-source merge, is **green across 2803 tests**.
`discharged` / `cleared` / `answered` carry-forward has no test in the tree.
That is *"the 'one store's worth of testing' the Out-of-scope line was worried
about, realized across all three registers rather than avoided."*

## Finding 4 — a comment asserts a guard that does not exist

`bin/perry-task:2126-2129` claims `tests/test_register_stores.py` asserts *"that
every command mutating one of the three sections has its event declared."* It
does not — all three tests in `TestTheMapIsCompleteAndReal` run in the forward
direction. The residue is visible: `SECTION_OF` is defined and **never read**.

*"On a task whose subject is a success line that asserted a write nobody
performed, a comment asserting a test nobody wrote is the same shape."*

## Finding 5 — three citations point at a file the branch does not carry

`bin/perry-task:2121`, `:6983` and `tests/test_register_stores.py:9` all cite
`evidence/2026-08/TASK-203-premeasurement.md`, which is not in the commit and
appears in no commit in `git log --all`. It was written to the PMO tree and
never added to the branch. The commit's central four-register table rests on it.

Relatedly, verification item 1 as written — *"`perry-lint --root .` prints a
real drift verdict for all six stores"* — is not reproducible on the branch,
because the stores mint on first write and no write has run against Perry's own
state. The property holds on a fixture; the claim does not describe the commit.

## Baseline

`690b8c2` = 2803 tests / 8 failures / 4 modules; `45a355d` = 2786 / same 8 /
same 4. Byte-identical sets; the +17 are `test_register_stores.py`. **This
change adds no failure** — but the reported baseline of "3 modules, 5 failures"
omits `test_risks_store.TestTheReadersAreOneFunction` (3), *"which is one of the
three registers this change touches."*

## Verdict

```
=== VERDICT ===
task: TASK-203
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-203-spec.md
checked: all destructive work on scratch copies (branch, base from git archive
         45a355d, seven mutant trees). Full suite both trees: 690b8c2 2803/8/4,
         45a355d 2786/8/4, identical sets. Author's 4 mutations re-run on 4
         separate trees — 8, 4, 2, 1 red (two under-reported upward). Own
         mutations: `current = None` GREEN on 2803; remove the validation
         Refused green; tighten the gate GREEN. Category enumerated twice —
         static walk of all cmd_* against the three sections (10, all declared)
         and an empirical sweep of all 26 mutating subcommands diffing sections
         against stores. Finding 1 enumerated across all five intake events.
         Finding 2 reproduced: 3 records → 0 bytes. Crash recovery exercised at
         both rename boundaries. Spec criteria 1 and 2 verified on a fixture.
not-checked: TASK-203-premeasurement.md — absent from the commit and from
         `git log --all`, so the four-register pre-measurement is unverified;
         re-deriving it means running write commands, which the constraints
         forbid against the project under review. `route`'s half of Finding 1
         used a synthetic two-track config. Concurrency under parallel writers,
         Windows and network filesystems, localized boards, and
         `perry-tasks *-render --write` interaction were not exercised. Did not
         audit whether aiMark or perry-state surface `discharged` to a user.
         The `--group "Top risks"` abuse path (and `prioritize` being absent
         from REGISTER_EVENTS) is pre-existing and was not pursued.
proof: bin/perry-task:2163 with the merge at :2212-2216 and the carry-forward at
       bin/perry_store.py:1012 — `add`, `intake`, `resolve-intake` and `route`
       all write `discharged: true` onto a live undischarged intake row when the
       board's rows shifted by any means other than a sweep, and perry-lint
       reports drifted 0. Second: bin/perry-task:2205 —
       `if not board.has_section(section) and not path.exists():` — an unrelated
       `perry-task add` truncates an existing 3-record intake.jsonl to zero
       bytes when `## Intake` is absent; the closing mutation is green across
       all 2803 tests.
=== END VERDICT ===
```
