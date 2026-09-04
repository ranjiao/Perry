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
import re
import tempfile
import subprocess
import sys
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


class TestTheHeadingsAreReadInTheProjectsOwnLanguage(unittest.TestCase):
    """Both sides of the pre-flight are internationalised, or neither is.

    TASK-201. `High-stakes operations` — the hook heading `escalation_union`
    reads — has carried `高风险操作` since the glossary shipped. The headings
    read on the *spec* side carried nothing. So a Chinese project armed a full
    union out of its hook and then presented the scan no sections at all: every
    `_section` came back empty, nothing matched, and the verdict was `pass` at
    exit 0 with the matching term sitting in the Deliverable in plain sight.
    TASK-200 measured three real `~/proj/gimegime-pmo` specs through it.

    **The scan is gone** (TASK-339): a dispatching agent reads the spec now, and
    an agent reads Chinese. What is left on this side is
    `P.spec_scope_sections`, which answers only *does this document declare a
    scope at all* and which `bin/perry-lint` reports across the corpus. The hole
    survives the deletion in a quieter shape — a missing glossary row makes a
    perfectly well-formed Chinese spec report `spec-scope-unscannable`, telling
    a reader that a scoped row is unscoped. So the glossary rule is kept.

    The two halves have to hold together: the Chinese spelling is read (or a
    Chinese project's specs all read as scopeless), and the English one still is
    (or the glossary replaced rather than added).
    """

    SPEC_ZH = ("# TASK-999 — 示例规格\n\n"
               "## 涉及文件\n\n- `viewer/parsers.py`\n\n"
               "## 交付物\n\n- 把结果推到 `production` 环境\n\n"
               "## 不在范围\n\n- 其他一概不做\n")
    SPEC_EN = ("# TASK-999 — a spec\n\n"
               "## Files in scope\n\n- `viewer/parsers.py`\n\n"
               "## Deliverable\n\n- push the result to `production`\n\n"
               "## Out of scope\n\n- everything else\n")

    def test_the_glossary_carries_every_heading_the_preflight_reads(self):
        """Structural, and stated for EVERY declared language rather than for
        `zh`: adding a language without these rows re-opens the hole exactly as
        `zh` had it, and the behavioural test below would keep passing because
        it only knows about Chinese."""
        gloss = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text(
                encoding="utf-8"))["i18n"]
        langs = set(gloss["languages"]) - {"en"}
        for canonical in (*P.SPEC_SCOPE_SECTIONS, "Out of scope",
                          "High-stakes operations"):
            entry = gloss["headings"].get(canonical) or {}
            self.assertEqual(
                set(entry), langs,
                f"`{canonical}` is a heading the dispatch pre-flight reads and "
                f"has no spelling in {sorted(langs - set(entry))} — a scoped "
                f"spec written in that language reads as scopeless")

    def test_a_chinese_spec_declares_its_scope(self):
        self.assertEqual(P.spec_scope_sections(self.SPEC_ZH),
                         ["Files in scope", "Deliverable"])

    def test_the_english_headings_still_work(self):
        """The glossary ADDS a spelling; it never replaces the canonical one."""
        self.assertEqual(P.spec_scope_sections(self.SPEC_EN),
                         ["Files in scope", "Deliverable"])

    def test_a_spec_with_neither_heading_declares_nothing(self):
        self.assertEqual(
            P.spec_scope_sections("# TASK-999\n\n## Why\n\nbecause.\n"), [])

    def test_an_empty_heading_is_a_heading_and_not_a_scope(self):
        """`_section` returns the empty string for "absent" and for "present
        and empty" alike; counting the heading alone would report a reading
        that did not happen."""
        self.assertEqual(
            P.spec_scope_sections("# T\n\n## Files in scope\n\n## Why\n\nx\n"),
            [])


class TestTheSpecScannerIsGone(unittest.TestCase):
    """The half of this module that was deleted, and the guard that it stays
    deleted. TASK-339, `USER-916`, `ADR-007` decision 3.

    `bin/perry-state --escalation-scan` matched the project's high-stakes
    fragments against a spec's `Files in scope` / `Deliverable` / `Out of scope`
    and returned a verdict in its exit code. Five rounds tried to make that
    match correct — bare substrings, blind to fields, cite-versus-write, a full
    stop, a markdown italic — and the last measurement is the argument that
    ended it: **formatting alone moved the verdict in both directions.** Bold or
    a sentence-final full stop cleared a declared write to the claim surface;
    bolding an own-tree path `**perry/evidence/…**` made it refuse, because the
    head `**perry` contains a `*`.

    What replaced it is prose — `work/reference/dispatch.md` pre-flight step 4 —
    and **no test in this repository can hold a written procedure.** These two
    hold the only part that is mechanical: that the code did not come back, and
    that the flag is not silently accepted again.
    """

    def test_the_scanner_and_its_path_machinery_are_gone_from_parsers(self):
        for name in ("scan_spec_escalations", "escalation_occurrences",
                     "path_root_is_foreign", "path_token_around",
                     "is_bare_directory_fragment", "_discount_reason",
                     "_PATH_CHAR", "_PATH_RUN", "_NAME_EDGE",
                     "ESCALATION_TOUCHES", "ESCALATION_DISCLAIMS",
                     "ESCALATION_UNCANCELLABLE"):
            self.assertFalse(
                hasattr(P, name),
                f"`{name}` is back in viewer/parsers.py — it exists only to "
                f"judge what a spec's prose means, which ADR-007 decision 3 "
                f"forbids and USER-916 removed")

    def test_the_flag_is_rejected_rather_than_quietly_accepted(self):
        """A usage error, not a verdict. The failure to avoid is a flag that
        parses, does nothing and exits 0 — which reads as `pass`."""
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n\n- State root: .\n")
        (root / ".perry" / "hook.md").write_text(
            "# Hook\n\n## High-stakes operations\n\n- Publishing — `publish`\n")
        spec = root / "TASK-999-spec.md"
        spec.write_text("# T\n\n## Deliverable\n\n- `publish` the thing\n")
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(spec)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stdout[:400])
        self.assertIn("unknown argument", r.stderr)

    def test_no_caller_survives_in_bin_or_viewer(self):
        """`work/` is deliberately not swept: `dispatch.md` and `autopilot.md`
        each carry one sentence recording that the command was removed and why,
        which is documentation of the deletion rather than a caller."""
        pat = re.compile(r"scan_spec_escalations|escalation_occurrences|"
                         r"P\.ESCALATION_TOUCHES")
        offenders = []
        for d in ("bin", "viewer"):
            for f in sorted((PERRY_HOME / d).rglob("*")):
                if f.is_file() and pat.search(f.read_text(errors="replace")):
                    offenders.append(str(f.relative_to(PERRY_HOME)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
