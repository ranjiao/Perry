# TASK-290 — round 2: PARTIAL RECORD, NOT A VERDICT

> **This is not a review and it reaches no verdict.** A V4 review of TASK-290
> round 2 was started on branch `review/task-290-round2-v4` (cut from `main` at
> `7f890f9`) and was stopped by the coordinator partway through orientation,
> before any criterion had been measured: the user decided that
> `bin/perry-state --escalation-scan` should not exist at all — Python is not to
> judge a document's semantics, and the dispatching agent reads the spec and
> `.perry/hook.md`'s high-stakes list and makes the call itself. That retires
> the row rather than answering it.
>
> **No PASS and no FAIL should be read out of this file.** Nothing below is a
> judgement of round 2's fix. What is written down here is only the part of the
> review that had already been produced when the stop arrived, kept because the
> replacement procedure has to state in words what the scanner did in code.

## What was actually established first-hand

Two facts, both from commands run in this worktree against `main` at `7f890f9`.

**The corpus is 148 specs, and the union is 35 fragments.**

```
$ ls perry/evidence/*/*-spec.md | wc -l
     148

$ bin/perry-state --root . --escalation-scan perry/evidence/2026-09/TASK-290-spec.md
{ … "armed": true, "verdict": "pass", "fragments_scanned": 35,
  "discounted": {"Deliverable": {"evidence/": [
      {"token": "evidence/", "why": "this-project's-own-tree"}]}} }
EXIT=0
```

That is the denominator only. **The pass / refuse / unarmed census was NOT
re-derived** — the enumeration script was written and never run. The figures in
circulation (the brief's *148 scanned · 133 pass · 15 refuse · 0 unarmed* on
2026-09-03, and round 2's own *147 scanned · 16 refused*) are therefore
**unverified by this document**, and they do not agree with each other on the
denominator. Anyone deciding what the agent-side procedure must catch should
re-run the enumeration rather than inherit either number:

```
for f in perry/evidence/*/*-spec.md; do bin/perry-state --root . --escalation-scan "$f"; done
```

**No gate-direction finding of my own.** No control spec was constructed, no
foreign-root case was run, TASK-107 was not re-scanned, and no mutation was
planted. The four claims below are read out of the round documents and the
source, **not** reproduced here, and each is marked as such.

## The foreign-root judgement — the part worth carrying forward

This is the item the replacement procedure most needs in words, and it is
first-hand: read from `viewer/parsers.py` in this worktree, not from a round
document.

`path_root_is_foreign` (`viewer/parsers.py:4446`) is the whole of what the
scanner meant by "someone else's tree", and it is a five-line rule with no
semantics in it:

```python
tok = token or ""
if tok[:1] in ("/", "~", "$"):
    return True
segments = tok.split("/")
if any(s == ".." for s in segments):
    return True
head = segments[0]
return any(c in head for c in "<>{}*$")
```

Stated as a procedure a human or a dispatching agent can follow:

- **Relative is internal, and that is the entire rule.** A relative path
  resolves against the root of the project the spec belongs to, so `evidence/`,
  `perry/evidence/2026-09/x.md` and `evidence/**/*-spec.md` all name *this*
  project's tree and cannot name anyone else's.
- **Foreign is five shapes**: an absolute path (`/srv/…`), a home anchor
  (`~/…`), a variable anchor (`$PERRY_HOME/…`), an upward escape (`../…`), and
  an **unresolved root** (`<target>/evidence/`, `{{project}}/design/`).
- **The unresolved root is a deliberate judgement in the safe direction.** A
  root nobody has resolved is not a root known to be this project. The code's
  own comment: a gate that guesses *"probably mine"* about a placeholder is the
  guessing the row existed to stop. **A replacement procedure that omits this
  case is weaker than the code it replaces**, and this is the single most
  likely thing to be dropped when the rule is rewritten in prose, because it is
  the one clause that is not obvious from an example.

**Why this constrained the character class, and why that matters to the
rewrite.** `_PATH_CHAR` (`viewer/parsers.py:4375`) admits `~ $ < > { } *`
*because* `path_root_is_foreign` recognises a foreign root **by** those
characters. Round 1's instruction was to narrow that class to filename
characters; the implementing agent refused it and measured that narrowing it
would re-root `~/other-project/evidence/2026-09/` to `project/evidence/2026`
and `$PERRY_HOME/inputs/` to `perry_home/inputs/`, both of which then read as
*this project's own tree* and **stop refusing**. That refusal-with-measurement
is recorded in `perry/evidence/2026-09/TASK-290-round2-result.md`; **I did not
re-run it**, and the reason it is worth keeping is not the verdict but the
shape of the trap: the marker that identifies a foreign root and the noise that
has to be stripped off a path are the same characters, so any rewrite that
strips formatting before deciding ownership will lose the ownership signal with
it. A prose procedure has the same trap — "ignore markdown around the path"
and "`~` means someone else's home" are the same character.

## Claims left unverified, for whoever inherits this

Each of these is asserted by a round document and was **not** reproduced here.
Listed because they are the questions a replacement procedure has to answer,
not because they are established.

1. **Citation vs. write.** Round 2 claims the specs blocked for citing a path
   now pass, via a `names-a-longer-file` discount measured against a filename
   character class (`_NAME_EDGE = [A-Za-z0-9_]`) applied to rule 1 only.
   Unverified. The brief also names five refusals still believed to be citation
   false positives — TASK-099, TASK-108, TASK-139, TASK-220, TASK-244 — which,
   if true, means the cite-vs-write problem was **not** fully closed in code and
   the agent-side procedure inherits it whole.
2. **True positives still refuse.** `perry/evidence/2026-09/TASK-107-spec.md`
   is expected to refuse on `~/.claude/skills`, the `ln -s` variants,
   `publish`, `rm -rf` and `--force-with-lease`. Not re-scanned here. **That
   fragment list is a ready-made checklist for the human procedure** — it is
   what a genuine high-stakes write looks like in this corpus.
3. **The known remaining hole.** `_schema/state-schema.json_` — a markdown
   italic whose trailing `_` is a word character — is reported to still pass,
   because `escalation_pattern`'s right-edge guard is `(?![A-Za-z0-9_])`
   (`viewer/parsers.py:4332`, `_ESC_WORD` at `:4298`). Filed as TASK-329. Not
   reproduced here. The generalisable lesson survives the deletion: **formatting
   alone was enough to change the verdict**, in both directions — round 1 found
   bold and a sentence-final period clearing the claim surface, and round 2
   found bolding an own-tree path (`**perry/evidence/…**`) making it *refuse*,
   because `path_root_is_foreign` reads the head `**perry` as containing `*`.
   A human reading the spec has no such failure mode, which is the strongest
   argument on record for the decision that superseded this row.
4. **Suite and lint.** Not run. Round 2 reports 114 modules / 3268 tests green
   and `bin/perry-lint --root .` at 0 errors / 37 warnings; the brief separately
   notes two known-red anti-vacuity controls in
   `tests/test_contract_key_parity.py` that decay with wall-clock time
   (TASK-335). None of this was observed here.

## What was not done at all

The census enumeration; every control spec (foreign-root, false-pass,
true-positive); the TASK-107 re-scan; the `_schema/state-schema.json_`
confirmation; every mutation; `tests/run`; `bin/perry-lint`. The review reached
the end of reading the spec, the round-2 result, the round-1 review and the
relevant source, and stopped there.

=== RESULT ===
Branch: review/task-290-round2-v4
Verdict: NONE — review stopped before measurement; row superseded by the decision to delete `bin/perry-state --escalation-scan`
Criteria met: 0 of 6 measured (not 0 of 6 failed — none were run)
Criteria NOT met: none adjudicated; all six left unmeasured
Corpus re-derived: NOT re-derived — denominator only, 148 spec files, 35 fragments armed
Mutations re-run: 0
Does the gate now refuse LESS anywhere it should not: not established either way
Tree clean: (see the commit on this branch; only this file was added)
=== END RESULT ===
