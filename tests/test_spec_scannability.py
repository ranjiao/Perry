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
132 on the live branch, 45 of the 119 this branch was cut from — every one of
them `pass` over a fully armed 35-fragment union. None of the 45 uses the
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


if __name__ == "__main__":
    unittest.main()
