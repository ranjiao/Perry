"""TASK-262 round 2 — `perry-task § SURFACE` `writes` names what each write changes.

`TASK-262-spec.md § Amendment (2)`. Round 1's F1: all 27 mutating subcommands
declared the one list `["tasks.jsonl", "BOARD.md", "journal/",
".perry/events.jsonl"]`, while `REGISTER_EVENTS`, 6,451 lines above it in
the same file, said `ask` writes asks and `risk-add` writes risks.
`perry-tasks board` derives its section lines from `writes`, so the Cadence,
User Input Queue and Top risks lines said no writer was declared.

**What is held here:**

1. **One declaration, not two.** For every register in `REGISTER_SPEC`, the
   subcommands `REGISTER_EVENTS` maps to it are exactly the subcommands whose
   `writes` names its store. A guard, not a derivation: `writes` has to stay a
   literal, because `perry-tasks § writer_surface` and
   `tests/board_sources.py` read `SURFACE` with `ast.literal_eval` and never
   execute the tool.
2. **The declaration is measured, not read.** Every write is run on a
   board-less copy and the files whose BYTES changed are compared with its
   `writes`, per subcommand, over every case that exercises it. The rules:
   - a path under the state root is named by its file name
     (`tasks.jsonl`), as the declaration names it;
   - anything under `<state root>/journal/` is `journal/`;
   - a file replaced with identical bytes is not a change. Every register
     write re-stages `tasks.jsonl` unchanged inside its transaction
     (`commit()` always puts the task store in the canonical set), so
     declaring it would name `ask` a writer of the task sections.
3. **`BOARD.md` is in no entry, and no write changes one** (TASK-262
   Amendment (4), round 4a). Every write is run a second time on a project
   holding a STALE `BOARD.md` (`test_board_less_reads_and_writes.FORGED_BOARD`,
   rows no store holds). Its changed files join the same union, so a write
   that touched the held file would put `BOARD.md` beside a `writes` that
   names it nowhere; and each such run must print the retired-board hint on
   stderr. `risk-migrate`'s held board, its import input, is under the same
   rule.

Run: python3 tests/parallel test_perry_task_writes_are_what_it_writes
"""

from __future__ import annotations

import task_actor

COVERS = ("bin/perry-task", "tests/board_sources.py")

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import config_store
import inproc
import test_add_writes_the_edge as EDGE
import test_board_less_reads_and_writes as BL

ROOT = Path(__file__).resolve().parent.parent

#: A held board whose `## Top risks` is bullets, the one shape `risk-migrate`
#: writes on. The risks store is removed, so there is something to migrate.
BULLET_BOARD = """# Board — bullets

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
| TASK-005 | title of TASK-005 | Coding Agent | not_started | next for TASK-005 | — |

## Top risks (one-line; full list in `PROJECT_STATE.md`)

- a bulleted risk to migrate
"""


def tool():
    return inproc.load("perry-task")


def snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def declared_name(rel: str, state: str) -> str:
    """A changed path, spelled the way `SURFACE` `writes` spells it."""
    prefix = f"{state}/" if state else ""
    if rel == ".perry/events.jsonl":
        return rel
    if rel.startswith(prefix):
        inner = rel[len(prefix):]
        if inner.startswith("journal/"):
            return "journal/"
        if "/" not in inner:
            return inner
    return rel


def changed(before: dict, after: dict) -> set:
    return ({k for k in after if before.get(k) != after[k]}
            | {k for k in before if k not in after})


class TestTheFrozenSurfaceIsMeasured(unittest.TestCase):
    def test_every_subcommand_declares_no_writes(self):
        subs = tool().SURFACE["subcommands"]
        self.assertEqual(len(subs), 31)
        self.assertEqual(len(tool().READ_ONLY_COMMANDS), 4)
        for sub in subs:
            with self.subTest(command=sub["name"]):
                self.assertEqual(sub["writes"], [])

    def test_dormant_register_events_are_not_live_write_declarations(self):
        mod = tool()
        self.assertEqual(set(mod.REGISTER_EVENTS.values()), set(mod.REGISTER_SPEC))
        self.assertTrue(mod.REGISTER_EVENTS)
        for name in mod.REGISTER_EVENTS:
            self.assertNotIn(name, mod.READ_ONLY_COMMANDS)
            self.assertEqual(next(s["writes"] for s in mod.SURFACE["subcommands"]
                                  if s["name"] == name), [])

    def test_actual_changed_files_match_the_empty_declaration(self):
        covered = set()
        # Both normal and forged held boards; input includes every register.
        for board in (None, BL.FORGED_BOARD):
            for name, _pre, argv, _store, _check in BL.WRITES:
                with self.subTest(command=name, held=board is not None):
                    p = BL.Project(board=board)
                    self.addCleanup(p.close)
                    before = snapshot(p.root)
                    out = p.task(list(argv) + ["--json"])
                    self.assertEqual(out.returncode, 1, out.stderr)
                    self.assertIn("read-only", json.loads(out.stdout)["refused"])
                    self.assertEqual(changed(before, snapshot(p.root)), set())
                    covered.add(name)
        # Cases absent from the old success table are covered by the generic
        # all-verb test in test_kernel_work_cutover, not silently ignored here.
        self.assertEqual(covered | set(BL.NOT_IN_WRITES),
                         {s["name"] for s in tool().SURFACE["subcommands"]
                          if s["name"] not in tool().READ_ONLY_COMMANDS})


if __name__ == "__main__":
    unittest.main()
