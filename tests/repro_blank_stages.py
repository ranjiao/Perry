"""TASK-431's reported consequence, reproducible on demand.

    python3 tests/repro_blank_stages.py

Copies `tests/fixtures/second-project` to a temp dir, rewrites ONE track's
`stages` cell to each declared blank spelling in turn, and prints what
`bin/perry-state --compact` says about that track.

**This is not a test and is deliberately not named like one.** It is the
measurement the row's finding was stated in, kept runnable so the next reader
can re-derive the table in the result rather than trust it.
`tests/test_blank_cell_is_one_rule.py § TestTheCompactPayloadIsClean` is the
assertion; this is the picture.

At `70458893` — before the fix — 20 of the 21 spellings below came back as a
DECLARED stage list, 20 of those a single stage named after the blank marker.
Only the bare em dash behaved, because it was the one literal `split_stages`
had been taught.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PERRY_HOME = Path(__file__).resolve().parent.parent
FIXTURE = PERRY_HOME / "tests" / "fixtures" / "second-project"
TRACK = "research"

#: The six `V4 round 8` named, first, so the row's own claim is legible in the
#: output; then the rest of the declared 17; then the decorated forms a real
#: board carries. Read from the schema, never restated.
SIX = ["-", "–", "n/a", "N/A", "none", "无"]
DECORATED = ["**—**", "`n/a`", " 无。 "]


def spellings() -> list[str]:
    blank = (json.loads((PERRY_HOME / "schema" / "state-schema.json")
                        .read_text(encoding="utf-8")).get("i18n") or {}
             ).get("blank_cell") or {}
    declared: list[str] = []
    for key, values in blank.items():
        if key == "note" or not isinstance(values, list):
            continue
        for value in values:
            if value not in declared:
                declared.append(value)
    return SIX + [s for s in declared if s not in SIX] + DECORATED


def compact_track(stages: str) -> dict | None:
    tmp = Path(tempfile.mkdtemp(prefix="t431-repro-"))
    try:
        dst = tmp / "proj"
        shutil.copytree(FIXTURE, dst)
        store = dst / ".perry" / "config.jsonl"
        out = []
        for line in store.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("kind") == "track" and record.get("track") == TRACK:
                record["stages"] = stages
            out.append(json.dumps(record, ensure_ascii=False))
        store.write_text("\n".join(out) + "\n", encoding="utf-8")
        run = subprocess.run(
            [sys.executable, str(PERRY_HOME / "bin" / "perry-state"),
             "--root", str(dst), "--compact"],
            capture_output=True, text=True)
        if run.returncode != 0:
            print(f"  perry-state failed: {run.stderr[:200]}")
            return None
        tracks = (json.loads(run.stdout).get("project") or {}).get("tracks") or []
        return next((t for t in tracks if t.get("track") == TRACK), None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    print(f"{'stages cell':>12} | {'stage_list':<52} | stages_declared")
    print("-" * 92)
    rows = []
    for spelling in spellings():
        track = compact_track(spelling)
        if track is None:
            continue
        print(f"{spelling!r:>12} | {str(track.get('stage_list')):<52} | "
              f"{track.get('stages_declared')}")
        rows.append((spelling, track.get("stage_list"),
                     track.get("stages_declared")))

    # The defect is a stage NAMED AFTER THE MARKER, i.e. the cell survived the
    # split. A mode-default fallback list with `stages_declared: false` is the
    # CORRECT outcome, so the criterion is `stages_declared`, not emptiness.
    declared = [r for r in rows if r[2]]
    named = [r for r in declared if r[1] and len(r[1]) == 1]
    print(f"\n{len(declared)} of {len(rows)} blank spellings were read as a "
          f"DECLARED stage list")
    print(f"{len(named)} of those are a single stage named after the blank marker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
