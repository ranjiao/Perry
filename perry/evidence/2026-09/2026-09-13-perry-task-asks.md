# `perry-task asks` — answered asks and their answers, as a query

**Not a row.** A read surface asked for by the user for aiMark, built in one
sitting and filed here per this project's standing rule that findings go in the
evidence rather than on the board. Contract: `schema/asks-list-contract.md`,
`perry-asks/list/1.0`.

---

## 1. What was missing

aiMark needed to read answered asks and what the answer was. No published
payload carried them:

- `perry-task list --json § asks.items` leaves answered asks out **by design**.
  Its contract row says "the unanswered asks", `asks.open` is pinned to
  `len(items)`, and TASK-170 records the decision not to widen it — a dashboard
  once said "2 items waiting on you" about two questions answered that day.
- `perry-state --section user_input_queue` filters the same way.
- `depends_on_resolved` reaches an answered ask only when some task depends on
  it, and carries `status` as a raw string.

The only route was reading `perry/asks.jsonl` and parsing the answer out of
`status` by hand — which is the set arithmetic aiMark had already refused once.

## 2. What landed

A second surface, the move `events` made one register over.

```bash
perry-task asks                 # the open asks
perry-task asks --all --json    # every ask, answered ones with the answer
```

**It cannot disagree with `list` about which asks are open.** The default
population comes from the same snapshot, through the same
`parsers.ask_is_answered`, carrying the same eight keys as `asks.items`.
`test_it_is_exactly_lists_asks_items` holds that key by key. `--all` adds the
answered asks, and every entry gains `answered`, `answered_on`, `answer` and
`blocks_ids`.

`parsers.ask_answer` lives beside `ask_is_answered` and normalises the cell
exactly as it does. Perry's own board carries `**answered 2026-08-16: 30
days**`, bold on both ends; a second spelling of the strip would have reported
that ask answered with no answer.

`answered` is deliberately wider than `answer`. `dropped …` and `withdrawn …`
close an ask too, and for those `answer` is `""` rather than a guess.

## 3. What the tests caught while it was being built

**`blocks_ids` could not see a key result.** The first pattern was the one
`perry-lint § check_reviews` uses on the same cell, `\b[A-Z]+-\d+\b`. For
`TASK-100, P003-O2-KR3` it returned `["TASK-100"]` — and `USER-929` blocks
exactly `P003-O2-KR3`, so a reverse lookup would have said nothing waits on the
ask that was filed for that KR. The contract page's own example named a KR id,
and the test built from it failed. The pattern now composes both id families,
KR shapes first.

## 4. Constraints met rather than moved

| constraint | how |
|---|---|
| `perry-task --help` under 3000 bytes | was 2971; two summaries shortened, none asserted by any test; now 2986 |
| contract page parity | documented 20 keys, emitted 20, no drift, no unassigned table |
| parity baseline | re-recorded; diffed — only the file count 6 → 7 and the new contract changed, no existing entry moved |
| surface declaration | `test_bin_surface`, 59 green |
| read-only | `asks.jsonl`, `BOARD.md` and the event log byte-identical across a run |

## 5. Mutations

`__pycache__` cleared before every run; both files verified against their
pre-battery snapshots afterwards.

| # | mutation | result |
|---|---|---|
| M1 | the default shows answered asks too | **RED** — 2, incl. `test_it_is_exactly_lists_asks_items` |
| M2 | counts taken over the shown slice, not the register | **RED** — 1 |
| M3 | the answer normalisation drops the `*`/`` ` `` strip | **RED** — 3, incl. `USER-001` and `USER-002` on the live board |
| M4 | the `ask_is_answered` guard inside `ask_answer` removed | **GREEN — the guard was dead, and is gone** |
| M5 | KR shapes removed from `blocks_ids` | **RED** — 1 |
| M6 | answer text lower-cased | **RED** — 3 |
| M7 | `--all` ignored | **RED** — 2 + 2 errors |

**M4 is the one worth reading.** `ask_answer` returned early unless
`ask_is_answered` agreed, and removing that left all 15 tests green. It could
not have done otherwise: a cell that matches `answered YYYY-MM-DD:` after the
strip is non-blank and begins with none of the open prefixes, so the predicate
is always `True` there. The guard read as protection and gave none — the same
shape as the dead skip in TASK-236's round 5 earlier the same day. It was
removed, and the invariant is now stated in the docstring as an invariant
rather than enforced by a check that cannot fire.

## 6. Two held counts caught the new surface, which is what they are for

The first full run carried two reds beyond the session's standing three, and
both reproduced alone:

| test | held | found |
|---|---|---|
| `test_handed_back_root § TestWhichSubcommandsWrite` | 30 `perry-task` subcommands | 31 |
| `test_semantics_on_every_payload § TestTheListIsEveryContractOnDisk` | 6 payloads, one per contract page | 7 pages on disk |

Neither is a defect in `asks`. Each is a hand-kept number that exists so that a
new subcommand or a new contract page cannot arrive unnoticed, and each
reddened on exactly that. The subcommand count is 31 with `asks` named in its
docstring as the read-only addition. `PAYLOADS` gains `perry-asks/list`, which
also joins `EMPTY_TODAY` because its `semantics` is `[]` at 1.0 — left out, the
module would have required a meaning change that has never happened.

## 7. Suite

Second run, after § 6's two counts were updated:

```
131 modules · 3829 tests · 129.3s · 8 workers
✗ 3 of 3829 TEST(S) failed
0. tree guard — ✓ nothing under /Users/bytedance/proj/Perry moved
```

The three are the session's standing reds: two conformance-witness keys in
`test_contract_key_parity` and the clock-dependent
`test_resume.TestStaleRuns.test_a_fresh_run_is_not_stale`. `test_asks_list` is
the 131st module.
