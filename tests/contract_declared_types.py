"""The type each contract PAGE declares for a field path.

**Why a page and not the fixture.** `tests/test_contract_invariance.py` records
the live payload's shape and holds the next reading to it. For a key whose
contract is a UNION — `int | null`, `number | null`, `string | null` — that
recording captures whichever branch the project happened to be in on the day it
was taken, and the gate then fails the first time the project supplies the
other one. It did: `intake.oldest_undischarged` was recorded `NoneType` and
went red when three intake rows arrived, on a payload that never left its
contract. `perry/evidence/2026-08/contract-invariance-union-types.md` counts
**five** such keys in that fixture and every one of them is declared a union on
its own page.

So for a TYPE the page is the authority and the fixture is a cache of one
observation. The fixture keeps the two jobs it is actually good at: what
EXISTS — a key it recorded and the payload no longer emits is still a removal —
and the type of the paths no page declares.

## How a declaration is read

The *Type* cell of a key table, and only when the **whole head of that cell**
parses into type words this file knows. Everything else declares nothing:

- ``| `priority` | string | `P0` \\| `P1` \\| `P2` … |`` — the enum is in the
  *Meaning* cell. The declaration is `string`.
- ``| `oldest_undischarged` | int \\| null | the `n` of the longest-waiting … |``
  — `{int, NoneType}`.
- ``| `role` | string — the declared role accountable for this row … |`` — a
  page that writes the type and its explanation into one cell is read up to the
  em dash. `string`.
- ``| `id` | the `RX-NNN` `risk-add` minted … |`` — prose. Nothing is declared
  and the path stays the fixture's business.

`number` is the one word that is two Python types. JSON has a single numeric
type and `json.load` returns `int` or `float` depending on whether the text
carried a `.`, so a page that says `number` cannot be read as promising which
— and a KR whose `current` moves from `0` to `0.5` is not a retype.

**Nothing here guesses.** An unrecognised word makes the whole cell decline to
declare, rather than contributing the half it understood.

## Placement is not decided twice

Where a key table hangs in the payload is `contract_key_parity.place`'s
question and it is asked there: same tables, same boxes, same rule for a
heading that names its collections. A second placement algorithm would be free
to disagree with the first about which object a table describes, and this file
would then declare types for paths the parity report says do not exist.
"""

from __future__ import annotations

import contract_key_parity as parity

#: The type vocabulary these pages actually use, in Python's names — the same
#: names `type(v).__name__` produces, because that is what the declaration gets
#: compared against.
WORDS = {
    "string": ("str",),
    "int": ("int",),
    "number": ("int", "float"),
    "bool": ("bool",),
    "boolean": ("bool",),
    "array": ("list",),
    "object": ("dict",),
    "null": ("NoneType",),
}


def type_words(cell: str) -> set[str]:
    """The Python type names a *Type* cell declares, or `set()`.

    Empty is the answer for prose, for an enum, and for anything carrying a
    word this file does not know — never a partial reading.
    """
    head = cell.split("—")[0].strip()
    if not head:
        return set()
    found: set[str] = set()
    for part in head.split("|"):
        word = part.strip().strip("`").strip().lower()
        if word not in WORDS:
            return set()
        found.update(WORDS[word])
    return found


def declared(text: str, boxes: dict[str, set[str]]) -> dict[str, set[str]]:
    """`{field path: the types the page allows there}` for one contract page.

    `boxes` is `contract_key_parity.containers(...)` over the payload the page
    is the contract for — the placement input, unchanged, so a table lands
    where the parity check says it lands.
    """
    out: dict[str, set[str]] = {}
    for heading, rows in parity.key_rows(text):
        spot = parity.place([key for key, _ in rows], boxes, heading)
        for box in spot.boxes:
            for key, cells in rows:
                words = type_words(cells[1]) if len(cells) > 1 else set()
                if words:
                    path = f"{box}.{key}" if box else key
                    out.setdefault(path, set()).update(words)
    return out
