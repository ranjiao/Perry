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

# Directory on disk → lane name in the contract. TASK-027 landed the rename, so
# the two are now the same string; the map is kept (rather than collapsed to a
# list) because it is what a future rename would edit, and because
# `test_all_three_lanes_appear_with_their_present_tense_directory` still checks
# that the contract names a directory that actually exists.
LANE_DIRS = {"goals": "goals", "work": "work", "decide": "decide"}


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
        okr = (PERRY_HOME / "goals" / "SKILL.md").read_text()
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
            "goals": "never writes",
            "work": "Never write to OKR files",
            "decide": "never writes",
        }
        for directory, phrase in expectations.items():
            text = (PERRY_HOME / directory / "SKILL.md").read_text()
            self.assertIn(
                phrase, text,
                f"{directory}/SKILL.md no longer states its own write refusal; "
                f"the router contract must not be the only copy",
            )


class TestDraftStatusIsHonest(unittest.TestCase):
    """The contract must be exactly one of: marked DRAFT, or signed off.

    Written to guard the unsigned state and it now guards the signed one, which
    is why it survived the signature rather than being deleted with the banner.
    The failure it prevents in both directions is the same: a section whose
    stated status has drifted from its real one.
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


class TestLaneAliases(unittest.TestCase):
    """Renaming the lanes must cost an existing user nothing.

    DESIGN-003 decision 5 chose the rename *with* permanent aliases precisely so
    the rename would be free at the command line. A user who typed
    `/perry pmo triage` yesterday must still be routed correctly today, and the
    router is prose — so what is testable is that the router documents every
    alias, and that no alias silently points at a lane directory that no longer
    exists.
    """

    ALIASES = {"okr": "goals", "pmo": "work", "design": "decide"}

    def test_every_alias_is_documented_in_the_router(self):
        s = ROUTER
        for old, new in self.ALIASES.items():
            self.assertRegex(
                s, rf"alias(es)?[^\n]*`?{old}`?",
                f"the router never tells the reader that `{old}` still works",
            )
            self.assertIn(f"`{new}`", s)

    def test_the_command_surface_shows_the_alias_map(self):
        m = re.search(r"### Command surface\s*```(.*?)```", ROUTER, re.S)
        self.assertTrue(m, "no Command surface block")
        block = m.group(1)
        for old, new in self.ALIASES.items():
            self.assertIn(f"{old} → {new}", block,
                          f"alias {old} → {new} not shown where users look")

    def test_every_lane_directory_named_by_the_router_exists(self):
        """The failure this catches is the rename half-landing: the router
        pointing at `$PERRY_HOME/<lane>/SKILL.md` for a directory that was moved
        out from under it."""
        for path in set(re.findall(r"\$PERRY_HOME/(\w+)/SKILL\.md", ROUTER)):
            self.assertTrue(
                (PERRY_HOME / path / "SKILL.md").exists(),
                f"router loads $PERRY_HOME/{path}/SKILL.md, which does not exist",
            )

    def test_no_alias_is_also_a_live_directory(self):
        """If `okr/` still existed alongside `goals/`, the alias would be
        ambiguous and the rename would have left two sources of truth."""
        for old in self.ALIASES:
            self.assertFalse(
                (PERRY_HOME / old / "SKILL.md").exists(),
                f"`{old}/SKILL.md` still exists after the rename — the alias "
                f"now has two possible targets",
            )

    def test_the_legacy_installer_cleanup_is_not_derived_from_current_dirs(self):
        """A cleanup routine that reads current state cannot remove what current
        state forgot: deriving the stale-symlink list from `$PERRY_HOME/*/`
        would look for links named `goals`/`work`/`decide`, which no installer
        ever created, and would never find an upgrading user's real leftovers."""
        setup = (PERRY_HOME / "setup").read_text()
        m = re.search(r"PERRY_LEGACY_CHILDREN=\(([^)]*)\)", setup)
        self.assertTrue(m, "setup no longer declares an explicit legacy list")
        self.assertEqual(setup.count("PERRY_LEGACY_CHILDREN=("), 1,
                         "the legacy list is declared more than once — a two-copy "
                         "invariant with nothing checking the copies agree")
        names = m.group(1).split()
        for old in self.ALIASES:
            self.assertIn(old, names,
                          f"`{old}` would never be cleaned off an upgrading "
                          f"user's machine")


class TestSchemaAgreesWithTheSignedContract(unittest.TestCase):
    """The check the V5 signature block claims exists.

    The signed note under `SKILL.md § The hand-off contract` says
    `tests/test_ownership.py` covers the schema/contract agreement mechanically.
    It did not: the suite asserted only that every file has exactly one owner
    and that the owner is a known lane. Both held while the schema said
    `DECISIONS.md` belonged to `work` and the contract said `decide` — a
    contract violation stayed green through 268 passing tests, and the
    signature cited a check that was not being performed.

    That is worse than the violation. A V5 note is a record of what was
    verified; if it names a check that does not run, the rung is decoration and
    the user signed something on a false premise. This class is what makes the
    sentence true. Found by the fourth independent review, finding 6.
    """

    # Every file the contract table assigns, parsed from the contract itself so
    # the table and this list cannot drift apart silently.
    def contract_rows(self) -> dict[str, set[str]]:
        rows: dict[str, set[str]] = {}
        for line in contract_section().split("\n"):
            m = re.match(r"\|\s*\*\*`(\w+)`\*\*[^|]*\|([^|]*)\|", line)
            if m:
                lane, owned = m.group(1), m.group(2)
                rows[lane] = set(re.findall(r"`([^`]+)`", owned))
        return rows

    def test_the_contract_table_parses(self):
        rows = self.contract_rows()
        self.assertEqual(set(rows), {"goals", "work", "decide"},
                         "the ownership table no longer has three lane rows")

    def test_every_schema_file_owner_matches_the_contract(self):
        """The specific failure this catches: schema says one lane, the signed
        contract says another, and nothing notices."""
        rows = self.contract_rows()
        for f in SCHEMA["files"]:
            owner = f["owner"]
            if owner in ("perry", "user"):
                continue
            path = f["path"]
            claimed_by = {lane for lane, owned in rows.items()
                          if any(path.startswith(o.rstrip("*/")) or o.rstrip("*/") in path
                                 for o in owned)}
            if not claimed_by:
                continue  # not named in the contract table; other tests cover it
            self.assertIn(
                owner, claimed_by,
                f"schema says `{path}` is owned by `{owner}`, the signed "
                f"contract assigns it to {claimed_by}",
            )

    def test_decisions_specifically_is_owned_by_decide_everywhere(self):
        """The file the contract moved, checked in every place it is declared —
        this is the one that was green while broken."""
        f = next(x for x in SCHEMA["files"] if x["id"] == "decisions")
        self.assertEqual(f["owner"], "decide")
        for path in ("DECISIONS.md", "decisions/"):
            c = next(x for x in SCHEMA["claims"] if x["path"] == path)
            self.assertEqual(c["owner"], "decide", f"claims[] still gives {path} to {c['owner']}")
        self.assertIn("DECISIONS.md", self.contract_rows()["decide"])

    def test_a_moved_files_template_moves_with_it(self):
        """`decide/reference/decisions.md` sourced templates from `work/state/`
        after the move — a lane reaching into another lane's tree."""
        f = next(x for x in SCHEMA["files"] if x["id"] == "decisions")
        tmpl = f.get("template", "")
        self.assertTrue(tmpl.startswith("decide/"), f"template still at {tmpl}")
        self.assertTrue((PERRY_HOME / tmpl).exists(), f"{tmpl} does not exist")

    def test_only_one_lane_bootstraps_the_decision_files(self):
        work_bootstrap = (PERRY_HOME / "work" / "reference" / "bootstrap.md").read_text()
        self.assertNotRegex(
            work_bootstrap, r"^\s*-\s+`DECISIONS\.md` \(from",
            "the work lane still bootstraps DECISIONS.md, and so does decide — "
            "two lanes creating one pair of files is the state the contract ends",
        )
