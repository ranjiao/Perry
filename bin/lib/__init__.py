"""Primitives every `bin/` tool needs, and each one of them used to rewrite.

`viewer/tables.py` is the precedent and it says why in its own first lines:
five tools already import `parsers`, so `viewer/` is where Perry's shared code
actually is, whatever the directory is called. This is the same argument one
directory over. `tables.py` serves the **readers**; the four functions here
serve the **tools** — how a Perry tool finds a project's state on disk
(`resolve_state_root`), keeps another tool out of it while it works
(`project_lock`), writes it without a torn file (`write_atomic`), and learns
what shape it is supposed to be (`load_schema`).

**The measurement that produced this module, and the argument for it.** Six
primitives had fourteen-plus implementations across `bin/`, and the count grew
inside a single commit: `ef16733` re-imported `fcntl`, `tempfile` and
`contextlib` and rebuilt three of them locally. That same commit imported
`render_row`, `split_row` and `squash` from `viewer/tables.py` rather than
writing a fifth cell writer. **One extraction stopped one duplication; the
primitives nobody extracted gained three implementations in one commit.** The
path of least resistance is whatever is importable, so the fix is to make these
importable rather than to ask people not to retype them.

**Each tool keeps its own `Refused`.** These functions take the exception class
to raise rather than defining one here, because a shared `Refused` would make
`perry-task`'s `except Refused` start catching refusals raised inside
`perry-conform` when one tool loads another — a real change in control flow,
and this extraction is supposed to change none.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import sys
import tempfile
import time
import re
import stat
from datetime import date as _date
from pathlib import Path

#: `bin/lib/` → `bin/` → the install. Every tool computes `PERRY_HOME` the same
#: way from its own location, and honours the same override, so a tool and the
#: library it imports can never disagree about which install they are in.
HERE = Path(__file__).resolve().parent
PERRY_HOME = Path(os.environ.get("PERRY_HOME") or HERE.parent.parent).resolve()
SCHEMA_PATH = PERRY_HOME / "schema" / "state-schema.json"


# ── writing ───────────────────────────────────────────────────────────────


def stage(path: Path, text: str | bytes) -> str:
    """Write text/bytes to a fresh temp file beside `path`, fsynced.

    Returns its name.

    Split out of `write_atomic` for `perry-task § commit`, which stages **two**
    files before renaming either — `BOARD.md` and the journal land together or
    not at all — and so cannot be expressed as two `write_atomic` calls. It
    carried its own inline copy of this body for that reason; the reason was
    real and the copy was not necessary.

    The temp name comes from `mkstemp`, not from `path.with_suffix(".tmp")`,
    which is the difference between the two implementations this replaces:

    - **it is unique.** A fixed `BOARD.md.tmp` is a name two concurrent writers
      collide on, and the loser's bytes end up in the winner's file.
    - **it is cleaned up.** On any failure the temp is unlinked. The fixed-name
      version left `BOARD.md.tmp` sitting in the user's project — untracked,
      unignored, and indistinguishable from something they should keep.
    - **it is fsynced before the rename**, so the rename cannot publish a file
      whose contents are still in the page cache after a crash.
    """
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        # `mkstemp` deliberately creates 0600 files. That is right for a new
        # secret and wrong for replacing an existing tracked document: the
        # rename would silently change a 0644 BOARD.md, journal, or store to
        # 0600. The replacement inherits the target's current permission bits.
        if path.exists():
            os.fchmod(fd, stat.S_IMODE(path.stat().st_mode))
        mode = "wb" if isinstance(text, bytes) else "w"
        with os.fdopen(fd, mode) as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return tmp


def write_atomic(path: Path, text: str | bytes) -> str:
    """Replace `path` with text/bytes and return the published SHA-256.

    A reader that opens the file at any moment sees the whole old version or
    the whole new one — `os.replace` is atomic on POSIX — which is the property
    every Perry state file depends on, because the readers are other Perry
    tools and the user's editor, not a database client waiting on a lock. The
    digest identifies the staged image, so a caller can distinguish its own
    write from a non-cooperating edit that lands immediately afterwards.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = stage(path, text)
    try:
        published = hashlib.sha256(Path(tmp).read_bytes()).hexdigest()
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return published


def sync_directory(path: Path) -> None:
    """Fsync a directory after durable-name changes, where the OS supports it."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


# ── locking ───────────────────────────────────────────────────────────────


@contextlib.contextmanager
def project_lock(state_root: Path, timeout: float = 10.0,
                 refused: type[BaseException] = RuntimeError):
    """One lock per project, not one per lane. Serializes read-modify-write.

    **Why the whole read-modify-write and not just the write.** `BOARD.md` is
    read when the board is loaded and written when it is committed, and between
    those two points another process can do the same thing — the second rename
    then discards the first process's row entirely. Measured, not theorized:
    five concurrent `add` calls left **two** rows on the board, with `TASK-001`
    and `TASK-002` each issued twice. The event log took all five, because it
    is opened `O_APPEND`; the append-only file survived exactly the race the
    read-modify-write document lost. A lock around the write alone would still
    let both processes mint the same id from the same stale board.

    **Why one key for every lane.** A `decide` write and a `goals` write and a
    `work` write touch different files and the same project, and a reader that
    catches them mid-flight sees a state no lane intended (DESIGN-005 § 5.4).
    So the key is the state root, and the four writers queue behind each other.

    **Why the lock file lives in the temp dir.** Two earlier placements each
    broke something real:

    - in `.perry/` — an unwritable `.perry/` made the lock uncreatable and
      refused the whole call, even though `BOARD.md` and the journal were both
      writable. The design's entire claim is that `.perry/` is derived and can
      never make Perry *wrong*.
    - beside `BOARD.md` — it then appears in the project, and a consumer repo
      does not inherit Perry's own `.gitignore`. Checked on a real Perry
      project the same night it shipped: `?? .board.lock`, untracked and
      unignored. A tool that makes every user edit their `.gitignore` to stay
      clean has pushed its own bookkeeping onto them.

    It is also not `flock` on `BOARD.md` itself: the commit renames a temp file
    over it, so every writer after the first would hold a lock on a replaced
    inode and exclusion would quietly stop working. A file outside the tree,
    never renamed, keyed by the path it guards, is the one shape that survives
    all three — and losing it between reboots costs nothing, because it only
    ever means "no one is writing right now", which is true after a reboot.
    """
    key = hashlib.sha1(str(state_root.resolve()).encode()).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"perry-task-{key}.lock"
    fh = open(lock_path, "w")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    # "another Perry write", not "another perry-task": the key
                    # is the project, so the holder is as often `goals` or
                    # `decide` as it is the tool printing this line.
                    raise refused(
                        f"another Perry write is holding {lock_path} and did "
                        f"not release it within {timeout:.0f}s. Nothing was "
                        f"written; retry, or remove the file if no process is live")
                # Without this the wait is a busy spin at 100% of a core for
                # the full timeout. One of the four copies had lost it.
                time.sleep(0.05)
        yield
    finally:
        # Suppressed, not propagated: the fd is closed on the next line and
        # closing releases the lock anyway, so a failure to unlock is not worth
        # replacing whatever exception the body was already raising.
        with contextlib.suppress(OSError):
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


# ── the shape ─────────────────────────────────────────────────────────────


#: **The one spelling of "is this cell a date", anchored.** It lives here and
#: not in a tool because two tools ask it: `bin/perry-goals` validates `--due`
#: with it and `bin/perry-diagnose` counts dated promises with it.
#:
#: TASK-091 anchored the goals copy and wrote above it "the one spelling",
#: which was false the moment it was written — `bin/perry-diagnose` kept a
#: second one that `search`ed, so `2026-09-30 or so` was refused by the writer
#: and counted as a dated promise by the reader. **The same value, two
#: answers, in the tool pair whose whole job is to agree.** Found by a V4 that
#: read the commit's claim and then grepped for the property rather than
#: trusting the diff.
#:
#: Anchored because a typed field asks whether the WHOLE cell is a date. A
#: cell with a date buried in prose is prose, and prose goes in
#: `By when note`.
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


#: Values meaning "this cell says nothing", from `schema § i18n.blank_cell`.
#: Read from the schema rather than written here, so a new language is a schema
#: edit. Three tools carried three different hardcoded lists and only one of
#: them had 无 — see the schema note for what that cost.
_BLANK_CELLS: set = set()


def normalize_typed_cell(value: str) -> str:
    """Normalize presentation around a typed cell, never its interior."""
    return (value or "").strip().strip("*`~ ")


def _blank_key(value: str) -> str:
    """Case/punctuation-insensitive key for one declared unfilled idiom."""
    return normalize_typed_cell(value).strip().lower().rstrip(".。!！?？").strip()


def is_blank_cell(value: str) -> bool:
    """Does this cell mean nothing, in any declared language?"""
    text = _blank_key(value)
    if not text:
        return True
    if not _BLANK_CELLS:
        try:
            blank = (load_schema().get("i18n") or {}).get("blank_cell") or {}
        except Exception:                                        # noqa: BLE001
            blank = {}
        for key, vals in blank.items():
            if key == "note" or not isinstance(vals, list):
                continue
            _BLANK_CELLS.update(_blank_key(str(v)) for v in vals)
        # A schema that cannot be read must not make every cell non-blank:
        # that would report every `—` on the board as a bad value.
        _BLANK_CELLS.update(_blank_key(v) for v in
                            {"—", "-", "–", "n/a", "none", "无"})
    return text in _BLANK_CELLS


#: `3d`, `2w`, `24h` — the shorthand `.perry/config.md § Tracks` writes. Here
#: for the same reason `ISO_DATE_RE` is: `bin/perry-goals` validates `--due`
#: with it and `bin/perry-lint` now checks the column against it, and a typed
#: column whose writer and reader disagree about the value space is the defect
#: this pair was split to remove.
SLA_TOKEN_RE = re.compile(r"^\d+\s*[dwhmy]$", re.I)


def is_sla_token(value: str) -> bool:
    return bool(SLA_TOKEN_RE.fullmatch(normalize_typed_cell(value)))


def is_iso_date(value: str) -> bool:
    """Does this cell hold exactly one REAL ISO date, decoration stripped?

    **The calendar, not only the shape.** `2026-13-45` and `2026-02-30` match
    the pattern and are not days. `bin/perry-goals § real_date` had always
    parsed as well as matched, so the writer refused them; a shape-only reader
    accepted them, and a sweep of sixteen values across the writer and the file
    check found exactly these two disagreeing.

    Three callers then do `date.fromisoformat(seen)` on the strength of this
    answer — `perry-lint`, `perry-knowledge`, `perry-state`, all on a knowledge
    card's `Last verified`. A shape-only `True` handed each of them a
    `ValueError` on a hand-typed card.
    """
    text = normalize_typed_cell(value)
    if not ISO_DATE_RE.fullmatch(text):
        return False
    try:
        _date.fromisoformat(text)
    except ValueError:
        return False
    return True


DUE_UNFILLED = "unfilled"
DUE_DATE = "date"
DUE_DURATION = "sla"
DUE_INVALID = "invalid"
DUE_PIPELINE_REQUIRES_DATE = "pipeline-requires-date"
DUE_QUEUE_MISSING_CLOCK = "queue-missing-sla"


def due_track_missing_clock(track: dict | None) -> bool:
    track = track or {}
    return (str(track.get("mode") or "project").strip().lower() == "queue"
            and is_blank_cell(str(track.get("sla") or "")))


def classify_due(track: dict | None, value: str) -> str:
    """Classify one `Due` cell under the track contract that governs it.

    This returns semantics rather than a writer refusal. The writer, lint, and
    migration need different actions for the same answer, but none gets to
    implement a different value space.
    """
    if is_blank_cell(value):
        return DUE_UNFILLED

    track = track or {}
    mode = str(track.get("mode") or "project").strip().lower()
    if is_iso_date(value):
        if due_track_missing_clock(track):
            return DUE_QUEUE_MISSING_CLOCK
        return DUE_DATE
    if is_sla_token(value):
        if due_track_missing_clock(track):
            return DUE_QUEUE_MISSING_CLOCK
        if mode == "pipeline":
            return DUE_PIPELINE_REQUIRES_DATE
        return DUE_DURATION
    return DUE_INVALID


def due_is_valid(track: dict | None, value: str) -> bool:
    """Whether `value` is a populated `Due` allowed by `track`."""
    return classify_due(track, value) in {DUE_DATE, DUE_DURATION}


def load_schema(refused: type[BaseException] = RuntimeError) -> dict:
    """`schema/state-schema.json`, or the caller's refusal.

    **This is the raising contract, and it is not the only one in `bin/`.**
    The five writers share it: a tool about to change a user's state file and
    unable to read the shape it must write cannot guess, so it refuses. The
    read side deliberately does the opposite — `perry-state`, `perry-explain`
    and `perry-diagnose` catch `(OSError, ValueError)` and fall back to a
    default, because a reporting tool that crashes on a missing schema is worse
    than one that reports slightly less. `perry-lint` prints and exits 2.

    Those are three different contracts, not three copies of this one, which is
    why only the five writers import this.
    """
    if not SCHEMA_PATH.exists():
        raise refused(f"schema not found at {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text())


# ── where the state lives ─────────────────────────────────────────────────


_PARSERS = None


def _parsers():
    """`viewer/parsers.py`, imported the way every tool in `bin/` imports it.

    Deferred to first call rather than done at module import, so a tool that
    only wants `write_atomic` does not pay for the largest module in the repo.
    """
    global _PARSERS
    if _PARSERS is None:
        viewer = str(PERRY_HOME / "viewer")
        if viewer not in sys.path:
            sys.path.insert(0, viewer)
        import parsers
        _PARSERS = parsers
    return _PARSERS


def resolve_state_root(project_root: Path) -> Path:
    """Where this project's Perry state files live.

    **The implementation is `viewer/parsers.py`'s and stays there**, because
    that is where every other reader already gets it — `perry-lint`,
    `perry-state`, `perry-task`, `perry-goals`, `perry-decide`, `perry-conform`,
    `perry-knowledge` and `perry-migrate` all call `P.resolve_state_root`. This
    is a re-export so that `bin/` has one import site rather than one function
    with two bodies; it is not a second implementation and must never become
    one.

    `perry-diagnose` carried the second body, described in its own docstring as
    a mirror "kept minimal so this script has no import dependency on the
    viewer" — a reason that had already stopped being true, since the same file
    imports `split_row` and `squash` from `viewer/tables.py` fourteen lines
    below where it computes `PERRY_HOME`.
    """
    return _parsers().resolve_state_root(project_root)


# ── what a KR's `current` actually is ─────────────────────────────────────
#
# `phase/<NNN>-linkage.md` carries `target` and `current` per KR, both
# hand-written, and until TASK-120 nothing derived, checked or aged them. Two
# readings on Perry's own register on 2026-08-21 were wrong in OPPOSITE
# directions and neither payload could say so:
#
#   P-O1.1  target 1, current 0  → read as 0% while all four linked tasks
#                                  were closed and the board WAS rendered
#                                  from the store;
#   P-O2.2  target 0, current 0  → read as MET while TASK-094 had measured
#                                  13 row splits and 87 header resolutions
#                                  still reaching `BOARD.md`.
#
# Six of the register's eight phase KRs have `target: 0`, so any KR whose
# `current` is left at the template's `0` reads as met the day it is written.
#
# **The line this code does not cross.** It never computes `current`. A KR's
# metric is typically a count of something in the repository — P-O2.1's is "0
# occurrences of the regex TASK-091 deleted" — and "the linked task is closed"
# does not establish that the count is zero; only re-running the count does.
# `perry/OKR.md § Operating Principles` opens with that rule, and the phase's
# own Definition of Done is a `grep -c` over `bin/`, which is why this comment
# does not name the symbol. So the linked-task tally below is emitted
# BESIDE `current`, under its own name, as a count of tasks and never as a
# fraction: a reader may put the two side by side and conclude the number is
# suspect, which is exactly the P-O1.1 reading, but nothing here draws that
# conclusion for them.

#: `schema/state-schema.json § enums.task_status`, restated rather than read so
#: this module has no load-order dependency on the schema file — and pinned to
#: it by `tests/test_kr_progress_provenance.py`, so the two cannot drift.
TASK_STATUSES = frozenset((
    "not_started", "blocked", "in_progress", "review", "done", "dropped"))

#: `bin/perry_store.py § TERMINAL_STATUSES`, and `viewer/parsers.py`'s copy of
#: the same set. Same pin, same test.
CLOSED_STATUSES = frozenset(("done", "dropped"))

#: Events whose `to` is a task status are state moves. `next`, `evidence` and
#: `rung` also carry `from`/`to`, holding prose, a file path and a rung — which
#: is why this filters on the VALUE rather than on the event name: a new event
#: kind that moves status is picked up, and a new one that does not cannot
#: sneak in by being named plausibly.
def _is_state_move(event: dict) -> bool:
    return str(event.get("to") or "") in TASK_STATUSES


def _ts_key(value: str) -> str:
    """A timestamp reduced to something two of them can be compared on.

    The register writes `updated` as an ISO datetime with a `Z`; the event log
    writes `ts` as a naive local datetime with no zone at all. There is no
    conversion that is honest between those two, so the `Z` is STRIPPED rather
    than applied — stated here because it means a register written within a few
    hours of a task move can order wrongly, and a reader is entitled to know
    that before trusting a `stale: false`.

    A date-only value becomes midnight, which errs toward reporting staleness:
    a false "recheck this" costs a look, and a false "this number is fine"
    costs the number.
    """
    text = str(value or "").strip().rstrip("Z")
    if not text:
        return ""
    if len(text) == 10:          # YYYY-MM-DD
        return text + "T00:00:00"
    return text


def task_status_index(state_root, board=None) -> dict:
    """`id` → status, from the STORE first and the projection second.

    `board.all_tasks` alone is not enough on an adopted project. The store's
    projection deliberately drops every closed row — `viewer/parsers.py §
    _records_by_group` skips a terminal status, because a closed row leaves
    `BOARD.md` — so a KR every one of whose tasks is finished would see none of
    them and report them all as unknown. `tasks.jsonl` keeps them, and it is
    the canonical side, so it wins where the two are both present.

    A project with no store has only the markdown, and there a closed row
    really is gone from the board. That is what the event log is asked about
    afterwards, in `kr_progress_provenance`.
    """
    out: dict[str, str] = {}
    for task in (getattr(board, "all_tasks", None) or []):
        if getattr(task, "id", ""):
            out[task.id] = task.status or ""
    for record in (_parsers().load_task_store(Path(state_root)) or []):
        if record.get("id"):
            out[str(record["id"])] = str(record.get("status") or "")
    return out


def kr_progress_provenance(current, task_ids, *, register_updated: str = "",
                           status_by_id: dict | None = None,
                           events: list | None = None,
                           events_present: bool = False) -> dict:
    """The three blocks that go beside a KR's `target` / `current`.

    Returns `current_provenance`, `current_staleness` and
    `linked_task_completion` — computed once, here, because `bin/perry-state`
    and `bin/perry-goals` both emit them and a second implementation is how the
    two would come to disagree about whether a number is stale.

    `current` is `None` for a KR the register never gave a number, and that is
    reported as `unasserted` rather than as `0.0`. The default matters more
    than it looks: with six of eight phase KRs driving a count to zero, a
    `current` defaulted to `0` reads as **met before the work starts**.
    """
    status_by_id = status_by_id or {}
    events = events or []
    ids = [str(t) for t in (task_ids or [])]

    asserted = current is not None
    provenance = {
        # What the number IS, not how good it is.
        "state": "asserted" if asserted else "unasserted",
        # Always false, and emitted rather than implied. No tool in Perry
        # re-runs a KR's metric, so no `current` it publishes is a measurement.
        # A future tool that does re-run one sets this true; until then a
        # consumer that wants to show "measured" has an explicit answer.
        "measured": False,
        "source": "linkage-register" if asserted else "",
        # The register timestamps ITSELF, not each KR. A reader must not take
        # this for the date this KR's number was arrived at, so the granularity
        # is emitted with the date.
        "asserted_at": _ts_key(register_updated) if asserted else "",
        "asserted_scope": "register" if asserted else "",
    }

    # ── the tally that is NOT progress ────────────────────────────────────
    # A task closed after `perry-task done` may be off `BOARD.md` entirely, so
    # the board is asked first and the event log second. An id neither knows is
    # `unknown` — never silently counted as open, which would report a dangling
    # edge as work outstanding.
    last_status: dict[str, str] = {}
    for event in events:
        if _is_state_move(event) and event.get("id"):
            last_status[str(event["id"])] = str(event["to"])
    tally = {"total": len(ids), "done": 0, "dropped": 0, "open": 0, "unknown": 0}
    for tid in ids:
        status = str(status_by_id.get(tid) or "") or last_status.get(tid, "")
        if status == "done":
            tally["done"] += 1
        elif status == "dropped":
            tally["dropped"] += 1
        elif status in TASK_STATUSES:
            tally["open"] += 1
        else:
            tally["unknown"] += 1

    # ── staleness ─────────────────────────────────────────────────────────
    # This is the linkage edge finally being read: not to compute the metric,
    # but to know when the number can no longer be trusted.
    since = provenance["asserted_at"]
    staleness = {"stale": False, "evaluated": False, "reason": "",
                 "since": since, "moved_tasks": []}
    if not asserted:
        staleness["reason"] = (
            "`current` was never asserted, so there is nothing to go stale")
    elif not since:
        staleness["reason"] = (
            "the register states no `updated` timestamp, so staleness cannot "
            "be evaluated")
    elif not events_present:
        staleness["reason"] = (
            "no event log, so whether a linked task has moved since "
            f"{since} cannot be evaluated")
    elif not ids:
        staleness["evaluated"] = True
        staleness["reason"] = "the register links no task to this KR"
    else:
        staleness["evaluated"] = True
        wanted = set(ids)
        moved: dict[str, dict] = {}
        for event in events:
            tid = str(event.get("id") or "")
            if tid not in wanted or not _is_state_move(event):
                continue
            at = _ts_key(event.get("ts", ""))
            if not at or at <= since:
                continue
            # Last move wins, so a task that moved twice is named once with
            # where it ended up.
            moved[tid] = {"id": tid, "from": str(event.get("from") or ""),
                          "to": str(event["to"]), "at": at}
        staleness["moved_tasks"] = [moved[t] for t in ids if t in moved]
        if moved:
            staleness["stale"] = True
            named = ", ".join(
                f"{m['id']} ({m['from'] or 'created'} → {m['to']})"
                for m in staleness["moved_tasks"])
            staleness["reason"] = (
                f"{len(moved)} linked task"
                f"{'s' if len(moved) != 1 else ''} changed state after "
                f"{since}: {named}")
        else:
            staleness["reason"] = (
                f"no linked task has changed state since {since}")

    return {"current_provenance": provenance,
            "current_staleness": staleness,
            "linked_task_completion": tally}


# ── the one question a dashboard asks ─────────────────────────────────────
#
# TASK-148. `bin/perry-task` stated this rule **twice**, ~200 lines apart, once
# in `_cmd_list_from_board` and once in `cmd_list`, and both are reachable.
# TASK-141 had to fix the rule and discovered it had to fix it twice — which is
# the two-readers-of-one-rule failure `schema/task-list-contract.md` warns about
# in its own prose, inside the tool that contract describes.
#
# **This is a move, not an edit.** The rule below is TASK-141's, unchanged; its
# evidence records three days of argument about the exception, and a behaviour
# change smuggled into a de-duplication is the hardest kind to review. Both
# payloads were diffed before and after the move and differ in nothing.

#: A row in one of these waits on somebody ELSE, so its own dependency list
#: being empty does not make it startable.
#:
#: `review` waits on a HUMAN — no dependency edge can ever contradict it, which
#: is why the `blocked_stale` exception below reaches `blocked` and not this.
WAITING_ON_SOMEBODY_ELSE = frozenset(("blocked", "review"))


def resolve_startability(tasks) -> None:
    """Set `blocked_stale` and `startable` on every task, in place.

    Takes the rows AFTER `blocked_by` has been computed — this decides nothing
    about the graph, it reads the graph against the stored `status`. Called by
    both of `bin/perry-task`'s list paths, which is the whole point of it
    living here rather than in either one of them.

    A row whose own `Status` says it is waiting is not startable however empty
    its dependency list is; `blocked` and `review` both mean somebody else has
    the ball. That is what makes this field answer the question a user actually
    asks ("I saw a pile of `review` rows and thought they could be advanced")
    on a board with not one declared edge on it.

    **With one exception, because the stored status was masking the graph.** A
    row that says `blocked`, declares dependencies, and has NONE of them left
    unsatisfied is not stating a fact — it is CONTRADICTING one already
    computed. Measured on Perry's own board: TASK-037 (waiting on TASK-092) and
    TASK-045 (on the closed TASK-044 → TASK-047 chain) both reported
    `blocked_by=[]` and `startable=False` in the same object, because `status`
    was read first and `startable` could never disagree with a stale cell.
    `done` does not touch its dependents, so the ordinary close path CREATES
    that state and the old ordering then hid it.

    `blocked_stale` names the disagreement rather than swallowing it, and
    `startable` stops deferring to the stored value on exactly those rows. The
    stored `Status` is left alone: `list` reads, and rewriting a cell nobody
    asked it to rewrite is a different decision than reporting the truth about
    it. So the row becomes startable and STILL reads `blocked` until a human or
    a subsequent write clears it.

    Three boundaries this deliberately does NOT cross:

    - a row with at least one dependency still open keeps `blocked_by`
      non-empty and stays unstartable. This is not "drop the check".
    - a `blocked` row that declares NO dependency is untouched. Its dependency
      is in prose Perry cannot read — that is precisely
      `conformance.blocked_without_dependency` — and "I cannot see it" is not
      "it closed", the same rule that makes an unknown id unsatisfied.
    - `review` is untouched, for the reason `WAITING_ON_SOMEBODY_ELSE` gives.
    """
    for task in tasks:
        task["blocked_stale"] = bool(
            task["open"] and task["status"] == "blocked"
            and task["depends_on"] and not task["blocked_by"])
        task["startable"] = bool(
            task["open"] and not task["blocked_by"]
            and (task["blocked_stale"]
                 or task["status"] not in WAITING_ON_SOMEBODY_ELSE))
