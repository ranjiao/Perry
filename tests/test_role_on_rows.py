"""`Role` is required once the project declares a role card — and only then.

DESIGN-006 § 5.2, decision #4, phase E. The asymmetry is the design, not a
convenience: **a project that never hears of roles behaves exactly as it does
today** (Goal 7) — no new column, no flag to learn, and no refusal naming a
concept it has not adopted. The same no-op property `modes/project.md` holds for
work modes.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import tables as T  # noqa: E402

TOOL = PERRY_HOME / "bin" / "perry-task"
HEADER = ["ID", "Title", "Owner", "Status", "Next action", "Evidence"]
CARD = """# Role · coding

- Accepted by: user
- Default rung: V3
- Executors: any

## Context

Writes code.

## Loads

- knowledge: build-system

## May touch

- write: source

## Must escalate

- any `force-push`
"""


class Base(unittest.TestCase):
    def project(self, roles: dict[str, str] | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / "perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\nState root: perry/\n", encoding="utf-8")
        (root / "perry" / "BOARD.md").write_text("\n".join([
            "# Board", "",
            "## P1", "", T.render_row(HEADER), "|" + "---|" * len(HEADER), "",
            "## Cadence", "",
            "| ID | Recurring task | Owner | Frequency | Next due | Last evidence |",
            "|---|---|---|---|---|---|", "",
            "## User Input Queue", "",
            "| ID | Needed from user | Blocks | Asked | Status |",
            "|---|---|---|---|---|", "",
            "## Top risks", "",
            "| ID | Risk | Opened | Severity | Cleared |",
            "|---|---|---|---|---|", "",
        ]), encoding="utf-8")
        for name, text in (roles or {}).items():
            p = root / ".perry" / "roles" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return root

    def add(self, root: Path, *extra):
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        return subprocess.run(
            [sys.executable, str(TOOL), "add", "--title", "t",
             "--deliverable", "an artifact with a test",
             "--verification", "the test passes",
             "--next", "n", *extra, "--root", str(root)],
            capture_output=True, text=True, env=env)

    def payload(self, root: Path) -> dict:
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        r = subprocess.run(
            [sys.executable, str(TOOL), "list", "--all", "--json",
             "--root", str(root)], capture_output=True, text=True, env=env)
        return json.loads(r.stdout)


class TestGoal7AProjectWithNoRoles(Base):
    """The half that must not regress. Every assertion here is about a project
    that has declared nothing."""

    def test_add_does_not_ask_for_a_role(self):
        root = self.project()
        out = self.add(root)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_no_refusal_ever_mentions_roles(self):
        """A project that has not adopted the concept must not meet it in an
        error message."""
        root = self.project()
        out = self.add(root)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("--role", out.stderr + out.stdout)
        self.assertNotIn("role card", (out.stderr + out.stdout).lower())

    def test_the_board_gains_no_role_column(self):
        root = self.project()
        self.add(root)
        board = (root / "perry" / "BOARD.md").read_text(encoding="utf-8")
        self.assertNotIn("Role", board)

    def test_the_payload_still_carries_the_key_as_empty(self):
        """Always present, never missing — the contract's own rule. A consumer
        needs no `if "role" in task`."""
        root = self.project()
        self.add(root)
        t = self.payload(root)["tasks"][0]
        self.assertIn("role", t)
        self.assertEqual(t["role"], "")

    def test_a_role_passed_anyway_is_filed_not_refused(self):
        """Nothing is demanded and nothing is rejected — the flag is inert
        rather than an error, so a shared script works on both kinds of
        project."""
        root = self.project()
        out = self.add(root, "--role", "coding")
        self.assertEqual(out.returncode, 0, out.stderr)


class TestAProjectThatHasDeclaredRoles(Base):
    def setUp(self):
        self.root = self.project({"coding.md": CARD})

    def test_a_roleless_row_is_refused(self):
        out = self.add(self.root)
        self.assertEqual(out.returncode, 1)
        self.assertIn("--role is required", out.stderr)

    def test_the_refusal_lists_the_roles_that_exist(self):
        """A user who must name one needs to know the set — otherwise the
        refusal is a puzzle."""
        out = self.add(self.root)
        self.assertIn("coding", out.stderr)

    def test_a_role_with_no_card_is_refused_and_points_at_the_shipped_ones(self):
        out = self.add(self.root, "--role", "finance")
        self.assertEqual(out.returncode, 1)
        self.assertIn("has no card", out.stderr)
        self.assertIn("packs/software-ops/roles/", out.stderr)

    def test_a_declared_role_lands_in_the_cell_and_the_payload(self):
        out = self.add(self.root, "--role", "coding")
        self.assertEqual(out.returncode, 0, out.stderr)
        board = (self.root / "perry" / "BOARD.md").read_text(encoding="utf-8")
        self.assertIn("Role", board)
        self.assertEqual(self.payload(self.root)["tasks"][0]["role"], "coding")

    def test_a_refusal_writes_nothing(self):
        before = (self.root / "perry" / "BOARD.md").read_bytes()
        self.add(self.root)
        self.add(self.root, "--role", "nope")
        self.assertEqual((self.root / "perry" / "BOARD.md").read_bytes(), before)


class TestTheContractDeclaresIt(unittest.TestCase):
    def test_the_version_moved_and_the_doc_says_why(self):
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        self.assertIn("perry-task/list/1.11", doc)
        self.assertIn("### 1.8", doc)
        self.assertIn("### 1.9", doc)
        self.assertIn("### 1.10", doc)
        self.assertIn("Goal 7", doc,
                      "the changelog must say a roleless project is unaffected")


if __name__ == "__main__":
    unittest.main()
