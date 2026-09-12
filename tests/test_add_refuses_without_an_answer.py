"""`perry-task add` refuses a row that answers the KR question neither way.

TASK-439. `phase/003-storage-code.md § Definition of Done` item 5 asks that
every `main`-track row opened after the gate lands carry an edge or a
declaration. **That gate was never built.** What existed was the QUESTION: a
stderr warning on `add`, and then the row, filed, with `kr: null` on its event
and a permanent place in `P003-O3-KR2`'s `never_answered` — permanent because a
later `perry-goals link` writes `via: "link"`, which the KR excludes by design.

Measured on this repository before the change: **19 of 59 rows, 32.2%**, and
**94.8%** of every main-track `add` ever run took the warned branch. That is
what a warning buys.

**The four states this module pins**, and the reason each one is here:

    --kr <ID>                edge written, exit 0        unchanged
    --unlinked               declaration written, 0      unchanged
    neither, register        REFUSED                  ←  this row
    neither, NO register     filed + warned              must NOT change

**Why the last line is a test and not an oversight.** `§ What it must not do`
item 4 requires `add` to keep working on a project with no linkage register,
and the reason the refusal cannot simply extend there is measurable rather than
stylistic: `--unlinked` is REFUSED outright on a store-less project
(`linkage_add_change` — it has no event field and no second home), and `--kr`
on a fresh project can only name a key result that does not exist, because
`plan-phase` is what writes the register. An unconditional refusal would leave
a GUESSED `--kr` as the only way to file any row at all on a fresh project, and
`reference/okr-linkage.md` forbids that guess. So the gate fires where the
question is answerable and stays a warning where it is not.

**How these tests are built to be able to fail**, which is the property this
project has had to re-earn six times:

*`TestTheRefusalIsNotVacuous`* is the anti-vacuity control the spec asks for. A
test that merely asserted a non-zero exit would pass against a binary that
refused for ANY reason — a missing `--summary`, an unwritable root, a typo in
the fixture. `TASK-281` round 1's refusal test rotted green exactly that way.
So the class asserts the refusal on a command line that is otherwise COMPLETE
and would have exited 0 before this row — the sibling `--kr` and `--unlinked`
runs in `TestBothRemediesStillWork` are that proof, from the same fixture — and
it reads the refusal's own subject matter out of the message rather than
trusting the exit code alone.

*`TestTheRefusalDoesNotSilentlyDeclare`* is the mutation target the spec names
second. The cheap wrong fix for this row is to stop refusing and instead treat
omission AS a declaration, which makes `P003-O3-KR2` jump to 100% overnight and
writes "serves no key result" into a canonical, un-withdrawable store for
hundreds of rows nobody asked. This class asserts through
`lib.same_action_linkage` — the reader — that a refused row reaches NEITHER
numerator path.

*`TestNothingWasWritten`* pins the refusal's position: before `mint_id`. A
refusal that fires after the id is minted burns an id per mistake, and
`ADR-013` says ids are terminal.

Run: python3 tests/parallel test_add_refuses_without_an_answer
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

# The row D module is imported for its FIXTURE only, exactly as TASK-394's
# module imports it. unittest collects only what is in this module's namespace,
# so nothing under `M.` is run twice.
import test_add_writes_the_edge as M  # noqa: E402
import lib  # noqa: E402


class Base(M.Fixture):
    """`M.Fixture` plus the two readings this row's assertions need."""

    def linkage(self, d: pathlib.Path) -> dict:
        """`P003-O3-KR2` as its own reader computes it, not as a literal."""
        lk = self.records(d)
        return lib.same_action_linkage(lk, self.events(d))

    def rows_on_board(self, d: pathlib.Path) -> list[str]:
        p = d / "tasks.jsonl"
        if not p.exists():
            return []
        return [json.loads(x)["id"]
                for x in p.read_text().split("\n") if x.strip()]


class TestTheRefusalIsNotVacuous(Base):
    """Neither flag, on a project that HAS a register, is refused.

    The anti-vacuity control: the same fixture and the same command line, minus
    only the KR answer, exits 0 in `TestBothRemediesStillWork`. So a green here
    cannot be a fixture that refuses everything.
    """

    def test_neither_flag_is_refused(self):
        d = self.project()
        proc = self.add(d, "a row with no answer")
        self.assertNotEqual(proc.returncode, 0,
                            f"add exited 0 without either flag:\n{proc.stdout}")

    def test_the_refusal_is_about_the_kr_question(self):
        """Not merely non-zero — refused for THIS reason.

        Without this, any unrelated refusal keeps the class green, which is the
        exact way `TASK-281` round 1's refusal test rotted.
        """
        d = self.project()
        proc = self.add(d, "a row with no answer")
        self.assertIn("--kr", proc.stderr)
        self.assertIn("--unlinked", proc.stderr)

    def test_the_refusal_names_which_one_means_serves_no_kr(self):
        """Deliverable 1: the refusal must say which remedy means what.

        A refusal that lists two flags without distinguishing them hands the
        caller a coin to flip, and one side of that coin writes a permanent
        record.
        """
        d = self.project()
        proc = self.add(d, "a row with no answer")
        low = proc.stderr.lower()
        self.assertIn("serves no", low)
        self.assertIn("cannot be withdrawn", low)


class TestNothingWasWritten(Base):
    """The refusal fires before anything lands, including the id."""

    def test_no_row_was_filed(self):
        d = self.project()
        before = self.rows_on_board(d)
        self.add(d, "a row with no answer")
        self.assertEqual(self.rows_on_board(d), before)

    def test_no_add_event_was_appended(self):
        d = self.project()
        before = len(self.events(d))
        self.add(d, "a row with no answer")
        self.assertEqual(len(self.events(d)), before)

    def test_no_id_was_burned(self):
        """ADR-013: ids are terminal, so a refusal must not consume one.

        Drives the refusal and then a successful `add`, and asserts the
        successful row took the id the refused one would have.
        """
        d = self.project()
        self.add(d, "a row with no answer")
        ok = self.add(d, "a row with an answer", self.STORE_KR)
        self.assertEqual(self.new_id(ok), "TASK-101")


class TestBothRemediesStillWork(Base):
    """The two answers the refusal names both exit 0 — and both are counted.

    This is the sibling control that makes `TestTheRefusalIsNotVacuous`
    meaningful, and it is also deliverable 1's other half: a refusal naming a
    remedy that does not work is the defect this row was sent to remove from
    the blank-`--kr` message.
    """

    def test_kr_is_accepted_and_counted(self):
        d = self.project()
        proc = self.add(d, "a row with a KR", self.STORE_KR)
        tid = self.new_id(proc)
        self.assertIn(tid, self.linkage(d)["linked_at_add"])

    def test_unlinked_is_accepted_and_counted(self):
        d = self.project()
        proc = self.add(d, "a row serving no KR", None, "--unlinked")
        tid = self.new_id(proc)
        self.assertIn(tid, self.linkage(d)["declared_unlinked_at_add"])


class TestTheRefusalDoesNotSilentlyDeclare(Base):
    """A refused row must reach NEITHER numerator path.

    The cheap wrong fix — treat omission as `--unlinked` — makes the KR jump to
    100% and writes an un-withdrawable "serves no key result" into a canonical
    store for every row nobody answered. Asserted through the reader, so a
    writer that emitted a record no reader counts cannot pass either.
    """

    def test_omission_is_not_a_declaration(self):
        d = self.project()
        before = self.linkage(d)
        self.add(d, "a row with no answer")
        after = self.linkage(d)
        self.assertEqual(after["declared_unlinked_at_add"],
                         before["declared_unlinked_at_add"])
        self.assertEqual(after["numerator"], before["numerator"])

    def test_omission_does_not_enter_the_population(self):
        """No row, so no denominator either — the KR must not move at all."""
        d = self.project()
        before = self.linkage(d)
        self.add(d, "a row with no answer")
        self.assertEqual(self.linkage(d)["denominator"], before["denominator"])


class TestAStoreLessProjectStillFiles(Base):
    """`§ What it must not do` item 4, driven rather than asserted in prose.

    Carries its own control: the register-bearing sibling of this exact command
    line is refused in `TestTheRefusalIsNotVacuous`, so a green here is the
    register guard working and not the refusal having quietly failed to ship.
    """

    def test_add_still_works_with_no_register(self):
        d = self.project(with_store=False)
        proc = self.add(d, "a row on a fresh project")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_it_still_warns(self):
        d = self.project(with_store=False)
        proc = self.add(d, "a row on a fresh project")
        self.assertIn("warning", proc.stderr.lower())

    def test_the_warning_does_not_advise_a_command_that_refuses(self):
        """The reconciliation, applied to the warning as well as the refusal.

        The old text offered `perry-task add --unlinked` and `perry-goals link
        --unlinked` — and BOTH refuse on a store-less project, which is now the
        only project that can reach this line. Every remedy it named was a
        remedy that refuses.
        """
        d = self.project(with_store=False)
        proc = self.add(d, "a row on a fresh project")
        self.assertNotIn("perry-task add --unlinked", proc.stderr)
        self.assertIn("plan-phase", proc.stderr)


class TestTheBlankRefusalIsReconciled(Base):
    """The blank-`--kr` refusal keeps its place, and stops giving dead advice.

    `TASK-281` round 3 settled that refusing `--kr ""` is RIGHT: blank-means-
    omission is the hazard, because `--kr "$KR"` with `KR` unset would other-
    wise file a never-answered row behind a warning. This row does not collapse
    it — it is load-bearing BECAUSE of the new refusal, since a caller told
    only "pass one of these two" would plausibly reach for `--unlinked` and
    write a permanent wrong declaration caused by an empty shell variable.

    What DID have to change is the sentence: it used to say *"omit `--kr` for
    that, which files the row and warns"*, which after this row is advice to
    run the command that now refuses.
    """

    def blank(self, d: pathlib.Path):
        """`--kr ""`, passed as an EXPLICIT empty value.

        Not `self.add(d, title, "")` — `M.Fixture.add` appends `--kr` only when
        the value is truthy, so an empty string there drops the flag entirely
        and drives the "neither" state instead. That mistake made three of this
        class's assertions pass against the wrong refusal, and one of them
        passed only because the new neither-message happens to contain the word
        "blank". It is the defect this file's own docstring is about, found in
        this file. The flag goes through `*extra`, where nothing filters it.
        """
        return self.add(d, "a row with a blank KR", None, "--kr", "")

    def test_blank_kr_is_still_refused(self):
        d = self.project()
        proc = self.blank(d)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("is blank", proc.stderr)

    def test_it_no_longer_advises_omitting_the_flag(self):
        d = self.project()
        proc = self.blank(d)
        self.assertNotIn("omit `--kr`", proc.stderr)
        self.assertNotIn("files the row and warns", proc.stderr)

    def test_it_points_at_the_flag_on_this_command(self):
        """Round 3's correction: `add --unlinked`, not `goals link --unlinked`.

        `link` is the after-the-fact path; at `add` time the faster remedy is
        the one TASK-394 shipped here, and it is the only one landing in the
        same transaction, which is the only form `P003-O3-KR2` counts.
        """
        d = self.project()
        proc = self.blank(d)
        self.assertIn("--unlinked", proc.stderr)

    def test_it_names_the_empty_variable_hazard(self):
        """The sentence is the whole reason this refusal is not redundant."""
        d = self.project()
        proc = self.blank(d)
        self.assertIn("$KR", proc.stderr)


class TestTheContradictionIsUntouched(Base):
    """`--kr X --unlinked` still refuses, and still for its own reason.

    Bound control: this row changes the "neither" state and must not disturb
    the "both" one, whose refusal names irreversibility rather than blankness.
    """

    def test_both_flags_still_refused(self):
        d = self.project()
        proc = self.add(d, "a contradictory row", self.STORE_KR, "--unlinked")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("contradictory", proc.stderr)


if __name__ == "__main__":
    unittest.main()
