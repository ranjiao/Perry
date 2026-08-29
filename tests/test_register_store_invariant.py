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

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gate import GATE_OFF          # tests/gate.py — why these fixtures opt out
from test_asks_store import REGISTER as ASK_TABLE
from test_intake_store import REGISTER as INTAKE_TABLE
from test_risks_store import REGISTER as RISK_TABLE
from test_task_writer import PT

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
import perry_store as S  # noqa: E402

TASK = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"
LINT = PERRY_HOME / "bin" / "perry-lint"

#: One queue-mode track. This repository declares one of its own — `.perry/
#: config.md § Tracks` carries `intake | queue | …`, declared 2026-08-20 under
#: TASK-133 — which is why the merge-hold reproduction is reachable on `main`
#: and not only on a synthetic project.
OPS_QUEUE = ("\n## Tracks\n\n"
             "| Track | Mode | Spine | Stages | WIP | SLA | Cycle "
             "| Default rung |\n"
             "|---|---|---|---|---|---|---|---|\n"
             "| ops | queue | OKR.md | new→triaged→resolved | 6 | 5d | 1w "
             "| V2 |\n")

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


class Fixture:
    """A throwaway Perry project with the three register stores minted."""

    def __init__(self, board: str, tracks: str = "", mint=("intake", "asks",
                                                           "risks")):
        self.dir = tempfile.mkdtemp()
        self.root = Path(self.dir)
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n" + GATE_OFF + tracks,
            encoding="utf-8")
        (self.root / "BOARD.md").write_text(board, encoding="utf-8")
        self._tasks("write", "--from-board")
        for name in mint:
            self._tasks(f"{name}-write", "--from-board")

    def _tasks(self, *argv) -> None:
        r = subprocess.run(["python3", str(TASKS), *argv,
                            "--root", str(self.root)],
                           capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(" ".join(argv) + "\n" + r.stdout + r.stderr)

    def run(self, *argv) -> tuple[int, str]:
        r = subprocess.run(["python3", str(TASK), *argv,
                            "--root", str(self.root)],
                           capture_output=True, text=True)
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

    def test_the_queue_track_reaches_cmd_adds_queue_branch(self):
        """`ops` is a queue track HERE, proved by the branch under test.

        `cmd_add`'s `if mode == "queue"` calls `ensure_section("Intake", …)`,
        and nothing else in `add` creates that section. So a board with no
        `## Intake` that grows one on `--track ops` and does not on the default
        project track is this fixture saying which branch it takes — which is
        the whole of door 4.
        """
        f = self.fixture(build_board(intake=None), tracks=OPS_QUEUE, mint=())
        self.assertEqual(f.run("add", "--title", "a project row",
                               "--deliverable", "d", "--verification", "v")[0], 0)
        self.assertNotIn("## Intake", f.board_text())
        self.assertEqual(f.run("add", "--title", "a queue row", "--track", "ops",
                               "--deliverable", "d", "--verification", "v")[0], 0)
        self.assertIn("## Intake", f.board_text())


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
    """

    def setUp(self):
        self.f = self.fixture(build_board(), tracks=OPS_QUEUE)
        self.before = self.f.raw("intake.jsonl")
        board_without_intake(self.f)

    def test_the_reproduction_starts_from_a_store_with_records_to_lose(self):
        """The control. A test that starts from an empty store proves nothing."""
        self.assertEqual(len(self.f.records("intake.jsonl")), 4)
        self.assertNotIn("## Intake", self.f.board_text())

    def test_an_ordinary_add_on_a_queue_track_cannot_empty_a_present_intake_store(self):
        rc, out = self.f.run("add", "--title", "a queue task probe",
                             "--track", "ops", "--deliverable", "d",
                             "--verification", "v")
        self.assertNotEqual(rc, 0, "the write was not refused:\n" + out)
        self.assertEqual(self.f.raw("intake.jsonl"), self.before,
                         "the intake store changed on a refused write")
        self.assertEqual(len(self.f.records("intake.jsonl")), 4)

    def test_the_refusal_names_the_store_and_a_way_forward(self):
        """And the way forward is a subcommand that exists.

        `perry-tasks` prefixes the three registers (`intake-write`) and leaves
        the task store's own subcommands bare (`write`), so a message built by
        pasting the store's name in front of `-write` sends the reader to
        `perry-tasks tasks-write`, which there is no such thing as.
        """
        _rc, out = self.f.run("add", "--title", "a queue task probe",
                              "--track", "ops", "--deliverable", "d",
                              "--verification", "v")
        self.assertIn("intake.jsonl", out)
        self.assertIn("perry-tasks intake-write --from-board", out)
        self.assertIn("perry-tasks intake-render --write", out)
        with self.assertRaises(PT.Refused) as caught:
            PT.refuse_to_shrink("tasks", Path("/nowhere/tasks.jsonl"),
                                "next", 5, 4)
        self.assertIn("perry-tasks write --from-board", str(caught.exception))
        self.assertNotIn("tasks-write", str(caught.exception))

    def test_a_dry_run_previews_the_refusal_rather_than_the_write(self):
        """`--dry-run` reaches the same gate the real write does.

        `commit()` calls `register_change` BEFORE `if dry_run: return plan`,
        deliberately: `cmd_add`'s own docstring says a preview that is not the
        write is worse than no preview, and a dry run that printed a plan for a
        write the tool would refuse is exactly that.
        """
        rc, out = self.f.run("add", "--title", "a queue task probe",
                             "--track", "ops", "--deliverable", "d",
                             "--verification", "v", "--dry-run")
        self.assertNotEqual(rc, 0, "the dry run previewed a refused write:\n"
                                   + out)
        self.assertIn("may never make a canonical store smaller", out)

    def test_a_refused_register_write_writes_nothing_at_all(self):
        """Refused before anything is staged — not half a transaction."""
        board = self.f.board_text()
        tasks = self.f.raw("tasks.jsonl")
        self.f.run("add", "--title", "a queue task probe", "--track", "ops",
                   "--deliverable", "d", "--verification", "v")
        self.assertEqual(self.f.board_text(), board)
        self.assertEqual(self.f.raw("tasks.jsonl"), tasks)


# ── 3. the four doors ─────────────────────────────────────────────────────


class TestTheFourDoors(Base):
    """One invariant, four doors. Each door is named for the round that found
    it, and each is closed by the same line of code."""

    # Door 1 — round 1. The exemption was keyed on the COMMAND NAME, on the
    # reasoning that `intake-sweep` is the only command that removes a row.
    # True, and the wrong question: it is the only command that moves rows
    # ITSELF, not the only way rows move.
    def test_door_one_a_row_tidied_off_the_board_by_hand_refuses_the_next_write(self):
        f = self.fixture(build_board())
        before = f.raw("intake.jsonl")
        rows = INTAKE_TABLE.split("\n")
        shrunk = "\n".join(rows[:2] + rows[3:])        # one row removed by hand
        f.write_board(build_board(intake=shrunk))
        rc, out = f.run("add", "--title", "an unrelated task",
                        "--deliverable", "d", "--verification", "v")
        self.assertNotEqual(rc, 0, out)
        self.assertEqual(f.raw("intake.jsonl"), before)

    # Door 2 — round 2. The exemption was keyed on `(request, arrived)`, which
    # is not unique: the same thing filed twice on the same day is the ordinary
    # reason a row gets `dropped — duplicate`.
    def test_door_two_a_duplicate_request_tidied_out_refuses_rather_than_fabricating(self):
        dup = ("| Arrived | Request | Outcome |\n|---|---|---|\n"
               "| 2026-08-01 | fix the login bug | "
               "dropped 2026-08-01 — folded in |\n"
               "| 2026-08-01 | fix the login bug | — |\n"
               "| 2026-08-02 | something else | — |\n")
        f = self.fixture(build_board(intake=dup))
        self.assertEqual(len(f.records("intake.jsonl")), 3)
        self.assertIs(f.records("intake.jsonl")[0]["discharged"], True)
        rows = dup.split("\n")
        f.write_board(build_board(
            intake="\n".join(rows[:2] + rows[3:])))     # the dropped one goes
        rc, out = f.run("add", "--title", "an ordinary task",
                        "--deliverable", "d", "--verification", "v")
        self.assertNotEqual(rc, 0, out)
        after = f.records("intake.jsonl")
        self.assertEqual(len(after), 3)
        self.assertIs(after[1]["discharged"], False,
                      "a live request was recorded as discharged")

    # Door 3 — round 2 and round 3. `<register>_records` returns `[]` for every
    # shape but `table`, and round 2 measured a store going to zero through
    # `prose` and through both `foreign` shapes. The invariant does not
    # enumerate shapes: `[] < n` is the refusal.
    def test_door_three_no_section_shape_on_any_register_may_empty_a_present_store(self):
        for key in REGISTERS:
            for shape in SHAPES[key]:
                if shape == "table":
                    continue
                with self.subTest(register=key, shape=shape):
                    # Minted from the healthy board, then the shape is broken
                    # on disk — exactly the order a human editing a board
                    # produces, and the only order in which the store has
                    # records to lose.
                    f = self.fixture(build_board(), mint=(key,))
                    store = REGISTERS[key][1]
                    before = f.raw(store)
                    self.assertTrue(f.records(store),
                                    "control: the store starts with records")
                    f.write_board(build_board(**{key: SHAPES[key][shape]}))
                    rc, out = f.run(*OWN_WRITE[key])
                    self.assertNotEqual(rc, 0, out)
                    self.assertEqual(f.raw(store), before,
                                     f"{store} changed on a {shape} section")

    def test_door_three_the_foreign_shape_is_refused_on_every_register(self):
        """The shape round 3 had no test for, on all three registers.

        Split out of the matrix above and stated on its own, because a cell
        inside a loop is exactly how it went missing.
        """
        for key in REGISTERS:
            for shape in ("foreign-two-tables", "foreign-renamed-key"):
                with self.subTest(register=key, shape=shape):
                    f = self.fixture(build_board(), mint=(key,))
                    store = REGISTERS[key][1]
                    before = f.raw(store)
                    f.write_board(build_board(**{key: SHAPES[key][shape]}))
                    board, ops = parse(f.board_text())
                    self.assertEqual(REGISTERS[key][2](board, ops)[0], "foreign",
                                     "control: the section really is foreign")
                    rc, out = f.run(*OWN_WRITE[key])
                    self.assertNotEqual(rc, 0, out)
                    self.assertEqual(f.raw(store), before)

    # Door 4 — round 3. `ensure_section` runs before `commit()` reads anything,
    # so the gate saw a freshly created, readable, EMPTY table. The invariant is
    # not a gate on the board and does not care when it is read.
    def test_door_four_a_register_command_may_not_rebuild_its_section_from_one_row(self):
        """Round 3's table: intake 3→1, ask 3→1, risk-add 3→1, all rc 0."""
        for key in REGISTERS:
            with self.subTest(register=key):
                f = self.fixture(build_board(), mint=(key,))
                store = REGISTERS[key][1]
                before = f.raw(store)
                f.write_board(build_board(**{key: None}))
                rc, out = f.run(*OWN_WRITE[key])
                self.assertNotEqual(rc, 0, out)
                self.assertEqual(f.raw(store), before,
                                 f"{store} was rebuilt from one row")


# ── 4. the three commands that may still shrink ───────────────────────────


class TestExplicitRemovalStillWorks(Base):
    """An invariant that also blocks the sweep has broken the register."""

    def test_intake_sweep_may_shrink_the_intake_store(self):
        f = self.fixture(build_board())
        self.assertEqual(len(f.records("intake.jsonl")), 4)
        rc, out = f.run("intake-sweep")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(f.records("intake.jsonl")), 3,
                         "the sweep did not reduce the store")

    def test_purge_may_shrink_the_task_store(self):
        """`tasks.jsonl` is canonical too, and `purge` is its one removal path.

        The row is closed through the tool rather than written closed into the
        fixture: `cmd_purge` refuses a record the projection still carries a
        line for, so a board-written `done` row is refused for a reason that
        has nothing to do with this invariant.
        """
        rows = ("| TASK-001 | a smoke test row | Coding Agent | not_started "
                "| — | — |\n")
        f = self.fixture(build_board(rows=rows))
        self.assertEqual(len(f.records("tasks.jsonl")), 1)
        self.assertEqual(f.run("drop", "TASK-001", "--reason", "never real")[0], 0)
        rc, out = f.run("purge", "TASK-001", "--reason", "a smoke test row")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(f.records("tasks.jsonl")), 0)

    def test_resolve_intake_is_not_blocked_and_does_not_in_fact_shrink(self):
        """Named by USER-906 as an explicit removal. It is not one.

        `cmd_resolve_intake` rewrites the row's `Outcome` cell; the row stays
        on the board and the record count does not move.

        **This test runs on a CLEAN board and therefore says nothing about the
        exemption.** The V4 round-4 review named it precisely: offered as the
        record that "the allowance is unused", it is the one test that cannot
        tell, because no shrink is possible here and `rc == 0` is true whether
        the allowance exists or not. What it does say is that the invariant
        does not block the ordinary discharge, which is worth a test of its
        own. The bound is `TestTheExemptionIsBounded`, one class down, and
        every test there runs on a board where a shrink IS possible.
        """
        f = self.fixture(build_board())
        rc, out = f.run("resolve-intake", "2", "--reason", "not for us")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(f.records("intake.jsonl")), 4)
        self.assertIs(f.records("intake.jsonl")[1]["discharged"], True)


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
        """
        f = self.fixture(build_board(intake=table))
        self.assertEqual(len(f.records("intake.jsonl")), 4,
                         "control: the store is minted from the whole table")
        tidy_intake_rows_off_the_board(f, keep)
        board = PT.Board(f.root / "BOARD.md")
        self.assertEqual(len(board.section_rows("Intake")), len(keep),
                         "control: the board was tidied to the kept rows")
        self.assertEqual(len(f.records("intake.jsonl")), 4,
                         "control: the STORE still holds every record, so a "
                         "derivation from this board shrinks it — a shrink is "
                         "possible here, which is the point")
        return f

    def test_resolve_intake_may_not_shrink_a_store_it_removes_nothing_from(self):
        """The V4 round-4 review's § 1, as a test. Two records at stake.

        `resolve-intake` rewrites one `Outcome` cell and removes no record, so
        it declares 0 and may shrink by 0. The two records tidied off the board
        by hand are records this command never addressed.
        """
        f = self.drifted([1, 2])
        before = f.raw("intake.jsonl")
        rc, out = f.run("resolve-intake", "1", "--outcome", "dropped",
                        "--reason", "not for us")
        self.assertNotEqual(
            rc, 0, "resolve-intake destroyed records it never touched:\n" + out)
        self.assertEqual(f.raw("intake.jsonl"), before,
                         "the store changed on a refused write")
        self.assertEqual(len(f.records("intake.jsonl")), 4)
        self.assertIn("removes 0 record(s)", out)
        self.assertIn("by exactly what it removes", out)

    def test_intake_sweep_may_not_shrink_by_more_than_the_rows_it_swept(self):
        """It swept one row; three records were about to go.

        The row kept at position 3 is the discharged one, so the sweep is
        legitimate and removes exactly one board row. The other two records are
        not its to remove.
        """
        f = self.drifted([1, 3])
        before = f.raw("intake.jsonl")
        rc, out = f.run("intake-sweep")
        self.assertNotEqual(
            rc, 0, "the sweep removed more than it swept:\n" + out)
        self.assertEqual(f.raw("intake.jsonl"), before,
                         "the store changed on a refused write")
        self.assertEqual(len(f.records("intake.jsonl")), 4)
        self.assertIn("removes 1 record(s)", out)

    def test_intake_sweep_may_shrink_by_exactly_the_rows_it_swept(self):
        """Two discharged rows, one sweep, two records — and it goes through.

        The bound is the sweep's OWN count, not a literal. A board with two
        discharged rows is refused by a bound written as `1` and permitted by
        the count `cmd_intake_sweep` already carries in its event.
        """
        f = self.fixture(build_board(intake=INTAKE_TWO_DISCHARGED))
        self.assertEqual(len(f.records("intake.jsonl")), 4,
                         "control: four records to start")
        rc, out = f.run("intake-sweep")
        self.assertEqual(rc, 0, out)
        self.assertIn("wrote 2 row(s) (intake-sweep)", out,
                      "control: the sweep declared two rows")
        self.assertEqual(len(f.records("intake.jsonl")), 2,
                         "the sweep did not remove both discharged rows")

    def test_purge_removes_the_one_record_it_names_and_leaves_the_other(self):
        """A store with two records, so the removal is bounded by something.

        Round 4's purge test ran 1 record to 0, where "removed exactly one" and
        "removed everything" are the same number.
        """
        rows = ("| TASK-001 | a smoke test row | Coding Agent | not_started "
                "| — | — |\n"
                "| TASK-002 | a row that stays | Coding Agent | not_started "
                "| — | — |\n")
        f = self.fixture(build_board(rows=rows))
        self.assertEqual([r["id"] for r in f.records("tasks.jsonl")],
                         ["TASK-001", "TASK-002"], "control")
        self.assertEqual(f.run("drop", "TASK-001", "--reason", "never real")[0],
                         0)
        rc, out = f.run("purge", "TASK-001", "--reason", "a smoke test row")
        self.assertEqual(rc, 0, out)
        self.assertEqual([r["id"] for r in f.records("tasks.jsonl")],
                         ["TASK-002"],
                         "purge did not remove exactly the record it named")

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
    """`refuse_to_shrink` as a unit — the one place the rule is written."""

    def call(self, event: str, before: int, after: int):
        PT.refuse_to_shrink("intake", Path("/nowhere/intake.jsonl"),
                            event, before, after)

    def test_an_ordinary_event_may_not_reduce_a_record_count(self):
        with self.assertRaises(PT.Refused):
            self.call("add", 3, 2)

    def test_growing_and_holding_steady_are_both_fine(self):
        self.call("add", 3, 3)
        self.call("add", 3, 9)
        self.call("add", 0, 0)

    def test_each_of_the_three_named_commands_may_shrink(self):
        for event in ("purge", "resolve-intake", "intake-sweep"):
            with self.subTest(event=event):
                self.call(event, 3, 0)

    def test_the_allowlist_is_exactly_the_three_commands_user_906_named(self):
        self.assertEqual(set(PT.SHRINK_ALLOWED),
                         {"purge", "resolve-intake", "intake-sweep"})

    def test_the_task_store_is_under_the_same_rule_as_the_registers(self):
        """One function, called at every canonical store, not one per store."""
        with self.assertRaises(PT.Refused):
            PT.refuse_to_shrink("tasks", Path("/nowhere/tasks.jsonl"),
                                "next", 5, 4)
        PT.refuse_to_shrink("tasks", Path("/nowhere/tasks.jsonl"),
                            "purge", 5, 4)


class TestTheTaskStoreCallSiteIsWired(Base):
    """**A guard that survives its own deletion does not count.**

    The rule above is a unit test of the FUNCTION. It says nothing about
    whether `commit()` actually calls it for `tasks.jsonl`, and deleting those
    two lines reddened nothing at all in the first mutation round — which is
    the shape TASK-095 shipped and was failed for.

    The reason it is hard to reach is real and is stated in the RESULT rather
    than worked around: `commit()` builds `records` FROM `current` by removing
    at most one record and appending at most one, so the only branch that
    shortens the task store is `purge`, and `purge` is in `SHRINK_ALLOWED`. The
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

    def test_a_row_replaced_by_hand_does_not_hand_its_discharge_to_the_newcomer(self):
        """The case the invariant cannot see: the count does not move.

        Delete a discharged request by hand and append a new one. `intake.jsonl`
        is keyed on `order`, so a positional merge would hand `discharged: True`
        at position n to a request that is still waiting, with its `Outcome`
        cell still reading `—` and `perry-lint` saying `drifted: 0` because
        `discharged` has no board column to compare against.
        """
        table = ("| Arrived | Request | Outcome |\n|---|---|---|\n"
                 "| 2026-08-01 | the dropped one | dropped 2026-08-02 — no |\n"
                 "| 2026-08-03 | still waiting | — |\n")
        f = self.fixture(build_board(intake=table))
        self.assertIs(f.records("intake.jsonl")[0]["discharged"], True)
        rows = table.split("\n")
        replaced = "\n".join(rows[:2] + rows[3:-1] +
                             ["| 2026-08-05 | a brand new request | — |", ""])
        f.write_board(build_board(intake=replaced))
        rc, out = f.run("add", "--title", "an ordinary task",
                        "--deliverable", "d", "--verification", "v")
        self.assertEqual(rc, 0, out)
        after = f.records("intake.jsonl")
        self.assertEqual(len(after), 2)
        self.assertIs(after[0]["discharged"], False,
                      "a still-waiting request inherited a discharge")


# ── 7. the store is read honestly ─────────────────────────────────────────


class TestTheStoreIsReadHonestly(Base):
    def test_a_corrupt_line_in_a_register_store_is_a_refusal_not_a_traceback(self):
        f = self.fixture(build_board())
        p = f.root / "intake.jsonl"
        p.write_text(p.read_text() + "{not json\n", encoding="utf-8")
        rc, out = f.run("intake", "--title", "another request")
        self.assertNotEqual(rc, 0)
        self.assertNotIn("Traceback", out)
        self.assertIn("intake.jsonl", out)
        self.assertIn("line 5", out)

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


class TestTheOrdinaryWriteReachesItsStore(Base):
    """The row's original deliverable, which the invariant must not undo."""

    def test_intake_on_a_project_with_no_store_creates_it_and_holds_the_row(self):
        f = self.fixture(build_board(), mint=())
        self.assertFalse((f.root / "intake.jsonl").exists())
        rc, out = f.run("intake", "--title", "a brand new request")
        self.assertEqual(rc, 0, out)
        got = f.records("intake.jsonl")
        self.assertEqual(len(got), 5)
        self.assertEqual(got[-1]["request"], "a brand new request")

    def test_ask_and_risk_add_reach_their_stores_too(self):
        f = self.fixture(build_board(), mint=())
        self.assertEqual(f.run("ask", "--needed", "a question")[0], 0)
        self.assertEqual(len(f.records("asks.jsonl")), 5)
        self.assertEqual(f.run("risk-add", "--title", "a risk")[0], 0)
        self.assertEqual(len(f.records("risks.jsonl")), 4)

    def test_the_lint_prints_a_drift_verdict_rather_than_unchecked(self):
        f = self.fixture(build_board(), mint=())
        f.run("intake", "--title", "a brand new request")
        r = subprocess.run(["python3", str(LINT), "--root", str(f.root)],
                           capture_output=True, text=True)
        self.assertNotIn("no `intake.jsonl`", r.stdout)
        self.assertIn("intake store: 5 record(s)", r.stdout)

    def test_intake_diff_byte_compares_clean_right_after_an_ordinary_write(self):
        f = self.fixture(build_board(), mint=())
        f.run("intake", "--title", "a brand new request")
        r = subprocess.run(["python3", str(TASKS), "intake-diff",
                            "--root", str(f.root)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_success_line_names_the_register_store_only_when_one_is_written(self):
        f = self.fixture(build_board())
        _rc, out = f.run("intake", "--title", "a request")
        self.assertIn("intake.jsonl", out)
        f2 = self.fixture(build_board(intake=None, asks=None, risks=None),
                          mint=())
        _rc, out = f2.run("add", "--title", "a plain task",
                          "--deliverable", "d", "--verification", "v")
        self.assertIn("tasks.jsonl", out)
        self.assertNotIn("intake.jsonl", out)


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

    def test_every_section_event_but_cadence_declares_the_store_it_touches(self):
        """`## Cadence` is the one register section with no store, so its two
        events are the only members of `SECTION_EVENTS` that may be absent."""
        self.assertEqual(
            set(PT.SECTION_EVENTS) - set(PT.REGISTER_EVENTS),
            {"cadence-add", "cadence-done"})

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


if __name__ == "__main__":
    unittest.main()
