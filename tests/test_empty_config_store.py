"""An empty `.perry/config.jsonl` is a usable store, and every tool says so. TASK-270.

`perry-config unset` of the last setting leaves a zero-record store at exit 0.
Until this row, every writer then refused it as a store that "holds records
that do not validate", `perry-lint` printed `config store: 0 record(s), all
valid`, and `NS-01` called the file one Perry did not write. Two of the three
messages were false and none named the recovery
(`perry/evidence/2026-09/TASK-270-reproduction-2026-09-16.md`).

**The rule** (`viewer/parsers.py § config_store_unusable`, the one predicate
the writers and the linter call): a writer refuses a config store exactly when
it may hold a declaration the reader could not see — bytes that did not parse,
or a record that did not validate. Record count is not part of the rule. The
refusal's own reason is that writing "would stamp DESIGN-003's implicit `main`
over whatever this project actually declares"; an empty store declares
nothing, so there is nothing to stamp over.

What this module pins, one class per outcome of the spec:

1. the writers do not refuse an empty store, and do not say "do not validate";
2. the writers and `perry-lint`'s census agree over every store shape — and a
   store with a record that genuinely does not validate is still refused;
3. `NS-01` does not call an empty `.perry/config.jsonl` foreign;
4. `perry-config` says when a write leaves the store empty, and what follows.

Every project is a copy of `tests/fixtures/sample-project` under a temporary
root (NN-5).

Run: python3 tests/parallel test_empty_config_store
"""

from __future__ import annotations

COVERS = (
    "bin/perry-config",
    "bin/perry-goals",
    "bin/perry-lint",
    "bin/perry-state",
    "bin/perry-task",
    "viewer/parsers.py",
    ".perry/config.jsonl",
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
CONFIG = ROOT / "bin" / "perry-config"
TASK = ROOT / "bin" / "perry-task"
GOALS = ROOT / "bin" / "perry-goals"
LINT = ROOT / "bin" / "perry-lint"

sys.path.insert(0, str(ROOT / "viewer"))
sys.path.insert(0, str(ROOT / "bin"))
import parsers as P  # noqa: E402

#: The refusal wording for a store whose records genuinely do not validate.
#: It must never be what an EMPTY store is told.
INVALID_WORDS = "holds records that do not validate"
#: The prefix both writers' register refusal starts with.
REGISTER_REFUSAL = "the track register cannot be read"
#: What the census prints when the store is unusable.
CENSUS_REFUSES = "every writer refuses the store whole"

#: A record that is well-formed JSON and does not validate: `mode` is a list.
BAD_RECORD = json.dumps({"kind": "track", "track": "intake", "mode": [],
                         "order": 9})


def _load_lint():
    loader = importlib.machinery.SourceFileLoader("perry_lint_t270", str(LINT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def _env() -> dict:
    env = dict(os.environ)
    env.pop("PERRY_PROJECT", None)
    env.pop("PERRY_HOME", None)
    return env


def run(tool: pathlib.Path, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(tool), *argv],
                          capture_output=True, text=True, env=_env(),
                          cwd=tempfile.gettempdir())


class _Project(unittest.TestCase):
    def project(self, store: str | None = None) -> pathlib.Path:
        """A sample-project copy. `store` replaces `.perry/config.jsonl`'s
        bytes when given; `None` keeps the fixture's five settings."""
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t270-")) / "p"
        self.addCleanup(shutil.rmtree, d.parent, ignore_errors=True)
        shutil.copytree(FIXTURE, d)
        if store is not None:
            (d / ".perry" / "config.jsonl").write_text(store, encoding="utf-8")
        return d

    def add(self, d: pathlib.Path) -> subprocess.CompletedProcess:
        return run(TASK, "add", "--root", str(d), "--title", "t270 row",
                   "--deliverable", "d", "--verification", "v",
                   "--summary", "a row", "--unlinked", "--owner", "o",
                   "--priority", "P2")

    def commit(self, d: pathlib.Path) -> subprocess.CompletedProcess:
        # `commit` reaches `perry-goals § tracks_of`; `list` does not.
        return run(GOALS, "commit", "--track", "main", "--promise", "p",
                   "--to", "someone", "--due", "2026-09-30", "--root", str(d))

    def census(self, d: pathlib.Path) -> str:
        out = run(LINT, "--root", str(d))
        lines = [l for l in out.stdout.splitlines() if "config store" in l]
        self.assertEqual(len(lines), 1, out.stdout[-2000:])
        return lines[0]


class EmptyStoreWriters(_Project):
    """Outcome 1: an empty store is not refused, and not called invalid."""

    def test_the_parser_classifies_an_empty_store_as_usable(self):
        d = self.project("")
        self.assertEqual(P.config_store_records(d), ([], ""))
        self.assertEqual(P.config_store_unusable(d), "")

    def test_a_blank_lines_only_store_is_the_same_empty_store(self):
        d = self.project("\n\n  \n")
        self.assertEqual(P.config_store_unusable(d), "")

    def test_perry_task_add_writes_on_an_empty_store(self):
        d = self.project("")
        out = self.add(d)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("wrote", out.stdout)
        self.assertNotIn(INVALID_WORDS, out.stderr)
        self.assertNotIn(REGISTER_REFUSAL, out.stderr)

    def test_perry_goals_passes_the_register_on_an_empty_store(self):
        """`commit` refuses on this fixture for its own reason (no
        `## Commitments`); what is asserted is that the register did not."""
        out = self.commit(self.project(""))
        self.assertNotIn(REGISTER_REFUSAL, out.stderr)
        self.assertNotIn(INVALID_WORDS, out.stderr)

    def test_the_end_to_end_reproduction(self):
        """The PMO's reproduction, through Perry's own commands only."""
        d = self.project()
        for label in ("Document language", "Repo layout", "PMO repo path",
                      "Code repo path", "Last updated"):
            out = run(CONFIG, "unset", "--root", str(d), label)
            self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual((d / ".perry" / "config.jsonl").read_text(), "")
        out = self.add(d)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("config store: empty", self.census(d))
        out = run(CONFIG, "set", "--root", str(d), "Document language",
                  "English")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.add(d).returncode, 0)


class WritersAndLinterAgree(_Project):
    """Outcome 2: one rule. Each shape asks the predicate, both writers and the
    census, and all four answers must line up."""

    SHAPES = {
        "fixture store": (None, False),
        "empty store": ("", False),
        "settings-only store": (json.dumps(
            {"kind": "setting", "key": "document_language",
             "label": "Document language", "value": "English",
             "order": 0}) + "\n", False),
        "store with an invalid record": (
            FIXTURE.joinpath(".perry", "config.jsonl").read_text()
            + BAD_RECORD + "\n", True),
        "only an invalid record": (BAD_RECORD + "\n", True),
        "torn trailing line": (
            FIXTURE.joinpath(".perry", "config.jsonl").read_text()
            + '{"kind": "track", "track": "hal', True),
    }

    def test_every_shape_gets_one_answer_from_every_tool(self):
        for label, (store, refused) in self.SHAPES.items():
            with self.subTest(label):
                d = self.project(store)
                self.assertEqual(bool(P.config_store_unusable(d)), refused,
                                 "the predicate")
                task = self.add(self.project(store))
                self.assertEqual(task.returncode != 0
                                 and REGISTER_REFUSAL in task.stderr, refused,
                                 f"perry-task: {task.stderr[-600:]}")
                goals = self.commit(self.project(store))
                self.assertEqual(REGISTER_REFUSAL in goals.stderr, refused,
                                 f"perry-goals: {goals.stderr[-600:]}")
                self.assertEqual(CENSUS_REFUSES in self.census(d), refused,
                                 "perry-lint's census")

    def test_a_non_empty_invalid_store_is_refused_exactly_as_before(self):
        """Must-not 3: the refusal for genuinely invalid records keeps its
        strictness and its wording."""
        d = self.project(FIXTURE.joinpath(".perry", "config.jsonl").read_text()
                         + BAD_RECORD + "\n")
        before = (d / "tasks.jsonl").read_bytes()
        out = self.add(d)
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn(INVALID_WORDS, out.stderr)
        self.assertIn("Nothing was written", out.stderr)
        self.assertEqual((d / "tasks.jsonl").read_bytes(), before)

    def test_the_writers_unusable_set_is_the_parsers_set(self):
        """Not a copy with the same two strings: the same object."""
        lint = _load_lint()
        ps = lint._state_module()
        self.assertIs(ps.TRACKS_STORE_UNUSABLE, P.CONFIG_STORE_UNUSABLE)


class NamespaceCheck(_Project):
    """Outcome 3: `NS-01` does not call Perry's own empty store foreign."""

    def ns01_lines(self, d: pathlib.Path) -> list[str]:
        out = run(LINT, "--root", str(d))
        return [l for l in out.stdout.splitlines()
                if "[NS-01]" in l and ".perry/config.jsonl" in l]

    def test_an_empty_config_store_is_not_a_collision(self):
        self.assertEqual(self.ns01_lines(self.project("")), [])

    def test_a_foreign_config_store_still_is(self):
        """The control: the fix is about emptiness, not about the name."""
        d = self.project(json.dumps({"not": "a perry record"}) + "\n")
        self.assertTrue(self.ns01_lines(d), "a foreign-shaped file must still "
                        "be reported, or the test above measures nothing")

    def test_emptiness_is_what_is_excused_and_never_a_record(self):
        """Scope. TASK-270 excused an empty file at a `.perry/`-anchored claim
        only, and pinned an empty `tasks.jsonl` as still foreign. TASK-275
        extended the same rule, in the same place, to the declared canonical
        stores under the state root — so this now pins the half that did NOT
        move: a record that is not Perry's is foreign at either kind of claim.
        `tests/test_empty_declared_store.py` holds the state-root half."""
        lint = _load_lint()
        schema = json.loads(lint.SCHEMA_PATH.read_text())
        claims = {c["path"]: c for c in schema["claims"]}
        d = pathlib.Path(tempfile.mkdtemp(prefix="perry-t270-ns-"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        empty = d / "empty.jsonl"
        empty.write_text("")
        foreign = d / "foreign.jsonl"
        foreign.write_text(json.dumps({"not": "a perry record"}) + "\n")
        for name in (".perry/config.jsonl", "tasks.jsonl"):
            with self.subTest(name):
                self.assertTrue(lint.looks_like_perry_state(
                    empty, schema, claims[name]))
                self.assertFalse(lint.looks_like_perry_state(
                    foreign, schema, claims[name]))


class UnsetSaysWhatItLeaves(_Project):
    """Outcome 4: emptying the store is allowed, and never silent."""

    ONE = json.dumps({"kind": "setting", "key": "document_language",
                      "label": "Document language", "value": "English",
                      "order": 0}) + "\n"

    def test_removing_the_last_record_says_so_and_names_the_recovery(self):
        d = self.project(self.ONE)
        out = run(CONFIG, "unset", "--root", str(d), "Document language")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("holding no records", out.stderr)
        self.assertIn("stays usable", out.stderr)
        self.assertIn("perry-config set <label> <value>", out.stderr)
        self.assertIn("perry-config track <name>", out.stderr)
        self.assertEqual((d / ".perry" / "config.jsonl").read_text(), "")

    def test_removing_a_record_that_is_not_the_last_says_nothing_extra(self):
        out = run(CONFIG, "unset", "--root", str(self.project()),
                  "Document language")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("holding no records", out.stderr)

    def test_dry_run_says_would_and_writes_nothing(self):
        d = self.project(self.ONE)
        out = run(CONFIG, "unset", "--dry-run", "--root", str(d),
                  "Document language")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("would leave", out.stderr)
        self.assertEqual((d / ".perry" / "config.jsonl").read_text(), self.ONE)

    def test_json_stdout_stays_one_object(self):
        d = self.project(self.ONE)
        out = run(CONFIG, "unset", "--json", "--root", str(d),
                  "Document language")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["records"], 0)
        self.assertIn("holding no records", out.stderr)

    def test_untrack_of_the_last_record_says_so_too(self):
        track = json.dumps({"kind": "track", "track": "main",
                            "mode": "project", "order": 0}) + "\n"
        d = self.project(track)
        out = run(CONFIG, "untrack", "--root", str(d), "main")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("holding no records", out.stderr)


if __name__ == "__main__":
    unittest.main()
