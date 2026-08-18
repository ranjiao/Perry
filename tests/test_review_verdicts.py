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
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

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
checked: {checked}
not-checked: {not_checked}
{proof}=== END VERDICT ===
"""


def verdict(task, result="PASS", checked="the refusal path on a copy",
            not_checked="Windows paths", proof="bin/x.py:12 the guard is absent"):
    return VERDICT.format(
        task=task, result=result, checked=checked, not_checked=not_checked,
        proof=f"proof: {proof}\n" if proof else "")


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

    def evidence(self, name, text):
        (self.dir / "evidence" / "2026-08" / name).write_text(text)

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


if __name__ == "__main__":
    unittest.main()
