# ADR-017 — One KR id grammar at both levels: O3-KR1 overall, P003-O2-KR1 in a phase

> Status: active
> Type: Architecture
> Date: 2026-09-02
> Deciders: Ran Jiao
> Supersedes: —   · Superseded by: —
> Sunset: —

## Context

Two KR id grammars are live and nothing records why.

Measured 2026-09-02: `perry/OKR.md` carries **20** unique ids, every one of the
form `KR-On.m`. `phase/003-linkage.md` carries the phase form `P003-O2-KR1`.

`DESIGN-007` decision 4 is explicit that the rename runs at **both** levels:
*"The overall (non-phase) KR follows as `O3-KR1` — the same grammar with the
phase segment absent, replacing today's `KR-O1.1`."* [[old-form]] Step 10 of its plan carries
it. Its stated reason is that a `serves` edge can store one value only if ids
are **project-unique and self-labelling**.

`DESIGN-009 § 3` makes the opposite a Non-Goal: *"Changing `KR-O<n>.<m>` ids.
They are the user's, they are on the board, and 27 of them resolve today."*

**The repository sided with DESIGN-009 and nobody recorded the reversal.** The
phase level migrated; the overall level did not. Six later design headers
(008 through 014) cite `KR-O2.1`-style ids [[old-form]], so the abandoned half of decision 4
is now load-bearing prose across the corpus.

Raised by the 2026-09-02 design-register audit as `C-03`, which names the cost:
*"Half-migrated ids mean the two levels are read by two grammars, which is what
`DESIGN-007 § 1.4` opened by complaining about."*

## Options

1. **Complete the migration — chosen.** `O3-KR1` overall, `P003-O2-KR1` in a
   phase. One grammar, the phase segment present or absent.
2. **Ratify the split.** Record that decision 4's overall half was abandoned and
   keep `KR-On.m`. **This was the PMO's recommendation** — cheapest, matches the
   repository, and 20 ids plus six design headers already depend on it.
3. **Leave it undecided**, noting it as an open question. Rejected: it has been
   undecided long enough for six documents to bind to one side of it.

## Chosen

**Option 1, over the PMO's recommendation of option 2.** Recorded that way
because the override is the decision, and because `DESIGN-009`'s reason for the
Non-Goal — *"they are the user's"* — was answered by the user electing to change
them.

The grammar is `[P<NNN>-]O<n>-KR<m>`: the phase segment is present in a phase KR
and absent in an overall one. `DESIGN-007`'s stated property is then true at both
levels rather than at one.

## Consequences

- **20 ids in `perry/OKR.md` are renamed.** That file belongs to the `goals`
  lane; this ADR proposes and does not perform it.
- **Every `linked:` field in `phase/<NNN>-linkage.md` points at an overall id**
  and must move with them — the phase register is `goals`-owned too.
- **Six design headers (`DESIGN-008` through `DESIGN-014`) cite the old form in
  their `Linked OKR:` line.** They are locked; a `## Changes` entry records the
  rename rather than editing the header, unless the lane decides the header
  field is metadata rather than body.
- Board rows carrying a `Commitment` or KR reference in prose are **not**
  rewritten by this ADR. A stale reference in an old row is history.
- **The migration must be one edit, not a sweep.** A half-done rename is worse
  than either grammar: `perry-goals link` refuses anything not resolving to
  exactly one KR, so a partially migrated register fails closed rather than
  silently — which is the property that makes this safe to attempt.
- `DESIGN-009 § 3`'s Non-Goal is superseded in substance. It is locked; a
  `## Changes` entry points here.

## Evidence

- `DESIGN-007` decision 4 and step 10 — the rename at both levels.
- `DESIGN-009 § 3` — the Non-Goal, and § 8's question that assumes survival.
- Measured 2026-09-02: 20 unique `KR-On.m` ids in `OKR.md`; phase form
  `P003-O2-KR1` in `phase/003-linkage.md`.
- The 2026-09-02 design-register audit, finding `C-03`.

## Changes (append-only after lock)

**2026-09-08 — the `Linked OKR:` header field is METADATA, and the count in
Context is off by one.** Both settled by the `decide` lane, which this ADR's own
Consequences delegate: *"a `## Changes` entry records the rename rather than
editing the header, **unless the lane decides the header field is metadata
rather than body**."*

**Metadata, and the evidence is decisive rather than definitional.** The field
has **no consumer**. `viewer/parsers.py:3397` parses `Linked OKR` into a
dataclass field and sets it at `:3409`; nothing in `bin/` reads it and `tests/`
does not reference it once. ADR-017's document round proved the consequence
rather than arguing it: it pointed `DESIGN-011`'s `Linked OKR` at a grammar
nothing resolves and re-measured — `perry-lint` **0 errors**, the
`perry-diagnose` finding set **byte-identical**, no `LOAD-02`, and
`user_load.dangling` **`[]` before and after**. A line that can name a
nonexistent id with every instrument green is not body.

**Consequence**: the seven headers are edited directly, **inside the atomic data
rename** this ADR requires (*"one edit, not a sweep"*), rather than becoming
seven `## Changes` entries in locked designs. That the field is decorative is a
defect in its own right and is `TASK-390`; it is **not** fixed by this rename and
must not be conflated with it.

**The count.** Context says *"Six later design headers (008 through 014) cite
`KR-O2.1`-style ids"* [[old-form]]. **There are seven** — `DESIGN-008`, `009`, `010`, `011`,
`012`, `013`, `014` — and **nine documents corpus-wide** carry an old-form
`Linked OKR`. Measured 2026-09-08 and verified independently. The Context
sentence is left as written, because it is a dated claim inside a
quotation-bearing clause and this entry is where the correction belongs.

**Also recorded, from the same round**: the corpus is **30 live references, 14
historical quotations and 6 mentions of the grammar itself**. The middle class
is the one with no automated guard — `reference/style.md`'s `[[old-form]]`
markers are the mechanism, and they cannot be applied until the old form is
actually obsolete, which is the same edit as the rename. Until then a wrongly
rewritten quotation is caught by a person reading the diff and by nothing else.

## What would reopen this

- The rename turns out to break a consumer nobody enumerated — aiMark reads
  these ids through `perry-goals list`, and a contract change there is a
  separate decision.
- `TASK-264`'s KR writer lands and makes the ids tool-managed, at which point
  their spelling stops being a document-level concern.
