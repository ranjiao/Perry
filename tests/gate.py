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

Usage — append it to whatever the fixture already writes, as long as what the
fixture already writes is only a PREAMBLE:

    (root / ".perry" / "config.md").write_text(
        "# Perry configuration\\n\\n- State root: .\\n" + GATE_OFF)

**Appending to a config that already has `##` sections does not work, and used
to.** `gate_mode` scanned the whole file with a regex, so a `Conformance gate`
line anywhere in it was found. It reads `.perry/config.jsonl` first now
(TASK-233), and `perry_md_store § scan_config` stores only settings written
**above the first `##`** — deliberately, because a real config's prose sections
are full of bullets carrying a colon that are sentences and not keys. So an
appended line lands outside the preamble, mints no record, and the store then
answers "this project declares no gate" — correctly, about a file that declares
it in a place the format does not read. Use `gate_off(text)` below, which puts
the line where the preamble is, and `gate_off_record` for a fixture that
hand-builds its store instead of deriving one with `perry-config write
--from-file`.
"""

from __future__ import annotations

import json

#: A `.perry/config.md` line. Must stay parseable by
#: `bin/perry-conform.gate_mode`'s `Conformance gate` matcher — if that
#: matcher's spelling ever changes, every fixture using this goes red at once,
#: which is the intended blast radius for a config key silently renamed.
GATE_OFF = "- Conformance gate: advisory\n"


def gate_off(config_md: str) -> str:
    """`config_md` with the opt-out line inside its preamble.

    For fixtures that build on a config which already carries `## Tracks` or
    prose. Appending would put the line where `scan_config` does not look; this
    puts it on the last line before the first `##`, which is where a user
    writing the documented shape puts it (`reference/config.md`).
    """
    lines = config_md.split("\n")
    cut = next((i for i, ln in enumerate(lines) if ln.startswith("##")),
               len(lines))
    # Back over the blank line that separates the preamble from the heading, so
    # the inserted bullet joins the bullets rather than the heading.
    while cut > 0 and not lines[cut - 1].strip():
        cut -= 1
    return "\n".join(lines[:cut] + [GATE_OFF.rstrip("\n")] + lines[cut:])


def gate_off_record(order: int = 90) -> str:
    """The same opt-out as one `.perry/config.jsonl` line, newline included.

    A fixture that writes a hand-built store rather than deriving one has to
    say this in the store too: `gate_mode` reads the store first, and a store
    that carries no `conformance_gate` record is a project that declares no
    gate — which is the right answer about a store that really does not carry
    it, and the wrong fixture for a test that is not about ADR-004.

    `order` defaults high so the record sorts after whatever settings the
    fixture's own preamble declares; nothing here reads it except the
    projection's line ordering.
    """
    return json.dumps({
        "kind": "setting", "key": "conformance_gate",
        "label": "Conformance gate", "value": "advisory", "order": order,
    }, ensure_ascii=False) + "\n"
