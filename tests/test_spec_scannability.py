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
        src = self.SUB.read_text(encoding="utf-8")
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
        src = self.SUB.read_text(encoding="utf-8")
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
        src = self.DISPATCH.read_text(encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
