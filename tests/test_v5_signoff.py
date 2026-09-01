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

import importlib.machinery
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
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
        (self.root / ".perry").mkdir()
        (self.root / ".perry" / "config.md").write_text(
            "# Perry configuration\n\n- Document language: English\n"
            "- Repo layout: single\n- State root: .\n")
        (self.root / "BOARD.md").write_text(BOARD)
        r = subprocess.run(
            ["python3", str(TASKS), "write", "--from-board", "--root",
             str(self.root)], capture_output=True, text=True)
        if r.returncode:
            raise AssertionError(r.stdout + r.stderr)

    def run(self, *argv) -> tuple[int, dict | str]:
        r = subprocess.run(
            ["python3", str(TOOL), *argv, "--root", str(self.root), "--json"],
            capture_output=True, text=True)
        try:
            return r.returncode, json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return r.returncode, r.stdout + r.stderr

    def a_task(self) -> str:
        _, a = self.run("add", "--title", "Flip the conformance default",
                        "--deliverable", "the gate enforces",
                        "--verification", "the suite is green")
        return a["id"]

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


class TestTheRecordIsASelection(unittest.TestCase):
    """V5 verification 1 — three measured items, one restated, two selected."""

    def setUp(self):
        self.p = Project()
        self.tid = self.p.a_task()
        self.code, self.out = self.p.close_v5(self.tid, "--checked", "1,3")
        self.assertEqual(self.code, 0, self.out)
        self.sig = self.out["signoff"]

    def test_the_two_selected_are_recorded_as_checked(self):
        checked = [i["text"] for i in self.sig["items"]
                   if i["disposition"] == "checked"]
        self.assertEqual(checked, [MEASURED[0], MEASURED[2]])

    def test_the_two_unselected_are_recorded_as_accepted_on_report(self):
        """Deliverable 4. Not dropped — that is the whole gain over free text,
        which could not distinguish the two at all."""
        rest = [i["text"] for i in self.sig["items"]
                if i["disposition"] == "accepted on report"]
        self.assertEqual(rest, [MEASURED[1], RESTATED[0]])
        self.assertEqual(len(self.sig["items"]), 4,
                         "an offered item left the record entirely")

    def test_the_labels_survive_verbatim_into_the_written_record(self):
        """Both labels, in the journal, spelled exactly as the record spells
        them. A record whose markdown says "accepted" and whose JSON says
        `accepted on report` has two answers to the question the rung asks."""
        journal = self.p.journal()
        self.assertIn("## V5 sign-off", journal)
        for label in ("checked", "accepted on report"):
            self.assertIn(f"**{label}**", journal,
                          f"the disposition label {label!r} did not survive")
        for item in self.sig["items"]:
            self.assertIn(item["text"], journal)
        self.assertIn("*(Perry verified)*", journal)
        self.assertIn("*(restated — Perry did not verify this)*", journal)

    def test_every_item_is_labelled_with_its_provenance(self):
        """Deliverable 2. Selecting a Perry-verified item means *I checked this
        too*; selecting a restated one means *I checked a claim Perry passed
        along*. The label is what keeps those from reading the same."""
        by_text = {i["text"]: i["provenance"] for i in self.sig["items"]}
        for text in MEASURED:
            self.assertEqual(by_text[text], "Perry verified")
        self.assertEqual(by_text[RESTATED[0]],
                         "restated — Perry did not verify this")

    def test_name_and_date_are_filled_in_not_typed(self):
        """Deliverable 3 — the two fields a human should never be retyping."""
        self.assertTrue(self.sig["signed_by"].strip(),
                        "an anonymous signature is not a weaker signature")
        self.assertEqual(self.sig["signed_on"], f"{date.today():%Y-%m-%d}")
        self.assertIn(self.sig["signed_by"], self.p.journal())

    def test_the_signature_rides_in_the_event_too(self):
        done = [e for e in self.p.events() if e.get("event") == "done"]
        self.assertEqual(len(done), 1)
        self.assertEqual(done[0]["signoff"]["counts"],
                         {"checked": 2, "accepted on report": 2,
                          "not looked at": 0})

    def test_the_row_still_closes_at_v5(self):
        """The sign-off is added to the close; it does not replace it."""
        self.assertEqual(self.out["rung"], "V5")
        self.assertNotIn(self.tid, (self.p.root / "BOARD.md").read_text())


class TestFreeTextIsAdditive(unittest.TestCase):
    """V5 verification 2 — recorded ALONGSIDE the selection, never instead."""

    ALSO = "I re-ran perry-conform declare --all against my own checkout."

    def test_free_text_lands_beside_the_selection(self):
        p = Project()
        tid = p.a_task()
        code, out = p.close_v5(tid, "--checked", "2", "--also", self.ALSO)
        self.assertEqual(code, 0, out)
        sig = out["signoff"]
        self.assertEqual(sig["also_checked"], self.ALSO)
        self.assertEqual(len(sig["items"]), 4,
                         "free text replaced the selection instead of joining it")
        self.assertEqual(sig["counts"]["checked"], 1)
        journal = p.journal()
        self.assertIn(self.ALSO, journal)
        self.assertIn(MEASURED[1], journal)
        self.assertIn("**accepted on report**", journal)

    def test_free_text_alone_is_a_signature(self):
        """Deliverable 5 read the other way: the user may have checked only
        something Perry never offered. That is a signature, not an empty one."""
        p = Project()
        tid = p.a_task()
        code, out = p.close_v5(tid, "--checked", "none", "--also", self.ALSO)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["signoff"]["counts"]["checked"], 0)
        self.assertEqual(out["signoff"]["also_checked"], self.ALSO)

    def test_the_free_text_is_not_run_through_the_drafting_guard(self):
        """`--also` is the USER's sentence. The guard exists to stop PERRY
        drafting a claim about a person; applying it to the user's own words
        would refuse them for describing what they did, which is the one thing
        only they may say."""
        p = Project()
        tid = p.a_task()
        code, out = p.close_v5(
            tid, "--checked", "none",
            "--also", "I reviewed the diff myself and approved it.")
        self.assertEqual(code, 0, out)
        self.assertIn("I reviewed the diff myself", p.journal())


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
        code, out = p.run("done", tid, "--evidence", "e.md", "--rung", "V5",
                          "--measured", "the user reviewed the diff",
                          "--checked", "1")
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


class TestAnEmptySignatureIsRefused(unittest.TestCase):
    """V5 verification 4 and deliverable 7."""

    def test_nothing_selected_and_no_free_text_is_refused(self):
        p = Project()
        tid = p.a_task()
        code, out = p.close_v5(tid, "--checked", "none")
        self.assertEqual(code, 1, out)
        self.assertIn("not a sign-off", json.dumps(out, ensure_ascii=False))

    def test_the_refused_close_wrote_nothing(self):
        """A refusal that half-closed the row would be worse than the blank
        signature it prevented."""
        p = Project()
        tid = p.a_task()
        p.close_v5(tid, "--checked", "none")
        self.assertIn(tid, (p.root / "BOARD.md").read_text())
        self.assertEqual([e["event"] for e in p.events()], ["add"])

    def test_pressing_return_at_the_prompt_is_what_this_costs(self):
        """`--checked` absent entirely is the same keystroke as `none`, and
        must not be the cheap path to a blank signature."""
        p = Project()
        tid = p.a_task()
        code, _ = p.close_v5(tid)
        self.assertEqual(code, 1)

    def test_an_empty_offered_item_is_refused(self):
        with self.assertRaises(PT.Refused):
            PT.signoff_options([""], [])

    def test_a_bare_close_that_never_engaged_the_path_is_unchanged(self):
        """The refusal fires when the sign-off path was ENGAGED and produced
        nothing. A close that passes no sign-off flag at all writes no
        signature rather than a blank one — rungs are advisory this release
        (DESIGN-003 § 4 decision 4) and hardening the rung itself is out of
        this row's scope."""
        p = Project()
        tid = p.a_task()
        code, out = p.run("done", tid, "--evidence", "e.md", "--rung", "V5")
        self.assertEqual(code, 0, out)
        self.assertIsNone(out["signoff"])


class TestThreeDispositionsNotTwo(unittest.TestCase):
    """The subjective question this row was dispatched with, pinned.

    **The alternative that was rejected: two categories** — `checked` and
    `accepted on report` — with nothing between "I read Perry's output and took
    its word" and "I never looked at this at all".

    It was rejected on the corpus. All three V5 signatures already in this
    repository write the third category by hand. TASK-034's carries a section
    headed *"Not checked, and recorded because V5's whole value is saying so"*
    beside what it did check. TASK-047's distinguishes *fixture opt-out 的理由已读
    并接受* — read, then accepted — from two costs taken on the strength of
    Perry's printed output. A format that cannot hold what the existing
    signatures already say is a regression against the corpus it must stay
    compatible with.

    The second reason is the drafting rule. Defaulting an unselected item to
    `accepted on report` is already the outer edge of what Perry may assert:
    it describes the SCOPE of the signature, not an act the user performed. So
    `not looked at` is never a default — it is reachable only by the user
    naming the item, which is what keeps it a user statement.
    """

    def test_not_looked_at_is_a_disposition_of_its_own(self):
        p = Project()
        tid = p.a_task()
        code, out = p.close_v5(tid, "--checked", "1", "--not-looked-at", "4")
        self.assertEqual(code, 0, out)
        by_text = {i["text"]: i["disposition"] for i in out["signoff"]["items"]}
        self.assertEqual(by_text[MEASURED[0]], "checked")
        self.assertEqual(by_text[MEASURED[1]], "accepted on report")
        self.assertEqual(by_text[RESTATED[0]], "not looked at")
        self.assertIn("**not looked at**", p.journal())

    def test_not_looked_at_is_never_a_default(self):
        p = Project()
        tid = p.a_task()
        _, out = p.close_v5(tid, "--checked", "1")
        self.assertEqual(out["signoff"]["counts"]["not looked at"], 0)

    def test_one_item_cannot_carry_two_dispositions(self):
        p = Project()
        tid = p.a_task()
        code, _ = p.close_v5(tid, "--checked", "1", "--not-looked-at", "1")
        self.assertEqual(code, 1)


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
        _, out = p.close_v5(tid, "--checked", "3")
        picked = [i["text"] for i in out["signoff"]["items"]
                  if i["disposition"] == "checked"]
        self.assertEqual(picked, [offer["options"][2]["text"]],
                         "option 3 in the prompt is not option 3 in the record")

    def test_the_offer_writes_nothing(self):
        p = Project()
        tid = p.a_task()
        before = (p.root / "BOARD.md").read_text()
        p.run("signoff-offer", tid, "--measured", MEASURED[0])
        self.assertEqual((p.root / "BOARD.md").read_text(), before)
        self.assertEqual([e["event"] for e in p.events()], ["add"])

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

    def test_the_same_selection_records_the_same_thing_from_either_spelling(self):
        """`--checked 1,3` is what the free-text host hands back; `--checked 1
        --checked 3` is what a structured host produces. One record."""
        a, b = Project(), Project()
        _, one = a.close_v5(a.a_task(), "--checked", "1,3")
        _, two = b.close_v5(b.a_task(), "--checked", "1", "--checked", "3")
        strip = lambda s: [(i["n"], i["disposition"]) for i in s["signoff"]["items"]]
        self.assertEqual(strip(one), strip(two))

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

    def test_every_v5_close_in_the_log_still_reads(self):
        """The property the count of three was standing in for."""
        events = self.v5_events()
        self.assertTrue(events, "no V5 close reads out of the log at all")
        for e in events:
            with self.subTest(tid=e["id"]):
                self.assertTrue(e.get("evidence"),
                                "a V5 close lost its evidence path")
                self.assertTrue(
                    (PERRY_HOME / "perry" / e["evidence"]).exists(),
                    f"{e['evidence']} is gone; a signature points at nothing")

    def test_a_close_predating_the_format_was_not_back_filled(self):
        """A signature must never appear on a close that did not have one.

        Which closes those are is read from the log rather than listed: an
        event with no `signoff` key predates the format by definition, and that
        stays true however many closes join it.
        """
        old = [e for e in self.v5_events() if "signoff" not in e]
        self.assertTrue(old, "the pre-format closes vanished from the log")
        state_root = PERRY_HOME / "perry"
        for e in old:
            with self.subTest(tid=e["id"]):
                text = (state_root / e["evidence"]).read_text()
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

    def test_signing_another_row_does_not_rewrite_the_one_before_it(self):
        """Verification 1, demonstrated rather than reasoned about.

        Two V5 closes in one project, in order. The first signature's block is
        compared byte-for-byte before and after the second is written — which
        is the property the old fixed set of three was a proxy for, and the
        only one of the two that survives a fourth close.
        """
        p = Project()
        first = p.a_task()
        code, _ = p.close_v5(first, "--checked", "1")
        self.assertEqual(code, 0)
        before = p.journal()
        block = before[before.index(f"**{first} — V5 sign-off"):]

        second = p.a_task()
        code, _ = p.close_v5(second, "--checked", "2", "--not-looked-at", "4")
        self.assertEqual(code, 0)
        after = p.journal()
        self.assertIn(block.rstrip(), after,
                      "the earlier signature changed when a later one landed")
        sigs = read_signatures(after)
        self.assertEqual([s["id"] for s in sigs], [first, second])
        self.assertEqual([p for s in sigs for p in unreadable(s)], [])

    def test_the_new_record_does_not_claim_to_be_the_old_one(self):
        """The old signatures are prose in an evidence file; the new one is a
        journal block plus an event. Both are readable, neither is rewritten,
        and nothing here converts one into the other."""
        p = Project()
        code, out = p.close_v5(p.a_task(), "--checked", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("signoff", out)
        self.assertNotIn("V5 sign-off", (p.root / "BOARD.md").read_text())


class TestV1toV4ClosesAreUntouched(unittest.TestCase):
    """Out of scope, asserted rather than assumed: they gain nothing here."""

    def test_a_v3_close_writes_exactly_what_it_wrote_before(self):
        p = Project()
        tid = p.a_task()
        code, out = p.run("done", tid, "--evidence", "evidence/x.md",
                          "--rung", "V3")
        self.assertEqual(code, 0, out)
        self.assertIsNone(out["signoff"])
        self.assertEqual(out["signoff_block"], "")
        journal = p.journal()
        self.assertNotIn("V5 sign-off", journal)
        self.assertNotIn("signed off:", journal)
        done = [e for e in p.events() if e["event"] == "done"][0]
        self.assertNotIn("signoff", done)


if __name__ == "__main__":
    unittest.main()
