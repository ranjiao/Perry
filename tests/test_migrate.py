"""TASK-044: migration is dry-runnable, lossless, recoverable, and declared.

The claim under test: **a project can be brought to Perry's shape by a program
whose preview cannot diverge from what it does, which refuses rather than lose
a character of somebody's writing, which can be undone, and which never runs
unasked.**

Three of ADR-004's five guarantees are assertions, and an assertion an agent
performs by reading is not one. So the shape of this suite is deliberate:

- the losslessness tests run against a board that Perry did NOT write. A board
  Perry generated is already Perry-shaped and proves nothing; `LEGACY_BOARD`
  below is modelled on `~/proj/gimegime-pmo` — work filed under headings its
  author chose, a four-column priority table, a status word Perry has no value
  for, and prose in a cell the schema has nowhere to put.
- `TestDryRunIsTheRealRun` compares bytes, not intentions.
- `TestRecoverable` exercises the recovery path rather than describing it.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import hashlib
import contextlib
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
MIGRATE = PERRY_HOME / "bin" / "perry-migrate"
CONFORM = PERRY_HOME / "bin" / "perry-conform"
LINT = PERRY_HOME / "bin" / "perry-lint"
TASK = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"

SCHEMA = json.loads((PERRY_HOME / "schema" / "state-schema.json").read_text())


def load(name: str, path: Path):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(path)))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M = load("perry_migrate_under_test", MIGRATE)


# ── fixtures ──────────────────────────────────────────────────────────────

#: Not a board Perry wrote. Modelled on the year-old real one this task was
#: built against: 41 tasks under `## Open — <workstream>`, one hand-kept `## P2`
#: with four columns, a status word its author invented, and free prose in
#: cells the schema does not model.
LEGACY_BOARD = """# Board — Legacy

> Last updated: 2026-01-04

## ID prefixes (canonical)

`INV-*` investments · `ENG-*` engineering.

## Open — investment line (policy · allocation)

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| INV-DRAFT-1 | policy draft, **blocked on the RM reply** (see `policy/INDEX.md`) | User | not_started | chase the RM |
| INV-ALLOC-2 | rebalance band ~200bp, defensive not tactical | User | in_progress | wait for Q3 |

## Open — engineering line · phase #004

| ID | Title | Owner | Status | Next action |
|---|---|---|---|---|
| ENG-7 | fd leak in the scheduler; 17 jobs re-registered | Coding Agent | done | — |

## P2 (low priority carry)

| ID | Title | Owner | Status |
|---|---|---|---|
| ENG-9 | conftest has no DB isolation | Coding Agent | not_started |

## Cadence

| ID | Recurring task | Owner | Frequency | Next due |
|---|---|---|---|---|
| CAD-1 | weekly reconcile | User | weekly | 2026-01-11 |

## User Input Queue

| USER-id | Needed from user | Blocks | Status |
|---|---|---|---|
| USER-3 | pick a broker | INV-DRAFT-1 | open |

## Top risks

- the RM has not replied since November
"""

#: The same board with a status word Perry has no value for. This is the real
#: one: `半解` ("half-solved") on gimegime-pmo's `## P2`.
UNRESOLVABLE_BOARD = LEGACY_BOARD.replace(
    "| ENG-9 | conftest has no DB isolation | Coding Agent | not_started |",
    "| ENG-9 | conftest has no DB isolation | Coding Agent | half-done |")

LEGACY_DESIGN = """# DESIGN-001: the thing

> **Status**: v1.1 LOCKED 2026-05-19 PM BJT** (Amendments A+B applied; v1.0 LOCKED 2026-05-18)
> **Owner**: User
> **Date**: 2026-05-18

## 1. Problem

It is broken.

## 2. Goals

Fix it.

## 3. Non-Goals

Everything else.

## 4. User Decisions

D-1: go.

## 5. Architecture

A box.

## 6. Implementation plan

Do the thing.

## 7. Risks & mitigations

None.
"""

CONFIG_EN = ("# Perry configuration\n\n- Document language: English\n"
             "- Repo layout: single\n- State root: .\n")
CONFIG_ZH = ("# Perry configuration\n\n- Document language: 中文\n"
             "- Repo layout: single\n- State root: .\n")

HOOK = "# Hook\n\n## High-stakes operations\n\n- anything that spends money\n"


class Project:
    """A throwaway project holding whatever files a test needs."""

    def __init__(self, files: dict[str, str] | None = None,
                 config: str = CONFIG_EN):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(config)
        (self.root / ".perry" / "hook.md").write_text(HOOK)
        for rel, text in (files or {"BOARD.md": LEGACY_BOARD}).items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)

    def run(self, *argv, tool: Path = MIGRATE, json_out: bool = True):
        argv = [*argv, "--root", str(self.root)]
        if json_out:
            argv.append("--json")
        r = subprocess.run(["python3", str(tool), *argv],
                           capture_output=True, text=True, env=dict(os.environ))
        try:
            return r.returncode, json.loads(r.stdout or "{}"), r.stderr
        except json.JSONDecodeError:
            return r.returncode, r.stdout, r.stderr

    def text(self, rel: str) -> str:
        return (self.root / rel).read_text()

    def tree(self) -> dict[str, str]:
        return {str(f.relative_to(self.root)):
                hashlib.sha256(f.read_bytes()).hexdigest()
                for f in sorted(self.root.rglob("*")) if f.is_file()}

    def lint_errors(self) -> int:
        r = subprocess.run(["python3", str(LINT), "--root", str(self.root),
                            "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["errors"]

    def plan(self):
        return M.plan_project(self.root, self.root, SCHEMA)

    def __del__(self):
        self.dir.cleanup()


def edit_for(plan, key: str):
    return next((e for e in plan.edits if e.key == key), None)


def spec_for(path: str) -> dict:
    """The schema's entry for a state file, by its declared path."""
    return next(f for f in SCHEMA["files"] if f["path"] == path)


BOARD_SPEC = spec_for("BOARD.md")
DESIGN_SPEC = spec_for("design/*.md")


# ── 1 · dry run first, always ─────────────────────────────────────────────


class TestDryRunIsTheRealRun(unittest.TestCase):

    def test_the_default_subcommand_writes_nothing(self):
        """Asserted on bytes, not by reading the code — every file in the
        project, hashed before and after."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        before = p.tree()
        rc, out, _ = p.run()
        self.assertEqual(p.tree(), before)
        self.assertEqual(out["mode"], "dry-run")

    def test_the_dry_run_prints_the_complete_diff_not_a_summary(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        rc, out, _ = p.run(json_out=False)
        self.assertIn("--- a/BOARD.md", out)
        self.assertIn("+++ b/BOARD.md", out)
        self.assertIn("## P0", out)
        self.assertIn("+| ID | Title | Owner | Status | Next action | Evidence |",
                      out.replace(" ", " "))

    def test_the_bytes_the_dry_run_showed_are_the_bytes_apply_writes(self):
        """The guarantee: a preview that can diverge is worse than none. It
        cannot diverge here because the plan carries the post-image and `apply`
        writes exactly that — this asserts the property, not the mechanism."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        _, dry, _ = p.run()
        _, real, _ = p.run("apply")
        for f in dry["files"]:
            if not f["writable"]:
                continue
            on_disk = hashlib.sha256(p.text(f["path"]).encode()).hexdigest()
            self.assertEqual(f["after_sha256"], on_disk,
                             f"{f['path']} on disk is not what the dry run showed")

    def test_the_dry_run_and_the_real_run_report_the_same_files_and_changes(self):
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": LEGACY_DESIGN})
        _, dry, _ = p.run()
        _, real, _ = p.run("apply")
        strip = lambda d: [(f["path"], f["before_sha256"], f["after_sha256"],
                            [c["kind"] for c in f["changes"]]) for f in d["files"]]
        self.assertEqual(strip(dry), strip(real))

    def test_planning_twice_produces_the_same_plan(self):
        """A plan that is not a pure function of the project's bytes cannot be
        previewed. Nothing here may depend on the clock: a dry run read on
        Monday and applied on Tuesday has to be the same edit."""
        p = Project({"BOARD.md": LEGACY_BOARD,
                     "knowledge/a/note.md": "# note\n\n> Source: a paste\n"})
        a = [e.after for e in p.plan().edits]
        b = [e.after for e in p.plan().edits]
        self.assertEqual(a, b)
        inserted = "\n".join(l for e in p.plan().edits
                             for l in e.after.split("\n")
                             if l not in e.before.split("\n"))
        self.assertNotRegex(inserted, r"\d{4}-\d{2}-\d{2}",
                            "migration writes no date: a plan read on Monday "
                            "and applied on Tuesday must be the same edit")

    def test_the_cross_file_consequence_is_reported_in_the_dry_run_too(self):
        """Normalizing a design doc's Status makes `locked-design-has-plan`
        readable for the first time. The dry run says so; a preview that hides
        a consequence only `apply` would reveal is the divergence § 1 forbids."""
        doc = LEGACY_DESIGN.replace("## 6. Implementation plan\n\nDo the thing.\n",
                                    "## 6. Implementation plan\n\n")
        doc = doc.replace("> **Status**: v1.1 LOCKED 2026-05-19 PM BJT**",
                          "> **Status**: Design locked（2026-06-03；D1**")
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-002-y.md": doc})
        _, dry, _ = p.run()
        rules = [f["rule"] for f in dry["newly_visible"]]
        self.assertIn("locked-design-has-plan", rules)


# ── 2 · nothing is lost ───────────────────────────────────────────────────


class TestNothingIsLost(unittest.TestCase):

    def test_every_id_present_before_is_present_after(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        before = M.ids(p.text("BOARD.md"))
        p.run("apply")
        after = M.ids(p.text("BOARD.md"))
        self.assertTrue(before, "the fixture must actually carry ids")
        self.assertEqual(before - after, set())

    def test_no_character_the_author_wrote_is_dropped(self):
        """Character granularity, not word: `> **状态**：进行中` is a single
        whitespace-delimited token, so a word-level check both misses damage
        inside it and reports the whole line as lost when its value is
        normalized."""
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": LEGACY_DESIGN})
        before = {k: p.text(k) for k in ("BOARD.md", "design/DESIGN-001-x.md")}
        p.run("apply")
        for k, was in before.items():
            missing = M.characters(was) - M.characters(p.text(k))
            self.assertEqual(missing, {}.__class__() if False else missing.__class__(),
                             f"{k} lost characters: {missing}")

    def test_free_prose_in_a_cell_the_schema_does_not_model_is_carried(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        after = p.text("BOARD.md")
        self.assertIn("policy draft, **blocked on the RM reply** "
                      "(see `policy/INDEX.md`)", after)
        self.assertIn("rebalance band ~200bp, defensive not tactical", after)

    def test_the_value_an_enum_field_had_is_kept_verbatim_beside_the_canonical_one(self):
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": LEGACY_DESIGN})
        p.run("apply")
        line = next(l for l in p.text("design/DESIGN-001-x.md").split("\n")
                    if "Status" in l)
        self.assertTrue(line.split("|")[0].strip().endswith("locked"), line)
        self.assertIn("v1.1 LOCKED 2026-05-19 PM BJT", line)

    def test_row_counts_per_section_are_preserved(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        before = M.rows_by_section(p.text("BOARD.md").split("\n"))
        p.run("apply")
        after = M.rows_by_section(p.text("BOARD.md").split("\n"))
        for section, n in before.items():
            self.assertEqual(after.get(section), n, section)

    def test_a_transform_that_loses_something_is_refused_rather_than_written(self):
        """The assertion is the tool's, not the reader's. Injecting a lossy
        transform must stop the write, not produce a report nobody checks."""
        text = LEGACY_BOARD
        before = text
        after = text.replace("| CAD-1 | weekly reconcile | User | weekly | 2026-01-11 |",
                             "| CAD-1 | weekly reconcile | User | weekly |  |")
        bad = M.losslessness(before, after, [])
        self.assertTrue(bad, "dropping a cell must be caught")
        self.assertTrue(any("character" in b or "cell" in b for b in bad), bad)

    def test_a_dropped_row_is_caught_even_when_every_character_survives(self):
        """Row counts are a separate check because a row moved out of its
        section keeps every character it had."""
        before = LEGACY_BOARD
        after = before.replace(
            "| ENG-9 | conftest has no DB isolation | Coding Agent | not_started |\n", "")
        after += "\n| ENG-9 | conftest has no DB isolation | Coding Agent | not_started |\n"
        bad = M.losslessness(before, after, [])
        self.assertTrue(any("row(s)" in b for b in bad), bad)

    def test_a_character_can_be_lost_with_no_cell_or_row_going_missing(self):
        """Why the character check is separate. Prose outside a table is
        invisible to the cell check, and `~200bp` losing its tilde is a change
        to what the sentence says."""
        before = "a note about ~200bp, defensive"
        after = "a note about 200bp, defensive"
        bad = M.losslessness(before, after, [before])
        self.assertEqual([b for b in bad if "character" not in b], [],
                         "no other check may fire on this input")
        self.assertTrue(any("character" in b for b in bad), bad)

    def test_an_id_can_be_lost_while_every_character_survives(self):
        """Why the id set is checked on its own. Characters are whitespace-
        blind, so a handle can be broken without a single one going missing —
        and an id is what attribution and every citation resolve on."""
        bad = M.losslessness("ADR-005 x", "ADR-005x", ["ADR-005 x"])
        self.assertEqual([b for b in bad if "id(s)" not in b], [],
                         "no other check may fire on this input")
        self.assertTrue(any("id(s)" in b for b in bad), bad)

    def test_a_write_that_does_not_match_the_plan_rolls_the_whole_run_back(self):
        """The tool checks its own writing. If the bytes on disk are not the
        bytes the preview showed, the run is undone rather than left half
        applied."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        before = p.tree()
        plan = p.plan()
        real = M.write_atomic
        calls = []

        def corrupt_the_first_write(path, text):
            calls.append(path)
            real(path, text + "\n" if len(calls) == 1 else text)

        M.write_atomic = corrupt_the_first_write
        try:
            with self.assertRaises(M.Refused):
                M.apply_plan(plan, SCHEMA)
        finally:
            M.write_atomic = real
        for path, digest in before.items():
            self.assertEqual(p.tree().get(path), digest, path)

    def test_a_line_edited_without_being_recorded_is_caught(self):
        """`rewritten` is the tool's own claim about what it changed. A
        transform that edits a line it did not declare fails here — the same
        discipline the mutation table is scored on."""
        before = "> **Owner**: User\n\n## P0\n"
        after = "> **Owner**: Someone Else User\n\n## P0\n"
        self.assertTrue(any("not recorded as rewritten" in b
                            for b in M.losslessness(before, after, [])))
        self.assertEqual(M.losslessness(before, after, ["> **Owner**: User"]), [])


# ── 3 · recoverable ───────────────────────────────────────────────────────


class TestRecoverable(unittest.TestCase):

    def test_a_run_writes_a_restore_point_and_names_it(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        rc, out, _ = p.run("apply", json_out=False)
        self.assertIn(".perry/migrate/", out)
        self.assertIn("perry-migrate restore", out)
        points = list((p.root / ".perry" / "migrate").glob("*.json"))
        self.assertEqual(len(points), 1)

    def test_restore_puts_every_byte_back(self):
        """Exercised, not described."""
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": LEGACY_DESIGN})
        before = p.tree()
        p.run("apply")
        self.assertNotEqual(p.tree(), before)
        rc, _, err = p.run("restore")
        self.assertEqual(rc, 0, err)
        after = p.tree()
        for path, digest in before.items():
            self.assertEqual(after.get(path), digest, path)

    def test_restore_also_withdraws_the_declarations_the_run_wrote(self):
        """A restore that put the files back and left the record standing would
        claim conformance for files that no longer have it."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        self.assertTrue((p.root / ".perry" / "conformance.md").exists())
        p.run("restore")
        self.assertFalse((p.root / ".perry" / "conformance.md").exists(),
                         "the record was created by the run and must go back "
                          "to not existing")

    def test_apply_and_restore_keep_board_and_store_in_the_same_restore_set(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        store = p.root / "tasks.jsonl"
        self.assertTrue(store.exists())
        diff = subprocess.run(
            [sys.executable, str(TASKS), "diff", "--root", str(p.root)],
            capture_output=True, text=True)
        self.assertEqual(diff.returncode, 0, diff.stdout + diff.stderr)
        self.assertTrue(json.loads(diff.stdout)["identical"])
        p.run("restore")
        self.assertFalse(store.exists(),
                         "restore left a store for the pre-migration board")

    def test_apply_recreates_a_missing_store_when_the_board_needs_no_edit(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        self.assertEqual(p.run("apply")[0], 0)
        store = p.root / "tasks.jsonl"
        self.assertTrue(store.exists())
        store.unlink()
        rc, out, err = p.run("apply")
        self.assertEqual(rc, 0, (out, err))
        self.assertTrue(store.exists(),
                        "a structurally current board suppressed store creation")
        diff = subprocess.run(
            [sys.executable, str(TASKS), "diff", "--root", str(p.root)],
            capture_output=True, text=True)
        self.assertEqual(diff.returncode, 0, diff.stdout + diff.stderr)
        self.assertTrue(json.loads(diff.stdout)["identical"])

    def test_apply_refuses_a_malformed_or_drifted_store_before_board_changes(self):
        for malformed in (True, False):
            with self.subTest(malformed=malformed):
                p = Project({"BOARD.md": LEGACY_BOARD})
                store = p.root / "tasks.jsonl"
                if malformed:
                    store.write_text('{"id":"INV-DRAFT-1","order":true}\n')
                else:
                    made = subprocess.run(
                        [sys.executable, str(TASKS), "write", "--from-board",
                         "--root", str(p.root)], capture_output=True, text=True)
                    self.assertEqual(made.returncode, 0, made.stderr)
                    records = [json.loads(line) for line in store.read_text().splitlines()]
                    records[0]["owner"] = "store-only edit"
                    store.write_text("".join(json.dumps(r) + "\n" for r in records))
                before = p.text("BOARD.md")
                rc, out, err = p.run("apply")
                self.assertEqual(rc, 1, (out, err))
                self.assertEqual(p.text("BOARD.md"), before)
                self.assertIn("tasks.jsonl", out.get("refused", ""))

    def test_apply_plans_and_writes_while_the_project_lock_is_held(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        active = {"value": False}
        real_lock, real_plan, real_apply = M.lib.project_lock, M.plan_project, M.apply_plan

        @contextlib.contextmanager
        def lock(*_args, **_kwargs):
            active["value"] = True
            try:
                yield
            finally:
                active["value"] = False

        def checked_plan(*args, **kwargs):
            self.assertTrue(active["value"], "migration planning escaped the lock")
            return real_plan(*args, **kwargs)

        def checked_apply(*args, **kwargs):
            self.assertTrue(active["value"], "migration writes escaped the lock")
            return real_apply(*args, **kwargs)

        M.lib.project_lock, M.plan_project, M.apply_plan = lock, checked_plan, checked_apply
        try:
            rc = M.main(["apply", "--root", str(p.root), "--json"])
        finally:
            M.lib.project_lock, M.plan_project, M.apply_plan = \
                real_lock, real_plan, real_apply
        self.assertEqual(rc, 0)

    def test_a_dirty_git_tree_is_reported_and_not_refused(self):
        """Refusing on a dirty tree answers the question only for projects
        under git, and the project this was built against is a local-only repo
        whose state files are routinely uncommitted."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        subprocess.run(["git", "init", "-q", str(p.root)], capture_output=True)
        (p.root / "untracked.txt").write_text("x")
        rc, out, _ = p.run(json_out=False)
        self.assertIn("uncommitted", out)
        rc, _, _ = p.run("apply")
        self.assertIn("BOARD.md", [f for f in p.tree()])
        self.assertTrue((p.root / ".perry" / "migrate").is_dir(),
                        "a dirty tree must not stop the run — the restore "
                        "point is what makes it recoverable")

    def test_the_restore_point_is_invisible_to_the_namespace_check(self):
        """`perry-lint --claims` globs `*.md`; a restore point that landed as
        markdown under `.perry/` would report Perry colliding with Perry, which
        is the defect TASK-043 shipped and fixed."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        r = subprocess.run(["python3", str(LINT), "--claims", "--root",
                            str(p.root), "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(r.stdout)["collisions"], 0)


# ── 4 · the user declares ─────────────────────────────────────────────────


class TestTheUserDeclares(unittest.TestCase):

    def test_migration_never_runs_as_a_side_effect_of_another_command(self):
        """Nothing in `bin/` may invoke this. A migration that fires from a
        `perry-task add` is TASK-040 B-2 with a bigger blast radius."""
        callers = []
        for tool in sorted((PERRY_HOME / "bin").glob("perry-*")):
            if tool.name == "perry-migrate":
                continue
            body = tool.read_text()
            for line in body.split("\n"):
                if "perry-migrate" in line and not line.lstrip().startswith(("#", "*")):
                    if re.search(r"(subprocess|import|_load|exec)", line):
                        callers.append(f"{tool.name}: {line.strip()}")
        self.assertEqual(callers, [])

    def test_the_declaration_goes_through_perry_conform_and_is_the_only_record(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        record = p.root / ".perry" / "conformance.md"
        self.assertTrue(record.exists())
        self.assertIn("| BOARD.md | 2 | ", record.read_text())
        self.assertIn("| migrate |", record.read_text(),
                      "the route field exists so a declaration says how it was "
                      "made; a migration's is not a hand `declare`")
        others = [f for f in (p.root / ".perry").rglob("*")
                  if f.is_file() and "conform" in f.name and f != record]
        self.assertEqual(others, [], "there must be exactly one record")

    def test_a_dry_run_declares_nothing(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run()
        self.assertFalse((p.root / ".perry" / "conformance.md").exists())

    def test_no_declare_migrates_without_declaring(self):
        """The two acts are separable: a user may want the shape fixed and
        want to read it before saying it is theirs."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        rc, out, _ = p.run("apply", "--no-declare")
        self.assertFalse((p.root / ".perry" / "conformance.md").exists())
        self.assertEqual(p.lint_errors(), 0)

    def test_the_gate_refusal_names_the_migration_and_the_dry_run(self):
        """`risk-add`'s shape: the count, the command, and the preview. Before
        this task the only command it could name reported the problem and
        fixed nothing."""
        C = load("perry_conform_for_message", CONFORM)
        v = C.Verdict(path="BOARD.md", state=C.UNDECLARED, shape_version=2,
                      errors=[object(), object(), object()])
        msg = C.message_for(v, "perry-task", None)
        commands = [l.strip() for l in msg.split("\n")]
        self.assertIn("3 error(s)", msg)
        self.assertIn("perry-migrate", commands, "the dry run, on its own line")
        self.assertIn("perry-migrate apply", commands)
        for line in msg.split("\n"):
            if line.strip().startswith("perry-"):
                self.assertTrue((PERRY_HOME / "bin" / line.split()[0]).exists(),
                                f"names a tool that does not exist: {line}")

    def test_a_migrated_file_can_be_written_to_under_an_enforcing_gate(self):
        """The point of the whole exercise: after migration the writers work."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        env = dict(os.environ, PERRY_CONFORMANCE="enforce")
        add = ["add", "--title", "a row", "--group", "P2",
               "--deliverable", "a thing that exists afterwards",
               "--verification", "the suite is green", "--root", str(p.root)]
        r = subprocess.run(["python3", str(TASK), *add], capture_output=True,
                           text=True, env=env)
        self.assertEqual(r.returncode, 1, "unmigrated must refuse")
        p.run("apply")
        r = subprocess.run(["python3", str(TASK), *add], capture_output=True,
                           text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


# ── 5 · partial migration is a state, not a failure ───────────────────────


class TestPartialIsAState(unittest.TestCase):

    def test_a_file_that_cannot_reach_conformance_is_left_byte_identical(self):
        """"Valid" for an incomplete migration means: every file is either
        exactly as its author left it, or conformant. Never in between — a file
        that changed and is still read-only is the worst of both."""
        p = Project({"BOARD.md": UNRESOLVABLE_BOARD})
        before = p.text("BOARD.md")
        rc, out, _ = p.run("apply")
        self.assertEqual(p.text("BOARD.md"), before)
        self.assertEqual(rc, 1)
        blocked = edit_for(p.plan(), "BOARD.md")
        self.assertTrue(blocked.residual)
        self.assertFalse(blocked.writable)

    def test_one_file_migrates_while_another_does_not_and_both_halves_work(self):
        p = Project({"BOARD.md": UNRESOLVABLE_BOARD,
                     "design/DESIGN-001-x.md": LEGACY_DESIGN})
        board_before = p.text("BOARD.md")
        p.run("apply")
        self.assertEqual(p.text("BOARD.md"), board_before)
        rc, out, _ = p.run("check", "design/DESIGN-001-x.md", tool=CONFORM)
        self.assertEqual(out["state"], "conformant")
        rc, out, _ = p.run("check", "BOARD.md", tool=CONFORM)
        self.assertEqual(out["state"], "undeclared")

    def test_only_migrates_the_named_file_and_nothing_else(self):
        p = Project({"BOARD.md": LEGACY_BOARD,
                     "design/DESIGN-001-x.md": LEGACY_DESIGN})
        design_before = p.text("design/DESIGN-001-x.md")
        p.run("apply", "--only", "BOARD.md")
        self.assertEqual(p.text("design/DESIGN-001-x.md"), design_before)
        self.assertNotEqual(p.text("BOARD.md"), LEGACY_BOARD)

    def test_the_refusal_names_the_finding_that_blocked_the_file(self):
        p = Project({"BOARD.md": UNRESOLVABLE_BOARD})
        rc, out, _ = p.run(json_out=False)
        self.assertIn("left byte-identical", out)
        self.assertIn("half-done", out)


# ── 6 · what must change, and what is merely different ────────────────────


class TestTheVocabularyIsNotRewritten(unittest.TestCase):

    def test_a_heading_the_project_chose_is_never_renamed_or_moved(self):
        """`## Open — investment line` is 41 rows on the real project.
        `bin/perry-task` already reads such a section as a `group`; renaming it
        would be Perry deciding what someone's workstream is called."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        after = p.text("BOARD.md")
        self.assertIn("## Open — investment line (policy · allocation)", after)
        self.assertIn("## Open — engineering line · phase #004", after)
        self.assertIn("## P2 (low priority carry)", after,
                      "the parenthetical is the author's; only the P2 prefix "
                      "is Perry's")

    def test_rows_are_never_moved_into_the_priority_sections_perry_creates(self):
        """The sections Perry adds are empty. Filing someone's task as P0 or P1
        is a decision about their work, and nothing in the file states it."""
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        lines = p.text("BOARD.md").split("\n")
        i = lines.index("## P0")
        block = lines[i:i + 6]
        self.assertFalse([l for l in block if l.startswith("|") and "---" not in l
                          and "ID" not in l],
                         f"## P0 must be created empty, got {block}")
        own = p.text("BOARD.md").split("## Open — investment line")[1].split("\n##")[0]
        self.assertIn("| INV-DRAFT-1 |", own,
                      "the rows must still be under the heading their author "
                      "filed them under")

    def test_a_table_sharing_no_column_with_the_schemas_is_not_widened(self):
        """A `| seed | Owner | Deliverable |` under `## Objective 1` is not
        Perry's phase-KR table. Bolting four empty columns onto it would be
        writing into a table Perry does not recognise."""
        phase = ("# Phase #001 — x\n\n> **Started**: 2026-01-01\n"
                 "> **Status**: active\n\n"
                 "## Phase Focus\n\nf\n\n## Operating Rules\n\nr\n\n"
                 "## Cost Ceiling\n\nc\n\n## User Commitments\n\nu\n\n"
                 "## User-Unavailable Degradation\n\nd\n\n"
                 "## Phase Scope Reduction Rule\n\ns\n\n"
                 "## Objective 1 — a\n\n| seed | Owner | Deliverable |\n|---|---|---|\n"
                 "| s1 | User | a thing |\n\n"
                 "## Definition of Done\n\nd\n\n## Not Doing in this phase\n\nn\n\n"
                 "## Process Note\n\np\n")
        p = Project({"BOARD.md": LEGACY_BOARD, "phase/001-x.md": phase})
        p.run("apply")
        self.assertEqual(p.text("phase/001-x.md"), phase,
                         "the file must be left exactly as found")
        e = edit_for(p.plan(), "phase/001-x.md")
        self.assertTrue(any(f.rule == "table-columns" for f in e.residual))

    def test_a_table_perry_recognises_is_widened_and_every_row_padded(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        after = p.text("BOARD.md")
        block = after.split("## P2 (low priority carry)")[1].split("\n##")[0]
        self.assertIn("| ID | Title | Owner | Status | Next action | Evidence |", block)
        row = next(l for l in block.split("\n") if "ENG-9" in l)
        self.assertEqual(len(row.strip().strip("|").split("|")), 6, row)
        self.assertIn("conftest has no DB isolation", row)

    def test_an_ambiguous_enum_value_is_never_guessed(self):
        """Two candidates means the migration does not know. A tool that picked
        one would be inventing a fact about somebody's design doc."""
        doc = LEGACY_DESIGN.replace(
            "> **Status**: v1.1 LOCKED 2026-05-19 PM BJT** (Amendments A+B applied; v1.0 LOCKED 2026-05-18)",
            "> **Status**: superseded by the locked v2")
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": doc})
        p.run("apply")
        self.assertEqual(p.text("design/DESIGN-001-x.md"), doc)

    def test_an_enum_spelling_resolves_only_through_the_declared_glossary(self):
        allowed = SCHEMA["enums"]["phase_status"]
        aliases = SCHEMA["migration"]["enum_aliases"]["phase_status"]
        self.assertEqual(M.enum_candidates("进行中", allowed, aliases), ["active"])
        self.assertEqual(M.enum_candidates("已评分（2026-06-10 score-phase；承诺 10/11）",
                                           allowed, aliases), ["scored"])
        self.assertEqual(M.enum_candidates("洽谈中", allowed, aliases), [],
                         "an unlisted spelling is not guessed at")

    def test_a_localized_project_gets_localized_headings_and_columns(self):
        """`bin/perry-task.ensure_section` localizes the sections it creates.
        A migration that hardcoded English would leave a board in two
        languages."""
        board = LEGACY_BOARD.replace("## Cadence\n", "## 例行节奏 (was Cadence)\n")
        board = board.replace("## Top risks\n\n- the RM has not replied since November\n", "")
        p = Project({"BOARD.md": board}, config=CONFIG_ZH)
        p.run("apply")
        after = p.text("BOARD.md")
        self.assertIn("| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |", after)
        self.assertIn("## 主要风险", after,
                      "a section Perry creates is named in the project's own "
                      "language, like the ones `perry-task` creates")
        self.assertEqual(p.lint_errors(), 0,
                         "a localized board Perry created must lint clean")

    def test_a_column_added_to_a_localized_table_matches_the_table_it_joins(self):
        """The spelling comes off the table's own header, not off the config:
        a new column has to match the row it is joining, and the header is the
        only thing that states that without a second file being right."""
        board = LEGACY_BOARD.replace(
            "| ID | Title | Owner | Status |\n|---|---|---|---|\n"
            "| ENG-9 | conftest has no DB isolation | Coding Agent | not_started |",
            "| 编号 | 标题 | 负责人 | 状态 |\n|---|---|---|---|\n"
            "| ENG-9 | conftest has no DB isolation | Coding Agent | not_started |")
        p = Project({"BOARD.md": board}, config=CONFIG_ZH)
        p.run("apply")
        block = p.text("BOARD.md").split("## P2 (low priority carry)")[1].split("\n##")[0]
        self.assertIn("| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |", block)

    def test_a_field_that_only_appears_in_a_table_row_is_never_rewritten(self):
        """`perry-lint` searches the whole file, so the field it validates is
        whichever comes first. Rewriting one that lives in a table row would
        put a `|` inside the row and turn one cell into two."""
        lines = ["| Status: draft | x |", "> **Status**: locked"]
        idx, _ = M.field_line(lines, "Status", DESIGN_SPEC, SCHEMA)
        self.assertIsNone(idx)

    def test_a_minted_source_id_never_collides_with_one_already_in_the_tree(self):
        """An id is an address, not a claim — but an address that is already
        taken re-points somebody's citation."""
        old = ("# old\n\n> Id: SRC-9\n> Source: x\n> Received: 2026-01-01\n"
               "> Status: active\n")
        p = Project({"BOARD.md": LEGACY_BOARD, "knowledge/a/old.md": old,
                     "knowledge/a/new.md": "# new\n\n> Source: y\n"})
        p.run("apply")
        self.assertIn("SRC-10", p.text("knowledge/a/new.md"))
        self.assertEqual(p.text("knowledge/a/old.md"), old)

    def test_warnings_are_never_acted_on(self):
        """Migration changes shape, not quality. Some of this schema's warnings
        are time-dependent, and a migration that chased them would rewrite a
        file because a calendar boundary passed."""
        # A design doc in `draft` with no `## Implementation plan` (a warning
        # today, an error the moment its Status says `locked`) AND no `Date`
        # (an error now). The migration must fix the second and leave the
        # first — a file with a real error is exactly where a transform driven
        # off the spec rather than off the findings starts overreaching.
        doc = LEGACY_DESIGN.replace(
            "> **Status**: v1.1 LOCKED 2026-05-19 PM BJT** (Amendments A+B applied; v1.0 LOCKED 2026-05-18)",
            "> **Status**: draft").replace(
            "## 6. Implementation plan\n\nDo the thing.\n", "").replace(
            "> **Date**: 2026-05-18\n", "")
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": doc})
        p.run("apply")
        after = p.text("design/DESIGN-001-x.md")
        self.assertIn("Date", after, "the error must be fixed")
        self.assertNotIn("## Implementation plan", after,
                         "a section that is only a warning must not be inserted")
        r = subprocess.run(["python3", str(LINT), "--root", str(p.root), "--json"],
                           capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(out["errors"], 0)
        self.assertTrue([f for f in out["findings"] if f["severity"] == "warn"],
                        "the fixture must still carry a warning afterwards")

    def test_perrys_own_machine_written_files_are_never_edited(self):
        """A shape error in a diagnosis or an adoption dossier is a defect in
        the tool that wrote it. Rewriting a finding's status to satisfy an enum
        would be editing a diagnostic record."""
        dossier = ("---\ndiagnosis: 1\nstage: read\nfindings:\n"
                   "  - id: LOAD-02\n    severity: error\n    source: read\n"
                   "    status: false_positive\n---\n\n# Diagnosis\n")
        p = Project({"BOARD.md": LEGACY_BOARD,
                     ".perry/diagnose/2026-08-17-diagnosis.md": dossier})
        rc, out, _ = p.run("apply")
        self.assertEqual(p.text(".perry/diagnose/2026-08-17-diagnosis.md"), dossier)
        self.assertTrue(any(s["path"].endswith("diagnosis.md")
                            for s in out["skipped"]), out["skipped"])


# ── 7 · the near-empty project ────────────────────────────────────────────


class TestTheNearEmptyProject(unittest.TestCase):

    def test_a_project_with_no_perry_state_is_refused_in_one_sentence(self):
        """The other real case. The failure mode here is a tool that finds
        nothing to do and says so at length, or half-builds a structure."""
        p = Project({"README.md": "# hello\n"}, config="")
        (p.root / ".perry" / "config.md").unlink()
        rc, out, err = p.run(json_out=False)
        self.assertEqual(rc, 1)
        said = (out if isinstance(out, str) else "") + err
        self.assertIn("perry adopt", said)
        self.assertLess(len(said.strip().split("\n")), 8)
        self.assertEqual(p.text("README.md"), "# hello\n")

    def test_a_conformant_project_is_told_there_is_nothing_to_do(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        p.run("apply")
        rc, out, _ = p.run(json_out=False)
        self.assertEqual(rc, 0)
        self.assertIn("nothing to migrate", out)


# ── 8 · one definition of the shape ───────────────────────────────────────


class TestOneDefinitionOfTheShape(unittest.TestCase):

    def test_the_migration_holds_no_opinion_about_what_perrys_shape_is(self):
        """It proposes edits; `perry-lint.check_file` judges them. If this file
        grew its own copy of the rules, the two would drift — which is the
        defect ADR-004 exists to end."""
        body = MIGRATE.read_text()
        self.assertNotIn("def check_file", body)
        self.assertIn("lint().check_file", body)

    def test_every_file_it_writes_lints_clean_by_perry_lints_own_reckoning(self):
        p = Project({"BOARD.md": LEGACY_BOARD,
                     "design/DESIGN-001-x.md": LEGACY_DESIGN})
        rc, out, _ = p.run("apply")
        self.assertEqual(p.lint_errors(), 0)
        for f in out["files"]:
            if f["writable"]:
                self.assertEqual(f["after_errors"], 0, f["path"])

    def test_the_shape_version_declared_is_the_schemas_own(self):
        p = Project({"BOARD.md": LEGACY_BOARD})
        _, out, _ = p.run()
        self.assertEqual(out["shape_version"], SCHEMA["schema_version"])

    def test_a_section_label_that_is_a_pattern_is_never_written_as_a_heading(self):
        """`## Objective <N> — <title>` and `## §1 … §8 (eight fixed sections)`
        describe a family. Writing one verbatim would insert punctuation as a
        section title."""
        for spec in SCHEMA["files"]:
            for req in spec.get("headings", []):
                label = M.literal_label(req)
                if label is None:
                    continue
                self.assertNotRegex(label, r"[<>…()]", f"{spec['path']}: {label}")


class TestAHeaderBlockIsNotAnyQuotedText(unittest.TestCase):
    """A news article sitting in `knowledge/` opens with a third-party-AI
    disclaimer in a blockquote. Migration appended its four header fields to
    that blockquote, so Perry's metadata rendered as the last sentences of
    somebody else's disclaimer — no character lost, the meaning changed.

    Found by the user reading the migrated file. Thirty mutations had passed
    over it, because every one of them asked whether the bytes survived and
    none asked what the file now said.
    """

    #: The real shape, reduced: an H1, prose, a rule, then a quoted disclaimer
    #: whose colon sits *inside* the bold — field-shaped to any pattern.
    ARTICLE = """# AI 船票全球飞涨

**来源：** 财新周刊

---

> **注意：** 本文由第三方AI提炼总结而成，可能与原文真实意图存在偏差。

正文第一段。
"""

    #: A digest Perry wrote: the header block is directly under the H1 and
    #: names fields the schema declares.
    DIGEST = """# Digest — 月度点评

> Source: 用户直接粘贴全文
> Received: 2026-08-12 by chat paste
> Status: active

## 摘要

内容。
"""

    def files(self, text, name="knowledge/market-context/a.md"):
        return {"BOARD.md": LEGACY_BOARD, name: text}

    def block(self, p, rel="knowledge/market-context/a.md"):
        """The contiguous run Perry wrote, not every quoted line in the file —
        the disclaimer is also `> `-prefixed, and counting it was this test's
        own first bug."""
        lines = p.text(rel).split("\n")
        start = next(i for i, l in enumerate(lines) if l.startswith("> Id:"))
        out = []
        while start < len(lines) and lines[start].startswith("> "):
            out.append(lines[start]); start += 1
        return out

    def test_quoted_prose_is_not_joined(self):
        p = Project(files=self.files(self.ARTICLE))
        p.run("apply", "--only", "knowledge/market-context/a.md")
        text = p.text("knowledge/market-context/a.md")
        disclaimer = next(i for i, l in enumerate(text.split("\n"))
                          if "第三方AI" in l)
        after = text.split("\n")[disclaimer + 1]
        self.assertNotIn("Id", after,
                         "the header fields joined a disclaimer that is not a "
                         "header block")

    def test_a_new_block_sits_directly_under_the_h1(self):
        p = Project(files=self.files(self.ARTICLE))
        p.run("apply", "--only", "knowledge/market-context/a.md")
        lines = p.text("knowledge/market-context/a.md").split("\n")
        self.assertTrue(lines[0].startswith("# "))
        self.assertEqual("", lines[1])
        self.assertTrue(lines[2].startswith("> Id:"), lines[:5])

    def test_a_new_block_is_one_language_and_one_colon(self):
        """`i18n.fields` maps `Status` and not `Id`/`Source`/`Received`, so
        translating through it produced three English names and one Chinese in
        a single block. `reference/i18n.md` requires one language per file."""
        p = Project(files=self.files(self.ARTICLE), config=CONFIG_ZH)
        p.run("apply", "--only", "knowledge/market-context/a.md")
        block = self.block(p)
        self.assertEqual(4, len(block), block)
        self.assertTrue(all(": " in l for l in block),
                        f"mixed colon forms in one block: {block}")
        self.assertFalse([l for l in block if "：" in l], block)

    def test_a_new_block_is_never_bolded(self):
        """`perry-lint --provenance` matches `^>\\s*Id\\s*[:：]`; a bolded
        `> **Id**:` does not satisfy it, so bolding a block Perry starts
        breaks the provenance chain the id exists for."""
        p = Project(files=self.files(self.ARTICLE))
        p.run("apply", "--only", "knowledge/market-context/a.md")
        self.assertRegex(p.text("knowledge/market-context/a.md"),
                         r"(?m)^>\s*Id\s*:")

    def test_every_field_lands_in_the_same_block(self):
        """`joining` was recomputed per field, so the first insertion turned a
        fresh block into an existing one and the rest followed the project's
        spelling instead of the schema's."""
        p = Project(files=self.files(self.ARTICLE), config=CONFIG_ZH)
        p.run("apply", "--only", "knowledge/market-context/a.md")
        lines = p.text("knowledge/market-context/a.md").split("\n")
        run = [i for i, l in enumerate(lines) if l.startswith("> Id:")]
        start = run[0]
        contiguous = 0
        while start + contiguous < len(lines) and \
                lines[start + contiguous].startswith("> "):
            contiguous += 1
        self.assertEqual(4, contiguous,
                         "the four fields were split across two blocks")

    def test_a_real_header_block_is_still_joined(self):
        """The discrimination must not cost the behaviour it protects: a
        digest missing only `Id` gets it appended to the block it has."""
        p = Project(files=self.files(self.DIGEST, "knowledge/x/d.md"))
        p.run("apply", "--only", "knowledge/x/d.md")
        lines = p.text("knowledge/x/d.md").split("\n")
        quoted = [i for i, l in enumerate(lines) if l.startswith("> ")]
        self.assertEqual(list(range(quoted[0], quoted[0] + len(quoted))), quoted,
                         "the digest's header block was split")
        self.assertEqual(4, len(quoted))


# ── 9 · a table, a value and a sentence are recognised by vocabulary ───────


class TestRecognitionIsByVocabularyNotByShape(unittest.TestCase):
    """TASK-051. Three transforms recognised their target by shape, and the
    three commonest words in any markdown table — `ID`, `Status`, `Owner` — are
    enough shape to be mistaken for Perry's.

    Every case below preserves every character, every cell, every id, every
    per-section row count, and declares every line it rewrites. That is TASK-052
    and it is asserted in § 10.
    """

    #: A legend under a heading `^P[012]\b` matches. Two rows, two columns, one
    #: of which is `ID` — and ADR-004's own Context table cites this exact shape
    #: as the reason ADR-004 exists.
    LEGEND_BOARD = """# Board — Legacy

> Last updated: 2026-01-04

## P0 holding

A legend, not a task table:

| ID | Meaning |
|---|---|
| INV-* | investments |
| ENG-* | engineering |

## Cadence

| ID | Recurring task | Owner | Frequency | Next due |
|---|---|---|---|---|
| CAD-1 | weekly reconcile | User | weekly | 2026-01-11 |
"""

    def test_a_legend_that_shares_one_column_name_is_not_widened(self):
        """One shared word is a coincidence, not a vocabulary. Before this,
        migration appended five columns to the legend, every lint error went to
        zero, the conformance marker declared the board conformant, and
        `perry-task list` returned two tasks with the ids `INV-` and `ENG-` and
        no titles — through a frozen contract, on a board a reader had
        correctly refused."""
        p = Project({"BOARD.md": self.LEGEND_BOARD})
        before = p.text("BOARD.md")
        p.run("apply")
        self.assertEqual(p.text("BOARD.md"), before,
                         "the legend was widened into a task table")
        self.assertNotIn("| ID | Meaning | Title |", p.text("BOARD.md"))
        self.assertFalse((p.root / ".perry" / "conformance.md").exists(),
                         "a board that was correctly refused must not be "
                         "declared conformant")

    def test_the_reader_still_refuses_the_legend_after_the_run(self):
        """The harm was never the columns; it was `perry-task list` returning
        rows built from the legend's own cells. Asserted through the reader, not
        through the file."""
        p = Project({"BOARD.md": self.LEGEND_BOARD})
        p.run("apply")
        r = subprocess.run(["python3", str(TASK), "list", "--all", "--json",
                            "--root", str(p.root)], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(out["tasks"], [], "the legend's rows became tasks")
        self.assertEqual(out["conformance"]["sections_skipped"], [])

    def test_a_table_missing_a_minority_of_the_schemas_names_is_still_widened(self):
        """The discrimination must not cost the behaviour it protects. The
        four-column `## P2` this suite was built around — the real one on
        `~/proj/gimegime-pmo` — is 4 of the board's 6 and must still widen.
        Covered by `test_a_table_perry_recognises_is_widened_and_every_row_padded`
        end to end; stated here at the boundary."""
        cols = ["ID", "Title", "Owner", "Status", "Next action", "Evidence"]
        L = M.lint()
        sat = lambda c, got: any(a in got for a in L.accepted(c))
        got = lambda names: [L.norm(n) for n in names]
        self.assertTrue(M.is_the_schemas_table(
            {"columns": cols}, got(["ID", "Title", "Owner", "Status"]), sat),
            "4 of 6 is the table this transform exists for")
        self.assertTrue(M.is_the_schemas_table(
            {"columns": cols},
            got(["ID", "Title", "Owner", "Status", "備考", "负责小组"]), sat),
            "columns the author added are not counted against the table")

    def test_a_minority_of_the_schemas_names_is_not_a_vocabulary(self):
        """The boundary itself. `| ID | Meaning |` is one of six and
        `| ID | Title |` is two of six: both are refused, and refusing the
        second is the stated cost of the rule — that file is reported and left
        byte-identical rather than turned into a table by Perry."""
        cols = ["ID", "Title", "Owner", "Status", "Next action", "Evidence"]
        L = M.lint()
        sat = lambda c, got: any(a in got for a in L.accepted(c))
        got = lambda names: [L.norm(n) for n in names]
        self.assertFalse(M.is_the_schemas_table(
            {"columns": cols}, got(["ID", "Meaning"]), sat))
        self.assertFalse(M.is_the_schemas_table(
            {"columns": cols}, got(["ID", "Title"]), sat))
        self.assertFalse(M.is_the_schemas_table(
            {"columns": cols}, got(["ID", "Title", "Owner"]), sat),
            "three of six is a tie, and a tie is not a majority")

    def test_a_status_that_says_it_is_not_locked_is_not_read_as_locked(self):
        """`test_an_ambiguous_enum_value_is_never_guessed` covers two candidates
        and none. It cannot cover *one wrong* candidate, and one hit was treated
        as certainty: `> Status: not yet locked — do not build from this` was
        written as `locked | not yet locked — do not build from this`. Every
        character survives and the claim is reversed."""
        doc = LEGACY_DESIGN.replace(
            "> **Status**: v1.1 LOCKED 2026-05-19 PM BJT** "
            "(Amendments A+B applied; v1.0 LOCKED 2026-05-18)",
            "> **Status**: not yet locked — do not build from this")
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": doc})
        p.run("apply")
        self.assertEqual(p.text("design/DESIGN-001-x.md"), doc,
                         "a value that says only what it is NOT was resolved")
        allowed = SCHEMA["enums"]["design_status"]
        neg = SCHEMA["migration"]["negations"]
        self.assertEqual(
            M.enum_candidates("not yet locked — do not build from this",
                              allowed, {}, neg), [])

    def test_a_negator_past_a_clause_boundary_does_not_deny_the_value(self):
        """The window is the clause the token sits in, not the whole value. A
        negator that governs a different clause — `not a draft; locked
        2026-05-19` — must leave `locked` standing, or every value carrying the
        word `not` anywhere becomes unresolvable."""
        allowed = SCHEMA["enums"]["design_status"]
        neg = SCHEMA["migration"]["negations"]
        self.assertEqual(
            M.enum_candidates("not a draft; locked 2026-05-19", allowed, {}, neg),
            ["locked"])
        self.assertEqual(
            M.enum_candidates("已评分，不再改动",
                              SCHEMA["enums"]["phase_status"],
                              SCHEMA["migration"]["enum_aliases"]["phase_status"],
                              neg),
            ["scored"], "a denial after the token denies the clause after it")

    def test_body_prose_that_mentions_a_field_is_never_rewritten(self):
        """`field_line` guarded only `is_row`/`is_separator`, and sentences are
        field-shaped. Perry's own repo carries the trigger at
        `perry/design/DESIGN-001-resumable-pipelines.md:126`."""
        doc = LEGACY_DESIGN.replace(
            "# DESIGN-001: the thing\n",
            "# DESIGN-001: the thing\n\nBackground: the vendor contract "
            "Status: superseded by the 2025 MSA, so we rebuilt.\n")
        p = Project({"BOARD.md": LEGACY_BOARD, "design/DESIGN-001-x.md": doc})
        p.run("apply")
        after = p.text("design/DESIGN-001-x.md")
        self.assertIn("Background: the vendor contract Status: superseded by "
                      "the 2025 MSA, so we rebuilt.", after)
        self.assertNotIn("superseded | superseded", after)

    def test_a_field_shaped_sentence_in_the_body_is_not_the_header_field(self):
        """At the unit, because two mechanisms now produce the same file: the
        transform declines the line and `meaning()` would refuse the write. This
        is the first of them, and the second assertion is the contract that
        keeps them from disagreeing — *presence* has to stay what `perry-lint`
        means by it, or `fix_missing_fields` adds a second `Status` while the
        linter goes on reading the first."""
        lines = ["# D", "",
                 "Background: the vendor contract Status: superseded by the "
                 "2025 MSA, so we rebuilt.", "", "> **Status**: draft"]
        idx, m = M.field_line(lines, "Status", DESIGN_SPEC, SCHEMA)
        self.assertIsNone(idx, "a sentence is not Perry's to write into")
        self.assertIn("superseded", m.group(1),
                      "the line reported must be the one the linter validates")

    def test_the_field_the_header_block_holds_is_still_rewritten(self):
        """The counterpart: refusing prose must not cost the transform. The
        same document with no prose sentence still gets its status
        normalized."""
        p = Project({"BOARD.md": LEGACY_BOARD,
                     "design/DESIGN-001-x.md": LEGACY_DESIGN})
        p.run("apply")
        line = next(l for l in p.text("design/DESIGN-001-x.md").split("\n")
                    if "Status" in l)
        self.assertTrue(line.split("|")[0].strip().endswith("locked"), line)


# ── 10 · what the file now says ───────────────────────────────────────────


class TestAColumnSplitIsNotAColumnAdd(unittest.TestCase):
    """TASK-091. `OKR.md § Commitments` traded one `By when` column for a typed
    `Due` plus a prose `By when note` (ADR-007, decision 3).

    T2's whole job is appending a column the schema declares and the file
    lacks, and doing that here is worse than doing nothing: the table ends up
    with an empty `Due`, every promise's clock still in the retired column, and
    `perry-lint` reporting zero errors. A file that looks migrated and is not
    is the failure ADR-004 exists to prevent, so this transform stands aside
    and names the command that owns the values."""

    PRE_SPLIT = """# OKR — legacy

## Mission

Ship it.

## Operating Principles

- one

## Commitments

| Id | Track | Promise | To whom | By when | Status |
|---|---|---|---|---|---|
| ops/1 | ops | Invoices | Finance | within the track SLA | active |
| rel/1 | rel | Release | Users | 2027-01-01 | active |

## Anti-Goals

- not this

## v1: 2026-01-01

### Objective 1 — ship

## Versioning log

- v1: 2026-01-01 — initial.
"""

    PRE_SPLIT_CN = PRE_SPLIT.replace(
        "| Id | Track | Promise | To whom | By when | Status |",
        "| 编号 | 轨道 | 承诺内容 | 承诺对象 | 截止 | 状态 |").replace(
        "| ops/1 | ops | Invoices | Finance | within the track SLA | active |",
        "| ops/1 | ops | 对账 | 财务 | 下周期 | active |")

    TRACKS = (CONFIG_EN +
              "\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | commitments | intake -> doing | — | 5d | weekly | V2 |\n"
              "| rel | pipeline | commitments | draft -> shipped | 3 | 10d | weekly | V3 |\n")

    def project(self):
        return Project({"OKR.md": self.PRE_SPLIT})

    def test_the_table_is_left_byte_identical(self):
        p = self.project()
        before = p.text("OKR.md")
        p.run("apply")
        self.assertEqual(before, p.text("OKR.md"),
                         "an empty `Due` was bolted onto a pre-split register")

    def test_the_finding_names_the_command_that_owns_the_values(self):
        p = self.project()
        _, out, _ = p.run()
        kinds = [c["kind"] for e in out["files"] for c in e["changes"]]
        self.assertIn("split-needed", kinds, out)
        detail = next(c["detail"] for e in out["files"] for c in e["changes"]
                      if c["kind"] == "split-needed")
        self.assertIn("perry-goals commit --migrate", detail)

    def test_it_is_reported_once_and_not_once_per_pass(self):
        """`migrate_text` runs the transforms until the linter stops finding
        fixable things, and this one is never fixable — so it is seen on every
        pass. Printed twice it reads as two tables."""
        p = self.project()
        _, out, _ = p.run()
        kinds = [c["kind"] for e in out["files"] for c in e["changes"]]
        self.assertEqual(1, kinds.count("split-needed"), kinds)

    def test_a_register_already_split_is_not_touched_either(self):
        p = Project({"OKR.md": self.PRE_SPLIT.replace(
            "| To whom | By when | Status |",
            "| To whom | Due | Status |")})
        before = p.text("OKR.md")
        p.run("apply")
        self.assertEqual(before, p.text("OKR.md"))
        _, out, _ = p.run()
        kinds = [c["kind"] for e in out["files"] for c in e["changes"]]
        self.assertNotIn("split-needed", kinds,
                         "a migrated register was reported as needing it")

    def test_chinese_pre_split_is_an_error_not_nothing_to_migrate(self):
        p = Project({"OKR.md": self.PRE_SPLIT_CN}, config=CONFIG_ZH)
        before = p.text("OKR.md")

        dry_rc, dry, _ = p.run()
        apply_rc, applied, _ = p.run("apply")

        self.assertEqual((dry_rc, apply_rc), (1, 1))
        self.assertEqual(before, p.text("OKR.md"))
        dry_file = next(f for f in dry["files"] if f["path"] == "OKR.md")
        apply_file = next(f for f in applied["files"] if f["path"] == "OKR.md")
        self.assertEqual(dry_file["residual"], apply_file["residual"],
                         "dry-run and apply classified the same cell differently")
        self.assertEqual([f["rule"] for f in dry_file["residual"]],
                         ["bad-typed-cell"])
        self.assertFalse(dry_file["writable"])

        rc, out, _ = p.run(json_out=False)
        self.assertEqual(rc, 1)
        self.assertNotIn("nothing to migrate", out)
        self.assertIn("bad-typed-cell", out)

    def test_migration_lint_uses_the_project_track_context(self):
        split = self.PRE_SPLIT.replace("| By when |", "| Due |")
        pipeline_bad = split.replace("within the track SLA", "2027-02-01") \
                            .replace("2027-01-01", "3d")
        queue_bad = split.replace("within the track SLA", "2027-02-01")
        no_clock = self.TRACKS.replace("| ops | queue | commitments | intake -> doing | — | 5d |",
                                       "| ops | queue | commitments | intake -> doing | — |  |")

        for text, config, phrase in (
                (pipeline_bad, self.TRACKS, "pipeline track requires"),
                (queue_bad, no_clock, "queue track has no declared clock")):
            with self.subTest(phrase=phrase):
                p = Project({"OKR.md": text}, config=config)
                rc, out, _ = p.run()
                self.assertEqual(rc, 1)
                residual = next(f for f in out["files"]
                                if f["path"] == "OKR.md")["residual"]
                self.assertEqual([f["rule"] for f in residual], ["bad-typed-cell"])
                self.assertIn(phrase, residual[0]["message"])

    def test_migration_lint_uses_localized_track_headers(self):
        split = self.PRE_SPLIT.replace("| By when |", "| Due |")
        pipeline_bad = split.replace("within the track SLA", "2027-02-01") \
                            .replace("2027-01-01", "3d")
        queue_bad = split.replace("within the track SLA", "2027-02-01")
        tracks = (CONFIG_ZH +
                  "\n## 轨道\n\n"
                  "| 轨道 | 模式 | 时限 |\n"
                  "|---|---|---|\n"
                  "| ops | queue | 5d |\n"
                  "| rel | pipeline | 10d |\n")
        no_clock = tracks.replace("| ops | queue | 5d |",
                                  "| ops | queue | |")

        for text, config, phrase in (
                (pipeline_bad, tracks, "pipeline track requires"),
                (queue_bad, no_clock, "queue track has no declared clock")):
            with self.subTest(phrase=phrase):
                p = Project({"OKR.md": text}, config=config)
                rc, out, _ = p.run()
                self.assertEqual(rc, 1)
                residual = next(f for f in out["files"]
                                if f["path"] == "OKR.md")["residual"]
                self.assertEqual([f["rule"] for f in residual], ["bad-typed-cell"])
                self.assertIn(phrase, residual[0]["message"])


class TestTheAssertionsAskWhatTheFileSays(unittest.TestCase):
    """TASK-052. Every assertion in `losslessness()` answers *is it all still
    there*. None answers *does it still mean that*, which is why thirty
    mutations found none of § 9.

    There is no single check that sees all three; `meaning()` is three readings,
    each stating what it cannot see. These tests assert the split explicitly —
    that the old assertions are silent on inputs the new ones refuse — because a
    claim that a check is needed is only worth as much as the demonstration that
    the existing ones do not make it.
    """

    BEFORE = ("# Board\n\n## P0 holding\n\n| ID | Meaning |\n|---|---|\n"
              "| INV-* | investments |\n")
    AFTER = ("# Board\n\n## P0 holding\n\n"
             "| ID | Meaning | Title | Owner | Status | Next action | Evidence |\n"
             "|---|---|---|---|---|---|---|\n"
             "| INV-* | investments |  |  |  |  |  |\n")

    def test_inventing_a_record_survives_every_losslessness_assertion(self):
        """The premise of the whole task, asserted rather than argued."""
        rewritten = [l for l in self.BEFORE.split("\n") if l.startswith("|")]
        self.assertEqual(M.losslessness(self.BEFORE, self.AFTER, rewritten), [],
                         "if this ever fails, `meaning()` has a cheaper twin")

    def test_a_record_perry_could_not_read_before_and_reads_now_is_refused(self):
        """`viewer/parsers` is the reader, not a second opinion written here."""
        bad = M.meaning(self.BEFORE, self.AFTER, "BOARD.md", BOARD_SPEC, SCHEMA)
        self.assertTrue(any("task(s) Perry did not read before" in b
                            for b in bad), bad)

    def test_widening_a_table_perry_recognises_changes_no_reading(self):
        """The negative control. A check that refused every widening would pass
        the test above and destroy the transform."""
        before = ("# Board\n\n## P2\n\n| ID | Title | Owner | Status |\n"
                  "|---|---|---|---|\n| ENG-9 | no DB isolation | User | done |\n")
        after = ("# Board\n\n## P2\n\n"
                 "| ID | Title | Owner | Status | Next action | Evidence |\n"
                 "|---|---|---|---|---|---|\n"
                 "| ENG-9 | no DB isolation | User | done |  |  |\n")
        self.assertEqual(M.meaning(before, after, "BOARD.md", BOARD_SPEC, SCHEMA),
                         [])

    def test_a_sentence_that_gained_a_word_is_refused(self):
        """Prose is not Perry's to write into, and this is the check that says
        so without knowing which transform did it."""
        before = ("# D\n\nBackground: the vendor contract Status: superseded "
                  "by the 2025 MSA.\n\n> **Status**: draft\n")
        after = before.replace("Status: superseded by",
                               "Status: superseded | superseded by")
        self.assertEqual(M.losslessness(
            before, after, [l for l in before.split("\n") if l.strip()]), [],
            "the byte-level assertions are silent on this")
        bad = M.meaning(before, after, "design/DESIGN-001-x.md", DESIGN_SPEC,
                        SCHEMA)
        self.assertTrue(any("neither a table row nor part of the header block"
                            in b for b in bad), bad)

    def test_a_canonical_value_the_authors_own_words_deny_is_refused(self):
        """The migration keeps the author's value beside the one it wrote, so
        the file carries its own evidence and this can re-read it."""
        before = "# D\n\n> **Status**: not yet locked — do not build\n"
        after = "# D\n\n> **Status**: locked | not yet locked — do not build\n"
        self.assertEqual(M.losslessness(
            before, after, ["> **Status**: not yet locked — do not build"]), [],
            "the byte-level assertions are silent on this")
        bad = M.meaning(before, after, "design/DESIGN-001-x.md", DESIGN_SPEC,
                        SCHEMA)
        self.assertTrue(any("does not say" in b for b in bad), bad)

    def test_a_cell_can_be_lost_while_every_character_survives(self):
        """Why the cell count is checked on its own — and the test it did not
        have. Replacing `cells(before) - cells(after)` with an empty `Counter()`
        left all 823 tests green, so the assertion was unguarded: every input
        that lost a cell also lost a character, a row or an id.

        Two cells re-cut across the same boundary keep every character, every
        `|`, the row, the section and the id set, and are not the same two
        cells."""
        before = "| ab | c |"
        after = "| a | bc |"
        bad = M.losslessness(before, after, [before])
        self.assertEqual([b for b in bad if "cell(s)" not in b], [],
                         "no other check may fire on this input")
        self.assertTrue(any("cell(s) lost" in b for b in bad), bad)

    def test_the_assertion_catches_what_the_transform_lets_through(self):
        """Why it is an assertion and not a code review, and the only test that
        can see the wiring: with the vocabulary test disabled — the defect
        exactly as it shipped — the legend is widened and the file is refused
        anyway, by the reading, before a byte is written.

        Both lines of defence are now live, which is why every other test here
        calls `meaning()` directly: the transforms no longer produce an input
        for it. This one puts the defect back."""
        p = Project({"BOARD.md": TestRecognitionIsByVocabularyNotByShape
                     .LEGEND_BOARD})
        real = M.is_the_schemas_table
        M.is_the_schemas_table = lambda *a, **kw: True
        try:
            plan = p.plan()
        finally:
            M.is_the_schemas_table = real
        e = edit_for(plan, "BOARD.md")
        self.assertTrue(e.touched, "the transform must have widened the legend")
        self.assertEqual(e.residual, [], "and taken it to zero shape errors")
        self.assertTrue(any("did not read before" in v for v in e.violations),
                        e.violations)
        self.assertFalse(e.writable, "an assertion nobody acts on is a comment")

    def test_a_refused_file_is_left_byte_identical_and_the_reason_is_printed(self):
        p = Project({"BOARD.md": TestRecognitionIsByVocabularyNotByShape
                     .LEGEND_BOARD})
        rc, out, _ = p.run(json_out=False)
        self.assertIn("left byte-identical", out)


class TestAMigratedIdIsReadableByItsOwnReader(unittest.TestCase):
    """Migration wrote an id `perry-lint --provenance` could not see.

    `fix_missing_fields` matched the surrounding block's bold style, so a digest
    whose neighbours are bolded got `> **Id**：SRC-n`, and the provenance check
    anchors `^>\\s*Id\\s*[:：]` literally. Measured on a migrated copy of a real
    project: 3 of 15 provenance findings were files migration had **just given
    an id to**, every one then declared conformant. Migration minted an id
    nothing could cite, which is the one thing the id is for.

    `header_block_end`'s docstring already named the hazard and named it one
    case too narrow — "a digest whose neighbours are *plain* must get a plain
    line" — when the dangerous case is neighbours who are bold.

    The fixture is deliberately **not** Perry-generated: a block Perry starts is
    never bolded, so a Perry-shaped fixture cannot reach this branch at all.
    That is `TASK-044-spec.md`'s governing sentence, and it is why 30 mutations
    walked past this.
    """

    DIGEST = ("# A digest someone else wrote\n"
              "\n"
              "> **Origin**: https://example.invalid/paper\n"
              "> **Fetched**: 2026-01-02\n"
              "\n"
              "Body prose that is not Perry's.\n")

    def test_a_bolded_neighbour_block_still_gets_a_readable_id(self):
        p = Project({"knowledge/research/digest.md": self.DIGEST})
        rc, _, err = p.run("apply")
        self.assertEqual(rc, 0, err)
        text = p.text("knowledge/research/digest.md")
        self.assertNotIn("**Id**", text, f"the id was bolded:\n{text}")
        self.assertRegex(text, r"(?m)^>\s*Id\s*[:：]\s*SRC-\d+",
                         f"not in the form its reader anchors on:\n{text}")

    def test_the_authors_own_bold_style_is_left_alone(self):
        """Perry stops bolding its OWN field. It does not un-bold theirs."""
        p = Project({"knowledge/research/digest.md": self.DIGEST})
        p.run("apply")
        text = p.text("knowledge/research/digest.md")
        self.assertIn("**Origin**", text)
        self.assertIn("**Fetched**", text)


class TestAFailedWriteIsRecoverableAndSaysSo(unittest.TestCase):
    """Guarantee 3 of `TASK-044-spec.md`: the recovery path is **named in the
    output**, and shown working rather than described.

    Only a write that *landed wrong* was handled. A write that **fails** — a
    read-only file, a full disk, a permission revoked mid-run — propagated as an
    unhandled traceback: a stranger's project left N-of-M migrated, the restore
    point on disk and **never named**, the declaration never run, and empty
    stdout. A traceback names nothing.
    """

    def project(self) -> Project:
        return Project(files={
            "BOARD.md": LEGACY_BOARD,
            "knowledge/research/a.md": "# A digest\n\nBody.\n",
            "knowledge/research/b.md": "# Another digest\n\nBody.\n",
        })

    def test_a_failing_write_rolls_back_and_names_the_restore_command(self):
        p = self.project()
        before = p.tree()
        target = None
        for e in M.plan_project(p.root, p.root, SCHEMA).writable:
            target = e.path
            break
        self.assertIsNotNone(target, "nothing writable in the fixture")

        real = M.write_atomic
        calls = {"n": 0}

        def flaky(path, text):
            calls["n"] += 1
            if calls["n"] == 2:          # fail PART WAY, not on the first file
                raise PermissionError(13, "Permission denied", str(path))
            return real(path, text)

        M.write_atomic = flaky
        try:
            with self.assertRaises(M.Refused) as caught:
                M.apply_plan(M.plan_project(p.root, p.root, SCHEMA), SCHEMA)
        finally:
            M.write_atomic = real

        msg = str(caught.exception)
        self.assertIn("perry-migrate restore", msg,
                      f"the recovery command is not named:\n{msg}")
        self.assertIn("Restore point:", msg,
                      f"the restore point path is not named:\n{msg}")
        # Compare the files that existed before. The restore point itself is
        # NEW and must survive the rollback — it is the thing the refusal just
        # told the user to run, and deleting it would make the message a lie.
        after = {k: v for k, v in p.tree().items()
                 if not k.startswith(".perry/migrate/")}
        self.assertEqual(after, before,
                         "the project was left half-migrated")
        self.assertTrue(
            [k for k in p.tree() if k.startswith(".perry/migrate/")],
            "the restore point the refusal names was not kept")

    def test_the_restore_point_is_named_even_when_the_rollback_also_fails(self):
        """The worst case must not be the one that says nothing. `undo` writes,
        so the failure that broke the run can break the repair — and then the
        user needs the path most."""
        point = Path(tempfile.mkdtemp()) / "2026-01-01-000000.json"
        point.write_text("{}")
        real = M.undo
        M.undo = lambda _p: (_ for _ in ()).throw(
            PermissionError(13, "Permission denied"))
        try:
            msg = M.rollback_message(point, "BOARD.md", "boom")
        finally:
            M.undo = real
        self.assertIn("rollback also failed", msg)
        self.assertIn("perry-migrate restore 2026-01-01-000000", msg)
        self.assertIn("still migrated", msg)


class TestNothingWritableIsNotACrash(unittest.TestCase):
    def test_apply_on_a_project_with_no_writable_edit_returns_a_run_key(self):
        """It raised `KeyError: 'run'` in the renderer — a traceback where
        "there was nothing to do" belongs."""
        p = Project(files={"BOARD.md": M.render_board_from_template()
                           if hasattr(M, "render_board_from_template")
                           else LEGACY_BOARD})
        plan = M.plan_project(p.root, p.root, SCHEMA)
        plan.edits = [e for e in plan.edits if False]
        out = M.apply_plan(plan, SCHEMA)
        self.assertIn("run", out)
        self.assertEqual(out["applied"], [])


class TestPositionIsNotEvidence(unittest.TestCase):
    """The fourth instance of one defect, and the branch that produced it.

    `is_header_block` had two ways to qualify, and the second was **position**:
    *"it opens immediately under the H1, which is where the template puts it."*
    Its own first paragraph already said position cannot decide this —
    *"sentences are field-shaped; only the vocabulary tells them apart"* — and
    the fallback said it anyway.

    So a real digest whose author opens with a seed thesis in a blockquote
    directly under the H1 got Perry's four fields appended to the end of that
    paragraph. No character lost; the meaning changed. `ADR-004`'s named
    failure mode: *"a board that still parses and no longer reads like
    theirs."*

    Every fixture here is somebody else's writing. A Perry-generated one cannot
    reach this branch, which is `TASK-044-spec.md`'s governing sentence and the
    reason thirty mutations walked past it.
    """

    THESIS = ("# 某人写的综述\n"
              "\n"
              "> **种子观点**：一段很长的引用，作者自己的论点，"
              "不是任何字段，也不属于 Perry。\n"
              ">\n"
              "> 第二段，同一个引用块里。\n"
              "\n"
              "## 正文\n"
              "\n"
              "内容。\n")

    def test_a_thesis_under_the_h1_is_not_a_header_block(self):
        p = Project({"knowledge/research/survey.md": self.THESIS})
        rc, _, err = p.run("apply")
        self.assertEqual(rc, 0, err)
        text = p.text("knowledge/research/survey.md")
        thesis_line = next(l for l in text.split("\n") if "种子观点" in l)
        after = text.split(thesis_line, 1)[1].split("\n")
        # The line after the author's opening line must still be their own.
        self.assertNotRegex(
            after[1] if len(after) > 1 else "",
            r"^>\s*\**\s*(Id|Source|Received|Status)",
            f"Perry wrote into the author's paragraph:\n{text}")

    def test_perrys_fields_land_in_a_block_of_their_own(self):
        p = Project({"knowledge/research/survey.md": self.THESIS})
        p.run("apply")
        lines = p.text("knowledge/research/survey.md").split("\n")
        i = next(i for i, l in enumerate(lines) if l.startswith("> Id:"))
        # its block must not contain the thesis
        j = i
        while j > 0 and lines[j - 1].strip().startswith(">"):
            j -= 1
        k = i
        while k + 1 < len(lines) and lines[k + 1].strip().startswith(">"):
            k += 1
        block = "\n".join(lines[j:k + 1])
        self.assertNotIn("种子观点", block)

    def test_all_four_fields_stay_together(self):
        """The half that only appeared once Perry started its own block: a
        blank line did not end a `>` run, so the span reached across it into
        the author's quote and the SECOND field onwards landed in their
        paragraph — the same defect, one field later."""
        p = Project({"knowledge/research/survey.md": self.THESIS})
        p.run("apply")
        lines = p.text("knowledge/research/survey.md").split("\n")
        idx = [i for i, l in enumerate(lines)
               if re.match(r"^>\s*(Id|Source|Received|Status)\s*:", l)]
        self.assertEqual(len(idx), 4, lines)
        self.assertEqual(idx, list(range(idx[0], idx[0] + 4)),
                         "the fields were split across blocks")

    def test_a_real_header_block_is_still_joined(self):
        """The vocabulary branch is the one that survived, so a block that
        names a declared field is still written into rather than duplicated."""
        p = Project({"knowledge/research/d.md":
                     "# A digest\n\n> Source: https://example.invalid\n\nBody.\n"})
        p.run("apply")
        text = p.text("knowledge/research/d.md")
        self.assertEqual(text.count("> Source:"), 1)
        self.assertIn("> Id:", text)
        lines = text.split("\n")
        i = lines.index("> Source: https://example.invalid")
        j = i
        while j + 1 < len(lines) and lines[j + 1].strip().startswith(">"):
            j += 1
        while i > 0 and lines[i - 1].strip().startswith(">"):
            i -= 1
        self.assertTrue(
            any(l.startswith("> Id:") for l in lines[i:j + 1]),
            f"a second block was started beside a real header block:\n{text}")

    def test_the_new_block_is_written_in_one_language(self):
        """A joined block inherits its neighbours' spelling; a new one uses the
        schema's. The mixed `Id:` / `状态：` block that appeared on the real
        file was a symptom of joining, and starting a block removes it."""
        p = Project({"knowledge/research/survey.md": self.THESIS})
        p.run("apply")
        text = p.text("knowledge/research/survey.md")
        self.assertNotIn("状态：", text)
        self.assertIn("> Status:", text)


class TestAReadOnlyFileDoesNotCrashPlanning(unittest.TestCase):
    """The crash was one stage upstream of where the first fix guarded.

    `apply_plan` was given a `try/except OSError` that rolls back and names the
    restore point. A V4 reviewer then found the real crash site: `cross_file_delta`
    builds a scratch **mirror** of the state tree during PLANNING, with
    `shutil.copy2`/`copytree`, which preserve mode bits — so a file the project
    has marked read-only produced a read-only copy in a directory Perry owns,
    and the next line wrote to it.

    That is worse than the one that was fixed first: at plan time **there is no
    restore point yet**, so the traceback was the whole of what the user got,
    and it killed `--dry-run` as well as `apply` — the command whose entire
    promise is that it writes nothing.

    Preserving the mode of a throwaway mirror buys nothing.
    """

    FILES = {"BOARD.md": LEGACY_BOARD,
             "knowledge/research/a.md": "# A digest\n\nBody.\n"}

    def read_only_project(self) -> "Project":
        # Kept on `self` so the `Project`'s TemporaryDirectory outlives the
        # test body; and no chmod-back cleanup, because a cleanup that runs
        # after the temp dir is collected is a FileNotFoundError pretending to
        # be a test failure — which is what the first version of this did.
        self._p = Project(files=dict(self.FILES))
        (self._p.root / "BOARD.md").chmod(0o444)
        return self._p

    def test_a_dry_run_survives_a_read_only_file(self):
        p = self.read_only_project()
        rc, out, err = p.run("", json_out=False)
        self.assertEqual(rc, 0, f"planning crashed:\n{err}")
        self.assertNotIn("Traceback", err)

    def test_apply_survives_it_too(self):
        p = self.read_only_project()
        rc, _, err = p.run("apply", json_out=False)
        self.assertEqual(rc, 0, f"apply crashed:\n{err}")
        self.assertNotIn("Traceback", err)

    def test_a_read_only_file_IS_migrated_and_that_is_recorded_not_asserted(self):
        """**This asserts what happens, not what I assumed happened.**

        My first version asserted the file is left alone, on the reasoning that
        `plan.writable` would exclude it. It does not: `write_atomic` writes a
        `.tmp` and calls `Path.replace`, and a **rename needs write permission
        on the directory, not on the target** — so a file the user marked
        read-only is migrated like any other.

        Whether that is right is a policy question about somebody else's files
        and it is not decided here. It is on the board as its own row. What is
        pinned is the behaviour, so the day it changes, it changes on purpose.
        """
        p = self.read_only_project()
        before = (p.root / "BOARD.md").read_bytes()
        p.run("apply", json_out=False)
        self.assertNotEqual((p.root / "BOARD.md").read_bytes(), before,
                            "behaviour changed — see the row on the read-only "
                            "policy before updating this test")

    def test_the_restore_point_carries_the_read_only_file_too(self):
        """Whatever the policy turns out to be, the recovery path must cover a
        file Perry wrote — that is guarantee 3, and it is what makes the
        current behaviour survivable rather than merely undetected."""
        p = self.read_only_project()
        before = (p.root / "BOARD.md").read_bytes()
        p.run("apply", json_out=False)
        points = sorted((p.root / ".perry" / "migrate").glob("*.json"))
        self.assertTrue(points, "no restore point was written")
        payload = json.loads(points[-1].read_text())
        self.assertIn("BOARD.md", payload["files"])
        self.assertEqual(payload["files"]["BOARD.md"].encode(), before)

    def test_the_rest_of_the_project_still_migrates(self):
        """One unwritable file must not stop the run — guarantee 5, partial
        migration is a state rather than a failure."""
        p = self.read_only_project()
        p.run("apply", json_out=False)
        self.assertIn("> Id:", p.text("knowledge/research/a.md"))


class TestEveryWriteSiteIsGuarded(unittest.TestCase):
    """**Three rounds each guarded the site it had seen, not the class.**

    Round 1 caught the edit loop. Round 2 found the crash was one stage
    upstream, in planning's scratch mirror. Round 3 stopped guessing and
    **enumerated all five places migration writes to a project** — and found
    three of them unguarded, including the recovery path itself.

    That enumeration is the fix, not the three patches. This test is it, made
    standing: every call that writes must sit inside an `OSError` handler, so a
    sixth write site cannot be added unguarded without failing here.

    The axis all three rounds missed until the enumeration: a read-only
    **directory**, not a read-only file. `write_atomic` renames, and a rename
    needs write permission on the *directory* — which is why every existing
    test, all driving read-only through a file, passed throughout.
    """

    #: Attribute/function names whose call puts bytes into the user's project.
    WRITES = {"write_atomic", "declare", "restore_point", "undo", "unlink",
              "write_text", "chmod", "replace", "mkdir"}

    #: Functions that ARE the guarded body — the `try` is around their callers,
    #: so calls inside them are covered by that.
    INSIDE_GUARDED = {"write_atomic", "undo", "restore_point", "render",
                      "cross_file_delta", "main"}

    @staticmethod
    def _name(node):
        f = node.func
        return getattr(f, "attr", None) or getattr(f, "id", None)

    def _scan(self):
        """AST, not a text scan.

        The first version grepped lines and flagged the module docstring, which
        quotes `path.write_text(...)` while explaining the design. A guard that
        reports prose is one people switch off.
        """
        import ast
        src = (PERRY_HOME / "bin" / "perry-migrate").read_text(encoding="utf-8")
        tree = ast.parse(src)
        out = []
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if fn.name in self.INSIDE_GUARDED:
                continue
            guarded = set()
            for t in ast.walk(fn):
                if isinstance(t, ast.Try) and any(
                        h.type is not None for h in t.handlers):
                    for body_node in t.body:
                        for inner in ast.walk(body_node):
                            guarded.add(id(inner))
            for call in ast.walk(fn):
                if isinstance(call, ast.Call) and self._name(call) in self.WRITES:
                    if id(call) not in guarded:
                        out.append(f"perry-migrate:{call.lineno} in "
                                   f"{fn.name}(): {self._name(call)}()")
        return out

    def test_every_project_write_sits_inside_an_oserror_handler(self):
        unguarded = self._scan()
        self.assertEqual(
            unguarded, [],
            "these write to the user's project outside a `try`, so a "
            "permission or a full disk becomes a traceback instead of a "
            "refusal naming the restore point:\n  " + "\n  ".join(unguarded))

    def test_the_scan_finds_the_writes_that_are_there(self):
        """Anti-vacuity. If the scan matched nothing, the test above would pass
        by finding no writes at all — which is how a guard becomes ceremony."""
        import ast
        src = (PERRY_HOME / "bin" / "perry-migrate").read_text(encoding="utf-8")
        found = {self._name(c) for c in ast.walk(ast.parse(src))
                 if isinstance(c, ast.Call) and self._name(c) in self.WRITES}
        self.assertGreaterEqual(len(found), 4,
                                f"the scan sees almost no writes: {found}")
        self.assertIn("write_atomic", found)


if __name__ == "__main__":
    unittest.main()
