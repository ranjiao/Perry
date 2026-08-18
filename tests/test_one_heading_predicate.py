"""Four implementations of "where is this section", three answers in one call.

On a board whose heading reads `## **Top risks**` — a human bolding a heading,
which no rule forbids:

- `viewer/parsers.py § parse_board` could not see the section → **0 risks**;
- `bin/perry-task § ensure_section` could not see it either, so `risk-add`
  **appended a second `## Top risks`** and exited 0;
- the **id minter** read the rows by a third rule, saw the existing risks, and
  minted the next id in sequence — proving the rows were readable;
- `viewer/parsers.py § top_risks_section` had a fourth regex, so even after the
  first three were fixed the reader still reported zero.

Every risk already recorded became invisible to every tool, `perry-lint` said
nothing, and the writer reported success. Found by a V4 reviewer; the fourth
matcher was found by fixing the other three and re-running.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402

TASK = PERRY_HOME / "bin" / "perry-task"
STATE = PERRY_HOME / "bin" / "perry-state"


def _task_mod():
    spec = importlib.util.spec_from_loader(
        "perry_task",
        importlib.machinery.SourceFileLoader("perry_task", str(TASK)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BOARD = """# Board

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification |
|---|---|---|---|---|---|---|

## {heading}

| ID | Risk | Opened | Severity | Cleared |
|---|---|---|---|---|
| RX-001 | first risk | 2026-08-01 | H | — |
| RX-002 | second risk | 2026-08-02 | M | — |
"""

#: Spellings a person may reasonably write. None is forbidden by any rule, and
#: the check is the CATEGORY — decoration — rather than the one that bit.
FULL_BOARD = """# Board

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

## User Input Queue

| USER-id | Needed from user | Blocks | Status |
|---|---|---|---|

## {heading}

| ID | Risk | Opened | Status |
|---|---|---|---|
| RX-001 | a real risk | 2026-08-01 | active |
"""

DECORATED = ["Top risks", "**Top risks**", "`Top risks`", "**Top risks**  ",
             "Top risks (one-line; full list in `PROJECT_STATE.md`)",
             "主要风险", "**主要风险**"]


class TestEveryMatcherAgrees(unittest.TestCase):
    def setUp(self):
        self.task = _task_mod()

    def missing_sections(self, board_text: str) -> list[dict]:
        """`perry-lint`'s `missing-section` findings for this board — the fifth
        implementation, and the one migration acts on."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / "perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: perry\n",
                encoding="utf-8")
            (root / "perry" / "BOARD.md").write_text(board_text, encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(PERRY_HOME / "bin" / "perry-lint"),
                 "--root", str(root), "--json"], capture_output=True, text=True)
            return [f for f in json.loads(r.stdout)["findings"]
                    if f["rule"] == "missing-section"]

    def test_migration_does_not_append_a_second_section(self):
        """The consequence, end to end, on the tool that rewrites a stranger's
        files. This is what makes the fifth implementation worse than the other
        four: they made risks unreadable, this one made migration *write*."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry").mkdir()
            (root / "perry").mkdir()
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: perry\n",
                encoding="utf-8")
            board = root / "perry" / "BOARD.md"
            board.write_text(FULL_BOARD.format(heading="**Top risks**"),
                             encoding="utf-8")
            subprocess.run(
                [sys.executable, str(PERRY_HOME / "bin" / "perry-migrate"),
                 "apply", "--root", str(root)], capture_output=True, text=True)
            self.assertEqual(board.read_text().count("Top risks"), 1,
                             board.read_text())

    def test_all_five_agree_on_every_decorated_spelling(self):
        """The property. Any one of them disagreeing is how the risks went
        invisible, so they are asserted together rather than one per test.

        **Four was wrong.** A V4 reviewer found a fifth — `perry-lint`'s
        required-section check applied the raw schema regex to the raw heading —
        and it was the dangerous one, because `perry-migrate` acts on lint
        findings: told the section was missing, it appended a second, empty
        `## Top risks` above the project's real one. 1 risk visible before,
        **0 after**, and lint then reported **0 errors** with the file declared
        conformant."""
        for h in DECORATED:
            text = BOARD.format(heading=h)
            line = f"## {h}"
            with self.subTest(heading=h):
                self.assertTrue(P.heading_is(h, "Top risks"), "parsers")
                self.assertTrue(self.task.heading_matches(line, "Top risks"),
                                "perry-task")
                self.assertIsNotNone(P.top_risks_section(text), "section body")
                self.assertEqual(len(P.parse_board(text).risks), 2, "parse_board")
                self.assertNotIn(
                    "Top risks",
                    " ".join(f["message"] for f in self.missing_sections(text)),
                    "perry-lint reports the section missing")

    def test_a_heading_that_only_starts_the_same_is_not_a_match(self):
        """The boundary the old regex's `(?!\\w)` protected, kept. `## P2` must
        not match `## P20`, or a project with twenty priority bands loses one."""
        self.assertFalse(self.task.heading_matches("## P20", "P2"))
        self.assertTrue(self.task.heading_matches("## P2 (低优先 carry)", "P2"))


class TestTheWriterDoesNotDuplicateTheSection(unittest.TestCase):
    def project(self, heading: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: perry\n", encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text(
            BOARD.format(heading=heading), encoding="utf-8")
        return root

    def run_task(self, root: Path, *argv):
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        return subprocess.run([sys.executable, str(TASK), *argv,
                               "--root", str(root)],
                              capture_output=True, text=True, env=env)

    def risks_seen(self, root: Path) -> int:
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        r = subprocess.run([sys.executable, str(STATE), "--json",
                            "--root", str(root)],
                           capture_output=True, text=True, env=env)
        return (json.loads(r.stdout).get("risks") or {}).get("count")

    def test_risk_add_on_a_bolded_heading_writes_into_the_existing_section(self):
        root = self.project("**Top risks**")
        self.assertEqual(self.risks_seen(root), 2,
                         "the reader could not see the risks already there")
        out = self.run_task(root, "risk-add", "--title", "third risk")
        self.assertEqual(out.returncode, 0, out.stderr)
        board = (root / "perry" / "BOARD.md").read_text(encoding="utf-8")
        self.assertEqual(board.count("Top risks"), 1,
                         f"a second section was appended:\n{board}")
        self.assertEqual(self.risks_seen(root), 3,
                         "the risks already recorded went invisible")

    def test_the_earlier_risks_are_still_addressable_afterwards(self):
        """The consequence a user meets: not "a count is wrong" but "the risk I
        recorded cannot be cleared"."""
        root = self.project("**Top risks**")
        self.run_task(root, "risk-add", "--title", "third risk")
        out = self.run_task(root, "risk-clear", "RX-001", "--reason", "handled")
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
