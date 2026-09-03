# TASK-290 — round 2

**Branch**: `coding/task-290-path-char-fix`
**Base commit**: `2f4c4355bdf18946495aecb13ed4fa891c33d66b` (`main`)

The worktree this round was cut in arrived at `d49964e`, **224 commits behind
`main`**. The branch was created explicitly at `2f4c435` before any work
started; `git merge-base HEAD main` is `2f4c435` and `git rev-list --count
HEAD..main` is 0. Every path named in the round-1 review resolved in the
checkout.

## Status

IN PROGRESS — reproduction and baseline recorded; fix not yet written.

## The defect

`_PATH_CHAR` at `viewer/parsers.py:4344` is used for two different questions and
is only right for one of them.

- **"How far does this path run?"** — `path_token_around`, which feeds rule 2's
  foreign-root test. This question genuinely needs the wide class: `~`, `$`,
  `<`, `>`, `{`, `}` are exactly the anchors `path_root_is_foreign` recognises a
  foreign or unresolved root by.
- **"Is this component a longer *name* than the fragment?"** — rule 1 in
  `_discount_reason`. This question needs a **filename** class. Measured from
  the wide token, any admitted non-name character adjacent to the match makes
  the component strictly longer than the fragment, and the occurrence is
  discounted as `names-a-longer-file` when the text names no longer file at all.

The round-1 review reached the same conclusion and stated it as *"the two
questions were collapsed onto one constant, and the second one is the one the
safety decision hangs on."*

## Reproduction — all four lines, before any change

`bin/perry-state --root . --escalation-scan <spec>`, against the live hook
(35 fragments armed), each spec declaring the write in `## Files in scope`.

| # | `Files in scope` line | verdict | exit | |
|---|---|---|---|---|
| A | `- schema/state-schema.json — the claim surface` | `refuse` | **3** | correct |
| B | `- This round rewrites schema/state-schema.json.` | `pass` | **0** | a full stop |
| C | ``- `schema/state-schema.json` — the claim surface`` | `refuse` | **3** | correct |
| D | `- **schema/state-schema.json** — the claim surface` | `pass` | **0** | markdown bold |

B and D reproduce the PMO's report exactly. Both payloads name the reason
themselves:

```json
"discounted": {"Files in scope": {"state-schema.json": [
    {"token": "schema/state-schema.json.",     "why": "names-a-longer-file"}]}}
"discounted": {"Files in scope": {"state-schema.json": [
    {"token": "**schema/state-schema.json**",  "why": "names-a-longer-file"}]}}
```

Neither text names a longer file. `**` is markdown and the trailing `.` is a
sentence.

## Baseline census — `main` at `2f4c435`

Enumerated exactly as the `## Bound` gives it, over every
`perry/evidence/*/*-spec.md`:

```
scanned : 147
refused :  16
```

by fragment (refusing spec × fragment pairs):

```
state-schema.json  11    claims  6    ln -s/-sf/-snf  3    diagnose  2
~/.claude/skills 1  setup 1  rm -rf 1  relocate 1  published 1  publish 1
adopt 1  --force-with-lease 1  $perry_home 1
```

The **13 legitimate refusals** the brief requires intact are all present:

- `state-schema.json` × 8 — TASK-100, 156, 196, 197, 201, 219, 235, 276
- `claims` × 5 — TASK-196, 197, 221, 235, 276

(The claim surface now refuses on 17 pairs, not 13: round 1's false-PASS
closure added `state-schema.json` on TASK-047, 085, 139 and `claims` on
TASK-100. Those four are round 1's win and must also survive.)

## The margin, measured

A refusal survives on N *live* occurrences — occurrences in a touch section that
`_discount_reason` did not discount. N = 1 means one character of formatting
flips the spec to exit 0.

```
refusing (spec, fragment) pairs : 31
pairs holding on live == 1      : 23
refusing specs                  : 16
specs where EVERY refusing fragment holds on live == 1 : 10
```

Of the 13 named legitimate refusals, **11 hold on exactly one live occurrence** —
reproducing the round-1 review's figure exactly on today's `main`.

## Fix

(pending)

## Controls

(pending)
