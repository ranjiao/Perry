"""`perry-task asks` — the User Input Queue as a query, answered asks included.

aiMark asked for a way to read answered asks and their answers without parsing
`perry/asks.jsonl`. `list --json § asks.items` leaves answered asks out by
design, so this is a second surface, and the property that matters most is the
one a second surface most easily loses: **it must not disagree with `list`
about which asks are open.** `TestTheDefaultIsTheSamePopulationAsList` holds
that, through the tool, on a project where both kinds exist.

Run: python3 tests/parallel test_asks_list
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))
sys.path.insert(0, str(ROOT / "tests"))

import test_add_writes_the_edge as M  # noqa: E402 — the fixture only
import parsers as P  # noqa: E402

TASK = ROOT / "bin" / "perry-task"


class Base(M.Fixture):

    def tool(self, d, *argv):
        return subprocess.run([sys.executable, str(TASK), *argv, "--root", str(d)],
                              capture_output=True, text=True, cwd=ROOT)

    def ask(self, d, needed, blocks="TASK-100"):
        proc = self.tool(d, "ask", "--needed", needed, "--blocks", blocks,
                         "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)["id"]

    def answer(self, d, uid, text):
        proc = self.tool(d, "answer", uid, "--answer", text, "--actor", "user")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def asks(self, d, *extra):
        proc = self.tool(d, "asks", "--json", *extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def two_kinds(self):
        """A project holding one open and one answered ask."""
        d = self.project()
        still_open = self.ask(d, "Which database should we use?", "TASK-100")
        closed = self.ask(d, "May we delete the legacy table?", "TASK-100, P003-O2-KR3")
        self.answer(d, closed, "Yes, After The Backup Runs")
        return d, still_open, closed


class TestTheDefaultIsTheSamePopulationAsList(Base):
    """The one property a second surface loses first."""

    def test_the_default_lists_only_open_asks(self):
        d, still_open, closed = self.two_kinds()
        ids = [a["id"] for a in self.asks(d)["asks"]]
        self.assertEqual([still_open], ids)

    def test_it_is_exactly_lists_asks_items(self):
        d, _, _ = self.two_kinds()
        proc = self.tool(d, "list", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        from_list = json.loads(proc.stdout)["asks"]
        mine = self.asks(d)
        self.assertEqual([a["id"] for a in from_list["items"]],
                         [a["id"] for a in mine["asks"]])
        self.assertEqual(from_list["open"], mine["open"])
        for theirs, ours in zip(from_list["items"], mine["asks"]):
            for key, value in theirs.items():
                self.assertEqual(value, ours[key], f"{key} differs from list")


class TestAllCarriesTheAnswer(Base):

    def test_all_includes_the_answered_ask(self):
        d, still_open, closed = self.two_kinds()
        ids = [a["id"] for a in self.asks(d, "--all")["asks"]]
        self.assertEqual({still_open, closed}, set(ids))

    def test_the_answer_and_its_date_are_fields(self):
        d, _, closed = self.two_kinds()
        entry = next(a for a in self.asks(d, "--all")["asks"] if a["id"] == closed)
        self.assertTrue(entry["answered"])
        self.assertRegex(entry["answered_on"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual("Yes, After The Backup Runs", entry["answer"],
                         "the answer must come back verbatim, case kept")

    def test_an_open_ask_has_no_answer(self):
        d, still_open, _ = self.two_kinds()
        entry = next(a for a in self.asks(d, "--all")["asks"]
                     if a["id"] == still_open)
        self.assertEqual((False, "", ""),
                         (entry["answered"], entry["answered_on"], entry["answer"]))

    def test_the_counts_cover_the_whole_register_either_way(self):
        d, _, _ = self.two_kinds()
        for extra in ((), ("--all",)):
            with self.subTest(flags=extra):
                out = self.asks(d, *extra)
                self.assertEqual((1, 1), (out["open"], out["answered"]))
                self.assertEqual(len(out["asks"]), out["count"])

    def test_blocks_ids_are_the_ids_in_the_cell(self):
        d, _, closed = self.two_kinds()
        entry = next(a for a in self.asks(d, "--all")["asks"] if a["id"] == closed)
        self.assertEqual(["TASK-100", "P003-O2-KR3"], entry["blocks_ids"])

    def test_the_payload_names_its_contract(self):
        d, _, _ = self.two_kinds()
        # 1.1: TASK-237 3a read the population from asks.jsonl and added state_root.
        # TASK-237 3b′: `installed` was added, a minor bump.
        # TASK-237 3c: `installed` narrowed (a store needs `.perry/`), a minor bump.
        self.assertEqual("perry-asks/list/1.3", self.asks(d, "--all")["contract"])


class TestItOnlyReads(Base):

    def test_the_store_and_the_log_are_untouched(self):
        d, _, _ = self.two_kinds()
        paths = [d / "asks.jsonl", d / ".perry" / "events.jsonl", d / "BOARD.md"]
        before = [p.read_bytes() if p.exists() else None for p in paths]
        self.asks(d, "--all")
        self.tool(d, "asks")
        after = [p.read_bytes() if p.exists() else None for p in paths]
        self.assertEqual(before, after)


class TestTheAnswerRule(unittest.TestCase):
    """`parsers.ask_answer`, against the shapes real boards carry."""

    def test_the_writer_form(self):
        self.assertEqual(("2026-09-13", "C, and more"),
                         P.ask_answer("answered 2026-09-13: C, and more"))

    def test_bold_on_both_ends_as_perrys_own_board_has_it(self):
        self.assertEqual(("2026-08-16", "30 days"),
                         P.ask_answer("**answered 2026-08-16: 30 days**"))

    def test_closed_another_way_is_answered_with_no_answer_text(self):
        cell = "dropped 2026-08-20 — folded into TASK-190"
        self.assertTrue(P.ask_is_answered(cell))
        self.assertEqual(("", ""), P.ask_answer(cell))

    def test_an_open_cell_yields_nothing(self):
        for cell in ("pending", "", "— not yet", "waiting on legal"):
            with self.subTest(cell=cell):
                self.assertEqual(("", ""), P.ask_answer(cell))

    def test_a_doubled_prefix_is_kept_verbatim(self):
        self.assertEqual(("2026-09-13", "answered 2026-09-13: B"),
                         P.ask_answer("answered 2026-09-13: answered 2026-09-13: B"))


class TestOnPerrysOwnBoard(unittest.TestCase):
    """Every ask the writer closed carries its answer on the real register."""

    def test_every_writer_form_row_has_answer_text(self):
        proc = subprocess.run([sys.executable, str(TASK), "asks", "--all",
                               "--json", "--root", str(ROOT)],
                              capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        writer_form = [a for a in out["asks"]
                       if P._ASK_ANSWER.match((a["status"] or "").strip().strip("*` "))]
        self.assertTrue(writer_form, "no answered ask on the board, so this "
                                     "checks nothing")
        for a in writer_form:
            with self.subTest(ask=a["id"]):
                self.assertTrue(a["answer"])
                self.assertTrue(a["answered_on"])


if __name__ == "__main__":
    unittest.main()
