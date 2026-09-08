# aiMark contract feedback, round 7 — digest and merge-time obligations

> **Source**: `/Users/bytedance/proj/aimark/doc/perry-contract-gaps-7.md`, 445 lines,
> measured by the aiMark team on `104873da`. aiMark at `8eb215b`.
> **Read by**: `work` lane, 2026-09-08, during the phase 003 mid-phase session.
> **Why this file exists**: two agents were already executing ADR-019 in isolated
> worktrees when this arrived, `SendMessage` is disabled in this session, and
> three of its facts change what the merge must check. This is the note that
> survives to merge time.

## The headline: their round-7 ask is obsoleted by work already in flight

§ 7 defers adopting `perry-task add --unlinked` and asks Perry for **one boolean
on `perry-goals/list`: whether a project's register is the store or the
document**. Their reasoning is sound on today's tree:

```
on tests/fixtures/sample-project, whose register is phase/002-linkage.md:
  add --kr P002-O1-KR1  →  ACCEPTED.  register_store: null, linkage_record: null
  add --unlinked        →  REFUSED:  "--unlinked needs `linkage.jsonl` and this
                                      project has none … Nothing was written."
```

`perry-goals list` reports `linkage: {present, phase, updated, error}` and
`present` is `true` on that fixture — because a phase *document* is a register.
So the predicate `--unlinked` is gated on is real and is published nowhere.

**ADR-019 dissolves the distinction rather than publishing it.** Once
`phase/<NNN>-linkage.md` stops existing, a register is always the store and the
boolean has no false case. Adding it would ship a field born obsolete.

**Do not build the boolean. Tell aiMark why**, and tell them what replaces it:
`--unlinked` becomes universally legal, which is the third picker option they
designed for in § 3 (*"serves no KR"* beside *"not stated"*).

## Merge-time obligations — three facts the agents never received

| # | Fact | What the merge must check |
|---|---|---|
| 1 | **aiMark parses neither linkage form.** *"It never parsed `phase/<NNN>-linkage.md` and it does not read `linkage.jsonl`."* Every occurrence in its source is a freshness `stat` or a cache key, never a read. `O4-KR1` is 0. | No consumer read path through the document needs preserving. This *lowers* the linkage agent's bar; confirm it did not preserve one defensively. |
| 2 | **`tests/fixtures/sample-project` uses the DOCUMENT form** — `phase/002-linkage.md`, no `linkage.jsonl` — and **aiMark's conformance suite runs against a copy of it**. | Whatever the agent did to that fixture reaches outside this repository. The merge must state explicitly whether a project holding only the document is migrated, refused, or left store-less. |
| 3 | **`--unlinked`'s refusal names a condition that can no longer be false.** | Reject a merge that leaves the message *"--unlinked needs `linkage.jsonl` and this project has none"* standing. |
| 4 | **`schema/README.md` tells external consumers to read the State root out of `.perry/config.md`** (`TASK-301`, open P1). `schema/` is a published consumer contract, not internal docs. | The config agent's doc sweep must have replaced it with something a consumer can actually reach — `viewer/parsers.py § resolve_state_root` is the reader. Highest-value 16 of its doc occurrences. |
| 5 | `bin/perry-config --help` names `perry-conform`, deleted by `TASK-261` (`TASK-302`, open P2). | If `perry-config` loses its subject entirely, both rows close on merge rather than leaving help text describing two things that do not exist. |

## Filed to the board

| Row | From | Priority |
|---|---|---|
| `TASK-396` — no published write contract, so a newly required flag reaches a consumer as a runtime refusal | § 9 Q1 | P1 |
| `TASK-397` — ADR-017 changed an identifier's value space and `perry-goals/list` stayed at 2.3 | § 9 Q3 | P1 |
| `TASK-398` — an advisory a program must act on is a payload field, not a stderr line | § 9 Q4 | P2 |

All three declared `unlinked` at `add`: they serve a consumer contract, not any
phase 003 KR, and guessing an edge is what `reference/okr-linkage.md` forbids.

## Not filed, deliberately

- **§ 7's boolean** — obsoleted by ADR-019, above.
- **§ 9 Q2, one KR grammar** — already `TASK-393` (*the shipped OKR template
  still mints the retired KR grammar*), open P1. aiMark's answer is "one, and
  fix `TASK-393`", and until then they treat dual-read as a **documented
  requirement** rather than a lucky accident. Their § 2.1 + § 1.5 argument is
  new and belongs on that row when it is worked: with a picker, two live
  grammars stop being a rendering problem and become a create-path problem —
  the user picks `KR-O1.1`, the store takes only `P<NNN>-…`, and the edge is
  written and then called malformed by the linter.
- **§ 1.2** — aiMark's own defect: `/api/tasks/act` filtered the request body
  through an inline copy of the field list that did not include `summary`, so
  the flag was in the builder and absent from the transport. Fixed on their
  side with one exported `WRITE_FIELDS` plus a test. Recorded here only because
  the shape is Perry's too, and it is the argument for `TASK-396`.

## What moved that this lane cannot write

**`O4-KR3` — *"A full task lifecycle — create → start → close with evidence —
driven end to end from the aiMark UI against a real project"* — is reported
met**, with a verbatim transcript through `/api/tasks/act` against a copy of the
fixture, and the three steps now run in aiMark's standing suite rather than as a
one-time demo.

`OKR.md` is the `goals` lane's file. This is a hand-off, not a write:
`/perry goals` should score `O4-KR3`, and the evidence is § 2 of the source
document plus `perry-conformance.test.ts`.

## Their suite, for the record

826 pass / 0 fail before this round; **834 pass / 0 fail** after, 5,554
assertions across 47 files. Eight new tests, six running the installed
`perry-task`, three of them writing.
