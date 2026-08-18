# toolchain/pycache-staleness — a same-second edit-and-revert leaves a stale `.pyc` that Python trusts

- Kind: knowledge
- Owner role: —
- Source: TASK-072 · evidence/2026-08/TASK-072-knowledge-cards.md
- Last verified: 2026-08-18
- Invalidated by: CPython making hash-based `.pyc` validation (PEP 552) the default, or Perry's tools ceasing to load modules via `SourceFileLoader`

CPython validates a cached `.pyc` against the source's **mtime in whole seconds
and its size**. A mutation harness that writes a variant, runs a test, and
restores the original within the same second produces a source file with the
original's size and a timestamp Python cannot distinguish from the cached one —
so the stale bytecode is loaded and the suite reports failures the source on
disk does not contain.

Perry is unusually exposed to this: every tool and test here loads modules
through `SourceFileLoader`, and mutation testing — editing exactly one line,
running one module, reverting — is this project's core verification discipline.
The failure looks like a flaky test or a blind guard, which is the worst
possible disguise for it, because both are things this project actively hunts.

**What to do:** clear `__pycache__` around every mutation run, not just before
the suite. Every harness in `tests/` does.

It cost two agents a confusing run each on 2026-08-18 before the cause was
named, and one of them nearly recorded a real guard as blind because of it.
