# TASK-472 — V4 review (round 2)

Reviewer: independent V4 agent, fresh context, not the author. Date: 2026-09-21.
Criteria: `perry/evidence/2026-09/TASK-472-spec.md`, the only authority for PASS/FAIL.
Under review: `e4e092ec..009a8a31` (branch `coding/task-472-round2`, merged to main at `78a9c5fa`).
Base the criteria exist on: `e4e092ec`, the same base. `git diff e4e092ec 009a8a31` does not touch the spec, and the spec resolves at both ends.
Round 1: `perry/evidence/2026-09/TASK-472-v4-review.md`. It FAILed criteria 1 and 6, and I did not rely on its PASSes.

**Result: PASS.** All three round-1 findings are fixed, and all six criteria
hold at `009a8a31`. The known M5 gap still stands: a retraction placed outside
a span's anchors is not caught. I reproduced it three ways. No criterion asks
for that guard, so I do not charge it as a FAIL. The disclosure of it is also
incomplete: the test comment that makes the false claim was never corrected
(§ 4). The evidence has three further defects that I record but do not charge,
per `review.md § 2 What V4 does not judge` (§ 3, criterion 6).

---

## 0 · Environment

- **The worktree started stale.** `.claude/worktrees/agent-a574f183b659ffadb`
  (branch `worktree-agent-a574f183b659ffadb`) was cut at `0b5bf99e`
  (2026-09-15), which is not a descendant of `009a8a31`. The branch had no
  commits of its own and a clean tree, so I fast-forwarded it with `--ff-only`,
  first to `009a8a31` and then, on the PMO's instruction, to `359a7be1`.
  `git rev-parse HEAD` then gave `359a7be16844df61437d99eb857cc940e2a5d3f8`.
  `009a8a31..359a7be1` touches only `.perry/events.jsonl`,
  `perry/journal/…/2026-09-21.md` and `perry/tasks.jsonl`. `git diff --quiet
  009a8a31` over every file I tested or cited below exits 0.
- **Nothing was run against the stale tree except one read.** At the very start
  I read `review-constraints.md` from `0b5bf99e`. After the fast-forward I
  re-read it at `009a8a31`, and every judgement below is made from the
  `009a8a31` text.
- **Scratch.** The brief says to use dispatch.md's `perry-scratch-derivation`
  block. This host refuses to run it verbatim, because the harness rejects
  `$(git …)` command substitution in an isolated agent's shell. So I ran its two
  parts separately: `git -C <worktree> rev-parse --show-toplevel` →
  `basename` → `${TMPDIR}/perry-scratch/agent-a574f183b659ffadb`. The result is
  the same path the block would give. The directory was new and empty when
  created, so it is not shared with the author (`perry-scratch/t472-r2`,
  `t472-merge`) or with the session scratchpad that round 1 and the author
  shared. Everything I wrote lives there. Below it is written as `<scratch>`.
- **Mutations** ran only on `<scratch>/copy`, a `git archive 009a8a31`. I did
  not edit the live checkout or my worktree's tracked files. The only file I
  added to the worktree is this verdict.

## 1 · The suite

I ran `bash tests/run --tier affected --base e4e092ec` in my worktree. Result:
**exit 0**, 45 of 161 modules, 1,361 tests, 56.4 s, 8 workers, tree guard
clean. `test_host_support` was selected and passed, so TASK-272's flake did
not occur and I re-ran nothing. A green in `affected` is not a green suite: 116
modules did not run. Log: `<scratch>/affected.log`.

I did not run the full suite. The change is 31 lines of prose, one digest and
two evidence files. The tier selected every module that covers
`work/reference/` and `tests/test_spec_scannability.py`. The mutations below
target the one guard over this prose directly. That left no concern a full run
would settle. The author's two full runs are on disk and I read their totals:
`perry-scratch/t472-r2/full.log` 157 modules / 4434 tests / 108.2 s green, and
`perry-scratch/t472-merge/full.log` 157 / 4434 / 127.4 s green. I did not
re-run them.

## 2 · Mutations

I ran 10 mutants plus 2 on `bin/perry-lint`. Each one was anchored by line
number, and the harness asserted the anchored line's text before editing. Before
each run I purged `__pycache__` and waited past a whole second. I checked each
restore against `git show 009a8a31:<path>`, not against a snapshot. I added
controls before and after: E0/E1 and D0/D9, all OK. As a final check I
compared all five touched files in the copy with `cmp` against the worktree,
whose `git diff --quiet 009a8a31` is clean. All were identical. The modules
were `test_spec_scannability`, `test_scratch_is_per_agent`,
`test_reference_pages_are_reachable`, `test_shipped_vocabulary` and
`test_one_choke_point` (161 tests), or `test_review_verdicts` for the D
mutants. Per-mutant logs: `<scratch>/logs/`. Table: `<scratch>/mutants.json`.

| Mutant | Site (009a8a31) | Result |
|---|---|---|
| N1 batch section deleted | `review-constraints.md:84-99` | **RED**, governed pin, constraints span |
| N2 batch rule inverted ("one per turn, never together") | `review-constraints.md:86` | **RED**, same |
| N3 the `$$` second recipe re-added inside the span | after `review-constraints.md:62` | **RED**, same |
| N8 canonical block renamed (`# scratch-derivation`) | `dispatch.md:116` | **RED**, dispatch pin + 2 `test_scratch_is_per_agent` tests |
| N9 the section the pointer names renamed | `dispatch.md:33` | **RED**, 1 fail + 7 errors (anchor missing) |
| N10 canonical block given a `-$$` suffix | `dispatch.md:117` | **RED**, dispatch pin + `test_the_path_is_stable_across_invocations_in_one_tree` |
| N11 retraction before `### The four rules` | `review.md:223` (inside § 2 span, the end anchor is exclusive) | **RED**, `review.md § 2 the prompt` |
| **N5** retraction of the batch and scratch rules, one line past the end anchor | after `review-constraints.md:133` | **GREEN, survived** |
| **N7** same retraction appended at end of file | after `review-constraints.md:198` | **GREEN, survived** |
| **N12** same retraction one line before the start anchor | after `review-constraints.md:53` | **GREEN, survived** |
| D1 two-FAIL stop disabled (`< limit` → `< limit + 97`) | `bin/perry-lint:3222` | **RED**, 11 fail / 8 error |
| D2 built-in round limit `2` → `99` | `bin/perry-lint:2653` | **RED**, `test_a_schema_declaring_zero_is_refused_as_well` |

The retraction text was: *"When this does not apply. On a short round,
batching a mutation with the run that tests it is the accepted practice, and a
fixed scratch name under a shared root is fine."*

N8–N10 are the invariant the scratch fix depends on. The pointer names
`dispatch.md § The tree the agent works in` and the block headed
`perry-scratch-derivation`, so the page it points at has to stay what it says.
Renaming either target, or making the block per-shell, reddens a named test.
The pointer cannot go stale from dispatch.md's side without a test going red.

I recomputed all seven `GOVERNED_SHA` digests with the test's own
`governed_text()`, and all match. The re-pin comment's figures are exact:
4,212 chars / 78 lines, and `git diff --numstat` gives 31 in / 8 out. The
constraints span covers lines 54–133 of 198 and contains the new batch section.
`e4e092ec..009a8a31` changes no line of `review.md`, `dispatch.md`,
`autopilot.md` or `bin/`. `17da62fc..e4e092ec` changes none of the in-scope
files, so the new base brings in nothing the round-1 checks did not see.

## 3 · The six criteria

### Criterion 1: PASS

*Batch half.* `review-constraints.md:84-98` states it:
*"Reads that do not depend on each other go out together"*, and *"Everything
with an order stays in order: a mutation and the run that tests it, a restore
and the check that verifies it, a write and the read that confirms it, anything
that needs someone's approval first."* That covers dependent actions,
mutations and approvals, which are the three things the criterion lists. The
section sits inside the governed span, and N1 and N2 kill it.

*Scratch half.* The second recipe is gone. I checked the whole category rather
than the one site: every scratch recipe under `work/`
(`grep perry-scratch|PERRY_SCRATCH|$$|rev-parse --short|mktemp`) is either the
canonical block at `dispatch.md:116-118` or a mention of it. The only `$$` and
`--short HEAD` left are in `review-constraints.md:65-67`, which explains why the
old recipe was removed. `digests.md:300`, `dispatch-preflight.md:10-12` and
`review.md:596` mention scratch without giving a recipe. The pointer is
accurate: the block is repository-derived and stable across commands. N3
reddens if the recipe is re-added inside the span.

Residual, not charged: the pointer's uniqueness is only as strong as worktree
isolation. `dispatch.md:138-143` says this itself, and dispatch.md's worktree
rule "governs every executor", but neither `review.md` nor
`review-constraints.md` says a V4 reviewer must be isolated. A reviewer
dispatched without the flag would resolve to `perry-scratch/Perry`, which the
primary checkout already uses (files there from 2026-09-18/19). The rule that
closes that gap exists and is one link away, so I do not count it as a missing
deliverable.

### Criterion 2: PASS

`review-constraints.md:100-114` is unchanged, byte for byte, from round 1:
success returns status and paths; failure keeps the exit code, a diagnostic
excerpt and the full log path; structured output is filtered structurally or
kept whole; truncated JSON is never fed back. Round 1 found that the old `$$`
recipe made *"which still exists"* false in practice. The stable derivation now
makes it true, and I used it for this round's logs.

### Criterion 3: PASS

`review-constraints.md:116-131` is unchanged and pinned: completion event
preferred, a bare `&` opts out, bounded polling otherwise, record calls and
waits, no scheduler, and a tool-call count is not a model-turn count. I ran
the affected tier and the N-mutant harness through the host's background
mechanism, and each returned on its own notification. I wrote no polling loop
and used no `&`.

### Criterion 4: PASS

`review.md § 2` is unchanged in this range, and its digest matches. The
template carries `<base SHA>..<head SHA>` and a *Base the criteria exist on*
line, and says that a changed base re-opens scope to *"every invariant they
touch"* (`review.md:215-218`). N11 reddens inside the span. This round's brief
followed the template, with both SHAs and the base named. Fresh V4 independence
(`§ 0`, `§ 4`) is untouched.

### Criterion 5: PASS

`review.md § 6` is unchanged, and its digest matches. I re-ran the stop by
mutation instead of trusting round 1: D1 and D2 both go RED, so the two-FAIL
stop in `bin/perry-lint` is still live and tested. `review.md:497-529` says to
name the unresolved criteria and the decision needed, not to re-ask the
principle, not to widen scope silently, and not to let the author raise its own
threshold. Nothing in the range authorises another round.

### Criterion 6: PASS

*Sentence 1.* `perry/evidence/2026-09/TASK-472-traces.md` exists and has one
reviewed-delivery trace and one small-change trace, each set against a baseline.
I re-derived Trace 1's baseline from the logs on disk. The logs are in the
session scratchpad, not in `perry-scratch`. I classified each run by its last
line, as the file says it did. There are 10 full-suite runs and 3 of them end
`✗ failures above`: `t474-full`, `t474-final` and `r3-merge`. The red reasons
match. `t474-final` is `test_no_other_subcommand_writes_OKR_md`. `r3-merge` is
`test_host_support…global_cap`, which is TASK-272 and the same failure as
`t469-merge`. `t474-full` has 5 failing tests, which the file describes as
"four guards … four real defects". I did not check whether 5 tests are 4
defects. The file concludes that the contracts are *not demonstrably* cheaper,
and that is what the evidence supports. The criterion asks for a comparison,
not a saving, and the spec says missing telemetry is to be recorded as unknown.

*Sentences 2–3.* `review.md § What the reviewer runs` is unchanged, and its
digest matches. The author's round-2 practice matches the trace: one targeted
module per step, one justified full run on the branch and one on the merge.

**Three defects in this evidence. Recorded, not charged.** `review.md § 2
What V4 does not judge` puts an incomplete exhibit on the author and a false
statement in an evidence file under "file a row", never a FAIL:

1. **Two placeholders were committed and never filled.**
   `TASK-472-traces.md:52-53` read *"(appended when run)"* for *Final
   verification* and *Merge-result verification*, and they still read that on
   main at `359a7be1`. The final run appears only in a second table (`:111`).
   The merge run (`t472-merge/full.log`, green) is not recorded anywhere in the
   file.
2. **Trace 2's baseline cannot be re-derived from the logs.**
   `TASK-472-traces.md:7-8` says *"every count below can be re-derived"* from
   the logs on disk. `:58-59` gives TASK-469 round 3 as running
   `test_startup_routing` and `test_context_budget` (61 tests) first. I found no
   log with that run: no `Ran 61 tests` anywhere in the session scratchpad or
   `perry-scratch`, and nothing in `TASK-469-round3-result.md`. The only TASK-469
   round-3 logs on disk are two **full** runs, and the first of them
   (`t469r3.log`) is red on `test_context_budget`. That is hard to square with a
   targeted run of that module having passed just before. The claim may be true.
   It is not supported by the source the file names.
3. **The traces count full-suite runs only.** Neither side includes the
   reviewer's commands, repeated reads or tool calls. The spec's Deliverable
   asks for evidence about *"repeated reads and tool turns"*. The file's
   "not demonstrably" conclusion is honest, and it is answering a narrower
   question than the Deliverable asks.

## 4 · The M5 disclosure, judged against the criteria

`TASK-472-result.md:143-159` reports M5 as a survivor that was left open on
purpose. I reproduced it three times: N5, N7 and N12 all stayed green, and the
retraction took back **both** round-2 fixes at once. So anyone can undo
criterion 1's batch rule and scratch rule from one line outside the span, and
nothing turns red.

This is not a FAIL. Criteria 1–6 are about what the contracts say, and none of
them asks for a guard. The Bound rules out *"new review categories"*, and a
vocabulary-containment check would be new machinery that no criterion asks for.
The disclosure is also accurate as far as it goes. Round 1 reached the same
conclusion, and on this base I reached it independently.

**The disclosure is incomplete in one place, and that matters more than the
gap.** `TASK-472-result.md:59-60` says *"'There is no gap between regions to
insert into' was false … Corrected 2026-09-21."* Only the result document was
corrected. The test still says it:

- `tests/test_spec_scannability.py:854-855`: *"as one contiguous span so there
  is no gap between them to insert a retraction into"*
- `tests/test_spec_scannability.py:868`: *"A span has no beside."*

Round 2 edited this same file at `:928-940`, 60 lines further down, and left
both sentences in place. N5, N7 and N12 show they are false for this span.
(`:808` makes the same claim about the dispatch spans, where the
`worktree|isolation` containment check makes it true. That one is not a
defect.) Under `review.md § 2` this is *"a comment … misstates something → file
a row"*, not a FAIL. Anyone reading the test will still be told the span is
closed.

## 5 · Did the pages under review steer this round?

- **The batch rule was the right rule, and I broke it once.** I ran a read-only
  digest check against `<scratch>/copy` while the mutation harness was running
  against the same copy. That is a check with an unknown state behind it, which
  is exactly what `:91-95` warns against. The digests all matched, and three of
  my mutants sit outside every span, so a match alone does not prove the copy
  was clean at that moment. I re-ran the check after the harness finished. The
  numbers in § 2 come from that second run.
- **The completion-event contract saved polling.** Both long runs returned on
  their notifications.
- **`review-constraints.md § Verify a restore` gave advice that did not work
  here.** It says to use `bin/perry-restore-check --root <copy>`, but that
  refuses a `git archive` copy (*"is not a commit in …/copy"*, exit 2) because
  the copy is not a repository. So I verified by hand against `git show`, which
  the section allows. That advice predates this row (`17ac69cc`, TASK-256), so
  I record it for triage and do not charge it.
- **The brief conflicted with the constraints page on committing.**
  `review-constraints.md § The repository is live` says *"Do not commit"*. This
  round's brief says to commit only the verdict file. I followed the brief,
  because it is the specific instruction for this round, and I committed nothing
  else.

## 6 · For the PMO

The row PASSes. It carries two small documentation defects, which are row
material under `review.md § 2`:

1. Strike or qualify `tests/test_spec_scannability.py:854-855` and `:868` so
   they match `TASK-472-result.md:59-64`.
2. Fill or delete the placeholders at `TASK-472-traces.md:52-53`. Either cite a
   log for the 61-test baseline at `:58-59`, or mark it as recalled rather than
   rebuilt.

The M5 gap is also open for anyone who wants to close it. It is a
containment check over the contracts' own vocabulary, the way
`test_every_mention_of_the_rule_is_inside_a_governed_region` does for
`worktree|isolation`. No criterion asks for it.

---

=== VERDICT ===
task: TASK-472
rung: V4
result: PASS
criteria: perry/evidence/2026-09/TASK-472-spec.md
checked: Round 2, e4e092ec..009a8a31, merged at 78a9c5fa. I re-derived all six criteria from the spec at base e4e092ec and did not rely on round 1's PASSes. The worktree was cut stale at 0b5bf99e; I fast-forwarded it to 009a8a31 and then 359a7be1, and the in-scope files are identical to 009a8a31. `bash tests/run --tier affected --base e4e092ec` exited 0: 45 of 161 modules, 1361 tests, 56.4s, test_host_support selected and green. I ran 12 mutants on a `git archive 009a8a31` copy, each anchored by line, with __pycache__ purged, a wait past the second boundary, restores verified against `git show 009a8a31:<path>`, and controls before and after. These were RED: N1 (batch section deleted, review-constraints.md:84-99), N2 (batch rule inverted, :86), N3 (`$$` recipe re-added inside the span, :62), N8, N9 and N10 (dispatch.md:116, :33 and :117, the canonical block and section the new pointer names), N11 (review.md:223 inside the § 2 span), D1 and D2 (bin/perry-lint:3222 and :2653, the two-FAIL stop). These were GREEN: N5, N7 and N12, a retraction of the batch and scratch rules placed after review-constraints.md:133, at end of file (:198) and before the span's start (:53). That reproduces M5 three ways. I recomputed all seven GOVERNED digests with the test's own governed_text(); all match, and the re-pin comment's 4212 chars / 78 lines / 31 in / 8 out is exact. I grepped all of work/ for other scratch recipes and none remain. I re-derived Trace 1's baseline from the on-disk logs, classified by last line: 10 runs, 3 red, and the red reasons match. I read the totals of the author's branch and merge full runs (157/4434 green, both).
not-checked: Full suite and slow tier: I ran neither, and relied on the author's logs. The 116 modules outside the affected tier. The canonical scratch block run verbatim (the host refuses `$(git …)`; I ran its two parts separately). Whether `t474-full`'s 5 failing tests are the "four defects" the trace names. Whether TASK-469 round 3 ran a 61-test targeted pass (I found no log). The mutants against modules other than the five named plus test_review_verdicts. Any token or model-turn cost. perry-lint --reviews over this verdict (the brief rules out running anything against perry/ state). bin/perry-restore-check (it refuses a non-git copy, so I verified restores by hand). Whether the six 2026-09-20 incidents the contracts cite happened as described.
proof: PASS. Recorded for a row, not charged: tests/test_spec_scannability.py:854-855 and :868 still claim "no gap … to insert a retraction into" / "A span has no beside" for the review-constraints span, while TASK-472-result.md:59-60 says that claim was corrected. N5, N7 and N12 disprove it. perry/evidence/2026-09/TASK-472-traces.md:52-53 carry unfilled "(appended when run)" placeholders. TASK-472-traces.md:58-59 gives a 61-test baseline that no on-disk log supports, although :7-8 says every count can be re-derived.
=== END VERDICT ===
