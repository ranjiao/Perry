"""TASK-043's gate: the declared, checkable conformance marker (ADR-004).

The claim under test: **Perry can tell "this file matches my shape, at shape
version N, and the user said so" apart from "this folder has a BOARD.md in
it"** — and every writer asks the first question about the one file it is
about to write, while every reader asks neither.

Two things this suite is deliberately built to catch, because they are the
failure modes the task's own rubric names:

- a gate that cannot fire — and, since TASK-047 flipped the shipped default to
  `enforce`, a gate that cannot be turned off. Both branches are exercised
  explicitly: § 7 asserts the refusal under the shipped default AND the write
  proceeding under `advisory`, reached both by `PERRY_CONFORMANCE` and by
  `.perry/config.md`. A guard that only ever runs in one mode is not a guard.
- a second definition of Perry's shape. `TestOneDefinitionOfTheShape` compares
  `perry-conform`'s per-file error counts against `perry-lint`'s own findings,
  file by file, on a real project. They agree because there is one
  implementation; if someone writes a second one, this goes red.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
TASK = PERRY_HOME / "bin" / "perry-task"
DECIDE = PERRY_HOME / "bin" / "perry-decide"
GOALS = PERRY_HOME / "bin" / "perry-goals"
STATE = PERRY_HOME / "bin" / "perry-state"
LINT = PERRY_HOME / "bin" / "perry-lint"
CONFORM = PERRY_HOME / "bin" / "perry-conform"
MIGRATE = PERRY_HOME / "bin" / "perry-migrate"

SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())


def load(name: str, path: Path):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


C = load("perry_conform_under_test", CONFORM)

BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

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

#: The same board with the ID column renamed. `perry-lint` calls this a
#: `table-columns` error, which is precisely a shape violation: every reader
#: keys on that header.
BOARD_WRONG_SHAPE = BOARD.replace(
    "| ID | Title | Owner | Status | Next action | Evidence |",
    "| Ticket | Title | Owner | Status | Next action | Evidence |", 1)

ADD = ("add", "--title", "a row", "--priority", "P1",
       "--deliverable", "a thing that exists afterwards",
       "--verification", "the suite is green")


class Project:
    """A throwaway project, unmarked by default — like every project alive."""

    def __init__(self, board: str | None = BOARD, config_extra: str = ""):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + config_extra)
        if board is not None:
            (self.root / "BOARD.md").write_text(board)
        # Armed, so the fixture carries no lint finding of its own and a test
        # that measures "did being undeclared add a finding" is measuring that
        # and not the hook warning every bare project starts with.
        (self.root / ".perry" / "hook.md").write_text(
            "# Hook\n\n## High-stakes operations\n\n- anything that spends money\n")

    def run(self, tool: Path, *argv, enforce: bool | None = None,
            json_out: bool = True) -> tuple[int, dict | str, str]:
        env = dict(os.environ)
        env.pop("PERRY_CONFORMANCE", None)
        if enforce is not None:
            env["PERRY_CONFORMANCE"] = "enforce" if enforce else "advisory"
        argv = [*argv, "--root", str(self.root)]
        if json_out:
            argv.append("--json")
        r = subprocess.run(["python3", str(tool), *argv],
                           capture_output=True, text=True, env=env)
        try:
            return r.returncode, json.loads(r.stdout or "{}"), r.stderr
        except json.JSONDecodeError:
            return r.returncode, r.stdout, r.stderr

    def marker(self) -> Path:
        return self.root / ".perry" / "conformance.md"

    def verdict(self, key: str = "BOARD.md"):
        return C.verdict(self.root, self.root, key, SCHEMA)

    def __del__(self):
        self.dir.cleanup()


# ── 1 · the marker records a decision; lint verifies a shape ──────────────


class TestTwoFactsNotOne(unittest.TestCase):

    def test_a_file_that_conforms_but_was_never_declared_is_not_conformant(self):
        """The default ADR-004 chose. `BOARD.md` here is byte-identical to one
        Perry would have written and lints clean — and it is still not
        conformant, because nobody said so."""
        p = Project()
        rc, out, _ = p.run(CONFORM, "check", "BOARD.md")
        self.assertEqual(out["errors"], 0, "the fixture board must lint clean")
        self.assertEqual(out["state"], C.UNDECLARED)
        self.assertEqual(rc, 1)

    def test_the_declaration_alone_is_not_trusted_when_the_file_no_longer_matches(self):
        """A user can edit a file after declaring it. That is a finding."""
        p = Project()
        rc, _, _ = p.run(CONFORM, "declare", "BOARD.md")
        self.assertEqual(rc, 0)
        self.assertEqual(p.verdict().state, C.CONFORMANT)
        (p.root / "BOARD.md").write_text(BOARD_WRONG_SHAPE)
        v = p.verdict()
        self.assertEqual(v.state, C.DRIFTED)
        self.assertTrue(v.errors, "drift with no lint error is not drift")

    def test_a_drifted_declaration_is_reported_and_not_revoked(self):
        """Not silently trusted, and not silently corrected either — the row
        the user wrote stays in the record."""
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        (p.root / "BOARD.md").write_text(BOARD_WRONG_SHAPE)
        p.run(CONFORM, "check", "BOARD.md")
        p.run(TASK, *ADD, enforce=False)          # a full advisory write cycle
        self.assertIn("| BOARD.md | 2 |", p.marker().read_text(),
                      "the declaration was revoked behind the user's back")

    def test_no_tool_stamps_the_marker_on_its_own_initiative(self):
        """ADR-004 § 4. A whole advisory write cycle — the mode that is allowed
        to proceed — must leave the record untouched."""
        p = Project()
        rc, out, _ = p.run(TASK, *ADD, enforce=False)
        self.assertEqual(rc, 0, out)
        self.assertFalse(p.marker().exists(),
                         "perry-task wrote a conformance declaration nobody made")
        rc, _, _ = p.run(DECIDE, "bootstrap", enforce=False)
        self.assertEqual(rc, 0)
        self.assertFalse(p.marker().exists(),
                         "perry-decide wrote a conformance declaration nobody made")

    def test_declare_refuses_to_record_a_declaration_that_would_be_false(self):
        p = Project(board=BOARD_WRONG_SHAPE)
        rc, out, _ = p.run(CONFORM, "declare", "BOARD.md")
        self.assertEqual(rc, 1)
        self.assertEqual(out["declared"], [])
        self.assertEqual(out["refused"][0]["path"], "BOARD.md")
        self.assertGreater(out["refused"][0]["errors"], 0)
        self.assertFalse(p.marker().exists())

    def test_declaring_is_never_implicit(self):
        """`declare` with no file and no --all refuses rather than guessing."""
        p = Project()
        rc, out, _ = p.run(CONFORM, "declare")
        self.assertEqual(rc, 1)
        self.assertIn("--all", out["refused"])
        self.assertFalse(p.marker().exists())


# ── 2 · per file, not per project ─────────────────────────────────────────


class TestPerFileNotPerProject(unittest.TestCase):

    def test_declaring_the_board_does_not_declare_the_decisions_index(self):
        p = Project()
        (p.root / "decisions").mkdir()
        p.run(DECIDE, "bootstrap", enforce=False)
        p.run(CONFORM, "declare", "BOARD.md")
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 0, f"the board was declared: {out}")
        rc, out, _ = p.run(DECIDE, "new", "x", "--title", "T",
                           "--type", "Process", enforce=True)
        self.assertEqual(rc, 1, "perry-decide gated on a file it does not write")
        self.assertIn("DECISIONS.md", out["refused"])
        self.assertNotIn("BOARD.md", out["refused"])

    def test_a_project_may_declare_one_file_and_not_another(self):
        """ADR-004 § 5 — partial migration is a state, not a failure. The rows
        that can be written are written; the exit code still says the request
        was not fully satisfied."""
        p = Project(board=BOARD_WRONG_SHAPE)
        rc, out, _ = p.run(CONFORM, "declare", "--all")
        declared = {d["path"] for d in out["declared"]}
        refused = {r["path"] for r in out["refused"]}
        self.assertIn(".perry/config.md", declared)
        self.assertIn("BOARD.md", refused)
        self.assertEqual(rc, 1)
        self.assertIn("| .perry/config.md |", p.marker().read_text())
        self.assertNotIn("| BOARD.md |", p.marker().read_text())


# ── 3 · versioned from the start ──────────────────────────────────────────


class TestVersionedFromTheStart(unittest.TestCase):

    def test_the_shape_version_is_the_schema_version_and_not_a_second_number(self):
        """One rule, one number. A `conformance_version` beside
        `schema_version` would be two counters for one fact, and the first
        schema change that bumped only one of them would make every marker
        a lie."""
        on_disk = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text())["schema_version"]
        self.assertEqual(C.shape_version(SCHEMA), on_disk)
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        self.assertIn(f"| BOARD.md | {on_disk} |", p.marker().read_text())

    def test_a_declaration_at_an_older_shape_version_is_never_silently_accepted(self):
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        p.marker().write_text(
            p.marker().read_text().replace(
                f"| BOARD.md | {C.shape_version(SCHEMA)} |", "| BOARD.md | 1 |"))
        v = p.verdict()
        self.assertEqual(v.state, C.STALE)
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 1)
        self.assertIn("shape version 1", out["refused"])
        self.assertIn("perry-conform declare", out["refused"])

    def test_the_declared_version_is_readable_without_re_deriving_it(self):
        """The whole point of storing it: a v1 project is distinguishable from
        a v2 project by reading the record, not by inspecting the files."""
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        p.marker().write_text(p.marker().read_text().replace(
            f"| BOARD.md | {C.shape_version(SCHEMA)} |", "| BOARD.md | 1 |"))
        rc, out, _ = p.run(CONFORM, "status")
        row = next(f for f in out["files"] if f["path"] == "BOARD.md")
        self.assertEqual(row["declared_version"], 1)
        self.assertEqual(row["shape_version"], C.shape_version(SCHEMA))
        self.assertNotEqual(row["declared_version"], row["shape_version"],
                            "a fixture where both agree cannot show the difference")


# ── 4 · a refusal names the way forward ───────────────────────────────────


class TestARefusalNamesTheWayForward(unittest.TestCase):
    """Four distinct non-ok states exist, and none of them is a wall."""

    def _states(self) -> dict:
        out = {}

        clean = Project()
        out[C.UNDECLARED] = clean.verdict()

        dirty = Project(board=BOARD_WRONG_SHAPE)
        out["undeclared_dirty"] = dirty.verdict()

        stale = Project()
        stale.run(CONFORM, "declare", "BOARD.md")
        stale.marker().write_text(stale.marker().read_text().replace(
            f"| BOARD.md | {C.shape_version(SCHEMA)} |", "| BOARD.md | 1 |"))
        out[C.STALE] = stale.verdict()

        drift = Project()
        drift.run(CONFORM, "declare", "BOARD.md")
        (drift.root / "BOARD.md").write_text(BOARD_WRONG_SHAPE)
        out[C.DRIFTED] = drift.verdict()
        self._keep = (clean, dirty, stale, drift)
        return out

    def test_every_non_conformant_state_names_a_command_that_exists(self):
        states = self._states()
        self.assertEqual(
            {v.state for v in states.values()},
            {C.UNDECLARED, C.STALE, C.DRIFTED},
            "the fixtures did not actually produce distinct verdicts")
        self.assertEqual(states["undeclared_dirty"].errors and True, True)
        for name, v in states.items():
            msg = C.message_for(v, "perry-task", None)
            self.assertTrue(msg, f"{name} refuses with no message at all")
            named = [w.strip() for line in msg.split("\n")
                     for w in [line] if line.strip().startswith("perry-")]
            self.assertTrue(named, f"{name} names no command to run: {msg}")
            for line in named:
                tool = line.split()[0]
                self.assertTrue((PERRY_HOME / "bin" / tool).exists(),
                                f"{name} names {tool!r}, which does not exist")

    def test_the_refusal_distinguishes_conformant_but_undeclared_from_malformed(self):
        """The two need different next steps: one is a declaration, the other
        is a migration. A gate that said "not conformant" to both would send
        half its users to the wrong place."""
        states = self._states()
        clean = C.message_for(states[C.UNDECLARED], "perry-task", None)
        dirty = C.message_for(states["undeclared_dirty"], "perry-task", None)
        self.assertIn("already matches Perry's shape", clean)
        self.assertNotIn("perry-lint", clean)
        self.assertIn("perry-lint", dirty)
        self.assertIn("read-only", dirty)

    def test_the_refusal_says_nothing_was_written(self):
        p = Project(board=BOARD_WRONG_SHAPE)
        before = (p.root / "BOARD.md").read_text()
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 1)
        self.assertEqual((p.root / "BOARD.md").read_text(), before)
        self.assertFalse((p.root / "journal").exists())
        self.assertFalse((p.root / ".perry" / "events.jsonl").exists())


# ── 5 · reading is not gated ──────────────────────────────────────────────


class TestReadingIsNotGated(unittest.TestCase):
    """The half of ADR-004 that is easy to break by accident. Every check here
    runs with the gate ENFORCING on a project that has declared nothing."""

    #: Frozen on 2026-08-17, before this task touched anything. A reader that
    #: gains or loses a top-level key breaks a consumer that does not read
    #: Perry's changelog.
    CONTRACTS = {
        # 1.5 was 1.4's key set exactly — that minor moved for two corrected
        # VALUES (`evidence_paths` and `conformance.evidence_not_found` on
        # closed rows, TASK-057), which is what this table is here to let
        # through while a gained or lost key is not.
        #
        # 1.6 DOES gain keys, so this line was edited deliberately: `risks`,
        # `asks` and `drift` (TASK-058 — three blocks a Work surface shows that
        # were readable only through the unversioned `perry-state --json`). The
        # freeze still freezes: every other key in the set is unchanged, the
        # version string had to move in the same edit, and a fourth key added
        # without touching this line still fails here.
        "perry-task/list/1.13": (
            TASK, ("list", "--all"),
            {"project_root", "state_root", "contract", "semantics", "tasks",
             "open", "closed", "events", "untitled", "conformance", "intake",
             "risks", "asks", "drift"}),
        "perry-decide/list/1.0": (
            DECIDE, ("list",),
            {"project_root", "state_root", "contract", "decisions", "active",
             "total", "expired_sunsets", "conformance"}),
        "perry-goals/list/2.1": (
            GOALS, ("list",),
            {"project_root", "state_root", "contract", "okr", "phase", "krs",
             "linkage", "counts", "conformance", "unlinked_task_ids",
             "answered_by"}),
    }

    def test_every_read_command_answers_on_an_undeclared_project(self):
        p = Project()
        for tool, argv in ((TASK, ("list",)), (DECIDE, ("list",)),
                           (GOALS, ("list",))):
            rc, out, err = p.run(tool, *argv, enforce=True)
            self.assertEqual(rc, 0, f"{tool.name} {argv} was gated: {out} {err}")

    def test_perry_state_answers_on_an_undeclared_project(self):
        p = Project()
        rc, out, err = p.run(STATE, enforce=True)
        self.assertEqual(rc, 0, err)
        self.assertIn("board", out)

    def test_the_three_contracts_do_not_change_shape(self):
        p = Project()
        for version, (tool, argv, keys) in self.CONTRACTS.items():
            with self.subTest(contract=version):
                rc, out, err = p.run(tool, *argv, enforce=True)
                self.assertEqual(rc, 0, err)
                self.assertEqual(out.get("contract"), version,
                                 "the contract version moved")
                self.assertEqual(set(out), keys,
                                 "a published contract gained or lost a key")

    def test_the_gate_adds_nothing_to_the_task_list_payload(self):
        """`list`'s `conformance` block already means something else — the rows
        this reader could not parse. A second, differently-meaning key under
        the same name is how a front-end learns the wrong thing."""
        p = Project()
        p.run(TASK, *ADD, enforce=False)
        rc, out, _ = p.run(TASK, "list", "--all", enforce=True)
        self.assertNotIn("state", out["conformance"],
                         "the shape verdict leaked into the read contract")
        self.assertNotIn("gate", out["conformance"])


# ── 6 · one definition of the shape ───────────────────────────────────────


SNAPSHOT = os.environ.get("PERRY_TEST_CORPUS")
REAL = Path(SNAPSHOT) if SNAPSHOT else Path.home() / "proj" / "gimegime-pmo"


class TestOneDefinitionOfTheShape(unittest.TestCase):
    """`perry-conform` must not contain a second answer to "is this Perry's
    shape". It contains none at all — it calls `perry-lint.check_file`."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = None
        if not (REAL / "BOARD.md").exists():
            return
        # A COPY, always. Something else on this machine writes to that folder.
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "project"
        shutil.copytree(REAL, cls.root,
                        ignore=shutil.ignore_patterns(".git"), symlinks=True)

    @classmethod
    def tearDownClass(cls):
        if cls.tmp:
            cls.tmp.cleanup()

    def test_per_file_error_counts_match_perry_lints_own_findings(self):
        if self.tmp is None:
            self.skipTest(f"no corpus at {REAL}")
        lint = json.loads(subprocess.run(
            ["python3", str(LINT), "--root", str(self.root), "--json"],
            capture_output=True, text=True).stdout)
        conform = json.loads(subprocess.run(
            ["python3", str(CONFORM), "status", "--root", str(self.root), "--json"],
            capture_output=True, text=True).stdout)

        by_file: dict[str, int] = {}
        for f in lint["findings"]:
            if f["severity"] == "error":
                by_file[f["file"]] = by_file.get(f["file"], 0) + 1
        self.assertTrue(by_file, "a corpus with no lint errors proves nothing here")

        for row in conform["files"]:
            with self.subTest(path=row["path"]):
                self.assertEqual(row["errors"], by_file.get(row["path"], 0))
        self.assertEqual(sum(r["errors"] for r in conform["files"]),
                         sum(by_file.values()),
                         "the two disagree about how many errors this project has")

    def test_the_real_project_can_declare_the_files_that_already_conform(self):
        """The concrete ADR-004 § 5 case: this project's board cannot be
        declared and three of its files can."""
        if self.tmp is None:
            self.skipTest(f"no corpus at {REAL}")
        r = subprocess.run(
            ["python3", str(CONFORM), "declare", "--all",
             "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(r.returncode, 1)
        self.assertTrue(out["declared"], "nothing at all could be declared")
        self.assertIn("BOARD.md", {x["path"] for x in out["refused"]})


class TestMigrationDoesNotReachTheWholeBoard(unittest.TestCase):
    """TASK-047, cost 1 — measured on a real project rather than argued.

    ADR-004 says flip the gate to `enforce` once the migration exists, and
    TASK-047 flipped it. What this pins is the residue the flip therefore
    ships with: on `~/proj/gimegime-pmo`, `perry-migrate` takes `BOARD.md` from
    3 errors to 1, and the survivor is a row reading `Status: 半解` — a
    distinction the user drew in their own words, which `perry-migrate`
    correctly refuses to coerce into `in_progress`.

    So a file a complete migration leaves non-conformant stays refused until a
    human edits it and declares it. That is a door needing a hand rather than a
    wall — the refusal names `perry-lint` and `perry-conform declare` as well
    as `perry-migrate` — but it is a real cost and it is stated, not
    discovered.

    Read-only: a dry run, on a copy, and it asserts nothing about WHICH
    residual finding remains — only that one does. This goes RED the day the
    residue is solved, which is the day the row in `bin/README.md` can go."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = None
        if not (REAL / "BOARD.md").exists():
            return
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "project"
        shutil.copytree(REAL, cls.root,
                        ignore=shutil.ignore_patterns(".git"), symlinks=True)

    @classmethod
    def tearDownClass(cls):
        if cls.tmp:
            cls.tmp.cleanup()

    def test_the_migration_plan_for_the_board_does_not_reach_zero(self):
        if self.tmp is None:
            self.skipTest(f"no corpus at {REAL}")
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-migrate"),
             "--root", str(self.root), "--only", "BOARD.md", "--json"],
            capture_output=True, text=True, timeout=600)
        plan = json.loads(r.stdout)
        board = next(f for f in plan["files"] if f["path"] == "BOARD.md")
        self.assertGreater(board["before_errors"], 0,
                           "the corpus board is already conformant — this test "
                           "no longer measures anything")
        self.assertGreater(
            board["after_errors"], 0,
            "perry-migrate now takes a real board to zero errors: cost 1 in "
            "bin/README.md § The switch-over checklist is gone. Delete this "
            "test and the row it pins — the flip itself already happened "
            "(TASK-047), so nothing about DEFAULT_MODE needs revisiting.")
        self.assertFalse(board["writable"],
                         "a plan with residual errors must not be applied — "
                         "ADR-004 guarantee 5, partial migration is per file")

    def test_that_the_migrated_store_is_read_while_board_is_unwritable(self):
        """Conformance gates projection writes, not reads of canonical tasks."""
        if self.tmp is None:
            self.skipTest(f"no corpus at {REAL}")
        seeded = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-tasks"), "write",
             "--from-board", "--root", str(self.root)],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
        r = subprocess.run(
            ["python3", str(TASK), "list", "--all",
             "--root", str(self.root), "--json"],
            capture_output=True, text=True,
            env=dict(os.environ, PERRY_CONFORMANCE="enforce"), timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreater(len(json.loads(r.stdout)["tasks"]), 20,
                           "the unwritable board stopped being readable")


class TestConformanceIsErrorsNotWarnings(unittest.TestCase):
    """Open question in the spec, answered: **errors only**.

    Warnings in this schema are quality signals, and at least one of them —
    `stale-run` — becomes true with the passage of time and nothing else. A
    declaration that revoked itself on a calendar boundary would not be a
    statement about shape."""

    def _stale_dossier(self) -> Project:
        p = Project()
        (p.root / ".perry" / "adoption").mkdir()
        (p.root / ".perry" / "adoption" / "run.md").write_text(
            "---\nadoption: 1\nproject: t\nstage: confirm\nstep: state_root\n"
            "updated: '2020-01-01T00:00:00Z'\n---\n\n# run\n")
        return p

    def test_a_file_carrying_only_warnings_can_be_declared(self):
        p = self._stale_dossier()
        lint = json.loads(subprocess.run(
            ["python3", str(LINT), "--root", str(p.root), "--json"],
            capture_output=True, text=True).stdout)
        warns = [f for f in lint["findings"]
                 if f["file"] == ".perry/adoption/run.md" and f["severity"] == "warn"]
        errs = [f for f in lint["findings"]
                if f["file"] == ".perry/adoption/run.md" and f["severity"] == "error"]
        self.assertTrue(warns, "the fixture produced no warning — nothing is proven")
        self.assertEqual(errs, [], "the fixture produced an error, not a warning")

        rc, out, _ = p.run(CONFORM, "declare", ".perry/adoption/run.md")
        self.assertEqual(rc, 0, out)
        self.assertEqual(p.verdict(".perry/adoption/run.md").state, C.CONFORMANT)

    def test_the_warning_the_fixture_relies_on_is_time_dependent(self):
        """Names the actual reason, so a future reader can check the argument
        rather than trust it."""
        p = self._stale_dossier()
        lint = json.loads(subprocess.run(
            ["python3", str(LINT), "--root", str(p.root), "--json"],
            capture_output=True, text=True).stdout)
        rules = {f["rule"] for f in lint["findings"]
                 if f["file"] == ".perry/adoption/run.md"}
        self.assertIn("stale-run", rules)


class TestTheGateSpeaksEveryDocumentLanguage(unittest.TestCase):
    """`perry-lint`'s glossary is module-level state that `main()` used to arm
    inline. Calling `check_file` without arming it reports a Chinese board's own
    column headers as the wrong columns — so a localized project would be told
    it is not Perry's shape when it is, and could never declare itself."""

    ZH = PERRY_HOME / "tests" / "fixtures" / "sample-project-zh"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "zh"
        shutil.copytree(self.ZH, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_localized_board_is_conformant_and_can_be_declared(self):
        head = (self.root / "BOARD.md").read_text().split("\n")
        self.assertTrue(any("负责人" in l or "任务" in l for l in head),
                        "the fixture is not actually localized")
        r = subprocess.run(
            ["python3", str(CONFORM), "declare", "BOARD.md",
             "--root", str(self.root), "--json"], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(out["refused"], [],
                         "a localized board was called malformed")
        self.assertEqual(r.returncode, 0)


# ── 7 · enforcing, and what enforcing costs ───────────────────────────────

#: A commitments register with the pre-TASK-091 single clock column — out of
#: Perry's shape by exactly the defect `perry-goals commit --migrate` exists to
#: repair, which is what makes it the fixture for the exemption. Kept here
#: rather than imported from `test_goals_writer` so that a change to that
#: suite's fixture cannot silently stop this one from testing the gate.
PRE_SPLIT_OKR = """# OKR — fixture

## Mission

Ship it.

## Commitments

| Id    | Track | Promise             | To whom | By when              | Status |
|-------|-------|---------------------|---------|----------------------|--------|
| rel/1 | rel   | Release 2.0         | Users   | 2027-01-01           | active |
| ops/7 | ops   | Invoices reconciled | Finance | within the track SLA | active |

## Anti-Goals

- not this
"""


class TestTheGateEnforces(unittest.TestCase):
    """TASK-047. `advisory` shipped for one release on an argument that named
    its own expiry condition — *enforcement flips when TASK-044 gives the
    non-conformant half of the population a road* — and TASK-044 landed
    2026-08-19. These assert the flip, both escape hatches, and both
    exemptions."""

    def test_the_shipped_default_is_enforce(self):
        p = Project()
        self.assertEqual(C.DEFAULT_MODE, C.ENFORCE)
        self.assertEqual(C.gate_mode(p.root), C.ENFORCE)

    def test_an_undeclared_project_is_refused_and_nothing_is_written(self):
        """V4.1. A refusal must mean the file was not touched — the gate is
        taken before the lock and before the command runs for this reason."""
        p = Project()
        before = (p.root / "BOARD.md").read_text()
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        self.assertEqual(rc, 1, out)
        self.assertIn("BOARD.md", out["refused"])
        self.assertEqual(before, (p.root / "BOARD.md").read_text(),
                         "a refused write left a mark on the file")
        self.assertFalse(p.marker().exists(),
                         "the refusal declared the file on the user's behalf")

    def test_the_refusal_names_the_file_the_version_and_a_declare_command(self):
        """V4.1, clause by clause. Three facts, because a refusal missing any
        one of them cannot be acted on without a second command."""
        p = Project()
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        msg = out["refused"]
        self.assertIn("BOARD.md", msg)
        self.assertIn(f"version {C.shape_version(SCHEMA)}", msg)
        self.assertIn("perry-conform declare BOARD.md", msg)

    def test_the_declare_command_the_refusal_names_is_runnable_verbatim(self):
        """The difference between naming a command and naming a road. The
        exact string is lifted out of the refusal and executed — if the
        message ever names a command that does not parse, this goes red."""
        p = Project()
        _, out, _ = p.run(TASK, *ADD, enforce=None)
        line = next(l.strip() for l in out["refused"].split("\n")
                    if l.strip().startswith("perry-conform declare"))
        argv = line.split()[1:] + ["--root", str(p.root)]
        r = subprocess.run(["python3", str(CONFORM), *argv],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(p.verdict("BOARD.md").state, C.CONFORMANT)
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        self.assertEqual(rc, 0, out)

    def test_advisory_lets_the_write_through_and_says_so(self):
        """V4.2. The escape hatch, and the reason `advisory` is not `off`: the
        gate computed the same verdict and printed the same message."""
        p = Project()
        rc, out, _ = p.run(TASK, *ADD, enforce=False)
        self.assertEqual(rc, 0, out)
        self.assertIn(out["id"], (p.root / "BOARD.md").read_text())
        self.assertEqual(out["conformance"]["state"], C.UNDECLARED)
        self.assertEqual(out["conformance"]["gate"], C.ADVISORY)
        self.assertTrue(out["conformance"]["allowed"])
        rc, _, err = p.run(TASK, *ADD, enforce=False, json_out=False)
        self.assertEqual(rc, 0, err)
        self.assertIn("conformance (advisory)", err)
        self.assertIn("perry-conform declare BOARD.md", err)

    def test_a_project_can_opt_out_of_enforcement_without_the_environment(self):
        """The other escape hatch. Going back is per project, not per release,
        and not a flag only the test suite can set."""
        p = Project(config_extra="- Conformance gate: advisory\n")
        self.assertEqual(C.gate_mode(p.root), C.ADVISORY)
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        self.assertEqual(rc, 0, out)

    def test_the_environment_overrides_the_project_setting(self):
        """Precedence, in the direction the flip makes load-bearing: a project
        that opted out can still be checked by a single enforcing run."""
        p = Project(config_extra="- Conformance gate: advisory\n")
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 1)
        self.assertIn("perry-conform declare", out["refused"])

    def test_declaring_the_file_turns_the_refusal_off(self):
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        rc, out, err = p.run(TASK, *ADD, enforce=None, json_out=False)
        self.assertEqual(rc, 0, err)
        self.assertNotIn("conformance", err)

    def test_the_refusal_on_a_malformed_file_names_perry_migrate(self):
        """Deliverable 4, and the whole reason the flip is defensible. The
        advisory release existed because this branch could only name
        `perry-lint`, which reports the problem and fixes nothing."""
        p = Project(board=BOARD_WRONG_SHAPE)
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        self.assertEqual(rc, 1, out)
        self.assertIn("perry-migrate", out["refused"])
        self.assertIn("perry-migrate apply", out["refused"])
        self.assertIn(f"shape version {C.shape_version(SCHEMA)}",
                      out["refused"])

    # ── the two documented exemptions ─────────────────────────────────────
    #
    # A gate that refuses the migration is a wall with no door: the migration
    # is how an undeclared project becomes declarable. Both exemptions are
    # asserted here, under the SHIPPED default rather than a forced `enforce`,
    # because after TASK-047 the shipped default is the mode users meet.

    def test_goals_commit_migrate_writes_an_undeclared_file_without_refusal(self):
        """V4.3. `perry-goals commit --migrate` splits the register's clock
        column — the file it repairs is out of shape by exactly that defect,
        so gating it would make the file permanently unmigratable."""
        p = Project()
        (p.root / "OKR.md").write_text(PRE_SPLIT_OKR)
        self.assertEqual(p.verdict("OKR.md").state, C.UNDECLARED)

        blocked, out, _ = p.run(GOALS, "commit", "--track", "ops",
                                "--promise", "a", "--to", "x", "--due", "3d",
                                enforce=None)
        self.assertEqual(blocked, 1,
                         "the fixture is not gated, so the exemption proves "
                         "nothing")

        rc, out, err = p.run(GOALS, "commit", "--migrate", enforce=None)
        self.assertEqual(rc, 0, f"{out} {err}")
        self.assertIn("Due", (p.root / "OKR.md").read_text())
        self.assertIn("By when note", (p.root / "OKR.md").read_text())
        self.assertFalse(p.marker().exists(),
                         "the exempt write declared the file on the user's "
                         "behalf")

    def test_the_exempt_goals_run_announces_the_exemption_exactly_once(self):
        """The exemption is loud, and it is not also advisory. Three
        independent `if`s printed both lines under `enforce`; unreachable
        while the default was advisory, wrong the day it flipped."""
        p = Project()
        (p.root / "OKR.md").write_text(PRE_SPLIT_OKR)
        rc, _, err = p.run(GOALS, "commit", "--migrate", enforce=None,
                           json_out=False)
        self.assertEqual(rc, 0, err)
        self.assertEqual(1, err.count("that is what a migration is"))
        self.assertNotIn("conformance (advisory)", err)
        self.assertNotIn("conformance (enforce)", err)

    def test_perry_migrate_runs_to_completion_against_an_undeclared_project(self):
        """V4.4. `perry-migrate` is exempt from its own gate — it is how an
        undeclared project becomes declarable, and it is the command the
        refusal names. Run to completion means `apply`, not just a plan."""
        p = Project(board=BOARD_WRONG_SHAPE)
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)
        rc, out, err = p.run(MIGRATE, "apply", enforce=None)
        self.assertEqual(rc, 0, f"{out} {err}")
        board = next(f for f in out["files"] if f["path"] == "BOARD.md")
        self.assertEqual(board["after_errors"], 0, board)
        self.assertEqual(p.verdict("BOARD.md").state, C.CONFORMANT,
                         "apply did not record the user's declaration")
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        self.assertEqual(rc, 0,
                         "the road the refusal names does not lead anywhere")

    # ── TASK-047 · what the flip costs ────────────────────────────────────
    #
    # Two costs came out of the measurement that preceded the flip. Neither is
    # a missing road — both are places a user meets the gate on day one, and
    # they are pinned here so that the day either stops being true a test says
    # so instead of `bin/README.md` quietly going stale. Each is written to go
    # RED when the cost is removed.

    def test_a_project_with_a_perfect_shape_is_still_refused_before_declaring(self):
        """Cost 2. Conformance is two facts and Perry can only produce one of
        them: a project Perry itself just wrote carries zero shape errors and
        is still `undeclared`, because `SKILL.md § Conformance gate` forbids an
        agent from declaring on the user's behalf (`perry/OKR.md` — *adoption
        proposes; the user declares*). So the first `perry-task add` on a
        spotless project asks the user for one command.

        Goes red when setup/adopt ends in the user's own declaration."""
        p = Project()
        lint = json.loads(subprocess.run(
            ["python3", str(LINT), "--root", str(p.root), "--json"],
            capture_output=True, text=True).stdout)
        board_errors = [f for f in lint["findings"]
                        if f["file"] == "BOARD.md" and f["severity"] == "error"]
        self.assertEqual(board_errors, [],
                         "the fixture is no longer a perfectly shaped board, "
                         "so this test would prove nothing")
        rc, out, _ = p.run(TASK, *ADD, enforce=None)
        self.assertEqual(
            rc, 1,
            "a zero-error project is now writable under the shipped default — "
            "cost 2 in bin/README.md § The switch-over checklist is gone; "
            "delete this test and the row it pins")
        self.assertIn("no one has declared it", out["refused"])

    def test_reading_is_not_gated_for_the_commands_a_refusal_names(self):
        """The guarantee ADR-004 calls non-negotiable, applied to the two
        readers the refusal message itself points at. A gated `perry-migrate`
        or `perry-lint` would close the loop: refused, and told to run a
        command that is refused for the same reason."""
        p = Project(board=BOARD_WRONG_SHAPE)
        env = dict(os.environ, PERRY_CONFORMANCE="enforce")
        for tool in (LINT, PERRY_HOME / "bin" / "perry-migrate"):
            with self.subTest(tool=tool.name):
                r = subprocess.run(
                    ["python3", str(tool), "--root", str(p.root), "--json"],
                    capture_output=True, text=True, env=env, timeout=300)
                self.assertIn(r.returncode, (0, 1),
                              f"{tool.name} crashed under enforce: {r.stderr}")
                self.assertNotIn("refused", r.stderr,
                                 f"{tool.name} is gated — the refusal names it")
                self.assertTrue(r.stdout.strip(),
                                f"{tool.name} produced no output under enforce")

    def test_the_switch_over_checklist_names_both_costs_and_the_way_back(self):
        """The checklist is the deliverable a reader acts on. It must name
        both costs the flip carries AND the way back — a document that
        announces an enforcing default without naming `advisory` is the wall
        this whole gate is built not to be."""
        doc = (PERRY_HOME / "bin" / "README.md").read_text()
        self.assertIn("switch-over checklist", doc.lower())
        body = doc.split("switch-over checklist", 1)[1].split("\n### ", 1)[0]
        for claim in ("perry-migrate", "declare", "BOARD.md", "undeclared",
                      "advisory", "PERRY_CONFORMANCE"):
            self.assertIn(claim, body,
                          f"the checklist no longer names {claim}")
        self.assertNotIn("not the default yet", doc,
                         "the checklist still describes a state that passed")


# ── 8 · a file that does not exist yet is not a stranger's file ───────────


class TestAbsentIsNotNonConformant(unittest.TestCase):

    def test_bootstrap_is_not_gated_on_the_file_it_creates(self):
        """`perry-decide bootstrap` creates `DECISIONS.md`. There is no shape
        to conform to before it exists, and the file it writes is Perry's own
        template — refusing here would make the lane unreachable."""
        p = Project()
        self.assertFalse((p.root / "DECISIONS.md").exists())
        self.assertEqual(p.verdict("DECISIONS.md").state, C.ABSENT)
        rc, out, err = p.run(DECIDE, "bootstrap", enforce=True)
        self.assertEqual(rc, 0, f"{out} {err}")
        self.assertTrue((p.root / "DECISIONS.md").exists())

    def test_the_file_bootstrap_created_is_still_not_declared(self):
        """…and Perry did not declare it on the user's behalf. The next write
        asks, and the refusal is the one-command kind."""
        p = Project()
        p.run(DECIDE, "bootstrap", enforce=True)
        self.assertFalse(p.marker().exists())
        self.assertEqual(p.verdict("DECISIONS.md").state, C.UNDECLARED)


# ── 9 · the record itself ─────────────────────────────────────────────────


class TestTheRecordIsReadHonestly(unittest.TestCase):

    def test_a_row_that_cannot_be_read_is_reported_not_treated_as_absent(self):
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        p.marker().write_text(p.marker().read_text().replace(
            f"| BOARD.md | {C.shape_version(SCHEMA)} |", "| BOARD.md | v-two |"))
        rc, out, _ = p.run(CONFORM, "status")
        self.assertEqual(len(out["unreadable_rows"]), 1)
        row = next(f for f in out["files"] if f["path"] == "BOARD.md")
        self.assertEqual(row["state"], C.UNDECLARED)
        self.assertEqual(row["record_unreadable_rows"], 1)

    def test_the_refusal_mentions_the_unreadable_rows(self):
        """Otherwise "you never declared it" is a confident lie about a file
        the user did declare, in a table they mistyped."""
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        p.marker().write_text(p.marker().read_text().replace(
            f"| BOARD.md | {C.shape_version(SCHEMA)} |", "| BOARD.md | v-two |"))
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 1)
        self.assertIn("could not be read", out["refused"])

    def test_the_record_is_not_reported_as_someone_elses_file(self):
        """`perry-lint --claims` asks "is anything in the territory Perry wants
        already someone else's". The record lives in `.perry/`, is not a
        `files[]` entry, and was reported as a foreign file the moment it was
        first written — which would tell a user that adopting Perry collides
        with Perry."""
        p = Project()
        def collisions() -> int:
            r = subprocess.run(
                ["python3", str(LINT), "--claims", "--root", str(p.root), "--json"],
                capture_output=True, text=True)
            return json.loads(r.stdout)["collisions"]

        self.assertEqual(collisions(), 0, "the fixture already collides")
        p.run(CONFORM, "declare", "BOARD.md")
        self.assertTrue(p.marker().exists())
        self.assertEqual(collisions(), 0,
                         "declaring conformance made Perry collide with itself")

    def test_the_record_survives_a_second_declaration(self):
        p = Project()
        (p.root / "decisions").mkdir()
        p.run(DECIDE, "bootstrap", enforce=False)
        p.run(CONFORM, "declare", "BOARD.md")
        p.run(CONFORM, "declare", "DECISIONS.md")
        text = p.marker().read_text()
        self.assertIn("| BOARD.md |", text)
        self.assertIn("| DECISIONS.md |", text)

    def test_dry_run_declares_nothing(self):
        p = Project()
        rc, out, _ = p.run(CONFORM, "declare", "BOARD.md", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual([d["path"] for d in out["declared"]], ["BOARD.md"])
        self.assertFalse(p.marker().exists())


# ── 10 · lint says how to get there ───────────────────────────────────────


class TestLintPointsAtTheDeclaration(unittest.TestCase):

    def _lint(self, root: Path) -> str:
        return subprocess.run(["python3", str(LINT), "--root", str(root)],
                              capture_output=True, text=True).stdout

    def test_lint_reports_the_declaration_count_and_names_the_tool(self):
        p = Project()
        before = self._lint(p.root)
        self.assertIn("0 file(s) declared conformant", before)
        self.assertIn("perry-conform status", before)
        p.run(CONFORM, "declare", "BOARD.md")
        after = self._lint(p.root)
        self.assertIn("1 file(s) declared conformant", after)

    def test_being_undeclared_produces_no_lint_finding_at_all(self):
        """`--strict` must not go red on every project in existence for a
        reason lint cannot fix. Measured as a difference rather than as an
        absolute: the findings before and after a declaration must be
        identical, so a finding that appeared only because the project was
        undeclared would show up here whatever else the fixture carries."""
        p = Project()
        def findings():
            r = subprocess.run(
                ["python3", str(LINT), "--root", str(p.root), "--strict", "--json"],
                capture_output=True, text=True)
            return r.returncode, json.loads(r.stdout)

        rc_before, before = findings()
        p.run(CONFORM, "declare", "BOARD.md")
        rc_after, after = findings()
        self.assertEqual(before["findings"], after["findings"])
        self.assertEqual(rc_before, rc_after)
        self.assertEqual(rc_before, 0, before["findings"])
        self.assertEqual(before["conformance"]["declared"], 0)
        self.assertEqual(after["conformance"]["declared"], 1)


# ── 11 · is_adopted still answers its own question ────────────────────────


class TestIsAdoptedIsNotReplaced(unittest.TestCase):
    """TASK-045 deletes tolerance branches; this task deletes nothing. The old
    predicate keeps its old meaning and its old callers."""

    def test_is_adopted_still_answers_does_this_folder_hold_perry_state(self):
        L = load("perry_lint_under_test", LINT)
        p = Project()
        self.assertTrue(L.is_adopted(p.root, p.root),
                        "is_adopted stopped answering its own question")
        self.assertNotEqual(p.verdict().state, C.CONFORMANT,
                            "the two predicates collapsed into one")


if __name__ == "__main__":
    unittest.main()
