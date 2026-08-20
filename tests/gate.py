"""The conformance gate's opt-out line, for fixtures that are not about it.

TASK-047 flipped `bin/perry-conform.DEFAULT_MODE` from `advisory` to `enforce`,
so a writer now REFUSES a state file nobody has declared. That is the shipped
behaviour and `tests/test_conformance.py § 7` is where it is asserted.

Every other suite in here builds a throwaway project and then tests something
that has nothing to do with ADR-004 — how a row is rendered, whether a widening
loses a cell, what `--dry-run` prints. Those fixtures are undeclared, because
nobody declared them, so after the flip every one of their writes was refused
and fifteen modules went red at once. The refusals were correct; the fixtures
were simply answering a question they were not asked.

**Why the opt-out and not a declaration.** Declaring would be the more faithful
fixture — a real adopted project IS declared, and Perry's own repo is 13/16 —
and for a clean fixture it would work. It cannot be the general answer here:
a large share of these fixtures are *deliberately malformed*, which is the whole
point of the suite that owns them (`test_prioritize` widens a board with 4 shape
errors; `test_row_integrity` corrupts rows on purpose). `perry-conform declare`
correctly refuses a file that does not match Perry's shape, so those fixtures
cannot be declared by construction. One control has to cover both kinds, and
`- Conformance gate: advisory` is the one the user has for exactly this reason.

This is NOT a way to keep the suite from meeting the gate. It is a per-fixture
statement that a given project is out of scope for ADR-004, written in the same
documented, user-facing control a real project would use. The gate itself —
both branches, both precedence paths, both exemptions — is exercised in
`tests/test_conformance.py`, and `tests/test_work_modes.py` still declares a
`.perry/config.md` for real rather than opting out.

Usage — append it to whatever the fixture already writes:

    (root / ".perry" / "config.md").write_text(
        "# Perry configuration\\n\\n- State root: .\\n" + GATE_OFF)
"""

from __future__ import annotations

#: A `.perry/config.md` line. Must stay parseable by
#: `bin/perry-conform.gate_mode`'s `Conformance gate` matcher — if that
#: matcher's spelling ever changes, every fixture using this goes red at once,
#: which is the intended blast radius for a config key silently renamed.
GATE_OFF = "- Conformance gate: advisory\n"
