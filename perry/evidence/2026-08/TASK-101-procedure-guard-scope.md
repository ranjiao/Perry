# TASK-101 - procedure guard covers every loadable procedure

> Completed: 2026-08-19
> Implementation: `61eb809 test(guard): scan all loadable procedures`
> Verification: V3

## Result

The mechanical procedure guard now derives a 47-page corpus from the root
router, root `reference/**/*.md`, each lane's entry point and reference tree,
and `packs/*/*.md`. The live corpus reports zero hand-write instructions for
state that already has a deterministic writer.

The guard also recognizes the two previously missing writer targets:
`knowledge/INDEX.md § Cards by topic` and `.perry/conformance.md`. The incident
close procedure records its narrative under journal Notes instead of writing
into the task-owned Status changes section.

## Verification

```text
python3 -m unittest tests.test_procedures_call_the_tool
22 tests passed
```

The focused suite asserts the real 47-page corpus has zero findings and keeps
the existing planted lane violations exact: one finding in the planted lane
entry point and two in its nested reference page.

Mutation trials independently removed or reverted each new boundary. All were
red for the expected behavioral reason: root SKILL traversal, root reference
traversal, pack traversal, closing-backtick descriptions, Detect inventories,
target-as-subject descriptions, lane-owner commands, both new writer targets,
and the incident Status changes instruction.

`git diff --check` passed for the implementation files.
