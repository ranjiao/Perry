"""**An ordinary write may never SHRINK a canonical store.** TASK-203, USER-906.

Three rounds of TASK-203 shipped three different predicates — the command name,
an identity tuple, the section's shape — and all three ended in the same
defect: an ordinary command silently truncating a canonical register store at
exit code 0, with `perry-lint` reporting the wreck as `0 row(s) drifted`. The
user answered USER-906 with option B, which is not a fourth predicate:

    Only `purge`, `resolve-intake` and `intake-sweep` may reduce a record
    count. Any derivation producing fewer records than the store already holds
    is a REFUSAL, not a write.

The order of this file is the argument.

1. **The fixtures are asserted to be the shape under test, before anything is
   asserted about behaviour.** Round 3 shipped a `foreign`-shape test whose
   legend table landed under `## Top risks` because `ensure_section` anchors
   `## Intake` before `## P0`, so the section was never foreign and the test
   was green with the guard reverted. Every board this module builds is
   handed to `perry_store`'s own shape function and the answer is asserted.

2. **The reproduction from `evidence/2026-08/TASK-203-merge-hold.md`**, which
   is this row's reason to exist: 3 records to 0 on `perry-task add --track
   ops` with `## Intake` absent.

3. **The four doors**, each named for the round that found it.

4. **The three commands that may still shrink**, because an invariant that
   also blocks the sweep has broken the register rather than protected it.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import task_actor

COVERS = ("bin/perry-task", "bin/perry-lint", "bin/perry_store.py")

import contextlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_asks_store import REGISTER as ASK_TABLE
from test_intake_store import REGISTER as INTAKE_TABLE
from test_risks_store import REGISTER as RISK_TABLE
from task_writer_support import PT

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
sys.path.insert(0, str(PERRY_HOME / "tests"))
import config_store  # noqa: E402
import inproc  # noqa: E402
import perry_store as S  # noqa: E402

TASK = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"
LINT = PERRY_HOME / "bin" / "perry-lint"

#: One queue-mode track. This repository declares one of its own —
#: `.perry/config.jsonl` carries a `kind: track` record for `intake` in
#: `queue` mode, declared 2026-08-20 under TASK-133 — which is why the
#: merge-hold reproduction is reachable on `main` and not only on a synthetic
#: project. It was a `## Tracks` row in `.perry/config.md` until ADR-019.
OPS_QUEUE = [config_store.track("ops", "queue", spine="OKR.md",
                                stages="new→triaged→resolved", wip="6",
                                sla="5d", cycle="1w", default_rung="V2")]

TASK_HEAD = ("| ID | Title | Owner | Status | Next action | Evidence |\n"
             "|---|---|---|---|---|---|\n")

#: The register's heading, its own writing subcommand, and the store file.
#: One row per register, so a test that covers "every register" is quantified
#: over this and not over whichever two somebody remembered.
REGISTERS = {
    "intake": ("Intake", "intake.jsonl", S.intake_section_shape),
    "asks": ("User Input Queue", "asks.jsonl", S.ask_section_shape),
    "risks": ("Top risks", "risks.jsonl", S.risk_section_shape),
}

#: How each register is written from scratch by its own command. The flags are
#: the ones `perry-task --help` documents.
OWN_WRITE = {
    "intake": ("intake", "--title", "a fresh request"),
    "asks": ("ask", "--needed", "a fresh question"),
    "risks": ("risk-add", "--title", "a fresh risk"),
}

# ── the four shapes each register section can be in ───────────────────────
#
# `absent` | `table` | `prose`/`bullets` | `foreign`, the four
# `<register>_section_shape` reports. `foreign` is two shapes, not one — a
# second table under the heading, and a table whose key column was renamed —
# and both are built here because round 2 measured a store going to zero
# through each of them and round 3 shipped a test that reached neither.

LEGEND = ("\n| Key | Meaning |\n|---|---|\n| — | still waiting |\n")

PROSE = "Nothing here yet; we write these up as they come in.\n"


def _renamed_key(table: str, old: str, new: str) -> str:
    """The register table with its KEY column renamed — a `foreign` shape.

    Only the header line is touched, and the assertion that the rename landed
    is in the caller's control test rather than here.
    """
    head, rest = table.split("\n", 1)
    assert f"| {old} |" in head, head
    return head.replace(f"| {old} |", f"| {new} |", 1) + "\n" + rest


SHAPES = {
    "intake": {
        "table": INTAKE_TABLE,
        "absent": None,
        "prose": PROSE,
        "foreign-two-tables": INTAKE_TABLE + LEGEND,
        "foreign-renamed-key": _renamed_key(INTAKE_TABLE, "Request", "Ask"),
    },
    "asks": {
        "table": ASK_TABLE,
        "absent": None,
        "prose": PROSE,
        "foreign-two-tables": ASK_TABLE + LEGEND,
        "foreign-renamed-key": _renamed_key(ASK_TABLE, "Needed from user",
                                            "Wanted"),
    },
    "risks": {
        "table": RISK_TABLE,
        "absent": None,
        "bullets": "- a risk somebody wrote by hand\n",
        "foreign-two-tables": RISK_TABLE + LEGEND,
        "foreign-renamed-key": _renamed_key(RISK_TABLE, "Risk", "Hazard"),
    },
}

#: What `<register>_section_shape` must answer for each entry above. Asserted
#: in `TestTheFixturesAreTheShapeUnderTest`, which is the control that stops
#: this module repeating round 3's vacuous foreign test.
EXPECTED_SHAPE = {
    "table": "table", "absent": "absent", "prose": "prose",
    "bullets": "bullets", "foreign-two-tables": "foreign",
    "foreign-renamed-key": "foreign",
}


def build_board(intake=INTAKE_TABLE, asks=ASK_TABLE, risks=RISK_TABLE,
                rows: str = "") -> str:
    """A whole board. A section given `None` is omitted entirely."""
    out = ["# Board — register invariant\n"]

    def section(heading, body):
        if body is not None:
            out.append(f"## {heading}\n\n{body}")

    section("Intake", intake)
    out.append(f"## P0 (must finish this period)\n\n{TASK_HEAD}{rows}")
    out.append(f"## P1\n\n{TASK_HEAD}")
    out.append(f"## P2\n\n{TASK_HEAD}")
    section("User Input Queue", asks)
    section("Top risks", risks)
    return "\n".join(out)


def parse(text: str):
    """(board, ops) for a board given as text, without touching any project."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "BOARD.md"
        p.write_text(text, encoding="utf-8")
        board = PT.Board(p)
        board.lines                      # force the read while the file exists
        return board, PT._ops()


@contextlib.contextmanager
def the_write_mutates_the_held_board():
    """**Constructed, not reached** — TASK-262 round 4a.

    Every door in this module was opened the same way: a human edits the held
    `BOARD.md`, and the next write builds its board from that file, so its
    derivation disagrees with the store. Since round 4a no write reads a held
    file (`bin/perry-task § main` builds with `declared_write_board`, from the
    stores), so no hand edit reaches `commit()` and none of these doors can be
    opened from the command line. `TestAHandEditToAHeldBoardReachesNoStore`
    below asserts exactly that, on the real path.

    The guards behind the doors — `refuse_to_shrink`, the bounded exemption,
    `carry_forward_is_addressable` and TASK-243's substitution report — are
    still in `commit()`, and a write whose in-memory board disagrees with its
    stores is still the state they exist for. So that state is CONSTRUCTED
    here the way `test_commit_asks_the_invariant_about_tasks_jsonl` constructs
    its own: for the duration of one in-process call, `declared_write_board`
    is replaced by the held file. It proves each guard is wired and still
    refuses or reports; it does not claim the state is reachable through the
    CLI, and the round 4a result says so in those words.
    """
    tool = inproc.load("perry-task")
    real = tool.declared_write_board

    def held(schema, state_root, path, project_root=None):
        return tool.Board(path)

    tool.declared_write_board = held
    try:
        yield
    finally:
        tool.declared_write_board = real


class Fixture:
    """A throwaway Perry project with the three register stores minted.

    **A fixture whose held board a test edits by hand drives its writes
    through `the_write_mutates_the_held_board`** (TASK-262 round 4a):
    `write_board` sets `hand_edited`, and `run(..., held=False)` asks for the
    real path explicitly.
    """

    def __init__(self, board: str, tracks: list | None = None,
                 mint=("intake", "asks", "risks")):
        self.dir = tempfile.mkdtemp()
        self.root = Path(self.dir)
        # `.perry/config.md` with a `## Tracks` table until ADR-019; the
        # register is `.perry/config.jsonl` and `tracks` is a list of records.
        config_store.write_config(self.root, tracks=tracks)
        (self.root / "BOARD.md").write_text(board, encoding="utf-8")
        self.hand_edited = False
        self._tasks("write", "--from-board")
        for name in mint:
            self._tasks(f"{name}-write", "--from-board")

    # **In-process** (TASK-368). Measured in this tree before converting: 246
    # `perry-tasks` calls and 94 `perry-task`, 13.0 of this module's 13.8
    # seconds are children, and the boundary is 97.7% / 92.1% of one of those
    # calls against a fixture — 90.2% of the module. Neither tool carries a
    # root-dependent module global: `perry-tasks`' two (`_TASK_MODULE`,
    # `_LINT_MODULE`) are sibling-module handles, and `perry-task`'s derive
    # from the schema at `PERRY_HOME`. Every `Fixture` gets its own
    # `mkdtemp()`, so no root is visited twice in one process either.
    def _tasks(self, *argv) -> None:
        r = inproc.run("perry-tasks", [*argv, "--root", str(self.root)])
        if r.returncode:
            raise AssertionError(" ".join(argv) + "\n" + r.stdout + r.stderr)

    def run(self, *argv, held: bool | None = None) -> tuple[int, str]:
        held = self.hand_edited if held is None else held
        with (the_write_mutates_the_held_board() if held
              else contextlib.nullcontext()):
            r = inproc.run("perry-task", task_actor.owned([*argv, "--root", str(self.root)], 'test_register_store_invariant'))
        return r.returncode, r.stdout + r.stderr

    def raw(self, name: str) -> bytes:
        p = self.root / name
        return p.read_bytes() if p.exists() else b""

    def records(self, name: str) -> list[dict]:
        return [json.loads(l) for l in
                self.raw(name).decode("utf-8").split("\n") if l.strip()]

    def board_text(self) -> str:
        return (self.root / "BOARD.md").read_text(encoding="utf-8")

    def write_board(self, text: str) -> None:
        (self.root / "BOARD.md").write_text(text, encoding="utf-8")
        self.hand_edited = True

    def cleanup(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


class Base(unittest.TestCase):
    def fixture(self, *a, **kw) -> Fixture:
        f = Fixture(*a, **kw)
        self.addCleanup(f.cleanup)
        return f


# ── 1. the fixtures are the shape under test ──────────────────────────────


class TestTheFixturesAreTheShapeUnderTest(Base):
    """Controls. Every assertion below this class rests on these.

    Round 3's third shape test appended its legend table to the END of the
    board file, which put it under `## Top risks` rather than `## Intake` —
    `ensure_section` anchors `## Intake` before `## P0`, so the last section is
    not the one the test named. The section stayed a clean single table, the
    `foreign` branch was never reached, and the test was green with the guard
    reverted AND green with the reader weakened. The `foreign` shape had no
    test on any register.
    """

    def test_every_shape_fixture_really_is_the_shape_it_claims(self):
        for key, (heading, _store, shape_of) in REGISTERS.items():
            for name, body in SHAPES[key].items():
                with self.subTest(register=key, shape=name):
                    text = build_board(**{key: body})
                    board, ops = parse(text)
                    self.assertEqual(shape_of(board, ops)[0],
                                     EXPECTED_SHAPE[name],
                                     f"`## {heading}` is not {name}:\n{text}")

    def test_the_foreign_legend_lands_inside_the_named_section(self):
        """The precise defect round 3 shipped, asserted as a fact about text."""
        for key, (heading, _store, _shape) in REGISTERS.items():
            with self.subTest(register=key):
                text = build_board(**{key: SHAPES[key]["foreign-two-tables"]})
                body = text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]
                self.assertIn("| Key | Meaning |", body,
                              f"the legend is not under `## {heading}`")

    def test_the_three_register_tables_hold_the_rows_these_tests_count(self):
        board, ops = parse(build_board())
        self.assertEqual(len(S.intake_records(board, ops)), 4)
        self.assertEqual(len(S.ask_records(board, ops)), 4)
        self.assertEqual(len(S.risk_records(board, ops)), 3)

    def test_the_minted_stores_hold_what_the_board_holds(self):
        f = self.fixture(build_board())
        self.assertEqual(len(f.records("intake.jsonl")), 4)
        self.assertEqual(len(f.records("asks.jsonl")), 4)
        self.assertEqual(len(f.records("risks.jsonl")), 3)


# ── 2. the reproduction ───────────────────────────────────────────────────


def board_without_intake(f: Fixture) -> None:
    """Delete `## Intake` from the board on disk, and nothing else.

    The state a project has before its first intake row, and the state
    `/pmo triage` can produce.
    """
    out, skip = [], False
    for line in f.board_text().split("\n"):
        if line.startswith("## Intake"):
            skip = True
            continue
        if skip and line.startswith("## "):
            skip = False
        if not skip:
            out.append(line)
    f.write_board("\n".join(out))
    assert "## Intake" not in f.board_text()


class TestTheReproduction(Base):
    """`evidence/2026-08/TASK-203-merge-hold.md`, on a queue-mode track.

    Measured on this repository's own data: with `## Intake` absent,
    `perry-task add --track intake` took `perry/intake.jsonl` from 8240 bytes
    and 24 records to 0, exit code 0, and `perry-lint` then reported
    `0 error(s)` and `intake store: 0 record(s), 0 row(s) drifted`.

    `cmd_add`'s queue branch calls `ensure_section("Intake", …)` BEFORE
    `commit()` reads anything, so any gate that asks about the board is asked
    about a board the command it guards has already changed. The invariant does
    not ask about the board. It counts.

    **Constructed since TASK-262 round 4a** (`the_write_mutates_the_held_board`):
    the deleted `## Intake` is in a held file no write reads any more.
    """

    def setUp(self):
        self.f = self.fixture(build_board(), tracks=OPS_QUEUE)
        self.before = self.f.raw("intake.jsonl")
        board_without_intake(self.f)

    def test_the_reproduction_starts_from_a_store_with_records_to_lose(self):
        """The control. A test that starts from an empty store proves nothing."""
        self.assertEqual(len(self.f.records("intake.jsonl")), 4)
        self.assertNotIn("## Intake", self.f.board_text())


# ── 3. the four doors ─────────────────────────────────────────────────────


# ── 4. the three commands that may still shrink ───────────────────────────


# ── 4b. the exemption is BOUNDED, on boards where a shrink is possible ────


#: `## Intake` with rows 3 and 4 discharged, so ONE sweep legitimately removes
#: TWO records. A bound written as the literal `1` rather than as the sweep's
#: own count is red on this board and green on the shared fixture, which is
#: why the class below uses both.
INTAKE_TWO_DISCHARGED = (
    "| Arrived | Request | Outcome |\n"
    "|---|---|---|\n"
    "| 2026-08-21 | a request that is still waiting for an outcome | — |\n"
    "| 2026-08-21 | a second request still waiting for an outcome | — |\n"
    "| 2026-08-27 | a request that went nowhere "
    "| dropped 2026-08-28 — folded into TASK-190 |\n"
    "| 2026-08-28 | a request that is waiting on the next phase "
    "| deferred 2026-08-28 — until phase 004 opens |\n"
)


def tidy_intake_rows_off_the_board(f: Fixture, keep) -> None:
    """Hand-tidy `## Intake` down to `keep` (1-based row numbers), and nothing
    else — the store is deliberately NOT rewritten.

    This is the `/pmo triage` state and the state
    `evidence/2026-08/TASK-203-merge-hold.md` was measured in: rows leave the
    board by hand and the store still holds them. The board is now SMALLER
    than the store, so the next derivation shrinks it — which is the whole
    condition round 4's tests for the three removal commands never created.
    """
    out, inside, seen = [], False, 0
    for line in f.board_text().split("\n"):
        if line.startswith("## "):
            inside = line.startswith("## Intake")
            out.append(line)
            continue
        if inside and line.startswith("|"):
            seen += 1
            # The first two `|` lines are the header and its separator.
            if seen <= 2 or (seen - 2) in keep:
                out.append(line)
            continue
        out.append(line)
    f.write_board("\n".join(out))


class TestTheExemptionIsBounded(Base):
    """**An allowed command may shrink by exactly the count it declares.**

    Round 4 granted the exemption by COMMAND NAME and without a bound, so a
    listed command could shrink a canonical store by any amount — including a
    shrink it did not perform. The V4 round-4 review used exactly that against
    this repository's own intake data: `resolve-intake`, which removes no
    record at all, took `perry/intake.jsonl` from 11781 bytes / 28 records to
    1420 bytes / 4 records at exit code 0, with `perry-lint` reporting
    `intake store: 4 record(s), 0 row(s) drifted`. That is the signature of
    `evidence/2026-08/TASK-203-merge-hold.md` — the defect this row exists to
    stop — reached one command over from the refusal that stops it.

    `intake-sweep` had the same hole: it reported sweeping one row and took the
    store from 4 records to 1.

    **The reason the round-4 suite could not see it is the reason this class is
    written the way it is.** Removing `"resolve-intake"` from the allowlist
    reddened two tests, both assertions about the constant, because the one
    behavioural test ran on a clean board where no shrink was possible and
    asserted `rc == 0` — which is true with the allowance and without it. So
    every test here first asserts, as a CONTROL, that the store is bigger than
    the board: on a clean board these tests do not merely pass, they fail their
    own control.
    """

    def drifted(self, keep, table=INTAKE_TABLE) -> Fixture:
        """A fixture whose store holds 4 records and whose board holds `keep`.

        The controls are here rather than in each test so that no test in this
        class can be written without them.

        **The last one is the one that makes this a control rather than a
        description.** The V4 round-5 review checked and found that
        `drifted([1, 2, 3, 4])` — a clean board, no drift, no shrink possible —
        passed every assertion here, because nothing compared the two numbers.
        The tests still went red on their behaviour assertions, so nothing was
        green for the wrong reason; but the claim "a clean-board version fails
        its own control" was true of the prose and not of the code. It is now
        true of the code.
        """
        f = self.fixture(build_board(intake=table))
        self.assertEqual(len(f.records("intake.jsonl")), 4,
                         "control: the store is minted from the whole table")
        tidy_intake_rows_off_the_board(f, keep)
        board = PT.Board(f.root / "BOARD.md")
        rows = len(board.section_rows("Intake"))
        self.assertEqual(rows, len(keep),
                         "control: the board was tidied to the kept rows")
        records = len(f.records("intake.jsonl"))
        self.assertEqual(records, 4,
                         "control: the STORE still holds every record")
        self.assertLess(rows, records,
                        "control: the board must hold FEWER rows than the "
                        "store, or no shrink is possible and this test cannot "
                        "tell whether the bound fired — which is exactly how "
                        "round 4's clean-board test passed with the allowance "
                        "and without it")
        return f


    def test_purge_may_not_take_two_records_with_one_removal(self):
        """`purge` declares 1, and `commit()` holds it to 1.

        `commit()`'s removal branch is `[r for r in current if r["id"] !=
        removed_id]`, so a store carrying the subject's id TWICE loses BOTH on
        one `purge` — a drop of 2 against a declaration of 1.

        Like `test_commit_asks_the_invariant_about_tasks_jsonl`, this state is
        constructed rather than reached: `load_task_records` refuses a
        duplicate id before `commit()` ever sees one, so the store is handed to
        `commit()` through a replaced loader for the duration of one call. It
        proves the DECLARATION is what bounds the write; it does not claim the
        duplicate is reachable through the CLI, and the RESULT says so in those
        words. `--dry-run` is used so a build with the bound removed writes
        nothing while going green.
        """
        rows = ("| TASK-001 | a task | Coding Agent | not_started | — | — |\n")
        f = self.fixture(build_board(rows=rows), mint=())
        board = PT.Board(f.root / "BOARD.md")
        current = PT.load_task_records(f.root)
        self.assertEqual([r["id"] for r in current], ["TASK-001"],
                         "control: the fixture holds exactly the one record")
        doubled = [dict(current[0]), dict(current[0])]
        event = {"ts": "2026-08-30T00:00:00Z", "event": "purge",
                 "id": "TASK-001", "title": "a task", "actor": "test",
                 "from": "not_started", "to": "purged"}
        original = PT.load_task_records
        PT.load_task_records = lambda _root: [dict(r) for r in doubled]
        try:
            with self.assertRaises(PT.Refused) as caught:
                PT.commit(f.root, f.root, board, "- [TASK-001] purged", event,
                          True, removed_id="TASK-001")
        finally:
            PT.load_task_records = original
        self.assertIn("removes 1 record(s)", str(caught.exception))
        self.assertIn("tasks.jsonl", str(caught.exception))


# ── 5. the invariant, on its own ──────────────────────────────────────────


class TestTheInvariantItself(unittest.TestCase):
    """`refuse_to_shrink` as a unit — the one place the rule is written.

    **These are assertions about the function and the constant, and the V4
    round-4 review is right that they do not count on their own.** Removing
    `"resolve-intake"` from round 4's allowlist reddened two tests of exactly
    this kind and nothing else, while the reachable defect went unnoticed. They
    are kept because a rule written in one place deserves a test in one place;
    the tests that carry the argument are in `TestTheExemptionIsBounded`, on
    boards where a shrink is possible.
    """

    def call(self, event: str, before: int, after: int, **extra):
        PT.refuse_to_shrink("intake", Path("/nowhere/intake.jsonl"),
                            {"event": event, **extra}, before, after)

    def test_an_ordinary_event_may_not_reduce_a_record_count(self):
        with self.assertRaises(PT.Refused):
            self.call("add", 3, 2)

    def test_growing_and_holding_steady_are_both_fine(self):
        self.call("add", 3, 3)
        self.call("add", 3, 9)
        self.call("add", 0, 0)

    def test_each_named_command_may_shrink_by_exactly_what_it_declares(self):
        for event, declared in (("purge", 1), ("resolve-intake", 0),
                                ("intake-sweep", 2)):
            with self.subTest(event=event):
                self.call(event, 9, 9 - declared, count=declared)
                with self.assertRaises(PT.Refused):
                    self.call(event, 9, 9 - declared - 1, count=declared)

    def test_the_allowance_is_the_three_commands_user_906_named_and_a_count(self):
        self.assertEqual(PT.SHRINK_ALLOWANCE,
                         {"purge": 1, "resolve-intake": 0,
                          "intake-sweep": "count"})

    def test_a_declaration_this_tool_cannot_read_declares_nothing(self):
        """Fail-closed. An unreadable count is 0, not "as much as you like".

        The frozenset this replaced treated the NAME as the permission, so a
        sweep whose count went missing would still have been allowed to remove
        everything. Every one of these is a shrink of 1 against a declaration
        the tool cannot read, and every one of them refuses.
        """
        for count in (None, "two", -1, True, 1.0):
            with self.subTest(count=count):
                self.assertEqual(
                    PT.declared_removal({"event": "intake-sweep",
                                         "count": count}), 0)
                with self.assertRaises(PT.Refused):
                    self.call("intake-sweep", 4, 3, count=count)

    def test_a_command_nobody_named_declares_nothing(self):
        self.assertEqual(PT.declared_removal({"event": "add", "count": 9}), 0)
        self.assertEqual(PT.declared_removal({}), 0)

    def test_the_task_store_is_under_the_same_rule_as_the_registers(self):
        """One function, called at every canonical store, not one per store."""
        with self.assertRaises(PT.Refused):
            PT.refuse_to_shrink("tasks", Path("/nowhere/tasks.jsonl"),
                                {"event": "next"}, 5, 4)
        PT.refuse_to_shrink("tasks", Path("/nowhere/tasks.jsonl"),
                            {"event": "purge"}, 5, 4)
        with self.assertRaises(PT.Refused):
            PT.refuse_to_shrink("tasks", Path("/nowhere/tasks.jsonl"),
                                {"event": "purge"}, 5, 3)


class TestTheTaskStoreCallSiteIsWired(Base):
    """**A guard that survives its own deletion does not count.**

    The rule above is a unit test of the FUNCTION. It says nothing about
    whether `commit()` actually calls it for `tasks.jsonl`, and deleting those
    two lines reddened nothing at all in the first mutation round — which is
    the shape TASK-095 shipped and was failed for.

    The reason it is hard to reach is real and is stated in the RESULT rather
    than worked around: `commit()` builds `records` FROM `current` by removing
    at most one record and appending at most one, so the only branch that
    shortens the task store is `purge`, whose declaration in `SHRINK_ALLOWANCE`
    is 1 — and `test_purge_may_not_take_two_records_with_one_removal` is what
    holds it to that. The
    one input that shortens it otherwise is a store carrying the subject's id
    twice — and `load_task_records` refuses a duplicate id before `commit()`
    ever sees it.

    So this test constructs that state deliberately, by replacing
    `load_task_records` for the duration of one `commit()` call. It proves the
    CALL SITE is wired; it does not claim the state is reachable through the
    CLI, and the RESULT says so in those words. `--dry-run` is used so that a
    build with the call site deleted writes nothing while going red.
    """

    def test_commit_asks_the_invariant_about_tasks_jsonl(self):
        row = ("| TASK-001 | a task | Coding Agent | not_started | — | — |\n")
        f = self.fixture(build_board(rows=row), mint=())
        board = PT.Board(f.root / "BOARD.md")
        current = PT.load_task_records(f.root)
        self.assertEqual([r["id"] for r in current], ["TASK-001"],
                         "control: the fixture holds exactly the one record")
        doubled = [dict(current[0]), dict(current[0])]
        event = {"ts": "2026-08-29T00:00:00Z", "event": "next",
                 "id": "TASK-001", "title": "a task", "actor": "test",
                 "from": "—", "to": "do the next thing"}
        original = PT.load_task_records
        PT.load_task_records = lambda _root: [dict(r) for r in doubled]
        try:
            with self.assertRaises(PT.Refused) as caught:
                PT.commit(f.root, f.root, board, "- [TASK-001] next", event,
                          True)
        finally:
            PT.load_task_records = original
        self.assertIn("may never make a canonical store smaller",
                      str(caught.exception))
        self.assertIn("tasks.jsonl", str(caught.exception))


# ── 6. the carry-forward join ─────────────────────────────────────────────


class TestTheCarryForwardJoin(Base):
    """`carry_forward_is_addressable` decides whether `discharged` may cross a
    write. It is NOT the invariant and gates no write — but a row can be
    replaced without the count moving, which the invariant cannot see."""

    @staticmethod
    def rec(order: int, request: str, arrived: str = "2026-08-01") -> dict:
        return {"order": order, "arrived": arrived, "request": request,
                "outcome": "—", "discharged": False}

    def test_a_repeated_identity_is_no_identity_even_when_no_two_are_adjacent(self):
        """Uniqueness ALONE, with adjacency excluded by construction.

        Round 3 found the shipped uniqueness test could not tell uniqueness
        from adjacency: its duplicate pair sat at orders 2 and 3, so a weaker
        guard tripping only on CONSECUTIVE equal identities was green across
        the whole suite. Here the duplicates are at 0/2 and 1/3 and no two
        neighbours are equal — asserted below, not assumed — and the derived
        rows sit at exactly the stored positions, so the positional check
        passes and only the uniqueness clause can answer False.
        """
        current = [self.rec(0, "A"), self.rec(1, "B"),
                   self.rec(2, "A"), self.rec(3, "B")]
        ident = [(r["request"], r["arrived"]) for r in current]
        self.assertTrue(
            all(a != b for a, b in zip(ident, ident[1:])),
            "control: no two adjacent identities may be equal, or this test "
            "is about adjacency")
        derived = [dict(r) for r in current]
        self.assertTrue(
            all(d["request"] == c["request"] for d, c in zip(derived, current)),
            "control: every derived row is at its stored position, so the "
            "positional check cannot be what answers")
        self.assertFalse(PT.carry_forward_is_addressable("intake", derived,
                                                         current))

    def test_the_same_shape_with_unique_requests_keeps_its_carry_forward(self):
        current = [self.rec(0, "A"), self.rec(1, "B"),
                   self.rec(2, "C"), self.rec(3, "D")]
        self.assertTrue(PT.carry_forward_is_addressable(
            "intake", [dict(r) for r in current], current))

    def test_the_id_keyed_registers_always_hold(self):
        for key in ("risks", "asks"):
            with self.subTest(register=key):
                self.assertTrue(PT.carry_forward_is_addressable(key, [], []))


# ── 7. the store is read honestly ─────────────────────────────────────────


class TestTheStoreIsReadHonestly(Base):

    def test_register_section_shape_reads_every_argument_it_takes(self):
        """`readable_as_register(board, key, section)` never read `section`.

        A parameter nothing reads is a claim about how the function is decided,
        and it was declared in the commit that answered a review finding about
        a name assigned and never read. The heading is a property of the
        register, so it is looked up from the register.
        """
        import inspect
        names = list(inspect.signature(PT.register_section_shape)
                     .parameters)
        self.assertEqual(names, ["board", "key"])
        src = inspect.getsource(PT.register_section_shape)
        for name in names:
            self.assertIn(name, src.split('"""')[-1],
                          f"{name} is declared and never read")


# ── 8. the ordinary write reaches its store at all ────────────────────────


# ── 8b. the real path: a held board's hand edit reaches no store ──────────


# ── 9. the map is complete, both ways ─────────────────────────────────────


class TestTheMapIsComplete(unittest.TestCase):
    """`REGISTER_EVENTS` against the vocabulary the file already declares.

    Keyed on `SECTION_EVENTS` and `TASK_EVENTS` — registers this repository
    already maintains and already tests — rather than on a regex over the
    source. Round 2 found the regex form evadable two ways in five minutes.
    """

    def test_every_register_event_is_an_event_this_tool_writes(self):
        known = set(PT.TASK_EVENTS) | set(PT.SECTION_EVENTS)
        self.assertEqual(set(PT.REGISTER_EVENTS) - known, set())

    def test_every_section_event_declares_the_store_it_touches(self):
        """Every register section has a store since TASK-237 3b, so no member
        of `SECTION_EVENTS` may be absent. `## Cadence` was the one exception,
        and its two events were the whole of it."""
        self.assertEqual(
            set(PT.SECTION_EVENTS) - set(PT.REGISTER_EVENTS), set())

    def test_every_register_names_a_store_this_repository_declares(self):
        for key, value in PT.REGISTER_EVENTS.items():
            with self.subTest(event=key):
                self.assertIn(value, PT.REGISTER_SPEC)

    def test_the_two_task_events_that_touch_intake_are_declared(self):
        """`route` discharges the row it promotes and `add` creates the section
        on a queue-mode track — both are TASK events touching another
        register's section, which is how door 4 was reachable at all."""
        for event in ("route", "add"):
            with self.subTest(event=event):
                self.assertEqual(PT.REGISTER_EVENTS[event], "intake")


class TestRetiredWritersCannotShrinkRegisters(Base):
    def test_every_register_keeps_its_canonical_bytes_after_a_held_row_is_deleted(self):
        for key, (heading, store, *_rest) in REGISTERS.items():
            with self.subTest(register=key):
                f = self.fixture(build_board(), mint=(key,))
                before = {str(p.relative_to(f.root)): p.read_bytes()
                          for p in f.root.rglob("*") if p.is_file()}
                for argv in (("intake", "--title", "a request"),
                             ("ask", "--needed", "Which direction?"),
                             ("risk-add", "--title", "a risk"),
                             ("resolve-intake", "1", "--outcome", "dropped", "--reason", "out of scope"),
                             ("intake-sweep",), ("purge", "TASK-001", "--reason", "out of scope")):
                    rc, out = f.run(*argv)
                    self.assertEqual(rc, 1, out)
                    self.assertIn("read-only", out)
                    self.assertEqual({str(p.relative_to(f.root)): p.read_bytes()
                                      for p in f.root.rglob("*") if p.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
