# ARCHITECTURE.md §7 OQ-1 closure — 2026-09-21 (USER-987)

## The user's confirmation

USER-987 was recorded as "Update ARCHITECTURE.md §7 OQ-1 … ? — yes". The exact
wording was then proposed in chat (AskUserQuestion, header "OQ-1") and the user
selected **"按此写入 (Recommended)"** with this preview, on 2026-09-21:

```
- **OQ-1 — The schema anchors this file in the wrong place.** *Closed
  2026-09-21 (USER-987).* TASK-451 (DESIGN-017 A1, main 6d471770) anchors
  `ARCHITECTURE.md` at the code root in `schema/state-schema.json`; TASK-452
  (A2, main 5d661ec6) makes `perry-state` read and cap-check it there, and
  `--section architecture` reports `exists: true` on this repository. The one
  remaining reader that ignores the code anchor, `perry-diagnose`'s ownership
  scan, is TASK-477. The text below is the question as it stood.
  ANSWERED for where it lives, open for the fix. …(原文不动)…

§8 新增：
- 2026-09-21 · v1 · USER-987: §7 OQ-1 closed after TASK-451 and TASK-452;
  its text is kept. No other section is edited.
```

The PMO recorded the USER-987 answer before showing that wording; the ask record
therefore authorises "update" and this file carries the confirmed text. Noted as
a recording-order defect against P004-O3-KR2's "recorded before it is acted on".

## Candidate

`pmo/architecture-oq1-closed` `664ca039652d9fc38018356146288d0f7b887e57`, base
main `75869a68`: one file, `ARCHITECTURE.md` +11/−2 (the question's head line is
moved below the closure paragraph word for word); 457 lines, eight sections.

## Architecture review (fresh context) — verbatim

```
=== ARCHITECTURE COMPLIANCE ===
Reviewer: independent architecture reviewer (Claude Opus 5 subagent). Fresh context, not the author. Read-only: nothing was edited, committed or checked out. Timestamp: 2026-09-21.
Base: 75869a684d65bafe5aa711a98a4dfa31e12b81cb
Head: 664ca039652d9fc38018356146288d0f7b887e57
Triggers:
- listed boundary paths: FALSE
- new top-level directory: FALSE
- new bin executable: FALSE
- contract-version change: FALSE (header `Version: v1` unchanged; §5 not in the diff)
- root architecture edit: TRUE (ARCHITECTURE.md)
- module architecture edit: FALSE
All six were verified with `git diff --stat 75869a68 664ca039`: one commit, one file, ARCHITECTURE.md, +11/−2.
Context:
- Sections read. Head: preamble 1–42, §1 at 43, §3 at 139, §6 at 241 (NN-6 at 293–303), §7 at 305, §8 at 372. Base: §8 at 366.
- Mapping. The root architecture document only. No module document is touched.
- Documents. ARCHITECTURE.md at base and head. schema files[id=architecture] (authority split) and claims[path=ARCHITECTURE.md] (anchor code). perry/asks.jsonl:88 (USER-987) and :89 (USER-988).
- Unresolved facts:
  1. The USER-987 record authorises updating OQ-1; it does not literally say "close" and does not contain the text. The claim that the user confirmed this exact wording rests on the chat.
  2. The cited commits 6d471770 and 5d661ec6 are the test-duration commits that follow the integration commits db74c48a and 13733b21. Both are ancestors of base and the claims are true at them; the citations are imprecise, not false.
Rules:
- NN-6, ARCHITECTURE.md:293–303, plus schema files[id=architecture].note — holds. Closure cites USER-987 (asks.jsonl:88, answered 2026-09-21; see unresolved 1). Nothing in §6 or §7 is deleted; the removed bullet head returns word for word at head:314. §1, §3 Forbidden, §5, §6 not in the diff.
- §8 append-only, ARCHITECTURE.md:372–375 — holds. One entry added above earlier entries, as every entry is placed. No existing §8 line changed.
- Truth of the new sentences, ARCHITECTURE.md:307–313 — holds. Head schema anchors architecture and its claim at "code"; bin/perry-state:1483 and :1751–1752 read and cap-check at lib.anchor_root(..., "code"), cap 500 at :1471; `perry-state --section architecture --root /Users/bytedance/proj/Perry` returns exists: true, section_count 8; bin/perry-diagnose:2641–2645 ignores the code anchor; TASK-477 is in_progress. Every code reader of the location enumerated (perry-state, perry-lint :4993/:5706, perry-state-cost :251, viewer/parsers.py:5235, perry-diagnose :1744 skips file claims) — the ownership scan is the only one that ignores the anchor.
- Hard cap 500 and eight fixed sections — holds. 457 lines at head (448 at base); §1–§8 in order; section_count 8.
- §7 "No row is open for this yet", ARCHITECTURE.md:324 — holds; now framed by line 313 as "the question as it stood".
- §1–§5, §6 NN-1…NN-5 — not touched.
- Preamble HTML comment, ARCHITECTURE.md:26–29 — not touched, but contradicts the current state: it still says perry-state "reports `exists: false` while this file sits here. §7's first open question carries that". False since TASK-452, before this edit. Descriptive and outside the eight sections; a follow-up, not a blocker.
Decision: PASS. Non-blocking notes: (1) the preamble comment at 26–29 is stale (already stale at base); (2) the cited SHAs are the duration commits, not the integration commits.
User decision required: none, provided the user confirmed this exact text in chat. The written record (USER-987) only authorises "update §7 OQ-1".
Not checked: the chat transcript behind USER-987; non-code readers of the location (skill/pack prose, test fixtures); DESIGN-017 §5.1 itself; no suite, lint or mutation run.
=== END COMPLIANCE ===
```

## Follow-ups

- Preamble comment `ARCHITECTURE.md:26-29` is stale (descriptive; agent may
  edit). To be corrected with TASK-477's landing, when OQ-1's "remaining reader"
  sentence also changes.

## Acceptance

| Step | Result |
|---|---|
| Full gate | `merge-check --base main delivery=pmo/architecture-oq1-closed --tier full`: green on tree `c1d6f792`, base `75869a68`, 158 modules / 4,461 tests |
| Durations | first committed onto the candidate branch itself, so `--verify-receipt` refused (candidate moved); moved to `integ/oq1` `adfa0720` and the candidate ref reset to `664ca039`; `--verify-receipt` then VERIFIED on `adfa0720` |
| Slow gate | `tests/run --tier slow` at `adfa0720`: 162 modules · 4,564 tests · all green |
| Merge | refs rechecked; `git merge --ff-only integ/oq1` → main `adfa0720` |
