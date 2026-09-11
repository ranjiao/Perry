# TASK-412 — spec

> Design: `DESIGN-016` § 1, the contract page it publishes
> Dispatch mode: auto
> Executor: claude-subagent — documentation and one test module
> Estimated cycle: small
> Subjective verification: whether a snippet on a page consumers copy should be
> executed by a test, or replaced by something that cannot be copied wrong
> Touches architecture: (none)
> Deployed: no

- **Owner**: Coding Agent · **Priority**: P2 · **Track / mode**: main / project
- **Dependencies**: —
- **KR linkage**: declared unlinked
- **Verification rung**: V4

## Why

`schema/task-list-contract.md` is the page a consumer of `perry-task list`
reads to decide whether the payload it got is one it understands. Its rule-3
snippet — the one that tells a consumer which changelog entries apply to them —
carries two defects, and **nothing executes it.**

Measured by V4 round 4, and still true at `fe0292fb`:

1. `:586` — `change["version"] > TESTED_MINOR_STR` is a **string** compare, so
   `"1.5" > "1.18"` is true and a consumer pinned at 1.18 is warned about an
   **older** change while newer ones pass. The same page's own
   `semantics[].version` row warns against exactly this: never as a float, and
   a string compare works only against a same-shaped string.
2. `:584` — `if (major, minor) > max(SUPPORTED)` with `SUPPORTED = {(1,18),(2,0)}`
   makes any 1.x minor drift unreportable, because `(1,19) > (2,0)` is false.

**Why this is a row and not a FAIL.** Both are latent. The tool ships 2.0, so
no consumer is misled today, and the page's *other* snippet — the rule-1 version
gate — the reviewer did execute, against a live payload: it accepts 2.0, accepts
1.18, rejects 3.0. The page is half-verified and this is the unverified half.

**The related fix that shows the shape is real**: the changelog guard on the
same page was wrong until `2ba2c565` — `range(minor+1)` demanded twenty headings
at 1.19 and one at 2.0 — and round 4 confirmed its no-gaps-per-major replacement
with four independent mutations, all red. A snippet on this page has already
been wrong once and been caught only by someone running it.

## Files in scope

- `schema/task-list-contract.md` — the two snippets and anything else on the
  page that a consumer is invited to copy.
- `bin/perry-task` — read, for what the payload actually carries. Change only if
  the page is found to describe something the tool does not do, which would be a
  different and larger finding; say so rather than quietly fixing either side.
- `tests/` — the module that executes the page's snippets, existing or new.
- `perry/evidence/2026-09/TASK-412-result.md` — written.

## Bound

```
Commit:      fe0292fb
Enumeration: every executable snippet on schema/task-list-contract.md. DERIVE
             the set from the page's fenced blocks rather than working from the
             two this spec names — the row exists because one snippet was
             executed and another was not, and a fix that covers exactly the
             two named here reproduces that asymmetry one page later
Size:        state the number your sweep returns, and how many are executed by
             a test today
Last element: the last fenced block on the page
```

## Deliverable

Both defects fixed, and **every executable snippet on the page executed by a
test** so the next one cannot ship wrong.

The version comparison is the substance: a comparison that is correct for
`1.5` against `1.18`, for `1.19` against `2.0`, and for every pair in the
enumerated version space, not for the pairs that happen to exist today.

`perry/evidence/2026-09/TASK-412-result.md`: the sweep, the two fixes with a
before-and-after table of the comparisons that change, and the mutations.

## What it must not do

1. **It must not make the snippet correct only for today's versions.** `2.0`
   ships now; the defect is about the versions that do not exist yet, which is
   why it was invisible.
2. **It must not change the payload or the tool's version.**
3. **It must not delete a snippet to avoid testing it**, unless it argues that
   a consumer should not be copying code from this page at all — which is a
   defensible position and, if taken, must replace the snippet with something
   better rather than with nothing.
4. **It must not leave a snippet on the page that no test runs.**

## Verification

1. **The reported wrong answers, reproduced and then gone.** `"1.5" > "1.18"`
   and `(1,19) > (2,0)`, printed before and after.
2. **Enumerated, not sampled.** Build the version space the page's own
   `SUPPORTED` and changelog define, and check every pair. A test over three
   hand-picked versions is how this shipped.
3. **Every snippet on the page executes and exits 0** against a live payload,
   or is marked non-executable in a way the test reads — the same rule
   criterion 11 applies to `bin/README.md`.
4. **Mutation, and the bar is the changelog guard's.** That fix took four
   independent mutations, all red. Restore each defect separately and show a
   named test go red for each; then mutate the fix in a third way you choose
   and say whether it reddened.
5. **A control**: show the rule-1 gate still accepts 2.0 and 1.18 and rejects
   3.0, so the fix did not move the half that was already right.

## Out of scope

- `perry-task list`'s payload, bound or contract version.
- The changelog guard, fixed at `2ba2c565`.
- Other pages under `schema/`, unless the sweep shows this page's snippets
  come from one.
