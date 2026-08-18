"""A role card is a hiring contract the harness instantiates, never a workflow.

DESIGN-006 § 5.2, decision #1, phase C. Each of the four blocks has a mechanical
consumer — `Context` and `May touch` are rendered into the delegation prompt,
`Loads` drives knowledge injection, `Must escalate` is **unioned** with the
project high-stakes list in the dispatch pre-flight, `Accepted by` and
`Default rung` feed the close gate. A fifth section is prose nothing reads.

The rejection is the design, not a detail: `## Workflow` is how the distinction
gets lost one card at a time.

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
LINT = PERRY_HOME / "bin" / "perry-lint"
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
SPEC = next(f for f in SCHEMA["files"] if f["id"] == "role-card")
ALLOWED = SPEC["sections"]["allowed"]

CARD = """# Role · finance

- Accepted by: user
- Default rung: V5
- Executors: any

## Context

Prepares the monthly close.

## Loads

- knowledge: reporting

## May touch

- write: reports/

## Must escalate

- any outbound `invoice`
"""


class Base(unittest.TestCase):
    def project(self, cards: dict[str, str] | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- State root: .\n", encoding="utf-8")
        for name, text in (cards or {}).items():
            p = root / ".perry" / "roles" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return root

    def rules(self, root: Path) -> list[dict]:
        r = subprocess.run(
            [sys.executable, str(LINT), "--knowledge", "--root", str(root),
             "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["findings"]


class TestTheRejectionIsTheCategory(Base):
    def test_a_well_formed_card_is_clean(self):
        self.assertEqual(self.rules(self.project({"finance.md": CARD})), [])

    def test_a_workflow_heading_is_rejected(self):
        bad = CARD + "\n## Workflow\n\n1. Open the ledger.\n"
        found = self.rules(self.project({"finance.md": bad}))
        self.assertEqual([f["rule"] for f in found], ["role-card-is-a-workflow"])
        self.assertIn("hiring contract", found[0]["message"])

    def test_every_other_spelling_of_a_workflow_is_rejected_too(self):
        """The point. A guard written against the literal string `Workflow`
        catches `Workflow` — this project has shipped that guard before, under
        another name, in every review round."""
        for heading in ("Steps", "Procedure", "How to", "Process", "Playbook",
                        "步骤", "流程"):
            found = self.rules(self.project(
                {"f.md": CARD + f"\n## {heading}\n\ndo the thing\n"}))
            self.assertEqual([f["rule"] for f in found],
                             ["role-card-is-a-workflow"], heading)

    def test_a_section_nobody_thought_of_is_rejected_by_the_CLOSED_SET(self):
        """Not on any blacklist, and still reported — which is what makes this
        a category rather than a list. That is the whole difference."""
        found = self.rules(self.project(
            {"f.md": CARD + "\n## Notes\n\nsome prose\n"}))
        self.assertEqual([f["rule"] for f in found],
                         ["role-card-unknown-section"])

    def test_the_allowed_set_comes_from_the_schema(self):
        src = LINT.read_text(encoding="utf-8")
        self.assertNotIn('"Context", "Loads"', src,
                         "the linter carries its own copy of the section list")
        self.assertEqual(sorted(ALLOWED),
                         sorted(["Context", "Loads", "May touch",
                                 "Must escalate"]))

    def test_a_missing_block_is_reported(self):
        without = CARD.replace("## Must escalate\n\n- any outbound `invoice`\n", "")
        found = self.rules(self.project({"f.md": without}))
        self.assertEqual([f["rule"] for f in found], ["role-card-incomplete"])
        self.assertIn("Must escalate", found[0]["message"])


class TestTheShippedDefaults(unittest.TestCase):
    """`packs/software-ops/` ships the three that were hardcoded in
    `work/reference/delegate.md`. They are the closing of that hardcoding, so
    they have to pass the check they exist to demonstrate."""

    def test_the_three_default_cards_exist_and_are_clean(self):
        rdir = PERRY_HOME / "packs" / "software-ops" / "roles"
        names = sorted(p.stem for p in rdir.glob("*.md"))
        self.assertEqual(names, ["coding", "research", "review"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".perry" / "roles").mkdir(parents=True)
            (root / ".perry" / "config.md").write_text(
                "# Perry configuration\n\n- State root: .\n", encoding="utf-8")
            for p in rdir.glob("*.md"):
                (root / ".perry" / "roles" / p.name).write_text(
                    p.read_text(), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(LINT), "--knowledge", "--root", str(root),
                 "--json"], capture_output=True, text=True)
            self.assertEqual(json.loads(r.stdout)["findings"], [])

    def test_the_review_role_asks_for_a_higher_rung_than_the_others(self):
        """A role is warranted only when it has an acceptance standard distinct
        from the default (§ 5.2's existence test). If all three shipped the same
        rung and the same boundary they would be one role, and shipping them as
        three would be the thing the doc warns against."""
        rdir = PERRY_HOME / "packs" / "software-ops" / "roles"
        rung = {p.stem: [l for l in p.read_text().split("\n")
                         if l.startswith("- Default rung:")][0]
                for p in rdir.glob("*.md")}
        self.assertNotEqual(len(set(rung.values())), 1,
                            f"all three shipped the same rung: {rung}")


class TestGoal7NoRolesChangesNothing(Base):
    """DESIGN-006 Goal 7: a project that has declared no roles behaves exactly
    as it does today — the same no-op property `modes/project.md` holds for work
    modes, and the reason a project can ignore this whole layer."""

    def test_a_project_with_no_roles_directory_reports_nothing(self):
        self.assertEqual(self.rules(self.project()), [])

    def test_an_empty_roles_directory_reports_nothing(self):
        root = self.project()
        (root / ".perry" / "roles").mkdir()
        self.assertEqual(self.rules(root), [])

    def test_perry_itself_declares_no_roles_and_stays_clean(self):
        r = subprocess.run(
            [sys.executable, str(LINT), "--json"],
            capture_output=True, text=True, cwd=PERRY_HOME)
        self.assertEqual(json.loads(r.stdout)["errors"], 0)


if __name__ == "__main__":
    unittest.main()
