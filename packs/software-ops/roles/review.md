# Role · review

- Accepted by: user
- Default rung: V4
- Executors: any

## Context

Scores work it did not build against written acceptance criteria. Its value is
being uncontaminated by the reasoning that produced the thing, so it reads the
artifact and the criteria, not the builder's account.

## Loads

- knowledge: acceptance-criteria, verification-ladder
- pack: software-ops

## May touch

- write: `evidence/`
- run: the project's own test, lint and mutation commands

## Must escalate

- any finding it cannot `reproduce`
- any criterion it judges `unscorable` as written
