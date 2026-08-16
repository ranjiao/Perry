# `/pmo viewer` — start the web console and open it in a browser

Purpose: let a **non-technical user** open Perry's read-only web console with one
command, without knowing about venvs, ports, or shell scripts. The agent starts
the local service in the background, waits until it answers, and opens the user's
browser at the address. `/pmo browse` is an alias.

The viewer itself is documented in `viewer/README.md` (pages, design, what it does
NOT do). This file is only about **launching** it for the user.

The viewer is the *local, zero-setup* consumption surface. The primary one is
**aiMark** (`~/proj/aimark`), which watches the project directory and renders it
live. Reach for the viewer when aiMark isn't running or isn't wanted; reach for
aiMark otherwise. Both read the same tier 1/2 markdown — neither is authoritative
over the other, and neither writes to the project.

## Sub-actions

| Invocation | Does |
|---|---|
| `/pmo viewer` (or `/pmo browse`) | Start (if not already running) + open the browser at the URL. Default. |
| `/pmo viewer stop` | Stop a viewer this session started. |
| `/pmo viewer --port <N>` | Use a specific port (default 8080). |

## Procedure — start + open

Run from the project directory (where `BOARD.md` lives — the standup's CWD).

1. **Pick the port.** Default `8080` (or `--port`, or `$PERRY_VIEWER_PORT`).

2. **Is it already up?** Check `curl -sf "http://127.0.0.1:$PORT/" >/dev/null`. If it answers, skip to step 5 (just open the browser) — don't start a second copy.

3. **Start the service in the background.** Always use the built-in launcher `$PERRY_HOME/bin/perry-viewer` (it auto-creates the venv + installs Flask/markdown on first run — the robust path for non-dev users; ignore any project-local wrapper script). The launcher foregrounds/`exec`s the server and blocks, so it MUST be backgrounded or it freezes the session:
   - **Claude Code**: launch with the Bash tool's `run_in_background: true`:
     ```
     bash "$PERRY_HOME/bin/perry-viewer" --port <PORT>
     ```
     Remember the returned background task id for `stop`.
   - **Codex / no background tool** (`$HOST = codex-cli`, see `$PERRY_HOME/reference/host-capabilities.md`):
     ```
     mkdir -p ~/.cache/perry
     nohup bash "$PERRY_HOME/bin/perry-viewer" --port <PORT> > ~/.cache/perry/viewer.log 2>&1 &
     ```

4. **Wait until it answers.** Poll `curl -sf "http://127.0.0.1:$PORT/" >/dev/null` until it returns 0. **First run can take ~60s** (venv creation + `pip install`); allow up to 90s. Do **not** use a foreground `sleep` loop (the harness blocks it) — on Claude Code use the **Monitor** tool with an until-condition on that curl command; on Codex, a short `for` loop with `sleep` in the backgrounded shell is fine. If it never comes up, read `~/.cache/perry/viewer.log` (or the background task output) and surface the error — common causes: no `python3` on PATH, pip/network failure during first-run install, port already taken by another app.

5. **Open the browser at the address** — for the human, use the OS default browser (not an agent-browsing tool):
   ```
   URL="http://127.0.0.1:$PORT/"
   case "$(uname)" in
     Darwin) open "$URL" ;;
     Linux)  xdg-open "$URL" >/dev/null 2>&1 & ;;         # WSL: falls through if xdg-open missing
     *)      cmd.exe /c start "" "$URL" 2>/dev/null \
               || powershell.exe -NoProfile -Command "Start-Process '$URL'" 2>/dev/null ;;
   esac
   ```
   If none succeeds (headless / SSH box with no display), don't fail — print the URL and tell the user to open it themselves. On Claude Code you may additionally offer to render it in the in-app Browser pane (`mcp__Claude_Browser__preview_start` with the URL) if the user prefers it in-panel.

6. **Report** — one compact block:
   ```
   🅿  Perry viewer running · project: <project name>
      → http://127.0.0.1:<PORT>/   (opened in your browser)
      Pages: Today · Board · OKR · Phase · Risks · Atlas · Pulse
      Stop any time: /pmo viewer stop   (or just close it / Ctrl-C)
   ```

## Procedure — stop

- **Claude Code**: stop the background task this session started (its task id from step 3) via the harness (TaskStop). Confirm the port stops answering.
- **Fallback (any host)**: `pkill -f "viewer/serve.py"` — the viewer has no PID file; matching on its script path is safe on a single-user localhost box.
- Tell the user it's stopped; nothing runs afterward (no daemon).

## Notes & guardrails

- **Localhost only.** The viewer binds `127.0.0.1` and holds private project state — never pass a flag or edit that would bind it to `0.0.0.0` or expose it beyond the loopback interface. If a user asks to share it, decline and explain it's read-only-local by design (`viewer/README.md § What it does NOT do`).
- **Read-only.** The viewer never writes project files; every mutation still goes through `/pmo`, `/okr`, `/design` in chat. Opening it is safe to do any time, including mid-standup.
- **Port already in use.** If `$PORT` is taken by a *non-Perry* process, retry once on `$PORT+1` and report the port actually used. If it's taken by an existing Perry viewer, just open that one.
- **Idempotent.** Re-running `/pmo viewer` when it's already up just re-opens the browser; it never starts a second server on the same port.
