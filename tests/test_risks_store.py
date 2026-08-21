"""`## Top risks` is a projection of a record store — ADR-007 again.

TASK-040. The row was minted as *"Top risks becomes a table with id / opened /
cleared"*, failed review, and the re-review found the root cause was **four
implementations** of "what is a risk row". ADR-007 then superseded the premise:
the answer to a register four readers disagree about is not a better table.

So this file checks two things, in this order, because the order is the
argument:

1. **The store can reproduce what it replaces, byte for byte, before it holds
   a single field the table could not.** A migration that cannot reproduce
   what it replaces has not read it, and a renderer that quietly keeps a cell
   verbatim passes `cmp` while reproducing nothing — so the report's own
   fallback counters are asserted to be zero, not just the bytes.

2. **The four readers are one function, by identity and not by agreement.**
   `tests/test_risks.py` compares the reader's predicate against the writer's
   over a corpus, which is the best a test can do while there are two. There
   is one now, so the assertion is `is`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from test_task_writer import PT, Project

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
sys.path.insert(0, str(PERRY_HOME / "bin"))
import parsers as P  # noqa: E402
import perry_store as S  # noqa: E402

TASKS = PERRY_HOME / "bin" / "perry-tasks"
LINT = PERRY_HOME / "bin" / "perry-lint"

#: Perry's own register, quoted from `perry/BOARD.md` — an open row with no
#: `Opened` date, a cleared row carrying one inside its `Status` cell, and
#: prose in the `Risk` cells with backticks, an em-dash and a strikethrough in
#: it. The section this store has to reproduce is a real one or the byte gate
#: is being run against text written to pass it.
REGISTER = (
    "| ID | Risk | Opened | Status |\n"
    "|---|---|---|---|\n"
    "| RX-001 | Perry is half-adopted: `.perry/config.md` exists and flips "
    "`is_adopted()`. | | open |\n"
    "| RX-002 | ~~`LOAD-03` (10 decisions queued on the user)~~ — cleared "
    "2026-08-16 when DESIGN-003's 8 rows were decided. | | cleared 2026-08-16 "
    "— the queue drained |\n"
    "| RX-003 | DESIGN-003 phase G rewrites `SKILL.md § The hand-off "
    "contract`. | 2026-08-18 | open |\n"
)


def board_with(section: str) -> str:
    h = "| ID | Title | Owner | Status | Next action | Evidence |"
    sep = "|" + "|".join(["---"] * 6) + "|"
    return (
        "# Board — T\n\n"
        f"## P0 (must finish this period)\n\n{h}\n{sep}\n\n"
        f"## P1\n\n{h}\n{sep}\n\n"
        f"## P2\n\n{h}\n{sep}\n\n"
        "## Top risks (one-line; full list in `PROJECT_STATE.md`)\n\n"
        f"{section}\n"
    )


def derive(text: str, current: list[dict] | None = None):
    """(board, ops, records) for a board given as text."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
    tmp.write(text)
    tmp.close()
    board = PT.Board(Path(tmp.name))
    return board, PT, S.risk_records(board, PT, current)


class TestByteIdentityComesFirst(unittest.TestCase):
    """Item 1. **Before `cleared` exists**, the store has to put the section
    back exactly as it found it."""

    def test_the_section_round_trips_byte_for_byte(self):
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        rendered, report = S.risk_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_from_store"], 3)

    def test_no_cell_survived_as_a_literal(self):
        """`cmp` alone cannot tell a rebuilt cell from a copied one.

        `describe_cell` keeps a cell verbatim when no stored field claims it
        and keeps prose around a stored value as a prefix/suffix. Both are
        legitimate and both come back byte-identical, so a renderer that
        reproduced nothing would pass the test above. These three counters are
        what makes the byte result mean something.
        """
        board, ops, records = derive(board_with(REGISTER))
        _, report = S.risk_render(board, records, ops)
        self.assertEqual(report["cells_verbatim"], {})
        self.assertEqual(report["cells_wearing_decoration"], {})
        self.assertEqual(report["cells_the_store_and_board_disagree_on"], [])
        self.assertEqual(report["rows_verbatim"], [])
        self.assertEqual(report["rows_not_on_board"], [])

    def test_byte_identity_does_not_depend_on_the_new_field(self):
        """**The ordering the row asked for, as a test.**

        `cleared` is the field the register could not express in a cell. If
        the byte gate needed it, the gate would be testing the new field
        rather than the migration. Stripped from every record, the section
        still reproduces — because `cleared` renders into no column at all.
        """
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        stripped = [{k: v for k, v in r.items() if k != "cleared"}
                    for r in records]
        rendered, report = S.risk_render(board, stripped, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["cells_verbatim"], {})

    def test_a_wrong_stored_value_reddens_the_gate(self):
        """A renderer that cannot be made to print a wrong value cannot be
        shown to print a right one."""
        text = board_with(REGISTER)
        board, ops, records = derive(text)
        records[0]["status"] = "cleared 2020-01-01"
        rendered, report = S.risk_render(board, records, ops)
        self.assertNotEqual(rendered, text)
        self.assertIn("cleared 2020-01-01", rendered)
        self.assertEqual(
            [d["column"] for d in report["cells_the_store_and_board_disagree_on"]],
            ["Status"])

    def test_a_pipe_in_a_risk_statement_round_trips(self):
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the header `\\| ID \\| Risk \\|` is ambiguous | "
                   "2026-08-01 | open |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual(records[0]["risk"],
                         "the header `| ID | Risk |` is ambiguous")
        self.assertEqual(S.risk_render(board, records, ops)[0], text)

    def test_every_row_of_the_register_is_a_record(self):
        """**The store does not decide what a project may call a risk.**

        A first cell this tool would not have minted — `| 2 待核项 |`, from a
        real board — is still a row of the register, so it becomes a record and
        renders from one. Filtering rows against an id pattern here would
        invent a rule and quietly demote somebody's row to layout;
        `perry-lint`'s `bad-id` check is where a handle that does not match the
        declared pattern is reported, and reporting is the whole posture.
        """
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | first | | open |\n"
                   "| 2 待核项 | not a handle this tool would mint | | |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual([r["id"] for r in records], ["RX-001", "2 待核项"])
        rendered, report = S.risk_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_verbatim"], [])

    def test_a_repeated_id_does_not_leave_a_hole_in_the_order(self):
        """`order` is a position among the rows the STORE holds, not among the
        lines — the rule `board_order` states for tasks. A second row carrying
        an id the store already has is not a second record, and letting it
        advance the counter would leave a gap in a sequence whose only job is
        to say which record comes before which."""
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | first | | open |\n"
                   "| RX-001 | a duplicate somebody pasted | | open |\n"
                   "| RX-002 | second | | open |\n")
        _b, _o, records = derive(board_with(section))
        self.assertEqual([(r["id"], r["order"]) for r in records],
                         [("RX-001", 0), ("RX-002", 1)])

    def test_columns_resolve_by_name_in_both_directions(self):
        """`schema/README.md § Columns resolve by name`. A register a human
        wrote is not obliged to put `ID` first, and reading the id off
        `cells[0]` while writing every other cell by resolved name is how one
        row's value lands in another row's column."""
        section = ("| Status | Risk | ID | Opened |\n"
                   "|---|---|---|---|\n"
                   "| open | the vendor contract lapses | RX-001 | 2026-08-01 |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual(records[0]["id"], "RX-001")
        self.assertEqual(records[0]["status"], "open")
        rendered, report = S.risk_render(board, records, ops)
        self.assertEqual(rendered, text)
        self.assertEqual(report["rows_from_store"], 1)
        self.assertEqual(report["cells_verbatim"], {})

    def test_a_localized_register_round_trips(self):
        """`reference/i18n.md`: a board may be written in the project's own
        language, and columns resolve by name."""
        section = ("| 编号 | 风险 | 提出 | 状态 |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | 供应商合同到期 | 2026-08-01 | open |\n")
        text = board_with(section)
        board, ops, records = derive(text)
        self.assertEqual(records[0]["risk"], "供应商合同到期")
        self.assertEqual(records[0]["opened"], "2026-08-01")
        self.assertEqual(S.risk_render(board, records, ops)[0], text)


class TestOpenedAndClearedAreReal(unittest.TestCase):
    """Item 3, including the trap on the other side of it."""

    def test_a_cleared_risk_carries_both_dates(self):
        _b, _o, records = derive(board_with(REGISTER))
        by_id = {r["id"]: r for r in records}
        self.assertEqual(by_id["RX-002"]["cleared"], "2026-08-16")
        self.assertEqual(by_id["RX-003"]["opened"], "2026-08-18")

    def test_a_risk_with_neither_date_is_not_invented_one(self):
        """**The `current: 0` defect, one register over.** A default that
        stands in for an unrecorded fact reads as a recorded one."""
        _b, _o, records = derive(board_with(REGISTER))
        by_id = {r["id"]: r for r in records}
        self.assertEqual(by_id["RX-001"]["opened"], "")
        self.assertEqual(by_id["RX-001"]["cleared"], "")

    def test_a_risk_cleared_without_a_date_carries_no_date(self):
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the vendor contract lapses | | cleared |\n")
        _b, _o, records = derive(board_with(section))
        self.assertEqual(records[0]["cleared"], "")
        self.assertEqual(records[0]["status"], "cleared")

    def test_the_store_is_what_cleared_means_once_there_is_one(self):
        """ADR-007 decision 2: the store is the value, the prose is a
        projection of it. A hand edit to the `Status` cell does not silently
        replace a stored date — `check_risk_store_drift` reports it."""
        stored = [{"id": "RX-002", "risk": "x", "opened": "",
                   "cleared": "2026-08-16", "status": "cleared 2026-08-16",
                   "order": 0}]
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-002 | x | | cleared 2099-01-01 |\n")
        _b, _o, records = derive(board_with(section), stored)
        self.assertEqual(records[0]["cleared"], "2026-08-16")

    def test_perry_state_emits_a_cleared_risks_dates(self):
        """A cleared risk is not in `items` — it is not a top risk — so before
        `cleared_items` its dates were emitted by nothing at all."""
        p = Project(board=board_with(REGISTER))
        out = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(p.root), "--json"],
            capture_output=True, text=True)
        risks = json.loads(out.stdout)["risks"]
        self.assertEqual([r["id"] for r in risks["cleared_items"]], ["RX-002"])
        self.assertEqual(risks["cleared_items"][0]["cleared_on"], "2026-08-16")
        self.assertNotIn("RX-002", [r["id"] for r in risks["items"]])
        self.assertEqual([r["opened"] for r in risks["items"]
                          if r["id"] == "RX-003"], ["2026-08-18"])


class TestTheReadersAreOneFunction(unittest.TestCase):
    """Item 4. `tests/test_risks.py` asserts the reader and the writer AGREE
    over a corpus, which is the strongest claim available while there are two
    of them. These assert there is one."""

    def test_the_register_header_predicate_is_one_object(self):
        self.assertIs(PT.is_risk_header, P.is_risk_register_header)

    def test_the_bullet_and_placeholder_rules_are_one_object(self):
        self.assertIs(PT._RISK_BULLET, P._RE_RISK_BULLET)
        self.assertIs(PT._RISK_PLACEHOLDER, P._RE_RISK_PLACEHOLDER)

    def test_the_columns_are_one_list(self):
        self.assertIs(PT.RISK_COLUMNS, P.RISK_COLUMNS)

    def test_the_writer_asks_the_store_which_table_is_the_register(self):
        """`bin/perry-task § risk_section_shape` used to scan the section
        itself. It delegates now, so "which table is the register" is answered
        once for the writer, the reader and the renderer."""
        board, ops, _ = derive(board_with(REGISTER))
        self.assertEqual(PT.risk_section_shape(board)[0], "table")
        self.assertEqual(S.risk_section_shape(board, ops)[0], "table")

    def test_clearing_a_risk_a_human_retired_is_refused(self):
        """The concrete cost of the fourth copy. `cmd_risk_clear` knew three
        of the eight words the reader knows, so a risk retired as `mitigated`
        read as live here and as cleared everywhere else — and clearing it
        again overwrote the first clear's date and its reason."""
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-001 | the vendor contract lapses | | mitigated "
                   "2026-01-04 — renewed |\n")
        p = Project(board=board_with(section))
        rc, out = p.run("risk-clear", "RX-001", "--reason", "again")
        self.assertEqual(rc, 1)
        self.assertIn("already cleared", json.dumps(out))
        self.assertIn("mitigated 2026-01-04 — renewed", p.board())


class TestAHandEditIsReported(unittest.TestCase):
    """Item 2. Reported at the severity the board's own drift check uses —
    `warn`, because the store is authoritative and rendering restores the
    projection. Reported, not refused."""

    def _lint(self, root: Path) -> dict:
        out = subprocess.run(
            [sys.executable, str(LINT), "--root", str(root), "--json"],
            capture_output=True, text=True)
        return json.loads(out.stdout)

    def _project(self, section: str, store: list[dict]) -> Project:
        # **Held on `self`.** `Project` owns a `TemporaryDirectory`, which
        # deletes the tree when the object is collected — so
        # `self._lint(self._project(...).root)` linted a path that no longer
        # existed and every drift assertion in this class failed with an empty
        # finding list, which is exactly what "no store" looks like.
        self._held = p = Project(board=board_with(section))
        (p.root / "risks.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in store))
        return p

    STORE = [{"id": "RX-001", "risk": "the vendor contract lapses",
              "opened": "2026-08-01", "cleared": "", "status": "open",
              "order": 0}]
    SECTION = ("| ID | Risk | Opened | Status |\n"
               "|---|---|---|---|\n"
               "| RX-001 | the vendor contract lapses | 2026-08-01 | open |\n")

    def test_a_clean_register_reports_nothing_and_says_it_compared(self):
        payload = self._lint(self._project(self.SECTION, self.STORE).root)
        self.assertEqual(payload["risk_store_drift"],
                         {"store_present": True, "comparison_performed": True,
                          "records": 1, "drifted": 0})
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"].startswith("risk-store")], [])

    def test_a_hand_edited_cell_is_reported_as_a_warning(self):
        edited = self.SECTION.replace("the vendor contract lapses",
                                      "somebody typed this in by hand")
        payload = self._lint(self._project(edited, self.STORE).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertEqual(drifted[0]["severity"], "warn")
        self.assertIn("RX-001", drifted[0]["message"])
        self.assertIn("`risk`", drifted[0]["message"])
        self.assertEqual(payload["risk_store_drift"]["drifted"], 1)
        # **Reported, not refused, and never an error.** A drifted register
        # still has a valid register shape, and the conformance gate's boundary
        # is precise: warnings are quality signals, errors are shape
        # violations. (The fixture board carries unrelated `missing-section`
        # errors, so `payload["errors"]` is not the assertion here — the
        # severity of THIS rule is.)
        self.assertEqual({f["severity"] for f in payload["findings"]
                          if f["rule"].startswith("risk-store")}, {"warn"})

    def test_a_hand_added_row_the_store_never_saw_is_reported(self):
        extra = self.SECTION + "| RX-002 | typed in by hand | | open |\n"
        payload = self._lint(self._project(extra, self.STORE).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("RX-002", drifted[0]["message"])
        self.assertIn("the store has no record of it", drifted[0]["message"])

    def test_a_stored_risk_the_section_does_not_render_is_reported(self):
        store = self.STORE + [{"id": "RX-002", "risk": "second", "opened": "",
                               "cleared": "", "status": "open", "order": 1}]
        payload = self._lint(self._project(self.SECTION, store).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("renders no row for it", drifted[0]["message"])

    def test_the_field_with_no_column_cannot_drift_and_is_not_lost(self):
        """**`cleared` renders into no cell, so nothing in the file can
        disagree with it** — and that is a property, not a hole.

        It is carried across every rebuild from the store, exactly as a task's
        `summary` is (`bin/perry-task § store_records`, ADR-009): a value the
        projection cannot express must not be recoverable from prose, or the
        store stops being what the field means. A hand edit that contradicts
        it is still caught, through the column that does exist — asserted in
        the test below.
        """
        store = [dict(self.STORE[0], cleared="2026-09-09")]
        payload = self._lint(self._project(self.SECTION, store).root)
        self.assertEqual(payload["risk_store_drift"]["drifted"], 0)
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"] == "risk-store-drift"], [])

    def test_a_hand_written_cleared_date_is_reported_through_status(self):
        store = [dict(self.STORE[0], cleared="2026-08-16",
                      status="cleared 2026-08-16 — the vendor renewed")]
        edited = self.SECTION.replace("| open |", "| cleared 2099-01-01 |")
        payload = self._lint(self._project(edited, store).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("`status`", drifted[0]["message"])
        self.assertIn("2099-01-01", drifted[0]["message"])

    def test_a_row_moved_by_hand_is_reported_once_for_the_section(self):
        """`order` is a fact about a sequence, not about a row. Comparing it
        like the other fields turns one moved row into a finding for every row
        beneath it — the whole-section diff `order` exists to prevent,
        re-created inside the report about it (`_order_drift`)."""
        section = ("| ID | Risk | Opened | Status |\n"
                   "|---|---|---|---|\n"
                   "| RX-002 | second | | open |\n"
                   "| RX-001 | first | | open |\n")
        store = [{"id": "RX-001", "risk": "first", "opened": "", "cleared": "",
                  "status": "open", "order": 0},
                 {"id": "RX-002", "risk": "second", "opened": "", "cleared": "",
                  "status": "open", "order": 1}]
        payload = self._lint(self._project(section, store).root)
        drifted = [f for f in payload["findings"] if f["rule"] == "risk-store-drift"]
        self.assertEqual(len(drifted), 1, drifted)
        self.assertIn("file RX-002 → RX-001", drifted[0]["message"])
        self.assertIn("store RX-001 → RX-002", drifted[0]["message"])

    def test_no_store_is_not_a_clean_store(self):
        self._held = p = Project(board=board_with(self.SECTION))
        payload = self._lint(p.root)
        self.assertEqual(payload["risk_store_drift"]["store_present"], False)
        self.assertEqual(payload["risk_store_drift"]["comparison_performed"],
                         False)
        self.assertEqual(
            [f for f in payload["findings"]
             if f["rule"].startswith("risk-store")], [])

    def test_a_badly_typed_record_is_named_and_does_not_kill_the_lint(self):
        store = [dict(self.STORE[0], order="0")]
        payload = self._lint(self._project(self.SECTION, store).root)
        bad = [f for f in payload["findings"]
               if f["rule"] == "risk-store-badly-typed"]
        self.assertEqual(len(bad), 1, bad)
        self.assertIn("`order`", bad[0]["message"])
        self.assertEqual(payload["risk_store_drift"]["comparison_performed"],
                         False)

    def test_the_risks_store_is_not_reported_as_a_file_perry_did_not_write(self):
        """`looks_like_perry_record` knew one record shape. A risks store has
        fields outside `STORED`, so without this it is reported as foreign
        against Perry's own claim, on every project that has one."""
        import importlib.machinery
        import importlib.util
        spec = importlib.util.spec_from_loader(
            "perry_lint_mod",
            importlib.machinery.SourceFileLoader("perry_lint_mod", str(LINT)))
        lint = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint)
        p = self._project(self.SECTION, self.STORE)
        self.assertTrue(lint.looks_like_perry_record(p.root / "risks.jsonl"))


class TestTheMigrationSurface(unittest.TestCase):

    def _tasks(self, root: Path, *argv):
        return subprocess.run([sys.executable, str(TASKS), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True)

    def test_risks_diff_is_green_on_a_section_it_can_reproduce(self):
        p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "risks-diff")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertTrue(report["identical"])
        self.assertEqual(report["source"], "board")
        self.assertEqual(report["rows_from_store"], 3)

    def test_risks_diff_reddens_when_the_store_and_the_section_disagree(self):
        p = Project(board=board_with(REGISTER))
        (p.root / "risks.jsonl").write_text(json.dumps(
            {"id": "RX-001", "risk": "not what the board says", "opened": "",
             "cleared": "", "status": "open", "order": 0}) + "\n")
        out = self._tasks(p.root, "risks-diff")
        self.assertEqual(out.returncode, 1)
        report = json.loads(out.stdout)
        self.assertFalse(report["identical"])
        self.assertEqual(report["source"], "store")
        self.assertIn("not what the board says",
                      report["first_difference"]["rendered"])

    def test_risks_render_write_refuses_without_a_store(self):
        """Rendering the section from records derived out of that same section
        writes the file back over itself and reports success."""
        p = Project(board=board_with(REGISTER))
        before = p.board()
        out = self._tasks(p.root, "risks-render", "--write")
        self.assertEqual(out.returncode, 2)
        self.assertIn("nothing to render", out.stderr)
        self.assertEqual(p.board(), before)

    def test_risks_build_names_the_shape_it_found(self):
        p = Project(board=board_with("- H · the vendor contract lapses\n"))
        report = json.loads(self._tasks(p.root, "risks-build").stdout)
        self.assertEqual(report["register"], "bullets")
        self.assertEqual(report["records"], 0)

    def test_risks_write_refuses_and_names_the_missing_declaration(self):
        """**The stop this row hit.** A canonical record file in the state
        root is declared in `schema/state-schema.json § claims` with an owner
        and an anchor, the way `tasks.jsonl` is. That surface is behind the
        project's safety gate, so the store is implemented and unwritten, and
        the refusal says which of the two it is."""
        p = Project(board=board_with(REGISTER))
        out = self._tasks(p.root, "risks-write", "--from-board")
        self.assertEqual(out.returncode, 1)
        self.assertIn("claims", out.stderr)
        self.assertFalse((p.root / "risks.jsonl").exists())

    def test_the_refusal_names_the_gap_that_is_actually_open(self):
        """Two gaps, one at a time, and the message must not outlive its own
        condition.

        The declaration landed on 2026-08-21. A refusal that keeps naming it
        sends whoever reads it to add a `claims[]` entry that is already
        there — the same wasted trip TASK-114's v1 delegation prompt sent an
        agent on, for the same reason: a message measured against a world that
        moved. So the branch is read off the schema, and BOTH branches are
        asserted here rather than only whichever one is live today."""
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("perry_tasks_uut",
                                                      str(TASKS))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)

        # The live schema declares it, so this is the branch shipping today.
        self.assertTrue(mod.risk_store_is_declared(),
                        "schema/state-schema.json no longer claims "
                        "risks.jsonl — the declaration was reverted")
        self.assertIn("DECLARATION has landed", mod.risk_store_refusal())
        self.assertIn("claims", mod.risk_store_refusal())

        # And the other branch, reached by making the reader say no. Without
        # this the two-message split is a constant nothing selects between.
        real = mod.risk_store_is_declared
        mod.risk_store_is_declared = lambda: False
        try:
            self.assertIn("What is missing is the DECLARATION",
                          mod.risk_store_refusal())
        finally:
            mod.risk_store_is_declared = real

    def test_an_unreadable_schema_does_not_claim_the_file_is_declared(self):
        """"I cannot see it" is not "it is there" — the same rule that makes an
        unknown dependency id unsatisfied. A schema that will not load must
        fall to the undeclared branch, or a broken install silently reports
        the safer of the two gaps as closed."""
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("perry_tasks_uut2",
                                                      str(TASKS))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)

        real = mod.lib.load_schema
        mod.lib.load_schema = lambda *a, **k: (_ for _ in ()).throw(
            OSError("no schema here"))
        try:
            self.assertFalse(mod.risk_store_is_declared())
            self.assertIn("What is missing is the DECLARATION",
                          mod.risk_store_refusal())
        finally:
            mod.lib.load_schema = real


if __name__ == "__main__":
    unittest.main()
