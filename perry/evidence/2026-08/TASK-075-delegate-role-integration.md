# TASK-075 — DESIGN-006 phase D: the escalation union only ever grows

> Source: `perry/design/DESIGN-006-roles-and-knowledge.md § 5.2`, § 5.4, § 6.1
> phase D. Builds on TASK-072 (phase A) and TASK-074 (phase C).
> Rung: **V3**. Every claim below is a run or a mutation.

## The safety property, and why it needed three tests

A role's `Must escalate` list is **added to** the project's high-stakes list
from `.perry/hook.md`. Reversed, hiring a role would quietly narrow what the
project refuses to do unsupervised — and it would be invisible, because a
narrowed scan still passes everything it is asked, cheerfully. The only symptom
is a dispatch that should have refused and did not.

One test is not enough, because each plausible shape of the mistake defeats a
different guard:

| Guard | What it asserts | Defeated by |
|---|---|---|
| structural | `project` and `roles` are reported as separate halves | a rewrite that keeps the halves honest and narrows only the scan list |
| provenance | `origins[frag]` says `hook` or `role:<name>` | the same |
| **behavioural** | a **project-only** term still trips the scan while a role is declared | nothing found so far — this is the one that holds |

`test_a_project_term_still_trips_the_scan_while_a_role_is_declared` is the
guard this phase exists to leave behind. **M2b** is the mutation it was written
against: `project`, `roles` and `origins` all still truthful, only the list the
scan actually uses narrows. Six tests go red and five of them are it or its
neighbours; the two shape-only guards would have passed.

## The one implementation

`viewer/parsers.py` owns `escalation_fragments`, `read_role_cards` and
`escalation_union`. `bin/perry-lint` and `bin/perry-state` both call it.
`high_stakes_fragments` in the linter is now four lines that delegate — it used
to carry its own `re.findall(r"`([^`]+)`")`, and two extractions of one rule is
how `squash` went wrong in this repo before, in a table header, which is a much
cheaper place to discover it than an escalation list.

`test_the_linter_does_not_carry_its_own_extraction` (M10) is that guard.
Verified byte-equal before the swap: on Perry, gimegime-pmo and PolyForge the
old and new extractions produce the same set, with zero duplicates dropped.

## What renders, and what stays advisory

`bin/perry-state --section roles` is the roster `delegate` renders from. One
read, four blocks, four consumers:

| Block | Payload | Kind |
|---|---|---|
| `Context`, `May touch` | `context`, `may_touch` — verbatim, byte-equal to the section body | **advisory** — they shape behaviour |
| `Loads` | `knowledge[]`, resolved from topics, with `stale` / `age_days` / `invalidated_by` | advisory, **but the stale flag is not** |
| `Must escalate` | `must_escalate.fragments` → `project.escalation.union` | **hard — this is the enforcement** |
| `Accepted by`, `Default rung` | `accepted_by`, `default_rung` | the close gate; stricter of mode-rung and role-rung wins |

Verbatim means verbatim: `test_context_and_may_touch_come_through_verbatim`
compares to the exact source text. **M7** summarizes `Context` to its first
line and the test goes red. These blocks are short by schema precisely so that
copying them costs nothing, and paraphrasing is how a boundary loses its edges
one delegation at a time.

## Stale knowledge is injected flagged — not dropped, not silent

The three options are not equivalent, and § 5.4 picks the third:

- **dropped** → the agent works without a claim the project believes, and
  re-derives it, badly. This is the plausible-sounding one, and **M4**;
- **unmarked** → the agent acts on a claim nobody has checked this quarter and
  cannot tell;
- **flagged** → the agent knows what it is standing on, and can report back
  that the card is wrong now, which is how the card gets fixed.

Also excluded from injection: archived cards (**M5** — an invalidated card is
archived *with its reason*, and re-injecting it undoes the archiving) and
digests (**M6** — told apart by the schema's `Kind:` discriminator, the same one
`--knowledge` and `--provenance` read).

A subscription naming a topic that does not exist is **reported**
(`missing_topic: true`), not dropped: a role that believes it loads
`ledger-quirks` and loads nothing looks better-briefed than it is.

## A prose escalation line enforces nothing

The pre-flight matches backticked fragments. A `Must escalate` line written as
prose sits under the only hard heading on the card, reads like a rule, and
contributes zero fragments — the `hook_TEMPLATE.md` backtick bug, in the file
that inherited its extraction rule. DESIGN-006 § 7 names it as the same failure
class, and this is the same fix: `role-escalation-not-extractable`, plus a
standup warning from `perry-state`.

`test_and_it_really_does_contribute_nothing` asserts the claim behind the
warning rather than assuming it. The check is *"extracts something"*, not
*"is entirely backticked"* — the stricter reading would fire on every card in
the shipped pack, which is asserted too.

## Goal 7 — and it is asserted where a phase-D regression would land

Lint silence was phase C's bar. It is the wrong bar here: `delegate` renders a
prompt and the pre-flight scans a spec, and both would break by *doing
something extra* on a project that asked for none of this. So:

- `--section roles` → `{"declared": 0, "cards": []}`, for both shapes of a
  roleless project (no directory, and an empty one);
- `escalation.union == escalation.project`, **the same list in the same order**
  — not "a superset of". A union that merely *contained* the hook's terms could
  have grown one the project never declared, and a scan that refuses more than
  it was asked to is its own kind of broken. **M8** adds one term and this goes
  red;
- the entire `perry-state --json` payload is equal between the two roleless
  shapes, modulo `generated_at` and the temp-dir name;
- `perry-lint --verification` findings are identical between them;
- `delegate.md` still carries the requirement blocks that used to be the only
  path (**M11**). Deleting them along with the hardcoded agent-type list would
  have quietly changed every prompt on every project that declared nothing —
  the Goal 7 regression arriving as a documentation edit rather than a code one.

## The hardcoded three: five sites, not one

The task named `work/reference/delegate.md`. It was not alone, and the pattern
that generated it is the reason to look:

| File | What it said | Now |
|---|---|---|
| `work/reference/delegate.md:3` | `(Coding / Research / Review)` in the opening line | removed; roles are cards, the three are shipped templates |
| `work/reference/delegate.md:1` | `<agent-type>` in the signature | `<role>` |
| `work/state/hook_TEMPLATE.md:43` | `Special agents available: {{roles beyond Coding / Research / Review}}` | points at `.perry/roles/` (§ 5.5 asked for exactly this) |
| `work/reference/extending.md:44` | `beyond the generic Coding/Research/Review trio` | points at the card template and the pack |
| `work/reference/git-boundaries.md:23, 37` | `every Coding/Research delegation prompt`, `autonomous Coding / Research Agent runs` | role-agnostic |
| `work/SKILL.md:35, 244` | `delegate <task-id> <agent-type>` ×2 | `<role>` |

**M12** puts the parenthetical back and
`test_delegate_no_longer_names_the_three_agent_types` goes red — including the
`<agent-type>` spelling, so the signature cannot drift back either.

Remaining mentions are in `perry/BOARD.md`, `perry/journal/` and
`DESIGN-006` itself. Those are records of the problem, not instances of it, and
rewriting history to hide a closed defect is worse than leaving it legible.

## `bin/perry-dispatch-limit` — untouched, and why

Limits govern executors; a role is a contract. A project with four roles and
two codex slots has two slots, not eight. `dispatch.md` now says so in one
paragraph, and a card's `executors` field may narrow which runtimes are
acceptable without ever granting one a slot. No line of that script changed.

## Mutations

12 written. 11 red, 1 green **by design** (M9a), and the green one is half of a
pair — see below. Every one reverted by rewriting the exact text read before the
edit, hash-verified, never a `git checkout`; anchored by **line number with a
substring assertion on that line**, because `str.replace(old, new, 1)` on a
string appearing three times has hit the wrong function in this repo before and
the run went green looking like a blind guard. Every run purged `__pycache__`
and waited past the second boundary on both edit and restore
(`knowledge/toolchain/pycache-staleness.md`).

| # | Mutation | Site | Result | Named test(s) |
|---|---|---|---|---|
| M1 | **union becomes a replacement** — roles declare the policy, the project's list is discarded | `parsers.py:2661` | RED (7) | `test_declaring_a_role_removes_nothing_from_the_project_list`, `…_a_project_term_still_trips…`, `…_two_halves_stay_separately_reported`, `…_each_fragment_says_which_side…` |
| M2 | project loop skipped when roles exist | `parsers.py:2665` | RED (8) | same, + `test_and_it_really_does_contribute_nothing` |
| M2b | **shape perfect, only the scan list narrows** — the one the behavioural test exists for | `parsers.py:2666` | RED (6) | `test_a_project_term_still_trips_the_scan_while_a_role_is_declared` |
| M3 | zero-backtick warning removed | `perry-lint:1185` | RED (1) | `test_an_unbackticked_escalation_line_is_warned_about` |
| M4 | stale card silently dropped from injection | `perry-state:683` | RED (2) | `test_a_stale_card_is_injected_WITH_its_flag_not_dropped` |
| M5 | archived card re-injected | `perry-state:678` | RED (1) | `test_an_archived_card_is_not_re_injected` |
| M6 | `Kind:` discriminator ignored — a digest injected as a claim | `perry-state:682` | RED (1) | `test_a_digest_in_a_subscribed_topic_is_not_a_card` |
| M7 | `Context` truncated instead of copied verbatim | `parsers.py:2617` | RED (1) | `test_context_and_may_touch_come_through_verbatim` |
| M8 | Goal 7 from the other side — union grows on a roleless project | `parsers.py:2659` | RED (2) | `test_the_preflight_scans_exactly_the_hook_list_and_nothing_else` |
| M9a | declared threshold 90 → 30, tools unchanged | `state-schema.json:769` | **GREEN, intended** | tracks the schema — the half that proves M9b is not vacuous |
| M9b | same, **plus** the script hardcodes 90 | + `perry-state:641` | RED (2) | `test_the_threshold_is_the_schemas_and_not_the_scripts` |
| M10 | a second backtick extraction reappears in the linter | `perry-lint:896` | RED (1) | `test_the_linter_does_not_carry_its_own_extraction` |
| M11 | roleless fallback deleted from `delegate.md` | `delegate.md:149` | RED (1) | `test_delegate_still_documents_the_path_for_a_project_with_no_cards` |
| M12 | hardcoded three restored | `delegate.md:3` | RED (1) | `test_delegate_no_longer_names_the_three_agent_types` |

**On M9a.** A single mutation of the staleness threshold would have been
decorative: the schema says 90 and a hardcoded 90 passes every test. So it is
run as a pair — move the *declared* number and confirm the tests track it
(green, correct), then move it *and* hardcode the old value and confirm the
disagreement is caught (red). Stated rather than left as an apparently-passing
mutation, because a green mutation with no explanation is exactly what a blind
guard looks like.

## The gate

```
python3 -m unittest discover -s tests -q        → Ran 1165 tests   OK
                                                  (1129 at branch point, +36)
python3 bin/perry-lint                          → 0 errors, 0 warnings
python3 bin/perry-lint --knowledge              → 0 findings, 1 card
python3 bin/perry-lint --root <copy gimegime>   → 59 errors, 28 warnings  (unchanged)
python3 bin/perry-lint --root <copy PolyForge>  → 11 errors,  0 warnings  (unchanged)
python3 bin/perry-lint --knowledge --root <copy gimegime> → 0 findings
```

Neither external project moved. Both were **snapshot copies** in the scratchpad;
the originals were never opened for writing.

## Found and not fixed

- **`escalation.union` is published but the pre-flight that consumes it is
  prose.** `dispatch.md` step 4 tells the agent to scan against it; nothing
  forces the agent to. That is true of the whole pre-flight today and is not a
  regression, but it does mean the union's *use* is V3-tested only at
  `perry-lint --verification`, which reads the same list for the consequence
  rule. A mechanical pre-flight is a bigger change than this phase and would
  want its own design.
- **`Executors: codex only` is parsed and published, and nothing enforces it.**
  Enforcing it would mean touching `bin/perry-dispatch-limit`, which § 6.1
  puts explicitly out of scope for phase D. The field is carried so a renderer
  can state it; the restriction is currently honoured by the human choosing the
  executor.
- **`Loads → pack:` is parsed and published and has no consumer yet.** A pack
  supplies practice (DESIGN-003 § 5.6); wiring pack procedures into the
  delegation prompt is a different seam and was not in the payload.
- **The roster answers half of § 7b's ask.** `--section roles` gives "which
  roles exist" in one call. "What is each working on" needs the task contract's
  `role` field, which is phase E.
