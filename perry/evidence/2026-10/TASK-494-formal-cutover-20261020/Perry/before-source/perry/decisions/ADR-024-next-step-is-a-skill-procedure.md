# ADR-024 — The next-step recommendation is a skill procedure, not a kernel rule table

> Status: active
> Type: Design
> Date: 2026-09-24
> Deciders: Ran Jiao
> Supersedes: ADR-023   · Superseded by: —
> Sunset: —

## Context

`perry/design/DESIGN-020-guided-planning.md § 9` records a user decision from
2026-09-15: the same state gives the same recommendation. ADR-023 built on it.
`perry-state --section next` evaluates `reference/next-rules.json` over the
payload it computes, and every lane subcommand is either recommended by some
rule or listed as never recommended.

`perry/design/DESIGN-023-a-kernel-and-a-skill.md` splits Perry into a kernel
that knows no methodology term (its Goal 1) and a skill that carries the method.
The rule table's terms are method: lane subcommands, phases, KRs, weekly
reviews. Its decision 5 asks which half recommends the next step.

## Options

1. **The skill decides from kernel queries.** The agent runs a fixed set of
   kernel queries and walks a table written in the skill's prose.
   - For: the kernel stays free of method, as Goal 1 requires.
   - Against: determinism moves from code to procedure. ADR-023's rejected
     Option 3 already recorded that two agents reading the same state can
     recommend different things.
2. **The kernel evaluates a rule table written only over kernel queries** —
   counts of items by type and state.
   - For: keeps DESIGN-020 § 9.
   - Against: needs a rule evaluator in the kernel, and limits rules to counts.
3. **Keep `perry-state` as it is.** Contradicts DESIGN-023 Goal 7, which
   deletes it.

## Chosen

**Option 1.** The user chose it on 2026-09-24 (DESIGN-023 § 4, decision 5), in
the knowledge that it reverses the 2026-09-15 decision.

## Consequences

- **Until phase G of DESIGN-023**, `perry-state --section next` and
  `reference/next-rules.json` keep running unchanged. The table is frozen: no
  rule is added to code that phase G removes.
- **At phase G**, the skill's procedure names the exact queries it runs,
  evaluates its table top to bottom with the first match winning, and prints
  the facts it used. That is how disagreement between two agents is kept
  visible, even though it cannot be prevented.
- **ADR-023's coverage guard** — every lane subcommand either recommended or
  listed as never recommended — becomes a checklist in the skill. Phase G
  decides whether a repository test keeps it.
- DESIGN-022's `R-kr-due` rule and the facts DESIGN-020 reads from documents
  (handoff age, latest weekly, retro recorded) move with it. Phase G gives each
  one a kernel item or query, so no number in a recommendation is counted by
  eye.
- DESIGN-020 carries a `## Changes` entry that points here.

## What would reopen this

After phase G, the user sees two sessions recommend different next steps for
the same state and finds that costly. Option 2 is then the fallback, within the
same Goal 1 limit.
