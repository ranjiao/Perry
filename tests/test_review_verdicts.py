"""`perry-lint --reviews` — the V4 verdict block, and the row that must move.

Perry ran **ten V4 rounds in one night** and they wrote the verdict five
different ways: bare `FAIL`, `**Verdict**`, `> **VERDICT —**`, `> **Verdict:**`,
and a decorated section heading (`## 1 · TASK-067 — row integrity · **FAIL**`).
Three carried no line any parser could find.

A verdict nothing can read is a verdict that gets misfiled, and it was — rows
sat at `review` after their review had already failed, and it was the USER who
noticed, not a check. `work/reference/review.md § 3` fixes the shape; this is
what makes the shape real, because a rule stated in prose that nothing
implements is this repository's most-found defect.

Run: python3 tests/parallel test_review_verdicts
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINT = ROOT / "bin" / "perry-lint"

BOARD = """# Board

## P1

| ID | Title | Owner | Status | Next action | Evidence | Verification |
| --- | --- | --- | --- | --- | --- | --- |
{rows}

## Top risks

| ID | Risk | Opened | Status |
| --- | --- | --- | --- |
"""

VERDICT = """=== VERDICT ===
task: {task}
rung: V4
result: {result}
criteria: evidence/2026-08/{task}-spec.md
{grade}checked: {checked}
not-checked: {not_checked}
{proof}=== END VERDICT ===
"""


def verdict(task, result="PASS", checked="the refusal path on a copy",
            not_checked="Windows paths", proof="bin/x.py:12 the guard is absent",
            grade=None):
    """A block in `review.md § 3`'s shape.

    `grade` is the optional field § 3 gained on 2026-09-11 (TASK-419): the
    grade of the criterion this FAIL was charged against. Default `None` means
    the line is absent, which is what all 111 blocks in this repository's own
    corpus look like and what every test above this one assumes.
    """
    return VERDICT.format(
        task=task, result=result, checked=checked, not_checked=not_checked,
        grade=f"grade: {grade}\n" if grade else "",
        proof=f"proof: {proof}\n" if proof else "")



def lint_module():
    """`bin/perry-lint` as a module, for unit-testing its pure resolvers.

    The precedence tests below used to spawn the linter once each. perry-lint
    loads the schema and the viewer package on every start, and 8-worker
    `tests/run` already sits close enough to the machine's limits that the
    added spawns made `test_host_support`'s global-concurrency-cap assertion
    flake — a test measuring contention, perturbed by a test suite creating
    it. The wiring is still checked end-to-end below; only the arithmetic
    moved in-process.
    """
    spec = importlib.util.spec_from_loader(
        "perry_lint",
        importlib.machinery.SourceFileLoader("perry_lint", str(LINT)))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ReviewLintCase(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        (self.dir / "evidence" / "2026-08").mkdir(parents=True)
        (self.dir / ".perry").mkdir()

    def board(self, rows):
        (self.dir / "BOARD.md").write_text(BOARD.format(rows="\n".join(rows)))

    def row(self, tid, status, rung="V4", ev=""):
        return (f"| {tid} | a thing | Claude | {status} | — | {ev} | {rung} |")

    def evidence(self, name, text, make_criteria=True):
        """Write a review document, and by default make its exhibit honest.

        `verdict()` cites `evidence/2026-08/<TASK>-spec.md`, and until this
        fixture created it the citation named a file the temp tree did not
        carry — which `citation-not-on-branch` reports, correctly, on every
        test in this file. These tests are about the verdict's SHAPE; the
        exhibit pre-check has its own class below and passes
        `make_criteria=False` to say so deliberately.

        The generated spec carries a `## Bound` for the same reason
        (`review.md § 1`): a fixture that trips a check it is not testing
        makes every unrelated assertion in the file depend on that check.
        """
        (self.dir / "evidence" / "2026-08" / name).write_text(text)
        if not make_criteria:
            return
        for m in re.finditer(r"^criteria:\s*(\S+)\s*$", text, re.M):
            path = self.dir / m.group(1)
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# criteria\n\n## Bound\nEnumeration: ls bin/\nSize: 1\n"
                "Remainder: none\n")

    def run_lint(self):
        proc = subprocess.run(
            [sys.executable, str(LINT), "--reviews", "--root", str(self.dir),
             "--state-root", ".", "--json"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def rules(self):
        return sorted(f["rule"] for f in self.run_lint()["findings"])


class TestTheReportedDefect(ReviewLintCase):
    """The one the user found and no tool did.

    A round returns FAIL, the verdict lands in the evidence file, and the row
    keeps sitting at `review` because moving it was a separate manual step
    nobody took. `review` means *out for verification*; a row whose verdict has
    arrived does not belong there in either direction.
    """

    def test_a_failed_row_still_at_review_is_reported(self):
        self.board([self.row("TASK-001", "review")])
        self.evidence("TASK-001-review.md", verdict("TASK-001", "FAIL"))
        self.assertIn("fail-verdict-left-at-review", self.rules())

    def test_a_failed_row_that_was_reopened_is_not(self):
        self.board([self.row("TASK-001", "in_progress")])
        self.evidence("TASK-001-review.md", verdict("TASK-001", "FAIL"))
        self.assertNotIn("fail-verdict-left-at-review", self.rules())

    def test_a_passing_row_at_review_is_not_reported(self):
        """A PASS whose row has not been closed yet is a normal in-flight
        state, not a defect — the close is the next call, not a violation."""
        self.board([self.row("TASK-001", "review")])
        self.evidence("TASK-001-review.md", verdict("TASK-001", "PASS"))
        self.assertNotIn("fail-verdict-left-at-review", self.rules())


class TestAResentRowIsNotTheSameAsAnIgnoredOne(ReviewLintCase):
    """A row sits at `review` for two opposite reasons.

    Either the verdict arrived and nobody moved the row — the defect the user
    found — or the FAIL was **acted on** and the row was re-sent for a fresh
    round, which is the correct workflow. The first version of this check
    reported the second as the first, the moment its own author fixed a round
    and returned the task.

    No new field was needed. A FAIL is what moves a row OFF `review`, so if the
    row has since come BACK, the verdict has been acted on — readable straight
    off the event log.
    """

    def events(self, *transitions):
        (self.dir / ".perry" / "events.jsonl").write_text("\n".join(
            json.dumps({"event": "status", "task": "TASK-001",
                        "field": "status", "to": t})
            for t in transitions) + "\n")

    def test_a_next_action_event_is_not_read_as_a_status(self):
        """**Events written before the `field` key existed carry no `field`.**

        The first version filtered on `field in (None, "status")`, so a `next`
        event — whose `to` is the next-action TEXT — was read as a status
        transition. A 900-character prose blob became the row's "current
        status", no row ever looked re-sent, and four rows that HAD been acted
        on sat reported as verdict-ignored.

        A missing key does not mean "this is the kind I want". The honest test
        is the VALUE, and the declared statuses come from the schema rather
        than a list here.
        """
        self.board([self.row("TASK-001", "review")])
        self.evidence("r.md", verdict("TASK-001", "FAIL"))
        (self.dir / ".perry" / "events.jsonl").write_text("\n".join([
            json.dumps({"event": "status", "task": "TASK-001", "to": "review"}),
            json.dumps({"event": "status", "task": "TASK-001",
                        "to": "in_progress"}),
            json.dumps({"event": "status", "task": "TASK-001", "to": "review"}),
            # A pre-`field` next event. Its `to` is prose, not a status.
            json.dumps({"event": "next", "task": "TASK-001",
                        "to": "a long next action explaining what was fixed"}),
        ]) + "\n")
        self.assertNotIn("fail-verdict-left-at-review", self.rules(),
                         "a next-action event was counted as a status move")

    def test_a_row_that_never_left_review_is_reported(self):
        self.board([self.row("TASK-001", "review")])
        self.evidence("r.md", verdict("TASK-001", "FAIL"))
        self.events("review")
        self.assertIn("fail-verdict-left-at-review", self.rules())

    def test_a_row_fixed_and_re_sent_is_not(self):
        self.board([self.row("TASK-001", "review")])
        self.evidence("r.md", verdict("TASK-001", "FAIL"))
        self.events("review", "in_progress", "review")
        self.assertNotIn("fail-verdict-left-at-review", self.rules())

    def test_a_row_moved_off_and_left_off_is_not_reported_either(self):
        """It is not at `review`, so the finding does not apply — asserted so
        the supersession rule cannot quietly become "any row with history"."""
        self.board([self.row("TASK-001", "in_progress")])
        self.evidence("r.md", verdict("TASK-001", "FAIL"))
        self.events("review", "in_progress")
        self.assertNotIn("fail-verdict-left-at-review", self.rules())

    def test_with_no_event_log_the_finding_still_fires(self):
        """A project with no log has no supersession evidence, and silence
        there would turn the check off for exactly the boards least likely to
        have moved the row."""
        self.board([self.row("TASK-001", "review")])
        self.evidence("r.md", verdict("TASK-001", "FAIL"))
        self.assertIn("fail-verdict-left-at-review", self.rules())


class TestTheSymmetricHalf(ReviewLintCase):
    """A row at `review` for which no round was ever sent.

    **Found on this board, by the user asking whether TASK-093 was finished.**
    It sat at `review` because it had been moved there and no round dispatched,
    and `--reviews` called the board clean — the only shape it knew was a
    verdict nobody acted on. Two symmetric failure modes and one covered.

    The finding reports the AGE and does not judge it: a row sent an hour ago
    and one forgotten a week ago are the same STATE, and a threshold would be
    the checker guessing which.
    """

    def events_to_review(self, tid="TASK-001", ts="2026-08-19T10:00:00"):
        (self.dir / ".perry" / "events.jsonl").write_text(
            json.dumps({"event": "status", "task": tid, "field": "status",
                        "to": "review", "ts": ts}) + "\n")

    def test_a_row_at_review_with_no_verdict_is_reported(self):
        self.board([self.row("TASK-001", "review")])
        self.events_to_review()
        self.assertIn("review-with-no-verdict", self.rules())

    def test_a_row_with_a_verdict_is_not(self):
        """A round that HAS returned is the other check's business, not this
        one's — reporting both would name every row twice."""
        self.board([self.row("TASK-001", "review")])
        self.evidence("r.md", verdict("TASK-001", "PASS"))
        self.events_to_review()
        self.assertNotIn("review-with-no-verdict", self.rules())

    def test_a_lower_rung_is_not_asked_for_a_round(self):
        """V4 is the rung that means *a fresh reviewer ran*. V2 and V3 make no
        such claim, and asking them for a verdict would turn the finding into
        noise on every board that uses `review` as a normal status."""
        self.board([self.row("TASK-001", "review", rung="V3")])
        self.events_to_review()
        self.assertNotIn("review-with-no-verdict", self.rules())

    def test_a_row_not_at_review_is_not(self):
        self.board([self.row("TASK-001", "in_progress")])
        self.events_to_review()
        self.assertNotIn("review-with-no-verdict", self.rules())

    def test_the_age_is_reported_and_not_judged(self):
        """No threshold: the message must carry the number so the reader can
        decide, and must not decide for them."""
        self.board([self.row("TASK-001", "review")])
        self.events_to_review(ts="2026-08-01T10:00:00")
        msg = next(f["message"] for f in self.run_lint()["findings"]
                   if f["rule"] == "review-with-no-verdict")
        self.assertIn("day(s) ago", msg)
        self.assertIn("only you can tell", msg)

    def test_with_no_event_the_age_is_unknown_not_zero(self):
        """Silence about when is not the same as "today", and a row whose move
        predates the event log must not be reported as fresh."""
        self.board([self.row("TASK-001", "review")])
        msg = next(f["message"] for f in self.run_lint()["findings"]
                   if f["rule"] == "review-with-no-verdict")
        self.assertIn("unknown time", msg)


class TestTheRungIsRunNotClaimed(ReviewLintCase):
    def test_a_v4_close_with_no_verdict_anywhere_is_reported(self):
        self.board([self.row("TASK-001", "done")])
        self.assertIn("v4-close-without-verdict", self.rules())

    def test_a_v4_close_with_a_verdict_is_clean(self):
        self.board([self.row("TASK-001", "done")])
        self.evidence("TASK-001-review.md", verdict("TASK-001"))
        self.assertEqual(self.rules(), [])

    def test_a_lower_rung_close_is_not_asked_for_one(self):
        """V4 is the rung that means *a fresh reviewer ran*. V2 and V3 make no
        such claim, and demanding a review document for them would turn the
        check into noise everyone learns to skip."""
        self.board([self.row("TASK-001", "done", rung="V2")])
        self.assertEqual(self.rules(), [])

    def test_a_close_that_left_the_board_is_still_checked(self):
        """`perry-task done` REMOVES the row. A board-only scan measures an
        empty set on any project that uses the tool — the trap
        `check_verification` documents and this check would otherwise repeat."""
        self.board([])
        (self.dir / ".perry" / "events.jsonl").write_text(json.dumps(
            {"event": "done", "task": "TASK-009", "rung": "V4"}) + "\n")
        self.assertIn("v4-close-without-verdict", self.rules())


class TestTheBlockItself(ReviewLintCase):
    def setUp(self):
        super().setUp()
        self.board([self.row("TASK-001", "done")])

    def test_a_missing_required_key_is_named(self):
        text = verdict("TASK-001").replace("not-checked: Windows paths\n", "")
        self.evidence("TASK-001-review.md", text)
        findings = self.run_lint()["findings"]
        self.assertIn("verdict-malformed", [f["rule"] for f in findings])
        self.assertIn("not-checked", " ".join(f["message"] for f in findings))

    def test_a_result_that_is_neither_word_is_refused(self):
        self.evidence("TASK-001-review.md",
                      verdict("TASK-001", "MOSTLY PASS"))
        self.assertIn("verdict-malformed", self.rules())

    def test_a_fail_with_no_proof_is_a_suspicion(self):
        self.evidence("TASK-001-review.md",
                      verdict("TASK-001", "FAIL", proof=""))
        self.assertIn("fail-without-proof", self.rules())

    def test_a_pass_needs_no_proof_line(self):
        """A PASS's evidence is its `checked:` line. Requiring `proof:` for a
        PASS would ask a reviewer to point at the absence of something."""
        self.evidence("TASK-001-review.md", verdict("TASK-001", proof=""))
        self.assertEqual(self.rules(), [])

    def test_one_round_over_five_rows_emits_five_verdicts(self):
        """The multi-row round is where the old prose format failed hardest:
        one document, five rows, one verdict word, and which row it applied to
        was recoverable only by reading."""
        self.board([self.row(f"TASK-00{n}", "done") for n in range(1, 6)])
        self.evidence("round.md", "\n".join(
            verdict(f"TASK-00{n}") for n in range(1, 6)))
        self.assertEqual(self.rules(), [])
        self.assertEqual(self.run_lint()["verdict_blocks"], 5)


class TestTheParserItself(unittest.TestCase):
    """Asserted on the parsed VALUE, because asserting on findings did not work.

    The first version of the multi-line test fed a block with a wrapped
    `checked:` and asserted the lint reported nothing. **It passed with the
    continuation handling deleted** — dropping the second line leaves
    `checked: the first clause,` behind, which is still non-empty, so no
    finding fires either way. A test whose subject can be removed without
    turning it red is not a test, and this file's whole reason for existing is
    that class of defect.
    """

    def setUp(self):
        spec = importlib.util.spec_from_loader(
            "perry_lint",
            importlib.machinery.SourceFileLoader("perry_lint", str(LINT)))
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_a_wrapped_field_keeps_both_lines(self):
        """`checked:` runs to several lines routinely. A parser that ends the
        field at the newline silently truncates the one line whose job is to
        tell the next round what it need not redo."""
        blocks = self.mod.parse_verdicts(
            "=== VERDICT ===\n"
            "task: TASK-001\nrung: V4\nresult: PASS\n"
            "criteria: evidence/2026-08/TASK-001-spec.md\n"
            "checked: the first clause,\n"
            "         and the second one\n"
            "not-checked: nothing\n"
            "=== END VERDICT ===\n")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0]["checked"],
                         "the first clause, and the second one")

    def test_a_repeated_key_keeps_the_last_value(self):
        """A corrected verdict is written by writing the line again. Keeping
        the first would read the correction back as the thing it corrected."""
        blocks = self.mod.parse_verdicts(
            "=== VERDICT ===\nresult: FAIL\nresult: PASS\n=== END VERDICT ===\n")
        self.assertEqual(blocks[0][0]["result"], "PASS")

    def test_the_line_number_points_at_the_block(self):
        blocks = self.mod.parse_verdicts(
            "intro\n\n=== VERDICT ===\nresult: PASS\n=== END VERDICT ===\n")
        self.assertEqual(blocks[0][1], 3)


class TestItReportsHowMuchItSaw(ReviewLintCase):
    def test_the_block_count_is_published_at_zero_findings(self):
        """`--knowledge` prints its card count for this reason: "0 violations"
        over 0 verdicts is trivially true, and a number that cannot tell "the
        convention holds" from "nobody has written one" is not a measurement."""
        self.board([self.row("TASK-001", "done")])
        self.evidence("TASK-001-review.md", verdict("TASK-001"))
        out = self.run_lint()
        self.assertEqual(out["count"], 0)
        self.assertEqual(out["verdict_blocks"], 1)


class TestItIsOptIn(unittest.TestCase):
    def test_the_default_pass_does_not_run_it(self):
        """A project that predates the convention has its reviews in prose.
        Promoting those to errors in the default pass would retroactively
        condemn every review it ever ran — the same reason `--verification` is
        opt-in."""
        proc = subprocess.run(
            [sys.executable, str(LINT), "--json"],
            capture_output=True, text=True, cwd=ROOT)
        rules = {f["rule"] for f in json.loads(proc.stdout).get("findings", [])}
        for r in ("v4-close-without-verdict", "fail-verdict-left-at-review",
                  "verdict-malformed", "fail-without-proof"):
            self.assertNotIn(r, rules)




class TestTwoFailsIsADecisionNotAThirdRound(ReviewLintCase):
    """The most expensive thing this board does, and nothing asked it to stop.

    Measured on Perry's own state: 20 rows entered V4, **74 rounds** were
    burned, 10 rows needed three or more, and TASK-050 and TASK-249 each
    reached round 11. TASK-095 FAILed five times and the escalation that
    finally ended it (USER-905) was filed BY HAND at round 5 — after which the
    user picked a principle and round 6 PASSed.

    All five of those FAILs read the same in the journal: *two situations
    answered as one, one step to the left of the last*. The rounds after the
    second were not finding new defects; they were re-deriving one principle
    differently. The agent could name that shape at round 2. Nothing asked it
    to stop there, so this is the thing that asks.
    """

    def two_fails(self, tid="TASK-500", status="in_progress"):
        self.board([self.row(tid, status)])
        self.evidence(f"{tid}-r1.md", verdict(tid, "FAIL"))
        self.evidence(f"{tid}-r2.md", verdict(tid, "FAIL"))
        return tid

    def test_two_fails_and_no_pass_is_reported(self):
        self.two_fails()
        self.assertIn("review-rounds-exhausted", self.rules())

    def test_one_fail_is_not(self):
        self.board([self.row("TASK-500", "in_progress")])
        self.evidence("TASK-500-r1.md", verdict("TASK-500", "FAIL"))
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_a_pass_anywhere_ends_the_question(self):
        tid = self.two_fails()
        self.evidence(f"{tid}-r3.md", verdict(tid, "PASS"))
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_an_open_ask_blocking_the_row_clears_it(self):
        """The out is the one TASK-095 took: escalate, do not re-round."""
        tid = self.two_fails()
        (self.dir / "asks.jsonl").write_text(json.dumps({
            "id": "USER-905", "needed": "pick a principle",
            "blocks": tid, "answered": False}) + "\n")
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_an_ANSWERED_ask_does_not_clear_it(self):
        """An answered ask is a decision already taken; it cannot license the
        next unexamined round the way a pending one licenses waiting."""
        tid = self.two_fails()
        (self.dir / "asks.jsonl").write_text(json.dumps({
            "id": "USER-905", "needed": "pick a principle",
            "blocks": tid, "answered": True}) + "\n")
        self.assertIn("review-rounds-exhausted", self.rules())

    def test_an_ask_blocking_a_DIFFERENT_row_does_not_clear_it(self):
        tid = self.two_fails()
        (self.dir / "asks.jsonl").write_text(json.dumps({
            "id": "USER-905", "needed": "x",
            "blocks": "TASK-999", "answered": False}) + "\n")
        self.assertIn("review-rounds-exhausted", self.rules())

    def test_a_closed_row_is_history_not_a_worklist(self):
        """The first cut reported five rows and four were long closed —
        TASK-037/TASK-203 `done`, TASK-042 `dropped`, TASK-050 `done` after
        eleven rounds. `done` removes the row, so a row absent from the board
        can receive no next round and this check has nothing to say about it.
        """
        self.board([])                       # the row has closed and left
        self.evidence("TASK-500-r1.md", verdict("TASK-500", "FAIL"))
        self.evidence("TASK-500-r2.md", verdict("TASK-500", "FAIL"))
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_it_names_every_failing_round_not_just_the_last(self):
        tid = self.two_fails()
        msg = next(f["message"] for f in self.run_lint()["findings"]
                   if f["rule"] == "review-rounds-exhausted")
        self.assertIn(f"{tid}-r1.md", msg)
        self.assertIn(f"{tid}-r2.md", msg)

    def test_it_does_not_claim_a_round_NUMBER(self):
        """`round` was measured and refused a bearer — it lives only in some
        filenames (`bin/perry-task.evidence_relations`). The FAIL count and the
        filename numbering disagree on this repo's own TASK-067, whose two
        FAILs sit in files named round3 and round4, so a message asserting
        'round 3 is next' would be wrong on the row that prompted the check.
        """
        tid = self.two_fails()
        msg = next(f["message"] for f in self.run_lint()["findings"]
                   if f["rule"] == "review-rounds-exhausted")
        self.assertIn("Another round", msg)
        self.assertNotRegex(msg, r"Round \d")


class TestTheCountIsByCriterionNotByBlock(ReviewLintCase):
    """Two FAILs are two FAILs — but only if they were the same KIND of FAIL.

    The check above counted verdict BLOCKS. A block is not a unit of failure;
    the criterion is. Measured on TASK-360, 2026-09-10: its two FAILs were
    round 4 on criterion 2 — `--help` from a non-first argument position, whose
    worst outcome is exit 2 and a line naming `--help` — and round 6 on
    criterion 3, a positional accepted, dropped and reported as success.
    `DESIGN-016-spec.md § What a criterion may do to a row` grades those **ROW**
    and **FAIL**. By the bar that now governs the row, it has failed ONCE, and
    the guard was charging it for a round it never spent.

    **This is not the guard being loosened and these tests exist to hold that
    line.** It fired correctly on TASK-362, whose two FAILs were criteria 5 and
    13, both FAIL-grade, and the ask it forced (USER-924) closed a whole
    category in one round. Only a FAIL that SAYS it was charged against a
    ROW-grade criterion stops counting. Silence counts. A typo counts. That is
    `test_an_ungraded_fail_counts_because_undeterminable_is_conservative`, and
    it is the one that matters, because 62 of the 62 FAIL blocks in this
    repository's corpus carry no `grade:` at all.
    """

    def fails(self, *grades, tid="TASK-500", status="in_progress"):
        self.board([self.row(tid, status)])
        for n, g in enumerate(grades, 1):
            self.evidence(f"{tid}-r{n}.md", verdict(tid, "FAIL", grade=g))
        return tid

    def msg(self):
        return next(f["message"] for f in self.run_lint()["findings"]
                    if f["rule"] == "review-rounds-exhausted")

    # ── the three shapes ────────────────────────────────────────────────

    def test_two_FAIL_grade_fails_exhaust_the_row(self):
        """TASK-362's shape. The guard must still fire, unchanged."""
        self.fails("FAIL — criterion 5", "FAIL — criterion 13")
        self.assertIn("review-rounds-exhausted", self.rules())

    def test_two_ROW_grade_fails_do_not_exhaust_the_row(self):
        """Two defects that fail no row are two rows filed, not two rounds
        spent. `review.md § 0` is the test and nobody was applying it per
        criterion."""
        self.fails("ROW — criterion 2b", "ROW — criterion 11")
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_one_of_each_is_one_failure_the_TASK_360_shape(self):
        """The row the spec was written on: round 4 ROW-grade, round 6
        FAIL-grade. One FAIL under the limit of two."""
        self.fails("ROW — criterion 2b", "FAIL — criterion 3")
        self.assertNotIn("review-rounds-exhausted", self.rules())

    # ── undeterminable is conservative ──────────────────────────────────

    def test_an_ungraded_fail_counts_because_undeterminable_is_conservative(self):
        """62 of 62 existing FAIL blocks carry no `grade:`. Reading silence as
        ROW would un-exhaust rows nobody regraded — § 6 loosened by an accident
        of when § 1 started refusing a round without written criteria."""
        self.fails(None, None)
        self.assertIn("review-rounds-exhausted", self.rules())

    def test_one_ROW_grade_and_one_ungraded_still_leaves_one_counted(self):
        self.fails("ROW — criterion 2b", None)
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_an_unreadable_grade_counts_and_is_reported_malformed(self):
        """`grade: row-grade` is a typo, not a grade. It must not read as ROW
        by prefix — that would quiet the guard by accident, the one direction
        this may not move — and the reviewer who wrote it must be told."""
        self.fails("row-grade", "row-grade")
        rules = self.rules()
        self.assertIn("review-rounds-exhausted", rules)
        self.assertIn("verdict-malformed", rules)

    def test_a_grade_that_is_neither_word_counts(self):
        self.fails("MAYBE", "PROBABLY")
        self.assertIn("review-rounds-exhausted", self.rules())

    # ── what the finding says ───────────────────────────────────────────

    def test_the_finding_reports_how_many_it_counted_by_default(self):
        """Requirement 3 of the spec: undeterminable is a STATED outcome. A
        count that silently absorbs the blocks it could not read is the lossy
        numerator this row was opened on, one level up."""
        self.fails(None, None)
        self.assertIn("undeterminable", self.msg())
        self.assertIn("2 of the 2 counted", self.msg())

    def test_the_finding_names_the_ROW_grade_fails_it_did_not_count(self):
        tid = self.fails("ROW — criterion 2b", "FAIL — c3", "FAIL — c7")
        msg = self.msg()
        self.assertIn("NOT counted", msg)
        self.assertIn(f"{tid}-r1.md", msg)       # the ROW-grade one, named
        self.assertIn("has FAILed 2 V4 rounds", msg)

    def test_the_named_rounds_are_the_charged_ones_only(self):
        """`where` used to list every FAIL block. A message that cites a round
        it did not count is a message that cannot be checked against itself."""
        tid = self.fails("ROW — criterion 2b", "FAIL — c3", "FAIL — c7")
        head = self.msg().split("Another round")[0]
        self.assertNotIn(f"{tid}-r1.md", head)
        self.assertIn(f"{tid}-r2.md", head)
        self.assertIn(f"{tid}-r3.md", head)

    def test_a_fully_graded_row_says_nothing_about_undeterminable(self):
        self.fails("FAIL — criterion 5", "FAIL — criterion 13")
        self.assertNotIn("undeterminable", self.msg())

    # ── the out is unchanged ────────────────────────────────────────────

    def test_an_open_ask_still_clears_a_FAIL_graded_row(self):
        """`review.md § 6`'s escalation is untouched by this row. The finding
        is cleared by the ask, never by the grade."""
        tid = self.fails("FAIL — criterion 5", "FAIL — criterion 13")
        (self.dir / "asks.jsonl").write_text(json.dumps({
            "id": "USER-924", "needed": "pick a principle",
            "blocks": tid, "answered": False}) + "\n")
        self.assertNotIn("review-rounds-exhausted", self.rules())

    def test_a_PASS_still_ends_the_question_whatever_the_grades(self):
        tid = self.fails("FAIL — criterion 5", "FAIL — criterion 13")
        self.evidence(f"{tid}-r3.md", verdict(tid, "PASS"))
        self.assertNotIn("review-rounds-exhausted", self.rules())

    # ── the resolver, in-process ────────────────────────────────────────

    def test_fail_grade_reads_the_first_token_and_ignores_the_criterion(self):
        g = lint_module().fail_grade
        self.assertEqual(g({"grade": "ROW — criterion 2b, `--help` anywhere"}),
                         "ROW")
        self.assertEqual(g({"grade": "FAIL, criterion 3"}), "FAIL")
        self.assertEqual(g({"grade": "row"}), "ROW")

    def test_fail_grade_returns_None_for_everything_it_cannot_read(self):
        g = lint_module().fail_grade
        for raw in ("", "   ", "row-grade", "ROWS", "2b", "— ROW", "PASS"):
            self.assertIsNone(g({"grade": raw}), raw)
        self.assertIsNone(g({}))


class TestTheRoundLimitIsDeclaredNotHardcoded(ReviewLintCase):
    """Two is a measured default, not a law, and a project may disagree.

    Same precedence `perry-conform § gate_mode` established for `Conformance
    gate`: env beats the project's declared field beats the shipped default in
    `schema § thresholds`. The finding names its source, because a gate that
    stops work without saying which register set it is one nobody can argue
    with — and this one stops the third round, which is exactly when somebody
    will want to.

    **The arithmetic is unit-tested and the wiring is spawned once.** These
    used to be one linter subprocess each; see `lint_module`.
    """

    def setUp(self):
        super().setUp()
        self.tid = "TASK-500"
        self.board([self.row(self.tid, "in_progress")])
        for n in (1, 2):
            self.evidence(f"{self.tid}-r{n}.md", verdict(self.tid, "FAIL"))
        self.M = lint_module()
        self.M.SCHEMA_THRESHOLDS.update(json.loads(
            (ROOT / "schema" / "state-schema.json").read_text())["thresholds"])

    def store(self, value, key="review_rounds_before_escalation"):
        (self.dir / ".perry" / "config.jsonl").write_text(json.dumps({
            "kind": "setting", "key": key,
            "label": "Review rounds before escalation",
            "value": value}) + "\n")

    def stray_markdown(self, body):
        """A `.perry/config.md` nothing should read. ADR-019 deleted the file;
        a leftover copy in a working tree is inert, and that is the assertion.
        Writing one anyway is what tells the fallback's REMOVAL apart from the
        fallback merely going unexercised."""
        (self.dir / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n" + body + "\n")

    def resolved(self, **env):
        with mock.patch.dict(os.environ, env, clear=False):
            for k, v in list(env.items()):
                if v is None:
                    os.environ.pop(k, None)
            return self.M.rounds_before_escalation(self.dir)

    # ── the arithmetic, in-process ───────────────────────────────────────

    def test_the_shipped_default_is_the_schema_value(self):
        schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
        declared = schema["thresholds"][
            "review_fail_rounds_before_escalation"]["value"]
        self.assertEqual(declared, 2)
        self.assertEqual(self.resolved(), (2, "schema § thresholds"))

    def test_env_wins_and_is_named(self):
        self.assertEqual(self.resolved(PERRY_REVIEW_ROUNDS="5"),
                         (5, "PERRY_REVIEW_ROUNDS"))

    def test_the_project_may_declare_it_in_the_store(self):
        self.store("5")
        self.assertEqual(self.resolved(), (5, ".perry/config.jsonl"))

    def test_a_stray_markdown_is_not_a_register_when_there_is_no_store(self):
        """The fallback ADR-019 removed. With no store at all, a
        `.perry/config.md` declaring 5 answers nothing and the schema does."""
        self.stray_markdown("- Review rounds before escalation: 5")
        self.assertEqual(self.resolved(), (2, "schema § thresholds"))

    def test_a_stray_markdown_does_not_compete_with_the_store(self):
        self.store("5")
        self.stray_markdown("- Review rounds before escalation: 9")
        self.assertEqual(self.resolved(), (5, ".perry/config.jsonl"))

    def test_a_store_without_the_key_does_NOT_fall_through_to_the_markdown(self):
        """A key the store does not carry is a setting the project does not
        declare, and there is no second register to ask."""
        self.store("English", key="document_language")
        self.stray_markdown("- Review rounds before escalation: 5")
        self.assertEqual(self.resolved(), (2, "schema § thresholds"))

    def test_env_beats_the_declared_field(self):
        self.store("5")
        self.assertEqual(self.resolved(PERRY_REVIEW_ROUNDS="3"),
                         (3, "PERRY_REVIEW_ROUNDS"))

    def test_a_non_numeric_declaration_falls_back_rather_than_crashing(self):
        self.store("lots")
        self.assertEqual(self.resolved(), (2, "schema § thresholds"))

    def test_the_resolver_never_returns_a_limit_below_one(self):
        """The invariant the comparison relies on, pinned where it is made.

        `len(fails) < limit` inverts at 0: a limit of 0 would fire the finding
        on every live row carrying any verdict block, INCLUDING rows with zero
        FAILs. The caller carries no second guard — two implementations of one
        rule is the defect this repository finds most often — so this is the
        only thing standing between a declared 0 and that inversion. Asserted
        across every register that can set it, because a guard on one branch
        is not a guard on the others.
        """
        cases = [("env zero", {"PERRY_REVIEW_ROUNDS": "0"}, None),
                 ("env negative", {"PERRY_REVIEW_ROUNDS": "-3"}, None),
                 ("store zero", {}, "0"),
                 ("store junk", {}, "none")]
        for where, env, store in cases:
            with self.subTest(where=where):
                cfg = self.dir / ".perry" / "config.jsonl"
                cfg.unlink(missing_ok=True)
                if store is not None:
                    self.store(store)
                limit, src = self.resolved(**env)
                self.assertGreaterEqual(limit, 1)
                self.assertEqual((limit, src), (2, "schema § thresholds"))

    def test_a_schema_declaring_zero_is_refused_as_well(self):
        """The third register, and the one the docstring above claims."""
        self.M.SCHEMA_THRESHOLDS["review_fail_rounds_before_escalation"] = {
            "value": 0}
        self.assertEqual(self.resolved(), (2, "built-in default"))

    # ── the wiring, spawned ──────────────────────────────────────────────

    def test_the_limit_reaches_the_finding_and_is_named_in_it(self):
        """One end-to-end spawn: the resolver's answer has to arrive at the
        message, or every test above is checking arithmetic nothing reads."""
        import os as _os
        proc = subprocess.run(
            [sys.executable, str(LINT), "--reviews", "--root", str(self.dir),
             "--state-root", ".", "--json"],
            capture_output=True, text=True, cwd=ROOT,
            env={**_os.environ, "PERRY_REVIEW_ROUNDS": "3"})
        hit = [f for f in json.loads(proc.stdout)["findings"]
               if f["rule"] == "review-rounds-exhausted"]
        self.assertEqual(hit, [], "limit 3 must silence a row with 2 FAILs")

        proc = subprocess.run(
            [sys.executable, str(LINT), "--reviews", "--root", str(self.dir),
             "--state-root", ".", "--json"],
            capture_output=True, text=True, cwd=ROOT,
            env={**_os.environ, "PERRY_REVIEW_ROUNDS": "2"})
        hit = [f for f in json.loads(proc.stdout)["findings"]
               if f["rule"] == "review-rounds-exhausted"]
        self.assertEqual(len(hit), 1)
        self.assertIn("the limit is 2 (from PERRY_REVIEW_ROUNDS)",
                      hit[0]["message"])


class ExhibitCase(ReviewLintCase):
    """Shared setup for the two pre-check findings.

    `review.md § 2 · What V4 does not judge`. Both of these were found by a
    fresh-context reviewer, at a full round each, when a regex knew: "three
    citations point at a file the branch does not carry", "a claimed filing,
    on the branch, that is not there". The round is the most expensive place
    on this board to learn either one.
    """

    def open_row(self, tid="TASK-001"):
        self.board([self.row(tid, "review")])

    def closed_row(self, tid="TASK-001"):
        self.board([self.row(tid, "done")])
        (self.dir / ".perry" / "events.jsonl").write_text(
            json.dumps({"event": "done", "task": tid, "rung": "V4"}) + "\n")

    def block(self, task="TASK-001", criteria="evidence/2026-08/spec.md",
              proof="", result="FAIL"):
        return (f"=== VERDICT ===\ntask: {task}\nrung: V4\n"
                f"result: {result}\ncriteria: {criteria}\n"
                f"checked: a thing\nnot-checked: another\n"
                f"proof: {proof or 'evidence/2026-08/spec.md:1 the line'}\n"
                f"=== END VERDICT ===\n")

    def spec(self, name="spec.md", bound=True):
        body = "# criteria\n"
        if bound:
            body += "\n## Bound\nEnumeration: ls bin/\nSize: 1\nRemainder: none\n"
        (self.dir / "evidence" / "2026-08" / name).write_text(body)


class TestTheExhibitIsCheckedBeforeTheRound(ExhibitCase):
    """`citation-not-on-branch` — a path the branch does not carry.

    Reported on OPEN rows only. A closed row's exhibit cannot be re-filed, so
    reporting it condemns retroactively — the thing this whole mode's docstring
    refuses to do.
    """

    def test_a_criteria_path_the_branch_does_not_carry_is_reported(self):
        self.open_row()
        self.evidence("r.md", self.block(), make_criteria=False)
        self.assertIn("citation-not-on-branch", self.rules())

    def test_a_criteria_path_that_exists_is_not(self):
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(), make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_proof_path_the_branch_does_not_carry_is_reported(self):
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(proof="evidence/2026-08/gone.md:4 x"),
                      make_criteria=False)
        hit = [f for f in self.run_lint()["findings"]
               if f["rule"] == "citation-not-on-branch"]
        self.assertEqual(len(hit), 1)
        self.assertIn("`proof:`", hit[0]["message"])

    def test_a_closed_row_is_not_condemned_retroactively(self):
        self.closed_row()
        self.evidence("r.md", self.block(result="PASS"), make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    # ── the exclusions, each one a token this board's own reviews produced ──

    def test_a_bare_filename_is_a_mention_not_a_citation(self):
        """`checked: tables.py` names a file, not a path, and the repository
        carries `viewer/tables.py`. Reporting it taught the check to report
        correct prose, which is how a guard gets switched off (§ 1)."""
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(proof="tables.py:12 the fold"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_command_name_is_not_a_path(self):
        """`/pmo` and `/architecture` are commands. The first version split on
        `/`, got an empty head, and `self.dir / ""` is a directory that always
        exists — so every command name in a proof line was a broken path."""
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(proof="/pmo /architecture are routed"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_possessive_is_stripped(self):
        self.open_row()
        self.spec()
        self.evidence(
            "r.md", self.block(proof="evidence/2026-08/spec.md's first line"),
            make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_trailing_paren_is_stripped(self):
        self.open_row()
        self.spec()
        self.evidence("r.md",
                      self.block(proof="evidence/2026-08/spec.md:1) the line"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_line_range_resolves(self):
        self.open_row()
        self.spec()
        self.evidence("r.md",
                      self.block(proof="evidence/2026-08/spec.md:1-9 the line"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_two_line_refs_on_one_path_is_prose(self):
        """`bin/perry-goals:927/:908/` is a sentence about two lines. A `:`
        surviving the suffix strip means the token is not a path."""
        self.open_row()
        self.spec()
        # No trailing `/`: a token ending in one is already stopped by the
        # empty-last-segment rule, so the first version of this test never
        # reached the clause it names. Mutation M8.
        self.evidence("r.md",
                      self.block(proof="evidence/2026-08:927/:908 both"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_scratch_copy_is_the_convention_working(self):
        """`review-constraints.md` REQUIRES destructive checks to run on a
        copy. Citing the copy is the reviewer obeying the rule."""
        self.open_row()
        self.spec()
        # The exclusion is only REACHED when `scratchpad/` is a real directory
        # — otherwise the head-is-a-directory rule stops the token first and
        # this test passes without testing anything. Mutation M7.
        (self.dir / "scratchpad" / "probe").mkdir(parents=True)
        self.evidence("r.md",
                      self.block(proof="scratchpad/probe/rj.py:4 reproduced"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_trailing_count_is_not_a_path(self):
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(proof="evidence/3 of them escape"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_colon_inside_a_path_is_prose(self):
        """A `:` that SURVIVES the line-suffix strip means the token is a
        sentence about a line, not a path — `bin/perry-goals:927/:908` was
        written on this board. The token must keep a real last segment or an
        earlier rule catches it first and this test proves nothing (M8)."""
        self.open_row()
        self.spec()
        self.evidence("r.md",
                      self.block(proof="evidence/2026-08:927/notes.md and"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_directory_fragment_is_not_a_missing_file(self):
        """A token ending in `/` names a folder in prose. Without the
        empty-last-segment rule it is looked up whole, misses, and is reported
        as a broken citation (M5)."""
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(proof="evidence/gone/ was swept"),
                      make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_a_bracketed_link_fragment_is_prose(self):
        self.open_row()
        self.spec()
        self.evidence(
            "r.md",
            self.block(proof="ADR-007](decisions/ADR-007-probe.md is cited"),
            make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())

    def test_checked_is_prose_and_is_not_mined(self):
        """`checked:` is a sentence by design — the convention's own example is
        "guarantees 1,2,4,5 on gimegime-pmo (365→380 ids)". Mining it for paths
        is guessing, and guessing is what makes a check unusable."""
        self.open_row()
        self.spec()
        text = self.block().replace(
            "checked: a thing", "checked: evidence/2026-08/never-existed.md")
        self.evidence("r.md", text, make_criteria=False)
        self.assertNotIn("citation-not-on-branch", self.rules())


class TestTheCriteriaMustBeBounded(ExhibitCase):
    """`criteria-unbounded` — no `## Bound`, so the round has no last element.

    TASK-050 ran **eleven** rounds against "no reader resolves a header cell by
    its own rule", a universal negative over a live tree. Rounds 8, 9 and 10
    each found a real escape — a pruned corpus, a one-line alias, a dict key —
    and round 11 PASSed on `a measured remainder of 8 out of 76`. It ended on
    the round the criterion became decidable, not on the round the last hole
    closed. `review.md § 1`.
    """

    def test_a_criteria_file_with_no_bound_is_reported(self):
        self.open_row()
        self.spec(bound=False)
        self.evidence("r.md", self.block(), make_criteria=False)
        self.assertIn("criteria-unbounded", self.rules())

    def test_a_criteria_file_with_a_bound_is_not(self):
        self.open_row()
        self.spec(bound=True)
        self.evidence("r.md", self.block(), make_criteria=False)
        self.assertNotIn("criteria-unbounded", self.rules())

    def test_a_nested_bound_still_counts(self):
        """The requirement is that the bound is WRITTEN DOWN, not where. A spec
        that puts it under a section heading has satisfied § 1."""
        self.open_row()
        (self.dir / "evidence" / "2026-08" / "spec.md").write_text(
            "# criteria\n\n## What must be true\n\n### Bound\nSize: 4\n")
        self.evidence("r.md", self.block(), make_criteria=False)
        self.assertNotIn("criteria-unbounded", self.rules())

    def test_a_closed_row_is_not_condemned_retroactively(self):
        self.closed_row()
        self.spec(bound=False)
        self.evidence("r.md", self.block(result="PASS"), make_criteria=False)
        self.assertNotIn("criteria-unbounded", self.rules())

    def test_a_missing_criteria_file_is_one_finding_not_two(self):
        """An absent file cannot be read for a bound. Reporting both would
        make the fix look like two problems when it is one."""
        self.open_row()
        self.evidence("r.md", self.block(), make_criteria=False)
        rules = self.rules()
        self.assertIn("citation-not-on-branch", rules)
        self.assertNotIn("criteria-unbounded", rules)


class TestStrictCanStopADispatch(ExhibitCase):
    """`--reviews --strict` exits non-zero, or the pre-check cannot gate.

    `review.md § 2` tells the dispatcher to run this before spawning the
    agent. A mode that always returns 0 makes that one more rule stated in
    prose that nothing implements — which is this repository's own most-found
    defect and the reason `review.md` exists at all.
    """

    def run_strict(self):
        return subprocess.run(
            [sys.executable, str(LINT), "--reviews", "--root", str(self.dir),
             "--state-root", ".", "--strict", "--quiet"],
            capture_output=True, text=True, cwd=ROOT).returncode

    def test_strict_is_red_when_the_exhibit_is(self):
        self.open_row()
        self.evidence("r.md", self.block(), make_criteria=False)
        self.assertEqual(self.run_strict(), 1)

    def test_strict_is_green_when_it_is_clean(self):
        self.open_row()
        self.spec()
        self.evidence("r.md", self.block(result="PASS"), make_criteria=False)
        self.assertEqual(self.run_strict(), 0)

    def test_without_strict_it_stays_advisory(self):
        """The DEFAULT stays 0 on findings. A project that predates the
        convention has prose reviews, and promoting those to a failing exit
        would condemn every round it ever ran."""
        self.open_row()
        self.evidence("r.md", self.block(), make_criteria=False)
        proc = subprocess.run(
            [sys.executable, str(LINT), "--reviews", "--root", str(self.dir),
             "--state-root", ".", "--quiet"],
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
