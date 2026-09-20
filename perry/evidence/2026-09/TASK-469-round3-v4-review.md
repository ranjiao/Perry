# TASK-469 round 3 — V4 review

Date: 2026-09-20. Reviewer: independent V4 agent (fresh context). I did not write
this code and this is not an agreement with the author's account.

- **Criteria:** `perry/evidence/2026-09/TASK-469-spec.md`, including its
  `Files in scope` widening of 2026-09-20 to `reference/config.md`.
- **Under review:** `d72cd042..256ae459` (branch `coding/task-469-round3`),
  merged to `main` at `728db267`.
- **Author's account:** `perry/evidence/2026-09/TASK-469-round3-result.md`.
- **Prior FAILs:** `TASK-469-v4-review.md`, `TASK-469-round2-v4-review.md`;
  escalated as USER-974, answered **principle A**.

Everything below was done on a disposable clone of the repository at `256ae459`
under the session scratchpad. Nothing in `/Users/bytedance/proj/Perry/perry` was
written, no Perry write tool was run, and no file in the live checkout was
mutated.

**Verdict: FAIL**, on the second half of USER-974's answer — the half that says
what the guard has to be. The prose fix is real and the four prose sites are the
right four; the guard that is supposed to hold them is a blacklist at one of
them, which is the instrument the user's answer explicitly refused.

---

## 1. What I ran

`bash tests/run --tier affected --base d72cd042` in the clone, with
`PERRY_PROJECT` and `PERRY_HOME` unset: **green**, 39 of 161 modules selected,
1,243 tests, tree guard "nothing moved". *This is not a green suite.*
`test_host_support.TestOpenCodeDispatchLimit` was not selected at all in this
tier, so there is no TASK-272 flake to attribute and nothing is excused by it.

Six mutations, each anchored by 1-based line number, `__pycache__` purged and
the clock advanced past the next whole-second boundary before each run, the
whole affected tier run each time, each file restored from
`git show 256ae459:<path>` and the restore verified with `bin/perry-restore-check
256ae459 <path>` — **all six restores verified, tree guard clean on every run.**

| # | Mutation | Result |
|---|---|---|
| M1 | `work/SKILL.md:25` — the author's own **B1**: rule kept verbatim, `, save when a \`packs/\` page is named` appended | **SURVIVED** |
| M2 | `reference/config.md:237-240` — § Conditional consumers rewritten to *"Work help **omits** pack commands whose pack is inactive from its executable index"* | **SURVIVED** |
| M3 | control, same lines — the literal pre-round-3 sentence *"Work help **hides** inactive pack commands…"* | KILLED |
| M4 | `work/SKILL.md:33-36` — principle A re-narrowed to rows: *"the procedure does not run when a **row** is rendered. Before opening a `packs/` page … apply it as usual."* | **SURVIVED** |
| M5 | `reference/config.md:170-172` — *"When `/perry help` needs to know which pack commands are active, run step 1 first."* inserted after the rule | **SURVIVED** |
| M6 | control, `goals/SKILL.md:22-23` — the route clause deleted | KILLED |

M3 dies on exactly one string:
`AssertionError: 'help hides' unexpectedly found in …: reference/config.md tells
an Explain request to 'help hides'`
(`tests/test_startup_routing.py:350`). M6 dies on
`test_every_site_states_the_route_rule_at_the_instruction`.

Also verified, without touching the tree: `bin/perry-restore-check 728db267 …`
shows `SKILL.md`, the three lane files, `reference/config.md`,
`reference/startup.md` and `tests/test_startup_routing.py` are byte-identical on
`main` to the reviewed branch tip — the merge preserved the reviewed bytes.

---

## 2. F1 — one of the four sites is guarded by a blacklist. That is the finding.

USER-974's answer carries two requirements, not one:

> …pack-dependent content — rows AND reference pages — is shown marked as
> needing that pack rather than filtered or withheld. **The guard for this must
> assert the rule's shape positively; a blacklist of softening words is not a
> guard.**

Round 3 built one positive guard,
`test_every_site_states_the_route_rule_at_the_instruction`
(`tests/test_startup_routing.py:324-341`). It reads `ROUTE_RULES`
(`:314-322`), which has **three** entries:

| Site | Positive assertion |
|---|---|
| `work/SKILL.md § Pack eligibility` (`:23-28`) | yes — paragraph must contain *"never on the explain route"* |
| `goals/SKILL.md` (`:21-24`) | yes — same clause |
| `reference/config.md`, the `/perry help` paragraph (`:166-174`) | yes — paragraph must contain *"not for step 1"* |
| **`reference/config.md § Conditional consumers` (`:236-242`)** | **none** |

The fourth site is one of the two the spec was widened for. Its rule — *work
help **marks** pack commands; it does not hide them* — is asserted nowhere. The
only thing standing over it is
`test_no_site_anywhere_tells_help_to_hide_a_pack_command`
(`tests/test_startup_routing.py:342-355`), which is a four-string blacklist
plus one more string:

```python
for verb in ("help hides", "hides inactive pack",
             "help filters", "filtered from its executable"):
    self.assertNotIn(verb, flat, …)
self.assertNotIn("also points here", flat, …)
```

M2/M3 are the proof and they are a matched pair. **M3** restores the exact
pre-round-3 sentence and dies — on the literal `help hides`, nothing else.
**M2** restores the same instruction with `omits … from its executable index`
and the whole affected tier stays green. After M2, `reference/config.md:237`
again tells the Explain route to drop commands whose pack is inactive, which is
the decision principle A says needs a read help may not make — and that is the
site the spec's `Files in scope` was widened to reach.

So the author's summary of the guard is not true as written:

> **it holds that the rule is STATED, at each of the four sites**, and does not
> hold that the rule is not TAKEN BACK in the sentence after it.

It holds that the rule is stated at **three** of the four. At the fourth it
holds that four particular English phrases are absent. That is the guard shape
USER-974 refused, at the site the scope widening was obtained for, and the
result's own claim about it is stronger than the code.

**Proof: `tests/test_startup_routing.py:314-322` (no `reference/config.md §
Conditional consumers` entry) with `tests/test_startup_routing.py:342-355` (the
blacklist standing in for it); the site it leaves open is
`reference/config.md:236-242`.**

## 3. F2 — the category, again: round 2's defect goes back in and nothing is red

This is the same finding one level over, and it is why F1 is not a nitpick.

`work/SKILL.md:30-39` is where principle A's operative content lives — "on
Explain the procedure does not run **at all**: not to render a row, and not
before opening a `packs/` page that `help <subcommand>` names." Nothing asserts
that paragraph. The only guard reaching it is
`test_the_lane_that_has_pack_help_rows_says_to_mark_not_filter`
(`:373-397`), whose two positive assertions over the trailing 2,000 characters
are `assertIn("mark", body)` (`:394`) and `assertIn("never filter", body)`
(`:397`).

**M4** rewrites `work/SKILL.md:33-36` to say the procedure does not run *when a
row is rendered*, and that before opening a `packs/` page named by
`help <subcommand>` it applies as usual. Both guarded substrings survive
untouched. The affected tier is **green**.

That mutant is round 2's F1 — the finding this row FAILed on, escalated to the
user, and answered — restored in the file that drives the behaviour, in the
paragraph round 3 wrote for it, with the fix's own wording still sitting five
lines above it. What the suite currently protects is round 3's *phrasing*, not
round 3's *rule*. Rule 1 asks for the category; the prose half of the category
was enumerated (§ 5) and the guard half was not.

**Proof: `work/SKILL.md:30-39` held only by `tests/test_startup_routing.py:394`
and `:397`.**

## 4. B1 — I was asked to attack it, and it does not hold

The author names B1, does not hide it, and argues it is a property of guarding
prose with string tests rather than a gap in this round's care, citing TASK-471.
I reproduced B1 (**M1, green**) and the general claim is right in the limit: no
string test can catch an exception added in a later paragraph or another file.

**But B1 specifically is reachable, by a one-line change to a test the author
already wrote.** `test_every_site_states_the_route_rule_at_the_instruction`
already isolates the rule's own paragraph —
`para = flat(text[i:text.index("\n\n", i)])` (`:333-334`) — precisely so that
neighbouring history cannot pollute it. Replace its `assertIn(clause, para)`
with `assertEqual(para, GOLDEN[rel])`, pinning the flattened paragraph, and add
the missing fourth site. That is the maximally *positive* assertion — "the rule
is exactly this text" — not a blacklist, and it is the technique this repository
already uses for `ROUTER_BYTES_AT_BASE` and for the template drift guard.

I ran that check outside the tree, building each mutant in memory from
`git show 256ae459:<path>` (`scratchpad/pinned_paragraph_probe.py`):

```
clean tree:  work/SKILL.md PASS   goals/SKILL.md PASS   reference/config.md PASS
mutants:
  M1 (the author's B1)             -> KILLED at '**Pack eligibility:**'
  M2 (config hide, reworded)       -> KILLED (anchor missing)
  M4 (round 2's defect, reworded)  -> KILLED at '**The rule is scoped by ROUTE,'
  M5 (config /perry help clawback) -> KILLED at '`/perry help` points here'
```

All four survivors die, including the one the author declared out of reach. The
cost is that rewording a rule paragraph requires editing the test, which is the
point of a pinned rule and is what "argued, not typed" already means for the
byte caps next door.

So the answer the dispatch asked for is: **the limit is real in general and the
author's application of it to B1 is wrong.** B1 survives because the check was
`assertIn` and not `assertEqual`, on a paragraph the author had already cut out
for exactly this purpose.

## 5. The category, enumerated — the prose half is right

I re-derived the help-reachable set rather than taking round 2's table: the
router, `reference/router-subcommands.md`, the three lane `SKILL.md` files, and
every `reference/` or `packs/` page named in their index Reference columns — 43
files — grepped for `perry-config show`, `perry-state --`, `perry-task list`,
`perry-tasks board`, `perry-lint --root` and `Pack capabilities`.

| Path | State after round 3 |
|---|---|
| `work/SKILL.md:23-28` | **fixed** — "before **running** an optional pack's route — and **never on the Explain route**, whatever Explain is loading". The clause round 2 left ("before loading software-ops references") is gone |
| `work/SKILL.md:30-39` | **fixed in prose** — covers rows *and* the `packs/` page `help <subcommand>` opens. Unguarded: F2 |
| `reference/config.md:166-174` | **fixed** — `/perry help` points here "for the descriptions below, not for step 1" |
| `reference/config.md:236-242` | **fixed in prose** — marks, does not hide. Unguarded: F1 |
| `goals/SKILL.md:21-24` | **fixed** — carries the route clause |
| `decide/SKILL.md` | confirmed by grep: the words *pack* and *config.md* do not occur in the file. The author's "checked, not assumed" is true |
| `work/reference/{health-check,add-task,planning,subcommands,bootstrap}.md`, `packs/software-ops/pack.md`, `goals/reference/phases.md` | each names the procedure inside a subcommand body and each is opened by `help <that subcommand>`. Acceptable, and *more* clearly so than at round 2: `work/SKILL.md:295` still says help "is navigation, not action", and `work/SKILL.md:34-36` now says in the always-loaded lane file that on Explain the procedure does not run "at all … not before opening a `packs/` page that `help <subcommand>` names" |
| `reference/router-subcommands.md:93-96` | acceptable, and the seam closed from the other side: it offers optional capabilities and defers the read to "**on that request**", which `reference/config.md:168-172` now agrees is not the help route |

No fifth unrepaired prose site. The four the author names are the four.

One inaccuracy to carry: the `PACK_SITES` docstring
(`tests/test_startup_routing.py:305-306`) says "Every file that names the pack
procedure". At least twelve shipped files name it; the constant is the five
files the rule must be *carried in*. Harmless today, misleading to the next
round that trusts it while enumerating.

## 6. F3 — recorded, not the basis of the FAIL: who owns "what else can Perry do?"

Round 3's `reference/config.md:170-172` rests the whole `/perry help` fix on a
classification: "The reads in step 1 belong to the discovery operation itself —
'what else can Perry do?' — which is a **Query** and runs the gates."

That classification is asserted in one page and contradicted in another:

- `reference/startup.md:25-29`: "**A question about Perry** is answered from
  Perry's pages … the config store is **not read for it**."
- `SKILL.md:85`: Explain is "help, how Perry works" → "No update check,
  **config**, state, modes, dashboard or write".
- `SKILL.md:207`: "For **"what else can Perry do?"** or enabling/disabling
  optional capabilities, use its discovery procedure."
- `reference/config.md:166`: the same phrase heads the trigger list for a
  procedure whose step 1 runs `perry-config show --json` and
  `perry-state --section project`.

So the identical sentence is Explain by the router's own test and a Query by
`config.md`'s assertion, and `SKILL.md:207` routes it without saying which. I do
not fail the row on this: USER-974 answered the route question and left
discovery reading as a Query, the author declares the classification in the file
rather than hiding it, and both earlier reviews reached the same disposition
from the other side. But it is the last place the rule rests on a label rather
than on a gate, nothing asserts the label, and it is where a fourth round should
look if this one is repaired narrowly.

## 7. The scope widening — necessary, and clean

Judged as the dispatch asks, as part of the review.

**Necessary.** Principle A binds "pack-dependent content — rows AND the `packs/`
pages `help <subcommand>` opens". `reference/config.md:168` sent `/perry help`
at a procedure whose step 1 reads the config store and the project payload, and
`:232` instructed work help to *hide* inactive pack commands — the inverse of
marking. Neither is reachable from inside the old `Files in scope`; both are
required by the answer. Fixing only the in-scope sites would have been round 2's
mistake a third time, which is what the spec's own paragraph says.

**Recorded, not quiet.** The widening is in the spec (`TASK-469-spec.md §
Files in scope`), on its own commit `d72cd042`, with the reason and the two line
numbers, and dated. The `Bound` section is not breached: no new intent engine,
no command redesign, still three routes and eight cases.

**Nothing else rode along.** `git diff d72cd042..256ae459 -- reference/config.md`
is two hunks, `+8 −4`, both inside the two named sites. The discovery
procedure's steps 1-4, § Apply an explicit request, the `perry-config` examples
and the software-ops coverage list are untouched. The root-cause read in step 1
is left as the spec says it would be.

## 8. The budget — verified independently, nothing raised

`python3 bin/perry-context-budget --bill all` in the clone at `256ae459`:

| Bill | Bytes | Budget |
|---|---:|---:|
| snapshot | 78,456 | 80,000 |
| add-task | **99,947** | 100,000 |
| close-task | 92,853 | 95,000 |
| dispatch | 114,338 | 115,000 |
| plan-phase | 108,906 | 110,000 |

All five within; `add-task` has 53 bytes of room. Tier caps:
`SKILL.md` **20,371** against the 20,480 cap and the binding 20,457 growth
guard, and unchanged by this range; `work/SKILL.md` 37,585 / 38,912;
`goals/SKILL.md` 22,383 / 22,528; `reference/config.md` 16,480 and
`reference/startup.md` 8,776 against the 32,768 L2 cap.

**No cap was raised.** The range touches six files and no `bin/` script;
`bin/perry-restore-check d72cd042 bin/perry-context-budget
tests/test_router_budget.py tests/test_next_section.py schema/state-schema.json`
passes at the head, so `BILL_BUDGETS`, `BUDGETS`, `ROUTER_BYTES_AT_BASE` and the
schema thresholds are byte-identical to the base.

**Nothing load-bearing left a file a command loads.** The paragraph moved out of
`work/SKILL.md` was the round-1/2 account ("This correction lives here… It was
first written into `reference/startup.md`…"); every rule in the old text is
present and strengthened in the new (`mark`, `do not filter` → "Never filter,
hide or withhold", plus the `packs/`-page clause the old text lacked), and what
left is narration. `reference/startup.md` is in **no** bill — I confirmed it
appears in none of the five file lists — so the move is real relief and not
accounting. The residual work/SKILL.md delta over base is +77 bytes.

## 9. The six criteria, re-derived

| AC | Finding |
|---|---|
| 1 | Three routes at `SKILL.md:84-87`; the Explain cell still names every exclusion. The prose sites that sent Explain into a state read are closed (§ 5). **Met in the shipped text**, with F3 recorded as the one classification the rule now rests on |
| 2 | `SKILL.md:89` still qualifies the absolute with step 1's config read; step 2 runs the recovery gate before the interrupted-run gate before any state read; `reference/startup.md § Query` keeps "not even a listing" and "Never resume". Round 3 touches none of it and `test_the_blocking_stop_is_not_turned_into_a_continue` and `test_first_time_setup_is_gated_where_step_one_prompts_for_it` still pass. **Met**, with round 2's reviewer's standing caveat that the config read precedes the gate by design and is now disclosed rather than removed |
| 3 | The Change row still sends bare `/perry` to steps 3b-6, so the explicit overview still renders the snapshot; the diff removes no gate from any lane. **Met** |
| 4 | All three lanes still defer steps −3 to −1 to the router and `reference/startup.md § Once per operation, refreshed when invalidated` still supplies the refresh rule; round 3 inserted its new section above it without touching it. **Met** |
| 5 | The eight-case matrix exists at `TASK-469-result.md:62-70` with expected reads, actual reads, decision and outcome, and no classifier was added (the range touches no `bin/` file). **Met on the artefact and on nothing stronger** — no round and no reviewer, including me, has re-run it. Case 2 (`/perry help work`) is now additionally *stale*: its recorded behaviour predates principle A, which changes what that exact route must render |
| 6 | Pointers and guards are valid in the sense that the affected tier is green. **Not met** on two counts: the guard the criterion covers does not hold the rule at `reference/config.md:236-242` (F1) or at `work/SKILL.md:30-39` (F2), while the result claims it holds at all four sites; and the conditional load set the criterion asks to be logged is stale **again** — `reference/startup.md` was logged at 6,111 B, was 7,392 B at round 2 (flagged by that review), and is **8,776 B** now after this round added 24 lines to that very page, with no restatement in `TASK-469-round3-result.md` |

## 10. Why FAIL, and what would clear it

Round 3 does the hardest part right. It stopped fixing the instance it was
shown, enumerated the prose sites, went and got the scope it needed in writing
rather than quietly, moved a paragraph instead of raising a budget, and named
its own surviving mutant in its result. All of that is real and none of it
should be re-litigated by round 4.

It fails because USER-974's answer has two clauses and round 3 delivered the
first everywhere and the second in three places out of four. The fourth is the
site the scope widening was obtained for, and what stands there is the blacklist
the user's answer names and refuses. M2/M3 make that concrete: the sentence goes
back in with one verb changed and the suite does not notice. F2 shows the same
hole one level up, where the mutant is not a hypothetical softening but round
2's actual FAIL restored.

The repair is small and I established it rather than asserting it (§ 4): pin the
rule paragraph at each site with `assertEqual` on the flattened paragraph the
test already extracts, and add the fourth site to `ROUTE_RULES`. That kills M1,
M2, M4 and M5 — every survivor this round has, the author's own B1 included.

=== VERDICT ===
task: TASK-469
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-469-spec.md
checked: Worked only in a disposable clone of the repository at 256ae459 under the session scratchpad; nothing in /Users/bytedance/proj/Perry/perry was written, no Perry write tool was run, no file in the live checkout was touched, and my review commit is in my own worktree. Ran `bash tests/run --tier affected --base d72cd042` with PERRY_PROJECT and PERRY_HOME unset — green, 39 of 161 modules, 1,243 tests, tree guard clean; NOT a green suite. test_host_support.TestOpenCodeDispatchLimit was not selected in this tier, so no TASK-272 flake arose and nothing is excused by it. Six mutations, each anchored by 1-based line number, __pycache__ purged and the clock advanced past the next whole-second boundary before each run, the full affected tier run each time, each file restored from `git show 256ae459:<path>` and every restore verified with bin/perry-restore-check 256ae459 (all six passed, tree guard "nothing moved" every run). FOUR SURVIVED: M1 = the author's own B1 (work/SKILL.md:25, ", save when a `packs/` page is named" appended); M2 = reference/config.md:237-240 rewritten to "Work help omits pack commands whose pack is inactive from its executable index", restoring the hiding rule the spec was widened to remove; M4 = work/SKILL.md:33-36 re-narrowed to rows with "Before opening a `packs/` page … apply it as usual", i.e. round 2's own F1 restored in the paragraph round 3 wrote; M5 = reference/config.md:170-172, "When `/perry help` needs to know which pack commands are active, run step 1 first." TWO CONTROLS DIED on the right assertions: M3 (the literal "Work help hides inactive pack commands") on test_no_site_anywhere_tells_help_to_hide_a_pack_command at the string 'help hides', and M6 (route clause deleted from goals/SKILL.md) on test_every_site_states_the_route_rule_at_the_instruction. Attacked B1 as dispatched and found the check the author missed: pinning the flattened rule paragraph with assertEqual — on the very paragraph test_every_site_states_the_route_rule_at_the_instruction already extracts at tests/test_startup_routing.py:333-334 — kills M1, M2, M4 and M5; demonstrated outside the tree by rebuilding each mutant in memory from `git show 256ae459:<path>` (scratchpad/pinned_paragraph_probe.py), clean tree passing at all three files. Re-derived the category over the help-reachable set myself (router + reference/router-subcommands.md + three lane SKILL.md + every reference/ and packs/ page named in their index Reference columns, 43 files) grepping for perry-config show, perry-state --, perry-task list, perry-tasks board, perry-lint --root and Pack capabilities: the four prose sites the author names are the four unrepaired ones, no fifth; confirmed by grep that decide/SKILL.md contains neither "pack" nor "config.md". Judged the scope widening: necessary for principle A, recorded in the spec on its own commit d72cd042 with line numbers and reason, and `git diff d72cd042..256ae459 -- reference/config.md` is two hunks (+8 −4) entirely inside the two named sites with nothing else changed. Verified the budget independently with `python3 bin/perry-context-budget --bill all` at the head — snapshot 78,456/80,000, add-task 99,947/100,000, close-task 92,853/95,000, dispatch 114,338/115,000, plan-phase 108,906/110,000, all within — and that no cap was raised: bin/perry-context-budget, tests/test_router_budget.py, tests/test_next_section.py and schema/state-schema.json are byte-identical to d72cd042 per bin/perry-restore-check, SKILL.md is 20,371 against the 20,480 cap and the binding 20,457 growth guard and is untouched by the range, and reference/startup.md (8,776 B, L2 cap 32,768) appears in none of the five bills, so the paragraph move is real relief. Confirmed the moved paragraph was narration and that every rule in it survives, strengthened, in work/SKILL.md:30-39. Confirmed with bin/perry-restore-check 728db267 that SKILL.md, the three lane files, reference/config.md, reference/startup.md and tests/test_startup_routing.py are byte-identical on main to the reviewed branch tip.
not-checked: I ran neither the `full` nor the `slow` tier at any commit, so every "green" here is the affected tier only and none of it is a green-suite claim. I did not re-run any of criterion 5's eight cases and produced no fresh-context transcript, so criterion 5 is graded on the artefact at TASK-469-result.md:62-70 and by reading the procedure, never by observing an agent — and I did not re-run case 2 even though principle A changes what `/perry help work` must render. I did not re-run the author's own six mutants A1-A6 and take no position on their specific edits; my four survivors are different edits. I did not mutate SKILL.md, decide/SKILL.md, reference/startup.md or tests/test_startup_routing.py at all. I did not drive any real agent down `/perry help runbook-check`, `/perry help health-check` or `/perry help` against a fixture — §5's disposal of the reference pages that still name the pack procedure rests on reading the shipped instructions, as it did at round 2, not on observing a run. I did not check the pinned-paragraph repair against the rest of the suite (I ran it outside the tree, not as a test module), so I have not shown it introduces no other red. I did not review the perry/ board, journal or ask rows for this task beyond reading USER-974, did not look at TASK-470/471/473 or verify the author's citation of TASK-471's V4, and did not exercise any non-English, split-layout, adopt, diagnose or relocate path.
proof: F1 — tests/test_startup_routing.py:314-322 (`ROUTE_RULES` carries no entry for `reference/config.md § Conditional consumers`) leaves reference/config.md:236-242 guarded only by the blacklist at tests/test_startup_routing.py:342-355, which USER-974's answer refuses by name; M2 rewrites reference/config.md:237 to "Work help omits pack commands whose pack is inactive from its executable index" and the affected tier stays green, while the control M3 dies at tests/test_startup_routing.py:350 on the literal string 'help hides'. F2 — work/SKILL.md:30-39, the paragraph carrying principle A's operative content, is held only by tests/test_startup_routing.py:394 and :397; M4 rewrites work/SKILL.md:33-36 into round 2's own F1 and the affected tier stays green.
=== END VERDICT ===
