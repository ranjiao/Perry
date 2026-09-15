"""An intake that overflows the board is the signal, not a formatting problem.

`modes/queue.md` puts `## Intake` inside `BOARD.md` on purpose — DESIGN-003
decision 3 chose zero new claimed paths — and says the pressure that creates on
the 200-line cap **is the feature**: *"an intake that overflows the board is a
project [that is not triaging]"*.

Two things contradicted that:

1. `perry-lint`'s `size-cap` finding prescribed *"split the overflow into a
   sibling file"* — moving the signal somewhere it can grow unnoticed, the one
   response the mode rules out.
2. `perry-state` carried **no intake block at all** — `## Intake` matched
   nothing in the board-section dispatch — so the correlation
   `work/reference/subcommands.md § triage` asks for (over cap *because* intake
   is undrained) was not computable from the payload the standup reads.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402

import config_store  # noqa: E402

LINT = PERRY_HOME / "bin" / "perry-lint"
STATE = PERRY_HOME / "bin" / "perry-state"

TASK_HEAD = ("| ID | Title | Owner | Status | Next action | Evidence | "
             "Verification |\n|---|---|---|---|---|---|---|\n")


class Base(unittest.TestCase):
    def project(self, intake_rows: int = 0, task_rows: int = 0) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        config_store.write_config(root, {"State root": "perry"})
        board = ["# Board", "", "## P1", "", TASK_HEAD.rstrip("\n")]
        board += [f"| T-{i} | t | o | not_started | n | — | V2 |"
                  for i in range(task_rows)]
        if intake_rows:
            board += ["", "## Intake", "",
                      "| Arrived | Request | Outcome |", "|---|---|---|"]
            board += [f"| 2026-08-{(i % 28) + 1:02d} | request {i} | — |"
                      for i in range(intake_rows)]
        (root / "perry" / "BOARD.md").write_text(
            "\n".join(board) + "\n", encoding="utf-8")
        self.imported(root)
        return root

    @staticmethod
    def imported(root: Path) -> None:
        """The board's tasks and `## Intake`, through their imports (TASK-262
        round 4b): `perry-state` reads `intake.jsonl`, not a held board.

        **`TestTheOverflowPrescriptionIsModeAware` left with the same round**
        (5 tests: the `size-cap` prescription over a held board of 220 intake
        rows — split, or do not split and triage). It policed the length of a
        file no reader opens any more; `files[id=board]` is not linted."""
        from held_board import import_board
        import_board(root, "write", "intake-write", remove=False)

    def size_cap(self, root: Path) -> str:
        r = subprocess.run([sys.executable, str(LINT), "--root", str(root),
                            "--json"], capture_output=True, text=True)
        for f in json.loads(r.stdout)["findings"]:
            if f["rule"] == "size-cap":
                return f["message"]
        return ""

    def state(self, root: Path) -> dict:
        r = subprocess.run([sys.executable, str(STATE), "--json",
                            "--root", str(root)], capture_output=True, text=True)
        return json.loads(r.stdout)


class TestTheStandupCanComputeTheCorrelation(Base):
    def test_the_payload_carries_the_intake_block(self):
        d = self.state(self.project(intake_rows=220))["intake"]
        self.assertEqual(d["rows"], 220)
        self.assertEqual(d["undischarged"], 220)
        self.assertEqual(d["oldest_undischarged"], "2026-08-01")

    def test_a_discharged_row_is_not_waiting(self):
        """`Outcome` is where a routing or a drop reason is written. The count
        that matters is what is still waiting, not how long the table is."""
        root = self.project(intake_rows=3)
        board = root / "perry" / "BOARD.md"
        board.write_text(
            board.read_text().replace("| request 0 | — |",
                                      "| request 0 | routed → TASK-001 |", 1),
            encoding="utf-8")
        self.imported(root)      # the edited section, re-imported (TASK-262 4b)
        d = self.state(root)["intake"]
        self.assertEqual((d["rows"], d["undischarged"]), (3, 2))

    def test_a_board_with_no_intake_section_reports_zeroes_not_a_missing_key(self):
        d = self.state(self.project(task_rows=2))["intake"]
        self.assertEqual(d, {"rows": 0, "undischarged": 0,
                             "oldest_undischarged": None})

    def test_the_board_parser_sees_the_section_at_all(self):
        """It matched nothing in the dispatch, which is why the payload had no
        block to carry."""
        board = ("# Board\n\n## Intake\n\n| Arrived | Request | Outcome |\n"
                 "|---|---|---|\n| 2026-08-01 | a | — |\n")
        self.assertEqual(len(P.parse_board(board).intake), 1)


if __name__ == "__main__":
    unittest.main()
