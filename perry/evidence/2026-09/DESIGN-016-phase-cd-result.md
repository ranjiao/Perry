# DESIGN-016 phases C and D — result

> Rows: TASK-365 (C2), TASK-366 (C3), TASK-409 (C5), TASK-410 (D1).
> Branch: `bin-contract-phase-a`, commit `0f367ff7`. Base: `4ebc0693`.
> Date: 2026-09-09 · Rung claimed: V3 · V4 pending.

## C2 — usage first, and the essays moved

| Tool | `--help` before | after |
|---|---|---|
| `perry-task` | 10,690 | 2,939 |
| `perry-tasks` | 4,257 | 2,129 |
| `perry-config` | 2,438 | 1,189 |
| `perry-task done --help` | (did not exist) | 313 |

The whole-tool block lists subcommand NAMES and their one-line summaries; the
flags belong to `<tool> <sub> --help`, which is goal 8 and is 313 bytes. Both
are generated from `SURFACE`, so neither can describe a flag the parser does not
take.

The essays are in `bin/README.md § The argument, per tool`, moved whole
(Decision 2). `tests/test_bin_surface.py` asserts three of their sentences are
there, and that every tool that moved one has a section.

## C3 — one no-argument behaviour, decided by the declaration

A tool with subcommands cannot act without one: bare call prints usage on
**stderr**, exit 2. A flag-only tool does its documented default, exit 0. Both
are read off `SURFACE`, so the rule is checkable rather than remembered, and the
test has a control asserting both groups are populated.

## C5 — the register is a parameter

```
$ perry-tasks build --register risks   ==   $ perry-tasks risks-build
```

Byte-identical output, asserted for three registers times two verbs. The
register list is derived from `schema/state-schema.json § claims` — the
`work`-owned JSONL stores at the state root — so `tasks`, `risks`, `intake`,
`asks` come from the schema and a fifth would arrive without an edit. An unknown
register names the declared set; a verb the register lacks names the verbs it
has. The twelve prefixed names stay as aliases for one release.

## D1 — the README, and what phase A moved under it

| # | Was | Is |
|---|---|---|
| R1 | `add` example missing three required fields | **NOT FIXED BY THIS COMMIT, and the test said it was.** The three flags were added on continuation lines ending in `\\` — a literal backslash in bash — so the fence was four commands and the first one was the same refused call. A V4 review ran it. Fixed afterwards, and the test now executes the block instead of grepping it |
| R2 | "no tool here calls an LLM … no dependencies at all" | names `perry-codex-preflight`, `codex exec`, and the `codex` / `git` / `timeout` dependency |
| R3 | "Four other modes"; one `--strict` rule | nine modes; `--strict` fails on `--reviews` and `--specs` and does nothing on `--verification` (21 warnings, exit 0) |
| R4 | `risks-*` and `intake-*` only | the ask register, and `--register` as the parameter form |
| R5 | `perry-detect-host` prints three values | four |
| R6 | `perry-lint --help` "ALL SIX declared stores" | SEVEN, which its census has printed since TASK-276 |
| R8 | `perry-config` projects `.perry/config.md` | a settings editor; ADR-019 deleted the file |
| — | exit codes 0/1/2 | plus `3`, and `perry-diagnose` exits 2 on a bad invocation |

**R7 is withdrawn.** It claimed four living documents still call
`perry-conform` / `perry-migrate`. They name them only to say they are deleted,
with the row that deleted them: `reference/config.md:153`,
`reference/glossary.md:124`, `reference/adoption.md:437-441`, and a quoted proof
line in `work/reference/review.md`. The review's C7 and my own § 1.6 row both
read the grep rather than the sentences.

`tests/test_bin_surface.py` now holds six of these to the tools rather than to a
reader: every tool has a row, the `add` example carries the required flags, the
dependency paragraph names what it needs, the store count matches the linter,
the exit table carries `3`, and the host values are the four it prints.

## Four tests that asserted the old docstring

They matched a hand-written `Usage:` block that no longer exists. Two were weak
in a way worth naming: `test_task_writer_contracts` checked
`assertIn("perry-task risk", help)`, a substring of `perry-task risk-add`, so a
procedure quoting a command that does not exist would have passed as long as a
real one started with the same letters — and its extraction regex stopped at the
hyphen, so it never saw a full name. All four read the declaration now, by exact
name.

## Suite

`bash tests/run`: 122 modules, 3432 tests, one module red — the
`test_contract_key_parity` pair that is red on `main`. Tree guard clean.
