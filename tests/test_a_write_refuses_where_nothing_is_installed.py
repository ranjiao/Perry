"""A write refuses on a directory that is not installed (TASK-237 round 2).

`TASK-237-spec.md § Amendment 2026-09-14 (9)`. The V4 round 1 finding F1: 3a
let a write lay its board out from the declarations when no `BOARD.md` exists,
and nothing asked whether the directory was a Perry project. Run in a copy of a
pre-ADR-019 consumer — `.perry/config.md` declaring `State root: perry`, the
board under `perry/` — `perry-task ask` exited 0, wrote `asks.jsonl`, the
journal and `.perry/events.jsonl` at the project root, and turned `installed`
true over an empty second project that hid the real board from every surface.
The pre-TASK-237 tools refused there.

**What is held here:**

1. Every `bin/` write whose declared `writes` names a canonical store, the
   journal or the event log exits 1 on an empty directory, a `BOARD.md`-only
   directory and a pre-ADR-019 directory, writes nothing, leaves `installed`
   false, and says why — `--dry-run` included. The table of writes is checked
   against each tool's `--describe`, so a new write subcommand is not silently
   outside it.
2. A pre-ADR-019 project is told to write its config store first, with the
   command and its root.
3. The start still installs: `perry-config set` and `track` exit 0 on an empty
   directory, and a write then lands. A read is not gated.
4. R2: on a task whose group matches no declared heading, the writes that
   raised `KeyError` land in the task's own `## <group>` section, the section
   `perry-tasks board` prints it under (`DECLARED_BOARD_CHOICES` "undeclared
   group"), with no traceback — with the board file held and without it.

Run: python3 tests/parallel test_a_write_refuses_where_nothing_is_installed
"""

from __future__ import annotations

import goals_actor
import task_actor

COVERS = (
    "tests/goals_actor.py",
    "bin/perry-task",
    "bin/perry-goals",
    "bin/perry-okr",
    "bin/perry-config",
    "bin/perry_store.py",
    "bin/perry_md_store.py",
    "bin/lib/",
)

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

import config_store
import inproc

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402

GATE = "is not an installed Perry project"

LEGACY_CONFIG = ("# Perry configuration\n\n- Document language: English\n"
                 "- Repo layout: single\n- State root: perry\n")
LEGACY_BOARD = ("# Board\n\n## P1\n\n| ID | Title | Owner | Status | Next action "
                "| Evidence |\n|---|---|---|---|---|---|\n| TASK-001 | a held row "
                "| Coding Agent | not_started | start | — |\n")

#: `(tool, subcommand) -> argv`. Enough to reach the dispatch boundary: the
#: gate is asked there, before any handler reads a flag or an id.
GATED = {
    ("perry-tasks", "write"): ["write", "--from-board"],
    ("perry-tasks", "risks-write"): ["risks-write", "--from-board"],
    ("perry-tasks", "intake-write"): ["intake-write", "--from-board"],
    ("perry-tasks", "asks-write"): ["asks-write", "--from-board"],
    ("perry-tasks", "cadence-write"): ["cadence-write", "--from-board"],
    ("perry-okr", "write"): ["write", "--from-file"],
    ("perry-okr", "migrate-ids"): ["migrate-ids"],
    ("perry-goals", "commit"): ["commit", "--track", "main", "--promise", "x"],
    ("perry-goals", "link"): ["link", "--unlinked", "TASK-001"],
    # TASK-264: both append to `linkage.jsonl` and `.perry/events.jsonl`.
    ("perry-goals", "measure"): ["measure", "P001-O1-KR1", "--check", "c",
                                 "--value", "1", "--evidence", "e.md",
                                 "--actor", "gate-test"],
    ("perry-goals", "check"): ["check", "P001-O1-KR1", "--id", "c",
                               "--direction", "done", "--target", "1",
                               "--label", "x", "--actor", "gate-test"],
    # TASK-264 D3: appends to `linkage.jsonl` or `okr.jsonl`, and the log.
    ("perry-goals", "kr"): ["kr", "add", "P001-O1-KR9", "--objective", "O1",
                            "--text", "x", "--reason", "r",
                            "--actor", "gate-test"],
}


def describe(tool: str) -> dict:
    out = inproc.run(tool, ["--describe", "--json"])
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def perry_task_writes() -> dict:
    """Every `perry-task` subcommand `--describe` declares with `writes`."""
    out = {}
    for sub in describe("perry-task")["subcommands"]:
        if sub.get("writes"):
            # The subcommand alone: the gate is asked before any id or flag is
            # read, and an id where a subcommand takes none is exit 2 at parse.
            out[("perry-task", sub["name"])] = ([sub["name"]],
                                                "--dry-run" in sub["flags"])
    return out


def goals_write_commands() -> set:
    """`perry-goals` declares no SURFACE: its commands off the reading branch."""
    path = ROOT / "bin" / "perry-goals"
    spec = importlib.util.spec_from_loader(
        "perry_goals_gate_test",
        importlib.machinery.SourceFileLoader("perry_goals_gate_test", str(path)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {c for c in mod.COMMANDS if c not in ("list", "krs")}


def every_gated_write() -> dict:
    """`(tool, sub) -> (argv, takes --dry-run)` for every write in scope."""
    table = perry_task_writes()
    dry = {}
    for tool in ("perry-tasks", "perry-okr"):
        for sub in describe(tool)["subcommands"]:
            dry[(tool, sub["name"])] = "--dry-run" in sub.get("flags", [])
    for key, argv in GATED.items():
        table[key] = (argv, dry.get(key, key[0] == "perry-goals"))
    return table


def make(shape: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"perry-gate-{shape}-")).resolve()
    if shape == "board-only":
        (d / "BOARD.md").write_text(LEGACY_BOARD, encoding="utf-8")
        (d / "OKR.md").write_text("# OKR\n", encoding="utf-8")
    elif shape == "pre-adr-019":
        (d / ".perry").mkdir()
        (d / ".perry" / "config.md").write_text(LEGACY_CONFIG, encoding="utf-8")
        (d / "perry").mkdir()
        (d / "perry" / "BOARD.md").write_text(LEGACY_BOARD, encoding="utf-8")
    return d


def snapshot(d: Path) -> dict:
    return {str(p.relative_to(d)): (p.read_bytes() if p.is_file() else None)
            for p in sorted(d.rglob("*"))}


SHAPES = ("empty", "board-only", "pre-adr-019")


class TestEveryWriteRefusesWhereNothingIsInstalled(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.table = every_gated_write()

    def test_the_table_covers_every_declared_write(self):
        declared = set(perry_task_writes())
        for tool in ("perry-tasks", "perry-okr"):
            declared |= {(tool, s["name"]) for s in describe(tool)["subcommands"]
                         if s.get("writes")
                         and any(Path(w).suffix == ".jsonl" for w in s["writes"])}
        declared |= {("perry-goals", c) for c in goals_write_commands()}
        self.assertEqual(declared, set(self.table))
        # Anti-vacuity: the table is not a list of nothing.
        self.assertGreaterEqual(len([k for k in self.table
                                     if k[0] == "perry-task"]), 27)

    def refuses(self, shape: str, tool: str, argv: list[str]):
        d = make(shape)
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        self.assertFalse(P.installed(d), f"anti-vacuity: {shape} is installed")
        before = snapshot(d)
        out = goals_actor.run(tool, task_actor.owned(argv, "install-gate-probe")
                         + ["--root", str(d)] if tool == "perry-task"
                         else argv + ["--root", str(d)])
        self.assertEqual(out.returncode, 1, out.stdout[-300:] + out.stderr[-300:])
        self.assertIn(GATE, out.stderr + out.stdout)
        self.assertNotIn("Traceback", out.stderr)
        self.assertEqual(snapshot(d), before, "a refused write changed the tree")
        self.assertFalse(P.installed(d), "a refused write installed the directory")
        return out

    def test_each_write_refuses_and_writes_nothing(self):
        for (tool, sub), (argv, _dry) in sorted(self.table.items()):
            for shape in SHAPES:
                with self.subTest(tool=tool, write=sub, shape=shape):
                    self.refuses(shape, tool, list(argv))

    def test_dry_run_gets_the_same_refusal(self):
        checked = 0
        for (tool, sub), (argv, dry) in sorted(self.table.items()):
            if not dry:
                continue
            for shape in SHAPES:
                with self.subTest(tool=tool, write=sub, shape=shape):
                    self.refuses(shape, tool, list(argv) + ["--dry-run"])
                    checked += 1
        self.assertGreaterEqual(checked, 27 * len(SHAPES))

    def test_a_pre_adr_019_project_is_told_to_write_the_config_store_first(self):
        out = self.refuses("pre-adr-019", "perry-task", ["ask", "--needed", "x"])
        self.assertIn("`.perry/config.md`", out.stderr)
        self.assertIn('perry-config" set \'State root\'', out.stderr)
        self.assertIn("--root", out.stderr)
        plain = self.refuses("empty", "perry-task", ["ask", "--needed", "x"])
        self.assertNotIn("config.md", plain.stderr)
        self.assertIn('perry-config" set', plain.stderr)

    def test_the_reviewers_reproduction_run_from_the_directory(self):
        """F1 as filed: no `--root`, from inside the copy, `PERRY_PROJECT` unset."""
        d = make("pre-adr-019")
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        before = snapshot(d)
        env = {k: v for k, v in os.environ.items() if not k.startswith("PERRY_")}
        env["PERRY_HOME"] = str(ROOT)
        out = subprocess.run(task_actor.command([sys.executable, str(ROOT / "bin" / "perry-task"),
                              "ask", "--needed", "f1 probe"], 'test_a_write_refuses_where_nothing_is_installed'),
                             capture_output=True, text=True, cwd=d, env=env)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertIn(GATE, out.stderr)
        self.assertEqual(snapshot(d), before)
        self.assertFalse(P.installed(d))


class TestTheStartStillInstalls(unittest.TestCase):

    def fresh(self, shape="empty") -> Path:
        d = make(shape)
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def test_perry_config_set_installs_an_empty_directory(self):
        d = self.fresh()
        out = inproc.run("perry-config", ["set", "Document language", "English",
                                          "--root", str(d)])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn(GATE, out.stderr)
        self.assertTrue(P.installed(d))
        add = inproc.run("perry-task", task_actor.owned(["add", "--title", "after the start",
                                        "--priority", "P1",
                                        "--deliverable", "d", "--verification",
                                        "v", "--summary",
                                        "A row written once the start has "
                                        "installed the project.",
                                        "--root", str(d)], 'test_a_write_refuses_where_nothing_is_installed'))
        self.assertEqual(add.returncode, 0, add.stderr)
        self.assertTrue((d / "tasks.jsonl").is_file())

    def test_perry_config_track_installs_an_empty_directory(self):
        d = self.fresh()
        out = inproc.run("perry-config", ["track", "main", "--root", str(d)])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(P.installed(d))

    def test_a_pre_adr_019_project_writes_once_its_store_declares_the_root(self):
        d = self.fresh("pre-adr-019")
        out = inproc.run("perry-config", ["set", "State root", "perry",
                                          "--root", str(d)])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(P.installed(d))
        ask = inproc.run("perry-task", task_actor.owned(["ask", "--needed", "after the set?",
                                        "--root", str(d)], 'test_a_write_refuses_where_nothing_is_installed'))
        self.assertEqual(ask.returncode, 0, ask.stderr)
        self.assertTrue((d / "perry" / "asks.jsonl").is_file())
        self.assertFalse((d / "asks.jsonl").exists(),
                         "the write landed outside the declared state root")

    def test_a_read_is_not_gated(self):
        d = self.fresh()
        for argv in (["list", "--json"], ["asks", "--json"], ["events", "--json"]):
            with self.subTest(read=argv[0]):
                out = inproc.run("perry-task", task_actor.owned(argv + ["--root", str(d)], 'test_a_write_refuses_where_nothing_is_installed'))
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertFalse(json.loads(out.stdout)["installed"])
        b = self.fresh("board-only")
        out = inproc.run("perry-tasks", ["build", "--root", str(b)])
        self.assertEqual(out.returncode, 0, out.stderr)


GROUP = "Open — 工程线"


def jsonl(records) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def a_task(tid, order, group, priority):
    return {"id": tid, "title": f"title of {tid}", "summary": "",
            "owner": "Coding Agent", "status": "not_started",
            "priority": priority, "track": "main", "stage": "",
            "stage_since": "", "arrived": "", "verification": "V3",
            "evidence": "", "next_action": f"next for {tid}", "depends_on": [],
            "design_refs": [], "commitment": "", "parent": "", "group": group,
            "role": "", "created": "2026-09-01", "order": order}


class TestAWriteInAnUndeclaredGroup(unittest.TestCase):
    """R2: `section()` was asked for a heading and indexed `PRIORITY_RE` by it."""

    #: `(write, argv, field, value the store must then hold)`.
    WRITES = [
        ("next", ["--next", "r2 probe"], "next_action", "r2 probe"),
        ("status", ["--status", "blocked", "--on", "TASK-001", "--reason", "r2",
                    "--next", "wait"], "status", "blocked"),
        ("retitle", ["--title", "r2 title"], "title", "r2 title"),
        ("rung", ["--rung", "V2"], "verification", "V2"),
        ("evidence", ["--evidence", "perry/evidence/proof.md"], "evidence",
         "perry/evidence/proof.md"),
        ("depends", ["--on", "TASK-001"], "depends_on", ["TASK-001"]),
    ]

    def project(self, held: bool) -> Path:
        d = Path(tempfile.mkdtemp(prefix="perry-r2-")).resolve()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        config_store.write_config(d, {"State root": "perry"},
                                  [config_store.track("main")])
        tasks = [a_task("TASK-001", 0, "P1", "P1"),
                 a_task("TASK-9500", 0, GROUP, "")]
        (d / ".perry" / "events.jsonl").write_text(jsonl(
            {"ts": "2026-09-01T10:00:00+08:00", "event": "add", "id": t["id"],
             "title": t["title"], "track": "main", "actor": "agent",
             "from": None, "to": "not_started"} for t in tasks),
            encoding="utf-8")
        (d / "perry" / "evidence").mkdir(parents=True)
        (d / "perry" / "evidence" / "proof.md").write_text("# proof\n",
                                                           encoding="utf-8")
        (d / "perry" / "tasks.jsonl").write_text(jsonl(tasks), encoding="utf-8")
        if held:
            board = inproc.run("perry-tasks", ["board", "--root", str(d)])
            self.assertEqual(board.returncode, 0, board.stderr)
            (d / "perry" / "BOARD.md").write_text(board.stdout, encoding="utf-8")
        return d

    def section_of(self, d: Path, tid: str):
        out = inproc.run("perry-tasks", ["board", "--root", str(d)])
        self.assertEqual(out.returncode, 0, out.stderr)
        heading = None
        for line in out.stdout.split("\n"):
            if line.startswith("## "):
                heading = line[3:].strip()
            elif line.startswith(f"| {tid} "):
                return heading
        return None

    def test_the_write_lands_in_the_tasks_own_section(self):
        for held in (False, True):
            for name, argv, field, value in self.WRITES:
                with self.subTest(write=name, held_board=held):
                    d = self.project(held)
                    self.assertEqual(self.section_of(d, "TASK-9500"), GROUP,
                                     "anti-vacuity: the board does not place "
                                     "the task under its group")
                    out = inproc.run("perry-task", task_actor.owned([name, "TASK-9500", *argv,
                                                    "--root", str(d)], 'test_a_write_refuses_where_nothing_is_installed'))
                    self.assertNotIn("Traceback", out.stderr)
                    self.assertNotIn("KeyError", out.stderr)
                    self.assertEqual(out.returncode, 0, out.stderr[-600:])
                    rec = next(json.loads(l) for l in (d / "perry" / "tasks.jsonl")
                               .read_text(encoding="utf-8").splitlines()
                               if l.strip() and json.loads(l)["id"] == "TASK-9500")
                    got = rec[field]
                    if isinstance(value, str) and field == "verification":
                        got = got[:len(value)]
                    self.assertEqual(got, value)
                    self.assertEqual(rec["group"], GROUP)
                    self.assertEqual(self.section_of(d, "TASK-9500"), GROUP)



if __name__ == "__main__":
    unittest.main()
