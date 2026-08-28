# Mode · `inquiry` — the question is answered, and the work ends

> Loaded by the router for any track whose `Mode` is `inquiry`.
> DESIGN-003 § 5.1, § 5.4. Covers research and intelligence (6.4% of observed
> agentic work), data analysis and BI (5.8%), meeting intelligence (1.8%) and
> education prep (2.4%).

Carries rules rather than references.

## The mode contract

Every row names where its data lives, because two prior reviews of the sibling
mode files failed on exactly one defect: *a control described in prose whose
data has nowhere to live.* Nothing below is a control unless it has a column.

| Slot | Value | Where it is written |
|---|---|---|
| **Ends when** | The question is answered — or abandoned, which is a real answer | — |
| **Unit that gets an ID** | The question | `BOARD.md` row |
| **Question tree** | The question this one was split out of; blank = a root question | `BOARD.md` → `Parent` |
| **Spine** | The open root questions | `BOARD.md`, rows with an empty `Parent` |
| **Horizon** | The root question. Closes when it is answered or abandoned | — |
| **Calendar** | **Advisory.** A question is not late; it is open or it is not | — |
| **Item states** | `Status` (global enum) and `Stage` — default `open → researching → answered` | `BOARD.md` → `Status`, `Stage` |
| **Question clock** | How long it has sat in its current stage | `BOARD.md` → `Stage since` |
| **WIP control** | A cap on open questions, `open:n` | `.perry/config.md § Tracks` → `WIP` |
| **The answer** | One file per answered question | `evidence/<YYYY-MM>/<ID>-answer.md` |
| **Sources** | One digest per source: `Id: SRC-<n>`, `Source:` (origin), `Received:` (fetch date) | `knowledge/<topic>/*.md` |
| **Claim → source** | `[SRC-n]` inline in the answer | checked by `perry-lint --provenance` |
| **Default rung** | **V4** — fresh-context review — **plus** clean provenance | `BOARD.md` → `Verification` |
| **Signature failure** | Re-deriving the same synthesis every session, because nothing was written back | — |

## Provenance is this mode's test suite

Software has a test suite. A pipeline has a human who signs. An inquiry has
neither, and the substitute is not "be careful" — it is that **every claim names
the source it came from, and the source can be re-opened**.

That is why `V4` alone is not the bar here. A fresh-context reviewer can tell
you an argument is coherent; it cannot tell you the number is real. So an
inquiry-mode close needs both:

1. **A fresh-context reviewer** against written acceptance criteria (V4's own
   requirement — the reviewer must not have seen the reasoning that produced the
   answer).
2. **`perry-lint --provenance` clean** for the answer file: every `SRC-n` it
   cites resolves to a digest under `knowledge/`, and every digest cited carries
   a `Source:` (its origin) and a `Received:` (its fetch date) — those are the
   field names, not paraphrases of them.

The second is a script, so it is cheap and it does not get tired. It checks five
things and none of them is a matter of judgment: an id that resolves to nothing
(`citation-dangling`), a digest with no id (`source-has-no-id`), an id that is
not of the form `SRC-<n>` (`source-id-malformed`), a digest missing `Source:` or
`Received:` (`source-missing-field`), and an id defined twice
(`source-id-reused`). That last one matters more than it looks — **ids are minted once and
never reused**, because a finding written a year ago that cites `[SRC-n]` has to
still resolve to the same source. An id that gets recycled does not dangle; it
silently re-points, which is worse.

**What provenance does not check.** That the source says what the claim says it
says. That the source is any good. That the sample was representative. Those are
the reviewer's job and the user's, and no lint will ever take them over — the
check establishes that a claim is *traceable*, not that it is *true*.

## Questions are a tree, and the tree is a column

Research does not proceed as a list. A question splits into sub-questions, those
split again, and the value of the whole thing is knowing which branch is still
open. `BOARD.md` has no nesting, so the edge is a cell: `Parent` carries the ID
of the question this row was split out of, and a blank `Parent` marks a root.

```markdown
| ID | Title | Owner | Status | Next action | Evidence | Track | Stage | Parent | Verification |
|---|---|---|---|---|---|---|---|---|---|
| Q-1 | Does batching cut cost? | Research Agent | in_progress | — | — | study | researching | — | V4 |
| Q-2 | What is the current per-call cost? | Research Agent | done | — | `evidence/2026-08/Q-2-answer.md` | study | answered | Q-1 | V4 |
```

Two rules:

1. **A parent cannot close before its children.** An answered root question with
   an open child means either the child was not load-bearing — in which case
   drop it and say why — or the answer is premature.
2. **Abandoning is answering.** A question dropped for a stated reason is
   closed, and the reason goes in the journal like any other drop. What must not
   happen is a question quietly falling off the board: the whole point of the
   tree is that it records what was asked, including what turned out not to
   matter.

## The answer is a file, not a conversation

**The mode's signature failure is re-deriving the same synthesis every
session**, and it has one cause: the answer lived in chat. So closing a question
requires `evidence/<YYYY-MM>/<ID>-answer.md`, and that file is the deliverable —
not a summary of one.

Minimum shape: the question restated, the answer, the claims with their
`[SRC-n]` citations, and what would change the answer. That last line is what
makes an answer re-checkable a year later instead of merely re-readable.

## WIP: cap the open questions

A research track fails by breadth, not by depth. Ten open questions is not ten
times the progress of one; it is one context split ten ways, and the tell is
that every session re-reads the same sources to re-establish where it was.

So `WIP` here is `open:n` — a cap on rows not at `Stage: answered`. **Default:
`open:5`.** When the cap is reached, nothing new opens until something closes or
is abandoned. A branch that cannot be closed and cannot be abandoned is the
finding, not an exception to the cap.

## Triage in this mode

1. **Open questions against the cap.** Over it, name what to close or abandon.
2. **Questions by stage age** (`today − Stage since`). A question in
   `researching` far longer than its siblings is usually two questions.
3. **Unsourced claims** — run `perry-lint --provenance`. A dangling `SRC-n` in
   an answer file is a claim whose evidence has gone missing, and it outranks
   everything else in this list.
4. **Roots with all children closed** — those are ready to answer, and they are
   the easiest thing to miss.
5. **Stale digests.** A source cited by an active answer whose file has not been
   re-read since the answer was written is a soft finding, not a hard one.

## What this mode does not assume

- **That the answer is what was asked for.** Inquiry tracks feed decisions.
  When the answer changes what should be built, that is a `decide` lane
  document, not a bigger answer file.
- **That the calendar matters.** It does not: a question is open or answered,
  and a deadline on a question produces a confident answer rather than a correct
  one. This is the one mode besides `project` where the calendar stays advisory.
- **That Perry fetches anything.** Sources arrive through `inputs/` and become
  digests through `/perry work digest`. This mode reads them and never goes and
  gets them.

## See also

- `perry/design/DESIGN-003-work-modes.md § 5.1`, `§ 5.4` — the mode table and
  the provenance contract.
- `work/reference/digests.md` — how a source becomes a digest, and the `Id:`
  minting rule.
- `reference/project-archetypes.md § Archetype B` — the knowledge-base archetype this
  mode generalizes, including the link-integrity and no-orphan checks it names.
