# User load — the human is the bottleneck

Shared contract. Read by `okr`, `pmo`, `design`, and `diagnose` alike, because
all four generate things a person has to read and decide, and all four fail the
same way when they forget who they are writing for.

## The premise

An agent has broad competence and perfect recall. It can reason about
cryptography, tax law, and CSS in the same session, and it remembers every ID
it ever minted. The user has neither. They are expert in a few areas, hazy in
the rest, and they cannot hold forty identifiers in their head.

**The project is theirs, and they are the only irreplaceable part of it.** So
the binding constraint on an agent-run project is almost never the agent's
capability. It is how much the person can absorb, look up, and decide. A
project that outruns that constraint doesn't announce itself — it just quietly
becomes something the user nods along to and no longer steers.

Two failure modes, both of which Perry has committed.

## Failure 1 · Decisions above the user's capacity

The agent researches deeply, finds four legitimate options, and presents them
with honest trade-offs. The user understands none of them. They pick the one
that sounds safest, or the first, or they say "you decide" and feel bad about
it. Either way the decision was not actually made by anyone — and it is now
recorded as if the user chose it.

This gets worse the better the agent is. Depth of analysis and usefulness of a
question come apart completely once the subject leaves the user's expertise.

### The test

Before asking, answer this yourself: **can the user predict what will be
different for them under each option?** Not "will they understand the
mechanism" — will they be able to tell the outcomes apart.

- **Yes** → ask. This is a real choice and it is theirs.
- **No** → do not ask it as-is. Take one of the three exits below.

### The three exits

1. **Reframe in consequences.** Most unanswerable questions become answerable
   when restated in what the user will experience. Not *"Postgres, SQLite, or
   DynamoDB?"* but *"Do you want this to run on your laptop with no setup, or
   to survive multiple people using it at once? The first is a day of work
   less."* Same decision, now decidable.
2. **Decide it and say so.** For anything reversible, pick the recommended
   option, state that you picked it, say what would make you revisit, and log
   it. This is the right default far more often than Perry's skills currently
   behave as though it is.
3. **Narrow, then ask.** Cut four options to two by ruling out what conflicts
   with the project's stated constraints, and show what you ruled out and why.
   Two options with a stated consequence each is decidable; four with technical
   trade-offs is not.

### Rules

- **Never present an option without what it means for the user.** A trade-off
  expressed only in mechanism ("row-level locking vs optimistic concurrency")
  is not a trade-off the user can weigh.
- **Cap open decisions at three at a time.** Past that, queue them and say you
  are queuing them. A decision backlog is worse than a work backlog: everything
  downstream either stalls or proceeds on a guess, and afterwards nobody can
  tell which happened.
- **Always offer the escape hatch, and mean it.** "Or I can pick and tell you
  what I picked" belongs on any question the user might not be equipped for.
  When they take it, do not ask a variant of the same question later.
- **Detect deferral and change mode.** Two "whatever you think" answers in a
  session is the user telling you the questions are landing wrong. Stop
  offering choices, start making recommendations they can veto, and say that is
  what you are doing.
- **Spend the user's attention on one-way doors.** Reversible decisions are
  cheap to get wrong and expensive to ask about. Irreversible ones are the
  opposite. If the skill is asking about the reversible ones, it has the budget
  backwards.

### What this costs, and the obligation it creates

Asking less means deciding more on the user's behalf, which is only acceptable
if those decisions stay **visible and reversible**. So every decision an agent
takes on the user's behalf is logged like any other — in `DECISIONS.md` or the
project's equivalent — and marked as agent-decided, with what would trigger a
revisit. The user must be able to find, later, every call that was made without
them. Silent autonomy is a worse failure than over-asking.

## Failure 2 · Identifiers the user cannot resolve

Stable IDs are genuinely good: precise, greppable, survive renames, keep a
board unambiguous. They are also write-optimized for the wrong reader. This
line is from Perry's own test fixture:

```
| REL-002 | Flake detector | Coding Agent | blocked | waiting on USER-014 |
```

To the agent that is complete. To the person it was written for, `USER-014` is
a dead end — they must go searching their own project to find out what they are
blocked on. Perry generates `REL-`, `ADR-`, `DESIGN-`, `P-O1.2`, `USER-`,
`CAD-`, `SRC-`, `CL-`, `RX-` and phase numbers. That is a private vocabulary,
issued to someone who never agreed to learn it.

### The rule: an ID never travels alone

**The first time an ID appears in any user-facing output — chat, dashboard,
report, generated document — it carries its human name.**

```
✗  REL-002 blocked on USER-014
✓  REL-002 ("Flake detector") is blocked on USER-014 ("Confirm staging env default")
```

Subsequent mentions in the same response may use the bare ID. Tables that
already carry a Title column satisfy this on their own. The cost is a few words;
the benefit is that the user can act on the sentence without leaving it.

### The lookup

`bin/perry-explain <ID>` resolves any ID in a project to what it is, where it
was defined, and everywhere it is referenced. `--all` prints the whole
glossary; `--dangling` lists IDs that are referenced but defined nowhere.

It reads the shapes markdown actually uses — table rows, headings, YAML ids,
ID-named files — rather than Perry's schema, so it works on any project. When a
user asks "what is X?", run it rather than searching by hand or guessing.

### Rules

- **Never mint an ID without a title in the same write.** An ID with no
  readable name defeats the lookup as thoroughly as having no lookup.
- **Never reference an ID that does not exist yet.** Prose naming work that was
  renamed, dropped, or only ever discussed is the hardest kind to resolve
  later, because nothing distinguishes those three cases afterwards.
- **Prefer the name in prose, the ID in tables.** Running text should read as
  English: "the flake detector is blocked on the staging-env decision". The ID
  belongs where things are indexed and cross-referenced.
- **Never invent an ID scheme the project did not ask for.** If a project has
  no IDs and no need to cross-reference, do not introduce them.

## How this is checked

- `bin/perry-diagnose` measures the surface in any project and reports
  `LOAD-01` (IDs with no way to look them up), `LOAD-02` (IDs referenced but
  never defined), `LOAD-03` (open decisions queued on the user), and `LOAD-04`
  (IDs defined with no readable name).
- `/perry diagnose` treats those as findings like any other, and its own
  interview obeys everything above — see `diagnose.md § The second rule`, which
  covers the adjacent problem of explaining findings the user cannot evaluate.

## See also

- [diagnose.md](diagnose.md) — the explanation contract for findings, and the
  procedure that reports the `LOAD-*` findings.
- [project-archetypes.md](project-archetypes.md) — the structural research;
  this file is its counterpart on the human side.
- [input-quality.md](input-quality.md) — the neighbouring gate, on the quality
  of what the user writes rather than the load placed on them.
