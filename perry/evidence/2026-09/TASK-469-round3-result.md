# TASK-469 round 3 result — USER-974 principle A

Date: 2026-09-20. Author: PMO Agent (Claude Opus 5), the same session that wrote
rounds 1 and 2 and their defects. Not reviewed: round 3's V4 is owed. Nothing was
run against this repository's own `perry/` state.

- **Base:** `d72cd042` (`main`, after the scope amendment below).
- **Branch:** `coding/task-469-round3`.
- **Under repair:** two V4 FAILs, `TASK-469-v4-review.md` and
  `TASK-469-round2-v4-review.md`, escalated as USER-974.

## The principle

**A: the rule is scoped by ROUTE, not by what is being rendered.** The
pack-eligibility procedure never runs on Explain, whatever Explain is loading.
Pack-dependent content — rows **and** the `packs/` pages `help <subcommand>`
opens — is shown **marked**, never filtered, hidden or withheld, because each of
those three is a decision about which pack is active and that decision needs the
read an ungated route may not do.

## The category, enumerated — four sites, not one

Rounds 1 and 2 each fixed the site they were shown. This is the list:

| Site | What it said |
|---|---|
| `work/SKILL.md` § Pack eligibility | "before **loading software-ops references**" — the half round 2 left in the same sentence it edited |
| `reference/config.md:168` | "`/perry help` **also points here**" — Explain sent at a procedure whose step 1 reads the config store and `--section project` |
| `reference/config.md:232` | "Work help **hides** inactive pack commands" — hiding needs the read, and is the opposite of marking |
| `goals/SKILL.md` | the same pointer, unscoped |

`decide/SKILL.md` names the procedure nowhere; checked, not assumed.

**Two of the four are in `reference/config.md`, which this row's spec did not
list.** The scope was widened, in the spec, with the reason recorded there —
`d72cd042` — rather than quietly. Rounds 1 and 2 both FAILed on this category
with that file out of scope; fixing only the in-scope sites a third time would
have shipped a third incomplete category fix. The read in step 1 stays as it is
for the *discovery* operation, which is a Query and legitimately reads.

## The budget, again, and again not raised

The round's prose put the `add-task` bill at 100,285 against 100,000. The
historical paragraph — two rounds' worth of account, not a rule — moved to
`reference/startup.md § The pack rule is scoped by route`, an L2 page that is
in no command's bill. All five bills are within budget and **none was raised**,
which is the same answer round 2 gave the router's L0 cap.

## Mutation proof, and the limit it exposes

Six structural mutants, one per site plus the two verbs that carry the rule.
`__pycache__` purged, clock advanced past a whole second, every file restored
and md5-verified. **All six killed.**

| Mutant | Result |
|---|---|
| A1 `work` — the D1 half returns | killed |
| A2 `work` — route scoping dropped | killed |
| A3 `work` — mark → hide | killed |
| A4 `config` — `/perry help` points at step 1 again | killed |
| A5 `config` — work help hides again | killed |
| A6 `goals` — route scoping dropped | killed |

**B1 survives and is reported rather than hidden.** Keep the rule sentence
verbatim and add a clause after it — "…, save when a `packs/` page is named" —
and the suite stays green.

Two approaches were tried and both are wrong. Round 2 used `WEASEL`, a blacklist
of English hedges; round 2's reviewer walked around it with a word the list did
not have, and no such list can be completed. Forbidding the nouns an exception
must name is the same list one level down.

**Both paragraphs above were wrong, and round 3's V4 disproved them. Corrected
2026-09-20.**

The claim was that no string test can hold a rule against being taken back in
place, and that this is a property of the medium. It is not. Pinning the
**flattened rule paragraph with `assertEqual`** holds it — on the very
paragraph `test_every_site_states_the_route_rule_at_the_instruction` already
extracts at `tests/test_startup_routing.py:333-334`. The reviewer demonstrated
it against four surviving mutants, including B1; I reproduced it: an `assertIn`
guard cannot see B1 because the clause is still present, and an `assertEqual`
on the same extraction sees it immediately.

What I should have written is the **trade-off**, not an impossibility: an exact
pin is brittle, because every legitimate rewording of a 466-character paragraph
then has to update the test. That is a cost to weigh, and I never weighed it —
I declared the problem unsolvable and moved on, in a result file, and repeated
it in the round's dispatch so the reviewer inherited my framing. He tested it
instead of restating it, which is the only reason it is corrected here.

The general limit on guarding prose with string tests is real, and TASK-471's
V4 found it on that row. **Its application to B1 was wrong**, and a general
truth invoked where a specific check exists is an excuse wearing a principle's
clothes.

## Two guards that reported my own text as the defect

Worth recording because both are the same mistake in miniature:

1. The first version read a 2,000-character window and went red on **this
   file's own account of what round 2 got wrong**, which quotes the retired
   wording. A guard that cannot tell an instruction from a description of a
   retired instruction reports the history as the defect.
2. The second pinned a phrase that markdown had wrapped across a newline.
   `TASK-431` broke a line-keyed allowlist by adding a comment above the line it
   named; this is that, one layer over. The check now normalises whitespace.

## Suites

`PERRY_PROJECT` and `PERRY_HOME` unset, in this worktree: **157 modules / 4426
tests / all green**, tree guard clean, `git diff --check` clean.

## Not claimed

- The slow tier was not run here.
- No V4. Round 3's independent review is owed.
- **Criterion 5's eight cases have still not been re-run** by any round or any
  reviewer. The guards added across rounds 2 and 3 check the text those cases
  exercise, which is a different thing and does not substitute for them.
- `reference/config.md` step 1 still reads project state for the discovery
  operation. That is intended under principle A and is not a residual defect.
