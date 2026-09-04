"""A spec that declares no scope for the dispatch pre-flight is REPORTED.

TASK-284, and **rewritten for TASK-339** — the gate this file was written
against no longer exists. `bin/perry-state --escalation-scan` matched the
project's high-stakes fragments against a spec's prose and returned a verdict;
`USER-916` removed it on 2026-09-04 because `ADR-007` decision 3 says the Python
layer never parses a document, and five rounds ended with the measurement that
formatting alone moved the verdict in both directions. The judgement is
`work/reference/dispatch.md` pre-flight step 4's, and the agent performs it.

**What did not change is the failure this file is about**, which is why the file
survived the deletion: the pre-flight — code or agent — reads a spec's
`## Files in scope` and `## Deliverable` to learn what a round will write, and a
spec offering neither gives it nothing. `P.spec_scope_sections` is what is left
in Python: it locates those two headings through `_section`, which matches
`^## <heading>`, and it renders no verdict and matches no fragment.

`work/reference/subcommands.md § add-task` step 3 says the spec file carries
"the same schema" as the journal block, and `perry-task add` renders that block
as **bullets** — `- **Deliverable**: …`. A bullet is invisible to `_section`. So
a spec written by following the documented procedure verbatim declared no scope,
and the old gate reported:

    "armed": true, "fragments_scanned": 35, "touches": {}, "verdict": "pass"

**That output was byte-identical to a spec that was read in full and found
clean.** The failure mode looked exactly like its success, which is why the
number went unnoticed: measured 2026-09-02, **45** spec files under
`perry/evidence/` with no section the gate could read — 45 of 135 on the live
branch (`coding/task-247-config-predicate`, `89295085`), 45 of the 119 this
branch was cut from (`d49964e`) — the SAME 45 files either way, and every one of
them `pass` over a fully armed 35-fragment union. Re-measured 2026-09-04: still
the same 45, now of 149. None of the 45 uses the bullet shape at all: 19 are
`### Deliverable` under a `## Schema` umbrella and 26 carry no such section in
any shape, which is why widening `_section` to read bullets would have closed
none of them.

The old gate already refused to call the OTHER empty input clean: no fragments
was `unarmed`, "deliberately not `pass`". The two halves are the same rule and
only one of them was implemented — and step 4.1 / 4.2 now say both halves in
prose, with `TestTheProcedureNamesTheShape` holding that neither loses its
go-ahead in a rewrite.

The tests below are written as two halves that must both hold, because either
alone is trivially satisfiable by breaking the other:

1. **An unscannable spec is reported.** Satisfiable on its own by reporting
   every spec, which would make the check noise and be scrolled past.
2. **A scannable spec is not.** Satisfiable on its own by reporting nothing,
   which is where this started.

And the MUTATION, which is the one that matters: strip the `## ` headings off
a spec that scans today and the check must go red. A check that stays green
when the sections are removed is measuring something other than what it says.

Run: python3 tests/test_spec_scannability.py
"""

from __future__ import annotations

import hashlib
import json
import re
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

#: The shape `perry-task add` renders and `add-task` step 3 tells the author to
#: copy. Reproduced here from `bin/perry-task § cmd_add`'s `definition` block,
#: not invented: this is what following the procedure verbatim produces.
BULLET_SPEC = """# TASK-001 — a title

> Dispatch mode: auto
> Executor: claude-subagent

- **Owner**: Coding Agent
- **Priority**: P1
- **Track / mode**: main / project
- **Deliverable**: edits `state-schema.json`
- **Verification**: the suite
- **Dependencies**: —
- **Out of scope**: —
- **KR linkage**: unlinked
"""

#: The same scope, in the shape the gate can read.
SECTION_SPEC = """# TASK-002 — a title

## Deliverable

Edits `state-schema.json`.

## Out of scope

- Nothing.
"""

HOOK = ("# Hook\n\n## High-stakes operations\n\n"
        "- The claim surface — `claims`, `state-schema.json`\n")


class TestTheSpecSaysWhetherItDeclaredAScope(unittest.TestCase):
    """`spec_scope_sections` is the other half of `armed`: one reports whether
    the HOOK had anything to screen with, the other whether the SPEC declared
    anything to screen. Both inputs can be empty; only one was ever visible.

    Until TASK-339 this drove `scan_spec_escalations`, which also matched the
    hook's fragments against the spec's prose and returned a verdict. That half
    is gone (`USER-916`, `ADR-007` decision 3) and the judgement is
    `work/reference/dispatch.md` step 4's. What is left here answers one
    structural question and renders no verdict at all.
    """

    def test_the_procedure_shape_declares_no_scope_and_says_so(self):
        """The finding itself. A spec written to the shape `perry-task add`
        renders offers neither `## ` heading, and nothing used to say so."""
        self.assertEqual(P.spec_scope_sections(BULLET_SPEC), [])

    def test_a_sectioned_spec_names_the_sections_it_offered(self):
        self.assertEqual(P.spec_scope_sections(SECTION_SPEC), ["Deliverable"])

    def test_out_of_scope_alone_is_not_scope(self):
        """`Out of scope` says what a round does NOT do, so it can never
        establish scope. A spec offering that section and neither of the other
        two has declared nothing for step 4.2 to read."""
        self.assertEqual(
            P.spec_scope_sections("# T\n\n## Out of scope\n\n- `claims`\n"), [])

    def test_an_empty_section_does_not_count(self):
        """A heading with nothing under it is a heading, not scope. `_section`
        returns the empty string either way, so counting the heading alone
        would report a reading that did not happen."""
        self.assertEqual(
            P.spec_scope_sections("# T\n\n## Deliverable\n\n## Verification\n\n- x\n"),
            [])

    def test_it_returns_no_verdict_and_matches_no_fragment(self):
        """The property this row bought. Its only argument is the document —
        there is no fragment list to pass, so there is nothing it can judge."""
        import inspect
        sig = inspect.signature(P.spec_scope_sections)
        self.assertEqual(list(sig.parameters), ["text"])
        src = inspect.getsource(P.spec_scope_sections)
        for banned in ("verdict", "refuse", "escalation_pattern",
                       "matching_escalations", "fragments"):
            self.assertNotIn(banned, src.split('"""')[-1],
                             f"`{banned}` is back in a function whose whole "
                             f"point is that it judges nothing")


class TestTheLinterReportsIt(unittest.TestCase):
    """`perry-lint --specs` — the reporting half. It does not prevent an empty
    scan; it makes one impossible to mistake for a clean pass."""

    def project(self, specs: dict[str, str]) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        (root / "evidence" / "2026-09").mkdir(parents=True)
        for name, text in specs.items():
            (root / "evidence" / "2026-09" / name).write_text(text)
        return root

    def lint(self, root: Path, *extra: str) -> tuple[int, dict]:
        r = subprocess.run(
            [sys.executable, str(LINT), "--specs", "--root", str(root),
             "--json", *extra],
            capture_output=True, text=True)
        return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else {})

    def test_the_unscannable_spec_is_named(self):
        root = self.project({"TASK-001-spec.md": BULLET_SPEC})
        code, out = self.lint(root)
        self.assertEqual(out["unscannable"], 1)
        self.assertEqual(out["specs_scanned"], 1)
        # Scoped to the rule under test. `BULLET_SPEC` is reproduced verbatim
        # from what `perry-task add` renders, and it carries no `## Bound`
        # either, so since TASK-308 it legitimately trips `spec-unbounded` as
        # well. Widening the fixture to silence that would falsify this file's
        # claim that BULLET_SPEC is what the documented procedure produces.
        self.assertEqual([f["rule"] for f in out["findings"]
                          if f["rule"] == "spec-scope-unscannable"],
                         ["spec-scope-unscannable"])
        self.assertEqual(out["findings"][0]["file"],
                         "evidence/2026-09/TASK-001-spec.md")
        # Advisory by default, on the `--verification` precedent: 45 rows of
        # this project's own history predate the rule.
        self.assertEqual(code, 0)

    def test_a_scannable_spec_is_not_reported(self):
        """Half 2. Without this the check is satisfiable by reporting
        everything, which is a check people learn to scroll past."""
        root = self.project({"TASK-002-spec.md": SECTION_SPEC})
        code, out = self.lint(root)
        self.assertEqual(out["unscannable"], 0)
        self.assertEqual([f["rule"] for f in out["findings"]
                          if f["rule"] == "spec-scope-unscannable"], [])
        self.assertEqual(out["specs_scanned"], 1)
        self.assertEqual(code, 0)

    def test_strict_promotes_so_a_dispatcher_can_be_stopped(self):
        root = self.project({"TASK-001-spec.md": BULLET_SPEC})
        code, _ = self.lint(root, "--strict")
        self.assertEqual(code, 1)

    def test_only_spec_files_are_judged(self):
        """`evidence/` also holds dispatch records, result reports and working
        artifacts. None of those is ever fed to the escalation gate, so
        reporting them would be a warning with no action behind it."""
        root = self.project({"TASK-001-result.md": BULLET_SPEC,
                             "TASK-001-dispatch-1.md": BULLET_SPEC})
        _, out = self.lint(root)
        self.assertEqual((out["specs_scanned"], out["count"]), (0, 0))

    def test_no_specs_is_not_a_pass(self):
        """Same discipline as `--verification` and `--provenance`: a count of
        zero unscannable over zero specs is trivially true, so the spec count
        is reported and the caller can tell the two apart."""
        root = self.project({})
        _, out = self.lint(root)
        self.assertEqual((out["specs_scanned"], out["unscannable"]), (0, 0))


class TestTheMutation(unittest.TestCase):
    """Strip the `## ` headings off a spec that scans today; the check must go
    red. A check that survives that mutation is measuring something else."""

    def project(self, spec_text: str) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        (root / "evidence" / "2026-09").mkdir(parents=True)
        (root / "evidence" / "2026-09" / "TASK-002-spec.md").write_text(
            spec_text)
        return root

    def unscannable(self, root: Path) -> int:
        r = subprocess.run(
            [sys.executable, str(LINT), "--specs", "--root", str(root),
             "--json"], capture_output=True, text=True)
        return json.loads(r.stdout)["unscannable"]

    def test_stripping_the_headings_turns_the_check_red(self):
        self.assertEqual(self.unscannable(self.project(SECTION_SPEC)), 0)
        stripped = "\n".join(
            ln for ln in SECTION_SPEC.splitlines()
            if not ln.startswith("## "))
        # The scope TEXT is all still there — only the headings are gone. That
        # is the whole point: the words `state-schema.json` are still in the
        # file and the gate can no longer see them.
        self.assertIn("state-schema.json", stripped)
        self.assertEqual(self.unscannable(self.project(stripped)), 1)

    def test_demoting_the_headings_one_level_also_turns_it_red(self):
        """19 of this repository's 45 unscannable specs are `### Deliverable`
        under a `## Schema` umbrella — the gate reads `## ` only, so a level
        that looks right to a human is invisible to it. This is not an
        argument for widening `_section`; it is the reason the census could
        not be closed by widening it."""
        demoted = SECTION_SPEC.replace("\n## ", "\n### ")
        self.assertEqual(self.unscannable(self.project(demoted)), 1)


class TestOneAnswerToWhichSectionsAreScanned(unittest.TestCase):
    """The linter must not carry its own copy of the section list. A second
    copy is how a report keeps describing a reading that changed underneath it
    — the same defect `SPEC_SCOPE_SECTIONS`' own comment records for the i18n
    table, and `test_escalation_boundaries` guards for the matcher."""

    def test_the_linter_reads_the_gates_list(self):
        src = LINT.read_text(encoding="utf-8")
        self.assertIn("P.SPEC_SCOPE_SECTIONS", src)
        self.assertIn("P.spec_scope_sections", src)
        start = src.index("def check_specs")
        body = src[start:src.index("\n#: How many drifted rows", start)]
        for literal in ('"Files in scope"', "'Files in scope'",
                        '"Deliverable"', "'Deliverable'"):
            self.assertNotIn(
                literal, body,
                "check_specs spells a scanned section itself — it must read "
                "P.SPEC_SCOPE_SECTIONS so the reader and its report cannot "
                "disagree about what is scanned")


class TestTheDefaultPassIsTheReader(unittest.TestCase):
    """Round 2's central guard. Round 1 shipped `--specs` and **nothing
    invoked it** — zero occurrences across `work/`, `modes/`, `decide/`,
    `goals/`, `reference/`, `packs/`, `SKILL.md`, `AGENTS.md` and `tests/run`,
    while every other mode of this linter is named by at least one procedure.
    A report reachable only by a flag nobody types is not a report, and the
    binding sentence of TASK-284's spec is that a spec must not be able to
    present zero scope to the gate *without something saying so*.

    So the check runs in the DEFAULT pass. These tests are what fails if
    someone moves it back behind the flag."""

    def project(self, specs: dict) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        (root / "evidence" / "2026-09").mkdir(parents=True)
        for name, text in specs.items():
            (root / "evidence" / "2026-09" / name).write_text(text)
        return root

    def lint(self, root: Path):
        """The DEFAULT invocation — `--specs` appears nowhere in this argv."""
        argv = [sys.executable, str(LINT), "--root", str(root)]
        self.assertNotIn("--specs", argv)
        r = subprocess.run(argv + ["--json"], capture_output=True, text=True)
        text = subprocess.run(argv, capture_output=True, text=True).stdout
        return r.returncode, json.loads(r.stdout), text

    def test_nobody_has_to_type_the_flag(self):
        code, out, text = self.lint(self.project(
            {"TASK-001-spec.md": BULLET_SPEC}))
        self.assertIn("spec-scope-unscannable",
                      [f["rule"] for f in out["findings"]])
        self.assertEqual(out["specs"],
                         {"specs": 1, "unscannable": 1, "unbounded": 1,
                          "checked": True})
        self.assertIn("spec-scope-unscannable", text)
        # Advisory: a WARNING, so a project carrying pre-rule specs lints
        # green-with-warnings rather than becoming newly broken. The promotion
        # trigger is RECORDED in `check_specs`, not implemented here.
        #
        # The exit code is deliberately not asserted: a bare temp project is
        # "adopted" the moment `.perry/config.md` exists and then reports its
        # absent required state files as errors, so this process exits 1 for
        # reasons that predate TASK-284 and would make the assertion measure
        # something else. Severity is the property this check owns.
        self.assertEqual(
            [f["severity"] for f in out["findings"]
             if f["rule"] == "spec-scope-unscannable"], ["warn"])
        self.assertIsInstance(code, int)

    def test_the_count_prints_every_run_not_only_when_it_is_bad(self):
        """A number that appears only when it is bad teaches a reader that its
        absence means nothing was checked. Same rule the six store lines
        printed beside it follow."""
        _, out, text = self.lint(self.project(
            {"TASK-002-spec.md": SECTION_SPEC}))
        self.assertEqual(out["specs"],
                         {"specs": 1, "unscannable": 0, "unbounded": 1,
                          "checked": True})
        self.assertIn("all 1 offer the escalation gate a section to scan", text)

    def test_a_scannable_spec_is_still_not_reported(self):
        _, out, _ = self.lint(self.project({"TASK-002-spec.md": SECTION_SPEC}))
        self.assertNotIn("spec-scope-unscannable",
                         [f["rule"] for f in out["findings"]])

    def test_the_named_list_is_capped_and_the_tail_is_counted(self):
        """45 identical warnings is a check people learn to scroll past —
        `check_store_drift`'s own reason for `DRIFT_ROWS_SHOWN`. The cap is on
        the naming, never on the count: `stats` and `--specs --json` still
        carry every one."""
        specs = {"TASK-%03d-spec.md" % n: BULLET_SPEC for n in range(1, 26)}
        _, out, _ = self.lint(self.project(specs))
        named = [f for f in out["findings"]
                 if f["rule"] == "spec-scope-unscannable"]
        self.assertEqual(out["specs"]["unscannable"], 25)
        self.assertEqual(len(named), 11)          # ten named plus one tail
        self.assertTrue(named[-1]["message"].startswith("and 15 further"))

    def test_paths_mean_the_same_thing_as_their_neighbours(self):
        """In the default pass every other finding is relative to the PROJECT
        root, while the state root may be a subdirectory. A path on the same
        screen that silently means something else is worse than a long one —
        on this repository the difference is `perry/evidence/…` and
        `evidence/…`."""
        # `.resolve()`d because `resolve_state_root` resolves the declared
        # root and then requires the project root to be one of its parents;
        # on macOS `/var/folders/…` is a symlink to `/private/var/…`, so an
        # unresolved temp root fails that test and this case would silently
        # skip rather than run.
        root = Path(tempfile.mkdtemp()).resolve()
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text(
            "# Config\n\n- State root: perry\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        state = root / "perry"
        (state / "evidence" / "2026-09").mkdir(parents=True)
        (state / "evidence" / "2026-09" / "TASK-001-spec.md").write_text(
            BULLET_SPEC)
        if P.resolve_state_root(root) != state:
            self.skipTest("this checkout resolves the state root differently")
        _, out, _ = self.lint(root)
        self.assertEqual(
            [f["file"] for f in out["findings"]
             if f["rule"] == "spec-scope-unscannable"],
            ["perry/evidence/2026-09/TASK-001-spec.md"])


def visible(text: str) -> str:
    """A markdown file's text with `<!-- … -->` comments removed.

    Every guard below is a text-presence guard, because the defects they hold
    down are text defects. A raw grep cannot tell a live paragraph from one
    somebody commented out — measured: mutating `dispatch.md`'s
    `scope_scanned` paragraph by prefixing `<!--` left the guard GREEN while
    the paragraph no longer rendered. It is not a hypothetical shape for a
    doc to rot into; commenting a section out is how prose gets disabled
    without being deleted. This does not make a text guard into a semantic
    one — nothing here can tell a correct paragraph from a plausible one —
    but it does close the gap between "the bytes are present" and "a reader
    sees it".
    """
    # `\Z` as an alternative terminator on purpose: an UNCLOSED `<!--`
    # comments out the whole rest of the document, and that is exactly the
    # mutation that caught this guard the second time — a closed-comment
    # pattern stripped nothing, so the bytes stayed and the guard stayed
    # green while the paragraph had stopped rendering.
    return re.sub(r"<!--.*?(?:-->|\Z)", "", text, flags=re.S)


class TestTheProcedureNamesTheShape(unittest.TestCase):
    """Fix 1, the procedure side — the only one of TASK-284's three fixes that
    can satisfy its Verification item 2 (*"a spec written by following
    `add-task` verbatim, from scratch, scans with a non-empty `touches`"*).

    Round 1 took only the report. A spec written per the then-current step 3
    still returned `verdict: pass`, `touches: {}`, exit 0 — which `dispatch.md`
    step 4 reads as proceed — while the identical words under a `## `
    heading exited 3. These are text guards because the defect was a text
    defect: the procedure said "the same schema" and the SHAPE is what
    mattered."""

    SUB = PERRY_HOME / "work" / "reference" / "subcommands.md"
    DISPATCH = PERRY_HOME / "work" / "reference" / "dispatch.md"
    TASK = PERRY_HOME / "bin" / "perry-task"

    def step3(self) -> str:
        src = visible(self.SUB.read_text(encoding="utf-8"))
        return src[src.index("3. **For P0 and P1 tasks**"):
                   src.index("### `close-task")]

    def test_step_3_names_the_heading_shape(self):
        step3 = self.step3()
        for required in ("## Files in scope", "## Deliverable",
                         "## Out of scope"):
            self.assertIn(required, step3)

    def test_step_3_says_why_and_not_merely_what(self):
        """*"and say why"* is the spec's own wording for fix 1. A shape rule
        with no reason attached is a style note, and the next author
        reformats it."""
        step3 = self.step3()
        self.assertIn("_section", step3)
        self.assertIn("^## ", step3)
        self.assertIn("verdict: pass", step3)

    def test_the_procedure_no_longer_says_the_same_schema(self):
        """That sentence is what produced the 45: `perry-task add` renders the
        journal block as bullets, so "the same schema" had one available
        reading and it was the wrong one."""
        src = self.SUB.read_text(encoding="utf-8")  # raw: a commented-out
        # copy of the old sentence is still gone from what a reader sees,
        # and this assertion is a NOT-in, so the strict reading is right.
        self.assertNotIn("containing the same schema", src)
        self.assertNotIn("uses the same template as the journal", src)

    def test_the_render_site_and_the_procedure_do_not_contradict(self):
        """The divergence is resolved by naming which surface each shape
        belongs to, in BOTH places. The journal block keeps its bullets — it
        is nested under `## New tasks added`, so a `## ` field inside it would
        close the section it lives in — and `cmd_add` now says so at the point
        where somebody would otherwise copy it into a spec."""
        src = self.TASK.read_text(encoding="utf-8")
        block = src[src.index("def cmd_add"):src.index("def cmd_start")]
        self.assertIn("must not be copied into one", block)
        self.assertIn("TASK-284", block)

    def test_dispatch_step_4_gives_the_empty_spec_half_a_reader(self):
        """The asymmetry this round is about: the empty-HOOK half had a
        `dispatch.md` paragraph and a mandatory go-ahead in chat; the empty-SPEC
        half had two JSON keys no procedure read.

        TASK-339 removed the scan, so there are no JSON keys left — but the
        asymmetry it fixed is the part that has to survive a rewrite into prose,
        and this is what fails if it does not. Both halves are named, both
        require the same go-ahead."""
        src = visible(self.DISPATCH.read_text(encoding="utf-8"))
        step4 = src[src.index("4. **Safety re-validation"):
                    src.index("5. Spec contains a `Subjective verification:")]
        flat = " ".join(step4.split())
        # the empty-SPEC half
        self.assertIn("neither `Files in scope` nor `Deliverable` is present "
                      "and non-empty", flat)
        # the empty-HOOK half
        self.assertIn("nothing is being screened", flat)
        # and one go-ahead rule covering both
        self.assertGreaterEqual(
            flat.count("explicit go-ahead in chat"), 2,
            "only one of the two empty halves requires a go-ahead — that is "
            "the asymmetry TASK-284 measured, arriving through the rewrite")

    def test_the_empty_spec_half_still_does_not_refuse_the_row(self):
        """45 of Perry's own 149 specs declare no scope. Turning that into a
        refusal would stop every dispatch touching them on the spot — an
        operational decision nobody has taken. The exit code used to be what
        carried this; now the sentence does, and this is what holds it."""
        src = visible(self.DISPATCH.read_text(encoding="utf-8"))
        step4 = src[src.index("4. **Safety re-validation"):
                    src.index("5. Spec contains a `Subjective verification:")]
        flat = " ".join(step4.split())
        self.assertIn("is not by itself a reason to refuse the row", flat)
        self.assertIn("it is a reason not to claim you screened it", flat)


class TestTheTwoClausesAProseRewriteLoses(unittest.TestCase):
    """TASK-339. The scanner is gone and `dispatch.md` step 4 replaced it with a
    written procedure. **No test in this repository can hold a written
    procedure** — three mutations planted against step 4 (dropping the
    unresolved-root shape, moving ownership detection after normalisation,
    deleting a doing-vs-naming tell) all ran GREEN against the full suite. What
    holds the procedure is a reader; that is the trade `USER-916` made and it is
    stated in `perry/evidence/2026-09/TASK-339-result.md` rather than hidden.

    These two clauses are the exception, and they are pinned because
    `perry/evidence/2026-09/TASK-290-round2-v4-review.md` names each of them, in
    writing, as the thing a prose rewrite is most likely to lose:

      *"**A replacement procedure that omits this case is weaker than the code
      it replaces**, and this is the single most likely thing to be dropped when
      the rule is rewritten in prose, because it is the one clause that is not
      obvious from an example."*  — on the unresolved root

      *"any rewrite that strips formatting before deciding ownership will lose
      the ownership signal with it"*  — on the ordering

    Pinned as PRESENCE, never as exact wording: an editor may rephrase either
    sentence and should be able to, and a guard that froze the paragraph would
    make the procedure unmaintainable — which is a worse failure than this one.
    `visible()` is used so that commenting a clause out, including with an
    unclosed `<!--`, reddens this rather than leaving it green.
    """

    DISPATCH = PERRY_HOME / "work" / "reference" / "dispatch.md"

    def step4(self) -> str:
        src = visible(self.DISPATCH.read_text(encoding="utf-8"))
        return src[src.index("4. **Safety re-validation"):
                   src.index("5. Spec contains a `Subjective verification:")]

    def enumeration(self) -> str:
        """The numbered list itself, NOT the whole step.

        Measured while writing this: a first version asserted `"unresolved
        root" in step4`, planted a mutation deleting list item 5, and stayed
        GREEN — the phrase also appears in the worked-paths table below, so the
        guard was reading the copy rather than the clause. A guard whose
        mutation passes is worth less than no guard, because it is also
        believed. Scoped to the list.
        """
        step4 = self.step4()
        start = step4.index("**Foreign is exactly five shapes:**")
        return step4[start:step4.index("**Shape 5", start)]

    def test_all_five_foreign_root_shapes_are_named(self):
        """Relative is internal and foreign is five shapes. Four are obvious
        from an example; the fifth is not, which is why it is pinned hardest."""
        block = self.enumeration()
        items = re.findall(r"^\s*(\d)\. ", block, re.M)
        self.assertEqual(
            items, ["1", "2", "3", "4", "5"],
            f"the foreign-root enumeration is no longer five items ({items}) "
            f"— dropping one makes this procedure weaker than the code it "
            f"replaced:\n{block}")
        flat = " ".join(block.split())
        self.assertIn("unresolved root", flat,
                      "the unresolved-root shape left the enumeration — a root "
                      "nobody has resolved is not a root known to be this "
                      "project")
        for shape in ("absolute", "home anchor", "variable anchor",
                      "upward escape"):
            self.assertIn(shape, flat, f"the `{shape}` shape is gone")

    def test_the_unresolved_root_says_why_and_not_merely_what(self):
        """A judgement made in the safe direction, with no example to make it
        obvious, is exactly the clause a later editor deletes as noise unless
        the reason travels with it."""
        flat = " ".join(self.step4().split())
        self.assertIn("safe direction", flat)

    def test_ownership_is_decided_before_normalisation(self):
        """The collision: the characters that IDENTIFY a foreign root are the
        same characters you would strip as formatting noise. `~` is an anchor;
        `*` is emphasis. Order is the whole property, so the heading states it
        and this fails if the ordering claim leaves."""
        step4 = self.step4()
        flat = " ".join(step4.split())
        self.assertIn("BEFORE you tidy any text", flat)
        self.assertIn("classify the root before you normalise", flat)
        # and the test that makes the ordering workable without a stripping
        # pass at all: pairing, not stripping.
        self.assertIn("balanced pair", flat)
        self.assertNotIn("Normalise the text first", flat)

    def test_the_two_worked_paths_are_both_shown(self):
        """`TASK-339` § Verification 3: the procedure must be shown refusing
        `~/other-project/evidence/2026-09/` and allowing
        `perry/evidence/2026-09/`, in the file itself, not only in evidence."""
        flat = " ".join(self.step4().split())
        self.assertIn("~/other-project/evidence/2026-09/", flat)
        self.assertIn("perry/evidence/2026-09/", flat)

    def test_relative_is_internal_full_stop(self):
        flat = " ".join(self.step4().split())
        self.assertIn("Relative is internal", flat)


class TestTheAdvisoryHasARecordedTrigger(unittest.TestCase):
    """DESIGN-003 decision 4 is cited accurately for keeping this advisory,
    but it reads *"Advisory first release, hard gate next"* **with a stated
    plan** in its §4 note — advisory for one release with `perry-lint`
    reporting the gap, then hard. Citing the precedent while recording no
    condition of your own is how an advisory becomes permanent by default."""

    def body(self) -> str:
        src = LINT.read_text(encoding="utf-8")
        return src[src.index("def check_specs"):
                   src.index("\n#: How many drifted rows")]

    def test_the_promotion_condition_is_written_down(self):
        body = self.body()
        self.assertIn("Promotion trigger", body)
        self.assertIn("DESIGN-003", body)

    def test_the_trigger_does_not_route_through_rewording(self):
        """`.perry/hook.md` calls rewording a spec to pass a gate the one
        thing a gate must never reward, so "drive the count to 0" must not be
        readable as "edit the 45"."""
        flat = " ".join(self.body().split())
        self.assertIn("not that anyone edits them", flat)


class TestTheLinterDoesNotFakeItsLocalization(unittest.TestCase):
    """Round 1's `--specs` branch called `load_glossary(schema)` under a
    comment claiming it armed the heading aliases. It does not:
    `load_glossary` fills `perry-lint`'s own `HEADING_ALIASES`, while
    `P.alias` reads `parsers._i18n()`, which self-loads from the schema and
    caches per name. The BEHAVIOUR was right either way — which is why nothing
    caught it — and a claim a file cannot back is ADR-007 rule 3's defect
    stated about a comment."""

    def zh_spec(self) -> str:
        return "# TASK-003 — 标题\n\n## 交付物\n\n" \
               "改动 `state-schema.json`。\n"

    def hooked(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        return root

    def test_the_branch_no_longer_calls_it(self):
        """Read the CODE, not the comment that explains its absence — a guard
        that greps the whole branch fails on the sentence recording why the
        call is gone."""
        src = LINT.read_text(encoding="utf-8")
        branch = src[src.index("if mode_specs:"):
                     src.index("# Localized column headers are legal")]
        code = [ln for ln in branch.splitlines()
                if not ln.lstrip().startswith("#")]
        self.assertNotIn("load_glossary", "\n".join(code))

    def test_a_localized_spec_still_declares_its_scope(self):
        """The property the removed call was said to protect, tested directly
        rather than asserted in a comment."""
        self.assertEqual(P.spec_scope_sections(self.zh_spec()), ["Deliverable"])

    def test_the_linter_does_not_report_the_localized_spec(self):
        root = self.hooked()
        (root / "evidence" / "2026-09").mkdir(parents=True)
        (root / "evidence" / "2026-09" / "TASK-003-spec.md").write_text(
            self.zh_spec(), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(LINT), "--specs", "--root", str(root),
             "--json"], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual((out["specs_scanned"], out["unscannable"]), (1, 0))


class TestTheAgentGetsItsOwnTree(unittest.TestCase):
    """TASK-285. `dispatch.md` told an agent to branch and said nothing about
    the tree, and a branch instruction with no isolation instruction is an
    instruction to run `git checkout -b` in the SHARED working tree.

    Measured 2026-09-03, before the fix: neither `worktree` nor `isolation`
    appeared anywhere in `dispatch.md`. Observed live the day before — TASK-247's
    subagent switched the shared tree to its own branch, and every PMO write
    after that landed there; the bill was four V4 review documents and 91
    journal lines sitting on a code branch while a merge commit bearing that
    branch's name sat in `main`'s history.

    These are text guards for the same reason the guards above are: the defect
    was a text defect — a rule that was not written down. `visible()` is used so
    that commenting the rule out, including with an unclosed `<!--`, reddens
    this rather than leaving it green.
    """

    DISPATCH = PERRY_HOME / "work" / "reference" / "dispatch.md"
    BOUNDARIES = PERRY_HOME / "work" / "reference" / "git-boundaries.md"
    DELEGATE = PERRY_HOME / "work" / "reference" / "delegate.md"

    def seen(self, path: Path) -> str:
        return visible(path.read_text(encoding="utf-8"))

    #: The rule, verbatim. **An allowlist, not a denylist**, and that is the
    #: whole design of this guard after two V4 rounds killed the other one.
    #:
    #: Round 1 defeated a modality-blind guard by softening the rule to "MAY".
    #: Round 2 defeated the hedge denylist by adding a retraction sentence
    #: INSIDE the blockquote, keeping the pinned imperative verbatim and using
    #: none of the eight banned words: *"Where a worktree is impractical,
    #: sharing the primary checkout instead is an acceptable alternative."* All
    #: nine tests reported OK while the row's headline deliverable stood
    #: retracted. The reviewer's own summary is the lesson: **a denylist over
    #: English has now lost this argument twice** — English retractions are not
    #: eight items long, and the next one will not be on the list either.
    #:
    #: So the rule block is pinned to exactly these bytes. Changing the rule
    #: now means changing this constant in the same commit, which is the
    #: friction a rule this expensive should carry. Same move this project
    #: chose in `USER-904` (one `header_index` instead of a smarter detector)
    #: and `USER-906` (one invariant instead of a fourth predicate): a small
    #: exact surface beats a clever filter.
    #:
    #: **What this constant does NOT do**, stated here because round 3's result
    #: document claimed otherwise and the V4 review caught it: pinning these
    #: bytes protects the paragraph's bytes, not its meaning. Round 3's reviewer
    #: retracted the rule by inserting a contradicting sentence three lines
    #: BELOW this block, touching nothing, with all eleven guards green. What
    #: closes that is `GOVERNED` below — this constant is the readable failure
    #: message, not the coverage.
    RULE = (
        "## The tree the agent works in\n"
        "\n"
        "> **A dispatched agent works in its own git worktree. The primary "
        "checkout is\n"
        "> never switched by an agent; it merges the agent's branch "
        "afterwards, and that\n"
        "> merge is the only code operation it performs.**"
    )

    def rule_block(self) -> str:
        """The blockquote that states the rule, isolated.

        **This slice is 5 lines of an 86-line governed span**, which round 2
        named as a defect in its own right and round 3's review then
        demonstrated: a retraction one line below it was invisible by
        construction. The section around it is now pinned as the complement of
        a declared rationale block (`GOVERNED`), so this slice is a readable
        failure message for the rule itself, never the coverage.
        """
        src = self.seen(self.DISPATCH)
        start = src.index("## The tree the agent works in")
        return src[start:src.index("\n\n", src.index(">", start))]

    def test_the_rule_is_pinned_verbatim(self):
        """The rule's own bytes. `test_the_governed_regions_are_pinned` is the
        primary guard; this one names the rule in its failure message."""
        self.assertEqual(self.rule_block(), self.RULE)

    #: The GOVERNED spans — **the complement of a declared-free zone, not an
    #: enumeration of remembered places.** This is the round-3 → round-4 change
    #: and it is the whole point of the rewrite.
    #:
    #: Round 3 pinned four regions chosen from memory. Four of round 2's twelve
    #: green mutations stayed green against it, because *a pin that protects a
    #: paragraph's BYTES does not protect its MEANING when a contradicting
    #: sentence can be added beside it.* The decisive one added nothing to any
    #: pinned region at all: it inserted **"When the rule does not apply. …
    #: sharing the primary checkout is the accepted practice"** three lines
    #: below the byte-pinned blockquote. Eleven guards reported OK while the
    #: row's headline deliverable stood retracted. The other three kept a
    #: pinned literal and reversed the sense of the line it sat on
    #: (`isolation` bullet, shared-cwd correction, `git-boundaries.md`'s
    #: premise) — all three outside the four regions, all three guarded only by
    #: `assertIn` over a substring window, the pattern that had then lost
    #: twice.
    #:
    #: So the direction is inverted. Each entry names a **contiguous span**
    #: between two anchors, and a list of **explicitly delimited free blocks**
    #: inside it. What is pinned is *the span minus the free blocks*. The
    #: consequence that matters: **inserting a sentence anywhere in a governed
    #: span, touching nothing, reddens** — there is no gap between regions to
    #: insert into, because the regions are what is left over after the free
    #: zone is removed rather than places somebody remembered to list.
    #:
    #: **Rationale is still deliberately NOT pinned** — that is `USER-914`, and
    #: pinning it would undo the decision the user actually made. It is now
    #: declared rather than implied: one block, at the tail of
    #: `dispatch.md § The tree the agent works in`, under its own heading, with
    #: a pinned paragraph immediately above it telling a reader where the
    #: normative text stops. What that costs is stated in
    #: `test_a_contradiction_inside_the_free_rationale_is_not_checkable`.
    #:
    #: Re-pinning is meant to cost a deliberate second edit. When one of these
    #: fails, read the diff it prints, decide whether the rule really changed,
    #: and update the digest in the same commit as the prose.
    GOVERNED = {
        # heading → the next executor heading: the rule, what each side does,
        # the merge argument, the free-zone signpost, and the whole of
        # § `Executor: claude-subagent`, which is where `dispatch.md:208-209`
        # (the `isolation` flag bullet and the shared-cwd correction) live.
        "dispatch.md § the tree + § Executor: claude-subagent": {
            "path": "DISPATCH",
            "span": ("## The tree the agent works in",
                     "### `Executor: opencode-subagent`"),
            "free": [("### Why it is a rule and not a preference\n",
                      "### `Executor: claude-subagent`")],
        },
        # The whole role-boundary section, so line 17 — the one sentence in
        # that file that states the rule, which round 3's slice began one
        # bullet below — is inside, along with the table's premise and every
        # Rules bullet. No free block: this section is normative throughout.
        "git-boundaries.md § Git Role Boundaries": {
            "path": "BOUNDARIES",
            "span": ("## Git Role Boundaries",
                     "## Time Estimation for Coding Agent Tasks"),
            "free": [],
        },
        # From the required-fields list (which also states which tree to
        # create) through the code-work block, so the retraction round 3
        # placed *above* the block is inside the span rather than beside it.
        "delegate.md § required fields + roleless path": {
            "path": "DELEGATE",
            "span": ("## Required fields in the rendered prompt",
                     "## Role ≠ executor"),
            "free": [],
        },
    }

    #: sha256 of `governed_text(name)`. When one of these fails legitimately,
    #: the failure message prints the digest to paste back — deliberately, so
    #: that re-pinning is a copy of a value you have just read the diff for and
    #: not a script you can run without looking.
    GOVERNED_SHA = {
        # span 5,271 chars / 86 lines — 4,121 pinned, 1,150 declared free
        "dispatch.md § the tree + § Executor: claude-subagent":
            "c12161e8db91bd41d52fc68cfee6ced764b5e5a60cc304e3cb87d9053dca2207",
        # span 4,269 chars / 26 lines — all pinned, no free block
        "git-boundaries.md § Git Role Boundaries":
            "e89b1321cd55a7a910322b6045e33b6763717c760d753175816f4a53a5dc45af",
        # span 3,036 chars / 39 lines — all pinned, no free block
        "delegate.md § required fields + roleless path":
            "867706de4988717819124856ae579749f412d0d44d32e800904cf07a1a0e5f58",
    }

    def governed_text(self, name: str) -> str:
        """The span's visible text with its declared free blocks cut out.

        A missing anchor raises `ValueError`, which is a test ERROR and
        therefore red: deleting a governed heading is not a way to go quiet.
        """
        spec = self.GOVERNED[name]
        src = self.seen(getattr(self, spec["path"]))
        a = src.index(spec["span"][0])
        b = src.index(spec["span"][1], a)
        span = src[a:b]
        kept, cursor = [], 0
        for start_after, end_before in spec["free"]:
            i = span.index(start_after, cursor) + len(start_after)
            j = span.index(end_before, i)
            kept.append(span[cursor:i])
            cursor = j
        kept.append(span[cursor:])
        return "".join(kept).rstrip()

    def test_the_governed_regions_are_pinned(self):
        """**The primary guard, and the one that closes round 2's N2.**

        Not "these four paragraphs are unchanged" but "everything in these
        three spans except one declared rationale block is unchanged". An
        inserted sentence has nowhere inside a span to land that is not pinned.
        """
        for name in self.GOVERNED:
            with self.subTest(region=name):
                text = self.governed_text(name)
                got = hashlib.sha256(text.encode("utf-8")).hexdigest()
                self.assertEqual(
                    got, self.GOVERNED_SHA[name],
                    f"\n{name} changed. If the rule really changed, re-pin it "
                    f"deliberately: {got}\n--- current text ---\n{text}\n")

    def test_every_mention_of_the_rule_is_inside_a_governed_region(self):
        """Round 3 declared its own limit as *"a fifth region added later is
        invisible"*. This closes that for the rule's own subject matter.

        Every visible line anywhere under `work/reference/` that says
        `worktree` or `isolation` must fall inside a governed span. Measured on
        this commit: those two words occur in exactly three files and 16 lines,
        every one of them inside a span. So a new paragraph about worktrees —
        in a fourth file, in a later section of one of these three, in a
        section that does not exist yet — reddens here rather than sitting
        unseen beside a pin.

        This is a **containment** check over the rule's own vocabulary, not a
        denylist over hedges: it does not ask what a sentence means, only where
        a sentence on this topic is allowed to live. Its limit is the
        vocabulary — a retraction that never says `worktree` or `isolation`
        (*"sharing the checkout the PMO is sitting in is fine on small rows"*)
        is outside its reach, which is why it is a second line and not the
        first one.
        """
        spans = []
        for name in self.GOVERNED:
            spec = self.GOVERNED[name]
            path = getattr(self, spec["path"])
            src = self.seen(path)
            a = src.index(spec["span"][0])
            b = src.index(spec["span"][1], a)
            spans.append((path, src[a:b]))
        refdir = self.DISPATCH.parent
        for path in sorted(refdir.glob("*.md")):
            src = self.seen(path)
            for n, line in enumerate(src.splitlines(), 1):
                if not re.search(r"worktree|isolation", line, re.I):
                    continue
                inside = any(p == path and line in span for p, span in spans)
                with self.subTest(where=f"{path.name}:{n}"):
                    self.assertTrue(
                        inside,
                        f"{path.name}:{n} talks about the isolation rule from "
                        f"outside every governed span, where nothing pins it:"
                        f"\n  {line.strip()[:160]}")

    def test_a_contradiction_inside_the_free_rationale_is_not_checkable(self):
        """**The honest limit, written down as a test so it cannot be lost.**

        `USER-914` chose: normative regions pinned, rationale prose free. The
        free block is therefore, by construction, bytes this suite does not
        read — and no assertion here can tell an improved explanation from a
        retraction written into it. Three rounds have now established that a
        denylist over English cannot; `perry/knowledge/` states the same rule
        for this project's code generally ("Python never parses document
        semantics").

        What this test *can* hold is that the free zone is exactly one block,
        that it is bounded at both ends by pinned anchors, and that the
        paragraph telling a reader where normative text stops is itself inside
        the pin. What holds the rest is not a test: the block sits at the tail
        of the section under a heading that announces it as explanation, the
        signpost above it says a sentence there granting an exception is a
        defect, and the diff is read at merge.
        """
        spec = self.GOVERNED["dispatch.md § the tree + § Executor: claude-subagent"]
        self.assertEqual(len(spec["free"]), 1)
        src = self.seen(self.DISPATCH)
        a = src.index(spec["span"][0])
        b = src.index(spec["span"][1], a)
        span = src[a:b]
        start = span.index(spec["free"][0][0]) + len(spec["free"][0][0])
        end = span.index(spec["free"][0][1], start)
        self.assertGreater(end - start, 200, "the free block resolved to ~nothing")
        # The signpost is above the free block, so it is inside the pin.
        self.assertIn("**Where the normative part of this section ends.**",
                      self.governed_text(
                          "dispatch.md § the tree + § Executor: claude-subagent"))
        self.assertNotIn("**Where the normative part of this section ends.**",
                         span[start:end])

    def test_the_rule_is_mandatory_and_not_merely_available(self):
        """**The finding this test exists for, and it was a green mutation.**
        The V4 round softened the rule to *"A dispatched agent MAY work in its
        own git worktree where convenient"* and softened the flag bullet to
        *"optional otherwise"* — and all seven guards reported OK. The row's
        headline deliverable could be inverted from mandatory to optional
        without reddening its own guard, because every assertion pinned the
        PRESENCE of words and none pinned their MODALITY.

        A rule that reads as a preference is the state this row exists to
        leave, so the guard has to be able to see the difference.
        """
        block = self.rule_block()
        # The imperative, pinned whole. Not `assertIn` on a fragment: the
        # mutation that defeated this guard kept every fragment intact.
        self.assertRegex(
            block,
            r"A dispatched agent works in its own git worktree\.")
        for hedge in ("MAY ", "may work", "where convenient", "if convenient",
                      "optional", "recommended", "should work", "prefer"):
            with self.subTest(hedge=hedge):
                self.assertNotIn(hedge, block)
        # And the flag bullet says the flag is not optional, in the section.
        src = self.seen(self.DISPATCH)
        flag = src[src.index('Pass `isolation: "worktree"`'):][:200]
        self.assertIn("not optional", flag)

    def test_dispatch_states_the_rule_and_names_the_flag(self):
        """A reader who reaches the executor section must learn the flag to
        pass, not merely that isolation is a good idea."""
        src = self.seen(self.DISPATCH)
        # Pinned to a whole line, not a substring. `assertIn` on the heading
        # text was GREEN under a mutation that renamed the heading to
        # `## The tree the agent works in RENAMED-AWAY` — the renamed heading
        # still *contains* the asserted string, so the guard could not see a
        # section that no longer exists under that name. Anchoring both ends
        # is what makes the assertion about a heading rather than about bytes.
        self.assertRegex(src, r"(?m)^## The tree the agent works in$")
        self.assertIn('isolation: "worktree"', src)
        self.assertIn("never switched by an agent", src)

    def test_the_shared_cwd_line_no_longer_reads_as_a_licence(self):
        """`Sub-agent shares parent cwd.` was true and was read as permission.
        It is corrected in place rather than deleted — it is a fact about the
        process — so the assertion is that the correction travels with it."""
        src = self.seen(self.DISPATCH)
        i = src.index("Sub-agent shares parent cwd")
        sentence = src[i:i + 400]
        self.assertIn("not a licence", sentence)

    def test_dispatch_says_why_not_merely_what(self):
        """A rule with no reason attached is a style note, and the next author
        deletes it. The two observed failures are the reason."""
        src = self.seen(self.DISPATCH)
        section = src[src.index("## The tree the agent works in"):
                      src.index("### `Executor: claude-subagent`")]
        self.assertIn("TASK-247", section)
        self.assertIn("branch is currently checked out", section)

    def test_the_merge_side_is_stated_where_the_rule_is(self):
        """The half that makes the rule usable: something has to merge, and it
        cannot be the worktree. Stating isolation without stating who merges
        leaves the branch stranded, which is the failure this row is about."""
        section = self.seen(self.DISPATCH)
        section = section[section.index("## The tree the agent works in"):
                          section.index("### `Executor: claude-subagent`")]
        self.assertIn("git merge --no-ff", section)

    def test_the_other_two_files_reference_the_rule(self):
        """One rule, one copy. Both files must point at it, and neither may
        restate it — a second authoritative copy is what rots."""
        for path in (self.BOUNDARIES, self.DELEGATE):
            with self.subTest(path=path.name):
                src = self.seen(path)
                self.assertIn("own worktree", src)
                self.assertIn("The tree the agent works in", src)

    def test_no_shipped_procedure_orders_an_unconditional_push(self):
        """`git-boundaries.md` and `delegate.md` both said *"push the branch and
        open a PR"* flatly, while `git push` and `origin` are in the default
        hook list Perry's own bootstrap writes — so following the procedure
        tripped the gate the same procedure arms. The fix is conditional
        wording.

        **Two exact literals was not enough**, and the V4 round proved it: the
        same order restored in different words stayed green in both files. So
        this asserts the PROPERTY — every line that commands a push or a PR
        carries a condition — rather than the absence of two sentences.
        """
        ordering = re.compile(
            r"(?<!not )\b(push(es|ing)? the branch|open (a|the) PR|"
            r"opens? a pull request|go through PR)", re.I)
        conditional = re.compile(
            r"only if|only where|where the|unless|subject to|permits?|"
            r"escalat|hook|condition", re.I)
        # **Per CLAUSE, not per line.** A line-level check was still green on
        # three of the round's mutations: the rest of a long bullet, or a
        # neighbouring table cell, supplied a word like "hook" or "condition"
        # and rescued an order that carried none of its own. Split table rows
        # on `|` and prose on sentence ends, then test only the piece that
        # actually contains the order.
        def clauses(line: str) -> list[str]:
            parts = line.split("|") if line.lstrip().startswith("|") else [line]
            out = []
            for part in parts:
                # `\*{0,2}` because a bolded lead sentence ends `.**` and a
                # bare `(?<=[.;])\s+` does not split there — which left the
                # round's M3 mutation green: the rest of the bullet supplied
                # the word "hook" for an order that carried no condition.
                out.extend(re.split(r"(?<=[.;])\*{0,2}\s+", part))
            return out

        for path in (self.BOUNDARIES, self.DELEGATE, self.DISPATCH):
            src = self.seen(path)
            for line in src.splitlines():
                for clause in clauses(line):
                    if ordering.search(clause):
                        with self.subTest(path=path.name,
                                          clause=clause.strip()[:60]):
                            self.assertRegex(
                                clause, conditional,
                                f"{path.name} orders a push/PR in a clause "
                                f"carrying no condition: "
                                f"{clause.strip()[:120]}")
        for path in (self.BOUNDARIES, self.DELEGATE):
            with self.subTest(path=path.name):
                self.assertIn(".perry/hook.md", self.seen(path))

    def test_the_result_block_does_not_require_a_field_a_compliant_agent_cannot_fill(self):
        """**V4 finding 1, and the change created it.** `dispatch.md` still
        listed `PR URL:` first among the RESULT block's REQUIRED fields, with
        `"n/a — direct push"` as its only alternative, while the rule this file
        now lands says *commit, do not push, do not open a PR* wherever the
        hook escalates a push. A compliant agent then had no truthful value for
        a required field, and step 4 gates the `review` transition on required
        fields being present.

        `git-boundaries.md` also began requiring the branch name in the RESULT
        block, which the RESULT format never defined — three files, three
        answers.
        """
        src = self.seen(self.DISPATCH)
        required = src[src.index("Read the agent's RESULT block. Required "
                                 "fields:"):][:1400]
        # The branch is unconditional — it is what the merge consumes. Assert
        # the MODALITY, not the field's presence: `Branch: <name>` — sometimes.
        # left this green in the round's own mutation.
        self.assertRegex(required, r"`Branch: <name>` — always\.")
        # The PR URL is not.
        pr = required[required.index("`PR URL:`"):][:400]
        self.assertRegex(pr, r"only where|only if|permits")
        # And the template agrees with the prose.
        block = src[src.index("=== RESULT ==="):src.index("=== END RESULT ===")]
        self.assertIn("Branch:", block)
        self.assertNotIn('# or "n/a — direct push" with reason', block)

    def test_the_rule_is_generic_not_perry_specific(self):
        """These files ship to every project. A sentence asserting something
        about THIS repository would be false in every other one — and it was
        written that way first, which is why the assertion exists."""
        for path in (self.DISPATCH, self.BOUNDARIES, self.DELEGATE):
            with self.subTest(path=path.name):
                src = self.seen(path)
                self.assertNotIn("this repository is public", src.lower())


# ── TASK-308 ─────────────────────────────────────────────────────────────
#: A spec carrying a bound. The bound's CONTENT is deliberately ordinary: this
#: check reads presence and shape, never quality, and a fixture whose bound is
#: unusually well drawn would hide a check that had started grading them.
BOUND_SPEC = """# TASK-003 — a title

## Deliverable

Edits `bin/perry-lint`.

## Bound

```
Enumeration: ls bin/perry-*
Size:        9 scripts
Remainder:   none
```
"""

#: The same spec with the bound removed and nothing else changed.
UNBOUND_SPEC = BOUND_SPEC[:BOUND_SPEC.index("## Bound")]


class TestABoundIsRequiredBeforeTheRoundNotAfterIt(unittest.TestCase):
    """`spec-unbounded` — the SPEC-side half of `review.md § 1` (TASK-308).

    The rule was already implemented and already correct, and could not fire in
    time. `criteria-unbounded` reads `criteria:` out of a `=== VERDICT ===`
    block, and such a block exists only once a round has ALREADY scored against
    the spec. So the check that would have bounded the round could only speak
    after it. Measured on `548f206`: 146 specs, 19 carrying a `## Bound`, 127
    not, and `criteria-unbounded` reporting **0** across all 127. TASK-285 and
    TASK-323 both reached V4 unbounded on 2026-09-03 and both discovered it
    mid-round.

    The binding property is the one in `test_the_whole_point` below: the
    fixture must contain **no review document anywhere**, or the test cannot
    tell the new check from the old one.
    """

    def project(self, specs: dict, extra: dict | None = None) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        (root / "evidence" / "2026-09").mkdir(parents=True)
        for name, text in specs.items():
            (root / "evidence" / "2026-09" / name).write_text(text)
        for name, text in (extra or {}).items():
            (root / "evidence" / "2026-09" / name).write_text(text)
        return root

    def assert_no_review_anywhere(self, root: Path) -> None:
        """The fixture's load-bearing property, asserted rather than assumed.

        If ANY file in this tree carried a verdict block, a green result would
        be consistent with the old verdict-side check having fired, and the
        test would prove nothing about reporting before a round.
        """
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            body = f.read_text(errors="replace")
            self.assertNotIn(
                "=== VERDICT ===", body,
                f"{f} carries a verdict block — this fixture must contain no "
                f"review document anywhere or it cannot distinguish the "
                f"spec-side check from the verdict-side one")
            self.assertNotIn(
                "review", f.name.lower(),
                f"{f} is named like a review document")

    def lint(self, root: Path, *extra: str):
        """The DEFAULT invocation. `--specs` appears nowhere in this argv —
        the whole finding is that a report behind a flag nobody types is not a
        report."""
        argv = [sys.executable, str(LINT), "--root", str(root), *extra]
        self.assertNotIn("--specs", argv)
        r = subprocess.run(argv + ["--json"], capture_output=True, text=True)
        text = subprocess.run(argv, capture_output=True, text=True).stdout
        return r.returncode, json.loads(r.stdout), text

    def rules(self, out) -> list[str]:
        return [f["rule"] for f in out["findings"]]

    # ── the property ─────────────────────────────────────────────────────
    def test_the_whole_point(self):
        """A spec with no bound, and NO review document anywhere, is reported
        by the default pass. This is the entire row."""
        root = self.project({"TASK-003-spec.md": UNBOUND_SPEC})
        self.assert_no_review_anywhere(root)
        _, out, text = self.lint(root)
        self.assertIn("spec-unbounded", self.rules(out))
        self.assertEqual(out["specs"]["unbounded"], 1)
        self.assertEqual(
            [f["file"] for f in out["findings"]
             if f["rule"] == "spec-unbounded"],
            ["evidence/2026-09/TASK-003-spec.md"])
        self.assertIn("spec-unbounded", text)

    # ── the control ──────────────────────────────────────────────────────
    def test_a_spec_that_has_a_bound_is_silent(self):
        """Half 2, and the one that makes half 1 mean anything. A check that
        fires on all 146 satisfies `test_the_whole_point` and is useless."""
        root = self.project({"TASK-003-spec.md": BOUND_SPEC})
        self.assert_no_review_anywhere(root)
        _, out, text = self.lint(root)
        self.assertNotIn("spec-unbounded", self.rules(out))
        self.assertEqual(out["specs"]["unbounded"], 0)
        self.assertIn("all 1 spec(s) carry a `## Bound`", text)

    def test_the_two_fixtures_differ_only_in_the_bound(self):
        """Guards the control itself. If the bounded and unbounded fixtures
        drifted apart in some other way, the pair above would be measuring
        that difference instead."""
        self.assertTrue(BOUND_SPEC.startswith(UNBOUND_SPEC))
        self.assertNotIn("## Bound", UNBOUND_SPEC)
        self.assertIn("## Bound", BOUND_SPEC)
        # The scope sections — the OTHER rule over this same file set — are
        # identical in both, so neither fixture can pass by being unscannable.
        self.assertIn("## Deliverable", UNBOUND_SPEC)
        self.assertIn("## Deliverable", BOUND_SPEC)

    def test_neither_fixture_trips_the_other_rule(self):
        """The two rules share a file set and a reporting pass. If either
        fixture were also unscannable, `spec-unbounded` findings and
        `spec-scope-unscannable` findings would be indistinguishable in a
        count."""
        for name, spec in (("bound", BOUND_SPEC), ("unbound", UNBOUND_SPEC)):
            with self.subTest(fixture=name):
                _, out, _ = self.lint(
                    self.project({"TASK-003-spec.md": spec}))
                self.assertEqual(out["specs"]["unscannable"], 0)

    # ── presence and shape, never quality ────────────────────────────────
    def test_a_bound_is_not_judged_on_its_content(self):
        """`review.md § 1` gives the reviewer the judgement of whether a bound
        is WELL DRAWN. A checker that scored it would be the fifth
        guard-over-English attempt on this board. An empty bound is a bound."""
        root = self.project(
            {"TASK-003-spec.md": UNBOUND_SPEC + "## Bound\n\nTBD.\n"})
        _, out, _ = self.lint(root)
        self.assertNotIn("spec-unbounded", self.rules(out))

    def test_a_nested_bound_still_counts(self):
        """Same reading as the verdict-side check, which this shares
        `_BOUND_RE` with: the requirement is that the bound is written down,
        not where. Two matchers would be two answers to one question."""
        root = self.project(
            {"TASK-003-spec.md":
             UNBOUND_SPEC + "## Verification\n\n### Bound\n\nSize: 4\n"})
        _, out, _ = self.lint(root)
        self.assertNotIn("spec-unbounded", self.rules(out))

    def test_the_word_alone_is_not_a_bound(self):
        """Shape, not substring. A spec that merely mentions bounds in prose
        has not written one, and a check that accepted that would report clean
        on the case it exists for."""
        for prose in ("The bound is obvious.\n",
                      "- **Bound**: four files\n",
                      "Bound: four files\n"):
            with self.subTest(prose=prose.strip()):
                _, out, _ = self.lint(self.project(
                    {"TASK-003-spec.md": UNBOUND_SPEC + prose}))
                self.assertIn("spec-unbounded", self.rules(out))

    # ── it reports, it does not refuse ───────────────────────────────────
    def test_it_is_advisory(self):
        """`Out of scope`, explicitly: report, do not refuse — the
        `DESIGN-003 § 4` decision 4 and TASK-284 `scope_scanned` precedent. An
        error here would retroactively block the 127 rows already in the
        tree."""
        _, out, _ = self.lint(self.project({"TASK-003-spec.md": UNBOUND_SPEC}))
        self.assertEqual(
            [f["severity"] for f in out["findings"]
             if f["rule"] == "spec-unbounded"], ["warn"])

    def test_only_spec_files_are_judged(self):
        """`evidence/` also holds dispatch records, results and working notes.
        None of those is a criteria file, and `review.md § 1` does not ask them
        for a bound."""
        root = self.project({}, extra={"TASK-003-result.md": UNBOUND_SPEC,
                                       "TASK-003-dispatch-1.md": UNBOUND_SPEC})
        _, out, _ = self.lint(root)
        self.assertNotIn("spec-unbounded", self.rules(out))
        self.assertEqual(out["specs"]["unbounded"], 0)

    # ── the severity decision, as behaviour ──────────────────────────────
    def test_the_named_list_is_capped_but_the_count_is_not(self):
        """The chosen severity: name the first N, carry the exact count, and
        let `--specs --json` name every one. 127 warnings is a wall of red that
        gets scrolled past, which `reference/diagnose.md` calls strictly worse
        than no check."""
        specs = {"TASK-%03d-spec.md" % n: UNBOUND_SPEC for n in range(1, 26)}
        root = self.project(specs)
        _, out, _ = self.lint(root)
        named = [f for f in out["findings"]
                 if f["rule"] == "spec-unbounded" and f["file"] != "evidence/"]
        tail = [f for f in out["findings"]
                if f["rule"] == "spec-unbounded" and f["file"] == "evidence/"]
        self.assertEqual(len(named), 10)
        self.assertEqual(len(tail), 1)
        self.assertIn("15 further", tail[0]["message"])
        # The CAP is on the naming. The COUNT is exact.
        self.assertEqual(out["specs"]["unbounded"], 25)

    def test_the_flag_names_every_one(self):
        specs = {"TASK-%03d-spec.md" % n: UNBOUND_SPEC for n in range(1, 26)}
        root = self.project(specs)
        r = subprocess.run(
            [sys.executable, str(LINT), "--specs", "--root", str(root),
             "--json"], capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(out["unbounded"], 25)
        self.assertEqual(
            len([f for f in out["findings"] if f["rule"] == "spec-unbounded"]),
            25)

    def test_the_census_prints_every_run_not_only_when_it_is_bad(self):
        """A number that appears only when it is bad teaches a reader that its
        absence means nothing was checked — the rule the store lines beside it
        follow. This one was 127 for the project's whole life and was never
        printed, which is why two rows reached V4 unbounded."""
        _, _, bad = self.lint(self.project({"TASK-003-spec.md": UNBOUND_SPEC}))
        self.assertIn("bounds:", bad)
        _, _, good = self.lint(self.project({"TASK-003-spec.md": BOUND_SPEC}))
        self.assertIn("bounds:", good)

    def test_strict_promotes_so_a_dispatcher_can_choose_to_be_stopped(self):
        root = self.project({"TASK-003-spec.md": UNBOUND_SPEC})
        code = subprocess.run(
            [sys.executable, str(LINT), "--specs", "--root", str(root),
             "--strict", "--quiet"], capture_output=True, text=True).returncode
        self.assertEqual(code, 1)


class TestBothHalvesOfTheBoundRuleSurvive(unittest.TestCase):
    """Two checks, one rule. This class is what fails if a later reader
    "unifies" them (TASK-308).

    They answer different questions. `spec-unbounded` — *this spec offers a
    round no finite set to check*, and needs no verdict to say so.
    `criteria-unbounded` — *this round scored against an unbounded criterion*,
    and can see a criteria file that is not a `*-spec.md`, which the spec-side
    pass never reads. Deleting either trades one blind spot for another.
    """

    def test_both_checks_are_present_in_the_source(self):
        src = LINT.read_text(encoding="utf-8")
        self.assertIn('"criteria-unbounded"', src,
                      "the verdict-side half was deleted")
        self.assertIn('"spec-unbounded"', src,
                      "the spec-side half was deleted")

    def test_each_docstring_says_which_question_it_answers(self):
        """So the next reader does not have to derive the difference from the
        call sites — which is how one of them gets removed as a duplicate."""
        src = LINT.read_text(encoding="utf-8")
        reviews = src[src.index("def check_reviews"):]
        reviews = reviews[:reviews.index('"""', reviews.index('"""') + 3)]
        specs = src[src.index("def check_specs"):]
        specs = specs[:specs.index('"""', specs.index('"""') + 3)]
        for name, body in (("check_reviews", reviews), ("check_specs", specs)):
            with self.subTest(fn=name):
                self.assertIn("question", body.lower())
                self.assertIn("TASK-308", body)

    def test_they_share_one_matcher(self):
        """Two regexes would be two answers to "what counts as a bound", which
        is the defect `check_specs` reads `P.SPEC_SCOPE_SECTIONS` to avoid."""
        src = LINT.read_text(encoding="utf-8")
        self.assertEqual(src.count("_BOUND_RE = re.compile"), 1)
        self.assertEqual(src.count("_BOUND_RE.search"), 2)

    def test_the_spec_side_check_reads_no_verdict(self):
        """The property that makes it fire in time. If `check_specs` learned to
        read verdict blocks or board state, it would be back to speaking only
        after a round — and scoping it to rows at `review` was the option this
        row considered and rejected for exactly that reason."""
        src = LINT.read_text(encoding="utf-8")
        start = src.index("def check_specs")
        body = src[start:src.index("\n#: How many drifted rows", start)]
        # Docstring off, then comment lines off. The assertion is about what
        # the check READS, not what its prose is allowed to mention — the
        # comment beside the new call site necessarily names `parse_verdicts`
        # to explain why the verdict-side half cannot do this job.
        code = body[body.index('"""', body.index('"""') + 3):]
        code = "\n".join(ln for ln in code.splitlines()
                         if not ln.lstrip().startswith("#"))
        for forbidden in ("parse_verdicts", "BOARD.md", "events.jsonl",
                          "tasks.jsonl"):
            self.assertNotIn(
                forbidden, code,
                f"check_specs consults {forbidden} — the spec-side check must "
                f"decide from the spec alone, or it cannot speak before a "
                f"round has been dispatched")


if __name__ == "__main__":
    unittest.main()
