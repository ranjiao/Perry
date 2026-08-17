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


class UnrenderableCell(ValueError):
    """A value a markdown table row cannot carry. Raised by `render_row`.

    Carries `index` and `value` so a CLI can name the field it refused rather
    than echoing a row the user never typed.
    """

    def __init__(self, index: int, value: str, why: str) -> None:
        self.index, self.value, self.why = index, value, why
        super().__init__(f"cell {index}: {why}")


def render_row(cells: list[str]) -> str:
    """`["a", "b"]` → `| a | b |`, one space of padding, no alignment.

    Deliberately not column-aligned. Aligning would rewrite every row of a
    table whenever one cell grew, turning a one-cell edit into a whole-table
    diff and burying the change nobody can then review.

    **Raises `UnrenderableCell` for a value that would not read back as
    itself.** The check is the round trip against `split_row`, not a list of
    characters, and that is the whole point of it.

    The previous version escaped `|` and nothing else. It was written after a
    `Next action` quoting a markdown header shifted every column after it and
    pushed `Risk` into `Verification` — so the guard was shaped around the one
    character that had bitten. Weeks later `--next` was handed text containing
    blank lines, `render_row` emitted the newlines verbatim, and three rows of
    Perry's own board were destroyed: each ended mid-cell with no closing `|`,
    the tail landed in the document as loose paragraphs, and the *next* `add`
    parsed the truncated line as the table's last row and inserted into the
    middle of the spilled text. `perry-lint` reported `✓ clean` throughout.

    `|` passes because escaping round-trips. `\\n` cannot round-trip through a
    markdown table at all, which is why this refuses rather than encodes: the
    caller asked to store something the format does not hold, and silently
    collapsing it would lose the user's writing without saying so.
    """
    out = "| " + " | ".join(
        c.strip().replace("|", _ESCAPED_PIPE) for c in cells) + " |"
    want = [c.strip() for c in cells]

    # The invariant is TWO clauses, and the round trip alone is not it.
    # `split_row` scans a string for `|` without caring about line breaks, so
    # `split_row(render_row(c)) == c` holds for a cell containing `\n` — the
    # first version of this guard was exactly that comparison and let a
    # multi-line `--next` straight through, which is the bug it was written
    # for. Found by probing the guard rather than by reading it.
    if len(out.splitlines()) > 1:
        i = next((n for n, c in enumerate(want)
                  if "\n" in c or "\r" in c), 0)
        raise UnrenderableCell(
            i, want[i] if i < len(want) else "",
            "contains a line break — a markdown table row is one line")
    got = split_row(out)
    if got != want:
        i = next((n for n, (a, b) in enumerate(zip(got, want)) if a != b),
                 min(len(want), len(got)))
        raise UnrenderableCell(i, want[i] if i < len(want) else "",
                               "does not read back as itself")
    return out


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
