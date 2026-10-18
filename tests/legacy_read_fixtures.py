"""Explicit archived inputs for the frozen readers.

These functions declare JSONL snapshots and history under temporary Project
roots. They never invoke or intercept a command, and test no writer behavior.
The native writer tests use kernel_work_support instead.
"""
import json
import re
import tempfile
from datetime import date
from pathlib import Path
from task_writer_support import PT

STAMP = "2026-09-01T12:00:00+08:00"


def rows(p, name):
    root = p.root.resolve()
    if not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise AssertionError("archived fixtures require a temporary project")
    path = root / name
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def write(p, name, values):
    rows(p, name)  # enforce the temporary-root boundary before touching disk
    (p.root / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in values))


def event(p, name, row, before="", after="", field="status"):
    path = p.root / ".perry/events.jsonl"
    records = rows(p, ".perry/events.jsonl")
    records.append({"ts": STAMP, "event": name, "id": row["id"], "title": row.get("title", ""),
                    "from": before, "to": after, "field": field, "actor": "archived-fixture",
                    "track": row.get("track", "main"), "owner": row.get("owner", "Coding Agent"),
                    "evidence": row.get("evidence", ""), "rung": row.get("verification", "V3")})
    path.parent.mkdir(parents=True, exist_ok=True)
    write(p, ".perry/events.jsonl", records)


def seed_task(p, *, event_name="add", **fields):
    current = rows(p, "tasks.jsonl")
    ceiling = max([int(m.group(1)) for r in current
                   if (m := re.fullmatch(r"TASK-(\d+)", r["id"]))] or [0])
    tid = f"TASK-{ceiling + 1:03}"
    p.seed_task(tid, **fields)
    record = next(r for r in rows(p, "tasks.jsonl") if r["id"] == tid)
    event(p, event_name, record, None, record["status"])
    return record


def set_task(p, tid, *, event_name, **fields):
    current = rows(p, "tasks.jsonl")
    record = next(r for r in current if r["id"] == tid)
    field = {"next": "next_action", "retitle": "title", "rung": "verification",
             "evidence": "evidence", "summary": "summary"}.get(event_name, "status")
    before = record.get(field, "")
    record.update(fields)
    write(p, "tasks.jsonl", current)
    event(p, event_name, record, before, record.get(field, ""), field)
    return record


def seed_ask(p, *, needed, asked=None, blocks="", status="pending"):
    current = rows(p, "asks.jsonl")
    record = {"id": f"USER-{len(current)+1:03}", "needed": needed,
              "asked": asked or str(date.today()), "blocks": blocks,
              "status": status, "answered": status.startswith("answered"), "order": len(current)}
    write(p, "asks.jsonl", [*current, record])
    return record


def set_ask(p, tid, *, answer):
    current = rows(p, "asks.jsonl")
    record = next(r for r in current if r["id"] == tid)
    record.update(status=f"answered {date.today()} — {answer}", answered=True)
    write(p, "asks.jsonl", current)
    return record


def seed_intake(p, *, title, arrived=None):
    current = rows(p, "intake.jsonl")
    record = {"request": title, "arrived": arrived or str(date.today()),
              "outcome": "—", "discharged": False, "order": len(current)}
    write(p, "intake.jsonl", [*current, record])
    return record


def seed_cadence(p, *, title, frequency):
    current = rows(p, "cadence.jsonl")
    record = {"id": f"CAD-{len(current)+1:03}", "title": title, "owner": "fixture",
              "frequency": frequency, "next_due": "n/a", "last_run": "", "last_evidence": "", "order": len(current)}
    write(p, "cadence.jsonl", [*current, record])
    return record
