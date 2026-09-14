"""TASK-237 deliverable 2 — a Perry project is not recognised by `BOARD.md` existing.

`USER-931` answer A: before `BOARD.md` may be deleted, every site that decides
"is this a Perry project / where is its root" must recognise a project that has
none. **Measured 2026-09-14: every code site already asks `configured(d)`**
(`.perry/config.jsonl`) beside `BOARD.md` / `OKR.md`, so no code site changes.
What was missing is a guard at two of them: with `configured(d)` deleted at
`bin/lib § resolve_project_root` (A2) or `bin/perry-lint § main`'s walk (A5),
the only test that goes red is one in this module — measured by mutation,
`TASK-237-result.md § 4`. The other seven were already caught elsewhere.

**One fixture for all nine, and its emptiness is asserted, not assumed.** A
fixture carrying `BOARD.md`, `OKR.md`, `phase/` or `design/DESIGN-*.md` answers
True through a sibling disjunct whatever `configured(d)` does — the way a guard
over an OR-chain passes while measuring nothing (`test_config_store_readers §
Fixture.bare` says the same). `setUp` refuses such a fixture before any test
runs.

The fixture is Perry's own shape: `.perry/config.jsonl` at the project root,
`State root: perry`, and `perry/tasks.jsonl` holding one open row. So a walk
that lands on the state root instead of the project root is a wrong answer
here, as it would be on this repository.

    site                                         asked by
    A1 viewer/parsers.py § _resolve_project_root  test_the_parsers_walk_…
    A2 bin/lib § resolve_project_root             test_the_lib_walk_…
    A3 bin/perry-state § resolve_root             test_perry_state_walks_…
    A4 bin/perry-state § build (installed)        test_perry_state_calls_it_installed
    A5 bin/perry-lint § main (the walk)           test_the_linter_walk_…
    A6 bin/perry-lint § is_adopted                test_the_linter_calls_it_adopted
    A7 bin/perry-explain § typed_task_lookup      test_explain_reads_the_task_store
    A8 bin/perry-diagnose § scan_tracking         test_diagnose_calls_it_installed
    A9 bin/perry-diagnose § diagnose (is_perry)   test_diagnose_treats_it_as_perry

A3, A4, A6, A8 and A9 were already reddened by
`tests/test_config_store_readers.py`, A1 by `tests/test_project_root_resolution.py`
and A7 by `tests/test_explain_typed_tasks.py`. They are asked again here so this
one fixture — config and a task store, nothing else — is the whole acceptance
of the amendment's verification 2, in one module a reviewer can mutate against.

Run: python3 tests/parallel test_board_less_project_is_recognised
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
sys.path.insert(0, str(ROOT / "viewer"))

SETTINGS = [
    {"kind": "setting", "key": "document_language", "label": "Document language",
     "value": "English", "order": 0},
    {"kind": "setting", "key": "repo_layout", "label": "Repo layout",
     "value": "single", "order": 1},
    {"kind": "setting", "key": "state_root", "label": "State root",
     "value": "perry", "order": 2},
    {"kind": "track", "track": "main", "mode": "project", "spine": "phase/",
     "stages": "", "wip": "", "sla": "", "cycle": "", "default_rung": "V3",
     "order": 0},
]

TASK = {"id": "TASK-001", "title": "a row with no board to sit on",
        "summary": "", "owner": "Coding Agent", "status": "not_started",
        "priority": "P1", "track": "main", "stage": "", "stage_since": "",
        "arrived": "", "verification": "V3", "evidence": "",
        "next_action": "prove the project is recognised without BOARD.md",
        "depends_on": [], "design_refs": [], "commitment": "", "parent": "",
        "group": "P1", "role": "", "created": "2026-09-14", "order": 0}

#: The other half of every site's OR-chain. Present anywhere in the fixture,
#: any one of these answers for `configured(d)` and the test measures nothing.
SIBLING_DISJUNCTS = ("BOARD.md", "OKR.md", "phase", "design")


def load_bin_module(name: str):
    import importlib.util
    from importlib.machinery import SourceFileLoader

    loader = SourceFileLoader(name.replace("-", "_") + "_t237",
                              str(ROOT / "bin" / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(loader.name, mod)
    loader.exec_module(mod)
    return mod


def env() -> dict:
    """`PERRY_PROJECT` short-circuits every walk, so a runner that exports it
    would turn the walk tests green while measuring nothing."""
    e = dict(os.environ)
    e.pop("PERRY_PROJECT", None)
    e["PERRY_HOME"] = str(ROOT)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return e


def run(argv: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True,
                          text=True, cwd=str(cwd), env=env())


class BoardLessProject(unittest.TestCase):

    def setUp(self):
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-boardless-")).resolve()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        (d / ".perry").mkdir()
        (d / ".perry" / "config.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in SETTINGS),
            encoding="utf-8")
        (d / "perry").mkdir()
        (d / "perry" / "tasks.jsonl").write_text(
            json.dumps(TASK, ensure_ascii=False) + "\n", encoding="utf-8")
        (d / "perry" / "work").mkdir()
        self.root, self.state, self.below = d, d / "perry", d / "perry" / "work"

        # The anti-vacuity gate. Checked over the whole fixture AND every
        # ancestor a walk could climb to, because an ancestor holding a
        # `BOARD.md` answers a mutated walk just as well as the project would.
        found = [p for p in d.rglob("*") if p.name in SIBLING_DISJUNCTS]
        self.assertEqual(found, [], "the fixture carries a sibling disjunct")
        for anc in d.parents:
            for name in ("BOARD.md", "OKR.md"):
                self.assertFalse(
                    (anc / name).exists(),
                    f"{anc / name} exists above the fixture, so a walk with "
                    f"`configured` deleted would still stop somewhere")

    # A1
    def test_the_parsers_walk_finds_the_project_from_below_its_state_root(self):
        p = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); import parsers; "
             "print(parsers.PROJECT_ROOT); print(parsers.STATE_ROOT)"
             % str(ROOT / "viewer")],
            capture_output=True, text=True, cwd=str(self.below), env=env())
        self.assertEqual(p.returncode, 0, p.stderr)
        project, state = p.stdout.split("\n")[:2]
        self.assertEqual(project, str(self.root))
        self.assertEqual(state, str(self.state))

    # A2
    def test_the_lib_walk_finds_the_project_from_below_its_state_root(self):
        p = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
             "import lib; print(lib.resolve_project_root(None))"
             % (str(ROOT / "bin"), str(ROOT / "viewer"))],
            capture_output=True, text=True, cwd=str(self.below), env=env())
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), str(self.root))

    # A3
    def test_perry_state_walks_to_the_project_from_below_its_state_root(self):
        p = run([str(ROOT / "bin" / "perry-state"), "--json"], cwd=self.below)
        self.assertEqual(p.returncode, 0, p.stderr)
        payload = json.loads(p.stdout)
        self.assertEqual(payload["project"]["root"], self.state.as_posix())
        self.assertTrue(payload["installed"])

    # A4
    def test_perry_state_calls_it_installed(self):
        p = run([str(ROOT / "bin" / "perry-state"), "--json",
                 "--root", str(self.root)], cwd=ROOT)
        self.assertEqual(p.returncode, 0, p.stderr)
        payload = json.loads(p.stdout)
        self.assertTrue(payload["installed"],
                        "work/SKILL.md § Bootstrap asks exactly this; False "
                        "would bootstrap a configured project on every session")
        self.assertNotIn("No Perry state found — run /perry for first-time setup.",
                         payload.get("warnings") or [])

    # A5
    def test_the_linter_walk_finds_the_project_from_below_its_state_root(self):
        """The label line names the root the walk settled on. The exit code is
        not asserted: a board-less project is `missing-file` red because the
        schema declares `BOARD.md` required, which is not detection."""
        p = run([str(ROOT / "bin" / "perry-lint")], cwd=self.below)
        self.assertIn(f"perry-lint · {self.root} (state root: perry/)\n",
                      p.stdout,
                      f"rc={p.returncode}\n{p.stdout[:400]}\n{p.stderr[:400]}")

    # A6
    def test_the_linter_calls_it_adopted(self):
        lint = load_bin_module("perry-lint")
        self.assertTrue(lint.is_adopted(self.root, self.state))

    # A7
    def test_explain_reads_the_task_store(self):
        explain = load_bin_module("perry-explain")
        got = explain.typed_task_lookup(self.root, "TASK-001")
        self.assertIsNotNone(got, "not adopted: the typed store was skipped")
        self.assertEqual(got["state"], "found")
        self.assertEqual(got["entry"]["title"], TASK["title"])

    # A8, A9
    def diagnose(self) -> dict:
        p = run([str(ROOT / "bin" / "perry-diagnose"), "--root", str(self.root),
                 "--json"], cwd=ROOT)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_diagnose_calls_it_installed(self):
        self.assertTrue(self.diagnose()["tracking"]["perry"]["installed"])

    def test_diagnose_treats_it_as_perry(self):
        self.assertTrue(self.diagnose()["namespace"]["applicable"])


if __name__ == "__main__":
    unittest.main()
