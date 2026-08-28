# TASK-107 — The safety gate matches bare substrings, so ordinary English trips it

> Source: reported 2026-08-20 while dispatching TASK-079 and TASK-086
> Dispatch mode: manual
> Executor: manual — a change to the high-stakes gate is not a change the
>   high-stakes gate should be asked to wave through on its own behalf
> Estimated cycle: small
> Subjective verification: the reworded rule in `.perry/hook.md` and
>   `work/state/hook_TEMPLATE.md` says what the matcher now does
> Touches architecture: (none)
> Deployed: no

## Schema

- **Owner**: Coding Agent
- **Priority**: P1
- **Attribution**: unlinked

## Context

`escalation_fragments` extracts backticked spans from
`.perry/hook.md § High-stakes operations`; two matchers then look for those
fragments in project text as bare lowercased substrings:

- `viewer/parsers.py` · `matching_escalations` — `[f for f in fragments if f in hay]`
- `bin/perry-lint` · the consequence check — a second, inlined copy

Bare substrings match inside words. Measured against this repository's own
corpus on 2026-08-20:

| Where | Fragment | Matched | Verdict |
|---|---|---|---|
| TASK-079 `Deliverable` | `origin` | "its **origin**al bytes" | false positive |
| TASK-086 `Deliverable` | `adopt` | "on an **adopt**ed project" | false positive |
| TASK-105 `Deliverable` | `main` | "re**main**s available" | false positive |
| TASK-106 `Deliverable` | `main` | "re**main**s" ×3 | false positive |
| TASK-047 `Files in scope` | `state-schema.json` | the task edits it | correct refusal |

TASK-086 trips four fragments, but `diagnose`, `relocate` and `claims` are also
named in its `Out of scope` and are green-lit there. `adopt` was the only one
forcing a human to adjudicate. The same is true of TASK-079 and `origin`.

Two costs, and the second is the one that matters. A gate that cries wolf on
ordinary English gets waved through, and then it protects nothing. And the
cheapest way to pass it today is to reword the spec — a safety gate that pays
out for rewording is worse than no gate, because the reward is invisible.

**`\b` is not available here.** ADR-007 records `CLOCK_RE` failing five rounds
because `\b` does not exist in Chinese: the English half matched word-bounded,
the Chinese half matched bare, and `下周期` wrote a live row while `next cycle`
was refused. `tests/fixtures/sample-project-zh/.perry/hook.md` is a live Chinese
hook whose match tokens are deliberately ASCII while its prose is not. Any guard
written with `\b` or `\w` reproduces ADR-007's failure at this surface.

## Deliverable

1. **One matcher, guarding on an explicit ASCII class.** `matching_escalations`
   keeps its name and signature and matches a fragment only where the
   fragment's own edge is a word edge:

   - a left guard `(?<![A-Za-z0-9_])` only when the fragment *starts* with
     `[A-Za-z0-9_]`, so `~/.claude/skills`, `--force-with-lease` and
     `$PERRY_HOME` keep matching;
   - a right guard `(?![A-Za-z0-9_])` only when the fragment *ends* with
     `[A-Za-z0-9_]`, so `design/`, `evidence/` and `knowledge/` keep matching
     the paths beneath them.

   The class is written out. Neither `\b` nor `\w` appears, so an ASCII
   fragment inside Chinese prose matches exactly as it does inside English.

2. **`bin/perry-lint`'s inlined copy is deleted and calls the shared matcher.**
   Two extractions of one rule is how a scan quietly stops scanning what it
   used to — the reason `escalation_union` is already the single
   implementation, applied to the matcher as well.

3. **The dispatch pre-flight is computed, not eyeballed.**
   `perry-state --escalation-scan <spec>` returns the verdict as a typed field:
   which fragments the scanned sections tripped, which were green-lit by
   `Out of scope`, and `verdict: pass | refuse | unarmed`. `dispatch.md`
   pre-flight step 4 calls it instead of asking an agent to perform the match
   by hand. Correcting the matcher without this changes nothing at dispatch
   time, because today the matching is done by a model reading the sentence
   that says "substring".

4. **The rule is documented where it is stated.** `.perry/hook.md` and
   `work/state/hook_TEMPLATE.md` both currently describe substring matching as
   intended behaviour; both change in this edit, as does the
   `matching_escalations` docstring.

5. **The forms the gate loses are added back by hand.** A right-edge guard
   cannot match `ln -sf` from `ln -s`, `rm -rfv` from `rm -rf`, or `tokens`
   from `token` — the same morphology that stops `adopted` matching `adopt`.
   The hook already enumerates forms this way (`publish` and `published`,
   `prod` and `production`, `ln -s` and `ln -snf`); the forms this change drops
   are added to `.perry/hook.md` and to the template's defaults rather than
   special-cased in the matcher.

6. Behaviour is otherwise unchanged: extraction, the union, role addition and
   the `armed` semantics are untouched. This task changes where a fragment is
   allowed to match, and nothing about which fragments exist.

## Verification — V5

1. A regression fixture carrying **each false positive above** — `origin` vs
   "original bytes", `adopt` vs "adopted project", `main` vs "remains" — and
   asserting each no longer matches.
2. The same fixture carrying **each true positive currently caught** —
   `git push origin main`, `state-schema.json`, `~/.claude/skills`, `design/`,
   `--force-with-lease`, `push --force` inside `push --force-with-lease`,
   `rm -rf`, `$PERRY_HOME` — asserting each still matches.
3. An ASCII fragment inside Chinese prose (`部署到 production 环境`) matches,
   and the ADR-007 asymmetry does not reappear.
4. A test asserting `bin/perry-lint` contains no second substring matcher, in
   the shape `test_escalation_union.py` already uses to assert
   `P.escalation_union` is the one implementation.
5. `perry-state --escalation-scan` on a spec whose `Out of scope` names a
   fragment returns it green-lit, not refused.
6. `python3 tests/parallel`, `bash tests/run`, `python3 bin/perry-lint`,
   `git diff --check`. Baseline on this branch is two pre-existing failures —
   `test_board_render.test_perrys_own_board` (`Depends on` renders verbatim)
   and `test_router_budget` (`SKILL.md` 21036 > 20480) — neither related to
   this gate; the suite must be no redder than that.
7. V5 sign-off: this row modifies the project's own high-stakes gate, which is
   what `perry-lint`'s consequence check requires a human name and date for.

## Files in scope

- `viewer/parsers.py` — the matcher and the spec-section scan
- `bin/perry-lint` — delete the inlined matcher, call the shared one
- `bin/perry-state` — the `--escalation-scan` mode
- `work/reference/dispatch.md` — pre-flight step 4 calls the scan
- `.perry/hook.md`, `work/state/hook_TEMPLATE.md` — the matching rule sentence
- focused tests and their fixtures

## Out of scope

- **Making `Deliverable` a typed store field.** ADR-007 names `deliverable` as
  prose that no regex questions, and this scan questions it. The store does not
  carry the field today, so the scan reads the document; closing that gap is a
  larger task and is not settled here.
- **`perry-lint`'s semantic noise.** 12 task titles trip the consequence check
  today and word edges fix exactly one of them ("adoption"); the rest —
  TASK-060 "mint_id does not **adopt** the board's own id prefix" — mention a
  term rather than do it. Telling mention from action is not a boundary
  problem and is its own row.
- Which fragments the hook lists, beyond adding back the forms item 5 names.
- Changing extraction, `escalation_union`, role addition, or `armed`.
- Any change to which paths Perry claims, or to `schema/state-schema.json`.
- Closing TASK-107 without the V5 evidence above.
