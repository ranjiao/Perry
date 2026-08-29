"""One rule for a header cell, across every reader — the category, not the list.

TASK-050 unified `viewer/parsers.py` onto `viewer/tables.py § squash` and was
reported done. A fresh-context V4 review then found **three surviving second
implementations** in files that never imported it — `bin/perry-state` (twice)
and `bin/perry-diagnose` (once) — each resolving a header cell with
`.strip("*` ").lower()`.

The two rules agree on plain text and disagree on decoration that covers only
part of a cell:

    '**Default** rung'   .lower() → 'default** rung'      squash → 'default rung'
    'Default  rung'      .lower() → 'default  rung'       squash → 'default rung'

So a project that bolded half a header lost that column silently: `parse_tracks`
reported no `Default rung` for every track, and `perry-diagnose.md_table` — which
reads the **user's** board and OKR — lost it too.

This module is the guard the previous round did not have. The previous one was
`assertIs(P.squash, PT.squash)`, which asserts two modules share a function and
says nothing about a third module that imported neither.

**TASK-094 narrowed what this is for.** ADR-007 decision 4 removes the question
for `BOARD.md`, `OKR.md` and `.perry/config.md`: a task row and a KR row are
read out of a store now and nothing asks a rendered document which column a
cell is. The last class measures that as a count. Everything above it survives
because it is what ADOPTION needs — a foreign project's board, a project's
`.perry/config.md § Tracks` register, `.perry/conformance.md` — and adoption
parses by definition. A file that kept only the count would be green on a
reader that invented a sixth rule for a project arriving from outside Perry.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
sys.path.insert(0, str(PERRY_HOME / "tests"))
from tables import squash            # noqa: E402
from header_rule import offenders, readers_under   # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from header_rule import offenders, readers_under  # noqa: E402
import parsers as P  # noqa: E402

# The counter, not a second copy of it. `tests/parallel` puts `tests/` on the
# path the same way `discover` does, which is how `test_risks` already reaches
# `test_task_writer`.
import test_row_integrity as RI  # noqa: E402

#: **The scan is one implementation, in `tests/header_rule.py`**, shared with
#: `tests/test_header_rule_harness.py`. Round 5's review found the harness
#: could not point the complement net at a planted copy — precisely because
#: there were two nets, one parameterised and one pinned to `PERRY_HOME`. There
#: is one now, and it takes a root.
READERS = readers_under(PERRY_HOME)


class TestOneRuleForAHeaderCell(unittest.TestCase):

    def test_the_two_rules_actually_diverge(self):
        """If they agreed, this whole module would be ceremony. They do not."""
        self.assertNotEqual(squash("**Default** rung"),
                            "**Default** rung".strip("*` ").lower())
        self.assertEqual(squash("**Default** rung"), "default rung")
        self.assertEqual(squash("Default  rung"), "default rung")

    def test_no_reader_folds_a_header_cell_by_a_second_rule(self):
        """The whole category, in one assertion, over the whole tree.

        **This replaced a regex over source lines and a whole-file substring
        test, and both were defeated by the round 5 reviewer.** The regex knew
        the spellings it had been taught; the substring test asked whether the
        token "squash" appeared anywhere in the file, which all 9 row-splitting
        readers already satisfy — so it contributed nothing against a new rule
        added to an existing reader. The reviewer proved it by appending a
        `.casefold()` header reader to `viewer/parsers.py` and getting `[]`
        from both.

        `tests/header_rule.py` asks the parser instead: a collection built by
        mapping over a row's cells, whose element expression case-folds, must
        fold through `squash`.
        """
        found = offenders(PERRY_HOME)
        self.assertEqual(found, [], "header cells folded by a second rule:\n"
                                    + "\n".join(found))

    def test_value_normalizers_are_not_flagged(self):
        """**The judgement in this module, asserted with a live number.**

        The tree holds ~30 case-folding comprehensions and not one is a header
        resolution: they lowercase directory names, aliases, spellings, modes
        and stages. Those normalize what a project WROTE, not WHICH COLUMN it
        wrote it in, and every earlier round's docstring warns that widening
        the guard to cover them flags correct call sites — a guard that reports
        correct code is one people switch off.

        Asserting the count would make this fail on every unrelated edit. What
        must hold is that a large number of them exist and none is reported.
        """
        import ast
        folding = 0
        for path in READERS:
            try:
                tree = ast.parse(path.read_text(errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp,
                                     ast.GeneratorExp)):
                    if ".lower()" in ast.unparse(node) \
                            or ".casefold()" in ast.unparse(node):
                        folding += 1
        self.assertGreater(folding, 20,
                           "the tree stopped normalizing values — this test is "
                           "measuring nothing and should be re-derived")
        self.assertEqual(offenders(PERRY_HOME), [])

    def test_the_norm_alias_is_the_same_object_and_not_a_second_copy(self):
        """`bin/perry-migrate` reaches the rule as `L.norm`. That is only
        acceptable while `norm` IS `squash`; the day someone gives it a body,
        the alias becomes the fifth implementation and this goes red."""
        loader = importlib.machinery.SourceFileLoader(
            "perry_lint", str(PERRY_HOME / "bin" / "perry-lint"))
        spec = importlib.util.spec_from_loader("perry_lint", loader)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertIs(mod.norm, squash)


class TestTheDecoratedHeaderIsActuallyRead(unittest.TestCase):
    """Behaviour, not grep. A guard that only greps can be satisfied by a
    rename; this one fails if the column is lost."""

    CONFIG = (
        "# Perry configuration\n\n- State root: .\n\n## Tracks\n\n"
        "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | **Default** rung |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| ops | queue | OKR.md | new -> done | — | 3d | — | V2 |\n")

    def _parse(self, text):
        loader = importlib.machinery.SourceFileLoader(
            "perry_state", str(PERRY_HOME / "bin" / "perry-state"))
        spec = importlib.util.spec_from_loader("perry_state", loader)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.parse_tracks(text)

    def test_a_header_with_decoration_on_half_the_cell_still_resolves(self):
        tracks = self._parse(self.CONFIG)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].get("default_rung"), "V2",
                         "the bolded header lost its column")

    def test_the_plain_spelling_is_unchanged(self):
        tracks = self._parse(self.CONFIG.replace("**Default** rung", "Default rung"))
        self.assertEqual(tracks[0].get("default_rung"), "V2")


class TestTheFifthCopy(unittest.TestCase):
    """`read_conformance` resolved its header row with `.strip("` ").lower()`.

    That strips backticks and spaces and **leaves asterisks**, so a bolded
    `| **File** |` header was not recognised as the header — it was read as a
    DECLARATION whose version cell is not a number, and `perry-conform status`
    reported `unreadable row` against a correct file while `perry-lint` still
    said clean.

    The fifth live copy of this rule, in `viewer/parsers.py` — **the file the
    first pass claimed to have unified.** Found by a reviewer running an AST
    sweep over all 111 lowercasing sites rather than grepping for the ones it
    already knew about, which is the difference between checking the category
    and checking the instances.

    Neither of this task's own guards could see it: one enumerates `bin/` and
    one file of `viewer/`, and the behavioural guard's fixture bolds **whole
    cells**, where `squash` and `strip("` ").lower()` happen to agree.
    """

    def probe(self, header):
        import shutil, tempfile
        import parsers as P
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / ".perry").mkdir()
        (tmp / ".perry" / "conformance.md").write_text(
            f"# Conformance\n\n{header}\n| --- | --- | --- | --- |\n"
            "| `BOARD.md` | 2 | 2026-08-18 | migrate |\n")
        rec = P.read_conformance(tmp)
        return list(rec.declarations), rec.unreadable

    def test_decoration_on_the_header_changes_nothing(self):
        plain = self.probe("| File | Shape version | Declared | Route |")
        for header in ("| **File** | **Shape version** | **Declared** | "
                       "**Route** |",
                       "| `File` | Shape version | Declared | Route |",
                       "|  File  |  Shape version | Declared | Route |"):
            with self.subTest(header=header):
                self.assertEqual(self.probe(header), plain)

    def test_a_bolded_header_is_not_reported_as_a_broken_row(self):
        _, unreadable = self.probe(
            "| **File** | **Shape version** | **Declared** | **Route** |")
        self.assertEqual(unreadable, [])


class TestNoHeaderCellIsResolvedForAStore(unittest.TestCase):
    """Verification 1, the header-cell half. TASK-094, ADR-007 decision 4.

    **The rule above is not being hardened, it is being removed** — for three
    files. `BOARD.md`, `OKR.md` and `.perry/config.md` are stores now, and a
    reader that asks a rendered document which column a cell is, is asking
    about a shape that no longer exists. What survives is adoption of a
    foreign project, which parses by definition, and the zeros below are
    paired with the same read on an unadopted project so that a zero cannot be
    scored by a reader that stopped doing anything at all.

    The counting is `tests/test_row_integrity.py § reader_calls` — one
    implementation, because two would be the defect this module is named for.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "BOARD.md").write_text(RI.STORED_BOARD, encoding="utf-8")
        (self.root / "OKR.md").write_text(RI.STORED_OKR, encoding="utf-8")
        (self.root / "tasks.jsonl").write_text(
            json.dumps(RI.STORED_TASK_RECORD, ensure_ascii=False) + "\n",
            encoding="utf-8")
        (self.root / "okr.jsonl").write_text(
            json.dumps(RI.STORED_KR_RECORD, ensure_ascii=False) + "\n",
            encoding="utf-8")

    def resolutions(self, run) -> dict:
        return {reg: n for (reg, prim), n in RI.reader_calls(run).items()
                if prim == "squash"}

    def test_no_header_cell_of_a_task_table_is_resolved_from_the_store(self):
        with_store = self.resolutions(
            lambda: P.parse_board(RI.STORED_BOARD,
                                  tasks=P.load_task_store(self.root)))
        self.assertNotIn("_parse_task_table", with_store)
        # `heading_is` is how `## 主要风险` is recognised as `## Top risks`.
        # A SECTION HEADING is prose and squashing it is not resolving a
        # header cell — that is the distinction `viewer/tables.py § squash`
        # documents and the one this module's own `SECOND_RULE` narrows on.
        # Allowed by name, because silently excusing it is how the next real
        # call site would hide behind it.
        self.assertEqual(
            set(with_store) - RI.BOARD_REGISTERS_WITHOUT_A_STORE
            - {"heading_is"}, set(),
            f"a header cell was resolved for a stored register: {with_store}")

    def test_the_same_read_without_a_store_DOES_resolve_them(self):
        """The zero above must be about a call site that is no longer reached,
        not about a function that no longer resolves anything."""
        self.assertIn("_parse_task_table",
                      self.resolutions(lambda: P.parse_board(RI.STORED_BOARD)))

    def test_no_header_cell_of_the_okr_is_resolved_from_the_store(self):
        with_store = self.resolutions(
            lambda: P.parse_okr(RI.STORED_OKR,
                                krs=P.load_okr_store(self.root)))
        self.assertEqual(
            {k: v for k, v in with_store.items() if k != "heading_is"}, {},
            f"a header cell was resolved for OKR.md: {with_store}")
        self.assertIn("_parse_okr_objectives",
                      self.resolutions(lambda: P.parse_okr(RI.STORED_OKR)))

    def test_no_header_cell_of_the_config_is_resolved_here(self):
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Config\n\n- State root: .\n", encoding="utf-8")
        self.assertEqual(
            self.resolutions(lambda: P.resolve_state_root(self.root)), {})


if __name__ == "__main__":
    unittest.main()
