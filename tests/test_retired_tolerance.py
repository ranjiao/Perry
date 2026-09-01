"""TASK-045 — the per-shape tolerance branches, retired behind the marker.

ADR-004 § *Where tolerance lives now* is the authority this suite enforces, and
it is two rules, not one:

| | Before | After |
|---|---|---|
| `/perry adopt`, `/perry diagnose` | tolerant | **tolerant, and more so** |
| `perry-state`, `perry-task`, `perry-goals`, `perry-decide`, `perry-lint` | tolerant | **strict**, against Perry's declared shape |
| Reading an unmigrated project | tolerant | tolerant enough to *report* and to drive adoption; no writes |

So this file has to hold two things at once, and the second is the one that is
easy to lose:

1. **§ 1 — the retired branch.** `bin/perry-task § Board.find_section_row` used
   to fall back to column 0 for "a section whose header names no id column at
   all: those tables predate the glossary and their first cell is the handle by
   convention". That is a per-shape branch by ADR-004's own definition — it
   accepts a shape the declared schema does not describe and reads it anyway,
   silently — and it is unreachable for a declared file, because all three
   sections it serves declare an id column whose absence `perry-lint` reports
   as a `table-columns` **error**. Restoring it turns every test in § 1 red.

2. **§ 2 — the tolerant readers that stay.** A project that has never migrated
   must still be *readable*, because that is what adoption reads. The existing
   suite mostly runs on migrated fixtures and cannot see this, so `LEGACY` below
   is a board with none of Perry's structure: work under the project's own
   headings, a bullet `## Top risks`, a `## User Input Queue` carrying `Idle`
   and no `Asked`, prose in `Frequency`, an `## Intake` a column wider than the
   schema's. Every reader in § 2 must keep reading it.

3. **§ 3 — the thing the `enforce` flip was supposed to buy.** A file the user
   declared, which then stopped matching its shape, is refused rather than
   written under protest.

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
TASK = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"
STATE = PERRY_HOME / "bin" / "perry-state"
LINT = PERRY_HOME / "bin" / "perry-lint"
CONFORM = PERRY_HOME / "bin" / "perry-conform"

sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))


#: A project that never migrated, and never will unless someone asks it to.
#: Every shape in here is one ADR-004's Context table names as a real board:
#: gimegime-pmo's own workstream headings instead of `## P0`/`## P1`/`## P2`,
#: the bullet `## Top risks` that predates the tool-written table, the `Idle`
#: column a project kept after dropping `Asked`, a four-column `## Intake`, and
#: a `Frequency` cell holding prose no scheduler can read.
LEGACY = """# Board — legacy

## Intake

| Arrived | Source | Request | Outcome |
|---|---|---|---|
| 2026-07-02 | email | a partner asked for the ledger export | — |

## Open — 投资线

| ID | Title | Owner | Status |
|---|---|---|---|
| INV-001 | 尽调 second pass | 老王 | open |

## Open — 工程线 · phase #004

| ID | Title | Owner | Status |
|---|---|---|---|
| ~~ENG-007~~ | retired build step | dev | done |

## Cadence

| ID | Recurring task | Owner | Frequency | Next due |
|---|---|---|---|---|
| CAD-001 | weekly ledger reconcile | 老王 | every other Friday | see evidence/ |

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|
| USER-001 | which staging default? | INV-001 | 12 | pending |

## Top risks

- H · the vendor contract lapses in September
- ~~M · the notarization cert expired~~ — cleared 2026-08-10
"""

#: Perry's own shape, for the sections § 1 is about. Declarable as it stands.
CONFORMANT = """# Board — T

## P0

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence

| ID | Recurring task | Owner | Frequency | Next due |
|---|---|---|---|---|
| CAD-001 | weekly reconcile | dev | weekly | 2026-08-30 |

## User Input Queue

| USER-id | Needed from user | Blocks | Asked | Status |
|---|---|---|---|---|
| USER-001 | which staging default? | — | 2026-08-01 | pending |

## Top risks

| ID | Risk | Opened | Status |
|---|---|---|---|
| RX-001 | the vendor contract lapses | 2026-08-01 | open |
"""


def without_id_column(board: str, heading: str) -> str:
    """The same board with one section's id column deleted, header and rows.

    Not a hand-written second board: the point is that everything else about
    the section is Perry's own shape, so a test that goes green cannot be
    passing for some other difference.
    """
    out, inside = [], False
    for line in board.split("\n"):
        if line.startswith("## "):
            inside = line.startswith(f"## {heading}")
        if inside and line.strip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            line = "|" + "|".join(cells[1:]) + "|"
        out.append(line)
    return "\n".join(out)


class Project:
    """A throwaway project. Advisory by default, because § 1 and § 2 are not
    about the gate — they are about what the tools do once past it."""

    def __init__(self, board: str = CONFORMANT, gate: str = "",
                 store: bool = False):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + gate)
        (self.root / "BOARD.md").write_text(board)
        if store:
            self.run(TASKS, "write", "--from-board", json_out=False)

    def run(self, tool: Path, *argv, json_out: bool = True):
        argv = [*argv, "--root", str(self.root)]
        if json_out:
            argv.append("--json")
        r = subprocess.run([sys.executable, str(tool), *argv],
                           capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}"), r.stderr
        except json.JSONDecodeError:
            return r.returncode, r.stdout, r.stderr

    def board(self) -> str:
        return (self.root / "BOARD.md").read_text()

    def __del__(self):
        self.dir.cleanup()


# ── 1 · the retired branch ────────────────────────────────────────────────


class TestTheIdColumnFallbackIsRetired(unittest.TestCase):
    """`Board.find_section_row` resolves the id column by name, or refuses.

    Every test here is a mutation anchor: put `next(…, 0)` back in place of
    `next(…, -1)` and the refusal becomes a silent write into column 0 — which
    on `| Risk | Opened | Status |` is somebody's risk *statement*, and on
    `| Needed from user | Blocks | Idle | Status |` is the question itself.
    """

    def refusal(self, board: str, *argv) -> str:
        p = Project(board=board)
        before = p.board()
        rc, out, err = p.run(TASK, *argv)
        self.assertEqual(rc, 1, f"expected a refusal, got {out!r}")
        self.assertEqual(p.board(), before, "the file was written anyway")
        return out.get("refused", "") if isinstance(out, dict) else err

    def test_risk_clear_refuses_a_top_risks_table_with_no_id_column(self):
        msg = self.refusal(without_id_column(CONFORMANT, "Top risks"),
                           "risk-clear", "RX-001", "--reason", "it stopped")
        self.assertIn("no id column", msg)
        self.assertIn("Top risks", msg)

    def test_answer_refuses_a_queue_with_no_id_column(self):
        msg = self.refusal(without_id_column(CONFORMANT, "User Input Queue"),
                           "answer", "USER-001", "--answer", "the second one")
        self.assertIn("no id column", msg)

    def test_cadence_done_refuses_a_register_with_no_id_column(self):
        msg = self.refusal(without_id_column(CONFORMANT, "Cadence"),
                           "cadence-done", "CAD-001",
                           "--evidence", "evidence/2026-08/run.md")
        self.assertIn("no id column", msg)

    def test_the_refusal_names_the_road_rather_than_stopping(self):
        """ADR-004 § 4: a gate that says "not conformant" and stops is a wall.
        Every refusal this row adds ends in a command the reader can run."""
        msg = self.refusal(without_id_column(CONFORMANT, "Top risks"),
                           "risk-clear", "RX-001", "--reason", "it stopped")
        self.assertIn("perry-migrate", msg)
        self.assertIn("perry-conform declare", msg)

    def test_the_wrong_row_is_not_cleared_by_guessing_column_zero(self):
        """The measured cost of the branch, as the property it violated.

        With the fallback in place `RX-001` matched nothing in column 0 and the
        loop fell through to "is not a row" — but on a table whose first column
        happens to hold handle-shaped text it matched the WRONG row and wrote
        the clear into it. Asserted as "no cell of this section changed".
        """
        board = without_id_column(CONFORMANT, "Top risks")
        p = Project(board=board)
        p.run(TASK, "risk-clear", "the vendor contract lapses",
              "--reason", "it stopped")
        self.assertEqual(p.board(), board)


    def test_the_localized_spelling_still_resolves(self):
        """`编号` is the declared Chinese spelling of `ID`, so it must resolve
        by NAME — the fallback was never what carried the localized case, and a
        retirement that broke it would be trading one silent defect for another.
        """
        p = Project(board=CONFORMANT.replace(
            "| ID | Risk | Opened | Status |\n|---|---|---|---|",
            "| 编号 | 风险 | 提出 | 状态 |\n|---|---|---|---|"))
        rc, out, err = p.run(TASK, "risk-clear", "RX-001", "--reason", "好了")
        self.assertEqual(rc, 0, f"{out!r} {err}")

    def test_the_missing_column_is_a_shape_error_not_a_matter_of_taste(self):
        """The reason the branch is retirable, asserted rather than argued:
        `perry-lint` calls the id-less section a `table-columns` ERROR, so the
        board cannot be declared conformant and, under `enforce`, cannot be
        written to at all."""
        p = Project(board=without_id_column(CONFORMANT, "Top risks"))
        _, out, _ = p.run(LINT)
        rules = {f["rule"] for f in out["findings"] if f["severity"] == "error"}
        self.assertIn("table-columns", rules)


# ── 2 · the tolerant readers that stay ────────────────────────────────────


class TestAProjectThatNeverMigratedStillReads(unittest.TestCase):
    """ADR-004 row 3. `adopt` and `diagnose` read a foreign project to propose
    a migration; if these go red, adoption has nothing to read.

    Deliberately a NEW fixture. The existing suite is built almost entirely on
    boards Perry itself wrote, so it cannot see a regression here.
    """

    @classmethod
    def setUpClass(cls):
        cls.p = Project(board=LEGACY, gate="", store=True)

    def test_perry_lint_reports_the_shape_rather_than_refusing_to_read(self):
        rc, out, _ = self.p.run(LINT)
        self.assertEqual(rc, 1, "an unmigrated board has findings")
        rules = [f["rule"] for f in out["findings"]]
        self.assertIn("missing-section", rules)
        # It read the whole file to say so — a reader that bailed on the first
        # unfamiliar heading would report one finding, not three.
        self.assertGreaterEqual(rules.count("missing-section"), 3)

    def test_the_namespace_check_adoption_runs_first_still_answers(self):
        """`reference/adoption.md § 3 step 0` — the one command the adoption
        interview runs before any goal talk."""
        rc, out, err = self.p.run(LINT, "--claims")
        self.assertEqual(rc, 0, err)

    def test_the_shared_reader_still_reads_the_bullet_risk_register(self):
        snap = P.load_snapshot(self.p.root)
        self.assertEqual(snap.risks_source, "bullets")
        self.assertEqual(len(snap.top_risks), 2)
        self.assertTrue(snap.top_risks[1].resolved,
                        "the struck-through bullet is a cleared risk")

    def test_the_queue_age_still_computes_from_a_board_with_no_asked_column(self):
        """`Idle` is declared optional precisely so this board keeps working —
        the number-out-of-the-cell branch in `bin/perry-state § idle_days` is a
        DECLARED shape, not a tolerance, and stays."""
        _, out, err = self.p.run(TASK, "list", "--all")
        self.assertEqual(out["asks"]["items"][0]["idle_days"], 12, err)

    def test_the_projects_own_headings_are_read_and_named(self):
        _, out, err = self.p.run(TASK, "list", "--all")
        headings = {s["heading"] for s in out["conformance"]["sections_read"]}
        self.assertIn("Open — 投资线", headings)
        self.assertIn("Open — 工程线 · phase #004", headings)
        self.assertEqual({t["id"] for t in out["tasks"]},
                         {"INV-001", "ENG-007"}, err)

    def test_an_unreadable_frequency_is_reported_never_rounded_to_fine(self):
        _, out, err = self.p.run(STATE)
        unreadable = out["cadence"]["unreadable_frequency"]
        self.assertEqual([r["id"] for r in unreadable], ["CAD-001"], err)

    def test_the_wider_intake_table_is_still_drained_by_name(self):
        """ADR-004's own Context row: *`route` cannot drain `## Intake` on a
        board whose table is four columns wide*. The extra column is legal —
        `perry-lint` checks that the declared columns are PRESENT, not that
        they are the only ones — so this must keep reading."""
        _, out, err = self.p.run(TASK, "list", "--all")
        rows = out["intake"]["rows"]
        self.assertEqual(len(rows), 1, err)
        self.assertIn("ledger export", rows[0]["request"])
        self.assertFalse(rows[0]["discharged"])

    def test_nothing_here_wrote_to_the_project(self):
        """The whole of row 3: *tolerant enough to report … no writes.*"""
        self.assertEqual(self.p.board(), LEGACY)


# ── 3 · what the enforce flip was supposed to buy ─────────────────────────




if __name__ == "__main__":
    unittest.main()
