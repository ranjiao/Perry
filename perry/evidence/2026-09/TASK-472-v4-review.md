# TASK-472 — V4 review (round 1)

Reviewer: independent V4 agent. Date: 2026-09-21.
Criteria: `perry/evidence/2026-09/TASK-472-spec.md` — the only authority for PASS/FAIL.
Under review: `1c28cce7..17da62fc` (branch `coding/task-472`, merged to main at `25cb21d7`).
Base the criteria exist on: `1c28cce7` — checked, `git show 1c28cce7:perry/evidence/2026-09/TASK-472-spec.md` resolves.

Worked in worktree `.claude/worktrees/agent-aa19e8f69bec60bb4`, branch
`review-472-v4`. **Every mutation was applied to a disposable `git archive`
copy of `17da62fc`** under a session-unique scratch directory; neither the live
checkout nor this worktree's own `work/reference/` was edited at any point.
Nothing was run against this repository's `perry/` state and no write-side
Perry tool was run. Every restore was verified against
`git show 17da62fc:<path>`, not against harness-snapshotted bytes.

**Result: FAIL**, on criteria 1 and 6. Criteria 2, 3, 4 and 5 hold. The guard
question the row puts at its centre resolves half in the author's favour and
half against: the deleted design did have the hole he says it had, and the
replacement has the same hole one boundary further out.

---

## 1 · The suite

`bash tests/run --tier affected --base 1c28cce7` → **exit 0**, 46 of 161
modules, 1,466 tests, 52.0s, 8 workers. `test_host_support` was not selected
and did not run, so TASK-272's parallel-runner flake did not arise and no
re-run was needed. A green in `affected` is not a green suite: 115 modules did
not run, and the findings below are not claims about them.

Full log: `<scratch>/affected-baseline.log`.

## 2 · What the mutations established

Seventeen mutants — A1–A4, B1–B6, C1, D1–D2, E1–E4 — each anchored by literal
text, `__pycache__` purged and the
clock advanced past a whole second on each side, every file restored and
verified against `git show 17da62fc:<path>`. All output kept for both
outcomes; per-mutant logs under `<scratch>/logs/`.

### 2.1 The `GOVERNED` spans do close the inside case

| Mutant | Where | Result |
|---|---|---|
| A1 retraction of criteria 1–3 | inside `review-constraints.md` span | **RED** — `test_the_governed_regions_are_pinned[review-constraints.md § the three execution contracts]` |
| A2 retraction of criterion 4 | inside `review.md § 2` span | **RED** — same test, `review.md § 2 the prompt` |
| A3 retraction of criterion 6 | inside `§ what the reviewer runs` span | **RED** — same test, `review.md § what the reviewer runs` |
| A4 retraction of criterion 5 | inside `§ 6` span | **RED** — same test, `review.md § 6 two FAILs` |
| C1 the scratch rule deleted | inside `review-constraints.md` span | **RED** |

The digests themselves recompute exactly. All seven `GOVERNED_SHA` entries
match, and the four new comments' measurements are accurate to the character:

```
review-constraints.md § the three execution contracts  lines  54..110  2710 chars / 55 lines
review.md § 2 the prompt                               lines 190..223  1499 chars / 32 lines
review.md § what the reviewer runs                     lines 306..349  2400 chars / 42 lines
review.md § 6 two FAILs                                lines 451..541  4784 chars / 89 lines
```

**Nothing rode along.** The whole reference diff `1c28cce7..17da62fc` contains
exactly one deleted line — `-Under review:        <paths / commit range>`, the
template line criterion 4 replaces. Every other change is an insertion. The
constraints span's comment claims "the span is entirely new prose, so the diff
is the span"; checked against the base, lines 51–56 of `1c28cce7` run straight
from `could not have fixed it.` into `## Do not run the write side`, so the
claim is exact. The three `review.md` spans do newly pin a large quantity of
*pre-existing* text — § 6's whole body, § 2's prompt template, the affected-tier
paragraphs — which their comments disclose ("§ 6 entire", "the brief's shape",
"the affected tier"). That is a real widening of what now costs a re-pin, and
it is disclosed rather than smuggled.

### 2.2 Half 1 of the author's argument is true

`perry/evidence/2026-09/TASK-472-result.md:50-52` says the deleted
`tests/test_review_contracts.py` was **measured** to have the hole before it
was deleted. The module never appears in `1c28cce7..17da62fc` — it was written
and removed inside the working session — so a reviewer cannot read it, only
rebuild it. I reconstructed that design from `17da62fc` — the three rules
pinned by digest over their flattened text — and inserted the author's own
retraction three lines below the pinned paragraph:

```
scratch            pin holds = True
failing-output     pin holds = True
completion-event   pin holds = True
=> that module would be GREEN (hole confirmed); retraction is in the file: True
```

The account of why the module was deleted is honest, and deleting it was right.

### 2.3 Half 2 is false: a span does have a beside — **finding**

`TASK-472-result.md:55-56` states the replacement's whole case:

> *"the four regions became `GOVERNED` spans, which pin the span minus its
> declared free blocks — **there is no gap between regions to insert into**."*

and `tests/test_spec_scannability.py:854-855` says the same in the code: *"as
one contiguous span so there is no gap between them to insert a retraction
into"* — restated at `:868` as *"A span has no beside."* The gap is not between the regions. It is **outside the closing
anchor**, and it is enormous.

| Mutant | Where planted | Result |
|---|---|---|
| B1 | `review-constraints.md:111`, one line past the span's end anchor | **GREEN — survived** |
| B2 | `review-constraints.md:53`, one line before the span's start anchor | **GREEN — survived** |
| B3 | `review.md:224`, under `### The four rules` | **GREEN — survived** |
| B4 | `review.md:350`, under `## 3 · The verdict block` | **GREEN — survived** |
| B5 | `review.md:542`, under `## Completion routing` | **GREEN — survived** |
| B6 | `review-constraints.md`, appended after the final line (176) | **GREEN — survived** |

Each B mutant is a retraction of the contracts the row shipped, in plain
imperative English, e.g. *"**When this does not apply.** On a long run,
dropping failing output to keep the log readable is the accepted practice, a
fixed scratch name under a shared root is fine for a single round, and a bare
`&` is an acceptable way to start a suite."* Six for six, the module is `OK`,
71 tests, no failures.

**A green module is not a green suite either, so B1 was re-run against every
module.** `python3 -m unittest discover -s tests` over the fixture with B1
planted: **4,535 tests, 681.6s**, and the string `review-constraints`,
`scannability`, `governed` and `GOVERNED` appears **zero** times in the whole
failure log. Nothing in the repository catches it. Stated with its limit: that
run reports 5 failures and 9 errors, all of them artefacts of driving the suite
with `unittest discover` inside a non-git `git archive` copy — the
`PERRY_PROJECT`/tree-guard cluster, two git-tracking tests, and
`test_risks_store`'s three `assertIs` identity checks that see the same object
imported under two module paths. I did not take a clean control run of that
same harness, so the claim I am making is the narrow one: **no module named
the retraction**, not "the suite was otherwise green".

**Why the older spans do not have this hole and the new ones do.** The
`dispatch.md` / `git-boundaries.md` / `delegate.md` spans are protected by
*two* mechanisms: the digest pin, and
`test_every_mention_of_the_rule_is_inside_a_governed_region`, which fires on
any line under `work/reference/` matching `worktree|isolation` from outside a
span. That second guard is what makes "there is no beside" true — and it is
keyed to the worktree rule's vocabulary. TASK-472 added four spans and **no
containment check over its own contracts' vocabulary** (`scratch`, `failing
output`, `truncated JSON`, `completion event`, `base SHA`, `flake`, `full
suite`, `threshold`). The author inherited a two-layer mechanism and shipped
one layer.

### 2.4 Rule 1: the category, enumerated

Not "here is another place" but every place. Computing the governed line
ranges over the two files at `17da62fc`:

```
review.md            623 lines, governed 166 (26%)  spans (190,223) (306,349) (451,541)
  ungoverned: 1-189, 223-305, 349-450, 541-623   — 457 lines, 12 headings
review-constraints.md 176 lines, governed  56 (31%)  span (54,110)
  ungoverned: 1-53, 110-176                      —  120 lines, 7 headings
```

**577 of the 799 lines of the two pages this row exists to write are outside
every governed span**, and a retraction placed on any of them is green. Beyond
those two files the same category continues, and I enumerate rather than stop
at the first:

These four were **mutated, not inferred**, against five modules that plausibly
cover them — `test_spec_scannability`, `test_scratch_is_per_agent`,
`test_reference_pages_are_reachable`, `test_shipped_vocabulary` and
`test_one_choke_point`, green together as shipped (`E0`, `OK`, 2 skipped):

| Mutant | Where planted | Result |
|---|---|---|
| E1 | `work/reference/autopilot.md`, appended after line 316 — a *neighbouring page* | **GREEN — survived** |
| E2 | `work/SKILL.md:58` — the *index row* that describes the page, rewritten to call the contracts "advisory" | **GREEN — survived** |
| E3 | `work/reference/review.md:554` — the *second, ungoverned copy* of the reviewer prompt, qualified so the contracts "do not bind this brief" | **GREEN — survived** |
| E4 | `work/reference/dispatch.md:156` — inside the *declared-free rationale block* | **GREEN — survived** |

E3 matters most of the four: `review.md:196` carries
`Read $PERRY_HOME/work/reference/review-constraints.md and follow it` **inside**
the pinned span, and `:554` carries the same line **outside** it, in the
integration reviewer brief. One copy of the pointer is guarded and the other is
not, so a round dispatched through the second brief can be told the contracts
do not apply to it with nothing red anywhere.

One further member of the category, listed but not mutated because it is by
design rather than a defect: `.perry/hook.md`, which `review-constraints.md:8`
invites a project to "add its own on top" in, and which no guard reads.

I did **not** file this as the FAIL. The six acceptance criteria are about the
*content* of the contracts; none of them requires a guard. What it is, is a
verification defect: `TASK-472-spec.md:47` requires "meaningful revert/negative
proof", and the negative proof at `TASK-472-result.md:78-85` is offered for the
proposition "a retraction cannot get in" while establishing only "a retraction
cannot get in *between the anchors*". Six mutants chosen inside the span cannot
test the boundary the design moved. Proof: `perry/evidence/2026-09/TASK-472-result.md:55` and
`tests/test_spec_scannability.py:855` and `:868`.

---

## 3 · The six criteria

### Criterion 1 — **FAIL**

> *"Batch independent reads; keep dependent actions, mutations and approvals
> sequential. Put long/repeated scripts in repository-derived unique scratch
> files; do not share scratch filenames across sessions."*

**The first half is not written anywhere.** At `17da62fc`,
`grep -rni "batch|parallel|independent read|sequential"` over
`work/reference/review.md` (623 lines) and `work/reference/review-constraints.md`
(176 lines) returns **zero hits**. Nor does any other page carry it: the six
files under `work/reference/` containing "batch" all use it of
`AskUserQuestion` batching of *questions*, and `conversational.md:7` names that
as a failure mode, not a contract.

The result document says otherwise, in the section a reader opens to learn what
is missing:

> `TASK-472-result.md:115-117` — *"Criterion 1's batch independent reads half
> **is stated in the contract** but is a behaviour of the agent following it,
> and nothing here measures whether a round actually batches."*

The clause after "but" is fair and I would not fail the row for it — the spec's
own Verification section does not ask for agent-behaviour measurement, and
USER-972 records that this host reports token usage as unknown. The clause
before "but" is false, and it converts a missing deliverable into a merely
unmeasured one.

**The second half is delivered but does not work as documented.**
`review-constraints.md:61` prescribes:

```
scratch="${TMPDIR:-/tmp}/perry-$(git rev-parse --short HEAD)-$$"
```

Two problems, both measured rather than read.

*(a) It is not stable across commands.* `$$` is the shell's PID and each
invocation is a new shell. Run twice from this worktree, two seconds apart:

```
review-constraints.md:61  invocation 1: /var/.../T//perry-0ff3eeef-73914
review-constraints.md:61  invocation 2: /var/.../T//perry-0ff3eeef-73919
dispatch.md:117           invocation 1: /var/.../T//perry-scratch/agent-aa19e8f69bec60bb4
dispatch.md:117           invocation 2: /var/.../T//perry-scratch/agent-aa19e8f69bec60bb4
```

It also moves whenever `HEAD` moves, which for a round that commits as it goes
is every few minutes. `dispatch.md:112-113` instructs the agent to "re-derive it in
each command rather than remembering a name"; an agent that obeys both pages
loses its harness, its mutant table and its captured output on every command —
and that collides head-on with criterion 2, which requires a failure to keep
"the path to the full log — **which still exists**". I hit this in this round
and had to record my scratch path in a file rather than re-derive it.

*(b) It is a second mechanism for a job an existing one does* — the exact
defect the result document congratulates the row for avoiding (`TASK-472-result.md:59-63`).
`dispatch.md:116-117` carries the canonical block, marked *"do not edit without
re-reading TASK-421"*, which `dispatch.md:184` and `:204` require every
dispatched prompt to carry **verbatim** — including the prompt that dispatched
this review. `dispatch.md:121-127` states the principle the new snippet breaks:

> *"**The agent contributes nothing to the uniqueness, and that is the whole
> mechanism.** … **'Pick a unique name' is what failed; this asks for no name
> at all.**"*

`review-constraints.md:57` reintroduces exactly that: *"make it unique to this
session"*, with an agent-side `$$`. That text is byte-pinned in `dispatch.md`
and unpinned in `review-constraints.md`, so the two pages a review agent reads
now disagree and only one of them is guarded.

Proof: `work/reference/review-constraints.md:57,61` against
`work/reference/dispatch.md:117` and `:121-127`; and the absence, whole-file,
of the batching half (`TASK-472-spec.md:27`).

### Criterion 2 — PASS

`review-constraints.md:77-91` states all three parts: success returns the
status line and evidence paths; failure keeps the exit code, enough diagnostic
to act on, and the path to the full log; structured output is filtered
structurally or kept whole, and *"never feed a truncated JSON document back as
if it were a valid one"*. Each clause is present and normative. A1 shows the
paragraph reddens when contradicted from inside the span. (The scratch-path
instability under criterion 1(a) undermines the "which still exists" clause in
practice; I have charged that to criterion 1, where the defective text lives,
and not twice.)

### Criterion 3 — PASS

`review-constraints.md:93-108`: prefer the host's completion event, a bare `&`
opts out of it, bounded polling with a delay matched to the work where no event
exists, record calls and waiting, no scheduler, and a tool-call count is not a
model-turn count. All five clauses present. I followed it in this round: three
long runs were started through the host's background mechanism and each
returned on its own notification; no polling loop was written and no `&` used.

### Criterion 4 — PASS

`review.md:202-218`. The template now carries `<base SHA>..<head SHA>` with
*"exact, both ends, never a branch name alone"* and a separate
`Base the criteria exist on:` line; the `citation-not-on-branch` incident is
cited as the reason, and the paragraph at `:215-218` says a changed base or a
widened change re-opens the round's scope to *"the changed findings and every
invariant they touch"*. Fresh V4 independence is untouched (`review.md § 0`,
`§ 4` unchanged in this range). The single deletion in the whole diff is the
old one-line `Under review:` template this replaces. A2 kills a contradiction
placed inside this span.

### Criterion 5 — PASS, and `§ 6` was not weakened

The stop is unchanged. Establishing that by mutation rather than by reading:

| Mutant | Site | Result |
|---|---|---|
| D0 | `tests/test_review_verdicts.py` as shipped | green |
| D1 | `bin/perry-lint:2653`, default threshold `2` → `99` | **RED** |
| D2 | `bin/perry-lint:2763`, the `review-rounds-exhausted` finding suppressed | **RED** |

So a row at two FAILs is still stopped and `perry-lint --reviews` still reports
`review-rounds-exhausted`; both are live behaviour with teeth, in code this row
did not touch (the diff contains no `bin/` change at all).

Reading the new text for anything that could be construed as authorising a
further round: `review.md:508` *"**The stop still stands.**"*; `:521-525` the
three choices are raise the threshold, close the row with the defects recorded,
or hand the fix to someone who has not authored it — the first of which is the
pre-existing `review_fail_rounds_before_escalation` knob, already documented at
`:530-537`, not a new authority. The new clause at `:526-529` — *"One party may
not raise that threshold: the author of the work"* — narrows it, and the
sentence that follows routes it to the user (*"Recommend it … and let the user
turn the knob"*). `:538-539`, *"A `review-rounds-exhausted` finding is never
cleared by running the round anyway"*, is pre-existing, retained, and inside the
pinned span. The criterion's own requirements — summarise unresolved criteria,
name the needed decision, do not silently widen scope or auto-approve — are met
at `:510-529`. Nothing in the new text authorises a further round.

One residual, recorded rather than charged: *"One party may not raise that
threshold"* is an exclusion list of one, so read in isolation it licenses any
*other* party, and `:533-534` already tells a round that `PERRY_REVIEW_ROUNDS=N`
overrides for a single run. The adjacent sentence closes it for a careful
reader. It predates this row and I am not failing the row for it.

### Criterion 6 — **FAIL**

Sentences 2 and 3 are delivered, at `review.md:324-334`: a reason is required
before re-running the full suite and unease is not a reason; a filed flake is
re-run **alone** first, `perry-task list --all --json` says whether a row
records it, and the full suite is then run **once**, citing the row; targeted
checks during iteration and the final merged-candidate full check are
preserved. A3 kills a contradiction placed inside this span.

Sentence 1 is not delivered. The criterion says *"Compare one small-change and
one reviewed-delivery trace against the baseline"*, and `TASK-472-spec.md:51`
puts the same thing in the row's `## Bound` as a named artefact: *"one
small-change trace and one reviewed-delivery trace"*. What exists is
`TASK-472-result.md:101-105`, a five-bullet list of one day's observed waste,
labelled *"which is criterion 6's 'compare a trace against the baseline'"*. A
list of five incidents is not a trace of a small change, is not a trace of a
reviewed delivery, and is not compared against anything: the only baseline in
the document is *"157 modules / 4434 tests green"* (`:8-12`), a suite
measurement with no command or turn trace attached to either side.
`perry/evidence/2026-09/` carries exactly three TASK-472 files — plan, spec,
result — and no trace artefact.

This is separable from the benefit claim, and I want to be precise about which
one I am failing. Declining to claim a saving is **honest**: USER-972 records
that this host reports token usage as `unknown`, the iteration plan forbids
substituting a byte estimate for a measured one, and `TASK-472-result.md:95-99`
says so plainly instead of dressing up a byte count. I would have failed the
row for the opposite behaviour. But "the benefit cannot be measured on this
host" does not excuse the two traces, which are a *bounded command-and-review
trace* — the thing `TASK-472-spec.md:45` calls "before/after bounded command
and review traces" — not a token figure. A trace of a small change through the
new contracts could have been produced on this host without any token
telemetry at all.

Proof: `perry/evidence/2026-09/TASK-472-result.md:95-107` against
`perry/evidence/2026-09/TASK-472-spec.md:37` and `:51`.

---

## 4 · The cost claim, checked independently

`TASK-472-result.md:87-93` reports +6,444 bytes and says no declared bill moved.
Both check out:

```
review.md            28761 → 32487   (+3726)
review-constraints.md 6146 →  8864   (+2718)                      total +6444
```

`python3 bin/perry-context-budget --bill all --json` at `17da62fc`:

```
snapshot     78456  within   5 files   review pages in bill: none
add-task     99947  within   5 files   review pages in bill: none
close-task   92853  within   4 files   review pages in bill: none
dispatch    114338  within   5 files   review pages in bill: none
plan-phase  108906  within   5 files   review pages in bill: none
```

Five bills, all `within`, and neither page appears in any bill's file list.
The claim is accurate and was made accurately.

---

## 5 · Did the pages under review steer this round?

The row's author named this hazard and could not check it from inside, so:
yes, in one place, and it is structural rather than dishonest.

**`review.md:324-327` steered against the check this row most needed.** *"Do
not re-run the full suite without a reason. A reason is a new change, a
failure, or a concern the last run left open — not unease."* That text is
written by the author of the row under review, lands in the page his reviewer
is required to follow, and on this row points away from the row's own risk: the
change abandons a guard module the author had already written and moves its job
onto four new digest pins, and the `affected` tier runs 46 of 161 modules. The rule did not stop me — a surviving mutant that must
be shown to be caught nowhere is a "concern the last run left open", which the
rule permits — but it made running the broader check something I had to
justify under the author's own text rather than something I simply did. A page
that governs how hard its own author gets reviewed should not be re-pinned by
the author's row without someone saying so out loud. I am saying so; I am not
failing the row for it, because the text is defensible on its merits and the
same objection applies to `§ 6`, which the author tightened rather than
loosened.

**`review-constraints.md:93-108` steered the round well**, and the honest
answer is not uniformly negative. Starting three long runs through the host's
completion mechanism instead of `&`-plus-polling was the contract's doing, and
it cost this round no polling calls at all.

**`review-constraints.md:11-29` is what made the central finding possible.**
"Plant into a copy" is why B1–B6 and E1–E4 could be measured at all, and why nothing in
the live tree or this worktree was ever red about nothing.

**The one place I declined to follow the page as written** is criterion 1's
scratch snippet, for the reason in § 3: re-deriving it per command loses the
round's own logs. I used a session-unique directory recorded once, which is
what `dispatch.md:117` yields and what the constraint intends.

---

## 6 · What held

- All seven `GOVERNED` digests recompute; the four new comments' char and line
  counts are exact; the constraints span really is entirely new prose.
- The only deletion in the reference diff is the one template line criterion 4
  replaces. `§ 6` was not weakened, by deletion or by addition.
- The deleted `test_review_contracts.py` really did have the hole the author
  says it had — reconstructed and confirmed.
- A retraction placed *inside* any of the four new spans reddens a named test.
- The two-FAIL stop is live, and mutating it in `bin/perry-lint` reddens.
- The byte cost and the "no declared bill moved" claim are both accurate.
- Nothing was run against the project's `perry/` state; no write-side tool ran.
- This document's own verdict block parses: `python3 bin/perry-lint --reviews
  --json` on this branch reads it as a FAIL for TASK-472 with no
  `verdict-malformed`, no `fail-without-proof` and no `citation-not-on-branch`.
  The one finding it raises — `fail-verdict-left-at-review` — is the expected
  consequence of a FAIL arriving while the row sits at `review`, and moving the
  row is the PMO's write, not this round's.

## 7 · What the row needs, stated as fixes rather than as questions

Neither finding is a fork and neither needs a decision from the user.

1. Write criterion 1's first half — batch independent reads, keep dependent
   actions, mutations and approvals sequential — into the governed span in
   `review-constraints.md`, re-pin the digest in the same commit, and correct
   `TASK-472-result.md:115`.
2. Replace `review-constraints.md:61` with the canonical
   `perry-scratch-derivation` block from `dispatch.md:117`, or amend that
   block once and have both pages point at it. Two spellings of one rule is
   the defect this row's own result document names.
3. Produce the small-change trace and the reviewed-delivery trace that
   `TASK-472-spec.md:51` bounds the row to, or file an ask to drop them from
   the Bound. They do not require token telemetry.
4. Optional and outside the criteria, but it is the row's headline claim:
   either add a containment check over the six contracts' vocabulary, the way
   `test_every_mention_of_the_rule_is_inside_a_governed_region` does for
   `worktree|isolation`, or strike "there is no gap between regions to insert
   into" from `tests/test_spec_scannability.py:855`, `:868` and
   `TASK-472-result.md:55`. The claim and the coverage should match in
   whichever direction is cheaper.

---

=== VERDICT ===
task: TASK-472
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-472-spec.md
checked: Re-derived all six criteria from the spec independently; no previous round existed. Ran `bash tests/run --tier affected --base 1c28cce7` — exit 0, 46/161 modules, 1466 tests, 52.0s (a green in affected is not a green suite; 115 modules did not run; test_host_support was not selected so TASK-272's flake did not arise). Seventeen mutations, all on a disposable `git archive` copy of 17da62fc in a session-unique scratch dir, `__pycache__` purged and the clock advanced past a second on both sides, every restore verified against `git show 17da62fc:<path>` and not against harness-snapshotted bytes; all output kept for both outcomes. A1–A4 and C1 (retraction or deletion placed INSIDE each of the four new GOVERNED spans) all RED. B1–B6 (the same retractions placed one line outside a span anchor, at review-constraints.md:53, :111, after :176 and review.md:224, :350, :542) all GREEN — six for six survivors; B1 was then re-run against EVERY module (`unittest discover`, 4535 tests, 681.6s) and the strings review-constraints / scannability / governed / GOVERNED appear zero times in the failure log, so nothing in the repository catches it. E1–E4 continued the same category outside the two pages — autopilot.md (neighbouring page), work/SKILL.md:58 (the index row), review.md:554 (the second, ungoverned copy of the reviewer prompt) and dispatch.md:156 (the declared-free rationale block) — all four GREEN against five plausibly-covering modules that are green as shipped. D1 (bin/perry-lint:2653, threshold 2→99) and D2 (bin/perry-lint:2763, review-rounds-exhausted suppressed) both RED, so the two-FAIL stop is live and tested. Reconstructed the deleted `tests/test_review_contracts.py` design and confirmed its hole: all three paragraph pins hold while the retraction sits in the file. Recomputed all seven GOVERNED_SHA digests (all match) and every span's char/line count against its comment (2710/55, 1499/32, 2400/42, 4784/89 — all exact); confirmed the constraints span is entirely new prose against 1c28cce7 and that the whole reference diff contains exactly one deleted line. Enumerated the ungoverned zones: 577 of the 799 lines of the two pages, 4 zones in review.md and 2 in review-constraints.md, plus review.md:554's second prompt copy, work/SKILL.md:58, every other work/reference page, and .perry/hook.md. Grepped both pages whole-file for criterion 1's batching half (zero hits) and all of work/reference for a pre-existing statement of it (none). Verified the byte growth (+3726, +2718 = +6444) against 1c28cce7 and ran `bin/perry-context-budget --bill all --json` (5 bills, all `within`, neither page in any file list). Ran the two documented scratch derivations twice each and measured that review-constraints.md:61 returns a different directory per invocation while dispatch.md:117 is stable. Read §6 in full for any clause authorising a further round.
not-checked: The slow tier and `tests/run --tier full` were not run by me. The all-module B1 run used `unittest discover` inside a non-git `git archive` copy and reported 5 failures / 9 errors that are artefacts of that harness (the PERRY_PROJECT and tree-guard cluster, two git-tracking tests, and test_risks_store's three assertIs identity checks); I did not take a clean control run of that same harness, so my claim is the narrow one — no module NAMED the retraction — not "the suite was otherwise green". I did not verify that the six 2026-09-20 incidents the contracts cite actually occurred; they are narrative and I took them as given. I did not mutation-test the `.perry/hook.md` extension path (listed by inspection only), and E1–E4 were run against five modules rather than all 161. I did not measure any token or model-turn cost, on this host or any other, and I did not evaluate the iteration plan's targets; I read `perry/evidence/2026-09/2026-09-18-token-efficiency-iteration-plan.md` no further than the lines the result document cites. I did not check whether the three review.md spans' newly-pinned PRE-EXISTING text creates re-pin friction for other in-flight rows. I did not test whether a round actually batches independent reads — nothing in the repository measures that, which is the point of the criterion-1 finding rather than a gap in it.
proof: work/reference/review-constraints.md — criterion 1's "batch independent reads" half is absent from the whole 176-line file and from the whole 623-line work/reference/review.md, while perry/evidence/2026-09/TASK-472-result.md:115 states it "is stated in the contract"; work/reference/review-constraints.md:61 ships a second, unguarded scratch derivation that contradicts the byte-pinned canonical block at work/reference/dispatch.md:117 and the principle at dispatch.md:121-127, and returns a different directory on every invocation; perry/evidence/2026-09/TASK-472-result.md:95-107 offers a five-bullet incident list in place of the small-change and reviewed-delivery traces that perry/evidence/2026-09/TASK-472-spec.md:37 and :51 require. Supporting, not charged as the FAIL: tests/test_spec_scannability.py:855 and perry/evidence/2026-09/TASK-472-result.md:55 claim "there is no gap between regions to insert into", disproved by ten surviving mutants planted at work/reference/review-constraints.md:53, :111 and after :176; work/reference/review.md:224, :350, :542 and :554; work/reference/autopilot.md (end of file); work/reference/dispatch.md:156; and work/SKILL.md:58.
=== END VERDICT ===
