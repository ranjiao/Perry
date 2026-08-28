# TASK-056 — the claim stated in three places, implemented in a fourth

> Rung: **V3**. Every claim below is a run or a mutation.

## What the claim was, and where it actually lived

`modes/pipeline.md § The mode contract`, `modes/queue.md § The mode contract` and
`schema/state-schema.json` all say the same thing: a track missing a no-default
column cannot run the triage step that reads it, and **triage reports that**
rather than skipping it.

Round 6 found it *"stated in three places and implemented nowhere"*. By the time
this was picked up that had changed, and the V4 re-review named the change
precisely: **`perry-lint` implements it, at file level.** So the rule had moved
from *implemented nowhere* to *implemented somewhere other than all three
documents say* — which is the same defect wearing a better disguise, because now
the documents look satisfied.

**Triage had nothing to read.** It is an agent procedure and the procedure
forbids eyeballing the board, so without a payload field it could not obey the
rule its own mode file states.

## The fix makes the three sentences true rather than weakening them

The alternative was to reword all three to say *"`perry-lint` reports it"*.
Rejected: the linter runs on files, triage runs on a decision, and the sentence
they wrote is the one a user needs — the step is blocked *now*, in front of
them, not in a lint run they may not do.

- `perry-state --json` → `project.config.tracks[].missing_defaults` names the
  no-default columns each track left blank.
- It is computed from `work_modes.modes.<mode>.no_default` — **the same source
  `perry-lint` reads**, never copied, so the two cannot name different tracks.
  A test asserts they name the same set.
- `work/reference/subcommands.md § triage` reads it before the per-mode walk and
  says the blocked step out loud.

Verified on a three-track register: `ops` (queue, no SLA, no Cycle) →
`["SLA", "Cycle"]`; `rel` (pipeline, both declared) → `[]`; `main` (project) →
`[]`, because `project` and `inquiry` declare an empty `no_default` and
reporting there would be Perry inventing a requirement the mode does not have.

## Mutations

6 written, 6 red — including two on the **schema**: dropping `SLA` from queue's
no-default set, and giving `project` mode one it does not have. Those two are
the ones that prove the rule is read rather than transcribed.

`test_the_documents_that_make_the_claim_still_make_it` asserts the three
sentences survive, so a future edit cannot satisfy this row by deleting the
claim instead of implementing it.

## What is left on TASK-019

This closes one of that row's three findings. The other two are untouched and
named on it: `perry-state` and `perry-task` still disagree about a track's
stages when the `Stages` cell is blank (`stages_of` has a mode-default fallback,
`parse_tracks` has none), and `grep -i wip bin/perry-task` still returns nothing.
