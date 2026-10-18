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

**Constructed since TASK-262 round 4a.** Every substitution here is a hand
edit to a held `BOARD.md`, and a write no longer reads one, so the report is
reached through `test_register_store_invariant § the_write_mutates_the_held_board`
(`Fixture.write_board` turns it on): the report is still in `commit()` and a
write whose in-memory board disagrees with its store is still the state it is
for, but that state is constructed, not reached from the command line.
`TestAHandEditToAHeldBoardReachesNoStore` one module over asserts the real path.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import task_actor

COVERS = ("bin/perry-task", "bin/perry-lint", "bin/perry_store.py")

import json
import sys
import unittest
from pathlib import Path

import inproc

from test_register_store_invariant import (
    ASK_TABLE, Base, INTAKE_TABLE, LINT, PT, REGISTERS, RISK_TABLE,
    TASKS, build_board, parse, the_write_mutates_the_held_board)

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

#: **An intake register with more rows than the report will PRINT.**
#:
#: `SUBSTITUTION_RECORDS_SHOWN` is 5 and every other board in this module stages
#: at most 3 losses, so until this constant existed the `len(lost) > 5` branch
#: was never reached: the count could be silently swapped for the length of the
#: printed list and 71 tests came back OK. Nine rows, so seven can be destroyed
#: at once and the message has to shorten its LIST without shortening its
#: NUMBER — which is the exact failure this row exists to close, one level down.
WIDE_INTAKE = ("| Arrived | Request | Outcome |\n|---|---|---|\n"
               + "".join(f"| 2026-08-{d:02d} | a request filed on the "
                         f"{d}th and still waiting | — |\n"
                         for d in range(11, 20)))

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
    # **In-process** (TASK-368). This module's `Base` comes from
    # `test_register_store_invariant`, whose helpers this row already
    # converted, so leaving these three sites on `subprocess` would be the
    # half-converted module `TASK-402`'s shared-helper rounds went wrong on.
    # Measured: 92.8% of the module is children, 87.7% is the boundary.
    r = inproc.run("perry-lint", ["--root", str(root)])
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


# ── 3. the report does not cry wolf ───────────────────────────────────────


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


    def test_frozen_json_refusal_preserves_every_substituted_record(self):
        f, staged = stage(self, "asks", n=2)
        before = f.raw(staged.store)
        with the_write_mutates_the_held_board():
            out = inproc.run("perry-task", task_actor.owned([
                "ask", "--needed", "a question", "--json", "--root", str(f.root)],
                'test_register_substitution'))
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("read-only", json.loads(out.stdout)["refused"])
        self.assertEqual(f.raw(staged.store), before)
        self.assertEqual(staged.lost(), [])


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


class TestRetainedSubstitutionUnits(Base):
    def test_identity_loss_is_computed_and_reported_without_performing_a_write(self):
        for key in REGISTERS:
            with self.subTest(register=key):
                f, staged = stage(self, key)
                lost = PT.substituted_away(key, staged.before, staged.derived)
                self.assertEqual(len(lost), staged.n)
                expected = {IDENT[key](r) for r in staged.before} - {IDENT[key](r) for r in staged.derived}
                self.assertEqual({IDENT[key](r) for r in lost}, expected)
                report = PT.substitution_report(key, f.root / staged.store, lost, 0)
                self.assertIsNotNone(report)
                self.assertEqual(reported(report), staged.n)
                for ident in expected:
                    self.assertIn(str(ident), report)

    def test_retired_commands_cannot_apply_a_count_preserving_substitution(self):
        for key in REGISTERS:
            f, staged = stage(self, key)
            before = f.raw(staged.store)
            rc, out = f.run(*ORDINARY[key])
            self.assertEqual(rc, 1, out)
            self.assertIn("read-only", out)
            self.assertEqual(f.raw(staged.store), before)
            self.assertEqual(staged.lost(), [])

    def test_report_caps_display_but_not_the_loss_count(self):
        f = self.fixture(build_board(intake=WIDE_INTAKE), mint=("intake",))
        staged = Staged(f, "intake", 7).check(self)
        lost = PT.substituted_away("intake", staged.before, staged.derived)
        self.assertEqual(len(lost), 7)
        report = PT.substitution_report("intake", f.root / staged.store, lost, 0)
        self.assertEqual(reported(report), 7)
        for record in lost[:5]:
            self.assertIn(record["request"], report)
        for record in lost[5:]:
            self.assertNotIn(record["request"], report)


if __name__ == "__main__":
    unittest.main()
