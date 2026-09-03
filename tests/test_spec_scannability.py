"""A spec that presents the escalation gate no scope is REPORTED — TASK-284.

`test_escalation_boundaries.py` guards where a fragment may match. This file
guards the case where there is nothing to match *against*, which is a different
failure and had no test at all.

`scan_spec_escalations` reads three sections through `_section`, which matches
`^## <heading>`. `work/reference/subcommands.md § add-task` step 3 says the
spec file carries "the same schema" as the journal block, and `perry-task add`
renders that block as **bullets** — `- **Deliverable**: …`. A bullet is
invisible to `_section`. So a spec written by following the documented
procedure verbatim is scanned against the empty string, and the gate reports:

    "armed": true, "fragments_scanned": 35, "touches": {}, "verdict": "pass"

**That output is byte-identical to a spec that was read in full and found
clean.** The gate's failure mode looks exactly like its success, which is why
the number went unnoticed: measured on this repository 2026-09-02, **45**
spec files under `perry/evidence/` with no section the gate can read — 45 of
135 on the live branch (`coding/task-247-config-predicate`, `89295085`), 45 of
the 119 this branch was cut from (`d49964e`) — the SAME 45 files either way,
and every one of them `pass` over a fully armed 35-fragment union. None of the 45 uses the
bullet shape at all: 19 are `### Deliverable` under a `## Schema` umbrella and
26 carry no such section in any shape, which is why widening `_section` to
read bullets would have closed none of them.

`scan_spec_escalations` already refuses to call the OTHER empty input clean:
no fragments is `unarmed`, "deliberately not `pass`". The two halves are the
same rule and only one of them was implemented.

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


class TestTheScanSaysWhatItScanned(unittest.TestCase):
    """`scanned` is the other half of `armed`: one reports whether the HOOK had
    anything to match with, the other whether the SPEC had anything to match
    against. Both inputs can be empty; only one of them was ever visible."""

    def scan(self, spec: str) -> dict:
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        return P.scan_spec_escalations(spec, P.escalation_union(root)["union"])

    def test_the_procedure_shape_scans_nothing_and_says_so(self):
        """The finding itself. `verdict` is still `pass` — this fix reports,
        it does not refuse — but `scanned` now distinguishes that `pass` from
        a real one."""
        out = self.scan(BULLET_SPEC)
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["touches"], {})
        self.assertTrue(out["armed"], "the fixture hook must be armed, or "
                                      "this test proves nothing")
        self.assertEqual(out["scanned"], [],
                         "a spec written to the documented schema scanned "
                         "nothing and the result did not say so")

    def test_a_sectioned_spec_names_the_sections_it_offered(self):
        out = self.scan(SECTION_SPEC)
        self.assertEqual(out["scanned"], ["Deliverable", "Out of scope"])
        self.assertEqual(out["scope_scanned"], ["Deliverable"])
        self.assertEqual(out["refuse"], ["state-schema.json"])

    def test_out_of_scope_alone_is_not_scope(self):
        """`Out of scope` can only ever green-light. A spec offering that
        section and neither touch section still presented the gate zero scope,
        so `scope_scanned` — what `--specs` reports on — stays empty."""
        out = self.scan("# T\n\n## Out of scope\n\n- `claims`\n")
        self.assertEqual(out["scanned"], ["Out of scope"])
        self.assertEqual(out["scope_scanned"], [])

    def test_an_empty_section_does_not_count_as_scanned(self):
        """A heading with nothing under it is a heading, not scope. `_section`
        returns the empty string either way, so counting the heading alone
        would report a scan that did not happen."""
        out = self.scan("# T\n\n## Deliverable\n\n## Verification\n\n- x\n")
        self.assertEqual(out["scope_scanned"], [])

    def test_the_gate_prints_scanned_beside_its_verdict(self):
        """The dispatcher reads JSON from `--escalation-scan`, and this is the
        surface where `pass` over nothing was indistinguishable from `pass`.
        Exit code is deliberately unchanged: 0, as before."""
        root = Path(tempfile.mkdtemp())
        (root / ".perry").mkdir()
        (root / ".perry" / "config.md").write_text("# Config\n")
        (root / ".perry" / "hook.md").write_text(HOOK)
        spec = root / "spec.md"
        spec.write_text(BULLET_SPEC)
        r = subprocess.run(
            [sys.executable, str(STATE), "--root", str(root),
             "--escalation-scan", str(spec)],
            capture_output=True, text=True)
        out = json.loads(r.stdout)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["scanned"], [])
        # Both fragments the fixture hook declares were live and matched
        # nothing, because there was nothing to match against.
        self.assertEqual(out["fragments_scanned"], 2)


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
        self.assertEqual([f["rule"] for f in out["findings"]],
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
        self.assertEqual((out["unscannable"], out["count"]), (0, 0))
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
    copy is how a report keeps describing a scan that changed underneath it —
    the same defect `ESCALATION_TOUCHES`' own comment records for the i18n
    table, and `test_escalation_boundaries` guards for the matcher."""

    def test_the_linter_reads_the_gates_list(self):
        src = LINT.read_text(encoding="utf-8")
        self.assertIn("P.ESCALATION_TOUCHES", src)
        self.assertIn("P.scan_spec_escalations", src)
        start = src.index("def check_specs")
        body = src[start:src.index("\n#: How many drifted rows", start)]
        for literal in ('"Files in scope"', "'Files in scope'",
                        '"Deliverable"', "'Deliverable'"):
            self.assertNotIn(
                literal, body,
                "check_specs spells a scanned section itself — it must read "
                "P.ESCALATION_TOUCHES so the gate and its report cannot "
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
                         {"specs": 1, "unscannable": 1, "checked": True})
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
                         {"specs": 1, "unscannable": 0, "checked": True})
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

    def test_dispatch_step_4_gives_scope_scanned_a_reader(self):
        """The asymmetry this round is about: the empty-HOOK half had an exit
        code, a `dispatch.md` paragraph and a mandatory go-ahead in chat; the
        empty-SPEC half had two JSON keys no procedure read."""
        src = visible(self.DISPATCH.read_text(encoding="utf-8"))
        step4 = src[src.index("4. **Safety re-validation**"):
                    src.index("5. Spec contains a `Subjective verification:")]
        self.assertIn("scope_scanned", step4)
        self.assertIn("explicit go-ahead in chat", step4)
        # And the exit code is NOT changed. A new one would refuse dispatch on
        # 45 of 135 existing specs on the spot — an operational decision
        # nobody took. `bin/perry-state § SCAN_EXIT` is untouched.
        self.assertIn("exit code is still 0", step4)

    def test_the_exit_codes_are_unchanged(self):
        state_src = (PERRY_HOME / "bin" / "perry-state").read_text(
            encoding="utf-8")
        self.assertIn('SCAN_EXIT = {"pass": 0, "refuse": 3, "unarmed": 4}',
                      state_src)


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

    def test_a_localized_spec_still_scans(self):
        """The property the removed call was said to protect, tested directly
        rather than asserted in a comment."""
        out = P.scan_spec_escalations(
            self.zh_spec(), P.escalation_union(self.hooked())["union"])
        self.assertEqual(out["scope_scanned"], ["Deliverable"])
        self.assertEqual(out["verdict"], "refuse")

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
    #: So the rule block is pinned to exactly these bytes. Any addition,
    #: removal or rewording reddens, including ones nobody predicted. Changing
    #: the rule now means changing this constant in the same commit, which is
    #: the friction a rule this expensive should carry. Same move this project
    #: chose in `USER-904` (one `header_index` instead of a smarter detector)
    #: and `USER-906` (one invariant instead of a fourth predicate): a small
    #: exact surface beats a clever filter.
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

        **This slice is 5 lines of a 62-line section**, which round 2 named as
        a defect in its own right: a retraction one line below it was invisible
        by construction. It is kept only because `test_the_rule_is_pinned_verbatim`
        now covers the block itself; the hedge scan below is a second, cheaper
        signal that gives a readable failure message, never the primary one.
        """
        src = self.seen(self.DISPATCH)
        start = src.index("## The tree the agent works in")
        return src[start:src.index("\n\n", src.index(">", start))]

    def test_the_rule_is_pinned_verbatim(self):
        """The primary guard. See `RULE` for why it is an allowlist."""
        self.assertEqual(self.rule_block(), self.RULE)

    #: The NORMATIVE regions — what the rule commands, as opposed to the prose
    #: that explains why. Pinned by digest rather than by literal: 3,306
    #: characters of embedded prose would be unreadable here and is exactly the
    #: kind of hand-copied fixture that drifts from the file it mirrors.
    #:
    #: **Rationale is deliberately NOT pinned.** The two observed failures, the
    #: measured `git` output and the argument for the local merge can all be
    #: improved without touching a test. What cannot change silently is what an
    #: agent is *told to do*. That line — normative pinned, explanatory free —
    #: is the reason this is three regions and not the whole 62-line section.
    #:
    #: Re-pinning is meant to cost a deliberate second edit. When one of these
    #: fails, read the diff it prints, decide whether the rule really changed,
    #: and update the digest in the same commit as the prose.
    NORMATIVE = {
        "dispatch.md § what each side does":
            "16b0febc04bfab7b11ffcde73146049146e90b9a75206736d3b9fb3bc101078b",
        "git-boundaries.md § Rules":
            "2d56156ad289be0f26111c83193701f44769846fe445cb337a6928d7ff480d27",
        "git-boundaries.md § role table":
            "994e2a695a846a4130c00b07fece4a7c4d26dc1687c17c76ded0c145b066b772",
        "delegate.md § code-work block":
            "f18669a9d13a6d5ecc3b91ab7fed66dd538acffed082f26d561659fb88fc6074",
    }

    def normative_regions(self) -> dict:
        D, B, G = (self.seen(p) for p in
                   (self.DISPATCH, self.BOUNDARIES, self.DELEGATE))
        return {
            "dispatch.md § what each side does": D[
                D.index("**What each side does.**"):
                D.index("**The merge cannot be delegated")].rstrip(),
            "git-boundaries.md § Rules": B[
                B.index("- **Coding Agent commits its own work.**"):
                B.index("- **No agent merges its own work.**")].rstrip(),
            "git-boundaries.md § role table": B[
                B.index("| Role | Works in |"):
                B.index("### Rules")].rstrip(),
            "delegate.md § code-work block": G[
                G.index("- **Work in its own worktree**"):
                G.index("- If a permitted push or PR fails")].rstrip(),
        }

    def test_the_normative_bullets_are_pinned(self):
        """Round 2 walked past the property check with two synonyms —
        `publishes its feature branch … raises a pull request` — restoring in
        full the order the scope was widened to remove. A regex over four
        surface forms is a denylist; this is not."""
        for name, text in self.normative_regions().items():
            with self.subTest(region=name):
                got = hashlib.sha256(text.encode("utf-8")).hexdigest()
                self.assertEqual(
                    got, self.NORMATIVE[name],
                    f"\n{name} changed. If the rule really changed, re-pin it "
                    f"deliberately: {got}\n--- current text ---\n{text}\n")

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


if __name__ == "__main__":
    unittest.main()
