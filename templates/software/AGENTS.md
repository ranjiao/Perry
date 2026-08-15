# {{project name}}

{{One sentence: what this produces and who consumes it.}}

## Commands

- Install: `{{npm ci}}`
- Test: `{{npm test}}` — run this before claiming any work is done
- Lint / typecheck: `{{npm run lint && npm run typecheck}}`
- Run locally: `{{npm run dev}}` (port {{3000}})

## How work gets done here

1. **Read `STATE.md` first.** It is the current truth; this file is only rules.
2. **Spec before code** for anything touching more than one file. Write it to
   `specs/<name>.md`: files and interfaces involved, what is out of scope, and
   an end-to-end check that proves it works. Then implement from the spec.
3. **Finish with evidence.** Paste the test output or the command you ran. A
   claim of done that cites nothing is a claim about confidence, not about the
   work.
4. **Log durable decisions** in `DECISIONS.md` — architecture, tool choice,
   anything reversed. Not turn-level choices.

## Session lanes

{{Pick one and delete the rest. Escalate only after two real collisions.}}

- **Serial** — one session at a time. Default; nothing to coordinate.
- **Ownership partition** — parallel sessions share this checkout, each owning
  a disjoint file set. Declare it here before starting:
  | Session | Owns | Must not touch |
  |---|---|---|
  | {{A}} | {{src/api/**}} | {{src/web/**}} |
- **Worktree isolation** — one `git worktree` per session, own branch, own
  port, own DB. Merge order and the integration review live in `STATE.md`.

## Conventions

- {{Style rule that differs from the language default.}}
- {{Env var or setup quirk that is not discoverable from the code.}}
- {{Branch / PR etiquette.}}

## Not here

Anything discoverable by reading the code. If a line above would not change
what an agent does, delete it — a long rules file gets ignored a line at a
time, and you cannot tell which line went first.
