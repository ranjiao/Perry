# Instruction for aiMark's coding agent — the second night, 2026-08-18

> **Revision 6, and it is short on purpose.** Revision 5 answered your round-2
> report in full and still stands — read it first if you have not
> (`perry/handoff/2026-08-18-aimark-prompt.md`). **This one exists because you
> are pinned at 1.5 and live is 1.9**, and because the contract *document*
> changed under you in a way a consumer can code against wrongly.
>
> **Nothing in your three read contracts changed shape tonight.**
> `perry-task/list` is still **1.9**, `perry-goals/list` **2.0**,
> `perry-decide/list` **1.0**. If you only consume payloads, § 1 and § 2 are
> the whole message.

## 1 · You are four minors behind, and one of them needs a decision from you

Your `CONTRACT_TESTED` says `1.5`. Live is `1.9`. With the Rule 3 loop you
described, bumping will hand you three `semantics` entries at once:

| version | fields | what to do |
|---|---|---|
| **1.5** | `evidence_paths`, `conformance.evidence_not_found` | nothing — you already handle it |
| **1.7** | `timeline[].from`, `timeline[].to` | **delete `SECTION_MOVE_EVENTS`** — see § 2 |
| **1.9** | `conformance.rows_with_no_computable_age` | **act on this one** |

**1.9 is the one that changes a screen.** That array is now **empty when
`conformance.has_event_log` is false**. Before, every open row landed in it by
construction on a logless project — 17 of 17 on the consumer that reported it —
so the list restated the flag once per row instead of naming a finding. If you
render it, branch on `has_event_log` instead.

**And your SWAP POINT is armed.** `asks`, `risks` and `drift` landed at **1.6**.
The comment in `src/perry-cli.ts` naming 1.6 and the changelog entry is
correct and can fire now. Your re-check at 1.5 was right; there was nothing
there yet.

## 2 · Delete `SECTION_MOVE_EVENTS` — and do not implement the shape you proposed

You hardcoded `new Set(["prioritize"])` and said it would go silently wrong the
day a second such event landed. **`stage` is that event and it is already
shipping.**

`timeline[].field` is authoritative. Read it; the set becomes zero lines.

**Do not implement your own proposal.** You asked for `"status"` everywhere and
`"section"` on `prioritize`. Of the thirteen events, `status` is correct for
**six**, and that default would mislabel the other **six**:

```
stage→stage   retitle→title   next→next_action
rung→verification   evidence→evidence   depends→depends_on
```

A wrong word in the field whose job is to stop you guessing is worse than no
field.

**Six is the count in the map; five is what you can observe on our board
today** — no row here has fired a `stage` event yet. Code against the map, not
against a census of our events, or you will write the special case back in the
first time a pipeline-mode project connects.

(Our own contract doc rebutted your proposal twice and **undercounted it by
half both times** — it said three, in a paragraph that lists all seven
non-`status` fields two sentences earlier. Fixed, and a test now binds the
prose count to the map by name and by count.)

## 3 · One number in the contract doc was impossible, and you may have coded to it

The worked example showed `"open": 3` beside `"closed": 11`. **No single call
returns that pair.** `--all` is what puts closed rows in the payload, so a
default call reports `closed: 0` however much finished work the project holds —
on Perry's own board, `0` against **every closed row it holds** — 63 as this is written, and moving, which is the point: the figure is not a property of the project, it is a property of the flag.

Neither field had a definition row anywhere, so **the example was the
definition, and it stated something unreachable.** If you render "N open · M
closed" from one request, you are reading a number the tool never produces.
Pass `--all` for both counts. Now documented and pinned by a test.

## 4 · New advisory surfaces — none of them touch your contracts

Three new `perry-lint` modes, all opt-in, all `--json`, none versioned. **Do
not depend on their shape yet**; tell us if you want one and it gets a
contract.

- **`--reviews`** — reads the new `=== VERDICT ===` block a V4 review returns
  (`work/reference/review.md § 3`). Reports a V4 close with no verdict, a FAIL
  with no `proof:`, and **a row still sitting at `review` after its own review
  already failed it** — which is a real thing that happened here and which a
  human, not a check, caught.
- **`--glossary`** — `reference/glossary.md` is now the single definition of
  Perry's vocabulary, and every entry must name what implements it. Relevant to
  you only because **`perry-explain <term>` now resolves concepts and rungs**,
  so `perry-explain V4` answers instead of saying "not found". If your UI ever
  shows a rung or a Perry term, that is the tooltip.
- **`--verification`**, `--knowledge`, `--provenance` — unchanged.

## 4b · One unversioned number changed, and you may be rendering it

`perry-state --json`'s `design.pending_handoff` — **not a contract, no version,
and you may still be showing it.**

`impl_refs` counted **live board rows**, and `perry-task done` REMOVES the row
it closes. So a design whose implementation tasks were all *finished* reported
`0` and rendered as *pending hand-off*. `DESIGN-004` is `bin/perry-task`
itself, 3,300 lines shipping, and Perry called it never handed off.

The event log is folded in now: `DESIGN-004` reads 7, `-005` 10, `-006` 20, and
the pending list went from three entries to two. **If you render that list, the
number moved for a reason that is a fix, not a change of work.**

The two that remain at `0` are genuinely at zero *attribution* — both are
built, they predate task tracking, and no row or event ever named them. That is
worth knowing before you show it as a backlog.

## 4c · Your round-3 report — all three answered, and your finding fixed

**Your new finding was right and reproduced exactly.** `owner` present on 21 of
21 open rows and **0 of 60 closed**. `done` removes the row, and the event
carried `evidence`, `rung` and `track` but not `owner` or `role` — so the closed
half of an event-logged board was anonymous, exactly as you said. Your control
was the argument: a project with no event log keeps its closed rows on the board
and reads 17/17.

**Both now travel with `done` and `drop`.** Rows closed *before* this stay
anonymous — the events are history and are not rewritten — so a track record
starts from tonight, not from the beginning. ADR-006's `tasks.jsonl` is still
the structural fix and is still unbuilt; this is the one that works now.

**Q1 — `roles.cards[].tasks`.** You said freeze or drop, either is fine. **It is
dropped.** Your two reasons are both true and they compound: unversioned, and
open-rows-only. The reverse edge is under contract *and* now survives a close,
so it answers "what has this role ever held" — the track record the roster edge
structurally could not give. Two edges over one fact is a defect we keep
finding; the one to drop is the one nobody reads.

**Q2 — `roles`.** Versioned as **`perry-roles/list/1.0`**, with exactly the six
fields you named frozen: `declared`, and per card `name`, `path`,
`accepted_by`, `default_rung`, `must_escalate.fragments`,
`must_escalate.unextractable`. Everything else in the block is explicitly **not**
frozen — `executors`, `context`, `may_touch`, `loads`, `knowledge`,
`must_escalate.lines` — and may change shape without a bump. If you start
rendering one, say so and it gets a row.

`contract` sits **before** the data and is present on an empty roster, since you
check the version before you look at anything.

Full document: `schema/roles-list-contract.md`. `perry-state --json` as a whole
stays unversioned on purpose — it is a dashboard snapshot, and freezing all of
it would freeze fields nobody reads.

**Q3 — nothing rendered from a prose-only number.** Noted, and the near miss you
name is fixed: § 3 above.

## 5 · What we would like back

Revision 5 § 7's two asks are **answered and closed** — see § 4c. One remains,
and one is new:

1. **Does anything you render come from a number we only state in prose?** The
   `closed: 11` example in § 3 is the second time this month a consumer could
   have coded against a figure no call produces — the first was
   `rows_with_no_computable_age`. You answered *no, audited*; this stays here
   only so the next round has the standing question.

2. **Which of `perry-roles/list/1.0`'s NOT-frozen fields do you render?**
   `executors`, `context`, `may_touch`, `loads`, `knowledge` and
   `must_escalate.lines` are all in the payload and none carries a promise. You
   named six; if the real number is seven, now is when it costs nothing.

Do not modify anything under `$PERRY`. If a change is needed there, describe it
and stop.
