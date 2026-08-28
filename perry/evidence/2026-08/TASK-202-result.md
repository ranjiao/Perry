# TASK-202 — the hook half of the check, and a fixture that believed it was armed

**From `coding/task-202` @ `bbe7781`.** Rung **V3**. `perry/` unmodified.

## Where it surfaces, and why that is the whole point

`bin/perry-lint § check_cross_file`, **on the default pass, no flag.** The role
card's equivalent lives in `check_role_cards`, which only runs under
`--knowledge` — *"defensible for an optional file a reader goes looking for, and
wrong for the hook, which is read on every dispatch of every project."*

It also lands as a standup warning in `bin/perry-state` and as
`hook.high_stakes_unextractable` in the payload, **so a delegation prompt can
mark a line unenforced instead of rendering it as a constraint.** That is the
consequence I had not thought about: an unenforceable rule was being shown to a
dispatched agent as though it bound them.

## Severity: `warn`, equal to the card's, deliberately

The hook's case is worse in consequence — no card to compensate, and TASK-200
caught `max_position` on a card standing in for exactly this hook. It still
argued for equal volume:

> an `error` would say a rule's enforceability depends on **which file it was
> written in**, which is the asymmetry being removed

and would turn every existing project's honest prose into a red `--strict` exit
on an unchanged run. **The difference belongs in reach — no flag — not in
volume.** I think that is right.

## Four places my spec was wrong

**1 · The card half had two reporters, not one.** `bin/perry-state:1573` also
warned in the standup, and **its copy still said the line "has no backticked
span"** — the exact wording TASK-201 falsified while fixing `perry-lint`'s copy.
Verified: `bin/perry-lint:1681` now reads *"Backticks are not the test; the
extractor is"*, and `bin/perry-state:1583` still said the old thing.

**That is my chain, not the agent's**: TASK-201's spec listed
`viewer/parsers.py`, `schema/state-schema.json` and `tests/` as files in scope
and never mentioned `bin/perry-state`, so TASK-201 fixed one of two copies and I
merged it without noticing.

**2 · `perry-lint` kept its own hook-section reader.** `bin/perry-lint:1296`
uses `heading_re("High-stakes operations")`, which lacks the `## High-stakes`
prefix tolerance `P._section` has — so a hook headed that way was **armed for
the gate and unarmed for the linter**, which `heading_re`'s own docstring
forbids. Left alone it would have printed *"no high-stakes list"* and then three
of that list's dead bullets. Both tools read `P.hook_escalation_lines` now.

**3 · Files in scope were short two** — `bin/perry-state` and
`schema/state-schema.json § cross_file`.

**4 · This repository's own fixture had the defect, and its comment claimed the
opposite.** `tests/test_conformance.py:118`:

> `# Armed, so the fixture carries no lint finding of its own and a test that`
> `# measures "did being undeclared add a finding" is measuring that and not`
> `# the hook warning every bare project starts with.`

and the bullet it writes is `- anything that spends money`. Measured:

```
line_fragments("- anything that spends money")  →  []
```

**Zero fragments. No backticks.** The old check asked *"has a backtick"* and let
it pass; the fixture believed it was armed and armed nothing — **and a different
test's measurability was resting on that belief.** The new check found it on its
first run and turned `--strict` red. Fixed by backticking the fragments.
`tests/test_migrate.py:155` carries the same line, is green, and was correctly
left alone.

## Unification, with a distinction I had not drawn

One predicate (`unextractable_lines`) and one sentence (`unextractable_says`).
`escalation_fragments`' docstring argues the two sides must *extract* the same
way; the same argument carries to *reporting*. But:

> **the asymmetry was never in the extractor** — `line_fragments` was already
> shared. It was in who called it. **A shared extractor with one caller is how a
> check covers half of what it describes.**

## Numbers

Fixture shaped like `gimegime-pmo`'s hook, 5 bullets → 3 fragments:

| | default lint | `--knowledge` | standup | payload |
|---|---|---|---|---|
| **before** | 0 | 0 | 0 | only `armed: true` |
| **after** | **3** | 0 | **3** | 3 dead bullets listed |

Perry itself **unchanged**: 0 errors, 3 warnings, 197 records 0 drifted, risks
4/0. 8 bullets, 35 fragments, **0 dead** — the latent case the spec predicted.

A hook-less project: **zero findings, not N**, asserted directly, plus the
empty-section spelling.

**Mutation: 12 written, 12 killed, 0 survived** — including "the two halves
judging one line differently", which is the defect this row exists to remove.

Suite **89 modules · 2697 tests · one red** (`test_diagnose`). Two existing
tests changed, both documented in place; the second (`test_i18n_one_table`) was
a source-proxy assertion that broke because a call moved into parsers, and its
behavioural guard still passes on the Chinese `## 高风险操作` fixture.
