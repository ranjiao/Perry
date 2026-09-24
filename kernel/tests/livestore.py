"""The live-store check's detection layer (§ 5.7, NN-K9).

`tests/tree_guard.py` hashes the checkout and cannot see inside `.git/`, where
the shared store lives. So the runner reads the live store's highest event seq
before and after the suite, read-only, and looks at every event written in
between. The store is shared by every worktree of the repository, so another
session's legitimate write can land during a run: an event whose actor carries
this run's session fails the suite; any other new event is reported, not
failed (the user's decision on OQ-K4, 2026-09-24).

Reading never creates anything: a store that does not exist is recorded as
absent and is never opened, and one that exists is opened `mode=ro`.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import urllib.parse
from pathlib import Path

KERNEL = Path(__file__).resolve().parents[1]
if str(KERNEL) not in sys.path:
    sys.path.insert(0, str(KERNEL))

from perry_kernel.paths import derived_store  # noqa: E402


def live_store_path(repo: Path):
    """The store a forgotten `--store` would reach from `repo`, or None when
    `repo` is not a project anchor."""
    repo = Path(repo).resolve()
    if not (repo / ".perry").is_dir():
        return None
    return derived_store(repo)


def _connect_ro(path: Path):
    uri = f"file:{urllib.parse.quote(str(path))}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=5.0)


def snapshot(path) -> dict:
    """`{path, exists, max_seq, error}`. Never creates the file or its dir."""
    out = {"path": str(path) if path else None, "exists": False,
           "max_seq": None, "error": None}
    if path is None or not Path(path).exists():
        return out
    out["exists"] = True
    try:
        conn = _connect_ro(Path(path))
        try:
            out["max_seq"] = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM event").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error as exc:
        out["error"] = str(exc)
    return out


def events_after(path, seq: int) -> list[dict]:
    conn = _connect_ro(Path(path))
    try:
        rows = conn.execute("SELECT seq, actor, command, items FROM event "
                            "WHERE seq > ? ORDER BY seq", (seq,)).fetchall()
    finally:
        conn.close()
    out = []
    for s, actor, command, items in rows:
        out.append({"seq": s, "actor": json.loads(actor) if actor else None,
                    "command": command, "items": json.loads(items)})
    return out


def verdict(before: dict, after: dict, session: str) -> tuple[bool, list[str]]:
    """`(ok, report lines)` for one run."""
    lines = []
    if not after["exists"]:
        if before["exists"]:
            return False, [f"the live store {after['path']} existed before the "
                           f"run and is gone after it"]
        return True, [f"live store absent before and after: {after['path']}"]
    if after["error"]:
        return False, [f"the live store {after['path']} could not be read "
                       f"after the run: {after['error']}"]
    start = before["max_seq"] or 0
    if not before["exists"]:
        lines.append(f"the live store {after['path']} appeared during the run")
    if after["max_seq"] == start and before["exists"]:
        return True, [f"live store unchanged at seq {start}: {after['path']}"]
    new = events_after(after["path"], start)
    own = [e for e in new if (e["actor"] or {}).get("session") == session]
    other = [e for e in new if e not in own]
    for e in other:
        lines.append(f"reported, not failed: event {e['seq']} "
                     f"({e['command']}) by session "
                     f"{(e['actor'] or {}).get('session')!r} — another "
                     f"session's write to the shared store")
    for e in own:
        lines.append(f"FAILED: event {e['seq']} ({e['command']}, items "
                     f"{', '.join(e['items']) or '-'}) was written by this "
                     f"run's session {session!r} to the live store")
    if not new and not before["exists"]:
        lines.append("it holds no event")
    return not own, lines
