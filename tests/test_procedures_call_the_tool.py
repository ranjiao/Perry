"""ADR-007 rule 3, as a guard: a procedure calls the tool, then writes prose.

    "The agent protocol inverts: before doing anything, call the tool to read
     or write fields. Then, from what the tool returned, GENERATE the spec and
     evidence documents."
                    — perry/decisions/ADR-007-fields-are-typed-prose-is-not.md

A procedure that says *"append a declaration to `BOARD.md`"* or
*"append the full definition to the journal"* is that rule inverted back. The field write
lands wherever the agent's markdown happened to land, the tool's event is never
appended, and the row shows up at the next standup as drift — which is the
failure ADR-006 and ADR-007 both exist to end.

**Measured before it was fixed: 19 such steps across the original 26 lane
procedure pages** — 15 in `decide/`, 4 in `work/`, 0 in `goals/`, which had
already been through TASK-042 and reads the way the rest now does. TASK-101
widens that same rule to the root router, root references and shipped pack
procedures; the target remains 0 across the complete loadable corpus.

Two of the 19 were teaching a hand edit that had had a tool path for weeks:
`plan-week`'s *"the tool has no `priority` subcommand yet"* (it has `prioritize`)
and `add-task` step 2's *"still written by hand"* (`perry-task add` renders the
whole definition block, and measured 3 blocks written the day before it learned
to and 0 after). A stale instruction is worse than a missing one — it is
followed.

## Why this walks the tree instead of naming pages

Four guards in this repository have been defeated the same way: a reviewer
planted a file the guard's hardcoded list did not name, and the guard reported
clean. So the corpus here is **derived**: the root `SKILL.md`, root
`reference/**/*.md`, every `packs/*/*.md`, and every top-level directory that
holds a `SKILL.md` beside a `reference/` directory. A lane contributes its
`SKILL.md` plus `reference/**/*.md`; lane `state/` pages remain shipped
templates rather than procedures. A fourth lane, a nested reference page, or a
new pack procedure is covered without editing a filename list here.

What IS declared here is the rule, not the corpus: which state file has a
deterministic writer, and what that writer is called. That list is closed by
`bin/` — it can only grow when someone writes a new tool — and every entry is
checked against `bin/` at import time by `test_owner_tools_exist`, so an entry
naming a tool that no longer exists is a red, not a silently dead rule.

## Two rules fire

* **R1 — a procedure step mutates a tool-owned target without naming the tool.**
  The unit is a numbered or bulleted step, or a paragraph: the shape a procedure
  is written in.
* **R2 — a sentence licenses the hand edit outright** ("is still written by
  hand", "is still a hand edit"). These are the ones that rot: both live
  instances named a gap the tool had already closed, so the page was teaching a
  hand edit as the only path months after the path existed.

## What is exempt, and why each exemption is a category

A guard that reports the cases people know are fine is a guard people switch
off. Each suppression below is a predicate over the text, not an entry on a
list of blessed lines:

1. **No writer exists → not a target at all.** `.perry/config.md` is read by
   `bin/perry-task` and written by nobody: `§ Tracks` is the user's own
   configuration, and `§ Document language` is answered at first-time setup.
   The same holds for `journal/` prose (`## Notes`), `OKR.md`'s narrative and
   version blocks, `phase/`, `design/`, `evidence/`, `weekly/` and `handoff/`.
   Rule 2 says Python never parses prose; nothing here writes it either. They
   are absent from `TARGETS` for that reason and cannot be reported.
2. **A prohibition is the rule, not a violation.** *"`design` never writes
   `BOARD.md`"* and *"Do not hand-write the row"* are the instruction this
   guard wants, phrased as a refusal.
3. **A description of what a tool or a lane does is not an order to the
   agent.** *"The tool removes the board row"* and *"PMO writes them as rows in
   `BOARD.md`"* state ownership; they do not tell a reader to open the file.
4. **A table row or a block quote is not a step.** File inventories, subcommand
   indexes and quoted user-facing briefings name outputs, and reading them as
   procedure would flag every ownership table Perry has.
5. **Adoption transcribes an authored document by hand, on purpose.** The one
   parser that survives ADR-007 § 6 answer 4 is adoption of a foreign project,
   "which is parsing by definition"; `reference/adoption.md` makes the matching
   promise on the write side — *adoption proposes, the user declares*. So a
   step under a `Migration` / `Adoption` heading may write an **authored
   document** (an ADR file) by hand. It may **not** write a **projection**
   (`BOARD.md`, `OKR.md § Commitments`, `BOARD.md`): a projection
   is rendered from the documents, so transcribing one is drift the moment the
   next tool call re-renders it.
6. **Bootstrap from a shipped template, for a file the tool cannot create.**
   `perry-task` refuses on a missing board — `no BOARD.md at <path>` — so
   `work/reference/bootstrap.md` copying `state/BOARD_TEMPLATE.md` is how the
   board comes to exist, not a hand edit of a field. This is conditioned on
   `creates_file`, not on the word "template": `perry-task add` DOES
   create `BOARD.md`, so the identical template phrasing about the
   record stays reportable.

   **The example this paragraph used to give was `DECISIONS.md`**, whose
   `perry-decide bootstrap` created it — three of the nineteen were exactly
   that phrasing. TASK-235 deleted the file, so the asymmetry needed a target
   that still has a creating writer, and `BOARD.md` is one.

Run: python3 tests/parallel test_procedures_call_the_tool
"""

from __future__ import annotations

import re
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- the corpus

def lane_dirs(root: Path = PERRY_HOME) -> list[Path]:
    """Every lane, by shape: a `SKILL.md` beside a `reference/` directory.

    Not `("work", "goals", "decide")`. The three names are what this happens to
    return today; the predicate is what makes a fourth lane covered on the day
    someone adds it.
    """
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and not d.name.startswith(".")
                  and (d / "SKILL.md").is_file() and (d / "reference").is_dir())


def procedure_pages(root: Path = PERRY_HOME) -> list[Path]:
    """Every loadable procedure page, derived from the repository shape.

    `rglob`, not `glob`, for reference trees: a page filed one directory deeper
    remains procedure. Packs have one declared shape, `packs/*/*.md`; files
    elsewhere under `packs/` are not silently promoted into agent procedure.
    """
    pages: list[Path] = []
    if (root / "SKILL.md").is_file():
        pages.append(root / "SKILL.md")
    if (root / "reference").is_dir():
        pages.extend(sorted((root / "reference").rglob("*.md")))
    for lane in lane_dirs(root):
        pages.append(lane / "SKILL.md")
        pages.extend(sorted((lane / "reference").rglob("*.md")))
    if (root / "packs").is_dir():
        pages.extend(sorted((root / "packs").glob("*/*.md")))
    return sorted(set(pages))


# ---------------------------------------------------------------- the rule

#: A state file with a deterministic writer, the tool that owns it, and whether
#: it is a PROJECTION (rendered from something else, so never transcribed) or an
#: authored DOCUMENT. Absent from this table = no `bin/perry-*` writes it, and
#: this guard has nothing to say about it. See exemption 1 in the docstring.
#:
#: `cell` is the same target named the way a sentence names it in passing —
#: "an existing row", "the `Status:` header". R2 reads one sentence rather than
#: a whole step, so it needs the looser form; R1 reads the step, where the
#: looser form would match half the prose in these pages.
TARGETS = {
    "BOARD.md row": dict(
        pattern=r"BOARD\.md|\bBOARD row\b|\bboard row\b",
        cell=r"BOARD\.md|\bboard row\b|\b(?:an? |the |each |existing )?"
             r"(?:existing )?row\b|\brow's\b",
        # `perry-task` refuses on a missing board — "no BOARD.md at <path>" —
        # so instantiating it from `state/BOARD_TEMPLATE.md` at bootstrap is the
        # only way the file comes to exist. See `creates_file` below.
        tool="perry-task", kind="projection", creates_file=False,
        template=r"\b(?:from|copy(?:ing)?|instantiate[sd]?)\b"
                 r"[^.]{0,80}\bBOARD_TEMPLATE\.md\b"),
    # The journal's two TOOL-WRITTEN sections, named exactly. `## Notes` is
    # absent on purpose (exemption 1: nothing writes it), and so is the ADR
    # body's `## Status change` — singular, a different file, a different lane,
    # and prose that `perry-decide` deliberately leaves alone.
    "the journal's status / definition block": dict(
        pattern=r"##\s*Status changes\b|##\s*New tasks added\b"
                r"|journal(?:'s)? status[- ]change|status[- ]change (?:journal )?line",
        cell=r"status[- ]change|definition block|New tasks added",
        tool="perry-task", kind="projection"),
    "an ADR's typed header": dict(
        # `ADR-NNN-<slug>` / `ADR-NNN-*.md` — the FILE. Bare `ADR-NNN` is left
        # out: it is how these pages name a decision in passing ("`ADR-NNN`
        # recorded"), and reading that as a file write reports the sentence
        # that hands the write off.
        pattern=r"ADR file|ADR-NNN-[<*]|target ADR|`Status:`",
        tool="perry-decide", kind="document"),
    "OKR.md § Commitments": dict(
        pattern=r"##\s*Commitments|OKR\.md\s*§\s*Commitments",
        tool="perry-goals", kind="projection"),
    # TASK-119. Declared the day `bin/perry-goals link` existed and not before:
    # until then `phase/<NNN>-linkage.md` had no writer, so every procedure
    # that appends an edge was an unavoidable hand edit rather than an
    # instruction that had gone stale (exemption 1 below). The pattern is the
    # file and the three lists that ARE the graph — a bare mention of
    # "linkage" is how these pages name the concept in passing.
    "phase/<NNN>-linkage.md": dict(
        pattern=r"-linkage\.md|linkage graph|linkage registry|`tasks\[\]`"
                r"|`unlinked\[\]`|`aliases\[\]`|`projects\[\]`",
        # Exemption 6 applies for the same reason it applies to `BOARD.md`:
        # `perry-goals link` REFUSES on a missing register ("no linkage
        # register at <path>"), so instantiating it from
        # `state/linkage_TEMPLATE.md` at `plan-phase` is the only way the file
        # comes to exist. Every write afterwards is the tool's.
        tool="perry-goals", kind="projection", creates_file=False,
        template=r"\b(?:from|copy(?:ing)?|instantiate[sd]?)\b"
                 r"[^.]{0,80}\blinkage_TEMPLATE\.md\b"),
    "knowledge/INDEX.md": dict(
        # `perry-knowledge` owns only the card catalog. Digest registration and
        # archive metadata share this file but remain authored by the digest
        # flow, so a bare index reference is deliberately not a target.
        pattern=r"(?:##\s*Cards by topic[^.]{0,80}knowledge/INDEX\.md"
                r"|knowledge/INDEX\.md[^.]{0,80}##\s*Cards by topic)",
        tool="perry-knowledge", kind="projection"),
}

def owner_pattern(tool: str) -> str:
    """Naming the owning tool discharges the step.

    A hyphenated subcommand in backticks (`risk-add`, `cadence-done`) counts as
    naming it: those names belong to one tool and to no English sentence. The
    bare ones (`add`, `status`, `done`, `next`) do not, which is why the second
    alternative requires a hyphen — otherwise every sentence containing the
    word "add" would discharge itself.
    """
    lanes = {
        "perry-task": r"`?(?:/perry\s+(?:work|pmo)|/pmo)\b",
        "perry-goals": r"`?(?:/perry\s+(?:goals|okr)|/okr)\b",
        "perry-decide": r"`?(?:/perry\s+(?:decide|design)|/design)\b",
    }
    lane = f"|{lanes[tool]}" if tool in lanes else ""
    return (rf"{tool}{lane}|`[a-z]+-[a-z-]+`\s*"
            rf"(?:mints|writes|records|creates|refuses)")


WRITE = (r"\b(?:re-?writes?|re-?write|writes?|write|adds?|add|added"
         r"|appends?|append|appended|updates?|update|updated|edits?|edit|edited"
         r"|inserts?|insert|inserted|creates?|create|flips?|flip|flipped"
         r"|records?|record|fills?|fill|marks?|mark|ticks?|tick"
         r"|removes?|remove|deletes?|delete|bumps?|bump|sets?|stamps?|stamp"
         r"|mints?|mint|increments?|increment|moves?|move|puts?|put"
         r"|populate[sd]?)\b")

#: A step that READS a state file is not editing it, and most of these pages
#: open with one. "Reads `BOARD.md` + last week's `weekly/…`. … Append to the
#: week's file" mentions a target and a write and does neither to the other.
READ = (r"\b(?:reads?|reading|scans?|scanning|opens?|opening|consults?|greps?"
        r"|detects?|detecting"
        r"|cross-checks?|checks?|walks?|surfaces?|from|in|against|per|of)"
        r"\s+[`'\"*(\[]*$")

# `Detect A / B / C` is one read instruction. For the second and later target,
# the verb is not immediately adjacent, so the ordinary READ anchor cannot see
# it. Keep this bounded to slash/comma inventories; "detect a problem, then
# update BOARD.md" remains a write.
DETECTION_LIST = re.compile(
    r"\b(?:detects?|detecting)\b(?:`[^`]*`|[^.!?;:]){0,80}"
    r"(?:/|,\s*(?:and\s+)?)"
    r"\s*[`'\"*(\[]*$", re.I)

#: How close a write verb has to sit to the target to be a write TO it. Wide
#: enough for "Update `BOARD.md` (move the row to the new shape
#: version)", narrow enough that a read at the head of a step and a write to
#: some other file two sentences later are not read as one instruction.
BEFORE, AFTER = 60, 90


def writes_to(flat: str, pattern: str) -> bool:
    """Does this unit write the thing `pattern` names, as opposed to read it?"""
    for m in re.finditer(pattern, flat):
        lead = flat[max(0, m.start() - BEFORE):m.start()]
        if re.search(READ, lead, re.I) or DETECTION_LIST.search(lead):
            continue
        near = (flat[max(0, m.start() - BEFORE):m.start()]
                + " " + flat[m.end():m.end() + AFTER])
        if re.search(WRITE, near, re.I):
            return True
    return False


#: Exemption 2 — the step refuses the write rather than ordering it.
PROHIBITION = re.compile(
    r"\bnever\b|\bnot\b|\bno\b|\bdon'?t\b|\brefuses?\b|\brefused\b"
    r"|\brather than\b|\binstead of\b|\bleft alone\b|\bmust not\b", re.I)

#: Exemption 3 — the subject of the verb is a tool or a lane, so the sentence
#: describes a write rather than commanding one.
DESCRIPTIVE = re.compile(
    r"(?:`?(?:bin/)?perry-\w+`?|\bthe tool\b|\bPMO\b|\bOKR\b|\bwork\b|\bgoals\b"
    r"|\bdecide\b|\bdesign\b|\bit\b|\bwhich\b|\bthat\b)`?\s+"
    r"(?:already |also |still |then |never |only |gets? )?" + WRITE
    + r"|^\**(?:writes|adds|appends|updates|edits|inserts|creates|flips|records"
      r"|fills|marks|ticks|removes|deletes|bumps|sets|stamps|mints|increments"
      r"|moves|puts|populates)\b"
    + r"|^\**(?:changing|creating)\b.{0,180}?" + WRITE
    + r"|(?:`?(?:BOARD\.md|DECISIONS\.md|OKR\.md)`?|\bthe row\b|\bthe index\b)"
      r"\s+(?:is|are)\s+(?:\w+\s+){0,4}"
      r"(?:rendered|written|appended|reported|created|updated)", re.I)


def target_is_subject(sentence: str, pattern: str) -> bool:
    """The target changes; the procedure is not ordering the reader to change it.

    Markdown closers and a paired path may sit between the target and its verb,
    as in ``OKR.md` + `phase/` move``. A comma is intentionally not accepted:
    "For the BOARD row, update Status" remains an instruction.
    """
    for match in re.finditer(pattern, sentence, re.I):
        tail = re.sub(r"^[`*_]+", "", sentence[match.end():]).lstrip()
        paired = r"(?:\+\s+`[^`]+`\s+)?"
        if re.match(paired + WRITE, tail, re.I):
            return True
        if re.match(r"is\s+explicitly\b", tail, re.I):
            return True
    return False

#: R2 — a copula asserting the hand path is how it is done *now*. Not "a
#: hand-written row is reported as `unrecorded`", which describes the detector.
HAND_LICENCE = re.compile(
    r"\b(?:is|are|remains?|stays?)\s+(?:\w+\s+){0,3}"
    r"(?:a hand[- ]edit\b|written by hand\b|edited by hand\b|written directly\b"
    r"|typed by hand\b|maintained by hand\b)", re.I)

#: The R2 form of exemption 2. The whole-step `PROHIBITION` is too broad for one
#: sentence: the live instance of R2 reads "…the tool has **no** `priority`
#: subcommand yet", where the negation is about the tool and the licence stands.
#: So the refusal has to attach to the hand edit itself.
NOT_BY_HAND = re.compile(
    r"\b(?:not|never)\s+(?:\w+\s+){0,3}"
    r"(?:written|edited|typed|maintained|a hand)", re.I)

#: Exemption 5 — the heading says this is adoption of something that already
#: exists. Scoped to authored documents; a projection is never transcribed.
#:
#: **`import` is bounded and the other four are not, and that asymmetry is the
#: whole comment.** The bare stem matched `## Hand-off contract with PMO (the
#: most **import**ant rule)` in `decide/SKILL.md`, which is not an adoption
#: section — so every step under it stopped being reportable for authored
#: documents, and a planted `Edit the target ADR yourself: flip its Status:
#: header` sat there silent while the identical plant four lines lower, under
#: `## Style rules`, went red. One of the two headings this pattern matched on
#: the live tree was a false match. Found by a V4 probing the exemption set
#: rather than the assertion, which sits at 0 and looks the same either way.
#:
#: `migrat` / `adopt` are left unbounded because their continuations are all in
#: the same family (migrate, migration, adopting, adoption) — there is no
#: English word that contains them and means something else. `import` is the
#: one stem here with a common unrelated descendant.
ADOPTION_HEADING = re.compile(
    r"migrat|adopt|legacy|pre-existing|\bimport(?:s|ed|ing)?\b", re.I)

#: Exemption 6 — instantiating a file from its shipped template is bootstrap,
#: not a field write, and it is exempt only where the owning tool cannot create
#: that file (`creates_file=False`). `perry-task` refuses on a missing
#: `BOARD.md`, so `work/reference/bootstrap.md` copying `BOARD_TEMPLATE.md` is
#: how the board comes to exist at all. `perry-task add` DOES create
#: `BOARD.md`, so the same phrasing about that record stays
#: reportable — the asymmetry that caught three of the nineteen, restated on a
#: target that still exists after TASK-235.
def from_target_template(flat: str, spec: dict) -> bool:
    """The step names template provenance for this target, not any template."""
    return bool(re.search(spec["template"], flat, re.I))


@dataclass(frozen=True)
class Suppression:
    """One target the guard deliberately stopped evaluating."""

    page: Path
    line: int
    section: str
    exemption: str
    target: str
    step: str


def blocks(text: str):
    """Markdown blocks outside fenced code, each with its first line number.

    Fences are dropped whole: a code block is a command to run, not a step, and
    the commands in these pages are exactly the tool invocations this guard is
    asking for.
    """
    out, cur, start, in_fence = [], [], 0, False
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.strip():
            if not cur:
                start = i
            cur.append(line)
        elif cur:
            out.append((start, "\n".join(cur)))
            cur = []
    if cur:
        out.append((start, "\n".join(cur)))
    return out


def steps(block: str):
    """A block's numbered / bulleted items, or the block itself if it has none."""
    lines = block.split("\n")
    marks = [i for i, l in enumerate(lines) if re.match(r"^\s*(?:\d+\.|[-*])\s", l)]
    if not marks:
        return [(0, block)]
    out = []
    if marks[0]:
        out.append((0, "\n".join(lines[:marks[0]])))
    for a, b in zip(marks, marks[1:] + [len(lines)]):
        out.append((a, "\n".join(lines[a:b])))
    return out


def sentences(unit: str):
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+", unit) if s.strip()]


def scan(
        page: Path,
        suppressions: list[Suppression] | None = None,
) -> list[tuple[int, str, str, str]]:
    """Every hand-edit instruction, optionally exposing each suppression."""
    text = page.read_text()
    section = ""
    found = []

    def suppress(line: int, exemption: str, target: str, step: str) -> None:
        if suppressions is not None:
            suppressions.append(Suppression(
                page=page,
                line=line,
                section=section,
                exemption=exemption,
                target=target,
                step=step,
            ))

    for bstart, block in blocks(text):
        lines = block.split("\n")
        # A heading and the prose under it are one block when no blank line
        # separates them — which is how half these pages are written. Peel the
        # heading off and keep the prose; skipping the block dropped the
        # procedure with it.
        while lines and lines[0].lstrip().startswith("#"):
            section = lines[0]
            lines.pop(0)
            bstart += 1
        # Exemption 4 — a table row or a block quote is not a procedure step.
        # Expose target-bearing exclusions through the same suppression stream
        # as the semantic exemptions below; otherwise this branch can widen
        # without a test being able to observe what disappeared.
        kept = []
        for line_offset, markdown_line in enumerate(lines):
            if not markdown_line.lstrip().startswith(("|", ">")):
                kept.append(markdown_line)
                continue
            flat_line = " ".join(markdown_line.split())
            for name, spec in TARGETS.items():
                if (re.search(spec["pattern"], flat_line)
                        and (writes_to(flat_line, spec["pattern"])
                             or HAND_LICENCE.search(flat_line))):
                    suppress(bstart + line_offset, "quoted-or-table", name,
                             flat_line)
        lines = kept
        if not lines:
            continue
        block = "\n".join(lines)
        adoption = bool(ADOPTION_HEADING.search(section))
        for offset, step in steps(block):
            flat = " ".join(step.split())
            units = sentences(flat)
            for name, spec in TARGETS.items():
                if not re.search(spec["pattern"], flat):
                    continue
                line = bstart + offset
                # Exemption 5 is section-scoped and records one suppressed
                # target per procedure step, regardless of sentence wrapping.
                if adoption and spec["kind"] == "document":
                    suppress(line, "adoption-document", name, flat)
                    continue

                # R2 first, and it is NOT discharged by naming the tool. A step
                # that runs the tool for one field and then says the next one is
                # "still written by hand" is the exact shape both live instances
                # had: the tool named, the hand edit licensed one clause later.
                hit = None
                for sentence in units:
                    if (HAND_LICENCE.search(sentence)
                            and re.search(spec.get("cell", spec["pattern"]),
                                          sentence)):
                        if NOT_BY_HAND.search(sentence):
                            suppress(line, "r2-refusal", name, sentence)
                            continue
                        hit = (line, name, "R2", sentence)
                        break
                if hit:
                    found.append(hit)
                    continue

                # R1 exemptions are local to the sentence containing the
                # target. A refusal, template, or tool call for one target may
                # not discharge a hand edit in the next sentence.
                for sentence in units:
                    if not re.search(spec["pattern"], sentence):
                        continue
                    # Exemption 6 — bootstrap from this target's shipped
                    # template, only where its writer cannot create the file.
                    if (not spec.get("creates_file", True)
                            and from_target_template(sentence, spec)):
                        suppress(line, "target-template", name, sentence)
                        continue
                    if re.search(owner_pattern(spec["tool"]), sentence):
                        suppress(line, "owner-call", name, sentence)
                        continue
                    if not writes_to(sentence, spec["pattern"]):
                        continue
                    if PROHIBITION.search(sentence):
                        suppress(line, "prohibition", name, sentence)
                        continue
                    if (DESCRIPTIVE.search(sentence)
                            or target_is_subject(sentence, spec["pattern"])):
                        suppress(line, "descriptive", name, sentence)
                        continue
                    found.append((line, name, "R1", sentence))
    return found


class ProceduresCallTheTool(unittest.TestCase):
    """ADR-007 rule 3 over every loadable procedure, target 0 (`P002-O3-KR1`)."""

    def scan_text(self, text: str, name: str = "page.md"):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / name
            page.write_text(text)
            suppressed: list[Suppression] = []
            findings = scan(page, suppressed)
            return findings, suppressed

    def test_corpus_is_walked_not_listed(self):
        """The corpus is derived, and it is not empty or accidentally tiny.

        A guard that silently scans nothing passes forever. This asserts the
        walk found lanes, that each contributed its `SKILL.md`, and that the
        `reference/` trees are in there too.
        """
        lanes = lane_dirs()
        self.assertGreaterEqual(len(lanes), 3, "no lanes found — the walk broke")
        pages = procedure_pages()
        self.assertIn(PERRY_HOME / "SKILL.md", pages)
        self.assertTrue(
            set((PERRY_HOME / "reference").rglob("*.md")) <= set(pages),
            "root reference pages were dropped")
        self.assertTrue(
            set((PERRY_HOME / "packs").glob("*/*.md")) <= set(pages),
            "pack procedure pages were dropped")
        for lane in lanes:
            self.assertIn(lane / "SKILL.md", pages)
            self.assertTrue(set((lane / "reference").rglob("*.md")) <= set(pages),
                            f"nested reference pages dropped for {lane.name}")
            self.assertFalse(any(lane / "state" in p.parents for p in pages),
                             f"{lane.name}/state is not a procedure corpus")
        refs = [p for p in pages if "reference" in p.parts]
        self.assertGreater(len(refs), 10,
                           "the reference trees were not walked")

    def test_root_router_reference_and_pack_shapes_are_each_load_bearing(self):
        """The TASK-101 expansion is derived, not a second filename list."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reference" / "deep").mkdir(parents=True)
            (root / "packs" / "ops").mkdir(parents=True)
            (root / "packs" / "TOO_SHALLOW.md").write_text(
                "1. Add a row to `BOARD.md` by hand.\n")
            (root / "packs" / "ops" / "nested").mkdir()
            (root / "packs" / "ops" / "nested" / "TOO_DEEP.md").write_text(
                "1. Add a row to `BOARD.md` by hand.\n")
            planted = {
                root / "SKILL.md":
                    "1. Add a row to `BOARD.md` by hand.\n",
                root / "reference" / "deep" / "page.md":
                    "1. Update `BOARD.md` by hand.\n",
                root / "packs" / "ops" / "incidents.md":
                    "1. Append the `## Status changes` line by hand.\n",
            }
            for page, text in planted.items():
                page.write_text(text)

            pages = procedure_pages(root)
            self.assertEqual(set(pages), set(planted),
                             "only the three declared root/pack shapes belong")
            for page in planted:
                self.assertTrue(scan(page), f"{page.relative_to(root)} not scanned")

    def test_a_planted_lane_and_a_planted_page_are_both_caught(self):
        """The anti-defeat property, exercised rather than asserted.

        Four guards in this repository were beaten by a file their hardcoded
        list did not name. A guard that walks the tree is only *claimed* to be
        immune until something is planted in it, so: build a lane that did not
        exist, put a nested page under it, and check that both are walked and
        both report. `test_no_procedure_hand_edits_a_tool_owned_file` sits at
        zero, so without this the whole module would pass with the scanner
        broken.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lane = root / "reckon"
            (lane / "reference" / "deep").mkdir(parents=True)
            (lane / "state").mkdir()
            (lane / "SKILL.md").write_text(
                "# reckon\n\n## Procedure\n\n"
                "1. Update `BOARD.md`: add a row for the file.\n")
            (lane / "reference" / "deep" / "buried.md").write_text(
                "# buried\n\n## Procedure\n\n"
                "1. Append the row to `BOARD.md` and write the "
                "`## Status changes` line yourself.\n")
            # Two pages that legitimately hand-edit, so the exemptions are
            # exercised on the same walk rather than only described above.
            (lane / "reference" / "config.md").write_text(
                "# config\n\n"
                "1. Edit `.perry/config.md` § Tracks yourself — declare the "
                "track's SLA and its default rung.\n")
            (lane / "reference" / "bootstrap.md").write_text(
                "# bootstrap\n\n"
                "1. Write `BOARD.md` from `state/BOARD_TEMPLATE.md`, empty "
                "tables.\n"
                "2. Write `BOARD.md` from "
                "`state/conformance_TEMPLATE.md`, empty record.\n")
            (lane / "state" / "SHIPPED.md").write_text(
                "1. Update `BOARD.md`: add a row by hand.\n")

            only_skill = root / "only-skill"
            only_skill.mkdir()
            (only_skill / "SKILL.md").write_text("# not a lane\n")
            only_reference = root / "only-reference" / "reference"
            only_reference.mkdir(parents=True)
            (only_reference / "page.md").write_text("# not a lane\n")

            pages = procedure_pages(root)
            self.assertEqual(lane_dirs(root), [lane],
                             "both halves of the lane shape are required")
            self.assertIn(lane / "SKILL.md", pages)
            self.assertIn(lane / "reference" / "deep" / "buried.md", pages)
            self.assertNotIn(lane / "state" / "SHIPPED.md", pages)

            reported = {p.name: scan(p) for p in pages}
            self.assertEqual(len(reported["SKILL.md"]), 1,
                             "the lane entry-point plant must stay red")
            self.assertEqual(len(reported["buried.md"]), 2,
                             "both nested-page plants must stay red")
            self.assertEqual(reported["config.md"], [],
                             "`.perry/config.md` is the user's own file — "
                             "reporting it is how a guard gets switched off")

            # Exemption 6 cuts one way and not the other, on one page: nothing
            # creates `BOARD.md`, `perry-task add` creates the record.
            boot = reported["bootstrap.md"]
            self.assertEqual([f[1] for f in boot], ["BOARD.md row"],
                             "the template exemption is conditioned on whether "
                             "the owning tool can create the file, not on the "
                             f"word 'template'; got {boot}")

    def test_adoption_suppressions_are_observed_from_scan(self):
        """Pin what `scan()` suppressed, not raw headings a regex matched."""
        suppressed: list[Suppression] = []
        for page in procedure_pages():
            scan(page, suppressed)
        adoption = [s for s in suppressed
                    if s.exemption == "adoption-document"]
        self.assertEqual(len(adoption), 1, adoption)
        item = adoption[0]
        self.assertEqual(
            (str(item.page.relative_to(PERRY_HOME)), item.line, item.section,
             item.target),
            ("decide/reference/decisions.md", 292,
             "## Migration: old monolithic `DECISIONS.md`",
             "an ADR's typed header"),
            "the signed-off set is the suppressions scan actually performed")
        self.assertTrue(item.step.startswith(
            "3. Write each to `decisions/ADR-NNN-<slug>.md`"), item.step)

    def test_adoption_scope_ends_at_the_next_real_heading(self):
        """A fenced heading is invisible and adoption cannot leak afterward."""
        findings, suppressed = self.scan_text(
            "# page\n\n"
            "## Import existing decisions\n\n"
            "1. Edit the target ADR: flip its `Status:` header.\n\n"
            "```md\n## Import example inside a fence\n```\n\n"
            "## Style rules\n\n"
            "1. Edit the target ADR: flip its `Status:` header.\n")
        self.assertEqual([(f[1], f[2]) for f in findings],
                         [("an ADR's typed header", "R1")])
        adoption = [s for s in suppressed
                    if s.exemption == "adoption-document"]
        self.assertEqual(len(adoption), 1, adoption)
        self.assertEqual(adoption[0].section, "## Import existing decisions")
        self.assertEqual(adoption[0].target, "an ADR's typed header")

    def test_stacked_headings_preserve_suppression_location_and_scope(self):
        """Contiguous headings are all peeled and advance the source line."""
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "stacked.md"
            page.write_text(
                "# page\n"
                "## Import existing decisions\n"
                "1. Edit the target ADR: flip its `Status:` header.\n")
            suppressed: list[Suppression] = []
            self.assertEqual(scan(page, suppressed), [])
            self.assertEqual(
                suppressed,
                [Suppression(
                    page=page,
                    line=3,
                    section="## Import existing decisions",
                    exemption="adoption-document",
                    target="an ADR's typed header",
                    step="1. Edit the target ADR: flip its `Status:` header.",
                )],
                "each stacked heading advances the line and the last heading "
                "owns the procedure step")

    def test_each_adoption_vocabulary_branch_is_load_bearing(self):
        """Dropping any justified adoption form exposes a document write."""
        headings = [
            "## Migration procedure",
            "## Adoption procedure",
            "## Legacy conversion",
            "## Pre-existing decisions",
            "## Import existing decisions",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                findings, suppressed = self.scan_text(
                    f"# page\n\n{heading}\n\n"
                    "1. Edit the target ADR: flip its `Status:` header.\n")
                self.assertEqual(findings, [])
                self.assertEqual(
                    [(s.exemption, s.section, s.target) for s in suppressed],
                    [("adoption-document", heading,
                      "an ADR's typed header")])

    def test_adoption_exempts_a_document_and_never_a_projection(self):
        """The document/projection split, exercised on both sides.

        The row calls this the subtlest of the six exemptions and the docstring
        argues it at length: adoption may transcribe an **authored document**,
        because that is what adoption is, but never a **projection**, because a
        projection is re-rendered from the documents and a transcribed one is
        drift by the next tool call.

        Both halves were argued and neither was tested. Replacing the
        `kind == "document"` condition with `True` — which is exactly the
        mistake the paragraph exists to prevent — left the module green.
        """
        step = ("1. Edit the target ADR yourself: flip its `Status:` header "
                "to `active`.\n"
                "2. Add the matching row to `BOARD.md` by hand.\n")
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "migrate.md"

            page.write_text("# m\n\n## Migration from a legacy board\n\n" + step)
            under = scan(page)
            self.assertEqual([f[1] for f in under], ["BOARD.md row"],
                             "under an adoption heading the ADR file is the "
                             "authored document adoption exists to transcribe, "
                             "and the record is the projection it may never "
                             f"write; got {under}")

            page.write_text("# m\n\n## Style rules\n\n" + step)
            outside = scan(page)
            self.assertEqual(
                sorted(f[1] for f in outside),
                ["BOARD.md row", "an ADR's typed header"],
                "outside an adoption heading both are reportable — if the "
                "document half is silent here, the exemption is not scoped to "
                f"the heading at all; got {outside}")

    def test_template_exemption_is_bound_to_the_target_template(self):
        findings, suppressed = self.scan_text(
            "# bootstrap\n\n## Procedure\n\n"
            "1. Write `BOARD.md` from `state/BOARD_TEMPLATE.md`.\n"
            "2. Write `BOARD.md` from `state/linkage_TEMPLATE.md`.\n")
        self.assertEqual([(f[0], f[1], f[2]) for f in findings],
                         [(6, "BOARD.md row", "R1")])
        templates = [s for s in suppressed
                     if s.exemption == "target-template"]
        self.assertEqual(len(templates), 1, templates)
        self.assertEqual((templates[0].line, templates[0].target),
                         (5, "BOARD.md row"))
        self.assertIn("BOARD_TEMPLATE.md", templates[0].step)

        findings, _ = self.scan_text(
            "# bootstrap\n\n## Procedure\n\n"
            "1. Read `state/BOARD_TEMPLATE.md` for context. Then write a row "
            "to `BOARD.md` by hand.\n")
        self.assertEqual([(f[1], f[2]) for f in findings],
                         [("BOARD.md row", "R1")],
                         "mentioning the right template is not provenance")

    def test_exemptions_are_local_to_the_target_sentence(self):
        cases = [
            ("1. Do not edit `BOARD.md`. Append the `## Status changes` line "
             "by hand.\n", "the journal's status / definition block"),
            ("1. Do not edit `BOARD.md`; append the `## Status changes` line "
             "by hand.\n", "the journal's status / definition block"),
            ("1. The tool updates `BOARD.md`. Append the "
             "`## Status changes` line by hand.\n",
             "the journal's status / definition block"),
            ("1. Run `perry-task add` to write `BOARD.md`. Append the "
             "`## Status changes` line by hand.\n",
             "the journal's status / definition block"),
            ("1. Write `BOARD.md` from `state/BOARD_TEMPLATE.md`. Then add "
             "another row to `BOARD.md` by hand.\n", "BOARD.md row"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                findings, _ = self.scan_text(
                    "# page\n\n## Procedure\n\n" + text)
                self.assertIn((expected, "R1"),
                              [(f[1], f[2]) for f in findings])

    def test_every_declared_target_has_positive_and_negative_behavior(self):
        cases = {
            "BOARD.md row": (
                "1. Add a row to `BOARD.md`.\n",
                "1. `perry-task add` writes the row to `BOARD.md`.\n"),
            "the journal's status / definition block": (
                "1. Append the `## Status changes` line to the journal.\n",
                "1. `perry-task status` records the `## Status changes` line.\n"),
            "an ADR's typed header": (
                "1. Flip the target ADR's `Status:` header.\n",
                "1. `perry-decide status` flips the target ADR's `Status:`.\n"),
            "OKR.md § Commitments": (
                "1. Insert a row into `OKR.md § Commitments`.\n",
                "1. `perry-goals commit` writes `OKR.md § Commitments`.\n"),
            "knowledge/INDEX.md": (
                "1. Update `## Cards by topic` in `knowledge/INDEX.md` by hand.\n",
                "1. `perry-knowledge promote` writes `## Cards by topic` in "
                "`knowledge/INDEX.md`.\n"),
            "phase/<NNN>-linkage.md": (
                "1. Append the task id to its KR's `tasks[]` in "
                "`phase/<NNN>-linkage.md`.\n",
                "1. `perry-goals link` appends the task id to its KR's "
                "`tasks[]`.\n"),
        }
        self.assertEqual(set(TARGETS), set(cases),
                         "a declared rule without both fixtures is unreviewed")
        for target, (positive, negative) in cases.items():
            with self.subTest(target=target, branch="positive"):
                findings, _ = self.scan_text(
                    "# page\n\n## Procedure\n\n" + positive)
                self.assertEqual([(f[1], f[2]) for f in findings],
                                 [(target, "R1")])
            with self.subTest(target=target, branch="negative"):
                findings, suppressed = self.scan_text(
                    "# page\n\n## Procedure\n\n" + negative)
                self.assertEqual(findings, [])
                self.assertIn(
                    ("owner-call", target),
                    [(s.exemption, s.target) for s in suppressed])

    def test_r2_cell_and_multiple_targets_are_independent(self):
        findings, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. Read `BOARD.md` first. The existing row is still written by "
            "hand. Append the `## Status changes` line yourself.\n")
        self.assertEqual(
            [(f[1], f[2]) for f in findings],
            [("BOARD.md row", "R2"),
             ("the journal's status / definition block", "R1")],
            "R2 uses the cell form, then scanning continues to later targets")

        findings, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. The existing row is still written by hand.\n")
        self.assertEqual(findings, [],
                         "the broad cell form cannot create an R1 target")

    def test_paragraph_steps_lists_and_leading_prose_are_all_scanned(self):
        paragraph, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "Update `BOARD.md` by hand.\n")
        self.assertEqual([(f[1], f[2]) for f in paragraph],
                         [("BOARD.md row", "R1")])

        split_from_tool, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. Run `perry-task list` to inspect the project\n"
            "2. Add a row to `BOARD.md` by hand\n")
        self.assertEqual([(f[1], f[2]) for f in split_from_tool],
                         [("BOARD.md row", "R1")])

        split_from_refusal, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. Do not edit `BOARD.md`\n"
            "2. Add a row to `BOARD.md` by hand\n")
        self.assertEqual([(f[1], f[2]) for f in split_from_refusal],
                         [("BOARD.md row", "R1")])

        leading, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "Update `BOARD.md` by hand.\n"
            "1. Run `perry-task list` afterward.\n")
        self.assertEqual([(f[1], f[2]) for f in leading],
                         [("BOARD.md row", "R1")])


    def test_bulleted_steps_keep_exemptions_inside_their_item(self):
        """Both Markdown bullet forms segment steps just like numbered items."""
        findings, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "- Do not edit `BOARD.md`\n"
            "* Add a row to `BOARD.md` by hand\n")
        self.assertEqual([(f[1], f[2]) for f in findings],
                         [("BOARD.md row", "R1")],
                         "a refusal in one bullet cannot exempt the next")

    def test_owner_boundary_and_both_proximity_directions(self):
        bare, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. `add` writes a row to `BOARD.md`.\n")
        self.assertEqual([(f[1], f[2]) for f in bare],
                         [("BOARD.md row", "R1")])

        hyphenated, suppressed = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. `task-add` writes a row to `BOARD.md`.\n")
        self.assertEqual(hyphenated, [])
        self.assertIn(("owner-call", "BOARD.md row"),
                      [(s.exemption, s.target) for s in suppressed])

        backward, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. Update the owner and status in the `BOARD.md` row.\n")
        forward, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. For the `BOARD.md` row, after checking its id and owner, "
            "update the Status cell.\n")
        self.assertEqual([f[1] for f in backward], ["BOARD.md row"])
        self.assertEqual([f[1] for f in forward], ["BOARD.md row"])

        distant, _ = self.scan_text(
            "# page\n\n## Procedure\n\n1. For the `BOARD.md` row, "
            + ("context " * 20) + "update the weekly narrative.\n")
        self.assertEqual(distant, [],
                         "a distant write to another output is not a row edit")

    def test_lane_commands_only_discharge_their_own_writer(self):
        cases = [
            ("/perry work", "BOARD.md", []),
            ("/perry goals", "OKR.md § Commitments", []),
            ("/perry decide", "the target ADR file", []),
        ]
        for command, target, expected in cases:
            with self.subTest(command=command, target=target):
                findings, suppressed = self.scan_text(
                    "# page\n\n## Procedure\n\n"
                    f"1. `{command}` then writes {target}.\n")
                self.assertEqual([(f[1], f[2]) for f in findings], expected)
                if not expected:
                    self.assertTrue(any(s.exemption == "owner-call"
                                        for s in suppressed), suppressed)
        self.assertIsNone(re.search(owner_pattern("perry-task"),
                                    "`/perry goals`"))
        self.assertIsNone(re.search(owner_pattern("perry-goals"),
                                    "`/perry work`"))

    def test_expanded_corpus_false_positive_boundaries_are_precise(self):
        """Four TASK-101 exemptions suppress descriptions, not instructions."""
        allowed = [
            ("1. `pmo` still writes `BOARD.md`.\n", True),
            ("1. Detect `OKR.md` / code / `BOARD.md` to pre-fill "
             "a draft.\n", False),
            ("1. The BOARD row flips to `review` after verification.\n", True),
            ("1. `BOARD.md` + `journal/` move to `work`.\n", True),
            ("1. **`OKR.md § Commitments` is explicitly `goals`.** Tracks put "
             "their spine there.\n", True),
            ("1. A reason that gets appended under `## Status changes` is "
             "auditable.\n", True),
        ]
        for text, observable in allowed:
            with self.subTest(text=text):
                findings, suppressed = self.scan_text(
                    "# page\n\n## Procedure\n\n" + text)
                self.assertEqual(findings, [])
                if observable:
                    self.assertTrue(suppressed,
                                    "semantic exemptions must be observable")

        refused = [
            "1. Detect the problem, then update `BOARD.md`.\n",
            "1. Detect `OKR.md` / code. Then update `BOARD.md`.\n",
            "1. For the BOARD row, after checking its id, update Status.\n",
        ]
        for text in refused:
            with self.subTest(text=text):
                findings, _ = self.scan_text(
                    "# page\n\n## Procedure\n\n" + text)
                self.assertTrue(findings, text)

    def test_prohibition_description_and_markdown_exemptions_are_observable(self):
        cases = [
            ("1. No edits to the `BOARD.md` row are allowed.\n",
             "prohibition"),
            ("1. It updates the `BOARD.md` row.\n", "descriptive"),
            ("1. It already updates the `BOARD.md` row.\n", "descriptive"),
            ("1. Writes the accompanying `BOARD.md` row itself.\n",
             "descriptive"),
            ("1. Creating a queue row also creates `BOARD.md § Intake`.\n",
             "descriptive"),
            ("1. `BOARD.md` is rendered afterwards and a derived-surface "
             "write is reported.\n", "descriptive"),
        ]
        for text, exemption in cases:
            with self.subTest(text=text):
                findings, suppressed = self.scan_text(
                    "# page\n\n## Procedure\n\n" + text)
                self.assertEqual(findings, [])
                self.assertTrue(any(s.exemption == exemption
                                    for s in suppressed), suppressed)

        findings, suppressed = self.scan_text(
            "# page\n\n## Inventory\n\n"
            "| Action | Update `BOARD.md`: add a row. |\n"
            "> Update `BOARD.md`: add a declaration row.\n")
        self.assertEqual(findings, [])
        self.assertEqual(
            [(s.exemption, s.target) for s in suppressed],
            [("quoted-or-table", "BOARD.md row"),
             ("quoted-or-table", "BOARD.md row")])

    def test_write_participles_and_read_anchors_do_not_go_silent(self):
        passive, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. The row must be added to `BOARD.md` by hand.\n")
        self.assertEqual([(f[1], f[2]) for f in passive],
                         [("BOARD.md row", "R1")])

        read_only, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. Consult `BOARD.md`, then append a note to the weekly report.\n")
        self.assertEqual(read_only, [],
                         "a read target is not the later write destination")

        write_after_check, _ = self.scan_text(
            "# page\n\n## Procedure\n\n"
            "1. Check the prerequisites and permissions, then update the "
            "`BOARD.md` row.\n")
        self.assertEqual([(f[1], f[2]) for f in write_after_check],
                         [("BOARD.md row", "R1")],
                         "READ is anchored immediately before the target")

    def test_r2_reports_a_licensed_hand_edit_and_a_refusal_is_not_one(self):
        """R2 fires, and its own refusal clause turns it off.

        R2 is the rule that caught the two steps teaching a hand edit months
        after the tool had closed the gap — the ones the docstring calls the
        kind that rot. Neutering `HAND_LICENCE` left the module green: the rule
        was described in three paragraphs and exercised by nothing, so a
        rewrite of the pattern could delete the whole rule and pass.

        The refusal half is tested with it because `NOT_BY_HAND` is what keeps
        R2 off the sentences that *forbid* the hand edit, and a suppression
        with no test is how a guard ends up reporting the cases people know
        are fine.
        """
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "steps.md"

            page.write_text(
                "# s\n\n## Procedure\n\n"
                "1. Run `perry-task list` first. The status-change line is "
                "still written by hand.\n")
            hit = scan(page)
            self.assertEqual([(f[1], f[2]) for f in hit],
                             [("the journal's status / definition block", "R2")],
                             "R2 must fire even though the step names the tool "
                             "— licensing the hand edit one clause after "
                             f"calling the tool is the live shape; got {hit}")

            page.write_text(
                "# s\n\n## Procedure\n\n"
                "1. Run `perry-task list` first. The status-change line is "
                "never written by hand.\n")
            suppressed: list[Suppression] = []
            self.assertEqual(scan(page, suppressed), [],
                             "a sentence refusing the hand edit is the "
                             "instruction this guard wants, not a violation")
            self.assertIn(
                ("r2-refusal", "the journal's status / definition block"),
                [(s.exemption, s.target) for s in suppressed])

            page.write_text(
                "# s\n\n## Procedure\n\n"
                "1. The status-change line is never written by hand. Later, "
                "the status-change line is still written by hand.\n")
            hit = scan(page)
            self.assertEqual([(f[1], f[2]) for f in hit],
                             [("the journal's status / definition block", "R2")],
                             "one refusal cannot discharge a later licence")

    def test_owner_tools_exist(self):
        """Every rule names a tool that is actually in `bin/`.

        The rule table is the one thing here that is written down. An entry
        pointing at a tool someone renamed would suppress its own findings
        forever — silently, because a rule that never fires looks like a clean
        repository.
        """
        for name, spec in TARGETS.items():
            with self.subTest(target=name):
                self.assertTrue((PERRY_HOME / "bin" / spec["tool"]).is_file(),
                                f"{spec['tool']} does not exist in bin/")

    def test_no_procedure_hand_edits_a_tool_owned_file(self):
        findings = []
        for page in procedure_pages():
            for line, target, rule, snippet in scan(page):
                findings.append(
                    f"  {page.relative_to(PERRY_HOME)}:{line}  [{rule}] "
                    f"{target}\n      {snippet[:160]}")
        self.assertEqual(
            findings, [],
            "ADR-007 rule 3: call the tool for the fields, then generate the "
            "document from what it returned. These steps write the fields "
            "themselves:\n" + "\n".join(findings))


if __name__ == "__main__":
    unittest.main()
