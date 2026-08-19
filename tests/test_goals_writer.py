"""TASK-037's gate, and TASK-042's writer.

DESIGN-005 § 5.5 rates the `perry-goals` writer the riskiest of the markdown
three, for a reason no ordinary test catches — `OKR.md` is prose the user
argued with, and a writer that tidies it produces a file that still passes
`perry-lint` and no longer reads the way its author wrote it.

So the first half runs against the **real** files on this machine, not against
a fixture Perry generated. They disagree about almost everything and not one of
them is malformed.

The second half is `commit`, whose specification is
`goals/reference/phases.md § commit <promise>` rule for rule. Every assertion
about a write is made **as a diff** — which lines changed, and that no others
did — because "the file still contains the right value" is exactly the check
that passes on a writer which reformatted everything around it.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))


def _load():
    """`bin/perry-goals` has no `.py` suffix, so import it by path."""
    spec = importlib.util.spec_from_loader(
        "perry_goals",
        importlib.machinery.SourceFileLoader(
            "perry_goals", str(ROOT / "bin" / "perry-goals")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(ROOT / 'viewer'))
import tables as T  # noqa: E402

G = _load()
GOALS = ROOT / "bin" / "perry-goals"

#: In-repo files, always present. `CORPUS` adds the ones that only exist on a
#: machine where those projects are checked out.
IN_REPO = [
    ROOT / "perry" / "OKR.md",
    ROOT / "tests" / "fixtures" / "sample-project" / "OKR.md",
    ROOT / "goals" / "state" / "OKR_TEMPLATE.md",
]
ELSEWHERE = [
    pathlib.Path.home() / "proj" / "gimegime-pmo" / "OKR.md",
    pathlib.Path.home() / "proj" / "aimark" / "perry" / "OKR.md",
]


def goals_module():
    """`bin/perry-goals` as a module, for asserting on its patterns and on
    what TASK-091 deleted directly rather than through the CLI."""
    import importlib.machinery
    import importlib.util
    spec = importlib.util.spec_from_loader(
        "perry_goals_mod",
        importlib.machinery.SourceFileLoader(
            "perry_goals_mod", str(ROOT / "bin" / "perry-goals")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestByteIdentity(unittest.TestCase):
    """Load it, change nothing, write it back."""

    def test_the_in_repo_files_round_trip(self):
        for path in IN_REPO:
            self.assertTrue(path.exists(), f"{path} is gone; fix this list")
            with self.subTest(path=path.name):
                doc = G.Okr(path)
                self.assertEqual(path.read_text(), doc.render())
                self.assertTrue(doc.unchanged())

    def test_the_files_outside_the_repo_round_trip_when_present(self):
        """Skipped rather than failed when those projects are not checked out
        — but never silently: a skip that prints nothing is the same as a
        check that was never written."""
        found = [p for p in ELSEWHERE if p.exists()]
        if not found:
            self.skipTest(
                f"none of {[str(p) for p in ELSEWHERE]} present on this "
                f"machine; the in-repo corpus still ran")
        for path in found:
            with self.subTest(path=str(path)):
                self.assertEqual(path.read_text(), G.Okr(path).render())

    def test_the_corpus_actually_disagrees(self):
        """A round-trip test over three files written by the same template
        proves nothing. This asserts the corpus contains the shapes the gate
        is about, so it cannot quietly become uniform."""
        texts = [p.read_text() for p in IN_REPO + ELSEWHERE if p.exists()]
        joined = "\n".join(texts)
        self.assertRegex(joined, r"(?m)^### Objective \d+[:—-]",
                         "no objective heading in the corpus at all")
        self.assertGreaterEqual(
            len({t.count("\n## v") for t in texts}), 2,
            "every file in the corpus has the same number of versions, so "
            "the multi-version shape is not being exercised")

    def test_a_file_with_no_trailing_newline_round_trips(self):
        """`splitlines()` would silently absorb the difference between a file
        ending in a newline and one that does not, and write back the wrong
        one. This is why `render` uses `split`/`join`."""
        import tempfile
        for text in ("# OKR\n\n## Mission\n\nship it",
                     "# OKR\n\n## Mission\n\nship it\n",
                     "# OKR\n\n## Mission\n\nship it\n\n\n"):
            with tempfile.TemporaryDirectory() as d:
                p = pathlib.Path(d) / "OKR.md"
                p.write_text(text)
                self.assertEqual(text, G.Okr(p).render(), repr(text))


class TestLocating(unittest.TestCase):
    """The section scanner, against the shapes the real files carry."""

    def okr(self, text: str):
        import tempfile
        self._d = tempfile.TemporaryDirectory()
        p = pathlib.Path(self._d.name) / "OKR.md"
        p.write_text(text)
        return G.Okr(p)

    NESTED = """# OKR

## v2: 2026-04-30

### Objective 1: 维持长期稳定收益

text

### Anti-Goals

- not this

## v4: 2026-05-29

### Objective 1: Insurance
"""

    def test_a_version_section_swallows_the_headings_beneath_it(self):
        """gimegime-pmo nests `### Anti-Goals` inside a version. A scanner
        that stopped at any heading would cut that version in half and a
        writer would then append into the middle of it."""
        o = self.okr(self.NESTED)
        lo, hi = o.section(r"v2\b")
        body = "\n".join(o.lines[lo:hi])
        self.assertIn("Anti-Goals", body)
        self.assertNotIn("v4", body)

    def test_a_missing_section_is_refused_not_guessed(self):
        o = self.okr(self.NESTED)
        self.assertFalse(o.has_section(r"Commitments"))
        with self.assertRaises(G.Refused):
            o.section(r"Commitments")

    def test_rows_key_by_header_not_position(self):
        """The defect `schema/README.md` names outright: columns resolve by
        name, never by position."""
        o = self.okr("""# OKR

## Commitments

| Id | Track | Promise | To whom | By when | Status |
|---|---|---|---|---|---|
| ops/1 | ops | Invoices reconciled | Finance | within the track SLA | active |
""")
        lo, hi = o.section(r"Commitments")
        rows = o.rows(lo, hi)
        self.assertEqual(1, len(rows))
        _, cells = rows[0]
        self.assertEqual("ops/1", cells["id"])
        self.assertEqual("Finance", cells["to whom"])
        self.assertEqual("within the track SLA", cells["by when"])

    def test_a_decorated_header_still_resolves(self):
        o = self.okr("""# OKR

## Commitments

| **Id** | **Track** | `Promise` |
|---|---|---|
| ops/1 | ops | Invoices reconciled |
""")
        lo, hi = o.section(r"Commitments")
        self.assertEqual("ops/1", o.rows(lo, hi)[0][1]["id"])


TRACKS = """# Perry configuration

- Document language: English
- Repo layout: single

## Tracks

| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |
|---|---|---|---|---|---|---|---|
| ops | queue | commitments | intake -> doing | — | 5d | weekly | V2 |
| rel | pipeline | commitments | draft -> shipped | 3 | 10d | weekly | V3 |
| bare | queue | commitments | intake -> doing | — |  | weekly | V2 |
| main | project | okr | — | — | — | — | V2 |
"""

BARE_OKR = """# OKR — fixture

## Mission

Ship it.

## Anti-Goals

- not this

## Versioning log

- v1: 2026-08-01 — initial.
"""

#: Deliberately hand-aligned, and deliberately NOT in the schema's column
#: order — a writer that places cells by position rather than by resolved name
#: fills `To whom` with a date here and the test says so.
#:
#: Post-TASK-091 it carries `Due` and **no** `By when note`: the note is
#: optional, most registers will not have it, and every widening path is
#: exercised by a table that starts without it.
ALIGNED = """# OKR — fixture

## Mission

Ship it.

## Commitments

> a note the user wrote

| Track | Id      | Promise                | To whom | Due        | Status | Discharged by |
|-------|---------|------------------------|---------|------------|--------|---------------|
| rel   | rel/1   | Release 2.0            | Users   | {past}     | active |               |
| ops   | ops/7   | Invoices reconciled    | Finance | 3d         | active | oldest-first  |

## Anti-Goals

- not this
"""

#: The same register as it was written **before** the split: one `By when`
#: column holding a date on one row and prose on the other. Every migration
#: test starts here, and so does every "this tool will not write into a
#: pre-split table" refusal.
PRE_SPLIT = """# OKR — fixture

## Mission

Ship it.

## Commitments

> a note the user wrote

| Id    | Track | Promise             | To whom | By when              | Status |
|-------|-------|---------------------|---------|----------------------|--------|
| rel/1 | rel   | Release 2.0         | Users   | 2027-01-01           | active |
| ops/7 | ops   | Invoices reconciled | Finance | within the track SLA | active |
| ops/8 | ops   | Statements filed    | Auditor | 3d                   | active |
| ops/9 | ops   | Ledger closed       | Finance | —                    | active |

## Anti-Goals

- not this
"""

#: The Chinese half of the same thing, and the reason the migration is
#: value-driven. `截止` is `Due`'s own Chinese spelling, so there is no header
#: cell to rename — only cells to route.
PRE_SPLIT_CN = """# OKR — 项目

## 使命

做出来。

## 承诺

| 编号 | 轨道 | 承诺内容 | 承诺对象 | 截止 | 状态 |
|---|---|---|---|---|---|
| ops/1 | ops | 对账 | 财务 | 下周期 | active |
| ops/2 | ops | 报表 | 审计 | 2027-01-01 | active |

## 反目标

- 不做这个
"""

#: The same table with the headers Perry's own glossary declares for zh. Note
#: `截止`, which the glossary maps from BOTH `Deadline` and `Due`.
CHINESE = """# OKR — 项目

## 使命

做出来。

## 承诺

| 编号 | 轨道 | 承诺内容 | 承诺对象 | 截止 | 状态 |
|---|---|---|---|---|---|
| ops/1 | ops | 对账 | 财务 | 3d | active |

## 反目标

- 不做这个
"""


class Project:
    """A throwaway project root. Never the Perry repo — a previous agent ran a
    writer against it and the test writes landed in Perry's real board."""

    def __init__(self, okr: str = BARE_OKR, tracks: str | None = TRACKS):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="perry-goals-test-"))
        self.okr_path = self.dir / "OKR.md"
        self.okr_path.write_text(okr)
        (self.dir / ".perry").mkdir()
        if tracks is not None:
            (self.dir / ".perry" / "config.md").write_text(tracks)

    def run(self, *argv, expect=None, **env):
        e = dict(os.environ, PERRY_CONFORMANCE="advisory", PERRY_HOME=str(ROOT))
        e.update(env)
        p = subprocess.run(
            [sys.executable, str(GOALS), *argv, "--root", str(self.dir)],
            capture_output=True, text=True, env=e)
        if expect is not None:
            assert p.returncode == expect, (p.returncode, p.stdout, p.stderr)
        return p

    def commit(self, *argv, expect=0, **env):
        return self.run("commit", *argv, expect=expect, **env)

    def text(self) -> str:
        return self.okr_path.read_text()

    def events(self) -> list[dict]:
        p = self.dir / ".perry" / "events.jsonl"
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().split("\n") if l.strip()]

    def changed_lines(self, before: str) -> list[tuple[str, str]]:
        """(old, new) for every line that is not byte-identical.

        Compared positionally after aligning on length, so an insert reports as
        one added line rather than shifting every line after it into the diff.
        """
        import difflib
        out = []
        for line in difflib.ndiff(before.split("\n"), self.text().split("\n")):
            if line.startswith("- "):
                out.append(("-", line[2:]))
            elif line.startswith("+ "):
                out.append(("+", line[2:]))
        return out

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class WriterCase(unittest.TestCase):
    def project(self, *a, **kw) -> Project:
        p = Project(*a, **kw)
        self.addCleanup(p.cleanup)
        return p


class TestCreatingACommitment(WriterCase):

    def test_a_create_appends_exactly_one_line_and_touches_nothing_else(self):
        """V3 in the spec: asserted as a diff, not as a grep. A writer that
        re-rendered the table would still contain the new row."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        before = p.text()
        p.commit("--track", "ops", "--promise", "Statements filed",
                 "--to", "Auditor", "--due", "3d")
        diff = p.changed_lines(before)
        self.assertEqual([d[0] for d in diff], ["+"], diff)
        self.assertIn("ops/8", diff[0][1])
        # every pre-existing line survives, in order and byte for byte
        after = p.text().split("\n")
        after.remove(diff[0][1])
        self.assertEqual(before.split("\n"), after)

    def test_cells_land_by_resolved_name_not_by_position(self):
        """`ALIGNED`'s header starts `| Track | Id |`, not `| Id | Track |`.
        Placing by position writes the id into `Track` and every consumer of
        this register then follows a link that points at nothing."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        p.commit("--track", "ops", "--promise", "Statements filed",
                 "--to", "Auditor", "--due", "3d")
        row = [l for l in p.text().split("\n") if "ops/8" in l][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual("ops", cells[0])
        self.assertEqual("ops/8", cells[1])
        self.assertEqual("Auditor", cells[3])
        self.assertEqual("active", cells[5])

    def test_the_id_is_minted_per_track(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x",
                 "--due", "3d")
        p.commit("--track", "rel", "--promise", "b", "--to", "y",
                 "--due", "2027-01-01")
        p.commit("--track", "ops", "--promise", "c", "--to", "z",
                 "--due", "3d")
        ids = [e["id"] for e in p.events() if e["event"] == "commit"]
        self.assertEqual(["ops/1", "rel/1", "ops/2"], ids)

    def test_an_id_is_never_reused_after_its_row_is_deleted_by_hand(self):
        """`phases.md`: *ids are never reused and never renumbered*. A board
        row's `Commitment` cell points at this string; reusing a number does
        not dangle visibly, it silently re-points work at another promise."""
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        p.okr_path.write_text(
            "\n".join(l for l in p.text().split("\n") if "ops/1" not in l))
        p.commit("--track", "ops", "--promise", "b", "--to", "y", "--due", "3d")
        self.assertIn("ops/2", p.text())
        self.assertNotIn("ops/1 ", p.text())

    def test_a_note_on_a_table_without_the_column_widens_it_and_says_so(self):
        """`By when note` is optional, so most registers do not carry it.
        Adding it reaches lines the caller did not name — the same edit as
        `Discharged by`, reported for the same reason."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        r = p.commit("--track", "ops", "--promise", "Statements filed",
                     "--to", "Auditor", "--due", "3d",
                     "--by-when-note", "within the track SLA")
        self.assertIn("widened", r.stdout)
        self.assertIn("By when note", r.stdout)
        row = [l for l in p.text().split("\n") if "ops/8" in l][0]
        self.assertIn("within the track SLA", row)

    def test_status_is_active_and_discharged_by_is_left_empty(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        row = [l for l in p.text().split("\n") if "ops/1" in l][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual("active", cells[5])
        self.assertEqual("", cells[6])


class TestCreatingTheSection(WriterCase):

    def test_it_is_refused_when_no_track_is_pipeline_or_queue(self):
        """`OKR_TEMPLATE.md` says to omit the section entirely on an
        all-`project` project. Creating it because someone typed `commit`
        would add a spine to a shape that has no use for one."""
        only_project = TRACKS.replace("| ops | queue", "| ops | project") \
                             .replace("| rel | pipeline", "| rel | project") \
                             .replace("| bare | queue", "| bare | project")
        p = self.project(BARE_OKR, only_project)
        before = p.text()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--due", "3d", expect=1)
        self.assertIn("no track", r.stderr)
        self.assertEqual(before, p.text())

    def test_it_is_created_from_the_template_note_included(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        note = "> Promises to a named party by a date"
        self.assertIn(note, p.text())
        self.assertIn(note, (ROOT / "goals" / "state" / "OKR_TEMPLATE.md").read_text())
        # and not the template's placeholder row
        self.assertNotIn("{{track}}", p.text())

    def test_it_lands_before_anti_goals_and_leaves_every_other_line_alone(self):
        p = self.project()
        before = p.text()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        self.assertLess(p.text().index("## Commitments"),
                        p.text().index("## Anti-Goals"))
        for line in before.split("\n"):
            if line.strip():
                self.assertIn(line, p.text().split("\n"))

    def test_a_file_with_no_anti_goals_gets_the_section_at_the_end(self):
        p = self.project("# OKR\n\n## Mission\n\nShip it.\n")
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        self.assertTrue(p.text().startswith("# OKR\n\n## Mission\n\nShip it.\n"))
        self.assertIn("## Commitments", p.text())


#: Every phrase the five failed review rounds fought over, in both languages.
#:
#: Round 1 refused `3d`. Round 2 fixed the Chinese half and left the English.
#: Round 3 fixed the English half, broke eleven pairs that had agreed, and
#: admitted `上天保佑` ("god willing") and `这年头` ("nowadays"). Round 4
#: measured why: three hand-kept vocabularies that only looked paired. Round 5
#: found the last one — `\b` does not exist in Chinese, so `下周期` ("next
#: cycle") wrote a live commitment row while `next cycle` was refused.
#:
#: **Not one of them is a question any more.** None of these is an ISO date or
#: an SLA token, so every one is refused by `--due` — including the ones the
#: old rule accepted — and every one is accepted verbatim by `--by-when-note`,
#: because nothing looks at it. One rule, two fields, no vocabulary.
FOUGHT_OVER = [
    "within the track SLA", "same business day", "5 days", "next cycle",
    "soon", "ASAP", "when we get to it", "eventually", "best effort",
    "month by month", "end of quarter", "the weekend", "god willing",
    "下周期", "下周", "下周五", "每周一次", "每月两次", "在时限内",
    "五个工作日", "季度末", "月底", "尽快", "有空再说", "日后再说",
    "上天保佑", "这年头", "改天", "年后再说",
]


class TestDueIsTypedAndTheNoteIsNot(WriterCase):
    """`phases.md § commit` step 4, after ADR-007 decision 3.

    The old column asked *does this cell name a clock?* — a natural-language
    question, asked of a regex, five times. `Due` asks *is this cell an ISO
    date or an SLA token?*, which has one answer in every language, and the
    prose the old column also carried moved to a field nothing inspects.
    """

    def test_a_pipeline_track_refuses_anything_but_a_date(self):
        p = self.project()
        for value in ("when it is ready", "3d", "within the track SLA"):
            with self.subTest(value=value):
                r = p.commit("--track", "rel", "--promise", "a", "--to", "x",
                             "--due", value, expect=1)
                self.assertIn("must be an ISO date", r.stderr)

    def test_a_pipeline_track_refuses_a_date_that_is_not_one(self):
        p = self.project()
        p.commit("--track", "rel", "--promise", "a", "--to", "x",
                 "--due", "2026-02-30", expect=1)

    def test_a_date_with_prose_around_it_is_not_a_date(self):
        """The predecessor SEARCHED for a date, so `2026-09-30 or so` counted
        as one and triage compared a sentence against today. A typed field
        asks whether the WHOLE cell is a date."""
        p = self.project()
        r = p.commit("--track", "rel", "--promise", "a", "--to", "x",
                     "--due", "2027-01-01 or so", expect=1)
        self.assertIn("must be an ISO date", r.stderr)

    def test_due_accepts_a_date_and_the_sla_shorthand_and_nothing_else(self):
        p = self.project()
        for value in ("2027-01-01", "3d", "2w", "24h", "6m", "1y"):
            with self.subTest(value=value):
                p.commit("--track", "ops", "--promise", "a", "--to", "x",
                         "--due", value)

    def test_every_phrase_the_five_rounds_fought_over_is_refused_by_due(self):
        """**In BOTH languages, under ONE rule.** The fifth round's defect was
        that the two halves were matched under different rules; there is now
        one rule and it mentions no language."""
        p = self.project()
        for value in FOUGHT_OVER:
            with self.subTest(value=value):
                before = p.text()
                r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                             "--due", value, expect=1)
                self.assertIn("`Due` is typed", r.stderr)
                self.assertIn("--by-when-note", r.stderr,
                              "the refusal did not say where the words go")
                self.assertEqual(before, p.text())

    def test_every_phrase_the_five_rounds_fought_over_lands_in_the_note(self):
        """The other half, and the point of the split: nothing is lost. Each
        phrase is stored **verbatim**, and the pair `下周期` / `next cycle` —
        which round 5 judged differently — gets the same verdict here because
        no rule is applied to either."""
        for value in FOUGHT_OVER:
            with self.subTest(value=value):
                p = self.project()
                p.commit("--track", "ops", "--promise", "a", "--to", "x",
                         "--due", "3d", "--by-when-note", value)
                row = [l for l in p.text().split("\n") if "ops/1" in l][0]
                self.assertIn(value, row)

    def test_the_note_alone_is_not_a_commitment(self):
        """A note ABOUT a deadline is not a deadline. `--due` has no default
        and the note cannot stand in for it."""
        p = self.project()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by-when-note", "within the track SLA", expect=1)
        self.assertIn("--due is required", r.stderr)

    def test_the_retired_flag_is_refused_by_name(self):
        """`--by` fed one column holding two value spaces. Aliasing it to
        `--due` would refuse every standing commitment whose deadline was
        worded rather than dated, with a message about a flag nobody typed."""
        p = self.project()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--by", "within the track SLA", expect=1)
        self.assertIn("--by is gone", r.stderr)
        self.assertIn("--by-when-note", r.stderr)
        self.assertEqual([], p.events())

    def test_the_retired_flag_refuses_in_json_too(self):
        """A refusal raised while reading the flags has no `args` to ask about
        `--json`. Without the guard in `main` it exited through the
        module-level handler with empty stdout."""
        p = self.project()
        r = p.run("commit", "--json", "--track", "ops", "--promise", "a",
                  "--to", "x", "--by", "3d", expect=1)
        self.assertIn("--by is gone", json.loads(r.stdout)["refused"])

    def test_a_queue_track_with_no_sla_in_the_register_is_refused(self):
        """"within the track SLA" pointing at an empty register is a promise
        with no clock at all."""
        p = self.project()
        r = p.commit("--track", "bare", "--promise", "a", "--to", "x",
                     "--due", "3d", "--by-when-note", "within the track SLA", expect=1)
        self.assertIn("no `SLA`", r.stderr)
        self.assertNotIn("bare/1", p.text())

    def test_an_undeclared_track_is_refused(self):
        p = self.project()
        r = p.commit("--track", "ghost", "--promise", "a", "--to", "x",
                     "--due", "3d", expect=1)
        self.assertIn("not declared", r.stderr)

    def test_a_promise_to_nobody_is_routed_not_filed(self):
        """*A promise with no named party is a KR, and belongs under an
        Objective instead* — the refusal says where it goes."""
        p = self.project()
        r = p.commit("--track", "ops", "--promise", "a", "--due", "3d",
                     expect=1)
        self.assertIn("Objective", r.stderr)


class TestEndingOne(WriterCase):

    def start(self) -> Project:
        p = self.project(ALIGNED.format(past="2027-01-01"))
        return p

    def test_close_changes_one_cell_of_one_line(self):
        p = self.start()
        before = p.text()
        p.commit("--close", "ops/7")
        diff = p.changed_lines(before)
        self.assertEqual(1, len([d for d in diff if d[0] == "+"]), diff)
        old = [d[1] for d in diff if d[0] == "-"][0]
        new = [d[1] for d in diff if d[0] == "+"][0]
        self.assertEqual(old.replace("| active |", "| closed |"), new,
                         "the edit re-spaced cells it was not asked to change")

    def test_close_with_an_empty_discharged_by_is_refused(self):
        """*A promise closed with no account of how is indistinguishable from
        one abandoned quietly.*"""
        p = self.start()
        before = p.text()
        r = p.commit("--close", "rel/1", expect=1)
        self.assertIn("Discharged by", r.stderr)
        self.assertEqual(before, p.text())

    def test_close_fills_discharged_by_when_given_one(self):
        p = self.start()
        p.commit("--close", "rel/1", "--discharged-by", "shipped on the 30th")
        row = [l for l in p.text().split("\n") if "rel/1" in l][0]
        self.assertIn("shipped on the 30th", row)
        self.assertIn("closed", row)

    def test_miss_needs_a_reason(self):
        p = self.start()
        before = p.text()
        p.commit("--miss", "rel/1", expect=1)
        self.assertEqual(before, p.text())

    def test_miss_appends_to_discharged_by_rather_than_replacing_it(self):
        p = self.start()
        p.commit("--miss", "ops/7", "--reason", "the vendor went quiet")
        row = [l for l in p.text().split("\n") if "ops/7" in l][0]
        self.assertIn("oldest-first", row)
        self.assertIn("the vendor went quiet", row)
        self.assertIn("missed", row)

    def test_ending_a_row_twice_is_refused(self):
        p = self.start()
        p.commit("--close", "ops/7", "--discharged-by", "done")
        r = p.commit("--close", "ops/7", "--discharged-by", "done again",
                     expect=1)
        self.assertIn("already", r.stderr)

    def test_an_unknown_id_is_refused(self):
        p = self.start()
        p.commit("--close", "ops/999", "--discharged-by", "x", expect=1)


class TestAMissedCommitmentIsNeverSilentlyReDated(WriterCase):
    """*Editing `By when` on a promise whose date has passed erases the fact
    that it was missed, and the party it was made to is the one person who
    cannot see the edit.*"""

    def past(self) -> str:
        return f"{date.today() - timedelta(days=3):%Y-%m-%d}"

    def future(self) -> str:
        return f"{date.today() + timedelta(days=30):%Y-%m-%d}"

    def test_re_dating_a_past_due_active_row_is_refused(self):
        p = self.project(ALIGNED.format(past=self.past()))
        before = p.text()
        r = p.commit("--id", "rel/1", "--due", self.future(), expect=1)
        self.assertIn("--miss rel/1", r.stderr)
        self.assertEqual(before, p.text())

    def test_re_dating_a_row_still_in_the_future_is_allowed(self):
        """The refusal is about a promise that was MISSED, not about editing a
        date. A guard keyed on "is this an active row" would block the ordinary
        correction the procedure never forbade."""
        p = self.project(ALIGNED.format(past=self.future()))
        p.commit("--id", "rel/1", "--due",
                 f"{date.today() + timedelta(days=60):%Y-%m-%d}")

    def test_re_dating_a_past_due_row_that_was_already_missed_is_allowed(self):
        p = self.project(ALIGNED.format(past=self.past()))
        p.commit("--miss", "rel/1", "--reason", "slipped")
        p.commit("--id", "rel/1", "--due", self.future())

    def test_the_route_the_refusal_names_actually_works(self):
        p = self.project(ALIGNED.format(past=self.past()))
        p.commit("--miss", "rel/1", "--reason", "the build broke")
        p.commit("--track", "rel", "--promise", "Release 2.0",
                 "--to", "Users", "--due", self.future())
        self.assertIn("rel/2", p.text())
        self.assertEqual(
            2, sum(1 for e in p.events() if e["id"].startswith("rel/")))


class TestAHandEditIsReconciledNotOverwritten(WriterCase):
    """DESIGN-005 § 9: the log became canonical *before* this writer was built,
    and the cost the user accepted was that a hand edit *raises a reconcile
    prompt — never silently overwritten, and never silently authoritative*."""

    def edited(self) -> Project:
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        p.okr_path.write_text(
            p.text().replace("| ops/1 | ops | a | x | 3d | active |",
                             "| ops/1 | ops | a | x | 3d | closed |"))
        return p

    def test_a_row_the_log_disagrees_with_refuses(self):
        p = self.edited()
        before = p.text()
        r = p.commit("--miss", "ops/1", "--reason", "did not happen", expect=1)
        self.assertIn("by hand", r.stderr)
        self.assertIn("--accept-hand-edit", r.stderr)
        self.assertEqual(before, p.text())

    def test_accepting_takes_the_FILE_value_never_the_log_value(self):
        p = self.edited()
        p.commit("--miss", "ops/1", "--reason", "did not happen",
                 "--accept-hand-edit")
        last = p.events()[-1]
        self.assertEqual("closed", last["from"],
                         "the log's value was used instead of the file's")
        self.assertEqual("missed", last["to"])

    def test_a_row_the_log_has_never_heard_of_is_not_a_hand_edit(self):
        """Every Commitments table alive today was written by hand. Treating
        those rows as edits makes the first write on every real project a wall
        of reconcile prompts about work done correctly under the old rules."""
        p = self.project(ALIGNED.format(past="2027-01-01"))
        self.assertEqual([], p.events())
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")


class TestTheEventLog(WriterCase):

    def test_every_write_emits_one_event(self):
        p = self.project(ALIGNED.format(past="2027-01-01"))
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        p.commit("--close", "ops/7", "--discharged-by", "done")
        p.commit("--miss", "rel/1", "--reason", "slipped")
        p.commit("--id", "ops/8", "--promise", "a, revised")
        self.assertEqual(["commit", "commit-close", "commit-miss",
                          "commit-update"],
                         [e["event"] for e in p.events()])

    def test_no_event_name_collides_with_the_board_orphan_detector(self):
        """`perry-state § reconcile_drift` keys its orphan check on `add` /
        `route` and its close check on `done` / `drop`. A commitment id
        carrying one of those names would be reported as a task whose row went
        missing — a drift finding about a row that never existed."""
        self.assertFalse(set(G.COMMIT_EVENTS)
                         & {"add", "route", "done", "drop"})

    def test_a_refusal_writes_no_event(self):
        p = self.project()
        p.commit("--track", "ops", "--promise", "a", "--to", "x",
                 "--due", "soon", expect=1)
        self.assertEqual([], p.events())

    def test_the_okr_write_stands_even_when_the_event_cannot_be_appended(self):
        """`perry-task § commit` chose this failure direction and documents it:
        the canonical file never disagrees with itself, and the derived record
        may be missing. Losing an event costs history resolution; losing the
        write costs the truth."""
        p = self.project()
        (p.dir / ".perry" / "events.jsonl").mkdir()  # a directory, not a file
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--due", "3d")
        self.assertIn("ops/1", p.text())
        self.assertIn("warning", r.stderr)


class TestTheHandOffContract(WriterCase):
    """`SKILL.md § The hand-off contract`: *each lane reads the others' files
    freely; no lane writes outside its own.*"""

    #: The rule is a predicate over the whole filesystem, so this is a
    #: category, not the three files the contract happens to name. A guard
    #: shaped around `BOARD.md` / `journal/` / `DECISIONS.md` would pass a
    #: write to `weekly/` that the same sentence forbids for the same reason.
    FOREIGN = ["BOARD.md", "journal/2026-08/2026-08-17.md", "DECISIONS.md",
               "decisions/ADR-001-x.md", "PROJECT_STATE.md",
               "evidence/2026-08/retro.md", "weekly/2026-W33.md",
               "handoff/session.md", "design/DESIGN-001-x.md"]

    def test_no_file_outside_the_goals_lane_can_be_written(self):
        p = self.project()
        for rel in self.FOREIGN:
            with self.subTest(path=rel):
                with self.assertRaises(G.Refused) as caught:
                    G.write_atomic(p.dir, p.dir / rel, "x")
                self.assertIn("hand-off contract", str(caught.exception))
                self.assertFalse((p.dir / rel).exists())

    def test_the_lane_it_names_is_the_right_one(self):
        p = self.project()
        for rel, lane in (("BOARD.md", "work"), ("journal/x.md", "work"),
                          ("DECISIONS.md", "decide"),
                          ("decisions/ADR-001.md", "decide")):
            with self.subTest(path=rel):
                with self.assertRaises(G.Refused) as caught:
                    G.write_atomic(p.dir, p.dir / rel, "x")
                self.assertIn(f"`{lane}`", str(caught.exception))

    def test_the_files_the_goals_lane_does_own_are_allowed(self):
        p = self.project()
        for rel in ("OKR.md", "phase/002-x.md", "phase/002-linkage.md",
                    "phase/CURRENT", "phase/snapshots/2026-08-17-002-x.md"):
            with self.subTest(path=rel):
                G.write_atomic(p.dir, p.dir / rel, "x")
                self.assertTrue((p.dir / rel).exists())

    def test_a_commit_leaves_every_other_lane_byte_identical(self):
        p = self.project()
        (p.dir / "BOARD.md").write_text("# board\n")
        (p.dir / "DECISIONS.md").write_text("# decisions\n")
        (p.dir / "journal").mkdir()
        (p.dir / "journal" / "2026-08-17.md").write_text("# day\n")
        p.commit("--track", "ops", "--promise", "a", "--to", "x", "--due", "3d")
        self.assertEqual("# board\n", (p.dir / "BOARD.md").read_text())
        self.assertEqual("# decisions\n", (p.dir / "DECISIONS.md").read_text())
        self.assertEqual("# day\n",
                         (p.dir / "journal" / "2026-08-17.md").read_text())

    def test_the_board_side_link_is_printed_as_a_hand_off(self):
        """The `Commitment` cell is the `work` lane's write, and the link runs
        from the board side on purpose. A lane that needs a change in another
        lane's file asks in chat and stops."""
        p = self.project()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--due", "3d")
        self.assertIn("hand-off", r.stdout)
        self.assertIn("ops/1", r.stdout)
        self.assertIn("does not write BOARD.md", r.stdout)


class TestTheLockAndTheGate(WriterCase):

    def test_a_write_takes_the_same_project_lock_the_other_writers_take(self):
        """DESIGN-005 § 5.4: one lock per project, not one per lane."""
        import fcntl
        import hashlib
        p = self.project()
        key = hashlib.sha1(str(p.dir.resolve()).encode()).hexdigest()[:16]
        lock = pathlib.Path(tempfile.gettempdir()) / f"perry-task-{key}.lock"
        with open(lock, "w") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                         "--due", "3d", expect=1)
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        self.assertIn("another Perry write is holding", r.stderr)
        self.assertNotIn("Commitments", p.text())

    def test_the_conformance_gate_refuses_a_write_on_an_undeclared_file(self):
        """ADR-004. `perry-task` and `perry-decide` already gate; this one
        gates on `OKR.md`, its own file and no other."""
        p = self.project()
        before = p.text()
        r = p.run("commit", "--track", "ops", "--promise", "a", "--to", "x",
                  "--due", "3d", expect=1, PERRY_CONFORMANCE="enforce")
        self.assertIn("ADR-004", r.stderr)
        self.assertEqual(before, p.text())

    def test_reading_is_never_gated(self):
        p = self.project()
        p.run("list", "--json", expect=0, PERRY_CONFORMANCE="enforce")

    def test_a_dry_run_writes_nothing(self):
        p = self.project()
        before = p.text()
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--due", "3d", "--dry-run", "--json")
        self.assertEqual(before, p.text())
        self.assertEqual([], p.events())
        self.assertTrue(json.loads(r.stdout)["dry_run"])


class TestALocalizedTable(WriterCase):

    def test_the_due_column_resolves_even_though_zh_shares_a_word(self):
        """`schema/state-schema.json § i18n.columns` maps BOTH `Deadline` and
        `Due` onto `截止`. Resolved globally, a Chinese Commitments table
        loses its `Due` column and a writer places the date by position.
        Resolution here is table-local, so the question has one answer."""
        p = self.project(CHINESE)
        p.commit("--track", "ops", "--promise", "报表", "--to", "审计",
                 "--due", "3d", "--by-when-note", "within the track SLA")
        row = [l for l in p.text().split("\n") if "ops/2" in l][0]
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual(["ops/2", "ops", "报表", "审计", "3d", "active",
                          "within the track SLA"], cells)

    def test_the_note_column_is_widened_in_chinese_too(self):
        """A table this tool can still read and a human cannot is the same
        failure as reformatting prose."""
        p = self.project(CHINESE)
        p.commit("--track", "ops", "--promise", "报表", "--to", "审计",
                 "--due", "3d", "--by-when-note", "在时限内")
        header = [l for l in p.text().split("\n") if l.startswith("| 编号")][0]
        self.assertIn("截止说明", header)
        self.assertNotIn("By when note", p.text())

    def test_the_chinese_heading_is_found(self):
        p = self.project(CHINESE)
        p.commit("--close", "ops/1", "--discharged-by", "已完成")
        self.assertIn("closed", p.text())

    def test_a_widened_chinese_table_gets_a_chinese_header(self):
        """A table this tool can still read and a human cannot is the same
        failure as reformatting prose — the file stops being the user's."""
        p = self.project(CHINESE)
        p.commit("--close", "ops/1", "--discharged-by", "已完成")
        header = [l for l in p.text().split("\n") if l.startswith("| 编号")][0]
        self.assertTrue(header.endswith("| 由谁完成 |"), header)
        self.assertNotIn("Discharged by", p.text())


class TestWideningIsTheOnlyEditThatTouchesOtherRows(WriterCase):
    """`Discharged by` is optional in the schema, `--close` has nowhere to put
    its account without it, and refusing would strand a real promise on a table
    that is not malformed. So the table is widened — and that is the only edit
    here that reaches lines the caller did not name, which is why it is
    reported and why its exactness is tested."""

    NARROW = (ALIGNED.format(past="2027-01-01")
              .replace(" | Discharged by |", " |")
              .replace("|--------|---------------|", "|--------|")
              .replace("| active |               |", "| active |")
              .replace("| active | oldest-first  |", "| active |"))

    def narrow(self) -> Project:
        p = self.project(self.NARROW)
        self.assertNotIn("Discharged by", p.text())
        return p

    def test_an_untouched_row_gains_a_cell_and_loses_no_byte(self):
        p = self.narrow()
        old = [l for l in p.text().split("\n") if "rel/1" in l][0]
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        new = [l for l in p.text().split("\n") if "rel/1" in l][0]
        self.assertEqual(old + "  |", new,
                         "a row the edit did not name was re-spaced")

    def test_the_header_and_separator_keep_their_own_style(self):
        p = self.narrow()
        head = [l for l in p.text().split("\n") if l.startswith("| Track")][0]
        sep = [l for l in p.text().split("\n") if l.startswith("|-------")][0]
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        lines = p.text().split("\n")
        self.assertEqual(head + " Discharged by |",
                         [l for l in lines if l.startswith("| Track")][0])
        self.assertEqual(sep + "--------|",
                         [l for l in lines if l.startswith("|-------")][0],
                         "the separator was rewritten in another style")

    def test_prose_around_the_table_is_untouched(self):
        p = self.narrow()
        before = p.text().split("\n")
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        for old, new in zip(before, p.text().split("\n")):
            if not old.strip().startswith("|"):
                self.assertEqual(old, new)

    def test_the_widening_is_reported_to_the_user(self):
        p = self.narrow()
        r = p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        self.assertIn("widened", r.stdout)

    def test_a_create_never_widens_a_table_missing_a_required_column(self):
        """Padding every row of a register this tool did not write is not a
        repair a writer gets to make silently."""
        okr = ALIGNED.format(past="2027-01-01").replace(
            "| To whom ", "").replace("|---------|---------|", "|---------|")
        p = self.project(okr.replace("| Users   |", "").replace("| Finance |", ""))
        r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                     "--due", "3d", expect=1)
        self.assertIn("To whom", r.stderr)


class TestTheRealFilesOnThisMachine(WriterCase):
    """Rule 3 of this task: against COPIES, never the originals."""

    def copy_of(self, source: pathlib.Path) -> Project | None:
        if not source.exists():
            return None
        p = Project(source.read_text(), tracks=None)
        self.addCleanup(p.cleanup)
        return p

    def test_both_refuse_and_change_nothing(self):
        """Neither project declares a `pipeline` or `queue` track, and neither
        `OKR.md` has a `## Commitments` section. The correct answer is a
        refusal that names the modes the section serves — and a file that is
        byte-identical afterwards."""
        found = 0
        for source in ELSEWHERE:
            p = self.copy_of(source)
            if p is None:
                continue
            found += 1
            with self.subTest(path=str(source)):
                before = p.text()
                r = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                             "--due", "3d", expect=1)
                self.assertIn("pipeline", r.stderr)
                self.assertEqual(before, p.text())
                self.assertEqual(source.read_text(), before,
                                 "the ORIGINAL was touched")
        if not found:
            self.skipTest(f"none of {[str(p) for p in ELSEWHERE]} present")

    def test_a_declared_queue_track_makes_the_section_land_cleanly(self):
        """The other half of the same question: given a track that needs the
        spine, does the section land in a real, unusual file without
        disturbing it? gimegime nests `### Anti-Goals` INSIDE a version, so a
        naive insert-before-Anti-Goals lands in the middle of `## v2`."""
        found = 0
        for source in ELSEWHERE:
            if not source.exists():
                continue
            found += 1
            p = Project(source.read_text(), tracks=TRACKS)
            self.addCleanup(p.cleanup)
            with self.subTest(path=str(source)):
                before = p.text()
                p.commit("--track", "ops", "--promise", "Statements filed",
                         "--to", "Auditor", "--due", "3d", "--by-when-note", "within the track SLA")
                added = [d for d in p.changed_lines(before) if d[0] == "-"]
                self.assertEqual([], added, "an existing line was rewritten")
                lines = p.text().split("\n")
                at = next(i for i, l in enumerate(lines)
                          if l.startswith("## Commitments"))
                # not swallowed by a version block
                prior = [l for l in lines[:at] if l.startswith("## ")]
                self.assertFalse(any(l.startswith("## v") for l in prior),
                                 f"landed inside {prior[-1] if prior else '?'}")
        if not found:
            self.skipTest(f"none of {[str(p) for p in ELSEWHERE]} present")


class TestTheReadContractDidNotMove(unittest.TestCase):
    """`perry-goals/list/2.0` is frozen and published. Shipping a writer is not
    a read-contract change, and this says so where it can fail."""

    def test_the_version_is_unchanged(self):
        self.assertEqual("perry-goals/list/2.0", G.LIST_CONTRACT)

    def test_the_contract_document_agrees(self):
        doc = (ROOT / "schema" / "goals-list-contract.md").read_text()
        self.assertIn(G.LIST_CONTRACT, doc)
        self.assertIn("## Changelog", doc)


class TestTheClockRegexIsGone(unittest.TestCase):
    """TASK-091's deliverable, asserted as an absence.

    The phase's Definition of Done is literally `grep -c CLOCK_RE bin/`
    returning 0, so that is what this runs. The vocabulary table and its two
    pattern builders go with it: a table nobody reads is documentation of a
    rule that no longer exists, and this repository's own measurement says
    unused vocabulary is its most-found defect class.
    """

    GONE = ["CLOCK_RE", "CLOCK_VOCAB", "_CN_EDGE", "_CN_EXTEND",
            "_CN_NUM_CHARS", "_EN_NUM", "_alts", "_group", "check_by_when"]

    def test_no_file_under_bin_mentions_the_regex(self):
        for path in sorted((ROOT / "bin").rglob("*")):
            if not path.is_file():
                continue
            with self.subTest(path=path.name):
                self.assertNotIn(
                    "CLOCK_RE", path.read_text(errors="replace"),
                    f"{path.name} still mentions the deleted regex")

    def test_the_vocabulary_and_its_helpers_are_not_importable(self):
        mod = goals_module()
        for name in self.GONE:
            with self.subTest(name=name):
                self.assertFalse(hasattr(mod, name),
                                 f"{name} survived the deletion")

    def test_what_replaced_it_is_two_anchored_formats(self):
        """Not a smaller vocabulary — a format. Both patterns are anchored at
        both ends, which is what makes "is the WHOLE cell this" the question
        rather than "does this cell contain something like this"."""
        mod = goals_module()
        self.assertEqual("^", mod.ISO_DATE_RE.pattern[0])
        self.assertEqual("$", mod.ISO_DATE_RE.pattern[-1])
        self.assertEqual("^", mod.SLA_TOKEN_RE.pattern[0])
        self.assertEqual("$", mod.SLA_TOKEN_RE.pattern[-1])

    def test_the_typed_check_names_no_language(self):
        """The fifth round's defect was two halves matched under different
        rules. There is now one rule, and it contains no CJK at all — so it
        cannot be enforced asymmetrically."""
        mod = goals_module()
        for pattern in (mod.ISO_DATE_RE.pattern, mod.SLA_TOKEN_RE.pattern):
            with self.subTest(pattern=pattern):
                self.assertFalse(
                    [c for c in pattern if "\u4e00" <= c <= "\u9fff"],
                    "the typed check grew a language-specific half")


class TestMigratingAPreSplitRegister(WriterCase):
    """`commit --migrate`, and the counting that proves nothing was lost.

    ADR-004's *a project migrates once*: the split is its own named write, not
    something a `--close` does on the way past. The count is the evidence —
    non-empty clock cells before must equal `Due` plus `By when note` after.
    """

    def clock_cells(self, text: str) -> list[str]:
        """Every non-empty cell of the register's clock column(s), in order.

        Read positionally FROM THE HEADER, so it works on both the pre-split
        table (one column) and the post-split one (two) without knowing which
        it is looking at."""
        rows = [l for l in text.split("\n")
                if l.strip().startswith("|") and not set(l) <= set("|- :\n")]
        header = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        want = [i for i, c in enumerate(header)
                if c in ("By when", "Due", "By when note", "截止", "截止说明")]
        out = []
        for row in rows[1:]:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            for i in want:
                v = cells[i] if i < len(cells) else ""
                if v and v not in G.BLANKISH:
                    out.append(v)
        return out

    def test_nothing_is_lost_and_each_cell_lands_in_its_own_field(self):
        p = self.project(PRE_SPLIT)
        before = self.clock_cells(p.text())
        self.assertEqual(["2027-01-01", "within the track SLA", "3d"], before)

        r = p.commit("--migrate")
        after = self.clock_cells(p.text())
        self.assertEqual(sorted(before), sorted(after),
                         "a clock cell was dropped or rewritten")

        rows = {l.split("|")[1].strip(): l for l in p.text().split("\n")
                if l.strip().startswith("| ")}
        self.assertIn("2027-01-01", rows["rel/1"])
        self.assertIn("within the track SLA", rows["ops/7"])
        self.assertIn("3d", rows["ops/8"])
        self.assertIn("3 non-empty clock cell(s) before, 3 after", r.stdout)

    def test_the_counts_are_reported_and_add_up(self):
        p = self.project(PRE_SPLIT)
        r = p.run("commit", "--migrate", "--json", expect=0)
        m = json.loads(r.stdout)["migrated"]
        self.assertEqual(4, m["rows"])
        self.assertEqual(2, m["kept_as_due"])       # 2027-01-01 and 3d
        self.assertEqual(1, m["moved_to_note"])     # within the track SLA
        self.assertEqual(1, m["empty"])             # the em dash
        self.assertEqual(m["rows"],
                         m["kept_as_due"] + m["moved_to_note"] + m["empty"],
                         "a row was counted twice or not at all")

    def test_the_header_is_renamed_and_the_note_column_added(self):
        p = self.project(PRE_SPLIT)
        p.commit("--migrate")
        header = [l for l in p.text().split("\n") if l.startswith("| Id ")][0]
        self.assertIn("Due", header)
        self.assertNotIn("By when |", header)
        self.assertIn("By when note", header)

    def test_an_em_dash_is_left_alone_rather_than_called_prose(self):
        """`SKILL.md`'s own example rows write an empty cell as an em dash. A
        migration that moved one into the note column would file a placeholder
        as the user's words."""
        p = self.project(PRE_SPLIT)
        p.commit("--migrate")
        row = [l for l in p.text().split("\n") if l.startswith("| ops/9")][0]
        self.assertIn("—", row)
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        self.assertEqual("", cells[-1], "the em dash was moved into the note")

    def test_it_works_in_chinese_where_there_is_no_header_to_rename(self):
        """`截止` is `Due`'s own Chinese spelling, so the header cell does not
        move — only the values do. This is the half of the problem that has an
        answer in both languages, which the deleted regex did not."""
        p = self.project(PRE_SPLIT_CN)
        before = self.clock_cells(p.text())
        self.assertEqual(["下周期", "2027-01-01"], before)
        p.commit("--migrate")
        self.assertEqual(sorted(before), sorted(self.clock_cells(p.text())))
        header = [l for l in p.text().split("\n") if l.startswith("| 编号")][0]
        self.assertIn("截止说明", header)
        row = [l for l in p.text().split("\n") if l.startswith("| ops/1 ")][0]
        self.assertTrue(row.rstrip().rstrip("|").rstrip().endswith("下周期"),
                        row)

    def test_prose_outside_the_table_is_untouched(self):
        p = self.project(PRE_SPLIT)
        before = p.text().split("\n")
        p.commit("--migrate")
        for old, new in zip(before, p.text().split("\n")):
            if not old.strip().startswith("|"):
                self.assertEqual(old, new)

    def test_running_it_twice_changes_nothing_the_second_time(self):
        p = self.project(PRE_SPLIT)
        p.commit("--migrate")
        once = p.text()
        p.commit("--migrate")
        self.assertEqual(once, p.text(), "the migration is not idempotent")

    def test_a_dry_run_writes_nothing_and_still_counts(self):
        p = self.project(PRE_SPLIT)
        before = p.text()
        r = p.run("commit", "--migrate", "--dry-run", "--json", expect=0)
        self.assertEqual(before, p.text())
        self.assertEqual([], p.events())
        self.assertEqual(1, json.loads(r.stdout)["migrated"]["moved_to_note"])

    def test_every_other_write_path_refuses_until_it_has_run(self):
        """Half-splitting a table on the way past a `--close` is exactly the
        migrate-as-a-side-effect ADR-004 forbids."""
        for argv in (["--track", "ops", "--promise", "a", "--to", "x",
                      "--due", "3d"],
                     ["--close", "ops/7", "--discharged-by", "done"],
                     ["--miss", "ops/7", "--reason", "slipped"],
                     ["--id", "ops/7", "--promise", "revised"]):
            with self.subTest(path=argv[0]):
                p = self.project(PRE_SPLIT)
                before = p.text()
                r = p.commit(*argv, expect=1)
                self.assertIn("commit --migrate", r.stderr)
                self.assertEqual(before, p.text())
                self.assertEqual([], p.events())

    def test_the_refusal_also_fires_where_there_is_no_header_to_see(self):
        """The Chinese case has no `By when` cell to find, so the gate is on
        the VALUES — a typed question asked of a typed column, which is the
        one thing the deleted regex was not."""
        p = self.project(PRE_SPLIT_CN)
        r = p.commit("--close", "ops/1", "--discharged-by", "已完成", expect=1)
        self.assertIn("commit --migrate", r.stderr)

    def test_after_migrating_the_ordinary_paths_work_again(self):
        p = self.project(PRE_SPLIT)
        p.commit("--migrate")
        p.commit("--close", "ops/7", "--discharged-by", "worked oldest-first")
        self.assertIn("closed", p.text())

    def test_two_clock_columns_at_once_is_reported_not_guessed(self):
        """A shape nothing here can produce — a hand edit, or a column-adding
        migration run before `perry-migrate` learned to stand aside. A row
        with a value in each is two deadlines for one promise, and picking one
        is not a call a writer gets to make."""
        p = self.project(PRE_SPLIT.replace(
            "| By when              | Status |",
            "| By when              | Status | Due        |").replace(
            "| active |", "| active | 2028-01-01 |"))
        before = p.text()
        r = p.commit("--migrate", expect=1)
        self.assertIn("BOTH", r.stderr)
        self.assertIn("By when", r.stderr)
        self.assertEqual(before, p.text())
        self.assertEqual([], p.events())

    def test_the_conformance_gate_does_not_lock_the_split_out(self):
        """**The deadlock this exemption exists to break.** Under `enforce`,
        ADR-004's gate makes a file that is not Perry's shape read-only — and a
        pre-split register is out of shape by exactly the defect this command
        fixes. Gated, the file could never be written to and never be repaired,
        with no third command. `perry-migrate` is exempt from its own gate for
        the same reason, and this is the transform it hands over."""
        p = self.project(PRE_SPLIT)
        blocked = p.commit("--track", "ops", "--promise", "a", "--to", "x",
                           "--due", "3d", expect=1,
                           PERRY_CONFORMANCE="enforce")
        self.assertIn("read-only", blocked.stderr)

        r = p.commit("--migrate", PERRY_CONFORMANCE="enforce")
        self.assertIn("split", r.stdout)
        self.assertIn("Due", p.text())
        self.assertIn("By when note", p.text())

    def test_it_takes_no_row_flags(self):
        p = self.project(PRE_SPLIT)
        r = p.commit("--migrate", "--track", "ops", "--promise", "a",
                     "--to", "x", "--due", "3d", expect=1)
        self.assertIn("Run it alone", r.stderr)



class TestCreateAndAmendAgreeAboutWhatACellCanHold(unittest.TestCase):
    """One tool, one value, two answers.

    `commit --promise $'a\\n\\nb'` was **refused** on the create path and
    **silently collapsed** on every amend path — `--miss --reason`,
    `--id --promise` and `--close --discharged-by` — because `splice_cell`
    carried its own `.replace("\\n", " ")` instead of `render_row`'s rule. A
    user writing a two-paragraph promise got a refusal from one subcommand and
    a quietly mangled cell from another.

    The reviewer's finding also included that **none of these three functions
    had any test coverage at all** — `splice_cell`, `append_cell` and
    `UnrenderableCell` appeared nowhere in this file. They now live in
    `viewer/tables.py` beside `split_row`, which is where the builder said they
    belonged and could not put them at the time.
    """

    OKR = ("# OKR\n\n## Mission\n\nx\n\n## Commitments\n\n"
           "| Id | Track | Promise | To whom | Due | Status | Discharged by |\n"
           "|---|---|---|---|---|---|---|\n"
           "| C-1 | ops | keep it up | Finance | 3d | active | — |\n")
    TRACKS = ("\n## Tracks\n\n"
              "| Track | Mode | Spine | Stages | WIP | SLA | Cycle | Default rung |\n"
              "|---|---|---|---|---|---|---|---|\n"
              "| ops | queue | OKR.md | new,triaged | — | 3d | — | V2 |\n")

    def project(self):
        return Project(okr=self.OKR, tracks=self.TRACKS)

    MULTILINE = "first paragraph\n\nsecond paragraph"

    def test_the_amend_paths_refuse_what_create_refuses(self):
        for argv in (["--id", "C-1", "--miss", "--reason", self.MULTILINE],
                     ["--id", "C-1", "--promise", self.MULTILINE],
                     ["--id", "C-1", "--close",
                      "--discharged-by", self.MULTILINE]):
            with self.subTest(path=argv[2]):
                p = self.project()
                before = p.okr_path.read_bytes()
                out = p.run("commit", *argv)
                self.assertEqual(out.returncode, 1,
                                 f"accepted silently: {out.stderr}")
                self.assertEqual(p.okr_path.read_bytes(),
                                 before, "a refusal wrote to the file")

    def test_whitespace_only_is_refused_rather_than_erasing_the_cell(self):
        """Refused on create, **silently erasing** on amend — the same shape as
        the line-break defect, one flag further along.

        The create branch tests `(args.promise or "").strip()`; the amend
        branch tested `is not None`. So `--promise '   '` was rejected outright
        by one subcommand and wiped the promise text by the other, with the
        event recording the spaces and nothing saying so.

        Asserted at CLI level and on the FILE, because the first version of
        this test asserted that the guard's source construct existed — and
        stayed green when the condition inside it was mutated to `if False:`.
        """
        for flag in ("--promise", "--to"):
            with self.subTest(flag=flag):
                p = self.project()
                before = p.okr_path.read_bytes()
                out = p.run("commit", "--id", "C-1", flag, "   ")
                self.assertEqual(out.returncode, 1,
                                 f"{flag} erased the cell: {out.stderr}")
                self.assertEqual(p.okr_path.read_bytes(), before,
                                 "a refusal wrote to the file")
                self.assertIn("erase", (out.stderr + out.stdout).lower())

    def test_a_real_edit_still_lands(self):
        """A guard that refuses every amend is not a guard. The neighbouring
        value must still be writable."""
        p = self.project()
        out = p.run("commit", "--id", "C-1", "--promise", "a new promise")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("a new promise", p.okr_path.read_text())

    def test_the_refusal_says_what_is_wrong_rather_than_collapsing(self):
        p = self.project()
        out = p.run("commit", "--id", "C-1", "--promise", self.MULTILINE)
        self.assertEqual(out.returncode, 1)
        self.assertIn("line break", (out.stderr + out.stdout).lower())
        self.assertNoTraceback(out)

    def assertNoTraceback(self, out):
        """**This test passed on a crash for a whole round.**

        A fix copied `bin/perry-task`'s flag-naming block into `perry-goals`'
        MODULE-LEVEL handler, where `args` does not exist. Every line-break
        refusal on all eight write paths ended in `NameError` — and the
        assertion above still passed, because the traceback's own last line
        contains the phrase `line break`.

        rc was still 1 and nothing was written, so every other assertion held
        too. A refusal and a crash are not the same event and a test that
        cannot tell them apart is checking the message, not the behaviour.
        """
        blob = out.stderr + out.stdout
        self.assertNotIn("Traceback (most recent call last)", blob, blob[-500:])
        self.assertNotIn("NameError", blob, blob[-500:])

    def test_no_refusal_on_any_write_path_ends_in_a_traceback(self):
        """The category, not the one path the crash was found on."""
        for argv in (["--id", "C-1", "--promise", self.MULTILINE],
                     ["--id", "C-1", "--miss", "--reason", self.MULTILINE],
                     ["--id", "C-1", "--close",
                      "--discharged-by", self.MULTILINE],
                     ["--track", "ops", "--promise", self.MULTILINE,
                      "--to", "x", "--due", "3d"]):
            with self.subTest(path=" ".join(argv[:3])):
                out = self.project().run("commit", *argv)
                self.assertEqual(out.returncode, 1)
                self.assertNoTraceback(out)

    def test_a_pipe_is_escaped_rather_than_refused_on_both_paths(self):
        """`|` round-trips, so it is carried; `\\n` cannot, so it is refused.
        The two are not the same and the tool must not treat them alike."""
        p = self.project()
        out = p.run("commit", "--id", "C-1", "--promise", "A | B")
        self.assertEqual(out.returncode, 0, out.stderr)
        text = p.okr_path.read_text(encoding="utf-8")
        self.assertIn("A \\| B", text)
        row = [l for l in text.split("\n") if l.startswith("| C-1")][0]
        self.assertEqual(len(T.split_row(row)), 7, row)

    def test_one_cell_changes_and_the_rest_of_the_row_keeps_its_bytes(self):
        """The reason `splice_cell` exists rather than `render_row` on a parsed
        row: a hand-aligned table stays aligned everywhere the edit did not
        reach."""
        p = self.project()
        before = [l for l in p.okr_path.read_text().split("\n")
                  if l.startswith("| C-1")][0]
        p.run("commit", "--id", "C-1", "--promise", "changed")
        after = [l for l in p.okr_path.read_text().split("\n")
                 if l.startswith("| C-1")][0]
        self.assertNotEqual(before, after)
        self.assertEqual(T.split_row(before)[3:], T.split_row(after)[3:],
                         "cells the edit did not name were rewritten")


if __name__ == "__main__":
    unittest.main()
