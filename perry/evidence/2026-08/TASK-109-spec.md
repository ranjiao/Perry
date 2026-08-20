# TASK-109 — A V5 sign-off is selected from measured facts, not authored from memory

> Source: raised by the user 2026-08-20, immediately after signing TASK-047 — "像是银行签约一样"
> Dispatch mode: auto
> Executor: claude-subagent (repository-local: one subcommand's flags, one lane procedure, and the tests that pin both)
> Estimated cycle: medium
> Subjective verification: whether `accepted on report` is the right second category, or whether a third — "not looked at" — is worth distinguishing from it
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## The problem, stated precisely

`V5 needs a signature` is right and the frequency is not the issue: **3 of 80
closed rows carry V5, 4%**. The cost is not how often it fires; it is what it
asks for when it does.

Today the user is asked to compose, from memory, prose describing checks that
**Perry itself ran and printed minutes earlier**. On TASK-047 those were: the
`claims[]` diff, the write behaviour under `enforce` / `advisory` / declared, and
the `perry-migrate` exemption. Perry had every one of them as a command and an
output. It then asked a human to re-derive them as a paragraph.

There is a second, quieter defect. The resulting sentence cannot express the
distinction that matters most: TASK-047's signature reads *实测了…三种情形*, and
what actually happened is that **Perry ran them and the user read the output**.
That is not the same as the user running them, and the format has no way to say
so. A record that flattens *I checked this* into *I accepted this* is weaker than
it looks, and it gets weaker the more Perry does.

## Deliverable

1. Closing a row at V5 offers **one** selection prompt, built from what Perry
   measured during this task: the objective-verification commands it ran, the
   scope cross-check, and any subjective-verification items the spec declared.
2. **Every offered item is labelled with its provenance** — whether Perry
   verified it independently, or is merely restating a claim. Selecting an item
   Perry verified means *I checked this too*; it must not read as *I accept
   Perry's word*, and the label is what keeps those apart.
3. **Name and date are filled automatically.** They are the two fields a human
   should never be typing.
4. **Unselected items are recorded, not dropped** — as `accepted on report`.
   This is strictly more information than today's free-text paragraph, which
   cannot distinguish the two at all.
5. **Free text stays**, for anything the user checked that Perry does not know
   about. It is additive, never a replacement for the selection.
6. **Perry never drafts a claim about what the user did.** It may offer
   `claims[] has zero lines in the diff` — a fact it measured. It may not offer
   `the user reviewed the diff`. This is the line that keeps the mechanism from
   becoming self-certification, and it is the same line `ADR-004` draws with
   *adoption proposes; the user declares*.
7. A V5 close with **nothing selected and no free text** is refused, not written
   blank. An empty signature is the failure the rung exists to prevent, and it
   must not be reachable by pressing return.

## Verification — V5

Rung reasoning, because it is worth arguing with: this row builds the mechanism
that records every future V5 signature, in every project Perry ships to. If it
is subtly wrong — an item labelled verified that was not, a selection silently
widened — then every signature written afterwards is compromised and nothing
downstream can tell. That is a larger blast radius than the V4 default covers.
The recursion is real and intended: this row's own close will be signed through
the mechanism it replaces.

1. Fixture close offering three Perry-measured items and one restated claim.
   Select two. Assert the written record names the two as **checked**, the other
   two as **accepted on report**, and that the labels survive verbatim.
2. Fixture where the user adds free text Perry did not offer. Assert it is
   recorded alongside, not instead of, the selection.
3. Assert **no drafted option asserts a user action** — a mechanical test over
   the option builder, not a review comment.
4. Assert a V5 close with an empty selection and empty free text is **refused**.
5. Assert the three V5 signatures already in this repository still read
   correctly; the change adds a path, it does not rewrite history.
6. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`.

## Files in scope

- `bin/perry-task` — the `done` subcommand's flags and the record it writes
- `work/reference/subcommands.md § close-task` — the procedure that calls it
- focused task-writer and close tests

## Out of scope

- The rungs themselves, what they mean, or which rung a row gets. Only how a V5
  signature is composed changes.
- V1–V4 closes. They gain nothing and must be byte-identical.
- Rewriting any signature already recorded.
- `schema/state-schema.json`, `claims`, and which paths Perry claims.
- `bin/perry-decide`, `bin/perry-diagnose`, `bin/perry-lint`, `bin/perry-migrate`
  — each is carried by an open unmerged branch or a live dispatch.
- Closing without the V5 evidence above.

## Changes

- 2026-08-20 — Note on the escalation scan, which returned `pass` with a match.
  The fragment `claims` appears in `Deliverable` because that section **quotes an
  example** — `claims[] has zero lines in the diff` is offered as a specimen of a
  fact Perry may draft. The row does not touch the claim surface, and
  `Out of scope` says so. This is a third shape of scan result, distinct from the
  two seen earlier today: TASK-079 and TASK-086 were substring artifacts inside
  longer words (fixed by TASK-107); TASK-047 and TASK-085 were true matches
  green-lit by the spec author's own disclaimer; this one is a true negative that
  matched a quotation. Recorded because the first two shapes each cost a round
  trip to the user, and a scanner that reads prose will keep producing new ones.
