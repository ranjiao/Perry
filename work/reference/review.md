# Independent review

V4 means a fresh context reviewing the concrete artifact against written criteria.
The implementer cannot award it. V5 additionally requires the named human's actual
acceptance; a request to implement does not confer signoff authority. Read
`$PERRY_HOME/reference/kernel.md`, `review-constraints.md` and `reference/operating-rules.md`.

## 0 · Whether this row gets a round at all

Follow the task's written rung and governing project policy. A change that can
corrupt unrecoverable state, publish a misleading answer, or weaken a safety gate
needs independent judgment. Outward-facing, irreversible, money/legal/safety
consequences require their applicable human authority and V5 when prescribed.
Do not lower a rung because a check is inconvenient. Structural V2 checks prove
structure; a reproducible V3 run proves only the recorded behavior. Neither
proves semantic acceptance or independent review.

## 1 · Refuse without written criteria

Query the task, attachments and relevant events with complete paging. Read the
written criteria before dispatching. Missing/unreadable criteria stop the review;
the reviewer must not invent the bar. Apply the [project contract](../../reference/project-contract.md):
for Git code, pin exact base/candidate commits and criteria hash; for non-Git or
non-code work, pin the retained immutable subject and criteria. A branch name or
a fingerprint without retained source is insufficient. Scope acceptance using
[acceptance.md](acceptance.md); delivery and human acceptance remain distinct.

The criteria must name a finite enumeration, its size, the command/source that
produced it, and visible exclusions. A universal negative over an unnamed tree
has no last element. Widening the bound is a separate task/decision, not an
endless new round. Open every required exhibit and verify its exact path/hash
before dispatch. Missing citations are a preflight gap; never spend a review
round pretending they are accessible.

## 2 · The prompt

Use a host-valid fresh-context reviewer and the normal dispatch isolation and
high-stakes gates. Give it `review-constraints.md`, the exact immutable subject
(base/head SHAs for Git code), criteria path/hash, actual source roots and the
author's applicable test/architecture receipts. The
reviewer did not write the implementation and is not being asked to agree with
it. Retain the actual completion event/result, not just a launched process.

### The four rules

1. Enumerate the finite category of a defect instead of finding one more instance.
2. Demonstrate actual wrong behavior with a reachable input or meaningful red
   mutation. A green mutation is a product/test gap, not a documentation issue.
3. Judge against written criteria and actual behavior. Untidy tests or an unrelated
   prose mistake get their own correction; they do not invent a new bar.
4. State what was and was not checked. A limited scan, subset or source rehearsal
   cannot become a full suite, live activation, V4 or V5 by wording.

### What the reviewer runs

Use the actual project's declared methods under the [project contract](../../reference/project-contract.md).
Run relevant targeted checks and independent adversarial cases; use required
full/integration gates when applicable. For research or non-code artifacts,
inspect the declared sources and artifact rather than inventing a code runner.
Missing required methods, environments or evidence prevent acceptance of that
scope. Keep commands/inspections, inputs, immutable subject, results and limits.
Rerun broad checks only for new changes, failures or unresolved coverage.

For **Perry source only**, the new stdlib full/slow suite and exact-merge helper
are defined in [tests/README.md](../../tests/README.md); use
`bash tests/run --tier full` (plus required slow checks) and independent
`python3 tests/merge-check --base <immutable-base> --candidate <immutable-head>
--tier full --record <external-directory>`, verifying its receipt. Other
projects use their declared equivalent, not these paths. No reviewer self-merges
or treats author-base green as merged-state validation. Applicable release
rules remain binding; no source-only check constitutes live activation.

## 3 · The verdict block

Write one block per task, plus criterion-by-criterion evidence and limitations:

```
=== VERDICT ===
task: <actual task ID>
rung: V4
result: PASS | FAIL
criteria: <resolvable path and pinned source>
checked: <criterion numbers, exact subject, commands and results>
not-checked: <exclusions, unrun checks and unknowns>
proof: <file/line plus reachable wrong input for each FAIL>
=== END VERDICT ===
```

Only the reviewer writes its verdict. A suspicion without a reproducible behavior
is a reported uncertainty, not a fabricated FAIL. A required criterion left
unverified prevents a PASS. If criteria grade some findings as separate rows,
record that explicitly; the reviewer cannot silently waive required criteria.
The skill reads this block for meaning. No retired lint regex certifies it.

## 4 · Preflight and evidence safety

Use `tools/document_checks.py review --input <absolute-packet.json>` for the
structural packet described in `reference/operating-rules.md`. Missing evidence,
self-review or invented V5 signoff must refuse. A helper success establishes
neither freshness nor semantic truth: verify the actual reviewer context,
source/criteria and actual human instruction independently. Never run native
mutations against the project under review; use explicit isolated test stores.

## 5 · After the round

Attach the actual review document with the current expectation. Record the
actual reviewer identity, not the implementer or a fabricated human actor. A
PASS permits only the transition authorized by the task's required rung; V4 does
not close V5. A FAIL returns work with the named failing criterion and next
fix. A stale sequence or refusal is not a recorded verdict; reread and reconcile.

## 6 · Two FAILs is a decision, not a third round

The default is two FAILs before escalation unless the user's actual approved
project preference says otherwise. Count criterion-level results from attached
review documents and native events; unknown history is not zero. At the limit,
stop automatic redispatch and create the actual ask/dependency via the native
contract. Explain the unresolved principle or, if already decided, the remaining
concrete defects. Do not invent a fork to fit a template.

The implementer cannot widen its own threshold. Recommend a justified change,
record the user's choice, and retain the old failures. Do not re-ask an already
answered principle or close defects silently. The old schema/config/regex round
counter is retired under the accepted H list; this explicit history review preserves the
decision gate. Preference edits follow `reference/config.md`.

## Completion routing

After completed writes follow [the shared closing step](../../reference/next.md#closing-step).
<!-- next-close: work review -->

## Integration architecture reviewer brief

This is the merge-time gate selected by `dispatch.md § Architecture review`,
separate from the task's required verification rung. Use a fresh context, never
an implementing author or an agent carrying the implementation conversation.
The integrator supplies the six trigger facts and immutable candidate inputs.

```
Read $PERRY_HOME/work/reference/review-constraints.md and follow it.
You are the independent architecture reviewer of this integration candidate.
Base: <full SHA>   Head: <full SHA>   Diff: <exact git diff base head>
Trigger facts: <all six classes, evidence and any unknowns>
Architecture: <root §1/§3/§6 at base and head with source line numbers>
Component mapping: <agent selection from the confirmed §2 component list>
Touched module documents: <paths and cited versions; explicitly list missing>

Check the diff and component mapping yourself. Read other root sections only
on demand (for example §5 for a contract version). A component root §2
declares no module document for has none, and that is not missing. Missing documents, unclear
component membership or unknown trigger facts are unresolved, not safe. Do not
infer a new rule from silence, and do not use an author's compliance verdict.
For each relevant rule, answer holds / contradicts / not touched, citing the
architecture rule's file:line and the diff evidence (or why it is not touched).
Consider §1 scope, §3 boundaries and each §6 rule, plus touched module rules.
A contradiction of a decided section stops acceptance for the existing user
decision gate. A descriptive mismatch needs correction and re-review.
Return this block for merge evidence; you do not merge or close a task:

=== ARCHITECTURE COMPLIANCE ===
Reviewer: <identity, fresh context, not the task author>; timestamp: <time>
Base: <full SHA>
Head: <full SHA>
Triggers: <six facts and supporting paths/modes/versions>
Context: <root sections; component mapping; module documents; unresolved facts>
Rules:
- <rule file:line> — holds | contradicts | not touched — <diff citation/reason>
Decision: PASS | BLOCKED — <contradictions, missing context, or none>
User decision required: <decided rule + question, or none>
Not checked: <explicit limits>
=== END COMPLIANCE ===
```

PASS requires all applicable rules resolved without contradiction or missing
context. Retain output verbatim and bind it to this candidate; changed base,
head or diff requires fresh selection/review. Task V4/V5 and human sign-off
remain independent requirements.

### Two bounded walkthrough fixtures

These are procedure fixtures, not live task verdicts or substitutes for an
integration review. A fresh reviewer records both scenario outputs in external
scratch evidence. Pin the fixture's base/head and exact diff, and cite actual
rule lines from that base rather than copying example line numbers.

1. **Reader boundary**: in a disposable fixture candidate, add only a comment
   to a retained skill-side helper (no behavior change). Record all six trigger facts:
   listed boundary path true; new top-level directory, new bin executable,
   contract-version change, root architecture edit and module architecture edit
   false. Select the reader component from confirmed §2. If its module document
   is absent, say so and return BLOCKED for missing context; never fabricate it.
   Produce an `ARCHITECTURE COMPLIANCE` block citing at least root §6 NN-1's
   actual rule line: the comment preserves the one-reader rule (`holds`);
   assess the other relevant rules as the brief requires. Missing context does
   not prevent reporting the supported rule-level finding.
2. **Evidence only**: in a disposable fixture candidate, add only a text file
   at `perry/evidence/<date>/architecture-walkthrough.md`. Record exact base/head,
   diff and all six facts false, then `Architecture trigger: none — evidence-only
   diff under perry/`. Do not launch an architecture reviewer for that candidate
   or produce an `ARCHITECTURE COMPLIANCE` block. The walkthrough reader reports
   the selection result; it does not turn the no-trigger case into a review.

**Bounded negative checks**: remove the required `review.md § Integration
architecture reviewer brief` pointer in a disposable dispatch copy, then restore
it; separately restore an executor instruction requiring its own compliance
attestation, then restore it. The existing pointer/instruction guards or fresh
semantic reviewer must report the missing connection and the self-award. Retain
mutated/reverted outcomes and verify restored bytes against the committed source.
Lexical guards check pointers/pinned bytes only; no Python prose-meaning classifier.
