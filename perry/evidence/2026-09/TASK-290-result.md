# TASK-290 — dispatch gate matches cited paths as if written

**Status:** in progress (stub committed first, per PMO instruction).

## Provenance

- Worktree was cut at `d49964e` — **163 commits behind `main`**, where the spec does
  not exist. Verified with `git rev-list --left-right --count HEAD...main`.
- Branch `coding/task-290-gate-cites-vs-writes` was therefore created from
  `main` at **`548f206`** ("Escalation override recorded before either row is
  dispatched"), which is the stated baseline.

## What this round will do

1. Read `perry/evidence/2026-09/TASK-290-spec.md` in full and honour its `## Bound`.
2. Re-derive the census on this checkout (claimed: 145 scanned / 25 refused;
   13 legitimate, 12 on citations).
3. Choose a **structural** mechanism — path-resolves-inside-project scoping and/or
   write-target vs citation — never a plain-language intent classifier.
4. Build the false-pass control (`Out of scope` mention cancelling a real
   `Files in scope` hit) and a true-positive control (claim surface, exit 3).
5. Plant mutations against every line claimed as load-bearing; restores verified
   against `git show <ref>:<path>` / `bin/perry-restore-check`, never a self-snapshot.

## Census before — re-derived on this branch (`548f206`)

Enumeration exactly as the `## Bound` gives it:

```
for f in perry/evidence/*/*-spec.md; do bin/perry-state --root . --escalation-scan "$f"; done
```

```
specs scanned : 146      (spec says 145 on 47fa45a)
refused       :  26      (spec says  25 on 47fa45a)
passed        : 120
fragments armed: 35      — matches the Bound exactly
```

**The +1 reconciles.** The extra spec is `perry/evidence/2026-09/TASK-323-spec.md`,
added between `47fa45a` and `548f206`, and it refuses on `evidence/` — so the
delta is `evidence/ 8 → 9` and nothing else moved. Every other number in the
spec's table is reproduced byte-for-byte.

```
by fragment (a spec may contribute more than one):

  state-schema.json    8   legitimate — the claim surface
  claims               5   legitimate — the claim surface
  -------------------------------------------------------------- 13
  evidence/            9   suspect   (8 in the spec, +TASK-323)
  diagnose             8   suspect
  design/              4   suspect
  knowledge/           1   suspect
  -------------------------------------------------------------- 22 fragment-hits
  ~/.claude/skills 1 · ln -s 1 · ln -sf 1 · ln -snf 1 · publish 1 ·
  published 1 · --force-with-lease 1 · rm -rf 1 · $perry_home 1 ·
  adopt 1 · relocate 1 · setup 1        the untriaged tail (Bound: not this row)
```

### The false pass is real, and there are seven of them

The spec says *an earlier row was dispatched on a `pass` whose only clean reason
was that its `Out of scope` incidentally mentioned `diagnose`*. That is not a
single anecdote. Scanning every spec for a non-empty `green_lit` on a `pass`:

| spec | green-lit fragment | verdict |
|---|---|---|
| `TASK-047-spec.md` | `state-schema.json` | `pass` |
| `TASK-085-spec.md` | `state-schema.json` | `pass` |
| `TASK-086-spec.md` | `diagnose`, `relocate`, `claims` | `pass` |
| `TASK-095-spec.md` | `diagnose` | `pass` |
| `TASK-109-spec.md` | `claims` | `pass` |
| `TASK-139-spec.md` | `state-schema.json` | `pass` |
| `TASK-247-spec.md` | `diagnose` | `pass` |

Five of the seven were green-lit on a **claim-surface** fragment — the 13 the
gate is supposed to be protecting. `green_lit` is already in the payload, so
this is not invisible so much as **unranked**: exit code `0` and the word `pass`
are identical to a genuinely clean scan, and nothing in `dispatch.md` step 4
tells a reader to go looking at a key that is empty 95% of the time.

Results follow below as they land.
