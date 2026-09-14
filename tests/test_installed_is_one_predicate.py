"""`installed` is one predicate, on every read payload (TASK-237 3b′).

Amendment (4) items 1 and 2, user decisions A and A (2026-09-14):

- every published read payload — `perry-task/list`, `perry-asks/list`,
  `perry-events/list`, `perry-goals/list`, `perry-decide/list`,
  `perry-knowledge/list` — carries `installed`, and on a directory that is not a
  Perry project keeps its empty shape at exit 0;
- `perry-state § installed` and all six answer from ONE criterion,
  `schema/README.md § installed`: `.perry/config.jsonl` at the project root, or
  a `.perry/` directory there AND a canonical store under the state root
  (TASK-237 Amendment (7): a store with no `.perry/` beside it does not count).
  `BOARD.md`, `OKR.md`, `phase/` and `design/` alone do not count;
- `perry-tasks board` refuses on a directory that is not installed: exit 1,
  the reason on stderr, nothing on stdout.

**Where the expectations come from.** Each directory is built here, and what
it should answer is written beside the arguments that built it. The canonical
store names are read from `schema/state-schema.json § claims` by this module,
with its own filter, not from `parsers § canonical_store_names`. No expectation
is read from a payload, a board or a tool.

**Anti-vacuity.** Both answers occur (the table asserts it), every payload is
asked of every directory, and the key set of a non-installed payload is compared
with the same payload on an installed directory, so "keeps its empty shape"
cannot pass by both being errors.

Run: python3 tests/parallel test_installed_is_one_predicate
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAYLOADS = (
    ("perry-task/list", ("perry-task", "list", "--json")),
    ("perry-asks/list", ("perry-task", "asks", "--all", "--json")),
    ("perry-events/list", ("perry-task", "events", "--json")),
    ("perry-goals/list", ("perry-goals", "list", "--json")),
    ("perry-decide/list", ("perry-decide", "list", "--json")),
    ("perry-knowledge/list", ("perry-knowledge", "list", "--json")),
)
STATE = ("perry-state", "--section", "installed")
BOARD = ("perry-tasks", "board")

CONFIG_RECORD = {"kind": "setting", "key": "document_language",
                 "label": "Document language", "value": "English", "order": 0}


def declared_stores() -> list[str]:
    claims = json.loads((ROOT / "schema" / "state-schema.json")
                        .read_text(encoding="utf-8"))["claims"]
    return sorted(c["path"] for c in claims
                  if c.get("kind") == "file" and c.get("anchor") == "state"
                  and c["path"].endswith(".jsonl"))


def build(d: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        if rel.endswith("/"):
            (d / rel).mkdir(parents=True, exist_ok=True)
            continue
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def env() -> dict:
    e = dict(os.environ)
    e.pop("PERRY_PROJECT", None)
    e["PERRY_HOME"] = str(ROOT)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return e


def run(argv: tuple[str, ...], d: Path) -> subprocess.CompletedProcess:
    tool, *rest = argv
    return subprocess.run([sys.executable, str(ROOT / "bin" / tool), *rest,
                           "--root", str(d)],
                          capture_output=True, text=True, cwd=str(d), env=env())


#: `(name, files, expected installed)`. The four the dispatch names first.
SHAPES = [
    ("empty", {}, False),
    ("board_only", {"BOARD.md": "# Board\n"}, False),
    ("config_only", {".perry/config.jsonl": json.dumps(CONFIG_RECORD) + "\n"}, True),
    # TASK-237 Amendment (7): a store with no `.perry/` beside it is some other
    # tool's file, not a Perry project (3b′ row R1). With `.perry/` it counts.
    ("tasks_only_without_dot_perry", {"tasks.jsonl": ""}, False),
    ("dot_perry_and_tasks", {".perry/": "", "tasks.jsonl": ""}, True),
    # The other markers the old disjunctions accepted.
    ("okr_only", {"OKR.md": "# OKR\n"}, False),
    ("phase_only", {"phase/001-first.md": "# Phase 001\n"}, False),
    ("design_only", {"design/DESIGN-001-x.md": "# DESIGN-001\n"}, False),
    ("all_markdown", {"BOARD.md": "# Board\n", "OKR.md": "# OKR\n",
                      "phase/001-first.md": "# P\n",
                      "design/DESIGN-001-x.md": "# D\n"}, False),
    # A store counts only under the state root. With no config the state root
    # is the directory itself, so a store one level down is not under it.
    ("store_below_an_undeclared_state_root",
     {".perry/": "", "perry/tasks.jsonl": ""}, False),
]


class InstalledIsOnePredicate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="perry-installed-")).resolve()
        cls.dirs: dict[str, tuple[Path, bool]] = {}
        shapes = list(SHAPES) + [(f"store_{name}", {".perry/": "", name: ""}, True)
                                 for name in declared_stores()] \
            + [(f"bare_store_{name}", {name: ""}, False)
               for name in declared_stores()]
        for name, files, want in shapes:
            d = cls.tmp / name
            d.mkdir()
            build(d, files)
            cls.dirs[name] = (d, want)
        jobs = [(name, key, argv) for name in cls.dirs
                for key, argv in (*PAYLOADS, ("state", STATE), ("board", BOARD))]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = pool.map(lambda j: (j[0], j[1], run(j[2], cls.dirs[j[0]][0])),
                               jobs)
        cls.out = {(name, key): proc for name, key, proc in results}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_table_is_not_vacuous(self):
        wants = {want for _d, want in self.dirs.values()}
        self.assertEqual(wants, {True, False})
        self.assertGreaterEqual(len(declared_stores()), 7,
                                "the schema declares fewer stores than on "
                                "2026-09-14; the store rows would thin out")

    def test_perry_state_answers_by_the_criterion(self):
        for name, (_d, want) in self.dirs.items():
            proc = self.out[(name, "state")]
            with self.subTest(directory=name):
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIs(json.loads(proc.stdout)["installed"], want)

    def test_every_payload_says_installed_by_the_one_criterion(self):
        for name, (_d, want) in self.dirs.items():
            for contract, _argv in PAYLOADS:
                proc = self.out[(name, contract)]
                with self.subTest(directory=name, contract=contract):
                    self.assertEqual(proc.returncode, 0, proc.stderr[-400:])
                    payload = json.loads(proc.stdout)
                    self.assertTrue(payload["contract"].startswith(contract + "/"))
                    self.assertIn("installed", payload,
                                  f"{contract} carries no `installed` key")
                    self.assertIs(payload["installed"], want)

    def test_a_non_installed_payload_keeps_its_empty_shape(self):
        installed_dir = "config_only"
        for name, (_d, want) in self.dirs.items():
            if want:
                continue
            for contract, _argv in PAYLOADS:
                with self.subTest(directory=name, contract=contract):
                    got = json.loads(self.out[(name, contract)].stdout)
                    ref = json.loads(self.out[(installed_dir, contract)].stdout)
                    self.assertEqual(sorted(got), sorted(ref))

    def test_board_refuses_where_nothing_is_installed(self):
        for name, (_d, want) in self.dirs.items():
            proc = self.out[(name, "board")]
            with self.subTest(directory=name):
                if want:
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertTrue(proc.stdout.startswith("# "))
                else:
                    self.assertEqual(proc.returncode, 1)
                    self.assertEqual(proc.stdout, "")
                    self.assertIn("not an installed Perry project", proc.stderr)


class TheCriterionIsWrittenOnceAndCited(unittest.TestCase):

    def test_the_readme_states_it(self):
        text = (ROOT / "schema" / "README.md").read_text(encoding="utf-8")
        self.assertIn("## `installed` — the one criterion", text)

    def test_each_contract_that_carries_the_key_cites_it(self):
        for contract, _argv in PAYLOADS:
            page = ROOT / "schema" / (contract.split("/")[0].split("-", 1)[1]
                                      + "-list-contract.md")
            with self.subTest(page=page.name):
                self.assertIn("schema/README.md § installed",
                              page.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
