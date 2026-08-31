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
checked: {checked}
not-checked: {not_checked}
{proof}=== END VERDICT ===
"""


def verdict(task, result="PASS", checked="the refusal path on a copy",
            not_checked="Windows paths", proof="bin/x.py:12 the guard is absent"):
    return VERDICT.format(
        task=task, result=result, checked=checked, not_checked=not_checked,
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

    def markdown(self, body):
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

    def test_the_markdown_is_the_fallback_when_there_is_no_store(self):
        self.markdown("- Review rounds before escalation: 5")
        self.assertEqual(self.resolved(), (5, ".perry/config.md"))

    def test_the_two_registers_are_named_apart(self):
        """Reporting a store value as `.perry/config.md` sends the reader to
        edit a projection instead of the register that answered."""
        self.store("5")
        self.markdown("- Review rounds before escalation: 9")
        self.assertEqual(self.resolved(), (5, ".perry/config.jsonl"))

    def test_a_store_without_the_key_does_NOT_fall_through_to_the_markdown(self):
        """The store is derived from the preamble, so a key it does not carry
        is a line the file does not have. Falling through would put one
        setting in two registers — the drift TASK-233 removed."""
        self.store("English", key="document_language")
        self.markdown("- Review rounds before escalation: 5")
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


if __name__ == "__main__":
    unittest.main()
