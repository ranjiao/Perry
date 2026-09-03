# TASK-290 — round 1, V4 review

**Result: FAIL.**

Not on the census, which reproduces exactly, and not on the false-PASS closure,
which is real and is the most valuable thing in this round. It fails on the one
question V4 asks of a safety gate: **is it now weaker anywhere.** It is. The new
rule 1 discounts a `Files in scope` declaration of `schema/state-schema.json`
— the claim surface, the fragment the spec says must keep refusing — whenever
the path is written in **markdown emphasis** or ends a **sentence**. Both go
from `refuse` / exit 3 before this change to `pass` / exit 0 after, through the
real CLI seam. Eleven of the thirteen legitimate refusals survive on a single
live occurrence, so the margin protecting them is one character.

## Provenance, and a checkout that was not current

- The tool cut this worktree at **`d49964e`**, **211 commits behind `main`** —
  verified with `git rev-list --count d49964e..main`, and `git merge-base
  --is-ancestor` confirms it is an ancestor. Nothing was read from the checkout.
  Every path was reached with `git show main:<path>`; all four resolved.
- Review target per the brief: `main` at **`c506ca5`**, confirmed identical to
  `main` when this round started.
- **`main` advanced to `a61d2e5` mid-round.** `git diff --stat c506ca5 a61d2e5`
  touches `.perry/events.jsonl`, `perry/BOARD.md`, `perry/tasks.jsonl`, a
  journal file and three `*-review.md` files. **None of the four files under
  review changed**, and no new `*-spec.md` landed, so the census denominator and
  every finding below hold at both commits.
- All destructive work was done on `git archive` copies under a uniquely-named
  scratch directory. The live checkout was never written to; `git status` was
  empty at the start and at the end. `bin/perry-restore-check` confirms
  `viewer/parsers.py` and `bin/perry-state` match `HEAD` in the scratch repo
  after every mutation.

## What I confirmed, before the finding

I did not inherit a number in this section.

**The census reproduces.** Enumerated exactly as the `## Bound` gives it, over
all 147 `perry/evidence/*/*-spec.md` on `main`, 35 fragments armed:

| | before (`parsers.py`+`perry-state` reverted to `548f206`) | after |
|---|---|---|
| scanned | 147 | 147 |
| refused | **26** | **16** |
| passed | 121 | 131 |

147 rather than the result's 146 is `TASK-273-spec.md`, exactly as the result's
own note predicted — and it predicted the after-count would still be 16. It is.

**All 13 legitimate refusals survive.** `state-schema.json` × 8 — TASK-100,
156, 196, 197, 201, 219, 235, 276 — and `claims` × 5 — TASK-196, 197, 221, 235,
276. Every one still refuses. Confirmed independently from the before/after
payloads, not from the result's table.

**Exactly four fragments changed treatment**, and the discount counts match the
result to the unit: `diagnose` 17 `names-a-longer-file`, `evidence/` 17
`this-project's-own-tree`, `design/` 5, `knowledge/` 2. No claim-surface
fragment is discounted anywhere in the live corpus.

**The false-PASS closure is real, and I verified it rather than reading it.**

| spec | before | after |
|---|---|---|
| `TASK-047` | `pass`, exit 0, `green_lit: [state-schema.json]` | `refuse`, **exit 3**, `contradictions: [state-schema.json]` |
| `TASK-085` | same | same |
| `TASK-139` | same | same |
| `TASK-100` | `refuse` on `state-schema.json` only | also refuses `claims` |

This is the finding the row exists for and it stands.

**`ESCALATION_UNCANCELLABLE` did not break the legitimate `Deliverable`-only
green lights.** `TASK-086` still green-lights `relocate` and `claims` and
passes; `TASK-109` still green-lights `claims` and passes; `TASK-107` still
green-lights `adopt` while refusing on its symlink/push fragments. Only
`Files in scope` became uncancellable, which is what the spec asked for.

**The 13 cleared specs — judged independently, one at a time.** I pulled the
exact source line behind every discounted occurrence rather than trusting the
result's table. All 13 are citations under the spec's own stated reading of the
hook bullet: TASK-099/263/323/200/308 name a file **in Perry's own tree that
the round produces**; TASK-113/126/153/210 name `bin/perry-diagnose` or
`tests/test_diagnose.py`, filenames not the pipeline; TASK-110/290 are bare
directory words inside prose sentences *about* the directories; TASK-140/293
write `perry/design/…`. **I found no wrongly cleared spec.**

One caveat I am recording rather than scoring: TASK-140 and TASK-293 clear only
because the hook's *"overwriting a project's **own** `design/`"* is read as
meaning **a foreign project's**. That is not the more natural English reading,
but the spec asserts it explicitly ("i.e. **a foreign project's**") and the spec
is the sole authority here, so it is not a defect of this round.

**The author's two claimed-fixed green mutations are genuinely closed.**
Re-planted independently: deleting the `if "/" not in token: return None` guard
(their GREEN 2) goes **red**; weakening `if f in green and f not in declared`
to `if f in green` (their GREEN 1) goes **red**. Their account is accurate here.

**Suite and lint.** `bash tests/run` on the scratch copy: 114 modules · 3258
tests, green. `bin/perry-lint --root .`: **0 errors**, 37 warnings, all
pre-existing categories (`spec-scope-unscannable` × 45 is TASK-284's, `bounds`
× 127, `summaries` × 16). One intermittent failure appeared in a single run —
`test_host_support.TestOpenCodeDispatchLimit.test_concurrent_mixed_registers_do_not_exceed_global_cap`,
`2 != 3` — and was green in the other two full runs. It is a concurrency flake
in the dispatch-limit module, unrelated to this change, but it is a flake in the
suite this round measured itself against and someone should own it.

## The finding — rule 1 discounts the claim surface on ordinary markdown

### Reproduction

Two spec files, each declaring a genuine claim-surface write in
`## Files in scope`, run through the real CLI seam in both trees:

`ctl-bold-spec.md` — the path in markdown bold:

```
## Files in scope
- **schema/state-schema.json** — the conformance default only.
```

`ctl-plain-spec.md` — the path ending a sentence:

```
## Files in scope
- This round rewrites schema/state-schema.json.
```

```
bin/perry-state --root . --escalation-scan <spec>
```

| spec | before (`548f206`) | after (`main`) |
|---|---|---|
| bold | `refuse`, `refuse: [state-schema.json]`, **exit 3** | `pass`, `refuse: []`, **exit 0** |
| sentence-final period | `refuse`, **exit 3** | `pass`, **exit 0** |

The `after` payload states the reason itself:

```json
"discounted": {"Files in scope": {"state-schema.json": [
    {"token": "**schema/state-schema.json**", "why": "names-a-longer-file"}]}}
```

The rule's own justification is *"the match sits strictly inside one component
of a path, so the text names a longer file"*. Here it does not: the text names
**exactly** `schema/state-schema.json`. The `**` is markdown, not a filename.

### Why it happens, and the category — not the instance

`_PATH_CHAR = "[A-Za-z0-9_./~$*<>{}@+-]"` (`viewer/parsers.py:4344`) defines how
far `path_token_around` widens the window. It deliberately admits characters
that are not filename characters — the docstring says so, swallowing `**` on
purpose for globs like `evidence/**/*-spec.md`. `_discount_reason` then measures
the enclosing "component" from that widened token, so any admitted character
adjacent to the match makes the component **strictly longer than the fragment**
and rule 1 fires.

Enumerating the whole class rather than the case I hit first — every character
in `_PATH_CHAR`, both appended and wrapping, against a live
`schema/state-schema.json` declaration:

```
'.'  '~'  '$'  '*'  '<'  '>'  '{'  '}'  '@'  '+'  '-'
```

**Eleven of the thirteen** turn a counted hit into `names-a-longer-file`, in
both positions. (`_` is the exception and fails differently — it blocks the
match at `escalation_pattern`'s right edge, so `_schema/state-schema.json_` is
not matched at all. That is pre-existing TASK-107 behaviour, not this row's.)

Which fragments are exposed: **any fragment with no `/` of its own**, because a
match carrying a separator skips rule 1 by design. That includes both claim-
surface fragments. Demonstrated live: `**bin/adopt**`, `**remotes/origin**` and
`**.perry/claims**` are all discounted; `**~/.claude/skills**` is not, because
it carries its own separators.

### Why this is producible, not theoretical

Markdown emphasis on a path is ordinary spec prose — `.perry/hook.md` itself
writes `**Writing into a project Perry does not own**`, and the result document
under review bolds paths repeatedly. A path ending a sentence is ordinary
English, and `Deliverable` is *prose* by this change's own reasoning. Neither
form appears on a claim-surface path in today's corpus — I checked, which is
why the census is honest — but V4 asks about inputs a user can produce, and
these are two of the most common ways to write a path in a markdown file.

The margin is thinner than "not present today" suggests. Live-occurrence counts
for the 13 legitimate refusals:

```
state-schema.json : TASK-100 156 196 197 201 219 235  live=1   TASK-276 live=2
claims            : TASK-196 197 221 235              live=1   TASK-276 live=2
```

**Eleven of the thirteen hold on exactly one live occurrence.** Bolding that one
occurrence, or ending its sentence with a period, flips the spec to exit 0.
"Rewording the spec is the cheapest way to pass the gate" is the failure mode
`.perry/hook.md` names in its own preamble as *"the one thing a safety gate must
never reward"* — and this change reintroduces it in a form that needs no
rewording at all, only formatting.

### Green mutations at the responsible line

Rule 2 of the round: a green mutation is a finding. Two, both at
`viewer/parsers.py:4344`, **run against the full 3258-test suite**, not a
subset:

| mutation | result |
|---|---|
| `_PATH_CHAR` loses `*` (glob / markdown emphasis) | **GREEN** |
| `_PATH_CHAR` loses `+` and `@` | **GREEN** |

Nothing in the repository pins the contents of the character class that decides
how far a path extends — which is exactly the line the finding turns on. The
first mutation would partially *fix* the bold hole while silently breaking glob
handling, and no test notices in either direction.

Restores after both were verified with `bin/perry-restore-check HEAD
viewer/parsers.py`, which compares against `git show HEAD:<path>`.

### The rest of the mutation round

Anchored by line number with an assert on the old text (a non-matching anchor is
a hard error), `__pycache__` cleared and the whole-second boundary waited past
before every run, restore verified against the ref every time. **16 planted, 14
red, 2 green** (the two above). Red: the separator-free-match clause (4500), the
`"/" in token` guard (4493), the strict `>` in the component test (4507), the
`/~$` foreign-root anchors (4404), the placeholder-root test (4410), the
bare-directory shape test (4384), rule 2's fragment gate (4509), the
uncancellable condition (4678), the discount-reporting branch (4476),
`discounted.pop` (4480), `counted = True` (4473), `declared` (4665),
`ESCALATION_UNCANCELLABLE`'s value (4564), the `contradictions` source (4666),
and `_PATH_CHAR` losing `.` (4344).

One correction to method worth recording: my first attempt at the
"one live occurrence outranks its excuses" mutation replaced the `break` with
`pass` and came back green. That is an **equivalent mutant**, not a hole —
`discounted.pop(frag, None)` two lines down does the same work. Re-targeted at
the `pop` itself, it goes red. A green that turns out to be an equivalent mutant
is not a finding, and reporting it as one would have been the same error in the
other direction.

## What would close this

Not my call to make, and I did not write a line of it — but the shape is
structural rather than a classifier, which is what the spec demands: rule 1
should measure the component against a **filename** character class, not
`_PATH_CHAR`. `_PATH_CHAR` is right for "how far does this path run"; it is
wrong for "is this component a longer name". The two questions were collapsed
onto one constant, and the second one is the one the safety decision hangs on.
A test that pins the class — the guard that does not exist today — comes with it.

## What I did not check

- **`work/reference/dispatch.md`** — I read the diff and it states the new rule
  accurately, but I did not verify that every other procedure referencing the
  old green-light doctrine was found. The edit is outside `Files in scope` and
  the author declared it; I am not scoring the overrun.
- **The untriaged tail** — `setup`, `adopt`, `relocate`, `publish`, `rm -rf`,
  `ln -s…`, `$perry_home`, `--force-with-lease`. The `## Bound` excludes them and
  I did not re-derive whether each is true or false; I confirmed only that the
  count and membership are unchanged before and after.
- **The 45 `spec-scope-unscannable` specs.** TASK-284's defect, deliberately out
  of scope. A gate that cannot see a spec's fields is a separate hole and I did
  not measure any interaction between the two.
- **CJK / non-ASCII hook fixtures.** `escalation_pattern`'s `_ESC_WORD` reasoning
  is about Chinese hooks; I exercised only the ASCII fixture and the live hook.
- **`bin/perry-lint`'s use of `matching_escalations`.** I confirmed by reading
  that the function is untouched and that lint still calls it; I did not mutate
  through the lint seam.
- **`Deliverable`-only claim-surface disclaimers.** `TASK-086` and `TASK-109`
  still pass by green-lighting `claims` from `Deliverable`. That is unchanged,
  deliberate ("precision, not reach"), and I did not evaluate whether it should
  also be closed — but it is a second, still-open way for a claim-surface
  mention to be cancelled, and someone should decide about it on purpose.
- **The `test_host_support` flake.** Observed once, green twice; I did not chase
  the root cause.
- **`perry/evidence` files older than this row**, and the events/journal lanes.
  I read no board state and ran no write-side Perry tool.

=== VERDICT ===
task: TASK-290
rung: V4
result: FAIL
criteria: perry/evidence/2026-09/TASK-290-spec.md
checked: worktree provenance (cut at d49964e, 211 behind main; every path read via `git show main:`); main confirmed c506ca5 at start and observed advancing to a61d2e5 mid-round with no file under review changed; full census re-derived independently on `git archive` copies in a scratch dir — 147 specs, 35 fragments, 26 refused before (parsers.py + perry-state reverted to 548f206) vs 16 after; all 13 legitimate refusals (state-schema.json x8, claims x5) confirmed intact; the four changed fragments' discount counts (diagnose 17, evidence/ 17, design/ 5, knowledge/ 2) reproduced; false-PASS closure verified end-to-end for TASK-047/085/139 (pass exit 0 -> refuse exit 3 with `contradictions`) plus TASK-100 gaining `claims`; Deliverable-only green lights confirmed unbroken (TASK-086, TASK-109, TASK-107); each of the 13 cleared specs judged independently from its own source line; two purpose-built control specs run through `bin/perry-state --escalation-scan` in both trees; full `_PATH_CHAR` character class enumerated for the discount; live-occurrence margin measured for all 13 legitimate refusals; 16 mutations planted line-anchored with old-text asserts, __pycache__ cleared, whole-second boundary waited, every restore verified with `bin/perry-restore-check HEAD <path>`; the two greens re-run against the full 3258-test suite; `bash tests/run` (114 modules / 3258 tests) and `bin/perry-lint --root .` (0 errors)
not-checked: work/reference/dispatch.md beyond reading its diff, and whether other procedures still state the old green-light doctrine; the untriaged tail's true/false status (Bound excludes it) beyond confirming membership is unchanged; the 45 spec-scope-unscannable specs and any interaction with TASK-284; CJK/non-ASCII hook fixtures; bin/perry-lint's matching_escalations seam by mutation; whether the still-open Deliverable-only cancellation of a claim-surface fragment (TASK-086, TASK-109) should also be closed; the root cause of the intermittent test_host_support dispatch-limit failure; all board, events and journal state
proof: Two spec files whose `## Files in scope` declares a genuine claim-surface write, each run through `bin/perry-state --root . --escalation-scan <spec>` on a `git archive` copy of main and on the same tree with viewer/parsers.py + bin/perry-state reverted to 548f206. (a) markdown bold: "- **schema/state-schema.json** - the conformance default only." Before: verdict refuse, refuse ["state-schema.json"], exit 3. After: verdict pass, refuse [], exit 0, discounted {"Files in scope": {"state-schema.json": [{"token": "**schema/state-schema.json**", "why": "names-a-longer-file"}]}}. (b) sentence-final period: "- This round rewrites schema/state-schema.json." Before: refuse, exit 3. After: pass, exit 0, token "schema/state-schema.json.". Cause: _PATH_CHAR (viewer/parsers.py:4344) admits 11 non-filename characters (. ~ $ * < > { } @ + -) into the token that _discount_reason measures the enclosing component from, so any of them adjacent to the match makes the component strictly longer than the fragment and rule 1 discounts it; this reaches every fragment with no "/" of its own, including both claim-surface fragments. Corroborated by two green mutations at that same line against the full 3258-test suite (_PATH_CHAR losing "*"; losing "+" and "@"), and by the margin measurement showing 11 of the 13 legitimate refusals survive on exactly one live occurrence.
=== END VERDICT ===
