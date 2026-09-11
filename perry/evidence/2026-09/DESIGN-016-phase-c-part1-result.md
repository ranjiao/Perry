# DESIGN-016 phase C, first half — result

> Rows: TASK-364 (C1), TASK-408 (C4).
> Branch: `bin-contract-phase-a`, commits `8b302a61` and `0766817a`.
> Date: 2026-09-09 · Rung claimed: V3 · V4 pending.

## What landed

**C1 — the declaration.** `SURFACE` in each tool, per subcommand, driving that
tool's parser. `lib.parse_surface` reads the vector against it,
`lib.describe_surface` answers `--describe --json` (which is TASK-396's ask),
`lib.usage_lines` generates the usage block. Six tools converted: `perry-task`,
`perry-tasks`, `perry-okr`, `perry-config`, `perry-state`, `perry-diagnose`.

**C4 — `bin/perry`.** `list`, `list --tools`, `describe <tool> [<sub>]`, and
forwarding. It holds no list of its own; every line comes from a `SURFACE`.

| Call | Bytes |
|---|---|
| `perry list` | 4,925 |
| `perry list --tools` | 885 |
| `perry describe tasks render` | ~700 |

`perry list` names the thirteen tools that do not declare a surface yet rather
than looking complete.

## Goal 12, which is what the declaration buys

```
$ perry-task start TASK-406 --design DESIGN-016
perry-task: --design is not accepted by 'start', and 'start' would have
ignored it. Accepted here: --actor, --describe, --dry-run, --next, --root
```

`perry-task`'s per-subcommand flag lists were derived from the code — which
`args.<attr>` each handler reads, including `cell_writer`'s closures — and
`tests/test_bin_surface.py` re-derives them on every run and reddens when the
declaration and the handlers disagree. That is the direction `--kr` and
`--design` broke twice.

Three accepted-and-dropped flags surfaced in the conversion: `route` was passed
`--title` and `--summary` by a test and reads neither; `--json` is read by
`main` rather than by any handler, so it is declared once as universal; and the
bespoke `--unlinked`-outside-`add` guard is gone because the general rule now
says the same thing for every flag, `--kr` included.

## The regression this branch had shipped, and how it was found

Phase A gave `perry-config` a stray-flag check with no allowlist, so
`perry-config track main --mode queue` — the only way to declare a track's mode
— exited 2. A V4 review found it; no test covered any `perry-config` subcommand
but `show`. The fix is the conversion: the track fields are declared from
`TRACK_FLAGS`, the table `cmd_track` already reads.

With it: `--help` from any position on that tool, a `--` escape that ends the
flag scan only for the tokens after it, and `--dry-run` / `--json` honoured by
`set`, `unset`, `track` and `untrack`.

## Suite

`bash tests/run` and `tests/parallel --slow`: 122 modules (125 with the harness
self-tests), 3414 tests, one module red — the `test_contract_key_parity` pair
that is red on `main`. Tree guard clean. New module
`tests/test_bin_surface.py`, 14 tests.

## Not done in C

C2 (usage-first `--help`, the essays into `bin/README.md`), C3 (one
no-argument behaviour), C5 (`--register` as a parameter). Thirteen tools still
declare no surface.
