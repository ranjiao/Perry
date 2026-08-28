# TASK-114 — aiMark reads Perry through the current contracts instead of an anchor five minors back

**Done 2026-08-21.** Rung **V3**, not the V4 the row carried — see *On the rung*.
The work is in `/Users/bytedance/proj/aimark`, driven by
`evidence/2026-08/TASK-114-delegation-prompt-v2.md` via USER-015.

## Verified independently

Not taken from the agent's report.

```
src/perry-cli.ts:72   task: "1.14"
src/perry-cli.ts:73   goals: "2.1"
```

**Acceptance 5 — the anchor is in exactly one non-test place.** `grep -rn '"1.14"\|"2.1"' src/`
excluding tests returns those two lines and nothing else.

**Acceptance 8 — the suite.** `bun test` run here: **672 pass, 0 fail**, 1964
`expect()` calls, 38 files. The agent's baseline was 654 pass / 1 fail; the one
failure was `perry-conformance.test.ts:212` asserting `changed` is empty — its
own guard correctly reporting the anchor was five minors back. It is green
because the statement became true, not because the assertion moved.

**Finding 1's premise.** `schema/task-list-contract.md:206` defines
`depends_on_unknown` as `{id, unknown}`, and line 236 gives it a key-by-key
section. There is no `missing` key anywhere in the contract.

**Finding 2's premise.** `src/perry-adapter.ts` and `src/perry-linkage.ts` do
not exist. `src/perry-cli.ts:11` says so in as many words — *"that adapter is
gone"* — and `src/work-model.ts:5` describes both in the past tense.

The aiMark diff is **uncommitted** in that repo at the time of writing.

## What the meaning-changes cost, per version

Two of the five needed code; the agent's account of which, checked against the
changelog range:

| version | what it did there |
|---|---|
| 1.10 | two fallbacks were reading `status_text` to recover something `status` could not carry. Since 1.10 there is nothing to recover — both could only substitute `""` for `""` while reading as though they still rescued the raw cell. Removed at `work-model.ts:84` and `task-monitor.tsx:79`. Display unaffected. |
| 1.11 | `work-model.ts:455` built `detail` as `[next_action, evidence].join(" · ")` — **aiMark's guess wearing the author's voice, in the slot Perry deliberately refuses to synthesize.** Now reads `summary`, absent when unset. |
| 1.12 | `blocked_stale` carried to `WorkTask.blockedStale` and rendered twice, in accent rather than the amber of a live blocker. The `blocked` badge stays: showing only one of the two picks a winner Perry declined to pick. |
| 1.13 | `means` and `readings` rendered verbatim, not collapsed to a count — the collapse is what got the array read as lint hygiene on 2026-08-20. Both idle checks gated on `has_event_log`; when false the strip says the checks did not run rather than showing nothing. |
| 1.14 | `askIndex()` resolves a `blocked_by` id against the user-input queue **by membership, never by a `USER-` prefix test** — a `USER-` id the queue never minted is still unknown and still unsatisfied, which is the same predicate Perry uses. |

1.14 proved live against Perry's own board: `TASK-040 → USER-016` renders the
question text from the queue, with no `tasks[]` lookup.

## Four findings came back. All four check out.

### 1 — a real consumer bug, and nothing failed

`depends_on_unknown` entries are `{id, unknown}`. aiMark parsed `r.missing`, so
**every entry named the row and dropped the ids** — the only actionable part of
it. Found while reading 1.14, the minor that changes what lands in that array.

Nothing on either side failed. The contract said one thing, the consumer read
another, and the array is `[]` on Perry's own board today, so it would have
looked correct forever. **This is the class of gap the row existed for**, and it
is the answer to "was the catch-up worth doing".

### 2 — my own prompt carried a stale claim, and I said it was fine

v2's out-of-scope item 1 reads:

> *"Do not remove aiMark's markdown parsing. The OKR chain view parses `OKR.md`,
> `BOARD.md` and `phase/NNN-linkage.md` in process."*

**That code was already deleted.** Acceptance 6's *"proven by the file list"*
was written expecting a file the diff cannot contain.

Worth stating exactly how this happened. v1 was withdrawn because three of its
claims were false; I checked those three — the version numbers and the pin —
found them wrong, and then **copied v1's three out-of-scope items forward
saying they were "still right"**. I verified the numbers and not the prose.
That is the same defect as v1's, one layer down, committed by the person
diagnosing it.

### 3 — two instructions in v2 contradict each other

The goals-2.1 section says *"if aiMark draws any KR progress indicator, it is
drawing an assertion, and 2.1 is the first version that lets it say so."*
Acceptance 6 forbids touching the OKR chain view. **The KR meter is in the OKR
chain view.**

The agent honoured item 6 — keys parsed and carried,
`krs_with_stale_current` surfaced in the rail, per-KR meter unmarked. So **a
stale number still renders identically to a fresh one at the KR itself**, which
is the exact thing 2.1 exists to prevent. Someone has to say which instruction
wins; both are recorded as attention items in `AIMARK.md`.

### 4 — `conformance.missing_projection` was never announced by any version

Sharper than reported. It is not merely outside the 1.10–1.14 range:

```
$ (split the changelog by version, search each section)
NOT mentioned in ANY changelog entry
$ git log --reverse -S missing_projection -- schema/task-list-contract.md
2af97e4 feat(tasks): read canonical task store
```

It ships (`missing_projection` is in the live payload), it has a key-table row
at line 210, and **no version ever announced it**.

`tests/contract_key_parity.py` — the instrument KR-O2.4 is measured by — cannot
see this: it compares *documented* against *emitted*, and this key is both. A
key that arrives without a version bump is invisible to it by construction.

## On the rung

The row carried **V4**. No independent fresh-context review round was run on
the aiMark diff — one agent did the work and the PMO checked three of its eight
acceptance items plus the premises of two findings. That is V3. Lowered to
match what actually happened rather than left at a number the process did not
earn.
