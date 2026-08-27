# TASK-175 — closed without a dispatch: aiMark had already built it

**Closed 2026-08-28.** Not by a Perry change and not by a dispatch of its own.
Perry's half shipped in `perry-goals/list/2.1`; aiMark's half shipped in its
`0b72629`. The row was open because nobody had checked.

## What the row asked for

> *"aiMark's KR meter renders a stale assertion identically to a fresh one."*
>
> `next_action`, decided by the user 2026-08-21: **mark it** — but *"do not
> caption every KR with 'this is an assertion', because it is true of all of
> them and says nothing. Only stale, and only unasserted."*

## Perry's half was already delivered

`perry-goals list --json` emits both keys on all 27 KRs, and
`schema/goals-list-contract.md:84-119` documents every subfield:

```
current_provenance   {state, measured, source, asserted_at, asserted_scope}
current_staleness    {stale, evaluated, reason, since, moved_tasks}
```

Measured on this project today: **6 KRs `asserted`, 21 `unasserted`**, and the
contract's `2.1` row credits TASK-120 for adding all four keys additively.

`asserted_scope: "register"` is emitted **beside** `asserted_at` for a stated
reason — the linkage register timestamps *itself*, not each KR, so the date is
not "when this number was arrived at".

## aiMark's half is built, and built to the restraint the user specified

`src/work-surface.tsx:120-127` reaches the user's conclusion in its own words
before rendering anything:

> *`current_provenance.measured` is `false` on every KR and no path sets it
> true … every KR would be decoration; the per-KR fact worth marking is
> staleness.*

That is the *"do not caption every KR"* instruction, arrived at independently.

| what | where |
|---|---|
| stale mark, gated on `staleness.stale` | `work-surface.tsx:531-537` — renders the reason **and** `moved_tasks` |
| the same, gated on `evaluated && stale` | `entity-pane.tsx:526` — *"the per-KR fact worth marking, and the only one"* |
| unasserted distinguished from asserted-and-fresh | `entity-pane.tsx:491-499` — a four-way branch: no `current` → `measured` → `asserted_at` with `register` scope → bare `asserted` |
| `asserted_scope` carried through verbatim | `work-surface.tsx:126` — commented as *"a trap"*, for the reason above |
| pinned version | `CHANGELOG.md:29` — `perry-task/list/1.14` and `perry-goals/list/2.1` |

**And it has tests**, one of which is this row's title restated as an assertion:

```
src/perry-cli.test.ts:887  goals 2.1's provenance and staleness parse,
                           and current is unchanged
src/perry-cli.test.ts:930  an unasserted current says so, and that is
                           not the same as fresh
```

`:924-925` assert `stale: true` and `moved_tasks: ["TASK-114"]` — so the mark is
proved against a moved task, not against a shape.

## What I verified, and what I did not — read this before trusting the close

**Verified**: the source and the tests, read directly in
`/Users/bytedance/proj/aimark` at its current checkout, plus Perry's own payload
and contract page re-measured today.

**Not verified**: I did not build or run aiMark, and I have not seen the
rendered result. A stale KR's mark exists in the code and in a unit test; whether
it is *legible* on screen — contrast, placement, whether it survives the chain
view's density — is a judgement about pixels I have not made.

**So the rung is V2 on evidence I read, not V3 on something I built.** The row
declared V3. I am closing at what the evidence supports and saying so rather
than letting the declared rung stand unearned — which is the failure mode
`perry-lint --verification` exists to catch, and it should not need to catch
this one.

**If you want V3**, the remaining step is one you can do in a minute: open
aiMark's OKR chain on this project, where `P-O1.1` and `P-O1.2` are asserted
and 21 KRs are unasserted, and confirm the three states are visually distinct.

## Why it was open at all

The same reason TASK-161 was: **it was resolved from a direction nobody was
watching.** TASK-161 was closed by TASK-176 and TASK-132 arriving from opposite
sides; this one was closed by the other repository. Perry has no signal for
"a row's subject moved in a project Perry does not own", and this is the second
instance in one night.
