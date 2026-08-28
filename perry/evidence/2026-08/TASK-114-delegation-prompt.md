# TASK-114 — delegation prompt for an aiMark coding agent

> Rendered 2026-08-20 by `/perry work delegate`. Perry did not execute this work.
> Paste the block below into a fresh session **in the aiMark repository**.
> This project has declared no role cards, so the roleless fallback applies.

---

You are working in the aiMark repository at `/Users/bytedance/proj/aimark`. Perry
lives in a separate repository at `/Users/bytedance/proj/Perry`, which is
**read-only to you** — read its contract documents, change nothing in it.

## The task

aiMark reads Perry's tasks through the contract `perry-task/list/**1.2**`. The
current contract is **`perry-task/list/1.11`**. Move the read path to the current
contract, and record the pinned version in exactly one place so the next drift is
visible instead of silent.

This is a **version catch-up, not an architecture change.** Three things are
deliberately out of scope, and each has its own reason:

- **Do not remove aiMark's markdown parsing.** The OKR chain view parses
  `OKR.md`, `BOARD.md` and `phase/NNN-linkage.md` in process. Deleting that is a
  separate, larger piece of work gated on a Perry change that has not landed
  (`perry/OKR.md § KR-O4.1`, target 0 lines by 2026-09-30). Touching it now means
  doing it twice.
- **Do not add a write path.** Perry has no write contract for outside
  consumers yet — its writers are CLI tools. Anything you build now would be
  built against a shape that does not exist.
- **Do not change what aiMark renders.** Same task set, same screens. If a field
  moves on screen, that is a regression in this task even if it looks better.

## What to read, in this order

All paths are in the Perry repository.

1. `schema/task-list-contract.md` — the contract itself, at 1.11. Read the whole
   file, and in particular its `## Changes`/semantics list: it records what moved
   between versions and which of those a consumer must care about.
2. `schema/goals-list-contract.md` and `schema/decide-list-contract.md` — the
   two contracts that cover goals and decisions. `perry-goals/list` is at **2.0**,
   a major version; `perry-decide/list` is at 1.0.
3. `schema/events-list-contract.md` — only if aiMark shows history or timelines.

Run the tools yourself against a real project to see actual payloads rather than
inferring them from the documents:

```
cd /Users/bytedance/proj/Perry
python3 bin/perry-task   list --all --json --root /Users/bytedance/proj/aimark
python3 bin/perry-goals  list --json      --root /Users/bytedance/proj/aimark
python3 bin/perry-decide  list --json      --root /Users/bytedance/proj/aimark
```

## Four things in the contract that will bite a 1.2-era consumer

These are the ones worth naming in advance; the contract document has the rest.

1. **`id` is an opaque stable string.** The contract says so explicitly: *"Do not
   parse a number out of it or sort by a numeric suffix."* A real board carries
   ids under several project-declared prefixes, some with no number at all. If
   aiMark sorts or groups by a parsed number anywhere, that is a live bug, not a
   style issue.
2. **`summary` is new in 1.11** — an optional stable explanation of why a task
   exists. `""` means unset, and it is *never* inferred from `title`,
   `next_action`, evidence or journal prose. If aiMark currently synthesises a
   description from those, replace it with this field rather than keeping both.
3. **`ts` has seconds precision and ties are normal, not duplicates.** Two events
   one operation apart routinely land in the same second. **Timeline order is
   array order and is authoritative.** If you re-sort a timeline by `ts`, use a
   stable sort or you will reorder a `start` after the `status` that followed it.
4. **`perry-goals/list` is 2.0**, so anything aiMark does with goals through an
   older shape needs re-reading against the document rather than adapting by
   guess.

## The pinned version, in one place

Today the pin is scattered enough that a nine-version drift went unnoticed. Put
the version string in exactly one constant, read it from there everywhere, and
make aiMark fail loudly — not silently degrade — when the payload's `contract`
field does not match what it expects. A consumer that silently accepts an
unexpected contract is how this happened.

## Acceptance

1. aiMark renders the same task set it renders today against a real project.
   Capture before and after and compare them.
2. A field the older contract did not carry is visibly read through the new one —
   `summary` is the obvious candidate.
3. The pinned version appears in exactly one place, proven by a search.
4. The diff touches no rendering of the OKR chain view, proven by the file list.
5. aiMark's own test suite is no redder than before you started. Measure it
   first; do not take a baseline on trust.

## Report back

State what you changed, the before/after render comparison, the search proving
the single pin, and anything in the contract that did not match what aiMark
assumed. That last one is the most valuable thing you can bring back — a place
where the document and the consumer disagree is a finding for Perry, not just
for aiMark.
