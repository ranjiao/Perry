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

import ast
import json
import subprocess
import sys
import tempfile
import unittest
import warnings
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


class TestTheScanReadsASpecInTheProjectsOwnLanguage(unittest.TestCase):
    """Both sides of the gate are internationalised, or neither is. TASK-201.

    `High-stakes operations` — the hook heading this gate reads — has carried
    `高风险操作` since the glossary shipped. The three headings the same gate
    reads on the *spec* side carried nothing. So a Chinese project armed a full
    union out of its hook and then presented the scan with no sections at all:
    every `_section` came back empty, nothing matched, and the verdict was
    `pass` at exit 0 with the matching term sitting in the Deliverable in plain
    sight. TASK-200 measured three real `~/proj/gimegime-pmo` specs through it —
    three `pass` verdicts, one of them containing a term its own role card
    escalates on.

    **The scan needed no code change**: it already resolved every heading
    through `alias()`. The defect was three missing glossary rows, which is the
    only place it could be fixed without shipping a second translation table.

    The tests below are the two halves that have to hold together: the Chinese
    spelling is read (or a Chinese project has no gate), and the English one
    still is (or the glossary replaced rather than added).
    """

    HOOK = ("# Hook — 示例项目\n\n## 高风险操作\n\n"
            "- 生产部署 — `production`、`deploy`\n")

    #: The same spec, said twice. Only the three headings differ.
    SPEC_ZH = ("# TASK-999 — 示例规格\n\n"
               "## 涉及文件\n\n- `viewer/parsers.py`\n\n"
               "## 交付物\n\n- 把结果推到 `production` 环境\n\n"
               "## 不在范围\n\n- 其他一概不做\n")
    SPEC_EN = ("# TASK-999 — a spec\n\n"
               "## Files in scope\n\n- `viewer/parsers.py`\n\n"
               "## Deliverable\n\n- push the result to `production`\n\n"
               "## Out of scope\n\n- everything else\n")

    def scan(self, spec_text: str) -> tuple[int, dict]:
        """Through the real `--root` seam, on a throwaway Chinese project."""
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: 中文\n"
            "- State root: .\n", encoding="utf-8")
        (root / ".perry" / "hook.md").write_text(self.HOOK, encoding="utf-8")
        spec = root / "spec.md"
        spec.write_text(spec_text, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(spec)], capture_output=True, text=True)
        return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else {})

    def test_the_glossary_carries_every_heading_this_gate_reads(self):
        """Structural, and stated for EVERY declared language rather than for
        `zh`: adding a language without these three re-opens the hole exactly
        as `zh` had it, and the behavioural test below would keep passing
        because it only knows about Chinese."""
        gloss = json.loads(
            (PERRY_HOME / "schema" / "state-schema.json").read_text(
                encoding="utf-8"))["i18n"]
        langs = set(gloss["languages"]) - {"en"}
        for canonical in (*P.ESCALATION_TOUCHES, P.ESCALATION_DISCLAIMS,
                          "High-stakes operations"):
            entry = gloss["headings"].get(canonical) or {}
            self.assertEqual(
                set(entry), langs,
                f"`{canonical}` is a heading the escalation gate reads and has "
                f"no spelling in {sorted(langs - set(entry))} — a spec written "
                f"in that language presents this gate with no sections, and it "
                f"reports `pass`")

    def test_a_chinese_deliverable_hit_refuses(self):
        """The measured before/after. Without the glossary rows this same
        fixture returned `pass` at exit 0 with `touches: {}`."""
        code, out = self.scan(self.SPEC_ZH)
        self.assertEqual(out["touches"], {"Deliverable": ["production"]})
        self.assertEqual(out["refuse"], ["production"])
        self.assertEqual((code, out["verdict"]), (3, "refuse"))

    def test_a_chinese_files_in_scope_hit_refuses(self):
        code, out = self.scan("## 涉及文件\n\n- 改 `deploy` 脚本\n")
        self.assertEqual(out["touches"], {"Files in scope": ["deploy"]})
        self.assertEqual((code, out["verdict"]), (3, "refuse"))

    def test_a_chinese_out_of_scope_green_lights_the_same_way(self):
        """The disclaim side has to translate too. Half-translating this one
        would refuse specs that had said in writing they do not do the thing —
        the crying-wolf failure this file's header is about."""
        code, out = self.scan("## 交付物\n\n- 读 `production` 的配置\n\n"
                              "## 不在范围\n\n- 部署到 `production`\n")
        self.assertEqual(out["green_lit"], ["production"])
        self.assertEqual((code, out["verdict"]), (0, "pass"))

    def test_the_english_headings_still_work_in_a_chinese_project(self):
        """`alias()` adds spellings; it never replaces the canonical one. A
        project mid-translation has both in the tree."""
        code, out = self.scan(self.SPEC_EN)
        self.assertEqual(out["refuse"], ["production"])
        self.assertEqual((code, out["verdict"]), (3, "refuse"))

    def test_the_scan_carries_no_second_translation_table(self):
        """The fix had one shape available that would have worked and been
        wrong: a Chinese literal next to the English one in here. Two glossaries
        is the defect this repository pays for most — `squash`, `heading_re`,
        the three-answers-in-one-call round DESIGN's `heading_is` came from."""
        src = (PERRY_HOME / "viewer" / "parsers.py").read_text(encoding="utf-8")
        start = src.index("def scan_spec_escalations")
        body = "\n".join(
            ln for ln in src[start:src.index("\n# ── Top-level snapshot",
                                             start)].splitlines()
            if not ln.strip().startswith("#"))
        self.assertNotRegex(
            body, r"[一-鿿]",
            "scan_spec_escalations spells a localized heading itself — it "
            "must resolve through alias() so the glossary stays the one place")
        self.assertIn('alias("headings"', body)


class TestACitedPathIsNotAWrittenOne(unittest.TestCase):
    """Where a fragment matched INSIDE a path — TASK-290.

    `TestOrdinaryEnglishNoLongerTrips` fixed the previous layer of this: a
    fragment may not match inside a word. It still matched inside a *path*, and
    a path is where these fragments live. Measured on this repository at
    `548f206`: 26 of 146 specs refused, and 13 of the 26 refused on a path the
    spec cites rather than writes —

        diagnose   matched `bin/perry-diagnose`, `tests/test_diagnose.py`
                   and `reference/diagnose.md`, three filenames, while the
                   hook's bullet says `diagnose` **execute stage** — a pipeline
        evidence/  matched `perry/evidence/2026-09/TASK-263-result.md`, which
                   is the file the round exists to produce, while the hook's
                   bullet says *"overwriting a project's **own**"* — someone
                   else's

    The row that fixes this class was itself refused by it, at exit 3, on the
    one sentence in its `## Deliverable` that explains the false positive, and
    it was dispatched only under this project's first `exit 3` override
    (`perry/evidence/2026-09/2026-09-03-escalation-override.md`).

    Same two-halves discipline as the rest of this file, and here the second
    half is the one that matters, because clearing 13 refusals is trivially
    satisfiable by matching less:

    1. **A cited path no longer refuses.**
    2. **A foreign path, and a fragment that fills its own path component,
       still do.** `schema/state-schema.json` is the case that decides it: the
       claim surface is 13 of the 26 refusals and every one of them is the gate
       working.
    """

    HOOK = ("# H\n\n## High-stakes operations\n\n"
            "- Writing into a project Perry does not own — `adopt` commit "
            "stage, `diagnose` execute stage, `relocate`\n"
            "- The claim surface — `claims`, `state-schema.json`\n"
            "- Host skill installation — `~/.claude/skills`\n"
            "- Destructive — `rm -rf`, overwriting a project's own `design/`, "
            "`evidence/`, `knowledge/`, `inputs/`\n")

    def scan(self, spec: str) -> dict:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(self.HOOK)
        return P.scan_spec_escalations(
            spec, P.escalation_union(root)["union"])

    def files(self, body: str) -> dict:
        return self.scan(f"## Files in scope\n\n{body}\n")

    # ── half 1: a citation stops refusing ────────────────────────────────

    def test_the_binary_that_shares_the_pipelines_name_stops_refusing(self):
        """Six of the eight `diagnose` refusals were this exact line."""
        out = self.files("- `bin/perry-diagnose` — the counting")
        self.assertEqual(out["refuse"], [])
        self.assertEqual(out["verdict"], "pass")

    def test_a_test_file_and_a_reference_doc_are_also_filenames(self):
        for path in ("tests/test_diagnose.py", "reference/diagnose.md",
                     "work/reference/diagnose.md"):
            with self.subTest(path=path):
                self.assertEqual(self.files(f"- `{path}`")["refuse"], [])

    def test_this_projects_own_evidence_file_stops_refusing(self):
        """`TASK-263`, `TASK-099`, `TASK-323` and this row: every one named the
        evidence file the round exists to produce."""
        out = self.files("- `perry/evidence/2026-09/TASK-263-result.md` — written.")
        self.assertEqual(out["refuse"], [])

    def test_a_bare_state_directory_is_this_projects_own(self):
        """The sentence that refused this row's own spec, reduced. A fragment
        that is one directory name and nothing else cannot say whose directory
        it is, and relative means this one's."""
        out = self.scan("## Deliverable\n\nthe hook means someone else's "
                        "`evidence/`; a path resolving inside the project\n")
        self.assertEqual(out["refuse"], [])
        self.assertEqual(out["verdict"], "pass")

    def test_a_glob_and_a_placeholder_segment_are_still_relative(self):
        for path in ("evidence/**/*-spec.md", "evidence/<YYYY-MM>/retro.md",
                     "perry/design/DESIGN-008-track-axes.md", "perry/design/"):
            with self.subTest(path=path):
                self.assertEqual(self.files(f"- `{path}`")["refuse"], [])

    # ── half 2: everything that must still refuse ────────────────────────

    def test_the_claim_surface_fills_its_own_component_and_still_refuses(self):
        """THE test. `schema/state-schema.json` is a path, and the fragment is
        the whole of its last component — so the first rule cannot reach it,
        and `state-schema.json` is not directory-shaped, so neither can the
        second. All 8 live `state-schema.json` refusals are this line."""
        out = self.files("- `schema/state-schema.json` — the `claims[]` entry")
        self.assertEqual(sorted(out["refuse"]), ["claims", "state-schema.json"])
        self.assertEqual(out["verdict"], "refuse")

    def test_a_bare_pipeline_word_still_refuses(self):
        """`TASK-220` names the router's subcommands in prose, not a file. It
        refused before and refuses after — the discount needs a path, and there
        is none."""
        out = self.scan("## Deliverable\n\nbeside `adopt` / `diagnose` / "
                        "`relocate` in the router\n")
        self.assertEqual(sorted(out["refuse"]),
                         ["adopt", "diagnose", "relocate"])

    def test_a_bare_identifier_with_no_path_around_it_still_refuses(self):
        """The conservative half of the first rule, and the case a mutation
        found untested: `perry-diagnose` written WITHOUT a directory is a
        longer name, but there is no path around it to prove it names a file.

        Both rules require a `/` in the token before they will discount
        anything, so this refuses — the safe direction. Deleting that guard
        left every other test in this file green, which is why it is pinned
        here on its own rather than left to the eight tests that happen to
        exercise paths."""
        out = self.files("- run `perry-diagnose` by hand afterwards")
        self.assertEqual(out["refuse"], ["diagnose"])

    def test_a_foreign_root_still_refuses(self):
        """The hook's actual meaning, restored rather than removed: overwriting
        someone ELSE's state directory. Four spellings of not-here."""
        for path in ("~/other-project/evidence/2026-09/",
                     "/srv/theirs/design/",
                     "../victim/knowledge/topics.md",
                     "$PERRY_HOME/inputs/"):
            with self.subTest(path=path):
                out = self.files(f"- overwrite `{path}`")
                self.assertTrue(out["refuse"],
                                f"{path} is not this project's tree, and the "
                                f"gate stopped refusing it")

    def test_an_unresolved_root_refuses_because_it_is_not_known_to_be_ours(self):
        """`<target>/evidence/` is exactly the shape an adopt/relocate row
        writes. A root nobody has resolved is not a root known to be this
        project, and guessing 'probably mine' is the guess this row removed."""
        self.assertTrue(self.files("- `<target>/evidence/`")["refuse"])
        self.assertTrue(self.files("- `{{project}}/design/`")["refuse"])

    def test_a_fragment_that_is_its_own_path_still_refuses(self):
        """`~/.claude/skills` spans three components and carries its own
        anchor, so it is neither directory-shaped nor strictly inside one
        component. `TASK-107` keeps this refusal."""
        out = self.files("- `~/.claude/skills` — the symlink")
        self.assertEqual(out["refuse"], ["~/.claude/skills"])

    # ── the discount is reported, never dropped ──────────────────────────

    def test_every_discount_is_in_the_payload_with_the_path_that_caused_it(self):
        """*A narrowed scan passes everything it is asked, cheerfully.* The
        only defence against that is that a discount is visible, so this is a
        structural guard and not a nicety: a rewrite that keeps the verdict and
        drops `discounted` has made the gate quieter in a way no reader of the
        JSON could detect."""
        out = self.files("- `bin/perry-diagnose`\n- `perry/evidence/2026-09/x.md`")
        got = out["discounted"]["Files in scope"]
        self.assertEqual([e["why"] for e in got["diagnose"]],
                         [P.DISCOUNT_LONGER_NAME])
        self.assertEqual(got["diagnose"][0]["token"], "bin/perry-diagnose")
        # `evidence/` carries its own separator, so it spans a component
        # rather than sitting inside one: the second rule is what clears it,
        # and the reason has to say which rule ran or the payload cannot be
        # audited against the two the module documents.
        self.assertEqual([e["why"] for e in got["evidence/"]],
                         [P.DISCOUNT_OWN_TREE])
        self.assertEqual(got["evidence/"][0]["token"],
                         "perry/evidence/2026-09/x.md")

    def test_one_live_occurrence_outranks_any_number_of_discounted_ones(self):
        """A spec citing `bin/perry-diagnose` twelve times and running the
        pipeline once must refuse. The discount is per-occurrence and the
        verdict is per-fragment, so the two have to be combined in the safe
        direction — and the excuses are dropped from the payload once one
        occurrence counts, because a refused fragment has no excuses."""
        out = self.files("- `bin/perry-diagnose`, then run `diagnose`")
        self.assertEqual(out["refuse"], ["diagnose"])
        self.assertNotIn("diagnose",
                         out["discounted"].get("Files in scope", {}))

    def test_the_matcher_itself_is_untouched(self):
        """`matching_escalations` is still the one matcher and still answers
        *is this fragment present* — `bin/perry-lint` calls it for a different
        question and must not inherit this one's answer."""
        self.assertEqual(
            P.matching_escalations("- `bin/perry-diagnose`", ["diagnose"]),
            ["diagnose"])

    def test_no_fragment_is_named_in_the_source(self):
        """The rule is a shape test, not a list. A hardcoded
        `{"design/", "evidence/", …}` would put the user's hook wording inside
        `parsers.py`, and the next hook to write `artifacts/` would silently not
        get the treatment its four siblings do — `.perry/hook.md` is the user's
        file and this module may not know what is in it."""
        src = (PERRY_HOME / "viewer" / "parsers.py").read_text(encoding="utf-8")
        # `parsers.py` carries `\w` inside a non-raw docstring (the
        # `heading_is` one, arguing about what NOT to use), which `compile`
        # reports as a DeprecationWarning. Importing the module never shows it
        # — the warning fires at compile time and the cached `.pyc` hides it —
        # so re-parsing here would add a warning to a green suite that is
        # nothing to do with this guard.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            tree = ast.parse(src)
        wanted = {"is_bare_directory_fragment", "path_root_is_foreign",
                  "path_token_around", "_discount_reason",
                  "escalation_occurrences"}
        seen = set()
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name not in wanted:
                continue
            seen.add(node.name)
            # Docstrings argue ABOUT the hook's wording and quote it on
            # purpose; the executable body may not know it.
            body = list(node.body)
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body = body[1:]
            code = "\n".join(ast.dump(n) for n in body)
            for named in ("evidence/", "design/", "knowledge/", "inputs/"):
                self.assertNotIn(
                    named, code,
                    f"{node.name} names the hook fragment {named!r} — the rule "
                    f"must be a shape test, so a hook that one day writes "
                    f"`artifacts/` gets the same treatment its siblings do")
        self.assertEqual(seen, wanted, "a rule function was renamed away from "
                                       "this guard without replacing it")


class TestOutOfScopeCannotCancelFilesInScope(unittest.TestCase):
    """The green-light asymmetry — TASK-290, and the half nobody had tested.

    Step 4's second rule is that an `Out of scope` hit green-lights the
    fragment: the spec has said in writing that it does not do the thing. That
    rule was applied to BOTH touch sections, and `Files in scope` is not prose
    — it is the enumerated list of paths the round will write. A spec that
    lists a path there and also names it under `Out of scope` has contradicted
    itself, and the gate resolved the contradiction by dispatching.

    Measured at `548f206`: seven specs passed with a non-empty `green_lit`, and
    **three of them — TASK-047, TASK-085, TASK-139 — named
    `schema/state-schema.json` in their own `Files in scope`.** The claim
    surface is the hook's most-bolded bullet and the reason `origin` is on the
    list at all, and it was being waved through on a sentence two headings
    down. Nothing in the output distinguished those passes from a clean scan:
    same `pass`, same exit 0.

    `TASK-047`'s spec is the specimen. It lists `schema/state-schema.json`
    under `Files in scope`, disclaims `schema/state-schema.json § claims[]`
    under `Out of scope`, and its own body says it *"really does edit
    `schema/state-schema.json`"*.
    """

    HOOK = ("# H\n\n## High-stakes operations\n\n"
            "- The claim surface — `claims`, `state-schema.json`\n"
            "- Publishing — `origin`\n")

    def scan(self, spec: str) -> dict:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(self.HOOK)
        return P.scan_spec_escalations(
            spec, P.escalation_union(root)["union"])

    #: The control. `Files in scope` names a genuinely escalated path; `Out of
    #: scope` names the same fragment. This scanned `pass`, exit 0.
    CONTROL = ("## Files in scope\n\n"
               "- `schema/state-schema.json` — the conformance default only\n\n"
               "## Deliverable\n\nA new default value.\n\n"
               "## Out of scope\n\n"
               "- `schema/state-schema.json § claims[]` — untouched\n")

    def test_the_control_refuses_where_it_used_to_pass(self):
        out = self.scan(self.CONTROL)
        self.assertEqual(out["verdict"], "refuse")
        self.assertEqual(out["refuse"], ["state-schema.json"])

    def test_the_contradiction_is_named_rather_than_resolved(self):
        """The gate does not decide which of the spec's two statements is
        true. It reports that the spec made both."""
        out = self.scan(self.CONTROL)
        self.assertEqual(out["contradictions"], ["state-schema.json"])
        self.assertEqual(out["green_lit"], [],
                         "a Files-in-scope hit is not a green light")

    def test_a_deliverable_hit_is_still_green_lightable(self):
        """Unchanged, and deliberately so — this row is about precision, not
        reach. `Deliverable` is prose about what the round achieves, so a
        disclaimer two headings down is a spec narrowing its own description.
        `TASK-086` and `TASK-109` still pass on exactly this."""
        out = self.scan("## Deliverable\n\n- reads the `claims` list\n\n"
                        "## Out of scope\n\n- editing `claims`\n")
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["green_lit"], ["claims"])
        self.assertEqual(out["contradictions"], [])

    def test_a_deliverable_green_light_loses_to_a_files_in_scope_hit(self):
        """Both sections name it; one of them is the write list. The write list
        wins, and the fragment appears once in `refuse` rather than twice."""
        out = self.scan("## Files in scope\n\n- `schema/state-schema.json`\n\n"
                        "## Deliverable\n\n- reads `state-schema.json`\n\n"
                        "## Out of scope\n\n- `state-schema.json`\n")
        self.assertEqual(out["refuse"], ["state-schema.json"])
        self.assertEqual(out["green_lit"], [])

    def test_a_green_light_is_earned_against_the_same_standard(self):
        """Symmetry. An `Out of scope` line reading `bin/perry-diagnose` names
        a file, so it no more disclaims the pipeline than a `Files in scope`
        line naming it would invoke one — otherwise the discount would be a
        one-way ratchet that makes disclaimers cheaper than hits."""
        hook = ("# H\n\n## High-stakes operations\n\n"
                "- Not ours — `diagnose`\n")
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(hook)
        out = P.scan_spec_escalations(
            "## Deliverable\n\n- run `diagnose` on it\n\n"
            "## Out of scope\n\n- `bin/perry-diagnose` is not edited\n",
            P.escalation_union(root)["union"])
        self.assertEqual(out["disclaims"], [])
        self.assertEqual(out["refuse"], ["diagnose"])

    def test_the_true_positive_control_is_still_exit_three(self):
        """Through the real CLI seam, because the exit code is what
        `dispatch.md` step 4 reads. A spec that really does edit the claim
        surface, with nothing anywhere disclaiming it."""
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(self.HOOK)
        spec = root / "spec.md"
        spec.write_text(
            "## Files in scope\n\n"
            "- `schema/state-schema.json` — one new `claims[]` entry\n\n"
            "## Deliverable\n\nThe store is declared in `claims[]`.\n\n"
            "## Out of scope\n\n- everything else\n")
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(spec)], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(sorted(out["refuse"]),
                         ["claims", "state-schema.json"])

    def test_a_discounted_fragment_still_gets_an_origin(self):
        """`--escalation-scan` attributes what it refuses so a refusal can be
        quoted back with the bullet it came from. A fragment the scan STOPPED
        counting is the one a reader most needs a source for."""
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(
            "# H\n\n## High-stakes operations\n\n- Own state — `evidence/`\n")
        spec = root / "spec.md"
        spec.write_text("## Files in scope\n\n- `perry/evidence/x.md`\n")
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(spec)], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(out["origins"]["evidence/"], ["hook"])


class TestTheCensusOnThisRepositorysOwnSpecs(unittest.TestCase):
    """The measured corpus, pinned — TASK-290 verification steps 1 and 2.

    The unit tests above are all synthetic hooks and synthetic specs, which is
    the right shape for a rule but cannot show that the rule met the corpus it
    was designed against. These run the real union from `.perry/hook.md` over
    every real spec, and assert the two numbers that decide whether this change
    was a fix or a narrowing.
    """

    @classmethod
    def setUpClass(cls):
        cls.fragments = P.escalation_union(PERRY_HOME)["union"]
        cls.specs = sorted((PERRY_HOME / "perry" / "evidence").glob(
            "*/*-spec.md"))
        cls.scans = {
            p: P.scan_spec_escalations(p.read_text(errors="replace"),
                                       cls.fragments)
            for p in cls.specs}

    def refusing(self) -> dict:
        return {p: o for p, o in self.scans.items() if o["verdict"] == "refuse"}

    def test_the_gate_is_still_armed_and_still_refuses(self):
        """A change that drops refusals to zero has disarmed it. This is the
        floor, asserted before any of the numbers below."""
        self.assertGreaterEqual(len(self.fragments), 30)
        self.assertGreater(len(self.refusing()), 10)

    def test_every_claim_surface_refusal_survives(self):
        """The 13, counted the way the spec's census counts — one per
        (spec, fragment) pair, `state-schema.json` 8 + `claims` 5 at `548f206`.
        The count only goes UP here, to 11 + 6, because three specs that had
        been cancelling their own `Files in scope` hit stopped being able to."""
        pairs = [(p.name, f) for p, o in self.scans.items() for f in o["refuse"]
                 if f in ("claims", "state-schema.json")]
        self.assertGreaterEqual(len(pairs), 13, sorted(pairs))

    def test_this_rows_own_spec_passes_and_says_why(self):
        """It was refused at exit 3 on `evidence/`, in the one sentence of its
        `## Deliverable` that explains the false positive, and was dispatched
        under this project's first `exit 3` override. The discount is asserted
        alongside the verdict so that 'passes' cannot come to mean 'was not
        read'."""
        spec = PERRY_HOME / "perry/evidence/2026-09/TASK-290-spec.md"
        if not spec.exists():                # a checkout without this row
            self.skipTest("TASK-290-spec.md is not in this tree")
        out = self.scans[spec]
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(
            out["discounted"]["Deliverable"]["evidence/"][0]["why"],
            P.DISCOUNT_OWN_TREE)

    def test_no_spec_passes_on_a_cancelled_files_in_scope_hit(self):
        """The false-pass class, asserted over the whole corpus rather than one
        specimen. Three specs were in this state at `548f206`."""
        for path, out in self.scans.items():
            with self.subTest(spec=path.name):
                if out["verdict"] == "pass":
                    self.assertEqual(out["contradictions"], [])


if __name__ == "__main__":
    unittest.main()
