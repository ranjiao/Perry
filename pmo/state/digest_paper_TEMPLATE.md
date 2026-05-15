# Digest — <paper / report title>

> Source: knowledge/<topic>/<source-filename>
> Source SHA-256: <hash>
> Received: <YYYY-MM-DD> by <user paste | file drop>
> Last digested: <YYYY-MM-DD> by PMO
> Status: active
> Superseded by: —
> Topics: <comma-separated>
> Verification level: standard
> Doc type: research-style                        # auto-detected; do not edit
> Authors / affiliation: <comma list, or '(unknown)'>
> Published / dated: <YYYY-MM-DD or '(unknown)'>
> Source venue: <arXiv:NNNN.NNNNN | journal | conf | company report | …>
> Referenced by: (auto-grep on INDEX rebuild)

## TL;DR (≤ 3 sentences)

<the paper's core claim, in the user's plain language — not the paper's abstract verbatim>

## Method

<how they did it: sample size, setup, baseline, evaluation procedure, key tools / datasets used. Specific enough that the reader can judge whether the method is sound and transferable.>

- **Sample / dataset**: <what data, how much, how collected>
- **Setup**: <experimental conditions, hyperparameters of note>
- **Baseline**: <what they compared against>
- **Evaluation**: <metric + protocol>

## Key results (with context)

Each result = number + the context that makes it meaningful (not the paper's claim as-is).

- **<result label>**: <metric> <value>, vs baseline <baseline-value>, on <dataset / cohort>. (§<source location>)
- ...

## Limitations

Both author-acknowledged AND critical-reading limitations the digest writer observed.

- **Author-acknowledged**: <what they said about scope / caveats>
- **Reader-observed**: <what feels under-discussed: sample bias / generalizability / overfit risk / unstated assumption>

## Reproducibility

- **Data available?**: <yes / partial / no — link if yes>
- **Code available?**: <yes / partial / no — link if yes>
- **Method described clearly enough to re-implement?**: <yes / mostly / no — note specific gaps>
- **Barrier to using in this project**: <compute cost / data licensing / time / specialised expertise / …>

## Applicable to this project?

Concrete judgment, not aspirational.

- **Verdict**: use / partially use / don't use
- **Reason**: <one paragraph>
- **If "use"**: where in the project this lands (file path / phase / task-id)
- **If "partially use"**: which part transfers, which doesn't

## Followup citations (2–3 max)

References from this paper that look worth reading next. NOT a dump of the references list — only the 2-3 highest-leverage ones, with the reason each is worth pulling.

- <Author Year>: <one line on why this is the next read>
- <Author Year>: <one line>

## Open questions

- <what PMO doesn't yet know but should track or surface to user>
- ...

## What PMO must remember in future work

- <when topic X comes up, must reference Y>
- <if asked about Z, the source's position is W>
- ...
