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


class TestOneDeclaration(unittest.TestCase):

    def test_register_events_and_writes_name_the_same_writers(self):
        mod = tool()
        subs = mod.SURFACE["subcommands"]
        names = {s["name"] for s in subs}
        self.assertLessEqual(set(mod.REGISTER_EVENTS), names,
                             "REGISTER_EVENTS names a subcommand SURFACE lacks")
        self.assertEqual(set(mod.REGISTER_EVENTS.values()), set(mod.REGISTER_SPEC))
        for key, spec in mod.REGISTER_SPEC.items():
            store = spec[1](Path("state")).name
            with self.subTest(register=key, store=store):
                by_events = {s for s, k in mod.REGISTER_EVENTS.items() if k == key}
                by_writes = {s["name"] for s in subs if store in (s.get("writes") or ())}
                self.assertTrue(by_events, "anti-vacuity: a register with no writer")
                self.assertEqual(by_writes, by_events)

    def test_every_mutating_subcommand_declares_and_no_read_does(self):
        mod = tool()
        for sub in mod.SURFACE["subcommands"]:
            with self.subTest(sub=sub["name"]):
                if sub["name"] in mod.READ_ONLY_COMMANDS:
                    self.assertEqual(sub["writes"], [])
                else:
                    self.assertTrue(sub["writes"])
                    self.assertIn("journal/", sub["writes"])
                    self.assertIn(".perry/events.jsonl", sub["writes"])

    def test_board_md_is_in_no_entry(self):
        for sub in tool().SURFACE["subcommands"]:
            with self.subTest(sub=sub["name"]):
                self.assertNotIn("BOARD.md", sub["writes"])


class TestEachWriteChangesWhatItDeclares(unittest.TestCase):
    """The measurement, kept: union of changed files per subcommand == `writes`."""

    @classmethod
    def setUpClass(cls):
        cls.seen: dict[str, set] = {}
        cls.failures: list[str] = []
        for name, prereqs, argv, _store, _check in BL.WRITES:
            cls.run_board_less(name, prereqs, argv)
            cls.run_with_a_stale_held_board(name, prereqs, argv)
        cls.run_add_on_a_queue_track_with_no_intake_store()
        cls.run_add_with_a_kr()
        cls.run_risk_migrate_from_bullets()

    @classmethod
    def record(cls, name, root: Path, state: str, argv, prereqs=(),
               held_board: bool = False):
        for pre in prereqs:
            out = inproc.run("perry-task", list(pre) + ["--root", str(root)])
            if out.returncode != 0:
                cls.failures.append(f"{name}: prerequisite {pre} exited "
                                    f"{out.returncode}: {out.stderr[-300:]}")
                return
        before = snapshot(root)
        out = inproc.run("perry-task", list(argv) + ["--root", str(root)])
        if out.returncode != 0:
            cls.failures.append(f"{name}: exited {out.returncode}"
                                f"{' with a held board' if held_board else ''}: "
                                f"{out.stderr[-300:]}")
            return
        got = {declared_name(p, state) for p in changed(before, snapshot(root))}
        if held_board:
            # Not discarded since TASK-262 round 4a: a changed `BOARD.md` lands
            # in `seen` and the comparison with `writes` goes red.
            held = (root.resolve() / state / "BOARD.md" if state
                    else root.resolve() / "BOARD.md")
            if tool().lib.retired_board_hint(held) not in out.stderr:
                cls.failures.append(f"{name}: no retired-board hint for {held}: "
                                    f"{out.stderr[-300:]}")
        cls.seen.setdefault(name, set()).update(got)

    @classmethod
    def run_board_less(cls, name, prereqs, argv):
        p = BL.Project(board=None)
        try:
            cls.record(name, p.root, "perry", argv, prereqs)
        finally:
            p.close()

    @classmethod
    def run_with_a_stale_held_board(cls, name, prereqs, argv):
        """The same write on a project whose `BOARD.md` disagrees with its
        stores. Before round 4a a stale file refused some of these and was
        rewritten by the rest."""
        p = BL.Project(board=BL.FORGED_BOARD)
        try:
            cls.record(name, p.root, "perry", argv, prereqs, held_board=True)
        finally:
            p.close()

    @classmethod
    def run_add_on_a_queue_track_with_no_intake_store(cls):
        """`add` on a queue-mode track creates the intake store."""
        p = BL.Project(board=None)
        try:
            (p.state / "intake.jsonl").unlink()
            cls.record("add", p.root, "perry",
                       ["add", "--title", "queue row", "--priority", "P2",
                        "--track", "intake", "--stage", "new",
                        "--deliverable", "d", "--verification", "v",
                        "--summary", "A queue-mode add, which creates the "
                                     "intake store."])
        finally:
            p.close()

    @classmethod
    def run_add_with_a_kr(cls):
        """`add --kr` appends the edge to `linkage.jsonl`."""
        d = Path(tempfile.mkdtemp(prefix="perry-writes-kr-")).resolve()
        try:
            config_store.write_config(d, tracks=EDGE.TRACKS)
            (d / "linkage.jsonl").write_text(EDGE.store({}), encoding="utf-8")
            (d / "tasks.jsonl").write_text(EDGE.task_record("TASK-100") + "\n",
                                           encoding="utf-8")
            cls.record("add", d, "",
                       ["add", "--title", "kr row", "--priority", "P2",
                        "--deliverable", "d", "--verification", "v",
                        "--kr", "P003-O1-KR1", "--summary",
                        "An add given a KR, which appends its edge."])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    @classmethod
    def run_risk_migrate_from_bullets(cls):
        """The one write that needs a held board: bullets are its input."""
        p = BL.Project(board=BULLET_BOARD)
        try:
            (p.state / "risks.jsonl").unlink()
            cls.record("risk-migrate", p.root, "perry", ["risk-migrate"],
                       held_board=True)
        finally:
            p.close()

    def test_every_case_ran(self):
        self.assertEqual(self.failures, [])

    def test_every_declared_write_is_measured(self):
        declared = {s["name"] for s in tool().SURFACE["subcommands"] if s["writes"]}
        self.assertEqual(set(self.seen), declared)
        self.assertGreaterEqual(len(declared), 27)

    def test_writes_is_the_union_of_what_its_cases_changed(self):
        for sub in tool().SURFACE["subcommands"]:
            if not sub["writes"]:
                continue
            with self.subTest(sub=sub["name"]):
                self.assertEqual(self.seen.get(sub["name"], set()),
                                 set(sub["writes"]))


if __name__ == "__main__":
    unittest.main()
