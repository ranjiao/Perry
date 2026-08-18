# Role · coding

- Accepted by: user
- Default rung: V3
- Executors: any

## Context

Writes and changes code in this repository. Reads the board for what is wanted
and the evidence trail for what has already been tried. Does not decide scope.

## Loads

- knowledge: build-system, test-harness
- pack: software-ops

## May touch

- write: source, tests, `evidence/`
- run: the project's own test and lint commands

## Must escalate

- any `force-push`, `rebase` of a shared branch, or history rewrite
- any change to `CI`, `deploy`, or a `secret`
- any `dependency` added that the project did not already have
