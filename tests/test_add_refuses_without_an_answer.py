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

PERRY_HOME = ROOT


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


class TestTheRefusalMakesNoVisibilityClaim(Base):
    """`USER-928` answer C: the claim is gone, and the measurement stays.

    **The same sentence FAILed two V4 rounds.** It told a caller that reaching
    for `--unlinked` buys a record that stays VISIBLE, which was the only
    non-neutral item in `§ What it must not do` item 1's argument that the
    refusal does not make `--unlinked` the easy default.

    * Round 1 charged it for naming `perry-lint`. `linkage-unlinked-exists`
      warns ONLY on a declared id that is not a record in `tasks.jsonl` — a
      typo, or a purged row. A healthy declaration hits its `continue`.
    * Round 2 charged the correction, which named
      `perry-state --section attribution`. That reader goes through
      `parsers.linkage_records_for_phase` and keeps a record only while its
      `phase` matches `phase/CURRENT`.

    The user was offered widening the reader (B) and chose to delete the claim
    (C). So `declared_unlinked` stays phase-scoped, and that is now a recorded
    property rather than a defect awaiting a fix.

    **These tests hold the deletion AND the reason**, which is the part that
    matters: `test_the_named_reader_is_phase_scoped` is what stops the claim
    being re-added in good faith by someone who checks it on a fresh board and
    sees it work. It fails the day the reader is widened, and that failure is
    the signal that C can be revisited.
    """

    def test_the_message_claims_no_standing_visibility(self):
        d = self.project()
        proc = self.add(d, "a row with no answer")
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        for gone in ("perry-lint", "perry-state", "declared_unlinked",
                     "as long as it stands"):
            self.assertNotIn(gone, proc.stderr,
                             f"the visibility claim is back, via {gone!r}. "
                             f"Two V4 rounds measured it false; re-adding it "
                             f"needs the reader widened first (USER-928 B)")

    def test_the_friction_it_keeps_is_the_true_one(self):
        """C leaves one item, and it must actually be stated."""
        d = self.project()
        proc = self.add(d, "a row with no answer")
        self.assertIn("CANNOT BE WITHDRAWN", proc.stderr)

    def test_the_named_reader_is_phase_scoped(self):
        """**Why the claim is gone, as a measurement rather than a memory.**

        A declaration written under the current phase is reported; the same
        record, on disk and unchanged, reports nowhere once a DIFFERENT phase
        is current and has a register of its own. This is the test that
        refuses to let the sentence come back.

        **The first draft of this test passed for the wrong reason.** It moved
        `phase/CURRENT` to a phase with no records at all, and
        `linkage_records_for_phase` returns `None` outright when its slice
        holds no `kr` record — so the declaration vanished through a
        different door and mutating the phase filter left the test GREEN.
        That green is what found this. Phase 004 now gets a register, so the
        slice is real and the only thing that can drop the record is the
        `unlinked` phase check the class docstring names.
        """
        d = self.project()
        tid = self.new_id(self.add(d, "a row serving no KR", None,
                                   "--unlinked"))
        self.assertIn(tid, self.attribution(d)["declared_unlinked"] or [],
                      "the declaration is not reported even under its own "
                      "phase — the reader changed shape and every claim in "
                      "this class needs re-deriving")

        lines = (d / "linkage.jsonl").read_text().rstrip("\n").split("\n")
        lines += [json.dumps({"kind": "objective", "phase": "004-next",
                              "id": "O1", "title": "an objective"}),
                  json.dumps({"kind": "kr", "phase": "004-next",
                              "objective": "O1", "id": "P004-O1-KR1",
                              "title": "a key result", "target": 1,
                              "current": 0, "stretch": False})]
        (d / "linkage.jsonl").write_text("\n".join(lines) + "\n")
        (d / "phase" / "CURRENT").write_text("004-next\n")

        self.assertIsNotNone(
            self.attribution(d)["declared_unlinked"],
            "phase 004's slice came back empty, so this test is measuring "
            "the no-register path again rather than the phase filter")
        self.assertNotIn(tid, self.attribution(d)["declared_unlinked"] or [],
                         "the reader is no longer phase-scoped. If that is "
                         "deliberate — USER-928 option B — the refusal MAY "
                         "claim standing visibility again, and this class is "
                         "the thing to revisit")

        record = [r for r in self.records(d)
                  if r.get("kind") == "unlinked" and r.get("task") == tid]
        self.assertEqual(1, len(record),
                         "the record did not survive the phase change on "
                         "disk, so the invisibility is not a reader scope")

    def test_the_lane_page_makes_no_visibility_claim_either(self):
        """The category, not the next instance (review.md § 2 rule 1).

        Round 1 found the claim in two product surfaces: the refusal, and the
        `add-task` bullet in `work/reference/subcommands.md`, which is the
        page an agent reads IN ORDER to open a row. Deleting it from one is
        how a rule with several enforcement points stays half-true.
        """
        page = (PERRY_HOME / "work" / "reference" / "subcommands.md").read_text()
        bullet = [ln for ln in page.split("\n")
                  if "--unlinked` is a declaration to mean" in ln]
        self.assertEqual(len(bullet), 1,
                         "the add-task KR bullet moved; re-anchor this test "
                         "rather than deleting it")
        self.assertIn("cannot be withdrawn", bullet[0].lower())
        self.assertNotIn("for as long as it stands", bullet[0])


class TestTheRefusalIsDeliberatelyTrackIndependent(Base):
    """Round 1's ROW-2, decided here rather than left to a green mutation.

    The reviewer measured that the refusal fires on the `intake` track too,
    where `P003-O3-KR2` counts nothing — `lib.same_action_linkage` skips every
    event whose track is not `main` (`bin/lib/__init__.py:1419`) — and that
    narrowing it to `main` changed nothing any test could see (`MUT-B`, green).
    An unpinned scope in either direction is the finding, so this class pins
    it, and the direction it pins is the one already shipped.

    **Why track-independent is the right answer and not merely the shipped
    one.** The refusal serves `phase/003 § Definition of Done` item 5, but the
    thing it protects is older and wider than one phase's KR: a row filed with
    no answer to the KR question is un-withdrawable from `never_answered`,
    because a later `perry-goals link` writes `via: "link"`. That is a property
    of the STORE, not of the track — an intake row promoted to `main` later
    carries its blank answer with it, and nothing on the promotion path goes
    back and asks. Scoping the gate to `main` would mean the only rows exempt
    from the question are the ones most likely to change track.

    The cost is real and named rather than hidden: on a non-main track the
    refusal buys today's metric nothing, so a caller there spends the minute
    for a future reader rather than for a number.
    """

    INTAKE = ("--track", "intake", "--stage", "new", "--arrived", "2026-09-13")

    def test_a_non_main_track_is_refused_too(self):
        d = self.project()
        proc = self.add(d, "an intake row with no answer", None, *self.INTAKE)
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("neither --kr nor --unlinked", proc.stderr)

    def test_the_control_exits_zero_on_the_same_track(self):
        """Anti-vacuity: the track itself is not what refuses."""
        proc = self.add(self.project(), "an intake row that answers",
                        None, "--unlinked", *self.INTAKE)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_the_metric_is_unmoved_either_way_which_is_the_cost(self):
        """The reviewer's measurement, kept as a test rather than as prose."""
        d = self.project()
        before = self.linkage(d)
        self.add(d, "an intake row that answers", None, "--unlinked",
                 *self.INTAKE)
        after = self.linkage(d)
        self.assertEqual(after["denominator"], before["denominator"],
                         "an intake row entered `P003-O3-KR2`'s population — "
                         "if that is now true, this row's cost argument "
                         "changed and the scope decision needs re-taking")


class TestTheGateKeysOffThePhaseNotTheFile(Base):
    """USER-928 answer A, closing round 2's FAIL-2.

    **The gate used to demand an answer the register could not supply.** It
    fired on `linkage.jsonl` merely EXISTING, while `--unlinked` needs more
    than that: `linkage_add_change` refuses a declaration when the store
    declares no key result for the current phase, because such a record has no
    phase to be made against.

    In that window — `phase/CURRENT` cleared, which
    `goals/reference/phases.md § score-phase` step 7 PRESCRIBES until the next
    `plan-phase` — the reviewer measured, and the PMO reproduced:

        add (neither flag)      refused — "pass exactly one"
        add --unlinked          REFUSED — "no key result for the current phase"
        add --kr P004-O9-KR9    written, exit 0, empty stderr

    The accepted one wrote an edge to a key result no record declares and
    `perry-lint` said nothing about it. **The only way past a gate whose own
    message says "resolve the id through `linkage.jsonl` rather than guessing
    it" was the guess `reference/okr-linkage.md` forbids.** Before this row all
    five such states filed with a warning, so the gate was strictly worse than
    what it replaced.

    The gate now asks `_current_store_phase` — the same predicate the writer
    asks — so the two cannot disagree about whether the register can answer.

    **What this does NOT fix, deliberately.** A fabricated `--kr` is still
    accepted in the gap. That is id validation, not this gate, and A removes
    the *forcing* rather than the acceptance: the caller is no longer pushed
    into the guess. `test_a_fabricated_kr_is_still_accepted_in_the_gap` pins
    that boundary rather than leaving a reader to assume it was closed.
    """

    def gap(self):
        """A project whose store has no records for the current phase.

        **`phase/CURRENT` names a REAL phase the store knows nothing about**,
        rather than being blank — and that distinction is round 3's second V4
        FAIL. The first version of this fixture cleared the pointer, so
        `_current_store_phase` returned at `if not number` and never read the
        store at all. Deleting the phase match it is named for left every test
        in this class green: the class asserted a property it never exercised.

        Pointing at `004-next` instead means the store IS read, the phase match
        IS evaluated, and it finds no `kr` for 004 among the 003 records the
        fixture writes. `test_the_phase_match_is_load_bearing` is the guard
        that keeps it that way.
        """
        d = self.project(store_edges={}, store_unlinked=[])
        (d / "phase" / "CURRENT").write_text("004-next\n")
        return d

    def between_phases(self):
        """**The window itself — a BLANK `phase/CURRENT` — kept beside `gap()`.**

        Round 5 made `gap()` point at `004-next` so the phase match would be
        evaluated, and in doing so REPLACED this fixture instead of adding it.
        The phase match gained a test and the between-phases window lost its
        only one: the state `goals/reference/phases.md § score-phase` step 7
        prescribes, and the one USER-928 answer A was built for. Round 5's V4
        FAIL measured it: reading a blank pointer as phase 003 left every test
        in this module green. Both shapes now exist, each with its own tests,
        and `test_the_window_fixture_really_is_blank` stops the swap recurring.
        """
        d = self.project(store_edges={}, store_unlinked=[])
        (d / "phase" / "CURRENT").write_text("")
        return d

    def test_the_window_fixture_really_is_blank(self):
        d = self.between_phases()
        self.assertEqual("", (d / "phase" / "CURRENT").read_text().strip(),
                         "the between-phases fixture no longer writes a blank "
                         "pointer, which is how round 5 lost this window")

    def test_the_window_files_the_row_with_a_warning(self):
        proc = self.add(self.between_phases(), "a row opened between phases")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("warning", proc.stderr.lower())

    def test_in_the_window_the_honest_answer_is_refused_and_the_row_still_files(self):
        """Round 2's FAIL-2, asserted on the window that produced it."""
        d = self.between_phases()
        self.assertNotEqual(
            0, self.add(d, "an honest declaration", None, "--unlinked").returncode)
        self.assertEqual(0, self.add(d, "a row").returncode,
                         "in the window the gate demands an answer the writer "
                         "refuses — round 2's FAIL-2, restored")

    def test_a_blank_pointer_is_not_read_as_a_phase(self):
        """The mutation round 5's verdict ran, as a test: were a blank
        `CURRENT` read as phase 003, the fixture's 003 records would declare,
        the gate would fire, and this would refuse."""
        proc = self.add(self.between_phases(), "a row")
        self.assertNotIn("neither --kr nor --unlinked", proc.stderr)

    def test_the_gap_files_the_row_instead_of_refusing(self):
        proc = self.add(self.gap(), "a row opened between phases")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_the_gap_still_warns(self):
        proc = self.add(self.gap(), "a row opened between phases")
        self.assertIn("warning", proc.stderr.lower())

    def test_the_warning_does_not_claim_the_store_is_missing(self):
        """The store is right there; saying otherwise is false about a file
        the caller can see. Two ways to reach that line, two true sentences."""
        proc = self.add(self.gap(), "a row opened between phases")
        self.assertNotIn("this project has no", proc.stderr)
        self.assertIn("no key result for the current phase", proc.stderr)

    def test_a_store_less_project_still_says_the_store_is_missing(self):
        """The control for the sentence above: the other branch is untouched."""
        proc = self.add(self.project(with_store=False), "a row, no register")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("this project has no", proc.stderr)

    def test_the_honest_answer_is_not_refused_while_the_row_is_filed(self):
        """**The asymmetry that made this a FAIL, asserted directly.**

        A gate is only legitimate if at least one answer it names can be given.
        In the gap `--unlinked` is refused by the writer, so the gate must not
        be the thing that demands it.
        """
        d = self.gap()
        declared = self.add(d, "an honest declaration", None, "--unlinked")
        self.assertNotEqual(declared.returncode, 0,
                            "the writer stopped refusing a declaration with "
                            "no phase — if that changed, this whole gap and "
                            "the gate's stand-down need re-deriving")
        self.assertEqual(self.add(d, "a row").returncode, 0,
                         "the writer refuses the honest answer AND the gate "
                         "still demands one — that is the FAIL, restored")

    def test_a_fabricated_kr_is_still_accepted_in_the_gap(self):
        """The bound. A removes the FORCING, not the acceptance.

        Written as a test so the limit is a measured fact rather than a
        sentence in a result document nobody re-runs. If id validation lands
        later this goes red, and that is the correct signal.
        """
        proc = self.add(self.gap(), "a row naming a KR nobody declares",
                        "P004-O9-KR9")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_the_gate_still_refuses_where_the_register_answers(self):
        """Anti-vacuity: the same command, a register with records, refused."""
        proc = self.add(self.project(), "a row with no answer")
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("neither --kr nor --unlinked", proc.stderr)

    def test_the_phase_match_is_load_bearing(self):
        """**The test the first fixture could not be.**

        `gap()` now points `phase/CURRENT` at a phase the store has no records
        for, so reaching this assertion requires the store to be READ and the
        phase compared. With the pointer blank — the old fixture —
        `_current_store_phase` returned before either happened and this class
        passed with the phase match deleted.
        """
        d = self.gap()
        self.assertEqual("004-next",
                         (d / "phase" / "CURRENT").read_text().strip(),
                         "the fixture stopped naming a real phase, so the "
                         "class is back to returning before the store is read")
        kinds = {r.get("kind") for r in self.records(d)}
        self.assertIn("kr", kinds,
                      "the fixture's store carries no `kr` record at all, so "
                      "the phase match below has nothing to compare and the "
                      "gap is reached for the wrong reason")
        phases = {str(r.get("phase") or "") for r in self.records(d)
                  if r.get("kind") == "kr"}
        self.assertTrue(phases and not any(p.startswith("004-") for p in phases),
                        f"the store now holds a `kr` for phase 004 ({phases}), "
                        f"so this fixture is no longer a gap")
        self.assertEqual(0, self.add(d, "a row").returncode)


class TestAnUnreadableRegisterIsItsOwnAnswer(Base):
    """Round 3's V4 FAIL-1: `""` meant three different things.

    `parsers.load_linkage_store` returns `None` for a MALFORMED store exactly
    as for an absent one. That contract is deliberate and documented there —
    the reader is read-only and `perry-lint § check_linkage_store` is the tool
    that says *why* a store will not parse — so it is not changed. What was
    wrong was reading its three-way answer as a two-way one.

    Measured: one git conflict marker appended to a `linkage.jsonl` full of key
    results for the open phase took `add` with neither flag from **rc=1** to
    **rc=0**, filed the row, and printed the between-phases warning — **every
    clause of which is false** of that project. The register does declare key
    results for the current phase and no `score-phase` window is open; it is
    unparseable, which is the one thing the message did not say. `--unlinked`
    stays refused there, so the row lands in `never_answered` permanently.

    A register nobody can parse is one we cannot ask, not one with nothing to
    say — which is the case for stopping rather than for waving through.
    """

    def gap(self):
        d = self.project(store_edges={}, store_unlinked=[])
        (d / "phase" / "CURRENT").write_text("004-next\n")
        return d

    def unparseable(self):
        """A register full of records for the open phase that will not load."""
        d = self.project()
        with (d / "linkage.jsonl").open("a", encoding="utf-8") as fh:
            fh.write("<<<<<<< HEAD\n")
        return d

    def test_an_unparseable_register_is_refused(self):
        proc = self.add(self.unparseable(), "a row with no answer")
        self.assertNotEqual(proc.returncode, 0, proc.stdout)

    def test_it_does_not_claim_the_between_phases_window(self):
        """The false sentence, named so it cannot come back."""
        proc = self.add(self.unparseable(), "a row with no answer")
        self.assertNotIn("score-phase", proc.stderr)
        self.assertNotIn("declares no key result", proc.stderr)

    def test_it_says_what_is_actually_wrong_and_who_diagnoses_it(self):
        proc = self.add(self.unparseable(), "a row with no answer")
        self.assertIn("could not be read", proc.stderr)
        self.assertIn("perry-lint", proc.stderr)

    def test_nothing_was_written(self):
        d = self.unparseable()
        before = self.rows_on_board(d)
        self.add(d, "a row with no answer")
        self.assertEqual(before, self.rows_on_board(d))

    def test_unlinked_on_an_unreadable_register_says_it_could_not_be_read(self):
        """Round 5's V4 ROW C, corrected under USER-930 answer A.

        The writer used to answer `--unlinked` here with "declares no key
        result for the current phase" — false of a file that still holds them.
        """
        proc = self.add(self.unparseable(), "a declaration", None, "--unlinked")
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("could not be read", proc.stderr)
        self.assertNotIn("declares no key result for the current", proc.stderr)

    def test_unlinked_between_phases_keeps_its_own_sentence(self):
        """The control: the other reason still gets the other message."""
        d = self.gap()
        proc = self.add(d, "a declaration", None, "--unlinked")
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("declares no key result for the current", proc.stderr)

    def test_an_answered_row_still_files(self):
        """**Anti-vacuity, and the bound.** This refusal is about the KR
        question being unanswerable, not about the store being broken. A
        caller who answers it is not blocked by a file this command only
        consulted to decide whether to ask."""
        proc = self.add(self.unparseable(), "a row with an answer",
                        self.STORE_KR)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_the_gap_and_the_unreadable_store_are_told_apart(self):
        """Three states, three answers, and only one of them files silently."""
        self.assertEqual(0, self.add(self.gap(), "a row").returncode)
        self.assertNotEqual(0, self.add(self.unparseable(), "a row").returncode)
        self.assertNotEqual(0, self.add(self.project(), "a row").returncode)


if __name__ == "__main__":
    unittest.main()
