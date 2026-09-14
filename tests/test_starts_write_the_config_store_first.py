"""Every documented start writes `.perry/config.jsonl` first (TASK-237 3b′).

**Why this exists.** `schema/README.md § installed` stopped counting `BOARD.md`,
`OKR.md`, `phase/` and `design/`. Four documented starts wrote only markdown —
the `work` bootstrap, a decide-only start, `goals init`, and `/perry adopt
--only=design,knowledge,arch` — and first-time setup still told the agent to
write `.perry/config.md`, which ADR-019 deleted and no reader reads. Under the
criterion each would read as not installed and be offered first-time setup on
every session (`TASK-237-d3b-result.md § 3.1`). User decision A, 2026-09-14:
every start writes the config store first, through `perry-config set`.

**What is read, and how.** The sections below are located by their heading
LINE, deterministically: a section runs from its heading to the next heading of
the same or a higher level, and a heading that matches nothing or more than one
line fails by name rather than guarding an empty string. Inside them this reads
two literals and nothing else — it judges no meaning:

1. `.perry/config.md` does not appear. Every place a start named that file,
   read or write, is a place the start would either write a file nobody reads
   or conclude the project is unconfigured.
2. A section that performs a start's first write carries at least one fenced
   line beginning `"$PERRY_HOME/bin/perry-config" set`, and **those lines are
   executed**, placeholders replaced by a fixed value, in an empty directory.
   `perry-state --section installed` must read `false` before and `true`
   after. A doc line that stops being a valid invocation reddens here.

Run: python3 tests/parallel test_starts_write_the_config_store_first
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: `(file, heading line prefix or None for the whole file)`. Enumerated from the
#: router (`SKILL.md § First-time setup`, `§ Router subcommands`) and each
#: lane's `§ Bootstrap` / `init`, not from the dispatch's list.
GUARDED = (
    ("SKILL.md", "## Mandatory first move"),
    ("SKILL.md", "## First-time setup"),
    ("SKILL.md", "## Configuration"),
    ("reference/first-run.md", None),
    ("work/SKILL.md", "## Mandatory first move: the Standup"),
    ("work/SKILL.md", "## Bootstrap"),
    ("work/reference/bootstrap.md", None),
    ("goals/SKILL.md", "## Mandatory first move: the OKR Snapshot"),
    ("goals/SKILL.md", "## Bootstrap"),
    ("goals/reference/setup.md", "## `init`"),
    ("decide/SKILL.md", "## Mandatory first move: the Design Snapshot"),
    ("decide/SKILL.md", "### `init`"),
    ("decide/SKILL.md", "## Bootstrap"),
    ("decide/reference/decisions.md", None),
    ("reference/adoption.md", None),
)

#: The sections that perform a start's first write — each must carry the tool
#: invocation, and each is executed.
WRITERS = (
    ("SKILL.md", "## First-time setup"),
    ("work/reference/bootstrap.md", None),
    ("goals/reference/setup.md", "## `init`"),
    ("decide/SKILL.md", "### `init`"),
    ("reference/adoption.md", None),
)

DELETED = ".perry/config.md"
TOOL = '"$PERRY_HOME/bin/perry-config" set'


def section(rel: str, heading: str | None) -> str:
    text = (ROOT / rel).read_text(encoding="utf-8")
    if heading is None:
        return text
    lines = text.splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if line.startswith(heading)]
    if len(hits) != 1:
        raise AssertionError(f"{rel}: heading {heading!r} matched {len(hits)} "
                             f"line(s); a guard over no section guards nothing")
    level = len(heading) - len(heading.lstrip("#"))
    out = [lines[hits[0]]]
    for line in lines[hits[0] + 1:]:
        m = re.match(r"^(#+)\s", line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "".join(out)


def env() -> dict:
    e = dict(os.environ)
    e.pop("PERRY_PROJECT", None)
    e["PERRY_HOME"] = str(ROOT)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return e


def installed(d: Path) -> bool:
    p = subprocess.run([sys.executable, str(ROOT / "bin" / "perry-state"),
                        "--root", str(d), "--section", "installed"],
                       capture_output=True, text=True, cwd=str(d), env=env())
    if p.returncode != 0:
        raise AssertionError(f"perry-state exited {p.returncode}: {p.stderr}")
    return json.loads(p.stdout)["installed"]


class TheDeletedFileIsNotNamed(unittest.TestCase):

    def test_no_start_section_names_the_deleted_config_file(self):
        for rel, heading in GUARDED:
            with self.subTest(file=rel, section=heading):
                body = section(rel, heading)
                self.assertGreater(len(body.strip()), 0)
                for n, line in enumerate(body.splitlines(), 1):
                    self.assertNotIn(
                        DELETED, line,
                        f"{rel} § {heading or '(whole file)'} line {n} of the "
                        f"section names `{DELETED}`, which ADR-019 deleted; a "
                        f"start that writes or reads it ends not installed")


class EveryStartWritesTheStoreThroughTheTool(unittest.TestCase):

    def commands(self, rel: str, heading: str | None) -> list[str]:
        return [line.strip() for line in section(rel, heading).splitlines()
                if line.strip().startswith(TOOL)]

    def test_each_writing_start_names_the_tool(self):
        for rel, heading in WRITERS:
            with self.subTest(file=rel, section=heading):
                self.assertTrue(self.commands(rel, heading),
                                f"{rel} § {heading or '(whole file)'} carries "
                                f"no `{TOOL}` line")

    def test_the_documented_lines_run_and_end_installed(self):
        for rel, heading in WRITERS:
            cmds = self.commands(rel, heading)
            with self.subTest(file=rel, section=heading):
                self.assertTrue(cmds)
                d = Path(tempfile.mkdtemp(prefix="perry-start-")).resolve()
                self.addCleanup(shutil.rmtree, d, ignore_errors=True)
                self.assertFalse(installed(d), "anti-vacuity: an empty "
                                 "directory already reads as installed")
                for line in cmds:
                    argv = shlex.split(re.sub(r"<[^>]+>", "x", line))
                    self.assertEqual(argv[:2], ["$PERRY_HOME/bin/perry-config",
                                                "set"])
                    self.assertIn("--root", argv)
                    argv[argv.index("--root") + 1] = str(d)
                    p = subprocess.run(
                        [sys.executable, str(ROOT / "bin" / "perry-config"),
                         *argv[1:]],
                        capture_output=True, text=True, cwd=str(d), env=env())
                    self.assertEqual(p.returncode, 0,
                                     f"{rel}: `{line}` exited {p.returncode}: "
                                     f"{p.stderr}")
                self.assertTrue((d / ".perry" / "config.jsonl").is_file())
                self.assertTrue(installed(d),
                                f"{rel}: the documented start's first write "
                                f"does not make the project installed")


if __name__ == "__main__":
    unittest.main()
