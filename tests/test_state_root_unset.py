"""`perry-config unset|set "State root"` refuses where it would strand the project's state.

USER-948 (2026-09-16), TASK-270 round 2. On a project whose state lives in
`perry/`, removing `State root` was exit 0 and silent; `resolve_state_root`
then answered the project root, the next `perry-task add` wrote `TASK-001`
into a new `./tasks.jsonl`, and every read lost the project's rows
(`perry/evidence/2026-09/TASK-270-result.md § 5`). The decision: `unset`
refuses when the root it points at holds a canonical store, names what it
found, and points at `/perry relocate` as the reversible move. No override,
and no writer-side guard.

USER-949, TASK-270 round 3: `set "State root" <other>` refuses when the current
root holds a canonical store and the target holds none. `/perry relocate` moves
the files first and sets after, so its own `set` proceeds with no bypass. Both
refusals ask `parsers.canonical_stores_under`, the presence test
`parsers.installed` uses.

What proceeds: a declared root holding no store (nothing to strand), and a
declared root that already is the project root (nothing moves).

Every project is built under a temporary root (NN-5).

Run: python3 tests/parallel test_state_root_unset
"""

from __future__ import annotations

COVERS = (
    "bin/perry-config",
    "viewer/parsers.py",
    "schema/state-schema.json",
    ".perry/config.jsonl",
)

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "sample-project"
CONFIG = ROOT / "bin" / "perry-config"
TASK = ROOT / "bin" / "perry-task"

sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402


def run(tool: pathlib.Path, *argv: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("PERRY_PROJECT", "PERRY_HOME")}
    return subprocess.run([sys.executable, str(tool), *argv],
                          capture_output=True, text=True, env=env,
                          cwd=tempfile.gettempdir())


class _Projects(unittest.TestCase):
    """Fixtures only; no tests."""

    def base(self) -> pathlib.Path:
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t270r2-")).resolve() / "p"
        self.addCleanup(shutil.rmtree, d.parent, ignore_errors=True)
        return d

    def relocated_project(self) -> pathlib.Path:
        """The sample project with its state in `perry/` and `.perry/` at the
        root, declaring `State root: perry` through Perry's own command."""
        d = self.base()
        d.mkdir()
        shutil.copytree(FIXTURE, d / "perry")
        (d / "perry" / ".perry").rename(d / ".perry")
        out = run(CONFIG, "set", "--root", str(d), "State root", "perry")
        self.assertEqual(out.returncode, 0, out.stderr)
        return d

    def bare_project(self, stores: tuple[str, ...]) -> pathlib.Path:
        """`.perry/config.jsonl` declaring `State root: perry`, and `perry/`
        holding exactly `stores` (empty files)."""
        d = self.base()
        (d / ".perry").mkdir(parents=True)
        shutil.copy(FIXTURE / ".perry" / "config.jsonl", d / ".perry")
        (d / "perry").mkdir()
        for name in stores:
            (d / "perry" / name).write_text("")
        out = run(CONFIG, "set", "--root", str(d), "State root", "perry")
        self.assertEqual(out.returncode, 0, out.stderr)
        return d

    def unset(self, d: pathlib.Path, *flags: str) -> subprocess.CompletedProcess:
        return run(CONFIG, "unset", *flags, "--root", str(d), "State root")


class StateRootUnset(_Projects):
    """USER-948, TASK-270 round 2."""

    # ── the refusal ───────────────────────────────────────────────────────

    def test_unset_refuses_over_a_state_root_holding_the_projects_rows(self):
        d = self.relocated_project()
        store = d / ".perry" / "config.jsonl"
        before = store.read_bytes()
        out = self.unset(d)
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("refused", out.stderr)
        self.assertIn("`perry/`", out.stderr)
        self.assertIn("tasks.jsonl", out.stderr)
        self.assertIn("project root", out.stderr)
        self.assertIn("/perry relocate <path>", out.stderr)
        self.assertIn("SKILL.md § /perry relocate", out.stderr)
        self.assertIn("Nothing was written", out.stderr)
        self.assertEqual(store.read_bytes(), before, "the setting must stay")
        self.assertEqual(P.resolve_state_root(d), (d / "perry").resolve())

    def test_the_projects_rows_still_list_after_the_refusal(self):
        d = self.relocated_project()
        self.unset(d)
        out = run(TASK, "list", "--root", str(d))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("REL-001", out.stdout)
        self.assertFalse((d / "tasks.jsonl").exists())

    def test_dry_run_refuses_the_same_way(self):
        out = self.unset(self.relocated_project(), "--dry-run")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("/perry relocate", out.stderr)

    def test_every_canonical_store_alone_is_state(self):
        """The names come from the schema's claims, each one on its own — a
        list written in the tool that dropped one would pass a fixture that
        holds them all."""
        names = P.canonical_store_names()
        self.assertIn("tasks.jsonl", names, "the fixture's premise")
        for name in names:
            with self.subTest(store=name):
                out = self.unset(self.bare_project((name,)))
                self.assertEqual(out.returncode, 1, out.stdout)
                self.assertIn(name, out.stderr)

    def test_there_is_no_override(self):
        """USER-948 offers `/perry relocate` as the only path."""
        out = self.unset(self.relocated_project(), "--force")
        self.assertEqual(out.returncode, 2, out.stderr)
        describe = json.loads(run(CONFIG, "--describe", "--json").stdout)
        unset = next(s for s in describe["subcommands"] if s["name"] == "unset")
        self.assertNotIn("--force", unset["flags"])
        self.assertNotIn("--force", describe.get("universal_flags", []))

    # ── when it proceeds ──────────────────────────────────────────────────

    def test_a_declared_root_holding_no_store_proceeds(self):
        d = self.bare_project(())
        out = self.unset(d)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("state_root",
                         (d / ".perry" / "config.jsonl").read_text())

    def test_a_declared_root_that_is_the_project_root_proceeds(self):
        """`State root: .` over a populated root: removing it moves nothing."""
        d = self.base()
        shutil.copytree(FIXTURE, d)
        self.assertEqual(run(CONFIG, "set", "--root", str(d), "State root",
                             ".").returncode, 0)
        out = self.unset(d)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_unsetting_another_setting_is_not_checked(self):
        out = run(CONFIG, "unset", "--root", str(self.relocated_project()),
                  "Repo layout")
        self.assertEqual(out.returncode, 0, out.stderr)


class StateRootSet(_Projects):
    """USER-949, TASK-270 round 3: `set "State root" <other>` refuses when the
    current root holds a canonical store and the target holds none."""

    def set_root(self, d: pathlib.Path, value: str,
                 *flags: str) -> subprocess.CompletedProcess:
        return run(CONFIG, "set", *flags, "--root", str(d), "State root", value)

    def relocate_by_its_procedure(self, d: pathlib.Path, dest: str) -> None:
        """`reference/router-subcommands.md § /perry relocate` steps 2 and 5:
        every claim not anchored at the project, moved if it exists. The set
        (step 6) is the caller's."""
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
        (d / dest).mkdir()
        for c in schema["claims"]:
            if c["anchor"] == "project":
                continue
            src = d / "perry" / c["path"].rstrip("/")
            if src.exists():
                shutil.move(str(src), str(d / dest / c["path"].rstrip("/")))

    # ── the refusal ───────────────────────────────────────────────────────

    def test_set_refuses_to_strand_a_state_root_holding_the_projects_rows(self):
        d = self.relocated_project()
        store = d / ".perry" / "config.jsonl"
        before = store.read_bytes()
        out = self.set_root(d, "elsewhere")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("refused", out.stderr)
        self.assertIn("`perry/`", out.stderr)
        self.assertIn("`elsewhere/`", out.stderr)
        self.assertIn("tasks.jsonl", out.stderr)
        self.assertIn("every later read and write", out.stderr)
        self.assertIn("/perry relocate <path>", out.stderr)
        self.assertIn("Nothing was written", out.stderr)
        self.assertEqual(store.read_bytes(), before)
        listed = run(TASK, "list", "--root", str(d))
        self.assertIn("REL-001", listed.stdout)
        self.assertFalse((d / "elsewhere").exists())

    def test_set_dry_run_refuses_the_same_way(self):
        out = self.set_root(self.relocated_project(), "elsewhere", "--dry-run")
        self.assertEqual(out.returncode, 1, out.stdout)

    def test_every_canonical_store_alone_is_state_on_both_sides(self):
        """Current root holding one store and an empty target refuses; the
        same store at the target lets it through. Each name on its own, from
        the schema."""
        for name in P.canonical_store_names():
            with self.subTest(side="current", store=name):
                d = self.bare_project((name,))
                (d / "elsewhere").mkdir()
                out = self.set_root(d, "elsewhere")
                self.assertEqual(out.returncode, 1, out.stdout)
                self.assertIn(name, out.stderr)
            with self.subTest(side="target", store=name):
                d = self.bare_project(("tasks.jsonl",))
                (d / "elsewhere").mkdir()
                (d / "elsewhere" / name).write_text("")
                out = self.set_root(d, "elsewhere")
                self.assertEqual(out.returncode, 0, out.stderr)

    def test_set_and_unset_ask_the_one_presence_test(self):
        """Over the same shapes, `set` to an empty root, `unset`, and
        `parsers.canonical_stores_under` give one answer."""
        shapes = [()] + [(n,) for n in P.canonical_store_names()]
        for stores in shapes:
            with self.subTest(stores=stores):
                expected = bool(P.canonical_stores_under(
                    self.bare_project(stores) / "perry"))
                self.assertEqual(expected, bool(stores))
                d = self.bare_project(stores)
                (d / "elsewhere").mkdir()
                set_refused = self.set_root(d, "elsewhere").returncode == 1
                unset_refused = self.unset(
                    self.bare_project(stores)).returncode == 1
                self.assertEqual((set_refused, unset_refused),
                                 (expected, expected))

    def test_there_is_no_override_on_set(self):
        out = self.set_root(self.relocated_project(), "elsewhere", "--force")
        self.assertEqual(out.returncode, 2, out.stderr)

    # ── when it proceeds ──────────────────────────────────────────────────

    def test_relocates_own_order_proceeds(self):
        """Move every claimed path first, then `set`: the target holds state
        by then, so no bypass is needed."""
        d = self.relocated_project()
        self.relocate_by_its_procedure(d, "newroot")
        out = self.set_root(d, "newroot")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(P.resolve_state_root(d), d / "newroot")
        self.assertIn("REL-001", run(TASK, "list", "--root", str(d)).stdout)

    def test_pointing_back_at_a_root_that_holds_state_proceeds(self):
        d = self.relocated_project()
        shutil.copytree(FIXTURE, d / "other", ignore=shutil.ignore_patterns(
            ".perry"))
        self.assertEqual(self.set_root(d, "other").returncode, 0)

    def test_a_value_that_does_not_move_state_proceeds(self):
        d = self.relocated_project()
        out = self.set_root(d, "./perry")
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_a_current_root_holding_nothing_proceeds(self):
        out = self.set_root(self.bare_project(()), "elsewhere")
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_setting_another_label_is_not_checked(self):
        out = run(CONFIG, "set", "--root", str(self.relocated_project()),
                  "Repo layout", "split")
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
