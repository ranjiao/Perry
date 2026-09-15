"""TASK-262 — what `perry-tasks board` says about where each printed thing comes from.

`P003-O2-KR3` (USER-907 answer (a)): a reader can tell, from the board alone,
a stored record from what the render made up. `bin/perry_store.py § DECLARED_
BOARD_CHOICES` "sources" is the render's side. This file is the check's side,
and **every expectation here is built from a declaration, never from the
output**:

* the section line: the store's path and anchor from `schema/state-schema.json
  § claims`, the writers from `bin/perry-task § SURFACE` (`writes`), read as a
  literal by this file's own reader. The wording is written here too, so a
  renderer that drops a line, names another store or another writer is red;
* the column mark: the register's `*FIELD_BY_COLUMN` map in `bin/perry_store`
  — the spec names those maps as the source (TASK-262 § Verification 2). A
  column is stored exactly when the map gives its folded header a field;
* the register a section belongs to: the schema's `files[id=board].tables[]
  .under` patterns, and a `## ` heading the template does not carry is an
  undeclared task group.

**THE STRIP RULE** (§ Verification 3), applied line by line to the output:

  1. delete every line that starts with `> ` — the legend and the section
     lines. The board at the base commit prints no such line (choice "prose"
     drops the template's `>` block);
  2. on a `# ` line, delete one trailing ` †`;
  3. on a table header line — a `|` line whose next line is a separator —
     replace every ` † |` with ` |`.

Nothing else is touched, so a changed cell, row, order or blank line survives
the strip and fails the comparison.

**The KR's measurement**, which this file prints when run:

    python3 tests/board_sources.py [--root PATH]

    sections naming their store and writer: 6/6 (100%)
    columns classified: 44/44 (100%)

Exit 0 when both are 100%, 1 when either is short, 2 when no board printed.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "viewer"))
sys.path.insert(0, str(ROOT / "bin"))
from tables import header_index, split_row  # noqa: E402

import perry_store  # noqa: E402

MARK = "†"
SEPARATOR = re.compile(r"^\|\s*:?-{2,}")

SCHEMA = json.loads((ROOT / "schema" / "state-schema.json").read_text(encoding="utf-8"))
SPEC = next(f for f in SCHEMA["files"] if f.get("id") == "board")
CLAIMS = SCHEMA["claims"]

#: A name each register's declared table `under` pattern takes, so the table
#: is found through the schema rather than by index.
SECTION_NAME = {"tasks": "P1", "asks": "User Input Queue", "risks": "Top risks",
                "intake": "Intake", "cadence": "Cadence"}

#: Which map a register's columns resolve through (§ Verification 2 names them).
FIELD_MAP = {"tasks": perry_store.FIELD_BY_COLUMN,
             "asks": perry_store.ASK_FIELD_BY_COLUMN,
             "risks": perry_store.RISK_FIELD_BY_COLUMN,
             "intake": perry_store.INTAKE_FIELD_BY_COLUMN,
             "cadence": perry_store.CADENCE_FIELD_BY_COLUMN}

ANCHOR = {"state": "under the state root", "project": "at the project root"}


def writer_surface() -> dict:
    """`bin/perry-task § SURFACE`, by this file's own literal reader."""
    tree = ast.parse((ROOT / "bin" / "perry-task").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(getattr(t, "id", None) == "SURFACE" for t in n.targets))
    return ast.literal_eval(node.value)


def template_headings() -> list[str]:
    return [l[3:].strip() for l in (ROOT / SPEC["template"]).read_text(
        encoding="utf-8").split("\n") if l.startswith("## ")]


def register_of(title: str) -> str | None:
    """The register a printed `## ` section belongs to, from the schema."""
    table = next((t for t in SPEC["tables"] if re.search(t["under"], title)), None)
    if table is None:
        return None if title in template_headings() else "tasks"
    return next((r for r, name in SECTION_NAME.items()
                 if re.search(table["under"], name)), None)


def store_claim(register: str) -> dict | None:
    return next((c for c in CLAIMS if c.get("path") == f"{register}.jsonl"
                 and c.get("kind") == "file"), None)


def writers(register: str, surface: dict) -> list[str]:
    path = f"{register}.jsonl"
    return [s["name"] for s in surface["subcommands"] if path in s.get("writes", [])]


def expected_source_line(register: str | None, surface: dict) -> str:
    if register is None:
        return (f"> {MARK} No store: this section's table is the template's, "
                f"not a register's")
    claim = store_claim(register)
    if claim is None:
        return (f"> {MARK} No store: `schema/state-schema.json § claims` "
                f"declares none for the {register} register")
    where = f"`{claim['path']}` {ANCHOR[claim['anchor']]}"
    names = writers(register, surface)
    if not names:
        return (f"> Stored in {where}; no `{surface['name']}` subcommand "
                f"declares a write to it")
    return f"> Stored in {where}; written by `{surface['name']}` " + ", ".join(names)


def is_stored(register: str | None, column: str) -> bool:
    if register is None:
        return False
    return bool(FIELD_MAP[register].get(header_index([column])[0]))


def strip(text: str) -> str:
    """THE STRIP RULE. See the module docstring."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if line.startswith("> "):
            continue
        if line.startswith("# ") and line.endswith(f" {MARK}"):
            line = line[:-len(f" {MARK}")]
        elif (line.startswith("|") and i + 1 < len(lines)
              and SEPARATOR.match(lines[i + 1])):
            line = line.replace(f" {MARK} |", " |")
        out.append(line)
    return "\n".join(out)


def measure(text: str, surface: dict | None = None) -> dict:
    """Every section and every column of `text`, each checked against the
    declarations. `{"sections": [...], "columns": [...]}`, one dict per item
    with `ok`."""
    surface = surface or writer_surface()
    lines = text.split("\n")
    sections, columns, register, title = [], [], None, None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            title = line[3:].strip()
            register = register_of(title)
            want = expected_source_line(register, surface)
            got = lines[i + 1] if i + 1 < len(lines) else ""
            sections.append({"title": title, "register": register,
                             "want": want, "got": got, "ok": got == want})
        elif (line.startswith("|") and i + 1 < len(lines)
              and SEPARATOR.match(lines[i + 1])):
            for cell in split_row(line):
                marked = cell.endswith(f" {MARK}")
                name = cell[:-len(f" {MARK}")] if marked else cell
                stored = is_stored(register, name)
                columns.append({"section": title, "column": name,
                                "marked": marked, "stored": stored,
                                "ok": marked != stored})
    return {"sections": sections, "columns": columns}


def printed(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "bin" / "perry-tasks"),
                           "board", "--root", str(root)],
                          capture_output=True, text=True)


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    proc = printed(root)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr, end="")
        return 2
    got = measure(proc.stdout)
    rc = 0
    for label, key in (("sections naming their store and writer", "sections"),
                       ("columns classified", "columns")):
        items = got[key]
        ok = sum(1 for x in items if x["ok"])
        pct = (100 * ok // len(items)) if items else 0
        print(f"{label}: {ok}/{len(items)} ({pct}%)")
        rc |= int(ok != len(items) or not items)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
