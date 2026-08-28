"""TASK-119 — `perry-goals link`, the writer `phase/<NNN>-linkage.md` was
documented as having and did not have.

`goals/SKILL.md § State files` has called that file **"machine-written"** since
the lane shipped, and `goals/reference/linkage.md` documents `link`, `--alias`,
`--unlinked` and `--project` as how it is maintained. Until this row there was
no `link`: this repository's own `perry/phase/002-linkage.md` was typed by hand
on 2026-08-20, every edge and every number.

Two properties decide whether the writer is worth having, and both are asserted
here as **bytes**, not as parses:

1. **A write leaves every byte it did not touch unchanged.** The corpus is this
   repository's own registers plus the shipped fixture, never a file this test
   generated — the same rule `tests/test_goals_writer.py` follows for `OKR.md`,
   and it binds harder here. `OKR.md` is prose a human argued with, so a
   re-render loses wording somebody would notice. This file is read by machines
   on both sides, so a re-render loses a KEY, and the result still parses and
   still lints. Nobody notices.

2. **The writer cannot create the state `perry-lint` rejects.** A task under two
   KRs is `linkage-task-single-kr`, and a refusal that leaves the file untouched
   is the only acceptable answer — asserted by re-running the linter's own check
   on the file afterwards, not by trusting the exit code.

And the defect TASK-120 handed over: **no invented `current`.** An unasserted
`current` is absent, never `0`, because most KRs here drive a count DOWN and a
zero reads as met on the day the register is written.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOALS = ROOT / "bin" / "perry-goals"
STATE = ROOT / "bin" / "perry-state"
TEMPLATE = ROOT / "goals" / "state" / "linkage_TEMPLATE.md"

sys.path.insert(0, str(ROOT / "viewer"))
import parsers as P  # noqa: E402


def _load(name: str, as_name: str):
    spec = importlib.util.spec_from_loader(
        as_name, importlib.machinery.SourceFileLoader(as_name, str(ROOT / "bin" / name)))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[as_name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("perry-goals", "perry_goals_for_linkage")
LINT = _load("perry-lint", "perry_lint_for_linkage")
SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text())
LINT.load_glossary(SCHEMA)
LINKAGE_SPEC = next(f for f in SCHEMA["files"] if f["id"] == "linkage")

#: The corpus, in the repository, on every machine — and it disagrees with
#: itself about the two things a line editor can get wrong. Perry's own two
#: registers quote every flow item (`tasks: ["TASK-038"]`); the shipped fixture
#: quotes none of them (`tasks: [REL-001]`, `aliases: [deploy-hardening]`) and
#: writes `agents:` as a block list. A writer that normalised either style into
#: the other would pass a round-trip test on a file it had rewritten.
CORPUS = [
    ROOT / "perry" / "phase" / "002-linkage.md",
    ROOT / "perry" / "phase" / "001-linkage.md",
    ROOT / "tests" / "fixtures" / "sample-project" / "phase" / "002-linkage.md",
]


def first_kr(model) -> str:
    """A KR id read out of the register under test, never typed here.

    Everything in the corpus is a REAL register, and `tests/
    live_state_expectations.py` is the standing guard about what a test may
    then say about one: a literal that enumerates what this project happens to
    hold today is a check that goes red when the project moves, for no reason
    anyone can act on. So the corpus tests below assert *properties of the
    write* — how many lines moved, which bytes survived — and take every id
    they need from the file itself. The behavioural assertions, the ones that
    have to name an id, run against `SYNTHETIC` instead."""
    return [k.id for o in model.objectives for k in o.krs][0]


def a_linked_task(model) -> tuple[str, str]:
    """(task id, the KR that already claims it), out of the register."""
    for o in model.objectives:
        for k in o.krs:
            if k.tasks:
                return k.tasks[0], k.id
    raise AssertionError("the corpus register declares no edge")


def another_kr(model, not_this: str) -> str:
    return [k.id for o in model.objectives for k in o.krs if k.id != not_this][0]


def changed_lines(before: str, after: str) -> list[tuple[int, str, str]]:
    """Every line index whose bytes differ, compared positionally.

    Positional on purpose: this is the byte compare the spec asks for, and it
    only holds when the write inserted and deleted nothing. `line_delta` below
    is asserted separately, so an insert cannot hide inside this list.
    """
    b, a = before.split("\n"), after.split("\n")
    return [(i, x, y) for i, (x, y) in enumerate(zip(b, a)) if x != y]


def lint_findings(path: pathlib.Path) -> list[str]:
    """`perry-lint`'s own rules for this file, run in process.

    The linter's check, not a re-implementation of it — "the writer cannot
    create a task under two KRs" has to be asserted with the same predicate
    that would reject the file, or the two can drift apart in exactly the way
    this project keeps finding."""
    return [f.rule for f in LINT.check_frontmatter(
        path, path.name, LINKAGE_SPEC, SCHEMA["enums"], is_template=False)]


class Project:
    """A throwaway project with one linkage register. Never the Perry repo."""

    def __init__(self, register: str, slug: str = "002-fields-are-typed"):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="perry-link-test-"))
        (self.dir / "phase").mkdir()
        (self.dir / ".perry").mkdir()
        (self.dir / "phase" / "CURRENT").write_text(slug)
        self.path = self.dir / "phase" / f"{slug.split('-')[0]}-linkage.md"
        self.path.write_text(register)

    @classmethod
    def of(cls, source: pathlib.Path) -> "Project":
        """A copy of a real register, under its own phase number."""
        return cls(source.read_text(), f"{source.name.split('-')[0]}-x")

    def run(self, *argv, expect=None, **env):
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        e.update(env)
        p = subprocess.run([sys.executable, str(GOALS), *argv, "--root", str(self.dir)],
                           capture_output=True, text=True, env=e)
        if expect is not None:
            assert p.returncode == expect, (p.returncode, p.stdout, p.stderr)
        return p

    def link(self, *argv, expect=0, **env):
        return self.run("link", *argv, expect=expect, **env)

    def text(self) -> str:
        return self.path.read_text()

    def model(self):
        return P.parse_linkage(self.text())

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def sample_project(case: unittest.TestCase) -> pathlib.Path:
    """A copy of the shipped fixture — a whole project, not just a register.

    `perry-state` reports the sections a project HAS, so a temp directory
    holding one file has no `linkage` section to read and a test asserting
    about it would pass on an empty payload."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="perry-link-fixture-"))
    case.addCleanup(shutil.rmtree, d, ignore_errors=True)
    shutil.copytree(ROOT / "tests" / "fixtures" / "sample-project", d / "p")
    (d / "p" / ".perry").mkdir(exist_ok=True)
    return d / "p"


class Case(unittest.TestCase):
    def project(self, *a, **kw) -> Project:
        p = Project(*a, **kw)
        self.addCleanup(p.cleanup)
        return p

    def corpus(self, source: pathlib.Path) -> Project:
        p = Project.of(source)
        self.addCleanup(p.cleanup)
        return p


# ── 1. the byte gate ──────────────────────────────────────────────────────


class TestAWriteTouchesTwoLines(Case):
    """Verification 1: proved with a byte compare, not with a parse."""

    def test_an_edge_changes_the_tasks_line_and_updated_and_nothing_else(self):
        for source in CORPUS:
            with self.subTest(register=source.name):
                p = self.corpus(source)
                before = p.text()
                p.link("ZZZ-001", first_kr(P.parse_linkage(before)))
                after = p.text()
                self.assertEqual(len(before.split("\n")), len(after.split("\n")),
                                 "an edge inserted or removed a line")
                diff = changed_lines(before, after)
                self.assertEqual(len(diff), 2, diff)
                keys = sorted(line.strip().split(":")[0] for _, line, _ in diff)
                self.assertEqual(keys, ["tasks", "updated"], diff)
                self.assertIn("ZZZ-001", diff[0][2] + diff[1][2])
                # and the untouched bytes, stated as bytes: put the two old
                # lines back and the file is the file that was read.
                restored = after.split("\n")
                for i, old, _ in diff:
                    restored[i] = old
                self.assertEqual("\n".join(restored), before)

    def test_the_registers_own_quoting_style_survives(self):
        """Perry's registers quote their task ids; the fixture's do not.

        A writer with one opinion about quoting would rewrite the other file's
        list on the first edge — a line it was asked to append to, reformatted
        around the append. Both are read identically, so neither is wrong, and
        that is exactly why the writer may not choose."""
        quoted = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        quoted.link("ZZZ-001", first_kr(quoted.model()))
        self.assertIn('"ZZZ-001"', quoted.text())

        bare = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "phase" / "002-linkage.md")
        bare.link("ZZZ-001", first_kr(bare.model()))
        line = [ln for ln in bare.text().split("\n") if "ZZZ-001" in ln][0]
        self.assertIn("[REL-001, ZZZ-001]", line)
        self.assertNotIn('"', line)

    def test_a_block_list_is_appended_to_as_a_block_list(self):
        """`tasks:` written as `- ` lines gets one more `- ` line."""
        p = self.project(BLOCK_STYLE)
        before = p.text()
        p.link("ZZZ-001", "P002-O1-KR1")
        after = p.text().split("\n")
        self.assertEqual(len(after), len(before.split("\n")) + 1)
        at = after.index("          - AAA-001")
        self.assertEqual(after[at + 1], "          - ZZZ-001",
                         "the new item did not land beside its neighbour")
        self.assertNotIn("[", after[at - 1])

    def test_every_refusal_leaves_the_file_byte_identical(self):
        """Seven refusals over the real register, each asserted as bytes.

        The ids come out of the file (`a_linked_task`), so this stays a
        statement about the writer when the project's own edges change."""
        model = P.parse_linkage(
            (ROOT / "perry" / "phase" / "002-linkage.md").read_text())
        linked, holder = a_linked_task(model)
        for argv in (["ZZZ-001", "P002-O9-KR9"],
                     [linked, another_kr(model, holder)],
                     ["--unlinked", linked],
                     ["--alias", "NOPE-001", "a name"],
                     ["--project", "NEW-001", "P002-O9-KR9", "a name"],
                     ["ZZZ-001"],
                     ["ZZZ-001", first_kr(model), "extra"]):
            with self.subTest(argv=argv):
                p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
                before = p.text()
                r = p.link(*argv, expect=1)
                self.assertEqual(p.text(), before)
                self.assertIn("Nothing was written", r.stderr)

    def test_a_second_identical_edge_writes_nothing_at_all(self):
        """Not even `updated`. A no-op that re-stamped the register would
        report the whole graph as freshly asserted on a run that changed
        nothing — the same lie `current: 0` tells one field over."""
        p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        kr = first_kr(p.model())
        p.link("ZZZ-001", kr)
        once = p.text()
        r = p.link("ZZZ-001", kr, expect=0)
        self.assertEqual(p.text(), once)
        self.assertIn("nothing to write", r.stdout)

    def test_a_dry_run_writes_nothing_and_prints_the_lines(self):
        p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        before = p.text()
        r = p.link("ZZZ-001", first_kr(p.model()), "--dry-run", "--json",
                   expect=0)
        self.assertEqual(p.text(), before)
        out = json.loads(r.stdout)
        self.assertTrue(out["dry_run"])
        self.assertFalse(out["written"])
        self.assertTrue(any("ZZZ-001" in line for line in out["diff"]))


# ── 2. the refusals ───────────────────────────────────────────────────────


class TestTheRefusalFires(Case):
    """Verification 2. Each one names what it could not decide, and writes
    nothing — `perry-lint` already rejects a task under two KRs, and the writer
    must not be able to produce that file in the first place."""

    def test_an_unresolvable_name_lists_the_phases_kr_ids(self):
        p = self.project(SYNTHETIC)
        r = p.link("ZZZ-001", "the store thing", expect=1)
        self.assertIn("is not a KR id, a Project id or a registered alias",
                      r.stderr)
        for kr in ("P002-O1-KR1", "P002-O1-KR2", "P002-O2-KR1"):
            self.assertIn(kr, r.stderr)
        self.assertIn("near-match is not a match", r.stderr)

    def test_a_kr_id_that_disagrees_with_its_nesting_is_refused(self):
        """`P002-O2-KR1` filed under `O1`, and the writer will not pick a side.

        This exists because the mutation matrix for TASK-180 found nothing
        holding the anchored `^P\\d{3}-(O\\d+)-KR\\d+$` in `link_edge`:
        reverting it to the pre-migration `^P-(O\\d+)\\.` left every module
        green, because `objective` silently falls back to the nesting and this
        refusal is the only reader that can tell the two apart. An id form the
        writer cannot parse is an id form whose disagreements it cannot see.
        """
        p = self.project(MISNESTED)
        before = p.text()
        r = p.link("--project", "NEW-001", "P002-O2-KR1", "a name", expect=1)
        self.assertEqual(p.text(), before, "a refusal wrote to the register")
        self.assertIn("encodes objective O2", r.stderr)
        self.assertIn("sits under O1", r.stderr)

    def test_an_ambiguous_name_names_its_candidates_and_writes_nothing(self):
        """Two Projects answering to one label, on two different KRs.

        The register `perry-lint` rejects — and a file the writer refuses to
        create can still be handed to it, which is the case that matters: the
        answer is the candidates, never the nearest one."""
        p = self.project(AMBIGUOUS)
        before = p.text()
        r = p.link("ZZZ-001", "shared name", expect=1)
        self.assertEqual(p.text(), before)
        self.assertIn("does not resolve to exactly one KR", r.stderr)
        self.assertIn("PROJ-A", r.stderr)
        self.assertIn("PROJ-B", r.stderr)
        self.assertIn("P002-O1-KR1", r.stderr)
        self.assertIn("P002-O1-KR2", r.stderr)
        self.assertIn("never by resemblance", r.stderr)

    def test_the_writer_cannot_put_one_task_under_two_krs(self):
        p = self.project(SYNTHETIC)
        self.assertNotIn("linkage-task-single-kr", lint_findings(p.path))
        p.link("ZZZ-001", "P002-O1-KR1")
        r = p.link("ZZZ-001", "P002-O2-KR1", expect=1)
        self.assertIn("already listed under P002-O1-KR1", r.stderr)
        self.assertIn("Move it, don't duplicate it", r.stderr)
        self.assertNotIn("linkage-task-single-kr", lint_findings(p.path))
        self.assertEqual(
            [k.id for o in p.model().objectives for k in o.krs
             if "ZZZ-001" in k.tasks], ["P002-O1-KR1"])

    def test_declaring_a_linked_task_unlinked_is_refused(self):
        p = self.project(SYNTHETIC)
        r = p.link("--unlinked", "AAA-001", expect=1)
        self.assertIn("attributed and drifting", r.stderr)

    def test_linking_a_declared_unlinked_task_undeclares_it(self):
        """One edit, not two: otherwise it renders as both at once."""
        p = self.project(SYNTHETIC)
        self.assertIn("BBB-002", p.model().unlinked)
        p.link("BBB-002", "P002-O1-KR2")
        model = p.model()
        self.assertNotIn("BBB-002", model.unlinked)
        self.assertEqual(model.kr_for_task("BBB-002"), "P002-O1-KR2")
        self.assertNotIn("linkage-task-single-kr", lint_findings(p.path))

    def test_an_alias_another_project_claims_is_refused(self):
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "phase" / "002-linkage.md")
        before = p.text()
        r = p.link("--alias", "REL-002", "Deploy script hardening", expect=1)
        self.assertEqual(p.text(), before)
        self.assertIn("already claimed by REL-001", r.stderr)
        self.assertIn("linkage-names-unique", r.stderr)

    def test_a_registered_alias_resolves_the_next_report_under_the_old_name(self):
        """What the registry is FOR: a name that drifted resolves to the same
        KR through a recorded alias, instead of through a resemblance."""
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "phase" / "002-linkage.md")
        p.link("ZZZ-001", "deploy-hardening")
        self.assertEqual(p.model().kr_for_task("ZZZ-001"), "P002-O1-KR1")

    def test_a_retired_project_is_named_rather_than_used(self):
        p = self.project(DROPPED)
        r = p.link("ZZZ-001", "PROJ-OLD", expect=1)
        self.assertIn("retired Project", r.stderr)
        self.assertIn("history, not an attribution", r.stderr)

    def test_a_new_project_derives_its_objective_and_keeps_the_linter_quiet(self):
        p = self.project(SYNTHETIC)
        p.link("--project", "PROJ-009", "P002-O2-KR1", "the reader cutover")
        entry = [x for x in p.model().projects if x.project_id == "PROJ-009"][0]
        self.assertEqual((entry.serves_kr, entry.objective, entry.status),
                         ("P002-O2-KR1", "O2", "active"))
        self.assertEqual(lint_findings(p.path), [])

    def test_a_project_id_already_in_the_graph_is_refused(self):
        p = self.corpus(
            ROOT / "tests" / "fixtures" / "sample-project" / "phase" / "002-linkage.md")
        r = p.link("--project", "REL-001", "P002-O1-KR1", "another name", expect=1)
        self.assertIn("already in this phase's graph", r.stderr)


# ── 3. no invented number ─────────────────────────────────────────────────


class TestNoInventedCurrent(Case):
    """Verification 3, and TASK-120's hand-over.

    `goals/state/linkage_TEMPLATE.md` wrote `current: 0` into every register a
    project ever created. Six of eight phase KRs on THIS project carry
    `target: 0` — they drive a count down — so that default made every one of
    them read as met on the day the register was written. Re-inserting it
    reddens the first test here, which reads the shipped template and nothing
    else."""

    def test_the_shipped_template_asserts_no_current(self):
        front, _ = P.split_frontmatter(TEMPLATE.read_text())
        offenders = [ln for ln in front.split("\n")
                     if re.match(r"^\s*current\s*:", ln)]
        self.assertEqual(offenders, [], "the template asserts a `current`")

    def test_a_register_made_from_the_template_carries_no_current(self):
        p = self.project(instantiate(TEMPLATE.read_text()))
        p.link("ZZZ-001", "P002-O1-KR1")
        for kr in [k for o in p.model().objectives for k in o.krs]:
            self.assertIsNone(kr.current, kr.id)
        front, _ = P.split_frontmatter(p.text())
        self.assertEqual([ln for ln in front.split("\n")
                          if re.match(r"^\s*current\s*:", ln)], [])

    def test_perry_reports_that_current_as_unasserted_and_not_as_zero(self):
        """The whole point of the default TASK-120 named: `0` and "nobody has
        said" are different facts, and only one of them can be `target: 0`
        met."""
        root = sample_project(self)
        (root / "phase" / "002-linkage.md").write_text(
            instantiate(TEMPLATE.read_text()))
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        run = subprocess.run(
            [sys.executable, str(GOALS), "link", "ZZZ-001", "P002-O1-KR1",
             "--root", str(root)], capture_output=True, text=True, env=e)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(subprocess.run(
            [sys.executable, str(STATE), "--json", "--section", "linkage",
             "--root", str(root)], capture_output=True, text=True,
            env=e).stdout)["linkage"]
        kr = [k for o in out["objectives"] for k in o["krs"]
              if k["id"] == "P002-O1-KR1"][0]
        self.assertIsNone(kr["current"])
        self.assertEqual(kr["current_provenance"]["state"], "unasserted")
        self.assertEqual(kr["current_provenance"]["asserted_at"], "")
        self.assertFalse(kr["current_staleness"]["stale"])

    def test_the_writer_never_writes_target_or_current(self):
        """Asserted over every write path, as text: neither key may appear on
        a line this tool added or changed."""
        p = self.project(SYNTHETIC)
        for argv in (["ZZZ-001", "P002-O1-KR1"],
                     ["--unlinked", "ZZZ-002"],
                     ["--project", "PROJ-009", "P002-O2-KR1", "a project"],
                     ["--alias", "PROJ-009", "another name"]):
            with self.subTest(argv=argv):
                out = json.loads(p.link(*argv, "--json", expect=0).stdout)
                added = [ln[5:] for ln in out["diff"] if ln.startswith("+")]
                self.assertTrue(added)
                for line in added:
                    self.assertNotRegex(line, r"^\s*(target|current)\s*:")


# ── 4. what Perry reads back ──────────────────────────────────────────────


class TestPerryReadsWhatTheWriterWrote(Case):
    """Verification 4: through `perry-state --section linkage`, with TASK-120's
    provenance keys resolving."""

    def setUp(self):
        self.root = sample_project(self)

    def tool(self, tool: pathlib.Path, *argv):
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        return subprocess.run([sys.executable, str(tool), *argv,
                               "--root", str(self.root)],
                              capture_output=True, text=True, env=e)

    def test_the_edge_the_writer_wrote_is_the_edge_perry_reports(self):
        w = self.tool(GOALS, "link", "ZZZ-001", "P002-O1-KR2")
        self.assertEqual(w.returncode, 0, w.stderr)
        out = json.loads(self.tool(
            STATE, "--json", "--section", "linkage").stdout)["linkage"]
        kr = [k for o in out["objectives"] for k in o["krs"]
              if k["id"] == "P002-O1-KR2"][0]
        self.assertIn("ZZZ-001", kr["tasks"])
        self.assertEqual(kr["current_provenance"]["asserted_scope"], "register")
        self.assertEqual(kr["current_provenance"]["source"], "linkage-register")
        self.assertEqual(kr["current_provenance"]["asserted_at"][:4], "20" + "26"[:2])
        self.assertIn("evaluated", kr["current_staleness"])

    def test_a_declared_unlinked_task_stops_being_drift_when_it_is_linked(self):
        """The read side of the same edge, and of the same-edit rule: a task
        the register declared unlinked is reported as drift until an edge is
        written, and must not be reported as both afterwards."""
        def attribution():
            return json.loads(self.tool(STATE, "--json", "--section",
                                        "attribution").stdout)["attribution"]
        before = attribution()
        self.assertEqual([t["id"] for t in before["unlinked"]], ["REL-009"])
        self.assertEqual(before["declared_unlinked"], ["REL-009"])
        w = self.tool(GOALS, "link", "REL-009", "P002-O2-KR1")
        self.assertEqual(w.returncode, 0, w.stderr)
        after = attribution()
        self.assertEqual(after["linked"], before["linked"] + 1)
        self.assertEqual(after["unlinked"], [])
        self.assertEqual(after["declared_unlinked"], [])


# ── 5. `updated`, and the field it is doing double duty as ────────────────


class TestUpdated(Case):

    def test_it_is_bumped_to_a_full_iso_datetime(self):
        p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        p.link("ZZZ-001", first_kr(p.model()))
        self.assertRegex(p.model().updated,
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_re_dating_someone_elses_assertion_is_reported_not_absorbed(self):
        """The one thing this writer makes worse, said out loud on every run.

        `asserted_at` is read from `updated` at `asserted_scope: "register"` —
        there is no per-KR assertion date — so an edge appended to one KR moves
        the staleness reference of every asserted `current` in the file. The
        fix is a new field in `schema/state-schema.json`, which is a decision
        the user makes; naming the ids on every write is what keeps it from
        being discovered as a silent number months from now."""
        p = self.project(SYNTHETIC)
        r = p.link("ZZZ-001", "P002-O1-KR1")
        self.assertIn("asserted_scope: register", r.stderr)
        self.assertIn("lose any staleness signal", r.stderr)
        self.assertIn("P002-O1-KR2", r.stderr)
        ids = json.loads(p.link("ZZZ-002", "P002-O1-KR2", "--json", expect=0).stdout)
        self.assertEqual(ids["current_assertions_redated"], ["P002-O1-KR2"])

    def test_a_register_with_no_asserted_current_says_nothing(self):
        p = self.project(instantiate(TEMPLATE.read_text()))
        r = p.link("ZZZ-001", "P002-O1-KR1")
        self.assertNotIn("staleness signal", r.stderr)


# ── 5b. a refusal says which of the values it means ───────────────────────


class TestARefusedValueIsLocated(Case):
    """TASK-037's rule, on the one `perry-goals` command with no flags.

    `bin/perry-goals § check_due` states it — *"the refusal says so and names
    the flag, so a user is never guessing where their words go"* — and every
    flag-carried value in `commit` now obeys it. `link` takes its values
    positionally (`goals/reference/linkage.md` writes the grammar that way),
    so there is no flag to name and `argument 1` was the whole of the answer:
    on `--project <PROJECT-ID> <KR-ID> "<name>"` that is a position to count
    out against a grammar the user has to go and find. The SLOT is named
    instead, read out of the same `usage` line the arity refusal prints.
    """

    def test_the_refusal_names_the_slot_not_just_a_position(self):
        p = self.project(SYNTHETIC)
        r = p.link("AAA-001\nsecond line", "P002-O1-KR1", expect=1)
        self.assertIn("<TASK-ID> (argument 1) contains a line break",
                      r.stderr)
        self.assertNotIn("was written", p.text())

    def test_each_shape_names_its_own_slots(self):
        """One list, four grammars. The slot names come from `usage`, so a
        grammar that changes cannot leave the refusal quoting the old one."""
        for argv, bad_at, slot in (
                (("{v}", "P002-O1-KR1"), 0, "<TASK-ID>"),
                (("AAA-009", "{v}"), 1, "<KR-ID>"),
                (("--unlinked", "{v}"), 1, "<TASK-ID>"),
                (("--alias", "PROJ-001", "{v}"), 2, "<the other name>"),
                (("--project", "{v}", "P002-O1-KR1", "n"), 1, "<PROJECT-ID>"),
                (("--project", "PROJ-009", "P002-O1-KR1", "{v}"), 3, "<name>")):
            with self.subTest(argv=argv):
                p = self.project(SYNTHETIC)
                r = p.link(*[a.format(v="a\nb") for a in argv], expect=1)
                position = bad_at - sum(1 for a in argv[:bad_at]
                                        if a.startswith("--"))
                self.assertIn(f"{slot} (argument {position + 1}) contains a "
                              f"line break", r.stderr)

    def test_a_quote_and_an_empty_value_are_located_the_same_way(self):
        """Three refusals share `check_writable`; all three carry the slot."""
        p = self.project(SYNTHETIC)
        self.assertIn("<KR-ID> (argument 2) contains a quote character",
                      p.link("AAA-009", 'P-"O1.1', expect=1).stderr)
        self.assertIn("<KR-ID> (argument 2) is empty",
                      p.link("AAA-009", "   ", expect=1).stderr)


# ── 6. what it refuses to edit at all ─────────────────────────────────────


class TestItRefusesWhatItCannotEditSafely(Case):

    def test_an_unreadable_register(self):
        p = self.project("---\nlinkage: 1\nobjectives:\n\tid: O1\n---\n")
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("cannot be read", r.stderr)

    def test_an_unfilled_template(self):
        p = self.project(TEMPLATE.read_text())
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("cannot be read", r.stderr)

    def test_crlf_is_refused_rather_than_mixed(self):
        p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        p.path.write_bytes(p.text().replace("\n", "\r\n").encode())
        r = p.link("ZZZ-001", first_kr(P.parse_linkage(
            p.path.read_bytes().decode())), expect=1)
        self.assertIn("CRLF", r.stderr)

    def test_no_current_phase(self):
        p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        (p.dir / "phase" / "CURRENT").write_text("")
        r = p.link("ZZZ-001", "P002-O1-KR1", expect=1)
        self.assertIn("no current phase", r.stderr)

    def test_a_value_the_reader_could_not_read_back(self):
        """The reader strips matching outer quotes and does nothing else — no
        escape processing at all — so a name carrying a quote character cannot
        round-trip. Refused, rather than written and half-read."""
        p = self.corpus(ROOT / "perry" / "phase" / "002-linkage.md")
        before = p.text()
        r = p.link("--project", "PROJ-009", first_kr(p.model()),
                   'the "real" name', expect=1)
        self.assertEqual(p.text(), before)
        self.assertIn("no escape processing", r.stderr)

    def test_it_still_refuses_another_lanes_file(self):
        """`SKILL.md § The hand-off contract`, unchanged by this row: `phase/`
        is this lane's, `BOARD.md` is not."""
        self.assertTrue(G.owned_by_goals("phase/002-linkage.md"))
        self.assertFalse(G.owned_by_goals("BOARD.md"))


# ── fixtures ──────────────────────────────────────────────────────────────


def instantiate(template: str) -> str:
    """The template with its placeholders filled, the way `plan-phase` does.

    Deliberately mechanical: what is under test is what the template does NOT
    contain, so anything this function added would be testing itself."""
    out = template.replace("{{NNN}}-{{slug}}", "002-a-phase")
    # The KR ids carry `{{NNN}}` too now (TASK-180: a phase-KR id names
    # its phase), and `plan-phase` fills that from the same number it
    # filled the slug from. Left to the catch-all below it would become
    # `Psome text-O1-KR1`, and the register would be testing a typo.
    out = out.replace("{{NNN}}", "002")
    out = out.replace("{{YYYY-MM-DD}}T{{HH:MM:SS}}Z", "2026-08-20T09:00:00Z")
    out = out.replace("{{PROJ-001}}", "PROJ-001")
    return re.sub(r"\{\{[^}]*\}\}", "some text", out)


#: The register the behavioural assertions run against: every id they name is
#: written here, so nothing this module claims can be falsified by this
#: project's own graph moving on. It carries the two shapes those assertions
#: need and the real registers happen to have today — a declared `unlinked`
#: entry, and two asserted `current` values — stated rather than borrowed.
SYNTHETIC = """---
linkage: 1
phase: "002-synthetic"
updated: "2026-08-20T09:00:00Z"
objectives:
  - id: O1
    title: "The first objective"
    krs:
      - id: P002-O1-KR1
        title: "A KR with an edge"
        metric: "1 of 1"
        target: 1
        tasks: ["AAA-001"]
      - id: P002-O1-KR2
        title: "A KR with an asserted current"
        metric: "0 occurrences (baseline 5)"
        target: 0
        current: 5
        tasks: []
  - id: O2
    title: "The second objective"
    krs:
      - id: P002-O2-KR1
        title: "A KR with no numbers at all"
        metric: "reported rather than honoured"
        tasks: []
unlinked: ["BBB-002"]
projects:
  - id: PROJ-001
    serves: P002-O1-KR1
    objective: O1
    name: "the first project"
    aliases: []
    status: active
---

# Phase #002 — synthetic
"""

#: A graph whose nesting contradicts its ids: `P002-O2-KR1` is filed under
#: `O1`. `perry-lint § linkage-objective-agrees` reports it; the writer refuses
#: to add a Project row to it rather than choosing which half is wrong.
MISNESTED = """---
linkage: 1
phase: "002-misnested"
updated: "2026-08-20T09:00:00Z"
objectives:
  - id: O1
    title: "The first objective"
    krs:
      - id: P002-O2-KR1
        title: "A KR filed under the wrong objective"
        metric: "1 of 1"
        target: 1
        tasks: []
unlinked: []
projects: []
---

# Phase #002 — misnested
"""

BLOCK_STYLE = """---
linkage: 1
phase: "002-block"
updated: "2026-08-20T09:00:00Z"
objectives:
  - id: O1
    title: "Written as block lists"
    krs:
      - id: P002-O1-KR1
        title: "A KR"
        metric: "some metric"
        tasks:
          - AAA-001
---

# Phase #002
"""

AMBIGUOUS = """---
linkage: 1
phase: "002-ambiguous"
updated: "2026-08-20T09:00:00Z"
objectives:
  - id: O1
    title: "Two projects, one label"
    krs:
      - id: P002-O1-KR1
        title: "First"
        metric: "m"
        tasks: []
      - id: P002-O1-KR2
        title: "Second"
        metric: "m"
        tasks: []
projects:
  - id: PROJ-A
    serves: P002-O1-KR1
    objective: O1
    name: "shared name"
    aliases: []
    status: active
  - id: PROJ-B
    serves: P002-O1-KR2
    objective: O1
    name: "another name"
    aliases: ["shared name"]
    status: active
---

# Phase #002
"""

DROPPED = """---
linkage: 1
phase: "002-dropped"
updated: "2026-08-20T09:00:00Z"
objectives:
  - id: O1
    title: "One retired project"
    krs:
      - id: P002-O1-KR1
        title: "A KR"
        metric: "m"
        tasks: []
projects:
  - id: PROJ-OLD
    serves: P002-O1-KR1
    objective: O1
    name: "retired"
    aliases: []
    status: dropped
---

# Phase #002
"""

if __name__ == "__main__":
    unittest.main(verbosity=2)
