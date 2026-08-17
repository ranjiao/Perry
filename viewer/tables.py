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


#: A `|` that is part of a value, not a delimiter. Markdown's own convention.
_ESCAPED_PIPE = "\\|"


def split_row(line: str) -> list[str]:
    """`| a | b |` → `["a", "b"]`, and `\\|` is a value, not a delimiter.

    Leading and trailing pipes are stripped before splitting, so a row and its
    header always yield the same number of cells for the same table.

    The escape half matters because the delimiter is a character people write.
    Splitting on every `|` turned a three-cell row whose middle cell mentioned
    a markdown table into a four-cell row, shifting every column after it —
    found by the conformance gate on Perry's own board, where a task's
    `Next action` quoting `| ID | Risk | Opened |` pushed the word `Risk` into
    the `Verification` column and tripped the enum check.
    """
    cells, cur = [], []
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith(_ESCAPED_PIPE):
        body = body[:-1]
    i = 0
    while i < len(body):
        if body[i] == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            cur.append("|")
            i += 2
        elif body[i] == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
        else:
            cur.append(body[i])
            i += 1
    cells.append("".join(cur).strip())
    return cells


def render_row(cells: list[str]) -> str:
    """`["a", "b"]` → `| a | b |`, one space of padding, no alignment.

    Deliberately not column-aligned. Aligning would rewrite every row of a
    table whenever one cell grew, turning a one-cell edit into a whole-table
    diff and burying the change nobody can then review.
    """
    return "| " + " | ".join(
        c.strip().replace("|", _ESCAPED_PIPE) for c in cells) + " |"


def squash(s: str) -> str:
    """Whitespace and decoration only — no language knowledge.

    `**Status**` and ``` `status` ``` and `Status ` all become `status`, so a
    header cell someone bolded still resolves. Mapping a *localized* header to
    its English key is a separate step that needs the glossary; this one has
    no opinion about language.

    `bin/perry-lint` defined this same function character-for-character under
    the name `norm`. It now imports this one.

    `viewer/parsers.py` — the read side — spelled the same idea
    `.strip().lower()` at eleven sites, which is NOT this function: it leaves
    the decoration on. So on `| ID | **Risk** | Opened | Status |` the writer
    said risk-table and the reader said not, and `risk-add` wrote rows that
    `perry-state` counted as zero. It imports this one too now (TASK-050), so
    "is this cell that column?" has exactly one answer in this repository.

    This is why the function is in `tables.py` and not in either caller: it is
    the only module both a writer and a reader could import without one of
    them depending on the other.
    """
    return re.sub(r"[\s`*]+", " ", s).strip().lower()
