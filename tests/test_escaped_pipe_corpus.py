"""Every reader is asked the same question about the same row, at runtime.

**Four V4 rounds have defeated the static guard, and the fifth would too.**
Round 4 of TASK-067 planted thirteen shapes: six were caught and seven were
not — `" | ".join`, `%`, `.format`, `+`-concat on the write side, and
`.split("|", 6)`, `re.split(r"\\|", …)` and a `SEP` constant on the read side.
No regex over source text is going to catch those, and each round that widened
the pattern was answered by a shape the pattern did not have.

The same review names the asymmetry that matters: the WRITERS are backstopped
by `perry-lint`'s `ragged-row`, which judges the produced file rather than the
source that produced it. **The readers are backstopped by nothing.** This is
that backstop.

A row whose cell contains an escaped pipe reads one way through `split_row` and
another way through any private splitter. So build the board, ask every reader,
and require them to agree — which is true regardless of how the reader is
spelled, how deep its file sits, or whether it was written after this test.

Run: python3 tests/parallel test_escaped_pipe_corpus
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The cell that separates a correct reader from one with its own splitter. A
#: naive split yields four cells where the contract says three, shifting every
#: column after it.
TRICKY = r"quotes a header \| ID \| Risk \| and keeps going"

BOARD = f"""# Board

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | plain row | Claude | not_started | — | — | V2 |
| TASK-002 | escaped pipe | Claude | not_started | {TRICKY} | — | V2 |
| TASK-003 | after it | Claude | blocked | — | — | V4 |

## Top risks

| ID | Risk | Opened | Status |
| --- | --- | --- | --- |
| RISK-1 | {TRICKY} | 2026-08-01 | open |
"""


class TestEveryReaderAgrees(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "perry").mkdir()
        (self.dir / ".perry").mkdir()
        (self.dir / ".perry" / "config.md").write_text("State root: perry\n")
        (self.dir / "perry" / "BOARD.md").write_text(BOARD)
        seeded = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "perry-tasks"), "write",
             "--from-board", "--root", str(self.dir)],
            capture_output=True, text=True)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)

    def run_tool(self, name, *args, expect_zero=True):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "bin" / name), *args,
             "--root", str(self.dir), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        # `perry-lint` exits non-zero on ANY error, and this fixture is a bare
        # board with no OKR and no phase — it has plenty. What matters is which
        # findings it reports, not how many, so the exit code is checked only
        # where a non-zero one would mean the tool failed to run.
        if expect_zero:
            self.assertEqual(
                proc.returncode, 0,
                f"{name} exited {proc.returncode}: {proc.stderr[-300:]}")
        self.assertTrue(proc.stdout.strip(),
                        f"{name} produced no JSON: {proc.stderr[-300:]}")
        return json.loads(proc.stdout)

    def test_the_task_reader_sees_the_pipe_as_one_cell(self):
        """The value round-trips: `\\|` is a pipe IN a cell, not a delimiter."""
        d = self.run_tool("perry-task", "list", "--all")
        row = next(t for t in d["tasks"] if t["id"] == "TASK-002")
        self.assertIn("| ID | Risk |", row["next_action"])
        self.assertEqual(row["verification"], "V2",
                         "the columns after the escaped pipe shifted")

    def test_the_column_after_it_is_not_shifted(self):
        """The actual consequence. A private splitter does not crash — it moves
        every column one to the left, and the row still looks plausible."""
        d = self.run_tool("perry-task", "list", "--all")
        by_id = {t["id"]: t for t in d["tasks"]}
        self.assertEqual(by_id["TASK-003"]["status"], "blocked")
        self.assertEqual(by_id["TASK-002"]["status"], "not_started")

    def test_the_state_reader_counts_the_same_rows(self):
        s = self.run_tool("perry-state")
        self.assertEqual(s["board"]["open"], 3)

    def test_the_linter_reports_no_ragged_row(self):
        """If a reader miscounts the cells, `ragged-row` is what says so — and
        a clean board must not trip it."""
        out = self.run_tool("perry-lint", expect_zero=False)
        self.assertEqual(
            [f for f in out["findings"] if f["rule"] == "ragged-row"], [],
            "a correctly escaped row was read as ragged")

    def test_the_risk_row_survives_it_too(self):
        """A second table, because the first reader to get this wrong got it
        wrong on `## Top risks` — the table nobody was testing."""
        s = self.run_tool("perry-state")
        self.assertEqual(s["risks"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
