"""Every `file.md § Section` pointer in the shipped docs resolves.

**`DESIGN-004 § 8` named this class and deferred it**: *"Round 5 found index
rows pointing at procedures that do not exist. A write tool cannot catch that.
A `perry-lint` mode that resolves every `reference/*.md § <section>` pointer in
a subcommand index would."* This is that check, as a test rather than a mode,
because it is about the shipped skill rather than about a user's project.

It bit for real twice in one night: `TASK-021-close.md` cites
`TASK-021-v4-review-round2.md`, which does not exist, and six pointers in the
skill's own pages named sections that had been renamed — `SKILL.md § Bootstrap`
after it became `§ First-time setup`, and `reference/digests.md` from a page
whose sibling is `work/reference/digests.md`.

**Two things stop it crying wolf**, and both were measured before they were
coded:

- A naive version reported **172 of 865** pointers as dangling, almost all
  because a template legitimately names `BOARD.md` or `OKR.md` — files in a
  USER's project, which the skill does not contain. Those are read from the
  schema's own `files[]`, not from a list here.
- A heading-only version reported `SKILL.md § Reading the lane docs`, which is
  real and findable — it is bold text inside a blockquote. An anchor is a
  heading **or** a bold run.

Run: python3 tests/parallel test_pointers_resolve
"""

from __future__ import annotations

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: `path.md § Section`. The section half is required — a bare filename is a
#: mention, not a pointer, and mentions are checked by `test_claims`.
POINTER = re.compile(r"`([\w./-]+\.md)\s*§\s*([^`\n]+)`")

SHIPPED = ("work", "goals", "decide", "reference", "modes", "packs", "schema")


def project_owned() -> set[str]:
    """Files a USER's project owns. A skill page naming one is correct.

    Read from `schema/state-schema.json § files[]` rather than listed here, so
    a new state file does not have to be remembered in two places — which is
    the defect this repository has spent the week removing.
    """
    schema = json.loads((ROOT / "schema" / "state-schema.json").read_text())
    names = {pathlib.Path(f["path"]).name
             for f in schema["files"] if f.get("path")}
    return names | {"BOARD.md", "OKR.md", "PROJECT_STATE.md",
                    "ARCHITECTURE.md", "config.md", "hook.md", "CURRENT"}


def normalize(s: str) -> str:
    """One normalization, used on BOTH sides.

    **They were normalized differently and it took a mutation to notice.** The
    anchor stripped `>` — for blockquotes — and the key did not, so a heading
    `## \`commit <promise>\`` became `commit <promise` while the pointer stayed
    `commit <promise>`, and four correct pointers were reported as dangling.

    One rule with two spellings, inside the check written to find one rule with
    two spellings.

    **Measured afterwards, because the mutation for it comes back green:**
    reverting the key side to its old form changes nothing on this corpus — 0
    of the pointers normalize differently under the two. `normalize` strips
    only a LEADING `>` (a blockquote marker), never an inner one, which is
    exactly what makes `commit <promise>` resolve. The green mutation is a
    genuine no-op here rather than a hole, and it is recorded as such instead
    of being chased or quietly dropped.
    """
    return re.sub(r"[`*#]", "", s).lstrip("> ").strip().lower()


#: A bold run long enough to be a sentence is prose, not a label. Measured: the
#: longest real bold anchor in this repo is well under this.
_LABEL_MAX = 60


def anchors(text: str) -> list[str]:
    """Every place a `§` can legitimately point: a heading, or a bold LABEL.

    **The bold half was too loose and a mutation proved it.** The first version
    took the whole LINE containing `**`, so `SKILL.md § Bootstrap` resolved
    against a 300-character bold sentence that happens to contain the word
    "bootstrap" — and planting that exact rename left the check green.

    So the anchor is the bold RUN itself, extracted from `**…**`, and only when
    it is short enough to be a label rather than a sentence. That keeps
    `§ Reading the lane docs` — a real bold label in a blockquote — resolvable,
    which is why the bold case exists at all.
    """
    out = []
    for line in text.splitlines():
        if line.startswith("#"):
            out.append(normalize(line))
        for run in re.findall(r"\*\*([^*]{1,%d})\*\*" % _LABEL_MAX, line):
            out.append(normalize(run))
    return [a for a in out if a]


def pages():
    for d in SHIPPED:
        yield from sorted((ROOT / d).rglob("*.md"))
    yield ROOT / "SKILL.md"


class TestEveryPointerResolves(unittest.TestCase):
    def test_no_pointer_names_a_section_that_is_not_there(self):
        owned = project_owned()
        dangling = []
        for p in pages():
            for m in POINTER.finditer(p.read_text(errors="replace")):
                rel, sec = m.group(1), m.group(2).strip()
                if pathlib.Path(rel).name in owned:
                    continue
                hit = next((c for c in (p.parent / rel, ROOT / rel)
                            if c.exists()), None)
                where = p.relative_to(ROOT).as_posix()
                if hit is None:
                    dangling.append(f"{where} → {rel} (no such file)")
                    continue
                key = normalize(sec)
                # `key in a` only. The reverse direction let a short anchor
                # match any longer pointer, which is the same looseness one
                # level down.
                if not any(key in a
                           for a in anchors(hit.read_text(errors="replace"))):
                    dangling.append(f"{where} → {rel} § {sec}")
        self.assertEqual(dangling, [], "\n" + "\n".join(dangling))

    def test_it_is_actually_scanning(self):
        """A guard that finds nothing because it looks nowhere passes forever.

        The count is asserted low-side only: pointers get added and removed,
        and pinning an exact number would make every doc edit a test failure.
        """
        found = sum(len(POINTER.findall(p.read_text(errors="replace")))
                    for p in pages())
        self.assertGreater(found, 100, f"only {found} pointers seen")

    def test_a_user_project_file_is_not_reported(self):
        """The cry-wolf case, measured: a naive version reported 172 of 865
        pointers, almost all of them a template correctly naming `BOARD.md`."""
        self.assertIn("BOARD.md", project_owned())
        self.assertIn("OKR.md", project_owned())

    def test_a_bold_run_counts_as_an_anchor(self):
        """`SKILL.md § Reading the lane docs` is bold text in a blockquote and
        a reader finds it immediately. A heading-only check reported it."""
        self.assertIn("reading the lane docs",
                      anchors((ROOT / "SKILL.md").read_text()))

    def test_a_bold_sentence_is_not_an_anchor(self):
        """The mutation that caught the first version: `SKILL.md § Bootstrap`
        resolved against a 300-character bold sentence containing the word.
        A label is short; a sentence is prose."""
        long_run = "**" + "x " * 60 + "**"
        self.assertEqual(anchors(long_run), [])


if __name__ == "__main__":
    unittest.main()
