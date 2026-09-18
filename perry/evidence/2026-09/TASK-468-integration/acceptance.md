# Integrated TASK-468 — session-bound usage measurement

Date: 2026-09-18.

**Authority:**
- The user's request to execute TASK-468–473 (the USER-967/968 iteration).
- USER-969: +166 line exception.
- USER-970: the ≤0 lines rule binds Objective 4 only, so this unlinked row is not bound. Its final net is +235.

No push, tag or public release.

## Identity

- **Frozen base:** `gate/task-468-base-20260918` = 820da3b1849df4f7155baf976b1045c6590bd129.
- **Delivery:** `worktree-agent-abf710762750f9d9b`.
  - Round 1 head: 5f182d3c.
  - Repair head: fe52036d, repair code 5752ff71.
  - The baseline was committed first, at 26a4053c.
- **Review:** `review-task-468` at 35b545eb (V4 FAIL, then re-review PASS-WITH-FINDINGS).
- **Gate input:** `integ/task-468` = review branch + release 0.1.17.
- **Final candidate:** `integ/task-468-final` = 3e0255df21ff5170014ddc8b7a877b3d2f86053b (artifact-only durations commit).
- **Main after merge:** fast-forward to 3e0255df; tree equal to the verified candidate.

## Gates

| Gate | Result |
|---|---|
| Full merged | 155 modules / 4,379 tests PASS |
| Receipt verification | VERIFIED before and after merge (frozen base) |
| Slow | 159 modules / 4,482 tests PASS |

## Task acceptance

**Round 1 V4: FAIL.** Four findings:
- H1: forked Codex children double-counted their parent's usage (+26.7% on a real parent).
- H2: Claude Workflow children were missed while coverage read complete.
- M1: unrecorded reasoning was shown as a measured 0.
- PMO check: in the real Desktop main session the tool read `unknown`.

**Repair and re-review: PASS-WITH-FINDINGS.**
- H1, H2 and M1 are fixed and verified on real data.
- The H1 fix leaves 379 plain rollouts unchanged, and 17 children each drop by exactly their inherited amount.
- L3–L7 are resolved.

**Desktop limitation, verified by the PMO.** In the Desktop main session:
- `CLAUDE_CODE_CHILD_SESSION=1`;
- `CLAUDE_CODE_SESSION_ID` equals the main transcript id;
- `AI_AGENT=claude-code_2-1-274_agent`, the same value subagents see.

No environment signal separates the main session from its subagents. The gate therefore stays `unknown` on Desktop, and autopilot falls back to `--max-dispatches`. This is documented in `reference/host-capabilities.md` and `work/reference/autopilot.md`.

**Carried to TASK-471**, which owns session budget checks. These are appended to its spec:
- R-M1 (Medium): on the plain Claude CLI, a subagent may bind its main session as `current`. The original defect, simulated. Settle it before any gate advice is relied on for Claude.
- R-L1: in a forked Codex child, the last `session_meta` wins. Fail-safe, but it misreports children.
- R-L2: two parts of the H1 fix are untested (mutants S2, S3 survive).
- R-L3: the explicit `--session` path is the only Desktop verdict and is undocumented.

TASK-468 closes at V4.

## Architecture review

Reviewer: an independent architecture reviewer (Claude Opus 5, fresh context, not the task author), 2026-09-18T09:40:18Z. Bound to base 820da3b1 and head 3e0255df.

**Triggers:** module architecture edit TRUE (`bin/ARCHITECTURE.md` §2 gains a descriptive subsection). All others FALSE. The JSON shape is not a §5-pinned contract.

**Decision: PASS.**
- The subprocess call to `perry-detect-host` is not an import.
- The host transcript reads are the calling session's own host logs, not Perry project state (§1, §3 hold).
- NN-3, NN-4 and NN-5 hold. Tests set `HOME` to a temp directory and strip the host environment.
- A refused bill now exits 1, aligning with the §5 exit contract.

**Non-blocking descriptive follow-ups:**
- `bin/ARCHITECTURE.md` §2 "The one tool that reaches outside" still names only `perry-codex-preflight`.
- No §8 change-log entry.

**User decision the reviewer raised:** NN-1 (ARCHITECTURE.md:242–248) lists no exception, yet `perry-context-budget` has long parsed `.perry/config.jsonl` directly. This predates this row, and `bin/README.md` now names it as a deviation. Should it be recorded as a Known exception under NN-1, or be routed through `viewer/parsers` in a later row? Asked separately; it does not block this integration.
