"""Contract tests for `claims[]` — the paths Perry occupies in someone else's project.

The claim under test: **there is exactly one authoritative list of what Perry
writes into a project it does not own, and every other consumer reads it.**

This exists because the list used to live in three places that disagreed. The
schema's `files[]` knew 13 paths, `SKILL.md` prose knew 5, `reference/adoption.md`
prose knew the same 5, and the PMO/OKR skills wrote seven directories that
appeared in none of them. A project owning `evidence/` or `knowledge/` therefore
collided silently even on the adopt path, because the collision check was prose
enumerating a subset of a list that was itself incomplete.

`claims[]` answers a different question from `files[]` and the distinction is
what makes two lists correct rather than redundant:

  files[]  — what Perry VALIDATES. A file glob with a template, a cap, a
             heading contract. `journal/<YYYY-MM>/<YYYY-MM-DD>.md`.
  claims[] — what Perry OCCUPIES. The directory a user's own folder collides
             with. `journal/`.

No prefix of that glob is the claim, which is why folding one into the other
does not work. See `perry/design/DESIGN-002-namespace-collision.md`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())
CLAIMS = SCHEMA["claims"]


def covering_claim(path: str, anchor: str) -> dict | None:
    """The claim whose territory contains `path`, or None."""
    for c in CLAIMS:
        if c["anchor"] != anchor:
            continue
        if c["kind"] == "dir" and path.startswith(c["path"]):
            return c
        if c["kind"] == "file" and path == c["path"]:
            return c
    return None


class TestClaimsShape(unittest.TestCase):

    def test_every_claim_is_well_formed(self):
        seen = set()
        for c in CLAIMS:
            for field in ("path", "kind", "owner", "anchor"):
                self.assertIn(field, c, f"claim {c.get('path')!r} missing {field}")
            self.assertIn(c["kind"], ("file", "dir"), c["path"])
            self.assertIn(c["anchor"], ("state", "project"), c["path"])
            self.assertIn(c["owner"], ("perry", "okr", "pmo", "design", "user"), c["path"])
            if c["kind"] == "dir":
                self.assertTrue(c["path"].endswith("/"),
                                f"{c['path']}: dir claims end in / so prefix matching is unambiguous")
            self.assertNotIn(c["path"], seen, f"{c['path']} claimed twice")
            seen.add(c["path"])

    def test_perry_dir_is_the_only_project_anchored_claim(self):
        """`.perry/` holds the State root pointer, so it cannot sit behind it.
        Anything else anchored at the project root would be unmovable too, which
        would make the escape hatch useless for it."""
        project = [c["path"] for c in CLAIMS if c["anchor"] == "project"]
        self.assertEqual(project, [".perry/"])

    def test_no_claim_escapes_the_project(self):
        for c in CLAIMS:
            self.assertFalse(c["path"].startswith("/"), c["path"])
            self.assertNotIn("..", c["path"], c["path"])


class TestClaimsCoverFiles(unittest.TestCase):
    """Every validated file must sit inside claimed territory.

    This is the drift guard. Adding a state file without declaring the ground it
    stands on is how the old prose lists fell behind in the first place."""

    def test_every_schema_file_is_covered(self):
        for spec in SCHEMA["files"]:
            path, anchor = spec["path"], spec.get("anchor", "state")
            with self.subTest(file=path):
                self.assertIsNotNone(
                    covering_claim(path, anchor),
                    f"files[id={spec['id']}] path {path!r} is under no claim — "
                    f"add one to claims[] or the collision check will not see it")

    def test_claim_owner_agrees_with_file_owner(self):
        for spec in SCHEMA["files"]:
            path, anchor = spec["path"], spec.get("anchor", "state")
            claim = covering_claim(path, anchor)
            if claim is None or claim["owner"] == "perry":
                continue
            with self.subTest(file=path):
                self.assertEqual(
                    spec["owner"], claim["owner"],
                    f"{path}: files[] says owner={spec['owner']}, "
                    f"claims[] says {claim['owner']}")


class TestClaimsCoverWhatTheSkillsWrite(unittest.TestCase):
    """The level above: a skill that writes a path no claim covers.

    `files[]` only knows the files Perry validates. The PMO and OKR skills also
    write `journal/`, `evidence/`, `weekly/`, `handoff/`, `knowledge/` and
    `inputs/`, none of which carry a per-file schema — and every one of them can
    collide with a directory the project already owns."""

    # Directories the skills write into that the earlier prose lists missed.
    # Named explicitly rather than scraped, so removing one from claims[] fails
    # here loudly instead of silently narrowing the check.
    UNDECLARED_BEFORE = [
        "journal/", "evidence/", "weekly/", "handoff/",
        "knowledge/", "inputs/", "decisions/",
    ]

    def test_the_seven_missing_directories_are_claimed(self):
        claimed = {c["path"] for c in CLAIMS}
        for d in self.UNDECLARED_BEFORE:
            with self.subTest(dir=d):
                self.assertIn(d, claimed,
                              f"{d} is written by a skill but claimed by nobody")

    def test_state_table_paths_are_claimed(self):
        """Scrape the skills' own `## State files` tables and check each path.

        Catches a new directory added to a skill without a matching claim."""
        # Only the FIRST cell of a row is a project path. Later cells name
        # Perry's own tree (`pmo/state/…_TEMPLATE.md`, `reference/…`), which is
        # source, not territory claimed in someone else's project.
        first_cell = re.compile(r"^\s*\|([^|]+)\|")
        pattern = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*/)[^`]*`")
        misses = []
        for skill in ("pmo/SKILL.md", "okr/SKILL.md", "design/SKILL.md"):
            text = (PERRY_HOME / skill).read_text()
            section = re.search(r"## State files(.*?)(?:\n## |\Z)", text, re.S)
            if not section:
                continue
            for row in section.group(1).splitlines():
                cell = first_cell.match(row)
                if not cell:
                    continue
                for d in set(pattern.findall(cell.group(1))):
                    if covering_claim(d, "state") is None:
                        misses.append(f"{skill}: {d}")
        self.assertEqual(misses, [],
                         "paths in a skill's State files table with no claim: "
                         + ", ".join(misses))


class TestTheCheckIsWiredIn(unittest.TestCase):
    """The check has to run on every entry path, not just the adopt one.

    The original defect was not that the mechanism was missing — `State root:`
    has existed all along. It was that only `/perry adopt` ever asked. A
    greenfield `/perry` in a folder already owning `design/` wrote over it with
    no question asked, because First-time setup asks Document language and Repo
    layout and nothing else."""

    SKILL = (PERRY_HOME / "SKILL.md").read_text()
    ADOPTION = (PERRY_HOME / "reference" / "adoption.md").read_text()

    def setup_section(self) -> str:
        start = self.SKILL.index("## First-time setup")
        return self.SKILL[start:self.SKILL.index("\n## ", start + 10)]

    def test_first_time_setup_runs_the_check(self):
        self.assertIn("--claims", self.setup_section(),
                      "First-time setup does not run the namespace check — the "
                      "greenfield path is unprotected, which is the original bug")

    def test_the_check_precedes_the_question_block(self):
        """Asking the language question first and the state-root question later
        costs a second round trip for no reason."""
        sec = self.setup_section()
        self.assertLess(sec.index("--claims"), sec.index('header `"Language"`'),
                        "the check must run before the AskUserQuestion block so "
                        "State root can ride along as a third question")

    def test_a_clean_folder_costs_no_question(self):
        sec = self.setup_section()
        self.assertRegex(sec, r"collisions: 0.*?ask nothing",
                         "a folder with no collision must not be asked about the "
                         "state root at all")

    def test_state_root_question_is_conditional(self):
        sec = self.setup_section()
        window = sec[sec.index('header `"State root"`'):][:400]
        self.assertIn("only when", window.lower(),
                      "the State root question must be conditional on a collision")

    def test_adopt_still_runs_it_too(self):
        self.assertIn("--claims", self.ADOPTION,
                      "the adopt path lost the check")


class TestNoProseListSurvives(unittest.TestCase):
    """Both prose lists were deleted rather than updated.

    A hand-maintained second copy is what produced the drift; updating it
    reproduces the defect on a delay."""

    PATHS = re.compile(
        r"`(?:OKR\.md|BOARD\.md|phase/|design/|journal/|evidence/|weekly/|handoff/)`")

    # Only where the text is deciding the state root. Ownership prose elsewhere
    # ("pmo is the only writer of BOARD.md, journal/, …") is a statement about
    # who writes what and is not a second copy of the claim list.
    CONTEXT = re.compile(r"already uses a director|directory Perry claims|State root", re.I)

    def test_the_collision_check_does_not_enumerate_paths(self):
        for rel in ("SKILL.md", "reference/adoption.md"):
            lines = (PERRY_HOME / rel).read_text().splitlines()
            for n, line in enumerate(lines, 1):
                if not self.CONTEXT.search(line):
                    continue
                if len(self.PATHS.findall(line)) >= 3:
                    self.fail(
                        f"{rel}:{n} enumerates claimed paths while deciding the "
                        f"state root. Read schema/state-schema.json claims[] "
                        f"instead — a hand-maintained second copy is what "
                        f"drifted.\n  {line.strip()[:140]}")


if __name__ == "__main__":
    unittest.main()
