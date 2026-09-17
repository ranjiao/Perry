# Independent bounded semantic walkthroughs

Reviewer-authored fixtures, not project history. `<USER-ID>` is a placeholder for the actual ID returned by the existing ask writer; it is never a minted record. No live or copied PMO writes occurred. Exact visible strings are in cards.json; count includes all newlines, spaces and pointer characters. The following are reviewer judgments, not Python classifications.

<a id="pending"></a>
## 1. New pending choice — PASS

Source facts: user requests an export, delivery method undecided; downloadable exports remain local while emailing sends the file outside the app. Neither option has been chosen. Existing open decisions in this synthetic scenario: three.

Procedure walk: PMO records the pending ask through `perry-task ask --actor <actor> --needed <question>`, retaining its returned ID. A dependent task uses the documented `--blocks` and `depends --on` edges. Because three decisions are already presented, queue this fourth card explicitly; do not present it until a slot opens. When shown, substitute the actual ID and remeasure the final string. No answer or email action follows silence. The 254-character placeholder rendering states the practical distinction and recommendation without attributing a selection to the user. Details remain here one level down; the recommendation is not permission to email.

<a id="immediate"></a>
## 2. Immediately answered choice — PASS

Source facts: user says exactly “Export only name and total.” This refers to an already requested CSV report; no record exists yet. Extra columns are excluded, not an implicit option approved by the user.

Procedure walk: PMO ask creates the actual ID; PMO answer records the quoted answer under that returned ID; only then implement the two-column report. An executor missing this record waits for PMO. Do not re-ask the question to complete paperwork. The 252-character rendering separately labels the recommendation and actual answer. Its two-column consequence follows the utterance and it does not turn the all-column alternative into authority.

Semantic mutation: same utterance and same two-column implementation, delete ask and answer and act immediately. REJECT under acceptance 2 and user-load.md:113-122: explicit authorization permits recording immediately; it does not waive recording-before-action. Restored trace ask → returned ID → answer → action: ACCEPT. This is independent fresh reviewer judgment; no tool was claimed to refuse natural language.

Additional input checks within this authority case: “maybe,” an unread report, and elapsed waiting provide no explicit answer and cannot discharge the dependent action. A clear later answer permits answer-writing; receiving the report alone does not.

<a id="reuse"></a>
## 3. Reuse for a spec amendment — PASS

Source facts: a hypothetical existing answered record, returned as `<USER-ID>`, says “Add offline CSV export; keep JSON out of scope.” The current criterion omitted offline support. This authority is stipulated as fixture input, not asserted to exist in the real project.

Procedure walk: read that answer and its scope, amend only the CSV offline requirement; cite the actual returned ID in the amendment and implementing commit. No ask or second answer needed. The 267-character rendering accurately preserves JSON's exclusion and states what changes for the user. Attempting to add JSON under the same ID is REJECTED: the source explicitly excludes it. A citation without matching scope cannot authorize it. A review finding about JSON is also not a user decision.

<a id="agent"></a>
## 4. Reversible agent action — PASS

Source facts: an authorized preview already exists; row height is reversible, no accessibility requirement mandates a particular height, and no external action or high-stakes gate is involved. Agent selects compact spacing to show more rows.

Procedure walk: record the selection in the project's decision log through its owning lane, visibly agent-decided, with the reason and restore trigger; do not create an answer alleging the user selected compact spacing. The 269-character rendering names its agent author and gives both benefit and revisit condition. If the user instead explicitly delegates selection, record that delegation first, while retaining agent attribution for the selection. If a named human sign-off or high-stakes gate applies, this autonomy route does not discharge it.

## Author fixtures independently inspected

Read examples.md, cards.json, semantic-mutation.md and result.md under /tmp/perry-scratch/task-445/phase004. Remeasured counts 221/228/274/244 exactly agree. Save-location remains pending; “Use CSV.” precedes recording and implementation; offline CSV authority covers the stated amendment; preview spacing is agent-decided. All four visible cards faithfully represent the fixture facts supplied. These fixtures and their synthetic concrete IDs are not real authority. Their author's verdict was not used as the review verdict.

## Numeric and reverting-fix mutations

Independent cards and author cards all fit the cap. card-600.txt is exactly 600 Unicode code points and passes the numeric boundary. card-601.txt adds one emoji code point and is rejected by the <=600 measurement. Padding is only a length probe, not an endorsed user card. card-restored.txt restores the original 254-character card without truncating evidence. Measurements are in measurements.json.

Reverting-fix mutation replaced precisely the three changed pages with their immutable base blobs; mutation.diff records all removals. Independently reading that mutant: it still has generic autonomy and ask/answer commands, but no card size constraint, no immediately-answered ordering, and no spec/commit USER citation requirement. Thus the mutant fails acceptance 1 and 2. It provides no instruction to reject the 601-character card, nor the unrecorded immediate action on those grounds. This is a semantic regression detected by the reviewer; existing lexical tests are not a semantic guard. Mutation tier output is retained separately without upgrading its result into evidence about meaning. Restoration is verified against fresh git show head blobs, not harness snapshots. After restoration, the four traces and length boundary again satisfy the restored procedure.
