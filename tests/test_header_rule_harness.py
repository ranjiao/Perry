"""The planting corpus for the one-header-rule check. TASK-050, round 9.

**Three reviewers have now defeated this file's corpus, and the third defeated
it by AUDIT rather than by planting.** Round 5 planted nine spellings and five
escaped both nets; round 7 planted twenty-five and twenty-one escaped; round 8
reported *"30 of 30 caught"* against a corpus it described as *"the UNION of
every shape the round 5 and round 7 reviews name"* and *"a superset of round
7's corpus"* — and it was neither. Round 7's own escape list names *"a scalar
header-row test"* and *"P23–P25, round 4's `_is_python` hole"*; **none of them
was in the corpus**, and the labels `P23`–`P25` had been re-used for three
different shapes, so the omission was invisible in the numbering. The reviewer
re-derived the missing shapes, planted them with a control at the same paths,
and all five escaped both nets.

So this file is rebuilt, and it is rebuilt under three rules:

1. **Every entry quotes the review line it comes from.** The `source` field is
   not decoration — it is what makes the denominator auditable instead of
   asserted. An entry with no quote cannot be checked against the review that
   produced it, and `test_every_entry_carries_its_provenance` refuses one.
2. **A label is never re-used for a different shape.** That is the specific
   mechanism that hid round 8's pruning, and
   `test_no_label_is_re_used_for_a_different_shape` asserts it directly.
3. **What escapes is a corpus too, with the same provenance.** Round 8 reported
   a fraction against the shapes it caught. This reports three fractions, and
   the one that is zero is the one that matters most to read.

## The three corpora, and what each measures

- `DRIFT` — **the net's own class**: the ONE rule (`squash`, or its `norm`
  alias) applied to a header row, or to a cell of one, outside
  `viewer/tables.py § header_index`. This is what
  `tests/header_rule.py § offenders_by_symbol` exists to see and every entry
  must be caught.
- `CLEAN` — legitimate code that must never be reported. Criterion 4 of the
  spec is this list, and round 7 failed it six times out of eight.
- `SECOND_RULE` — **every shape the round 4, 5 and 7 reviews name, and it is
  asserted to ESCAPE.** A reader that invents its own rule calls no blessed
  symbol, so the symbol check is blind to it *by construction*. That is a
  declared limit, not a defect to be fixed by an eighth detector: seven rounds
  proved the shape net cannot be finished, and round 8 proved that keeping an
  unfinished one next to the symbol check puts a false positive in front of
  correct code. What covers this class is
  `tests/test_header_index_is_the_only_fold.py`, which watches the real readers
  parse a decorated document and asks whether every decorated header cell
  reached `header_index` — a reader that grows its own rule stops reaching it.

**Round 8's shape net (`offenders`) is deleted.** With it went `ROW_NAMES`
(eleven variable names), the `("header", "headers", "hdr")` subscript test, and
the `.split("|")` row inference that produced the declared false positive. No
allowlist of variable names survives anywhere in `tests/header_rule.py`.

Everything is planted into a `tempfile` COPY.
`work/reference/review-constraints.md` is explicit: for the seconds a planted
file exists, a shared checkout has a file that makes this guard legitimately
red, and anything else running the suite sees a real-looking failure about
nothing.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from header_rule import offenders_by_symbol, readers_under      # noqa: E402

PERRY_HOME = Path(__file__).resolve().parent.parent

SHEBANG = "#!/usr/bin/env python3\n"

#: The entries planted with **no first line at all** — the two whose whole
#: subject is round 4's hole *"a file whose first line is a docstring, a `# -*-
#: coding:` line, or a licence header is invisible"*. Round 9's reviewer
#: measured that `_plant` was prepending a shebang to them, so neither could
#: discriminate the hole it names; R9-6 reddening `D21` and not `D20` is that
#: measurement. Two paths, and `TestTheCorpusIsAuditable §
#: test_the_no_shebang_entries_are_planted_without_one` asserts the bytes.
NO_SHEBANG = frozenset({"bin/probe-d20", "bin/probe-s12"})

#: Directories a planted copy does not need. `perry/` is 4 MB of evidence
#: markdown and holds no reader; `tests/` is this file.
NOT_COPIED = {".git", "perry", "tests", "__pycache__", ".perry"}

#: `(label, source, path, body)`.
#:
#: `source` is the review sentence the entry is derived from, quoted. `path` is
#: as load-bearing as `body`: three historical blind spots were about WHERE the
#: file sat and two more about what it was NAMED.
#:
#: **DRIFT — the one rule, applied outside `header_index`.** All must be caught.
DRIFT = [
    ("D01 comprehension over `split_row`",
     "round 8 review, M9: `bin/perry-diagnose:1825` -> `[squash(c) for c in "
     "cells]` (the DRIFT case) — net 1 fires, net 2 correctly does not",
     "bin/perry-probe-d01",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    cells = split_row(line)\n'
     '    return [squash(c) for c in cells]\n'),

    ("D02 a tuple-returning file-local function (`ihdr`)",
     "round 8 review, M9b: `ihdr` reaches the walk only through `_, ihdr = "
     "board.section_table(...)`, and the returns-dataflow closes it",
     "bin/perry-probe-d02",
     'from tables import squash, split_row\n'
     'def section_table(n):\n'
     '    return 1, split_row(n)\n'
     'def read(n):\n'
     '    _, ihdr = section_table(n)\n'
     '    return [squash(h) for h in ihdr]\n'),

    ("D03 one element-preserving unwrap (`prev_cells`)",
     "round 7 Finding 1: `viewer/parsers.py:1827` — `header = [squash(c) for c "
     "in prev_cells]` in `_table_rows` — GREEN",
     "bin/perry-probe-d03",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    prev_cells = [c.strip() for c in split_row(line)]\n'
     '    return [squash(c) for c in prev_cells]\n'),

    ("D04 SCALAR, `squash(cells[0])`",
     "round 4 verdict: `bin/perry-state:157` — `squash(cells[0]) != \"term\"` "
     "— reverted to a second rule leaves all 1363 tests green",
     "bin/perry-probe-d04",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    cells = split_row(line)\n'
     '    return squash(cells[0]) != "term"\n'),

    ("D05 SCALAR, the `fifth copy` shape",
     "round 8 review, Finding 1: the scalar class is structural — that is the "
     "exact shape of the `fifth copy` (viewer/parsers.py:428, "
     "read_conformance), the copy that produced a real user-visible defect",
     "bin/perry-probe-d05",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    rel = split_row(line)[0]\n'
     '    return squash(rel) in ("file", "path")\n'),

    ("D06 `map(norm, row)`",
     "round 5 review, Finding 2: the `.casefold()` and `map()` blind spots",
     "bin/perry-probe-d06",
     'from tables import squash as norm, split_row\n'
     'def read(line):\n'
     '    return list(map(norm, split_row(line)))\n'),

    ("D07 a `for`/`append` loop, no comprehension at all",
     "round 5 review, Finding 1, case H: plain `for` loop with `.append()` "
     "instead of a comprehension — escapes both",
     "bin/perry-probe-d07",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    out = []\n'
     '    for c in split_row(line):\n'
     '        out.append(squash(c))\n'
     '    return out\n'),

    ("D08 a dict-comprehension header index",
     "round 5 review, Finding 1, case F: dict-comprehension header index — "
     "and case F is LIVE at bin/perry-diagnose:1826",
     "bin/perry-probe-d08",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    return {squash(c): i for i, c in enumerate(split_row(line))}\n'),

    ("D09 the rule factored into a file-local scalar helper",
     "round 5 review, Finding 1, case G: the rule factored into a scalar "
     "helper `_norm` — caught by complement only",
     "bin/perry-probe-d09",
     'from tables import squash, split_row\n'
     'def _key(s):\n'
     '    return squash(s)\n'
     'def read(line):\n'
     '    return [_key(c) for c in split_row(line)]\n'),

    ("D10 a `lambda` folding helper",
     "round 7 Finding 2: escapes include ... a `lambda` folding helper",
     "bin/perry-probe-d10",
     'from tables import squash, split_row\n'
     'fold = lambda s: squash(s)\n'
     'def read(line):\n'
     '    return [fold(c) for c in split_row(line)]\n'),

    ("D11 SCALAR fold of a loop variable",
     "round 7 Finding 2: escapes include ... a scalar header-row test",
     "bin/perry-probe-d11",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    for c in split_row(line):\n'
     '        if squash(c) == "id":\n'
     '            return True\n'
     '    return False\n'),

    ("D12 accumulation through `out +=`",
     "round 7 Finding 2: escapes include ... `out +=`",
     "bin/perry-probe-d12",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    out = []\n'
     '    for c in split_row(line):\n'
     '        out += [squash(c)]\n'
     '    return out\n'),

    ("D13 a SLICE of the row, `cells[1:]`",
     "round 7 Finding 2: escapes include ... `cells[1:]`",
     "bin/perry-probe-d13",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    cells = split_row(line)\n'
     '    return [squash(c) for c in cells[1:]]\n'),

    ("D14 an ALIASED row parameter, `cs = cells`",
     "round 7 Finding 2: escapes include ... an aliased row parameter "
     "(`cs = cells`)",
     "bin/perry-probe-d14",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    cs = split_row(line)\n'
     '    ks = cs\n'
     '    return [squash(c) for c in ks]\n'),

    ("D15 a walrus",
     "round 7 Finding 2: escapes include ... a walrus",
     "bin/perry-probe-d15",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    if (cs := split_row(line)):\n'
     '        return [squash(c) for c in cs]\n'
     '    return []\n'),

    ("D16 `zip` between the row and its values",
     "round 7 Finding 2: escapes include ... `zip`",
     "bin/perry-probe-d16",
     'from tables import squash, split_row\n'
     'def read(line, values):\n'
     '    return {squash(k): v for k, v in zip(split_row(line), values)}\n'),

    ("D17 a parameter this file passes a row to",
     "round 8 review, Finding 2: for net 1 the allowlist is not load-bearing "
     "on anything I could construct — so the symbol check is name-free; this "
     "plants the shape that would need a name if it were not",
     "bin/perry-probe-d17",
     'from tables import squash, split_row\n'
     'def fold(stuff):\n'
     '    return [squash(c) for c in stuff]\n'
     'def read(line):\n'
     '    return fold(split_row(line))\n'),

    ("D18 a re-fold of `header_index`'s OWN output",
     "TASK-050 spec amendment: no call to `squash` on a row cell exists "
     "outside `header_index()`",
     "bin/perry-probe-d18",
     'from tables import squash, split_row, header_index\n'
     'def read(line):\n'
     '    keys = header_index(split_row(line))\n'
     '    return [squash(k) for k in keys]\n'),

    ("D19 planted in a SUBDIRECTORY",
     "round 3, carried in this file since round 5: a SUBDIRECTORY was "
     "invisible",
     "bin/lib/probe_d19.py",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    return [squash(c) for c in split_row(line)]\n'),

    ("D20 no suffix and NO SHEBANG",
     "round 4: a file whose first line is a docstring, a `# -*- coding:` line, "
     "or a licence header is invisible",
     "bin/probe-d20",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    return [squash(c) for c in split_row(line)]\n'),

    ("D21 a non-`.py` dotted suffix",
     "round 4: any non-`.py` suffix returns `False` without reading anything "
     "(line 54) ... the rule is \"trust the extension\"",
     "bin/probe_d21.reader",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    return [squash(c) for c in split_row(line)]\n'),

    ("D22 OUTSIDE `bin/` and `viewer/`",
     "round 8 review, Finding 1: ESCAPED R4 · python reader outside bin/ and "
     "viewer/ (packs/)",
     "packs/probe_d22.py",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    return [squash(c) for c in split_row(line)]\n'),

    ("D23 `sorted(key=norm)`",
     "round 7 Finding 2: escapes include ... `sorted(key=str.lower)`",
     "bin/perry-probe-d23",
     'from tables import squash as norm, split_row\n'
     'def read(line):\n'
     '    return sorted(split_row(line), key=norm)\n'),

    ("D32 an alias passed to `map`, never CALLED",
     "round 9 review, the FAIL: the corpus plants both HARDER indirections "
     "and neither easy one — and `D06 map(norm, row)` plants the `map` shape "
     "only for a name already in `BLESSED`. Mutation R10-5 was GREEN without "
     "this entry: every other alias shape is redundantly caught by the SCALAR "
     "half, because an alias in a comprehension is a Call node. Here it is "
     "not, so the mapping half is the only thing that can see it",
     "bin/perry-probe-d32",
     'from tables import squash, split_row\n'
     'fold = squash\n'
     'def read(line):\n'
     '    return list(map(fold, split_row(line)))\n'),

    ("D33 an alias used as a `sorted` key, never CALLED",
     "round 7 Finding 2: escapes include ... `sorted(key=str.lower)` — "
     "planted as `D23` for the blessed name and here for an alias, the same "
     "gap `D32` closes for `map`",
     "bin/perry-probe-d33",
     'from tables import squash, split_row\n'
     'fold = squash\n'
     'def read(line):\n'
     '    return sorted(split_row(line), key=fold)\n'),

    ("D25 a BARE ALIAS of the rule, `fold = squash`",
     "round 9 review, the FAIL: ESCAPED B `fold = squash` (ONE character "
     "simpler than D10, which is caught) — a one-line rebinding of `squash` "
     "to any name other than `norm` maps the one rule across a header row "
     "with every guard this row ships reporting nothing",
     "bin/perry-probe-d25",
     'from tables import squash, split_row\n'
     'fold = squash\n'
     'def read(line):\n'
     '    return [fold(c) for c in split_row(line)]\n'),

    ("D26 an IMPORT ALIAS onto an untrusted name",
     "round 9 review, the FAIL: ESCAPED E `from tables import squash as fold` "
     "— corpus entry `D06` is `from tables import squash as norm`, aliasing "
     "that happens to land on a name already in `BLESSED`; the case where the "
     "alias lands anywhere else is the one that is neither planted nor handled",
     "bin/perry-probe-d26",
     'from tables import squash as fold, split_row\n'
     'def read(line):\n'
     '    return [fold(c) for c in split_row(line)]\n'),

    ("D27 an ALIAS through the module object, `fold = tables.squash`",
     "round 9 review, the FAIL: ESCAPED F `import tables; fold = tables.squash`",
     "bin/perry-probe-d27",
     'import tables\n'
     'from tables import split_row\n'
     'fold = tables.squash\n'
     'def read(line):\n'
     '    return [fold(c) for c in split_row(line)]\n'),

    ("D28 a bare alias applied to ONE CELL",
     "round 9 review, the FAIL: ESCAPED C `fold = squash`, SCALAR on a cell — "
     "the scalar half of the same escape, which the round 9 probe planted "
     "separately because the two halves of the net are separate",
     "bin/perry-probe-d28",
     'from tables import squash, split_row\n'
     'fold = squash\n'
     'def read(line):\n'
     '    cells = split_row(line)\n'
     '    return fold(cells[0]) == "id"\n'),

    ("D29 the repository's OWN idiom, renamed",
     "round 9 review, the FAIL: ESCAPED G the repo's OWN idiom, renamed — "
     "`bin/perry-lint:250` is literally `norm = squash`; `norm` happens to be "
     "in `BLESSED`, so that one site is seen and the same line written with "
     "any other name is not",
     "bin/perry-probe-d29",
     'from tables import squash, split_row\n'
     'keyof = squash\n'
     'def read(line):\n'
     '    return [keyof(c) for c in split_row(line)]\n'),

    ("D30 a CHAIN of aliases, bound OUT OF ORDER",
     "round 9 review, the FAIL: it is small to fix — resolve module-level "
     "`NAME = <blessed>` bindings into the blessed set; a resolver that does "
     "not run to a fixpoint closes the one-step case and not this one. The "
     "first link is nested inside an `if`, so `ast.walk`'s breadth-first "
     "order reaches the SECOND link first and one pass cannot close it — "
     "mutation R10-4 was GREEN against the in-order spelling and is the "
     "reason this entry is written this way",
     "bin/perry-probe-d30",
     'import os\n'
     'from tables import squash, split_row\n'
     'if os.name == "posix":\n'
     '    a = squash\n'
     'fold = a\n'
     'def read(line):\n'
     '    return [fold(c) for c in split_row(line)]\n'),

    ("D31 an alias bound INSIDE the reader",
     "round 9 review, the FAIL: `_RowLocals` resolves a fold reached through "
     "a `def` wrapper and through a name-bound `lambda` ... but nothing "
     "resolves a plain rebinding — and a rebinding is not obliged to sit at "
     "module level",
     "bin/perry-probe-d31",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    fold = squash\n'
     '    return [fold(c) for c in split_row(line)]\n'),

    ("D34 a row carried on a DICT KEY, built in the SAME function",
     "round 10 review, the FAIL: `t = {'header': split_row(line)}; "
     "[squash(c) for c in t['header']]` ESCAPED — *P2 is local dataflow "
     "inside one function*, and the round's own reason for leaving it open "
     "(interprocedural, across a module boundary) does not apply to it",
     "bin/perry-probe-d34",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    t = {"header": split_row(line)}\n'
     '    return [squash(c) for c in t["header"]]\n'),

    ("D35 a dict a FILE-LOCAL function returned",
     "round 10 review, the FAIL: `t = table_of(line); hdr = t['header']; "
     "[squash(c) for c in hdr]` ESCAPED — teach `source()` that a subscript "
     "of a dict this file built, or of what a file-local function returned, "
     "is a row; `_RowLocals.returns` already carries tuple positions and a "
     "string key is the same bookkeeping",
     "bin/perry-probe-d35",
     'from tables import squash, split_row\n'
     'def table_of(line):\n'
     '    return {"header": split_row(line), "rows": []}\n'
     'def read(line):\n'
     '    t = table_of(line)\n'
     '    hdr = t["header"]\n'
     '    return [squash(c) for c in hdr]\n'),

    ("D36 a LIST OF DICTS, indexed",
     "round 10 review, the FAIL: `[squash(c) for c in "
     "tables_of(line)[0]['header']]` ESCAPED — `bin/perry_store.py:681` is "
     "`tables[0]['header']` and it is written three times in that file",
     "bin/perry-probe-d36",
     'from tables import squash, split_row\n'
     'def tables_of(line):\n'
     '    return [{"header": split_row(line)}]\n'
     'def read(line):\n'
     '    return [squash(c) for c in tables_of(line)[0]["header"]]\n'),

    ("D42 a LOOP over a list of tables",
     "round 10 review, the FAIL: `[squash(c) for c in "
     "tables_of(line)[0]['header']]` ESCAPED — the same list of dicts walked "
     "instead of indexed, which is how `bin/perry_md_store.py:468` and `:543` "
     "and `bin/perry_store.py:531` all read a header: `for tbl in tables:` "
     "then `tbl['header']`. Planted because neutralising the loop-target "
     "binding left every other entry of this corpus caught",
     "bin/perry-probe-d42",
     'from tables import squash, split_row\n'
     'def tables_of(lines):\n'
     '    out = []\n'
     '    for line in lines:\n'
     '        out.append({"header": split_row(line)})\n'
     '    return out\n'
     'def read(lines):\n'
     '    for tbl in tables_of(lines):\n'
     '        return [squash(c) for c in tbl["header"]]\n'
     '    return []\n'),

    ("D37 a row carried on an OBJECT ATTRIBUTE",
     "round 10 review, smaller results: *a row carried on an object "
     "attribute escapes too* — `t = T(line); [squash(c) for c in t.header]`, "
     "on both trees; same family as the dict, recorded so the fix covers both",
     "bin/perry-probe-d37",
     'from tables import squash, split_row\n'
     'class Table:\n'
     '    def __init__(self, line):\n'
     '        self.header = split_row(line)\n'
     'def read(line):\n'
     '    t = Table(line)\n'
     '    return [squash(c) for c in t.header]\n'),

    ("D38 the FOUR-LINK chain `bin/perry_store.py` actually writes",
     "round 10 review, the FAIL: the escape is on a live production file — "
     "`bin/perry_store.py § risk_plan`, which already reads `header, keys = "
     "table['header'], table['keys']` at :854. `markdown_tables` APPENDS its "
     "tables, `risk_section_shape` returns them at a TUPLE POSITION, "
     "`risk_table` INDEXES one out, `risk_plan` UNPACKS the header. One "
     "corpus entry for the whole chain, because closing three links and not "
     "the fourth still escapes",
     "bin/perry-probe-d38",
     'from tables import squash, split_row\n'
     'def markdown_tables(lines):\n'
     '    out = []\n'
     '    for line in lines:\n'
     '        out.append({"header": split_row(line), "rows": []})\n'
     '    return out\n'
     'def section_shape(lines):\n'
     '    tables = markdown_tables(lines)\n'
     '    return "table", tables\n'
     'def one_table(lines):\n'
     '    shape, tables = section_shape(lines)\n'
     '    return tables[0] if shape == "table" else None\n'
     'def plan(lines):\n'
     '    table = one_table(lines)\n'
     '    header, rows = table["header"], table["rows"]\n'
     '    return [squash(c) for c in header]\n'),

    ("D39 a table handed over by `yield`",
     "round 10 review, the FAIL: the fix is to teach `source()` that a "
     "subscript of a dict this file built is a row — `bin/perry-task § "
     "_section_tables` is the ONE walk over the board's task-bearing "
     "sections and it `yield`s its tables, so a producer that never "
     "`return`s is the same local case one function further on",
     "bin/perry-probe-d39",
     'from tables import squash, split_row\n'
     'def sections(lines):\n'
     '    for line in lines:\n'
     '        yield "Work", {"header": split_row(line)}\n'
     'def read(lines):\n'
     '    for title, table in sections(lines):\n'
     '        return [squash(c) for c in table["header"]]\n'
     '    return []\n'),

    ("D43 a table RE-YIELDED by `yield from`",
     "round 11 review: two branches of the new machinery still survive their "
     "own deletion — the `YieldFrom` step and `ast.Set` in the literal "
     "branch; either give them a test or delete them the way the other ten "
     "were deleted. `yield from` re-yields, so it does NOT add an element "
     "level, and a step that gets that wrong reads one subscript too deep",
     "bin/perry-probe-d43",
     'from tables import squash, split_row\n'
     'def tables_of(lines):\n'
     '    out = []\n'
     '    for line in lines:\n'
     '        out.append({"header": split_row(line)})\n'
     '    return out\n'
     'def sections(lines):\n'
     '    yield from tables_of(lines)\n'
     'def read(lines):\n'
     '    for table in sections(lines):\n'
     '        return [squash(c) for c in table["header"]]\n'
     '    return []\n'),

    ("D44 a table reached through a METHOD of a file-local class",
     "round 11 review, correction 3: the hand-written sweep did not reach "
     "every branch. `_rpaths_of` resolves a call by the ATTRIBUTE name as "
     "`_returns_of` already does, and nothing planted it — this is "
     "`bin/perry-task § Board.task_tables()` and `bin/perry_store.py § plan`, "
     "which read `table['header']` off a method of a class, minus the "
     "cross-module root that keeps the live ones out of reach",
     "bin/perry-probe-d44",
     'from tables import squash, split_row\n'
     'class Board:\n'
     '    def __init__(self, lines):\n'
     '        self.lines = lines\n'
     '    def tables(self):\n'
     '        out = []\n'
     '        for line in self.lines:\n'
     '            out.append({"header": split_row(line)})\n'
     '        return out\n'
     'def read(lines):\n'
     '    board = Board(lines)\n'
     '    for table in board.tables():\n'
     '        return [squash(c) for c in table["header"]]\n'
     '    return []\n'),

    ("D45 a table bound by a COMPREHENSION generator",
     "round 11 review, correction 3: the sweep did not reach every branch — "
     "`_bind_element` is called for a comprehension's generators as well as "
     "for a `for` statement, and only the statement form was planted. Round "
     "10's review named the indexed list of dicts; this is the same list "
     "walked by a comprehension",
     "bin/perry-probe-d45",
     'from tables import squash, split_row\n'
     'def tables_of(lines):\n'
     '    out = []\n'
     '    for line in lines:\n'
     '        out.append({"header": split_row(line)})\n'
     '    return out\n'
     'def read(lines):\n'
     '    return [squash(c) for t in tables_of(lines) for c in t["header"]]\n'),

    ("D46 a tuple unpack whose element is one CELL",
     "round 11 review, correction 3: the sweep did not reach every branch — "
     "the tuple-unpack branch has a `cell()` half and nothing planted it. "
     "`bin/perry_store.py:857` is `i, cells = row['line'], row['cells']`, so "
     "unpacking element-wise out of a carried row is this file's own idiom",
     "bin/perry-probe-d46",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    t = {"header": split_row(line)}\n'
     '    first, rest = t["header"][0], t["header"][1:]\n'
     '    return squash(first) == "id"\n'),

    ("D47 a row written INTO a dict, then folded out of it",
     "round 11 review, correction 3: the sweep did not reach every branch — "
     "the SUBSCRIPT half of the carried-write branch was unplanted while the "
     "attribute half was pinned by `D37`. `D24` is its sibling: a dict "
     "assignment built the header index, this one holds the header row",
     "bin/perry-probe-d47",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    spec = {}\n'
     '    spec["header"] = split_row(line)\n'
     '    return [squash(c) for c in spec["header"]]\n'),

    ("D40 a dict-carried row, SCALAR on one cell",
     "round 10 review, the FAIL: a header row carried through a dict key is "
     "invisible to BOTH halves — the scalar half is planted separately "
     "because, as round 9 put it, the two halves of the net are separate",
     "bin/perry-probe-d40",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    t = {"header": split_row(line)}\n'
     '    return squash(t["header"][0]) == "id"\n'),

    ("D41 a dict-carried row folded through `ops.norm`",
     "round 10 review, the FAIL: and with the repository's other spelling of "
     "the rule, `ops.norm` — `Q1_opsnorm_dict ESCAPED t = {'header': "
     "split_row(line)}; [ops.norm(c) for c in t['header']]`",
     "bin/perry-probe-d41",
     'import ops\n'
     'from tables import split_row\n'
     'def read(line):\n'
     '    t = {"header": split_row(line)}\n'
     '    return [ops.norm(c) for c in t["header"]]\n'),

    ("D24 a dict-ASSIGNMENT header index",
     "round 7 Finding 2: escapes include ... a dict-assignment header index",
     "bin/perry-probe-d24",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    idx = {}\n'
     '    for i, c in enumerate(split_row(line)):\n'
     '        idx[squash(c)] = i\n'
     '    return idx\n'),
]

#: **Correct code. Criterion 4 of the spec is this list**, and round 7 reported
#: six of these eight. Round 8 reported one — `C05` — and that one failure is
#: what failed round 8: appending an ordinary multi-value-cell normalizer to a
#: real reader turned `bash tests/run` red, and one of the two failing tests
#: was named `test_value_normalizers_are_not_flagged`.
CLEAN = [
    ("C01 the correct reader",
     "TASK-050 spec amendment: one `header_index()` becomes the only "
     "function allowed to fold a header cell — this is that shape, and a "
     "check that reported it would report the answer",
     "bin/perry-probe-c01",
     'from tables import header_index, split_row\n'
     'def read(line):\n    return header_index(split_row(line))\n'),

    ("C02 cells kept VERBATIM",
     "round 8's harness: the live shape at bin/perry-diagnose",
     "bin/perry-probe-c02",
     'from tables import split_row\n'
     'def read(line):\n    return [c.strip("*` ") for c in split_row(line)]\n'),

    ("C03 a value normalizer over aliases",
     "spec criterion 4: value normalizers keep their own rules, deliberately",
     "bin/perry-probe-c03",
     'def read(aliases):\n    return [a.strip().lower() for a in aliases]\n'),

    ("C04 a value normalizer over directory names",
     "round 8's harness: the live shape at bin/perry-diagnose",
     "bin/perry-probe-c04",
     'def read(inventory):\n    return [d.lower() for d in inventory["dirs"]]\n'),

    ("C05 a MULTI-VALUE CELL split on `|` — round 8's declared false positive",
     "round 8 review: appending an ordinary multi-value-cell normalizer to a "
     "real reader turns `bash tests/run` RED, and one of the two failing tests "
     "is named `test_value_normalizers_are_not_flagged`",
     "bin/perry-probe-c05",
     'def tags(cell):\n    return [t.strip().lower() for t in cell.split("|")]\n'),

    ("C06 the same multi-value cell, folded through THE ONE RULE",
     "round 5 review, latent risk: `tags = [t.strip().lower() for t in "
     "cell.split(\"|\")]` is flagged — the harder version of C05, because here "
     "the fold IS `squash` and only the row inference can separate them",
     "bin/perry-probe-c06",
     'from tables import squash\n'
     'def tags(cell):\n    return [squash(t) for t in cell.split("|")]\n'),

    ("C07 the prose keyword tokenizer",
     "round 7 Finding 4: one character from firing on live code — adding "
     "`.lower()` to `bin/perry-knowledge:242`'s prose tokenizer",
     "bin/perry-probe-c07",
     'import re\n'
     'def keywords(text):\n'
     '    return [w.lower() for w in re.findall(r"\\w+", text)]\n'),

    ("C08 a Status/Outcome value normalizer over a row's VALUES",
     "spec criterion 4: `Status`, `Outcome` and `parse_frequency` normalize "
     "what a project wrote, not which column it wrote it in",
     "bin/perry-probe-c08",
     'def statuses(records):\n'
     '    return {(r.get("status") or "").strip().lower() for r in records}\n'),

    ("C09 a stage-vocabulary fold over declared spellings",
     "round 7's eight legitimate shapes, carried since round 8",
     "bin/perry-probe-c09",
     'VOCAB = ["New", "In review", "Done"]\n'
     'def stages():\n    return {v.casefold() for v in VOCAB}\n'),

    ("C10 `squash` of a CANONICAL column name",
     "round 8 result § 1: scalar `squash` of a canonical column NAME being "
     "compared against a folded header is untouched and unchecked",
     "bin/perry-probe-c10",
     'from tables import squash\n'
     'def accepted(column):\n    return [squash(n) for n in (column, "id")]\n'),

    ("C11 `squash` of a single VALUE in a file that splits rows",
     "round 4: add one `squash()` call on a VALUE — which is what "
     "bin/perry-state, bin/perry-diagnose and bin/perry-explain all "
     "legitimately do",
     "bin/perry-probe-c11",
     'from tables import squash, split_row\n'
     'def read(line):\n'
     '    cells = split_row(line)\n'
     '    return squash("Status"), cells\n'),

    ("C13 a dict of VALUES, folded",
     "round 10 review, the FAIL, and criterion 4 of the spec: the fix must "
     "teach `source()` that a subscript of a dict this file built is a ROW — "
     "a dict whose value is a value is not, and a check that cannot tell "
     "them apart is the false-positive generator round 8 was failed for",
     "bin/perry-probe-c13",
     'from tables import squash\n'
     'def read(record):\n'
     '    d = {"status": record.get("status", "")}\n'
     '    return squash(d["status"])\n'),

    ("C14 a generator yielding a dict of VALUES",
     "round 10 review, the FAIL: the same sentence for the `yield` half — "
     "the entry that must be caught (`D39`) and this one differ only in "
     "whether what was put in the dict came off a row, which is the "
     "provenance the design is stated over",
     "bin/perry-probe-c14",
     'from tables import squash\n'
     'def statuses(records):\n'
     '    for r in records:\n'
     '        yield {"status": r.get("status", "")}\n'
     'def read(records):\n'
     '    return [squash(d["status"]) for d in statuses(records)]\n'),

    ("C12 a row transformed but never FOLDED",
     "TASK-050 spec, opening: `**Default** rung` lowercases to `default** "
     "rung` and matches nothing — the rule is about the FOLD, and `.upper()` "
     "resolves no column, so a check that reported this read a shape",
     "bin/perry-probe-c12",
     'from tables import split_row\n'
     'def read(line):\n    return [c.upper() for c in split_row(line)]\n'),
]

#: **The declared limit, planted and measured rather than described.**
#:
#: A reader that invents its OWN rule calls no blessed symbol, so
#: `offenders_by_symbol` is blind to every entry below *by construction*. This
#: is the class round 8 reported as "30 of 30 caught" using a net that seven
#: rounds had defeated and that reported correct code; round 9 deleted that net
#: and states the consequence as a number.
#:
#: What covers this class instead is
#: `tests/test_header_index_is_the_only_fold.py §
#: TestTheDecoratedHeaderReachesTheOneFold` — a reader that grows its own rule
#: stops calling `header_index`, and the decorated cells it used to resolve
#: stop arriving. `test_a_bolded_kr_header_still_yields_the_KR` is the same
#: property asserted behaviourally on the one site that historically lost data.
SECOND_RULE = [
    ("S01 the original spelling",
     "round 2: three copies in files that never imported `squash`",
     "bin/perry-probe-s01",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("S02 the loop subject renamed",
     "round 3: the pattern matched a SPELLING",
     "bin/perry-probe-s02",
     "def read(header):\n    return [h.strip().lower() for h in header]\n"),

    ("S03 a second rule in a SUBDIRECTORY",
     "round 3: a SUBDIRECTORY was invisible",
     "bin/lib/probe_s03.py",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("S04 the parenthesised comprehension",
     "round 4: the `[` had to sit right after the `=`",
     "bin/perry-probe-s04",
     "from tables import split_row\n"
     "def read(prev, ok):\n"
     "    header = ([c.strip().lower() for c in split_row(prev)] if ok else [])\n"
     "    return header\n"),

    ("S05 a generator expression",
     "round 4 verdict: nine planted readers ... a dict comprehension, a "
     "GENERATOR EXPRESSION, a helper whose header parameter is named `titles`",
     "bin/perry-probe-s05",
     "from tables import split_row\n"
     "def read(line):\n"
     "    return tuple(c.strip().lower() for c in split_row(line))\n"),

    ("S06 a helper whose header parameter is named `titles`",
     "round 4 verdict: a helper whose header parameter is named `titles`",
     "bin/perry-probe-s06",
     "def read(titles):\n    return [t.strip().lower() for t in titles]\n"),

    ("S07 a list comp whose iterable is named `row`",
     "round 4 verdict: a list comp whose iterable is named `row`",
     "bin/perry-probe-s07",
     "def read(row):\n    return [c.strip().lower() for c in row]\n"),

    ("S08 a bare `return [...]`",
     "round 4 verdict: a `return [...]`",
     "bin/perry-probe-s08",
     "from tables import split_row\n"
     "def read(line):\n"
     '    return [c.strip("*` ").lower() for c in split_row(line)]\n'),

    ("S09 a multi-line comprehension",
     "round 4 verdict: a multi-line comprehension",
     "bin/perry-probe-s09",
     "from tables import split_row\n"
     "def read(line):\n"
     "    return [\n"
     '        c.strip("*` ").lower()\n'
     "        for c in split_row(line)\n"
     "    ]\n"),

    ("S10 a SCALAR header-row test under `bin/lib/`",
     "round 4 verdict: a scalar header-row test planted at BOTH "
     "bin/lib/scalar.py and viewer/scalar_reader.py",
     "bin/lib/probe_s10.py",
     "from tables import split_row\n"
     "def read(line):\n"
     '    return split_row(line)[0].strip("*` ").lower() == "file"\n'),

    ("S11 the same SCALAR test under `viewer/`",
     "round 4 verdict: ... and viewer/scalar_reader.py",
     "viewer/probe_s11.py",
     "from tables import split_row\n"
     "def read(line):\n"
     '    return split_row(line)[0].strip("*` ").lower() == "file"\n'),

    ("S12 a reader with NO shebang and no suffix",
     "round 4: the SAME BYTES are green at bin/perry-rowdump, red the moment "
     "`#!/usr/bin/env python3` is prepended",
     "bin/probe-s12",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("S13 a reader with a non-`.py` dotted suffix",
     "round 4: any non-`.py` suffix returns `False` without reading anything",
     "bin/probe_s13.reader",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("S14 a reader OUTSIDE `bin/` and `viewer/`",
     "round 8 review, Finding 1: ESCAPED R4 · python reader outside bin/ and "
     "viewer/ (packs/)",
     "packs/probe_s14.py",
     "def read(cells):\n    return [c.strip().lower() for c in cells]\n"),

    ("S15 `.casefold()` in a non-splitting helper",
     "round 5 review, Finding 1, case A: `.casefold()` in a non-splitting "
     "helper taking `cells` — escapes both",
     "bin/perry-probe-s15",
     "def read(cells):\n    return [c.strip().casefold() for c in cells]\n"),

    ("S16 `.casefold()` plus an own splitter, in a file that has `squash`",
     "round 5 review, Finding 1, case C: `.casefold()` + own splitter, in a "
     "file that already contains `squash` — escapes both",
     "bin/perry-probe-s16",
     "from tables import squash\n"
     "def elsewhere(x):\n    return squash(x)\n"
     'def read(line):\n'
     '    return [c.strip().casefold() for c in line.split("|")]\n'),

    ("S17 a `PIPE` constant splitter",
     "round 5 review, Finding 1, case D: `.lower()`, splitter via a "
     "`PIPE = \"|\"` constant — escapes both",
     "bin/perry-probe-s17",
     'PIPE = "|"\n'
     "def read(line):\n"
     "    return [c.strip().lower() for c in line.split(PIPE)]\n"),

    ("S18 `re.split` instead of `str.split`",
     "round 5 review, Finding 1, case E: `.lower()`, splitter via "
     "`re.split(r\"\\|\", line)` — escapes both",
     "bin/perry-probe-s18",
     "import re\n"
     "def read(line):\n"
     '    return [c.strip().lower() for c in re.split(r"\\|", line)]\n'),

    ("S19 a `for`/`append` loop with a second rule",
     "round 5 review, Finding 1, case H: plain `for` loop with `.append()` "
     "instead of a comprehension — escapes both",
     "bin/perry-probe-s19",
     "def read(cells):\n"
     "    out = []\n"
     "    for c in cells:\n"
     "        out.append(c.strip().lower())\n"
     "    return out\n"),

    ("S20 a dict-comprehension header index with a second rule",
     "round 5 review, Finding 1, case F: dict-comprehension header index",
     "bin/perry-probe-s20",
     "def read(cells):\n"
     "    return {c.strip().lower(): i for i, c in enumerate(cells)}\n"),

    ("S21 the second rule factored into a scalar helper `_norm`",
     "round 5 review, Finding 1, case G: the rule factored into a scalar "
     "helper `_norm`",
     "bin/perry-probe-s21",
     'def _norm(s):\n    return s.strip("*` ").lower()\n'
     "from tables import split_row\n"
     "def read(line):\n    return [_norm(c) for c in split_row(line)]\n"),

    ("S22 `map()` instead of a comprehension",
     "round 5 review, Finding 2: the `.casefold()` and `map()` blind spots",
     "bin/perry-probe-s22",
     "def read(cells):\n    return list(map(str.lower, cells))\n"),

    ("S23 the round 5 DECISIVE case, appended to `viewer/parsers.py`",
     "round 5 review, Finding 2: `def parse_foreign_board_header(line): "
     "return [c.strip(\"*` \").casefold() for c in line.split(\"|\") if "
     "c.strip()]` — both guards reporting nothing",
     "viewer/probe_s23.py",
     "def parse_foreign_board_header(line):\n"
     '    return [c.strip("*` ").casefold() for c in line.split("|") '
     "if c.strip()]\n"),

    ("S24 P21, `split_row` on its own line",
     "round 7 Finding 2: P21 is the one that matters — `parts = "
     "split_row(line)` then `[c.strip(\"*` \").casefold() for c in parts]`, "
     "the most ordinary spelling there is",
     "bin/perry-probe-s24",
     "from tables import split_row\n"
     "def parse_foreign_header_v2(line):\n"
     "    parts = split_row(line)\n"
     '    return [c.strip("*` ").casefold() for c in parts]\n'),

    ("S25 a SLICE of the row with a second rule",
     "round 7 Finding 2: escapes include `cells[1:]`",
     "bin/perry-probe-s25",
     "from tables import split_row\n"
     "def read(line):\n"
     "    cells = split_row(line)\n"
     "    return [c.strip().lower() for c in cells[1:]]\n"),

    ("S26 a dict-ASSIGNMENT header index with a second rule",
     "round 7 Finding 2: escapes include a dict-assignment header index",
     "bin/perry-probe-s26",
     "from tables import split_row\n"
     "def read(line):\n"
     "    idx = {}\n"
     "    for i, c in enumerate(split_row(line)):\n"
     "        idx[c.strip().lower()] = i\n"
     "    return idx\n"),

    ("S27 a `lambda` second-rule helper",
     "round 7 Finding 2: escapes include a `lambda` folding helper",
     "bin/perry-probe-s27",
     'fold = lambda s: s.strip("*` ").lower()\n'
     "from tables import split_row\n"
     "def read(line):\n    return [fold(c) for c in split_row(line)]\n"),

    ("S28 TWO levels of local indirection",
     "round 7 Finding 2: escapes include two-level local indirection",
     "bin/perry-probe-s28",
     "def _low(s):\n    return s.lower()\n"
     'def _key(s):\n    return _low(s.strip("*` "))\n'
     "from tables import split_row\n"
     "def read(line):\n    return [_key(c) for c in split_row(line)]\n"),

    ("S29 the splitter on a CLASS ATTRIBUTE",
     "round 7 Finding 2: escapes include a splitter on a class attribute",
     "bin/perry-probe-s29",
     'class Fmt:\n    SEP = "|"\n'
     "def read(line):\n"
     "    return [c.strip().lower() for c in line.split(Fmt.SEP)]\n"),

    ("S30 the splitter in a DICT",
     "round 7 Finding 2: escapes include a splitter ... in a dict",
     "bin/perry-probe-s30",
     'SEPS = {"row": "|"}\n'
     "def read(line):\n"
     '    return [c.strip().lower() for c in line.split(SEPS["row"])]\n'),

    ("S31 an ALIASED row parameter with a second rule",
     "round 7 Finding 2: escapes include an aliased row parameter "
     "(`cs = cells`)",
     "bin/perry-probe-s31",
     "from tables import split_row\n"
     "def read(line):\n"
     "    cs = split_row(line)\n"
     "    ks = cs\n"
     "    return [c.strip().lower() for c in ks]\n"),

    ("S32 `sorted(key=str.lower)`",
     "round 7 Finding 2: escapes include `sorted(key=str.lower)`",
     "bin/perry-probe-s32",
     "from tables import split_row\n"
     "def read(line):\n"
     "    return sorted(split_row(line), key=str.lower)\n"),

    ("S33 `filter` instead of a comprehension",
     "round 7 Finding 2: escapes include `filter`",
     "bin/perry-probe-s33",
     "from tables import split_row\n"
     "def read(line):\n"
     '    return list(filter(lambda c: c.lower() == "id", split_row(line)))\n'),

    ("S34 accumulation through `out.add`",
     "round 7 Finding 2: escapes include `out.add`",
     "bin/perry-probe-s34",
     "from tables import split_row\n"
     "def read(line):\n"
     "    out = set()\n"
     "    for c in split_row(line):\n"
     "        out.add(c.strip().casefold())\n"
     "    return out\n"),

    ("S35 accumulation through `out +=`",
     "round 7 Finding 2: escapes include `out +=`",
     "bin/perry-probe-s35",
     "from tables import split_row\n"
     "def read(line):\n"
     "    out = []\n"
     "    for c in split_row(line):\n"
     "        out += [c.strip().lower()]\n"
     "    return out\n"),

    ("S36 `zip` between the row and its values",
     "round 7 Finding 2: escapes include `zip`",
     "bin/perry-probe-s36",
     "from tables import split_row\n"
     "def read(line, values):\n"
     "    return {k.lower(): v for k, v in zip(split_row(line), values)}\n"),

    ("S37 a walrus",
     "round 7 Finding 2: escapes include a walrus",
     "bin/perry-probe-s37",
     "from tables import split_row\n"
     "def read(line):\n"
     "    if (cs := split_row(line)):\n"
     "        return [c.strip().lower() for c in cs]\n"
     "    return []\n"),

    ("S38 `functools.partial` of a folding helper",
     "round 7 Finding 2: escapes include `functools.partial`",
     "bin/perry-probe-s38",
     "import functools\n"
     "from tables import split_row\n"
     "def _norm(pad, s):\n    return s.strip(pad).lower()\n"
     'key = functools.partial(_norm, "*` ")\n'
     "def read(line):\n    return [key(c) for c in split_row(line)]\n"),

    ("S39 a SCALAR header-row test",
     "round 7 Finding 2: escapes include ... a scalar header-row test — "
     "ABSENT from round 8's corpus, and re-derived by round 8's reviewer as "
     "ESCAPED R7 · a SCALAR header-row test (the `fifth copy` shape, "
     "parsers.py:428)",
     "bin/perry-probe-s39",
     "from tables import split_row\n"
     "def read(line):\n"
     "    cells = split_row(line)\n"
     '    return cells[0].strip("*` ").lower() == "file"\n'),

    ("S40 a SCALAR test on a header cell, `header` variable",
     "round 8 review, Finding 1: ESCAPED R7 · scalar test on a header cell, "
     "header var (`header[0].strip().lower()`)",
     "bin/perry-probe-s40",
     "def read(header):\n"
     '    return header[0].strip().lower() == "file"\n'),

    ("S41 `str.translate` as the fold",
     "round 7 Finding 2: escapes include `str.translate`",
     "bin/perry-probe-s41",
     "from tables import split_row\n"
     "TBL = str.maketrans({})\n"
     "def read(line):\n"
     "    return [c.translate(TBL) for c in split_row(line)]\n"),
]

#: **What the reviews name but this corpus cannot reconstruct.** Round 5's
#: Finding 1 says *"a nine-case probe and five escaped both nets"* and its table
#: names seven of the nine — cases `B` and `I` appear in no sentence of the
#: review. They are counted in the denominator below and not planted, because
#: inventing a shape and labelling it `B` is exactly the substitution that hid
#: round 8's pruning.
UNRECOVERABLE = 2


def _copy() -> Path:
    """One `tempfile` copy of the tree, for planting into."""
    tmp = Path(tempfile.mkdtemp(prefix="perry-header-r9-"))
    shutil.copytree(PERRY_HOME, tmp / "t",
                    ignore=lambda d, names: [n for n in names
                                             if n in NOT_COPIED])
    return tmp


def _hits(root: Path, where: str) -> list[str]:
    """What the net reports about the file planted at `where`.

    Matched on the FULL relative path, not the basename: this corpus plants at
    `bin/`, `bin/lib/`, `viewer/` and `packs/`, and a basename match would read
    a hit in one directory as a hit in another — which is how a scan that never
    looked at a directory reports success there.
    """
    return [o for o in offenders_by_symbol(root) if o.startswith(where + ":")]


def _plant(root: Path, where: str, body: str) -> Path:
    """Write one corpus body to its path, with a shebang unless the entry's
    whole subject is not having one.

    **Round 9 review, smaller results:** *"`_plant` writes `SHEBANG + body`
    unconditionally, so `D20 no suffix and NO SHEBANG` — and `S12`, same label
    — are planted WITH `#!/usr/bin/env python3`. The entry cannot discriminate
    the round 4 hole it names."* Its proof is mutation R9-6: putting round 8's
    `is_python` back (`if p.suffix: return False`) reddens `D21` and **not**
    `D20`, because under that rule a suffix-less file with a shebang is still
    seen. Keyed on the PATH, which
    `test_no_two_entries_are_planted_at_the_same_path` already guarantees is
    unique, so the exception cannot silently spread to a second entry.
    """
    target = root / where
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body if where in NO_SHEBANG else SHEBANG + body)
    return target


def measure() -> dict:
    """The three fractions, computed rather than asserted."""
    tmp = _copy()
    root = tmp / "t"
    out = {"drift_escaped": [], "clean_flagged": [], "second_rule_caught": []}
    try:
        for key, corpus in (("drift_escaped", DRIFT),
                            ("clean_flagged", CLEAN),
                            ("second_rule_caught", SECOND_RULE)):
            for label, _source, where, body in corpus:
                target = _plant(root, where, body)
                try:
                    hit = bool(_hits(root, where))
                    if (key == "drift_escaped" and not hit) \
                            or (key != "drift_escaped" and hit):
                        out[key].append(label)
                finally:
                    target.unlink(missing_ok=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


class TestTheCorpusIsAuditable(unittest.TestCase):
    """**The three rules the rebuild is under.** Round 8's corpus failed all
    three: it dropped four shapes two reviews had named, re-used three labels
    for different shapes so the drop was invisible in the numbering, and cited
    no source for any entry."""

    def all_entries(self):
        return DRIFT + CLEAN + SECOND_RULE

    def test_no_label_is_re_used_for_a_different_shape(self):
        """The specific mechanism that hid round 8's pruning: *"the labels
        P23–P25 were re-used for three DIFFERENT shapes, so the omission is
        invisible in the numbering."*"""
        labels = [e[0] for e in self.all_entries()]
        dupes = sorted({l for l in labels if labels.count(l) > 1})
        self.assertEqual(dupes, [], f"labels re-used: {dupes}")
        keys = [l.split()[0] for l in labels]
        dupes = sorted({k for k in keys if keys.count(k) > 1})
        self.assertEqual(dupes, [], f"label KEYS re-used: {dupes}")

    def test_every_entry_carries_its_provenance(self):
        """A denominator you cannot audit is a denominator you cannot trust.
        Every entry quotes the review sentence it is derived from."""
        for label, source, _where, _body in self.all_entries():
            with self.subTest(label):
                self.assertTrue(source and len(source) > 30,
                                f"{label} cites no review line")
                self.assertRegex(source.lower(), r"round \d|spec|task-050")

    def test_no_two_entries_are_planted_at_the_same_path(self):
        """Two shapes at one path is one shape measured twice."""
        paths = [e[2] for e in self.all_entries()]
        dupes = sorted({p for p in paths if paths.count(p) > 1})
        self.assertEqual(dupes, [], f"paths re-used: {dupes}")

    def test_the_no_shebang_entries_are_planted_without_one(self):
        """**Round 9's D20 finding, closed by assertion rather than by
        comment.** Two entries — `D20` and `S12` — exist to discriminate round
        4's hole *"a file whose first line is a docstring, a `# -*- coding:`
        line, or a licence header is invisible"*, and `_plant` was prepending
        `#!/usr/bin/env python3` to both, so neither could. The reviewer's own
        proof was that mutation R9-6 (round 8's `is_python`) reddens `D21` and
        not `D20`.

        This asserts the bytes on disk, not the intent: every `NO_SHEBANG`
        path is a real corpus path, every entry whose label says NO SHEBANG is
        in the set, and what lands on disk starts with the body.
        """
        by_path = {e[2]: e for e in self.all_entries()}
        for where in sorted(NO_SHEBANG):
            with self.subTest(where):
                self.assertIn(where, by_path,
                              f"{where} is exempted from the shebang and is "
                              f"not a corpus path")
        claimed = {e[2] for e in self.all_entries()
                   if "NO SHEBANG" in e[0].upper()}
        self.assertEqual(claimed, set(NO_SHEBANG),
                         "an entry whose label says NO SHEBANG is planted "
                         "with one, or vice versa")
        tmp = _copy()
        root = tmp / "t"
        try:
            for where in sorted(NO_SHEBANG):
                with self.subTest(where):
                    target = _plant(root, where, by_path[where][3])
                    try:
                        text = target.read_text()
                        self.assertFalse(
                            text.startswith("#!"),
                            f"{where} is planted WITH a shebang, so it cannot "
                            f"discriminate the hole it names")
                        self.assertEqual(text, by_path[where][3])
                        self.assertEqual(Path(where).suffix, "")
                    finally:
                        target.unlink(missing_ok=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_denominator_is_at_least_round_8s_honest_one(self):
        """Round 8's reviewer put the honest denominator at *"30 of at least
        33"*. The rebuilt second-rule corpus alone is larger than that, and it
        is larger because it was derived from the reviews rather than from the
        previous corpus."""
        self.assertGreaterEqual(len(SECOND_RULE) + UNRECOVERABLE, 33)


class TestTheCopyItselfIsClean(unittest.TestCase):
    """The controls. Without them every result below is unreadable."""

    def test_an_unplanted_copy_reports_nothing(self):
        tmp = _copy()
        try:
            self.assertEqual(offenders_by_symbol(tmp / "t"), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_copy_carries_the_readers(self):
        """A copy that lost the tree would make every scan below vacuous."""
        tmp = _copy()
        try:
            self.assertEqual(len(readers_under(tmp / "t")),
                             len(readers_under(PERRY_HOME)))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_control_is_caught_at_every_path_the_corpus_uses(self):
        """**Round 8's reviewer's method, adopted.** A planting that escapes
        proves nothing until a control planted at the SAME PATH is caught —
        otherwise "escaped" and "the scan never looked here" are the same
        result. This plants the same offending body at every distinct directory
        the corpus uses."""
        tmp = _copy()
        root = tmp / "t"
        control = ('from tables import squash, split_row\n'
                   'def read(line):\n'
                   '    return [squash(c) for c in split_row(line)]\n')
        dirs = sorted({str(Path(e[2]).parent) for e in DRIFT + SECOND_RULE})
        try:
            for d in dirs:
                where = f"{d}/perry-probe-control"
                with self.subTest(where):
                    target = _plant(root, where, control)
                    try:
                        self.assertTrue(
                            _hits(root, where),
                            f"the control planted at {where} was NOT caught, "
                            f"so nothing this corpus reports about {d} means "
                            f"anything")
                    finally:
                        target.unlink(missing_ok=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestTheDriftCorpusIsCaught(unittest.TestCase):
    """**The net's own class, and every entry must be caught.**

    The one rule applied to a header row, or to a cell of one, outside
    `header_index`. This is what the amendment asks the guard to be: *"no call
    to `squash` on a row cell exists outside `header_index()`. State it over the
    symbol, not over a shape."*
    """

    def test_each_drift_shape_is_caught(self):
        tmp = _copy()
        root = tmp / "t"
        try:
            for label, source, where, body in DRIFT:
                with self.subTest(label):
                    target = _plant(root, where, body)
                    try:
                        self.assertTrue(
                            _hits(root, where),
                            f"planted the ONE RULE outside `header_index` at "
                            f"{where} ({label}) and the check reported nothing "
                            f"about it. Source: {source}")
                    finally:
                        target.unlink(missing_ok=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestCorrectCodeIsNotReported(unittest.TestCase):
    """**Criterion 4, and it is now ZERO rather than one.**

    Round 7 reported six of eight legitimate shapes. Round 8 reported one and
    declared it, and that one declaration is what failed round 8: the shape it
    declared is an ordinary value normalizer, and appending one to a real reader
    turned the suite red. The inference that produced it — treating any
    `.split("|")` as a row's cells — is deleted, so `C05` and `C06` are silent
    for a structural reason and not by an exception.
    """

    def test_each_clean_shape_is_left_alone(self):
        tmp = _copy()
        root = tmp / "t"
        try:
            for label, source, where, body in CLEAN:
                with self.subTest(label):
                    target = _plant(root, where, body)
                    try:
                        self.assertEqual(
                            _hits(root, where), [],
                            f"{label} at {where} was reported, and it is "
                            f"correct code — the false-positive failure every "
                            f"round of this row has warned about. "
                            f"Source: {source}")
                    finally:
                        target.unlink(missing_ok=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_multi_value_cell_normalizer_is_not_reported_either_way(self):
        """**The test round 8's reviewer asked for, asserting what it claims.**

        Round 8 asserted only that `cell.split("|")` and `line.split("|")` get
        the SAME verdict — which *"any name-blind check satisfies, including one
        that flags neither"*. It measured name-blindness, not undecidability.

        The claim now is stronger and is what the design actually buys: BOTH are
        silent, because neither is a row unless `split_row` produced it. The
        home-made splitter in the second one is not this check's business —
        criterion 3 owns it, and `tests/test_row_integrity.py §
        test_no_tool_splits_a_row_on_a_raw_pipe` reports a bare `.split("|")`
        anywhere in `bin/` or `viewer/` whatever the receiver is called.
        """
        tmp = _copy()
        root = tmp / "t"
        cases = [
            ("bin/perry-probe-fp-cell",
             'def tags(cell):\n'
             '    return [t.strip().lower() for t in cell.split("|")]\n'),
            ("bin/perry-probe-fp-line",
             'def read(line):\n'
             '    return [t.strip().lower() for t in line.split("|")]\n'),
        ]
        try:
            for where, body in cases:
                with self.subTest(where):
                    target = _plant(root, where, body)
                    try:
                        self.assertEqual(_hits(root, where), [])
                    finally:
                        target.unlink(missing_ok=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_row_splitter_half_is_owned_by_criterion_3(self):
        """The claim above leans on another module. Assert the lean, so it
        cannot rot: `test_row_integrity`'s `SPLIT_RE` matches a bare
        `.split("|")` and its scan covers `bin/` and `viewer/`."""
        import test_row_integrity as RI
        rule = RI.TestEveryoneReadsTheRowTheSameWay.SPLIT_RE
        self.assertTrue(rule.search('for t in cell.split("|"):'))
        self.assertTrue(rule.search('for t in line.split("|"):'))


class TestTheSecondRuleCorpusEscapes(unittest.TestCase):
    """**The declared limit, planted and measured.**

    Forty-one shapes the round 4, 5 and 7 reviews name, each quoting the line it
    came from. Every one invents its OWN rule, so it calls no blessed symbol and
    the symbol check cannot see it. That is not a bug to be fixed by an eighth
    detector — seven rounds are the evidence that the detector cannot be
    finished, and round 8 is the evidence that keeping an unfinished one is
    worse than not having it.

    `TestTheCopyItselfIsClean §
    test_the_control_is_caught_at_every_path_the_corpus_uses` is what makes
    these zeros readable: the same offending body planted at each of these
    directories IS caught, so "escaped" here means the shape, not the path.
    """

    def test_each_second_rule_shape_escapes(self):
        tmp = _copy()
        root = tmp / "t"
        try:
            for label, source, where, body in SECOND_RULE:
                with self.subTest(label):
                    target = _plant(root, where, body)
                    try:
                        self.assertEqual(
                            _hits(root, where), [],
                            f"{label} is now CAUGHT — good news. Move it into "
                            f"DRIFT, keeping its label and its source, and "
                            f"re-derive the fraction in the round's evidence. "
                            f"Source: {source}")
                    finally:
                        target.unlink(missing_ok=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    m = measure()
    print(f"DRIFT       caught  : {len(DRIFT) - len(m['drift_escaped'])} "
          f"of {len(DRIFT)}")
    for e in m["drift_escaped"]:
        print(f"  ESCAPED: {e}")
    print(f"CLEAN       flagged : {len(m['clean_flagged'])} of {len(CLEAN)}")
    for e in m["clean_flagged"]:
        print(f"  FLAGGED: {e}")
    print(f"SECOND_RULE caught  : {len(m['second_rule_caught'])} "
          f"of {len(SECOND_RULE)} (+{UNRECOVERABLE} the reviews do not name) "
          f"— zero is the DECLARED limit, not a failure")
    for e in m["second_rule_caught"]:
        print(f"  CAUGHT : {e}")
