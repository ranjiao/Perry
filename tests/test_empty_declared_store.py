"""An EMPTY declared canonical store is Perry's; a foreign record is not. TASK-275.

`intake-sweep` discharges intake rows, and discharging the last one leaves
`intake.jsonl` empty. The next `perry-lint` run printed, on the same project:

    ⚠ intake.jsonl [NS-01] `intake.jsonl` holds 1 file(s) Perry did not write …
    · intake store: 0 record(s); …

— Perry's own declared store, reported as a collision with advice to relocate.
`looks_like_perry_record` judges a `.jsonl` by its first record, and an empty
file has none.

**The rule** (`bin/perry-lint § looks_like_perry_state`, beside TASK-270's):
an empty file at a claim anchored in `.perry/`, or at a declared canonical
store (`parsers.canonical_store_names` — a `file` claim anchored at the state
root whose path ends in `.jsonl`), is Perry's. An empty file carries nothing
that could be misread as Perry's, so it excuses nothing foreign. A non-empty
file at the same path is still judged by its first record, exactly as before.

No schema change: the row's pointer was to declare intake's record shape in
`schema/state-schema.json § stores.declared`, and that file needs the user's
consent. The empty case needs no record shape at all.

Every project is a copy of `tests/fixtures/sample-project` under a temporary
root (NN-5).

Run: python3 tests/parallel test_empty_declared_store
"""

from __future__ import annotations

COVERS = (
    "bin/perry-lint",
    "viewer/parsers.py",
    "tests/fixtures/sample-project/",
)

import importlib.machinery
import importlib.util
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
LINT = ROOT / "bin" / "perry-lint"

sys.path.insert(0, str(ROOT / "viewer"))
sys.path.insert(0, str(ROOT / "bin"))
import parsers as P  # noqa: E402

#: A well-formed JSON object no Perry store declares.
FOREIGN = json.dumps({"not": "a perry record"}) + "\n"


def _load_lint():
    loader = importlib.machinery.SourceFileLoader("perry_lint_t275", str(LINT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def _env() -> dict:
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    env.pop("PERRY_HOME", None)
    return env


class _Project(unittest.TestCase):
    def project(self, intake: str) -> pathlib.Path:
        """A sample-project copy whose `intake.jsonl` holds `intake`."""
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t275-")) / "p"
        self.addCleanup(shutil.rmtree, d.parent, ignore_errors=True)
        shutil.copytree(FIXTURE, d)
        (d / "intake.jsonl").write_text(intake, encoding="utf-8")
        return d

    def intake_ns01(self, d: pathlib.Path) -> list[str]:
        out = subprocess.run(
            [sys.executable, str(LINT), "--root", str(d)],
            capture_output=True, text=True, env=_env(),
            cwd=tempfile.gettempdir())
        return [l for l in out.stdout.splitlines()
                if "[NS-01]" in l and "intake.jsonl" in l]


class TheReproduction(_Project):
    """The row's reproduction, before and after, through the real tool."""

    def test_an_empty_intake_store_is_not_a_collision(self):
        self.assertEqual(self.intake_ns01(self.project("")), [])

    def test_a_blank_lines_only_intake_store_is_the_same_empty_store(self):
        """`perry_md_store.load_store` parses this to `[]`, as it does ''."""
        self.assertEqual(self.intake_ns01(self.project("\n\n")), [])

    def test_a_foreign_intake_file_is_still_a_collision(self):
        """The control: the fix is about emptiness, not about the name."""
        self.assertTrue(self.intake_ns01(self.project(FOREIGN)),
                        "a non-empty foreign file at a declared store path "
                        "must still draw NS-01, or the test above measures "
                        "nothing")


class EveryDeclaredStore(unittest.TestCase):
    """The rule is the declaration's, so it holds for every store it names."""

    def setUp(self):
        self.lint = _load_lint()
        self.schema = json.loads(self.lint.SCHEMA_PATH.read_text())
        self.claims = {c["path"]: c for c in self.schema["claims"]}
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t275-ns-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        self.empty = d / "empty.jsonl"
        self.empty.write_text("")
        self.foreign = d / "foreign.jsonl"
        self.foreign.write_text(FOREIGN)

    def stores(self) -> tuple[str, ...]:
        names = P.canonical_store_names()
        # Not vacuous: the declaration names intake among the others.
        self.assertIn("intake.jsonl", names)
        self.assertGreaterEqual(len(names), 2)
        return names

    def test_an_empty_file_at_every_declared_store_is_perrys(self):
        for name in self.stores():
            with self.subTest(name):
                self.assertTrue(self.lint.looks_like_perry_state(
                    self.empty, self.schema, self.claims[name]))

    def test_a_foreign_record_at_every_declared_store_is_not(self):
        for name in self.stores():
            with self.subTest(name):
                self.assertFalse(self.lint.looks_like_perry_state(
                    self.foreign, self.schema, self.claims[name]))

    def test_the_criterion_is_the_declaration_not_the_suffix(self):
        """A state-root `.jsonl` claim the schema does not declare is not
        excused when empty — the rule reads `canonical_store_names`, it does
        not excuse every empty `.jsonl`."""
        undeclared = {"path": "not-a-declared-store.jsonl", "kind": "file",
                      "owner": "work", "anchor": "state"}
        self.assertNotIn(undeclared["path"], P.canonical_store_names())
        self.assertFalse(self.lint.looks_like_perry_state(
            self.empty, self.schema, undeclared))


if __name__ == "__main__":
    unittest.main()
