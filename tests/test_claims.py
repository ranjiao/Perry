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
import sys
import subprocess
import pathlib
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
            self.assertIn(c["owner"], ("perry", "goals", "work", "decide", "user"), c["path"])
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
        # Perry's own tree (`work/state/…_TEMPLATE.md`, `reference/…`), which is
        # source, not territory claimed in someone else's project.
        first_cell = re.compile(r"^\s*\|([^|]+)\|")
        pattern = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*/)[^`]*`")
        misses = []
        for skill in ("work/SKILL.md", "goals/SKILL.md", "decide/SKILL.md"):
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


class TestRemediesExist(unittest.TestCase):
    """A finding that recommends a command must recommend a real one.

    `NS-01` tells the user to run `/perry relocate`. Decision #2 was taken
    strictly — no per-path `Ignore:` — so relocation is one of only two
    remedies, which is what promoted it from convenience to requirement."""

    SKILL = (PERRY_HOME / "SKILL.md").read_text()
    DIAGNOSE = (PERRY_HOME / "reference" / "diagnose.md").read_text()

    def test_ns01_is_in_the_catalog(self):
        """The catalog is the lookup for a stable ID. One without an entry is a
        worse experience than prose."""
        self.assertRegex(self.DIAGNOSE, r"\| `NS-01` \| warn \|")

    def test_ns01_is_a_warning_not_an_error(self):
        """A user may knowingly keep one file in a claimed folder. A permanent
        red for a deliberate choice is how a check trains its user to skip it."""
        row = next(l for l in self.DIAGNOSE.splitlines() if l.startswith("| `NS-01`"))
        self.assertIn("| warn |", row)

    def test_relocate_is_documented(self):
        self.assertIn("## `/perry relocate", self.SKILL,
                      "NS-01 recommends a command that does not exist")

    def test_relocate_is_in_the_command_surface(self):
        surface = self.SKILL[self.SKILL.index("### Command surface"):][:600]
        self.assertIn("relocate", surface)

    def test_relocate_refuses_a_dirty_tree(self):
        sec = self.SKILL[self.SKILL.index("## `/perry relocate"):][:2600]
        self.assertIn("dirty tree", sec,
                      "the git mv set is the only thing making this reversible")

    def test_relocate_computes_moves_from_claims(self):
        sec = self.SKILL[self.SKILL.index("## `/perry relocate"):][:2600]
        self.assertIn("claims[]", sec,
                      "a hand-written path list here reproduces the drift this "
                      "whole design exists to close")


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


class TestNoTestFileEndsEarly(unittest.TestCase):
    """`tests/test_work_modes.py` had `unittest.main()` two thirds of the way
    down. `python3 -m unittest discover` imported the module and saw all 78
    tests, but running the file directly — the natural thing to do while
    iterating on it — executed main() before the remaining classes were
    defined, ran 48, and printed **OK**.

    A green result over a silently truncated set is the worst thing a suite
    can report: success for work it never looked at. Found as m-9 in the V4
    review of TASK-019/020, and `test_task_writer.py` still carries a comment
    from the first time the same defect was fixed there — which is why this
    is a guard and not a one-line move.
    """

    DRIVER = """
import os, runpy, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))
ns = {}
seen = {}
def count():
    seen["at_entry"] = len([v for v in ns.values()
        if isinstance(v, type) and issubclass(v, unittest.TestCase)])
    raise SystemExit
unittest.main = count
try:
    ns.update(runpy.run_path(sys.argv[1], run_name="__main__"))
except SystemExit:
    pass
total = len([v for v in ns.values()
    if isinstance(v, type) and issubclass(v, unittest.TestCase)])
print(seen.get("at_entry", total), total)
"""

    def files(self):
        here = pathlib.Path(__file__).parent
        return [f for f in sorted(here.glob("test_*.py"))
                if "unittest.main()" in f.read_text()]

    def test_the_entry_point_is_the_last_statement_in_every_test_file(self):
        for f in self.files():
            tail = f.read_text().rstrip().split("\n")[-2:]
            self.assertEqual(
                ['if __name__ == "__main__":', "    unittest.main()"], tail,
                f"{f.name}: unittest.main() is not the last statement, so "
                f"running the file directly skips everything after it")

    def test_every_class_is_defined_before_the_entry_point_runs(self):
        """The guard above is structural — it checks where the block sits.
        This checks the consequence: how many TestCases exist at the moment
        `unittest.main()` is reached. A file could satisfy the first and still
        truncate, by carrying a second `main()` higher up.

        It does not run the suites. Running them to count them took 80s, which
        would make the cheapest guard in the repo the slowest; the driver
        replaces `unittest.main` with a counter, so nothing past import runs.
        """
        for f in self.files():
            r = subprocess.run(
                [sys.executable, "-c", self.DRIVER, str(f)],
                capture_output=True, text=True, cwd=f.parent.parent)
            self.assertEqual(0, r.returncode, r.stderr[-800:])
            at_entry, total = r.stdout.split()
            self.assertEqual(
                total, at_entry,
                f"{f.name}: the file defines {total} TestCase classes but only "
                f"{at_entry} existed when unittest.main() ran — running the "
                f"file directly skips the rest and still reports OK")


class TestEveryToolResolvesTheStateRoot(unittest.TestCase):
    """No tool may reach for the project root to find a state file.

    `bin/perry-goals` shipped passing `project_root` to `load_snapshot`, which
    takes the **state** root and reads `root / "OKR.md"` directly. On every
    project whose state root is not `.` it read the wrong directory and
    reported `okr_present: false` inside a payload that looked entirely
    well-formed — Perry and aiMark both keep state under `perry/`, and both
    were reported as having no goals.

    Two shapes in circulation is two code paths a reader can disagree about.
    The fix is not to remove the option — `gimegime-pmo` is a PMO repo whose
    whole purpose is Perry state and nesting it would be redundant — but to
    make one function the only way to find it.
    """

    STATE_FILES = ("BOARD.md", "OKR.md", "DECISIONS.md", "PROJECT_STATE.md")
    TOOLS = ("perry-task", "perry-goals", "perry-decide", "perry-state")

    def test_no_tool_joins_a_state_file_onto_the_project_root(self):
        offenders = []
        for name in self.TOOLS:
            src = (PERRY_HOME / "bin" / name).read_text()
            for n, line in enumerate(src.splitlines(), 1):
                if line.lstrip().startswith("#") or "resolve_state_root" in line:
                    continue
                for f in self.STATE_FILES:
                    if re.search(rf'project_root\s*/\s*["\']{re.escape(f)}', line):
                        offenders.append(f"bin/{name}:{n}  {line.strip()[:80]}")
        self.assertFalse(
            offenders,
            "a tool built a state-file path from the project root instead of "
            "the state root:\n    " + "\n    ".join(offenders))

    def test_no_tool_passes_the_project_root_to_load_snapshot(self):
        """The exact form the bug took. `load_snapshot` takes the state root;
        the name does not say so, which is what made it easy to get wrong."""
        offenders = []
        for name in self.TOOLS:
            src = (PERRY_HOME / "bin" / name).read_text()
            for n, line in enumerate(src.splitlines(), 1):
                if "load_snapshot(" in line and "project_root" in line:
                    offenders.append(f"bin/{name}:{n}  {line.strip()[:80]}")
        self.assertFalse(
            offenders,
            "load_snapshot takes the STATE root:\n    " + "\n    ".join(offenders))

    def test_every_tool_actually_calls_the_resolver(self):
        """A tool that never resolves cannot honour a declared state root at
        all — the failure this pair exists to prevent, one step earlier."""
        for name in self.TOOLS:
            src = (PERRY_HOME / "bin" / name).read_text()
            self.assertIn("resolve_state_root", src,
                          f"bin/{name} never resolves the state root")


class TestEveryDeclaredSubcommandHasAProcedure(unittest.TestCase):
    """`goals/SKILL.md` listed `commit <promise>` with a paragraph of behaviour
    and pointed at `reference/phases.md`, which had never heard of it. A user
    who typed it got whatever the agent invented on the spot, and two users got
    two different things.

    Same defect class as the router naming three directories that did not
    exist (TASK-027 round 3) and `subcommands.md` citing a restatement
    `autopilot.md` does not contain (m-10). The index is a promise that a
    procedure exists somewhere; nothing checked that it did.

    Found as M-7 in the V4 review of TASK-019/020.
    """

    ROOT = pathlib.Path(__file__).resolve().parent.parent
    LANES = ("goals", "work", "decide")

    def rows(self, lane):
        """The index table, and only it.

        A lane SKILL.md holds several tables that look alike — `decide` also
        has one listing state files, whose rows would parse as subcommands
        pointing at templates. The index is identified by the row every lane
        has and no other table does: `help`. Take the contiguous block of
        table lines containing it.
        """
        lines = (self.ROOT / lane / "SKILL.md").read_text().split("\n")
        blocks, cur = [], []
        for line in lines:
            if line.startswith("|"):
                cur.append(line)
            else:
                if cur:
                    blocks.append(cur)
                cur = []
        if cur:
            blocks.append(cur)
        index = [b for b in blocks
                 if any(re.match(r"^\|\s*`help[ `]", l) for l in b)]
        self.assertEqual(1, len(index),
                         f"{lane}/SKILL.md: could not identify the index table")
        out = []
        for line in index[0]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            m = re.match(r"^`([a-z][a-z-]*)[^`]*`$", cells[0])
            if m:
                out.append((m.group(1), cells[-1].strip("`")))
        return out

    def resolve(self, lane, cell):
        """Every file a reference cell names. `Subcommands` and
        `(handled here)` mean the lane's own SKILL.md — the reference is a
        section, not a file. A cell may name more than one file
        (`` `subcommands.md` + `reporting-format.md` ``); all must exist, and
        the procedure has to be in one of them."""
        out = []
        for ref in re.split(r"[+,]", cell):
            ref = ref.strip().strip("`").strip()
            if not ref.endswith(".md"):
                out.append(self.ROOT / lane / "SKILL.md")
            elif ref.startswith("$PERRY_HOME/"):
                out.append(self.ROOT / ref[len("$PERRY_HOME/"):])
            else:
                out.append(self.ROOT / lane / ref)
        return out

    def test_the_index_is_not_empty(self):
        """A parser that silently matched nothing would make both checks
        below pass on any input at all."""
        for lane in self.LANES:
            self.assertGreaterEqual(
                len(self.rows(lane)), 8,
                f"{lane}/SKILL.md: the index parser found almost no rows, so "
                f"the checks below are grading an empty set")

    def test_every_row_names_a_reference_that_exists(self):
        for lane in self.LANES:
            for name, ref in self.rows(lane):
                for path in self.resolve(lane, ref):
                    self.assertTrue(
                        path.exists(),
                        f"{lane}/SKILL.md: `{name}` points at {path.name}, "
                        f"which does not exist")

    def test_every_row_has_a_procedure_in_the_reference_it_names(self):
        for lane in self.LANES:
            for name, ref in self.rows(lane):
                pat = re.compile(rf"(?m)^#+ .*`[^`]*\b{re.escape(name)}\b")
                body = "\n".join(p.read_text() for p in self.resolve(lane, ref)
                                  if p.exists())
                self.assertRegex(
                    body, pat,
                    f"{lane}/SKILL.md declares `{name}` and points at {ref}, "
                    f"but that file has no heading for it — the index promises "
                    f"a procedure nobody wrote, and each user gets a different "
                    f"one improvised on the spot")


class TestTheStageInvariantReachesEveryFileThatMovesARow(unittest.TestCase):
    """`work/reference/subcommands.md` said the stage invariant "is restated in
    `reference/dispatch.md` and `reference/autopilot.md` rather than relying on
    this one". Neither file contained the word `Stage`.

    The sentence was doing real work: reference files are loaded one at a time,
    so a claim that another file carries the rule is the only thing standing
    between a dispatch loop and a hand-edited cell. Being false made it worse
    than absent — it stopped anyone from noticing the gap.

    Found as m-10 in the V4 review of TASK-019/020.
    """

    ROOT = pathlib.Path(__file__).resolve().parent.parent
    CLAIMANT = "work/reference/subcommands.md"

    def test_the_files_named_as_restating_it_actually_do(self):
        """Checks the claim as written: pull the cited paths out of the
        sentence itself, so renaming a file or moving the restatement breaks
        this rather than going quiet."""
        text = (self.ROOT / self.CLAIMANT).read_text()
        sentences = [s for s in re.split(r"(?<=\.)\s", text)
                     if "restated in" in s]
        self.assertTrue(
            sentences,
            f"{self.CLAIMANT}: the claim this test grades is gone. If the "
            f"restatements were dropped on purpose, delete this test with "
            f"them; if the wording changed, update the match.")
        for s in sentences:
            cited = re.findall(r"`(reference/[\w-]+\.md)`", s)
            self.assertTrue(cited, f"claims a restatement but names no file: {s}")
            for ref in cited:
                path = self.ROOT / "work" / ref
                self.assertTrue(path.exists(), f"{ref} does not exist")
                self.assertIn(
                    "Stage since", path.read_text(),
                    f"{self.CLAIMANT} says {ref} restates the stage "
                    f"invariant; {ref} does not mention it")

    def test_every_file_that_lands_a_row_carries_the_stage_rule(self):
        """The claim above is prose. This is the rule underneath it: a
        procedure that tells the agent to write `Status` on completion is a
        procedure where the stage moves too, and `Stage` and `Status` are
        orthogonal — a stage move produces no status change and leaves no
        trace at all if hand-edited."""
        for name in ("subcommands.md", "dispatch.md", "autopilot.md"):
            body = (self.ROOT / "work" / "reference" / name).read_text()
            if "--status review" not in body:
                continue
            self.assertRegex(
                body, r'perry-task["`]? stage',
                f"{name} instructs a status write on completion but never "
                f"names `perry-task stage`, so a pipeline row's dwell clock "
                f"gets hand-edited or left stale")


if __name__ == "__main__":
    unittest.main()
