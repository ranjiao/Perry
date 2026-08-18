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
STATE = PERRY_HOME / "bin" / "perry-state"
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

    # ── phase D: the same property at `delegate` and the pre-flight ────────
    #
    # Lint silence was the phase-C bar. It is not where a phase-D regression
    # would land: `delegate` renders a prompt and the pre-flight scans a spec,
    # and both would break by DOING something extra on a project that asked for
    # none of this. So the property is re-asserted where the behaviour is.

    HOOK = ("# Hook\n\n## High-stakes operations\n\n"
            "- Destructive filesystem operations — `rm -rf`, `rm -f`\n")

    def hooked(self, roles_dir: bool = False) -> Path:
        root = self.project()
        (root / ".perry" / "hook.md").write_text(self.HOOK, encoding="utf-8")
        if roles_dir:
            (root / ".perry" / "roles").mkdir()
        return root

    def state(self, root: Path, section: str) -> dict:
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--section", section], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)[section]

    def test_delegate_has_no_roster_to_render_from(self):
        """`declared: 0` is what sends `delegate` down the unchanged path.
        Not an error, and not a prompt to declare one."""
        for roles_dir in (False, True):
            got = self.state(self.hooked(roles_dir), "roles")
            # `contract` is present even on an empty roster: a consumer checks
        # the version BEFORE it looks at the data, so a payload that carries
        # one only when it has cards is a payload a consumer cannot check.
        self.assertEqual(got, {"contract": "perry-roles/list/1.0",
                               "declared": 0, "cards": []}, roles_dir)

    def test_the_preflight_scans_exactly_the_hook_list_and_nothing_else(self):
        """Not "a superset of" — the SAME LIST, in the same order. A union that
        merely contained the hook's terms could still have grown a term the
        project never declared, and a scan that refuses more than the project
        asked for is its own kind of broken."""
        for roles_dir in (False, True):
            esc = self.state(self.hooked(roles_dir), "project")["escalation"]
            self.assertEqual(esc["union"], esc["project"], roles_dir)
            self.assertEqual(esc["union"], ["rm -rf", "rm -f"], roles_dir)
            self.assertEqual(esc["roles"], {}, roles_dir)
            self.assertEqual({o for v in esc["origins"].values() for o in v},
                             {"hook"}, roles_dir)

    def test_an_empty_roles_directory_changes_no_byte_of_the_payload(self):
        """The two shapes a roleless project comes in — never adopted the layer,
        or created the directory and never filled it — must be indistinguishable
        downstream."""
        def payload(root: Path) -> dict:
            r = subprocess.run(
                [sys.executable, str(STATE), "--root", str(root), "--json"],
                capture_output=True, text=True)
            out = json.loads(r.stdout)
            out.pop("generated_at", None)
            # The temp-dir name, not state. Everything else must match.
            out["project"].pop("root", None)
            out["project"].pop("name", None)
            return out
        self.assertEqual(payload(self.hooked(False)), payload(self.hooked(True)))

    def test_the_consequence_check_is_unmoved(self):
        """`perry-lint --verification` reads the union. On a roleless project
        it must find what it found before the union existed."""
        results = []
        for roles_dir in (False, True):
            root = self.hooked(roles_dir)
            (root / "BOARD.md").write_text(
                "# Board — T\n\n## P0 (must finish this period)\n\n"
                "| ID | Title | Owner | Status | Next action | Evidence | Verification |\n"
                "|---|---|---|---|---|---|---|\n"
                "| T-1 | rm -rf the cache | agent | done | — | `make x` ok | V3 |\n",
                encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(LINT), "--verification", "--root",
                 str(root), "--json"], capture_output=True, text=True)
            results.append(json.loads(r.stdout)["findings"])
        self.assertIn("consequence-needs-signoff",
                      [f["rule"] for f in results[0]])
        self.assertEqual(results[0], results[1])

    def test_delegate_still_documents_the_path_for_a_project_with_no_cards(self):
        """The requirement blocks that used to be the ONLY path are what a
        roleless project still renders from. Deleting them along with the
        hardcoded agent-type list would have quietly changed every prompt on
        every project that declared nothing — which is the regression Goal 7
        names, arriving as a documentation edit rather than a code one."""
        text = (PERRY_HOME / "work" / "reference" / "delegate.md").read_text()
        self.assertIn("Roleless projects", text)
        for owed in ("coding/<task-id>-<slug>", "Do NOT merge own PR",
                     "Hypothesis / data period / universe"):
            self.assertIn(owed, text, owed)

    def test_delegate_no_longer_names_the_three_agent_types(self):
        """The hardcoding this phase closes. They are shipped cards now."""
        text = (PERRY_HOME / "work" / "reference" / "delegate.md").read_text()
        self.assertNotIn("Coding / Research / Review", text)
        self.assertNotIn("Coding/Research/Review", text)
        self.assertNotIn("<agent-type>", text)



class TestTheRolesPayloadIsVersioned(unittest.TestCase):
    """aiMark's round-3 answer to Q2: **yes, we depend on it — version it.**

    A payload a front-end renders and nothing promises is a promise made by
    accident. Six fields were named as what they actually render, and those are
    what `perry-roles/list/1.0` freezes: `declared`, and per card `name`,
    `path`, `accepted_by`, `default_rung`, `must_escalate.fragments` and
    `must_escalate.unextractable`.

    The same report retired `cards[].tasks`: *"dead weight for us. It's
    unversioned and open-rows-only; the reverse edge is under contract and
    covers closed work."* Both halves are true — `tasks[].role` lives in
    `perry-task/list`, carries a promise this never had, and survives a close
    now that `role` travels on the `done` event. Two edges over one fact is the
    defect this repository keeps finding; the one to drop is the one nobody
    reads.
    """

    def payload(self, root):
        import json
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(root), "--json"],
            capture_output=True, text=True, cwd=PERRY_HOME)
        return json.loads(proc.stdout)["roles"]

    def test_the_contract_is_present_before_the_data(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry").mkdir()
            (root / ".perry" / "config.md").write_text("State root: .\n")
            (root / "BOARD.md").write_text("# Board\n")
            self.assertEqual(self.payload(root)["contract"],
                             "perry-roles/list/1.0")

    def test_the_six_frozen_fields_are_all_there(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry" / "roles").mkdir(parents=True)
            (root / ".perry" / "config.md").write_text("State root: .\n")
            (root / "BOARD.md").write_text("# Board\n")
            (root / ".perry" / "roles" / "finance.md").write_text(
                "# Finance\n\n"
                "- Accepted by: the finance lead\n"
                "- Default rung: V5\n\n"
                "## Must escalate\n\n- anything over 10k\n")
            card = self.payload(root)["cards"][0]
            for field in ("name", "path", "accepted_by", "default_rung"):
                self.assertIn(field, card, f"{field} is frozen at 1.0")
            for field in ("fragments", "unextractable"):
                self.assertIn(field, card["must_escalate"])

    def test_the_dead_edge_is_gone(self):
        """Dropped rather than frozen, at its only consumer's request. If it
        comes back, it comes back with a version and a reader."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".perry" / "roles").mkdir(parents=True)
            (root / ".perry" / "config.md").write_text("State root: .\n")
            (root / "BOARD.md").write_text("# Board\n")
            (root / ".perry" / "roles" / "finance.md").write_text(
                "# Finance\n\n- Accepted by: x\n- Default rung: V5\n")
            self.assertNotIn("tasks", self.payload(root)["cards"][0])

if __name__ == "__main__":
    unittest.main()
