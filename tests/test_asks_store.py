"""`## User Input Queue` is a projection of a record store — ADR-007, a fourth
register.

TASK-197, following TASK-040 and TASK-196. The order of this file is the
argument:

1. **The store reproduces what it replaces, byte for byte, before it holds a
   single field the table could not.** A renderer that quietly keeps a cell
   verbatim passes `cmp` while reproducing nothing, so the report's own
   fallback counters are asserted — and here one of them is asserted NON-empty
   on purpose, because one column of this register is deliberately not stored.

2. **`Idle` IS THAT COLUMN, AND IT IS THE ROW.** It is an age — `today −
   Asked` — and `bin/perry-state § idle_days` already derives it at read time.
   A live project deleted the column outright on the ground that a stored age
   is stale the moment it is written. So the store carries `Asked`, the INPUT,
   and makes no claim at all about `Idle`. The class below asserts what that
   buys and what it costs, in both directions: a hand edit to `Idle` is not
   drift and `asks-render --write` does not repair it, while a hand edit to
   `Asked` is drift like any other stored cell.

3. **The byte gate is load-bearing here, and that was measured.** TASK-196
   found the same gate a tautology one register over and said so. That
   argument turned on intake rows having no id; a `USER-` row has one, so the
   risks class is back — a repeated id collapses two lines into one record.
   `TestTheByteGateIsLoadBearingHere` measures eleven inputs rather than
   asserting the conclusion.

4. **"Has this question come back?" is one function.** `parsers.ask_is_answered`,
   which `bin/perry-state § answered` now calls rather than spells.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

from task_writer_support import PT, Project

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
import parsers as P  # noqa: E402
import perry_store as S  # noqa: E402

TASKS = PERRY_HOME / "bin" / "perry-tasks"
LINT = PERRY_HOME / "bin" / "perry-lint"

#: The register in the shape Perry's own board writes it — **six columns**,
#: `Idle` AND `Asked`. Quoted in shape, not in content: the rows are fixtures
#: with fixed text, because a test that reads the surrounding project as its
#: expected value goes red the next time somebody asks a question.
#:
#: The four rows are the four real cases: a row from before `Asked` existed
#: (`Idle: —`, no date, decorated status), a pending row whose question carries
#: an escaped pipe and a backtick, a pending row with a real `Idle` number, and
#: an answered row.
HEADER = ("| USER-id | Needed from user | Blocks | Idle | Status | Asked |\n"
          "|---|---|---|---|---|---|\n")
REGISTER = HEADER + (
    "| USER-001 | Staleness threshold N | TASK-005 | — | "
    "**answered 2026-08-16: 30 days** |  |\n"
    "| USER-002 | pick the export format for `a \\| b` | TASK-009 | 12d | "
    "pending | 2026-08-16 |\n"
    "| USER-003 | confirm the retention window | — | 3d | pending | "
    "2026-08-25 |\n"
    "| USER-004 | sign off on the migration plan | TASK-011 | — | "
    "answered 2026-08-27: yes, go | 2026-08-26 |\n")

#: The five-column shape `perry-task ask` creates from scratch — `Asked`, no
#: `Idle` at all. The store has to hold this board too, and hold it without
#: inventing the column.
NO_IDLE = ("| USER-id | Needed from user | Blocks | Asked | Status |\n"
           "|---|---|---|---|---|\n"
           "| USER-001 | pick a retention window | TASK-005 | 2026-08-25 | "
           "pending |\n")


def board_with(section: str) -> str:
    h = "| ID | Title | Owner | Status | Next action | Evidence |"
    sep = "|" + "|".join(["---"] * 6) + "|"
    return (
        "# Board — T\n\n"
        f"## User Input Queue\n\n{section}\n"
        f"## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
        f"## P1\n\n{h}\n{sep}\n\n"
        f"## P2\n\n{h}\n{sep}\n"
    )


def derive(text: str, current: list[dict] | None = None):
    """(board, ops, records) for a board given as text."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    tmp.write(text)
    tmp.close()
    board = PT.Board(Path(tmp.name))
    return board, PT, S.ask_records(board, PT, current)


class TestByteIdentityComesFirst(unittest.TestCase):
    """Item 1. Before `answered` exists, the store has to put the section back
    exactly as it found it."""

    def test_the_section_round_trips_byte_for_byte(self):
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        rendered, report = S.ask_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_from_store"], 4)

    def test_the_five_column_shape_round_trips_too(self):
        """The shape `perry-task ask` writes: `Asked`, no `Idle`. Nothing
        invents the column and nothing is lost by its absence."""
        text = board_with(NO_IDLE)
        board, ops, records = derive(text)
        rendered, report = S.ask_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["cells_verbatim"], {})

    def test_only_idle_survives_as_a_literal(self):
        """`cmp` alone cannot tell a rebuilt cell from a copied one. These
        counters are what make the byte result mean something — and here one of
        them is deliberately non-empty: `Idle` is copied on every row because no
        stored field claims it, and the counter is the receipt for that
        decision rather than a hole in the proof."""
        board, ops, records = derive(board_with(REGISTER))
        _, report = S.ask_render(board, records, ops)
        self.assertEqual(report["cells_verbatim"], {"Idle": 4})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(report["cells_the_store_and_board_disagree_on"], [])
        self.assertEqual(report["rows_out_of_stored_order"], {})
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_not_on_board"], [])

    def test_byte_identity_does_not_depend_on_the_new_field(self):
        """`answered` is the field the six columns cannot express. If the byte
        gate needed it, the gate would be testing the new field rather than the
        migration."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        stripped = [{k: v for k, v in r.items() if k != "answered"}
                    for r in records]
        rendered, _ = S.ask_render(board, stripped, ops)
        self.assertEqual(rendered, text)

    def test_a_decorated_id_keeps_its_decoration_and_stores_the_handle(self):
        """`~~**USER-001**~~` is presentation; `USER-001` is data."""
        text = board_with(HEADER + (
            "| ~~**USER-001**~~ | withdrawn question | — | — | "
            "dropped 2026-08-20 |  |\n"))
        board, ops, records = derive(text)
        self.assertEqual(records[0]["id"], "USER-001")
        rendered, report = S.ask_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["cells_wearing_decoration"], {"USER-id": 1})

    def test_a_row_with_no_handle_is_layout_and_does_not_advance_order(self):
        """`risk_records`' rule, and the right one here: the key is the id, so
        skipping a layout row moves nothing. Intake could not do this — its key
        is the position, and skipping a row there renumbers every row below.

        A row whose id cell is EMPTY never reaches the plan at all —
        `markdown_tables` drops a line with no first cell — so it is neither a
        record nor a `rows_verbatim` entry. It renders untouched, and the real
        row keeps `order: 0` rather than being pushed to 1 by a line that is
        not a question."""
        text = board_with(HEADER + (
            "|  | a note somebody left in the table | — | — | — |  |\n"
            "| USER-002 | a real question | TASK-009 | 3d | pending | "
            "2026-08-25 |\n"))
        board, ops, records = derive(text)
        self.assertEqual([r["id"] for r in records], ["USER-002"])
        self.assertEqual(records[0]["order"], 0)
        rendered, report = S.ask_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_from_store"], 1)


class TestIdleIsDerivedAndIsNotStored(unittest.TestCase):
    """**Item 2 — the judgement call of the row, as assertions.**

    `Idle` is `today − Asked`. `bin/perry-state § idle_days` computes it, the
    contract publishes it as `idle_days` with *"a stored age is stale the
    morning after it is written"* beside it, and `perry-task ask` has stamped
    `Asked` and left `Idle` alone since TASK-039 — whose docstring records what
    the other choice cost: **both rows on Perry's own board carried `Idle: —`**,
    the one field the queue exists for, unfilled.

    So the store holds the INPUT and not the AGE. What follows is what that
    buys and, in the last two tests, what it costs — stated rather than hidden.
    """

    def test_idle_is_not_a_stored_field(self):
        self.assertNotIn("idle", S.ASK_STORED)
        self.assertIn("asked", S.ASK_STORED)

    def test_no_column_renders_from_idle(self):
        """The rendering table is where "not stored" becomes "not claimed"."""
        self.assertNotIn("idle", S.ASK_FIELD_BY_COLUMN.values())
        self.assertNotIn("idle", S.ASK_FIELD_BY_COLUMN)

    def test_a_record_carries_no_age_however_the_cell_reads(self):
        """`9d`, `—` and `` are three spellings of a number the store must not
        hold. None of them reaches a record."""
        for cell in ("9d", "—", "", "0", "47 days"):
            with self.subTest(cell=cell):
                _b, _o, records = derive(board_with(HEADER + (
                    f"| USER-001 | q | — | {cell} | pending | 2026-08-25 |\n")))
                self.assertEqual(set(records[0]), set(S.ASK_STORED))
                self.assertNotIn("idle", records[0])

    def test_the_record_is_identical_whatever_idle_says(self):
        """**The proof, at record level.** Two boards differing only in the
        `Idle` cell derive the same store. If the age were stored these would
        differ, and the store would carry a number that was true on the day
        somebody typed it."""
        a = derive(board_with(HEADER + (
            "| USER-001 | q | — | 3d | pending | 2026-08-25 |\n")))[2]
        b = derive(board_with(HEADER + (
            "| USER-001 | q | — | 999d | pending | 2026-08-25 |\n")))[2]
        self.assertEqual(a, b)

    def test_the_age_is_computed_from_asked_at_read_time(self):
        """The other half of the same decision: the number a reader wants is
        produced, not stored. `days_since` is the arithmetic and `idle_days`
        prefers `asked` over the cell exactly as the contract says."""
        state = _perry_state()
        row = P.UserInput(id="USER-001", needed_from_user="q", blocks="—",
                          idle="999d", status="pending", asked="")
        self.assertEqual(state.idle_days(row), 999,
                         "with no `Asked` the cell is the only source and is "
                         "used — this is the boards that dropped `Asked`")
        from datetime import date, timedelta
        row.asked = f"{date.today() - timedelta(days=4):%Y-%m-%d}"
        self.assertEqual(state.idle_days(row), 4,
                         "`Asked` wins, and the answer is right this morning "
                         "rather than on the morning the cell was typed")

    def test_editing_idle_by_hand_is_not_drift(self):
        """**The cost, and it is the intended one.** The store asserts nothing
        about this column, so `perry-lint` reports nothing when it changes. A
        checker that reported it would be inventing a claim to enforce."""
        p = _imported(self)
        _edit(p, "| 3d | pending | 2026-08-25 |", "| 47d | pending | 2026-08-25 |")
        stats = _lint(p.root)["ask_store_drift"]
        self.assertEqual(stats["records"], 4)
        self.assertEqual(stats["drifted"], 0)

    def test_editing_asked_by_hand_IS_drift(self):
        """The mirror, and the reason the pair is the design rather than a gap:
        the INPUT is stored, so editing it moves every age computed from it and
        is reported like any other cell."""
        p = _imported(self)
        _edit(p, "| 3d | pending | 2026-08-25 |", "| 3d | pending | 2026-07-12 |")
        stats = _lint(p.root)["ask_store_drift"]
        self.assertEqual(stats["drifted"], 1)
        findings = [f for f in _lint(p.root)["findings"]
                    if f["rule"] == "ask-store-drift"]
        self.assertIn("`asked`", findings[0]["message"])

    def test_render_write_does_not_repair_an_edited_idle_cell(self):
        """And the store does not put it back, because it never held it. Every
        stored column is restored and `Idle` is left as the human left it —
        which is the honest behaviour for a column the store makes no claim
        about, and is stated here so nobody reads it as a renderer bug."""
        p = _imported(self)
        _edit(p, "| 3d | pending | 2026-08-25 |", "| 47d | pending | 2026-08-25 |")
        _edit(p, "confirm the retention window", "confirm the WINDOW")
        out = _tasks(p.root, "asks-render", "--write")
        self.assertEqual(out.returncode, 0, out.stderr)
        board = (p.root / "BOARD.md").read_text()
        self.assertIn("confirm the retention window", board,
                      "the stored cell came back from the store")
        self.assertIn("| 47d |", board,
                      "the derived cell was left alone")
        self.assertEqual(_lint(p.root)["ask_store_drift"]["drifted"], 0)


class TestBlocksIsStoredBecauseItIsNotDerivable(unittest.TestCase):
    """`blocks` on a TASK record is DERIVED — the inverse of `depends_on`. The
    same reading was tried for this column and it does not hold, so the column
    is stored. These assert the reason rather than the conclusion."""

    def test_a_blocks_cell_survives_with_no_dependency_edge_anywhere(self):
        """The register's `Blocks` cell names `TASK-005`, and no task in the
        fixture declares `depends_on: ["USER-001"]`. A derived column would
        render empty here; a stored one renders the cell."""
        p = _imported(self)
        records = _store(p)
        self.assertEqual(records[0]["blocks"], "TASK-005")
        tasks = [json.loads(l) for l in
                 (p.root / "tasks.jsonl").read_text().split("\n") if l.strip()]
        self.assertEqual(
            [t["id"] for t in tasks if "USER-001" in (t.get("depends_on") or [])],
            [], "no inverse edge exists, so there is nothing to derive from")
        self.assertEqual(_lint(p.root)["ask_store_drift"]["drifted"], 0)

    def test_a_blocks_cell_that_is_not_an_id_at_all_survives(self):
        """The contract calls it *"free text, often a task id"*. Often is not
        always, and a store may not round often up."""
        text = board_with(HEADER + (
            "| USER-001 | q | the whole of phase D, and the RFC under it | "
            "— | pending | 2026-08-25 |\n"))
        board, ops, records = derive(text)
        self.assertEqual(records[0]["blocks"],
                         "the whole of phase D, and the RFC under it")
        self.assertEqual(S.ask_render(board, records, ops)[0], text)


class TestTheByteGateIsLoadBearingHere(unittest.TestCase):
    """**Item 3, measured rather than inherited.**

    TASK-196 reported the byte gate a tautology for intake and built a
    row-count gate instead — its argument was that an intake row has no id, so
    nothing collapses. A `USER-` row HAS an id, so the risks class is back.
    These measure it: one input differs and the rest do not.
    """

    #: Inputs that are byte-identical either way — the honest half of the
    #: measurement, kept so "the gate catches something" is not read as "the
    #: gate catches things".
    TAUTOLOGICAL = {
        "escaped pipe":
            "| USER-001 | choose `a \\| b` | TASK-005 | — | pending | 2026-08-20 |\n",
        "ragged short row": "| USER-001 | short | TASK-005 |\n",
        "ragged long row":
            "| USER-001 | long | T | — | pending | 2026-08-20 | extra |\n",
        "no trailing pipe":
            "| USER-001 | no trailing pipe | TASK-005 | — | pending | 2026-08-20\n",
        "blank first cell":
            "|  | no id at all | TASK-005 | — | pending | 2026-08-20 |\n",
        "indented row":
            "  | USER-001 | indented | TASK-005 | — | pending | 2026-08-20 |\n",
        "struck-out id":
            "| ~~**USER-001**~~ | struck out | TASK-005 | — | pending | 2026-08-20 |\n",
        "an Idle cell with a real number":
            "| USER-001 | idle is 9d | TASK-005 | 9d | pending | 2026-08-20 |\n",
    }

    def test_a_repeated_user_id_is_caught_by_the_bytes(self):
        """**The class the gate exists for.** `ask_records` collapses a
        repeated id into ONE record and `ask_plan` renders BOTH lines from it,
        so the second line comes back carrying the first row's question,
        blocker, status and date. Two questions become one and the bytes are
        what say so."""
        text = board_with(HEADER + (
            "| USER-001 | first question | TASK-005 | — | pending | 2026-08-20 |\n"
            "| USER-001 | a DIFFERENT question | TASK-009 | 3d | pending | "
            "2026-08-21 |\n"))
        board, ops, records = derive(text)
        self.assertEqual(len(records), 1, "two lines, one record")
        rendered, _ = S.ask_render(board, records, ops)
        self.assertNotEqual(rendered, text)
        self.assertIn(
            "| USER-001 | first question | TASK-005 | 3d | pending | "
            "2026-08-20 |", rendered,
            "the second line came back wearing the FIRST row's question, "
            "blocker, status and date — and note the `Idle` cell `3d` "
            "survived, because the store never claimed that column")

    def test_the_duplicate_is_refused_before_a_byte_is_written(self):
        p = _imported(self)
        before = (p.root / "asks.jsonl").read_bytes()
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            "| USER-003 | confirm the retention window",
            "| USER-002 | confirm the retention window", 1))
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("byte for byte", out.stderr)
        self.assertIn("REPEATED `USER-` id", out.stderr)
        self.assertEqual((p.root / "asks.jsonl").read_bytes(), before)

    def test_the_inputs_the_gate_cannot_see(self):
        """Reported rather than hidden: eight malformed or unusual rows render
        byte-identical either way. The gate is not a general correctness
        check — it catches one class, and that class is the one a register
        keyed on its id dies of."""
        for name, row in self.TAUTOLOGICAL.items():
            with self.subTest(row=name):
                text = board_with(HEADER + row)
                board, ops, records = derive(text)
                self.assertEqual(S.ask_render(board, records, ops)[0], text)

    def test_a_column_no_stored_field_claims_is_counted_not_smuggled(self):
        """What the counters carry that the bytes cannot: a `Notes` column
        lands in `cells_verbatim` beside `Idle`, and a reader who saw only
        `identical: true` would believe the store held both."""
        text = board_with(
            "| USER-id | Needed from user | Blocks | Idle | Status | Asked | Notes |\n"
            "|---|---|---|---|---|---|---|\n"
            "| USER-001 | q | TASK-005 | 3d | pending | 2026-08-25 | see #12 |\n")
        board, ops, records = derive(text)
        rendered, report = S.ask_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["cells_verbatim"], {"Idle": 1, "Notes": 1})


class TestAnsweredIsTheOneFieldWithNoColumn(unittest.TestCase):
    """Item 4. This register's `cleared` and `discharged`."""

    def test_the_predicate_is_one_function(self):
        """`bin/perry-state § answered` calls `parsers.ask_is_answered` rather
        than spelling it. A store with a fifth opinion about whether a question
        came back would decide whether somebody is told to start work."""
        state = _perry_state()
        for status in ("pending", "", "answered 2026-08-16: yes", "—",
                       "**answered 2026-08-16: 30 days**", "waiting on legal",
                       "dropped 2026-08-20", "open"):
            with self.subTest(status=status):
                row = P.UserInput(id="USER-001", needed_from_user="q",
                                  blocks="—", idle="", status=status)
                self.assertEqual(state.answered(row),
                                 P.ask_is_answered(status))

    def test_an_empty_status_is_not_answered(self):
        self.assertFalse(P.ask_is_answered(""))
        self.assertFalse(P.ask_is_answered("   "))

    def test_the_field_is_derived_from_prose_on_a_row_the_store_never_saw(self):
        """The migration case: the `Status` prose IS the only record there is."""
        _b, _o, records = derive(board_with(REGISTER))
        self.assertEqual([r["answered"] for r in records],
                         [True, False, False, True])

    def test_true_is_carried_across_and_false_is_not(self):
        """The asymmetry `perry-task answer` makes real by refusing a second
        answer: `True` is a fact the board cannot un-say, `False` is "still on
        the user", which the `Status` cell answers for itself."""
        text = board_with(REGISTER)
        stored = [{"id": "USER-002", "answered": True},
                  {"id": "USER-004", "answered": False}]
        _b, _o, records = derive(text, stored)
        by_id = {r["id"]: r for r in records}
        self.assertTrue(by_id["USER-002"]["answered"],
                        "stored True survives a board that says `pending`")
        self.assertTrue(by_id["USER-004"]["answered"],
                        "stored False does not override the cell's own answer")

    def test_a_string_in_the_field_is_malformed_rather_than_truthy(self):
        good, findings = S.validate_ask_records(
            [{"id": "USER-001", "answered": "true", "order": 0}])
        self.assertEqual(good, [])
        self.assertIn("`answered` is str", findings[0]["message"])


class TestTheImportIsGated(unittest.TestCase):
    """ADR-004 over the four refusals, each of which writes nothing."""

    def test_no_from_board_no_write(self):
        self._held = p = Project(board=board_with(REGISTER))
        out = _tasks(p.root, "asks-write")
        self.assertEqual(out.returncode, 1)
        self.assertIn("--from-board", out.stderr)
        self.assertFalse((p.root / "asks.jsonl").exists())

    def test_a_section_with_no_table_is_refused(self):
        self._held = p = Project(board=board_with(
            "Nobody has asked the user anything yet.\n"))
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 1)
        self.assertIn("holds no table", out.stderr)
        self.assertFalse((p.root / "asks.jsonl").exists())

    def test_a_second_table_under_the_heading_is_refused(self):
        p = _imported(self)
        before = (p.root / "asks.jsonl").read_bytes()
        board = p.root / "BOARD.md"
        board.write_text(board.read_text().replace(
            "## P0 (must finish this period)",
            "| Priority | Meaning |\n|---|---|\n| P0 | now |\n\n"
            "## P0 (must finish this period)", 1))
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("more than one table", out.stderr)
        self.assertEqual((p.root / "asks.jsonl").read_bytes(), before)

    def test_a_table_with_no_question_column_is_foreign(self):
        text = board_with("| USER-id | Notes |\n|---|---|\n"
                          "| USER-001 | see #12 |\n")
        board, ops, _r = derive(text)
        self.assertEqual(S.ask_section_shape(board, ops)[0], "foreign")

    def test_an_unreadable_store_is_not_overwritten(self):
        p = _imported(self)
        (p.root / "asks.jsonl").write_text("{not json\n")
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 2)
        self.assertIn("cannot be read", out.stderr)
        self.assertEqual((p.root / "asks.jsonl").read_text(), "{not json\n")

    def test_a_malformed_store_is_not_overwritten(self):
        p = _imported(self)
        (p.root / "asks.jsonl").write_text(
            json.dumps({"id": "USER-001", "order": "0", "answered": False})
            + "\n")
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 2)
        self.assertIn("malformed", out.stderr)
        self.assertIn("`order` is str", out.stderr)

    def test_what_the_import_replaces_is_disclosed(self):
        p = _imported(self)
        records = _store(p)
        records[0]["needed"] = "something else entirely"
        (p.root / "asks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("USER-001.needed", out.stderr)
        self.assertIn("something else entirely", out.stderr)

    def test_the_import_appends_no_event(self):
        """It asks nobody anything and answers nothing. Every event it could
        append would carry today's timestamp for a question put weeks ago."""
        self._held = p = Project(board=board_with(REGISTER))
        before = len(p.events())
        out = _tasks(p.root, "asks-write", "--from-board")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(len(p.events()), before)

    def _uut(self, name: str):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(name, str(TASKS))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_the_claim_is_declared_and_withdrawing_it_stops_the_write(self):
        mod = self._uut("perry_tasks_uut_asks")
        self.assertTrue(mod.ask_store_is_declared(),
                        "schema/state-schema.json no longer claims asks.jsonl "
                        "— the declaration was reverted")
        self._held = p = Project(board=board_with(REGISTER))
        real = mod.ask_store_is_declared
        mod.ask_store_is_declared = lambda: False
        noise = io.StringIO()
        try:
            with contextlib.redirect_stderr(noise):
                rc = mod.cmd_asks_write(p.root, ["--from-board"])
        finally:
            mod.ask_store_is_declared = real
        self.assertIn("What is missing is the DECLARATION", noise.getvalue())
        self.assertEqual(rc, 1)
        self.assertFalse((p.root / "asks.jsonl").exists())

    def test_an_unreadable_schema_does_not_claim_the_file_is_declared(self):
        mod = self._uut("perry_tasks_uut_asks2")
        real = mod.lib.load_schema
        mod.lib.load_schema = lambda *a, **k: (_ for _ in ()).throw(
            OSError("no schema here"))
        try:
            self.assertFalse(mod.ask_store_is_declared())
        finally:
            mod.lib.load_schema = real
        self.assertIn("What is missing is the DECLARATION",
                      mod.ASK_STORE_UNDECLARED)


class TestDriftIsReportedRatherThanAbsorbed(unittest.TestCase):
    """ADR-007 decision 2 over the fourth register, and the honest-line rule
    `perry-lint` follows for the other three."""

    def test_a_clean_import_reports_no_drift(self):
        p = _imported(self)
        stats = _lint(p.root)["ask_store_drift"]
        self.assertEqual(stats, {"store_present": True,
                                 "comparison_performed": True,
                                 "records": 4, "drifted": 0})

    def test_no_store_is_not_the_same_answer_as_a_clean_one(self):
        self._held = p = Project(board=board_with(REGISTER))
        payload = _lint(p.root)
        self.assertEqual(payload["ask_store_drift"]["store_present"], False)
        self.assertEqual(payload["ask_store_drift"]["comparison_performed"],
                         False)
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"].startswith("ask-store")], [])
        out = subprocess.run([sys.executable, str(LINT), "--root", str(p.root)],
                             capture_output=True, text=True)
        self.assertIn("no `asks.jsonl`", out.stdout)
        self.assertIn("unchecked, not clean", out.stdout)

    def test_one_hand_edit_is_exactly_one_finding(self):
        p = _imported(self)
        _edit(p, "sign off on the migration plan", "sign off on the PLAN")
        payload = _lint(p.root)
        rows = [f for f in payload["findings"] if f["rule"] == "ask-store-drift"]
        self.assertEqual(len(rows), 1)
        self.assertIn("USER-004", rows[0]["message"])
        self.assertEqual(payload["ask_store_drift"]["drifted"], 1)

    def test_a_row_the_store_never_saw_is_reported_once(self):
        """And an inserted row does NOT report every row below it — the key is
        the id, so nothing beneath it was renamed. That is the difference from
        `## Intake`, where the position IS the name."""
        p = _imported(self)
        _edit(p, "| USER-002 |",
              "| USER-009 | a brand new question | — | — | pending | "
              "2026-08-28 |\n| USER-002 |")
        payload = _lint(p.root)
        rows = [f for f in payload["findings"] if f["rule"] == "ask-store-drift"]
        self.assertEqual(len(rows), 1, [r["message"] for r in rows])
        self.assertIn("USER-009", rows[0]["message"])

    def test_a_moved_row_is_reported_once_for_the_section(self):
        p = _imported(self)
        board = p.root / "BOARD.md"
        lines = board.read_text().split("\n")
        i = next(n for n, l in enumerate(lines) if l.startswith("| USER-003 |"))
        j = next(n for n, l in enumerate(lines) if l.startswith("| USER-002 |"))
        lines[i], lines[j] = lines[j], lines[i]
        board.write_text("\n".join(lines))
        rows = [f for f in _lint(p.root)["findings"]
                if f["rule"] == "ask-store-drift"]
        self.assertEqual(len(rows), 1, [r["message"] for r in rows])
        self.assertIn("different order", rows[0]["message"])

    def test_the_ordinary_writer_reaches_the_store_and_leaves_no_drift(self):
        """**Converted by TASK-203.** It read
        `test_the_ordinary_writer_still_writes_the_section_and_that_is_drift`,
        and its docstring said `answer` writes the board and not the store —
        *"deliberately not converted (TASK-203)"*. TASK-203 is the row that
        converts it, so the assertion is now the other half of the same fact:
        the section and the store are written in one transaction, so there is
        nothing left to report as drift.

        The drift READING is not lost with it. It was never this command's to
        prove — `perry-task` keeps the store current, and what drifts a store
        is a hand edit, which
        `TestDriftIsReportedRatherThanAbsorbed`' other four tests cover by
        editing `BOARD.md` directly.
        """
        p = _imported(self)
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-task"), "answer",
             "USER-002", "--answer", "CSV, with a header row",
             "--root", str(p.root), "--json"],
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(_lint(p.root)["ask_store_drift"]["drifted"], 0)
        record = next(r for r in
                      [json.loads(l) for l in
                       (p.root / "asks.jsonl").read_text().split("\n")
                       if l.strip()] if r["id"] == "USER-002")
        self.assertIn("CSV, with a header row", record["status"])
        self.assertIs(record["answered"], True)

    def test_the_store_is_claimed_as_a_file_perry_wrote(self):
        """Without this every project that runs the import gets an `NS-01`
        against Perry's own claim — the bug TASK-196 had to fix for a store
        with no `id`, and this one has an `id`, so it needs the id branch to
        know a third shape."""
        p = _imported(self)
        lint = _lint_module()
        self.assertTrue(lint.looks_like_perry_record(p.root / "asks.jsonl"))
        # Narrowed to this file on purpose: `Project` fixtures carry an
        # unrelated `NS-01` about `tasks.jsonl` that predates this row, and a
        # test that asserted the whole list empty would be asserting somebody
        # else's bug stays fixed. Matched on `file` and NOT on a substring of
        # the message — `"asks.jsonl" in "tasks.jsonl"` is True, which is how
        # the first version of this passed the wrong finding through.
        self.assertEqual(
            [f for f in _lint(p.root)["findings"]
             if f["rule"] == "NS-01" and f["file"] == "asks.jsonl"], [])


# ── helpers ───────────────────────────────────────────────────────────────


def _tasks(root: Path, *argv):
    return subprocess.run([sys.executable, str(TASKS), *argv,
                           "--root", str(root)], capture_output=True, text=True)


def _lint(root: Path) -> dict:
    out = subprocess.run(
        [sys.executable, str(LINT), "--root", str(root), "--json"],
        capture_output=True, text=True)
    return json.loads(out.stdout)


def _store(p: Project) -> list[dict]:
    return [json.loads(l) for l in
            (p.root / "asks.jsonl").read_text().split("\n") if l.strip()]


def _imported(case: unittest.TestCase) -> Project:
    case._held = p = Project(board=board_with(REGISTER))
    out = _tasks(p.root, "asks-write", "--from-board")
    case.assertEqual(out.returncode, 0, out.stderr)
    return p


def _edit(p: Project, old: str, new: str) -> None:
    board = p.root / "BOARD.md"
    text = board.read_text()
    assert old in text, old
    board.write_text(text.replace(old, new, 1))


_STATE = None


def _perry_state():
    global _STATE
    if _STATE is None:
        _STATE = _load("perry_state_for_asks", PERRY_HOME / "bin" / "perry-state")
    return _STATE


_LINT_MOD = None


def _lint_module():
    global _LINT_MOD
    if _LINT_MOD is None:
        _LINT_MOD = _load("perry_lint_for_asks", LINT)
    return _LINT_MOD


def _load(name: str, path: Path):
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    unittest.main()
