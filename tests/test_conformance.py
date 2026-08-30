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
  file by file, on `tests/fixtures/witness-project` — a project in the
  repository, read through `--root`, whose findings are constructed rather
  than captured. They agree because there is one implementation; if someone
  writes a second one, this goes red.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import re
import shlex
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
        #
        # **The fragments are backticked, and were not.** This line read
        # `- anything that spends money` — a bullet, so `hook-high-stakes-armed`
        # stayed quiet, and zero fragments, so the gate it silenced was empty.
        # TASK-202's check found it here, in this repository's own fixtures,
        # the first time it ran: written by someone satisfying "armed" who
        # believed a bullet was a rule. That is the whole defect, and the
        # fixture now models a hook that actually arms something.
        (self.root / ".perry" / "hook.md").write_text(
            "# Hook\n\n## High-stakes operations\n\n"
            "- anything that spends money — `invoice`, `billing`\n")

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
        """The record — `.perry/conformance.jsonl` since TASK-234."""
        return self.root / C.P.CONFORMANCE_FILE

    def legacy_marker(self) -> Path:
        """`.perry/conformance.md`, the record every project written before
        TASK-234 carries. Not a register any more: a conversion source."""
        return self.root / C.P.CONFORMANCE_LEGACY_FILE

    def line(self, path: str = "BOARD.md", version: int | None = None,
             declared: str = "2026-08-28", route: str = "declare",
             **extra) -> str:
        """One canonical store line, as `perry-conform declare` writes it."""
        rec = {"kind": "declaration", "path": path,
               "shape_version": C.shape_version(SCHEMA) if version is None
               else version,
               "declared": declared, "route": route,
               "writer": "", "recorded_at": "", "run": ""}
        rec.update(extra)
        return json.dumps(rec, ensure_ascii=False) + "\n"

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
        self.assertEqual(
            [d.path for d in C.P.read_conformance(p.root).declarations.values()],
            ["BOARD.md"], "the declaration was revoked behind the user's back")

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

    def test_declaring_the_board_does_not_declare_the_okr(self):
        """**This was written against `perry-decide` and `DECISIONS.md`.**
        TASK-235 deleted that file, and with it this lane's gate — the ADR
        bodies `perry-decide` still writes have no `files[]` shape to conform
        to, so gating it on anything would be a gate that cannot fire. The
        property under test is ADR-004 § 5's, not that lane's: two writers,
        two files, one declaration, and the second writer still refuses."""
        p = Project()
        (p.root / "OKR.md").write_text(PRE_SPLIT_OKR)
        p.run(CONFORM, "declare", "BOARD.md")
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 0, f"the board was declared: {out}")
        rc, out, _ = p.run(GOALS, "commit", "--track", "ops", "--promise", "a",
                           "--to", "x", "--due", "3d", enforce=True)
        self.assertEqual(rc, 1, "perry-goals wrote an undeclared OKR.md")
        self.assertIn("OKR.md", out["refused"])
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
        stored = C.P.read_conformance(p.root).declarations
        self.assertIn(".perry/config.md", stored)
        self.assertNotIn("BOARD.md", stored)


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
        self.assertEqual(
            C.P.read_conformance(p.root).declarations["BOARD.md"].shape_version,
            on_disk)

    def test_a_declaration_at_an_older_shape_version_is_never_silently_accepted(self):
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        p.marker().write_text(p.line(version=1))
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
        p.marker().write_text(p.line(version=1))
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
        stale.marker().write_text(stale.line(version=1))
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
        "perry-task/list/1.18": (
            TASK, ("list", "--all"),
            {"project_root", "state_root", "contract", "semantics", "tasks",
             "open", "closed", "events", "untitled", "conformance", "intake",
             "risks", "asks", "drift"}),
        #
        # Both lines below were edited deliberately by TASK-205, on the same
        # terms: each payload gains `semantics` and states so in its version
        # string in the same edit. `perry-decide/list` carries it EMPTY, which
        # is the shipped fact and not a placeholder — a consumer checks before
        # it looks, so the key is asserted here by presence, not by content.
        "perry-decide/list/2.0": (
            DECIDE, ("list",),
            {"project_root", "state_root", "contract", "semantics",
             "decisions", "active", "total", "expired_sunsets",
             "conformance"}),
        "perry-goals/list/2.3": (
            GOALS, ("list",),
            {"project_root", "state_root", "contract", "semantics", "okr",
             "phase", "krs", "linkage", "counts", "conformance",
             "unlinked_task_ids", "answered_by"}),
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


#: The corpus for § 6, and it is inside the repository on every machine.
#:
#: It used to be `~/proj/gimegime-pmo`, behind `PERRY_TEST_CORPUS` and an
#: `if (REAL / "BOARD.md").exists()` in `setUpClass`. On the author's machine
#: the four tests below ran; on every other checkout they skipped, so the "one
#: definition of the shape" claim — the thing this section exists to hold —
#: had no coverage anywhere it mattered. TASK-111's sweep named this file and
#: left it its own row; TASK-124 is that row.
#:
#: `tests/fixtures/witness-project` (TASK-132) replaces it, read through the
#: **same `--root` seam** the real project was read through. It is not a
#: snapshot of anybody's project: every finding in it is constructed, one per
#: rule, and its own top-risk line says so. And nothing below asserts what
#: those findings ARE — the assertions are that `perry-conform` and
#: `perry-lint` report the *same* per-file error counts, whatever the fixture
#: happens to carry. A golden file recording what one real project looked like
#: on capture day is the failure TASK-145 spent a row escaping; this is the
#: other shape, where correctness is a property of the two checkers and the
#: fixture only has to be non-trivial.
#:
#: `PERRY_TEST_CORPUS` is gone. It was a way to point these tests at a
#: different directory, and the only thing it ever pointed them at was the one
#: directory that is now unnecessary; keeping it would leave a second, untested
#: way for this corpus to become something else.
WITNESS = PERRY_HOME / "tests" / "fixtures" / "witness-project"


def copy_of(src: Path, into: tempfile.TemporaryDirectory) -> Path:
    """A COPY, always — `declare` and `perry-tasks write` both write, and the
    fixture is read by other modules in the same run."""
    root = Path(into.name) / "project"
    shutil.copytree(src, root, ignore=shutil.ignore_patterns(".git"),
                    symlinks=True)
    return root


def lint_errors_by_file(root: Path) -> dict[str, int]:
    lint = json.loads(subprocess.run(
        ["python3", str(LINT), "--root", str(root), "--json"],
        capture_output=True, text=True).stdout)
    by_file: dict[str, int] = {}
    for f in lint["findings"]:
        if f["severity"] == "error":
            by_file[f["file"]] = by_file.get(f["file"], 0) + 1
    return by_file


class TestOneDefinitionOfTheShape(unittest.TestCase):
    """`perry-conform` must not contain a second answer to "is this Perry's
    shape". It contains none at all — it calls `perry-lint.check_file`."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = copy_of(WITNESS, cls.tmp)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_corpus_can_still_tell_the_two_checkers_apart(self):
        """The anti-vacuity guard, stated before the comparisons that need it.

        A corpus with no errors makes both tests below pass against a
        `perry-conform` that returns 0 for everything, and a corpus whose
        errors all sit in one file, or all come out the same count, makes them
        pass against one that reports the project total per file. This is the
        one place that asserts something about the fixture, and it asserts the
        least that the measurement requires: two files, two counts."""
        by_file = lint_errors_by_file(self.root)
        self.assertGreaterEqual(
            len(by_file), 2,
            f"{WITNESS.name} carries lint errors in fewer than two files "
            f"({by_file}) — the per-file comparison below cannot fail")
        self.assertGreaterEqual(
            len(set(by_file.values())), 2,
            f"every file with errors in {WITNESS.name} carries the same "
            f"number of them ({by_file}) — a perry-conform that reported the "
            f"project total for every file would pass")

    def test_per_file_error_counts_match_perry_lints_own_findings(self):
        by_file = lint_errors_by_file(self.root)
        conform = json.loads(subprocess.run(
            ["python3", str(CONFORM), "status", "--root", str(self.root), "--json"],
            capture_output=True, text=True).stdout)

        for row in conform["files"]:
            with self.subTest(path=row["path"]):
                self.assertEqual(row["errors"], by_file.get(row["path"], 0))
        self.assertEqual(sum(r["errors"] for r in conform["files"]),
                         sum(by_file.values()),
                         "the two disagree about how many errors this project has")
        self.assertEqual(
            {r["path"] for r in conform["files"] if r["errors"]}, set(by_file),
            "the two disagree about WHICH files this project's errors are in")

    def test_declare_all_splits_the_project_exactly_where_status_does(self):
        """The concrete ADR-004 § 5 case, as a property rather than a census:
        `declare --all` declares every file `perry-conform status` reports at
        zero errors and refuses every file it reports with errors — so a
        partial declaration is partial along the line the checker draws, not
        along a list of filenames someone wrote down. Both sides are asserted
        non-empty, because a project where everything is refused and one where
        everything is declared each pass half of this by accident."""
        conform = json.loads(subprocess.run(
            ["python3", str(CONFORM), "status", "--root", str(self.root), "--json"],
            capture_output=True, text=True).stdout)
        clean = {r["path"] for r in conform["files"] if r["errors"] == 0}
        dirty = {r["path"] for r in conform["files"] if r["errors"] > 0}
        self.assertTrue(clean, "nothing in the corpus conforms")
        self.assertTrue(dirty, "everything in the corpus conforms")

        r = subprocess.run(
            ["python3", str(CONFORM), "declare", "--all",
             "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(r.returncode, 1, "a partial declaration exits 1")
        self.assertEqual({x["path"] for x in out["declared"]}, clean)
        self.assertEqual({x["path"] for x in out["refused"]}, dirty)


#: A board with exactly two errors, of two kinds, chosen so that
#: `perry-migrate` must fix one and must refuse the other:
#:
#: - `## Cadence` is missing. That is a shape error `fix_sections` repairs by
#:   adding the empty section, and nothing is invented in doing it.
#: - `T-001`'s status reads `half-solved`, which is not in the enum and is not
#:   an alias of anything in it. It is a distinction its author drew in their
#:   own words, and coercing it to `in_progress` would be asserting a fact
#:   nobody stated.
#:
#: Written here rather than committed as a project because what is under test
#: is the migrator's behaviour on a board of this shape, not any project's
#: history. `T-002` is present so the board is not one unmigratable row.
BOARD_WITH_A_ROW_MIGRATION_CANNOT_COERCE = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| T-001 | the row whose state its author named themselves | Coding Agent | half-solved | say what half-solved means | — |
| T-002 | an ordinary row | Coding Agent | in_progress | keep going | — |

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## User Input Queue

| USER-id | Needed from user | Blocks | Idle | Status |
|---|---|---|---|---|

## Top risks

- none
"""


class TestMigrationDoesNotReachTheWholeBoard(unittest.TestCase):
    """TASK-047, cost 1 — the residue the `enforce` flip ships with.

    ADR-004 says flip the gate to `enforce` once the migration exists, and
    TASK-047 flipped it. What this pins is what that flip therefore costs: a
    board can carry a shape error `perry-migrate` **must not** fix, because
    fixing it would mean choosing a meaning its author did not choose. The
    file then stays refused until a human edits it and declares it. That is a
    door needing a hand rather than a wall — the refusal names `perry-lint`
    and `perry-conform declare` as well as `perry-migrate` — but it is a real
    cost and it is stated, not discovered.

    It used to be measured on `~/proj/gimegime-pmo`, whose board carried a row
    reading `Status: 半解`, and it therefore measured nothing on any other
    machine. The row is now written by the test, which is the stronger claim
    in any case: the old assertions were "*that* project still has a residue",
    and these are "a board of this shape gets partly migrated and is not
    written" — true of the project too, and checkable everywhere.

    Read-only about the fixture: a dry run, on a board this class wrote, and
    it asserts nothing about which residual finding remains — only that one
    does, and that the migration got strictly closer without arriving. This
    goes RED the day `perry-migrate` learns to coerce a status nobody defined,
    which is the day the row in `bin/README.md` needs re-reading rather than
    deleting."""

    def project(self) -> Project:
        return Project(board=BOARD_WITH_A_ROW_MIGRATION_CANNOT_COERCE)

    def plan_for_the_board(self, p: Project) -> dict:
        r = subprocess.run(
            ["python3", str(MIGRATE), "--root", str(p.root),
             "--only", "BOARD.md", "--json"],
            capture_output=True, text=True, timeout=600)
        plan = json.loads(r.stdout)
        self.assertIn("files", plan, plan)
        return next(f for f in plan["files"] if f["path"] == "BOARD.md")

    def test_the_migration_plan_for_the_board_does_not_reach_zero(self):
        board = self.plan_for_the_board(self.project())
        self.assertGreater(board["before_errors"], 0,
                           "the board this test wrote is already conformant — "
                           "it no longer measures anything")
        self.assertGreater(
            board["after_errors"], 0,
            "perry-migrate now takes this board to zero errors, which means it "
            "coerced a status its author invented. Cost 1 in bin/README.md "
            "§ The switch-over checklist is either gone or wrong — the flip "
            "itself already happened (TASK-047), so nothing about DEFAULT_MODE "
            "needs revisiting, but the residue this pins does.")
        self.assertLess(
            board["after_errors"], board["before_errors"],
            "the plan fixed nothing at all, so 'does not reach zero' is true "
            "for the wrong reason — migration is not partial here, it is inert")
        self.assertFalse(board["writable"],
                         "a plan with residual errors must not be applied — "
                         "ADR-004 guarantee 5, partial migration is per file")

    def test_the_residue_is_the_cell_no_one_may_choose_a_meaning_for(self):
        """Names which finding survives, so the cost above can be checked
        rather than trusted. Deliberately not asserted by the test above: that
        one is about the arithmetic of a partial migration, and would still be
        making its point if the residue were some other rule."""
        board = self.plan_for_the_board(self.project())
        rules = {f["rule"] for f in board["residual"]}
        self.assertEqual(rules, {"bad-enum"}, board["residual"])
        self.assertIn("half-solved",
                      " ".join(f["message"] for f in board["residual"]))
        self.assertEqual(
            [c["kind"] for c in board["changes"]], ["section-added"],
            "the half of the board migration CAN fix stopped being fixed")

    def test_that_the_store_is_read_while_the_board_is_unwritable(self):
        """Conformance gates projection writes, not reads of canonical tasks.

        The count is taken from the board this test wrote — every row of it
        comes back, not "more than twenty", which was a census of the author's
        project and would have gone red the week it was triaged."""
        p = self.project()
        expected = sum(1 for line in BOARD_WITH_A_ROW_MIGRATION_CANNOT_COERCE
                       .split("\n") if line.startswith("| T-"))
        self.assertEqual(expected, 2, "the board constant lost a row")

        rc, out, _ = p.run(CONFORM, "status", enforce=True)
        board = next(f for f in out["files"] if f["path"] == "BOARD.md")
        self.assertGreater(board["errors"], 0,
                           "the board conforms, so nothing here is gated and "
                           "the read below proves nothing")

        seeded = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-tasks"), "write",
             "--from-board", "--root", str(p.root)],
            capture_output=True, text=True, timeout=300)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
        r = subprocess.run(
            ["python3", str(TASK), "list", "--all",
             "--root", str(p.root), "--json"],
            capture_output=True, text=True,
            env=dict(os.environ, PERRY_CONFORMANCE="enforce"), timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(json.loads(r.stdout)["tasks"]), expected,
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
    """**Asserted on the gate, and it used to be asserted through a tool.**

    The pair below ran `perry-decide bootstrap`, which created `DECISIONS.md`
    — the one shipped case of a tool creating the very file it gated on.
    TASK-235 deleted that file, so no shipped tool has that shape any more and
    the CLI half of these two has no stand-in: `perry-task` refuses on a
    missing board, `perry-goals link` refuses on a missing register, and
    `perry-goals commit` refuses on a missing `OKR.md`. Substituting one of
    those would test a refusal, which is the opposite property.

    So the gate is called directly. What is under test is `verdict` and
    `gate` — a file that is not there yet is `absent`, `absent` is allowed, and
    the file appearing does not declare it — and that is what the tools were
    only ever a delivery mechanism for.
    """

    def test_an_absent_file_is_allowed_rather_than_refused(self):
        """There is no shape to conform to before a file exists, and refusing
        here would make every lane unreachable on a new project."""
        p = Project(board=None)
        self.assertFalse((p.root / "BOARD.md").exists())
        self.assertEqual(p.verdict("BOARD.md").state, C.ABSENT)
        gate = C.gate(p.root, p.root, "BOARD.md", tool="perry-task",
                      root_arg=None)
        self.assertTrue(gate.ok, gate.message)

    def test_the_file_appearing_does_not_declare_it(self):
        """…and Perry did not declare it on the user's behalf. The next write
        asks, and the refusal is the one-command kind."""
        p = Project(board=None)
        (p.root / "BOARD.md").write_text(BOARD)
        self.assertFalse(p.marker().exists())
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 1)
        self.assertIn("perry-conform declare BOARD.md", out["refused"])


# ── 9 · the record itself ─────────────────────────────────────────────────


class TestTheRecordIsReadHonestly(unittest.TestCase):

    def test_a_row_that_cannot_be_read_is_reported_not_treated_as_absent(self):
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        p.marker().write_text(p.line().replace('"shape_version": 2',
                                                '"shape_version": "v-two"'))
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
        p.marker().write_text(p.line().replace('"shape_version": 2',
                                                '"shape_version": "v-two"'))
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
        p.run(CONFORM, "declare", "BOARD.md")
        p.run(CONFORM, "declare", ".perry/hook.md")
        stored = C.P.read_conformance(p.root).declarations
        self.assertIn("BOARD.md", stored)
        self.assertIn(".perry/hook.md", stored)

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


# ── 10b · a decorated row is not a declaration, and never becomes one ──────
#
# **TASK-241's suite, moved to the door it now guards, not deleted.**
#
# Every test below was written against `read_conformance` while the record was
# `.perry/conformance.md`. TASK-234 made the record a store, and its subject
# MOVED rather than disappeared: the markdown is still on disk in every project
# written before the conversion, it is still read exactly once — by
# `perry-conform migrate`, through `read_legacy_conformance`, which is TASK-241's
# reader unchanged — and a row that fools that reader is now laundered into a
# JSON declaration nothing downstream can tell from a real one. That is TASK-241's
# harm at a ONE-WAY DOOR instead of at a re-runnable read.
#
# So each test keeps its shape and gains a second assertion. Both layers matter
# and each can go red alone:
#
#   1. the READER still refuses the row — the round trip and the fence rule,
#      unchanged, now measured on `read_legacy_conformance`;
#   2. the CONVERSION refuses the FILE — the whole-file fixed point, which is
#      what catches the shapes the per-row round trip is blind to BY
#      CONSTRUCTION (a fenced row, and TASK-248's `<pre>` / HTML comment /
#      `<details>` row, are byte-for-byte genuine rows).
#
# Layer 2 is not a substitute for layer 1: a fixed-point check with the reader
# reverted would convert a decorated row that round-trips to itself, which is
# exactly `test_an_asterisked_path_reads_exactly_as_it_did_before` below.


#: Every `perry-<tool> …` a message hands back, as a reader would copy it —
#: through the closing backtick, the end of the line, or the sentence's full
#: stop, whichever comes first.
_NAMED_COMMAND = re.compile(r"perry-[a-z][a-z-]*(?:[ ][^\n`*]*)?")


def commands_named(message: str) -> list[str]:
    """The commands a refusal hands back, extracted from the TEXT.

    Not from a list the test also wrote: the whole defect this closes was an
    assertion that constructed what it expected and so could not see what was
    printed. Only the two shapes this codebase uses to hand back a command are
    read — an indented line of its own, and a backticked span after `run` /
    `with` / `is` — so prose that merely NAMES a tool ("`perry-conform declare`
    would have written") is not mistaken for an instruction.
    """
    out = []
    for line in message.split("\n"):
        if line.startswith("    ") and line.strip().startswith("perry-"):
            out.append(line.strip())
    for m in re.finditer(r"\b(?:run|with|is|try|use)[ :]+`(perry-[^`]+)`",
                         message, re.IGNORECASE):
        out.append(m.group(1).strip())
    return out


def assert_every_command_carries(case, message: str, root, why: str) -> None:
    """**A refusal that names a command must name it with the root the caller
    used.** This is the class, not the instance.

    `perry-conform` propagates the invocation's `--root` into every branch of
    `message_for` through `_root_flag()`, and did not into either refusal in
    `migrate_record`. The consequence is worse than a command that errors: the
    dropped-root command exits 0 and reports "nothing to convert — already
    this project's record", about a project the reader never asked about,
    while their own record stays unconverted and keeps gating every write.
    """
    named = commands_named(message)
    case.assertTrue(named,
                    f"{why}: no command was found in the refusal, so this "
                    f"assertion is vacuous — the extractor or the message "
                    f"changed shape:\n{message}")
    for cmd in named:
        case.assertIn(
            f"--root {root}", cmd,
            f"{why}: the refusal hands back {cmd!r}, which drops the "
            f"`--root {root}` the reader's own invocation carried. Run from "
            f"where the reader is standing it exits 0 with a success-shaped "
            f"sentence about a different project.")


class TestADecoratedRowIsNotADeclaration(unittest.TestCase):
    """`read_legacy_conformance` stripped each cell with ``strip("` ")``, so a
    row whose path cell was in BACKTICKS parsed to the same plain key as a row a
    person had declared on purpose. Same for an INDENTED row (`_CONFORMANCE_ROW`
    is `^\\s*\\|`) and for a row inside a ``` FENCE (this reader tracked none).

    Found by the `TASK-226` V4 reviewer, who measured the harm: one hand-written
    backticked row flips a real file from `undeclared` to **conformant**, and
    because the writer rewrote the whole record from the parsed declarations,
    the next legitimate declare **laundered** it into a canonical row nothing
    downstream can tell from a real one. The record's own header invited hand
    editing — *"Delete a row to withdraw a declaration"* — so this is reachable
    by design, not contrivance.

    **THREE SHAPES, THREE TESTS.** One test covering all three would still pass
    with two of the three regressed, and the three are stopped by two different
    mechanisms — the row round trip catches decoration written INSIDE the row,
    and only fence tracking catches the fenced row, which is byte-for-byte
    identical to a genuine one.

    **Each test carries its own control.** It first plants the UNDECORATED row
    and asserts that it really does read as a declaration and convert cleanly —
    so the trap is proved live in the same test that proves it closed, and none
    of these can pass because the reader stopped reading, because the fixture
    stopped being lint-clean, or because the row was malformed for some fourth
    reason.

    **Shape 3 has more than one spelling, and the first fix only closed one.**
    That fix was a boolean toggle flipped by any fence-looking line, so a fence
    NESTED in another — which is how every markdown document that shows a fenced
    block writes it — turned tracking off and gave the row back. Six further
    spellings were measured live on that fix (§ "the fence has to be markdown's
    fence" below) and each has its own test, because a single test over all of
    them would pass with five regressed.
    """

    VER = C.shape_version(SCHEMA)

    def plant(self, body: str) -> tuple:
        """A project whose MARKDOWN record is exactly the real header plus
        `body`, and what the legacy reader makes of it.

        Returns `(project, keys honoured, number of unreadable rows)` — the two
        halves of what the conversion would be allowed to carry across."""
        p = Project()
        p.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n" + body)
        rec = C.P.read_legacy_conformance(p.root)
        self._keep = p
        return p, sorted(rec.declarations), len(rec.unreadable)

    def canonical(self) -> str:
        return f"| BOARD.md | {self.VER} | 2026-08-28 | declare |\n"

    def assert_conversion_refuses(self, p, why: str, names: str | None = None):
        """`perry-conform migrate` refuses, NOTHING was written, **and the
        refusal names the offending line and a command that fixes it.**

        Exit code and both files, not just the message: a crash and a refusal
        both print no declaration, and a conversion that wrote the store and
        then reported a problem would have already gone through the door.

        **The last two assertions were missing and that is why the FAIL
        happened.** This helper checked only `"refused" in out`, so a refusal
        that named `perry-conform status` — a command that computes no diff and
        reports nothing about the markdown's contents — shipped past the whole
        suite. `bin/perry-conform § message_for` states the standard in the
        same file the violation was in: *"a gate that says 'not conformant' and
        stops is a wall — every branch here ends in a command the reader can
        run."* Applying it here is what the helper is for.

        `names` is the exact text the reader has to find in their file, when
        the caller knows it. A refusal that prints a diff of the WRONG lines is
        a refusal that passes every assertion above.
        """
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 1, f"{why}: the conversion did not refuse ({out})")
        self.assertIsInstance(out, dict, f"migrate printed no JSON: {out} {err}")
        self.assertIn("refused", out, why)
        self.assertFalse(p.marker().exists(),
                         f"{why}: the store was written anyway")
        self.assertTrue(p.legacy_marker().exists(),
                        f"{why}: the markdown record was deleted anyway")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)

        message = out["refused"]
        self.assertIn("perry-conform migrate", message,
                      f"{why}: the refusal names no command to run — a wall")
        # **Named is not enough: it has to be the command THIS reader can
        # run.** Every invocation of this helper runs with `--root <tmpdir>`,
        # and for three rounds every one of them asserted only that some
        # `perry-conform migrate` appeared in the message — which was true, and
        # was not about the reader's situation in the test. The shipped
        # refusal named the command with the root DROPPED, so a reader who
        # copied it got `rc=0` and "nothing to convert" about a different
        # project. Checked generically rather than for `migrate` alone: a
        # refusal that grows a NEW command tomorrow is caught by the same
        # assertion.
        assert_every_command_carries(self, message, p.root, why)
        self.assertNotIn(
            "perry-conform status", message,
            f"{why}: the refusal points at `status`, which computes no diff "
            f"and reports nothing about the markdown's contents")
        # **The refusal must LOCATE the problem**, by one of the two shapes
        # this tool has: a numbered line (the unreadable-rows branch, which
        # always did) or a unified diff (the fixed-point branch, which did not
        # and is the FAIL this helper failed to catch).
        self.assertRegex(
            message,
            r"(--- " + re.escape(C.P.CONFORMANCE_LEGACY_FILE) + r"|line \d+:)",
            f"{why}: the refusal locates nothing — neither a line number nor a "
            f"diff — so the way forward is reading the file by eye while "
            f"`declare`, `perry-migrate apply` and every gate call site refuse")
        if names is not None:
            self.assertIn(names, message,
                          f"{why}: the refusal does not quote the offending "
                          f"line {names!r} — locating the WRONG line passes "
                          f"every other assertion here")

    # ── the control, shared by all three ──────────────────────────────────

    def assert_trap_would_have_worked(self):
        """The undecorated row. If this stops reading as a declaration and
        converting cleanly, every test below is vacuous — so every test below
        runs it first."""
        p, keys, unreadable = self.plant(self.canonical())
        self.assertEqual(
            (keys, unreadable), (["BOARD.md"], 0),
            "the control row no longer reads as a declaration — the tests "
            "below would pass for the wrong reason")
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0, f"the control conversion refused: {out} {err}")
        self.assertEqual(p.verdict("BOARD.md").state, C.CONFORMANT,
                         "the control row did not survive the conversion — "
                         "the tests below would pass for the wrong reason")

    # ── shape 1 ───────────────────────────────────────────────────────────

    def test_a_backticked_path_cell_is_not_a_declaration(self):
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            f"| `BOARD.md` | {self.VER} | 2026-08-28 | declare |\n")
        self.assertEqual(keys, [], "a backticked path cell still declares a file")
        self.assertEqual(unreadable, 1,
                         "the row was dropped silently instead of reported")
        self.assert_conversion_refuses(
            p, "a backticked path cell", names="| `BOARD.md` |")

    # ── shape 2 ───────────────────────────────────────────────────────────

    def test_an_indented_row_is_not_a_declaration(self):
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant("   " + self.canonical())
        self.assertEqual(keys, [], "an indented row still declares a file")
        self.assertEqual(unreadable, 1,
                         "the row was dropped silently instead of reported")
        self.assert_conversion_refuses(
            p, "an indented row", names=self.canonical().strip())

    # ── shape 3 ───────────────────────────────────────────────────────────

    def test_a_row_inside_a_code_fence_is_not_a_declaration(self):
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant("```\n" + self.canonical() + "```\n")
        self.assertEqual(keys, [],
                         "a row inside a code fence still declares a file")
        self.assertEqual(unreadable, 1,
                         "the row was dropped silently instead of reported")
        self.assert_conversion_refuses(
            p, "a fenced row", names=self.canonical().strip())

    # ── the fence has to be markdown's fence ──────────────────────────────
    #
    # Every test in this block was measured GREEN-side-up on the first version
    # of the guard — that is, the row declared `BOARD.md` and `unreadable` was
    # 0, exactly as if no guard existed — because the toggle closed on a line
    # that markdown does not close on. They are six different ways to write the
    # same lie, and they get six tests.

    def test_a_backtick_fence_nested_in_a_tilde_fence_is_still_a_fence(self):
        """`~~~` opens; the ``` ``` ``` under it is CONTENT, not a close — a
        different delimiter character cannot close. This is the plainest way a
        document shows a fenced block: wrap it in the other fence character."""
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "~~~\n```\n" + self.canonical() + "```\n~~~\n")
        self.assertEqual(keys, [],
                         "a backtick fence inside a tilde fence closed it")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a backtick fence in a tilde fence",
            names=self.canonical().strip())

    def test_a_three_backtick_line_inside_a_four_backtick_fence_is_still_a_fence(self):
        """The other plain way: open with a LONGER run. A close must be at
        least as long as the open, so ``` inside ```` is content."""
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "````\n```\n" + self.canonical() + "````\n")
        self.assertEqual(keys, [], "a short fence run closed a longer fence")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a short run inside a longer fence",
            names=self.canonical().strip())

    def test_a_tilde_fence_nested_in_a_backtick_fence_is_still_a_fence(self):
        """The mirror of the first, and it is not the same test: the toggle was
        symmetric but the rule is not, so a fix that keyed on the character
        could close one direction and leave the other open."""
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "```\n~~~\n" + self.canonical() + "~~~\n```\n")
        self.assertEqual(keys, [],
                         "a tilde fence inside a backtick fence closed it")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a tilde fence in a backtick fence",
            names=self.canonical().strip())

    def test_a_fence_line_with_trailing_text_does_not_close_the_fence(self):
        """An info string is allowed on the OPENING fence only. ```` ```x ````
        inside an open fence is a content line — and it is exactly what an
        example showing an opening fence looks like."""
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "```\n```x\n" + self.canonical() + "```\n")
        self.assertEqual(keys, [],
                         "a fence line with an info string closed a fence")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a fence line with an info string",
            names=self.canonical().strip())

    def test_a_four_space_indented_fence_line_does_not_close_the_fence(self):
        """A closing fence may be indented at most three spaces. At four it is
        content — which is how a fenced block nested in a list item or a
        blockquote-free indent appears."""
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "```\n    ```\n" + self.canonical() + "```\n")
        self.assertEqual(keys, [],
                         "a four-space-indented fence line closed a fence")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a four-space-indented fence line",
            names=self.canonical().strip())

    def test_a_whole_table_inside_a_nested_fence_declares_nothing(self):
        """The shape that decided the mechanism.

        A document does not show one bare row; it shows the table — header,
        delimiter, row. This is why the reader tracks FENCES and not "rows in
        the contiguous run under the `| File |` header": measured, that rule
        closes every bare-row shape above and then reads THIS one as a
        declaration, because the fenced example brings its own header and so
        starts its own run. Both rows must be refused, and reported."""
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "~~~\n```\n"
            "| File | Shape version | Declared | Route |\n"
            "|---|---|---|---|\n" + self.canonical()
            + "```\n~~~\n")
        self.assertEqual(keys, [],
                         "an example table in a nested fence declared a file")
        self.assertEqual(unreadable, 2,
                         "the fenced rows were dropped silently, not reported")
        self.assert_conversion_refuses(
            p, "an example table in a nested fence",
            names=self.canonical().strip())

    # ── and the two the corner sweep says must stay shut ──────────────────
    #
    # CommonMark says neither of these OPENS a fence. This reader opens on both
    # anyway, deliberately: an unsure line costs a loud `unreadable` if we treat
    # it as a fence and a false `conformant` if we do not, and this is the file
    # that gates every write. Named, because "be liberal about opening" is the
    # half of the rule that a later tidy-up toward strict CommonMark would
    # delete without noticing it had reopened anything.

    def test_a_four_space_indented_fence_still_opens_one(self):
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "    ```\n" + self.canonical() + "    ```\n")
        self.assertEqual(keys, [],
                         "a four-space-indented fence stopped opening one")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a four-space-indented opener",
            names=self.canonical().strip())

    def test_a_backtick_fence_with_a_backtick_in_its_info_string_still_opens_one(self):
        self.assert_trap_would_have_worked()
        p, keys, unreadable = self.plant(
            "```a`b\n" + self.canonical() + "```\n")
        self.assertEqual(keys, [],
                         "a backtick in the info string stopped opening a fence")
        self.assertEqual(unreadable, 1)
        self.assert_conversion_refuses(
            p, "a backtick in the info string",
            names=self.canonical().strip())

    # ── the shape the round trip is blind to BY CONSTRUCTION (TASK-248) ────

    def test_a_canonical_row_inside_an_html_block_is_not_carried_across(self):
        """**TASK-248's shape, and the reason the conversion is a FILE-level
        fixed point rather than the per-row round trip.**

        A bare canonical row inside `<pre>`, an HTML comment or `<details>` is
        byte-for-byte a genuine row, so the round trip honours it and always
        did: measured `conformant` with 0 unreadable at the fork point, at
        TASK-241 round 1 and at round 2. It is not a regression and no
        predicate over the row can see it — what makes it not a declaration is
        what surrounds it, exactly as for a fenced row.

        Three spellings, one test each would be better and one test here is
        honest about what it measures: they are one mechanism away, and the
        mechanism is that the lines around the row are not in `render_legacy`'s
        output. Each spelling is asserted separately below so a fix that closed
        one would still go red on the other two."""
        for name, wrap in (
                ("<pre>", "<pre>\n%s</pre>\n"),
                ("an HTML comment", "<!--\n%s-->\n"),
                ("<details>", "<details>\n%s</details>\n")):
            with self.subTest(html=name):
                p, keys, unreadable = self.plant(wrap % self.canonical())
                # The reader HONOURS it — stated, not hidden, because it is
                # what makes the file-level check load-bearing rather than
                # belt-and-braces.
                self.assertEqual(
                    keys, ["BOARD.md"],
                    f"a row inside {name} stopped reading as a row — then this "
                    f"test no longer measures the shape it exists for")
                self.assertEqual(unreadable, 0)
                self.assert_conversion_refuses(
                    p, f"a row inside {name}", names="-" + wrap.split("%s")[0].strip())

    # ── a cell that cannot be written back at all ─────────────────────────

    def test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed(self):
        """`read_legacy_conformance` splits the record on `"\\n"`; `render_row`
        refuses through `line_break_at`, which uses `str.splitlines()` —
        **eleven** boundaries, not one. So a path cell holding `U+2028` sits
        inside a single line for the reader and makes the canonical form
        unwritable.

        Without the `except UnrenderableCell` the round trip raises straight out
        of the reader and `perry-conform` dies with a traceback on a
        hand-edited record — on the tool the enforce gate calls. This test
        exists because the RESULT for round 1 claimed nothing it added could be
        deleted with the suite unchanged, and a reviewer deleted this guard with
        the suite unchanged. Asserts the exit code of BOTH surfaces that read
        the file: a crash and a refusal both produce no declaration."""
        p, keys, unreadable = self.plant(
            f"| BOARD .md | {self.VER} | 2026-08-28 | declare |\n")
        self.assertEqual(keys, [])
        self.assertEqual(unreadable, 1,
                         "the unwritable row was dropped instead of reported")
        rc, out, err = p.run(CONFORM, "status")
        self.assertEqual(rc, 0, f"status crashed on the record: {err}")
        self.assertIsInstance(out, dict, f"status printed no JSON: {out} {err}")
        self.assert_conversion_refuses(p, "a cell that cannot be written back")

    # ── the harm the shapes lead to ───────────────────────────────────────

    def test_a_nested_fence_row_is_not_laundered_by_the_next_declare(self):
        """The laundering came back with the nesting, so it is measured again
        against the shape that reopened it — and against the writer that can
        still do it, which is the conversion `declare` runs before it writes.

        The declare here is of a DIFFERENT file — a legitimate one — because
        that is the whole point: the user does something entirely ordinary and
        the record quietly canonicalises a claim nobody made."""
        p, _, _ = self.plant(
            "~~~\n```\n" + self.canonical() + "```\n~~~\n")
        rc, out, err = p.run(CONFORM, "declare", ".perry/hook.md")
        self.assertEqual(rc, 1, f"the declare went through: {out} {err}")
        self.assertIn("refused", out)
        self.assertFalse(p.marker().exists(),
                         "the fenced row was laundered into a store line")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)
        self.assertEqual(p.verdict(".perry/hook.md").state, C.UNDECLARED,
                         "a record it refuses to convert must not be half "
                         "converted with the new declaration on top")

    def test_a_planted_row_is_not_laundered_by_the_next_declare(self):
        """The second half of the measured defect, and the worse half: after
        the rewrite the row is indistinguishable from one a person wrote."""
        p, _, _ = self.plant(
            f"| `BOARD.md` | {self.VER} | 2026-08-28 | declare |\n")
        rc, out, err = p.run(CONFORM, "declare", ".perry/hook.md")
        self.assertEqual(rc, 1, f"the declare went through: {out} {err}")
        self.assertFalse(p.marker().exists(),
                         "the decorated row was laundered into a store line")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)

    # ── and the case that must NOT change ─────────────────────────────────

    def test_an_asterisked_path_reads_exactly_as_it_did_before(self):
        """``strip("` ")`` never removed asterisks, so `| **BOARD.md** |` has
        always parsed to the decorated key `**BOARD.md**` — inert, because no
        key `state_files()` produces carries asterisks. TASK-226 filed it as an
        observation and it stays one. The guard is about rows that reach a
        REAL key; widening it to reject asterisks too would be a different
        change, and the round trip deliberately lets this row through because
        it is already exactly what the writer would write for that key.

        **This is also what proves the file-level fixed point is not a
        substitute for the row round trip.** This row survives the file check —
        the file IS what `render_legacy` would write — so the only thing
        standing between a decorated row and a real key is the round trip."""
        p, keys, unreadable = self.plant(
            f"| **BOARD.md** | {self.VER} | 2026-08-28 | declare |\n")
        self.assertEqual(keys, ["**BOARD.md**"])
        self.assertEqual(unreadable, 0)
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0, f"the conversion refused a fixed point: {out}")
        self.assertEqual(list(C.P.read_conformance(p.root).declarations),
                         ["**BOARD.md**"],
                         "the inert key stopped travelling across unchanged")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED,
                         "the asterisked row started flipping a real verdict")

    def test_a_bolded_header_row_is_still_not_a_row(self):
        """`squash` answers this and answered it before TASK-241 (TASK-050).
        Here so that a guard added ABOVE the header check — where it would
        report the header as an unreadable row — cannot land green."""
        p = Project()
        p.legacy_marker().write_text(
            "# Perry conformance\n\n"
            "| **File** | **Shape version** | **Declared** | **Route** |\n"
            "|---|---|---|---|\n" + self.canonical())
        rec = C.P.read_legacy_conformance(p.root)
        self.assertEqual(list(rec.declarations), ["BOARD.md"])
        self.assertEqual(rec.unreadable, [])
        # And the conversion still refuses it, because a hand-edited header is
        # not what the writer wrote — two independent reasons this file is not
        # carried across, and neither one hides the other.
        self.assert_conversion_refuses(p, "a hand-edited header")

    def test_perrys_own_record_is_read_without_a_single_refusal(self):
        """The guard is strict, and a strict guard that refuses the real file
        would take the enforce gate down for this repository. Every line of the
        shipped record must still read — and the markdown it was converted from
        must be gone, because two registers for this fact is the defect
        TASK-234 exists to remove."""
        rec = C.P.read_conformance(PERRY_HOME)
        self.assertTrue(rec.exists, "Perry's own record was never converted")
        self.assertEqual(rec.unreadable, [],
                         "the reader refuses lines in Perry's own record")
        self.assertGreater(len(rec.declarations), 0)
        self.assertIsNone(rec.stray_legacy,
                          "the markdown record is still on disk beside the "
                          "store — two registers for the gating fact")


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



# ── 12 · the record is a store (TASK-234) ─────────────────────────────────


class TestTheRecordIsAStore(unittest.TestCase):
    """DESIGN-013 § 5.1 on the cheapest file it applies to.

    The record was 23 rows of four regular columns under a header that was
    already a constant in the writer, with no per-row prose at all — so the
    rule's document side has nothing to weigh. What the table cost was a
    parser, and the parser is where TASK-241 and TASK-248 lived.
    """

    def stored(self, p) -> list[dict]:
        return [json.loads(l) for l in p.marker().read_text().split("\n")
                if l.strip()]

    def test_one_json_object_per_line_with_the_declared_fields(self):
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        rows = self.stored(p)
        self.assertEqual(len(rows), 1)
        self.assertEqual(list(rows[0]), list(C.P.CONFORMANCE_FIELDS),
                         "the store's field order is not the declared one")
        self.assertEqual(rows[0]["kind"], C.P.CONFORMANCE_KIND)
        self.assertEqual(rows[0]["path"], "BOARD.md")
        self.assertIsInstance(rows[0]["shape_version"], int,
                              "the version is a JSON number, not a string — "
                              "storing it as text would put back the ambiguity "
                              "the table's `\\d+` had to police")

    def test_a_declaration_records_who_wrote_it_and_when(self):
        """**The point of the conversion, not a bonus for having done it.**

        `TASK-226` — where did this row come from — was an investigation
        because four regular columns could not answer it. A record that can is
        the reason DESIGN-013 § 5.1 was worth applying to this file."""
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        row = self.stored(p)[0]
        self.assertEqual(row["writer"], "perry-conform declare")
        self.assertTrue(row["recorded_at"], "the moment was not recorded")
        self.assertIsNotNone(
            __import__("datetime").datetime.fromisoformat(row["recorded_at"]),
            "the moment is not an ISO timestamp")
        self.assertNotEqual(
            row["recorded_at"], row["declared"],
            "`recorded_at` is the MOMENT and `declared` is the day — a store "
            "that made them the same string would have carried nothing new")

    def test_a_malformed_line_does_not_void_its_neighbours(self):
        """**Per line, not all-or-nothing**, and this is TASK-241 round 2's
        measurement carried across the format change: under a whole-file rule
        one stray line voids all 23 of Perry's real declarations and takes the
        enforce gate down with them. Here it voids one and says which."""
        p = Project()
        p.marker().parent.mkdir(exist_ok=True)
        p.marker().write_text(
            "{ not json at all\n"
            + p.line("BOARD.md")
            + p.line(".perry/hook.md"))
        rec = C.P.read_conformance(p.root)
        self.assertEqual(sorted(rec.declarations), [".perry/hook.md", "BOARD.md"],
                         "a malformed line voided the lines around it")
        self.assertEqual([n for n, _ in rec.unreadable], [1],
                         "the malformed line was dropped silently")
        self.assertEqual(p.verdict("BOARD.md").state, C.CONFORMANT)

    def test_a_line_that_is_not_a_declaration_is_reported_not_skipped(self):
        """Four shapes, one property: refused, and said out loud. A line that
        is neither `declared` nor `absent` must not read as either."""
        for name, line in (
                ("not JSON", "{ not json at all\n"),
                ("not an object", '["BOARD.md", 2]\n'),
                ("a foreign kind", '{"kind": "setting", "path": "BOARD.md", '
                                   '"shape_version": 2, "declared": "2026-08-28", '
                                   '"route": "declare"}\n'),
                ("a string version", '{"kind": "declaration", "path": "BOARD.md", '
                                     '"shape_version": "2", "declared": '
                                     '"2026-08-28", "route": "declare"}\n')):
            with self.subTest(shape=name):
                p = Project()
                p.marker().parent.mkdir(exist_ok=True)
                p.marker().write_text(line)
                rec = C.P.read_conformance(p.root)
                self.assertEqual(rec.declarations, {}, name)
                self.assertEqual(len(rec.unreadable), 1,
                                 f"{name} was dropped silently")
                self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)

    def test_two_lines_for_one_path_are_unreadable_rather_than_last_one_wins(self):
        """They disagree about when the file was declared. A reader that
        silently picked one would make the record's answer depend on line
        order, which is the shape of a defect nobody can reproduce."""
        p = Project()
        p.marker().parent.mkdir(exist_ok=True)
        p.marker().write_text(p.line(declared="2026-08-01")
                              + p.line(declared="2026-08-28"))
        rec = C.P.read_conformance(p.root)
        self.assertEqual(len(rec.unreadable), 1)
        self.assertEqual(rec.declarations["BOARD.md"].declared, "2026-08-01",
                         "the SECOND line won, so the record's answer depends "
                         "on the order somebody typed two lines in")

    def test_a_blank_line_is_layout_and_not_a_finding(self):
        """A trailing newline is how every jsonl this project writes ends, and
        a store that reported its own last byte as unreadable would report a
        finding against every correct file."""
        p = Project()
        p.marker().parent.mkdir(exist_ok=True)
        p.marker().write_text("\n" + p.line() + "\n\n")
        rec = C.P.read_conformance(p.root)
        self.assertEqual(rec.unreadable, [])
        self.assertEqual(list(rec.declarations), ["BOARD.md"])


class TestTheRecordIsNotDeclarableAboutItself(unittest.TestCase):
    """`schema/state-schema.json` says the record is deliberately NOT a
    `files[]` entry: *"it is a record of the user's decisions ABOUT state, not
    state, and listing it here would make it declarable-conformant about
    itself."* TASK-234 had to carry that across a format change EXPLICITLY
    rather than let it lapse, and it is what makes the conversion possible at
    all — the gate has no opinion about a file that is not a `files[]` entry,
    so the write that migrates the record needs no exemption.
    """

    def test_the_record_is_not_a_files_entry(self):
        paths = {spec["path"] for spec in SCHEMA["files"]}
        for name in (C.P.CONFORMANCE_FILE, C.P.CONFORMANCE_LEGACY_FILE):
            with self.subTest(record=name):
                self.assertNotIn(
                    name, paths,
                    f"{name} became a files[] entry, so it is now declarable "
                    f"conformant about itself and the write that migrates it "
                    f"is gated on its own verdict")

    def test_no_writer_gates_on_the_record(self):
        """The bootstrap property, measured rather than asserted: `state_files`
        never yields the record, so no `gate()` call can ever be about it."""
        p = Project()
        p.run(CONFORM, "declare", "BOARD.md")
        keys = [k for k, _, _ in
                C.state_files(p.root, p.root, SCHEMA)]
        self.assertIn("BOARD.md", keys, "the fixture yields no files at all")
        for name in (C.P.CONFORMANCE_FILE, C.P.CONFORMANCE_LEGACY_FILE):
            self.assertNotIn(name, keys)
        self.assertEqual(C.verdict(p.root, p.root, C.P.CONFORMANCE_FILE,
                                   SCHEMA).state, C.ABSENT,
                         "the record has a verdict of its own")

    def test_the_record_is_not_a_claim_of_its_own_and_does_not_need_one(self):
        """The SEPARATE question, with its own answer (TASK-234).

        `claims[]` asks what territory Perry occupies in someone else's
        project, and `.perry/` is already claimed as a dir — so the store is
        covered exactly as the markdown was, which
        `TestTheRecordIsReadHonestly § test_the_record_is_not_reported_as_
        someone_elses_file` measures. An entry of its own would add nothing the
        collision check can see and would add a seventh store to the six that
        `perry/phase/003-linkage.md`'s KR1, KR2 and KR3 are each phrased
        *"of 6"* over. Moving that denominator is the goals lane's decision,
        not a side effect of a format change."""
        claimed = {c["path"] for c in SCHEMA["claims"]}
        self.assertNotIn(C.P.CONFORMANCE_FILE, claimed)
        self.assertIn(".perry/", claimed,
                      "the territory that covers the record is unclaimed")
        stores = sorted(c["path"] for c in SCHEMA["claims"]
                        if c["path"].endswith(".jsonl")
                        and c["path"] != ".perry/events.jsonl")
        self.assertEqual(
            len(stores), 6,
            f"the number of claimed stores moved to {len(stores)} ({stores}); "
            f"perry/phase/003-linkage.md's KR1, KR2 and KR3 are each phrased "
            f"'of 6' and are now wrong")


class TestTheMarkdownRecordIsConvertedOnce(unittest.TestCase):
    """Bootstrap order, which the row had to settle before any code (§ 5.1).

    A project written before TASK-234 keeps its declarations in
    `.perry/conformance.md`. The store reader does not read it — a fallback
    would be a second live register for the fact that gates every write, and
    would carry TASK-248's hole for as long as any project left the markdown in
    place. So the project is `undeclared` until it converts, and the refusal
    names `perry-conform migrate` rather than `perry-conform declare`, because
    `declare` would mint a declaration dated today over one the user made weeks
    ago.
    """

    #: **Sorted by path, because that is what the writer wrote.** The
    #: conversion's fixed point is byte-for-byte, so a record whose rows a hand
    #: has reordered is one this tool cannot say it is copying — measured here
    #: the first time this fixture was written the other way round.
    LEGACY = ("| .perry/hook.md | 2 | 2026-08-21 | declare |\n"
              "| BOARD.md | 2 | 2026-08-20 | migrate |\n")

    def legacy_project(self) -> Project:
        p = Project()
        p.legacy_marker().write_text("\n".join(C.LEGACY_HEADER) + "\n" + self.LEGACY)
        return p

    def test_the_markdown_alone_declares_nothing(self):
        p = self.legacy_project()
        self.assertEqual(C.P.read_conformance(p.root).declarations, {},
                         "the markdown is still being read as a register")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)

    def test_the_refusal_names_migrate_and_not_declare(self):
        p = self.legacy_project()
        rc, out, _ = p.run(TASK, *ADD, enforce=True)
        self.assertEqual(rc, 1)
        self.assertIn("perry-conform migrate", out["refused"])
        self.assertNotIn("perry-conform declare", out["refused"],
                         "the refusal names the command that would mint a new "
                         "declaration over the user's own")
        self.assertIn(".perry/conformance.md", out["refused"],
                      "the refusal does not say which file it is talking about")

    def test_the_conversion_carries_every_date_and_route_unchanged(self):
        p = self.legacy_project()
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0, f"{out} {err}")
        stored = C.P.read_conformance(p.root).declarations
        self.assertEqual(
            {k: (d.shape_version, d.declared, d.route) for k, d in stored.items()},
            {"BOARD.md": (2, "2026-08-20", "migrate"),
             ".perry/hook.md": (2, "2026-08-21", "declare")})
        self.assertFalse(p.legacy_marker().exists(),
                         "two registers for the gating fact")
        self.assertEqual(p.verdict("BOARD.md").state, C.CONFORMANT)

    def test_the_conversion_invents_no_provenance(self):
        """The three new fields stay EMPTY on a converted row. The markdown
        never held them, and a value stamped at conversion time would put a
        fact in the record that nobody recorded — a writer of
        `perry-conform migrate` and a moment weeks after the user decided."""
        p = self.legacy_project()
        p.run(CONFORM, "migrate")
        for row in [json.loads(l) for l in
                    p.marker().read_text().split("\n") if l.strip()]:
            self.assertEqual((row["writer"], row["recorded_at"], row["run"]),
                             ("", "", ""), row["path"])

    def test_the_conversion_declares_nothing_the_record_did_not_hold(self):
        """`SKILL.md § Conformance gate` reserves the declaration to the user.
        `migrate` is runnable by an agent precisely because it cannot mint one:
        it writes the parsed record and nothing else, so a file the markdown
        did not declare is undeclared afterwards."""
        p = self.legacy_project()
        p.run(CONFORM, "migrate")
        self.assertEqual(sorted(C.P.read_conformance(p.root).declarations),
                         [".perry/hook.md", "BOARD.md"])
        self.assertEqual(p.verdict(".perry/config.md").state, C.UNDECLARED)

    def test_declaring_converts_first_and_says_so(self):
        """The one writer of the record is the one place the conversion can
        live without becoming a second one."""
        p = self.legacy_project()
        rc, out, err = p.run(CONFORM, "declare", ".perry/config.md")
        self.assertEqual(rc, 0, f"{out} {err}")
        self.assertEqual(out["converted"]["declarations"], 2,
                         "the conversion was silent")
        stored = C.P.read_conformance(p.root).declarations
        self.assertEqual(sorted(stored),
                         [".perry/config.md", ".perry/hook.md", "BOARD.md"])
        self.assertEqual(stored["BOARD.md"].declared, "2026-08-20",
                         "the user's own date was overwritten")
        self.assertEqual(stored[".perry/config.md"].writer,
                         "perry-conform declare")

    def test_a_dry_run_converts_nothing(self):
        p = self.legacy_project()
        rc, out, _ = p.run(CONFORM, "declare", ".perry/config.md", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertFalse(p.marker().exists())
        self.assertTrue(p.legacy_marker().exists())

    def test_converting_twice_is_a_no_op_and_deletes_nothing(self):
        p = self.legacy_project()
        p.run(CONFORM, "migrate")
        before = p.marker().read_text()
        rc, out, _ = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0)
        self.assertIsNone(out["converted"])
        self.assertEqual(p.marker().read_text(), before)

    def test_a_markdown_beside_a_store_is_reported_and_not_read(self):
        """Two registers for the fact that gates every write. The store is the
        record; the markdown is named because a user editing it would be
        editing nothing and would have no way to find that out."""
        p = self.legacy_project()
        p.run(CONFORM, "migrate")
        p.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n"
            + "| .perry/config.md | 2 | 2026-08-20 | declare |\n")
        rec = C.P.read_conformance(p.root)
        self.assertEqual(rec.stray_legacy, p.legacy_marker())
        self.assertNotIn(".perry/config.md", rec.declarations,
                         "the markdown beside the store is being read")
        rc, out, _ = p.run(CONFORM, "status")
        self.assertEqual(Path(out["stray_legacy_record"]).resolve(),
                         p.legacy_marker().resolve())

    def test_a_stale_markdown_never_overwrites_a_store(self):
        """The conversion runs on a project that has NO store. A project that
        has both — a markdown restored from an old backup, a bad merge — must
        keep the store: the markdown is by definition the older record, and
        converting it again would silently roll every declaration back to
        whatever it said then. Found by mutation: nothing stopped it.
        """
        p = self.legacy_project()
        p.run(CONFORM, "migrate")
        p.run(CONFORM, "declare", ".perry/config.md")
        store = p.marker().read_text()
        self.assertIn(".perry/config.md", store)
        p.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n" + self.LEGACY)

        rc, out, err = p.run(CONFORM, "migrate")

        self.assertEqual(rc, 0, f"{out} {err}")
        self.assertIsNone(out["converted"], "the store was converted over")
        self.assertEqual(p.marker().read_text(), store,
                         "a stale markdown overwrote the store")
        self.assertTrue(p.legacy_marker().exists(),
                        "the markdown was deleted by a conversion that did "
                        "not happen")
        self.assertEqual(p.verdict(".perry/config.md").state, C.CONFORMANT,
                         "a declaration the store held was rolled back")

    def test_an_unreadable_row_is_refused_rather_than_deleted_at_the_door(self):
        """The conversion will not carry a record it cannot say it is copying,
        and refusing is the only honest answer at a one-way door: the
        alternative is a rewrite that deletes a line the user typed."""
        p = Project()
        p.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n" + self.LEGACY
            + "| OKR.md | v-two | 2026-08-20 | declare |\n")
        rc, out, _ = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 1)
        self.assertIn("will not honour", out["refused"])
        self.assertFalse(p.marker().exists())
        self.assertTrue(p.legacy_marker().exists(),
                        "the record was deleted anyway")


class TestTheRefusalNamesTheLine(unittest.TestCase):
    """**The V4 FAIL, and the standard it broke.**

    The first version of this row shipped a refusal that told the reader to run
    `perry-conform status`. Measured by the reviewer: `status` computes no
    diff, reports nothing about the markdown's contents, and names
    `perry-conform migrate` — the command that had just refused. No shipped
    surface named the offending line, in text or `--json`; `status`, `check`,
    `migrate`, `declare` and `perry-lint` were all checked. Meanwhile every
    write path on such a project is closed: `declare` calls `migrate_record`
    first and raises, `perry-migrate apply` refuses and rolls back, and all
    three gate call sites refuse for want of a store.

    So the claim *"the cost of refusing is look at your file"* was false. The
    measured cost was: read 37 lines by eye, with no tool help, while nothing
    can write. And `bin/perry-conform § message_for` states the standard in the
    same file: *"a gate that says 'not conformant' and stops is a wall — every
    branch here ends in a command the reader can run."*

    It is reachable by ordinary editing: 7 of 9 plausible hand edits refuse,
    and the edit the record's own header invites — *"delete a row to withdraw a
    declaration"* — is one of the two that survive.
    """

    HEADER = None  # set in setUp

    def record(self, body: str) -> Project:
        p = Project()
        p.legacy_marker().write_text("\n".join(C.LEGACY_HEADER) + "\n" + body)
        return p

    CANON = ("| .perry/hook.md | 2 | 2026-08-21 | declare |\n"
             "| BOARD.md | 2 | 2026-08-20 | declare |\n")

    def refusal(self, body: str) -> str:
        p = self.record(body)
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 1, f"the conversion did not refuse: {out} {err}")
        return out["refused"]

    def test_the_canonical_record_still_converts(self):
        """The control. Every test below asserts a REFUSAL, and a refusal is
        free if the conversion refuses everything."""
        p = self.record(self.CANON)
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0, f"the control record refused: {out} {err}")

    def test_deleting_a_row_still_withdraws_a_declaration(self):
        """The second control, and it is the edit the file's own header
        invites. If this ever refuses, the header is lying to the user."""
        p = self.record("| BOARD.md | 2 | 2026-08-20 | declare |\n")
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0, f"deleting a row refused: {out} {err}")
        self.assertEqual(list(C.P.read_conformance(p.root).declarations),
                         ["BOARD.md"])

    def test_the_refusal_carries_a_diff_and_not_a_command_that_computes_none(self):
        message = self.refusal(self.CANON + "\nre-declare OKR.md later\n")
        self.assertIn("--- .perry/conformance.md", message,
                      "the refusal carries no diff")
        self.assertIn("+++ what Perry reads out of it", message)
        self.assertIn("-re-declare OKR.md later", message,
                      "the diff does not name the line the reader must delete")
        self.assertIn("perry-conform migrate", message,
                      "the refusal names no command to run")
        self.assertNotIn("perry-conform status", message,
                         "the refusal still points at a command that computes "
                         "no diff and says nothing about this file")

    def test_the_diff_says_which_direction_is_which(self):
        """A hunk with no legend is a hunk the reader has to guess at."""
        message = self.refusal(self.CANON + "stray\n")
        self.assertIn("`-` is your file", message)
        self.assertIn("`+` is what Perry reads out of it", message)

    def test_each_plausible_hand_edit_is_located_by_the_diff(self):
        """One subTest per edit, so a fix that located one would still go red
        on the others."""
        for name, body, must_name in (
                ("a trailing blank line", self.CANON + "\n", "@@"),
                ("a note under the table",
                 self.CANON + "\nreminder: check OKR.md\n",
                 "-reminder: check OKR.md"),
                ("rows re-ordered by hand",
                 "| BOARD.md | 2 | 2026-08-20 | declare |\n"
                 "| .perry/hook.md | 2 | 2026-08-21 | declare |\n",
                 "-| .perry/hook.md | 2 | 2026-08-21 | declare |"),
                ("a row hidden in an HTML comment",
                 self.CANON + "<!--\n| OKR.md | 2 | 2026-08-20 | declare |\n-->\n",
                 "-<!--")):
            with self.subTest(edit=name):
                message = self.refusal(body)
                self.assertIn("--- .perry/conformance.md", message, name)
                self.assertIn(must_name, message,
                              f"{name}: the diff does not locate it")

    def test_a_wholly_rewritten_record_is_capped_and_says_how_much_it_dropped(self):
        """A refusal is read in a terminal. A whole record replaced by hand
        would print two lines per row and bury its own last sentence — the
        command to run — so the hunk is capped, and the cap says how many lines
        it dropped rather than trailing off."""
        rows = [f"| phase/{i:03d}-x.md | 2 | 2026-08-20 | declare |\n"
                for i in range(60)]
        # Reversed, so the file differs from the record almost everywhere — a
        # stray line at the end of a long file makes a two-line hunk, which is
        # the point of the tight context and not a case the cap has to handle.
        body = "".join(reversed(rows))
        p = self.record(body)
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 1, f"the conversion did not refuse: {out} {err}")
        message = out["refused"]
        self.assertIn("more diff line(s)", message, "the hunk was not capped")

        # **The NUMBER, not just the notice.** Asserting the sentence exists
        # let a mutation replace the count with a constant and stay green — the
        # same shape as the FAIL itself: an assertion sitting beside the thing
        # that matters. Recomputed from the file on disk and the shipped
        # reader, the way a reader checking the message would.
        import difflib
        authored = p.legacy_marker().read_text()
        canonical = C.render_legacy(
            C.P.read_legacy_conformance(p.root).declarations)
        total = len(list(difflib.unified_diff(
            authored.splitlines(), canonical.splitlines(),
            fromfile=C.P.CONFORMANCE_LEGACY_FILE,
            tofile="what Perry reads out of it", lineterm="", n=1)))
        expected = total - C.DIFF_CAP
        self.assertGreater(expected, 0, "the fixture does not reach the cap")
        self.assertIn(f"and {expected} more diff line(s)", message,
                      f"the refusal miscounts what it dropped (expected "
                      f"{expected} of {total})")
        # The diff BLOCK, not every indented line in the message — the
        # `perry-conform migrate` the last sentence names is indented too, and
        # counting it made this assertion off by one in the direction that
        # hides a cap one line too loose.
        block = message[message.index("    --- "):message.index("\n\nFix those")]
        self.assertLessEqual(len(block.split("\n")), C.DIFF_CAP + 1,
                             "the cap did not hold")
        self.assertTrue(message.rstrip().endswith("**Nothing was written.**"),
                        "the diff buried the message's last sentence")

    def test_a_crlf_record_converts_and_the_wording_does_not_say_byte(self):
        """**"Byte-for-byte" overclaimed and the phrase is gone.** The
        comparison is against `Path.read_text()`, which applies universal
        newline translation, so a record saved with CRLF converts. That is the
        behaviour we want — a CRLF record is still Perry's record — but the
        docstring said "byte-for-byte", which it is not. Pinned so the sentence
        and the code cannot drift apart again."""
        p = Project()
        p.legacy_marker().write_text(
            ("\n".join(C.LEGACY_HEADER) + "\n" + self.CANON).replace("\n", "\r\n"),
            newline="")
        self.assertIn(b"\r\n", p.legacy_marker().read_bytes(),
                      "the fixture is not CRLF, so this measures nothing")
        rc, out, err = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 0, f"a CRLF record refused: {out} {err}")
        self.assertEqual(sorted(C.P.read_conformance(p.root).declarations),
                         [".perry/hook.md", "BOARD.md"])
        # **The guard pinned one literal in one file, and the V4 round-3
        # reviewer said so: `"byte-for-byte what"` in `bin/perry-conform`
        # only.** A reworded overclaim — "byte for byte", "byte-for-byte
        # identical to what" — walked past it, and `bin/README.md`, which
        # documents the same conversion for the same reader, was not covered at
        # all. Decided in round 4: widen it rather than leave it, because the
        # sentence it protects lives in both files.
        #
        # It is a REGEX and not a ban on the phrase, deliberately. Both files
        # use "byte-for-byte" correctly about other things — a row inside an
        # HTML comment IS byte-for-byte a genuine row, `perry-tasks risks-diff`
        # DOES byte-compare — and a guard that made those red would be deleted
        # by the next person who hit it. What is banned is the phrase
        # describing what the file is compared AGAINST.
        overclaim = re.compile(
            r"byte[- ]for[- ]byte(\s+identical)?\s+(to\s+)?what", re.IGNORECASE)
        for rel in ("bin/perry-conform", "bin/README.md"):
            text = (PERRY_HOME / rel).read_text()
            found = overclaim.search(text)
            self.assertIsNone(
                found,
                f"{rel} claims a byte comparison it does not make "
                f"({found.group(0) if found else ''!r}) — `read_text` "
                f"translates newlines, which is why a CRLF record converts")
            # And the correction itself is pinned, in both places: deleting the
            # sentence that states the difference passes a NotIn assertion.
            self.assertIn(
                "ine-for-line, not byte-for-byte", text,
                f"{rel} no longer states the difference between what the "
                f"comparison does and what the word would have claimed")


class TestTheCommandTheRefusalNamesIsTheOneTheReaderCanRun(unittest.TestCase):
    """**The round-3 V4 FAIL: the refusal named the command with the root
    dropped, and the dropped-root command succeeds against a DIFFERENT
    project.**

    `bin/perry-conform § message_for` propagates the invocation's `--root`
    into every branch through `_root_flag()`. `migrate_record`'s two refusals
    did not — including the one round 3 rewrote under the wall standard's own
    banner. A reader routed there by `perry-conform migrate --root $PROJ`, who
    copied the command they were handed, got:

        $ perry-conform migrate
        perry-conform: nothing to convert — .perry/conformance.jsonl is
        already this project's record (or it has none).
        rc=0

    **Exit 0 and a success-shaped sentence**, about a project they never asked
    about, while their own record sat unconverted and still gating every
    write. A named command that errors is worse than none; this is the worse
    still variant, because nothing tells the reader anything went wrong.

    Sixteen invocations of `assert_conversion_refuses` asserted this message
    while themselves running with `--root <tmpdir>`, and every one of them was
    green: `assertIn("perry-conform migrate", message)` is true of the broken
    string. **The assertion checked that A command was named, never that it was
    the command the caller could actually run.** So this test does not
    construct what it expects. It:

      1. plants two REAL projects — the reader's, and a different one the
         reader is standing in, which has already converted;
      2. measures the harm the dropped root causes, so the test states what it
         is preventing rather than asserting a substring;
      3. takes the command OUT OF THE REFUSAL TEXT and runs it, unedited;
      4. asserts it converted the reader's project and left the other one
         byte-identical.

    A test that built the expected string by hand would pass on the broken
    implementation. This one cannot: step 3 runs whatever the message says.
    """

    def snapshot(self, root: Path) -> dict:
        return {f.relative_to(root).as_posix(): f.read_bytes()
                for f in sorted(root.rglob("*")) if f.is_file()}

    def test_the_named_command_converts_the_readers_project_from_elsewhere(self):
        # ── the reader's project: a record with one real declaration and a
        # stray line under it, which is the edit the record's own header
        # invites and one of the two that survive the row round trip.
        theirs = Project()
        canonical = f"| BOARD.md | {C.shape_version(SCHEMA)} | 2026-08-20 | declare |\n"
        header = "\n".join(C.LEGACY_HEADER) + "\n"
        theirs.legacy_marker().write_text(
            header + canonical + "\nreminder: check OKR.md\n")

        # ── a DIFFERENT project, and the one the reader is standing in. It has
        # already converted, so `perry-conform migrate` run here is a no-op
        # that exits 0 — which is exactly what makes the dropped root silent
        # rather than loud.
        elsewhere = Project()
        rc, _, _ = elsewhere.run(CONFORM, "declare", "BOARD.md")
        self.assertEqual(rc, 0, "the second project would not declare")
        self.assertTrue(elsewhere.marker().exists())
        before = self.snapshot(elsewhere.root)

        # ── 1 · the refusal, reached the way the reader reaches it
        rc, out, err = theirs.run(CONFORM, "migrate")
        self.assertEqual(rc, 1, f"the conversion did not refuse: {out} {err}")
        message = out["refused"]

        # ── 2 · the harm, measured on this tree rather than asserted. The
        # command the BROKEN refusal named, run from where the reader stands.
        harm = subprocess.run(
            ["python3", str(CONFORM), "migrate"],
            cwd=elsewhere.root, capture_output=True, text=True)
        self.assertEqual(harm.returncode, 0,
                         "the dropped-root command is expected to SUCCEED — "
                         "that is what makes it dangerous; if it now errors "
                         "this test is measuring something else")
        self.assertIn("nothing to convert", harm.stdout)
        self.assertTrue(
            theirs.legacy_marker().exists(),
            "the dropped-root command converted the reader's project after "
            "all — then there is no defect and this test is vacuous")
        self.assertFalse(theirs.marker().exists())

        # ── 3 · the command, taken out of the message
        named = commands_named(message)
        self.assertEqual(
            len(named), 1,
            f"expected exactly one command in the refusal, got {named!r}")
        cmd = named[0]
        argv = shlex.split(cmd)
        self.assertEqual(argv[0], "perry-conform",
                         f"the refusal names something other than this tool: {cmd!r}")
        self.assertNotEqual(
            argv[1:], ["migrate"],
            "the refusal hands back the bare command measured in step 2, "
            "which exits 0 about a different project")

        # The reader does what the refusal told them to: fix those lines.
        theirs.legacy_marker().write_text(header + canonical)

        # ── 4 · run it verbatim, from where the reader is standing
        ran = subprocess.run(
            ["python3", str(CONFORM), *argv[1:]],
            cwd=elsewhere.root, capture_output=True, text=True)
        self.assertEqual(
            ran.returncode, 0,
            f"the command the refusal named failed: {ran.stdout} {ran.stderr}")
        self.assertIn("carried 1 declaration(s)", ran.stdout,
                      f"it did not convert anything: {ran.stdout}")

        # ── the RIGHT project, and only it
        self.assertTrue(theirs.marker().exists(),
                        "the reader's record was not converted")
        self.assertFalse(theirs.legacy_marker().exists(),
                         "the markdown record was left behind")
        decls = C.P.read_conformance(theirs.root).declarations
        self.assertEqual(sorted(decls), ["BOARD.md"])
        self.assertEqual(decls["BOARD.md"].declared, "2026-08-20",
                         "the date was not carried across unchanged")
        self.assertEqual(theirs.verdict("BOARD.md").state, C.CONFORMANT)
        self.assertEqual(
            self.snapshot(elsewhere.root), before,
            "the command changed the project the reader was standing in")

    def test_the_unreadable_rows_refusal_names_it_too(self):
        """The other branch, and the one reached from `declare` — where the
        old wording also said "again", which the reader had not done."""
        theirs = Project()
        theirs.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n"
            + "| OKR.md | v-two | 2026-08-20 | declare |\n")
        rc, out, _ = theirs.run(CONFORM, "migrate")
        self.assertEqual(rc, 1)
        message = out["refused"]
        self.assertIn("will not honour", message)
        assert_every_command_carries(
            self, message, theirs.root, "the unreadable-rows branch")
        self.assertNotIn(
            "migrate` again", message,
            "reached from `declare` or `perry-migrate apply` the reader ran "
            "neither `migrate` nor it twice, so `again` is a false sentence")

    def test_the_declare_route_into_the_conversion_carries_the_root_too(self):
        """`declare` converts the record first, so the same refusal is reached
        from a command that is not `migrate`. It has to name the root the
        reader typed on THAT command."""
        theirs = Project()
        theirs.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n"
            + f"| BOARD.md | {C.shape_version(SCHEMA)} | 2026-08-20 | declare |\n"
            + "\nreminder: check OKR.md\n")
        rc, out, _ = theirs.run(CONFORM, "declare", "BOARD.md")
        self.assertEqual(rc, 1, f"declare did not refuse: {out}")
        assert_every_command_carries(
            self, out["refused"], theirs.root, "the `declare` route")

    def test_no_refusal_in_perry_conform_names_a_command_without_the_root(self):
        """**The class, guarded at the source.** Fixing the two sentences is
        an instance; this is what stops the next one.

        Every `perry-*` command a runtime message HANDS BACK — on an indented
        line of its own, or backticked after `run` / `with` / `is` — must carry
        the invocation's root, spelled `{r}` or `{_root_flag(...)}`. Prose that
        merely names a tool is not an instruction and is not caught: *"is not
        what `perry-conform declare` would have written"* names a command the
        reader is being told NOT to run.

        Read off the AST rather than by grepping the text, so a docstring
        discussing the defect — this one, and `migrate_record`'s — is not a
        finding.
        """
        import ast

        tools = ("conform", "lint", "migrate", "task", "tasks", "goals",
                 "state", "decide", "okr", "config", "knowledge")
        cmd = re.compile(r"perry-(?:" + "|".join(tools) + r")\b")
        root = re.compile(r"\{r\}|\{_root_flag\([^)]*\)\}|--root")
        cue = re.compile(r"(?:(?:^|\n)[ ]{2,}|\b(?:run|with|is|try|use)[ :]+`?)$",
                         re.IGNORECASE)

        def is_str(n):
            return isinstance(n, ast.Constant) and isinstance(n.value, str)

        def render(node):
            """The template, with each `{expr}` left visible as itself."""
            if is_str(node):
                return node.value
            if isinstance(node, ast.JoinedStr):
                return "".join(
                    v.value if is_str(v) else "{" + ast.unparse(v.value) + "}"
                    for v in node.values)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                a, b = render(node.left), render(node.right)
                return None if a is None or b is None else a + b
            return None

        source = (PERRY_HOME / "bin" / "perry-conform").read_text()
        tree = ast.parse(source)
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(getattr(node, "body", None), list):
                for st in node.body:
                    if isinstance(st, ast.Expr) and is_str(st.value):
                        docstrings.add(id(st.value))

        seen, handed, bad = set(), [], []
        for node in ast.walk(tree):
            if id(node) in seen or id(node) in docstrings:
                continue
            text = render(node)
            if text is None:
                continue
            for sub in ast.walk(node):
                seen.add(id(sub))
            for m in cmd.finditer(text):
                if not cue.search(text[:m.start()]):
                    continue          # a mention, not an instruction
                tail = re.match(r"[^`\n'\"]*", text[m.end():]).group(0)
                phrase = (m.group(0) + tail).rstrip()
                handed.append((node.lineno, phrase))
                if not root.search(phrase):
                    bad.append((node.lineno, phrase))

        self.assertEqual(
            bad, [],
            f"these messages hand back a command with the caller's root "
            f"dropped — run from where the reader is standing each acts on a "
            f"different project: {bad}")
        # Non-vacuous: the sweep has to be FINDING the commands, not returning
        # an empty set because the shapes it looks for stopped existing.
        self.assertGreaterEqual(
            len(handed), 12,
            f"the sweep found only {len(handed)} handed-back command(s) in "
            f"bin/perry-conform, so its empty finding list means nothing")


class TestTheDefensiveBranchesAreLoadBearing(unittest.TestCase):
    """**Branches that survived their own deletion, now pinned.**

    The V4 reviewer swept the new code for defensive branches that could be
    removed with the suite green and found five; a wider sweep on the same
    method found seven. The reviewer's ruling was that none could produce a
    false verdict or destroy data, and asked for them to be tested or named as
    unpinned with that reasoning rather than left under a general claim.

    Six are tested here. One of the six turned out not to be defensive at all —
    see `test_a_short_diff_does_not_claim_it_dropped_a_negative_number`.

    **The one NOT tested, named with its reasoning**, per the ruling:

    - `bin/perry-conform § verdict`'s `legacy_record=record.legacy is not None`
      versus `bool(record.legacy)`. These are the same predicate: `record.legacy`
      is `None` or a `Path` that came from `/`-joining two non-empty strings, and
      every such `Path` is truthy. It is an EQUIVALENT MUTANT, not an untested
      branch — there is no input that distinguishes them, so a test asserting
      the difference cannot be written. Recorded so a later sweep does not
      re-find it and file it again.
    """

    def store(self, line: str) -> Project:
        p = Project()
        p.marker().parent.mkdir(exist_ok=True)
        p.marker().write_text(line)
        return p

    def test_a_non_string_path_is_refused_rather_than_used_as_a_key(self):
        """`{"path": 123}` would otherwise become a dict key of the wrong type,
        which no `state_files()` key can ever equal — an unreachable
        declaration that reports as present."""
        for value in ("123", '""', "null", "[]"):
            with self.subTest(path=value):
                p = self.store('{"kind": "declaration", "path": ' + value
                               + ', "shape_version": 2, "declared": '
                               '"2026-08-28", "route": "declare"}\n')
                rec = C.P.read_conformance(p.root)
                self.assertEqual(rec.declarations, {}, value)
                self.assertEqual(len(rec.unreadable), 1,
                                 f"path {value} was dropped silently")

    def test_a_non_string_declared_or_route_is_refused(self):
        """Both cells reach a human — `declared` is printed in every STALE and
        DRIFTED refusal — and a non-string there formats as itself and reads
        as a date nobody wrote."""
        for field, value in (("declared", "20260828"), ("declared", "null"),
                             ("route", "2"), ("route", "null")):
            with self.subTest(**{field: value}):
                rec = {"kind": '"declaration"', "path": '"BOARD.md"',
                       "shape_version": "2", "declared": '"2026-08-28"',
                       "route": '"declare"'}
                rec[field] = value
                p = self.store("{" + ", ".join(
                    f'"{k}": {v}' for k, v in rec.items()) + "}\n")
                got = C.P.read_conformance(p.root)
                self.assertEqual(got.declarations, {}, f"{field}={value}")
                self.assertEqual(len(got.unreadable), 1)

    def test_an_empty_route_reads_as_declare_rather_than_as_blank(self):
        """`route` answers *how was this declared*, and the two values are
        `declare` and `migrate`. A blank is neither, and it is what a row
        written before `route` existed parses to."""
        p = self.store('{"kind": "declaration", "path": "BOARD.md", '
                       '"shape_version": 2, "declared": "2026-08-28", '
                       '"route": ""}\n')
        self.assertEqual(
            C.P.read_conformance(p.root).declarations["BOARD.md"].route,
            "declare")
        rc, out, _ = p.run(CONFORM, "status")
        row = next(f for f in out["files"] if f["path"] == "BOARD.md")
        self.assertEqual(row["route"], "declare")

    def test_non_string_provenance_reads_as_empty_rather_than_as_itself(self):
        """The three provenance fields are free text a reader is shown. A
        number or an object there would travel into `status --json` and into
        the next rewrite of the record exactly as typed."""
        p = self.store('{"kind": "declaration", "path": "BOARD.md", '
                       '"shape_version": 2, "declared": "2026-08-28", '
                       '"route": "declare", "writer": 7, '
                       '"recorded_at": {"x": 1}, "run": []}\n')
        decl = C.P.read_conformance(p.root).declarations["BOARD.md"]
        self.assertEqual((decl.writer, decl.recorded_at, decl.run), ("", "", ""))

    def test_a_record_that_exists_but_cannot_be_read_is_not_a_crash(self):
        """`exists()` is true and `read_text` raises — a directory where the
        record should be, a revoked permission, a device. `perry-conform
        status` is what the enforce gate calls, so a traceback here is a
        traceback on every write.

        A directory, because it raises `IsADirectoryError` (an `OSError`) on
        every platform and needs no permission games that a root-running CI
        would skip past."""
        p = Project()
        p.marker().mkdir(parents=True)
        self.assertTrue(p.marker().exists())
        rec = C.P.read_conformance(p.root)
        self.assertEqual(rec.declarations, {})
        rc, out, err = p.run(CONFORM, "status")
        self.assertEqual(rc, 0, f"status crashed on an unreadable record: {err}")
        self.assertIsInstance(out, dict, f"status printed no JSON: {out} {err}")

    def test_a_short_diff_does_not_claim_it_dropped_a_negative_number(self):
        """**Not a defensive branch — a live one.** `max(0, len(lines) - CAP)`
        looks like belt-and-braces and is not: without it, `dropped` is
        NEGATIVE for every diff shorter than the cap, `if dropped:` is true for
        a negative number, and every ordinary refusal ends *"… and -37 more
        diff line(s)"*. That is a false statement to the reader, printed on the
        one message the V4 FAIL was about. Found by sweeping for survivors."""
        p = Project()
        p.legacy_marker().write_text(
            "\n".join(C.LEGACY_HEADER) + "\n"
            + "| BOARD.md | 2 | 2026-08-20 | declare |\n" + "stray\n")
        rc, out, _ = p.run(CONFORM, "migrate")
        self.assertEqual(rc, 1)
        self.assertNotIn("more diff line(s)", out["refused"],
                         "a short diff claims it dropped lines")
        self.assertNotIn("-1", out["refused"].split("@@")[0],
                         "a negative count reached the message")


class TestWhatTheConversionDoesNotDissolve(unittest.TestCase):
    """**TASK-246 survives the format change, and this is where that is said.**

    TASK-246: *an unreadable row is DELETED by the next declare, not reported.*
    The writer rebuilds the whole record from the parsed declarations, exactly
    as the markdown writer did, so a line it could not read is not carried
    forward. Converting the record shrinks the POPULATION of such lines — a
    backticked, indented or fenced row is ordinary markdown and a person could
    plausibly type one, where a broken JSON line is rarer — and it does not
    touch the mechanism.

    Asserted as it IS rather than as it should be, so that the day TASK-246 is
    fixed this test goes red and is rewritten deliberately, instead of the
    project believing a row died when it did not.
    """

    def test_an_unreadable_line_is_still_dropped_by_the_next_declare(self):
        p = Project()
        p.marker().parent.mkdir(exist_ok=True)
        p.marker().write_text(p.line("BOARD.md") + "{ not json at all\n")
        self.assertEqual(len(C.P.read_conformance(p.root).unreadable), 1)
        rc, out, err = p.run(CONFORM, "declare", ".perry/hook.md")
        self.assertEqual(rc, 0, f"{out} {err}")
        self.assertNotIn("not json at all", p.marker().read_text(),
                         "TASK-246 is dissolved — rewrite this test and close "
                         "the row rather than leaving it open")
        self.assertEqual(C.P.read_conformance(p.root).unreadable, [])


if __name__ == "__main__":
    unittest.main()
