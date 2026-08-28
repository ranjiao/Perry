# TASK-180 — migrate every phase-KR id, once, with no compatibility left behind

Dispatch mode: auto
Verification: V3
Re-verified: 2026-08-28 against `0341c7b`

## The decision, and who made it

**DESIGN-007 decision #4 is `locked`, 2026-08-19**: phase-KR ids become
**`P002-O3-KR1`** — segment-labelled and project-unique, *"on the ground that
every segment should carry its own label rather than rely on position"*.

**The user decided the migration shape on 2026-08-28**: *一次性迁移，把所有历史
数据换成新格式，不保留对老的错误格式的兼容* — one-time, all historical data,
**no compatibility with the old form.** No dual-read, no fallback branch, no
"accept both for one release".

You are not being asked to re-litigate either. You are being asked to execute
them correctly.

## The mapping

```
P-O<a>.<b>   in phase <NNN>   →   P<NNN>-O<a>-KR<b>
```

Phase numbers are zero-padded to three digits, from DESIGN-007's own worked
example: `002/P-O3.1` → `P002-O3-KR1`.

## Scope: `P-O*` only. `KR-O*` is a different family and is OUT.

DESIGN-007 line 16 says *"the phase-KR id"*. The **overall** OKR's KRs are
`KR-O1.1` — **34 in `OKR.md`, 34 in `okr.jsonl`** — and they are **not** in
scope. Touching them would be a second migration nobody decided.

## What you are working on: 73 files, 382 occurrences

Measured over `git ls-files` (**not** a bare `grep -r` — `.claude/worktrees/`
holds full repo copies from old agents and inflates every count; my first
measurement made that mistake).

| bucket | files | hits | how the phase is decided |
|---|---|---|---|
| `perry/phase/001-*` | 2 | 69 | **P001**, from the filename |
| `perry/phase/002-*` | 2 | 22 | **P002**, from the filename |
| `bin/`, `viewer/` | 6 | 13 | the regexes themselves |
| `tests/` | 16 | 143 | per-case; most are fixture ids, not references |
| `schema/` | 2 | 5 | documentation examples |
| templates & reference | 12 | 29 | **placeholders** — see below |
| `perry/evidence/` | 25 | 65 | **prose — judgement** |
| `perry/journal/` | 3 | 18 | **prose — judgement** |
| `perry/handoff/`, `BOARD.md` | 2 | 6 | **prose — judgement** |
| `perry/design/` | 2 | 9 | prose |
| `.perry/events.jsonl` | 1 | 3 | **append-only — CANNOT be rewritten** |

**7 of the 8 ids collide across the two phases** — `P-O1.1`, `P-O1.2`,
`P-O1.3`, `P-O2.1`, `P-O2.2`, `P-O3.1`, `P-O3.2`. Only `P-O1.4` (001 only) and
`P-O2.3` (002 only) are decidable from the id alone. **So a global
search-and-replace is wrong for 7 of 8 ids and you must not attempt one.**

## Resolving the phase in prose

```
phase 001   Started 2026-08-17   Status: scored    linkage updated 2026-08-18
phase 002   Started 2026-08-19   Status: active    linkage updated 2026-08-21
```

The date a document was written is a **strong prior, not proof**. **Confirm each
occurrence against the KR title or subject near it**, and against the two
registers:

```
001  P-O1.1  "Non-`project` modes running on a live, non-fixture track"
002  P-O1.1  "`BOARD.md` is rendered from `perry/tasks.jsonl` …"
```

**Where context genuinely does not decide it, do not guess.** List those
occurrences in your result record with file and line, leave them untouched, and
say so. An unresolved handful reported is worth more than 382 confident
rewrites with three wrong ones buried in them.

## The carve-out, and it is the intellectually load-bearing part

Some documents **quote the old form as the artifact under discussion**, not as a
reference to a KR. Rewriting those destroys the thing they exist to record.
Known instances, and there will be more:

- `perry/evidence/2026-08/2026-08-28-a-locked-decision-that-never-shipped.md`
  lines 52-53 print `001-linkage.md P-O1.1` beside `002-linkage.md P-O1.1`
  **to demonstrate the collision.** Migrated, the demonstration says nothing.
- `perry/design/DESIGN-007-*.md:16` quotes the drafted `002/P-O3.1` **as the
  rejected form**, and its own frontmatter `Linked OKR: P-O3.1 (phase 002 …)`
  is a *reference* and does migrate.

**The rule: a reference migrates; a quotation of the old form as evidence
stays.** Every one you keep must carry an explicit marker on the same line or in
the sentence — so a future `grep` for the old form returns only deliberate
survivors, and the verification below can assert exactly that.

This is the same distinction `TASK-142`'s `means` text draws and the one
`TASK-179` is standing at. **Do not reword a verbatim quotation to avoid the
problem.**

## `.perry/events.jsonl` — append-only, and the answer is to append

Three entries carry `P-O1.2`, all written 2026-08-28 04:02–04:08 (they are mine,
from last night's intake rows and `USER-903`). **You must not rewrite, compact
or reorder that file.** Verify your result is a **strict prefix extension** of
the original, exactly as TASK-167 did.

So those three keep the old id forever, and *"no compatibility"* must not mean
*"the log becomes unreadable"*. **Append one `migration` event carrying the
complete old→new mapping**, including which phase each resolved to, so the log
is self-describing: a reader meeting `P-O1.2` in an event from 04:02 can resolve
it **through the log itself**, with no fallback branch in any reader. That is
the difference between compatibility in the code (forbidden) and history in the
record (required).

## The regexes

```
bin/perry-lint:124     KR_ID_RE = r"\bP-O\d+\.\d+\b"
bin/perry-explain:64   ID_RE = re.compile(r"\b((?:P-O\d+\.\d+)|…)\b")
```

Both accept **only** the new form afterwards. **The old form must be rejected,
not merely unmatched** — if some check can be handed `P-O1.1` and silently do
nothing, that is the compatibility the user ruled out, wearing a different hat.
Say which behaviour you chose and why.

Note `perry-explain:64`'s second alternative `[A-Z][A-Z0-9]{1,9}-\d{1,4}` will
**not** match `P002-O3-KR1` (it ends in `KR1`, not digits). Check whether the
generic arm needs to change or whether the specific arm is enough — and
whether **TASK-158's `declared_id_families`**, merged last night, already has
opinions about this.

## Templates and placeholders

`goals/`, `reference/`, `state/`, `schema/` use `P-O1.1` as an **example**, not
a reference. They become the new *shape* — pick a consistent placeholder and say
what you picked. `SKILL.md § Style rules` forbids minting an example id that
resolves to nothing, so prefer the documented placeholder form over a concrete
id.

## Files in scope

Everything under `git ls-files` except: `.perry/events.jsonl` (append only),
`perry/okr.jsonl` and `perry/OKR.md` (they hold `KR-O*`, out of scope).

**`perry/` is normally read-only to you; for this row it is not** — the phase
registers are the canonical data being migrated. Use the tools where a tool
exists. Do not hand-edit `perry/tasks.jsonl` (it has **0** occurrences anyway).

## Verification

1. `grep -rE '\bP-O[0-9]+\.[0-9]+\b' $(git ls-files)` returns **only** the
   deliberate survivors, **each with its marker**. List them in your record.
2. `perry-explain` resolves every new id to **exactly one** KR in **one** phase.
   Show it for at least one id that used to collide.
3. **Mutation**: restore either old regex → a named test reddens. Report counts.
4. The events log is a **strict prefix extension**; the blank line at 67 intact;
   the migration event present and complete.
5. `perry-lint`: 0 errors, 3 warnings, 173 records, 0 rows drifted — unchanged.
6. `perry-okr diff`: `identical: true` — you must not disturb `OKR.md`.
7. Suite: **88 modules, one red** (`test_diagnose`, standing).

**Do not run `perry-conform declare`.** Do not `git push`. Do not touch `main`.
