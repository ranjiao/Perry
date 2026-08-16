"""Contract tests for the hand-off contract — `SKILL.md § The hand-off contract`.

The claim under test: **each lane reads the others' files freely; no lane writes
outside its own.**

`bin/perry-lint` cannot check this. A wrong ownership contract does not produce
a malformed file — it produces a *correctly shaped* file written by the wrong
lane, which looks identical on disk and only shows up later as one lane silently
reverting another's work. That is the entire reason TASK-026 carries a V5 human
gate rather than a script.

What a test file *can* pin is narrower but real: that the declared ownership is
internally consistent across every place Perry states it. The contract is
written down in five places — this router section, each of the three lane
SKILL.md files, and `schema/state-schema.json § files[].owner` — and the failure
mode that has actually happened before (DESIGN-002) is those copies drifting
apart. So this file checks the copies against each other, and checks that every
file Perry writes has exactly one owner.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
ROUTER = (PERRY_HOME / "SKILL.md").read_text()

# Directory on disk → lane name in the contract. The rename (TASK-027) has not
# landed, so the contract states target names and the directories keep the old
# ones; this map is the seam, and it disappears when TASK-027 does.
LANE_DIRS = {"okr": "goals", "pmo": "work", "design": "decide"}


def contract_section() -> str:
    m = re.search(r"^## The hand-off contract.*?(?=^## )", ROUTER, re.M | re.S)
    assert m, "SKILL.md has no `## The hand-off contract` section"
    return m.group(0)


class TestOneOwnerPerFile(unittest.TestCase):
    """Concurrency safety and doc-rot resistance are the same rule."""

    def test_every_schema_file_declares_exactly_one_owner(self):
        for f in SCHEMA["files"]:
            self.assertIn("owner", f, f"{f['id']} declares no owner")
            self.assertIsInstance(f["owner"], str,
                                  f"{f['id']} owner must be a single lane")
            self.assertTrue(f["owner"], f"{f['id']} owner is empty")

    def test_every_claimed_path_declares_exactly_one_owner(self):
        for c in SCHEMA["claims"]:
            self.assertTrue(c.get("owner"), f"{c['path']} claims no owner")

    def test_no_file_is_owned_by_a_lane_that_does_not_exist(self):
        known = set(LANE_DIRS) | set(LANE_DIRS.values()) | {"perry", "user"}
        for f in SCHEMA["files"]:
            self.assertIn(f["owner"], known,
                          f"{f['id']} is owned by unknown lane {f['owner']!r}")
        for c in SCHEMA["claims"]:
            self.assertIn(c["owner"], known,
                          f"{c['path']} is owned by unknown lane {c['owner']!r}")


class TestContractStatesTheInvariant(unittest.TestCase):
    """The sentence the whole contract reduces to must survive every rewrite."""

    def test_the_invariant_sentence_is_present(self):
        s = contract_section().lower()
        self.assertIn("reads the others' files freely", s)
        self.assertIn("no lane writes outside its own", s)

    def test_it_is_declared_a_file_ownership_contract_not_a_registration_one(self):
        """The distinction is what let three skills collapse into one entrance
        without changing how state is written. Losing it invites someone to
        conclude the rule went away with the skill registrations."""
        self.assertIn("file-ownership", contract_section())

    def test_all_three_lanes_appear_with_their_present_tense_directory(self):
        s = contract_section()
        for directory, lane in LANE_DIRS.items():
            self.assertIn(lane, s, f"contract does not name the `{lane}` lane")
            self.assertIn(
                f"{directory}/", s,
                f"contract names `{lane}` without saying it is `{directory}/` "
                f"on disk today — naming a directory that does not exist yet "
                f"is what reference/user-load.md forbids",
            )


class TestTheTwoMovedFiles(unittest.TestCase):
    """DESIGN-003 decisions 5 and 6 move two things. Both must be unambiguous."""

    def test_decisions_are_owned_by_the_decide_lane_in_the_contract(self):
        s = contract_section()
        row = next((l for l in s.split("\n") if "**`decide`**" in l), "")
        self.assertTrue(row, "no `decide` row in the ownership table")
        self.assertIn("DECISIONS.md", row,
                      "decision 6 moves DECISIONS.md to the decide lane")
        self.assertIn("decisions/", row)

    def test_commitments_is_owned_by_the_goals_lane_in_the_contract(self):
        s = contract_section()
        row = next((l for l in s.split("\n") if "**`goals`**" in l), "")
        self.assertTrue(row, "no `goals` row in the ownership table")
        self.assertIn("Commitments", row,
                      "V4 finding B4: the section was written by two modes and "
                      "claimed by no lane")

    def test_commitments_ownership_agrees_with_the_goals_lane_skill(self):
        okr = (PERRY_HOME / "okr" / "SKILL.md").read_text()
        self.assertIn("Commitments", okr,
                      "the lane that owns it must say so in its own SKILL.md, "
                      "or the contract is the only copy and drifts")

    def test_the_mode_files_do_not_claim_to_write_commitments(self):
        for name in ("pipeline", "queue"):
            text = (PERRY_HOME / "modes" / f"{name}.md").read_text()
            if "Commitments" not in text:
                continue
            self.assertTrue(
                re.search(r"\*{0,2}goals\*{0,2}\s+lane", text),
                f"modes/{name}.md uses OKR.md § Commitments without naming the "
                f"goals lane as its writer",
            )


class TestRefusalCasesAreNamed(unittest.TestCase):
    """A contract that says what is owned but not what refusal looks like gets
    read as advice. The three cases below are the ones the DESIGN-003 rename
    actually creates."""

    def test_the_contract_names_concrete_refusal_cases(self):
        s = contract_section()
        self.assertIn("asks in chat and stops", s)
        for case in ("`BOARD.md`", "`DECISIONS.md`", "`journal/`"):
            self.assertIn(case, s, f"refusal case for {case} not named")

    def test_each_lane_skill_still_forbids_writing_outside_itself(self):
        expectations = {
            "okr": "never writes",
            "pmo": "Never write to OKR files",
            "design": "never writes",
        }
        for directory, phrase in expectations.items():
            text = (PERRY_HOME / directory / "SKILL.md").read_text()
            self.assertIn(
                phrase, text,
                f"{directory}/SKILL.md no longer states its own write refusal; "
                f"the router contract must not be the only copy",
            )


class TestDraftStatusIsHonest(unittest.TestCase):
    """While the section is unsigned it must say so.

    Delete this class in the same commit that removes the DRAFT banner after
    V5 sign-off — a test asserting a banner exists is exactly as wrong as the
    banner outliving the signature.
    """

    def test_an_unsigned_contract_is_marked_draft(self):
        s = contract_section()
        signed = "Signed off:" in s
        drafted = "DRAFT" in s and "V5" in s
        self.assertTrue(
            signed or drafted,
            "the contract is neither marked DRAFT nor carries a sign-off line",
        )
        self.assertFalse(
            signed and drafted,
            "the contract claims to be both signed off and a draft",
        )


if __name__ == "__main__":
    unittest.main()
