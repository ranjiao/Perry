# `dispatch` — the measurements and history behind its rules

Not loaded by `dispatch`. `dispatch.md` and `dispatch-preflight.md` keep every rule, gate and refusal; this page keeps the incidents and measurements that explain them. Moved on 2026-09-21 (TASK-470); the prose is carried over unchanged.

## What dispatch cost in one session

From `dispatch-preflight.md § 0 · Whether to dispatch at all`.

Measured across
**eight dispatches in one session on 2026-09-07**: **seven were handed a base
~500 commits stale** (`TASK-381`), **two collided in a shared scratchpad**
(`TASK-373`), **one left a planted mutation in its tree** when it stopped, and
**one reddened the suite by following its scratch-location brief exactly**
(`TASK-385`). Four of those are rows that exist only because work was
dispatched.

## Why no command performs step 4

From `dispatch-preflight.md` step 4.

Until 2026-09-04 this step was `"$PERRY_HOME/bin/perry-state" --escalation-scan <spec>` and the exit code was the verdict. That command is gone. `USER-916`: *"不要用python代码来检查文件语义。应该去掉这个检查逻辑，让agent自己来判断gate."* — Python is not to judge a document's meaning, `ADR-007` decision 3 says the Python layer never parses a document at all, and five rounds of trying to make the match correct ended with the measurement that settles it: **formatting alone moved the verdict in both directions.** A bold marker or a sentence-final full stop cleared a declared write to the claim surface; bolding an own-tree path `**perry/evidence/…**` made the gate *refuse*, because the head `**perry` contains a `*`. A reader has no such failure mode. The judgement is yours.

## What "eyeball it" cost

From `dispatch-preflight.md` step 4, after **This is not "read the list and eyeball it".**

That is what the step said before TASK-107 and it refused two dispatches in one day over the words "original" and "adopted".

## 4.5 applied

From `dispatch-preflight.md` step 4.5.

This is what refuses `TASK-107`, whose `Files in scope` reads *"`.perry/hook.md`, `work/state/hook_TEMPLATE.md` — the matching rule sentence"* and whose `Deliverable` item 5 says the dropped forms *"are added to `.perry/hook.md` and to the template's defaults"*. It is **not** refused by the nine high-stakes fragments its `Deliverable` quotes — those are tell 2, and a procedure that refused on them is the same procedure that refuses `TASK-244` on the word `setup`.

## Why the stale TTL is 4h

From `dispatch.md § On completion` step 0 and `§ Failure handling`.

Raised from 1h by TASK-160 because the sweep was reaping markers 72 minutes into live runs and the cap silently stopped being the cap.

A failed dispatch that does not release leaks a slot until stale-TTL expires, which since TASK-160 is 4h rather than 1h. The sweep is deliberately slower than the longest cycle this project has measured (2h15m), so a leaked slot is a slot lost for the rest of the afternoon.
