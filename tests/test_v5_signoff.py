"""TASK-109 — a V5 sign-off is SELECTED from measured facts, not authored.

V5 is the one rung whose content is a human's: "name, date, and what they
checked". Until this row the tool took none of it. `done --rung V5` wrote a
rung, and the signature was a paragraph the user composed by hand.

TASK-047 is the case that named the defect. Perry ran three checks, printed
their output, and showed the user; the user then wrote, from memory, a sentence
describing those same three checks. Two things are wrong with that, and the
second is the one that matters:

  1. the user re-derives by hand a record the system already holds, and
  2. free text cannot distinguish *I re-ran this* from *Perry ran this and I
     read the output*. The gap widens the more Perry does.

What keeps the fix from being a rubber stamp is one rule, and it is enforced
here mechanically rather than by review:

    Perry may draft only facts it MEASURED. It may never draft a claim about
    what the USER did.

`TestNoDraftedOptionAssertsAUserAction` is that rule as a test over the option
builder — the only place a drafted string is minted.

Run: python3 -m unittest discover -s tests   (or ./tests/run)
"""

from __future__ import annotations

import task_actor

COVERS = (
    "bin/perry-task",
    "reference/host-capabilities.md",
    "schema/state-schema.json",
    "SKILL.md",
    "perry/",
    ".perry/",
)

import importlib.machinery
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from kernel_work_support import ACTOR, ready, task
from datetime import date
from pathlib import Path


PERRY_HOME = Path(__file__).resolve().parent.parent
TOOL = PERRY_HOME / "bin" / "perry-task"
TASKS = PERRY_HOME / "bin" / "perry-tasks"


def load_tool():
    spec = importlib.util.spec_from_loader(
        "perry_task", importlib.machinery.SourceFileLoader("perry_task", str(TOOL)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PT = load_tool()

BOARD = """# Board — T

## P0 (must finish this period)

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P1

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|

## P2

| ID | Title | Owner | Status | Next action | Evidence |
|---|---|---|---|---|---|
"""

#: The fixture V5 verification 1 asks for: three facts Perry measured during
#: the task, and one claim it is only passing along. Worded the way a real
#: dispatch would word them — an observation, never an act.
MEASURED = [
    "claims[] carries zero changed lines in the diff on schema/state-schema.json",
    "write behaviour under enforce / advisory / declared: 3 runs, exit codes recorded",
    "the perry-migrate exemption still runs on an undeclared project",
]
RESTATED = ["the branch carrying this change is unmerged"]


class Project:
    """A throwaway Perry project the tool can close a row in."""

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = Path(self.dir.name)
        # Installed the way a start installs a project (TASK-237 round 2).
        import config_store
        config_store.write_config(self.root)
        (self.root / "BOARD.md").write_text(BOARD)
        r = subprocess.run(
            ["python3", str(TASKS), "write", "--from-board", "--root",
             str(self.root)], capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stdout + r.stderr)

    def run(self, *argv) -> tuple[int, dict | str]:
        r = subprocess.run(
            task_actor.command(["python3", str(TOOL), *argv, "--root", str(self.root), "--json"], 'test_v5_signoff'),
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def a_task(self) -> str:
        """Explicit archived input for the retained read-only offer command."""
        path = self.root / "tasks.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        tid = f"TASK-{len(rows)+1:03}"
        rows.append(PT.perry_store.record({"id": tid, "title": "Flip the conformance default",
            "status": "not_started", "priority": "P1", "verification": "V5"}, len(rows)))
        path.write_text(PT.perry_store.store_text(rows))
        return tid

    def journal(self) -> str:
        for p in (self.root / "journal").rglob("*.md"):
            return p.read_text()
        return ""

    def events(self) -> list[dict]:
        p = self.root / ".perry" / "events.jsonl"
        return ([json.loads(l) for l in p.read_text().split("\n") if l.strip()]
                if p.exists() else [])

    def close_v5(self, tid, *extra):
        return self.run("done", tid, "--evidence", "evidence/x.md",
                        "--rung", "V5",
                        *[f for t in MEASURED for f in ("--measured", t)],
                        *[f for t in RESTATED for f in ("--restated", t)],
                        *extra)

    def __del__(self):
        self.dir.cleanup()


class TestRetainedSelectionRecordUnits(unittest.TestCase):
    def test_selection_keeps_every_fact_and_its_provenance(self):
        options = PT.signoff_options(MEASURED, RESTATED)
        sig = PT.build_signoff(options, {1, 3}, set(), "", "Example signer", "2026-09-01")
        self.assertEqual(sig["counts"], {"checked": 2, "accepted on report": 2, "not looked at": 0})
        self.assertEqual([i["text"] for i in sig["items"] if i["disposition"] == "checked"],
                         [MEASURED[0], MEASURED[2]])
        self.assertEqual([i["text"] for i in sig["items"]], MEASURED + RESTATED)
        self.assertEqual([i["provenance"] for i in sig["items"]],
                         ["Perry verified"] * 3 + ["restated — Perry did not verify this"])
        block = PT.render_signoff("TASK-001", sig)
        for text in ("Example signer", "2026-09-01", "**checked**", "**accepted on report**", *MEASURED, *RESTATED):
            self.assertIn(text, block)
        self.assertEqual(read_signatures("## V5 sign-off\n\n" + block)[0]["who"], "Example signer")


class TestRetainedFreeTextUnits(unittest.TestCase):
    def test_user_words_join_the_selection_without_being_drafted_by_perry(self):
        options = PT.signoff_options(MEASURED, RESTATED)
        for checked in ({2}, set()):
            sig = PT.build_signoff(options, checked, set(), "I reviewed the diff myself.",
                                   "Example signer", "2026-09-01")
            self.assertEqual(len(sig["items"]), 4)
            self.assertEqual(sig["counts"]["checked"], len(checked))
            self.assertEqual(sig["also_checked"], "I reviewed the diff myself.")
            self.assertIn(sig["also_checked"], PT.render_signoff("TASK-001", sig))


class TestNoDraftedOptionAssertsAUserAction(unittest.TestCase):
    """V5 verification 3 and deliverable 6, as a machine check.

    This is the load-bearing test in the file. If Perry may draft *the user
    reviewed the diff*, then a V5 close is Perry certifying its own work with a
    human's name on it, and every other guarantee here is decoration.

    A review comment cannot enforce this: it holds until the first hurried
    close. `PT.signoff_options` is the only place a drafted string is minted,
    so the rule is checked there and nowhere else needs to remember it.
    """

    #: Each of these is a claim about a person. None is Perry's to write.
    USER_CLAIMS = [
        "the user reviewed the diff",
        "the user accepted the two costs",
        "you confirmed the migrate exemption",
        "your checkout was declared",
        "the human read the fixture opt-out reasoning",
        "the reviewer signed off on the rung",
        "the signer approved the enforce default",
        "reviewed the claims[] diff",
        "approved the migration plan",
        "accepted on the strength of the printed output",
        "acknowledged the residue on a real board",
        "用户已阅并接受两项代价",
        "同意把 enforce 设为默认值",
    ]

    #: The complement, and the anti-vacuity guard: a rule that refused
    #: everything would pass the list above and be useless. Every one of these
    #: is a fact Perry can measure, and several are near-misses on purpose —
    #: `user-facing` contains `user`, `acceptance` contains `accept`.
    MEASURABLE = [
        "claims[] carries zero changed lines in the diff",
        "the perry-migrate exemption still runs on an undeclared project",
        "the user-facing message names the mode rather than the literal string",
        "3 of 80 closed rows carry V5",
        "the acceptance-criteria file resolves to an existing path",
        "tests/parallel: 59 modules, 1717 tests, 3 red",
        "SKILL.md is 21030 bytes against a 20480 cap",
        "owner is present on 21 of 21 open rows and 0 of 60 closed ones",
    ]

    def test_a_drafted_claim_about_a_person_is_refused(self):
        for claim in self.USER_CLAIMS:
            for flag, kwargs in (("--measured", {"measured": [claim]}),
                                 ("--restated", {"restated": [claim]})):
                with self.subTest(claim=claim, flag=flag):
                    with self.assertRaises(PT.Refused) as caught:
                        PT.signoff_options(kwargs.get("measured", []),
                                           kwargs.get("restated", []))
                    self.assertIn(claim, str(caught.exception),
                                  "the refusal must quote what it refused")

    def test_a_measured_fact_is_not_refused(self):
        options = PT.signoff_options(self.MEASURABLE, [])
        self.assertEqual(len(options), len(self.MEASURABLE))
        self.assertEqual([o["n"] for o in options],
                         list(range(1, len(self.MEASURABLE) + 1)))

    def test_the_refusal_reaches_the_cli_not_just_the_function(self):
        p = Project()
        tid = p.a_task()
        code, out = p.run("signoff-offer", tid,
                          "--measured", "the user reviewed the diff")
        self.assertEqual(code, 1)
        self.assertIn("refused", out)
        self.assertEqual(p.journal().count("V5 sign-off"), 0,
                         "a refused sign-off wrote something anyway")

    def test_no_option_the_builder_emits_carries_a_user_claim(self):
        """The rule stated over the OUTPUT rather than the input, so a future
        builder that rewrites or decorates an option cannot smuggle one past
        the entry check."""
        for option in PT.signoff_options(self.MEASURABLE, ["a restated claim"]):
            PT.check_no_user_claim(option["text"], "--measured")
            self.assertIn(option["provenance"],
                          ("Perry verified",
                           "restated — Perry did not verify this"))


class TestRetainedEmptySignatureUnits(unittest.TestCase):
    def test_nothing_checked_and_no_user_words_is_refused(self):
        for options in ([], PT.signoff_options(MEASURED, RESTATED)):
            with self.assertRaises(PT.Refused):
                PT.build_signoff(options, set(), set(), "", "Example signer", "2026-09-01")

    def test_an_empty_offered_fact_is_refused(self):
        with self.assertRaises(PT.Refused):
            PT.signoff_options([""], [])


class TestRetainedDispositionUnits(unittest.TestCase):
    def test_not_looked_at_is_explicit_and_never_a_default(self):
        options = PT.signoff_options(MEASURED, RESTATED)
        sig = PT.build_signoff(options, {1}, {2}, "", "Example signer", "2026-09-01")
        self.assertEqual([i["disposition"] for i in sig["items"]],
                         ["checked", "not looked at", "accepted on report", "accepted on report"])
        default = PT.build_signoff(options, {1}, set(), "", "Example signer", "2026-09-01")
        self.assertEqual(default["counts"]["not looked at"], 0)
        with self.assertRaises(PT.Refused):
            PT.build_signoff(options, {1}, {1}, "", "Example signer", "2026-09-01")


class TestTheOfferIsBuiltNotComposed(unittest.TestCase):
    """Deliverable 1, and the numbering contract between offer and close."""

    def test_the_offer_numbers_items_the_way_done_reads_them(self):
        p = Project()
        tid = p.a_task()
        code, offer = p.run(
            "signoff-offer", tid,
            *[f for t in MEASURED for f in ("--measured", t)],
            *[f for t in RESTATED for f in ("--restated", t)])
        self.assertEqual(code, 0, offer)
        self.assertEqual([o["text"] for o in offer["options"]],
                         MEASURED + RESTATED)
        sig = PT.build_signoff(offer["options"], {3}, set(), "", "Example signer", "2026-09-01")
        picked = [i["text"] for i in sig["items"] if i["disposition"] == "checked"]
        self.assertEqual(picked, [offer["options"][2]["text"]],
                         "option 3 in the prompt is not option 3 in the record")

    def test_the_offer_writes_nothing(self):
        p = Project()
        tid = p.a_task()
        before = (p.root / "BOARD.md").read_text()
        p.run("signoff-offer", tid, "--measured", MEASURED[0])
        self.assertEqual((p.root / "BOARD.md").read_text(), before)
        self.assertEqual(p.events(), [])

    def test_it_degrades_to_a_numbered_free_text_prompt(self):
        """`reference/host-capabilities.md § Prompt rendering`: Codex has no
        selection UI and gets numbered options plus free text. The RENDERING
        changes per host; the record does not."""
        p = Project()
        tid = p.a_task()
        _, offer = p.run("signoff-offer", tid,
                         *[f for t in MEASURED for f in ("--measured", t)])
        self.assertTrue(offer["multi_select"])
        prompt = offer["prompt"]
        for n in (1, 2, 3):
            self.assertIn(f"  {n}) ", prompt)
        self.assertIn("all", prompt)
        self.assertIn("none", prompt)
        self.assertIn("accepted on report", prompt)
        self.assertIn(tid, prompt)

    def test_retired_close_refuses_either_selection_spelling_without_changes(self):
        p = Project()
        tid = p.a_task()
        before = {str(f.relative_to(p.root)): f.read_bytes()
                  for f in p.root.rglob("*") if f.is_file()}
        for extra in (("--checked", "1,3"), ("--checked", "1", "--checked", "3")):
            code, out = p.close_v5(tid, *extra)
            self.assertEqual(code, 1, out)
            self.assertIn("read-only", out["refused"])
            self.assertEqual({str(f.relative_to(p.root)): f.read_bytes()
                              for f in p.root.rglob("*") if f.is_file()}, before)

    def test_an_offer_with_nothing_measured_is_refused(self):
        p = Project()
        tid = p.a_task()
        code, _ = p.run("signoff-offer", tid)
        self.assertEqual(code, 1)

    def test_a_signoff_on_a_rung_that_is_not_v5_is_refused(self):
        """V5 is "human sign-off"; V4 is a rubric and V6 is the world. Hanging
        a signature on either records a human gate nobody asked for."""
        for rung in ("V3", "V4", "V6"):
            with self.subTest(rung=rung):
                p = Project()
                code, _ = p.run("done", p.a_task(), "--evidence", "e.md",
                                "--rung", rung, "--measured", MEASURED[0],
                                "--checked", "1")
                self.assertEqual(code, 1)


# ── reading the signatures the journal already holds ──────────────────────
# The old test named three task ids. Three more were signed the afternoon it
# shipped and it went red on a set-difference — the same shape `c9018ae` had
# already fixed once that day in `test_board_render` (`rows_from_store > 20`,
# made false by an ordinary close). **A count taken from live project state is
# not a property; it is a snapshot with an expiry date nobody wrote down.**
#
# The property is what the count was standing in for: every signature already
# in the journal still parses, and still reads with its disposition headings
# intact. It holds over three signatures and over thirty, and a signature added
# tomorrow satisfies it or reddens it on its own merits.

#: `render_signoff` in `bin/perry-task` writes exactly this header.
SIG_HEAD = re.compile(
    r"^\*\*(?P<id>[A-Z][A-Z0-9]*-\d+) — V5 sign-off\. "
    r"(?P<who>.+?), (?P<when>\d{4}-\d{2}-\d{2})\.\*\*$")
#: A disposition heading, or the free-text heading that may follow the groups.
SIG_HEADING = re.compile(r"^\*\*(?P<label>[^*]+)\*\*$")
#: `- <text> *(<provenance>)*`
SIG_ITEM = re.compile(r"^- (?P<text>.+?) \*\((?P<prov>[^)]+)\)\*$")

DISPOSITIONS = ("checked", "accepted on report", "not looked at")
PROVENANCES = ("Perry verified", "restated — Perry did not verify this")
FREE_TEXT_HEADING = "checked, and not among what Perry offered"


def read_signatures(text: str) -> list[dict]:
    """Every `## V5 sign-off` block in one journal file, parsed.

    Deliberately a re-implementation rather than an import of
    `render_signoff`: a reader with the writer's own code cannot tell you the
    markdown is still readable, only that it is self-consistent.
    """
    sigs: list[dict] = []
    in_section = False
    cur: dict | None = None
    label: str | None = None
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith("## "):
            in_section = line.strip() == "## V5 sign-off"
            cur = None
            continue
        if not in_section or not line.strip():
            continue
        head = SIG_HEAD.match(line.strip())
        if head:
            cur = {**head.groupdict(), "line": n, "groups": {}, "free": None}
            sigs.append(cur)
            label = None
            continue
        if cur is None:
            continue
        heading = SIG_HEADING.match(line.strip())
        if heading:
            label = heading.group("label")
            if label != FREE_TEXT_HEADING:
                cur["groups"].setdefault(label, [])
            continue
        item = SIG_ITEM.match(line.strip())
        if item and label is not None and label != FREE_TEXT_HEADING:
            cur["groups"].setdefault(label, []).append(
                (item.group("text"), item.group("prov")))
        elif label == FREE_TEXT_HEADING:
            cur["free"] = line.strip()
    return sigs


def unreadable(sig: dict) -> list[str]:
    """Everything wrong with one parsed signature, as readable lines.

    One function, used by the live check and by the mutation test that proves
    the live check can fail. A guard nobody has watched go red is not a guard.
    """
    bad = []
    if not sig["who"].strip():
        bad.append(f"{sig['id']}: the signer's name is gone")
    for label in sig["groups"]:
        if label not in DISPOSITIONS:
            bad.append(f"{sig['id']}: {label!r} is not a disposition this "
                       f"format defines")
    if not any(sig["groups"].get(d) for d in DISPOSITIONS):
        if not sig["free"]:
            bad.append(f"{sig['id']}: no disposition heading carries an item, "
                       f"and there is no free-text statement either")
    for label, items in sig["groups"].items():
        if label in DISPOSITIONS and not items:
            bad.append(f"{sig['id']}: the {label!r} heading is empty")
        for text, prov in items:
            if prov not in PROVENANCES:
                bad.append(f"{sig['id']}: {text[:40]!r} carries provenance "
                           f"{prov!r}, which is not one this format defines")
    return bad


class TestHistoryIsNotRewritten(unittest.TestCase):
    """V5 verification 5 — this adds a path; it does not touch what is signed.

    Two generations of signature live in this repository and both must keep
    reading. The closes that PREDATE the selection format carry no `signoff`
    key, and their evidence file is the signature: a name and a date in prose.
    The ones written by `render_signoff` carry a `signoff` in the event and a
    block in the journal, and their dispositions must still be there.

    **Nothing here names a task id or a total.** Every assertion is quantified
    over whatever the log and the journal hold when it runs, so signing another
    row tomorrow cannot redden it — only rewriting one can.
    """

    def v5_events(self):
        log = PERRY_HOME / ".perry" / "events.jsonl"
        out = []
        for line in log.read_text().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("rung") == "V5" and event.get("event") == "done":
                out.append(event)
        return out

    def signatures(self):
        sigs = []
        for path in sorted((PERRY_HOME / "perry" / "journal").rglob("*.md")):
            sigs += read_signatures(path.read_text())
        return sigs

    def evidence(self, e):
        """State-root-relative, or repo-relative if it starts `perry/`."""
        p = e["evidence"]
        return PERRY_HOME / (p if p.startswith("perry/") else "perry/" + p)

    def test_every_v5_close_in_the_log_still_reads(self):
        """The property the count of three was standing in for."""
        events = self.v5_events()
        self.assertTrue(events, "no V5 close reads out of the log at all")
        for e in events:
            with self.subTest(tid=e["id"]):
                self.assertTrue(e.get("evidence"),
                                "a V5 close lost its evidence path")
                self.assertTrue(
                    self.evidence(e).exists(),
                    f"{e['evidence']} is gone; a signature points at nothing")

    def test_a_close_predating_the_format_was_not_back_filled(self):
        """A signature must never appear on a close that did not have one.

        Which closes those are is read from the log rather than listed: an
        event with no `signoff` key predates the format by definition, and that
        stays true however many closes join it.
        """
        old = [e for e in self.v5_events() if "signoff" not in e]
        self.assertTrue(old, "the pre-format closes vanished from the log")
        for e in old:
            with self.subTest(tid=e["id"]):
                text = self.evidence(e).read_text()
                self.assertRegex(text, r"\d{4}-\d{2}-\d{2}",
                                 "the signature lost its date")
                self.assertTrue(
                    re.search(r"[Ss]igned off|sign-off|签", text),
                    "the signature block is no longer findable in the file")

    def test_every_signature_in_the_journal_still_parses(self):
        """Item 1, stated over the corpus instead of over a list of three."""
        sigs = self.signatures()
        self.assertTrue(sigs, "no V5 signature parses out of the journal")
        problems = [p for s in sigs for p in unreadable(s)]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_the_journal_block_and_the_event_agree_on_the_dispositions(self):
        """The anti-rewrite check with teeth.

        A signature can lose its meaning without losing its shape — move one
        item from `checked` to `accepted on report` and the block still parses.
        The event carries the counts the user actually chose, and it is a
        different file, so the two disagreeing is exactly what a rewritten
        record looks like.
        """
        by_id = {s["id"]: s for s in self.signatures()}
        signed = [e for e in self.v5_events() if "signoff" in e]
        self.assertTrue(signed, "no close carries the selection format")
        for e in signed:
            with self.subTest(tid=e["id"]):
                sig = by_id.get(e["id"])
                self.assertIsNotNone(
                    sig, "an event carries a signature the journal does not")
                counts = {d: len(sig["groups"].get(d, []))
                          for d in DISPOSITIONS}
                self.assertEqual(counts, e["signoff"]["counts"],
                                 "the journal block and the event disagree "
                                 "about what was checked")

    def test_the_check_fails_on_a_record_whose_dispositions_were_rewritten(self):
        """Verification 2 — the check is watched going red before it is trusted.

        The mutation is done on a COPY of the journal text, in memory. `perry/`
        is the PMO's state and this file writes none of it.
        """
        text = (PERRY_HOME / "perry" / "journal" / "2026-08"
                / "2026-08-20.md").read_text()
        self.assertEqual([p for s in read_signatures(text) for p in unreadable(s)],
                         [], "the unmutated journal is already failing")
        for mutation, why in (
                (lambda t: t.replace("**accepted on report**", "**accepted**", 1),
                 "a disposition heading renamed"),
                (lambda t: t.replace("*(Perry verified)*", "*(verified)*", 1),
                 "a provenance label rewritten"),
                (lambda t: re.sub(r"(— V5 sign-off\. ).+?(, \d{4})",
                                  r"\1 \2", t, count=1),
                 "the signer's name blanked"),
                (lambda t: t.replace(
                    "- the dangling-id check reports [] — TASK-107 resolves "
                    "and REL-00 is gone *(Perry verified)*\n", "", 1),
                 "an item deleted out of a signed record")):
            with self.subTest(mutation=why):
                mutated = mutation(text)
                self.assertNotEqual(mutated, text, "the mutation did nothing")
                found = [p for s in read_signatures(mutated)
                         for p in unreadable(s)]
                counts = {s["id"]: {d: len(s["groups"].get(d, []))
                                    for d in DISPOSITIONS}
                          for s in read_signatures(mutated)}
                drifted = [e["id"] for e in self.v5_events()
                           if "signoff" in e
                           and counts.get(e["id"]) != e["signoff"]["counts"]]
                self.assertTrue(found or drifted, f"{why} was not caught")

    def test_rendering_a_second_signature_preserves_the_first_block(self):
        options = PT.signoff_options(MEASURED, RESTATED)
        first = PT.build_signoff(options, {1}, set(), "", "Example signer", "2026-09-01")
        second = PT.build_signoff(options, {2}, {4}, "", "Example signer", "2026-09-02")
        one = PT.render_signoff("TASK-001", first)
        two = PT.render_signoff("TASK-002", second)
        self.assertEqual(read_signatures("## V5 sign-off\n\n" + one + two)[0], read_signatures("## V5 sign-off\n\n" + one)[0])
        self.assertEqual([s["id"] for s in read_signatures("## V5 sign-off\n\n" + one + two)], ["TASK-001", "TASK-002"])


class TestNativeHumanBoundary(unittest.TestCase):
    def test_v5_needs_a_human_actor_and_keeps_the_signed_evidence(self):
        sb = ready(self)
        tid = task(sb, verification="V5")
        before = sb.seq()
        out = sb.run("item move", data={"actor": ACTOR, "id": tid,
            "transition": "done", "set": {"evidence": "evidence/signoff.md"}})
        self.assertFalse(out.ok, out)
        self.assertEqual(sb.seq(), before)
        self.assertEqual(sb.get(tid)["state"], "not_started")
        human = {"kind": "human", "name": "Example signer", "session": "fixture-human-signoff"}
        sb.ok("attach add", data={"actor": human, "id": tid, "ref": "evidence/signoff.md"})
        sb.move(tid, "done", actor=human, set={"evidence": "evidence/signoff.md"})
        self.assertEqual(sb.get(tid)["state"], "done")
        self.assertEqual(sb.events()[-1]["actor"], human)
        self.assertEqual(sb.get(tid)["fields"]["evidence"], "evidence/signoff.md")
        self.assertFalse((sb.root / "journal").exists())

    def test_v3_closure_does_not_invent_a_human_signature(self):
        sb = ready(self)
        tid = task(sb, verification="V3")
        sb.move(tid, "done", set={"evidence": "proof.md"})
        self.assertEqual(sb.events()[-1]["actor"], ACTOR)
        self.assertIsNone(sb.get(tid)["fields"]["verified_by"])


if __name__ == "__main__":
    unittest.main()
