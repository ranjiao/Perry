"""**A count-preserving substitution destroys canonical records.** TASK-243.

`refuse_to_shrink` is a COUNT rule and USER-906 chose it as one. 32 records to
32 records is not fewer, so the invariant is silent, and it is right to be:
this module adds no predicate to it and asserts, behaviourally, that none was
added (`TestTheInvariantIsStillACountRule`).

The question here is IDENTITY. Swap N rows of a register on the board by hand
— same count, different rows — and any register-touching command persists the
swap. Measured 2026-08-30 on this repository's own state:

    intake  · resolve-intake   10 lost, 10 gained, rc 0, 10 drifted → 0 drifted
    intake  · intake           10 lost, 11 gained, rc 0, 10 drifted → 0 drifted
    asks    · ask               3 lost,  4 gained, rc 0,  6 drifted → 0 drifted
    risks   · risk-add          2 lost,  3 gained, rc 0,  4 drifted → 0 drifted
    zh      · ask          USER-014 lost,          rc 0,  2 drifted → 0 drifted

**The ending this row chose is REPORT, not refuse**, and the choice is forced
rather than conventional. On `## Intake` a record's identity IS its text, so
fixing a typo in a Request cell and swapping a row out from under a stored
record are the same edit at the set level. A refusal would hard-block the typo
fix and name `perry-tasks intake-write --from-board` as the remedy for it,
which is TASK-095 round 5's defect exactly. A tool that cannot tell the two
apart must say what it sees.

**The property, and it is falsifiable on its own:** no canonical record leaves
a register store unreported. Before this change the operator's sequence was
`10 drifted → (silence) → 0 drifted`; the silence is the defect, and every test
in § 2 asserts against the number the write itself prints.

**Every board in this module is one where a substitution IS possible, and the
precondition is asserted as a control BEFORE any behaviour.** TASK-203 round 4
shipped a test on a clean board where no shrink was possible — the one test
that could not tell — and its round 5 had to add an `assertLess` before its own
control could fail. `stage_substitution` returns a `Staged` whose four control
assertions run first, in `check()`, and one of them is `assertGreater`.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from test_register_store_invariant import (
    ASK_TABLE, Base, INTAKE_TABLE, LINT, PT, REGISTERS, RISK_TABLE,
    TASKS, build_board, parse)

PERRY_HOME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PERRY_HOME / "bin"))
import perry_store as S  # noqa: E402

#: The whole table for each register, so a substitution can be built by
#: replacing rows of it. Quantified over `REGISTERS` everywhere below, so a
#: fourth register cannot be added without this module noticing.
TABLE = {"intake": INTAKE_TABLE, "asks": ASK_TABLE, "risks": RISK_TABLE}

#: A replacement row per register, `j` making it distinct. Shape-identical to
#: the row it replaces — a filler that broke the table would be refused by the
#: shape check for a reason that has nothing to do with this row, and the test
#: would pass for the wrong reason.
FILLER = {
    "intake": lambda j: f"| 2026-08-30 | a request typed in by hand {j} | — |",
    "asks": lambda j: (f"| USER-90{j} | a question typed in by hand {j} "
                       f"| — | — | pending |  |"),
    "risks": lambda j: f"| RX-90{j} | a risk typed in by hand {j} |  | open |",
}

#: What each register's records are matched on. **Read from the shipped map**,
#: not restated: a test that spelled the identity itself would go green if the
#: shipped one changed underneath it, which is the whole failure mode this
#: module is about.
IDENT = PT.REGISTER_IDENTITY


#: A register's derivation, by key. Read from `perry_store` rather than through
#: `perry-task`, so the control can say what the BOARD holds without going
#: through the write that is under test.
DERIVE = {"intake": S.intake_records, "asks": S.ask_records,
          "risks": S.risk_records}


def replace_rows(board_text: str, heading: str, n: int, filler) -> str:
    """The board with the FIRST `n` data rows of `## heading` replaced.

    **Edited on the board AS IT STANDS, not rebuilt from the pristine table.**
    A version of this that rebuilt from the fixture constant silently undid
    whatever the test had already done — a discharged row, an earlier write —
    and one test then swept a board with nothing on it to sweep, which is a
    fixture answering a question nobody asked.

    In place at the head rather than truncated at the tail, so a row a test
    discharged earlier survives the substitution and the sweep still has work.
    """
    lines = board_text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == f"## {heading}")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("## ")), len(lines))
    body = [i for i in range(start, end) if lines[i].startswith("| ")]
    data = [i for i in body if set(lines[i].replace("|", "").replace(" ", ""))
            - set("-")][1:]
    assert len(data) > n, (heading, len(data), n)
    for j, i in enumerate(data[:n]):
        lines[i] = filler(j)
    return "\n".join(lines)


class Staged:
    """A board with N rows of one register replaced by N others.

    The count is preserved on purpose. `refuse_to_shrink` is asked and answers
    "not fewer", which is correct, and the write proceeds — so everything below
    is about what the write SAYS, never about whether it happened.
    """

    def __init__(self, fixture, key: str, n: int):
        self.f, self.key, self.n = fixture, key, n
        self.store = REGISTERS[key][1]
        self.before = fixture.records(self.store)
        fixture.write_board(replace_rows(
            fixture.board_text(), REGISTERS[key][0], n, FILLER[key]))
        board, ops = parse(fixture.board_text())
        self.derived = DERIVE[key](board, ops)

    def check(self, case: unittest.TestCase) -> "Staged":
        """The four controls. Called before any behaviour is asserted."""
        ident = IDENT[self.key]
        was = [ident(r) for r in self.before]
        now = [ident(r) for r in self.derived]
        case.assertGreater(
            len(self.before), 0, "control: the store starts with records")
        case.assertEqual(
            len(self.derived), len(self.before),
            "control: the substitution must PRESERVE the count, or this is a "
            "shrink and `refuse_to_shrink` — not this row — is what answers")
        case.assertEqual(
            len(set(was) - set(now)), self.n,
            f"control: {self.n} record identities must be about to be lost")
        # The invariant, asked directly about these two numbers. It must be
        # SILENT — this board is outside its bound, which is why the row exists.
        PT.refuse_to_shrink(self.key, Path("/nowhere/" + self.store),
                            {"event": "intake"},
                            len(self.before), len(self.derived))
        return self

    def lost(self) -> list:
        """Identities in the store before the write and not in it after."""
        ident = IDENT[self.key]
        after = {ident(r) for r in self.f.records(self.store)}
        return [ident(r) for r in self.before if ident(r) not in after]


def stage(case, key: str, n: int = 2, **kw) -> tuple:
    """A minted fixture plus a checked `Staged` substitution on `key`."""
    f = case.fixture(build_board(), mint=(key,), **kw)
    return f, Staged(f, key, n).check(case)


def reported(out: str) -> int:
    """How many canonical records the command's own output says it destroyed.

    Parsed out of the message rather than read from a payload, because the
    message is the surface a person reads and it is the surface this row says
    must not be silent.
    """
    for line in out.split("\n"):
        if "canonical" in line and "record(s)" in line:
            return int(line.split("canonical")[0].split("⚠")[1].strip())
    return 0


def lint_drift(root: Path, key: str) -> int:
    """`perry-lint`'s drifted count for one register, from the census line."""
    label = {"intake": "intake store:", "asks": "ask store:",
             "risks": "risks store:"}[key]
    r = subprocess.run(["python3", str(LINT), "--root", str(root)],
                       capture_output=True, text=True)
    for line in r.stdout.split("\n"):
        if label in line:
            return int(line.split("record(s),")[1].strip().split(" ")[0])
    raise AssertionError(f"no `{label}` census line:\n{r.stdout}")


# ── 1. the controls, stated on their own ──────────────────────────────────


class TestTheStagedBoardIsASubstitutionAndNotAShrink(Base):
    """Controls. Every assertion in this module rests on these.

    Round 4 of this row's parent shipped its bound test on a CLEAN board, where
    no shrink was possible and `rc == 0` was true with the guard reverted or
    not. A control that cannot fail is the same mistake one level up, so each
    of these is asserted here as a fact about the fixture, separately from any
    test that uses it.
    """

    def test_every_register_can_stage_a_substitution_at_equal_count(self):
        for key in REGISTERS:
            with self.subTest(register=key):
                _f, staged = stage(self, key)
                self.assertEqual(len(staged.derived), len(staged.before))
                self.assertEqual(len(staged.before), staged.n + len(
                    [r for r in staged.before
                     if IDENT[key](r) in {IDENT[key](d)
                                          for d in staged.derived}]))

    def test_the_control_itself_can_fail_when_no_substitution_is_staged(self):
        """The control's control. `check()` must be red on a clean board.

        Round 5 of TASK-203 had to add an `assertLess` before its own control
        could fail; this asserts the equivalent here rather than claiming it.
        """
        f = self.fixture(build_board(), mint=("intake",))
        staged = Staged.__new__(Staged)
        staged.f, staged.key, staged.n = f, "intake", 2
        staged.store = REGISTERS["intake"][1]
        staged.before = f.records("intake.jsonl")
        board, ops = parse(f.board_text())
        staged.derived = S.intake_records(board, ops)   # board untouched
        with self.assertRaises(AssertionError) as caught:
            staged.check(self)
        self.assertIn("record identities must be about to be lost",
                      str(caught.exception))

    def test_the_staged_board_is_still_a_readable_table_on_every_register(self):
        """A filler that broke the shape would be refused for another reason."""
        for key in REGISTERS:
            with self.subTest(register=key):
                f, _staged = stage(self, key)
                board, ops = parse(f.board_text())
                self.assertEqual(REGISTERS[key][2](board, ops)[0], "table")


# ── 2. the reproduction, and the property ─────────────────────────────────


#: Register → a register-touching command that removes nothing. `resolve-intake`
#: is listed separately below because it is the one the row names: it DECLARES
#: 0 removals, so it sits inside `refuse_to_shrink`'s bound and was the
#: reviewer's reproduction.
ORDINARY = {
    "intake": ("intake", "--title", "an ordinary new request"),
    "asks": ("ask", "--needed", "an ordinary new question"),
    "risks": ("risk-add", "--title", "an ordinary new risk"),
}


class TestTheSubstitutionIsReportedOnEveryRegister(Base):
    """The measured reproduction, on all three registers."""

    def test_an_ordinary_write_names_every_record_it_destroys(self):
        for key in REGISTERS:
            with self.subTest(register=key):
                f, staged = stage(self, key)
                rc, out = f.run(*ORDINARY[key])
                self.assertEqual(rc, 0, "reported, not refused:\n" + out)
                self.assertEqual(len(staged.lost()), staged.n,
                                 "the substitution did not land")
                self.assertEqual(reported(out), staged.n,
                                 "the write did not name what it destroyed:\n"
                                 + out)

    def test_the_report_names_the_lost_records_themselves(self):
        for key in REGISTERS:
            with self.subTest(register=key):
                f, staged = stage(self, key)
                _rc, out = f.run(*ORDINARY[key])
                for ident in staged.lost():
                    self.assertIn(str(ident), out,
                                  f"{ident!r} was destroyed and not named")

    def test_the_report_names_the_register_and_the_way_back(self):
        for key in REGISTERS:
            with self.subTest(register=key):
                f, _staged = stage(self, key)
                _rc, out = f.run(*ORDINARY[key])
                self.assertIn(f"## {REGISTERS[key][0]}", out)
                self.assertIn(f"perry-tasks {key}-write --from-board", out)
                self.assertIn(".perry/events.jsonl", out)

    def test_the_drift_report_may_not_fall_to_zero_unaccompanied(self):
        """**The property.** The drift count goes to 0 as records are destroyed.

        That fall is honest — after the write the board and the store really do
        agree — and it is exactly what made the loss silent. What must not
        happen is the fall being unaccompanied, so the number the write prints
        is asserted against the number of records actually lost, with the drift
        before and after asserted around it as controls.
        """
        for key in REGISTERS:
            with self.subTest(register=key):
                f, staged = stage(self, key)
                before = lint_drift(f.root, key)
                self.assertGreater(
                    before, 0, "control: lint must SEE the substitution before "
                               "the write, or there is no fall to accompany")
                rc, out = f.run(*ORDINARY[key])
                self.assertEqual(rc, 0, out)
                self.assertEqual(lint_drift(f.root, key), 0,
                                 "control: the write launders the drift")
                self.assertEqual(
                    len(staged.lost()), staged.n,
                    "control: canonical records really were destroyed")
                self.assertEqual(reported(out), staged.n,
                                 f"{before} row(s) drifted fell to 0 and the "
                                 f"write named {reported(out)} of "
                                 f"{staged.n} destroyed record(s):\n" + out)


class TestResolveIntakeIsInsideItsBoundAndStillReports(Base):
    """The row's own reproduction: the command that declares 0 removals.

    `resolve-intake` rewrites an `Outcome` cell and removes nothing, so
    `declared_removal` answers 0 and `refuse_to_shrink` permits it — correctly,
    on a count that did not move. It is the command the V4 reviewer used to
    destroy ten records at rc 0.
    """

    def test_resolve_intake_declares_zero_and_the_invariant_permits_it(self):
        self.assertEqual(PT.declared_removal({"event": "resolve-intake"}), 0)
        PT.refuse_to_shrink("intake", Path("/nowhere/intake.jsonl"),
                            {"event": "resolve-intake"}, 32, 32)

    def test_resolve_intake_reports_the_records_the_swap_destroyed(self):
        f, staged = stage(self, "intake", n=2)
        rc, out = f.run("resolve-intake", "1", "--outcome", "dropped",
                        "--reason", "not for us")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(staged.lost()), 2)
        self.assertEqual(reported(out), 2, out)


class TestTheLocalizedBoardReportsTheSameWay(Base):
    """The `zh` register, where the reviewer reproduced it on `asks.jsonl`.

    The heading is `## 用户输入队列` and the store is the same file. A report
    that resolved its heading from an English literal would be silent here.
    """

    ZH_ASKS = (
        "| 用户输入编号 | 需要用户提供 | 阻塞 | 闲置 | 状态 |\n"
        "|---|---|---|---|---|\n"
        "| USER-014 | 确认预发布环境的默认值 | REL-002 | 6d | open |\n"
        "| USER-015 | 确认灰度比例 | REL-003 | 2d | open |\n")

    def board(self, asks: str) -> str:
        return ("# 看板 — 替换\n\n## 用户输入队列\n\n" + asks
                + "\n## P0（本周期必须完成）\n\n"
                  "| 编号 | 标题 | 负责人 | 状态 | 下一步 | 证据 |\n"
                  "|---|---|---|---|---|---|\n")

    def test_a_substitution_on_the_localized_queue_is_reported(self):
        f = self.fixture(self.board(self.ZH_ASKS), mint=("asks",))
        before = {r["id"] for r in f.records("asks.jsonl")}
        self.assertEqual(before, {"USER-014", "USER-015"},
                         "control: the localized heading minted a store")
        f.write_board(self.board(self.ZH_ASKS.replace(
            "| USER-014 | 确认预发布环境的默认值 | REL-002 | 6d | open |\n",
            "| USER-016 | 手改替换进来的一行 | REL-009 | 1d | open |\n")))
        board, ops = parse(f.board_text())
        self.assertEqual(len(S.ask_records(board, ops)), 2,
                         "control: the count is preserved")
        rc, out = f.run("ask", "--needed", "一条普通的新提问")
        self.assertEqual(rc, 0, out)
        after = {r["id"] for r in f.records("asks.jsonl")}
        self.assertNotIn("USER-014", after,
                         "control: the canonical record was destroyed")
        self.assertEqual(reported(out), 1, out)
        self.assertIn("USER-014", out)


# ── 3. the report does not cry wolf ───────────────────────────────────────


class TestTheReportIsSilentWhenNothingWasDestroyed(Base):
    """A report that fires on the ordinary case is a report piped to /dev/null."""

    def test_no_ordinary_command_on_an_in_sync_board_reports_anything(self):
        f = self.fixture(build_board())
        for argv in (("resolve-intake", "2", "--outcome", "dropped",
                      "--reason", "no"),
                     ("intake", "--title", "an ordinary new request"),
                     ("ask", "--needed", "an ordinary new question"),
                     ("risk-add", "--title", "an ordinary new risk"),
                     ("risk-clear", "RX-001", "--reason", "done"),
                     ("answer", "USER-002", "--answer", "csv")):
            with self.subTest(command=argv[0]):
                rc, out = f.run(*argv)
                self.assertEqual(rc, 0, out)
                self.assertEqual(reported(out), 0, out)

    def test_an_intake_sweep_removes_records_and_is_not_a_finding(self):
        """The declaration is subtracted, and the control proves it was needed.

        The swept row leaves the store by identity like any other loss, so this
        would fire on every ordinary sweep if `declared_removal` were not
        subtracted. The control asserts `substituted_away` really does return
        it — without that, the test would be green because nothing was lost,
        which is the wrong reason and is indistinguishable from the right one.
        """
        f = self.fixture(build_board())
        before = f.records("intake.jsonl")
        rc, out = f.run("intake-sweep")
        self.assertEqual(rc, 0, out)
        after = f.records("intake.jsonl")
        self.assertLess(len(after), len(before),
                        "control: the sweep really removed a record")
        self.assertEqual(
            len(PT.substituted_away("intake", before, after)), 1,
            "control: the swept row IS lost by identity, so this test is "
            "about the declaration and not about an empty list")
        self.assertEqual(reported(out), 0, "an ordinary sweep cried wolf:\n"
                         + out)

    def test_a_sweep_over_a_substitution_reports_only_the_excess(self):
        """One legitimately swept row and two swapped ones: two unaccounted."""
        f = self.fixture(build_board())
        staged = Staged(f, "intake", 2).check(self)
        rc, out = f.run("intake-sweep")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(staged.lost()), 3,
                         "control: two swapped and one swept")
        self.assertIn("declares it removes 1 record(s)", out)
        self.assertIn("2 of them are unaccounted for", out)


# ── 4. the identity is a multiset ─────────────────────────────────────────


class TestTheIdentityIsAMultiset(Base):
    """`(request, arrived)` is not unique and the report must survive that.

    Round 2 of this row's parent keyed an exemption on this tuple and the tuple
    was not unique, which is why `carry_forward_is_addressable` refuses to join
    through a repeat. Under SET subtraction two stored copies would be answered
    by one derived copy and deleting one of a pair by hand would report
    nothing — the exact silence this row is about, one level down.
    """

    DUP = ("| Arrived | Request | Outcome |\n|---|---|---|\n"
           "| 2026-08-01 | fix the login bug | — |\n"
           "| 2026-08-01 | fix the login bug | — |\n"
           "| 2026-08-02 | something else | — |\n")

    def test_one_of_a_duplicated_pair_deleted_by_hand_is_reported(self):
        f = self.fixture(build_board(intake=self.DUP), mint=("intake",))
        before = f.records("intake.jsonl")
        ident = IDENT["intake"]
        self.assertEqual(len(before), 3, "control: three records")
        self.assertEqual(
            len({ident(r) for r in before}), 2,
            "control: the identity really does repeat, so a SET is short one")
        f.write_board(replace_rows(f.board_text(), "Intake", 1,
                                   FILLER["intake"]))
        board, ops = parse(f.board_text())
        self.assertEqual(len(S.intake_records(board, ops)), 3,
                         "control: the count is preserved")
        rc, out = f.run("resolve-intake", "1", "--outcome", "dropped",
                        "--reason", "no")
        self.assertEqual(rc, 0, out)
        self.assertEqual(reported(out), 1,
                         "a set-subtraction answer is 0 here:\n" + out)

    def test_substituted_away_matches_copy_for_copy(self):
        """Stated directly on the function, on numbers a set cannot tell apart."""
        two = [{"request": "a", "arrived": "d"}, {"request": "a", "arrived": "d"}]
        one = [{"request": "a", "arrived": "d"}]
        self.assertEqual(len(PT.substituted_away("intake", two, one)), 1)
        self.assertEqual(len(PT.substituted_away("intake", two, two)), 0)
        self.assertEqual(len(PT.substituted_away("intake", one, two)), 0)


# ── 5. there is a way back, not only a warning ────────────────────────────


class TestTheLostRecordsAreRecoverable(Base):
    """A warning nobody can act on is a warning that documents a data loss."""

    def test_the_event_carries_the_whole_lost_record(self):
        f, staged = stage(self, "intake", n=2)
        rc, out = f.run("intake", "--title", "an ordinary new request")
        self.assertEqual(rc, 0, out)
        events = [json.loads(l) for l in
                  (f.root / ".perry" / "events.jsonl").read_text().split("\n")
                  if l.strip()]
        lost = events[-1].get("substituted")
        self.assertEqual(len(lost or []), 2, events[-1])
        self.assertEqual({IDENT["intake"](r) for r in lost},
                         set(staged.lost()))
        # Whole records, not identities: the point of the field is that the
        # store can be rebuilt from it.
        self.assertIn("order", lost[0])

    def test_a_clean_write_leaves_no_substituted_field_on_its_event(self):
        """Control for the test above — the field means one thing.

        `intake-sweep` also fails to carry its rows forward and is accounted
        for by the command itself, so it must not land under the same key.
        """
        f = self.fixture(build_board())
        for argv in (("intake", "--title", "an ordinary new request"),
                     ("intake-sweep",)):
            with self.subTest(command=argv[0]):
                self.assertEqual(f.run(*argv)[0], 0)
                events = [json.loads(l) for l in
                          (f.root / ".perry" / "events.jsonl"
                           ).read_text().split("\n") if l.strip()]
                self.assertNotIn("substituted", events[-1])

    def test_the_json_payload_carries_the_report_for_a_caller_with_no_stream(self):
        f, staged = stage(self, "asks", n=2)
        r = subprocess.run(
            ["python3", str(PERRY_HOME / "bin" / "perry-task"), "ask",
             "--needed", "an ordinary new question", "--json",
             "--root", str(f.root)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        payload = json.loads(r.stdout)["register_store"]
        self.assertEqual(len(payload["substituted"]), staged.n)

    def test_the_named_way_back_is_a_subcommand_that_exists(self):
        """`perry-tasks intake-write --from-board`, run for real.

        The refusal one function over used to name `perry-tasks tasks-write`,
        which there is no such thing as; a report that names a command nobody
        can run is the same defect with a friendlier tone.
        """
        for key in REGISTERS:
            with self.subTest(register=key):
                f, _staged = stage(self, key)
                r = subprocess.run(
                    ["python3", str(TASKS), f"{key}-write", "--from-board",
                     "--root", str(f.root)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


# ── 6. nothing was added to the invariant ─────────────────────────────────


class TestTheInvariantIsStillACountRule(Base):
    """USER-906 chose option B and this row may not quietly make it option E.

    Asserted behaviourally rather than by reading the source: the invariant is
    handed the exact numbers a substitution produces and must not raise. If a
    fifth predicate ever lands in `refuse_to_shrink`, one of these is red.
    """

    def test_equal_counts_are_permitted_on_every_register_and_command(self):
        for key in REGISTERS:
            for name in ("intake", "ask", "risk-add", "resolve-intake",
                         "intake-sweep", "purge", "add", "route", "answer"):
                with self.subTest(register=key, event=name):
                    PT.refuse_to_shrink(key, Path("/nowhere/x.jsonl"),
                                        {"event": name, "count": 0}, 7, 7)

    def test_a_shrink_is_still_refused_on_the_same_board(self):
        """The other half. The bound did not get looser while this row ran."""
        f = self.fixture(build_board(), mint=("intake",))
        before = f.raw("intake.jsonl")
        rows = INTAKE_TABLE.strip().split("\n")
        f.write_board(build_board(intake="\n".join(rows[:-1]) + "\n"))
        board, ops = parse(f.board_text())
        self.assertLess(len(S.intake_records(board, ops)),
                        len(f.records("intake.jsonl")),
                        "control: the board must derive FEWER records, or the "
                        "invariant is not the thing being asked")
        # Both refusal branches, on the same board: an ORDINARY write (`add`
        # touches `## Intake` and removes nothing from it) and a DECLARED
        # removal over its own bound. One test would leave the other branch
        # untested and neither is the whole rule.
        rc, out = f.run("add", "--title", "an unrelated task",
                        "--deliverable", "d", "--verification", "v")
        self.assertNotEqual(rc, 0, "an ordinary shrink was permitted:\n" + out)
        self.assertIn("may never make a canonical store smaller", out)
        rc, out = f.run("resolve-intake", "1", "--outcome", "dropped",
                        "--reason", "no")
        self.assertNotEqual(rc, 0, "a bounded shrink was permitted:\n" + out)
        self.assertIn("removes 0 record(s)", out)
        self.assertEqual(f.raw("intake.jsonl"), before)

    def test_the_substitution_report_never_changes_the_exit_code(self):
        for key in REGISTERS:
            with self.subTest(register=key):
                f, _staged = stage(self, key)
                self.assertEqual(f.run(*ORDINARY[key])[0], 0,
                                 "the report became a refusal")

    def test_a_dry_run_previews_the_report_and_writes_nothing(self):
        f, staged = stage(self, "intake", n=2)
        before = f.raw("intake.jsonl")
        rc, out = f.run("intake", "--title", "a previewed request", "--dry-run")
        self.assertEqual(rc, 0, out)
        self.assertEqual(reported(out), staged.n, out)
        self.assertIn("would not survive", out)
        self.assertEqual(f.raw("intake.jsonl"), before,
                         "the dry run wrote the store")


# ── 7. the identity map is complete ───────────────────────────────────────


class TestEveryRegisterHasAnIdentity(unittest.TestCase):
    """A fourth register may not arrive without saying what identifies it.

    Same shape as `TestTheMapIsComplete` one module over: quantified over the
    shipped `REGISTER_SPEC`, so adding a register and forgetting this is a red
    test rather than a silent register nothing reports on.
    """

    def test_every_register_spec_key_has_an_identity(self):
        self.assertEqual(set(PT.REGISTER_SPEC), set(PT.REGISTER_IDENTITY))

    def test_the_intake_identity_is_the_one_the_carry_forward_join_uses(self):
        """One tuple, one place. `carry_forward_is_addressable` reads this map.

        Behavioural: a stored record whose identity moved must stop the
        carry-forward, and that is decided by the SAME function this module
        reports through.
        """
        current = [{"order": 0, "request": "a", "arrived": "d",
                    "discharged": True}]
        same = [{"order": 0, "request": "a", "arrived": "d"}]
        moved = [{"order": 0, "request": "b", "arrived": "d"}]
        self.assertTrue(
            PT.carry_forward_is_addressable("intake", same, current))
        self.assertFalse(
            PT.carry_forward_is_addressable("intake", moved, current))
        self.assertEqual(len(PT.substituted_away("intake", current, moved)), 1)
        self.assertEqual(len(PT.substituted_away("intake", current, same)), 0)


if __name__ == "__main__":
    unittest.main()
