# {{project name}}

{{One sentence: what this team or function produces, and for whom.}}

## Read this first, every session

`STATE.md` — what is in flight, what is blocked, what shipped. Then `INTAKE.md`
if you are picking up new work.

## Layout

| Path | What | Rule |
|---|---|---|
| `STATE.md` | What is true now | Update at the end of every session |
| `INTAKE.md` | Unrouted incoming requests | Triage before starting anything new |
| `deliverables/` | The work itself | One file per deliverable |
| `runbooks/` | Recurring procedures | Follow, then improve if it was wrong |
| `incidents/` | What went wrong and why | Written after, not during |
| `journal/YYYY-MM.md` | Append-only history | One line per meaningful event |
| `DECISIONS.md` | Durable calls | Append-only |

## How work gets done here

1. **Triage intake before starting.** Unrouted requests are this project's
   version of clutter: they pile up, get half-remembered, and resurface as
   emergencies. Every intake item leaves the queue as scheduled, delegated, or
   declined — never by going quiet.
2. **Check `runbooks/` before improvising.** If a runbook exists, follow it. If
   it was wrong, fix it in the same session — a runbook nobody corrects is how
   the next incident gets improvised from scratch.
3. **Finish against the check**, not against a feeling:
   ```bash
   bin/deliverable-lint
   ```
   Structure, unresolved placeholders, and sign-off. Non-zero exit means not
   done.
4. **Append to `journal/`** as you go. Never rewrite it.

## The gate

**Nothing outward-facing ships without a named human sign-off.** Published
posts, customer messages, anything with the project's name on it: draft it,
revise it, run the lint — then stop and ask. Record the sign-off in the
deliverable as `Sign-off: <name>, YYYY-MM-DD`.

An agent may judge whether a draft meets its criteria. It may not judge whether
the criteria were the right ones, and that is the judgement publishing needs.

## Sessions

Sessions stay out of each other's way by **owning different deliverables** —
one session per artifact, incident, or piece. The shared surfaces are
`STATE.md` (small, rewritten, so keep edits short) and `journal/`
(append-only, so it never conflicts).

## Voice and conventions

- {{Tone rules for anything written for an audience.}}
- {{Names, terms, or spellings that must be exact.}}
- {{What never goes in writing.}}
