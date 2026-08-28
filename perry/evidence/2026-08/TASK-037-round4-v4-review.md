# TASK-037 — V4, round 4

Criteria: `perry/evidence/2026-08/TASK-037-spec.md`. Under review: `bin/perry-goals`
as a writer, and `viewer/tables.py`.

All destructive work was done on **copies** of the repository under
`…/scratchpad/perry-copy` and `…/scratchpad/r4-037/copy2` (rsync of the working
tree, `.git` and `__pycache__` excluded). Every probe project was a throwaway
temp directory created by the reviewer, never a Perry checkout. Against the
repository under review the only tools run were read tools — `perry-task list
--json`, `perry-lint`, `git log/diff/status` — plus `bin/perry-goals commit`
pointed at `--root <tmpdir>`, and `python3 -m unittest tests.test_diagnose` once
to separate a copy artefact from a real red.

**The tree moved under this round.** `HEAD` advanced (`a14ec19` → `75e9196`) and
`bin/perry-goals`, `tests/test_goals_writer.py`, `perry/BOARD.md`,
`perry/journal/2026-08/2026-08-18.md` and `.perry/events.jsonl` all became dirty
in the working tree while it ran — another agent is rewriting the `CLOCK_RE`
block (`bin/perry-goals:870-1008`, TASK-067's clock rule). That hunk does not
touch anything below, and the load-bearing finding was **re-measured against the
working tree as it stood at the end of the round**. Line numbers below are that
file.

---

## 0 · The verdict in one command

The five claimed fixes are, at the level of `viewer/tables.py`, **real**. One
rule, four writers, eleven characters, all agreeing — measured, and every fix
reddens under mutation. And the tool cannot tell a user any of it, because the
commit that unified the rule also copied `perry-task`'s flag-naming block into a
scope that has no `args`:

```
$ perry-goals commit --id ops/1 --promise $'a\n\nb' --root <tmp>
tables.UnrenderableCell: cell 0: contains a line break — a markdown table row is one line

During handling of the above exception, another exception occurred:

  File ".../bin/perry-goals", line 1556, in <module>
    _v = getattr(args, _name, None)
NameError: name 'args' is not defined
```

Round 3's F3 was *"`splice_cell` raises `Refused`, which is not defined in that
module — the user gets a `NameError` where a refusal belongs."* Round 4 moved
the undefined name from `viewer/tables.py:193` to `bin/perry-goals:1556`. The
command round 3 printed as its reproduction — `commit --close ops/1
--discharged-by done` on a Commitments table with no `Status` column — still
ends in `NameError`. Only the name changed.

---

## 1 · The enumeration (rule 1)

### 1a · Every flag on every subcommand of `perry-goals` that reaches a cell

From `parse()` (`bin/perry-goals:1364-1381`) and `cmd_commit`, the flags whose
value lands in a markdown cell are exactly six:

| flag | column | create | `--id` amend | `--close` | `--miss` |
|---|---|---|---|---|---|
| `--track` | Track | ✔ | — | — | — |
| `--promise` | Promise | ✔ | ✔ | — | — |
| `--to` | To whom | ✔ | ✔ | — | — |
| `--by` | By when | ✔ | ✔ | — | — |
| `--discharged-by` | Discharged by | ✔ | ✔ | ✔ | — |
| `--reason` | Discharged by | — | — | — | ✔ |

Eight distinct write paths. `--id`, `--close`, `--miss`, `--actor`, `--root`,
`--level` carry values that never reach a cell (`--actor` reaches the event log
only).

### 1b · Every character class that could end a row

`str.splitlines()` breaks on eleven boundaries. All eleven were run, plus
`\x1f` (unit separator — whitespace to Python, **not** a `splitlines()`
boundary), through all four value-writers in `viewer/tables.py`:

| | `render_row` | `check_cell` | `append_cell` (trailing `\|`) | `append_cell` (no trailing `\|`) |
|---|---|---|---|---|
| `\n` `\r` `\v` `\f` `\x1c` `\x1d` `\x1e` `U+2028` `U+2029` `\x85` | refuse | refuse | refuse | refuse |
| `\x1f` | ok | ok | ok | ok |

Ten refusals and one acceptance, unanimous. Round 3's F1 — six characters
refused on create and accepted on amend — **is fixed**, and fixed by enumeration
from the language rather than from the bug report: `\x1d` and `\x1e` were in
neither round 3's list nor the fix's own `EXOTIC` table, and they are handled
because `line_break_at` asks `splitlines()` rather than listing characters.

At CLI level, 8 write paths × 11 characters = 88 invocations. **All eleven
characters produce the same answer on all eight paths**, and for the ten
refusing characters that answer is a `NameError` traceback (§ 2).

### 1c · "a value the create path and the amend path answer differently about"

Every shared flag, run on create and on `--id` amend, over ten value classes
(whitespace-only, empty, tab-only, NBSP-only, `" pad "`, `a|b`, `a\|b`,
`a\x1fb`, `a\tb`, 300 characters). Each run on its own throwaway project, the
resulting cell read back with `viewer/tables.split_row`:

| flag | disagreement found |
|---|---|
| `--promise` | none — refused on both for all four blank forms, identical stored bytes for the other six |
| `--to` | none |
| `--by` | none — `check_by_when` runs on both branches |
| `--discharged-by` | none — **clears on both** for `''`, `'   '`, `'\t'`, `'\xa0'` |

So claim (4) holds and the `--discharged-by` exclusion the prompt asked about
holds in both directions: `--discharged-by ''` still clears, on create and on
amend alike. See F6 for what is *not* true about it.

### 1d · The category outside `Under review`

`grep -c UnrenderableCell`: `perry-task` 2, `perry-goals` 2, **`perry-decide` 0,
`perry-conform` 0, `perry-migrate` 0** — and all three call `render_row`. The
translation from "a value a row cannot carry" to "a refusal" exists in two of
the five writers. Measured on a throwaway project:

```
$ perry-decide new test-slug --title $'first\n\nsecond' --type architecture   → rc 0
DECISIONS.md:  | [ADR-001](decisions/ADR-001-test-slug.md) | first |  |  | — |
```

Title truncated at the break, `Type` and `Date` blanked, exit 0, nothing said.
Reported as the category, **not** as this row's proof — `perry-decide` is not in
this round's `Under review` line and I did not chase the mechanism.

---

## 2 · F1 — every `UnrenderableCell` refusal in `perry-goals` is a traceback

`bin/perry-goals:1537-1565` is a **module-level** `try/except` around
`sys.exit(main(sys.argv[1:]))`. `args` is a local of `main()`
(`bin/perry-goals:1464`). The handler reads it at `:1556`.

`perry-task`'s twin (`bin/perry-task:4054-4079`) is the same block **inside**
`main()`, where `args` is in scope and `args.as_json` is honoured. `git show
56b1b54` — the commit that made claimed fixes (1) and (3) — replaced
`perry-goals`' working one-line

```python
print(f"perry-goals: refused — the value {exc.value[:60]!r} …")
```

with `perry-task`'s twelve-line loop, copied verbatim into a scope that has no
`args`. Before that commit the refusal printed; after it, it crashes.

Measured (throwaway projects, current working tree):

| path | value | rc | stdout | stderr |
|---|---|---|---|---|
| create `--promise` | any of the ten | 1 | empty | 2-frame traceback, `NameError` |
| create `--to` | " | 1 | empty | " |
| create `--discharged-by` | " | 1 | empty | " |
| amend `--promise` / `--to` / `--discharged-by` | " | 1 | empty | " |
| `--close --discharged-by` | " | 1 | empty | " |
| `--miss --reason` | " | 1 | empty | " |
| `--close` / `--miss`, table with no `Status` column | — | 1 | empty | " |
| any ragged row via `--miss` | — | 1 | empty | " |
| **all of the above with `--json`** | — | 1 | **empty** | " |

The file is unchanged in every case and no event is appended, so this is a bad
refusal rather than a bad write. It is still the thing `Refused`'s own docstring
forbids — *"A refusal is a first-class outcome, not a crash"* — and an agent
reading `--json` gets rc 1 with no payload for the whole `UnrenderableCell`
class, which is round 3's F6 unfixed and made worse.

**Category enumerated.** Every `if __name__ == "__main__"` block in `bin/` was
read. `perry-goals` is the only tool whose module-level handler references a
name defined inside `main()`. One instance, and it is the one under review.

## 3 · F2 — the suite cannot distinguish a refusal from this crash

`tests/test_goals_writer.py:1155`:

```python
self.assertIn("line break", (out.stderr + out.stdout).lower())
```

The traceback's own last line is `tables.UnrenderableCell: cell 0: contains a
line break — a markdown table row is one line`, so the assertion passes **on the
crash**. `test_the_amend_paths_refuse_what_create_refuses` asserts `rc == 1` and
that the file is byte-unchanged; a crash satisfies both.

**Mutation M-G** (copy only): the handler's `print` (`bin/perry-goals:1562` live, `:1502` on the copy) → `print("perry-goals:
ZZZZ", …)`, destroying the refusal message entirely.
`tests.test_goals_writer` **GREEN** (75 tests), `tests.test_one_line_break_rule`
**GREEN** (7 tests). `perry-goals`' `UnrenderableCell` refusal output has no
coverage at all. That is why F1 shipped, and it is the same sentence round 3
wrote about `append_cell`: *"deleting the line left all 1310 tests green, so it
had no coverage either."*

## 4 · F3 — the flag-naming test tests the other tool, and writes to the repo

`tests/test_one_line_break_rule.py § TestTheRefusalNamesTheFlag` is the only test
of the flag-naming feature. It shells **`bin/perry-task`**:

```python
subprocess.run([sys.executable, str(ROOT / "bin" / "perry-task"), *args],
               capture_output=True, text=True, cwd=ROOT)
```

Two things follow.

1. The copy of the handler that works is the one under test; the copy that
   `NameError`s is untested. A test named for the rule, placed in the module
   named for the rule, covering one of the rule's two implementations — which
   is the defect class this whole task is about, in the test file written to
   close it.

2. `cwd=ROOT` with **no `--root`**, running `perry-task add` and `perry-task
   next TASK-038`, which are writers, against the Perry repository itself. It
   is safe only while the guard it is testing works. Under **mutation M-A**
   (`viewer/tables.py:49` → `if False:`) on my copy it wrote

   ```
   | TASK-084 | x
   y | Coding Agent | not_started | — | — |  |  |
   ```

   into the copy's `perry/BOARD.md` and overwrote TASK-038's `Next action`
   cell with `x\ny`, destroying ~2 KB of real prose; three unrelated modules
   (`test_task_writer`, `test_role_cards`, `test_decoration_changes_nothing`)
   then went red on a board that had been corrupted by the test. Its own
   docstring records that the same probe *"wrote three junk rows onto the live
   board"* once already. `work/reference/review-constraints.md` says plant into
   a copy; this test plants into the checkout, permanently, on every run.

## 5 · F4 — the refusal names the wrong flag, or no flag

Behind the `NameError` there is a second defect. Verified on a copy with a
one-line reviewer scaffold (`args = parse(sys.argv[1:])` inserted at module
scope so the handler can run at all — stated because it is a write, and it was
made only in the copy):

```
commit --miss ops/1 --reason BAD                    → refused — --reason was given …       ✔
commit --miss ops/1 --reason BAD --promise BAD      → refused — --promise was given …      ✘ wrong flag
commit --track ops --promise ok --to BAD --by …     → refused — was given …                ✘ no flag
commit --id ops/1 --to BAD                          → refused — was given …                ✘ no flag
commit --id ops/1 --by '5 days<VT>ago'              → refused — was given …                ✘ no flag
```

The comment at `bin/perry-goals:1550` says *"Exact match only — a near-miss
would name the wrong flag, which is worse than naming none."* Exactness is not
the collision that matters: **two flags carrying the same string** is, and then
the fixed list order decides. `--miss` never reads `--promise`, and the message
tells the user to fix it.

The list itself is `perry-task`'s vocabulary copied verbatim:

```python
("next", "title", "deliverable", "verification", "evidence",
 "promise", "reason", "discharged_by", "note", "risk", "question", "answer")
```

Nine of those twelve are not flags of `perry-goals` at all. Three of
`perry-goals`' six cell-carrying flags — `--track`, `--to`, `--by` (§ 1a) — are
missing, so a third of its write surface prints the ungrammatical `refused —
was given 'a\x0bb', which contains a line break`. `exc.field` is the declared
fallback (`UnrenderableCell.naming`, `viewer/tables.py:108`) and **no call site
in either tool ever sets it** — `grep -n '\.naming(' bin/ viewer/` returns
nothing — so the fallback is dead and the message loses its subject.

## 6 · F5 — `--json` still gets nothing (round 3's F6, unfixed)

Not among the five claimed fixes, and still true, and now returning a traceback
instead of a sentence. `bin/perry-goals:1544` cannot honour `args.as_json`
because it cannot see `args`. `perry-task:4077` does. Every other refusal on
`perry-goals` emits `{"refused": …}` on stdout; this one class does not.

## 7 · F6 — the `--discharged-by` exclusion is not pinned

The row claims *"`--discharged-by` is deliberately excluded and a test pins that
exclusion."* The behaviour is correct (§ 1c). The pin does not exist.

**Mutation M-F** (copy only): the swept-flag tuple (`:1312` live, `:1252` copy) →

```python
for _flag, _column in (("promise", "Promise"), ("to", "To whom"),
                       ("discharged_by", "Discharged by")):
```

which removes the only way to undo a mistaken discharge. Targeted set
(`test_one_line_break_rule`, `test_amend_matches_create`, `test_goals_writer`,
`test_row_integrity`): **all GREEN**. Full suite: 42 modules, 1363 tests, the
same four copy-artefact reds it has without the mutation and **no new red**. A
deliberate exclusion with no test is an accident waiting to be tidied away by
the next round that reads the guard and notices one flag missing.

---

## 8 · Mutations run (rule 2)

Copy only. Each edit anchored by line number, applied and reverted by index —
never `str.replace` — `__pycache__` cleared before every run and the whole-second
boundary waited past. The copy was diffed against the live file after the
scaffold was removed and came back byte-identical.

| # | site | edit | result |
|---|---|---|---|
| M-A | `viewer/tables.py:49` | `if False:` | **RED** — one_line_break_rule 17F, goals_writer 2F, row_integrity 6F |
| M-B | `viewer/tables.py:49` | restore the old `"\n" in / "\r" in` rule | **RED** — one_line_break_rule 12F (only that module) |
| M-C | whitespace guard `if` (`:1314` live, `:1254` copy) | → `if False:` | **RED** — goals_writer 2F |
| M-D | `bin/perry-goals:241` | `append_separator_cell` assumes a trailing pipe | **RED** — amend_matches_create 1F |
| M-E | `viewer/tables.py:236` | `raise UnrenderableCell` → `raise Refused` | **RED** — one_line_break_rule 1E |
| M-H | `viewer/tables.py:269` | put round 3's `.replace("\n"," ")` back into `append_cell` | **RED** — row_integrity 1F |
| M-F | swept-flag tuple (`:1312` live, `:1252` copy) | sweep `--discharged-by` in | **GREEN** → F6 |
| M-G | handler `print` (`:1562` live, `:1502` copy) | destroy the refusal message | **GREEN** → F2 |

M-A through M-E and M-H are the five claimed fixes plus round 3's F2, and every
one of them is genuinely held by a test. M-B is the sharper of the pair: putting
back exactly the rule `check_cell` used at round 3 reddens only the new module,
which is what a purpose-built regression test is supposed to look like.

## 9 · What holds (rule 3 — re-derived, not inherited)

- **One line-break rule, one function.** `line_break_at` (`viewer/tables.py:30`)
  is called by `render_row:151`, `check_cell:180`, `splice_cell` via
  `check_cell:247`, and `append_cell` on both branches (`:279` re-render,
  `:280` append). Unanimous over all eleven `splitlines()` boundaries plus
  `\x1f`. Round 3's F1 is fixed and its enumeration is wider than the report
  that caused it.
- **Round 3's F2 is fixed.** `viewer/tables.py:269` is `raw = str(value).strip()`
  — no collapse — and both branches escape exactly once:
  `append_cell("| a | b |","p|q")` and `append_cell("| a | b","p|q")` both yield
  `| a | b | p\|q |`, reading back as `p|q`.
- **Round 3's F4 is fixed.** Whitespace-only refused on both paths for
  `--promise` and `--to`, with the file byte-unchanged.
- **Round 3's F5 is fixed.** A table with a leading pipe and no trailing pipe
  widens to header 7 / separator 7 / rows 7, and the widened separator is still
  a separator.
- **`splice_cell` out of range raises a defined type** (`UnrenderableCell`),
  M-E red.
- **`--discharged-by ''` still clears** on create and amend — measured, four
  blank forms, both paths.
- **`python3 bin/perry-lint`** on the repository under review: `✓ clean`, rc 0,
  13 files declared conformant.
- **Full suite on the copy**: 42 modules · 1363 tests · ~102 s. Four modules red
  — `test_diagnose`, `test_role_cards`, `test_decoration_changes_nothing`,
  `test_task_writer` — all of which read the repository's own state.
  `test_diagnose` passes on the live tree and fails on the copy, and the other
  three were reddened by M-A through the mechanism in F3; none is a TASK-037
  defect.

## 10 · Latent, not blocking

`line_break_at`'s second clause is `str(c).strip("\n\r") != str(c)`, so a
*trailing* boundary is caught for LF and CR and for none of the other nine:
`line_break_at(["a\n"])` → `0`, `line_break_at(["a\v"])` → `None`. Unreachable
today because all four callers `.strip()` first, which strips every one of them.
A fifth caller that does not strip inherits exactly the two-spellings asymmetry
the function was written to remove.

## 11 · Spec items still unimplemented

Unchanged from round 3, reported for completeness rather than as the proof:
`COMMANDS = {"list": None, "commit": cmd_commit}` (`bin/perry-goals:1412`) —
there is no writer for `phase/<NNN>-<slug>.md` or `phase/<NNN>-linkage.md`, and
neither declared refusal (*a KR edge to an unresolvable id*, *a phase file for a
phase that already exists*) exists. Nothing in `Out of scope` excludes them.

## 12 · What would make it pass

1. Move the `except UnrenderableCell` handler **into `main()`**, where `args`
   lives and `args.as_json` can be honoured — the shape `bin/perry-task:4054`
   already has. A CLI-level test that asserts the refusal line *starts with*
   `perry-goals: refused —` and that stderr contains no `Traceback`, so M-G
   turns red.
2. Name the flags from `perry-goals`' own surface, and resolve the collision
   rather than assuming it away: thread `UnrenderableCell.naming(flag)` at the
   `ensure`/`set_cell`/`append_table_row` call sites, which is the only layer
   that knows which flag it is writing, and let the value-match be the fallback
   rather than the rule. `--track`, `--to` and `--by` must be nameable.
3. Give the flag-naming test a `perry-goals` case, and give both cases a
   `--root <tmpdir>` so the suite stops writing to the checkout it runs in.
4. Pin the `--discharged-by` exclusion so M-F turns red.
5. Either translate `UnrenderableCell` in `perry-decide`, `perry-conform` and
   `perry-migrate` too, or record why two of five writers is the right number.

---

=== VERDICT ===
task: TASK-037
rung: V4
result: FAIL
criteria: perry/evidence/2026-08/TASK-037-spec.md
checked: on COPIES and throwaway project roots — all 6 cell-carrying flags across
         all 4 subcommands (8 write paths) enumerated from `parse()`; all 11
         `str.splitlines()` boundaries plus `\x1f` through all 4 value-writers in
         viewer/tables.py (unanimous) and through all 8 CLI paths (88 runs);
         create-vs-amend compared over 10 value classes per shared flag with the
         cell read back via `split_row`; `--discharged-by ''` confirmed clearing
         on both paths; widen on a table with no trailing pipe (7/7/7); 8
         mutations M-A…M-H, line-anchored, `__pycache__` cleared and the
         whole-second boundary waited past, copy diffed byte-identical after;
         full suite on the copy 42 modules/1363 tests; `perry-lint` clean rc 0;
         every `if __name__` handler in bin/ read for the same scoping defect
not-checked: `perry-task`, `perry-conform` and `perry-migrate` write paths were
         enumerated as `render_row` callers but not run against the character
         corpus; `perry-decide` was run once and its truncation is reported, not
         diagnosed; the byte-identity gate was NOT re-run this round (round 3
         confirmed it on all four real OKR.md and nothing in this diff touches
         `Okr.render`); the Chinese/`CLOCK_RE` block was rewritten by another
         agent mid-round and was not reviewed; `phase/` writers (none exist);
         concurrency and the project lock; any non-macOS path; whether the four
         copy-only suite reds have a cause other than F3's mechanism
proof: bin/perry-goals:1556 (`_v = getattr(args, _name, None)`) sits in the
         MODULE-LEVEL `except UnrenderableCell` block opened at :1544, while
         `args` is a local of `main()` assigned at :1464. Every line-break
         refusal on every one of the eight write paths therefore ends in
         `NameError: name 'args' is not defined` after a two-frame traceback,
         with empty stdout under `--json` — measured 88/88 for the ten refusing
         characters, and including the exact command round 3 filed as F3
         (`commit --close ops/1 --discharged-by done` on a Commitments table with
         no `Status` column), which still raises a NameError; only the undefined
         name moved, from viewer/tables.py:193 to bin/perry-goals:1556.
         Introduced by commit 56b1b54, which replaced a working one-line print
         with `bin/perry-task:4054`'s handler copied into a scope that has no
         `args`. Mutation M-G (the handler's own print line → a meaningless message)
         leaves tests.test_goals_writer and tests.test_one_line_break_rule GREEN,
         because tests/test_goals_writer.py:1155 asserts `"line break" in
         stderr` and the traceback's own last line contains it.
=== END VERDICT ===
