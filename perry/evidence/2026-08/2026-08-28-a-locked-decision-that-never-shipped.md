# DESIGN-007 decision #4 was locked nine days ago and never implemented

<!-- [[old-form]] · This document QUOTES the pre-TASK-180 phase-KR form as
     the artifact under discussion; it does not reference KRs by it. TASK-180
     migrated the project on 2026-08-28 and deliberately left every id below
     standing. Occurrences inside a fence or a verbatim blockquote are marked
     by the sentence that introduces them; the rest carry the marker inline. -->

> Raised by the user 2026-08-28, on seeing me write `P-O1.2` [[old-form]] in
> a summary.
> They were right and I was wrong; this is what the measurement found behind it.

## The decision

`DESIGN-007-the-entity-model.md`, **`Status: locked`, `Locked: 2026-08-19`**:

| # | Decision | Chosen | Date |
|---|---|---|---|
| 4 | KR id namespace | **Segment-labelled and project-unique — `P002-O3-KR1`** | 2026-08-19 |

The document also records *why* it changed during review:

> the phase-KR id, from the drafted `002/P-O3.1` to **`P002-O3-KR1`**, on the <!-- [[old-form]] -->
> ground that **every segment should carry its own label rather than rely on
> position**

And its principle 5 states the rule the decision serves:

> **Every id is unique in its declared namespace**, and the namespace is
> declared. A KR id that repeats across phases is either made unique or
> documented as phase-scoped, **not left ambiguous**.

## What shipped: nothing

```
$ grep -rn "P002\|P00[0-9]-O" bin/ tests/ schema/ perry/   (excluding DESIGN-007)
   → no matches
```

The old form is still hardcoded in two places:

```
bin/perry-lint:124     KR_ID_RE = r"\bP-O\d+\.\d+\b"
bin/perry-explain:64   ID_RE = re.compile(r"\b((?:P-O\d+\.\d+)|…)\b")
```

**`TASK-103` — "Lock DESIGN-007" — is `done`.** Locking was the whole row;
implementing decision #4 was never given one. **No open row carries it.**

This is the second instance tonight of the same shape: TASK-092 closed with
half its title outstanding and the phase KR honestly recording `1 of 2`. Here
the decision closed and nothing recorded anything.

## The ambiguity is real, and it has already cost a bug

Same id, two phases, two different KRs — the block below is the collision
itself [[old-form]], and migrating it would delete the demonstration:

```
001-linkage.md  P-O1.1  "Non-`project` modes running on a live, non-fixture track"
002-linkage.md  P-O1.1  "`BOARD.md` is rendered from `perry/tasks.jsonl` …"
```

`bin/perry-lint:1111` carries the scar:

> **A linkage file belongs to ITS phase, not to the current one.** This judged
> every `*-linkage.md` against the CURRENT phase's KR set, so the moment a phase
> was scored and the next one opened, the old phase's registry — which correctly
> names the KRs it was written for — was reported as dangling. **It fired on the
> first rollover this project ever did.**

The fix recovers the phase from **the filename**:

```python
own = lf.name.split("-", 1)[0]
```

**That line exists because the id does not carry its own phase.** Under
`P002-O3-KR1` there is nothing to re-derive. The locked decision would have
deleted this workaround; instead the workaround shipped and the decision did
not.

TASK-156's agent reasoned from the same fact last night, independently: *"a KR
id is phase-scoped — `P-O1.1` [[old-form]] names different KRs in 001 and 002 — which is
exactly why that guard had to re-derive its comparand per file."* It built a
correct guard **on top of the ambiguity**, because the ambiguity is the world it
found.

## The detail that makes this hard to see

**`DESIGN-007`'s own frontmatter uses the format it decided to replace**, as
it stood before TASK-180 [[old-form]] — the line below is quoted, not live:

```
> Linked OKR: P-O3.1 (phase 002 — `fields-are-typed`)
```

A locked document written in the notation it abolished, parenthesising the
phase in prose — which is the ambiguity, spelled out by hand, in the document
that ruled against it.

## What I got wrong

I wrote `P-O1.2` [[old-form]] in a handoff and in a summary as though it
identified one KR. **It does not.** I had also been treating the
phase-scoping of `P-O1.1` [[old-form]] as a *fact
about the world* — I repeated it in three evidence records last night as the
reason a guard must be phase-scoped — **without ever checking whether it was a
decided state or an undone one.** It is undone.

The lesson is narrow and worth keeping: *"the code does X consistently"* is not
evidence that X is intended. `perry-explain` and `perry-lint` agreeing on
`P-O\d+\.\d+` made it look settled.

## Scope, if it is taken

Migrating ids touches the two regexes, both linkage registers, the phase files,
`schema/goals-list-contract.md`'s examples, and every evidence record that
quotes a KR id — **and the last of those is the reason to decide it
deliberately rather than sweep it.** `TASK-142`'s `means` text forbids
rewording verbatim quotes, which is the same wall TASK-179 is standing at.

**It is the user's decision, not a cleanup.** DESIGN-007 is locked, so
implementing it needs no new argument — but the migration's blast radius does.
