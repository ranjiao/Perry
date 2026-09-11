"""TASK-437 — every tool that reads the task store reports the SAME population.

The defect this module exists for: `bin/perry-goals § kr_rows` called
`lib.task_status_index(snap.project_root, ...)` while the task store lives
under the STATE root. On Perry's own project — 429 records in
`perry/tasks.jsonl` — the index came back with 156 entries, all of them the
markdown projection, and every KR's progress was computed over 36 percent of
the work. Nothing anywhere said so, because `task_status_index` falls back to
`board.all_tasks` when it finds no store, and a fallback is indistinguishable
from an answer.

**Why the comparison is between TOOLS and the STORE FILE, and not inside the
code.** The spec forbids a test that computes its expectation the way the code
does, and four rounds on this project have lost to exactly that. So this module
never imports `lib`, never imports `viewer/parsers.py`, and never asks Perry
how to read a store. It reads `tasks.jsonl` with `json.loads` on each line —
six lines of stdlib, at `expected_population` below — and that is one honest
side. The other side is what each tool PUBLISHES in its own JSON contract. The
two sides share no code at all, which is what makes an agreement mean
something: the only way both can be wrong together is for the store file itself
to be wrong, and then both are right about it.

**Why it reaches the tools rather than the function.** A unit test on
`task_status_index` cannot see this defect: the function was never wrong. It
was handed the wrong directory by a caller, and the caller is a tool. The
confusable unit is a call site, so the comparison has to start from something
that contains call sites.

**How one comparison covers every tool, and not just the two alive today.**
`TestTheCensusIsComplete` greps `bin/` for callers of `task_status_index` and
fails if that set is not exactly the set this module exercises. A third reader
added next year does not quietly escape the comparison; it reddens this test
until somebody adds it. That is the difference between a guard that covers a
class and a guard that covers the two examples its author happened to know.

Run: python3 tests/parallel -j 4 test_store_population_agrees
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(os.environ.get("PERRY_HOME")
                  or Path(__file__).resolve().parent.parent)
GOALS = PERRY_HOME / "bin" / "perry-goals"
STATE = PERRY_HOME / "bin" / "perry-state"


# ── the fixture ───────────────────────────────────────────────────────────
#
# Three properties make the defect observable, and every one of them is a
# property of a REAL project rather than a trick:
#
#   1. the two roots DIFFER (`state_root: perry`), which is Perry's own layout
#      and the condition under which the defect is not invisible;
#   2. the store carries rows that are NOT on `BOARD.md` — a closed row leaves
#      the board by design (`viewer/parsers.py § _records_by_group` skips a
#      terminal status), so those rows exist in exactly one place;
#   3. `.perry/events.jsonl` is EMPTY. This is the one that matters most and it
#      is the reason Perry's own project showed no symptom: the tally in
#      `lib § kr_progress_provenance` reads
#      `status_by_id.get(tid) or last_status.get(tid)`, and on this repository
#      the event log happens to carry a state move for all 429 store ids, so a
#      second source silently supplied every value the first one lost. A
#      project adopted into Perry has a full store and no event history, which
#      is the class of project that would have seen the wrong number.

#: `group` rather than `priority` is what puts a row on the board:
#: `viewer/parsers.py § _records_by_group` files rows by `group` and SKIPS every
#: terminal one, which is the rule that makes the four closed rows below exist
#: in the store and nowhere else.
TASKS = [
    # On the board AND in the store.
    {"id": "TASK-001", "title": "Open one", "status": "in_progress",
     "group": "P1", "order": 0, "owner": "Coding Agent", "track": "main"},
    {"id": "TASK-002", "title": "Open two", "status": "not_started",
     "group": "P1", "order": 1, "owner": "Coding Agent", "track": "main"},
    {"id": "TASK-003", "title": "Blocked", "status": "blocked",
     "group": "P1", "order": 2, "owner": "Coding Agent", "track": "main"},
    # Terminal: in the store ONLY. A closed row leaves `BOARD.md`.
    {"id": "TASK-004", "title": "Closed one", "status": "done",
     "group": "P1", "order": 3, "owner": "Coding Agent", "track": "main"},
    {"id": "TASK-005", "title": "Closed two", "status": "done",
     "group": "P1", "order": 4, "owner": "Coding Agent", "track": "main"},
    {"id": "TASK-006", "title": "Closed three", "status": "done",
     "group": "P1", "order": 5, "owner": "Coding Agent", "track": "main"},
    {"id": "TASK-007", "title": "Dropped", "status": "dropped",
     "group": "P1", "order": 6, "owner": "Coding Agent", "track": "main"},
]

TERMINAL = {"done", "dropped"}

#: Every task is linked, so every task is consulted. `KR2` is the sharp one:
#: all four of its rows are terminal, so it is the KR that a project-root read
#: reports as entirely unknown.
EDGES = [
    ("TASK-001", "P001-O1-KR1"), ("TASK-002", "P001-O1-KR1"),
    ("TASK-003", "P001-O1-KR1"),
    ("TASK-004", "P001-O1-KR2"), ("TASK-005", "P001-O1-KR2"),
    ("TASK-006", "P001-O1-KR2"), ("TASK-007", "P001-O1-KR2"),
]

PHASE = """# Phase #001 — a-phase

> **Owner**: `goals` skill (only writer).
> **Started**: 2026-08-01
> **Status**: active
> **Source**: `OKR.md` v1

## Phase Focus

Two KRs, one of which links only rows that have left the board.

---

## Objective 1 — Read the store

### Key Results

| Id | KR text | Metric / Target | Linked overall KR |
|----|---------|-----------------|---------------------|
| P001-O1-KR1 | Rows still on the board | 0 (baseline 3) | |
| P001-O1-KR2 | Rows only in the store | 0 (baseline 4) | |
"""

CONFIG = [
    {"kind": "setting", "key": "document_language",
     "label": "Document language", "value": "English", "order": 0},
    {"kind": "setting", "key": "repo_layout", "label": "Repo layout",
     "value": "single", "order": 1},
    {"kind": "setting", "key": "state_root", "label": "State root",
     "value": "", "order": 2},
    {"kind": "track", "track": "main", "mode": "project", "spine": "phase/",
     "stages": "", "wip": "", "sla": "", "cycle": "", "default_rung": "V3",
     "order": 0},
]


def linkage_records() -> list[dict]:
    return [
        {"kind": "objective", "phase": "001-a-phase", "id": "O1",
         "title": "Read the store"},
        {"kind": "kr", "phase": "001-a-phase", "objective": "O1",
         "id": "P001-O1-KR1", "title": "Rows still on the board",
         "metric": "0 (baseline 3)", "target": 0, "current": 3,
         "stretch": False, "asserted_at": "2026-08-15T12:00:00Z"},
        {"kind": "kr", "phase": "001-a-phase", "objective": "O1",
         "id": "P001-O1-KR2", "title": "Rows only in the store",
         "metric": "0 (baseline 4)", "target": 0, "current": 4,
         "stretch": False, "asserted_at": "2026-08-15T12:00:00Z"},
        *({"kind": "edge", "task": task, "kr": kr_id,
           "declared_at": "2026-08-01T00:00:00Z", "actor": "goals",
           "via": "link"} for task, kr_id in EDGES),
    ]


def build_project(state_rel: str) -> Path:
    """A project whose state root is `state_rel` relative to the project root.

    `state_rel == "."` is the coinciding-roots layout that most projects have
    and where this defect is invisible; `"perry"` is Perry's own.
    """
    # `.resolve()` is LOAD-BEARING, and without it this whole module tests the
    # wrong thing. `resolve_state_root` refuses a state root that escapes the
    # project — `if project_root not in root.parents` — after calling
    # `.resolve()` on the candidate. On macOS `mkdtemp` hands back a path under
    # `/var`, which is a symlink to `/private/var`, so the resolved candidate's
    # parents are `/private/var/...` while `project_root` is still `/var/...`,
    # the containment test fails, and the declared state root is discarded in
    # silence. Measured: `declared_state_root` returned `"perry"` and
    # `resolve_state_root` returned the project root, so `TestRootsDiffer` built
    # a project whose roots COINCIDE and whose state files were then in a
    # directory no tool looked at. Every assertion still passed and the M1
    # mutation still reddened — for the wrong reason.
    root = Path(tempfile.mkdtemp(prefix="task437-")).resolve()
    (root / ".perry").mkdir()
    config = [dict(r) for r in CONFIG]
    for rec in config:
        if rec.get("key") == "state_root":
            rec["value"] = "" if state_rel == "." else state_rel
    (root / ".perry" / "config.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in config), encoding="utf-8")
    # EMPTY, deliberately. See the fixture note above.
    (root / ".perry" / "events.jsonl").write_text("", encoding="utf-8")

    state = root if state_rel == "." else root / state_rel
    state.mkdir(parents=True, exist_ok=True)
    (state / "phase").mkdir()
    (state / "phase" / "001-a-phase.md").write_text(PHASE, encoding="utf-8")
    (state / "phase" / "CURRENT").write_text("001-a-phase\n", encoding="utf-8")
    (state / "OKR.md").write_text(
        "# OKR — fixture\n\n## Mission\n\nShip it.\n\n---\n\n## v1: 2026-08-01\n",
        encoding="utf-8")
    (state / "linkage.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n"
                for r in linkage_records()), encoding="utf-8")
    (state / "tasks.jsonl").write_text(
        "".join(json.dumps(t) + "\n" for t in TASKS), encoding="utf-8")
    # The board carries the NON-terminal rows only, which is what the
    # projection does. The terminal rows exist in the store and nowhere else.
    #
    # This table has to actually PARSE, and the first draft did not — the
    # column was headed `Task` rather than `Title`, `board.all_tasks` came back
    # empty, and the wrong-root read then produced an index of size ZERO. That
    # is a worse fixture than it looks: a tool returning nothing is caught by
    # any check at all, while the defect being reproduced here is a tool
    # returning a PLAUSIBLE SUBSET. With the board parsing, a project-root read
    # yields the three open rows and hides the four closed ones, which is the
    # 156-of-429 shape on Perry's own project.
    cols = ["ID", "Title", "Owner", "Status", "Next action", "Evidence",
            "Verification", "Depends on", "Track"]
    (state / "BOARD.md").write_text(
        "# Board\n\n## P1\n\n"
        + "| " + " | ".join(cols) + " |\n"
        + "|" + "---|" * len(cols) + "\n"
        + "".join(f"| {t['id']} | {t['title']} | Coding Agent | {t['status']} "
                  f"| — | — | V3 | — | main |\n"
                  for t in TASKS if t["status"] not in TERMINAL),
        encoding="utf-8")
    return root


# ── side one: the store on disk, read by this test and by nothing else ────


def expected_population(root: Path, state_rel: str) -> dict[str, str]:
    """`id` -> status, straight off `tasks.jsonl`. **No Perry code.**

    This is the whole point of the module. It is deliberately the dumbest
    possible reader — open the file, split on newlines, `json.loads` each one —
    so that it cannot share a bug with the thing it is checking. It does not
    call `resolve_state_root` either: the test is TOLD where the state root is,
    because it is the test that built the project.
    """
    state = root if state_rel == "." else root / state_rel
    out: dict[str, str] = {}
    for line in (state / "tasks.jsonl").read_text(encoding="utf-8").split("\n"):
        if line.strip():
            rec = json.loads(line)
            out[str(rec["id"])] = str(rec.get("status") or "")
    return out


def expected_tally(population: dict[str, str], ids: list[str]) -> dict:
    """The four counts, from the dict above. Arithmetic, not a re-derivation."""
    tally = {"total": len(ids), "done": 0, "dropped": 0, "open": 0, "unknown": 0}
    for tid in ids:
        status = population.get(tid)
        if status == "done":
            tally["done"] += 1
        elif status == "dropped":
            tally["dropped"] += 1
        elif status:
            tally["open"] += 1
        else:
            tally["unknown"] += 1
    return tally


# ── side two: what each tool publishes ────────────────────────────────────


def goals_krs(root: Path) -> dict[str, dict]:
    r = subprocess.run(
        ["python3", str(GOALS), "list", "--root", str(root), "--json"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return {k["id"]: k for k in json.loads(r.stdout)["krs"]}


def state_payload(root: Path) -> dict:
    r = subprocess.run(
        ["python3", str(STATE), "--json", "--root", str(root)],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


def state_krs(root: Path) -> dict[str, dict]:
    payload = state_payload(root)
    return {k["id"]: k
            for o in (payload.get("linkage", {}).get("objectives") or [])
            for k in (o.get("krs") or [])}


#: Every tool that publishes a task population, and how to read it. The census
#: below asserts this table is complete.
READERS = {"perry-goals": goals_krs, "perry-state": state_krs}


class PopulationCase:
    """Shared fixture and assertions. **A mixin, not a `TestCase`.**

    `unittest` collects every `TestCase` subclass in the module, so a base
    class that both defines tests and IS one runs a silent extra copy of them
    against whatever `state_rel` the base happens to carry — 11 tests where 10
    were written, one of them a duplicate nobody chose. Keeping the shared code
    out of the `TestCase` hierarchy is what stops that.
    """

    state_rel = "perry"

    def setUp(self):
        self.root = build_project(self.state_rel)
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.population = expected_population(self.root, self.state_rel)

    def test_the_fixture_has_the_roots_it_claims(self):
        """The premise, asserted instead of assumed — and it was false once.

        A fixture that means to separate the two roots and quietly fails to is
        not a weaker test, it is a test of something else: `TestRootsDiffer`
        was for one revision a second copy of `TestRootsCoincide` whose state
        files sat in a directory no tool read, and it was GREEN, and the M1
        mutation reddened it for a reason that had nothing to do with the
        defect. See the `.resolve()` note in `build_project`.

        The check is taken from the tool's OWN published `project.root`, which
        is the state root it actually resolved — not from this module
        re-deriving it, and not from the config file the fixture wrote.
        """
        resolved = Path(state_payload(self.root)["project"]["root"])
        expected = self.root if self.state_rel == "." else self.root / self.state_rel
        self.assertEqual(expected, resolved,
                         "the tool did not resolve the state root this fixture "
                         "declared, so this class is not testing what it says")
        self.assertEqual(self.state_rel != ".", resolved != self.root)
        # And the store really is in exactly one place.
        self.assertTrue((resolved / "tasks.jsonl").is_file())
        if self.state_rel != ".":
            self.assertFalse((self.root / "tasks.jsonl").exists())

    def assert_agrees(self, name, krs):
        self.assertTrue(krs, f"{name} published no KRs at all")
        for kr_id, kr in sorted(krs.items()):
            ids = [str(t) for t in (kr.get("tasks") or kr.get("task_ids") or [])]
            with self.subTest(tool=name, kr=kr_id):
                self.assertEqual(
                    kr["linked_task_completion"],
                    expected_tally(self.population, ids),
                    f"{name} disagrees with {self.state_rel}/tasks.jsonl "
                    f"about {kr_id}")


class TestRootsDiffer(PopulationCase, unittest.TestCase):
    """Perry's own layout, and the only one where the defect is visible."""

    state_rel = "perry"

    def test_perry_goals_matches_the_store_on_disk(self):
        self.assert_agrees("perry-goals", goals_krs(self.root))

    def test_perry_state_matches_the_store_on_disk(self):
        self.assert_agrees("perry-state", state_krs(self.root))

    def test_no_linked_row_is_unknown(self):
        """The sharp edge, stated as the symptom rather than as a count.

        Every task in this fixture is in the store, so no tool has any excuse
        for `unknown`. Before the fix `perry-goals` reported all four of KR2's
        rows unknown, because it looked for `tasks.jsonl` in the project root
        and the board it fell back to does not carry a closed row.
        """
        for name, read in sorted(READERS.items()):
            for kr_id, kr in sorted(read(self.root).items()):
                with self.subTest(tool=name, kr=kr_id):
                    self.assertEqual(
                        0, kr["linked_task_completion"]["unknown"],
                        f"{name} cannot resolve every linked row of {kr_id} "
                        f"even though all of them are in tasks.jsonl")

    def test_the_two_tools_agree_with_each_other(self):
        """Not transitively implied, and worth its own failure message.

        Both could match the store and still differ on a field this module's
        tally does not cover; and when both are wrong the same way, this is the
        assertion whose message says "the tools agree and the store does not".
        """
        g, s = goals_krs(self.root), state_krs(self.root)
        self.assertEqual(sorted(g), sorted(s), "the two tools publish different KRs")
        for kr_id in sorted(g):
            with self.subTest(kr=kr_id):
                self.assertEqual(g[kr_id]["linked_task_completion"],
                                 s[kr_id]["linked_task_completion"])


class TestRootsCoincide(PopulationCase, unittest.TestCase):
    """Most projects. A fix that breaks this trades one wrong answer for another."""

    state_rel = "."

    def test_perry_goals_matches_the_store_on_disk(self):
        self.assert_agrees("perry-goals", goals_krs(self.root))

    def test_perry_state_matches_the_store_on_disk(self):
        self.assert_agrees("perry-state", state_krs(self.root))

    def test_no_linked_row_is_unknown(self):
        for name, read in sorted(READERS.items()):
            for kr_id, kr in sorted(read(self.root).items()):
                with self.subTest(tool=name, kr=kr_id):
                    self.assertEqual(
                        0, kr["linked_task_completion"]["unknown"])


class TestTheCensusIsComplete(unittest.TestCase):
    """The comparison covers every tool that reads the store, not two examples.

    Without this, the module is a guard over `perry-goals` and `perry-state`
    that a third reader walks straight past. With it, adding a caller of
    `task_status_index` to `bin/` reddens this test until that caller is
    entered in `READERS` — so the census is maintained by failure rather than
    by somebody remembering.
    """

    def test_readers_lists_every_caller_of_task_status_index(self):
        callers = set()
        for path in sorted((PERRY_HOME / "bin").iterdir()):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            # The DEFINITION is in bin/lib/, which this loop does not reach;
            # every hit here is a call. `\s*\(` rather than `(` because the
            # live call in perry-goals wraps its argument list to the next line.
            if re.search(r"task_status_index\s*\(", text):
                callers.add(path.name)
        self.assertEqual(
            set(READERS), callers,
            "bin/ callers of task_status_index and the tools this module "
            "compares have diverged. Add the new reader to READERS (and give "
            "it a way to publish its task population) or remove the stale one")


if __name__ == "__main__":
    unittest.main(verbosity=2)
