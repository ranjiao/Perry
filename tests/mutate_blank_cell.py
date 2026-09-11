"""TASK-431's mutation round, re-runnable.

    python3 tests/mutate_blank_cell.py [<git ref>]

For each site the row changed, put the OLD literal back and show a NAMED test
go red. `work/reference/review.md § 2` rule 2: a claim that code handles a case
is verified by breaking the code and watching the check go red, and **a green
mutation is a finding either way** — either the guard does not work or the test
does not test it.

The discipline here is not decoration; each line of it was bought by a round
that got a wrong answer and believed it:

* **Anchor on text whose occurrence count is checked, and report the line.**
  Never `str.replace(old, new, 1)` on a string that occurs more than once. This
  harness refuses rather than guessing, and it caught itself doing it: the
  anchor for `rung_satisfied` is a strict SUBSTRING of the anchor for
  `done-needs-evidence` twenty spaces further in, so the count came back 2 and
  the mutation was declined instead of landing in the wrong function.
* **Clear `__pycache__` and sleep past the whole-second boundary.** CPython
  validates cached bytecode on mtime-in-whole-seconds plus size, so a same-size
  edit reverted inside one second runs the stale `.pyc` and shows a result that
  never happened.
* **Restore from `git show <ref>:<path>`, and verify with
  `bin/perry-restore-check`.** Never against bytes this script snapshotted: a
  file that was ALREADY mutated when the harness started gets "restored" to
  that mutation and reported OK, which is the failure `perry-restore-check`
  exists to catch.

Run it from a clean tree. It edits files in `bin/` and `viewer/` and puts them
back, so a dirty tree means the restore target is not what you think it is.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent

#: `(label, path, anchor, replacement)`. The anchor is the CURRENT text; the
#: replacement is the literal this row removed, put back verbatim.
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("1  perry-lint · suspect-separator guard reads its own set",
     "bin/perry-lint",
     "                        if not cell or lib.is_blank_cell(cell):",
     '                        if not cell or cell in {"", "—", "–", "-", "n/a", "N/A", "tbd", "TBD", "?"}:'),

    ("2  perry-state · split_stages back to the em dash alone",
     "bin/perry-state",
     '    if lib.is_blank_cell(cell or ""):',
     '    if (cell or "").strip() in ("", "—"):'),

    ("3  perry-state · split_stages keeps blank interior elements",
     "bin/perry-state",
     "            if p.strip() and not lib.is_blank_cell(p)]",
     "            if p.strip()]"),

    ("4  perry-state · missing_defaults back to its own 7-element list",
     "bin/perry-state",
     '        if lib.is_blank_cell(col(key) or ""):',
     '        if (col(key) or "").strip().lower() in {"", "—", "–", "-", "n/a", "tbd", "?"}:'),

    ("5  perry-state · parse_config back to blank_marker + em dash",
     "bin/perry-state",
     "        [n for n in names if n and not lib.is_blank_cell(n)])",
     '        [n for n in names if n and n != blank_marker() and n != "—"])'),

    ("6  perry-lint · done-needs-evidence back to its own set",
     "bin/perry-lint",
     "                    if not ev or lib.is_blank_cell(ev):",
     '                    if not ev or ev in {"—", "-", ""}:'),

    # Anchored with the surrounding newlines: without them this is a substring
    # of mutation 6's line and the count comes back 2.
    ("7  perry-lint · rung_satisfied back to its own tuple",
     "bin/perry-lint",
     "\n    if not ev or lib.is_blank_cell(ev):\n",
     '\n    if not ev or ev in ("—", "-"):\n'),

    ("8  perry-explain · harvest back to the em dash alone",
     "bin/perry-explain",
     "                            if v and not lib.is_blank_cell(v):",
     '                            if v and v != "—":'),

    ("9  perry-knowledge · a source cell decided locally again",
     "bin/perry-knowledge",
     '    if not src or lib.is_blank_cell(src):\n        return answer(False, "no-source",',
     '    if not src or src in {"", "—", "-", "n/a", "tbd"}:\n        return answer(False, "no-source",'),

    ("10 viewer · parse_due drops the blank test",
     "viewer/parsers.py",
     "        if t.lower() in _NO_DATE or is_blank_cell(t):",
     "        if t.lower() in _NO_DATE:"),

    ("11 viewer · ask_is_answered drops the blank test",
     "viewer/parsers.py",
     '    return (bool(s) and not is_blank_cell(status_cell or "")\n'
     "            and not s.startswith(_ASK_STILL_OPEN))",
     "    return bool(s) and not s.startswith(_ASK_STILL_OPEN)"),

    # The other half of the same rule: the prefix members are NOT redundant.
    ("11b viewer · _ASK_STILL_OPEN loses its em-dash prefixes",
     "viewer/parsers.py",
     '_ASK_STILL_OPEN = ("pending", "waiting", "open", "—", "-")',
     '_ASK_STILL_OPEN = ("pending", "waiting", "open")'),

    ("12 viewer · intake_is_discharged drops the blank test",
     "viewer/parsers.py",
     '    return (not is_blank_cell(outcome or "")\n'
     '            and squash(outcome or "") not in INTAKE_UNSET_OUTCOME)',
     '    return squash(outcome or "") not in INTAKE_UNSET_OUTCOME'),

    ("13 viewer · the wrapper grows a literal fallback list",
     "viewer/parsers.py",
     '        return not (value or "").strip()',
     '        return (value or "").strip().lower() in {"", "—", "n/a"}'),
]

MODULE = "test_blank_cell_is_one_rule"


def _clear_pycache() -> None:
    for cache in PERRY_HOME.rglob("__pycache__"):
        for pyc in cache.glob("*.pyc"):
            pyc.unlink(missing_ok=True)


def _settle() -> None:
    """Past the whole-second boundary CPython's .pyc validity check uses."""
    _clear_pycache()
    time.sleep(1.2)


def main(argv: list[str]) -> int:
    ref = argv[0] if argv else "HEAD"
    ref = subprocess.run(["git", "rev-parse", ref], cwd=PERRY_HOME,
                         capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=PERRY_HOME,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print("refusing: the tree is dirty, so the restore target is not what "
              "you think it is.\n" + dirty)
        return 2

    results = []
    for label, path, anchor, replacement in MUTATIONS:
        target = PERRY_HOME / path
        text = target.read_text(encoding="utf-8")
        count = text.count(anchor)
        if count != 1:
            results.append((label, "ANCHOR", f"{count} occurrences, need 1"))
            print(f"!!    {label} — anchor matched {count} times, declined")
            continue
        lineno = text[:text.index(anchor)].count("\n") + 1
        target.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
        _settle()
        run = subprocess.run([sys.executable, "tests/parallel", MODULE],
                             cwd=PERRY_HOME, capture_output=True, text=True)
        out = run.stdout + run.stderr
        named = sorted({line.split()[1] for line in out.splitlines()
                        if line.strip().startswith(("FAIL ", "ERROR "))
                        and len(line.split()) > 1})

        blob = subprocess.run(["git", "show", f"{ref}:{path}"],
                              cwd=PERRY_HOME, capture_output=True)
        target.write_bytes(blob.stdout)
        check = subprocess.run(
            [sys.executable, "bin/perry-restore-check", ref, path],
            cwd=PERRY_HOME, capture_output=True, text=True)
        _settle()

        verdict = "RED" if run.returncode else "GREEN"
        results.append((label, verdict,
                        f"{path}:{lineno} · restore="
                        f"{'ok' if check.returncode == 0 else 'FAILED'}"))
        print(f"{verdict:5} {label}  ({path}:{lineno})  "
              f"restore={'ok' if check.returncode == 0 else 'FAILED'}")
        for name in named[:2]:
            print(f"        {name}")

    green = [r for r in results if r[1] != "RED"]
    print(f"\n{len(results) - len(green)} of {len(results)} mutations went RED")
    for label, verdict, detail in green:
        print(f"  FINDING · {verdict} · {label} — {detail}")
    return 1 if green else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
