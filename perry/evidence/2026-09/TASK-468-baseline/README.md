# TASK-468 frozen baseline

Captured 2026-09-18T16:18:59+0800, **before any workflow or tool edit**, in the
TASK-468 worktree at base commit `c48e25fe2ca9be598fe7be919b246eaefa30356e`
(main's tip at dispatch). The receipt is `receipt.json` (sha256
`6cf3d642edae34575388b50dc981354956bd3a356e906caf4c522636e73ed6d1`).

## What was captured

- **Commit and host settings.** Host `claude-code` (per `bin/perry-detect-host`),
  Claude Desktop entrypoint, Agent SDK 0.3.274, model `claude-opus-5`, effort
  `high`. The capturing agent is a **child** session
  (`CLAUDE_CODE_CHILD_SESSION=1`); `CLAUDE_CODE_SESSION_ID` names its parent,
  `bcc8bb26-9e88-4097-95fb-951ab3eeeda7`. `PERRY_HOME`, `PERRY_PROJECT`,
  `PERRY_HOST` and every Codex/OpenCode sentinel were unset.
- **Static load.** The five TASK-457 bills at the base commit, with per-file
  bytes and sha256: snapshot 77,257 / 80,000; add-task 99,351 / 100,000;
  close-task 90,213 / 95,000; dispatch 113,558 / 115,000; plan-phase
  107,747 / 110,000. File sizes: `SKILL.md` 20,453; `work/SKILL.md` 36,907;
  `goals/SKILL.md` 22,415; `decide/SKILL.md` 24,081;
  `work/reference/dispatch.md` 31,487.
- **Claude transcripts** (`~/.claude/projects/-Users-bytedance-proj-Perry`):
  58 session files (224,722,971 bytes), 512 subagent files, 20 project
  directories in total. The parent session named by the host identity, read at
  2,813,516 bytes: 956 lines, 0 malformed, 300 usage-bearing records but only
  **167 distinct messages** (the host writes one record per content block and
  repeats the message's usage on each). Deduplicated totals: input 364; cached
  input 35,567,461; cache creation 300,127; output 119,534, of which reasoning
  (`thinking_tokens`) 22,701. Peak per-request context 352,067. It spawned 10
  children (`Agent`/`Task` tool uses); 10 subagent files exist and all carry
  usage: 912 distinct messages; input 1,834; cached input 214,712,683; cache
  creation 4,982,537; output 703,972, of which reasoning 227,730.
- **Codex rollouts** (`~/.codex/sessions`): 459 rollouts, 19 with a Perry cwd,
  3 of those children (`parent_thread_id`), 3 `spawn_agent` calls. 2,164
  cumulative `token_count` snapshots, 86 exact repeats. Summed deltas of the
  cumulative counter, in the host's own field names: input_tokens 293,197,234
  (cached_input_tokens 286,671,744 is inside it), output_tokens 665,533
  (reasoning_output_tokens 198,630 is inside it), total_tokens 293,862,767.
  Models/effort by turn context: gpt-6-astra medium 57, low 29; gpt-5.6-sol
  high 8; gpt-5.5 high 2.

Only paths, counts, sizes, model names and numeric usage fields were read into
the receipt. No transcript text, tool input or tool output was copied.

## The legacy gate at the base commit

The pre-change `bin/perry-context-budget`, run from this child session:

| Invocation | Result |
|---|---|
| `--json` from the worktree cwd | `unknown`, exit 0: the worktree's slug directory does not exist, so it found nothing |
| `--json --root /Users/bytedance/proj/Perry` | **`OVER`, 352,067, exit 1**: it picked the newest file in the main checkout's slug directory, which is the *parent* session's transcript, and reported the parent's context as this child's |

That second row is the defect TASK-468 exists for: newest-file selection gave a
confident current-session verdict about another session.

## Limits

- The Claude parent-session figures are a snapshot of a live, growing file.
  Re-running gives larger numbers; the receipt records the byte size read.
- These are aggregate host figures, not a controlled before/after run. The
  nine matched runs belong to TASK-473.
- Cached token volume is not monetary cost or quota. No conversion was made.

## Method

Run from the worktree root at the base commit:
`python3 capture.py . > receipt.json`. The script (123 lines, sha256
`d8276dd7176a004fc70a81e90f112fe1641eeb2ed9aee78b7c5c9f997e3cfbdd`) is kept
here as evidence of the method, not as shipped code, so it is quoted in this
file rather than committed as a `.py` module:

```python
"""TASK-468 frozen baseline: read-only aggregate over real transcripts.

Emits paths, counts, sizes and numeric usage categories only. No message
content, tool input or tool output is read into the output.
"""
import collections
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

REPO = pathlib.Path(sys.argv[1]).resolve()
HOME = pathlib.Path.home()
PERRY_MAIN = "/Users/bytedance/proj/Perry"
out = {"captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
       "commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}

# Host / model / settings, from environment names that carry no secrets.
env_keys = ["CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION",
            "CLAUDE_EFFORT", "CLAUDE_AGENT_SDK_VERSION", "CLAUDE_CODE_DESKTOP_APP_VERSION",
            "CODEX_THREAD_ID", "CODEX_SANDBOX", "OPENCODE", "PERRY_HOST", "PERRY_HOME", "PERRY_PROJECT"]
out["host_env"] = {k: os.environ.get(k) for k in env_keys}
out["detect_host"] = subprocess.run(["bash", str(REPO / "bin/perry-detect-host")], capture_output=True, text=True).stdout.strip()

# Static load at the base commit.
bills = json.loads(subprocess.run([sys.executable, str(REPO / "bin/perry-context-budget"), "--bill", "all", "--json"],
                                  capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k not in ("PERRY_HOME", "PERRY_PROJECT")}).stdout)
for bill in bills["bills"]:
    for f in bill.get("files", []):
        f["sha256"] = hashlib.sha256((REPO / f["path"]).read_bytes()).hexdigest()
out["static_bills"] = [{k: b.get(k) for k in ("command", "status", "total_bytes", "budget_bytes", "files", "excluded")} for b in bills["bills"]]
out["file_bytes"] = {p: (REPO / p).stat().st_size for p in ["SKILL.md", "work/SKILL.md", "goals/SKILL.md", "decide/SKILL.md", "work/reference/dispatch.md"]}


def claude_usage(path):
    msgs, bad, lines, recs = {}, 0, 0, 0
    models = collections.Counter(); spawned = 0
    with open(path, "rb") as fh:
        for raw in fh:
            lines += 1
            try:
                r = json.loads(raw)
            except ValueError:
                bad += 1; continue
            m = r.get("message") or {}
            if isinstance(m.get("content"), list):
                spawned += sum(1 for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"))
            u = m.get("usage")
            if isinstance(u, dict) and u:
                recs += 1
                msgs[m.get("id") or r.get("requestId") or r.get("uuid")] = u
                models[m.get("model")] += 1
    tot = collections.Counter()
    peak = 0
    for u in msgs.values():
        tot["input"] += u.get("input_tokens", 0)
        tot["cached_input"] += u.get("cache_read_input_tokens", 0)
        tot["cache_creation"] += u.get("cache_creation_input_tokens", 0)
        tot["output"] += u.get("output_tokens", 0)
        tot["reasoning_in_output"] += (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)
        peak = max(peak, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
    return {"lines": lines, "malformed_lines": bad, "usage_records": recs, "distinct_messages": len(msgs),
            "totals": dict(tot), "peak_context": peak, "models": dict(models), "spawn_tool_uses": spawned}


cdir = HOME / ".claude/projects" / PERRY_MAIN.replace("/", "-")
tops = sorted(cdir.glob("*.jsonl"))
subs = sorted(cdir.glob("*/subagents/*.jsonl"))
out["claude_inventory"] = {"dir": str(cdir), "session_files": len(tops), "subagent_files": len(subs),
                           "session_bytes": sum(p.stat().st_size for p in tops),
                           "project_dirs_total": len([d for d in (HOME / ".claude/projects").iterdir() if d.is_dir()])}
sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
main_t = cdir / f"{sid}.jsonl"
if main_t.is_file():
    s = claude_usage(main_t)
    s.update(path=str(main_t), bytes=main_t.stat().st_size, mtime=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(main_t.stat().st_mtime)))
    kids = sorted((cdir / sid / "subagents").glob("*.jsonl"))
    ks = [claude_usage(k) for k in kids]
    s["children"] = {"files": len(kids), "with_usage": sum(1 for k in ks if k["distinct_messages"]),
                     "totals": dict(sum((collections.Counter(k["totals"]) for k in ks), collections.Counter())),
                     "distinct_messages": sum(k["distinct_messages"] for k in ks)}
    newest = max(tops, key=lambda p: p.stat().st_mtime)
    s["newest_file_in_project_dir"] = newest.name
    out["claude_current_parent_session"] = s


def codex_rollout(path):
    meta, snaps, bad = {}, [], 0
    models = collections.Counter(); spawns = 0
    with open(path, "rb") as fh:
        for raw in fh:
            try:
                r = json.loads(raw)
            except ValueError:
                bad += 1; continue
            p = r.get("payload") if isinstance(r.get("payload"), dict) else {}
            if r.get("type") == "session_meta":
                meta = {k: p.get(k) for k in ("id", "cwd", "parent_thread_id", "cli_version")}
            elif r.get("type") == "turn_context":
                models[(p.get("model"), p.get("effort"))] += 1
            elif p.get("type") == "token_count" and p.get("info"):
                snaps.append(p["info"].get("total_token_usage") or {})
            elif p.get("type") in ("function_call", "custom_tool_call") and p.get("name") == "spawn_agent":
                spawns += 1
    tot, prev, dup = collections.Counter(), None, 0
    for s in snaps:
        if s == prev:
            dup += 1; continue
        base = prev if prev and all(s.get(k, 0) >= prev.get(k, 0) for k in s) else {}
        for k, v in s.items():
            tot[k] += v - base.get(k, 0)
        prev = s
    return meta, tot, len(snaps), dup, bad, models, spawns


croot = HOME / ".codex/sessions"
if croot.is_dir():
    rolls = sorted(croot.rglob("*.jsonl"))
    perry = []
    agg = collections.Counter(); models = collections.Counter(); snaps = dups = bad = spawns = child = 0
    for f in rolls:
        meta, tot, n, d, b, m, sp = codex_rollout(f)
        if str(meta.get("cwd") or "").startswith(PERRY_MAIN):
            perry.append(f); agg += tot; models += m; snaps += n; dups += d; bad += b; spawns += sp
            child += bool(meta.get("parent_thread_id"))
    out["codex_inventory"] = {"dir": str(croot), "rollouts": len(rolls), "perry_cwd_rollouts": len(perry),
                              "perry_child_rollouts": child, "perry_spawn_calls": spawns,
                              "token_count_snapshots": snaps, "duplicate_snapshots": dups, "malformed_lines": bad,
                              "models_effort": {f"{k[0]}|{k[1]}": v for k, v in models.most_common()},
                              "totals_raw_host_fields": dict(agg),
                              "first": perry[0].name if perry else None, "last": perry[-1].name if perry else None}

print(json.dumps(out, indent=2, default=str))
```
