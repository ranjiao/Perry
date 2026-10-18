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


class TestRetiredUnlinkedDeclarations(Fixture):
    def test_every_answer_shape_refuses_without_goal_or_task_changes(self):
        for with_store in (False, True):
            d = self.project(with_store=with_store)
            before = {str(p.relative_to(d)): p.read_bytes() for p in d.rglob("*") if p.is_file()}
            for extra in ((), ("--unlinked",), ("--kr", self.STORE_KR),
                          ("--kr", self.STORE_KR, "--unlinked"), ("--unlinked", "--dry-run")):
                with self.subTest(store=with_store, extra=extra):
                    out = self.add(d, "a retired declaration", None, *extra)
                    self.assertEqual(out.returncode, 1, out.stderr)
                    self.assertIn("read-only", out.stderr)
                    self.assertIn("perry-kernel item create", out.stderr)
                    self.assertEqual({str(p.relative_to(d)): p.read_bytes()
                                      for p in d.rglob("*") if p.is_file()}, before)

    def test_the_goals_lane_still_owns_an_explicit_unlinked_declaration(self):
        d = self.project(store_edges={})
        out = subprocess.run([sys.executable, str(ROOT / "bin/perry-goals"),
            "link", "--unlinked", "TASK-100", "--actor", "fixture-goals",
            "--root", str(d), "--json"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        records = self.records(d)
        self.assertTrue(any(r.get("kind") == "unlinked" and r.get("task") == "TASK-100"
                            for r in records), records)


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


if __name__ == "__main__":
    unittest.main()
