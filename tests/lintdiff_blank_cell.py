"""TASK-431 verification 3: does the widened blank rule change what lint says?

    python3 tests/lintdiff_blank_cell.py <base-ref>      # default 70458893

Materialises `<base-ref>` into a temp dir with `git archive` and runs THAT
tree's `bin/perry-lint` and this tree's over the **same** temp project, so the
only variable is the linter. Prints the findings that appear in one and not
the other.

**Why `git archive` and not a second worktree**: the comparison has to be
against an independent materialisation of a commit, and a worktree would put
a second checkout of this repository on disk beside the one the agent is
working in — which is how a session ends up editing the wrong tree. This is
read-only and lands in a temp directory.

Two cells are probed, because the interesting answers are different:

* `stages` — the cell the row's finding is about. The answer here is **no
  change**, and that is the point: the suspect-separator guard only fires on a
  cell containing a suspect character, and the only declared spellings that do
  (`n/a`, `N/A`) were already in the old hardcoded set. The bogus stage went
  away because `split_stages` stopped producing it, not because lint started
  reporting it.
* `sla` — a column `pipeline` mode declares as having no default. Here the
  answer is **one extra finding** for every spelling the English-only list did
  not know, which is the localization gap closing where you can see it.
"""

from __future__ import annotations

import collections
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "second-project"
TRACK = "research"


def spellings() -> list[str]:
    blank = (json.loads((PERRY_HOME / "schema" / "state-schema.json")
                        .read_text(encoding="utf-8")).get("i18n") or {}
             ).get("blank_cell") or {}
    out: list[str] = []
    for key, values in blank.items():
        if key == "note" or not isinstance(values, list):
            continue
        for value in values:
            if value not in out:
                out.append(value)
    return out


def materialise(ref: str) -> Path:
    base = Path(tempfile.mkdtemp(prefix="t431-base-"))
    archive = subprocess.run(["git", "archive", ref], cwd=PERRY_HOME,
                             capture_output=True)
    if archive.returncode != 0:
        raise SystemExit(f"git archive {ref} failed: "
                         f"{archive.stderr.decode()[:200]}")
    subprocess.run(["tar", "-x", "-C", str(base)], input=archive.stdout,
                   check=True)
    return base


def findings(home: Path, project: Path) -> list[str]:
    run = subprocess.run(
        [sys.executable, str(home / "bin" / "perry-lint"),
         "--root", str(project), "--json"], capture_output=True, text=True)
    data = json.loads(run.stdout)
    rows = data.get("findings") if isinstance(data, dict) else data
    return [f"{f.get('level')}/{f.get('code')}: {str(f.get('message'))[:110]}"
            for f in (rows or [])]


def project_with(field: str, value: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="t431-lint-"))
    dst = tmp / "proj"
    shutil.copytree(FIXTURE, dst)
    store = dst / ".perry" / "config.jsonl"
    out = []
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("kind") == "track" and record.get("track") == TRACK:
            record[field] = value
        out.append(json.dumps(record, ensure_ascii=False))
    store.write_text("\n".join(out) + "\n", encoding="utf-8")
    return dst


def main(argv: list[str]) -> int:
    base_home = materialise(argv[0] if argv else "70458893")
    try:
        for field, values in (("stages", spellings()),
                              ("sla", ["", "n/a", "无", "待定", "不适用",
                                       "暂无", "N.A.", "TBA", "3d"])):
            print(f"\n=== `{field}` cell " + "=" * 50)
            changed = 0
            for value in values:
                project = project_with(field, value)
                try:
                    before = collections.Counter(findings(base_home, project))
                    after = collections.Counter(findings(PERRY_HOME, project))
                finally:
                    shutil.rmtree(project.parent, ignore_errors=True)
                if before == after:
                    print(f"{value!r:>10} | same ({sum(before.values())})")
                    continue
                changed += 1
                print(f"{value!r:>10} | before {sum(before.values())} · "
                      f"after {sum(after.values())}")
                for text, n in (after - before).items():
                    print(f"           + ({n}x) {text}")
                for text, n in (before - after).items():
                    print(f"           - ({n}x) {text}")
            print(f"{changed} of {len(values)} values changed lint's findings")
    finally:
        shutil.rmtree(base_home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
