# TASK-475 V4 review, round 2 — `perry-goals objective add`

Date: 2026-09-21. Reviewer: Review Agent (Claude Opus 5), fresh context. I did not write this
code and did not write round 1.

Under review: the whole delivery `801cf912..6064ca6f`. Round 2 itself is `a0e5e51a..6064ca6f`
(c6d706ea, 6064ca6f), merged at `7d7e9605`. The worktree was fast-forwarded to `90b88d0b`,
where `bin/perry-goals` and `viewer/parsers.py` are byte-identical to `6064ca6f`.

**Criteria.** The task record has no Deliverable or Verification text, so, as round 1 did, I
reviewed against the TASK-475 entry in `perry/journal/2026-09/2026-09-21.md` (§ New tasks
added):

- *Deliverable*: refusals for a phase that is missing or scored, a bad id and a **reused id**.
- *Verification*: `objective add O1` then `kr add P<NNN>-O1-KR1 --objective O1` both succeed
  and `krs` lists the KR; **each refusal writes nothing**; deleting each refusal's guard
  turns its test red.

**Method.** All probes and mutations ran on a `git archive 6064ca6f` copy under the
`perry-scratch-derivation` directory, which is outside the repository. I ran no write-side
Perry tool against this repository's `perry/`.

## F1's fix holds

The round-1 input was a git conflict marker appended to `linkage.jsonl` on a phase that
already declares O1. On that input, `objective add O1` and `objective add O2` now both exit 1,
and the store and the event log are byte-identical before and after. The same is true of a
truncated last JSON line with no newline, a UTF-8 BOM, a non-UTF-8 byte, and a store that is
a directory. An absent store is still created by the first `objective add`.

## The category: a store that is present but not usable as read

| input (existing store) | `objective add` | what the readers do |
|---|---|---|
| unparseable line / truncated JSON / BOM / non-UTF-8 / directory | refused, nothing written | `load_linkage_store` → `None` |
| non-dict line (`[1, 2]`, `42`, `null`, `"s"`), dup O1 | refused, nothing written | skip the line; lint reports `linkage-store-malformed` |
| non-dict line, new O2 | written; readers show it | same |
| record missing `kind` / `phase` / `id` | O1 written; one O1 is visible | the malformed record is ignored; lint names it |
| CRLF store, dup O1 | refused; a new O2 is appended LF-terminated and read back | parses (`\r` is JSON whitespace) |
| existing id `o1`, ` O1`, `O1 ` | O1 written; one O1 is visible | the malformed id is ignored; lint names it |
| existing id `O01` | O1 written | the schema pattern admits both ids; distinct objectives |
| empty file / blank lines / no final newline | written, newline repaired | parses |
| same id in a foreign phase | written (per-phase ids, as tested) | per phase |
| O1 whose every KR is withdrawn | refused (the objective is not withdrawn; there is no objective revision kind) | — |
| **same id, same phase number, phase slug spelled differently** (`<NNN>-other`, `<NNN>-fresh ` with a trailing space, `<NNN>-FRESH`) | **written, exit 0: a second O1** | **both O1 records are in the phase; `krs` lists O1 twice** |
| same id, phase spelled `<NNN>` with no slug | written | the reader drops the bare-number record; one O1 |

## Finding F2 — the reused-id refusal keys on the slug; every reader keys on the number (FAIL)

**Why.** `cmd_objective` decides "the phase already declares O1" with
`str(r.get("phase") or "") == slug` (`bin/perry-goals:4412-4414`, @6064ca6f). This is an
exact match on `<NNN>-<slug>`. The reader every consumer goes through,
`linkage_records_for_phase`, assigns an objective to a phase by
`str(r.get("phase") or "").startswith(f"{phase_number}-")` (`viewer/parsers.py:4475`,
`:4485`). This is the phase **number**. `linkage_from_store` then emits one objective per
record (`viewer/parsers.py:4414-4421`). So any record the reader places in this phase and the
guard does not see is written a second time, and the second record is read.

**Input a user can produce, with no hand edit to the store.** A phase is planned, then its
slug is renamed:

1. The phase is planned: `objective add O1`, then `kr add P<NNN>-O1-KR1`.
2. The user renames `phase/<NNN>-fresh.md` to `phase/<NNN>-renamed.md` and points `CURRENT`
   at the new name.
3. `krs` still lists `O1` with its KR. It is correct to, because it reads by number.
4. `kr add P<NNN>-O1-KR2 --objective O1` refuses with "it has none". That false message
   comes from the same exact-slug rule, at `:4187`.
5. The remedy the user reaches for is `objective add O1`. It **exits 0** and appends a
   second O1 plus an `objective_add` event.

**Effect.**

- `perry-goals krs` lists `[O1 [P<NNN>-O1-KR1], O1 [P<NNN>-O1-KR1]]`.
- `perry-state --json` publishes `phase.kr_total: 2` for a phase that has one KR.
- `perry-lint` reports `0 malformed` and no linkage finding for the duplicate, so nothing
  tells the user.

Appending the same record to a fresh phase gives the same result for the spellings
`<NNN>-other`, `<NNN>-fresh ` and `<NNN>-FRESH`.

**Against the criteria.** The Deliverable requires a reused-id refusal, and the
Verification requires that each refusal writes nothing. The refusal is skipped for an id
that the phase already declares, as the tools that report on the phase define "the phase".
The write double-counts in a published number. This answers yes to review.md § 0's second
question.

**The fix is named, and there is no fork to decide.** Key the reuse check on the phase
number, the way the reader does. Filter with
`P.linkage_phase_number(str(r.get("phase") or "")) == P.linkage_phase_number(slug)` in place
of the exact-slug comparison. Then add a test that pre-seeds an O1 under a differently
spelled slug of the same number.

**The rest of the category, enumerated.** `grep -n 'get("phase") or "") == '` over `bin/`
finds three sites, all in `bin/perry-goals`:

- `:4414`, this row's guard. It writes a duplicate.
- `:4187`, the `kr add` objective membership check. It refuses, with a false "it has none".
- `:4249`, the `kr add` per-objective active-KR cap count. It undercounts after a rename, so
  the cap can be bypassed.

The last two predate this row. They are the same identity split and should be filed as their
own row, not charged here.

## Mutation — round 2's guard and its neighbours

Method for each mutant:

- anchored by line number, with the anchor text asserted before the edit;
- `__pycache__` purged, and more than 1 s waited on each side of the edit;
- `tests/test_goals_objective_add.py` run on the copy;
- restored from `git show 6064ca6f:bin/perry-goals`, and the restore compared byte for byte
  against that output.

After the loop, `cmp` against `git show` output matched for `bin/perry-goals`,
`tests/test_goals_objective_add.py` and `viewer/parsers.py`. `bin/perry-restore-check --root
<copy> 6064ca6f` refuses a non-git copy with exit 2, as it did in round 1, so the comparison
was done by hand. The unmutated module is green.

| mutant (`bin/perry-goals` @6064ca6f) | result | red test |
|---|---|---|
| R1 unreadable-store guard deleted (4403) | red | `test_an_unreadable_store` |
| R2 guard also refuses an absent store (4403) | red | `test_the_first_phase_creates_the_store` |
| R3 reuse refusal deleted (4415) | red | `test_an_id_the_phase_already_declares` |
| R4 reuse not scoped to phase (4414) | red | 4 tests, including `test_the_same_id_in_another_phase_is_not_a_reuse` |
| R5 non-dict filter removed (4411) | **green** | none |

R5 is green, but it is not a write defect. Without the filter, a non-dict line makes
`r.get` raise before any write. The line is untested, and the consequence is a traceback
instead of a refusal. I report it as an observation, not a FAIL.

## The PMO's edit to the round-1 verdict

`git diff a0e5e51a 6064ca6f -- perry/evidence/2026-09/TASK-475-v4-review.md` shows two
changes:

- one added note at the top;
- four replacements of the concrete fixture KR id with `P<NNN>-O1-KR1`. One is in the
  Verification walk-through, one in the `krs` result, one in the readers bullet and one in
  `checked:`.

`result:`, `grade:`, `proof:` (still citing `:4402`, `:3879-3880` and `:4406` @4414ddee), F1's
text, the mutation table and every other line are unchanged. **No finding changed.**

## Test tier

`bash tests/run --tier affected --base 801cf912` on the worktree at `90b88d0b` selected 83 of
162 modules, and 3 slow-tier modules were held back. 80 modules and 2309 tests passed, green
for affected. This is not a green suite.

## Not checked

- The full suite and the slow tier.
- The viewer front end beyond `parsers.load_linkage` and `perry-state --json`.
- Locking and concurrency.
- Whether Perry's procedure forbids renaming a phase slug by hand. I found no verb that
  renames one and no lint that objects.
- R5's traceback path was not run. That no write happens is by reading.
- Windows paths.
- SkyTonight.
- The round-1 mutants M1–M13 were not re-run on the new base. R3 and R4 re-cover M7 and M8.

**This is round 2's FAIL on this row.** Under review.md § 6 no third round is dispatched.
The next step is the escalation ask. It names F2's fix above and says plainly that no
principle is in dispute.

=== VERDICT ===
task: TASK-475
rung: V4
result: FAIL
grade: FAIL — Deliverable "refusals for … reused id" + Verification "each refusal writes nothing"
criteria: perry/journal/2026-09/2026-09-21.md
checked: on a git-archive copy of 6064ca6f: F1 input and 5 other unparseable-store shapes refused with store and log unchanged; non-dict, missing kind/phase/id, CRLF, id case/whitespace/O01, empty/blank/no-final-newline, foreign-phase and withdrawn-KR inputs; same-number differently-spelled phase (rename route) writes a duplicate O1 that krs lists twice and perry-state counts as kr_total 2; 5 mutants (4 red, 1 green, no write consequence) with restores compared to git show; PMO edit to the round-1 verdict diffed; affected tier 80/2309 green on 90b88d0b
not-checked: full suite; slow tier; viewer UI; locking; whether a hand rename of a phase slug is sanctioned; R5 traceback path by run; round-1 M1-M13 on the new base; Windows; SkyTonight
proof: bin/perry-goals:4412-4414 dedupes objectives by exact `phase == slug`, while viewer/parsers.py:4485 places them by phase number; with an O1 recorded under a differently spelled slug of the current phase number, `objective add O1` exits 0 and appends a second O1 that krs lists twice
=== END VERDICT ===
