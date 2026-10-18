"""`Role` is required once the project declares a role card — and only then.

DESIGN-006 § 5.2, decision #4, phase E. The asymmetry is the design, not a
convenience: **a project that never hears of roles behaves exactly as it does
today** (Goal 7) — no new column, no flag to learn, and no refusal naming a
concept it has not adopted. The same no-op property `modes/project.md` holds for
work modes.

Run: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "modes/project.md",
    "packs/software-ops/roles/",
    "schema/task-list-contract.md",
)

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

import config_store  # noqa: E402
from kernel_work_support import ACTOR, ready, task

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
        config_store.write_config(root, {"State root": "perry/"})
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
            task_actor.command([sys.executable, str(TOOL), "add", "--title", "t",
             "--summary", "A fixture row that exists so the writer has something to write. It carries no meaning beyond that.",
             "--deliverable", "an artifact with a test",
             "--verification", "the test passes",
             "--next", "n", *extra, "--root", str(root)], 'test_role_on_rows'),
            capture_output=True, text=True, env=env)

    def payload(self, root: Path) -> dict:
        env = dict(os.environ, PERRY_HOME=str(PERRY_HOME))
        r = subprocess.run(
            [sys.executable, str(TOOL), "list", "--all", "--json",
             "--root", str(root)], capture_output=True, text=True, env=env)
        return json.loads(r.stdout)


class TestRolesStayHostMetadata(Base):
    def test_native_create_needs_no_role_even_when_a_host_card_exists(self):
        sb = ready(self)
        card = sb.root / ".perry/roles/coding.md"
        card.parent.mkdir(parents=True)
        card.write_text(CARD)
        tid = task(sb)
        self.assertNotIn("role", sb.get(tid)["fields"])
        self.assertEqual(card.read_text(), CARD)

    def test_a_role_cannot_be_smuggled_into_a_native_task_field(self):
        sb = ready(self)
        tid = task(sb)
        before = sb.seq()
        out = sb.run("item update", data={"actor": ACTOR, "id": tid,
                                           "set": {"role": "coding"}})
        self.assertFalse(out.ok, out)
        self.assertEqual(sb.seq(), before)
        self.assertNotIn("role", sb.get(tid)["fields"])

    def test_dispatch_still_loads_role_cards_as_host_context(self):
        text = (PERRY_HOME / "work/reference/dispatch-preflight.md").read_text()
        self.assertIn("role", text.lower())
        self.assertIn(".perry/roles/", text)

    def test_retired_add_cannot_write_with_or_without_a_role_card(self):
        for roles in (None, {"coding.md": CARD}):
            root = self.project(roles)
            before = {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
            for args in ((), ("--role", "coding"), ("--role", "finance")):
                with self.subTest(roles=bool(roles), args=args):
                    out = self.add(root, *args)
                    self.assertEqual(out.returncode, 1, out.stderr)
                    self.assertIn("perry-kernel item create", out.stderr)
                    self.assertEqual({str(p.relative_to(root)): p.read_bytes()
                                      for p in root.rglob("*") if p.is_file()}, before)


class TestLegacyRoleReader(Base):
    def test_role_is_explicit_or_empty_in_the_frozen_payload(self):
        for role in ("coding", ""):
            with self.subTest(role=role):
                root = self.project()
                (root / "perry/tasks.jsonl").write_text(json.dumps({
                    "id": "TASK-001", "title": "Archived task", "status": "not_started",
                    "priority": "P1", "role": role}) + "\n")
                rows = self.payload(root)["tasks"]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["role"], role)


class TestTheContractDeclaresIt(unittest.TestCase):
    def test_the_version_moved_and_the_doc_says_why(self):
        doc = (PERRY_HOME / "schema" / "task-list-contract.md").read_text()
        # The version the TOOL emits, not a literal. This assertion is about
        # the doc and the payload naming one version; pinning the number here
        # made every later minor edit this file for a reason unrelated to
        # roles, which is how a check stops meaning what its name says.
        contract = next(
            line.split('"')[1] for line in
            (PERRY_HOME / "bin" / "perry-task").read_text().split("\n")
            if line.startswith("LIST_CONTRACT = "))
        self.assertIn(contract, doc)
        self.assertIn("### 1.8", doc)
        self.assertIn("### 1.9", doc)
        self.assertIn("### 1.10", doc)
        self.assertIn("Goal 7", doc,
                      "the changelog must say a roleless project is unaffected")


if __name__ == "__main__":
    unittest.main()
