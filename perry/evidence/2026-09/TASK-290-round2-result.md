# TASK-290 — round 2

**Branch**: `coding/task-290-path-char-fix`
**Base commit**: `2f4c4355bdf18946495aecb13ed4fa891c33d66b` (`main`)

The worktree this round was cut in arrived at `d49964e`, **224 commits behind
`main`**. The branch was created explicitly at `2f4c435` before any work
started; `git merge-base HEAD main` is `2f4c435` and `git rev-list --count
HEAD..main` is 0. Every path named in the brief and the round-1 review resolved
in the checkout.

## The defect

`_PATH_CHAR` at `viewer/parsers.py:4344` was used for two different questions
and is only right for one of them.

- **"How far does this path run?"** — `path_token_around`, which feeds rule 2's
  foreign-root test. This question genuinely needs the wide class: `~`, `$`,
  `<`, `{` are exactly the anchors `path_root_is_foreign` recognises a foreign
  or unresolved root by.
- **"Is this component a longer *name* than the fragment?"** — rule 1 in
  `_discount_reason`. This needs a **filename** class. Measured off the wide
  token, any admitted non-name character adjacent to the match made the
  component strictly longer than the fragment, and the occurrence was
  discounted `names-a-longer-file` when the text named no longer file at all.

The round-1 review reached the same conclusion: *"the two questions were
collapsed onto one constant, and the second one is the one the safety decision
hangs on."*

## Reproduction — all four lines, before any change

`bin/perry-state --root . --escalation-scan <spec>` against the live hook
(35 fragments armed), each spec declaring the write in `## Files in scope`.

| # | `Files in scope` line | verdict | exit | |
|---|---|---|---|---|
| A | `- schema/state-schema.json — the claim surface` | `refuse` | **3** | correct |
| B | `- This round rewrites schema/state-schema.json.` | `pass` | **0** | a full stop |
| C | ``- `schema/state-schema.json` — the claim surface`` | `refuse` | **3** | correct |
| D | `- **schema/state-schema.json** — the claim surface` | `pass` | **0** | markdown bold |

Both payloads named the reason themselves:

```json
"discounted": {"Files in scope": {"state-schema.json": [
    {"token": "schema/state-schema.json.",    "why": "names-a-longer-file"}]}}
"discounted": {"Files in scope": {"state-schema.json": [
    {"token": "**schema/state-schema.json**", "why": "names-a-longer-file"}]}}
```

Swept over the whole class rather than the two reported spellings: **all eleven
characters** (`. ~ $ * < > { } @ + -`), in **both** positions — 22 of 22 —
turned a declared claim-surface write into `pass`/exit 0, and so did the same
sweep on `.perry/claims`.

## The margin, measured

A refusal survives on N *live* occurrences — occurrences in a touch section
`_discount_reason` did not discount. N = 1 means one character of formatting
flips the spec to exit 0.

```
refusing (spec, fragment) pairs : 31
pairs holding on live == 1      : 23
refusing specs                  : 16
specs where EVERY refusing fragment holds on live == 1 : 10
```

Of the 13 named legitimate refusals, **11 hold on exactly one live
occurrence** — reproducing the round-1 review's figure exactly on today's
`main`. (The brief's "6 of the 16" is low; the measured figure is 10 of 16.)

## The fix

Two constants, two questions.

**`_PATH_CHAR` is unchanged in content** and gains a per-character
justification, because it is one half of a safety decision and the set should
not have to be inferred: `A-Za-z0-9` the names, `/` the separator, `_`/`-` the
joiners, `.` the extension and leading dot, `~`/`$` the root anchors
`path_root_is_foreign` reads, `<>`/`{}` the two placeholder spellings, `*` the
glob, `@`/`+` carried but not load-bearing.

**`_NAME_EDGE = "[A-Za-z0-9_]"` is new** — what a path component may *begin and
end with*. Rule 1 now trims the `/`-delimited component inward from each end to
the first character a filename can be bounded by. `.` and `-` are deliberately
absent from the edge class: both belong **inside** a component and neither ends
one, and admitting either re-opens the sentence-final-period hole.

Both trim loops stop at the match, so the trim only ever removes characters
**outside** the fragment. A component that is longer because of its own name
keeps every character that made it longer.

### Why `_PATH_CHAR` was NOT narrowed — the brief's instruction 1, tested

The brief asked for `_PATH_CHAR` to admit only path-component characters.
Applied to the single shared constant, that closes this hole and **opens three
worse ones**. Measured, with the eleven characters dropped:

| case | before | with `_PATH_CHAR` narrowed |
|---|---|---|
| `~/other-project/evidence/2026-09/` | refuse | **cleared** — re-roots to `project/evidence/2026` |
| `$PERRY_HOME/inputs/` | refuse | **cleared** — re-roots to `perry_home/inputs/` |
| `**$PERRY_HOME/inputs/**` | refuse | **cleared** |
| `reference/diagnose.md` | discounted | refuses again (false positive returns) |
| `schema/state-schema.json.bak` | discounted | refuses again |

`path_root_is_foreign` recognises a foreign root *by* those characters. Writing
into a namespace Perry was never given is this hook's signature risk; trading it
for a markdown-emphasis hole is not a fix. The reasoning is recorded at the
constant and pinned by
`test_the_root_anchors_must_stay_in_the_path_class`.

## Controls

**The four lines, after** — A `refuse`/3, B `refuse`/**3**, C `refuse`/3,
D `refuse`/**3**. All four correct.

**The census, after** — `147` scanned, `16` refused. The refused
(spec, fragment) pair list is **byte-identical** to the baseline, so all 13
legitimate refusals survive and so do round 1's four additions (TASK-047, 085,
139 on `state-schema.json`, TASK-100 on `claims`).

**A behaviour table of 53 cases** run before and after: the only lines that
changed are the 26 that had to. Every legitimate discount (`bin/perry-diagnose`,
`reference/diagnose.md`, `**bin/perry-diagnose**`, `bin/perry-diagnose.`,
`bin/**perry-diagnose**`, `state-schema.json.bak`, `bin/perry-claims-report`,
own-tree `perry/evidence/…`, `evidence/**/*-spec.md`) and every foreign-root
refusal (`~/`, `/srv/`, `../`, `$PERRY_HOME/`, `<target>/`, `{{project}}/`,
`*/`, and each of those in bold) is unchanged.

## Mutation round

Anchored by line number **with an assert on the old text** — a non-matching
anchor is a hard error, never a silent no-op. `__pycache__` cleared and the
whole-second boundary waited past before every run. All destructive work on a
`git archive` copy in a uniquely-named scratch directory, itself made a git
repo so restores could be verified against a real ref.

**Restores verified with `git show HEAD:<path>` written back and byte-compared,
single-path only.** `bin/perry-restore-check` was not used: TASK-256 found its
`ok = all(...)` mutates to `any` with all fifteen tests green, so a multi-path
call can report a false pass.

**18 planted · 16 red · 2 green.**

Red, each against `tests/test_escalation_boundaries.py`:

| | mutation |
|---|---|
| M01 | `_PATH_CHAR` loses `*` — **round 1's green #1** |
| M02 | `_PATH_CHAR` loses `+` and `@` — **round 1's green #2** |
| M03–M05 | `_PATH_CHAR` loses `~` / `$` / `.` |
| M06 | `_PATH_CHAR` narrowed to name chars — the brief's own lever |
| M07–M10 | `_NAME_EDGE` admits `.` / admits `.` and `-` / widened to `_PATH_CHAR` / loses `_` |
| M11 | the right trim loop never runs — **the reverted line** |
| M12 | the left trim loop never runs |
| M13 | the right trim drops its `not` |
| M16 | the strict `>` in the component test becomes `>=` |
| M17 | the `"/" in token` guard deleted |
| M18 | the separator-spanning clause deleted |

**Round 1's two green mutations are now red.** That was the point of the guard.

### The two greens, and why neither is a hole

Both are the trim loops' bounds — `comp_end > end` (M14) and
`comp_start < start` (M15) — the guards that stop a trim from eating into the
match.

- **M14 is provably unreachable.** The bound can only fire when the fragment's
  own **last** character is not a name-edge character *and* the fragment carries
  no `/` (rule 1 is skipped otherwise). Enumerated over the live 35-fragment
  union: **no fragment qualifies.**
- **M15 has two candidates** — `$perry_home` and `--force-with-lease` — and
  neither changes a verdict. Run under the mutation, the full 147-spec census
  and the 53-case behaviour table are both **byte-identical** to the unmutated
  tree, and every spelling of the two candidates on a path was checked directly.

Both are **equivalent mutants**, not findings, and both fail in the safe
direction: removing a bound can only *shrink* a component, which can only turn a
discount into a refusal. Reporting them as holes would be the same error as
missing one.

## Suite and lint

| | baseline `2f4c435` | branch |
|---|---|---|
| `bash tests/run` | 114 modules · **3258** tests · all green | 114 modules · **3268** tests · all green |
| `bin/perry-lint --root .` | — | **0 errors**, 37 warnings |

+10 tests is exactly the new `TestTheCharacterClassesTheDiscountHangsOn`. The
37 warnings are the pre-existing categories (`spec-scope-unscannable` × 45 —
TASK-284's; `bounds` × 127; `summaries` × 16). The `test_host_support`
dispatch-limit flake did not appear in either run.

## Two pre-existing holes found in passing — neither is this row's

Both were confirmed present on the **baseline** as well as the branch, so
neither is caused or closed by this change. Each is a candidate row.

1. **Markdown *italic* with underscores still clears the claim surface.**
   `- _schema/state-schema.json_` and `- schema/state-schema.json_` are **not
   matched at all** — `escalation_pattern`'s right-edge guard is `(?![A-Za-z0-9_])`
   and a trailing `_` is a word character. This is the same *category* as the
   defect just fixed — formatting alone passes the gate — but it lives at the
   TASK-107 matcher, not at rule 1, and closing it means changing what
   `_ESC_WORD` means. The round-1 review flagged it as pre-existing and out of
   scope; it is still open and it is the sharpest remaining edge.

2. **Bolding an own-tree path makes it refuse.** `- **perry/evidence/2026-09/x.md**`
   refuses, because `path_root_is_foreign` reads the head as `**perry`, sees a
   `*`, and calls it foreign. A false positive in the **safe** direction, and
   `Making the gate refuse more` is explicitly out of this row's scope — but it
   defeats round 1's own `evidence/` discount on any bolded path.

## Files changed

- `viewer/parsers.py` — `_PATH_CHAR` documented per character; `_NAME_EDGE`
  added; rule 1 in `_discount_reason` trims the component to it.
- `tests/test_escalation_boundaries.py` — `TestTheCharacterClassesTheDiscountHangsOn`,
  10 tests, extending the file the spec named rather than starting a third.
- `perry/evidence/2026-09/TASK-290-round2-result.md` — this file.

`.perry/hook.md`, `schema/state-schema.json` and everything under `claims` were
not touched. Nothing was pushed; no PR was opened; `main` is still `2f4c435`.
