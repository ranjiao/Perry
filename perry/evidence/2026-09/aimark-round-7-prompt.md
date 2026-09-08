# Delegation prompt for an aiMark coding agent — round 7

> Rendered 2026-09-08 against `~/proj/Perry` at `ee5f3c42` on `main`. Every
> version, count, refusal string and payload quoted below was taken from a
> command run on that tree today, not from a document.
>
> **Perry has not executed this work.** Paste the block below into a fresh
> session **in the aiMark repository**.
>
> **Where aiMark reads Perry from.** `resolvePerryHome` probes
> `~/.claude/skills/perry`, a symlink to `/Users/bytedance/proj/Perry`. That
> checkout is **587 commits ahead of `origin/main`** and none of it is pushed —
> so aiMark already sees everything below, and reading GitHub would show you a
> different project. Read the working tree.
>
> **This round is not shaped like the others.** Rounds 2–6 asked you to find
> gaps. This one is Perry disclosing three changes it made under your feet, one
> of which is breaking your create path right now. The finding half is § 4.

---

You are working in the aiMark repository at `/Users/bytedance/proj/aimark`
(HEAD `c0cffd2`, branch `arch-review-p0-p1`). Perry lives at
`/Users/bytedance/proj/Perry` and is **read-only to you** — read its contract
documents and run its read tools; change nothing in it.

## 0 · Round 6 is answered — and two of the three asks are still open on Perry

Your `doc/perry-contract-gaps-6.md` § 10 sent back four items. Three were for
Perry. Here is the honest state of each, including the two Perry has not done.

| your § 10 | ask | disposition |
|---|---|---|
| 1 | is there a case where a consumer must resolve the state root itself? | **answered below — no.** Measured 2026-09-02, and it sat in a task row instead of reaching you. That delay is Perry's. |
| 2 | `schema/README.md § Where the files are` is stale | **filed as `TASK-301`, `not_started`.** Still stale today. |
| 3 | `bin/perry-config --help` names a deleted tool | **filed as `TASK-302`, `not_started`.** Still names it today. |
| 4 | `tests/fixtures/sample-project` is store-less and task-less | not a request; unchanged, and § 1.4 below turns it into something useful |

### 0.1 — § 10 item 1, answered: no consumer must resolve the state root itself

**You were right to decline the markdown fallback.** The measurement, 2026-09-02:

`perry-state` resolves the state root **itself** and publishes it, including on
a project that has no store. Built a project carrying only `.perry/config.md`
with `State root: docs` and no `config.jsonl`:

```
perry-state --section project   →   state_root "docs",  settings_source "absent"
```

So a consumer that can run the tools **never** needs to parse the markdown, and
one that read the store alone would get it wrong on a store-less project — the
tool's fallback is the thing that makes both cases answer the same. The only
consumer that would need to resolve the root itself is one that cannot run the
tools at all, and Perry has none.

`tests/fixtures/sample-project` reports `state_root ""` because its own
`config.md` declares no such line, not because the fallback is missing.

**What that makes `TASK-301`**: not "the page is stale" but "the page instructs
the consumer to do a job the tool already does better." That is the fix, and it
is not shipped.

---

## 1 · Three changes landed under a version that did not move

`src/perry-cli.ts § CONTRACT_TESTED` reads, today:

```ts
task: "1.18",  goals: "2.3",  decide: "2.0",  events: "1.2",
knowledge: "1.1",  roles: "1.1",
```

**All six are current.** There is no version drift and nothing in this section
is detectable by that constant — which is the point of the section.

| contract | you | live | gap |
|---|---|---|---|
| `perry-task/list` | 1.18 | 1.18 | none in the payload; **the WRITE path changed** — §§ 1.1–1.4 |
| `perry-goals/list` | 2.3 | 2.3 | none in the shape; **every KR id VALUE changed** — § 1.5 |
| `perry-decide/list` | 2.0 | 2.0 | none |
| `perry-events/list` | 1.2 | 1.2 | none (one doc defect, § 3) |
| `perry-knowledge/list` | 1.1 | 1.1 | none |
| `perry-roles/list` | 1.1 | 1.1 | none |

Between your round-6 measurement (`9ce39c9`, 2026-09-02) and `ee5f3c42` there
are **69 commits touching `bin/` and `schema/`** (74 counting
`viewer/parsers.py`). All of the consequence is
below the version line.

### 1.1 — `perry-task add` refuses without `--summary`, and your create path does not send one — **BREAKING, LIVE TODAY**

Landed `b0b98582`, 2026-09-03, `TASK-325`.

`src/perry-cli.ts § writeArgs` builds the `add` argv as:

```
--title --deliverable --verification --priority --owner --next
--track --group --kr --rung --prefix --role
```

There is no `--summary`. Run against `ee5f3c42`, with your exact flag set:

```
$ perry-task add --title "probe row" --deliverable d --verification v \
    --root <fixture> --actor aiMark --json
{
  "refused": "--summary is required: one or two sentences of plain language
   saying why this row exists and what is true when it is done, for a reader
   who was not in the conversation that filed it. The title is shorthand for
   people who already know; this is the field `perry-explain` prints and a
   front-end renders. `perry-lint --summaries` lists the rows already filed
   without one"
}
```

Adding `--summary` succeeds and returns the row. **So every create from the
aiMark UI is refused right now**, and `O4-KR3` — *"a full task lifecycle,
create → start → close, driven end to end from the aiMark UI"* — is not
merely undone, it is unreachable by construction until this flag is sent.

**Perry did not bump for it, on purpose, and said so in the page**:
`schema/task-list-contract.md:605` — *"The contract stays at
`perry-task/list/1.18`. This is the stated version consequence, not a silent
hold."* The reasoning is that no payload key changed shape. That reasoning is
about the READ contract and it is defensible; the cost is that the only
mechanism you have for noticing — `CONTRACT_TESTED` plus `semantics` — cannot
see a write-path refusal by design. **That is the gap this round exists to
name**, and § 4 is where you get to say what should replace it.

The field's definition, for what the form has to ask for:
`schema/task-list-contract.md:134` — plain language, in the project's declared
document language, for a reader who was not in the conversation that filed the
row; `""` means unset; **never inferred** from `title`, `next_action`, specs,
evidence or journal prose. Perry checks **structure only** — absent, or
restating the title. Nothing checks the prose, so do not read the tool's
silence as a quality signal.

### 1.2 — `add --kr` was accepted and inert until 2026-09-07

You have been passing `--kr` on every create. Perry accepted it from
2026-08-17 and, in the words of `e106f1f6`'s own message:

> *"`--kr` was already accepted by `perry-task add` and read by exactly one
> line — the journal's `- **KR linkage**:` prose — so the flag had no effect on
> any state a reader consults."*

`TASK-279` (2026-09-07) made it write the edge inside the row's transaction.
**Every KR attribution aiMark made at create time before that date reached
journal prose and nothing else** — no linkage edge, and nothing
`perry-goals list` or `perry-state --section attribution` would report. If any
of your rows or screens assume those edges exist, they do not, and no migration
backfills them.

Blank values are now refused (`TASK-281`): `--kr "   "` is an explicit refusal,
not a way to say "no KR". Your `flag()` helper only pushes a trimmed non-empty
value, so **you never send a blank one** — that is already correct and worth
keeping deliberately rather than by accident.

**Two known, unfixed costs of using `--kr` at add time**, so the choice is
informed rather than inherited: `TASK-383` — on a project whose register is
still the phase document, every `add --kr` writes the edge into the store,
leaves the document stale, and no shipped tool can clear the resulting lint
drift; and `TASK-391` — `--actor goals` alongside `--kr` writes a record a test
forbids and the append-only writer cannot retract it. Both are `P1` and both
are `not_started`. Neither is a reason to stop sending `--kr`; both are reasons
to know what it costs, and § 4 question 1 is where you say whether a write
contract should have told you.

### 1.3 — a new stderr advisory on every `add` without `--kr`, exit 0, and `--json` does not silence it

`writeArgs`'s own comment says `--json` is always passed because *"it silences
the advisory conformance line, which would otherwise arrive on stderr and read
like an error to a UI that only knows exit codes."* That premise no longer
holds for this line. Measured today:

```
$ perry-task add … --summary "…" --json 2>/dev/null   # stdout: clean JSON
$ perry-task add … --summary "…" --json 1>/dev/null   # stderr:
perry-task: warning — TASK-003 was created without `--kr`, so no KR edge was
recorded and the row reads as never-asked. It is NOT declared unlinked:
`perry-goals link TASK-003 <KR-ID>` attributes it, `perry-goals link --unlinked
TASK-003` declares outright that it serves no KR, and `perry-task add
--unlinked` declares it at creation on a row not yet filed.
exit 0
```

The write succeeded. A UI that treats non-empty stderr as failure will now
report a false error on the common path — creating a row without naming a KR.

The `add` result also gained two keys: `register_store` and `linkage_record`,
both `null` when no edge was written.

### 1.4 — `--unlinked` exists, and it is refused on a store-less project — including aiMark's own

`TASK-394`, 2026-09-07. `perry-task add --unlinked` declares **at creation**
that a row serves no KR — the third state, distinct from "attributed to a KR"
and from "never asked". `--kr` and `--unlinked` together are refused on
presence, with no precedence rule.

**The two flags do not behave alike on the same project, and this is the part
that matters for a tool that drives arbitrary projects.** Measured today on a
store-less fixture:

```
add --kr O9-KR9        →  ACCEPTED. "register_store": null, "linkage_record": null.
                          The unresolvable id is not checked (§ 2.1).
add --unlinked         →  REFUSED: "--unlinked needs `linkage.jsonl` and this
                          project has none, so the declaration would be accepted
                          and stored nowhere. … Nothing was written."
```

**aiMark's own project is store-less.** `/Users/bytedance/proj/aimark/perry/`
holds `BOARD.md`, `OKR.md`, `DECISIONS.md`, `PROJECT_STATE.md`, `decisions/`,
`journal/`, `knowledge/` — no `tasks.jsonl`, no `linkage.jsonl`. So on your own
dogfood project `--unlinked` is refused, `--kr` reaches an event field and
nothing else, and `perry-lint --summaries` answers *"no `tasks.jsonl` —
summaries are unchecked, not clean"*. Whatever you build has to render that
project correctly, and it is the majority case, not the edge one.

### 1.5 — every overall KR id VALUE changed, and `perry-goals/list` is still 2.3 with nothing in `semantics`

`ADR-017` completed the rename Perry had half-done for weeks:

```
KR-O<n>.<m>   →   O<n>-KR<m>        overall
P<NNN>-O<n>-KR<m>                   in a phase, unchanged since TASK-180
```

Measured on `ee5f3c42`: `perry/OKR.md` carries **41 new-form ids and 0
old-form**; `perry-goals list --json` returns `O1-KR1`, `O4-KR2`, and so on.

**And the contract did not move.** `perry-goals/list` is still `2.3`; the
payload's `semantics` array's newest entry is still `2.2`;
`schema/goals-list-contract.md` has not been touched since 2026-08-28 and does
not mention `ADR-017` anywhere.

By that page's own precedent this is wrong. `2.2` is described in its changelog
as *"no key added, one value's meaning changed"* — the exact shape of this
change — and it moved the minor and wrote a `semantics` entry. **This one
should have been `2.4`, and Perry is telling you that rather than waiting for
you to find it.** Whether it becomes `2.4` is § 4, question 2.

Three `ADR-017` rounds each recorded, in writing, *"I did not check aiMark"*
(`perry/evidence/2026-09/ADR-017-rename-result.md:381` and three others), and
the ADR's own *"What would reopen this"* names you first. So this is disclosed,
not discovered.

**What Perry found when it finally did look**, so you are not re-deriving it:
`objectiveLabel` in `src/work-model.ts` matches `(?:^|[-_.])O(\d+)(?=[-_.]|$)`
and reads **both** grammars; `src/work-model.test.ts:1397-1399` asserts both.
That function survives. Perry did not audit your other id consumers and is not
claiming they do.

**And you cannot drop the old grammar, because Perry still mints it.**
`goals/state/OKR_TEMPLATE.md` carries six old-form ids and is what a new
project's `OKR.md` is built from — filed as `TASK-393`, `not_started`. Your own
`perry/OKR.md` is old-form throughout. So today the honest answer is **both
grammars are live**, and § 4 question 2 is where that gets settled rather than
left to a regex that happens to work.

### 1.6 — `linkage.jsonl` is a seventh store, and the goals contract page has not caught up

`TASK-276` / `TASK-277` / `TASK-278`, 2026-09-04 to 09-07. The KR↔task register
moved from `phase/<NNN>-linkage.md` into a JSONL store: declared in
`schema/state-schema.json` `claims[]` with three record schemas, registered in
the `perry-lint` census as the seventh store, and `perry-goals link` and
`perry-goals krs` now judge and write from it.

`schema/goals-list-contract.md` does not mention `linkage.jsonl` — the word
appears only in `state-schema.json`. The payload keys you read
(`answered_by`, `linkage`, `unlinked_task_ids`) are unchanged in name and type;
what changed is what answers them.

Round 6 § 6 said aiMark has **never** parsed the phase linkage markdown, and
that is why this is a note and not a break. Say so again if it is still true —
it is the cheapest confirmation in this round.

---

## 2 · Hazards Perry is telling you about deliberately

**2.1 — `add --kr` never resolves the id, so a typo lands in the store and
nothing reports it. Perry found this while writing this prompt; it is not on
the board yet.**

The refusals at `bin/perry-task:3658-3684` check the flag's *presence* and its
*blankness* and stop there, and the code comment says outright that whether
`NOT-A-REAL-KR` resolves is a different row's question. Measured today on a
fixture carrying a `linkage.jsonl` that declares exactly `P002-O1-KR1`:

```
perry-task add --kr P002-O1-KR1  →  ACCEPTED. edge record written. correct.
perry-task add --kr O9-KR9       →  ACCEPTED. edge record written.
                                    perry-lint then warns [linkage-store-malformed]:
                                    "`kr` is 'O9-KR9', which does not match
                                     ^P\d{3}-O\d+-KR\d+$"
perry-task add --kr P002-O7-KR9  →  ACCEPTED. edge record written.
                                    perry-lint reports NOTHING. No such KR exists.
```

**The third line is the one that matters.** A well-formed phase KR id that the
register does not declare is written into `linkage.jsonl` as a real edge and no
instrument reports it. `perry-lint` checks the id's *grammar*, never its
*existence*.

And the other writer into the same store refuses the same attribution hard:

```
$ perry-goals link TASK-001 O9-KR9
perry-goals: refused — 'O9-KR9' is not a KR id, a Project id or a registered
alias in this phase's graph. Its KR ids are: P002-O1-KR1, P002-O1-KR2,
P002-O2-KR1. A near-match is not a match — attribution is never guessed from a
name (reference/okr-linkage.md § The one rule). … Nothing was written
```

Two writers, one store, two rules. **So: build the `--kr` control as a picker
from `perry-goals list`, never a free-text field.** Perry will not catch a typo
at `add`, and the second line above also tells you the store only accepts the
**phase** form `P<NNN>-O<n>-KR<m>` — an *overall* id in the ADR-017 grammar
(`O2-KR1`) is written and then called malformed by the linter.

That refusal text is also the shape your picker wants: it enumerates the valid
ids. Use it.

**2.2 — `summary` is on `perry-task list` and NOT on `perry-state`'s board.**
Filed as `TASK-384`, `P1`, `not_started`, and measured there: `perry-state`'s
board payload omits the key on **all 145 rows** while `perry-task list` carries
it on **133**, and `schema/state-schema.json` never mentions the field. A
consumer following `SKILL.md`'s instruction to read `perry-state` cannot see a
field the writer will not let a row exist without. **Read `summary` off
`perry-task list`.**

**2.3 — the board is a live tree.** Unchanged from round 5. Perry's checkout is
not clean between reads and two reads minutes apart legitimately disagree; a
moving count is not a contract violation.

---

## 3 · Known open on Perry's board — please do not spend this round re-reporting them

Every one of these is filed, argued and unfixed. If you hit one, a line saying
"still true at `ee5f3c42`" is worth more than a re-derivation.

| row | state | what |
|---|---|---|
| `TASK-301` | P1 not_started | `schema/README.md` still sends a consumer to `.perry/config.md` for the state root — **your round-6 § 10 item 2** |
| `TASK-302` | P2 not_started | `bin/perry-config --help` names deleted `perry-conform` — **your § 10 item 3** |
| `TASK-354` | P2 not_started | `schema/events-list-contract.md:61` says twenty-six kinds; the table has twenty-seven |
| `TASK-384` | P1 not_started | § 2.2 above |
| `TASK-393` | P1 not_started | `OKR_TEMPLATE.md` still mints the retired KR grammar |
| `TASK-271` | P1 not_started | `tracks_source` on two published payloads, four values, no entry in `schema/` or `reference/` |
| `TASK-390` | P1 not_started | a design's `Linked OKR` line is parsed into a field nothing reads |
| `TASK-383` | P1 not_started | **`add --kr` leaves permanent lint drift** on a project whose register is still `phase/<NNN>-linkage.md`: the edge lands in the store, the document goes stale, and `perry-goals link` answers "nothing to write" because it checks the store. One row of drift per `add --kr`, unclearable by any shipped tool |
| `TASK-391` | P1 not_started | `add --kr --actor goals` — a combination the help text documents — appends a record a test forbids, and the append-only writer has no retraction |
| `TASK-206` | P1 not_started | **a write returns no seq** — your round-5 § 4.2 ask, still open |
| `TASK-184` | P1 not_started | `okr.objectives[].id` filled from the store; would move goals to `2.2`-style additive again |

`TASK-206` is the one to notice: you asked for it in round 5, Perry filed it,
and it has not moved. It is also the thing § 4 needs an answer about.

---

## 4 · The ask back — four questions, and the write contract is still zero

Perry's Objective 4, at `ee5f3c42`:

| KR | target | actual |
|---|---|---|
| `O4-KR1` lines in aiMark parsing Perry's markdown | 0 | your count, you own it |
| `O4-KR2` a versioned, test-locked **write** contract exists | 1 | **0 — none exists** |
| `O4-KR3` a full lifecycle driven from the aiMark UI | 1 | **0, and currently unreachable — § 1.1** |
| `O4-KR4` goals and decisions writable on the same shape | 2 of 2 | 0 |

Round 5 asked you to specify the write contract and you answered in
`perry-contract-gaps-5.md` § 4 — verbs 1–4 need nothing new, a write should
return the row plus a `seq`, and you refused a conflict-resolution API on the
grounds that *"a dialog that offered 'overwrite anyway' would be aiMark
deciding something it has no information about."* Perry filed `TASK-206` and
`TASK-207` and shipped neither. **That is why § 1.1 could happen**: with no
write contract, there was no surface a required-flag change was obliged to
break, so it broke you instead.

So, four questions, in the measured form your reports take:

1. **What is the minimum write contract that would have caught § 1.1?** Not the
   full design — the smallest published thing whose test would have gone red
   the day `--summary` became required. A version string on the write path? A
   `perry-task add --describe` that enumerates required flags? Something else?
   Perry will build what you name and will not invent it from the inside — that
   is the same call `TASK-059` and `goals/2.2` made, and this round is the bill
   for it.

2. **One KR grammar or two?** Perry retired `KR-O<n>.<m>` in its own data and
   still mints it from the shipped template (§ 1.5), and your own board is
   old-form. Either Perry fixes `TASK-393` and you may eventually assume one
   grammar, or both stay live forever and the dual-read is a documented
   requirement rather than a lucky regex. Which do you want, and what does it
   cost you either way?

3. **Should the ADR-017 rename have been `perry-goals/list/2.4` with a
   `semantics` entry?** Perry believes yes, by its own `2.2` precedent. You are
   the consumer whose detection mechanism it would have fired. If you think a
   value-space change to *identifiers* deserves a major rather than a minor,
   say so now — the bump has not been made yet and can be shaped by this
   answer.

4. **What do you want on stderr?** § 1.3 broke a premise your code documents.
   State the rule you want Perry to hold: `--json` silences everything
   advisory, or advisories move onto the payload as a key, or exit codes carry
   it. Perry will hold whichever you name.

---

## 5 · Acceptance

1. `writeArgs`'s `add` branch sends `--summary`, and the create form asks for
   it with the definition at `schema/task-list-contract.md:134` in front of the
   user — not a placeholder the user skips.
2. The lifecycle create → start → close is driven end to end against a real
   project and the result is stated, pass or fail. That is `O4-KR3` and it is
   the one KR this round can actually move.
3. `--kr` is a picker built from `perry-goals list`, not free text (§ 2.1) — or
   an explicit note saying why free text is acceptable to you. If aiMark has
   created any row with `--kr` since 2026-09-07, check those edges against
   `perry-goals list` for a dangling one; nothing on Perry's side would have
   reported it.
4. The stderr advisory (§ 1.3) no longer surfaces as an error, and § 4 question
   4 says what you want instead.
5. `summary` is read from `perry-task list`, never from `perry-state` (§ 2.2).
6. A one-line verdict on § 1.6: does aiMark still not parse the linkage
   register?
7. `--unlinked` is either adopted as a create-time option **gated on the target
   project having `linkage.jsonl`** (§ 1.4), or explicitly deferred with a
   reason. Your call, but say which.
8. `CONTRACT_TESTED` is unchanged and a comment says why — it is current, and
   that is exactly the finding this round reports.
9. The suite is green and you report the numbers, before and after.

## 6 · Report back

Same format as rounds 2 through 6 — `doc/perry-contract-gaps-7.md`, measured
against `~/proj/Perry`, every claim carrying the command that produced it.

Include § 4 in it. Rounds 5 and 6 both asked for the write contract and both
times Perry filed the answer and shipped nothing; § 1.1 is what that cost.
Question 1 is the one that stops it happening a third time.

## 7 · Out of scope

- Do not modify anything in `/Users/bytedance/proj/Perry`.
- Do not migrate aiMark's own `perry/OKR.md` to the new KR grammar. Both forms
  are live (§ 1.5) and `TASK-393` is Perry's to fix first; migrating now would
  make your board the only new-form store-less project in existence and prove
  nothing about either grammar.
- Do not re-report § 3. A "still true" line is enough.
- Do not build against `okr.objectives[].id`; `TASK-184` is `not_started` and
  it is still `""` on every objective.
- Do not widen the layout reader. `TASK-172`'s deferral (four document
  collections reachable through no contract) is unchanged and is still the
  user's call, not this round's.
