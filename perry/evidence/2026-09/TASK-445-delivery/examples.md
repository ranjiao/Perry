# Quoted synthetic fixture exhibit

The identifiers in this quoted exhibit belong to its synthetic fixture, not this project. The exact original Markdown is preserved in `../phase004-synthetic-exhibit-originals.json` (keys are evidence-relative paths).

> # Four bounded scenarios
>
> Synthetic reviewer fixtures only. USER-101/102/103 are hypothetical returned IDs, not project records. No ask/answer command was executed; no store was created. examples.md is this file.
>
> <a id="save-location"></a>
> ## New pending choice
> Measured visible card: 221 Unicode code points.
> ```text
> USER-101 — Save location · pending
> For you: local files work offline; shared storage lets teammates read them.
> Recommend: local for solo work. Options: local/offline; shared/team access.
> Details: examples.md#save-location
> ```
> PMO asks using the existing writer, receives USER-101, presents the card, and waits. No answer and no dependent action.
>
> <a id="export-format"></a>
> ## Immediately answered choice
> Measured visible card: 228 Unicode code points.
> ```text
> USER-102 — Export format · answered
> For you: CSV opens in your spreadsheet; JSON keeps nested fields.
> Recommend: CSV for your sheet. Options: CSV/table; JSON/structured data.
> Answer: “Use CSV.”
> Details: examples.md#export-format
> ```
> Conversation: user says “Use CSV.” PMO creates the ask, receives USER-102, records that exact answer with answer, then implements CSV. No repeat question.
>
> <a id="offline-scope"></a>
> ## Prior authority for a spec amendment
> Measured visible card: 274 Unicode code points.
> ```text
> USER-103 — Offline export scope · prior authority
> For you: the spec now states exports work without a network.
> Recorded answer: “Include offline CSV export.” Recommend: apply that requirement; keeping network-only export conflicts with it.
> Details: examples.md#offline-scope
> ```
> Prior USER-103 answer explicitly says “Include offline CSV export.” Amendment adds offline CSV acceptance and cites USER-103; implementing commit cites USER-103. No new permission or wider format support is inferred.
>
> <a id="preview-spacing"></a>
> ## Agent-decided reversible action
> Measured visible card: 244 Unicode code points.
> ```text
> Agent-decided — Preview spacing
> For you: more rows fit on screen.
> Recommend/selected: compact spacing. Alternative: roomy spacing for easier reading.
> Revisit: restore roomy spacing if reading becomes harder.
> Details: examples.md#preview-spacing
> ```
> Agent chooses compact preview spacing under existing reversible autonomy, logs agent-decided and the restore trigger. No USER answer is created for this selection.
