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
for `BOARD.md`, `OKR.md` and the config: a task row and a KR row are
read out of a store now and nothing asks a rendered document which column a
cell is. The last class measures that as a count. Everything above it survives
because it is what ADOPTION needs — a foreign project's board, a project's
`.perry/conformance.md` — and adoption parses by definition. The track
register left this list entirely when ADR-019 deleted the file its table was
in. A file that kept only the count would be green on a
reader that invented a sixth rule for a project arriving from outside Perry.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

COVERS = ("bin/", "viewer/", "templates/", "perry/", "tests/header_rule.py")

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
from tables import header_index, squash            # noqa: E402
# Imported ONCE. Round 7's review found this module importing `header_rule`
# twice, four lines apart.
import header_rule  # noqa: E402
from header_rule import (offenders_by_symbol, readers_under,  # noqa: E402
                         source_of)
import parsers as P  # noqa: E402

# The counter, not a second copy of it. `tests/parallel` puts `tests/` on the
# path the same way `discover` does, which is how `test_risks` already reaches
# `test_task_writer`.
import test_row_integrity as RI  # noqa: E402

import config_store  # noqa: E402

#: **The scan is one implementation, in `tests/header_rule.py`**, shared with
#: `tests/test_header_rule_harness.py`. Round 5's review found the harness
#: could not point the complement net at a planted copy — precisely because
#: there were two nets, one parameterised and one pinned to `PERRY_HOME`. There
#: is one now, and it takes a root.
READERS = readers_under(PERRY_HOME)


class TestAVanishedFileIsSkippedButATrackedOneIsNot(unittest.TestCase):
    """`source_of` decides what a missing file means, and the two answers differ.

    `READERS` is built once at import, so every guard here reads a list that
    can be stale by the time it reads it. Under the parallel runner that was
    not theoretical: this module was red in 3 of 3 full-suite runs and green in
    5 of 5 runs alone on 2026-09-03, through a `try` that caught `SyntaxError`
    and not `FileNotFoundError` (`TASK-334`).

    Tolerating the disappearance is only half the fix. A file `git` still
    tracks going missing mid-run is a real fault, and skipping it would let a
    shipped reader fall out of the domain silently — the failure `_domain()`
    had in `TASK-067`, where a guard whose domain quietly shrank went on
    reporting clean.
    """

    def test_no_guard_parses_straight_out_of_read_text(self):
        """The call sites must ROUTE, and only source can hold them to it.

        Reverting any of the three sites to `ast.parse(p.read_text(...))`
        leaves every behavioural test in this module green, because the race
        needs the parallel runner and a file that happens to vanish. That
        green revert is the finding: the property is structural, so the check
        has to be structural too — the shape already used by
        `test_perry_lint_binds_the_predicate_from_lib_rather_than_copying_it`.

        It looks for the composed form specifically, `ast.parse` applied
        directly to a `.read_text(...)` call, rather than banning `read_text`:
        `is_reader` reads a file to decide whether it is source at all and
        already catches `OSError` itself, and a ban would have to special-case
        it.
        """
        import ast as _ast
        for rel in ("tests/header_rule.py", "tests/test_one_header_rule.py"):
            src = (PERRY_HOME / rel).read_text(encoding="utf-8")
            tree = _ast.parse(src)
            for node in _ast.walk(tree):
                if not (isinstance(node, _ast.Call)
                        and isinstance(node.func, _ast.Attribute)
                        and node.func.attr == "parse"):
                    continue
                for arg in node.args:
                    bad = (isinstance(arg, _ast.Call)
                           and isinstance(arg.func, _ast.Attribute)
                           and arg.func.attr == "read_text")
                    self.assertFalse(bad, (
                        f"{rel}:{node.lineno} parses straight out of "
                        "read_text. A file that vanishes between the walk and "
                        "the read errors the guard instead of being skipped "
                        "(TASK-334) — route it through header_rule.source_of."))

    def test_a_missing_untracked_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(source_of(Path(d) / "gone.py"))

    def test_an_existing_tracked_file_is_read(self):
        text = source_of(PERRY_HOME / "bin" / "perry-lint")
        self.assertIsNotNone(text)
        self.assertIn("perry-lint", text)

    def test_a_missing_TRACKED_file_raises_and_names_the_path(self):
        """Patched rather than staged, and that is deliberate.

        The honest end-to-end fixture would `git add` a file and delete it, or
        rename a tracked one aside. Both mutate state the whole repository
        shares — the index, or a file another of the eight workers is reading —
        and this module's own defect is a parallelism race, so a test that
        introduces one to prove a point would be the wrong trade. The decision
        under test is `source_of`'s, not `git`'s; `_git_tracks` has its own two
        cases above and below.
        """
        real = header_rule._git_tracks
        header_rule._git_tracks = lambda p: True
        try:
            with tempfile.TemporaryDirectory() as d:
                missing = Path(d) / "tracked-but-gone.py"
                with self.assertRaises(AssertionError) as caught:
                    source_of(missing)
            self.assertIn(str(missing), str(caught.exception))
        finally:
            header_rule._git_tracks = real

    def test_git_tracks_answers_both_ways(self):
        self.assertTrue(header_rule._git_tracks(PERRY_HOME / "bin" / "perry-lint"))
        with tempfile.TemporaryDirectory() as d:
            probe = Path(d) / "never-added.py"
            probe.write_text("x = 1\n")
            self.assertFalse(header_rule._git_tracks(probe))


class TestOneRuleForAHeaderCell(unittest.TestCase):

    def test_the_two_rules_actually_diverge(self):
        """If they agreed, this whole module would be ceremony. They do not."""
        self.assertNotEqual(squash("**Default** rung"),
                            "**Default** rung".strip("*` ").lower())
        self.assertEqual(squash("**Default** rung"), "default rung")
        self.assertEqual(squash("Default  rung"), "default rung")

    def test_nothing_outside_header_index_maps_squash_across_a_row(self):
        """**Round 8's check, and it is over a SYMBOL.**

        `viewer/tables.py § header_index` is the only function allowed to fold
        a header cell. The check that keeps it that way is not a shape to
        recognise — seven rounds of evidence say a shape check loses — it is
        an equality against zero over one symbol: nothing outside that function
        maps `squash` (or its `norm` alias) across a row's cells.

        It holds no list of variable names and it cannot fire on a value
        normalizer, because a value normalizer folds a value and not a row.
        """
        found = offenders_by_symbol(PERRY_HOME)
        self.assertEqual(found, [],
                         "`squash` is mapped across a row outside "
                         "`header_index`:\n" + "\n".join(found))

    def test_the_one_fold_is_reachable_and_is_the_one_rule(self):
        """`header_index` folds by `squash` and by nothing else, so the symbol
        check above is about the rule and not merely about a call site."""
        self.assertEqual(header_index(["**Default** rung", "  Status "]),
                         ["default rung", "status"])
        self.assertEqual(header_index(["Status"], alias={"status": "s"}.get),
                         ["s"])

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
            text = source_of(path)
            if text is None:
                continue            # vanished mid-run; see header_rule.source_of
            try:
                tree = ast.parse(text)
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
        self.assertEqual(offenders_by_symbol(PERRY_HOME), [])

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


# `TestTheDecoratedHeaderIsActuallyRead` stood here. It fed
# `bin/perry-state § parse_tracks` a `## Tracks` table whose header cell read
# `| **Default** rung |` and asserted the column was still resolved — the
# behavioural half of the `squash` rule, so that a guard which only greps could
# not be satisfied by a rename.
#
# ADR-019 deleted `.perry/config.md`, and `parse_tracks` with it. A track is a
# store record, its fields are keys, and there is no header cell to decorate:
# the question this class asked cannot be asked of the register any more. It is
# removed rather than re-pointed, because the other documents in this module's
# scope carry their own decorated-header cases and a third copy aimed at
# whatever was nearest would be a test kept for its name.


class TestTheFifthCopy(unittest.TestCase):
    """`read_legacy_conformance` resolves its header row with `squash`.

    **The reader moved and the rule did not** (TASK-234). The record is
    `.perry/conformance.jsonl` now, which has no header row for anything to
    resolve; the markdown reader below is still shipped, is still the one thing
    that reads a pre-TASK-234 record, and still has to tell a header from a
    declaration. Pointed at `read_legacy_conformance` rather than deleted,
    because the copy this class is named for is exactly where it always was —
    if it is ever reverted, a bolded header is a laundered declaration at the
    one-way door `perry-conform migrate` opens.

    The original text follows, unchanged, because it is the finding:

    `read_conformance` resolved its header row with `.strip("` ").lower()`.

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
            # A CANONICAL data row. It used to be `| `BOARD.md` | …` — a
            # backticked path — which TASK-241 now refuses as unreadable,
            # because a decorated path cell was how a hand-written row flipped
            # a real file's verdict. The decoration under test here is on the
            # HEADER, not the path, so the row's own shape is incidental to
            # this class and the test keeps all of its power: bold the header
            # while `squash` is broken and the header is still read as a
            # declaration whose version cell is not a number, which is exactly
            # what `test_a_bolded_header_is_not_reported_as_a_broken_row`
            # catches.
            "| BOARD.md | 2 | 2026-08-18 | migrate |\n")
        rec = P.read_legacy_conformance(tmp)
        # A guard rail on the guard rail: this class exists to compare a
        # DECORATED header against a plain one, and `([], [])` == `([], [])`
        # is a comparison that holds when the reader has stopped reading. The
        # plain case must be non-empty or every subTest below is vacuous —
        # which is what it became the moment `read_conformance` was pointed at
        # the store and this probe was not.
        assert rec.declarations or rec.unreadable, (
            "read_legacy_conformance returned nothing at all for a record it "
            "should read — the comparisons in this class would be vacuous")
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
    files. `BOARD.md`, `OKR.md` and the config are stores now, and a
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
        config_store.write_config(self.root, {"State root": "."})
        self.assertEqual(
            self.resolutions(lambda: P.resolve_state_root(self.root)), {})


if __name__ == "__main__":
    unittest.main()
