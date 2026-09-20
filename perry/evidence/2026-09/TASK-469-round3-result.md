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

**So this is the honest state of the guard: it holds that the rule is STATED,
at each of the four sites, and does not hold that the rule is not TAKEN BACK in
the sentence after it.** The six structural mutants show the first half is real.
TASK-471's V4 reached the same conclusion about that row's prose — six of seven
prose mutants survived there — so this is a property of guarding prose with
string tests, not of this round's care. It is named here so the next reader does
not have to rediscover it, and it was named in round 3's dispatch so the
reviewer could attack exactly it.

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
