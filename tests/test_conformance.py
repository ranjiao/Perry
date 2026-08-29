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
        p.run(CONFORM, "declare", "BOARD.md")
        p.run(CONFORM, "declare", ".perry/hook.md")
        text = p.marker().read_text()
        self.assertIn("| BOARD.md |", text)
        self.assertIn("| .perry/hook.md |", text)

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


# ── 10b · a decorated row is not a declaration (TASK-241) ─────────────────


class TestADecoratedRowIsNotADeclaration(unittest.TestCase):
    """`read_conformance` stripped each cell with ``strip("` ")``, so a row
    whose path cell was in BACKTICKS parsed to the same plain key as a row a
    person had declared on purpose. Same for an INDENTED row (`_CONFORMANCE_ROW`
    is `^\\s*\\|`) and for a row inside a ``` FENCE (this reader tracked none).

    Found by the `TASK-226` V4 reviewer, who measured the harm: one hand-written
    backticked row flips a real file from `undeclared` to **conformant**, and
    because `declare` rewrites the whole file from the parsed declarations
    (`bin/perry-conform § render`), the next legitimate declare **launders** it
    into a plain canonical row nothing downstream can tell from a real one.
    `.perry/conformance.md` is the file that gates every write under ADR-004's
    enforce gate, and its own header invites hand editing — *"Delete a row to
    withdraw a declaration"* — so this is reachable by design, not contrivance.

    **THREE SHAPES, THREE TESTS.** One test covering all three would still pass
    with two of the three regressed, and the three are stopped by two different
    mechanisms — the row round trip catches decoration written INSIDE the row,
    and only fence tracking catches the fenced row, which is byte-for-byte
    identical to a genuine one.

    **Each test carries its own control.** It first plants the UNDECORATED row
    and asserts that the verdict really does flip to `conformant` — so the trap
    is proved live in the same test that proves it closed, and none of these can
    pass because the reader stopped reading, because the fixture stopped being
    lint-clean, or because the row was malformed for some fourth reason.

    **Shape 3 has more than one spelling, and the first fix only closed one.**
    That fix was a boolean toggle flipped by any fence-looking line, so a fence
    NESTED in another — which is how every markdown document that shows a fenced
    block writes it — turned tracking off and gave the row back. Six further
    spellings were measured live on that fix (§ "the fence has to be markdown's
    fence" below) and each has its own test, because a single test over all of
    them would pass with five regressed.
    """

    VER = C.shape_version(SCHEMA)

    def plant(self, body: str):
        """A project whose record is exactly the real header plus `body`.

        Returns `(state of BOARD.md, number of unreadable rows)` as
        `perry-conform status` reports them — the surface the gate reads, not
        the parser in isolation."""
        p = Project()
        p.marker().write_text("\n".join(C.HEADER) + "\n" + body)
        rc, out, err = p.run(CONFORM, "status")
        row = next(f for f in out["files"] if f["path"] == "BOARD.md")
        return row["state"], len(out["unreadable_rows"])

    def canonical(self) -> str:
        return f"| BOARD.md | {self.VER} | 2026-08-28 | declare |\n"

    # ── the control, shared by all three ──────────────────────────────────

    def assert_trap_would_have_worked(self):
        """The undecorated row. If this stops flipping the verdict, every test
        below is vacuous — so every test below runs it first."""
        self.assertEqual(
            self.plant(self.canonical()), (C.CONFORMANT, 0),
            "the control row no longer declares BOARD.md — the three tests "
            "below would pass for the wrong reason")

    # ── shape 1 ───────────────────────────────────────────────────────────

    def test_a_backticked_path_cell_is_not_a_declaration(self):
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            f"| `BOARD.md` | {self.VER} | 2026-08-28 | declare |\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a backticked path cell still declares a file")
        self.assertEqual(unreadable, 1,
                         "the row was dropped silently instead of reported")

    # ── shape 2 ───────────────────────────────────────────────────────────

    def test_an_indented_row_is_not_a_declaration(self):
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant("   " + self.canonical())
        self.assertEqual(state, C.UNDECLARED,
                         "an indented row still declares a file")
        self.assertEqual(unreadable, 1,
                         "the row was dropped silently instead of reported")

    # ── shape 3 ───────────────────────────────────────────────────────────

    def test_a_row_inside_a_code_fence_is_not_a_declaration(self):
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant("```\n" + self.canonical() + "```\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a row inside a code fence still declares a file")
        self.assertEqual(unreadable, 1,
                         "the row was dropped silently instead of reported")

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
        state, unreadable = self.plant(
            "~~~\n```\n" + self.canonical() + "```\n~~~\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a backtick fence inside a tilde fence closed it")
        self.assertEqual(unreadable, 1)

    def test_a_three_backtick_line_inside_a_four_backtick_fence_is_still_a_fence(self):
        """The other plain way: open with a LONGER run. A close must be at
        least as long as the open, so ``` inside ```` is content."""
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            "````\n```\n" + self.canonical() + "````\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a short fence run closed a longer fence")
        self.assertEqual(unreadable, 1)

    def test_a_tilde_fence_nested_in_a_backtick_fence_is_still_a_fence(self):
        """The mirror of the first, and it is not the same test: the toggle was
        symmetric but the rule is not, so a fix that keyed on the character
        could close one direction and leave the other open."""
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            "```\n~~~\n" + self.canonical() + "~~~\n```\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a tilde fence inside a backtick fence closed it")
        self.assertEqual(unreadable, 1)

    def test_a_fence_line_with_trailing_text_does_not_close_the_fence(self):
        """An info string is allowed on the OPENING fence only. ```` ```x ````
        inside an open fence is a content line — and it is exactly what an
        example showing an opening fence looks like."""
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            "```\n```x\n" + self.canonical() + "```\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a fence line with an info string closed a fence")
        self.assertEqual(unreadable, 1)

    def test_a_four_space_indented_fence_line_does_not_close_the_fence(self):
        """A closing fence may be indented at most three spaces. At four it is
        content — which is how a fenced block nested in a list item or a
        blockquote-free indent appears."""
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            "```\n    ```\n" + self.canonical() + "```\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a four-space-indented fence line closed a fence")
        self.assertEqual(unreadable, 1)

    def test_a_whole_table_inside_a_nested_fence_declares_nothing(self):
        """The shape that decided the mechanism.

        A document does not show one bare row; it shows the table — header,
        delimiter, row. This is why the reader tracks FENCES and not "rows in
        the contiguous run under the `| File |` header": measured, that rule
        closes every bare-row shape above and then reads THIS one as a
        declaration, because the fenced example brings its own header and so
        starts its own run. Both rows must be refused, and reported."""
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            "~~~\n```\n"
            "| File | Shape version | Declared | Route |\n"
            "|---|---|---|---|\n" + self.canonical()
            + "```\n~~~\n")
        self.assertEqual(state, C.UNDECLARED,
                         "an example table in a nested fence declared a file")
        self.assertEqual(unreadable, 2,
                         "the fenced rows were dropped silently, not reported")

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
        state, unreadable = self.plant(
            "    ```\n" + self.canonical() + "    ```\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a four-space-indented fence stopped opening one")
        self.assertEqual(unreadable, 1)

    def test_a_backtick_fence_with_a_backtick_in_its_info_string_still_opens_one(self):
        self.assert_trap_would_have_worked()
        state, unreadable = self.plant(
            "```a`b\n" + self.canonical() + "```\n")
        self.assertEqual(state, C.UNDECLARED,
                         "a backtick in the info string stopped opening a fence")
        self.assertEqual(unreadable, 1)

    # ── a cell that cannot be written back at all ─────────────────────────

    def test_a_path_cell_that_cannot_be_written_back_is_reported_not_crashed(self):
        """`read_conformance` splits the record on `"\\n"`; `render_row` refuses
        through `line_break_at`, which uses `str.splitlines()` — **eleven**
        boundaries, not one. So a path cell holding `U+2028` sits inside a
        single line for the reader and makes the canonical form unwritable.

        Without the `except UnrenderableCell` the round trip raises straight out
        of `read_conformance` and `perry-conform status` dies with a traceback
        on a hand-edited record — on the tool the enforce gate calls. This test
        exists because the RESULT for round 1 claimed nothing it added could be
        deleted with the suite unchanged, and a reviewer deleted this guard with
        the suite unchanged. Asserts the exit code, not just the report: a crash
        and a refusal both produce no declaration."""
        p = Project()
        p.marker().write_text(
            "\n".join(C.HEADER) + "\n"
            + f"| BOARD\u2028.md | {self.VER} | 2026-08-28 | declare |\n")
        rc, out, err = p.run(CONFORM, "status")
        self.assertEqual(rc, 0, f"status crashed on the record: {err}")
        self.assertIsInstance(out, dict, f"status printed no JSON: {out} {err}")
        self.assertEqual(len(out["unreadable_rows"]), 1,
                         "the unwritable row was dropped instead of reported")
        rec = C.P.read_conformance(p.root)
        self.assertEqual(rec.declarations, {})

    # ── the harm the three shapes lead to ─────────────────────────────────

    def test_a_nested_fence_row_is_not_laundered_by_the_next_declare(self):
        """The laundering came back with the nesting, so it is measured again
        against the shape that reopened it. Same story as the backticked row
        below: an ordinary declare of a DIFFERENT file, and the record quietly
        canonicalises a claim nobody made."""
        p = Project()
        p.marker().write_text(
            "\n".join(C.HEADER) + "\n"
            + "~~~\n```\n"
            + f"| BOARD.md | {self.VER} | 2026-08-28 | declare |\n"
            + "```\n~~~\n")
        rc, out, err = p.run(CONFORM, "declare", ".perry/hook.md")
        self.assertEqual(rc, 0, f"the control declare failed: {out} {err}")
        text = p.marker().read_text()
        self.assertIn("| .perry/hook.md |", text, "nothing was rewritten")
        self.assertNotIn(f"| BOARD.md | {self.VER} |", text,
                         "the fenced row was laundered into a canonical one")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)

    def test_a_planted_row_is_not_laundered_by_the_next_declare(self):
        """The second half of the measured defect, and the worse half: after
        the rewrite the row is indistinguishable from one a person wrote.

        The declare here is of a DIFFERENT file — a legitimate one — because
        that is the whole point: the user does something entirely ordinary and
        the record quietly canonicalises a claim they never made."""
        p = Project()
        p.marker().write_text(
            "\n".join(C.HEADER) + "\n"
            + f"| `BOARD.md` | {self.VER} | 2026-08-28 | declare |\n")
        rc, out, err = p.run(CONFORM, "declare", ".perry/hook.md")
        self.assertEqual(rc, 0, f"the control declare failed: {out} {err}")
        text = p.marker().read_text()
        self.assertIn("| .perry/hook.md |", text, "nothing was rewritten")
        self.assertNotIn(f"| BOARD.md | {self.VER} |", text,
                         "the decorated row was laundered into a canonical one")
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED)

    # ── and the case that must NOT change ─────────────────────────────────

    def test_an_asterisked_path_reads_exactly_as_it_did_before(self):
        """``strip("` ")`` never removed asterisks, so `| **BOARD.md** |` has
        always parsed to the decorated key `**BOARD.md**` — inert, because no
        key `state_files()` produces carries asterisks. TASK-226 filed it as an
        observation and it stays one. This guard is about rows that reach a
        REAL key; widening it to reject asterisks too would be a different
        change, and the round trip deliberately lets this row through because
        it is already exactly what `render` would write for that key."""
        p = Project()
        p.marker().write_text(
            "\n".join(C.HEADER) + "\n"
            + f"| **BOARD.md** | {self.VER} | 2026-08-28 | declare |\n")
        rec = C.P.read_conformance(p.root)
        self.assertEqual(list(rec.declarations), ["**BOARD.md**"])
        self.assertEqual(rec.unreadable, [])
        self.assertEqual(p.verdict("BOARD.md").state, C.UNDECLARED,
                         "the asterisked row started flipping a real verdict")

    def test_a_bolded_header_row_is_still_not_a_row(self):
        """`squash` answers this and answered it before TASK-241 (TASK-050).
        Here so that a guard added ABOVE the header check — where it would
        report the header as an unreadable row — cannot land green."""
        p = Project()
        p.marker().write_text(
            "# Perry conformance\n\n"
            "| **File** | **Shape version** | **Declared** | **Route** |\n"
            "|---|---|---|---|\n" + self.canonical())
        rec = C.P.read_conformance(p.root)
        self.assertEqual(list(rec.declarations), ["BOARD.md"])
        self.assertEqual(rec.unreadable, [])

    def test_perrys_own_record_is_read_without_a_single_refusal(self):
        """The guard is strict, and a strict guard that refuses the real file
        would take the enforce gate down for this repository. Every row of the
        shipped `.perry/conformance.md` must still read."""
        rec = C.P.read_conformance(PERRY_HOME)
        self.assertTrue(rec.exists)
        self.assertEqual(rec.unreadable, [],
                         "the guard refuses rows in Perry's own record")
        self.assertGreater(len(rec.declarations), 0)


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
