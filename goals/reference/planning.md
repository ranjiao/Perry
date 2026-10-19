# Planning drafts, review and approval

A draft is owned Markdown under `plans/`, attached to the appropriate native
`phase` or `objective` draft item. It holds questions, answers, premise changes,
unknowns, scope and the last pending question as narrative. Native state carries
lifecycle/approval, not a duplicate frontmatter register. This replaces every
legacy `perry-goals draft` operation; no separate finalizer is needed.

Persist the first answer before the next question. On resume, read the attachment
and native events, show the pending question, and avoid counting it twice. Use
the elicitation bank and stop at its question budget with a visible provisional
draft. Do not restart the interview or silently change the horizon.

When consequential gaps are resolved, show the absolute attachment path, its
SHA256 and a concise summary. Present approve / change / user edit / abandon.
Silence, continuing discussion, approval of one answer and a clean quality pass
are not approval of the complete draft. User edit means wait, then re-read.
Any change to reviewed bytes invalidates approval; obtain a fresh explicit
choice before moving the draft. Save the real consent reference and reviewed
hash in `approval_ref`/event note. Never impersonate a human actor.

On approval, use the setup/phase procedure to create and relate the remaining
native records and move drafts to their approved states. Report every partial
write and the minted IDs if interrupted. Do not auto-activate on startup.
Abandon uses the declared withdraw/drop transition with the user's reason and
retains the narrative. Completion hands off only what the user approved.
