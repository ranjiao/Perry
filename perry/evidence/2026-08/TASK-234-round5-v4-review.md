# TASK-234 — V4 review, round 5 (the third layer, looked for and not found)

Subject: branch `coding/task-234-conformance-store`, tip `138ad79` (11 commits
on `f783dd5`). Base: `main` at **`f5e7a78`**, where it stood for this whole
round — it did not move while these numbers were taken. Merge probe is
`f5e7a78` + `138ad79` = **`95fef8d`**, cut and run by this reviewer.

Reviewer worked in its own detached worktrees (`scratchpad/v5-main`, `-tip`,
`-mut`, `-probe`) and its own branch (`review/task-234-round5`). The project
under review was never modified; the live checkout at
`/Users/bytedance/proj/Perry` was read only and is clean at `f5e7a78`.
Destructive verification was done on throwaway projects this round planted
under `scratchpad/r5vspace` and `scratchpad/r5vattack`.

**Verdict: PASS.** Rounds 3 and 4 both failed on one sentence of
`bin/perry-conform:360` — *"a wall — every branch here ends in a command the
reader can run"* — one register deeper each time. **I went looking for the
third register with the strongest instrument I could build and there is not
one.** Every handed-back command in both tools, on every branch I could reach,
parses, carries the exact root the caller typed, and runs correctly when pasted
into a real `/bin/sh` on a project path carrying ten shell-hostile characters,
a state file whose own name carries three of them, and a relative `--root`.
Findings below are accuracy and coverage, not correctness; the largest is that
one census number in the RESULT is 50 % too big for the population it names.

---

## 0 · Baselines, counted the way the runner makes hard, measured this session

Sum of the per-module `FAILED (failures=N)`; `errors=N` summed **separately**,
because a module can report `FAILED (errors=1)` with no failures and a
failures-only sum misses it. `grep -c '^FAIL:'` undercounts (`tests/parallel:283`
truncates a red module's stderr to its last 25 lines with nothing visibly
elided). The summary line counts MODULES.

```
grep -oE 'FAILED \(failures=[0-9]+' <log> | grep -oE '[0-9]+$' | paste -sd+ - | bc
grep -oE 'FAILED \(errors=[0-9]+'   <log> | grep -oE '[0-9]+$' | paste -sd+ - | bc
```

| tree | modules | tests | seconds | modules red | **failures** | **errors** | `grep -c '^FAIL:'` (the trap) |
|---|---|---|---|---|---|---|---|
| `main` @ `f5e7a78` | 105 | 3148 | 273.6 | 3 | **4** | **0** | 3 |
| tip `138ad79` | 103 | 3150 | 227.6 | 3 | **4** | **0** | 3 |
| merge probe `f5e7a78` + `138ad79` = `95fef8d` | 105 | 3200 | 244.3 | 3 | **4** | **0** | 3 |

Sequential on one machine, so the seconds are comparable. Red set identical in
all three, by name: `test_diagnose.py` (failures=2), `test_heading_title.py`
(1), `test_kr_progress_provenance.py` (1). The merge is clean (no conflicts)
and introduces no new red. `3148 → 3200` on the probe is **+52**, which is the
tip's own 3150 − 3124-at-fork plus `main`'s 26 — the row's own arithmetic,
reproduced.

**`test_host_support` appears in none of the three runs**, so no number here
depends on the known intermittent being quiet. Recorded rather than netted out.

**md5 bracket** (`git ls-files -z | xargs -0 md5 -q | md5 -q`), before and
after each suite run, `git status --porcelain` **empty** after each:

| run | before | after |
|---|---|---|
| `main` @ `f5e7a78` | `f1d22d04888c206006fa860d492836a3` | `f1d22d04888c206006fa860d492836a3` |
| tip `138ad79` | `fa525b9964445cbfbd2cc6c8ae8d2b42` | `fa525b9964445cbfbd2cc6c8ae8d2b42` |
| probe `95fef8d` | `2c5a005939f4b9a5e0805970838550d1` | `2c5a005939f4b9a5e0805970838550d1` |

The last four commits on the branch (`debdee8`, `35e0336`, `1706a0e`,
`138ad79`) touch **only** `perry/evidence/2026-08/TASK-234-result.md` —
verified with `git show --stat`. So the row's own runs at `35e0336` and the
suite at the tip are runs of the same code.

---

## 1 · The third layer — looked for, with what instrument, and not found

Round 3: the command named the wrong project. Round 4: the command named the
right project in a form that does not parse. Round 5's answer is `_q` plus a
source rule plus a hostile fixture plus `/bin/sh`. The question this round owes
is whether there is a fourth thing wrong with the same sentence.

### 1.1 · Every reachable branch, on a real shell, on my own planted projects

I planted throwaway projects under `scratchpad/r5vspace` (never Perry, never a
worktree of it), drove eight distinct refusal surfaces, extracted every command
with the **shipped** extractor (`tests/handed_back.py § commands_named`),
and pasted each into `/bin/sh -c` with only the tool's own name substituted:

| surface | commands | all parse | root exact | `/bin/sh` |
|---|---|---|---|---|
| gate refusal, legacy record present | 1 | ✓ | ✓ | rc 0 |
| gate refusal, conformant-but-undeclared | 4 | ✓ | ✓ | rc 0 ×4 |
| gate refusal, malformed board | 4 | ✓ | ✓ | rc 0 ×4 |
| `migrate`, fixed-point refusal | 1 | ✓ | ✓ | rc 1 (record still unfixed — correct) |
| `migrate`, unreadable-rows refusal | 1 | ✓ | ✓ | rc 1 |
| `declare` route into the conversion | 1 | ✓ | ✓ | rc 1 |
| `status` with a legacy record | 2 | ✓ | ✓ | rc 0 (+1 `<file>` placeholder) |
| `declare` with a refused file | 1 | ✓ | ✓ | rc 1 |
| `perry-migrate` dry run / apply / `restore --list` | 3 | ✓ | ✓ | rc 0 — **the restore actually ran and put 2 files back** |

Then the whole round trip, end to end, on a project at
`…/My Project (v2) & 'draft' "q" $x; echo hi #1 *`, standing in a *different*
Perry project: the refusal hands back

```
    perry-conform migrate --root '/…/My Project (v2) & '"'"'draft'"'"' "q" $x; echo hi #1 *'
```

the reader fixes the named lines, pastes that line into `/bin/sh` — **rc 0, one
declaration carried with its 2026-08-20 date intact, the markdown deleted, and
the project they were standing in byte-identical.** That is the standard, met.

Two arguments beyond the root also go through `_q` and I exercised both:

* **A state file whose own name is shell-hostile.** `knowledge/research/My
  Notes & 'draft'.md`. The refusal hands back
  `perry-conform declare 'knowledge/research/My Notes & '"'"'draft'"'"'.md' --root '…'`
  and pasting it into `/bin/sh` declares that file, rc 0. (Round 5's own § 1.3
  says this was handed back raw before — it is not now.)
* **A relative `--root`.** Typed `--root '../My Project (v2) & …'` from a
  sibling directory; the refusal hands the relative form back verbatim and it
  works from the same cwd. This is the payoff of carrying the *typed* root
  rather than the resolved one, and it is the case a resolved root would have
  answered differently.

### 1.2 · The two characters the row excludes, measured

**Newline** — the row says this is unmeasured. It is now.

`_q` quotes it correctly. The message becomes two lines, the second
unindented:

```
Fix those lines, then run:
    perry-conform migrate --root '/…/My
Project'
**Nothing was written.**
```

Pasted **whole** into `/bin/sh` this works: rc 0, the reader's project
converted, `.perry/conformance.jsonl` written. Copying only the indented line
gives `unexpected EOF while looking for matching '`, rc 2, and
`commands_named` — being line-based — sees the same truncated half. So the
declared limitation is real and is *milder* than the RESULT states: the
sentence "a command carrying one cannot be handed back on a single line at all"
is true, but the command **is** handed back correctly across two lines and does
run. The residual is a continuation line that does not look like part of the
command.

**Backtick** — reproduced exactly as § 10.12 describes on a root
``/tmp/a `b` c``: the two indented commands parse and carry the root a backtick
and all; the two inline backticked ones truncate at the reader's backtick and do
not parse. The framing — *"the break is in the message's markdown, not in the
quoting"* — is **right**: `_q`'s output is a correct shell word, and what fails
is the single-backtick delimiter. The pin-that-goes-red-when-closed is the same
device the row already uses for TASK-246 and is defensible.

**What the framing gets wrong is the size.** § 10.12 says *"two branches of
`message_for`"*. Resolved off the AST, **eight** handed-back commands in these
two tools are delimited by inline backticks around an interpolated root:

| site | command |
|---|---|
| `bin/perry-conform:460` | `perry-lint{r}` |
| `bin/perry-conform:460` | `perry-conform declare {_q(v.path)}{r}` |
| `bin/perry-conform:876` | `perry-conform migrate{_root_flag(root_arg)}` |
| `bin/perry-conform:890` | `perry-conform declare <file>{_root_flag(root_arg)}` |
| `bin/perry-conform:961` | `perry-lint{_root_flag(root_arg)}` |
| `bin/perry-migrate:689` | `perry-goals commit --migrate{_root_flag(root_arg)}` |
| `bin/perry-migrate:1725` | `perry-tasks render --write{r}` |
| `bin/perry-migrate:1725` | `perry-tasks write --from-board{r}` |

I ran three of the six that are not in `message_for` on a backtick root and
watched them truncate: `perry-conform status` prints two, and a refused
`declare` prints one. `test_a_backtick_in_the_root_is_quoted_and_what_that_costs`
calls `C.message_for` directly, so **only the first two are pinned**. Two of the
unpinned six are the `perry-tasks render --write` / `write --from-board` pair
that § 10.9 is about, and those *write* — so the residual is not uniformly the
harmless shape the paragraph implies.

Harm requires a backtick in a directory name, so this is a correction to the
document, not a FAIL.

---

## 2 · Routing around the choke point — 19 spellings, 8 got through

The RESULT's argument (§ 1.3) is that a choke point alone is a convention, and
that the new part is a source rule that makes the bypass spelling red. I wrote
19 handed-back commands in a file of my own (`scratchpad/r5vattack/bypass.py`),
each reaching the message with a shell-unsafe argument, and ran the shipped
sweep over it.

**11 caught, 8 missed.**

| # | spelling | caught? |
|---|---|---|
| B1 | `--root {root_arg}` in the template (control) | ✔ |
| B2 | `r = " --root " + root_arg`, then `f"…migrate{r}"` | ✘ |
| B3 | `r = " --root %s" % root_arg` | ✘ |
| B4 | `r = "".join([" --root ", root_arg])` | ✘ |
| B5 | `Template(" --root $root").substitute(...)` | ✘ |
| B6 | `r = " --root {}".format(root_arg)` | ✔ (via the literal `{}`) |
| B7 | `--root {_passthrough(root_arg)}` | ✔ |
| B8 | nested f-string `--root {f'{root_arg}'}` | ✔ |
| B9 | module constant `FLAG = " --root "`, then `FLAG + root_arg` | ✘ |
| B10 | `r = " --root " + str(root_arg)` — the name the allow-list blesses | ✘ |
| B11 | `declare {path}{r}` | ✔ |
| B12 | `"    perry-conform migrate --root %s\n" % root_arg` | ✘ |
| B13 | the same with `.format(p=…)` | ✔ |
| B14 | `{root_arg!s}` | ✔ |
| B15 | short flag `-r {root_arg}` | ✔ (as `no root`) |
| B16 | `{_q(root_arg)[1:-1]}` | ✔ |
| B17 | hand-quoted `--root '{root_arg}'` | ✘ |
| B18 | `{FIXES['legacy']} --root {root_arg}` | ✔ |
| B19 | `{flag} {root_arg}` | ✔ |

Two shapes are new relative to the fixture's own 19 and both are structural:

1. **Assemble the flag before the template.** `render()` returns `None` for a
   `BinOp` whose operand is a `Name`, so `" --root " + root_arg` is never
   examined as a template; the surviving `Constant` `" --root "` has no `{`, so
   `FLAG_VALUE` cannot fire. The variable is then interpolated into the command
   phrase, and if it is called `r` — the natural name, and the one this codebase
   uses — `SAFE_INTERP` blesses it by name. Same for `%`, `str.join`,
   `string.Template`, and a module constant. `.format` is the exception, and only
   because its `{}` survives into a literal.
2. **A literal quote in the template truncates the phrase.** `TAIL` is
   `[^`\n'"]*`, so `f"perry-conform migrate --root '{root_arg}'"` is read as the
   phrase `perry-conform migrate --root` — `ROOT` matches the literal `--root`,
   the interpolation is outside the phrase, and the sweep prints **`ok`**.
   Hand-quoting is exactly what someone reaching for "fix the quoting" writes,
   and it breaks on any path containing an apostrophe.

**None of the eight is reachable in the shipped tree.** I checked by AST: no
handed-back template in either tool contains a literal quote, and no flag value
is assembled outside a template. So this bounds the guard, it does not indict
the code. It does mean the RESULT's *"the bypass spelling is not discouraged, it
is RED"* is true of the spellings the fixture plants and not of the class — which
§ 10.13 already says in general terms and can now say with two named shapes.

**M42, M43, M44, re-run, whole of `tests.test_conformance` + `tests.test_migrate`:**

| id | result | distinct failing methods |
|---|---|---|
| M42 (`_root_flag` interpolates raw) | RED | 24 |
| M43 (`{v.path}` un-quoted) | RED | **1** — `test_no_refusal…without_the_root` only |
| M44 (`{tail}` re-glued) | RED | **1** — same |

M43 and M44 are red on the source guard **and nothing else**, exactly as § 6.1
claims. M42's 24 methods matches the row's own figure.

---

## 3 · The parameter removal — every caller checked, none weakened

Signatures by `inspect`, on the tip:

```
declare        (…, run: 'str' = '', *, root_arg: 'str | None') -> 'dict'
migrate_record (project_root: 'Path', *, root_arg: 'str | None') -> 'dict | None'
plan_project   (project_root, state_root, schema, only=None, *, root_arg: 'str | None') -> 'Plan'
rollback_message (point, key, why, allow_changed=None, *, root_arg: 'str | None') -> 'str'
do_restore     (project_root, positional, do_list, as_json, *, root_arg: 'str | None') -> 'int'
fix_tables     (…, rewritten, *, root_arg: 'str | None') -> 'list[str]'
migrate_text   (…, mint, *, root_arg: 'str | None') -> 'Edit'
apply_plan     (plan: 'Plan', schema: 'dict', declare: 'bool' = True) -> 'dict'
render         (plan: 'Plan', applied: 'dict | None') -> 'None'
Plan.root_arg  : str | None, NO default
```

`apply_plan` and `render` genuinely have no root parameter; `Plan.root_arg` has
no default; `plan_project` requires it keyword-only. The round-4 finding
(three silent defaults in `bin/perry-migrate`) is closed on all three.

**Callers, enumerated.**

* `apply_plan` — one production caller (`bin/perry-migrate:2295`); nine test
  call sites. Every one either passes a plan from `Project.plan()` or builds one
  inline with `root_arg=str(p.root)` — the **hostile** root. None passes `None`.
* `plan_project` — two production callers (`:2293`, `:2298`), both from `main`
  with the typed `root_arg`; eight test call sites, all with `root_arg=str(p.root)`.
* `render` — one production caller (`:2315`). The `M.render(...)` cluster in
  `tests/test_md_store.py` is a **different** `render` (`bin/perry_md_store.py`),
  not this one; checked, not assumed.
* **Nothing is stubbed.** The one test that replaces these functions —
  `test_apply_plans_and_writes_while_the_project_lock_is_held` — wraps
  `real_plan` / `real_apply` and delegates, asserting only that the lock is held.
  `test_migrate.py`'s other monkeypatches replace `write_atomic`, `undo` and
  `shutil.copy2`, never the three functions under discussion.

**Does `Plan` carry the *typed* root?** Two mutations, whole of both modules:

| id | mutation | result |
|---|---|---|
| R5-1 | `plan_project` builds `Plan(…, root_arg=None)` | **RED** (4 methods) |
| R5-2 | `plan_project` builds `Plan(…, root_arg=str(project_root))` — the **resolved** path instead of the typed string | **RED** (2 methods) |

R5-2 is the one that matters: on this machine `tempfile` roots resolve
`/var/…` → `/private/var/…`, so the resolved root is a *different string* and
`assert_every_command_carries`'s parse-and-compare catches it. The claim is
pinned, not merely written. My relative-`--root` round trip (§ 1.1) is the
reader-facing reason it should be.

---

## 4 · `tests/handed_back.py`, and assertions that can pass over an empty set

The consolidation is real and the vacuity guard is where it belongs:
`assert_every_command_carries` opens with `assertTrue(named, …)`, so the M56
class — a test asserting over an empty extraction — cannot recur at any of its
seven call sites. Both `_INDENTED` and the sweep's `CUE` are `[ ]{2,}` now, and
**M56 is red** (reproduced, § 5).

I diffed `tests/` across `f783dd5..138ad79` for removed assertions. The only
removals are the two `assertIn`/`assertRegex` pairs in `test_migrate.py` that
were **replaced** by extraction plus `assert_every_command_carries` — a
strengthening. No assertion was deleted or relaxed.

Four things worth naming, none a defect:

1. **Two hand-written extractors survive beside the shared one**, both in
   `tests/test_conformance.py`:
   `test_every_non_conformant_state_names_a_command_that_exists` (line 384,
   `line.strip().startswith("perry-")`) and
   `test_a_backtick_in_the_root_is_quoted_and_what_that_costs` (line 2477,
   `l.startswith("    ")`). The row's own argument — *"the rule lives here so
   there is one of it"* — is carried out for the root assertion and not for
   these. Neither is load-bearing about the root; the second is *why* § 1.2's
   residual is measured on two sites and not eight.
2. **`test_the_sweep_reports_every_planted_defect_it_claims_to_see` would pass
   over an empty `regions()`.** Its `assertTrue(found)` guards the sweep's
   output, not the fixture's inventory: if `regions()` returned `[]` the
   per-spelling loop would be empty and the test green. It is saved by its
   sibling `test_the_recall_the_result_quotes_is_the_recall_measured_here`,
   which pins `(seen, missed) == (18, 1)`. A pair, not a test — worth knowing
   before either is edited.
3. **The non-vacuity floor is 20 and the actual count is 21.** One command of
   slack in `test_no_refusal_in_perry_conform_names_a_command_without_the_root`.
   Real, but thin.
4. **Nothing asserts the fixture root is hostile.** See § 6.

---

## 5 · Mutations — 57/57 reproduced independently, plus 16 of my own

**The row's whole harness, re-run by me**, in `scratchpad/v5-tip`,
`python3 tests/mutate_task_234.py`: **`57/57 mutations reddened their named
test`**, no `✗`. Tree digest `fa525b9964445cbfbd2cc6c8ae8d2b42` before and
after, `git status --porcelain` empty. So `57/57` is now a number two people
have seen.

**Sixteen of my own**, anchored on exact text with a uniqueness assertion,
`__pycache__` cleared and the whole-second boundary crossed either side,
`PYTHONDONTWRITEBYTECODE=1`, **GREEN asserted before mutating**, and **restored
by writing back `git show HEAD:<file>` — the git object, never bytes my harness
wrote** — with `git status --porcelain` re-checked empty after each. Target for
every one: the whole of `tests.test_conformance` + `tests.test_migrate`.

| id | mutation | result | methods |
|---|---|---|---|
| M42 | `_root_flag` interpolates the root raw | RED | 24 |
| M43 | `{v.path}` un-quoted in the STALE branch | RED | 1 (source guard) |
| M44 | `{tail}` re-glued to the DRIFTED command | RED | 1 (source guard) |
| R5-1 | `Plan` gets `root_arg=None` | RED | 4 |
| R5-2 | `Plan` gets the **resolved** root, not the typed one | RED | 2 |
| R5-3 | `rollback_message` stops quoting the restore-point stem | RED | 1 (source guard) |
| R5-4 | the `undo with:` line stops quoting the run id | RED | 1 (source guard) |
| R5-5 | `render`'s `r = _root_flag(None)` | RED | 1 |
| R5-6 | `see them with \`perry-lint\`` drops the root | RED | 1 (source guard) |
| R5-7 | the inline `declare` in the errors branch drops the root | RED | 1 (source guard) |
| R5-8 | the legacy-record branch's `migrate` drops the root | RED | 1 (source guard) |
| R5-9 | `do_restore`'s listing command drops the root | RED | 2 |
| R5-10 | `assert_every_command_carries` reverted to round 4's substring rule | RED | 20 |
| R5-11 | the sweep's `TAIL` stops excluding the backtick | **GREEN — SURVIVOR** | 0 |
| R5-12 | the sweep's `CUE` loses its indentation branch | RED | 3 |
| R5-15 | `_q` quotes with **double** quotes, inner quotes escaped | RED | 5 |
| R5-14 | the fixture root made friendly, alone | GREEN (expected — recorded, § 6) | 0 |
| R5-16 | the fixture root made friendly **and** round 4's defect put back | RED | **2** |

Six of these are worth a sentence.

**R5-15 is the mutation the RESULT says it could not construct.** § 6.1 ends
*"I did not construct a mutation caught by only that layer, and say so rather
than claim one."* Quote with `"` instead of `'` and escape the inner quotes:
`shlex.split` does not expand `$`, so the parse-based helper reads the exact
root and **all sixteen invocations stay green**; the source guard stays green
because `_q` is still called. `/bin/sh` expands the fixture root's `$x` to
nothing, addresses a path that does not exist, and
`test_the_named_command_converts_the_readers_project_from_elsewhere` goes red.
Four incidental exact-text assertions elsewhere also go red (they read
`perry-conform declare BOARD.md` as a substring, which double-quoting breaks),
so it is not *uniquely* the shell layer — but it is red on the shell layer and
**invisible to both of the layers the three-layer argument is about**. The
`/bin/sh -c` step earns its keep, measured.

**R5-16 is the strongest evidence for the fix's shape, and it is the row's own
argument confirmed.** Make the fixture root friendly and put round 4's shipped
defect back: 24 red methods collapse to **2** — and the two that remain are
`test_no_refusal_in_perry_conform_names_a_command_without_the_root` (the source
rule, via `FLAG_VALUE`) and `test_a_backtick_in_the_root_is_quoted_and_what_that
_costs` (which builds its own root and does not use the fixture). So the claim
that a source rule is needed *because a choke point is a convention* is not an
argument here, it is a measurement: with every runtime layer disarmed, the
source rule still catches the round-4 FAIL.

**R5-11 is a survivor and it is the sweep's own ok/bad boundary again.**
Removing the backtick from `TAIL`'s excluded set — so a phrase runs past its
closing backtick into the following prose — leaves both modules green. That is
the same shape as the round-4 reviewer's R-N8 which this round closed for
`ROOT`, `SAFE_INTERP`, `IS_WHOLLY_A_COMMAND` and `FLAG_VALUE` (M45–M48): the
*phrase boundary* has no positive control. `tests/fixtures/handed_back_spellings.py`
is the natural place for one — a planted command followed by prose that would be
swallowed. Not charged as a defect: the boundary is correct today, and the
mutation makes the sweep noisier rather than blinder.

**R5-10 is a flawed probe and I say so rather than count it.** I meant to test
whether the *parse* half of the assertion is load-bearing; what I actually
measured is that round 4's `assertIn(f"--root {root}", cmd)` is now
**incompatible** with the corrected output — `_q` emits
`'…& '"'"'draft'"'"' …'`, which does not contain the raw root as a substring.
That is a real datum (the two rules are genuinely different, not one weaker than
the other) but it is not the datum I was after.

---

## 6 · The fixture is the guard, and nothing guards the fixture

`tests/handed_back.py § HOSTILE_ROOT_NAME` is
`My Project (v2) & 'draft' "q" $x; echo hi #1 *`. Verified character by
character: space, `(`, `)`, `&`, `'`, `"`, `$`, `;`, `#`, `*` — **ten**
present; backtick and newline absent, both declared and both measured in § 1.2.

**No fixture quietly uses a friendly root.** Both `Project` classes
(`tests/test_conformance.py:126`, `tests/test_migrate.py:177`) build under it,
and `dirname` is never passed by any caller — grepped, not assumed. The three
other tempdir fixtures in `test_conformance.py` (`copy_of`,
`TestOneDefinitionOfTheShape`, `TestTheGateSpeaksEveryDocumentLanguage`) do use
friendly roots and none of them asserts anything about a handed-back command;
checked one by one.

**But the hostile name is a bare string constant with no assertion on it.**
R5-14: replace it with `"proj"` and both modules stay green. R5-16: do that
*and* put round 4's FAIL back, and 24 red signals become 2. So a future edit
that "tidies" the fixture name — the same instinct that produced
`tempfile.TemporaryDirectory()` in round 4 — silently disarms twenty-two of the
twenty-four signals, and the suite says nothing.

This is § 11's own table, one row further on: round 4's entry reads *"the input
never exercised the failure"*, and the answer was a hostile default in the
fixture. A hostile default that nothing asserts is a hostile default that can be
edited back. The exposure is **bounded** — the source guard and the backtick
test survive it, which is exactly what round 4 did not have — and the fix is one
line beside the constant, the same shape as
`assertIn(b"\r\n", …, "the fixture is not CRLF, so this measures nothing")`
already in `test_a_crlf_record_converts_and_the_wording_does_not_say_byte`.

Recorded, not charged.

---

## 7 · The two claims re-derived

### 7.1 · The CRLF regex — **both halves hold**

I reconstructed the round-4 reviewer's nine plausible overclaims and put them to
both regexes:

| regex | catches |
|---|---|
| round 4's `byte[- ]for[- ]byte(\s+identical)?\s+(to\s+)?what` | **3 / 9** |
| round 5's widened one | **9 / 9** |

and the **widening that was not taken** (`byte-for-byte` + any short run of
characters + the object) also catches 9/9 and fires on exactly the two sentences
the RESULT names, no more:

```
bin/perry-conform : 'byte-for-byte" was not what'      ← the CORRECTING comment
bin/README.md     : 'byte for byte **while the file'   ← perry-config's TRUE claim
```

The shipped regex fires on nothing in either file. The positive pin
`"ine-for-line, not byte-for-byte"` occurs **exactly once** in each file, so
M39/M57 are not vacuous. `3/9 → 9/9` and the rejection-on-measurement are both
correct as written.

### 7.2 · The census outside these two tools — **the defect counts are right, the headline is not**

§ 10.14 prints, under *"The round-5 rule over all twelve other `bin/perry-*`
tools"*:

```
63 handed-back command(s), 232 mention(s);
25 handed back without the caller's root, 19 interpolating a value raw
```

Re-derived with the shipped sweep over the twelve Python tools that are not
`perry-conform` or `perry-migrate` (four `bin/perry-*` are shell scripts and the
sweep cannot parse them):

```
42 handed-back command(s), 208 mention(s);
25 handed back without the caller's root, 19 interpolating a value raw
```

**`63 − 42 = 21` and `232 − 208 = 24` are exactly `bin/perry-conform` +
`bin/perry-migrate`'s own contribution**, which I measured separately
(`21 handed-back, 24 mentions, 0 rootless, 0 unquoted`). So the headline pair is
a count over **fourteen** tools carried into a sentence about **twelve**. The
population of the follow-on row is **42**, not 63 — the class outside these two
tools is a third smaller than the document says. The row's own § 11 has a name
for this: *a number whose subject moved*.

Everything else in the paragraph reproduces exactly:

* **25 rootless**, split `perry-tasks` 11, `perry-task` 9, `perry-decide` 2,
  `perry-goals` 1, `perry-lint` 1, `perry-state` 1 — confirmed per tool.
* **19 raw interpolations**, split **3 in a genuine command phrase (all in
  `bin/perry-task`) / 16 `FLAG_VALUE` in prose** — confirmed by listing them.

One correction inside the correction. Of the three "genuine" ones, **two
interpolate the command's verb, not an argument**:

```
bin/perry-task:2307  'perry-tasks {verb}write --from-board'
bin/perry-task:3859  'perry-task {ʼdoneʼ if want == ʼdoneʼ else ʼdropʼ}'
```

Neither can carry a space, so neither is the round-4 defect. Only
`bin/perry-task:734` — `perry-task cadence-done {id} --evidence <path>` — is a
raw *value*. The genuine count is **1**, not 3, and the over-report rate is
18/19 rather than 16/19. The paragraph's conclusion (the rule is too blunt to
extend past these two tools without sharpening) is if anything strengthened.

---

## 8 · What else was checked and holds

* **The sweep over the two tools is at zero on both rulings**, rc 0, and its
  census over `bin/perry-conform` alone reproduces (14 handed-back / 16
  mentions / 0 / 0).
* **`_q` is genuinely the only quoting call.** `shlex.quote` appears in
  `bin/perry-conform § _q` and nowhere else in `bin/` outside `_q`'s two
  callers; `bin/perry-migrate § _q` imports it rather than re-typing it.
* **`root_arg` is the raw typed string.** `main` reads it off `argv` and
  `_roots()` resolves a *separate* value; the two never cross. Confirmed by
  reading both `main`s and by R5-2.
* **The M56 disagreement is closed on both sides.** `_INDENTED` and `CUE` are
  both `[ ]{2,}`; `do_restore`'s three-space listing is extracted (I saw it come
  out of a live run) and M56 is red.
* **No new red at the merge**, and nothing this branch adds trips `main`'s new
  `tests/test_tree_guard.py`: the probe run is 105 modules with the same three
  red as `main`, and the tree-guard section reports *"nothing under … moved"* in
  all three logs.
* **`perry-conform status`'s `<file>` and `perry-migrate restore <run-id>` are
  placeholders**, not commands to paste; the sweep's `_ARG` admits `<name>`
  deliberately. I did not run them and do not count them as defects.

---

## 9 · What I did NOT verify

1. **`bin/perry-lint`'s 22 fix hints** (§ 10.10). Not re-measured, in either
   round.
2. **The `_plan_task_store` and `fix_tables` refusals end to end.** Same gap the
   row declares in § 10.9: the flag is in the template and the template is
   guarded (M52, M53, R5-6 … all red), but I did not build a project whose task
   store disagrees with its board, nor one whose `Commitments` table carries the
   pre-split `By when` column, and read the message off a running tool. I did
   confirm those two commands truncate on a backtick root (§ 1.2) by reading the
   template, not by triggering the refusal.
3. **A `.perry/conformance.md` hand-maintained by anyone but Perry** (§ 10.3).
   Not sampled by round 3, round 4 or me. Still a substitute.
4. **The five remaining branches of the backtick residual**, beyond confirming
   three of them truncate and resolving all eight off the AST.
5. **`schema/state-schema.json`, `reference/config.md`, `viewer/parsers.py`**
   beyond reading the diff, the `inspect` signatures, and the mutations above.
   The 57/57 harness covers `viewer/parsers.py`'s eleven guards; I did not read
   that file's diff line by line.
6. **`tests/test_procedures_call_the_tool.py`, `test_one_header_rule.py`,
   `test_header_index_is_the_only_fold.py`** — touched by the branch, covered
   only by the suite runs and by M19/M20 in the harness.
7. **A reader who is not in a Perry project at all** (§ 10.11). Unmeasured here
   too.
8. **The board and `perry/tasks.jsonl`.** Untouched and unread; the PMO owns
   them. No identifiers were minted.
9. **Anything under `.perry/events.jsonl`.** No write-side Perry tool was run
   against the repository or any worktree of it. `perry-conform declare` and
   `perry-migrate apply` were run **only** inside throwaway projects this round
   planted under `scratchpad/r5vspace`. `perry-tasks render --write` and
   `perry-tasks --dry-run` were never run anywhere.

---

## 10 · Verdict

**PASS.** This row merges.

The round-4 FAIL is closed and closed at the right level. `_q` is one choke
point and every argument of every handed-back command in both tools goes
through it — the root, the file path, the restore-point stem, the run id. The
source rule reaches the choke point's own body, where no command-phrase rule
can, and **R5-16 proves it is not decoration**: with the hostile fixture
disarmed, the source rule is one of only two things left that catch round 4's
defect. The hostile fixture root carries ten shell-hostile characters, no
fixture quietly opts out of it, and the end-to-end proof pastes what the
message printed into a real `/bin/sh` — a layer **R5-15** shows is not
redundant with the other two.

I went looking for the third register and could not find one. Eight refusal
surfaces, every command extracted by the shipped extractor and pasted into
`/bin/sh`, on a hostile project path, on a state file whose own name is
hostile, and on a relative `--root`: all parse, all name the reader's own
project, all do what the sentence says. The two excluded characters are
measured — the newline case works when the whole two-line block is pasted, which
is better than the document claims, and the backtick case is a markdown
delimiter problem, correctly diagnosed. `57/57` is reproduced by a second party
with the tree digest bracketed. The three trees read 4 failures and 0 errors
with the same three red modules by name, and the merge is clean.

Five things for the record, none blocking, in descending order of how much
they would cost the next reader:

1. **§ 10.14's headline census is over fourteen tools, not twelve** (§ 7.2).
   The population of the follow-on row is 42 handed-back commands, not 63. The
   two defect counts (25, 19) and both splits are right.
2. **§ 10.12 sizes the backtick residual at two and it is eight** (§ 1.2), of
   which only the `message_for` pair is pinned, and two of the unpinned six are
   the commands that write.
3. **The hostile fixture root has no assertion on it** (§ 6). One line beside
   the constant would close it, and the row already writes exactly that line for
   its CRLF fixture.
4. **The sweep's phrase boundary has no positive control** (R5-11), and eight of
   nineteen fresh bypass spellings get past the source rule (§ 2) — two of them
   shapes the fixture does not plant. None is reachable in the shipped tree; the
   recall number is a bound on a self-chosen population and § 10.13 should say
   so with those two shapes named.
5. Of the "3 genuine" raw interpolations outside these tools, **two interpolate
   a verb rather than an argument** (§ 7.2); the genuine count is 1.

---

*checked:* every suite run, mutation and probe was performed in this reviewer's
own detached worktrees (`scratchpad/v5-main`, `-tip`, `-mut`, `-probe`), never
in `/Users/bytedance/proj/Perry`, which is clean at `f5e7a78` and was read
only. Destructive verification was done on throwaway projects under
`scratchpad/r5vspace`; the sweep's bypass file lives in `scratchpad/r5vattack`
and is not in any Perry tree. Every mutated file was restored by writing back
`git show HEAD:<file>` — the git object, not bytes this harness wrote — with
`git status --porcelain` re-checked empty and the whole-tree `md5` compared
against the value taken before the first mutation (`fa525b9964445cbfbd2cc6c8ae8d2b42`, both sides). One mutation pair (R5-16) left a file dirty when its first restore
asserted cleanliness before the second had run; both files were restored from
their git objects and the tree digest re-checked before anything else ran. No
`git checkout`, `stash`, `reset` or `clean` was run in any tree. No write-side
Perry tool was run against the project or any worktree of it. `perry/BOARD.md`
and `perry/tasks.jsonl` were not touched and no identifiers were minted.
