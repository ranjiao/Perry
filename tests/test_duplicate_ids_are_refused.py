"""A duplicate id is REFUSED, in both directions, and never silently resolved.

TASK-273, following USER-904, USER-906 and USER-915 — the three rounds that
each chose *make the bad state refused* over *teach a resolver to guess better*.

Two registers key their store on an id, `## Top risks` and `## User Input
Queue`, and until this row both of their derivations guessed:

1. `risk_records` / `ask_records` walk the board with a `seen` set and
   `continue` past the second row carrying an id they already have — the FIRST
   row wins, written nowhere.
2. Both open with `by_id = {r.get("id"): r for r in current}` — the LAST
   record wins, written nowhere — and `cleared` / `answered` are then carried
   forward from that survivor onto the other record's row.

**What the board half actually destroys was measured rather than assumed, and
it is not what the loop looks like it does.** Two rows sharing an id lose the
second row's prose on the next render, but the record SET is intact, so the
skip alone destroys nothing. The casualty arrives one step later:
`mint_risk_id` reads the board's TEXT, the shadowed id is absent from it, and
the next `risk-add` reissues a number a live stored record still holds and
overwrites it — exit 0, `refuse_to_shrink` seeing three records become three,
`substituted_away` joining on the id and seeing it on both sides. Every
existing guard is looking somewhere else and each is right about where it
looks. `TestABoardDuplicateIsRefused` is the guard for the state itself.

**The store half is where `perry-lint` is not enough, and this file says why.**
The linter already reports a repeated id — `risk-store-badly-typed` — and it
reports it only while the duplicate is still on disk. The first ordinary write
LAUNDERS it: the store is rewritten from the collapsed set, the duplicate is
gone, the wrong `cleared` stays, and the linter has nothing left to say. So the
report is the linter's and the refusal is the writer's, because they are asked
different questions — what is wrong with this store, versus may I replace it.

**Two controls, and they are the point.** A board with no duplicates must write
exactly as it did before, and a legitimately repeated value that is not an id —
two risks opened on one day, two asks asked on one day, two intake rows filed
for the same request — must not be caught by any of it.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-task"
LINT = PERRY_HOME / "bin" / "perry-lint"
sys.path.insert(0, str(PERRY_HOME / "bin"))
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import perry_store as S  # noqa: E402
from task_writer_support import PT  # noqa: E402

H = "| ID | Title | Owner | Status | Next action | Evidence |"
SEP = "|" + "|".join(["---"] * 6) + "|"
RISK_HEAD = "| ID | Risk | Opened | Status |\n|---|---|---|---|"
ASK_HEAD = ("| USER-id | Needed from user | Blocks | Asked | Status |\n"
            "|---|---|---|---|---|")
INTAKE_HEAD = "| Arrived | Request | Outcome |\n|---|---|---|"


def board(risks: list[str] = (), asks: list[str] = (),
          intake: list[str] = ()) -> str:
    out = ["# Board — T\n",
           f"## P0 (must finish this period)\n\n{H}\n{SEP}\n",
           f"## P1\n\n{H}\n{SEP}\n",
           f"## P2\n\n{H}\n{SEP}\n"]
    if intake:
        out.append("## Intake\n\n" + INTAKE_HEAD + "\n"
                   + "\n".join(intake) + "\n")
    out.append("## User Input Queue\n\n" + ASK_HEAD + "\n"
               + "\n".join(asks) + "\n")
    out.append("## Top risks\n\n" + RISK_HEAD + "\n"
               + "\n".join(risks) + "\n")
    return "\n".join(out)


class Fixture:
    """A throwaway project whose register stores sit at the project root.

    `State root: .` — so `risks.jsonl` and `asks.jsonl` are siblings of
    `BOARD.md`. Written out here rather than reused from `task_writer_support`
    because every test in this file needs to plant a store BY HAND, which is
    the one thing the shared helper's `import_board` will not do.
    """

    def __init__(self, text: str, risks=None, asks=None):
        self.root = Path(tempfile.mkdtemp(prefix="t273-"))
        # Installed the way a start installs a project (TASK-237 round 2).
        import config_store
        config_store.write_config(self.root)
        (self.root / "BOARD.md").write_text(text)
        for name, recs in (("risks.jsonl", risks), ("asks.jsonl", asks)):
            if recs is not None:
                (self.root / name).write_text(
                    "".join(json.dumps(r, ensure_ascii=False) + "\n"
                            for r in recs))

    def run(self, *argv):
        return subprocess.run(
            ["python3", str(TOOL), *argv, "--root", str(self.root)],
            capture_output=True, text=True)

    def store(self, name):
        p = self.root / name
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] \
            if p.exists() else []

    def raw(self, name):
        p = self.root / name
        return p.read_text() if p.exists() else ""


def risk_row(rid, risk, opened="2026-01-01", status="open"):
    return f"| {rid} | {risk} | {opened} | {status} |"


def risk_rec(rid, risk, opened="2026-01-01", status="open", cleared="",
             order=0):
    return {"id": rid, "risk": risk, "opened": opened, "cleared": cleared,
            "status": status, "order": order}


def ask_row(rid, needed, blocks="", asked="2026-01-01", status="waiting"):
    return f"| {rid} | {needed} | {blocks} | {asked} | {status} |"


def ask_rec(rid, needed, blocks="", asked="2026-01-01", status="waiting",
            answered=False, order=0):
    return {"id": rid, "needed": needed, "blocks": blocks, "asked": asked,
            "status": status, "answered": answered, "order": order}


ADD = ("risk-add", "--title", "a brand new risk", "--actor", "Coding Agent")


class TestABoardDuplicateIsRefused(unittest.TestCase):
    """Deliverable 1. A repeated id on the BOARD is a refusal that names both
    rows, writes nothing, and exits 1."""

    def test_two_risk_rows_with_one_id_refuse_and_name_both_lines(self):
        f = Fixture(
            board(risks=[risk_row("RX-001", "first"),
                         risk_row("RX-002", "second"),
                         risk_row("RX-001", "third, id mistyped")]),
            risks=[risk_rec("RX-001", "first", order=0),
                   risk_rec("RX-002", "second", order=1),
                   risk_rec("RX-003", "third, id mistyped", order=2)])
        before = f.raw("risks.jsonl")
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("carries the same id on more than one row", r.stderr)
        self.assertIn("RX-001", r.stderr)
        # BOTH rows, not just the id: a refusal that named one line would send
        # a human to the row that is fine.
        self.assertRegex(r.stderr, r"`RX-001` on lines \d+, \d+")
        self.assertIn("Nothing was written", r.stderr)
        self.assertEqual(f.raw("risks.jsonl"), before)

    def test_the_record_the_write_would_have_destroyed_is_still_there(self):
        """Verification 3: no record is lost in either case."""
        f = Fixture(
            board(risks=[risk_row("RX-001", "first"),
                         risk_row("RX-002", "second"),
                         risk_row("RX-001", "third, id mistyped")]),
            risks=[risk_rec("RX-001", "first", order=0),
                   risk_rec("RX-002", "second", order=1),
                   risk_rec("RX-003", "the record that would have gone",
                            order=2)])
        f.run(*ADD)
        self.assertEqual(
            [(r["id"], r["risk"]) for r in f.store("risks.jsonl")],
            [("RX-001", "first"), ("RX-002", "second"),
             ("RX-003", "the record that would have gone")])

    def test_two_ask_rows_with_one_id_refuse(self):
        """The sibling register, and the same two lines serve it."""
        f = Fixture(
            board(asks=[ask_row("USER-001", "a question"),
                        ask_row("USER-001", "a different question")]),
            asks=[ask_rec("USER-001", "a question", order=0),
                  ask_rec("USER-002", "a different question", order=1)])
        before = f.raw("asks.jsonl")
        r = f.run("ask", "--needed", "one more thing", "--actor",
                  "Coding Agent")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("carries the same id on more than one row", r.stderr)
        self.assertIn("USER-001", r.stderr)
        self.assertEqual(f.raw("asks.jsonl"), before)

    def test_a_DECORATED_duplicate_id_is_still_a_duplicate(self):
        """`~~RX-001~~` and `RX-001` are one id, and the check must agree with
        the derivation about that.

        A cleared risk wears a strikethrough on this board — the shape
        `risk_record` exists to replace — so a struck-out row carrying an id a
        live row also carries is the realistic way this defect arrives, not a
        contrived one. `risk_records` reads both through `strip_handle`; a
        check that read the raw cell would see two different ids, report
        nothing, and let the collapse happen behind it.
        """
        f = Fixture(
            board(risks=[risk_row("RX-001", "first"),
                         risk_row("~~RX-001~~", "the struck-out twin")]),
            risks=[risk_rec("RX-001", "first", order=0)])
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("carries the same id on more than one row", r.stderr)
        self.assertIn("RX-001", r.stderr)

    def test_every_duplicate_is_named_not_only_the_first(self):
        """One pass through the refusal has to be enough to fix the board."""
        f = Fixture(
            board(risks=[risk_row("RX-001", "a"), risk_row("RX-001", "b"),
                         risk_row("RX-002", "c"), risk_row("RX-002", "d")]),
            risks=[risk_rec("RX-001", "a", order=0),
                   risk_rec("RX-002", "c", order=1)])
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 1)
        self.assertIn("RX-001", r.stderr)
        self.assertIn("RX-002", r.stderr)

    def test_the_report_itself_finds_both_rows(self):
        """`duplicate_row_ids` is the report and decides nothing."""
        text = board(risks=[risk_row("RX-001", "a"), risk_row("RX-002", "b"),
                            risk_row("RX-001", "c")])
        tmp = Path(tempfile.mkdtemp()) / "BOARD.md"
        tmp.write_text(text)
        b = PT.Board(tmp)
        dupes = S.duplicate_row_ids(S.risk_table(b, PT), PT, "id")
        self.assertEqual([d["id"] for d in dupes], ["RX-001"])
        self.assertEqual(len(dupes[0]["rows"]), 2)


class TestAStoreDuplicateIsRefused(unittest.TestCase):
    """Deliverable 2's other half. `perry-lint` REPORTS the corrupt store; the
    writer REFUSES to replace one, because a write launders the corruption."""

    def planted(self):
        return Fixture(
            board(risks=[risk_row("RX-001", "first"),
                         risk_row("RX-002", "second")]),
            risks=[risk_rec("RX-001", "first", status="open", cleared="",
                            order=0),
                   risk_rec("RX-001", "a stale duplicate",
                            status="cleared 2026-02-02", cleared="2026-02-02",
                            order=1),
                   risk_rec("RX-002", "second", order=2)])

    def test_an_ordinary_write_over_a_duplicated_store_is_refused(self):
        f = self.planted()
        before = f.raw("risks.jsonl")
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("more than one record for the same id", r.stderr)
        self.assertRegex(r.stderr, r"`RX-001` on lines \d+, \d+")
        self.assertIn("Nothing was written", r.stderr)
        self.assertEqual(f.raw("risks.jsonl"), before)

    def test_the_cleared_date_does_not_leak_onto_the_open_row(self):
        """The measured defect: an OPEN risk coming back with a cleared date."""
        f = self.planted()
        f.run(*ADD)
        survivors = [r for r in f.store("risks.jsonl") if r["id"] == "RX-001"]
        self.assertEqual(len(survivors), 2)
        open_row = [r for r in survivors if r["risk"] == "first"][0]
        self.assertEqual(open_row["cleared"], "")

    def test_the_refusal_says_why_the_two_halves_get_different_surfaces(self):
        """Deliverable 2 asks for that sentence in one line, so it is asserted
        rather than left in a docstring the next reader will unify away."""
        f = self.planted()
        r = f.run(*ADD)
        self.assertIn("the linter is asked what is wrong with the store as it "
                      "stands, and this tool is asked to REPLACE it",
                      r.stderr)

    def test_perry_lint_still_reports_it_and_that_half_is_unchanged(self):
        f = self.planted()
        r = subprocess.run(["python3", str(LINT), "--root", str(f.root)],
                           capture_output=True, text=True)
        self.assertIn("risk-store-badly-typed", r.stdout + r.stderr)
        self.assertIn("expected unique risk id", r.stdout + r.stderr)

    def test_the_report_itself_finds_both_records(self):
        dupes = S.duplicate_record_ids(
            [risk_rec("RX-001", "a", order=0), risk_rec("RX-002", "b", order=1),
             risk_rec("RX-001", "c", order=2)])
        self.assertEqual(dupes, [{"id": "RX-001", "lines": [1, 3]}])


class TestAControlBoardWritesExactlyAsBefore(unittest.TestCase):
    """Control 1. No duplicates anywhere: the write happens, unchanged."""

    def test_a_clean_board_still_writes(self):
        f = Fixture(
            board(risks=[risk_row("RX-001", "first"),
                         risk_row("RX-002", "second")]),
            risks=[risk_rec("RX-001", "first", order=0),
                   risk_rec("RX-002", "second", order=1)])
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stderr.strip(), "")
        self.assertEqual([x["id"] for x in f.store("risks.jsonl")],
                         ["RX-001", "RX-002", "RX-003"])

    def test_a_clean_ask_board_still_writes(self):
        f = Fixture(
            board(asks=[ask_row("USER-001", "a question")]),
            asks=[ask_rec("USER-001", "a question", order=0)])
        r = f.run("ask", "--needed", "one more thing", "--actor",
                  "Coding Agent")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([x["id"] for x in f.store("asks.jsonl")],
                         ["USER-001", "USER-002"])


class TestARepeatedValueThatIsNotAnIdIsNotCaught(unittest.TestCase):
    """Control 2. The gate is on the ID and on nothing else.

    A register whose every row shares a date, a severity or a status is an
    ordinary register. A duplicate-id gate that also fired on those would be
    the gate nobody keeps.
    """

    def test_two_risks_opened_on_the_same_day_write_normally(self):
        f = Fixture(
            board(risks=[risk_row("RX-001", "first", opened="2026-01-01"),
                         risk_row("RX-002", "second", opened="2026-01-01")]),
            risks=[risk_rec("RX-001", "first", opened="2026-01-01", order=0),
                   risk_rec("RX-002", "second", opened="2026-01-01", order=1)])
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(f.store("risks.jsonl")), 3)

    def test_two_risks_with_the_same_status_and_prose_write_normally(self):
        """Same severity, same status, same sentence — different ids."""
        f = Fixture(
            board(risks=[risk_row("RX-001", "the very same sentence",
                                  status="open"),
                         risk_row("RX-002", "the very same sentence",
                                  status="open")]),
            risks=[risk_rec("RX-001", "the very same sentence", order=0),
                   risk_rec("RX-002", "the very same sentence", order=1)])
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(f.store("risks.jsonl")), 3)

    def test_two_asks_asked_on_the_same_date_write_normally(self):
        f = Fixture(
            board(asks=[ask_row("USER-001", "q one", asked="2026-01-01"),
                        ask_row("USER-002", "q two", asked="2026-01-01")]),
            asks=[ask_rec("USER-001", "q one", asked="2026-01-01", order=0),
                  ask_rec("USER-002", "q two", asked="2026-01-01", order=1)])
        r = f.run("ask", "--needed", "one more thing", "--actor",
                  "Coding Agent")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(f.store("asks.jsonl")), 3)

    def test_layout_rows_with_no_handle_are_not_two_rows_sharing_a_blank_id(self):
        dupes = S.duplicate_record_ids(
            [{"id": "", "risk": "a"}, {"id": "", "risk": "b"}])
        self.assertEqual(dupes, [])

    def test_rows_with_an_empty_id_cell_are_not_two_rows_sharing_a_blank_id(self):
        """TWO GREEN MUTATIONS LED HERE, and the second one taught the lesson.

        The round planted `if not rid:` → `if rid is None:` in
        `duplicate_row_ids` and nothing went red. The first attempt at a test
        used prose in the `ID` cell and stayed green too — `strip_handle` only
        removes decoration, so prose comes back as prose and two DIFFERENT
        notes are two different ids, not a duplicate.

        The reason the branch could not be reached from a board at all is the
        one `intake_records` states in its own docstring: **`markdown_tables`
        already drops a line with no first cell**, so `risk_table` never yields
        a row whose id cell is empty. `if not rid` is a guard against a caller
        that does not exist yet, not against any board a human can write.

        So it is tested where it IS reachable — directly, on a table handed in
        by hand. That keeps the contract true for the next caller that builds
        a table some other way, and it says out loud that no board fixture can
        exercise it, which is the thing a reader would otherwise have to
        rediscover with a mutation.
        """
        table = {"header": ["ID", "Risk", "Opened", "Status"],
                 "keys": ["id", "risk", "opened", "status"],
                 "rows": [{"line": 10, "cells": ["", "a note", "", ""],
                           "values": {"id": "", "risk": "a note"}},
                          {"line": 11, "cells": ["", "another note", "", ""],
                           "values": {"id": "", "risk": "another note"}}]}
        self.assertEqual(S.duplicate_row_ids(table, PT, "id"), [])

    def test_a_row_whose_id_cell_is_blank_never_reaches_the_check(self):
        """The reachability claim above, asserted rather than believed."""
        text = board(risks=[risk_row("RX-001", "a real risk"),
                            "|  | a prose note | | |"])
        tmp = Path(tempfile.mkdtemp()) / "BOARD.md"
        tmp.write_text(text)
        table = S.risk_table(PT.Board(tmp), PT)
        self.assertEqual(len(table["rows"]), 1)
        self.assertEqual(
            [PT.strip_handle(r["values"].get("id", "")) for r in table["rows"]],
            ["RX-001"])

    def test_a_board_carrying_such_a_line_still_writes(self):
        """Control 1 again, on a board with a non-row line under the table."""
        f = Fixture(
            board(risks=[risk_row("RX-001", "a real risk"),
                         "|  | a prose note | | |"]),
            risks=[risk_rec("RX-001", "a real risk", order=0)])
        r = f.run(*ADD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class TestIntakeIsNotServedByTheseLines(unittest.TestCase):
    """The spec's out-of-scope question, answered: `## Intake` is out, and what
    keeps it out is that it has no id at all."""

    def test_intake_is_declared_out_on_both_sides_not_merely_harmless(self):
        """A GREEN MUTATION FOUND THIS TEST CLASS, and it is recorded here.

        TASK-273's mutation round planted `"intake"` INTO `REGISTER_ID_KEYED`
        and the behavioural test below stayed green. The mutation is inert:
        `INTAKE_STORED` has no `id` field at all, so `duplicate_record_ids`
        returns `[]` for an intake store however the set is spelled. The
        behavioural test could never have caught it.

        That makes `REGISTER_ID_KEYED` a second lock on a door the missing `id`
        field already locks — which is fine to keep and NOT fine to leave
        undefended, because the next reader has no way to tell a deliberate
        exclusion from an oversight. So the decision is asserted directly, on
        both sides: the store side by the set, the board side by the `None` in
        `REGISTER_SPEC` that stops `duplicate_row_ids` ever being called for
        `## Intake`.
        """
        self.assertNotIn("intake", PT.REGISTER_ID_KEYED)
        # TASK-237 3b: `cadence` joined, keyed on the row's `ID` like the two
        # before it — so it is in on both sides, where intake is out on both.
        self.assertEqual(PT.REGISTER_ID_KEYED,
                         frozenset({"risks", "asks", "cadence"}))
        self.assertIsNone(PT.REGISTER_SPEC["intake"][5])
        self.assertIsNotNone(PT.REGISTER_SPEC["risks"][5])
        self.assertIsNotNone(PT.REGISTER_SPEC["asks"][5])
        self.assertIsNotNone(PT.REGISTER_SPEC["cadence"][5])
        self.assertNotIn("id", S.INTAKE_STORED)

    def test_intake_records_has_no_seen_set_and_no_id(self):
        import inspect
        src = inspect.getsource(S.intake_records)
        self.assertNotIn("seen", src)
        self.assertNotIn("by_id", src)
        self.assertIn("by_order", src)

    def test_two_intake_rows_for_the_same_request_on_the_same_day_are_fine(self):
        """The ordinary shape of a thing filed twice — `dropped — duplicate`
        exists for exactly this and must keep working."""
        f = Fixture(
            board(intake=["| 2026-01-01 | the same request | |",
                          "| 2026-01-01 | the same request | |"],
                  risks=[risk_row("RX-001", "first")]),
            risks=[risk_rec("RX-001", "first", order=0)])
        r = f.run("intake", "--title", "one more request", "--actor",
                  "Coding Agent")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(f.store("intake.jsonl")), 3)


class TestTheFromBoardImportIsGuardedToo(unittest.TestCase):
    """The other caller of the same two lines — and the one whose existing
    guard was measured and found to have a hole.

    `bin/perry-tasks § cmd_asks_write` documents eleven measured inputs and
    concludes its byte gate catches the duplicate-id class. It catches the ten
    whose PROSE differs. Two rows carrying the same id AND identical cells
    render back byte for byte, so the gate has no question to fail, and three
    board rows imported as two records at exit code 0.

    This is not a fourth site under the spec's Bound: it is one more caller of
    `risk_records` / `ask_records`, and the lines being guarded are still the
    `by_id` collapse and the `seen` skip.
    """

    def run_tasks(self, root, *argv):
        return subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-tasks"), *argv,
             "--root", str(root)], capture_output=True, text=True)

    def test_a_duplicate_with_identical_prose_is_refused(self):
        """The one the byte gate cannot see."""
        f = Fixture(board(risks=[risk_row("RX-001", "first"),
                                 risk_row("RX-002", "second"),
                                 risk_row("RX-001", "first")]))
        r = self.run_tasks(f.root, "risks-write", "--from-board")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("carries the same id on more than one row", r.stderr)
        self.assertIn("would import as 1 record(s)", r.stderr)
        self.assertFalse((f.root / "risks.jsonl").exists())

    def test_a_duplicate_with_different_prose_is_refused_before_the_byte_gate(self):
        f = Fixture(board(risks=[risk_row("RX-001", "first"),
                                 risk_row("RX-001", "quite different")]))
        r = self.run_tasks(f.root, "risks-write", "--from-board")
        self.assertEqual(r.returncode, 1)
        # The duplicate refusal, not the byte gate's "do not render back".
        self.assertIn("carries the same id on more than one row", r.stderr)

    def test_the_ask_importer_is_guarded_the_same_way(self):
        f = Fixture(board(risks=[risk_row("RX-001", "first")],
                          asks=[ask_row("USER-001", "q one"),
                                ask_row("USER-001", "q one")]))
        r = self.run_tasks(f.root, "asks-write", "--from-board")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("carries the same id on more than one row", r.stderr)
        self.assertFalse((f.root / "asks.jsonl").exists())

    def test_a_clean_board_still_imports(self):
        """Control 1, on this door."""
        f = Fixture(board(risks=[risk_row("RX-001", "first"),
                                 risk_row("RX-002", "second")]))
        r = self.run_tasks(f.root, "risks-write", "--from-board")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual([x["id"] for x in f.store("risks.jsonl")],
                         ["RX-001", "RX-002"])

    def test_repeated_non_id_cells_still_import(self):
        """Control 2, on this door: same date, same prose, different ids."""
        f = Fixture(board(risks=[risk_row("RX-001", "same words",
                                          opened="2026-01-01"),
                                 risk_row("RX-002", "same words",
                                          opened="2026-01-01")]))
        r = self.run_tasks(f.root, "risks-write", "--from-board")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(f.store("risks.jsonl")), 2)


class TestTasksJsonlDoesNotShareTheHole(unittest.TestCase):
    """Deliverable 3, decided. `perry/tasks.jsonl` is SAFE, and three separate
    things make it so — none of which is care taken at the duplicate site.

    1. **Its `seen` set is in a VALIDATOR, not in a board-walking builder.**
       `perry_store.validate_records:202-248` reaches `elif tid in seen` and
       appends a FINDING — `expected: unique task id` — rather than
       `continue`-ing past the record. It reports where the register builders
       skipped.
    2. **The task store is not rebuilt from the board by an ordinary write.**
       `## P0/P1/P2` is rendered OUTPUT under ADR-007; `perry-task`'s task
       path mutates the record set and re-renders the board from it, so there
       is no board-to-record derivation for a board duplicate to corrupt. The
       board-to-store direction exists only behind the explicit, consented
       `perry-tasks write --from-board`.
    3. **Its findings are gated, not advisory.** `load_task_records` and
       `commit` both run `validate_records` and refuse on findings, so a
       duplicated `tasks.jsonl` stops a write rather than being collapsed
       into one.

    So there is no new row here. What TASK-273 changed is that the two
    id-keyed REGISTERS now behave the way tasks already did.
    """

    def test_the_tasks_validator_reports_a_duplicate_rather_than_skipping_it(self):
        good, findings = S.validate_records(
            [{"id": "TASK-001", "title": "a", "summary": ""},
             {"id": "TASK-001", "title": "b", "summary": ""}])
        self.assertEqual(len(good), 1)
        self.assertEqual(len(findings), 1)
        self.assertIn("unique task id", findings[0]["message"])

    def test_the_tasks_validator_does_not_silently_drop_the_second_record(self):
        """The distinction that makes tasks safe: a finding, not a `continue`.

        `risk_records`' skip produced no record AND no finding. This produces
        no record and one finding, and every caller gates on findings.
        """
        _good, findings = S.validate_records(
            [{"id": "TASK-001", "title": "a", "summary": ""},
             {"id": "TASK-001", "title": "b", "summary": ""}])
        self.assertEqual(findings[0]["id"], "TASK-001")

    def test_a_duplicated_tasks_store_refuses_an_ordinary_write(self):
        f = Fixture(board(risks=[risk_row("RX-001", "first")]),
                    risks=[risk_rec("RX-001", "first", order=0)])
        (f.root / "tasks.jsonl").write_text(
            json.dumps({"id": "TASK-001", "title": "a", "status": "todo",
                        "summary": "A row that exists so there is one."})
            + "\n" +
            json.dumps({"id": "TASK-001", "title": "b", "status": "todo",
                        "summary": "A second row wearing the same id."})
            + "\n")
        r = f.run("add", "--title", "a new task", "--actor", "Coding Agent",
                  "--deliverable", "a thing that exists afterwards",
                  "--verification", "the suite is green",
                  "--summary", "A fixture row so the writer has something "
                               "to write down here.")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("unique task id", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
