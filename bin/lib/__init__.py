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


def stage(path: Path, text: str) -> str:
    """Write `text` to a fresh temp file beside `path`, fsynced. Returns its name.

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
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return tmp


def write_atomic(path: Path, text: str) -> None:
    """Replace `path` with `text`, or leave it exactly as it was.

    A reader that opens the file at any moment sees the whole old version or
    the whole new one — `os.replace` is atomic on POSIX — which is the property
    every Perry state file depends on, because the readers are other Perry
    tools and the user's editor, not a database client waiting on a lock.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = stage(path, text)
    try:
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


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


def is_blank_cell(value: str) -> bool:
    """Does this cell mean nothing, in any declared language?"""
    text = (value or "").strip().strip("*`~ ").strip().lower()
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
            _BLANK_CELLS.update(str(v).strip().lower() for v in vals)
        # A schema that cannot be read must not make every cell non-blank:
        # that would report every `—` on the board as a bad value.
        _BLANK_CELLS.update({"—", "-", "–", "n/a", "none", "无"})
    return text in _BLANK_CELLS


#: `3d`, `2w`, `24h` — the shorthand `.perry/config.md § Tracks` writes. Here
#: for the same reason `ISO_DATE_RE` is: `bin/perry-goals` validates `--due`
#: with it and `bin/perry-lint` now checks the column against it, and a typed
#: column whose writer and reader disagree about the value space is the defect
#: this pair was split to remove.
SLA_TOKEN_RE = re.compile(r"^\d+\s*[dwhmy]$", re.I)


def is_sla_token(value: str) -> bool:
    return bool(SLA_TOKEN_RE.match((value or "").strip().strip("*` ")))


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
    text = (value or "").strip().strip("*` ")
    if not ISO_DATE_RE.match(text):
        return False
    try:
        _date.fromisoformat(text)
    except ValueError:
        return False
    return True


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
