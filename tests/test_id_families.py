"""TASK-158 — a project's own id families, and the checks that read them.

The claim under test: **a project that declares its own id family gets the
same treatment Perry's own families get, and no tool was taught its name.**

The row said "the citation families are hardcoded in the tool, so a project
with its own id family gets noise on every legitimate citation" and did not say
which tool. The symptom found it. On a project whose decisions are `DEC-014`
and whose specs are `SPEC-007` — both real documents, both resolved by
`perry-explain`, neither reported by `perry-diagnose` — every write through
`perry-task` that cited either one printed:

    ⚠ --next contains DEC-014, SPEC-007, which reads as an id and names
      nothing. `perry-diagnose` reports it as dangling.

Both halves of that sentence were false, and the second one names a tool the
user can run to see that it is false. `bin/perry-task §
idish_tokens_that_resolve_nowhere` was asking whether the family was one of
**Perry's** six, which is a question about Perry and not about the project.

So the fixtures below are projects, built through the real `--root` seam, and
the assertions are about what a tool prints when run against them. Nothing here
reads the repository it is sitting in: a test whose expected value is Perry's
own board would go red the day Perry adopted a fifth family, and would have
stayed green through the entire defect.

Run: python3 tests/parallel test_id_families
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
import lib  # noqa: E402

TASK = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"
EXPLAIN = PERRY_HOME / "bin" / "perry-explain"
DIAGNOSE = PERRY_HOME / "bin" / "perry-diagnose"

#: The families this module's fixture project uses. **Written in two pieces
#: nowhere** — they are meant to be spelled out, because the whole assertion is
#: that no tool contains these letters. `test_no_tool_was_taught_these_names`
#: greps `bin/` for them, and this module lives under `tests/`, which
#: `perry-explain § is_illustrative` already excludes from the id scan, so
#: naming them here adds nothing to Perry's own dangling report.
FOREIGN_DECISION = "DEC-014"
FOREIGN_SPEC = "SPEC-007"
FOREIGN_TASK = "PLAT-001"

BOARD = f"""# Board — Platform team

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| {FOREIGN_TASK} | Ship the ingest rewrite | Coding Agent | open | land the parser | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## Cadence (recurring; doesn't consume P0 slots)

| ID | Recurring task | Owner | Frequency | Next due | Last evidence |
|---|---|---|---|---|---|

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|

## Top risks

- none
"""


class Project:
    """A throwaway project whose ids are a family Perry never heard of.

    `foreign=False` builds the same project with the id-named documents left
    out, which is the control: the tokens are then citations of nothing and
    must still be warned about.
    """

    def __init__(self, foreign: bool = True):
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n"
            "- Conformance gate: advisory\n", encoding="utf-8")
        (self.root / "BOARD.md").write_text(BOARD, encoding="utf-8")
        if foreign:
            (self.root / "decisions").mkdir()
            (self.root / "decisions" / f"{FOREIGN_DECISION}-ingest-format.md"
             ).write_text(
                f"# {FOREIGN_DECISION} — the ingest format is "
                "newline-delimited JSON\n\n- Status: accepted\n"
                "- Date: 2026-08-01\n\nThe ingest format is NDJSON.\n",
                encoding="utf-8")
            (self.root / "design").mkdir()
            (self.root / "design" / f"{FOREIGN_SPEC}-parser.md").write_text(
                f"# {FOREIGN_SPEC} — parser topology\n\n"
                "The parser is a two-stage pipeline.\n", encoding="utf-8")
        self._run(TASKS, "write", "--from-board")

    def cleanup(self) -> None:
        self._dir.cleanup()

    def _run(self, tool: Path, *argv) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(tool), *argv, "--root", str(self.root)],
            capture_output=True, text=True, check=False)

    def write_next(self, prose: str) -> str:
        """`perry-task next` with `prose`, returning only its own warnings.

        The conformance advisory and the write line are filtered out: this
        module is about one warning, and a fixture that trips a second one
        should not be able to make an assertion about the first pass or fail.
        """
        r = self._run(TASK, "next", FOREIGN_TASK, "--next", prose)
        assert r.returncode == 0, r.stdout + r.stderr
        return "\n".join(l for l in r.stderr.split("\n")
                         if l.startswith("perry-task: ⚠ --"))

    def dangling(self) -> list[str]:
        r = self._run(DIAGNOSE, "--json")
        return (json.loads(r.stdout).get("user_load") or {}).get("dangling")

    def explains(self, token: str) -> bool:
        return self._run(EXPLAIN, token).returncode == 0


class TestALegitimateCitationIsQuiet(unittest.TestCase):
    """The reproduction, and the fix, on a project built for the purpose."""

    @classmethod
    def setUpClass(cls):
        cls.project = Project()
        cls.addClassCleanup(cls.project.cleanup)

    def test_the_project_really_does_define_these_ids(self):
        """The premise, asserted before anything is asserted about noise.

        If `perry-explain` could not resolve these either, the warning would
        have been *true* and this module would be pinning a defect in place.
        `perry-diagnose` is asked the same question a second way, because it is
        the tool the warning names.

        On its OWN copy of the fixture, untouched by any write. The class
        fixture is shared, and `perry-task next` puts whatever it was handed
        into the board — so a sibling test's `ROUND-3` becomes a dangling id in
        the project this one is measuring, and the premise fails for a reason
        that has nothing to do with the premise.
        """
        project = Project()
        self.addCleanup(project.cleanup)
        for token in (FOREIGN_DECISION, FOREIGN_SPEC):
            self.assertTrue(
                project.explains(token),
                f"{token} is not resolvable by `perry-explain` in this "
                "fixture — the fixture, not the tool, is what is broken")
        self.assertEqual(
            project.dangling(), [],
            "`perry-diagnose` reports an id in this fixture as dangling, so "
            "the write-site warning about it would be TRUE and this module "
            "would be asserting the wrong thing")

    def test_citing_the_projects_own_families_prints_nothing(self):
        """The row's symptom. Every legitimate citation used to print.

        Both families in one cell, because both were in the one warning the
        reproduction produced, and a fix that learned one family from the board
        and missed the other would pass a single-token assertion.
        """
        self.assertEqual(
            self.project.write_next(
                f"land the parser per {FOREIGN_SPEC}, "
                f"format fixed by {FOREIGN_DECISION}"), "",
            "a citation of an id this project defines was warned about — the "
            "advisory is back to asking whether the family is one of PERRY's")

    def test_prose_shaped_like_an_id_is_still_warned_about(self):
        """The half that must not be lost, on the same project.

        This is what the check is FOR: `ALL FIVE ROUND-3 FINDINGS` is English
        to its author and an identifier to every id reader here. A fix that
        widened the known set until nothing was ever warned about would pass
        the test above and delete the feature.
        """
        warning = self.project.write_next("fix ALL FIVE ROUND-3 FINDINGS")
        self.assertIn("ROUND-3", warning,
                      "id-shaped prose stopped being warned about")

    def test_an_undefined_token_of_a_declared_family_is_still_warned(self):
        """Not so wide that a family name buys the whole family silence.

        `ROUND` is the family, `ROUND-3` the token, and the check works at the
        family level on purpose — `ADR-006` is a legitimate citation on a
        project whose first ADR is not written yet. What must not happen is the
        opposite mistake: a project's `decisions/` making every capitalised
        word citable. `LOAD-02` is the finding code from the defect that
        produced this check, and it is not a family this project declares.
        """
        self.assertIn("LOAD-02", self.project.write_next(
            "reproduce LOAD-02 before touching it"))


class TestTheControlProject(unittest.TestCase):
    """The same tokens, on a project that does NOT define them.

    Without this, `test_citing_the_projects_own_families_prints_nothing` is
    satisfied by a tool that stopped warning about everything.
    """

    @classmethod
    def setUpClass(cls):
        cls.project = Project(foreign=False)
        cls.addClassCleanup(cls.project.cleanup)

    def test_the_same_citation_is_warned_about_when_nothing_defines_it(self):
        warning = self.project.write_next(
            f"land the parser per {FOREIGN_SPEC}, "
            f"format fixed by {FOREIGN_DECISION}")
        for token in (FOREIGN_DECISION, FOREIGN_SPEC):
            self.assertIn(
                token, warning,
                f"{token} names nothing on this project and was not warned "
                "about — the advisory has stopped firing rather than started "
                "reading the project")

    def test_perrys_own_families_are_known_before_any_file_declares_them(self):
        """The floor, and why it is a floor rather than the answer.

        A project that has not written its first ADR still cites `ADR-006`
        legitimately — `schema/task-list-contract.md` says outright that
        `DESIGN-`, `ADR-` and `USER-` ids appear in these cells constantly. So
        Perry's six are known with no evidence of them on disk, and this
        fixture has none: no `decisions/`, no `design/`, no queue row.
        """
        self.assertEqual(
            self.project.write_next(
                "see ADR-006 and USER-014, per DESIGN-002"), "",
            "a family Perry itself mints was warned about on a project that "
            "has not written one yet")


class TestTheFamiliesAreReadFromOnePlace(unittest.TestCase):
    """The unification half of the row: one spelling, not four."""

    #: Every Python file under `bin/`. `rglob`, so `bin/lib/` is included —
    #: it is the implementation and the only place these letters belong.
    TOOLS = sorted(p for p in (PERRY_HOME / "bin").rglob("*")
                   if p.is_file() and (p.suffix == ".py" or (
                       not p.suffix
                       and "python" in p.read_text(errors="replace")
                       .split("\n", 1)[0])))

    #: The alternation that was written out in `bin/perry-lint` and
    #: `bin/perry-diagnose`, byte for byte, answering one question in two
    #: files. Matched as a REGEX FRAGMENT rather than as a word list, so a
    #: reordered or re-spelled copy is caught too.
    FAMILY_ALTERNATION = re.compile(
        r"\((?:DESIGN|ADR|TASK|USER)(?:\|(?:DESIGN|ADR|TASK|USER)){3}\)-")

    def test_the_filename_predicate_is_spelled_once(self):
        """`would Perry have written this file` had two implementations.

        `bin/perry-lint § looks_like_perry_state` and `bin/perry-diagnose §
        _perry_shaped` are the same predicate with the same list in it, and a
        project adopting Perry meets both. Asked as "does any tool contain the
        alternation", never as "do these two files", so the next copy is
        caught wherever it is written.
        """
        offenders = [str(p.relative_to(PERRY_HOME)) for p in self.TOOLS
                     if p.parent.name != "lib"
                     and self.FAMILY_ALTERNATION.search(
                         p.read_text(errors="replace"))]
        self.assertEqual(
            offenders, [],
            "these files spell Perry's artifact families out again instead of "
            "reading `bin/lib § PERRY_ARTIFACT_FAMILIES`")

    def test_the_scan_would_catch_the_copy_it_replaced(self):
        """The guard above, proved to fire. A grep that matches nothing is
        indistinguishable from a grep that is broken."""
        for spelling in (r'r"^(DESIGN|ADR|TASK|USER)-\d"',
                         r'r"^(USER|TASK|ADR|DESIGN)-\d"'):
            self.assertTrue(self.FAMILY_ALTERNATION.search(spelling),
                            f"the scan does not see {spelling}")

    def test_both_predicates_still_answer_exactly_as_they_did(self):
        """The move changed no verdict. Perry's three standing `NS-01`
        warnings are files of its own this correctly does NOT claim, and a
        widening would have silenced them — which is how a de-duplication
        turns into a behaviour change nobody reviewed."""
        was = re.compile(r"^(DESIGN|ADR|TASK|USER)-\d")
        for stem in ("ADR-002-single-region", "DESIGN-001-x", "TASK-158-spec",
                     "USER-014", "DEC-014-ingest-format", "SPEC-007-parser",
                     "2026-08-28-a-kr-with-no-open-task", "README", "001-x",
                     "TASKS-1", "ADRs-2", "adr-002", "SRC-1-notes"):
            self.assertEqual(
                lib.perry_named_artifact(stem), bool(was.match(stem)),
                f"`perry_named_artifact` disagrees with the expression it "
                f"replaced on {stem!r}")

    def test_no_tool_was_taught_this_projects_families(self):
        """"Without the tool being taught that family by name" — measured.

        The cheap way to make the fixture above pass is to add `DEC` and
        `SPEC` to a set somewhere, which would fix this project and no other.
        """
        for family in ("DEC", "SPEC", "PLAT"):
            hits = [str(p.relative_to(PERRY_HOME)) for p in self.TOOLS
                    if re.search(rf'["\']{family}["\']',
                                 p.read_text(errors="replace"))]
            self.assertEqual(hits, [], f"a tool names {family!r}")

    def test_the_citation_floor_and_the_filename_list_stay_distinct(self):
        """Two names because they answer two questions.

        `SRC` and `KR` are citable and never filenames; collapsing the pair
        into one constant would make `SRC-1-notes.md` read as a file Perry
        wrote, which is the collision `NS-01` exists to report.
        """
        self.assertEqual(
            set(lib.PERRY_ARTIFACT_FAMILIES) & {"SRC", "KR"}, set(),
            "a family that is never a filename got into the filename list")
        self.assertTrue(
            {"SRC", "KR"} <= lib.PERRY_CITATION_FAMILIES,
            "a family Perry mints ids in stopped being citable")


class TestDeclaredIdFamilies(unittest.TestCase):
    """`bin/lib § declared_id_families` — the derivation itself."""

    def test_it_reads_the_families_off_the_project(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "decisions").mkdir()
            (root / "decisions" / f"{FOREIGN_DECISION}-x.md").touch()
            (root / "design").mkdir()
            (root / "design" / f"{FOREIGN_SPEC}-y.md").touch()
            (root / "notes.md").touch()
            (root / "README.md").touch()
            self.assertEqual(lib.declared_id_families(root),
                             {"DEC", "SPEC"})

    def test_it_does_not_descend_into_another_project(self):
        """A vendored checkout or an agent worktree is a different project,
        and its families are not this one's. Same rule the id resolver walks
        by, because it is now literally the same walk."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("node_modules", "worktree"):
                (root / name).mkdir()
                (root / name / "OTHER-001-x.md").touch()
            (root / "worktree" / ".git").mkdir()
            self.assertEqual(lib.declared_id_families(root), set())

    def test_a_filename_that_is_not_an_id_declares_no_family(self):
        for stem in ("2026-08-28-retro", "README", "001-linkage",
                     "notes", "adr-002-lowercase"):
            self.assertIsNone(lib.id_family(stem),
                              f"{stem!r} was read as declaring a family")


if __name__ == "__main__":
    unittest.main()
