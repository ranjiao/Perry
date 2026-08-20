"""Where an escalation fragment is allowed to match — TASK-107.

`test_escalation_union.py` guards WHICH fragments exist. This file guards WHERE
each one may match, which is a different failure and had a different bug.

The matcher was `f in hay`: a bare, case-folded substring test. Substrings match
inside words, so on 2026-08-20, on this repository's own corpus:

    origin  matched "still carries its original bytes"     TASK-079
    adopt   matched "on an adopted project"                TASK-086
    main    matched "remains available"                    TASK-105
    main    matched "remains a compact projection"         TASK-106

Four dispatches stopped for a human. None of the four tasks touched a git
remote, ran an adoption, or went near `main`. The cost is not the adjudication:
a gate that cries wolf on ordinary English gets waved through, and then it is
not protecting anything. Worse, the cheapest way to pass it was to REWORD THE
SPEC — a safety gate that pays out for rewording is worse than no gate, because
the payout is invisible.

So the tests below are written as two halves that must both hold, because
either one alone is trivially satisfiable by breaking the other:

1. **The false positives are gone.** Satisfiable on its own by matching nothing.
2. **Every true positive still matches**, including the fragments a naive `\\b`
   would silently kill — `~/.claude/skills` (leading `~`), `design/` (trailing
   `/`), `--force-with-lease` (leading `-`), `$PERRY_HOME` (leading `$`).
   Satisfiable on its own by going back to substrings.

And one that is not about English at all. **ADR-007 forbids `\\b` here.** Its
fifth `CLOCK_RE` round failed because `\\b` does not exist in Chinese: the
English half of a rule matched word-bounded and the Chinese half matched bare,
so `下周期` wrote a live commitment row while `next cycle` was refused. A hook's
match tokens are ASCII by construction — `tests/fixtures/sample-project-zh/
.perry/hook.md` states that invariant in the fixture itself — while the prose
around them is not, so the guard has to be an explicit ASCII class. If someone
"simplifies" it to `\\b` or `\\w`, `TestTheChineseHalfMatchesToo` is what fails.

Run: python3 tests/test_escalation_boundaries.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
LINT = PERRY_HOME / "bin" / "perry-lint"
STATE = PERRY_HOME / "bin" / "perry-state"
sys.path.insert(0, str(PERRY_HOME / "viewer"))
import parsers as P  # noqa: E402


def scan(text: str, *fragments: str) -> list[str]:
    return P.matching_escalations(text, list(fragments))


class TestOrdinaryEnglishNoLongerTrips(unittest.TestCase):
    """Half one. Every row is a sentence that really appeared in a spec."""

    #: (fragment, the real sentence, where it came from)
    MEASURED = [
        ("origin", "the restore point still carries its original bytes",
         "TASK-079 § Deliverable"),
        ("adopt", "On an adopted project, a plain `perry-lint` run",
         "TASK-086 § Deliverable"),
        ("main", "generic cross-project lookup behavior remains available",
         "TASK-105 § Deliverable"),
        ("main", "`BOARD.md` remains a compact projection",
         "TASK-106 § Deliverable"),
        ("adopt", "keep what adoption needs",
         "TASK-041 title, via perry-lint's consequence check"),
    ]

    def test_the_four_measured_false_positives(self):
        for frag, sentence, where in self.MEASURED:
            with self.subTest(where=where):
                self.assertEqual(
                    scan(sentence, frag), [],
                    f"{frag!r} still matches inside {sentence!r} ({where})")

    def test_the_rest_of_the_english_main_hits(self):
        """`main` is the worst fragment in Perry's own hook: three common
        English words contain it. Left-guard and right-guard each catch a
        different one, so both edges are exercised here on purpose."""
        for sentence in ("in the domain model",         # guarded on the left
                         "maintaining the parser",      # guarded on the right
                         "the remaining rows"):         # guarded on both
            with self.subTest(sentence=sentence):
                self.assertEqual(scan(sentence, "main"), [])

    def test_prod_does_not_match_reproduce_or_production(self):
        """The shipped template lists `prod` AND `production` separately, which
        only means something once `prod` stops matching the longer word."""
        self.assertEqual(scan("reproduce the bug", "prod"), [])
        self.assertEqual(scan("a production deploy", "prod"), [])
        self.assertEqual(scan("a production deploy", "production"),
                         ["production"])


class TestEveryTruePositiveStillMatches(unittest.TestCase):
    """Half two. Going back to substrings passes half one's tests and fails
    nothing here — which is why half one is not allowed to stand alone."""

    #: (fragment, text that must trip it, what shape of fragment it guards)
    KEPT = [
        ("origin", "git push origin main", "a bare word, used as itself"),
        ("main", "git push origin main", "a bare word at end of line"),
        ("adopt", "run `/perry adopt` on the repo", "a word behind punctuation"),
        ("git push", "then git push and tag it", "two words with a space"),
        ("rm -rf", "rm -rf build", "a command with a flag"),
        ("state-schema.json", "edits schema/state-schema.json here",
         "a filename with a dot and a dash, inside a path"),
        ("~/.claude/skills", "symlink into ~/.claude/skills",
         "LEADING TILDE — a naive \\b kills this outright"),
        ("design/", "overwrite the project's design/ tree",
         "TRAILING SLASH — a naive \\b kills this outright"),
        ("design/", "overwrite design/DESIGN-002.md",
         "trailing slash, matching the path beneath it"),
        ("--force-with-lease", "push --force-with-lease onto the branch",
         "LEADING DASHES — a naive \\b kills this outright"),
        ("push --force", "push --force-with-lease onto the branch",
         "a fragment that is a prefix of a longer real command"),
        ("$perry_home", "git pull inside $PERRY_HOME",
         "LEADING DOLLAR, and case-folded"),
        ("npm install -g", "npm install -g something", "flag at the end"),
        ("ln -snf", "ln -snf a b", "a flag cluster listed in full"),
    ]

    def test_each_kept(self):
        for frag, text, why in self.KEPT:
            with self.subTest(fragment=frag, guards=why):
                self.assertEqual(scan(text, frag), [frag],
                                 f"{frag!r} stopped matching {text!r} — {why}")

    def test_every_fragment_in_perrys_own_hook_matches_its_own_text(self):
        """A fragment that cannot match its own literal spelling is dead, and a
        dead fragment is invisible: the gate reports clean. This is the check
        that would have caught a `\\b` guard applied to `design/` — it extracts
        fine, unions fine, and matches nothing forever."""
        union = P.escalation_union(PERRY_HOME)["union"]
        self.assertTrue(union, "Perry's own hook extracted no fragments")
        for frag in union:
            with self.subTest(fragment=frag):
                self.assertEqual(scan(frag, frag), [frag],
                                 f"{frag!r} does not match itself")

    def test_the_shipped_template_defaults_all_match_themselves(self):
        """Same guard, on the list every new project starts from."""
        tmpl = (PERRY_HOME / "work" / "state" / "hook_TEMPLATE.md").read_text()
        frags = P.escalation_fragments(
            [b for b in P._bullets(P._section(P._strip_comments(tmpl),
                                              "High-stakes operations"))])
        self.assertTrue(frags, "the template extracted no fragments")
        for frag in frags:
            with self.subTest(fragment=frag):
                self.assertEqual(scan(frag, frag), [frag])


class TestTheChineseHalfMatchesToo(unittest.TestCase):
    """ADR-007's fifth round, guarded at this surface.

    `\\b` does not exist in Chinese. A `\\b`-guarded matcher word-bounds the
    English half of a hook and leaves the Chinese half matching bare — the exact
    asymmetry that let `下周期` through. An explicit ASCII class has one meaning
    in both, which is why the matcher spells the class out."""

    def test_an_ascii_fragment_inside_chinese_prose_matches(self):
        for text, frag in (("部署到 production 环境", "production"),
                           ("我们要 deploy 到生产环境", "deploy"),
                           ("请勿执行 rm -rf 操作", "rm -rf")):
            with self.subTest(text=text):
                self.assertEqual(scan(text, frag), [frag])

    def test_the_matcher_never_spells_a_boundary_as_backslash_b(self):
        """Structural, because the behavioural test above passes for the wrong
        reason on any corpus that happens to put a space around the token."""
        src = (PERRY_HOME / "viewer" / "parsers.py").read_text()
        start = src.index("def escalation_pattern")
        body = src[start:src.index("def matching_escalations", start)]
        code = "\n".join(ln for ln in body.splitlines()
                         if not ln.strip().startswith("#"))
        for banned in (r"\b", r"\w", r"\W"):
            self.assertNotIn(
                banned, code.split('"""')[-1],
                f"escalation_pattern uses {banned!r} — ADR-007: it has no "
                f"meaning in Chinese, and this is round six of that bug")

    def test_the_zh_fixture_hook_still_arms(self):
        root = PERRY_HOME / "tests" / "fixtures" / "sample-project-zh"
        u = P.escalation_union(root)
        self.assertTrue(u["armed"], "the Chinese fixture's gate went unarmed")
        for frag in u["union"]:
            self.assertEqual(scan(frag, frag), [frag], frag)


class TestOneMatcher(unittest.TestCase):
    """`P.escalation_union` is the one extractor for the reason stated in
    `test_escalation_union.py`; the matcher needs the same guard, because a
    second copy is how a scan quietly stops scanning what it used to. There
    were two, and the copy in `perry-lint` was the bare substring test."""

    def test_perry_lint_carries_no_second_substring_matcher(self):
        src = LINT.read_text(encoding="utf-8")
        self.assertNotIn("f for f in stakes if f in hay", src,
                         "perry-lint re-implements the escalation matcher")
        self.assertIn("P.matching_escalations", src)

    def test_the_consequence_check_no_longer_reads_adopt_out_of_adoption(self):
        """End-to-end through the linter, on the title that tripped it."""
        self.assertEqual(
            P.matching_escalations("TASK-041 keep what adoption needs",
                                   ["adopt", "adoption"]),
            ["adoption"])


class TestTheSpecScanIsComputed(unittest.TestCase):
    """`scan_spec_escalations` — step 4's two rules, in code.

    Correcting the matcher alone would have changed nothing at dispatch time:
    nothing called it. `dispatch.md` handed an agent a fragment list and a
    paragraph, and the agent matched substrings because the hook's own sentence
    said substring."""

    HOOK = ("# Hook\n\n## High-stakes operations\n\n"
            "- Publishing — `origin`, `git push`\n"
            "- The claim surface — `claims`, `state-schema.json`\n")

    def project(self, hook: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        if hook is not None:
            (root / ".perry" / "hook.md").write_text(hook)
        return root

    def scan(self, spec: str, hook: str | None = None) -> dict:
        root = self.project(self.HOOK if hook is None else hook)
        return P.scan_spec_escalations(
            spec, P.escalation_union(root)["union"])

    def test_a_deliverable_hit_refuses(self):
        out = self.scan("## Deliverable\n\n- push to `origin`\n")
        self.assertEqual(out["verdict"], "refuse")
        self.assertEqual(out["refuse"], ["origin"])

    def test_a_files_in_scope_hit_refuses(self):
        out = self.scan("## Files in scope\n\n- `state-schema.json`\n")
        self.assertEqual(out["verdict"], "refuse")

    def test_an_out_of_scope_hit_green_lights_that_fragment(self):
        """Step 4's second rule: the spec has said in writing that it does not
        do the thing. TASK-086 is why this matters — three of its four
        Deliverable hits were disclaimed in its own `Out of scope`."""
        out = self.scan("## Deliverable\n\n- reads the `claims` list\n\n"
                        "## Out of scope\n\n- editing `claims`\n")
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["green_lit"], ["claims"])
        self.assertEqual(out["refuse"], [])

    def test_out_of_scope_green_lights_only_the_line_in_question(self):
        out = self.scan("## Deliverable\n\n- reads `claims`, pushes to "
                        "`origin`\n\n## Out of scope\n\n- editing `claims`\n")
        self.assertEqual(out["verdict"], "refuse")
        self.assertEqual(out["refuse"], ["origin"])

    def test_ordinary_english_in_a_deliverable_passes(self):
        """TASK-079, end to end: the sentence that stopped the dispatch."""
        out = self.scan("## Deliverable\n\n- the restore point still carries "
                        "its original bytes\n")
        self.assertEqual(out["verdict"], "pass", out)

    def test_no_hook_is_unarmed_and_never_pass(self):
        """An empty list matches nothing and would wave everything through.
        Reporting that as `pass` is the one outcome a gate must not produce."""
        out = self.scan("## Deliverable\n\n- anything\n", hook="# Hook\n")
        self.assertEqual(out["verdict"], "unarmed")
        self.assertFalse(out["armed"])


class TestTheGateAnswersInItsExitCode(unittest.TestCase):
    """`perry-state --escalation-scan` is what `dispatch.md` now calls, so its
    exit code is load-bearing: an agent that misreads JSON still gets the
    verdict. 0 pass · 3 refuse · 4 unarmed · 2 the path was wrong."""

    def run_scan(self, spec_text: str, hook: str) -> tuple[int, dict]:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(hook)
        spec = root / "spec.md"
        spec.write_text(spec_text)
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(spec)],
            capture_output=True, text=True)
        return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else {})

    HOOK = "# H\n\n## High-stakes operations\n\n- Publishing — `origin`\n"

    def test_pass_is_zero(self):
        code, out = self.run_scan(
            "## Deliverable\n\n- its original bytes\n", self.HOOK)
        self.assertEqual((code, out["verdict"]), (0, "pass"))

    def test_refuse_is_three(self):
        code, out = self.run_scan(
            "## Deliverable\n\n- push to `origin`\n", self.HOOK)
        self.assertEqual((code, out["verdict"]), (3, "refuse"))

    def test_unarmed_is_four_and_is_not_folded_into_pass(self):
        code, out = self.run_scan("## Deliverable\n\n- anything\n", "# H\n")
        self.assertEqual((code, out["verdict"]), (4, "unarmed"))

    def test_a_missing_spec_is_a_usage_error_not_a_pass(self):
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(self.HOOK)
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(root / "nope.md")],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_the_scan_reads_the_hook_from_the_project_root(self):
        """`.perry/` is anchored at the project root even when state lives in a
        subdirectory. Handing this the STATE root returned zero fragments and a
        clean `unarmed` from a project whose hook lists thirty things — a gate
        reporting it has nothing to check, which is the failure it exists to
        prevent."""
        code, out = self.run_scan(
            "## Deliverable\n\n- push to `origin`\n", self.HOOK)
        self.assertEqual(out["fragments_scanned"], 1)
        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
