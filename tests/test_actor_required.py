"""TASK-289 round 1 — every `perry-task` write names who is writing (USER-950).

`perry/evidence/2026-09/TASK-289-spec.md`. Measured 2026-09-16: all 27 of
`perry-task`'s write subcommands accepted `--actor` and none required it; an
absent actor was recorded as `"agent"`, an owner no session can claim. The
row's incident was five linkage edges the session filing it could not account
for.

**What is held here:**

1. **The writing set is `SURFACE`'s, not a list.** A subcommand that declares a
   non-empty `writes` requires `--actor` (`lib.required_flags`), and every such
   subcommand accepts the flag, or it could never run. The 27 is asserted as a
   floor for anti-vacuity only.
2. **Every writer refuses without `--actor`, with `--actor ""` and with a blank
   value:** exit 2, the flag named, and not one byte of the project changed —
   with `--dry-run` too. Each writer is run with the argv that WRITES when the
   actor is given (`test_board_less_reads_and_writes.WRITES`), so the refusal
   is shown to stand in front of a write that would otherwise land.
3. **A write with an actor records it**, in the event and, for `add --kr`, in
   the linkage record that used to fall back to `"agent"`.
4. **No read demands it:** every subcommand with no `writes` runs, exit 0,
   without the flag, and its usage line does not list it as required.
5. **The documents:** every `perry-task <writer>` invocation in `SKILL.md`,
   `goals/`, `work/`, `decide/` and `reference/` carries `--actor`. An
   invocation is syntactic, so this is a mechanical check, not a reading: a
   writer named in a fenced block, or in an inline code span with anything
   after the subcommand. A bare name in running text (`` `perry-task start` ``)
   refers to the command and is not an invocation.

Run: python3 tests/parallel test_actor_required
"""

from __future__ import annotations

COVERS = (
    "bin/perry-task",
    "bin/perry-goals",
    "bin/lib/",
    "SKILL.md",
    "goals/",
    "work/",
    "decide/",
    "reference/",
)

import hashlib
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import inproc
import test_add_writes_the_edge as EDGE
import test_board_less_reads_and_writes as BL

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import lib  # noqa: E402

ACTOR = "probe-agent"


def describe() -> dict:
    out = inproc.run("perry-task", ["--describe", "--json"])
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def writers() -> dict[str, dict]:
    return {s["name"]: s for s in describe()["subcommands"] if s.get("writes")}


def readers() -> dict[str, dict]:
    return {s["name"]: s for s in describe()["subcommands"] if not s.get("writes")}


def without_actor(argv: list[str]) -> list[str]:
    out, skip = [], False
    for tok in argv:
        if skip:
            skip = False
            continue
        if tok == "--actor":
            skip = True
            continue
        out.append(tok)
    return out


def snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def argv_for(name: str) -> list[str]:
    """The argv that writes, from the board-less table; the bare subcommand
    (with an id where it takes one) for a writer that table does not run."""
    for row_name, _pre, argv, _store, _check in BL.WRITES:
        if row_name == name:
            return without_actor(list(argv))
    # `takes_id` is in `SURFACE`, not in `--describe`'s output.
    sub = lib.surface_subcommand(inproc.load("perry-task").SURFACE, name)
    return [name] if sub.get("takes_id") is False else [name, "TASK-005"]


class TestTheWritingSetIsDeclared(unittest.TestCase):

    def test_the_set_is_every_subcommand_that_declares_writes(self):
        mod = inproc.load("perry-task")
        declared = {s["name"] for s in mod.SURFACE["subcommands"] if s.get("writes")}
        required = {s["name"] for s in mod.SURFACE["subcommands"]
                    if "--actor" in lib.required_flags(mod.SURFACE, s["name"])}
        self.assertEqual(required, declared)
        # Anti-vacuity, not the rule: the 2026-09-16 measurement.
        self.assertGreaterEqual(len(declared), 27)

    def test_every_writer_accepts_the_flag_it_requires(self):
        for name, sub in writers().items():
            with self.subTest(sub=name):
                self.assertIn("--actor", sub["flags"])

    def test_a_writer_declared_tomorrow_is_covered_without_a_list(self):
        made = {"name": "t", "flags": [{"name": "--actor", "arg": "value"}],
                "subcommands": [
                    {"name": "new-write", "flags": ["--actor"], "writes": ["x.jsonl"]},
                    {"name": "new-read", "flags": ["--actor"], "writes": []}]}
        self.assertEqual(lib.required_flags(made, "new-write"), {"--actor"})
        self.assertEqual(lib.required_flags(made, "new-read"), set())
        self.assertIsNotNone(lib.actor_refusal(made, "new-write", None))
        self.assertIsNone(lib.actor_refusal(made, "new-read", None))


class TestEveryWriterRefusesWithoutAnOwner(unittest.TestCase):

    def test_each_writer_refuses_absent_empty_and_blank(self):
        """One project per writer: a refusal changes no byte, so the snapshot
        taken before the first variant must still hold after the last."""
        names = sorted(writers())
        self.assertGreaterEqual(len(names), 27)
        for name in names:
            argv = argv_for(name)
            p = BL.Project(board=None)
            try:
                before = snapshot(p.root)
                for label, extra, given in (
                        ("absent", [], "was not given"),
                        ("empty", ["--actor", ""], "was given empty"),
                        ("blank", ["--actor", "   "], "was given empty"),
                        ("dry-run", ["--dry-run"], "was not given")):
                    with self.subTest(sub=name, actor=label):
                        out = inproc.run("perry-task", argv + extra + ["--root", str(p.root)])
                        self.assertEqual(out.returncode, 2,
                                         f"{argv + extra}: {out.stderr[-400:]}")
                        self.assertIn("--actor", out.stderr)
                        self.assertIn(given, out.stderr)
                        self.assertIn("Nothing was written", out.stderr)
                        self.assertEqual(snapshot(p.root), before,
                                         f"{argv + extra} changed the project")
            finally:
                p.close()

    def test_the_same_argv_writes_once_the_actor_is_given(self):
        """The refusal stands in front of a write that would land, not in front
        of an argv that was going to be refused anyway."""
        for row_name, prereqs, argv, _store, _check in BL.WRITES:
            with self.subTest(sub=row_name):
                p = BL.Project(board=None)
                try:
                    for pre in prereqs:
                        pre = without_actor(list(pre)) + ["--actor", ACTOR]
                        self.assertEqual(p.task(pre).returncode, 0)
                    out = p.task(without_actor(list(argv)) + ["--actor", ACTOR])
                    self.assertEqual(out.returncode, 0, out.stderr[-400:])
                finally:
                    p.close()


class TestAWriteRecordsItsActor(unittest.TestCase):

    def test_the_event_carries_the_actor_given(self):
        p = BL.Project(board=None)
        try:
            out = p.task(["start", "TASK-005", "--next", "go", "--actor", ACTOR])
            self.assertEqual(out.returncode, 0, out.stderr)
            events = [json.loads(l) for l in (p.root / ".perry" / "events.jsonl")
                      .read_text(encoding="utf-8").splitlines() if l.strip()]
            last = events[-1]
            self.assertEqual((last["event"], last["id"], last["actor"]),
                             ("start", "TASK-005", ACTOR))
        finally:
            p.close()



class TestTheLinkageRecordHasNoDefault(EDGE.Fixture):
    """`add --kr` wrote `event.get("actor") or "agent"` into `linkage.jsonl`."""

    def test_add_kr_records_the_actor_given(self):
        d = self.project()
        proc = self.add(d, "a linked row", self.STORE_KR, "--actor", ACTOR)
        tid = self.new_id(proc)
        edge = self.records(d)[-1]
        self.assertEqual((edge["task"], edge["actor"]), (tid, ACTOR))

    def test_a_nonblank_actor_is_recorded_without_rewriting_it(self):
        d = self.project()
        actor = "  probe-agent  "
        self.new_id(self.add(d, "an actor identity", self.STORE_KR,
                             "--actor", actor))
        self.assertEqual(self.records(d)[-1]["actor"], actor)

    def test_an_event_with_no_actor_is_refused_not_defaulted(self):
        """Defence in depth for a second caller of the writer: `main` refuses
        first, so only a direct call reaches this."""
        d = self.project()
        for event in ({"event": "add", "id": "TASK-999", "kr": self.STORE_KR},
                      {"event": "add", "id": "TASK-999", "kr": self.STORE_KR,
                       "actor": "  "}):
            with self.subTest(event=event):
                with self.assertRaises(EDGE.PT.Refused):
                    EDGE.PT.linkage_add_change(d, event)


class TestNoReadDemandsIt(unittest.TestCase):

    READ_ARGV = {
        "list": ["list", "--json"],
        "events": ["events", "--json"],
        "asks": ["asks", "--json"],
        "signoff-offer": ["signoff-offer", "TASK-005", "--measured", "a check",
                          "--restated", "the ask"],
    }

    def test_every_read_runs_without_the_flag(self):
        names = sorted(readers())
        self.assertTrue(names, "anti-vacuity: no read subcommand")
        for name in names:
            with self.subTest(sub=name):
                self.assertIn(name, self.READ_ARGV,
                              f"a new read subcommand {name!r}: give it an argv here")
                p = BL.Project(board=None)
                try:
                    out = inproc.run("perry-task", self.READ_ARGV[name] + ["--root", str(p.root)])
                    self.assertNotIn("--actor", out.stderr)
                    self.assertEqual(out.returncode, 0, out.stderr[-400:])
                finally:
                    p.close()

    def test_usage_marks_the_flag_required_on_writers_only(self):
        mod = inproc.load("perry-task")
        for s in mod.SURFACE["subcommands"]:
            with self.subTest(sub=s["name"]):
                usage = lib.usage_lines(mod.SURFACE, s["name"])
                if s.get("writes"):
                    self.assertIn(" --actor <value>", usage)
                    self.assertNotIn("[--actor", usage)
                else:
                    self.assertNotIn("--actor", usage)


# ── the documents ─────────────────────────────────────────────────────────

CMD = re.compile(r"""perry-task["']?[ \t]+([a-z][a-z-]*)""")
SPAN = re.compile(r"(`+)((?:(?!\1).)+?)\1", re.S)


def shipped_documents() -> list[Path]:
    out = [ROOT / "SKILL.md"]
    for lane in ("goals", "work", "decide"):
        out += sorted((ROOT / lane).rglob("*.md"))
    out += sorted((ROOT / "reference").glob("*.md"))
    return out


def code_commands(text: str):
    """`(line, code, fenced)` for every fenced command and inline code span.

    A fenced command joins its backslash continuations, so a flag on the next
    line is part of it.
    """
    fenced, prose, in_fence = [], [], False
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            prose.append("")
            continue
        if in_fence:
            if fenced and fenced[-1][3]:
                ln, code, _, _ = fenced[-1]
                fenced[-1] = (ln, code + " " + line, True,
                              line.rstrip().endswith("\\"))
            else:
                fenced.append((i, line, True, line.rstrip().endswith("\\")))
            prose.append("")
        else:
            if fenced and fenced[-1][3]:
                fenced[-1] = fenced[-1][:3] + (False,)
            prose.append(line)
    body = "\n".join(prose)
    spans = [(body.count("\n", 0, m.start()) + 1, m.group(2), False)
             for m in SPAN.finditer(body) if "\n\n" not in m.group(2)]
    return [f[:3] for f in fenced] + spans


def invocations(text: str, writing: set[str]):
    """`(line, command, has_actor)` for each writing invocation in `text`."""
    for ln, code, fenced in code_commands(text):
        matches = list(CMD.finditer(code))
        for n, c in enumerate(matches):
            if c.group(1) not in writing:
                continue
            end = matches[n + 1].start() if n + 1 < len(matches) else len(code)
            rest = code[c.end():end]
            if not fenced and not rest.strip():
                continue  # a bare name in running text refers to the command
            command = rest.split(" #")[0]
            yield ln, (c.group(0) + command).strip(), "--actor" in command


class TestEveryDocumentExampleCarriesTheActor(unittest.TestCase):

    def test_no_writing_invocation_lacks_the_actor(self):
        writing = set(writers())
        seen, missing = 0, []
        for path in shipped_documents():
            text = path.read_text(encoding="utf-8")
            for ln, command, has in invocations(text, writing):
                seen += 1
                if not has:
                    missing.append(f"{path.relative_to(ROOT)}:{ln}: {command[:120]}")
        # Anti-vacuity: 51 invocations on 2026-09-16.
        self.assertGreaterEqual(seen, 40)
        self.assertEqual(missing, [], "a perry-task write example with no "
                         "--actor:\n" + "\n".join(missing))

    def test_the_scanner_sees_each_shape(self):
        w = {"status", "intake-sweep", "done"}
        text = ("run `perry-task status <ID> --status review` now\n"
                "and `perry-task done` is named, not run\n"
                "```\n\"$PERRY_HOME/bin/perry-task\" intake-sweep\n"
                "perry-task status <ID> --status x \\\n    --actor a\n```\n"
                "`perry-task status <ID> --status\n> review --actor b`\n")
        got = [(ln, has) for ln, _c, has in invocations(text, w)]
        self.assertEqual(sorted(got), [(1, False), (4, False), (5, True), (8, True)])




class TestGoalsActorContract(unittest.TestCase):
    """Round 2: all existing goals write modes, with the raw runner."""

    def cases(self):
        import test_goals_writer as GW
        import test_linkage_writer as LW
        import test_goals_kr_writer as KW
        for mode, tail in (
                ("create", ["--track", "ops", "--promise", "new", "--to", "ops", "--due", "3d"]),
                ("amend", ["--id", "ops/1", "--promise", "amended"]),
                ("close", ["--close", "ops/1", "--discharged-by", "fixture delivered"]),
                ("miss", ["--miss", "ops/1", "--reason", "fixture"]),
                ("migrate", ["--migrate"])):
            p = GW.Project(GW.PRE_SPLIT if mode == "migrate" else GW.BARE_OKR)
            self.addCleanup(shutil.rmtree, p.dir, ignore_errors=True)
            if mode in ("amend", "close", "miss"):
                result = inproc.run("perry-goals", ["commit", "--track", "ops",
                    "--promise", "old", "--to", "ops", "--due", "3d",
                    "--actor", "setup", "--root", str(p.dir)])
                self.assertEqual(result.returncode, 0, result.stderr)
            yield "commit/" + mode, p.dir, ["commit", *tail]
        for mode, tail in (
                ("edge", ["ZZZ-001", "P002-O1-KR1"]),
                ("alias", ["--alias", "PROJ-001", "fresh-name"]),
                ("unlinked", ["--unlinked", "ZZZ-001"]),
                ("project", ["--project", "PROJ-002", "P002-O1-KR1", "new project"])):
            p = LW.Project(LW.SYNTHETIC, "002-synthetic")
            self.addCleanup(p.cleanup)
            yield "link/" + mode, p.dir, ["link", *tail]
        for verb in ("check", "measure"):
            tmp = Path(tempfile.mkdtemp(prefix="goals-actor-"))
            self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
            root = KW.make_project(tmp / "p")
            check = ["check", "P004-O1-KR1", "--id", "n", "--direction",
                     "done", "--target", "1", "--label", "done"]
            if verb == "measure":
                result = inproc.run("perry-goals", [*check, "--actor", "setup", "--root", str(root)])
                self.assertEqual(result.returncode, 0, result.stderr)
            yield verb, root, (check if verb == "check" else [
                "measure", "P004-O1-KR1", "--check", "n", "--value", "1",
                "--evidence", "evidence/2026-09/m.md"])
        # TASK-264 D3: `kr add | restate | withdraw` (DESIGN-022 § 5.7).
        for op, tail in (
                ("add", ["P004-O1-KR9", "--objective", "O1", "--text", "new"]),
                ("restate", ["P004-O1-KR1", "--set", "title=restated"]),
                ("withdraw", ["P004-O1-KR1"])):
            tmp = Path(tempfile.mkdtemp(prefix="goals-actor-"))
            self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
            root = KW.make_project(tmp / "p")
            yield "kr/" + op, root, ["kr", op, *tail, "--reason", "fixture"]
        # TASK-475: `objective add`.
        tmp = Path(tempfile.mkdtemp(prefix="goals-actor-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        root = KW.make_project(tmp / "p")
        yield "objective/add", root, ["objective", "add", "O2", "--text", "new",
                                      "--reason", "fixture"]

    def test_every_mode_refuses_absent_empty_blank_and_multiline_before_writing(self):
        seen = set()
        for mode, root, argv in self.cases():
            seen.add(argv[0])
            before = snapshot(root)
            for actor in (None, "", " ", "a\nb", "a\rb"):
                for dry in (False, True):
                    with self.subTest(mode=mode, actor=actor, dry=dry):
                        extra = [] if actor is None else ["--actor", actor]
                        got = inproc.run("perry-goals", [*argv, *extra,
                            *(["--dry-run"] if dry else []), "--root", str(root)])
                        self.assertEqual(got.returncode, 2, got.stdout + got.stderr)
                        self.assertIn("--actor", got.stderr)
                        self.assertIn("Usage: perry-goals", got.stderr)
                        self.assertIn("Nothing was written", got.stderr)
                        self.assertEqual(snapshot(root), before)
        mod = inproc.load("perry-goals")
        self.assertEqual(seen, set(mod.COMMANDS) - mod.READ_COMMANDS)
        self.assertEqual(seen, {s["name"] for s in mod.ACTOR_SURFACE["subcommands"]
                               if "--actor" in lib.required_flags(mod.ACTOR_SURFACE, s)})

    def test_each_mode_records_its_explicit_actor(self):
        for mode, root, argv in self.cases():
            with self.subTest(mode=mode):
                actor = " lane:fixture " if argv[0] in ("commit", "link") else "lane:fixture"
                got = inproc.run("perry-goals", [*argv, "--actor", actor,
                                                "--root", str(root), "--json"])
                self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
                events = [json.loads(line) for line in (root / ".perry/events.jsonl").read_text().splitlines()]
                self.assertEqual(events[-1]["actor"], actor)
                if argv[0] in ("link", "check", "measure") or argv[1:2] in (
                        ["restate"], ["withdraw"]):
                    record = json.loads((root / "linkage.jsonl").read_text().splitlines()[-1])
                    self.assertEqual(record["actor"], actor)

    def test_every_reader_stays_actor_free(self):
        import test_goals_kr_writer as KW
        tmp = Path(tempfile.mkdtemp(prefix="goals-actor-read-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        root = KW.make_project(tmp / "p")
        mod = inproc.load("perry-goals")
        self.assertEqual(mod.READ_COMMANDS, {"list", "krs"})
        for name in mod.READ_COMMANDS:
            with self.subTest(reader=name):
                before = snapshot(root)
                got = inproc.run("perry-goals", [name, "--root", str(root), "--json"])
                self.assertEqual(got.returncode, 0, got.stdout + got.stderr)
                self.assertEqual(snapshot(root), before)

    def test_single_line_validation_is_shared_and_opt_in(self):
        mod = inproc.load("perry-goals")
        self.assertIsNotNone(lib.actor_refusal(mod.ACTOR_SURFACE, "commit", "a\nb", single_line=True))
        self.assertIsNone(lib.actor_refusal(mod.ACTOR_SURFACE, "commit", "a\nb"))
        self.assertIsNone(lib.actor_refusal(mod.ACTOR_SURFACE, "list", None, single_line=True))

    def test_goals_executable_examples_name_an_actor(self):
        from unittest.mock import patch
        matcher = re.compile(r"""perry-goals["']?[ \t]+([a-z][a-z-]*)""")
        missing, seen = [], 0
        with patch.dict(globals(), CMD=matcher):
            for path in shipped_documents():
                for ln, command, has in invocations(path.read_text(), {"commit", "link", "check", "measure", "kr"}):
                    seen += 1
                    if not has:
                        missing.append(f"{path.relative_to(ROOT)}:{ln}: {command}")
        self.assertGreaterEqual(seen, 12)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
