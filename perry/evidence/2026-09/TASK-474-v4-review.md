# TASK-474 — V4 review: the phase lifecycle writer

Date: 2026-09-20. Reviewer: an independent V4 round. I did not write this code
and I did not start from the author's verdict.

- **Under review**: `8a081790..0dcbec17` (branch `coding/task-474-phase-lifecycle`),
  also merged to `main` at `ac256a3a`.
- **Review worktree**: `/Users/bytedance/proj/Perry/.claude/worktrees/agent-a446b86b5fcb12945`,
  branch `review/task-474-v4`, checked out at `ac256a3a` so that the code and
  the corrected criteria are in one tree.
- **Criteria**: `perry/evidence/2026-09/TASK-474-spec.md`.
- **Nothing was run against `/Users/bytedance/proj/Perry/perry`.** Every verb in
  this review ran against `tests/fixtures/sample-project` copied into
  `/private/tmp/claude-501/.../scratchpad/probe/`.

## A note on which spec is the authority

The branch under review does **not** contain the spec it was built against.
`6965b1ce` — "correct TASK-474 criterion 1 before implementation" — is a
`main`-side commit whose parent is `8a081790`; it never entered
`coding/task-474-phase-lifecycle` and arrives only at the merge `ac256a3a`. So
at `0dcbec17` the file still says `new` must **not** write `phase/CURRENT`,
which the implementation does.

I reviewed against the **corrected** text, and I checked the correction's own
argument rather than taking it: `goals/reference/phases.md § plan-phase` does
carry both sentences, the "does not reserve a number, set a start date, make a
phase active or change `phase/CURRENT`" sentence is about the chat draft, and
the same page does require the writer's result to identify "the ten-section
phase prose and the activated phase pointer". The correction is sound. It is
still worth saying plainly that the criterion was rewritten by the same person
who then implemented it, and that a reader of the branch alone cannot see that.

## Method

`bash tests/run --tier affected --base 8a081790` — 70 modules / 2043 tests /
205.2s / **green**, and a green affected tier is not a green suite.

Mutations are anchored by line number (never `str.replace`), `__pycache__` is
purged and the clock advanced past a whole second on both sides of each edit,
and every restore is verified with `bin/perry-restore-check ac256a3a <path>` —
against the ref, not against bytes this round snapshotted. Every restore
reported `✓ bin/perry-goals matches ac256a3a (7fb891704075…)`.

| # | Mutation | Result |
|---|---|---|
| M-A2 | re-inline the `phase/CURRENT` sentinel set into `current_phase`, a fourth copy beside `phase_pointer` | **red** — `test_blank_cell_is_one_rule … test_no_site_decides_blankness_for_itself` reports `('bin/perry-goals','current_phase',('none','—'))` |
| M-B | a seventh, unregistered `write_atomic(...)` site inside `phase_command` | **red** — `test_okr_store_is_the_source.test_no_other_subcommand_writes_OKR_md` |
| M-C | the `new` "phase still active" refusal overwrites `linkage.jsonl` **and** `okr.jsonl` before raising | **GREEN — finding F3** |
| M-D1 | the same refusal rewrites `phase/CURRENT` before raising | red |
| M-D2 | the same refusal drops a file into `phase/snapshots/` before raising | red |
| M-E | delete `close`'s already-scored refusal, `bin/perry-goals:4840-4842` | **GREEN across the whole affected tier — finding F4** |

## The three claims the round was told to scrutinise

**1. The two guard-test edits are registrations, not relaxations — confirmed.**

`tests/test_blank_cell_is_one_rule.py`: the `EXEMPT` key moved from
`("bin/perry-goals","current_phase",…)` to `("bin/perry-goals","phase_pointer",…)`.
The key is one function, so it cannot cover a second site. Constructed the case
where the guard must still fire (M-A2): with the sentinel set back in
`current_phase` the sweep reports that site and the guard is red. The reverse
direction is guarded too, by the module's own
`test_the_exemptions_are_all_still_real`, which fails if the exempted function
stops carrying the literal. Not a relaxation.

`tests/test_okr_store_is_the_source.py`: the six new entries extend an
**exact ordered list** of every `write_atomic(` / `write_text(` / `.write(`
line in `bin/perry-goals`; the grep that builds `calls` was not touched. M-B
added a seventh site and the guard went red naming it. Not a relaxation.

**2. "All six write sites are behind `assert_owned` and cannot reach `OKR.md`"
— true, but the stated reason is wrong.**

Enumerated: `bin/perry-goals:4778`, `:4779` (`new`), `:4813` (`activate`),
`:4851`, `:4852`, `:4854` (`close`). All six are the module-local
`write_atomic(state_root, …)` at `:793`, which calls `assert_owned` first, so
the first half is exact. No other bytes-on-disk path exists in
`phase_command`; the two `mkdir` calls are both under `phase/` and both inside
`if not dry`.

But `assert_owned` is **not** what stops these writes reaching `OKR.md`:
`owned_by_goals` (`bin/perry-goals:761`) returns `True` for `OKR.md`, because
`OKR.md` is this lane's own file. The comment in the registration reads "all
through this tool's own `write_atomic`, so all behind `assert_owned` … None of
them can reach `OKR.md`", and the "so" does not carry. What actually holds is
path construction: every destination is `state_root/"phase"/…` built from a
number derived from the directory listing and a slug matched against
`PHASE_SLUG_RE`. I probed that directly — `--slug ../../escape` is refused as
"not a short hyphenated slug", nothing written. The conclusion stands; the
rationale a future reader will rely on does not.

**3. "Each refusal leaves the whole `phase/` tree byte-identical, asserted by
hash" — the hash is real, and it covers two of the four paths the criterion
names.**

`phase_hash` (`tests/test_phase_lifecycle.py:86-93`) `rglob`s `d/"phase"`, so
it does cover `phase/CURRENT` and `phase/snapshots/` — verified by mutation,
not by reading: M-D1 and M-D2 both went red. Criterion 7, however, names
"`phase/`, `phase/CURRENT`, `linkage.jsonl` **and** `okr.jsonl`". M-C made a
refusal overwrite both `linkage.jsonl` and `okr.jsonl` before raising and the
module stayed **green**. See F3.

## Findings

### F1 — FAIL. `splice_header` indexes a `split("\n")` list with a `splitlines()` index

- `bin/perry-goals:4656` — `phase_header`: `for n, line in enumerate(text.splitlines())`
- `bin/perry-goals:4676` — `splice_header`: `lines = text.split("\n")`, then `lines[n] = re.sub(...)`

`str.splitlines()` breaks on `\x0b \x0c \x1c \x1d \x1e \x85    ` and
on a lone `\r`; `"\n"` does not. One such character anywhere above the target
header shifts `n`, and there is no check that `lines[n]` is the line
`phase_header` found. Two distinct failures follow, both measured on a fixture
copy:

*Silent no-op (criterion 1).* A body carrying one form feed above the header
block:

```
$ perry-goals phase new --root p1 --slug ff-probe --body-file body_ff.md --actor t
perry-goals: wrote phase/003-ff-probe.md · phase 003-ff-probe · active
$ head -6 p1/phase/003-ff-probe.md
> **Started**: {{YYYY-MM-DD}}
> **Status**: active | scored
```

Exit 0, `phase/CURRENT` written, `--json` reporting `"started": <today>,
"status": "active"` — and **neither header stamped**. `re.sub` matched nothing
on the wrong line and `splice_header` returned the text unchanged without
raising. Criterion 1 requires both stamps.

*Half-written crash (criterion 5).* Two such characters make the index run off
the end. On a fixture whose phase document carried them:

```
$ perry-goals phase close --actor t --root .../crash
  File ".../bin/perry-goals", line 4678, in splice_header
    rf"\g<1> {value}", lines[n])
IndexError: list index out of range
$ ls .../crash/phase/snapshots
2026-09-20-002-release-pipeline-final.md          # written
$ grep Status .../crash/phase/002-release-pipeline.md
> **Status**: active                              # NOT flipped
$ cat .../crash/phase/CURRENT
002-release-pipeline                              # NOT cleared
```

An unhandled traceback — `phase_main` catches `OSError` and `Refused`, not
`IndexError` — **after** the first of `close`'s three writes has landed. One of
the three effects happened and two did not, which is precisely what the new
module's own docstring says it exists to prevent: "A refusal that exits 1 after
having already written half of what it planned is the failure mode this file
exists to catch." Worse, the phase is now permanently stuck: every retry hits
`a final snapshot already exists at phase/snapshots/…` (`:4847`), and the only
way out is the hand-edit `goals/reference/phases.md § Writing it` forbids.

This is not an exotic category in this codebase — it is a recurrence of one it
has already named. `bin/perry-goals:400-404`, thirty lines from the class
criterion 5 tells this writer to imitate, says in as many words that
`split("\n")`/`join("\n")` is used *because* `splitlines()` is not lossless.
`bin/perry-goals:238` records `tests/test_one_line_break_rule.py`, opened
because two spellings of one line-break rule "disagreed on six of the eleven
boundaries `str.splitlines()` breaks on". This change re-introduces exactly
that disagreement, inside one function pair.

**Enumeration of the category** (rule 1 — every site, not the next one):

| Site | Counts/indexes with | Agrees with? |
|---|---|---|
| `bin/perry-goals:4656` `phase_header` | `splitlines()` | — pairs with :4676 |
| `bin/perry-goals:4676` `splice_header` | `split("\n")` | **no** — F1 |
| `bin/perry-goals:4769` `new` cap gate | `len(text.splitlines())` | **no** — F2, vs `bin/perry-lint:846` |
| `tests/test_phase_lifecycle.py:229-231` | `splitlines()` both sides | consistent, but only compares the document to itself |
| `bin/perry-goals:395`, `:973`, `:1511` (pre-existing) | `split("\n")` | consistent with the linter |

`phase_docs` does no line work. Those five are all of them in the change.

### F2 — FAIL. The cap gate counts lines differently from the linter that owns the cap

- `bin/perry-goals:4769` — `cap, lines = phase_cap(), len(text.splitlines())`
- `bin/perry-lint:846` — `lines = raw.split("\n")`, gated at `:849`

Criterion 3 is right that the cap *number* must come from the schema, and it
does (`phase_cap`, schema `files[id=phase].cap == 300`). But the *count* is a
second implementation, and it is one lower than the linter's for every file
ending in a newline — which is every file this writer produces (`text = body if
body.endswith("\n") else body + "\n"`, `:4764`). At the boundary the writer
writes a file its own project immediately rejects:

```
$ perry-goals phase new --root p300 --slug big-one --body-file body300.md --actor t
perry-goals: wrote phase/003-big-one.md · phase 003-big-one · active
$ wc -l p300/phase/003-big-one.md
     300
$ perry-lint --root p300
  ✗ phase/003-big-one.md [size-cap] 301 lines, over the tier-1 cap of 300.
```

Criterion 3's purpose is that `phase new` refuse rather than write an over-cap
tier-1 document. At exactly 300 written lines it does the opposite. Whichever
of the two counts is "right", a gate that disagrees with the check it is
standing in for is not a gate. No test covers the boundary —
`test_new_is_refused_over_the_tier_one_cap_and_names_both_numbers` uses a
581-line body, which is 281 lines clear of the disagreement.

### F3 — criterion 7's assertion covers two of the four paths it names

- `tests/test_phase_lifecycle.py:86-93` (`phase_hash`), `:95-103` (`refused`)

M-C is green. Criterion 7 says `linkage.jsonl` and `okr.jsonl` in as many
words; neither is hashed. The author's evidence table marks criterion 7 "Met"
on a sentence — "hashes all of `phase/`" — that is true and is not what the
criterion asks for.

The *behaviour* is fine, and I enumerated it rather than sampling it. I built
every refusal `phase_command` can raise, each on its own fixture copy, and
hashed the **whole project tree** before and after. All sixteen refuse with
exit 1 and move no byte anywhere: `new` × no-OKR / active / bad-slug /
no-Status-header / over-cap; `activate` × unknown-number / already-active /
scored / another-active; `close` × nothing-active / unknown-number /
not-the-active-one / no-Status-header / already-scored / snapshot-exists. (The
seventeenth, `new`'s `target.exists()` at `:4755`, is unreachable: the number
is always `max+1` over the same glob that would have to contain the
collision.) The three `--dry-run` modes likewise move nothing, including
`.perry/events.jsonl`.

So F3 is a gap in what is *asserted*, not in what the code does — but criterion
7 is a statement about the assertion.

### F4 — a refusal criterion 5 names has no test and no mutant

- `bin/perry-goals:4840-4842` — `close`'s `if hit[1] == "scored"` refusal

M-E deleted it and **the whole affected tier stayed green**. Criterion 5 names
two refusals for `close` ("refused when the named phase is not the active one,
**and when its `**Status**` is already `scored`**") and the spec's Verification
section requires one test per named refusal, each shown red under its own
mutation. `tests/test_phase_lifecycle.py` has
`test_close_is_refused_on_a_phase_that_is_not_the_active_one` and nothing for
the second; the result file's mutant table has M7 for the first and no entry
for the second. Nine of the sixteen refusals above have a test at all.

### F5 — minor: `activate`'s gate order loses the sentence criterion 4 asks for

- scored gate `bin/perry-goals:4802-4807`, active gate `:4808-4811`

The scored check runs first, so when another phase is active *and* the target
is scored, the refusal says "phase X is scored" and never names the active
phase. Criterion 4 requires the refusal to name it. It is still a refusal and
still writes nothing; the ordering is the only thing at issue.

## Criteria, one verdict each (the spec's Bound)

| AC | Verdict | Why |
|---|---|---|
| 1 | **Not met** | numbering, body, lock and `CURRENT` are right; the `Started`/`Status` stamp silently no-ops — F1 |
| 2 | Met | refusal names the prerequisite, whole tree unmoved (R1) |
| 3 | **Not met** | cap read from the schema, but counted differently from `perry-lint` — F2 |
| 4 | Met | `new` and `activate` both refuse and name the active phase (R2, R10); ordering nit F5 |
| 5 | **Not met** | the in-place flip crashes half-written on a document `splitlines()` splits differently — F1; the already-scored refusal is untested — F4 |
| 6 | Met | all three modes take `--dry-run` and move no byte anywhere; all three exit 2 without `--actor` |
| 7 | **Not met as written** | behaviour holds on all 16 refusals; the hash omits `linkage.jsonl` and `okr.jsonl` — F3 |
| 8 | Met | `phases.md § Writing it`, `planning.md`, `goals/SKILL.md` ×2, `setup.md` all describe the writer and all still declare the overall-OKR author missing |
| 9 | Met | `DRAFT_MISSING` keeps one clause; `test_goals_writer` now asserts its identity, not only the count |

## On the author's own result file

Treated as claims. Most hold: the base/head are what they say, the five guard
refusals listed did happen and were not waved through, the M10 story is
accurate and the current test plants `003-copy.md`, which does match the glob.
Two do not: "12 mutants … **No survivors**" is true only of the twelve chosen —
M-C and M-E are survivors in code this row added — and the criterion 7 row
reads "Met" for an assertion that covers half of what the criterion names.

## What I did not check

- **The full and slow tiers.** Only `--tier affected --base 8a081790`, plus
  single-module runs under mutation. The author did not claim them either.
- **`perry-lint --reviews` on this document.**
- **Concurrency.** `project_lock` is taken, but I did not race two `phase`
  invocations, and I did not check crash-recovery beyond the F1 case.
- **i18n.** No Chinese-language phase document was exercised; `phase_header`
  matches an ASCII `**Started**` / `**Status**` literal and I did not check
  whether a translated phase template spells those cells differently.
- **`refuse_write_unless_installed` / ADR-019 behaviour** on a pre-ADR-019
  project. I ran only against `tests/fixtures/sample-project`.
- **The event records** `phase-new|activate|close` append to
  `.perry/events.jsonl` — I confirmed one is written on a write and none on a
  dry run, but did not check the record against any consumer or schema.
- **`tests/durations.json`.** The `null`/`null` entry is what the suite calls
  "unmeasured" and the run accepted it; I did not verify that claim against
  `tests/parallel`'s own rules.
- **`goals/SKILL.md` router budget and the reference-page reachability guards** —
  they are in the affected tier and green, and I did not mutate them.

=== VERDICT ===
task: TASK-474
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-474-spec.md
checked: read the change at ac256a3a in an isolated worktree; ran `bash tests/run --tier affected --base 8a081790` green (70 modules / 2043 tests / 205.2s) as the baseline; six line-anchored mutations with __pycache__ purged and the clock advanced past a whole second on both sides, each restore verified by `bin/perry-restore-check ac256a3a bin/perry-goals`; constructed the fire-case for both edited guards (M-A2 red on test_blank_cell_is_one_rule, M-B red on test_okr_store_is_the_source) and confirmed neither edit is a relaxation; enumerated all six phase write sites and confirmed each goes through the assert_owned wrapper and is built from state_root/"phase" with a regex-checked slug; enumerated and exercised all sixteen refusals phase_command can raise, each on its own copy of tests/fixtures/sample-project with a whole-project byte hash before and after — all sixteen refuse and move nothing; confirmed the three --dry-run modes move nothing including .perry/events.jsonl; confirmed by mutation that phase_hash does cover phase/CURRENT and phase/snapshots and does not cover linkage.jsonl or okr.jsonl; reproduced the splitlines/split index defect on a fixture copy in both its forms; measured the cap boundary at exactly 300 written lines against bin/perry-lint. Nothing ran against /Users/bytedance/proj/Perry/perry.
not-checked: the full and slow tiers (only --tier affected); `perry-lint --reviews` on this review; concurrent/racing `phase` invocations and crash recovery beyond the F1 case; any non-English phase template (phase_header matches an ASCII `**Started**`/`**Status**` literal); `refuse_write_unless_installed` on a pre-ADR-019 project; the shape of the `phase-*` event records against any consumer; whether `tests/durations.json`'s null entry satisfies tests/parallel's own rules; the SKILL router-budget and reference-reachability guards (green in the affected tier, not mutated).
proof: bin/perry-goals:4676 — `splice_header` indexes `lines = text.split("\n")` with the index `phase_header` produced from `text.splitlines()` at bin/perry-goals:4656. On a phase document carrying two characters `str.splitlines()` breaks on and `"\n"` does not, `perry-goals phase close` raised an unhandled IndexError at bin/perry-goals:4678 AFTER writing phase/snapshots/2026-09-20-002-release-pipeline-final.md, leaving `**Status**` unflipped and phase/CURRENT unchanged — and every retry then refuses at bin/perry-goals:4847 because the snapshot exists. With one such character it is worse-behaved still: `phase new` exits 0, writes phase/CURRENT and reports `"status": "active"` while leaving `**Started**: {{YYYY-MM-DD}}` and `**Status**: active | scored` unstamped (criteria 1 and 5). Also bin/perry-goals:4769 — the cap gate counts `len(text.splitlines())` where bin/perry-lint:846 counts `raw.split("\n")`, so a 300-line body is written and then reported `[size-cap] 301 lines, over the tier-1 cap of 300` (criterion 3). Also tests/test_phase_lifecycle.py:86-103 — the per-refusal hash omits `linkage.jsonl` and `okr.jsonl`, which criterion 7 names; a mutation making a refusal overwrite both stayed green. Also bin/perry-goals:4840-4842 — deleting `close`'s already-scored refusal, which criterion 5 names, leaves the whole affected tier green.
=== END VERDICT ===
