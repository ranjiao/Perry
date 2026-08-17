"""Markdown table surgery for a Perry project's state files. The write side.

`parsers.py` next door is the read side and says so in its first line: "never
writes". This is its counterpart, and it lives beside it on purpose — five
tools already import `parsers`, so `viewer/` is where Perry's shared code
actually is, whatever the directory is called. Opening a second shared
location would be the defect these functions exist to prevent.

**Everything here edits lines in place.** Nothing round-trips through a parsed
model, because round-tripping normalizes whitespace, alignment and column
order, and every downstream reader keys on those. The property a Perry writer
has to hold is that a tool-written file is byte-identical to the hand-written
one it replaces, except for the cells it was asked to change.

Extracted from `bin/perry-task` for TASK-037: `bin/perry-goals` needs the same
operations, and copying them would make one rule two implementations — the
defect five review rounds kept finding. The extraction itself changed no
behaviour; `perry-task`'s suite passed unedited across it.
"""

from __future__ import annotations

import re


def split_row(line: str) -> list[str]:
    """`| a | b |` → `["a", "b"]`.

    Leading and trailing pipes are stripped before splitting, so a row and its
    header always yield the same number of cells for the same table.
    """
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render_row(cells: list[str]) -> str:
    """`["a", "b"]` → `| a | b |`, one space of padding, no alignment.

    Deliberately not column-aligned. Aligning would rewrite every row of a
    table whenever one cell grew, turning a one-cell edit into a whole-table
    diff and burying the change nobody can then review.
    """
    return "| " + " | ".join(c.strip() for c in cells) + " |"


def squash(s: str) -> str:
    """Whitespace and decoration only — no language knowledge.

    `**Status**` and ``` `status` ``` and `Status ` all become `status`, so a
    header cell someone bolded still resolves. Mapping a *localized* header to
    its English key is a separate step that needs the glossary; this one has
    no opinion about language.

    `bin/perry-lint` defined this same function character-for-character under
    the name `norm`. It now imports this one.
    """
    return re.sub(r"[\s`*]+", " ", s).strip().lower()
