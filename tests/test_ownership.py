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

    # Every lane-owned path in the schema, mapped to the contract cell that
    # must claim it. Explicit, because the substring heuristic this replaces
    # silently skipped whatever it failed to match.
    SCHEMA_PATH_TO_CONTRACT = {
        "BOARD.md": "BOARD.md",
        "journal/<YYYY-MM>/<YYYY-MM-DD>.md": "journal/",
        "PROJECT_STATE.md": "PROJECT_STATE.md",
        "evidence/<YYYY-MM>/<TASK-ID>-*.md": "evidence/",
        "weekly/<YYYY-WW>.md": "weekly/",
        "handoff/<YYYY-MM-DD>.md": "handoff/",
        "OKR.md": "OKR.md",
        "phase/[0-9][0-9][0-9]-*.md": "phase/<NNN>-<slug>.md",
        "phase/[0-9][0-9][0-9]-linkage.md": "phase/<NNN>-<slug>.md",
        "design/*.md": "design/<DESIGN-ID>-<slug>.md",
        "DECISIONS.md": "DECISIONS.md",
        "decisions/ADR-NNN-<slug>.md": "decisions/",
    }

    # Schema-declared, lane-owned, and NOT named in the signed contract table.
    # Found the moment the check above stopped skipping what it could not
    # match. Left as a recorded gap rather than fixed here: the table carries a
    # V5 signature, and `SKILL.md § The hand-off contract` says an edit that
    # changes an ownership row needs a fresh one. Adding these silently would
    # be forging it.
    NOT_IN_THE_SIGNED_CONTRACT = {
        "runbook/*.md": "schema owner `work`; the table names no runbook cell",
        "knowledge/*/*.md": "schema owner `work`; the table names no knowledge cell",
    }

    def test_the_gap_between_schema_and_contract_does_not_grow(self):
        """Two lane-owned paths are in the schema and not in the signed table.

        This asserts the list is exactly those two. A third would mean a new
        file was given an owner in the schema without the contract being
        updated — which is how the first two got there.
        """
        rows = self.contract_rows()
        actually_absent = set()
        for f in SCHEMA["files"]:
            if f["owner"] in ("perry", "user"):
                continue
            cell = self.SCHEMA_PATH_TO_CONTRACT.get(f["path"])
            if cell and any(cell in owned for owned in rows.values()):
                continue
            actually_absent.add(f["path"])
        self.assertEqual(
            actually_absent, set(self.NOT_IN_THE_SIGNED_CONTRACT),
            "the set of schema-owned files missing from the signed contract "
            "changed. If a file was added, the contract needs a fresh V5 "
            "signature — not a quiet entry in this test.")

    def test_every_schema_file_owner_matches_the_contract(self):
        """The specific failure this catches: schema says one lane, the signed
        contract says another, and nothing notices.

        It did not catch it. `if not claimed_by: continue` silently skipped
        every schema path whose glob failed to substring-match a contract cell
        — measured coverage was **4 of 9** lane-owned files, and the five it
        skipped included `design/*.md`, the decide lane's core file. A round-4
        reviewer reassigned four of them in the schema and all 24 tests in this
        module stayed green. That `DECISIONS.md` had a hardcoded backstop
        immediately below is the pattern exactly: the case a review named got
        patched, the general check stayed one round behind.

        The map above is now explicit, and an unmapped path **fails** rather
        than passing quietly.
        """
        rows = self.contract_rows()
        checked = 0
        for f in SCHEMA["files"]:
            owner = f["owner"]
            if owner in ("perry", "user"):
                continue
            path = f["path"]
            if path in self.NOT_IN_THE_SIGNED_CONTRACT:
                continue
            cell = self.SCHEMA_PATH_TO_CONTRACT.get(path)
            self.assertIsNotNone(
                cell,
                f"schema declares `{path}` owned by `{owner}` and this test "
                f"has no mapping for it — add one, or add it to "
                f"NOT_IN_THE_SIGNED_CONTRACT with a reason. Skipping it "
                f"silently is how five files went unchecked.")
            claimed_by = {lane for lane, owned in rows.items() if cell in owned}
            self.assertTrue(
                claimed_by,
                f"no lane in the signed contract claims `{cell}`")
            self.assertIn(
                owner, claimed_by,
                f"schema says `{path}` is owned by `{owner}`, the signed "
                f"contract assigns it to {claimed_by}",
            )
            checked += 1
        self.assertGreaterEqual(
            checked, 7,
            f"only {checked} lane-owned files were checked; the schema has "
            f"more and they must not fall through")

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
        """The regex used to be anchored to the file bullet — `DECISIONS.md
        (from …)` — so it read one line of the step and was blind to the rest.
        `work/reference/bootstrap.md` refused to create `decisions/` in one
        bullet and then listed it among the directories to create three lines
        below, and this test was green throughout.

        Now it checks the whole step: neither decide-owned path may appear in
        any *creating* instruction, whichever bullet carries it.
        """
        work_bootstrap = (PERRY_HOME / "work" / "reference" / "bootstrap.md").read_text()
        step = re.search(r"^2\.\s+\*\*Create state files.*?(?=^\d+\.\s)",
                         work_bootstrap, re.M | re.S)
        self.assertIsNotNone(step, "bootstrap.md's create-state-files step moved")

        # Read the paths OUT of the instruction rather than scanning the line
        # for a forbidden substring. A first attempt skipped any line
        # containing `**not**` — and the mutation that put `decisions/` back
        # into the create-list left the disclaimer on the same line, so the
        # whole line was skipped and the test stayed green on the bug it names.
        # Everything up to the first em dash is the list; the rest is prose.
        created: list[str] = []
        for line in step.group(0).splitlines():
            body = re.sub(r"^\s*-\s*", "", line).split(" — ")[0]
            if re.match(r"\*\*not\*\*", body.strip()):
                continue  # the bullet that forbids, in full
            created += re.findall(r"`([^`]+)`", body)

        for path in ("DECISIONS.md", "decisions/", "design/"):
            self.assertNotIn(
                path, created,
                f"work's bootstrap creates `{path}`, which the contract gives "
                f"to `decide`. Created here: {created}")

    # Which lane owns what, as a set of paths each OTHER lane must not be
    # instructed to write. Derived from the signed contract table, not restated.
    FOREIGN_WRITES = {
        "goals": ("BOARD.md", "journal/", "evidence/", "weekly/", "handoff/",
                  "DECISIONS.md", "decisions/"),
        "work": ("OKR.md", "phase/", "DECISIONS.md", "decisions/"),
        "decide": ("BOARD.md", "journal/", "OKR.md", "phase/", "evidence/"),
    }

    # Verbs that make a sentence an instruction to write rather than to read.
    WRITE_VERBS = re.compile(
        r"\b(append|write|add a row|tick|update|create|edit|record)\b", re.I)

    def test_no_lane_reference_page_instructs_a_write_it_may_not_perform(self):
        """The reviewers kept finding these, and the tests kept missing them
        because every ownership check scanned `<lane>/SKILL.md` only.

        The stale instructions were all one level down: `goals/reference/
        setup.md` and `pivots.md` told PMO to append a `DECISIONS.md` ADR
        months after those files moved to `decide`; `goals/reference/phases.md`
        wrote into `evidence/`, which `goals/SKILL.md` forbids two files away;
        `decide/reference/decisions.md` step 8 appended to `journal/`, which
        the router names as one of three cases that must refuse.

        `*/reference/*.md` is where procedures actually live. A contract test
        that reads only the summary pages is checking the wrong documents.
        """
        offenders = []
        for lane, forbidden in self.FOREIGN_WRITES.items():
            for page in sorted((PERRY_HOME / lane / "reference").glob("*.md")):
                for n, line in enumerate(page.read_text().splitlines(), 1):
                    if not self.WRITE_VERBS.search(line):
                        continue
                    # A line that forbids, hands off, or narrates history is
                    # the fix, not the defect.
                    if re.search(r"\bnot\b|\bdon'?t\b|\bdoesn'?t\b|never|belong|"
                                 r"hand (it |the |off)|owned by|moved to|refuse|"
                                 r"instead of|used to|for a release|read(s)? ",
                                 line, re.I):
                        continue
                    # Match any backticked span that STARTS with the forbidden
                    # path, not the bare path alone. The first version compared
                    # `f"`{path}`" in line`, so it saw `` `evidence/` `` and
                    # missed `` `evidence/<YYYY-MM>/retro.md` `` — which is how
                    # every one of these is actually written. Proved by
                    # mutation: restoring the real defect left the test green.
                    for span in re.findall(r"`([^`]+)`", line):
                        for path in forbidden:
                            if span == path or span.startswith(path):
                                offenders.append(
                                    f"{lane}/reference/{page.name}:{n} → writes "
                                    f"`{span}`\n      {line.strip()[:110]}")
                                break
        self.assertFalse(
            offenders,
            "a lane's reference page instructs a write the signed contract "
            "forbids:\n    " + "\n    ".join(offenders))

    def test_no_other_lane_claims_the_moved_files_in_its_own_prose(self):
        """Every lane SKILL.md states the contract in its own words, and
        `goals/SKILL.md` kept the pre-move sentence — "PMO is the only writer
        of … `DECISIONS.md` …" — long after the move.

        This module's docstring says the contract is written in five places and
        that copies drifting apart is the failure that has actually happened.
        The existing tests checked the router table, the schema and `decide/`.
        The prose copies in the *other two lanes* were the unchecked pair, and
        that is where the stale claim was.
        """
        for lane in ("goals", "work"):
            text = (PERRY_HOME / lane / "SKILL.md").read_text()
            self.assertIn("only writer of", text,
                          f"{lane}/SKILL.md no longer states the contract at "
                          f"all — this test would pass vacuously")
            # Capture the LIST, not a span of characters. Two earlier attempts
            # failed for opposite reasons: `[^.]*` stopped inside "`BOARD.md`"
            # because every path here contains a dot, and end-of-line ran past
            # several claims into the sentence that corrects them. The list is
            # backticked items joined by commas and "and", and it ends at the
            # first token that is neither — which is exactly what this matches.
            claims = re.findall(r"only writer of ((?:\s*(?:and|,)?\s*`[^`]+`)+)",
                                text)
            self.assertTrue(claims, f"{lane}/SKILL.md: no claim list parsed")
            for claim in claims:
                for path in ("DECISIONS.md", "decisions/"):
                    self.assertNotIn(
                        path, claim,
                        f"{lane}/SKILL.md still claims `{path}`, which moved to "
                        f"`decide` on 2026-08-16:\n  …only writer of{claim}")
