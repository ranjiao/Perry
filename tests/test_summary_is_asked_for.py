"""TASK-325: the summary field is asked for at the writer and reported at the linter.

The defect this guards is not that `summary` was missing — it has existed since
contract 1.11, with two writers, three readers and a definition row. It is that
**nothing ever asked for it**, and it reached 25 of 114 open rows on Perry's own
board. So the tests below are mostly about the ASKING: a refusal that fires, a
report that fires, and the one place both read their rule from.

**Every predicate here is structural.** There is no test that a summary reads
well, because there is no such check — twice on 2026-09-02 a guard on this
project tried to recognise bad English and lost, and
`TestTheCheckDoesNotJudgeLanguage` pins that this one does not try.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_store_is_the_write_target import Project

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "bin" / "perry-task"
LINT = ROOT / "bin" / "perry-lint"

sys.path.insert(0, str(ROOT / "bin"))
import lib  # noqa: E402


#: A summary that passes every structural rule. Used as the CONTROL throughout:
#: a check that flags this is useless no matter what else it catches.
GOOD = ("Perry ships two opposite orderings of the phase-close pipeline. "
        "Nothing picks one, so whoever runs it picks by which page they read.")


def add_raw(root: Path, *argv: str) -> subprocess.CompletedProcess:
    """`add` with NOTHING injected — the harness shims inject `--summary`."""
    return subprocess.run(
        [sys.executable, str(TASK), "add", *argv, "--root", str(root),
         "--json"], capture_output=True, text=True)


def lint(root: Path, *argv: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(LINT), "--root", str(root), *argv],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


class TestAddRefusesWithoutASummary(unittest.TestCase):
    """Part 1 of TASK-325: `add` asks, and refuses when it is not answered.

    A HARD gate rather than an advisory, and the reason is measured rather than
    preferred: `--summary` was an OPTIONAL flag on this subcommand from
    contract 1.11 — nothing refused, nothing reported, no procedure mentioned
    it — and it reached 25 of 114 open rows. An advisory here would re-run the
    experiment that produced the defect.
    """

    def setUp(self):
        self.project = Project(self)

    def test_add_refuses_when_summary_is_absent(self):
        r = add_raw(self.project.root, "--title", "a title",
                    "--deliverable", "d", "--verification", "v")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("--summary is required", r.stdout + r.stderr)
        # And it wrote nothing. A refusal that half-writes is worse than none.
        self.assertFalse((self.project.root / "tasks.jsonl").exists()
                         and json.loads(
                             (self.project.root / "tasks.jsonl")
                             .read_text().strip().split("\n")[0] or "{}"
                         ).get("title") == "a title")

    def test_add_refuses_a_summary_that_is_only_the_title_again(self):
        r = add_raw(self.project.root, "--title", "the parser drops zh headers",
                    "--summary", "The parser drops zh headers.",
                    "--deliverable", "d", "--verification", "v")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("restates the title", r.stdout + r.stderr)

    def test_add_accepts_a_fragment_and_a_value_with_no_sentence(self):
        """The inverse of the test that stood here until TASK-330.

        Until 2026-09-03 `add` refused both of these — the first on
        `summary-is-a-fragment` ("word(s)"), the second on
        `summary-has-no-sentence`. The user removed both rules: whether prose
        reads like prose is the writing agent's responsibility, not a check's.
        Kept as an assertion rather than deleted, because the writer is where
        a reverted removal would actually bite a user.

        Asserted on `"refused"` rather than on the two old refusal strings:
        the second fixture literally CONTAINS the words "no sentence", so a
        `assertNotIn("no sentence", ...)` fires on the accepted payload
        echoing the summary back and reports a pass as a failure. Found by
        this row's own mutation round.
        """
        for summary in ("It broke.", "a value carrying no sentence terminator"):
            with self.subTest(summary=summary):
                r = add_raw(self.project.root, "--title", "a title",
                            "--summary", summary,
                            "--deliverable", "d", "--verification", "v")
                out = r.stdout + r.stderr
                self.assertEqual(r.returncode, 0, out)
                self.assertNotIn("refused", out)

    def test_the_control_a_good_summary_is_accepted_and_stored(self):
        """THE CONTROL. A gate that refuses everything satisfies every test above."""
        r = add_raw(self.project.root, "--title", "a title",
                    "--summary", GOOD,
                    "--deliverable", "d", "--verification", "v")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tid = json.loads(r.stdout)["id"]
        rc, payload = self.project.task("list", "--all")
        self.assertEqual(rc, 0, payload)
        row = next(t for t in payload["tasks"] if t["id"] == tid)
        self.assertEqual(row["summary"], GOOD)


class TestTheRewriteWriterHoldsTheSameLine(unittest.TestCase):
    """`perry-task summary` refuses what `add` refuses.

    Without this, `add`'s refusal is one command away from being undone and the
    linter would report a row the tool had just accepted.
    """

    def setUp(self):
        self.project = Project(self)
        r = add_raw(self.project.root, "--title", "the parser drops zh headers",
                    "--summary", GOOD, "--deliverable", "d",
                    "--verification", "v")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.tid = json.loads(r.stdout)["id"]

    def test_summary_refuses_a_second_title(self):
        rc, out = self.project.task("summary", self.tid,
                                    "--summary", "The parser drops zh headers.")
        self.assertEqual(rc, 1, out)
        self.assertIn("restates the title", str(out))

    def test_clear_is_deliberately_not_gated(self):
        """A wrong summary must stay removable.

        A confidently wrong summary is worse than an empty field — the empty
        field at least tells the reader to go and look. So `--clear` passes,
        and the linter then reports the row, which is the honest outcome.
        """
        rc, out = self.project.task("summary", self.tid, "--clear")
        self.assertEqual(rc, 0, out)
        rc, txt = lint(self.project.root, "--summaries")
        self.assertIn("summary-missing", txt)


class TestTheLinterReportsWhatTheWriterRefuses(unittest.TestCase):
    """Part 2 of TASK-325, both directions.

    A check tested in one direction only is untested: it must FIRE on a real
    blank row and be SILENT on a genuinely good summary.
    """

    def setUp(self):
        self.project = Project(self)

    def test_it_fires_on_a_blank_row_and_names_it(self):
        self.project.root.joinpath("tasks.jsonl").write_text(
            json.dumps({"id": "TASK-900", "title": "a row nobody explained",
                        "status": "not_started", "summary": ""}) + "\n",
            encoding="utf-8")
        rc, txt = lint(self.project.root, "--summaries")
        self.assertEqual(rc, 0, txt)
        self.assertIn("summary-missing", txt)
        self.assertIn("TASK-900", txt)

    def test_it_is_silent_on_a_good_summary(self):
        """THE CONTROL. A check that flags everything fires above and is useless."""
        self.project.root.joinpath("tasks.jsonl").write_text(
            json.dumps({"id": "TASK-901", "title": "a row somebody explained",
                        "status": "not_started", "summary": GOOD}) + "\n",
            encoding="utf-8")
        rc, txt = lint(self.project.root, "--summaries")
        self.assertEqual(rc, 0, txt)
        self.assertNotIn("summary-", txt)
        self.assertIn("1 of 1 open row(s) carry a summary", txt)

    def test_closed_rows_are_not_scanned(self):
        """History is out of scope, and a check that reported it could not be finished."""
        self.project.root.joinpath("tasks.jsonl").write_text("\n".join(
            json.dumps({"id": f"TASK-9{i:02d}", "title": "t",
                        "status": st, "summary": ""})
            for i, st in enumerate(("done", "dropped", "not_started"))) + "\n",
            encoding="utf-8")
        rc, txt = lint(self.project.root, "--summaries")
        self.assertEqual(rc, 0, txt)
        self.assertIn("TASK-902", txt)          # the open one
        self.assertNotIn("TASK-900", txt)       # done
        self.assertNotIn("TASK-901", txt)       # dropped

    def test_the_default_pass_reports_it_without_being_asked(self):
        """A flag nobody types is not a report.

        The measured cause of this whole row is that nothing ASKED for the
        field. Putting the report behind `--summaries` alone would reproduce
        that, which is why `check_summaries` runs in the default pass — the
        same argument `check_specs` carries one check over.
        """
        self.project.root.joinpath("tasks.jsonl").write_text(
            json.dumps({"id": "TASK-900", "title": "a row nobody explained",
                        "status": "not_started", "summary": ""}) + "\n",
            encoding="utf-8")
        rc, txt = lint(self.project.root)
        self.assertIn("summaries:", txt)
        self.assertIn("summary-missing", txt)

    def test_it_stays_advisory_and_never_makes_the_run_red(self):
        """89 blank rows must not turn every project's CI red for a field that
        was optional until today. The hard half is `add`, which refuses.

        Asserted on the SEVERITY of this check's own findings rather than on
        the run's exit code: the throwaway fixture board carries unrelated
        `missing-section` errors of its own, so an exit-code assertion here
        would pass or fail for reasons that have nothing to do with summaries.
        """
        self.project.root.joinpath("tasks.jsonl").write_text(
            json.dumps({"id": "TASK-900", "title": "t",
                        "status": "not_started", "summary": ""}) + "\n",
            encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(LINT), "--root", str(self.project.root),
             "--json"], capture_output=True, text=True)
        payload = json.loads(r.stdout)
        ours = [f for f in payload["findings"]
                if f["rule"].startswith("summary-")]
        self.assertTrue(ours, r.stdout)
        self.assertEqual({f["severity"] for f in ours}, {"warn"})

    def test_a_missing_store_reports_unchecked_rather_than_clean(self):
        """A census that did not happen must not print like a clean one."""
        store = self.project.root / "tasks.jsonl"
        if store.exists():
            store.unlink()
        rc, txt = lint(self.project.root, "--summaries")
        self.assertIn("unchecked, not clean", txt)


class TestOnePlaceDefinesWhatASummaryIs(unittest.TestCase):
    """The writer and the linter read the SAME predicate.

    Two copies is how the tool that refuses and the tool that reports quietly
    start disagreeing about what they are for — DESIGN-013's whole subject.
    """

    def test_perry_lint_binds_the_predicate_from_lib_rather_than_copying_it(self):
        src = (ROOT / "bin" / "perry-lint").read_text(encoding="utf-8")
        self.assertIn("summary_shape = lib.summary_shape", src)
        self.assertNotIn("def summary_shape(", src)

    def test_perry_task_calls_the_same_one(self):
        src = (ROOT / "bin" / "perry-task").read_text(encoding="utf-8")
        self.assertIn("lib.summary_shape(", src)
        self.assertNotIn("def summary_shape(", src)

    def test_the_contract_enumerates_exactly_the_rules_the_predicate_emits(self):
        """`task-list-contract.md`'s `summary` row names the live rules and no others.

        The contract is the READ interface a front-end builds against, so an
        enumeration in it is a PROMISE about what the tools can report. It was
        wrong for the length of one row: TASK-330 removed
        `summary-has-no-sentence` and `summary-is-a-fragment`, and the field
        definition went on requiring "at least one complete sentence" and
        listing "equal to the title, no sentence, under five words" — two
        validations no tool performed any more. A consumer trusting that
        enumeration would have treated a one-word summary as impossible.

        The rule set is read from the CODE with `ast`, never from the
        predicate's docstring: a docstring is prose and agreeing with prose is
        not the property. Removed rules belong in `§ Changelog`, which this
        test deliberately does not police — the changelog's job is to name
        what left.
        """
        import ast
        import re

        src = (ROOT / "bin" / "lib" / "__init__.py").read_text(encoding="utf-8")
        fn = next(n for n in ast.walk(ast.parse(src))
                  if isinstance(n, ast.FunctionDef) and n.name == "summary_shape")
        emitted = {n.value for n in ast.walk(fn)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and n.value.startswith("summary-")}
        self.assertTrue(emitted, "found no rule names in summary_shape — the "
                                 "extraction broke, not the contract")

        contract = (ROOT / "schema" / "task-list-contract.md").read_text(encoding="utf-8")
        rows = [l for l in contract.splitlines()
                if l.startswith("| `summary` | string |")]
        self.assertEqual(len(rows), 1, "expected exactly one `summary` field row")
        named = set(re.findall(r"summary-[a-z-]+", rows[0]))

        self.assertEqual(named, emitted,
                         f"the contract's `summary` row names {sorted(named)} "
                         f"but the predicate emits {sorted(emitted)} — one of "
                         "the two was changed without the other")

    def test_the_writer_and_the_linter_agree_over_a_corpus(self):
        """Not 'both import it' — both ANSWER the same, over cases that differ."""
        project = Project(self)
        # The last two were refused until TASK-330 (2026-09-03) removed the
        # two rules that judged language. They stay in the corpus with their
        # verdicts flipped rather than being dropped: the property under test
        # is that the writer and the linter ANSWER THE SAME, and a case they
        # now both ACCEPT tests that as sharply as one they both refuse — more
        # so, since a removal that reached only one of the two tools would
        # show up right here.
        cases = [
            ("a title", "", True),
            ("a title", "A title.", True),
            ("a title", "It broke.", False),
            ("a title", "no terminator anywhere in this value", False),
            ("the parser drops zh headers", GOOD, False),
        ]
        for title, summary, expect_refused in cases:
            with self.subTest(summary=summary[:30]):
                predicted = bool(lib.summary_shape(title, summary))
                self.assertEqual(predicted, expect_refused)
                argv = ["--title", title, "--deliverable", "d",
                        "--verification", "v"]
                if summary:
                    argv += ["--summary", summary]
                r = add_raw(project.root, *argv)
                self.assertEqual(r.returncode == 1, expect_refused,
                                 r.stdout + r.stderr)


class TestTheCheckDoesNotJudgeLanguage(unittest.TestCase):
    """The properties this check deliberately does NOT have.

    Twice on 2026-09-02 a guard on this project tried to recognise bad English
    and lost: a hedge denylist defeated by a retraction using none of its eight
    words, a push-order regex by two synonyms. The reviewer's verdict was that
    a denylist over English had lost the argument twice. These tests exist so
    the next person to widen this check has to delete one on purpose.
    """

    def test_a_leading_bare_id_is_not_a_finding(self):
        """The predicate TASK-325's own spec proposed, and the corpus refuted.

        Ten of the 49 summaries on Perry's board open with a bare citation and
        ALL TEN are good summaries — TASK-218's "DESIGN-012 I1. Today each of
        the four phase-close stages…" among them. Shipped as proposed the rule
        would have had zero precision over its entire true-positive set.
        """
        self.assertEqual(lib.summary_shape(
            "thread the closing phase id through every close stage",
            "DESIGN-012 I1. Today each of the four phase-close stages re-reads "
            "phase/CURRENT, so the moment one stage advances it every later "
            "stage aims at the wrong phase."), [])

    def test_ids_paths_and_backticks_are_not_findings(self):
        """39 of 49 carry one. That is a summary citing its source."""
        self.assertEqual(lib.summary_shape(
            "a title",
            "`viewer/parsers.py:3899` builds top_risks from BOARD.md while "
            "perry/risks.jsonl exists. The readers beside it already prefer "
            "their stores."), [])

    def test_no_wording_vocabulary_or_hedge_rule_exists_in_the_predicate(self):
        """Structure only. Two summaries with identical shape and opposite
        wording must get identical verdicts — which is what makes this check
        undefeatable by a synonym, and also what makes it modest."""
        a = "This row exists because the reader cannot tell what it is about."
        b = "Perhaps possibly maybe arguably it might conceivably be unclear."
        self.assertEqual(lib.summary_shape("a title", a),
                         lib.summary_shape("a title", b))
        self.assertEqual(lib.summary_shape("a title", b), [])

    def test_a_summary_shorter_than_its_title_is_not_a_finding(self):
        """Considered and rejected as a rule: a good plain-language gloss of a
        long shorthand title is frequently shorter than it, which is the
        outcome this row wants rather than one to penalise."""
        self.assertEqual(lib.summary_shape(
            "linkage-kr-exists fires only on an absent id, so a KR nested "
            "under the wrong objective lints clean",
            "The linter misses a misfiled KR."), [])

    def test_a_chinese_summary_is_not_refused_for_being_chinese(self):
        """The check must not silently mean "structural, IN ENGLISH".

        Both halves of this were real defects, found by this row's own suite
        rather than by reading. `str.split()` makes `新的稳定说明` exactly ONE
        word, so any length floor refused every Chinese summary ever written;
        and an ASCII-only fold sent every Chinese summary to `""`, which
        `"a title".startswith("")` reports as repeating its title. Perry
        declares a document language per project and ships zh fixtures, so
        both would have been live.
        """
        self.assertEqual(lib.summary_shape(
            "an English title",
            "这一行说明了这条记录为什么存在，以及完成之后会得到什么。"), [])
        # And the rule still WORKS in Chinese rather than merely not firing:
        # a Chinese summary that is its Chinese title is still caught.
        self.assertIn("summary-repeats-title", [r for r, _ in lib.summary_shape(
            "板子写错了。", "板子写错了。")])

    def test_a_one_character_title_does_not_swallow_every_summary(self):
        """`"a fixture row…"` starts with `"a"`, so a bare prefix test made a
        row titled "A" repeat its title with EVERY possible summary. The rule
        measures what the summary ADDS, not that it starts the same way."""
        self.assertEqual(lib.summary_shape(
            "A", "A fixture row that exists so the writer has something to "
                 "write. It carries no meaning beyond that."), [])

    def test_neither_a_fragment_nor_a_sentenceless_value_is_a_finding(self):
        """The two rules TASK-330 removed, pinned as absences.

        Until 2026-09-03 `summary-has-no-sentence` and `summary-is-a-fragment`
        refused both of these. The user removed them: whether prose reads like
        prose is the writing agent's responsibility, not a check's. This test
        is the replacement for the one that used to guard the word floor's
        headroom — the floor is gone, and what needs guarding now is that it
        stays gone.
        """
        self.assertEqual(lib.summary_shape("a title", "Short."), [])
        self.assertEqual(lib.summary_shape("a title", "short"), [])
        self.assertEqual(
            lib.summary_shape("a title", "no terminator anywhere here"), [])
        # `SUMMARY_MIN_WORDS` survives as `summary-repeats-title`'s threshold
        # and must not drift back into being a length floor: this value is
        # three tokens with no terminator — both removed rules at once — and
        # is accepted.
        self.assertEqual(lib.summary_shape("a title", "太短了"), [])


if __name__ == "__main__":
    unittest.main()
