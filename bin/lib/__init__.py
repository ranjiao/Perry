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
another tool it loads — a real change in control flow,
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
from datetime import datetime as _datetime
from datetime import timezone as _timezone
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


_BLANK_MARKER: str | None = None


def blank_marker() -> str:
    """How this project's files spell "this cell says nothing": `—`.

    `schema § i18n.blank_cell.en`, first entry — the same list `is_blank_cell`
    matches against, so the spelling this hands back cannot become one that
    function would not recognise. It lives here rather than in a caller because
    three of them need it: `bin/perry-state § track_from_record` puts the marker
    back on a stored blank, `stored_settings` does the same for a setting, and
    `perry_md_store § scaffold_config` writes it into a file being rebuilt from
    the store with no file on disk to copy it from.
    """
    global _BLANK_MARKER
    if _BLANK_MARKER is None:
        try:
            blank = (load_schema().get("i18n") or {}).get("blank_cell") or {}
            en = [v for v in (blank.get("en") or []) if isinstance(v, str)]
        except Exception:                                        # noqa: BLE001
            en = []
        _BLANK_MARKER = en[0] if en else "\u2014"
    return _BLANK_MARKER


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
SLA_TOKEN_RE = re.compile(r"^(\d+)\s*([dwhmy])$", re.I)


def is_sla_token(value: str) -> bool:
    return bool(SLA_TOKEN_RE.fullmatch(normalize_typed_cell(value)))


def parse_sla(value: str) -> tuple[int, str] | None:
    """`5d` → `(5, "d")`, `2w` → `(2, "w")`. `None` if it is not the token.

    **The groups on `SLA_TOKEN_RE` are the whole point.** The breach step in
    `modes/queue.md § Triage in this mode` measures `today − Arrived` against
    `.perry/config.md § Tracks` → `SLA`, and the only thing that had ever read
    an SLA cell was `classify_due` above — which asks whether the cell *is* a
    duration and never what duration it is. A second reader would have needed a
    second spelling of `<n><unit>`, and this repository has now paid three
    times for a writer and a reader with separate copies of one format (column
    order, the period table, the stage separators). So the pattern gains two
    groups and stays one pattern; `is_sla_token` is unchanged by it, and the
    anchors `tests/test_goals_writer.py` asserts on are still the first and
    last characters.
    """
    m = SLA_TOKEN_RE.fullmatch(normalize_typed_cell(value))
    if not m:
        return None
    return int(m.group(1)), m.group(2).lower()


def sla_deadline(arrived: _date, value: str) -> _date | None:
    """The last day an arrival is still inside `value`. `None` if unreadable.

    Calendar arithmetic is `viewer/parsers.py § advance` — the same function
    `perry-task cadence-done` stamps `Next due` with — so a month is a calendar
    month here for the reason it is one there: `modes/queue.md` says outright
    that **`5d` means five calendar days**, and a 30-day month would move a
    month-end promise off month-end.

    Two unit conversions, both stated rather than assumed:

    - `y` is 12 months, which is what `parse_frequency` already does with it.
    - `h` is rounded **up** to whole days. `Arrived` is a date, so a clock with
      no time of day cannot resolve `4h`; rounding up is the direction that
      refuses to report a breach the recorded data cannot prove, and it is the
      only direction that keeps `24h` meaning one day.
    """
    parsed = parse_sla(value)
    if parsed is None:
        return None
    n, unit = parsed
    if unit == "h":
        n, unit = -(-n // 24), "d"
    elif unit == "y":
        n, unit = n * 12, "m"
    return _parsers().advance(arrived, n, unit)


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


# ── which project, and what the caller actually typed ─────────────────────


def empty_root_error(flag: str, value: str | None) -> str | None:
    """The refusal `--root ""` earns, or `None` when the value is usable.

    **An empty `--root` is a bad invocation, not a default.**
    `resolve_project_root` below tests truthiness, so `--root ""` fell through
    to `$PERRY_PROJECT` and then to the walk up from the cwd: `perry-task add
    --root "$PROJ" …` with `PROJ` unset exited 0 having written into whichever
    project the cwd resolves to, while the one the caller named was untouched.
    That is DESIGN-016 § 1.1's own defect reached through the commonest shell
    idiom there is.

    **Why this is a function and not a line.** The refusal shipped inside
    `parse_surface`, which only the six surface-declaring tools call, so it
    reached six of the fourteen `--root` readers and a V4 round measured the
    other eight still resolving the cwd's project — `perry-goals commit …
    --root ""` run from inside a different project wrote `OKR.md`, `okr.jsonl`
    and `.perry/events.jsonl` there. Fourteen tools parse their own argument
    vector for reasons `parse_surface`'s docstring gives; what they must not
    each own is *what counts as empty* and *what the caller is told*. Both
    live here, and every caller asks rather than answers.

    Callers pass the flag they are holding, so a value loop can ask about
    every flag it reads without knowing which one this rule is about.
    """
    if flag == "--root" and value == "":
        return ("--root was given an empty value. If that came from a shell "
                "variable, the variable is unset")
    return None


def resolve_project_root(explicit: str | os.PathLike | None = None, *,
                         walk: bool = True) -> Path:
    """The project a tool acts on: `--root`, then `$PERRY_PROJECT`, then the cwd.

    **That order is the published contract and three tools had it inverted.**
    `bin/README.md § Which project?` states it, ADR-002 is why it exists, and
    `bin/perry_md_store § main`, `bin/perry-tasks § main` and `bin/perry-config
    § main` all read the environment AFTER the flag, so `$PERRY_PROJECT` won.
    Measured 2026-09-04 (DESIGN-016 § 1.1): in an empty directory with
    `PERRY_PROJECT` pointing at this repository, `perry-tasks build --root
    <empty>` reported 352 stored records — the other project's — while
    `perry-task list --root <empty>` on the same invocation correctly reported
    0. Those three tools include two writers, so the failure was not a wrong
    read; it was a write landing in a project the caller did not name.

    `walk` is the difference between the tools that judge a project and the one
    tool that judges a *directory*: `perry-diagnose` stops at the cwd on
    purpose, so that pointing it at a folder with no state reports "no state
    here" rather than answering about an ancestor. Every other tool walks up,
    and the predicate is `viewer/parsers § _resolve_project_root`'s, called
    rather than copied — `tests/test_project_root.py` exists because that walk
    had two bodies once.
    """
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("PERRY_PROJECT")
    if env:
        return Path(env).expanduser().resolve()
    cur = Path.cwd().resolve()
    if not walk:
        return cur
    for d in [cur, *cur.parents]:
        if (_parsers().configured(d) or (d / "BOARD.md").exists()
                or (d / "OKR.md").exists()):
            return d
    return cur


# ── the declared surface ─────────────────────────────────────────────────
#
# **One declaration per tool, in the tool, and the parser is driven by it.**
# DESIGN-016 Decision 5, answered 2026-09-09. There is no `bin/commands.json`
# and there is no dispatcher holding a second copy of the list: a tool that
# already keeps a flag table is the only place the fact belongs, and everything
# else — `--describe --json`, `bin/perry list`, the generated usage block, the
# README table — reads it from there.
#
# The shape, and it is deliberately JSON-native so `--describe` is a dump:
#
#     SURFACE = {
#       "name": "perry-tasks", "kind": "write" | "read" | "cache-only",
#       "summary": "one line",
#       "root_resolution": "standard" | "cwd" | "none",
#       "exit_codes": {"0": "...", "1": "...", "2": "..."},
#       "flags": [{"name": "--root", "arg": "path", "summary": "...",
#                  "repeatable": False, "required": False}],
#       "subcommands": [{"name": "build", "summary": "...",
#                        "flags": ["--root"], "writes": []}],
#     }
#
# A flag is described ONCE in `flags` and referenced by name from each
# subcommand that accepts it. That reference list is goal 12: a flag reaching a
# subcommand that would drop it is refused rather than ignored, which is the
# defect `--kr` and `--design` shipped twice (DESIGN-016 § 1.4).

#: Flags every tool takes, so nineteen declarations do not each restate them.
COMMON_FLAGS = (
    {"name": "--root", "arg": "path", "summary":
     "the project to act on; else $PERRY_PROJECT, else the walk up from cwd"},
    {"name": "--help", "summary": "print usage and exit, from any position"},
    # `--describe --json` is TASK-396's ask, and it is the same table the
    # parser above reads rather than a second description of it. It answers
    # about the whole tool, or about one subcommand when one is named.
    {"name": "--describe", "summary":
     "print this tool's declared surface as JSON and exit; name a subcommand "
     "for that subcommand alone"},
)


def surface_flags(surface: dict) -> dict:
    """`{flag name: its declaration}`, common flags included."""
    out = {f["name"]: f for f in COMMON_FLAGS}
    out.update({f["name"]: f for f in surface.get("flags", ())})
    return out


def always_accepted(surface: dict) -> set[str]:
    """Flags every subcommand of THIS tool takes, plus the common ones.

    `perry-task --json` is the example the shape was found on: it chooses the
    OUTPUT format in `main` and no handler reads it, so deriving each
    subcommand's flags from what its handler reads leaves it out of all thirty
    — and `add --json`, which every caller in the suite passes, becomes a
    refusal. A flag the tool honours everywhere is declared once, here, rather
    than repeated thirty times or quietly exempted from the check.
    """
    return ({f["name"] for f in COMMON_FLAGS}
            | set(surface.get("universal_flags", ())))


def subcommand_flags(surface: dict, item: dict) -> list[str]:
    """Every flag `item` accepts: what it declares, plus what the tool honours
    everywhere.

    **One builder because there were three, and only one of them was
    compared.** `describe_surface` spelled this for the whole-tool payload and
    again for the single-subcommand payload; `usage_lines` spelled it a third
    time and got the operator precedence wrong. A V4 round emptied the second
    one and the whole suite stayed green while `perry describe task add`
    reported that `add` takes 0 flags instead of 27 — which is the branch
    `bin/README.md` publishes as the way to ask about one subcommand.

    Callers that need to hide `--help` and `--describe` from a usage line
    subtract them from the RESULT; doing it inside an expression with `|` is
    how the third spelling went wrong.
    """
    return sorted(set(item.get("flags", ())) | always_accepted(surface))


def surface_subcommand(surface: dict, name: str) -> dict | None:
    return next((s for s in surface.get("subcommands", ())
                 if s["name"] == name), None)


def check_surface(surface: dict) -> list[str]:
    """Findings, empty when the declaration is internally consistent.

    Held by `tests/test_bin_surface.py` rather than trusted: a subcommand that
    references a flag nobody declared would parse as "unknown flag" at runtime
    and read as a typo in the caller's command rather than in this table.
    """
    findings: list[str] = []
    declared = surface_flags(surface)
    for key in ("name", "kind", "summary", "root_resolution", "subcommands"):
        if key not in surface:
            findings.append(f"the declaration has no {key!r}")
    if surface.get("kind") not in (None, "read", "write", "cache-only"):
        findings.append(f"kind {surface['kind']!r} is not read/write/cache-only")
    seen: set[str] = set()
    for sub in surface.get("subcommands", ()):
        if sub["name"] in seen:
            findings.append(f"{sub['name']!r} is declared twice")
        seen.add(sub["name"])
        for flag in sub.get("flags", ()):
            if flag not in declared:
                findings.append(
                    f"{sub['name']} accepts {flag}, which no `flags` entry "
                    f"declares")
    for flag in surface.get("flags", ()):
        if flag["name"] in {f["name"] for f in COMMON_FLAGS}:
            findings.append(f"{flag['name']} is already a common flag")
    for flag in surface.get("universal_flags", ()):
        if flag not in declared:
            findings.append(f"{flag} is universal and no `flags` entry "
                            f"declares it")
    return findings


def parse_surface(surface: dict, argv: list[str]) -> dict:
    """Read `argv` against the declaration. Nothing is dispatched until it is.

    Returns `{"help", "sub", "values", "seen", "extra", "error"}`. `error` is a
    ready-made message and is `None` when the vector is legal.

    Three refusals, and the third is the one that is new (goal 12):

    * a token that starts with `-` and no `flags` entry declares — a typo;
    * a subcommand no `subcommands` entry declares, with the legal set named;
    * a DECLARED flag on a subcommand that does not list it. `perry-task add
      --design` was accepted by a flat 46-flag table and dropped by `cmd_add`,
      so the row it wrote carried no design edge and nothing said so.
    """
    declared = surface_flags(surface)
    subs = {s["name"]: s for s in surface.get("subcommands", ())}
    out: dict = {"help": False, "describe": False, "sub": None, "values": {},
                 "seen": set(), "extra": [], "error": None}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--":
            # Everything after `--` is a VALUE, verbatim, however it is spelled
            # — `perry-config set "Chat language" -- --weird`. It ends the flag
            # scan for the tokens after it and for nothing else: an undeclared
            # flag BEFORE the `--` is still the typo it was.
            out["extra"].extend(argv[i + 1:])
            break
        if token in ("-h", "--help"):
            out["help"] = True
        elif token == "--describe":
            out["describe"] = True
        elif token in declared:
            out["seen"].add(token)
            if declared[token].get("arg"):
                if i + 1 >= len(argv):
                    out["error"] = f"{token} takes a value"
                    return out
                # `empty_root_error` above owns both what counts as empty and
                # the sentence the caller reads, because the same rule has to
                # hold in the eight tools that never reach this parser.
                # Refused here rather than in the resolver because `lib`
                # deliberately has no shared `Refused` (see this module's
                # docstring) and every declaring tool already prints `error`
                # and exits 2.
                bad = empty_root_error(token, argv[i + 1])
                if bad is not None:
                    out["error"] = bad
                    return out
                got = out["values"]
                if declared[token].get("repeatable"):
                    got.setdefault(token, []).append(argv[i + 1])
                else:
                    got[token] = argv[i + 1]
                i += 1
        elif token.startswith("-"):
            out["error"] = f"unknown argument {token!r} (try --help)"
            return out
        elif out["sub"] is None and subs:
            out["sub"] = token
        else:
            out["extra"].append(token)
        i += 1
    # Both of these answer ABOUT the tool rather than running it, so neither
    # needs a subcommand and neither may be refused for the lack of one.
    if out["help"] or out["describe"]:
        if out["sub"] is not None and out["sub"] not in subs:
            out["error"] = (f"{out['sub']!r} is not a subcommand. "
                            f"Expected one of: {', '.join(sorted(subs))}")
        return out
    if subs:
        if out["sub"] is None:
            out["error"] = f"expected one of: {', '.join(sorted(subs))}"
            return out
        if out["sub"] not in subs:
            out["error"] = (f"{out['sub']!r} is not a subcommand. "
                            f"Expected one of: {', '.join(sorted(subs))}")
            return out
        allowed = set(subs[out["sub"]].get("flags", ()))
        allowed.update(always_accepted(surface))
        for flag in sorted(out["seen"] - allowed):
            out["error"] = (
                f"{flag} is not accepted by {out['sub']!r}, and {out['sub']!r} "
                f"would have ignored it. Accepted here: "
                f"{', '.join(sorted(allowed - {'--help'})) or 'nothing but --root'}")
            return out
    return out


def describe_surface(surface: dict, sub: str | None = None) -> dict:
    """The declaration, or one subcommand of it, as JSON.

    This is `TASK-396`'s published write contract and `bin/perry describe`'s
    only source, arriving as a by-product of the table the parser already
    reads rather than as a second mechanism.
    """
    flags = surface_flags(surface)
    if sub is None:
        return {"tool": surface["name"], "kind": surface["kind"],
                "summary": surface["summary"],
                "root_resolution": surface.get("root_resolution", "standard"),
                "exit_codes": surface.get("exit_codes", {}),
                "flags": [flags[n] for n in sorted(flags)],
                "subcommands": [
                    {"name": s["name"], "summary": s.get("summary", ""),
                     "flags": subcommand_flags(surface, s),
                     "writes": list(s.get("writes", ()))}
                    for s in surface.get("subcommands", ())]}
    found = surface_subcommand(surface, sub)
    if found is None:
        return {"tool": surface["name"], "error":
                f"{sub!r} is not a subcommand of {surface['name']}",
                "subcommands": [s["name"] for s in surface.get("subcommands", ())]}
    names = subcommand_flags(surface, found)
    return {"tool": surface["name"], "subcommand": found["name"],
            "summary": found.get("summary", ""),
            "writes": list(found.get("writes", ())),
            "flags": [flags[n] for n in names if n in flags]}


def usage_lines(surface: dict, sub: str | None = None) -> str:
    """The usage block, generated. `<tool> --help § Usage` prints this.

    DESIGN-016 § 1.3: `--help` was a design paper — 10,689 bytes on
    `perry-task`, with `Usage:` at line 51 — so an agent asking what `done`
    takes paid ~2.5k tokens and read fifty lines of history first.
    """
    flags = surface_flags(surface)

    def spell(name: str) -> str:
        flag = flags.get(name, {"name": name})
        return f"{name} <{flag['arg']}>" if flag.get("arg") else name

    lines = [f"Usage: {surface['name']} <subcommand> [flags]"
             if surface.get("subcommands") else
             f"Usage: {surface['name']} [flags]"]
    picked = ([surface_subcommand(surface, sub)] if sub
              else list(surface.get("subcommands", ())))
    # **The whole tool gets NAMES; one subcommand gets its flags.** Printing
    # every flag of thirty subcommands is how `perry-task --help` got to 10,690
    # bytes, and the caller who wanted `done` read all of it (DESIGN-016
    # § 1.3). `<tool> <sub> --help` is one call and about 300 bytes.
    whole_tool = sub is None and len(picked) > 1
    for item in picked:
        if item is None:
            continue
        # Subtracted from the RESULT. Written as one expression this read
        # `set(...) | (always_accepted(...) - {...})`, which keeps `--help` and
        # `--describe` whenever a subcommand declares them itself. Harmless
        # while none does, and wrong the day one does.
        names = [n for n in subcommand_flags(surface, item)
                 if n not in ("--help", "--describe")]
        if whole_tool:
            lines.append(f"  {item['name']:<16} {item.get('summary', '')}")
            continue
        lines.append(f"  {surface['name']} {item['name']} "
                     f"{' '.join('[' + spell(n) + ']' for n in names)}")
        if item.get("summary"):
            lines.append(f"      {item['summary']}")
    if whole_tool:
        lines.append("")
        lines.append(f"  {surface['name']} <subcommand> --help   the flags for "
                     f"one of them")
        lines.append(f"  {surface['name']} --describe --json     the whole "
                     f"surface as data")
    if not surface.get("subcommands"):
        for name in sorted(flags):
            if name == "--help":
                continue
            lines.append(f"  {spell(name):<28} {flags[name].get('summary','')}")
    return "\n".join(lines)


def exists_or_unreadable(path: Path) -> bool | None:
    """`viewer.parsers.exists_or_unreadable`, reached without importing it here.

    **A deliberate second spelling of a four-line function, and the reason is
    an import cycle, not an oversight.** `viewer/parsers.py` is imported BY
    `perry_md_store`, and `lib` is imported by tools before `viewer/` is on
    the path, so neither can take the other at module scope. The two bodies
    are held identical by
    `tests/test_bin_argument_contract § TestOnePrimitiveAnsweredTwice`, which
    runs both over the same three inputs — present, absent, and a parent that
    may not be searched.
    """
    try:
        return path.exists()
    except OSError:
        return None


def scan_argv(argv: list[str], *, bools: tuple[str, ...] = (),
              values: tuple[str, ...] = ()) -> tuple[list[str], set[str],
                                                     dict[str, str], str | None]:
    """Split `argv` into positionals, flags seen, flag values, and one error.

    Returns `(positionals, seen, values, error)`. `error` is a ready-made
    message — the caller prints it and exits 2 — and is `None` when everything
    in `argv` was declared here.

    **Why this exists rather than a membership test.** `bin/perry_md_store`
    asked `if "--write" not in argv` and `if "--from-file" not in argv`, which
    means `--wrte` is not a typo, it is a no-op that exits 0: the render prints,
    nothing is written, and the caller is told the run succeeded. The whole
    argument vector is scanned before anything is dispatched, so `-h` in any
    position prints help without running the command in front of it — which
    `perry-tasks render --write --help` did (DESIGN-016 § 1.1).

    Scanning is deliberately dumb: a token that starts with `-` and is not
    declared is the error, everything else is a positional. Per-subcommand flag
    scoping is DESIGN-016 goal 12 and belongs to the declaration in phase C1,
    not here — this function is what phase A2 needs and no more.
    """
    positionals: list[str] = []
    seen: set[str] = set()
    got: dict[str, str] = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in ("-h", "--help"):
            seen.add("--help")
        elif token in bools:
            seen.add(token)
        elif token in values:
            if i + 1 >= len(argv):
                return positionals, seen, got, f"{token} takes a value"
            got[token] = argv[i + 1]
            i += 1
        elif token.startswith("-"):
            return (positionals, seen, got,
                    f"unknown argument {token!r} (try --help)")
        else:
            positionals.append(token)
        i += 1
    return positionals, seen, got, None


def resolve_state_root(project_root: Path) -> Path:
    """Where this project's Perry state files live.

    **The implementation is `viewer/parsers.py`'s and stays there**, because
    that is where every other reader already gets it — `perry-lint`,
    `perry-state`, `perry-task`, `perry-goals`, `perry-decide` and
    `perry-knowledge` all call `P.resolve_state_root`. This
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
#   P002-O1-KR1  target 1, current 0  → read as 0% while all four linked
#                                       tasks were closed and the board WAS
#                                       rendered from the store;
#   P002-O2-KR2  target 0, current 0  → read as MET while TASK-094 had
#                                       measured 13 row splits and 87 header
#                                       resolutions still reaching `BOARD.md`.
#
# Six of the register's eight phase KRs have `target: 0`, so any KR whose
# `current` is left at the template's `0` reads as met the day it is written.
#
# **The line this code does not cross.** It never computes `current`. A KR's
# metric is typically a count of something in the repository — P002-O2-KR1's is "0
# occurrences of the regex TASK-091 deleted" — and "the linked task is closed"
# does not establish that the count is zero; only re-running the count does.
# `perry/OKR.md § Operating Principles` opens with that rule, and the phase's
# own Definition of Done is a `grep -c` over `bin/`, which is why this comment
# does not name the symbol. So the linked-task tally below is emitted
# BESIDE `current`, under its own name, as a count of tasks and never as a
# fraction: a reader may put the two side by side and conclude the number is
# suspect, which is exactly the P002-O1-KR1 reading, but nothing here draws that
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


# ── the one clock ─────────────────────────────────────────────────────────
#
# TASK-144. Two surfaces stamped time in two zones and one expression compared
# them as STRINGS. Measured on this machine, which is UTC+8:
#
#     event log   '2026-08-28T02:15:22'    no zone — LOCAL wall clock
#     register    '2026-08-21T10:04:08Z'   UTC
#
# `current_staleness` asked "has a linked task moved since this number was
# asserted?" by comparing the two texts, so every task that moved inside the
# offset — eight hours here, whatever the machine says anywhere else —
# answered `stale: false` when it had moved.
#
# **What changed, and why it is the log that changed and not the register.**
# A new event stamps its local wall clock WITH the offset it was written at
# (`2026-08-28T02:15:22+08:00`), so it is self-describing from now on:
#
#   - Dropping the register's `Z` instead would make every timestamp in the
#     project machine-local, and `.perry/events.jsonl` is a COMMITTED file. A
#     second machine in a second zone would then read a file whose meaning
#     depends on who is holding it, permanently and undetectably.
#   - Converting only at the comparison would leave two shapes in the tree and
#     the next comparison somebody writes is wrong again — the defect, not a
#     fix for it.
#   - Stamping the log in UTC would be self-describing too, but it moves the
#     wall clock of new lines eight hours BACKWARDS against the 798 already in
#     the file, so the log's text stops rising and anything that read it as a
#     rising string breaks at the cutover. Keeping local and appending the
#     offset leaves the text rising and adds only a suffix.
#
# **The 798 zoneless entries are left exactly as they are and are read as
# local.** That is not a guess: `datetime.now()` wrote them, so local wall
# clock is what they hold. Rewriting them to say so is a migration and a
# decision, not this row — and the rule below costs nothing to state and makes
# them mean, today, what they meant when they were written.
#
# The stamps below and `_ts_moment` are the whole of it: two writers and ONE
# reader. A second converter anywhere is how the skew comes back.


def event_stamp() -> str:
    """The stamp every appended event carries: local wall clock, WITH offset.

    `2026-08-28T02:15:22+08:00`. Local rather than UTC so the text of the log
    keeps rising across the 798 lines that predate this, and offset-bearing so
    no reader ever has to assume which machine wrote a line again.
    """
    return _datetime.now().astimezone().isoformat(timespec="seconds")


def register_stamp() -> str:
    """The stamp the linkage register's `updated` carries: UTC, with `Z`.

    Unchanged by TASK-144 — the register was already saying which zone it
    meant, and `schema/goals-list-contract.md` and `tests/test_linkage_writer
    .py § TestUpdated` both pin the shape. It lives here so the two writers
    that stamp Perry's clocks are read side by side.
    """
    return _datetime.now(_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_moment(value):
    """**The one converter.** Any timestamp Perry writes or has written → UTC.

    Returns an aware `datetime` in UTC, or `None` for anything unreadable —
    never a partly-interpreted value, because a timestamp that cannot be
    placed on a line must not be allowed to sort against ones that can.

    The four shapes, and the rule each is read by:

    - `2026-08-21T10:04:08Z` / `+08:00` — zone-bearing. Converted. This is
      what both writers emit from now on.
    - `2026-08-28T02:15:22` — zoneless, and there are 798 of them in this
      project's append-only log. **Read as the reading machine's local time**,
      because `datetime.now()` wrote them and local wall clock is exactly what
      they hold. A log carried to another zone therefore reads its OLD lines
      by the new machine's offset; its new ones say what they mean.
    - `2026-08-21` — a date, not a wall clock. Read as UTC midnight: the
      register is the only surface that writes one, and the register is UTC.
    - anything else, including `""` — `None`.

    Accepts a `datetime` as well as a string so a caller holding a clock
    reading rather than a field gets the same rule applied to it, rather than
    writing the second half of this function at its own call site.
    """
    if isinstance(value, _datetime):
        moment = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        if text.endswith("Z"):          # `fromisoformat` learned `Z` in 3.11
            text = text[:-1] + "+00:00"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            # A date carries no wall clock to be local ABOUT, so this one does
            # not go through the naive rule below. Midnight also errs toward
            # reporting staleness, which is the direction to err in: a false
            # "recheck this" costs a look, a false "this number is fine" costs
            # the number.
            text += "T00:00:00+00:00"
        try:
            moment = _datetime.fromisoformat(text)
        except ValueError:
            return None
    if moment.tzinfo is None:
        moment = moment.astimezone()    # naive → this machine's local zone
    return moment.astimezone(_timezone.utc)


def ts_key(value) -> str:
    """`ts_moment`'s string face: the UTC text two timestamps are compared on.

    Carries its `Z`, because this string is also EMITTED — as
    `current_provenance.asserted_at`, `current_staleness.since` and
    `moved_tasks[].at` — and a payload that publishes a zoneless timestamp is
    the defect this row removed, reintroduced at the contract boundary.
    """
    moment = ts_moment(value)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ") if moment else ""


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


#: KR id → the name of the function in this module that RE-RUNS its metric.
#:
#: `kr_progress_provenance`'s `measured: False` was "always false, and emitted
#: rather than implied", because no tool in Perry re-ran a KR's metric. This
#: table is the exception list, and it is a table rather than an `if` so that
#: every reader of a KR's `current` dispatches through one place —
#: `computed_kr_current` — and two readers cannot come to disagree about
#: whether a number was measured or typed. DESIGN-015 § 6 row F.
#:
#: What is declared here is WHICH KR is computed and BY WHAT, never the value.
#: The value is the thing this row exists to stop anybody typing.
COMPUTED_KR_METRICS = {
    "P003-O3-KR2": "same_action_linkage",
}


#: Whether `{"kind": "unlinked", "via": "add"}` — the store half of
#: `P003-O3-KR2`'s second numerator path — has **no writer anywhere in Perry**.
#:
#: **It has one, since `TASK-394`: `perry-task add --unlinked`.** The flag is
#: parsed by `bin/perry-task § parse`, refused against `--kr` by `cmd_add`, and
#: written by `bin/perry-task § linkage_add_change` into the same `commit()`
#: and the same recovery marker as `tasks.jsonl` and the journal. `via` is
#: still a hardcoded literal at every writer of `perry/linkage.jsonl` — there
#: is still no `--via` flag and `schema/state-schema.json` still pins the field
#: to `^(add|link)$` — but `linkage_add_change` now emits BOTH of the record
#: kinds `DESIGN-015 § 5.5` assigns to the `work` lane, not `edge` alone.
#:
#: **What was true when this constant read `True`, kept because the reasoning
#: is what makes the flip checkable.** `via: "add"` was reachable on `edge`
#: records and unreachable on `unlinked` ones: `perry-task
#: § linkage_edge_change` (as it was then named) wrote `edge` records ONLY, and
#: `perry-goals § linkage_store_text` and `perry-tasks § LINKAGE_IMPORT_VIA`
#: both write `"link"`. Row F stated the gap rather than closing it, on the
#: Bound: a new writer on this store was row D's territory. `TASK-394` is the
#: row that was dispatched to close it, and closing it is why this line moved.
#:
#: **The consequence that has now been discharged.**
#: `phase/003-storage-code.md § DoD` item 5 offers a row two ways to comply:
#: "a KR edge **or** an `unlinked` declaration written by its own `add`". The
#: second was unsatisfiable as shipped, so a row that honestly served no KR had
#: no way to say so at `add` and pinned the denominator permanently — the 100%
#: target was unreachable by construction. `USER-921` raised exactly that, and
#: chose to build the writer rather than restate the KR, because after the
#: restatement a KR at 100% would no longer say whether anyone was ever asked.
#:
#: **The trap this constant exists to keep marked.** `TASK-281`'s V4 closed
#: mutation M13 against a fixture — a store holding `unlinked(task, "add")` —
#: that Perry could not then produce, so the closure went red while production
#: behaviour was untouched. That fixture is now producible, which is precisely
#: why every guard `TASK-394` added is reddened by driving the CLI rather than
#: by handing a record to a reader.
#:
#: Kept as a constant, not a comment, so it stays **checked** in the other
#: direction too: the computation reads it, and
#: `test_same_action_linkage § TheUnlinkedAtAddPathHasAWriter` drives the real
#: binary and fails the day the flag stops working. Flipping this line alone
#: does not make the path reachable and does not make it unreachable — the
#: tests assert the flag's BEHAVIOUR against this value, so a stale constant
#: is a red suite rather than a quiet lie in a payload.
UNLINKED_AT_ADD_HAS_NO_WRITER = False


def _corroborates(claimed, store_krs) -> bool:
    """Does the `add` event's `kr` agree with the store's `via: "add"` edges?

    **The one predicate for both directions.** `same_action_linkage` asks this
    question twice — from the event's side, to decide the numerator, and from
    the store's side, to decide `store_edge_without_event` — and they are the
    same question. Two spellings of it are how a row ends up counted in the
    numerator AND reported as a desync, or neither.

    `claimed` is `None` for all three of "no `add` event exists", "its `kr`
    key is missing" and "`kr: null`", and that collapse is deliberate. **An
    earlier draft carried a `_NO_ADD_EVENT` sentinel to keep the three
    apart**; mutation N13 removed it and came back GREEN, because nothing
    downstream ever asked which one it was — every caller treats all three as
    "the event does not name a KR", which is the only thing either direction
    needs to know. It was deleted rather than pinned with a test, on this
    round's own precedent for round 1's M14: a test over a distinction that
    changes no answer tells the next reader it does something.

    The value is stripped, because `perry-task § linkage_add_change` strips
    before writing, and a reader that did not would fail to match its own
    writer's output and report every padded `--kr` as a desync.
    """
    if claimed is None:
        return False
    return str(claimed).strip() in store_krs


#: Decimal places a measured percentage is published to. One, matching
#: `bin/perry-context-budget § pct` — the only other percentage this tree
#: publishes rather than prints — so a consumer reading two Perry payloads
#: does not meet two precisions.
MEASURED_PERCENT_PLACES = 1


def measured_percent(numerator: int, denominator: int) -> float | None:
    """`numerator / denominator` as a percentage, published to one decimal.

    **The rule, and it is on `schema/goals-list-contract.md` because a
    consumer has to be able to state it too:** a measured percentage is
    rounded to one decimal place, and `0.0` and `100.0` are RESERVED for the
    exact cases — `numerator == 0` and `numerator == denominator`. Nothing
    strictly between the ends is ever published at an end.

    **Why round at all.** `13 / 38` is `34.21052631578947` in IEEE 754, and
    that is what `perry-goals list --json` published: seventeen significant
    figures of a ratio of two small integers, sixteen of which are an
    artefact of binary floating point rather than anything measured. Every
    consumer then rounds it differently or not at all, so the same
    measurement renders as three different numbers on three surfaces and
    none of them is Perry's answer. Publishing the precision is the only way
    the answer is one answer.

    **Why the ends are reserved, and why that is not a direction.**
    `perry-goals/list/2.0` removed `progress` because Perry cannot tell which
    way a KR runs, so this must not round "toward the unmet end" — there is
    no such end here to know. What it can tell is EXACTNESS: `1999 / 2000`
    is `99.95`, which rounds to `100.0` at one decimal and publishes *every
    row answered* about a phase with a row that was not. `0` and `100` are
    the two values a consumer may read as a whole fact, so they are the two
    this function only ever returns from a whole fact. Off the end, the
    nearest representable non-end value is published instead — `99.9` and
    `0.1` — which is still a rounding and is the only rounding of the four
    that cannot be read as a completeness claim it did not measure.

    **The unrounded ratio is never lost.** `numerator` and `denominator` are
    published beside it in `current_measurement`, exactly and as integers, so
    a consumer that needs the full ratio divides them itself and one that
    needs "is it met" compares them — which is the comparison it should have
    been making anyway, and the one thing this rounding is designed not to be
    able to answer wrongly.

    `None` for an empty denominator: no population is not `0` measured, and
    that distinction belongs to the caller's own docstring.
    """
    if not denominator:
        return None
    value = round(100.0 * numerator / denominator, MEASURED_PERCENT_PLACES)
    step = 10.0 ** -MEASURED_PERCENT_PLACES
    if value >= 100.0 and numerator < denominator:
        return round(100.0 - step, MEASURED_PERCENT_PLACES)
    if value <= 0.0 and numerator > 0:
        return step
    return value


def same_action_linkage(linkage_records, events, *, track: str = "main") -> dict:
    """`P003-O3-KR2`, measured: rows that took a KR edge or an `unlinked`
    declaration **in the same action as `add`**, over the rows that were asked.

    Reads BOTH sides, because the KR's three parts do not live in one file
    (DESIGN-015 § 5.3):

    * **The population** — `.perry/events.jsonl`. A row is in it when its own
      `add` event carries a `kr` KEY, whatever the key's value.
    * **The numerator, half one** — **BOTH files, and both are required.** The
      row's `add` event carries a non-null `kr`, AND `perry/linkage.jsonl`
      holds an `edge` record for that row with `via: "add"` naming the same
      KR. § 5.3 writes those two under ONE `commit()`, so "the transaction
      landed whole" is the honest reading of "linked in the same action", and
      it is the only reading neither file can fake alone.
    * **The numerator, half two** — `perry/linkage.jsonl`, an `unlinked`
      record with `via: "add"`. A declaration of "no KR" is an answer, and
      `add` is where it was given. **No writer in Perry can produce this
      record today** — see `UNLINKED_AT_ADD_HAS_NO_WRITER` below, which is
      pinned to the code by a test rather than left as a remark.

    **Why half one takes both files, and what it cost to learn.** It used to
    take the event's word alone::

        if event.get("kr") is not None:      # the whole numerator
            linked.append(tid)

    Two things followed, and both were reproduced on real data before this
    was changed.

    *The number could be raised by typing spaces.* `perry-task add --kr "   "`
    wrote a truthy `kr` onto the event while `linkage_add_change` stripped it
    to `""` and wrote no edge at all; the row counted. Measured on `339f553`:
    15.38% (2/13) → 21.43% (3/14) with **zero** records added to the store and
    no warning printed. The KR that exists to catch dishonest linkage moved up
    on the most dishonest input available.

    *And the store could not move the number at all.* Deleting every
    `via: "add"` record from `perry/linkage.jsonl` — 123 records to 121, which
    `perry-tasks linkage-write --root . --from-register` does as a matter of
    course — left the published figure at exactly 15.38%. Half the computation
    the spec exists to protect was decoration.

    Requiring both halves closes both, and it closes them in the direction
    that cannot flatter: a desync now REMOVES a row from the numerator and
    names it in a diagnostic, where before one silently added a row.

    **Why the population is the `kr` key and not the phase's whole intake.**
    `phase/003-storage-code.md § Definition of Done` item 5, restated
    2026-08-31, is the authority: *every `main`-track row opened **after the
    gate lands** carries a KR edge or an `unlinked` declaration written by its
    own `add`. The rows that were never asked before the gate are phase 004's.*

    So "after the gate landed" has to be decided from the data, and the gate
    left a signature in it. Row D changed the SHAPE of the `add` event: before
    it, no `add` event has a `kr` key; after it, every `add` writes one, `null`
    when the flag was absent (§ 5.2, "record and warn"). `"kr" in event` is
    therefore the gate's own mark on each row it governed — per row, with no
    typed date, no commit SHA and no clock, none of which is in the store or
    the log this KR is supposed to be computed from.

    The alternative — every row opened since the phase began — is arithmetic
    that contradicts the DoD it is meant to score. Those rows' `add` already
    happened, without a gate to ask them; no future work can give them an
    answer *at `add`*, so the KR could never leave 0 and would be measuring the
    size of the backlog rather than whether the gate holds. **Both readings
    return 0% today** (0/1 and 0/190) and differ only in the denominator, so
    the choice changes nothing about today's number and everything about
    whether tomorrow's can move.

    **The same-action property is the whole point, and it is an EVENT property.**
    A row added without `--kr` and linked an hour later by `perry-goals link`
    has an `edge` in the store and is in the population, and it must NOT count:
    its `add` event's `kr` is null and its store record's `via` is `"link"`.
    A computation that reads only the store cannot tell that row from one
    linked at `add`, and will publish a plausible number for a different
    quantity.

    Returns the measurement, never a bare float. `current` is `None` when the
    population is empty — a phase where nothing has been opened under the gate
    has no denominator, and reporting `0` (nothing linked) or `100` (nothing
    unlinked) would both be inventing an answer out of an absence.
    """
    records = [r for r in (linkage_records or []) if isinstance(r, dict)]
    unlinked_at_add = {
        str(r.get("task") or "") for r in records
        if r.get("kind") == "unlinked" and r.get("via") == "add"}
    # task id → the KR ids the STORE says were edged in that row's own `add`.
    # A set, not a single value: the store is append-only and a task may carry
    # more than one record. Values are stripped, because
    # `perry-task § linkage_add_change` strips before writing and a reader
    # that did not would fail to match its own writer's output.
    edge_at_add: dict[str, set] = {}
    for r in records:
        if r.get("kind") != "edge" or r.get("via") != "add":
            continue
        tid = str(r.get("task") or "")
        if tid:
            edge_at_add.setdefault(tid, set()).add(str(r.get("kr") or "").strip())

    # Every `add` event in the log, by task id, mapped to what its `kr` says.
    # Built over ALL `add` events, not just the population's, because the
    # detector below has to answer for tasks whose event never arrived — and
    # `.get` returning `None` for those is exactly the right answer.
    add_event_kr: dict[str, object] = {}
    for event in (events or []):
        if not isinstance(event, dict) or event.get("event") != "add":
            continue
        tid = str(event.get("id") or "")
        if tid and tid not in add_event_kr:
            add_event_kr[tid] = event.get("kr")

    population: list[str] = []
    linked: list[str] = []
    declared: list[str] = []
    never_answered: list[str] = []
    # Half-landed the OTHER way: the event claims a KR and the store has no
    # edge to back it. This is what `--kr "   "` produced, and it is also the
    # shape of a crash between the store write and the event append.
    event_without_store_edge: list[str] = []
    seen: set[str] = set()
    for event in (events or []):
        if not isinstance(event, dict) or event.get("event") != "add":
            continue
        # The gate's signature. `.get("kr")` would collapse "the gate wrote
        # null" into "the gate never ran", which is the entire population.
        if "kr" not in event:
            continue
        if track and str(event.get("track") or "") != track:
            continue
        tid = str(event.get("id") or "")
        if not tid or tid in seen:
            continue
        seen.add(tid)
        population.append(tid)
        claimed = event.get("kr")
        if claimed is not None:
            # BOTH halves, or it is not a link made in the same action. The
            # store must name the same KR the event names: an edge to a
            # DIFFERENT KR is not corroboration, it is a third disagreement.
            if _corroborates(claimed, edge_at_add.get(tid, set())):
                linked.append(tid)
            else:
                event_without_store_edge.append(tid)
                never_answered.append(tid)
        elif tid in unlinked_at_add:
            declared.append(tid)
        else:
            never_answered.append(tid)

    # ── The desync detectors, and WHY NEITHER IS GATED ON THE EVENT ──────────
    #
    # `store_edge_without_event` used to read:
    #
    #     if tid in seen and tid not in set(linked)
    #
    # `seen` is the population, and the population is built from the `add`
    # event. So the detector built to find "the store landed and the event did
    # not" could only see rows whose event HAD landed — it was gated on the
    # very artefact whose absence it detects. `TASK-279`'s V4 drove the crash
    # matrix to seven points and found the detector reporting EMPTY at two of
    # them, for exactly this reason: the event append is `open(..., "a")`, not
    # a canonical rename, so a crash there leaves the store's half alone in the
    # tree and the old gate dropped it on the floor.
    #
    # Reproduced at three shapes before the rewrite; only the middle one was
    # ever reported:
    #
    #   A  store edge, NO `add` event          → old: [] (blind)  new: reported
    #   B  store edge, `add` event `kr: null`  → old: reported    new: reported
    #   C  store edge, `add` event, no `kr` key → old: [] (blind) new: reported
    #
    # The new gate is the STORE — the half that survives — and the question
    # asked of the event is only "does it corroborate", where "there is no
    # event" is a perfectly good no. Deliberately NOT track-filtered: the
    # record carries no track, and for shape A there is no event to read one
    # off. A `via: "add"` edge whose event is gone is a desync on any track,
    # and inventing a track for it would reintroduce the guess.
    # Written as ONE condition rather than an `if`/`elif` pair, and that is a
    # correction to this round's own first draft. The pair read:
    #
    #     if claimed is absent or claimed is None:   append
    #     elif str(claimed).strip() not in krs:       append
    #
    # which looks like two cases and is one: `str(None)` and the sentinel
    # are never KR ids, so the `elif` already caught everything the `if` did.
    # Mutation N03 re-gated the `if` on `tid in seen` — the exact defect being
    # removed — and came back GREEN, because the `elif` quietly did the work.
    # A branch that cannot change the answer is a branch no mutation can
    # measure, and it would have made the next reader's re-gating invisible
    # too.
    store_edge_without_event = sorted(
        tid for tid, krs in edge_at_add.items()
        if not _corroborates(add_event_kr.get(tid), krs))

    denominator = len(population)
    numerator = len(linked) + len(declared)
    return {
        "kr": "P003-O3-KR2",
        "measured": True,
        "source": "linkage.jsonl + .perry/events.jsonl",
        "current": measured_percent(numerator, denominator),
        "numerator": numerator,
        "denominator": denominator,
        "population": population,
        "linked_at_add": linked,
        "declared_unlinked_at_add": declared,
        "never_answered": never_answered,
        "store_edge_without_event": store_edge_without_event,
        "event_kr_without_store_edge": sorted(event_without_store_edge),
        # The honest statement, carried in the payload rather than left in a
        # comment, because a reader looking at `declared_unlinked_at_add: []`
        # is owed the difference between "nobody declared one" and "nobody
        # CAN". Since `TASK-394` the answer is `True` — `perry-task add
        # --unlinked` is the writer — and the key stays rather than being
        # dropped, because an empty list still means the first of those two
        # and a reader still cannot tell which without being told. Pinned to
        # the code by `test_same_action_linkage
        # § TheUnlinkedAtAddPathHasAWriter`, which drives the real binary and
        # reddens the day the flag stops writing the record.
        "declared_unlinked_at_add_reachable": not UNLINKED_AT_ADD_HAS_NO_WRITER,
        "reason": (
            "no row has been opened under the `add --kr` gate yet, so this KR "
            "has no denominator" if not denominator else
            f"{numerator} of {denominator} `{track}`-track row(s) opened under "
            f"the gate answered the KR question in their own `add`"),
    }


def computed_kr_current(kr_id: str, *, linkage_records=None, events=None):
    """The measurement for a KR whose metric this module re-runs, or `None`.

    The one dispatch point for `COMPUTED_KR_METRICS`. Every reader that
    publishes a KR's `current` calls this before falling back to the register,
    so "is this number measured or typed?" has one answer per KR rather than
    one answer per reader.
    """
    name = COMPUTED_KR_METRICS.get(str(kr_id or ""))
    if not name:
        return None
    return globals()[name](linkage_records, events)


def kr_progress_provenance(current, task_ids, *, asserted_at: str = "",
                           status_by_id: dict | None = None,
                           events: list | None = None,
                           events_present: bool = False,
                           computed: dict | None = None) -> dict:
    """The three blocks that go beside a KR's `target` / `current`.

    Returns `current_provenance`, `current_staleness` and
    `linked_task_completion` — computed once, here, because `bin/perry-state`
    and `bin/perry-goals` both emit them and a second implementation is how the
    two would come to disagree about whether a number is stale.

    `current` is `None` for a KR the store never gave a number, and that is
    reported as `unasserted` rather than as `0.0`. The default matters more
    than it looks: with six of eight phase KRs driving a count to zero, a
    `current` defaulted to `0` reads as **met before the work starts**.

    **`asserted_at` is the KR's OWN date, and `""` is a third answer.**
    TASK-155: this argument used to be `register_updated`, the one file-level
    `updated:` stamp of `phase/<NNN>-linkage.md`, shared by every KR in the
    phase — so appending one edge to one KR re-dated numbers asserted weeks
    ago under every other KR, and each of them read fresh with nothing about
    the number changed. ADR-019 deleted that document and
    `stores.declared["linkage.jsonl"].records.kr.asserted_at` is the per-KR
    field that replaces it.

    An asserted `current` with no `asserted_at` is neither fresh nor stale:
    nobody recorded when the number was arrived at. It reports
    `asserted_scope: ""` and `staleness.evaluated: False`. **It is never
    defaulted to now**, which would be TASK-155's defect with a different
    spelling — every number would read as measured this second — and it is
    never defaulted to any other write's timestamp either, which is what
    reading the document's `updated:` was.
    """
    status_by_id = status_by_id or {}
    events = events or []
    ids = [str(t) for t in (task_ids or [])]

    # `asserted` describes the REGISTER's number and is read only on the paths
    # a computed KR does not take. It used to be preceded here by
    # `current = computed.get("current")` — overwriting the register's value
    # before this line — which read as "the measurement wins" but was dead:
    # every branch below that a computed KR reaches ignores `asserted`, and
    # the value actually reaches the payload from `out["current"]` at the
    # bottom of this function. TASK-281's mutation M14 deleted that assignment
    # and no test went red, which is what a green mutation is for; the line is
    # gone rather than pinned, because a test over dead code would have made
    # the next reader believe it did something.
    asserted = current is not None
    if computed is not None:
        # `measured` stops being "always false". It is true even when
        # `current` is `None`: a phase with no rows opened under the gate was
        # MEASURED to have no denominator, which is a different fact from a
        # number nobody wrote down, and the two must not both read
        # `unasserted`.
        provenance = {
            "state": "measured",
            "measured": True,
            "source": computed.get("source", ""),
            # Deliberately empty. A measurement is not asserted, and it has no
            # assertion date to go stale from — it is re-run on every read.
            "asserted_at": "",
            "asserted_scope": "",
        }
    else:
        provenance = {
            # What the number IS, not how good it is.
            "state": "asserted" if asserted else "unasserted",
            # Always false, and emitted rather than implied. No tool in Perry
            # re-runs a KR's metric, so no `current` it publishes is a
            # measurement. A future tool that does re-run one sets this true;
            # until then a consumer that wants to show "measured" has an
            # explicit answer.
            "measured": False,
            "source": "linkage-store" if asserted else "",
            # **This KR's own date, or nothing.** `asserted_scope` is emitted
            # beside it so a reader can tell "asserted on this date" from
            # "asserted, date unrecorded" — the two used to be indistinguish-
            # able because the date always came back non-empty, from a stamp
            # that belonged to the file rather than to the number.
            "asserted_at": ts_key(asserted_at) if asserted else "",
            "asserted_scope": ("kr" if asserted and ts_key(asserted_at)
                               else ""),
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
    if computed is not None:
        # A measured number cannot go stale: it is re-derived from the store
        # and the event log on every read, so there is no interval between
        # when it was arrived at and when it is published for a task to move
        # in. This is `evaluated: True` — the question was asked and answered
        # — not the `False` that means "could not tell".
        staleness["evaluated"] = True
        staleness["reason"] = (
            "`current` is recomputed on every read from "
            f"{provenance['source']}, so it cannot be stale")
    elif not asserted:
        staleness["reason"] = (
            "`current` was never asserted, so there is nothing to go stale")
    elif not since:
        staleness["reason"] = (
            "no `asserted_at` is recorded for this KR's `current`, so there "
            "is no date to measure a task's move against and staleness "
            "cannot be evaluated. This is not `false` — nobody wrote down "
            "when the number was arrived at, which is a different fact from "
            "no task having moved since")
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
            at = ts_key(event.get("ts", ""))
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

    out = {"current_provenance": provenance,
           "current_staleness": staleness,
           "linked_task_completion": tally}
    if computed is not None:
        # `current` is returned ONLY for a computed KR, and returning it here
        # is what makes the two publishers agree by construction rather than
        # by review. Both `bin/perry-state § encode_linkage_objective` and
        # `bin/perry-goals § the krs payload` splice this mapping in AFTER
        # their own `current`, so the measured value replaces the register's
        # at both sites from one place. Adding a second `if kr.id == …` at
        # either call site is the thing this return exists to prevent.
        out["current"] = computed.get("current")
        out["current_measurement"] = {
            k: v for k, v in computed.items() if k != "current"}
    return out


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


# ── which id families a project uses ──────────────────────────────────────
#
# TASK-158. Perry's own families were written out by name in four places, and
# each one of them answered a slightly different question with the same six
# letters. The spellings are here now — one per question, each read by its
# callers rather than retyped — and the *project's* families are derived
# instead of listed, because there is no list Perry could have written that
# has `DEC` or `SPEC` on it.


#: A markdown artifact named after an id: `ADR-002-single-region.md`,
#: `TASK-158-spec.md`, `DEC-014-ingest-format.md`. Group 1 is the family.
#:
#: The shape is `bin/perry-explain § ID_RE`'s, minus the KR form: a capitalised
#: word, a hyphen, digits. That is deliberate — `perry-explain` is the resolver
#: every id reader in this repository defers to, and a family this cannot see
#: is a family its `harvest` cannot see either.
ID_NAMED_FILE_RE = re.compile(r"^([A-Z][A-Z0-9]{1,9})-\d")


def id_family(stem: str) -> str | None:
    """The id family a filename declares, or None when it declares none."""
    m = ID_NAMED_FILE_RE.match(stem)
    return m.group(1) if m else None


#: The families **Perry itself** mints ids in and writes citations of. Closed
#: on purpose, and it is the floor rather than the answer: a project that has
#: not written its first ADR yet still cites `ADR-006` legitimately, so these
#: are known before any evidence of them exists on disk.
#:
#: `SRC` and `KR` are in here and NOT in `PERRY_ARTIFACT_FAMILIES` below,
#: which is the reason these are two names and not one. A `SRC-n` lives in a
#: `Id:` line inside a digest and a `KR` in a register row; neither is ever a
#: filename, so a file called `SRC-1-notes.md` is not something Perry wrote.
PERRY_CITATION_FAMILIES = frozenset(("ADR", "DESIGN", "USER", "SRC", "KR",
                                     "TASK"))

#: The families Perry puts in a FILENAME — `DESIGN-001-…`, `ADR-002-…`. Read
#: by `bin/perry-lint § looks_like_perry_state` and
#: `bin/perry-diagnose § _perry_shaped`, which are one predicate — "would Perry
#: have written this file" — that was spelled out in both files.
#:
#: **This one stays closed, and widening it is a different decision.** Those
#: two callers ask whether a file in a folder Perry claimed is Perry's or the
#: user's; answering "yes" for every id-named file would silence the collision
#: warning that exists to tell an adopting project its `decisions/` already has
#: something in it. Perry's own three standing NS-01 warnings are files of its
#: own that this correctly does not claim.
PERRY_ARTIFACT_FAMILIES = ("DESIGN", "ADR", "TASK", "USER")

_PERRY_ARTIFACT_RE = re.compile(
    r"^(?:" + "|".join(PERRY_ARTIFACT_FAMILIES) + r")-\d")


def perry_named_artifact(stem: str) -> bool:
    """Is this file stem one of Perry's own id-named artifacts?"""
    return _PERRY_ARTIFACT_RE.match(stem) is not None


#: Directories a walk over a project must not descend into: another toolchain's
#: cache, another agent's workspace, a vendored tree. Lives here because
#: `bin/perry-explain § walk_md` and `declared_id_families` below walk the same
#: tree for the same reason, and a second skip list is a second answer to
#: "what counts as this project".
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
    ".claude", ".agents", ".trae",
    "target", ".next", "vendor", "site-packages", ".pytest_cache", ".tox",
}

MD_SUFFIXES = (".md", ".markdown")


def walk_md(root: Path):
    """Every markdown file under `root` that belongs to THIS project.

    A directory carrying its own `.git` is a different project — a vendored
    checkout, a submodule, an agent worktree. Skipping by name never finishes,
    and this walk feeds `perry-diagnose`'s user-load scan, which reported a
    dangling id that existed in no file of this repo: it was reading a
    subagent's half-written source out of a worktree. `.git` is a directory in
    a clone and a file in a worktree.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # A directory this walk may not search cannot be shown to be a nested
        # checkout, and `Path.exists()` raises rather than saying so. Treat it
        # as not-a-checkout and let `os.walk` skip it on its own error path —
        # the alternative is that one unreadable directory anywhere under the
        # root turns every document scan into a traceback.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and exists_or_unreadable(
                           Path(dirpath) / d / ".git") is not True]
        for fn in filenames:
            if fn.lower().endswith(MD_SUFFIXES):
                yield Path(dirpath) / fn


def blank_code_spans(text: str) -> str:
    """One line of markdown with every inline code span blanked to spaces.

    The sibling of the fence skip in `bin/perry-explain § harvest`: a fenced
    block is quoted material and so is a code span, and the scanner honoured
    one spelling and not the other. `see \\`TASK-042\\`` and its fenced twin
    are the same sentence with different punctuation.

    **Spaces, not deletion, and the length is preserved.** A caller that
    reports a position on the line reports the same position it would have
    without this, and no two tokens are joined by removing what sat between
    them.

    **Code span rules, from CommonMark, and both hard cases:**

    * A run of *n* backticks opens a span, and the next run of *exactly* n
      closes it. So ``\\`\\`a \\`b\\` c\\`\\``` is one span with a literal
      backtick pair inside it, blanked whole — a shorter run inside a longer
      one is content, not a delimiter.
    * A run with no matching closer is **not a span at all**. The backtick
      stays, the text around it stays prose, and scanning continues after the
      run. An unbalanced backtick is ordinary in prose, and the alternative —
      treating the rest of the line as code — would silently blind a reader
      to everything after somebody's typo.
    """
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        if text[i] != "`":
            i += 1
            continue
        opener = i
        while i < n and text[i] == "`":
            i += 1
        run = i - opener
        close, k = -1, i
        while k < n:
            if text[k] != "`":
                k += 1
                continue
            end = k
            while end < n and text[end] == "`":
                end += 1
            if end - k == run:
                close = k
                break
            k = end
        if close < 0:
            # Unmatched. `i` already sits past the run, so the search resumes
            # after it rather than re-reading the same backticks forever.
            continue
        # A CommonMark code span may cross a source line. Preserve newlines so
        # callers that report file:line locations keep the original mapping.
        out[opener:close + run] = [
            "\n" if c == "\n" else " "
            for c in text[opener:close + run]
        ]
        i = close + run
    return "".join(out)


def declared_id_families(root: Path) -> set[str]:
    """The id families THIS project uses, read off the project.

    A project declares a family by using it, and the place it uses it that
    every id reader here already agrees on is the filename:
    `bin/perry-explain § harvest` opens with *"a file named for an ID defines
    it"*, and that definition point is exactly what keeps `perry-diagnose` from
    reporting the id dangling. So a tool that wants to know whether a citation
    of `DEC-014` is a citation or a typo can ask the same question the reader
    downstream of it will ask, and get the same answer — without being taught
    the letters `DEC`.

    **Filenames, and nothing read.** `harvest` also takes definitions from
    headings, table rows and YAML ids, and it costs a read of every markdown
    document in the project to do it. This is called from a WRITE path, where
    that is a cost paid on every `perry-task next`; the stems come out of the
    same walk for free. Measured on this repository: 456 markdown files, 80 ms
    for the walk, against about a second to read them. The consequence is
    stated rather than hidden — a family whose only definition point is a
    heading inside a document named something else is not learned here, and a
    citation of it is still warned about.

    **A fixture's family counts, and that is not a bug.** `harvest` defines an
    id from an id-named file wherever it sits, `is_illustrative` only filtering
    what counts as a *mention*. So this repository's own
    `tests/fixtures/.../REL-001-spec.md` puts `REL` in this set — and it must,
    because `perry-diagnose`, reading the same tree, will not report `REL-002`
    dangling either. A caller that filtered fixtures out here would go back to
    warning about ids the tool it cites is silent about, which is the defect
    this function was extracted to end.
    """
    return {fam for path in walk_md(root)
            if (fam := id_family(path.stem)) is not None}


# ── what a task summary has to be, structurally (TASK-325) ────────────────


#: How much a summary has to ADD to its title before `summary-repeats-title`
#: stops firing — and nothing else. **This is not a minimum summary length.**
#: It was one until 2026-09-03, when TASK-330 removed the rule that read it
#: that way: how long a summary ought to be is the writing agent's business,
#: not a check's. What survives is the one arm that needs a threshold for a
#: structural reason — a summary that is its title plus four words has not
#: explained it — so the constant stays, scoped to that arm, rather than
#: being re-inlined there as a second copy of the same number.
#: Do not quote it as a length floor. There is no length floor.
SUMMARY_MIN_WORDS = 5

#: **`\W` under Unicode, not `[^0-9a-z]`.** The first draft folded away
#: everything outside ASCII, so every Chinese summary folded to the EMPTY
#: string — and since `"a title".startswith("")` is true, every one of them was
#: reported as repeating its title. Same root cause as the length floor that
#: TASK-330 removed: a rule that calls itself structural while quietly
#: meaning "in English".
_SUMMARY_FOLD = re.compile(r"[\W_]+", re.UNICODE)
#: CJK ideographs, kana and Hangul — scripts that do not put spaces between
#: words. **This exists because the first draft of the token count used
#: `str.split()` and nothing else, which makes `新的稳定说明` exactly ONE word
#: and would have refused every Chinese summary ever written.** The length
#: rule that first needed it is gone (TASK-330), but `summary-repeats-title`
#: still counts tokens to decide what a summary ADDS, so the defect is still
#: reachable and this still guards it. **Its pin moved with it.** TASK-325 held
#: this property through the removed floor, so between 2026-09-03 and TASK-336
#: reverting `summary_tokens` to `str.split()` left the whole suite green; it
#: is now held in `tests/test_summary_is_asked_for.py` by
#: `test_a_chinese_summary_that_extends_its_chinese_title_is_not_a_repeat`,
#: which reaches it through the one rule that survives, and by the
#: neighbouring `…_does_restate_its_title_is_still_caught`, whose job is to
#: stop the answer being "never fire on CJK". Perry declares a document
#: language per project, ships zh fixtures, and states in
#: `SKILL.md` that its field names stay English precisely so the rest need not
#: — so a "structural" rule that silently means "structural, in English" is
#: the same defect as a denylist over English, one layer down.
_SUMMARY_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯]")


def summary_tokens(s: str) -> int:
    """Token count for `summary-repeats-title`, without assuming spaces.

    A CJK character counts as one token and each whitespace-separated run of
    everything else counts as one. So `新的稳定说明` is 6 rather than 1, and an
    English sentence counts the way `str.split()` already counted it.

    **Its one caller measures what a summary ADDS to its title.** This is not
    a "how long should a summary be" facility, and since TASK-330 there is no
    rule here that asks that question. Anything reading this as a signal about
    the quality or sufficiency of a summary is reading it wrong.
    """
    cjk = len(_SUMMARY_CJK.findall(s))
    rest = len(_SUMMARY_CJK.sub(" ", s).split())
    return cjk + rest


def summary_fold(s: str) -> str:
    """Case- and punctuation-insensitive key for comparing summary to title."""
    return _SUMMARY_FOLD.sub(" ", (s or "").lower()).strip()


#: Rules `summary_shape` used to emit, as `rule -> (date, row)`.
#:
#: **This is the half of the NOT CHECKED register that is data rather than
#: prose.** The *reason* each rule left stays in `summary_shape`'s docstring,
#: where it is on the same screen as the predicate someone is reading when they
#: wonder why there is no sentence check; moving that to a sidecar would
#: separate the reason from the code it explains and make a second artifact to
#: keep in sync, which is DESIGN-013's subject. But the `(rule, date, row)`
#: tuple is not prose — it is a record with one spelling per field, and until
#: TASK-332 round 2 its only home was a hardcoded tuple inside
#: `tests/test_summary_is_asked_for.py`. That was a THIRD copy, and an
#: invisible one: the next author to remove a rule would have written the
#: docstring entry, left this list alone, and the guard would have stayed green
#: over a removal it was not pinning — TASK-330's M5 again, one removal later.
#:
#: The guard now iterates THIS dict and requires every field of every entry to
#: appear in the register. So adding a row here is what arms the guard, and the
#: two copies cannot drift apart silently, which is the property DESIGN-013
#: actually asks for. It is not a licence to delete the prose: the names live
#: inside the reasoning paragraph, so prose and record fall together.
SUMMARY_RULES_REMOVED: dict[str, tuple[str, str]] = {
    "summary-has-no-sentence": ("2026-09-03", "TASK-330"),
    "summary-is-a-fragment": ("2026-09-03", "TASK-330"),
}


def summary_shape(title: str, summary: str) -> list[tuple[str, str]]:
    """Every STRUCTURAL rule this summary breaks, as `(rule, why)` pairs.

    **It lives in `lib` because two tools have to agree about it.**
    `bin/perry-task` refuses a bad summary at the moment of writing and
    `bin/perry-lint` reports one already written; a second copy of the
    predicate is how those two quietly start disagreeing about what they are
    for, which is DESIGN-013's whole subject.
    `tests/test_summary_is_asked_for.py § TestOnePlaceDefinesWhatASummaryIs`
    pins that they answer identically over one corpus. (That citation said
    `tests/test_task_summary.py` until TASK-330; the agreement test has never
    lived there, and a pointer to the wrong file is how the next author
    concludes the agreement is unpinned and writes a second copy.)

    **This function judges structure and nothing else, and the list of things
    it does not judge is part of its contract.** Twice on 2026-09-02 a guard
    on this project tried to recognise bad English and lost — a hedge denylist
    defeated by a retraction using none of its eight words, a push-order regex
    by two synonyms — and the reviewer's verdict was that a denylist over
    English had lost the argument twice. So:

    CHECKED, each a fact about bytes rather than about prose:

    - `summary-missing` — absent, empty, or whitespace only.
    - `summary-repeats-title` — equal to the title once case and punctuation
      are folded away, or one is a prefix of the other. A summary that IS the
      title adds nothing to it by construction; saying so involves no
      judgement of quality.

    NOT CHECKED, deliberately, each for a measured reason:

    - **Whether the summary contains a sentence, and whether it is long
      enough to be one.** Both WERE checked, as `summary-has-no-sentence` and
      `summary-is-a-fragment`, from TASK-325 until 2026-09-03. **The user
      removed them (TASK-330): the quality of a summary is the writing
      agent's responsibility, not a check's, and "does this prose read like
      prose" is not a question this predicate is entitled to answer.** They
      are recorded here rather than simply deleted because a rule that
      vanishes without a reason reads as an oversight to the next author, and
      because this is the obvious pair for that author to re-propose. Neither
      had ever fired: across the 129 summaries on the board at removal both
      counted zero, so nothing on the corpus moved and what changed is only
      what the writer refuses from now on. `SUMMARY_MIN_WORDS` and
      `summary_tokens` outlive them, scoped to `summary-repeats-title`'s
      prefix arm, which needs a threshold for a structural reason.
    - **Whether the summary opens with a bare id.** TASK-325's spec proposed
      exactly this predicate and named `TASK-218` ("DESIGN-012 I1") as its
      example. Measured over the 49 summaries on this board: ten open with a
      bare citation and **all ten are good summaries**, so implemented as
      proposed the rule would have shipped at zero precision over its entire
      true-positive set. A leading citation followed by an explanation is this
      project's house style.
    - **Whether it contains ids, paths or backticks.** 39 of 49 do. That is a
      summary citing its source, which is the behaviour to keep.
    - **Readability, reading level, vocabulary, hedging, tone.** No test of
      any kind. This function does not measure whether a summary is plain
      language and must not be quoted as though it does.
    - **Whether the summary is TRUE of its row.** Nothing structural can
      establish that. It is why TASK-325's backfill left rows blank rather
      than guessing: a confidently wrong summary is worse than an empty field,
      because the empty field at least tells the reader to go and look.
    - **Whether it is shorter than its title.** Considered and rejected: a
      good plain-language gloss of a long shorthand title is frequently
      shorter than it, which is the outcome this whole row wants.
    """
    s = (summary or "").strip()
    if not s:
        return [("summary-missing",
                 "no summary — `perry-explain` on this row prints its title "
                 "back at the reader and nothing else")]
    out: list[tuple[str, str]] = []
    ft, fs = summary_fold(title), summary_fold(s)
    # BOTH must be non-empty. `x.startswith("")` is true for every `x`, so a
    # summary that folds to nothing would otherwise "repeat" every title.
    #
    # **A bare prefix test is not enough, and the fixture that proved it is a
    # row titled "A".** `"a fixture row that exists…"` starts with `"a"`, so
    # every summary on that row read as a repeat of its title. The defect this
    # rule is for is "the summary ADDS NOTHING to the title", so that is what
    # it measures: identical after folding, or one contains the other and the
    # difference between them is under `SUMMARY_MIN_WORDS`. A summary
    # that opens by restating its title and then explains for another forty
    # words is not the defect — it is wordy, and wordiness is a matter of
    # taste, which this check does not have.
    if ft and fs:
        added = abs(summary_tokens(fs) - summary_tokens(ft))
        if fs == ft or ((fs.startswith(ft) or ft.startswith(fs))
                        and added < SUMMARY_MIN_WORDS):
            out.append(("summary-repeats-title",
                        "the summary restates the title rather than "
                        "explaining it — a reader who did not understand the "
                        "title learns nothing new from it"))
    return out
