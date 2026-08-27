# TASK-178 spec — delete the read-only web viewer

> Dispatch mode: auto · Executor: `claude-subagent` · Estimated cycle: medium
> Decided by the user 2026-08-21: aiMark exists, so the local console has no value.

## The boundary, measured before this spec was written

**"Delete the viewer" and "delete `viewer/`" are different instructions and only
the first is safe.**

```
viewer/parsers.py    3,615 lines   referenced by 44 files   ← KEEP
viewer/tables.py       305 lines   referenced by 21 files   ← KEEP
viewer/serve.py        561 lines   referenced by 4, all tests or docs
```

`parsers.py § load_snapshot` and `tables.py § squash` are the **single
implementations** that `perry-state`, `perry-task`, `perry-goals`, `perry-lint`
and `perry-diagnose` all call. They are what this project spent four review
rounds unifying (`tests/test_one_header_rule.py` exists because of it). They are
**not the viewer** — they live in a directory that happens to be named after one.

Nothing outside `viewer/` imports `serve.py`. The greps that look like imports
are `bin/perry-state:9` **mentioning it in a comment** and `row.serves_kr`
matching `serve` as a substring. Confirm this yourself before deleting.

## Delete

- `viewer/serve.py`
- `viewer/templates/` (12 files) and `viewer/static/`
- `viewer/requirements.txt` (`Flask>=3.0`, `markdown>=3.5`)
- `viewer/README.md` — read it first; if it documents anything about
  `parsers.py`/`tables.py` that survives, move that text, do not lose it
- `bin/perry-viewer`
- `work/reference/viewer.md`
- `tests/test_kr_chain_render.py` and `tests/test_project_root.py` — **but read
  them first.** They render templates, so they go with the templates; if either
  asserts anything that is **not** about rendering, that assertion must be
  preserved somewhere else. Say what you moved.
- Every routing line in `work/SKILL.md` — line 35 (`reference/viewer.md`),
  line 108 (the "open the dashboard" trigger), and the `bin/perry-viewer` clause
  of the tier-3 paragraph at line 96, which must be rewritten to name **aiMark
  alone**.

## Must not touch

- **`viewer/parsers.py` and `viewer/tables.py`.** Byte-identical when you finish.
- `perry/`. `git diff -- perry/` must end empty.
- `schema/state-schema.json`.
- **Do not rename `viewer/`.** It stops being a viewer and that is a real naming
  problem, filed separately — renaming touches 44 files' imports and is its own
  decision.

## A bug you will find, and must delete rather than fix

`viewer/serve.py:98-110` and `viewer/templates/today.html:32` label an
**unfiltered** `snap.board.user_input_queue | length` as the KPI *"Needs user"*,
with empty-state text *"No user input pending."* The viewer never reads the
`asks` payload, so it shows **answered** rows as needing the user — the exact
*"2 items waiting on you"* bug the CLI fixed and recorded in
`bin/perry-state § answered`'s docstring.

**Do not fix it. It goes away with the file.** Note it in your report as closed
by deletion.

## The dependency consequence, and it is the point

`Flask`, `markdown` and `jinja2` are Perry's **only** non-stdlib dependencies and
they live entirely inside the viewer. After this row the phase Cost Ceiling's
claim — *"Perry is stdlib Python and stays that way"* — is true in fact rather
than in intent.

## Verification

1. `grep -rn` finds no reference to the viewer outside `.git/` and
   `perry/evidence/` history — not in `bin/`, `tests/`, `work/`, `goals/`,
   `decide/`, `schema/`, `README.md`, `INSTALL.md`.
2. **The suite is green on an interpreter with no third-party packages
   installed at all.** This is the verification that matters; it is what the
   deletion buys. Say which interpreter you used and prove it has no Flask,
   markdown or jinja2.
3. `viewer/parsers.py` and `viewer/tables.py` are byte-identical —
   `git diff --stat` shows them absent.
4. `perry-state --json`, `perry-task list --all --json`, `perry-goals list
   --json`, `perry-decide list --json`, `perry-lint --root .` and
   `perry-diagnose --root . --json` all still work. Paste the contract line of
   each.
5. `perry-lint --root .` — 0 errors.

## Ground rules

- Branch `coding/task-178-delete-viewer`, commit there, **no PR, no push**.
- **Commit as soon as you have something coherent, and keep committing.**
- `/usr/bin/python3` explicitly; **measure your own baseline** first.
- `/usr/bin/python3 tests/parallel -j 4`. Verify yours is the only
  `tests/parallel` — with a pattern that **cannot match your own argv**;
  `until ! pgrep -f "tests/parallel"` matches itself and never exits.
- Expected baseline: **80 modules · 2360 tests · 2 red** —
  `test_contract_invariance` (a union-typed key) and `test_diagnose` (TWO
  failures: `['TASK-007','TASK-9999']`, and a queue-register reconcile reading
  `1 != 0`). **Neither is yours**, and the second `test_diagnose` failure is
  caused by an evidence record quoting a fixture id — see
  `evidence/2026-08/TASK-153-result.md:50`. Report a different set rather than
  absorbing it.
- Your deletion removes `test_kr_chain_render` and `test_project_root`, so your
  final module count will be **lower**. That is expected; state the delta.
