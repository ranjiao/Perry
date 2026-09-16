"""`perry-task add --unlinked` writes the declaration, in the row's own transaction.

TASK-394, the `work`-lane half of `DESIGN-015 § 5.5` that was never built. Row D
(`TASK-279`, `tests/test_add_writes_the_edge.py`) gave `add` the `edge` record;
this row gives it the `unlinked` one, so that § 5.5's table

    | kind       | work (`perry-task`)                    | goals (`perry-goals`) |
    | edge       | `add --kr`                             | `link`                |
    | unlinked   | `add` with an explicit declaration  ←   | `link --unlinked`     |

has no empty cell left. **No reader changed.** `bin/lib § same_action_linkage`
has read `{"kind":"unlinked", …, "via":"add"}` as its second numerator path
since row F; `lib.UNLINKED_AT_ADD_HAS_NO_WRITER` carried the fact that nothing
could produce one. This module is that writer's test, and the constant is now
`False`.

**The one sequence this module exists for**, with nothing run in between:

    perry-task add --title "…" --unlinked
    perry-state --section linkage

The new row must count as ANSWERED and the KR must rise. Before this row the
identical command line exited 2 with `unknown argument '--unlinked'`.

**How these tests are built to be able to fail.**

*The one sequence* (`TestTheOneSequence`) asserts through
`lib.same_action_linkage` — the reader — rather than against a literal record.
The spec asks for exactly that control: a test that matched
`{"kind":"unlinked",…}` by string comparison would pass against a writer that
emitted a record no reader counts, which is the whole defect class row F's
`UNLINKED_AT_ADD_HAS_NO_WRITER` was written to mark.

*Silence* (`TestSilenceIsStillNeverAsked`) is the control that keeps this row
inside its Bound. `DESIGN-015 § 5.2` says omitting the answer stays legal and
stays a warning; a declaration is a THIRD state, not a replacement for silence.
If `--unlinked` had been implemented by making omission mean "no KR", this
class goes red and the one sequence still passes.

*The contradiction* (`TestTheContradictionIsRefused`) drives `--kr X
--unlinked` and asserts a REFUSAL, not a resolution. `TASK-281` round 2 refused
a blank `--kr` for three reasons and the first — *ambiguous in a way a default
cannot resolve* — is this case exactly.

*The store-less project* (`TestAStoreLessProjectRefusesTheDeclaration`) is the
asymmetry with `--kr`, and it carries its own control: the same fixture files a
plain row and exits 0, so the refusal cannot rot green on a broken fixture the
way `TASK-281` round 1's did.

*Atomicity* (`TestTheDeclarationIsNotASecondTransaction`) inherits **seven**
crash points, not row D's five-claimed / four-driven. `TASK-279`'s V4 measured
the real number: row D's harness kills only before *canonical renames*, and the
event append is `open(..., "a")` — not a rename — so three points were
structurally unreachable by it. All seven are driven here.

Run: python3 tests/parallel test_add_declares_unlinked
"""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "bin/perry-state",
    "bin/perry_store.py",
    "bin/lib/",
)

import json
import pathlib
import signal
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

# The row D module is imported for its FIXTURE, not for its tests — those stay
# under `M.` and unittest collects only what is in this module's namespace, so
# nothing is run twice. Imported rather than copied on purpose: a second copy of
# `document()` / `store()` is a second thing to keep in step with the schema,
# and the two rows write into the same store.
import test_add_writes_the_edge as M  # noqa: E402
import lib  # noqa: E402

TASK = ROOT / "bin" / "perry-task"
STATE = ROOT / "bin" / "perry-state"

MARKER = ".perry-task-transaction.json"


class Fixture(M.Fixture):
    """Row D's project, plus the seams `--unlinked` needs."""

    def declare(self, d: pathlib.Path, title: str = "a declared row",
                *extra: str) -> subprocess.CompletedProcess:
        return self.add(d, title, None, "--unlinked", *extra)

    def measurement(self, d: pathlib.Path) -> dict:
        """`P003-O3-KR2` as the READER computes it, from this project's files.

        Deliberately `lib.same_action_linkage` and not a hand-rolled scan of
        `linkage.jsonl`: the control this module owes is that the record the
        writer emits is the record `bin/lib:741` already reads, and only the
        reader itself can state that.
        """
        return lib.same_action_linkage(self.records(d), self.events(d))

    def declared(self, d: pathlib.Path) -> list[str]:
        return self.measurement(d)["declared_unlinked_at_add"]

    def has_row(self, d: pathlib.Path, tid: str) -> bool:
        p = d / "tasks.jsonl"
        if not p.exists():
            return False
        return any(json.loads(l).get("id") == tid
                   for l in p.read_text().split("\n") if l.strip())

    def has_declaration(self, d: pathlib.Path, tid: str) -> bool:
        return any(r.get("kind") == "unlinked" and r.get("task") == tid
                   and r.get("via") == "add"
                   for r in self.records(d))


class TestTheOneSequence(Fixture):
    """`add --unlinked`, then the reader. Nothing run in between."""

    def test_the_declared_row_counts_as_answered_and_the_kr_rises(self):
        d = self.project()
        before = self.measurement(d)
        tid = self.new_id(self.declare(d))
        after = self.measurement(d)

        self.assertIn(tid, after["declared_unlinked_at_add"],
                      "the row `add --unlinked` just declared is not in the "
                      "reader's second numerator path — the record did not "
                      "reach `same_action_linkage`")
        self.assertNotIn(tid, after["never_answered"],
                         "a declared row is still reported never-answered; "
                         "the declaration is not being read as an answer")
        self.assertEqual(after["numerator"], before["numerator"] + 1,
                         "the numerator did not rise by exactly one")
        self.assertEqual(after["denominator"], before["denominator"] + 1,
                         "the declared row must be in the DENOMINATOR too — "
                         "it was asked, and it answered")
        self.assertGreater(after["current"], before["current"] or 0.0,
                           "the KR did not rise")

    def test_the_record_is_the_shape_the_reader_already_read(self):
        """The control the spec asks for: assert against the PREDICATE.

        `_corroborates`/`same_action_linkage` decide the second numerator path
        on `kind == "unlinked" and via == "add"`. Asserting that the reader
        counts the row is the only assertion that cannot pass for a record no
        reader consults — which is exactly how `TASK-281` round 1's M13 was
        closed against a fixture Perry could not produce.
        """
        d = self.project()
        tid = self.new_id(self.declare(d))
        mine = [r for r in self.records(d) if r.get("task") == tid]
        self.assertEqual(len(mine), 1,
                         "`add --unlinked` wrote %d records for one row"
                         % len(mine))
        rec = mine[0]
        # Field-for-field the goals lane's `unlinked` record, `via` apart. Two
        # writers of one store spelling one record two ways is the drift
        # DESIGN-015 exists to remove.
        #
        # `phase` joined the shape at ADR-019: the store holds every phase at
        # once now, and a declaration is made against ONE board — without it
        # phase 001's declarations would count against phase 003's.
        self.assertEqual(
            sorted(rec),
            sorted(["kind", "task", "phase", "declared_at", "actor", "via"]))
        self.assertEqual(rec["kind"], "unlinked")
        self.assertEqual(rec["via"], "add")
        self.assertNotIn("kr", rec,
                         "an `unlinked` record must not carry a `kr` field")
        # Read back by the reader, not by this test's own idea of the shape.
        self.assertIn(tid, self.declared(d))

    def test_no_edge_record_is_written_for_a_declared_row(self):
        """§ 5.5's `kr` × `work` cell is NEVER, and `edge` needs a `--kr`."""
        d = self.project()
        tid = self.new_id(self.declare(d))
        kinds = [r["kind"] for r in self.records(d) if r.get("task") == tid]
        self.assertEqual(kinds, ["unlinked"])

    def test_the_add_event_carries_kr_null_and_no_declaration(self):
        """The declaration lives in the STORE and only in the store.

        § 5.2 derives never-asked from the store's silence, so a second copy on
        the event would be one fact in two places with no detector for the
        drift — `same_action_linkage` reports `store_edge_without_event` and
        `event_kr_without_store_edge` for EDGES and has no equivalent pair for
        declarations. `kr: null` is what puts the row in the denominator.
        """
        d = self.project()
        tid = self.new_id(self.declare(d))
        add = [e for e in self.events(d)
               if e.get("event") == "add" and e.get("id") == tid]
        self.assertEqual(len(add), 1)
        self.assertIn("kr", add[0], "the `kr` KEY must be present and null")
        self.assertIsNone(add[0]["kr"])
        self.assertNotIn("unlinked", add[0],
                         "the declaration was copied onto the event — that is "
                         "a second place for one fact, and nothing reads it")

    def test_the_success_line_names_the_store_it_wrote(self):
        d = self.project()
        proc = self.declare(d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("linkage.jsonl", proc.stdout,
                      "the success line did not name the store this write "
                      "actually appended to")

    def test_a_declared_row_does_not_warn_that_it_reads_never_asked(self):
        """The warning's content is 'the row reads as never-asked'. After a
        declaration that sentence is FALSE of the row, so printing it would
        tell the caller their declaration did not land."""
        d = self.project()
        proc = self.declare(d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("never-asked", proc.stderr)

    def test_the_record_carries_the_declaring_actor(self):
        """**Closes mutation M16, on an input a user can produce.**

        Hardcoding `"actor": "agent"` in the writer reddened NOTHING in the
        first round — not this module and not row D's, which has written the
        same field since `TASK-279`. `--actor` is an ordinary flag, so the
        gap was reachable from any command line; it was simply unasserted.

        The field is not decoration. `schema/state-schema.json` calls it *"who
        declared it. Written from the start, before anything enforces the
        per-kind rule, so DESIGN-015 § 5.5 is AUDITABLE before it is
        enforced"* — § 7's mitigation for the risk that a lane writes a kind it
        may not. An actor that is always `agent` cannot audit anything.
        """
        d = self.project()
        tid = self.new_id(self.declare(d, "a declared row",
                                       "--actor", "a named declarer"))
        rec = [r for r in self.records(d) if r.get("task") == tid][0]
        self.assertEqual(rec["actor"], "a named declarer")

    def test_the_journal_tells_the_three_states_apart(self):
        """A declared row and a never-asked row must not render identically in
        the one human-readable record of the write."""
        d = self.project()
        self.declare(d)
        journal = "\n".join(
            p.read_text() for p in sorted((d / "journal").rglob("*.md")))
        self.assertIn("declared unlinked", journal)
        self.assertNotIn("KR linkage: unlinked", journal)


class TestSilenceIsStillNeverAsked(Fixture):
    """§ 5.2's silence, as TASK-439 left it: refused where it can be answered.

    This class used to assert that omitting both flags stays legal, warns, and
    lands in the DENOMINATOR — § 5.2's "record and warn", and TASK-394's
    control that `--unlinked` had not quietly redefined omission. **TASK-439
    is the row that changed it.** On a project with a linkage register,
    omission is now REFUSED, so a silent row reaches neither numerator nor
    denominator, because there is no row.

    Both halves are kept rather than one deleted, because both are still true
    of some project:

    * WITH a register — silence is refused, and `P003-O3-KR2` does not move at
      all, not even its denominator;
    * with NO register — § 5.2 survives unchanged, that being the one project
      where the question has no answer to give (`--unlinked` is refused
      without a store; `--kr` could only name a key result that does not yet
      exist).

    TASK-394's original point — a declaration is a THIRD state, not a
    replacement for silence — is still driven: by the declaration classes
    above, and by `tests/test_add_refuses_without_an_answer.py
    § TestTheRefusalDoesNotSilentlyDeclare`, which asserts the refusal does not
    convert omission into a declaration behind the caller's back.
    """

    def test_a_row_with_neither_flag_is_refused(self):
        d = self.project()
        before = self.measurement(d)
        proc = self.add(d, "a silent row")
        self.assertNotEqual(proc.returncode, 0,
                            f"silence was accepted:\n{proc.stdout}")
        after = self.measurement(d)
        self.assertEqual(after["numerator"], before["numerator"])
        self.assertEqual(after["denominator"], before["denominator"],
                         "a refused row reached the DENOMINATOR — the refusal "
                         "must fire before the `add` event is written")

    def test_with_no_register_silence_still_files_and_warns(self):
        """§ 5.2 where it survives, driven rather than asserted in prose."""
        d = self.project(with_store=False)
        proc = self.add(d, "a silent row")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tid = self.new_id(proc)
        self.assertIn("never-asked", proc.stderr,
                      "silence stopped warning — § 5.2's `record and warn`")
        after = self.measurement(d)
        self.assertIn(tid, after["never_answered"])
        self.assertNotIn(tid, after["declared_unlinked_at_add"])

    def test_silence_writes_no_linkage_record_at_all(self):
        d = self.project()
        before = len(self.records(d))
        self.add(d, "a silent row")
        self.assertEqual(len(self.records(d)), before,
                         "`add` with no flags wrote a linkage record — "
                         "never-asked is derived from ABSENCE (§ 5.2), and "
                         "since TASK-439 the row is not even created")

    def test_rows_already_filed_are_not_retroactively_declared(self):
        """Spec's must-not #2, and it is why the KR does not jump on landing.
        `TASK-100` was filed by the fixture without an answer; filing a
        declared row beside it must leave it exactly where it was."""
        d = self.project()
        before = self.measurement(d)
        self.declare(d)
        after = self.measurement(d)
        self.assertEqual(after["never_answered"], before["never_answered"],
                         "declaring one row changed another row's state")


class TestTheContradictionIsRefused(Fixture):
    """`--kr` and `--unlinked` are two answers to one question."""

    def test_both_flags_together_are_refused(self):
        d = self.project()
        before = len(self.records(d))
        proc = self.add(d, "a contradicted row", self.STORE_KR, "--unlinked")
        self.assertNotEqual(proc.returncode, 0,
                            "`--kr` and `--unlinked` together were ACCEPTED; "
                            "one of the two answers won silently")
        self.assertIn("contradictory", proc.stdout + proc.stderr)
        self.assertEqual(len(self.records(d)), before,
                         "a refused command wrote to the store")

    def test_the_refusal_says_the_declaration_cannot_be_withdrawn(self):
        """The judgement this row owes the caller, at the point it is made.

        The store is append-only and `perry-task` has no retraction, so a
        caller who picks `--unlinked` to resolve this refusal is making an
        irreversible choice. Telling them afterwards is telling them too late.
        """
        d = self.project()
        proc = self.add(d, "a contradicted row", self.STORE_KR, "--unlinked")
        said = proc.stdout + proc.stderr
        self.assertIn("CANNOT BE WITHDRAWN", said)
        self.assertIn("perry-goals link", said,
                      "the refusal names no way back at all")

    def test_it_is_refused_on_presence_not_on_value(self):
        """`--kr "" --unlinked` is still two answers. Reporting it as a blank
        `--kr` would tell the caller to fix the value when the fix is to drop
        a flag."""
        d = self.project()
        proc = self.add(d, "a contradicted row", None, "--kr", "   ",
                        "--unlinked")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("contradictory", proc.stdout + proc.stderr)

    def test_a_blank_kr_alone_is_still_refused_for_its_own_reason(self):
        """TASK-281 round 2's refusal, unchanged. The contradiction check runs
        first and must not have swallowed it."""
        d = self.project()
        proc = self.add(d, "a blank row", None, "--kr", "   ")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("is blank", proc.stdout + proc.stderr)


class TestAStoreLessProjectRefusesTheDeclaration(Fixture):
    """`--unlinked` has no event field to fall back to, so accepting it on a
    project with no store would file a row that still reads never-asked."""

    def test_the_declaration_is_refused_when_there_is_no_store(self):
        d = self.project(with_store=False)
        proc = self.declare(d)
        self.assertNotEqual(proc.returncode, 0,
                            "`--unlinked` was accepted on a project with no "
                            "linkage store; the declaration went nowhere")
        said = proc.stdout + proc.stderr
        self.assertIn("linkage.jsonl", said)
        self.assertIn("perry-goals link --unlinked", said,
                      "the refusal does not say how to declare it instead")

    def test_the_refusal_creates_no_store(self):
        """The rule row D states for `--kr`: a one-record store on a project
        whose register is the document would replace the whole graph."""
        d = self.project(with_store=False)
        self.declare(d)
        self.assertFalse((d / "linkage.jsonl").exists())

    def test_the_control_the_same_fixture_can_file_a_row(self):
        """Without this, the refusal above passes for any broken fixture —
        which is the green-for-the-wrong-reason `TASK-281` round 1 shipped."""
        d = self.project(with_store=False)
        self.assertEqual(self.add(d, "a control row").returncode, 0)

    def test_a_kr_on_a_store_less_project_is_still_accepted(self):
        """The asymmetry, stated as a test. `--kr` degrades to the event,
        which still records the answer; `--unlinked` has nowhere to degrade
        to. If someone 'fixes the inconsistency' by refusing both, this goes
        red and says why it must not be."""
        d = self.project(with_store=False)
        proc = self.add(d, "a linked row", self.STORE_KR)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tid = self.new_id(proc)
        add = [e for e in self.events(d)
               if e.get("event") == "add" and e.get("id") == tid]
        self.assertEqual(add[0]["kr"], self.STORE_KR)


class TestUnlinkedBelongsToAddAlone(Fixture):
    """Elsewhere the flag would parse, do nothing, and exit 0."""

    def next_action(self, d: pathlib.Path,
                    *extra: str) -> subprocess.CompletedProcess:
        """`next` rather than `start`: the fixture's seeded row is already
        `in_progress`, so `start` refuses for a reason of its own and the
        control below could never distinguish the two refusals. The value
        differs from the fixture's own `carry on` for the same reason: `next`
        refuses a no-op change, which would be a third refusal wearing the
        same exit code."""
        return subprocess.run(
            task_actor.command([sys.executable, str(TASK), "next", "TASK-100", "--root", str(d),
             "--next", "a different next action"] + list(extra), 'test_add_declares_unlinked'),
            capture_output=True, text=True, cwd=ROOT)

    def test_it_is_refused_on_another_subcommand(self):
        d = self.project()
        proc = self.next_action(d, "--unlinked")
        self.assertNotEqual(proc.returncode, 0,
                            "`next --unlinked` was accepted and ignored")
        # The wording moved when the bespoke guard became the general rule
        # (DESIGN-016 goal 12): `SURFACE` lists `--unlinked` under `add` alone
        # and `parse` refuses it everywhere else. What this test is about —
        # refused rather than ignored, and the row untouched — is unchanged.
        message = proc.stdout + proc.stderr
        self.assertIn("--unlinked is not accepted by", message)
        self.assertIn("would have ignored it", message)

    def test_the_control_the_same_subcommand_works_without_it(self):
        """Without this, the refusal above passes for any broken invocation."""
        d = self.project()
        proc = self.next_action(d)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestTheWriterGuardIsReachedWhenCalledDirectly(Fixture):
    """**Mutation M06, and the honest label on how it is closed.**

    Deleting `linkage_add_change`'s own `declared_unlinked and kr` guard
    reddened nothing, because `cmd_add` refuses the contradiction first and
    **no command line can reach this branch**. That is the same shape as row
    D's M15 — an `event != "add"` guard unreachable through the process
    boundary — and it is closed the same way: by calling the writer directly,
    with a shape no command produces today and any second caller could produce
    tomorrow.

    **This closure is NOT on a user-producible input, and it is reported as
    such** rather than counted as an ordinary red. What makes the guard worth
    keeping anyway is measured rather than asserted: mutation M05 deleted
    `cmd_add`'s refusal and `test_both_flags_together_are_refused` STILL
    caught the contradiction — through this guard. The two are individually
    redundant and jointly load-bearing, which is the argument for keeping both
    and is why M17 plants their deletion together.
    """

    def writer(self):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader(
            "perry_task_for_declare_tests", str(TASK))
        spec = importlib.util.spec_from_loader(
            "perry_task_for_declare_tests", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_a_direct_caller_passing_both_answers_is_refused(self):
        mod = self.writer()
        d = self.project()
        with self.assertRaises(mod.Refused) as caught:
            mod.linkage_add_change(
                d, {"event": "add", "id": "TASK-900",
                    "kr": "P003-O1-KR1", "actor": "agent"}, True)
        self.assertIn("contradictory", str(caught.exception))
        self.assertIn("no precedence", str(caught.exception))

    def test_the_refused_call_wrote_nothing(self):
        mod = self.writer()
        d = self.project()
        before = (d / "linkage.jsonl").read_text()
        with self.assertRaises(mod.Refused):
            mod.linkage_add_change(
                d, {"event": "add", "id": "TASK-900",
                    "kr": "P003-O1-KR1", "actor": "agent"}, True)
        self.assertEqual((d / "linkage.jsonl").read_text(), before)

    def test_the_control_the_same_call_without_a_kr_succeeds(self):
        """Without this the assertion above passes for any exception at all —
        an import error, a bad fixture, a signature that stopped matching."""
        mod = self.writer()
        d = self.project()
        change = mod.linkage_add_change(
            d, {"event": "add", "id": "TASK-900", "kr": None,
                "actor": "agent"}, True)
        self.assertIsNotNone(change)
        self.assertEqual(change[2]["kind"], "unlinked")


class TestTheDeclarationIsNotASecondTransaction(Fixture):
    """SIGKILL at **five** crash points; the declaration must not survive alone.

    **Seven until TASK-262 round 4a, measured then.** On this fixture `add`
    made four canonical renames — `tasks.jsonl`, `intake.jsonl`,
    `linkage.jsonl`, the journal — because the held board's `## Intake` put
    the intake register in the canonical set, and then wrote `BOARD.md`. A
    write now builds from the declared board and writes no board file: the
    renames are three (no intake store exists here, and `add` on a project
    track writes none), so `canonical:3` was never reached, and `afterboard`
    (E2, after `BOARD.md` and before the event append) is the same state as
    `afterpair` (E1). Both were deleted rather than kept green for nothing.

    Row D claimed five and drove four. `TASK-279`'s V4 measured seven: its
    harness kills only before renames whose DESTINATION is a canonical target,
    so the marker's own rename, the gap after `replace_canonical_pair`, and the
    event append — an `open(..., "a")`, not a rename — were all structurally
    unreachable by it. This class inherits the seven.

    | # | point                                        | reached by |
    |---|----------------------------------------------|------------|
    | 1-3 | before each canonical rename               | `canonical:N` |
    | M0 | before the MARKER's own rename               | `marker`   |
    | E1 | after `replace_canonical_pair`, before the event append | `afterpair`|

    SIGKILL and not an exception, for row D's reason: an exception unwinds into
    `replace_canonical_pair`'s `except OSError` and takes the deliberate
    rollback path, which is a branch that is already covered. The branch this
    has to survive is the one where nothing gets to run.
    """

    CHILD = r'''
import importlib.machinery, importlib.util, os, signal, sys
TOOL, ROOT, MODE, TITLE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
spec = importlib.util.spec_from_loader(
    "perry_task", importlib.machinery.SourceFileLoader("perry_task", TOOL))
mod = importlib.util.module_from_spec(spec)
sys.modules["perry_task"] = mod
spec.loader.exec_module(mod)
MARKER = ".perry-task-transaction.json"
die = lambda: os.kill(os.getpid(), signal.SIGKILL)
real_replace = os.replace

if MODE.startswith("canonical:"):
    # Row D's counter, unchanged. Only renames whose DESTINATION is a canonical
    # target are counted; the marker is written through `lib.write_atomic`,
    # which renames too, and counting it would make N mean a different crash
    # point on different runs.
    N = int(MODE.split(":")[1])
    seen = [0]
    def counting(src, dst, *a, **kw):
        name = os.path.basename(str(dst))
        canonical = (name in ("tasks.jsonl", "intake.jsonl", "linkage.jsonl")
                     or (name.endswith(".md") and name[:1].isdigit()))
        if not canonical:
            return real_replace(src, dst, *a, **kw)
        if seen[0] >= N:
            die()
        seen[0] += 1
        return real_replace(src, dst, *a, **kw)
    os.replace = counting
elif MODE == "marker":
    # M0 — before the durable marker itself lands. Nothing may be on disk.
    def before_marker(src, dst, *a, **kw):
        if os.path.basename(str(dst)) == MARKER:
            die()
        return real_replace(src, dst, *a, **kw)
    os.replace = before_marker
elif MODE == "afterpair":
    # E1 — the canonical set is entirely on disk; the event is not.
    real_pair = mod.replace_canonical_pair
    def after_pair(*a, **kw):
        real_pair(*a, **kw)
        die()
    mod.replace_canonical_pair = after_pair
else:
    raise SystemExit("unknown mode " + MODE)

sys.exit(mod.main(["add", "--actor", "unlinked-crash-probe", "--title", TITLE, "--root", ROOT,
                   "--deliverable", "d", "--verification", "v",
                   "--unlinked", "--summary",
                   "Files a throwaway row so the writer reaches its writes."]))
'''

    POINTS = ["canonical:0", "canonical:1", "canonical:2",
              "marker", "afterpair"]

    def crash_at(self, d: pathlib.Path, mode: str) -> subprocess.CompletedProcess:
        child = d / "_declare_crash_child.py"
        child.write_text(self.CHILD)
        return subprocess.run(
            task_actor.command([sys.executable, str(child), str(TASK), str(d), mode,
             "an atomicity probe"], 'test_add_declares_unlinked'),
            capture_output=True, text=True, cwd=ROOT)

    def next_id(self, d: pathlib.Path) -> str:
        """The id the crashing run will mint, read off a `--dry-run`.

        Derived rather than assumed: an assertion about the wrong id passes for
        free, which is the shape that makes a crash test decorative.

        **Carries `--unlinked` since TASK-439.** `add` now refuses a row that
        answers the KR question neither way, and the refusal fires before
        `mint_id` — so a `--dry-run` that passes neither flag never reaches the
        id this helper exists to read. It mirrors the flag the crashing run
        itself passes, keeping the probe and the run under test one command
        line apart.
        """
        proc = subprocess.run(
            task_actor.command([sys.executable, str(TASK), "add", "--title", "probe",
             "--root", str(d), "--deliverable", "d", "--verification", "v",
             "--summary", "Reads back the id the next add will mint.",
             "--unlinked", "--dry-run", "--json"], 'test_add_declares_unlinked'),
            capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)["id"]

    def test_the_declaration_never_survives_without_its_row(self):
        for mode in self.POINTS:
            with self.subTest(crash_point=mode):
                d = self.project()
                tid = self.next_id(d)
                proc = self.crash_at(d, mode)
                self.assertEqual(
                    proc.returncode, -signal.SIGKILL,
                    f"the child exited {proc.returncode} instead of dying — "
                    f"the crash point was never reached, so this subtest "
                    f"proves nothing. stderr={proc.stderr[:300]}")

                # Mid-crash: the declaration must never be on disk for a row
                # `tasks.jsonl` does not carry.
                self.assertFalse(
                    self.has_declaration(d, tid) and not self.has_row(d, tid),
                    f"at {mode} the store held an `unlinked` declaration for "
                    f"a task `tasks.jsonl` does not carry")

                # "The next locked Perry run." Read-only on purpose: recovery
                # must not need a second WRITE, or a crashed tree stays broken
                # until somebody happens to file another row.
                rec = subprocess.run(
                    [sys.executable, str(TASK), "list", "--root", str(d)],
                    capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(rec.returncode, 0, rec.stderr)

                self.assertEqual(
                    self.has_row(d, tid), self.has_declaration(d, tid),
                    f"after recovery at {mode} the row and its declaration "
                    f"disagree — the declaration is a second transaction that "
                    f"half-landed")

    def test_the_marker_does_not_outlive_recovery(self):
        d = self.project()
        self.crash_at(d, "canonical:2")
        self.assertTrue((d / MARKER).exists(),
                        "no marker after the crash — the transaction was "
                        "never staged and the probe measured nothing")
        subprocess.run([sys.executable, str(TASK), "list", "--root", str(d)],
                       capture_output=True, text=True, cwd=ROOT)
        self.assertFalse((d / MARKER).exists(),
                         "the marker survived a locked run")

    def test_a_crash_before_the_marker_lands_writes_nothing(self):
        """M0. Named separately from the loop because its verdict is stronger:
        not merely 'not alone' but 'nothing at all', and a marker left behind
        here would be a transaction no run can resolve."""
        d = self.project()
        before = len(self.records(d))
        tid = self.next_id(d)
        proc = self.crash_at(d, "marker")
        self.assertEqual(proc.returncode, -signal.SIGKILL, proc.stderr[:300])
        self.assertFalse(self.has_row(d, tid))
        self.assertFalse(self.has_declaration(d, tid))
        self.assertEqual(len(self.records(d)), before)
        self.assertFalse((d / MARKER).exists())

    def test_after_the_canonical_set_lands_the_declaration_has_its_row(self):
        """E1's positive half. 'Never alone' is satisfied vacuously if the
        declaration never lands at all, so the late point must be shown to land
        it WITH its row rather than to have dropped both."""
        for mode in ("afterpair",):
            with self.subTest(crash_point=mode):
                d = self.project()
                tid = self.next_id(d)
                self.crash_at(d, mode)
                self.assertTrue(
                    self.has_row(d, tid),
                    f"at {mode} the canonical set had already landed, so the "
                    f"row must be on disk — this probe measured nothing")
                self.assertTrue(
                    self.has_declaration(d, tid),
                    f"at {mode} the row landed without its declaration — the "
                    f"declaration is NOT in the canonical set")


if __name__ == "__main__":
    unittest.main()
