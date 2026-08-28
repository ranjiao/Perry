# TASK-200 — one board, two roles: an extraction report from `~/proj/gimegime-pmo`

> Back-reference: `perry/design/DESIGN-006-roles-and-knowledge.md` § 5.2 (card
> model), § 6.1 phase F (pass condition), § 7 (escalation-union risk row),
> decision #4 (`Role:` on task rows).
> Source project: `~/proj/gimegime-pmo` and `~/proj/gimegime` — both read-only,
> nothing written to either. Perry worktree `coding/task-200`.
> Everything below ran under `PYTHONNOUSERSITE=1 /usr/bin/python3`.

**This is a proposal, not a live card.** No `.perry/roles/` directory was
created in this repo or anywhere else, and `perry-conform declare` was not run.
The card text was passed to `viewer/parsers.py:parse_role_card` directly, which
is byte-for-byte the code path `read_role_cards` would take, with no file on
disk.

---

## 0 · The answer, before the evidence

The row's question, as corrected: **can one board carry two roles whose
escalation boundaries are different in kind?**

**Partly, and the part that fails is the money.** Measured on the real project:

1. **The two boundaries are disjoint.** The shipped `coding` card and the
   drafted `advisory-checker` card contribute **29 fragments to the union and
   share exactly zero**. They are not two settings of one boundary; they are two
   vocabularies.
2. **The union handles the overlap case correctly, and this is a real win.** A
   工程线 row owned by `Coding Agent` whose *subject* is an investment risk cap
   (`BOARD.md:53 POLICY-CAP-CODE-SYNC`, `rules.py` R-2 上限 30%→40%) scans
   `pass` under the coding card alone and **`refuse` under the union**, on
   `max_position`, attributed to `role:advisory-checker`. The additive union is
   the mechanism that makes a hybrid board safe against exactly this row, and
   nothing else in Perry would have caught it.
3. **The union cannot see the 投资线 rows at all.** `BOARD.md:57 DUE-ADR-010` —
   `9/1 无条件 redeploy … 卖 XLU 600 股` — scans **`pass` under every
   combination**: hook alone, +coding, +advisory, +both. A −$40,819-class row
   (`BOARD.md:47`) has no token in it that any role's `Must escalate` can name.
4. **The reason is not Chinese, and not "action vs. path".** Both of those
   framings in the spec are wrong about the code (§ 3.1). The reasons are:
   polarity — the invariant `系统永不下单` names the *prohibition*, and entering
   it inverts the gate (§ 5.2) — and a length floor that discards **18 of the 20**
   Chinese trading verbs, `下单` included, **without a lint warning** (§ 5.3, § 8).
5. **`DUE-*` is a third shape the model has no field for** (§ 7).

Field-by-field: `Context`, `May touch`, `Accepted by` carry as-is. `Loads`
carries the syntax and resolves to the empty set. `Default rung` carries with a
derivation. `Executors` cannot name this role's real executor. `Must escalate`
carries only the code-shaped half of the invariant.

---

## 1 · What the project actually is

Not a finance project. **A hybrid, on one board, in a split-repo layout.**

- `.perry/config.md:4` — `Repo layout: split`; `:5` PMO repo
  `/Users/bytedance/proj/Gimegime-pmo`, `:6` code repo
  `/Users/bytedance/proj/Gimegime`.
- `.perry/config.md:14` — `Split was triggered 2026-05-05 after ≥3
  branch-contention incidents on 5/4 with Coding Agent and PMO Agent both
  committing in the code repo.`

So one board manages both the software development of `~/proj/gimegime` and
real investment work against ~$3M. The board declares the partition itself:

- `BOARD.md:35` — `ARCH-V2/ADVISOR/POLICY/FRAMEWORK/INSTRUMENT-*` … `RES-N` …
  `INFRA-N` … `CADENCE-*` = 工程线 families.
- `BOARD.md:37` — `**`IPS-*` / `ALLOC-*` / `DUE-*` = 投资线**（2026-07-28
  新增）—— 政策起草 / 资产配置 / 日期型强制动作。与工程线物理分区，见下一节。`
- `BOARD.md:39` `## Open — 投资线（政策 · 配置 · 到期动作）` and `BOARD.md:74`
  `## Open — 工程线 · phase #004 W24（流程层）` — two sections, one file.
- `BOARD.md:41` gives the reason for the partition: `投资线与工程线节奏差一个
  数量级（月/季 vs 天/周）`.

**The two lines' rows are different objects.** `BOARD.md:47 THESIS-2015HK-GAP`
is `9,320 股 · 成本 HKD 83.43 · 现价 49.06 · **−41.2%（−$40,819）**` — the row's
content *is* a holding. `BOARD.md:81 THESIS-REGISTRY-v0` is `registry
schema+三件套闸门+kill-signal 监控 wire（kr:P-O1.3）| Coding Agent`. [[old-form]]
> The `kr:P-O1.3` above is quoted verbatim from `~/proj/gimegime-pmo`, which
> TASK-180 did not migrate — that project is outside this repository and its
> ids are its own. Rewriting a quotation would misreport what its board says.

**And the partition is not clean, which is the load-bearing fact for this row.**
Three rows sitting *inside* the 投资线 section are owned by `Coding Agent`:
`BOARD.md:53 POLICY-CAP-CODE-SYNC`, `BOARD.md:54 INFRA-BRIEF-COMMITS-ALL`,
`BOARD.md:55 POLICY-REFS-CODE`. The board is partitioned by **cadence and
subject**, not by role. Any model that assumes section ⇒ role is already wrong
about this file.

**The 工程线 half already has its card.** Those rows say `Owner: Coding Agent`
and `packs/software-ops/roles/coding.md` ships. So only one card needed
extracting.

---

## 2 · The proposed card — 投资线

Shape per `work/state/role_card_TEMPLATE.md`; the four `##` sections are the
closed set `schema/state-schema.json § files[id=role-card].sections.allowed`
enforces. Chinese kept in the original per `.perry/config.md:3` — a translated
invariant is a different invariant.

```markdown
# Role · advisory-checker

- Accepted by: user
- Default rung: V5
- Executors: any

## Context

顾问户 `advisory` 的第二顾问：审第一顾问（RM / 投资经理）的提议。
观察 / 审顾问提议 / 记账 —— 只产 recommendation + reasoning trace。
决策权 100% 在用户；所有 advisory action 经用户手动执行（NN-1 v3 Tier 3）。
不读 research cognition board（NN-16）；不 active pull 爬 RM portal。

## Loads

- knowledge: bos, look-capital, saas-holdings-research, market-context

## May touch

- write: `evidence/`, `journal/`, `policy/theses/`
- run: read-only MCP only — `mcp__gimegime__get_brief`,
  `mcp__gimegime__get_portfolio_summary`, `mcp__gimegime__get_position`,
  `mcp__gimegime__list_positions`, `mcp__gimegime__get_risk_metrics`,
  `mcp__gimegime__get_recent_journal_entries`

## Must escalate

- 系统永不下单 — any `submit_order`, `place_order`, `execute_trade`, `broker`,
  `alpaca`, `下单`
- any write to `data/advisory/positions.yaml`
- any credential: `.env`, `broker_creds`, `alpaca_key`, `ALPACA_API_KEY`,
  `OPENROUTER_API_KEY`
- any risk-gate parameter: `risk_limits.py`, `kill_switch`, `max_daily_loss`,
  `max_position`, `stale_order_minutes`
- any strategy lifecycle move: `phase=paper`, `phase=live`, `enable-paper`,
  `enable_live`, `enable-live`
- any cost-ceiling change: `monthly_spend`, `cost_ceiling`
- anything needing a `Type: Trading` decision
- advisor-checker 不 active pull 爬 RM portal（ToS / 风控 / 维护风险）
```

**One card, not three, and not four.** § 5.2's existence test applied first.
`ARCHITECTURE.md:22–24` declares three account domains with three system roles,
but only `advisory` has a boundary distinct from the default: `auto_live` is
`dormant` (`:24`), and `auto_paper`'s role is `跑实验 / 学习 / propose
promotion` (`:23`) — that is the shipped `research` card with a different
knowledge topic. Three cards would have been the proliferation § 7 warns of.

### 2.1 · Citations — every line

| Card line | Source |
|---|---|
| `# Role · advisory-checker` | `ARCHITECTURE.md:44` — `A_AC["<b>Advisor-checker</b>…(本户专属新组件)"]`; the component name is the project's |
| `Accepted by: user` | `ARCHITECTURE.md:3` — `Owner: user (agents 起草, user 定稿)`; `ARCHITECTURE.md:28` — `决策权 100% 在用户`; `.perry/hook.md:10` — `投资判断必须可解释、可审计、可由用户最终决定` |
| `Default rung: V5` | **Derived, not quoted.** `.perry/hook.md:114–117 § Subjective verification (always human)` names tasks whose verification `无法归约为 CLI command exit code 或数值断言`; `bin/perry-explain V5` = "human sign-off". The hook-line → `V5` mapping is mine. See § 4.2. |
| `Executors: any` | **Contradicted by the project — § 4.3.** `.perry/hook.md:84` — `` `BoS RM` (human, not an Agent) … PMO can draft messages for the user to send; cannot send directly `` |
| Context L1 | `ARCHITECTURE.md:28` — `advisory 侧 system 是"审第一顾问（RM）的第二顾问"`; `ARCHITECTURE.md:22` — operator `RM / 投资经理（外部）` |
| Context L2 | `ARCHITECTURE.md:43` — `观察 / 审顾问提议 / 记账`; `evidence/2026-05/INFRA-advisor-checker-spec.md:86` — `pipeline 只产 recommendation + reasoning trace，无任何下单/交易调用` |
| Context L3 | `ARCHITECTURE.md:28`; `ARCHITECTURE.md:456` — `所有 advisory action 经用户手动执行（NN-1 v3 Tier 3）`; `OKR.md:108` |
| Context L4 | `ARCHITECTURE.md:458` — `**advisor-checker 不读 research cognition board**（NN-16）`; `OKR.md:113` — `**advisor-checker passive only**：不 active pull 爬 RM portal（ToS/风控/维护风险）` |
| `knowledge: bos, look-capital, saas-holdings-research, market-context` | `knowledge/INDEX.md § Active by topic` — the four topic headings verbatim (`### bos (2)`, `### look-capital (3)`, `### saas-holdings-research (2)`, `### market-context (1)`) |
| *(no `pack:` line)* | **Deliberate absence.** `packs/` ships only `software-ops`; there is no finance pack. An em-dash placeholder would parse as a topic name. |
| `write: evidence/` | `.perry/hook.md:41` — `Evidence file under `evidence/<YYYY-MM>/<TASK-ID>-promotion-<from>-to-<to>.md`` |
| `write: journal/` | `ARCHITECTURE.md:87` — `Decision journal … 统一 append-only daily markdown` |
| `write: policy/theses/` | `.perry/hook.md:58` — `**All investment policy lives under `policy/`**`; `BOARD.md:46` — `` `policy/theses/DUOL.md`（三轴判据，注册表第二条）`` |
| `run:` the six MCP tools | `.perry/hook.md:129–134 § Project-preferred MCP tools`, verbatim; read-only per `ARCHITECTURE.md:463` — `MCP server read-only` |
| escalate `submit_order`, `place_order`, `execute_trade`, `broker`, `alpaca` | `evidence/2026-06/WEB-ADVISORY-INGEST-report.md:98` — `no `submit_order` / `place_order` / `execute_trade` / `broker` / `alpaca` reference anywhere…`; `journal/2026-05/2026-05-29.md:163` — `AST-walk test 验证无 order/broker/execute call` |
| escalate `下单` | `ARCHITECTURE.md:43` (`系统永不下单`), `:22` (`**永不下单**`), `OKR.md:108`. **Never reaches the union — § 5.3.** |
| escalate `data/advisory/positions.yaml` | `ARCHITECTURE.md:45` — `事件驱动 · 手编 YAML + git commit / <code>data/advisory/positions.yaml</code>` |
| escalate `.env`, `broker_creds`, `alpaca_key`, `ALPACA_API_KEY`, `OPENROUTER_API_KEY` | `.perry/hook.md:97`, `.perry/hook.md:107` |
| escalate `risk_limits.py`, `kill_switch`, `max_daily_loss`, `max_position`, `stale_order_minutes` | `.perry/hook.md:95`, `.perry/hook.md:106` |
| escalate `phase=paper`, `phase=live`, `enable-paper`, `enable_live`, `enable-live` | `.perry/hook.md:96`, `.perry/hook.md:105` |
| escalate `monthly_spend`, `cost_ceiling` | `.perry/hook.md:109` |
| escalate `Type: Trading` | `.perry/hook.md:70` — `` `Trading` — anything authorizing or restricting real-account / paper / live operations ``; `ARCHITECTURE.md:26` — `Gate 3 小额实资金（需 ADR Type: Trading）` |
| escalate `advisor-checker 不 active pull 爬 RM portal…` | `OKR.md:113`. **Left unbackticked on purpose — it is the linter's own warning case, exercised deliberately; § 5.5.** |

Nothing in the card is uncited. The two lines that are not quotations are marked
above as derived (`Default rung`) or as contradicted (`Executors`).

---

## 3 · What was read and run

Single implementation, read in full before running: `viewer/parsers.py:3099–3395`
— `escalation_fragments`, `hook_escalation_lines`, `RoleCard`,
`parse_role_card`, `read_role_cards`, `escalation_union`, `escalation_pattern`,
`matching_escalations`, `scan_spec_escalations`. Its two callers:
`bin/perry-lint:1542–1622` (`check_role_cards`, including the
`role-escalation-not-extractable` warning) and `bin/perry-state:1934–1963`
(`escalation_scan`). Contract: `schema/roles-list-contract.md`.

### 3.1 · Two things the spec got wrong about the code

Following the code, per standing instruction:

1. **"a path … the scanner can match against what a task touches" / "nothing in
   a task's file list matches it."** There is no file list.
   `scan_spec_escalations` (`viewer/parsers.py:3351`) matches fragments against
   the **prose text** of three named spec sections —
   `ESCALATION_TOUCHES = ("Files in scope", "Deliverable")` and
   `ESCALATION_DISCLAIMS = "Out of scope"` (`:3345–3349`). It reads markdown, not
   a manifest. A verb inside a `## Deliverable` sentence is exactly as matchable
   as a path. The shipped cards already rely on this: `coding.md:24` escalates on
   `` `force-push` ``, `` `rebase` ``; `review.md:25` on `` `reproduce` ``. Those
   are verbs, and the action/path distinction the spec builds its question on is
   not a distinction the extractor makes.
2. **"That is an action, not a path" as the reason CJK fails.** CJK is
   deliberately supported. `viewer/parsers.py:3277–3288` writes the word class
   out as `_ESC_WORD = "[A-Za-z0-9_]"` and documents why: `\b` does not exist in
   Chinese, so a `\b`-guarded matcher would word-bound the English half of a hook
   and leave the Chinese half bare (ADR-007's `CLOCK_RE` round). A fully-CJK
   fragment therefore gets no guards and becomes a plain substring test.
   `escalation_fragments(["- any `系统永不下单`"])` returns `['系统永不下单']`, and
   it matches. **The invariant extracts. It fails for other reasons.**

---

## 4 · Field-by-field verdict

### 4.1 · `## Context` — **carries as-is**

Four lines, all quotation, no software assumption: an external human
counterparty, a decision-rights split, two negative constraints.
`parse_role_card` returns it as an opaque string rendered verbatim into the
delegation prompt, so the Chinese survives untouched. No breaking case found.
The only strain is compression — the identity is spread over
`ARCHITECTURE.md:22/28/43/456` and `OKR.md:108/113`, and four lines is a
summary, not a distortion.

### 4.2 · `Accepted by` + `Default rung` — **carries, with one derivation**

`Accepted by: user` is exact. `Default rung: V5` is derived: the project states
its acceptance standard as a *class of task* (`.perry/hook.md:116` — verification
that `无法归约为 CLI command exit code 或数值断言`), never as a rung.

*The concrete break, and it is small.* The role's rung is not constant.
`.perry/hook.md:114–117` makes human verification a property of the task
(research candidate selection, backtest acceptance, stage-gate approval), and
this same role also does 记账 — routine record-keeping that is plainly not V5. One
`Default rung` per role forces the strict floor onto the routine work, because
"the stricter wins". That cost lands harder on a finance role than a software
one: a finance role's cheap work and its irreversible work sit in the same job,
where a software role can be split by repository.

### 4.3 · `Executors` — **does not carry**

`Executors: any` is the only honest value and it is wrong. **The executor of an
advisory action is a human being outside the project.** `.perry/hook.md:84`:
`` `BoS RM` (human, not an Agent) … PMO can draft messages for the user to send;
cannot send directly. Treat as `User` with a long external latency (typically 1–2
business days for replies) ``. `ARCHITECTURE.md:314` puts the same fact in the
architecture: `用户手动 → RM 执行<br/>(顾问户, system 永不下单)`.

The axis was defined against runtimes — § 5.2 gives `any` or "codex only", and
§ 5.5 keeps `bin/perry-dispatch-limit` untouched because "limits govern
executors, not roles". `.perry/config.md:7` lists the project's runtimes as
`claude-subagent, codex`, and `:20` adds a third, `manual`. A counterparty with a
two-business-day latency is none of those. gimegime-pmo already invented the
missing object and left it in free text under `## Special agents available`
(`.perry/hook.md:82–85`) — the exact line § 5.5 says role cards replace. **They
do not.** Two of the four "special agents" there are humans, and the card model
has no field for either.

Not fatal — `Executors: any` degrades to today's behaviour — but phase F cannot
claim that free-text line is closed. It is closed for software roles only.

### 4.4 · `## Loads` — **carries the syntax, resolves to the empty set**

The four topics parse (`loads_knowledge = ['bos', 'look-capital',
'saas-holdings-research', 'market-context']`) and all four are real headings in
`knowledge/INDEX.md`. Mechanism intact.

*The concrete case that breaks it:* § 5.4 injects "every non-archived **card** in
R's subscribed topics". gimegime-pmo has **zero** knowledge cards —
`grep -rl "Kind: knowledge" knowledge/` returns nothing and `knowledge/INDEX.md`
has no `## Cards by topic` section. All 16 markdown files under `knowledge/` are
event digests, which DESIGN-006 § 1.2 explicitly distinguishes from domain
knowledge. The subscription resolves to nothing on the one project the pass
condition names.

Loosening "card" to "file in the topic" fails worse:
`knowledge/look-capital/2026-08-FCN-monthly-digest.md` is **23,013 bytes** — one
file, roughly ten times § 5.4's "size-capped precisely so subscription stays
affordable" budget — and `knowledge/look-capital/` is 1.2 MB with its PDFs.
§ 5.4's remedy ("a topic that outgrows the budget is the signal to split
topics") does not apply: a monthly FCN report is one claim-bearing document, and
splitting `look-capital` by month yields twelve oversized topics instead of one.

**Verdict: carries with a change** — a real project's existing knowledge tree
must be promoted into cards before `Loads` means anything, and DESIGN-006 phase B
lists bulk import as out of scope.

### 4.5 · `## May touch` — **carries as-is**

Both bullets are advisory prose, rendered verbatim, uninterpreted.
`run: read-only MCP only` maps cleanly onto § 5.3's source-of-truth card idea:
`.perry/hook.md:129–134` is already a hand-written source-of-truth declaration in
the wrong file, with no `Last verified` and no `Invalidated by` — exactly the
staleness § 5.3 exists to catch.

*The strain, stated:* `May touch` is advisory and nothing enforces it. For a
software role that is fine — the union and the filesystem catch real damage. Here,
`write:` **excluding** `data/advisory/positions.yaml` *is* a safety property
(that file is the system's record of the portfolio, `ARCHITECTURE.md:45`), and it
holds only because the same path is repeated under `Must escalate`. The card
needs the path in two sections to get one guarantee. That redundancy is required
by the model, not introduced by me.

### 4.6 · `## Must escalate` — § 5 and § 6

---

## 5 · `Must escalate`, part one: can `系统永不下单` be a span the union catches?

**No.** Not because it is Chinese, and not because it is an action (§ 3.1
disposes of both). Two independent reasons.

### 5.1 · What extracts

```
P.escalation_fragments(["- any `系统永不下单`"]) → ['系统永不下单']
P.escalation_fragments(["- any `永不下单`"])   → ['永不下单']
P.escalation_fragments(["- any `下单`"])       → []            ← § 5.3
```

### 5.2 · Reason one — the invariant has inverted polarity

`系统永不下单` matches only text that **restates the prohibition** — which is
what a *compliant* spec contains and what a *violating* spec never says.

Measured on two specs in the project's own vocabulary. The violating one does
what `ARCHITECTURE.md:456` forbids; the compliant one is a task the project
actually ran (`evidence/2026-06/ADVISOR-TRACE-CHINESE-report.md:19,71`).

```
VIOLATING  ## Files in scope: `core/brokers/alpaca_adapter.py` — 新增 `submit_order` 调用
           ## Deliverable   : …自动下单执行，写回 `data/advisory/positions.yaml`
COMPLIANT  ## Deliverable   : trace banner 改为「**系统永不下单。** 本结果仅为建议…」
           ## Out of scope  : **不碰 prod / 不下单 / 不爬外部 / 不真烧 token**
```

| fragment list | VIOLATING | COMPLIANT |
|---|---|---|
| `系统永不下单` | **`pass`** — waves the violation through | **`refuse`** — blocks the compliant task |
| `永不下单` | **`pass`** | **`refuse`** |
| `下单` | `refuse` ✅ | `pass` ✅ (green-lit by `Out of scope`) |
| the card's 24 extracted spans | `refuse` ✅ (`submit_order`, `broker`, `data/advisory/positions.yaml`) | `pass` ✅ |

The gate built from the invariant *as the project states it* is **exactly
inverted**: it fires on the task that honours the rule and is silent on the task
that breaks it. That is worse than an unarmed gate, because it also trains the
user to wave it through — the failure `matching_escalations`' own docstring
records from TASK-107 ("a gate crying wolf on ordinary English gets waved
through, and the cheapest way to pass it was to reword the spec").

**The general rule this establishes, and it is the finding worth keeping:** an
escalation entry must name **what a violating task would say**, never **the rule
it would break**. `系统永不下单` is a rule. The union has no polarity — it cannot
express "escalate when this is *absent*" — so a negated invariant can only ever
enter it through its violation-side tokens.

### 5.3 · Reason two — the violation-side token is silently discarded

The correct fragment is the verb, `下单`. The table above shows it behaves
perfectly, and it is the project's own word
(`INFRA-advisor-checker-spec.md:86` — `无任何下单/交易调用`;
`ARCHITECTURE.md:26 §8` — `不下单`). It never reaches the union.

`escalation_fragments` (`viewer/parsers.py:3133`) drops any span with
`len(frag) <= 2`. `下单` is two characters. In ASCII, two characters is a
fragment of a token and dropping it is right. In Chinese, two characters is a
complete verb. The threshold counts codepoints, and the two languages do not
carry the same information per codepoint.

**And it is silent.** Parsing the drafted card:

```
>>> Was `下单` extracted?      False
>>> Was its line lint-warned?  False
```

`escalate_unextractable` (`viewer/parsers.py:3220`) flags a bullet only when
`not _BACKTICKED.search(b)`. The line *has* backticks — five other spans on it
extract — so `bin/perry-lint:1615`'s `role-escalation-not-extractable` warning
does not fire. **This is the failure class DESIGN-006 § 7 says was fixed,
arriving through the hole the fix left:** the guard checks whether a line
contains backticks, not whether a line contributed a fragment. Scale in § 8.

### 5.4 · So what can hold the invariant

**Re-expressed, the code-shaped half — and the project had already done the
re-expression.** `evidence/2026-06/WEB-ADVISORY-INGEST-report.md:98` verifies
系统永不下单 by grepping for `submit_order` / `place_order` / `execute_trade` /
`broker` / `alpaca`, backed by an AST test `test_source_has_no_order_calls`
(`journal/2026-05/2026-05-29.md:163`). Those five extract, and § 5.2's table
shows they give the right verdict both ways.

**What that costs, stated rather than hidden.** The projection is not the
invariant. `submit_order` is Python. 系统永不下单 also forbids the user's agent
emailing the RM to buy, filling a broker web form, or hand-adding an order row to
`data/advisory/positions.yaml` — the card covers the last of those by listing the
path, and the first two are outside anything a spec scanner can see. **The union
holds the code-shaped half of this invariant and nothing else, and the card must
not be read as enforcing the rest.**

### 5.5 · One bullet left unbackticked on purpose

The last bullet — `advisor-checker 不 active pull 爬 RM portal`
(`OKR.md:113`) — is a genuine constraint with no matchable token. Backticking it
would be a lie about enforcement. Left as prose so `bin/perry-lint` reports it:

```
role-escalation-not-extractable: `Must escalate` line '…不 active pull 爬 RM
portal…' has no backticked span, so it contributes nothing to the pre-flight
scan.
```

That warning is correct and the card should ship carrying it. It is the one place
the tooling tells the truth about a finance constraint it cannot enforce — and
the contrast with § 5.3, where a *backticked* CJK constraint enforces nothing and
warns about nothing, is the whole gap.

---

## 6 · `Must escalate`, part two: can the two roles coexist on one board?

### 6.1 · The two boundaries share nothing

```
hook only          :  3 fragments
hook + coding      :  8
hook + advisory    : 24
hook + BOTH        : 29
overlap coding ∩ advisory : []          ← empty
```

Twenty-nine fragments, zero shared. `coding.md` escalates on `force-push`,
`rebase`, `ci`, `deploy`, `secret`, `dependency`; `advisory-checker` on
`submit_order`, `max_position`, `phase=live`, `type: trading`,
`data/advisory/positions.yaml`. These are not two settings of one boundary. They
are two vocabularies that happen to be typed into the same field.

### 6.2 · The scan is flat and role-blind

`bin/perry-state:1954–1957`:

```python
union = P.escalation_union(project_root)
out = P.scan_spec_escalations(spec.read_text(errors="replace"), union["union"])
```

`escalation_scan` takes **a project root and a spec path**. It never reads the
task row, so it never reads the row's `Role:` cell. `union["union"]` is the flat
concatenation of the hook's fragments and *every* declared role's. Decision #4
put `Role:` on the row; the pre-flight does not consume it.

This is not an oversight — it is goal 6 ("permissions are additive-only… there is
no mechanism by which a role grants itself anything the hook forbids") taken to
its conclusion. Filtering the union by the row's role would be a *narrowing*, and
`escalation_union`'s docstring refuses narrowing by construction. **The
consequence, which the design does not state:** on a multi-role board, every
role's escalations apply to every row. Declaring the 投资线 role imposes 24 finance
fragments on every 工程线 dispatch.

### 6.3 · Measured on four specs drawn from real board rows

| # | spec (source row) | hook | +coding | +advisory | +both |
|---|---|---|---|---|---|
| A | 工程线 `THESIS-REGISTRY-v0` (`BOARD.md:81`) — registry schema, migration, tests | pass | pass | pass | pass |
| B | 工程线 `POLICY-CAP-CODE-SYNC` (`BOARD.md:53`) — `rules.py` R-2 上限 30%→40% | pass | **pass** | **refuse** | **refuse** |
| C | 投资线 `DUE-ADR-010` (`BOARD.md:57`) — 9/1 无条件 redeploy，卖 XLU 600 股 | pass | pass | **pass** | **pass** |
| D | 工程线 framework L5 execution — `broker` adapter 抽象，回测 mock | pass | pass | pass (green-lit) | pass (green-lit) |

**B is the win, and it is a real one.** A row owned by `Coding Agent`, sitting in
the 投资线 section, whose subject is a live risk cap on a $3M portfolio. The
coding card passes it. The union refuses it on `max_position`, with
`origins["max_position"] = ["role:advisory-checker"]`. Nothing else in Perry
would have caught that row, and the additive union caught it precisely because it
is *not* filtered by the row's role. **§ 6.2's "flaw" is what makes B work.**

**D shows the accepted cost, and the `Out of scope` escape working.** A research
spec legitimately about broker adapters matches `broker` in both `Files in scope`
and `Deliverable`, and is green-lit because the writer wrote `不接真 broker` under
`## Out of scope`. Without that line it is a false refusal on a 工程线 row caused
by a 投资线 card. `.perry/hook.md:112` already documents this escape as the spec
writer's safety self-attestation.

**C is the failure.** Nothing catches it under any combination.

### 6.4 · The row that needs two roles, and the cell that holds one

`BOARD.md:53 POLICY-CAP-CODE-SYNC` is simultaneously a coding task (`rules.py`,
`cli/portfolio.py`, PR #204/#205, regression suite) and an investment-policy
change (R-2 主题上限 30%→40%; the same row records the live result, `cap 40% /
breached no / r2_pct 31.50%` — 31.5 % of a ~$3M portfolio). Its `Owner` cell
says `Coding Agent`.

`schema/task-list-contract.md:151` types the field:

> `role` | string — the declared role accountable for this row, or `""`.

**One string.** Decision #4 makes it required once roles are declared. A hybrid
board's most dangerous rows are exactly the ones on the seam, and the seam rows
need two values in a single-valued cell. Today the union papers over this,
because it applies every role's fragments to every row anyway — but that means
**the field that says which role is accountable has no effect on the gate that
decides whether the row is safe**. The two facts are consistent only by accident.
If the union were ever narrowed to the row's role (an optimisation someone will
propose the first time D's false positive annoys them), B stops being caught.

**Recorded as the sharpest structural finding of this row.**

### 6.5 · The row nothing catches

`BOARD.md:57 DUE-ADR-010`: `2026-09-01 ACTION-7 无条件 redeploy（T3，卖 XLU 600
股 + 回部署）`, `9/1 是无条件触发`. Real money, a fixed date, and a warning in the
row itself that `执行方案不存在`.

Every fragment set scans it `pass`. Testing candidates one at a time to establish
this is structural, not a failure of imagination:

| candidate span | extracted? | verdict on spec C |
|---|---|---|
| `卖出` | **no** (2 chars) | — |
| `减仓` | **no** (2 chars) | — |
| `deploy` (from `coding.md`) | yes | `pass` — guarded, does not match `redeploy` |
| `redeploy` | yes | `refuse` |
| `XLU` | yes | `refuse` |
| `CATALYST-CALENDAR.md` | yes | `refuse` |
| `600 股` | yes | `refuse` |

So it **is** catchable — by a ticker, a filename, or a share count. Every one of
those is an **enumeration**, not a rule: to cover the portfolio you would list
every holding, and holdings change. A knowledge card would at least carry
`Last verified` and `Invalidated by` (§ 5.3 of the design); **a role card has no
staleness field at all**, and `perry-lint --knowledge` computes staleness for
knowledge cards only. A ticker list in `Must escalate` is a gate that decays
silently — the exact property DESIGN-006 § 1.2 says makes domain knowledge a
distinct kind of memory, reintroduced in the one file that has no mechanism for
it.

The honest statement: **the union can catch a money action only by naming the
instrument, and the card model gives that naming no expiry.**

---

## 7 · `DUE-*` — a third shape, with a verdict of its own

`BOARD.md:37` defines `DUE-*` as `日期型强制动作` — an action that must happen
by a date because an external event forces it. `BOARD.md:42` names the source of
truth: `到期动作的源仍是 CATALYST-CALENDAR.md（单一真相源）；本表是它的 board
视图`.

**`Must escalate` has no vocabulary for a deadline, and cannot acquire one
within its current mechanism.** The scan is a text match over three spec sections
(`viewer/parsers.py:3345–3372`). It has no clock, no access to the row, and no
access to `CATALYST-CALENDAR.md`. The dangerous state of a `DUE-*` row is *the
absence of a dispatch before a date* — and the union fires only when a dispatch
happens. **It is structurally incapable of firing on a thing that did not
occur.**

`BOARD.md:57` records what that costs in practice: `DUE-ADR-010`'s trigger was
locked 2026-05-15 and `自 … 从未进 CATALYST-CALENDAR`, discovered 7/28 — and the
row calls it `R-2-Z 缺口后的第三个同类实例`. Three instances of the same
class of miss on one board, none of which any escalation list could have caught.

*Where it does belong, reported not built:* this is a **risk row with a due
date**, not an escalation. Perry has `risks.jsonl` (unwritten on this project —
`perry-lint` says "no `risks.jsonl` — drift against the risks store is
unchecked, not clean") and a triage lane. A date-forced action is a triage
question, not a dispatch-time gate. **No change made.**

---

## 8 · The scale of the CJK verb problem

`escalation_fragments` on the twenty Chinese trading verbs a 投资线 role would
plausibly want to escalate on:

```
DROPPED (len<=2): 下单 买入 卖出 减仓 加仓 调仓 转账 赎回 提现 平仓
                  开仓 止损 建仓 换仓 申购 补仓 清仓 割肉
KEPT            : 加杠杆(3) 强制赎回(4)
→ 18 of 20 unrepresentable
```

Chinese finance verbs are overwhelmingly two-character compounds. A 投资线 role
card written naturally, in the project's declared document language
(`.perry/config.md:3`), in backticks, produces **zero fragments and zero
warnings**, and reads as fully constrained. That is § 5.3's mechanism at the
scale of an entire domain vocabulary.

---

## 9 · Two things found on the way

### 9.1 · The project's own escalation list is already 60 % blind

`P.escalation_union(Path("~/proj/gimegime-pmo"))`:

```json
{"project": ["phase=paper", "phase=live", ".env"], "roles": {},
 "union": ["phase=paper", "phase=live", ".env"], "armed": true}
```

`.perry/hook.md:91 § High-stakes operations requiring user authorization` has
five bullets; three contribute **zero** fragments:

- `:95` `Any change to risk-gate parameters (kill switch behavior,
  max_daily_loss, max_position, stale_order_minutes)` — parameter names in bare
  parentheses, no backticks
- `:98` `Adding a new paid data source or LLM provider`
- `:99` `Increasing the monthly cost ceiling above the current cap`

The project's real refusal-trigger list — the one with all the backticks — lives
at `.perry/hook.md:104–109` under `## Auto-dispatch contract (/pmo dispatch)`, a
heading `hook_escalation_lines` does not read.

So on the very project § 6.1 F names as the pass-condition candidate, the shipped
hook already carries the § 7 bug, and the drafted card's `Must escalate` repairs
it from the role side: 3 → 26 fragments, 23 attributed to
`role:advisory-checker`, including the `max_position` that catches row B. **This
is the strongest evidence in the report that the union half of the model
survives contact with a real project.**

### 9.2 · The scan cannot read a Chinese spec at all

`P.alias("headings", "Files in scope")` → `('Files in scope',)`. Same for
`Deliverable` and `Out of scope`. `schema/state-schema.json § i18n.headings` has
`zh` aliases for 35 headings — including `High-stakes operations → 高风险操作` —
and **none for the three sections the escalation scan reads**.

Measured: the violating spec from § 5.2, with its headings written
`## 涉及文件` / `## 交付物` / `## 不在范围`, scans `verdict: "pass"` with the full
24-fragment list. Every section comes back empty, nothing matches, the gate
reports clean.

Not hypothetical here. gimegime-pmo's real specs use `## §8. Executor 交付物` and
`## §6. 安全约束（必守）` (`evidence/2026-05/INFRA-advisor-checker-spec.md:84,102`).
Running the real scan over three real gimegime specs with the 24-span card:

| spec | verdict | whole-document match |
|---|---|---|
| `evidence/2026-05/INFRA-advisor-checker-spec.md` | `pass` | — |
| `evidence/2026-06/INFRA-framework-build-phase1-spec.md` | `pass` | `broker` present in the body |
| `evidence/2026-06/INFRA-research-harness-v1-spec.md` | `pass` | — |

Three `pass` verdicts, one containing a term the card escalates on. The gate is
armed, reports clean, and has read nothing.

---

## 10 · Findings requiring a tool change — reported, not made

Nothing in `bin/`, `schema/`, `viewer/`, `packs/` or `tests/` was modified.

1. **`escalation_fragments`' `len(frag) > 2` floor discards CJK verbs**
   (`viewer/parsers.py:3133`). 18 of 20 Chinese trading verbs, `下单` included.
   Candidate fix: make the floor character-class-aware, or weight by script.
   **A behaviour change to a safety gate — needs its own row and its own
   reverting test.**
2. **`escalate_unextractable` under-reports** (`viewer/parsers.py:3220`). It flags
   a bullet with *no* backticks; it should flag a bullet that contributed *no
   fragment*. Note `schema/roles-list-contract.md § must_escalate.unextractable`
   freezes this field for aiMark, so widening it is a **semantics** change under
   that contract's rule 3, not a silent fix.
3. **`i18n.headings` has no `zh` aliases for `Files in scope` / `Deliverable` /
   `Out of scope`** (§ 9.2). The three sections the pre-flight reads are the three
   the glossary omits, while the hook heading it reads *is* glossaried. Per the
   schema's own note: "adding a language means adding its aliases here and
   widening the `match` regexes in `files[].headings`".
4. **The pre-flight ignores the row's `Role:`** (§ 6.2, `bin/perry-state:1954`).
   Currently correct-by-accident and load-bearing — row B is caught *because* of
   it. **Worth pinning with a test before someone "optimises" it**, since the
   union's additive guarantee is stated for the fragment list but not for the
   scan's input.
5. **A single-valued `role` cell cannot describe a seam row** (§ 6.4,
   `schema/task-list-contract.md:151`). A decision, not a patch.
6. **`Executors` cannot name a human counterparty** (§ 4.3). A gap between § 5.2's
   model and what `## Special agents available` already carries in the field.
7. **A role card has no staleness field** (§ 6.5). Knowledge cards get
   `Last verified` / `Invalidated by` and a lint check; a `Must escalate` list of
   tickers or paths decays silently.
8. **No bulk promotion path from an existing `knowledge/` tree to cards**
   (§ 4.4). Phase B lists bulk import out of scope; the pass condition needs it,
   because a real project arrives with digests already written.
9. *(cosmetic)* `scan_spec_escalations`' `green_lit` does not de-duplicate across
   `touches` sections while `refuse` does (`viewer/parsers.py:3378–3384`) — spec D
   reports `['broker', 'broker']`.

---

## 11 · Answer to the pass condition

DESIGN-006 § 6.1 F: *"the abstraction survives contact with a real non-software
role, or the extraction report says why not."* The project turned out to be a
hybrid, which made the test sharper: **can one board carry two roles whose
escalation boundaries differ in kind?**

**Yes for the seam, no for the money.**

The additive union is the part that survives, and it survives well: on a real
board it catches a real coding row whose subject is a live risk cap, and it
repairs a real blind spot the project's own hook has been shipping (§ 9.1). Two
disjoint vocabularies coexist in one flat list without collapsing, and the
`Out of scope` green light absorbs the cross-line false positive.

What does not survive is the 投资线 half's central invariant. `系统永不下单`
cannot be a useful union entry: as the whole phrase it is polarity-inverted,
firing on compliance and passing violation; as its violation-side verb `下单` it
is silently discarded, along with 17 of the 19 other verbs a Chinese finance role
would reach for, with no warning from the linter that is supposed to catch
exactly this class. The invariant enters the union only as the five ASCII
identifiers the project already greps for, which cover its code-shaped half and
nothing else. And `DUE-*` — an action forced by a date — is a shape the mechanism
cannot represent at all, because the union fires on dispatches and the danger is
a dispatch that never happens.

**The abstraction holds the software half of a hybrid board and the seam between
the halves. It does not hold the half where the money is.**
