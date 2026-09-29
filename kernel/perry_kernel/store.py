"""The store: sqlite3 in WAL mode, one transaction per command (§ 5.7).

Every write, live or replayed, goes through `apply_event`. `import` replays an
export through the same function a live command writes through, so a replay
cannot disagree with the writes it replays.
"""

from __future__ import annotations

import json
import random
import sqlite3
import time
import urllib.parse
from pathlib import Path

from .errors import KernelError
from .values import canonical, same

APPLICATION_ID = 0x5045524B  # "PERK"
FORMAT = 1
BUSY_TIMEOUT_S = 5.0

#: One statement per entry: `executescript` would COMMIT the open transaction.
SCHEMA = (
    "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE template (version INTEGER PRIMARY KEY, body TEXT NOT NULL, "
    "applied_seq INTEGER NOT NULL, applied_at TEXT NOT NULL)",
    "CREATE TABLE item (id TEXT PRIMARY KEY, type TEXT NOT NULL, "
    "prefix TEXT NOT NULL, num INTEGER NOT NULL, state TEXT, "
    "seq INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
    "CREATE INDEX item_order ON item (prefix, num)",
    "CREATE TABLE value (item TEXT NOT NULL, field TEXT NOT NULL, "
    "value TEXT NOT NULL, PRIMARY KEY (item, field))",
    "CREATE TABLE relation (kind TEXT NOT NULL, src TEXT NOT NULL, "
    "dst TEXT NOT NULL, PRIMARY KEY (kind, src, dst))",
    "CREATE INDEX relation_dst ON relation (kind, dst)",
    "CREATE TABLE attachment (item TEXT NOT NULL, ref TEXT NOT NULL, "
    "hash TEXT, PRIMARY KEY (item, ref))",
    "CREATE TABLE event (seq INTEGER PRIMARY KEY, at TEXT NOT NULL, "
    "actor TEXT, command TEXT NOT NULL, items TEXT NOT NULL, transition TEXT, "
    "changes TEXT NOT NULL, note TEXT, warnings TEXT NOT NULL)",
    "CREATE TABLE ceiling (prefix TEXT PRIMARY KEY, n INTEGER NOT NULL)",
    # Defence in depth for NN-K10 and the append-only log: the store itself
    # refuses what no command is allowed to do.
    "CREATE TRIGGER event_append_only_u BEFORE UPDATE ON event "
    "BEGIN SELECT RAISE(ABORT, 'events are append-only'); END",
    "CREATE TRIGGER event_append_only_d BEFORE DELETE ON event "
    "BEGIN SELECT RAISE(ABORT, 'events are append-only'); END",
    "CREATE TRIGGER item_never_deleted BEFORE DELETE ON item "
    "BEGIN SELECT RAISE(ABORT, 'no command deletes an item'); END",
    "CREATE TRIGGER ceiling_never_falls BEFORE UPDATE ON ceiling "
    "WHEN NEW.n < OLD.n "
    "BEGIN SELECT RAISE(ABORT, 'a ceiling is never lowered'); END",
    "CREATE TRIGGER ceiling_never_deleted BEFORE DELETE ON ceiling "
    "BEGIN SELECT RAISE(ABORT, 'a ceiling is never lowered'); END",
)

TABLES = ("meta", "template", "item", "value", "relation", "attachment",
          "event", "ceiling")


#: The longest number part an id can have: a type pads to at most 18 digits
#: (`template.MAX_DIGITS`), and a minted number never passes 2^53, which has
#: 16. Checked before `int()`, which refuses more than 4,300 digits by raising.
MAX_ID_DIGITS = 18


def split_id(item_id: str):
    """`(prefix, number)`, or None when `item_id` is not an id's shape."""
    if not isinstance(item_id, str) or "-" not in item_id:
        return None
    prefix, _, digits = item_id.partition("-")
    if (not prefix or not digits.isascii() or not digits.isdigit()
            or len(digits) > MAX_ID_DIGITS):
        return None
    return prefix, int(digits)


def id_order(item_id: str):
    parts = split_id(item_id)
    return parts if parts else (item_id, -1)


def _deadline() -> float:
    return time.monotonic() + BUSY_TIMEOUT_S


def _busy(exc: sqlite3.Error) -> bool:
    low = str(exc).lower()
    return "locked" in low or "busy" in low


def _retrying(fn, deadline: float):
    """`fn()`, run again while sqlite answers busy or locked and `deadline`
    has not passed. sqlite's busy handler waits out a lock another connection
    holds, but it is not called where waiting could deadlock (two
    connections upgrading one file's lock at once, as two first inits do):
    SQLITE_BUSY then comes back at once. `store_busy` means the lock was not
    acquired within 5 s, so the kernel waits the rest of the 5 s itself."""
    while True:
        try:
            return fn()
        except sqlite3.OperationalError as exc:
            if not _busy(exc) or time.monotonic() >= deadline:
                raise
            time.sleep(0.005 + random.random() * 0.02)


def _db_error(exc: sqlite3.Error, path) -> KernelError:
    text = str(exc)
    low = text.lower()
    if "locked" in low or "busy" in low:
        return KernelError("store_busy", f"{path}: the write lock was not "
                                         f"acquired within "
                                         f"{BUSY_TIMEOUT_S:g} s",
                           {"store": str(path)})
    if "not a database" in low:
        return KernelError("store_foreign", f"{path} is not a kernel store",
                           {"store": str(path)})
    if "readonly" in low or "unable to open" in low or "disk i/o" in low:
        return KernelError("io_error", f"{path}: {text}", {"path": str(path)})
    return KernelError("store_corrupt", f"{path}: {text}", {"store": str(path)})


class Store:
    """One open store. Use as a context manager: the transaction is the
    `with` block, and leaving it by an exception rolls it back."""

    def __init__(self, conn: sqlite3.Connection, path, write: bool):
        self.conn = conn
        self.path = path
        self.write = write
        self._committed = False
        self._mismatch = "internal"

    # ── opening ────────────────────────────────────────────────────────────

    @staticmethod
    def _connect(path, *, create: bool) -> sqlite3.Connection:
        if str(path) == ":memory:":
            conn = sqlite3.connect(":memory:", isolation_level=None)
        else:
            mode = "rwc" if create else "rw"
            uri = f"file:{urllib.parse.quote(str(path))}?mode={mode}"
            conn = sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_S,
                                   isolation_level=None)
        conn.execute(f"PRAGMA busy_timeout = {int(BUSY_TIMEOUT_S * 1000)}")
        return conn

    @staticmethod
    def probe(path) -> str:
        """`absent`, `empty` (no kernel content), `store`, or raises
        store_foreign / store_version / store_corrupt. A probe is a hint read
        outside any write transaction; a write decides again inside its own
        (`contents`), because another process can init in between (F6).

        The header and the table list are read in ONE read snapshot. Read one
        statement at a time, a concurrent init committing between them
        showed `application_id` 0 beside `user_version` 1, and the store was
        called foreign (round 4)."""
        p = Path(path)
        try:
            exists, is_dir = p.exists(), p.is_dir()
        except OSError as exc:
            raise KernelError("io_error", f"cannot inspect {p}: "
                                          f"{exc.strerror}", {"path": str(p)})
        if not exists:
            return "absent"
        if is_dir:
            raise KernelError("store_foreign", f"{p} is a directory",
                              {"store": str(p)})

        def read_header():
            conn = Store._connect(p, create=False)
            try:
                conn.execute("BEGIN")
                return Store._header(conn)
            finally:
                conn.close()  # ends the read transaction

        try:
            header = _retrying(read_header, _deadline())
        except sqlite3.Error as exc:
            raise _db_error(exc, p)
        return Store._verdict(header, p)

    @staticmethod
    def _header(conn):
        """`(application_id, user_version, table names)`, read on `conn` in
        whatever transaction it has open. sqlite errors propagate."""
        app = conn.execute("PRAGMA application_id").fetchone()[0]
        ver = conn.execute("PRAGMA user_version").fetchone()[0]
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")]
        return app, ver, names

    @staticmethod
    def _verdict(header, p) -> str:
        """`empty` or `store`; raises store_foreign / version / corrupt."""
        app, ver, names = header
        if app == 0 and ver == 0 and not names:
            return "empty"
        if app != APPLICATION_ID:
            raise KernelError("store_foreign", f"{p} is not a kernel store; it "
                                               f"is left untouched",
                              {"store": str(p)})
        if ver > FORMAT:
            raise KernelError("store_version",
                              f"{p} is format {ver}; this kernel reads "
                              f"format {FORMAT}", {"store": str(p),
                                                   "format": ver})
        if ver != FORMAT or not set(TABLES) <= set(names):
            raise KernelError("store_corrupt", f"{p}: the kernel's tables are "
                                               f"incomplete", {"store": str(p)})
        return "store"

    def contents(self) -> str:
        """`empty` or `store`, decided inside this store's open transaction:
        a write that must know whether the store is initialised asks here,
        under the lock, never from an earlier probe."""
        try:
            header = self._header(self.conn)
        except sqlite3.Error as exc:
            raise _db_error(exc, self.path)
        return self._verdict(header, self.path)

    @classmethod
    def open(cls, path, *, write: bool) -> "Store":
        """Open an initialised store and begin the command's transaction.

        The deadline is set before the probe, not after it (TASK-489, F4): a
        probe that waited out a busy store leaves the steps below only what
        remains of the 5 s, so `store_busy` comes within 5 s of the call
        rather than after the probe's wait and a whole deadline more."""
        deadline = _deadline()
        state = cls.probe(path)
        if state in ("absent", "empty"):
            raise KernelError("store_missing",
                              f"{path} has not been initialised; run init",
                              {"store": str(path)})
        try:
            conn = cls._connect(path, create=False)
            mode = _retrying(lambda: conn.execute(
                "PRAGMA journal_mode").fetchone()[0], deadline)
            if str(mode).lower() != "wal":
                conn.close()
                raise KernelError("store_corrupt",
                                  f"{path}: journal_mode is {mode}, not wal",
                                  {"store": str(path)})
            _retrying(lambda: conn.execute("PRAGMA synchronous = FULL"),
                      deadline)
            if conn.execute("PRAGMA synchronous").fetchone()[0] != 2:
                conn.close()
                raise KernelError("store_corrupt", f"{path}: synchronous=FULL "
                                                   f"could not be set",
                                  {"store": str(path)})
            _retrying(lambda: conn.execute(
                "BEGIN IMMEDIATE" if write else "BEGIN"), deadline)
            if not write:
                # A deferred read transaction takes its snapshot at the first
                # read; take it now.
                _retrying(lambda: conn.execute(
                    "SELECT value FROM meta WHERE key = 'format'").fetchall(),
                    deadline)
            return cls(conn, path, write)
        except sqlite3.Error as exc:
            raise _db_error(exc, path)

    @classmethod
    def create(cls, path, *, memory: bool = False) -> "Store":
        """A new store's file, in WAL mode, inside an open write transaction.
        The schema is written by `initialise` in the same transaction."""
        deadline = _deadline()
        try:
            if memory:
                conn = cls._connect(":memory:", create=True)
            else:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                conn = cls._connect(path, create=True)
                mode = _retrying(lambda: conn.execute(
                    "PRAGMA journal_mode = WAL").fetchone()[0], deadline)
                if str(mode).lower() != "wal":
                    conn.close()
                    raise KernelError("io_error", f"{path}: WAL mode refused",
                                      {"path": str(path)})
                _retrying(lambda: conn.execute("PRAGMA synchronous = FULL"),
                          deadline)
            _retrying(lambda: conn.execute("BEGIN IMMEDIATE"), deadline)
            return cls(conn, path, True)
        except OSError as exc:
            raise KernelError("io_error", f"cannot create {path}: "
                                          f"{exc.strerror}", {"path": str(path)})
        except sqlite3.Error as exc:
            raise _db_error(exc, path)

    def initialise(self):
        """The schema and the format marker, in the open transaction. The
        state root arrives by the `init` event's `state_root` change."""
        self.q(f"PRAGMA application_id = {APPLICATION_ID}")
        self.q(f"PRAGMA user_version = {FORMAT}")
        for statement in SCHEMA:
            self.q(statement)
        self.q("INSERT INTO meta VALUES ('format', ?)", (str(FORMAT),))

    # ── the transaction ────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if not self._committed:
                self.conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        finally:
            self.conn.close()
        return False

    def commit(self):
        try:
            self.conn.execute("COMMIT")
        except sqlite3.Error as exc:
            raise _db_error(exc, self.path)
        self._committed = True

    def rollback(self):
        try:
            self.conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        self._committed = True  # nothing left to roll back on exit

    def q(self, sql: str, params=()):
        try:
            return self.conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            raise _db_error(exc, self.path)

    # ── reads ──────────────────────────────────────────────────────────────

    def _loads(self, text, where: str):
        """A stored JSON value, or store_corrupt: a row that cannot be read
        back is damage, not an internal fault (§ 5.1)."""
        try:
            return json.loads(text)
        except (TypeError, ValueError):
            raise KernelError("store_corrupt",
                              f"{self.path}: {where} cannot be read back",
                              {"store": str(self.path), "row": where})

    def meta(self, key: str):
        rows = self.q("SELECT value FROM meta WHERE key = ?", (key,))
        return rows[0][0] if rows else None

    def meta_seq(self, key: str):
        """A meta value that holds an event seq, or None when unset. Text
        that is not a short run of ASCII digits is damage, checked before
        `int()` sees it."""
        raw = self.meta(key)
        if raw is None:
            return None
        if not (raw.isascii() and raw.isdigit() and len(raw) <= 19):
            raise KernelError("store_corrupt", f"{self.path}: meta {key} "
                                               f"cannot be read back",
                              {"store": str(self.path), "row": f"meta {key}"})
        return int(raw)

    def set_meta(self, key: str, value: str):
        self.q("INSERT INTO meta VALUES (?, ?) ON CONFLICT(key) DO UPDATE "
               "SET value = excluded.value", (key, value))

    def store_seq(self) -> int:
        return self.q("SELECT COALESCE(MAX(seq), 0) FROM event")[0][0]

    def event_count(self) -> int:
        return self.q("SELECT COUNT(*) FROM event")[0][0]

    def template_row(self):
        rows = self.q("SELECT version, body, applied_seq, applied_at "
                      "FROM template ORDER BY version DESC LIMIT 1")
        if not rows:
            return None
        version, body, applied_seq, applied_at = rows[0]
        return {"version": version,
                "template": self._loads(body, f"template {version}"),
                "applied_seq": applied_seq, "applied_at": applied_at}

    def item_row(self, item_id: str):
        rows = self.q("SELECT id, type, state, seq, created_at, updated_at "
                      "FROM item WHERE id = ?", (item_id,))
        if not rows:
            return None
        i, t, s, seq, c, u = rows[0]
        return {"id": i, "type": t, "state": s, "seq": seq, "created_at": c,
                "updated_at": u}

    def item_type(self, item_id: str):
        rows = self.q("SELECT type FROM item WHERE id = ?", (item_id,))
        return rows[0][0] if rows else None

    def values(self, item_id: str) -> dict:
        return {f: self._loads(v, f"{item_id}.{f}") for f, v in self.q(
            "SELECT field, value FROM value WHERE item = ?", (item_id,))}

    def all_item_ids(self) -> list[str]:
        return [r[0] for r in self.q("SELECT id FROM item ORDER BY prefix, num")]

    def edges(self, kind=None, src=None, dst=None) -> list[tuple]:
        sql, params, where = "SELECT kind, src, dst FROM relation", [], []
        for col, val in (("kind", kind), ("src", src), ("dst", dst)):
            if val is not None:
                where.append(f"{col} = ?")
                params.append(val)
        if where:
            sql += " WHERE " + " AND ".join(where)
        rows = self.q(sql, params)
        return sorted(rows, key=lambda r: (r[0], id_order(r[1]),
                                           id_order(r[2])))

    def edges_touching(self, item_id: str) -> list[tuple]:
        rows = self.q("SELECT kind, src, dst FROM relation WHERE src = ? OR "
                      "dst = ?", (item_id, item_id))
        return sorted(rows, key=lambda r: (r[0], id_order(r[1]),
                                           id_order(r[2])))

    def has_edge(self, kind, src, dst) -> bool:
        return bool(self.q("SELECT 1 FROM relation WHERE kind = ? AND src = ? "
                           "AND dst = ?", (kind, src, dst)))

    def reaches(self, kind: str, start: str, target: str) -> bool:
        """Is `target` reachable from `start` along edges of `kind`?"""
        seen, frontier = {start}, [start]
        while frontier:
            node = frontier.pop()
            if node == target:
                return True
            for (nxt,) in self.q("SELECT dst FROM relation WHERE kind = ? AND "
                                 "src = ?", (kind, node)):
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
        return False

    def attachments(self, item_id: str) -> list[dict]:
        return [{"ref": r, "hash": h} for r, h in self.q(
            "SELECT ref, hash FROM attachment WHERE item = ? ORDER BY ref",
            (item_id,))]

    def attachment_hash(self, item_id: str, ref: str):
        """`(present, hash)`."""
        rows = self.q("SELECT hash FROM attachment WHERE item = ? AND ref = ?",
                      (item_id, ref))
        return (True, rows[0][0]) if rows else (False, None)

    def ceiling(self, prefix: str):
        rows = self.q("SELECT n FROM ceiling WHERE prefix = ?", (prefix,))
        return rows[0][0] if rows else None

    def items_in(self, item_type: str, state: str) -> list[str]:
        return [r[0] for r in self.q(
            "SELECT id FROM item WHERE type = ? AND state = ? "
            "ORDER BY prefix, num", (item_type, state))]

    def events(self) -> list[dict]:
        return [self._event(r) for r in self.q(
            "SELECT seq, at, actor, command, items, transition, changes, note, "
            "warnings FROM event ORDER BY seq")]

    def _event(self, row) -> dict:
        seq, at, actor, command, items, transition, changes, note, warn = row
        where = f"event {seq}"
        return {"seq": seq, "at": at,
                "actor": (self._loads(actor, where) if actor is not None
                          else None),
                "command": command, "items": self._loads(items, where),
                "transition": transition,
                "changes": self._loads(changes, where),
                "note": note, "warnings": self._loads(warn, where)}

    # ── the one write path ────────────────────────────────────────────────

    def current(self, primary, key: str):
        """The stored value a change key names, for the before comparison."""
        if key == "state_root":
            return self.meta("state_root")
        if key == "template":
            row = self.template_row()
            return row["version"] if row else None
        if key.startswith("ceiling:"):
            return self.ceiling(key[len("ceiling:"):])
        if key.startswith("rel:"):
            _, kind, src, dst = key.split(":", 3)
            return self.has_edge(kind, src, dst)
        row = self.item_row(primary) if primary else None
        if key == "type":
            return row["type"] if row else None
        if key == "state":
            return row["state"] if row else None
        if key.startswith("field:"):
            rows = self.q("SELECT value FROM value WHERE item = ? AND "
                          "field = ?", (primary, key[len("field:"):]))
            return (self._loads(rows[0][0], f"{primary}.{key[6:]}") if rows
                    else None)
        if key.startswith("attach:"):
            present, digest = self.attachment_hash(primary,
                                                   key[len("attach:"):])
            return {"hash": digest} if present else None
        raise KernelError("export_invalid", f"unknown change key {key}",
                          {"key": key})

    def apply_event(self, event: dict, *, mismatch: str, check=None) -> None:
        """Replay: apply the changes, then append the event."""
        self.apply_changes(event, mismatch=mismatch, check=check)
        self.append_event(event)

    def apply_changes(self, event: dict, *, mismatch: str,
                      check=None) -> None:
        """Apply every change of `event` and bump each touched item's seq.
        `items[0]` is the item that the `type`, `state`, `field:` and
        `attach:` keys belong to.

        Every change's `before` is compared with the stored value first. A
        replay that disagrees is `export_invalid`; a live write that disagrees
        is a kernel defect, so the caller passes `internal`.

        `check(event, primary, key, after)`, when given, runs after the
        before comparison and before the change lands, so it sees the store
        as the event's earlier changes left it. `import` passes the check
        that holds a replayed value to the template in force (TASK-489); a
        live write has already checked its values against the template."""
        seq, at = event["seq"], event["at"]
        items = event["items"]
        primary = items[0] if items else None
        self._mismatch = mismatch
        for change in event["changes"]:
            key, before, after = change["key"], change["before"], change["after"]
            now = self.current(primary, key)
            if not same(now, before):
                raise KernelError(
                    mismatch,
                    f"event {seq}: {key} is {canonical(now)} in the store, "
                    f"and the event says it was {canonical(before)}",
                    {"seq": seq, "key": key, "stored": now, "before": before})
            if check is not None:
                check(event, primary, key, after)
            self._apply_change(primary, key, after, seq, at)
        for item_id in items:
            self.q("UPDATE item SET seq = ?, updated_at = ? WHERE id = ?",
                   (seq, at, item_id))
            row = self.item_row(item_id)
            if row is None or row["state"] is None:
                raise KernelError(mismatch,
                                  f"event {seq} leaves {item_id} without a "
                                  f"type and a state", {"seq": seq})

    def append_event(self, event: dict) -> None:
        self.q("INSERT INTO event VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
               (event["seq"], event["at"],
                canonical(event["actor"]) if event["actor"] is not None
                else None,
                event["command"], canonical(event["items"]),
                event["transition"], canonical(event["changes"]),
                event["note"], canonical(event["warnings"])))

    def _apply_change(self, primary, key, after, seq, at):
        if key == "state_root":
            self.set_meta("state_root", after)
        elif key == "template":
            self.q("INSERT INTO template VALUES (?, ?, ?, ?)",
                   (after["version"], json.dumps(after, ensure_ascii=False),
                    seq, at))
        elif key.startswith("ceiling:"):
            self._raise_ceiling(key[len("ceiling:"):], after)
        elif key.startswith("rel:"):
            _, kind, src, dst = key.split(":", 3)
            if self.has_edge(kind, src, dst) == bool(after):
                # No command writes a relation change that flips nothing: `rel
                # add` of an edge that exists, and `rel remove` of one that
                # does not, are `unchanged` and append no event (NN-K8). A
                # replayed one is refused for every kind alike, so a no-op
                # `parent` change and a no-op `blocks` change get one answer
                # (TASK-487 round 3, F1; decided in TASK-489).
                raise KernelError(self._mismatch,
                                  f"event {seq}: {key} changes nothing; the "
                                  f"edge is already "
                                  f"{'there' if after else 'absent'}",
                                  {"seq": seq, "key": key})
            if after:
                for end in (src, dst):
                    if self.item_type(end) is None:
                        raise KernelError(self._mismatch,
                                          f"event {seq}: {key} names no item "
                                          f"{end}", {"seq": seq, "key": key})
                self._check_edge_shape(kind, src, dst, seq)
                self.q("INSERT OR IGNORE INTO relation VALUES (?, ?, ?)",
                       (kind, src, dst))
            else:
                self.q("DELETE FROM relation WHERE kind = ? AND src = ? AND "
                       "dst = ?", (kind, src, dst))
        elif key == "type":
            prefix, num = split_id(primary)
            self.q("INSERT INTO item (id, type, prefix, num, state, seq, "
                   "created_at, updated_at) VALUES (?, ?, ?, ?, NULL, ?, ?, ?)",
                   (primary, after, prefix, num, seq, at, at))
            self._raise_ceiling(prefix, num)
        elif key == "state":
            self.q("UPDATE item SET state = ? WHERE id = ?", (after, primary))
        elif key.startswith("field:"):
            field = key[len("field:"):]
            if after is None:
                self.q("DELETE FROM value WHERE item = ? AND field = ?",
                       (primary, field))
            else:
                self.q("INSERT INTO value VALUES (?, ?, ?) ON CONFLICT(item, "
                       "field) DO UPDATE SET value = excluded.value",
                       (primary, field, canonical(after)))
        elif key.startswith("attach:"):
            ref = key[len("attach:"):]
            if after is None:
                self.q("DELETE FROM attachment WHERE item = ? AND ref = ?",
                       (primary, ref))
            else:
                self.q("INSERT INTO attachment VALUES (?, ?, ?) ON CONFLICT("
                       "item, ref) DO UPDATE SET hash = excluded.hash",
                       (primary, ref, after.get("hash")))
        else:
            raise KernelError("internal", f"unknown change key {key}")

    def _check_edge_shape(self, kind: str, src: str, dst: str, seq: int):
        """The shape every edge keeps, checked on the one path that writes
        edges: `rel add`, both ends of `item create`'s relations, and
        `import`'s replay. No self-edge, at most one `parent` per item, and no
        `blocks` or `parent` cycle. A live write is refused with the rule's
        own code; a replay that breaks one is `export_invalid`."""
        replay = self._mismatch != "internal"
        details = {"kind": kind, "from": src, "to": dst}

        def refuse(code, message, **extra):
            if replay:
                raise KernelError(self._mismatch, f"event {seq}: {message}",
                                  {"seq": seq, **details, **extra})
            raise KernelError(code, message, {**details, **extra})

        if src == dst:
            refuse("relation_invalid", f"{src} cannot relate to itself")
        if kind == "parent":
            # The edge being added is never among these. A live write reaches
            # here only for an edge that is absent: `rel add` of an existing
            # edge is `unchanged` before it gets this far, and `item create`
            # makes edges to an item that did not exist. A replayed change
            # reaches here only if it flips the edge: `_apply_change` refuses
            # one whose edge is already there (`before: true, after: true`)
            # first. So src -> dst does not exist yet on any path.
            others = [d for _k, _s, d in self.edges(kind="parent", src=src)]
            if others:
                refuse("relation_invalid", f"{src} already has a parent, "
                                           f"{others[0]}", parent=others[0])
        if kind in ("blocks", "parent") and self.reaches(kind, dst, src):
            refuse("relation_cycle",
                   f"{kind} {src} -> {dst} would close a cycle")

    def _raise_ceiling(self, prefix: str, n: int):
        now = self.ceiling(prefix)
        if now is None:
            self.q("INSERT INTO ceiling VALUES (?, ?)", (prefix, n))
        elif n > now:
            self.q("UPDATE ceiling SET n = ? WHERE prefix = ?", (n, prefix))
