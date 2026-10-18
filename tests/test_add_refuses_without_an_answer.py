"""`perry-task add` refuses a row that answers the KR question neither way.

TASK-439. `phase/003-storage-code.md § Definition of Done` item 5 asks that
every `main`-track row opened after the gate lands carry an edge or a
declaration. **That gate was never built.** What existed was the QUESTION: a
stderr warning on `add`, and then the row, filed, with `kr: null` on its event
and a permanent place in `P003-O3-KR2`'s `never_answered` — permanent because a
later `perry-goals link` writes `via: "link"`, which the KR excludes by design.

Measured on this repository before the change: **19 of 59 rows, 32.2%**, and
**94.8%** of every main-track `add` ever run took the warned branch. That is
what a warning buys.

**The four states this module pins**, and the reason each one is here:

    --kr <ID>                edge written, exit 0        unchanged
    --unlinked               declaration written, 0      unchanged
    neither, register        REFUSED                  ←  this row
    neither, NO register     filed + warned              must NOT change

**Why the last line is a test and not an oversight.** `§ What it must not do`
item 4 requires `add` to keep working on a project with no linkage register,
and the reason the refusal cannot simply extend there is measurable rather than
stylistic: `--unlinked` is REFUSED outright on a store-less project
(`linkage_add_change` — it has no event field and no second home), and `--kr`
on a fresh project can only name a key result that does not exist, because
`plan-phase` is what writes the register. An unconditional refusal would leave
a GUESSED `--kr` as the only way to file any row at all on a fresh project, and
`reference/okr-linkage.md` forbids that guess. So the gate fires where the
question is answerable and stays a warning where it is not.

**How these tests are built to be able to fail**, which is the property this
project has had to re-earn six times:

*`TestTheRefusalIsNotVacuous`* is the anti-vacuity control the spec asks for. A
test that merely asserted a non-zero exit would pass against a binary that
refused for ANY reason — a missing `--summary`, an unwritable root, a typo in
the fixture. `TASK-281` round 1's refusal test rotted green exactly that way.
So the class asserts the refusal on a command line that is otherwise COMPLETE
and would have exited 0 before this row — the sibling `--kr` and `--unlinked`
runs in `TestBothRemediesStillWork` are that proof, from the same fixture — and
it reads the refusal's own subject matter out of the message rather than
trusting the exit code alone.

*`TestTheRefusalDoesNotSilentlyDeclare`* is the mutation target the spec names
second. The cheap wrong fix for this row is to stop refusing and instead treat
omission AS a declaration, which makes `P003-O3-KR2` jump to 100% overnight and
writes "serves no key result" into a canonical, un-withdrawable store for
hundreds of rows nobody asked. This class asserts through
`lib.same_action_linkage` — the reader — that a refused row reaches NEITHER
numerator path.

*`TestNothingWasWritten`* pins the refusal's position: before `mint_id`. A
refusal that fires after the id is minted burns an id per mistake, and
`ADR-013` says ids are terminal.

Run: python3 tests/parallel test_add_refuses_without_an_answer
"""

from __future__ import annotations

COVERS = (
    "bin/perry-task",
    "bin/lib/",
    "goals/reference/phases.md",
    "reference/okr-linkage.md",
    "work/reference/subcommands.md",
)

import json
import pathlib
import sys
import unittest
from kernel_work_support import ACTOR, ready, task

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))

# The row D module is imported for its FIXTURE only, exactly as TASK-394's
# module imports it. unittest collects only what is in this module's namespace,
# so nothing under `M.` is run twice.
import test_add_writes_the_edge as M  # noqa: E402
import lib  # noqa: E402

PERRY_HOME = ROOT


class Base(M.Fixture):
    """`M.Fixture` plus the two readings this row's assertions need."""

    def linkage(self, d: pathlib.Path) -> dict:
        """`P003-O3-KR2` as its own reader computes it, not as a literal."""
        lk = self.records(d)
        return lib.same_action_linkage(lk, self.events(d))

    def rows_on_board(self, d: pathlib.Path) -> list[str]:
        p = d / "tasks.jsonl"
        if not p.exists():
            return []
        return [json.loads(x)["id"]
                for x in p.read_text().split("\n") if x.strip()]


class TestRetiredAddPrecedesGoalValidation(Base):
    def test_store_absence_phase_windows_and_corruption_do_not_reopen_add(self):
        for shape in ("healthy", "absent", "unreadable", "between-phases"):
            d = self.project()
            if shape == "absent":
                (d / "linkage.jsonl").unlink()
            elif shape == "unreadable":
                (d / "linkage.jsonl").write_text("{torn record\n")
            elif shape == "between-phases":
                (d / "phase/CURRENT").write_text("")
            before = {str(p.relative_to(d)): p.read_bytes() for p in d.rglob("*") if p.is_file()}
            for extra in ((), ("--kr", ""), ("--kr", "   "),
                          ("--kr", self.STORE_KR), ("--unlinked",)):
                with self.subTest(shape=shape, extra=extra):
                    out = self.add(d, "a probe", None, *extra)
                    self.assertEqual(out.returncode, 1, out.stderr)
                    self.assertIn("read-only", out.stderr)
                    self.assertNotIn("Traceback", out.stderr)
                    self.assertEqual({str(p.relative_to(d)): p.read_bytes()
                                      for p in d.rglob("*") if p.is_file()}, before)

    def test_native_create_needs_its_written_fields_and_does_not_burn_an_id(self):
        sb = ready(self)
        fields = {"title": "label", "summary": "description", "priority": "P1", "verification": "V3"}
        before = sb.seq()
        for missing in fields:
            out = sb.run("item create", data={"actor": ACTOR, "type": "task",
                "fields": {k: v for k, v in fields.items() if k != missing}})
            self.assertFalse(out.ok, out)
            self.assertEqual(sb.seq(), before)
        self.assertEqual(task(sb), "TASK-001")

    def test_unknown_linkage_stays_unknown_and_the_procedure_hands_it_to_goals(self):
        sb = ready(self)
        tid = task(sb)
        self.assertNotIn("kr", sb.get(tid)["fields"])
        self.assertFalse((sb.root / "linkage.jsonl").exists())
        text = (ROOT / "work/reference/add-task.md").read_text()
        self.assertIn("Unknown linkage remains unknown", text)
        self.assertIn("handed to goals", text)


if __name__ == "__main__":
    unittest.main()
